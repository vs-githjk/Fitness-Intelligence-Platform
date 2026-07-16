import { expect, request, test } from '@playwright/test'
import { apiUrl } from './config'

test('real coach roster never survives sign-out into the coach demo', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email address').fill('coach@fitness.example.com')
  await page.locator('input[name="password"]').fill('DemoPass123!')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/coach\/dashboard$/)
  await expect(page.getByText('Arjun Trainee', { exact: true }).first()).toBeVisible()

  await page.getByRole('button', { name: 'Sign out' }).first().click()
  await page.getByRole('link', { name: 'Explore Demo' }).click()
  const demoRosterResponse = page.waitForResponse(response =>
    response.url().endsWith('/coach/trainees') && response.request().method() === 'GET',
  )
  await page.getByRole('button', { name: 'View as Coach' }).click()
  const demoRoster = await (await demoRosterResponse).json() as Array<{ trainee_id: string }>

  await expect(page.getByRole('status', { name: 'Demo workspace' })).toBeVisible()
  expect(demoRoster).toHaveLength(7)
  await expect(page.getByText('Aarav Improving', { exact: true }).first()).toBeVisible()
  await expect(page.getByText('Arjun Trainee', { exact: true })).toHaveCount(0)
})

test('visitor explores read-only trainee and coach demo workspaces', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/login')
  await expect(page).toHaveTitle('FitIntel 360')
  await expect(page.getByAltText('FitIntel 360').first()).toHaveAttribute('src', '/brand/fitintel360-logo.png')
  await page.getByRole('link', { name: 'Explore Demo' }).click()
  await expect(page.getByRole('heading', { name: 'Explore the public demo' })).toBeVisible()
  await page.getByRole('button', { name: 'View as Trainee' }).click()
  await expect(page).toHaveURL(/\/trainee\/today$/)
  await expect(page.locator('img[src="/brand/fitintel360-mark.png"]:visible')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
  await expect(page.getByRole('status', { name: 'Demo workspace' })).toContainText('changes are disabled')
  await expect(page.getByRole('heading', { name: 'Synthetic demo coach' })).toBeVisible()
  await expect(page.getByText('Maya Demo Coach', { exact: true })).toBeVisible()
  await expect(page.getByText('This is sample information from the read-only demo workspace.')).toBeVisible()
  await expect(page.getByText('Training readiness', { exact: true })).toBeVisible()
  await page.goto('/trainee/progress')
  await expect(page.getByRole('heading', { name: 'Longitudinal fitness intelligence' })).toBeVisible()
  await page.getByRole('button', { name: 'Exit demo' }).first().click()
  await expect(page).toHaveURL(/\/login$/)

  await page.getByRole('link', { name: 'Explore Demo' }).click()
  await page.getByRole('button', { name: 'View as Coach' }).click()
  await expect(page).toHaveURL(/\/coach\/dashboard$/)
  await expect(page.getByRole('heading', { name: 'Today across your roster' })).toBeVisible()
  const review = page.getByRole('link', { name: /Review trainee/ }).first()
  await expect(review).toBeVisible()
  await review.click()
  await expect(page.getByRole('heading', { name: 'Daily recovery and readiness' })).toBeVisible()

  const token = await page.evaluate(() => localStorage.getItem('access_token'))
  const api = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${token}` } })
  const mutation = await api.post(`${apiUrl}/coach/invites`, { data: { expires_in_days: 1 } })
  expect(mutation.status()).toBe(403)
  expect(await mutation.json()).toMatchObject({ detail: { code: 'demo_read_only' } })
  await api.dispose()

  await page.getByRole('button', { name: 'Exit demo' }).first().click()
  await expect(page.getByLabel('Email address')).toBeVisible()
  await expect(page.getByRole('textbox', { name: 'Password' })).toBeVisible()
})

test('trainee coach details stay isolated across normal and demo sessions', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Email address').fill('trainee@fitness.example.com')
  await page.locator('input[name="password"]').fill('DemoPass123!')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/trainee\/(today|dashboard)$/)
  await expect(page.getByRole('heading', { name: 'Your coach' })).toBeVisible()
  await expect(page.getByText('Maya Coach', { exact: true })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Email Maya Coach outside FitIntel 360' })).toBeVisible()

  await page.getByRole('button', { name: 'Sign out' }).first().click()
  await page.getByRole('link', { name: 'Explore Demo' }).click()
  await page.getByRole('button', { name: 'View as Trainee' }).click()
  await expect(page.getByRole('heading', { name: 'Synthetic demo coach' })).toBeVisible()
  await expect(page.getByText('Maya Demo Coach', { exact: true })).toBeVisible()
  await expect(page.getByText('Maya Coach', { exact: true })).toHaveCount(0)

  await page.setViewportSize({ width: 320, height: 800 })
  await expect(page.getByRole('heading', { name: 'Synthetic demo coach' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
})

test('coach creates and manually copies an invitation without email delivery UI', async ({ page }) => {
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: 'http://localhost:5175' })
  await page.goto('/login')
  await page.getByLabel('Email address').fill('coach@fitness.example.com')
  await page.locator('input[name="password"]').fill('DemoPass123!')
  await page.getByRole('button', { name: 'Sign in' }).click()
  await expect(page).toHaveURL(/\/coach\/dashboard$/)
  await page.goto('/coach/invites')

  await expect(page.getByLabel('Restrict to trainee email (optional)')).toBeVisible()
  await expect(page.getByText(/does not send this invitation by email/i)).toBeVisible()
  await expect(page.getByText(/Leave it blank to allow any eligible trainee possessing the invitation/i)).toBeVisible()
  await expect(page.getByRole('button', { name: /send email/i })).toHaveCount(0)
  await page.getByRole('button', { name: 'Create invite' }).click()
  await expect(page.getByText('Invitation created—copy it now')).toBeVisible()
  await page.getByRole('button', { name: 'Copy invitation link' }).click()
  await expect(page.getByText('Link copied')).toBeVisible()
})
