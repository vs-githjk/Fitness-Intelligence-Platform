import { expect, request, test } from '@playwright/test'
import { apiUrl } from './config'

test('visitor explores read-only trainee and coach demo workspaces', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('link', { name: 'Explore Demo' }).click()
  await expect(page.getByRole('heading', { name: 'Explore the public demo' })).toBeVisible()
  await page.getByRole('button', { name: 'View as Trainee' }).click()
  await expect(page).toHaveURL(/\/trainee\/today$/)
  await expect(page.getByRole('status', { name: 'Demo workspace' })).toContainText('changes are disabled')
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
