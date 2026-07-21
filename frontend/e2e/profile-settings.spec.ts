import { expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

async function login(email: string, password = 'DemoPass123!') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/login`, { data: { email, password } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() }
}

async function demoSession(role: 'coach' | 'trainee') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/demo-session`, { data: { role } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() }
}

async function setSession(page: Page, auth: { access_token: string; user: unknown }) {
  await page.addInitScript((session) => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

test('coach edits and persists their profile display name', async ({ page }) => {
  const { ctx, auth } = await login('coach@fitness.example.com')
  await ctx.dispose()
  await setSession(page, auth)
  await page.goto('/profile')
  await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible()
  const nameField = page.getByLabel(/Preferred display name/)
  await nameField.fill('Coach E2E Display')
  await page.getByRole('button', { name: 'Save profile' }).click()
  await expect(page.getByText('Profile saved')).toBeVisible()

  await page.reload()
  await expect(page.getByLabel(/Preferred display name/)).toHaveValue('Coach E2E Display')
})

test('trainee changes and persists a unit preference', async ({ page }) => {
  const { ctx, auth } = await login('trainee@fitness.example.com')
  await ctx.dispose()
  await setSession(page, auth)
  await page.goto('/settings')
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
  await page.getByLabel('Weight unit').selectOption('lb')
  await page.getByRole('button', { name: 'Save settings' }).click()
  await expect(page.getByText('Settings saved')).toBeVisible()

  await page.reload()
  await expect(page.getByLabel('Weight unit')).toHaveValue('lb')

  // Restore the default so the shared seed stays deterministic for other specs.
  await page.getByLabel('Weight unit').selectOption('kg')
  await page.getByRole('button', { name: 'Save settings' }).click()
  await expect(page.getByText('Settings saved')).toBeVisible()
})

test('demo trainee can view settings but cannot mutate identity', async ({ page }) => {
  const { ctx, auth } = await demoSession('trainee')
  // The mutation endpoint is demo-protected at the API level.
  const denied = await ctx.put(`${apiUrl}/me/preferences`, {
    headers: { Authorization: `Bearer ${auth.access_token}` },
    data: { weight_unit: 'lb' },
  })
  expect(denied.status()).toBe(403)
  expect((await denied.json()).detail.code).toBe('demo_read_only')
  await ctx.dispose()

  await setSession(page, auth)
  await page.goto('/settings')
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
  await expect(page.getByRole('status', { name: 'Demo workspace' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Save settings' })).toBeDisabled()
  await expect(page.getByLabel('Weight unit')).toBeDisabled()
})

test('profile page has no horizontal overflow at 320px', async ({ page }) => {
  const { ctx, auth } = await login('trainee@fitness.example.com')
  await ctx.dispose()
  await setSession(page, auth)
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/profile')
  await expect(page.getByRole('heading', { name: 'Your profile' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
})
