import { expect, request, test } from '@playwright/test'
import { systemApiUrl } from './config'

test('hosted staging exposes safe public health and SPA routes', async ({ page }) => {
  const api = await request.newContext()
  const live = await api.get(`${systemApiUrl}/health/live`)
  expect(live.ok()).toBeTruthy()
  expect(await live.json()).toMatchObject({ status: 'healthy', version: '0.4.2' })
  await api.dispose()

  await page.goto('/login')
  await expect(page.getByRole('status', { name: 'Staging environment' })).toContainText('synthetic test data only')
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()

  await page.goto('/trainee/today')
  await expect(page).toHaveURL(/\/login$/)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
})
