import { APIRequestContext, expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

// A real 1x1 PNG so the backend's magic-byte signature check passes.
const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
)

async function login(email: string, password = 'DemoPass123!') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/login`, { data: { email, password } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() as { access_token: string; user: { id: string } } }
}

async function demoSession(role: 'coach' | 'trainee') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/demo-session`, { data: { role } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() as { access_token: string; user: unknown } }
}

async function setSession(page: Page, auth: { access_token: string; user: unknown }) {
  await page.addInitScript(session => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

async function apiSetAvatar(ctx: APIRequestContext, token: string) {
  const res = await ctx.put(`${apiUrl}/me/avatar`, {
    headers: { Authorization: `Bearer ${token}` },
    multipart: { file: { name: 'avatar.png', mimeType: 'image/png', buffer: PNG } },
  })
  expect(res.ok()).toBeTruthy()
}

async function apiRemoveAvatar(ctx: APIRequestContext, token: string) {
  const res = await ctx.delete(`${apiUrl}/me/avatar`, { headers: { Authorization: `Bearer ${token}` } })
  expect(res.status()).toBe(204)
}

test('coach uploads, replaces, edits, and removes their profile', async ({ page }) => {
  test.slow()
  const { ctx, auth } = await login('coach@fitness.example.com')
  await setSession(page, auth)
  await page.goto('/profile')
  await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible()

  // Upload a photo through the UI.
  await page.getByLabel('Choose a profile photo').setInputFiles({ name: 'me.png', mimeType: 'image/png', buffer: PNG })
  await expect(page.getByTestId('avatar-preview')).toBeVisible()
  await page.getByRole('button', { name: 'Upload photo' }).click()
  await expect(page.getByText('Your photo was updated.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Remove' })).toBeVisible()

  // Replace it with a different file.
  await page.getByLabel('Choose a profile photo').setInputFiles({ name: 'me2.png', mimeType: 'image/png', buffer: PNG })
  await page.getByRole('button', { name: 'Upload photo' }).click()
  await expect(page.getByText('Your photo was updated.')).toBeVisible()

  // Edit professional fields.
  await page.getByLabel(/Headline/).fill('E2E strength coach')
  await page.getByLabel(/Specialties/).fill('Powerlifting, Mobility')
  await page.getByLabel(/Years of experience/).fill('9')
  await expect(page.getByTestId('specialty-preview')).toContainText('Powerlifting')
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByText('Profile saved')).toBeVisible()

  await page.reload()
  await expect(page.getByLabel(/Headline/)).toHaveValue('E2E strength coach')
  await expect(page.getByLabel(/Years of experience/)).toHaveValue('9')

  // Remove the photo and restore the seed to its avatar-free state.
  await page.getByRole('button', { name: 'Remove' }).click()
  await expect(page.getByText('Your photo was removed.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Add photo' })).toBeVisible()
  await ctx.dispose()
})

test('trainee edits training goals without seeing coach-only fields', async ({ page }) => {
  const { ctx, auth } = await login('trainee@fitness.example.com')
  await ctx.dispose()
  await setSession(page, auth)
  await page.goto('/profile')
  await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible()
  await expect(page.getByLabel(/Specialties/)).toHaveCount(0)

  const goals = page.getByLabel(/working toward/)
  await goals.fill('Deadlift bodyweight by winter')
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByText('Profile saved')).toBeVisible()
  await page.reload()
  await expect(page.getByLabel(/working toward/)).toHaveValue('Deadlift bodyweight by winter')
})

test('a coach photo is delivered to their assigned trainee', async ({ page }) => {
  const coach = await login('coach@fitness.example.com')
  await apiSetAvatar(coach.ctx, coach.auth.access_token)

  const trainee = await login('trainee@fitness.example.com')
  // The relationship endpoint advertises the authorized delivery path.
  const relationship = await trainee.ctx.get(`${apiUrl}/trainee/coach`, {
    headers: { Authorization: `Bearer ${trainee.auth.access_token}` },
  })
  const rel = await relationship.json()
  expect(rel.assignment_status).toBe('active')
  expect(rel.coach_avatar_url).toBe(`/users/${coach.auth.user.id}/avatar/content`)
  // And that path streams the image bytes to the related trainee.
  const image = await trainee.ctx.get(`${apiUrl}/users/${coach.auth.user.id}/avatar/content`, {
    headers: { Authorization: `Bearer ${trainee.auth.access_token}` },
  })
  expect(image.ok()).toBeTruthy()
  expect(image.headers()['content-type']).toContain('image/')

  // The trainee UI renders the coach's photo on the Today page.
  await setSession(page, trainee.auth)
  await page.goto('/trainee/today')
  const coachCard = page.locator('section', { has: page.getByRole('heading', { name: 'Your coach' }) })
  await expect(coachCard.locator('img')).toBeVisible()

  await apiRemoveAvatar(coach.ctx, coach.auth.access_token)
  await coach.ctx.dispose()
  await trainee.ctx.dispose()
})

test('demo coach cannot edit profile or avatar', async ({ page }) => {
  const { ctx, auth } = await demoSession('coach')
  const denied = await ctx.put(`${apiUrl}/me/avatar`, {
    headers: { Authorization: `Bearer ${auth.access_token}` },
    multipart: { file: { name: 'x.png', mimeType: 'image/png', buffer: PNG } },
  })
  expect(denied.status()).toBe(403)
  expect((await denied.json()).detail.code).toBe('demo_read_only')
  await ctx.dispose()

  await setSession(page, auth)
  await page.goto('/profile')
  await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Add photo' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Save profile' })).toBeDisabled()
})
