import { APIRequestContext, expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

// A real 1x1 PNG and a minimal MP4 whose 'ftyp' box passes the server signature check.
const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
)
const MP4 = Buffer.concat([Buffer.from([0, 0, 0, 0x18]), Buffer.from('ftypisom'), Buffer.alloc(40)])

async function login(email: string, password = 'DemoPass123!') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/login`, { data: { email, password } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() as { access_token: string } }
}

async function demoSession(role: 'coach' | 'trainee') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/demo-session`, { data: { role } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() as { access_token: string; user: unknown } }
}

async function setSession(page: Page, auth: { access_token: string; user?: unknown }) {
  await page.addInitScript(session => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user ?? { role: 'coach' }))
  }, auth)
}

async function firstSystemExerciseId(ctx: APIRequestContext, token: string): Promise<string> {
  const res = await ctx.get(`${apiUrl}/coach/exercises?scope=system`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const list = await res.json()
  return list[0].id
}

test('coach authors an exercise with knowledge, image, and video', async ({ page }) => {
  test.slow()
  const { ctx, auth } = await login('coach@fitness.example.com')
  await setSession(page, { access_token: auth.access_token, user: { role: 'coach', id: 'x', email: 'coach@fitness.example.com', first_name: 'C', last_name: 'H', is_demo: false } })

  await page.goto('/coach/programming/exercises/new')
  await page.getByLabel('Name').fill(`E2E Media Exercise ${Date.now()}`)
  await page.getByLabel('Instructions').fill('Perform the movement with controlled tempo.')
  await page.getByLabel('Category').fill('strength')
  await page.getByLabel('Movement pattern').fill('squat')
  await page.getByLabel('Primary muscle groups').fill('quadriceps, glutes')
  await page.getByLabel('Difficulty').selectOption('beginner')
  await page.getByLabel('Coaching cues').fill('Chest tall, knees out')
  await page.getByLabel('Common mistakes').fill('Heels lifting')
  await page.getByRole('button', { name: 'Save draft' }).click()
  await expect(page.getByText('Draft saved')).toBeVisible()

  // The read-only preview reflects the authored knowledge.
  await expect(page.getByRole('heading', { name: 'Preview' })).toBeVisible()
  await expect(page.getByText('Chest tall')).toBeVisible()
  await expect(page.getByText('No image yet')).toBeVisible()
  await expect(page.getByText('No video yet')).toBeVisible()

  // Upload a primary image and a demonstration video through the media manager.
  await page.getByLabel('Choose primary image').setInputFiles({ name: 'demo.png', mimeType: 'image/png', buffer: PNG })
  await page.getByRole('button', { name: 'Upload' }).click()
  await expect(page.getByText('No image yet')).toHaveCount(0)

  await page.getByLabel('Choose demonstration video').setInputFiles({ name: 'demo.mp4', mimeType: 'video/mp4', buffer: MP4 })
  await page.getByRole('button', { name: 'Upload' }).click()
  await expect(page.getByText('No video yet')).toHaveCount(0)

  // Publish the exercise; media becomes part of the immutable version.
  await page.getByRole('button', { name: 'Review and publish' }).click()
  await page.getByRole('button', { name: 'Confirm publication' }).click()
  await expect(page.getByText(/Immutable published version 1/)).toBeVisible()
  await ctx.dispose()
})

test('a system starter exercise is read-only with no media controls', async ({ page }) => {
  const { ctx, auth } = await login('coach@fitness.example.com')
  const systemId = await firstSystemExerciseId(ctx, auth.access_token)
  await ctx.dispose()
  await setSession(page, { access_token: auth.access_token, user: { role: 'coach', id: 'x', email: 'coach@fitness.example.com', first_name: 'C', last_name: 'H', is_demo: false } })

  await page.goto(`/coach/programming/exercises/${systemId}`)
  await expect(page.getByText('System · read-only')).toBeVisible()
  // No upload controls are offered for system exercises, but the preview still renders.
  await expect(page.getByLabel('Choose primary image')).toHaveCount(0)
  await expect(page.getByRole('heading', { name: 'Preview' })).toBeVisible()
  await expect(page.getByLabel('Name')).toBeDisabled()
})

test('demo coach cannot upload exercise media', async ({ page }) => {
  const { ctx, auth } = await demoSession('coach')
  const systemId = await firstSystemExerciseId(ctx, auth.access_token)
  // The mutation is demo-protected at the API level.
  const denied = await ctx.put(`${apiUrl}/coach/exercises/${systemId}/media/primary_image`, {
    headers: { Authorization: `Bearer ${auth.access_token}` },
    multipart: { file: { name: 'x.png', mimeType: 'image/png', buffer: PNG } },
  })
  expect([403]).toContain(denied.status())
  await ctx.dispose()

  await setSession(page, auth)
  await page.goto(`/coach/programming/exercises/${systemId}`)
  await expect(page.getByText('System · read-only')).toBeVisible()
})
