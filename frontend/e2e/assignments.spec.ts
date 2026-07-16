import { expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

async function credentialSession(page: Page, email: string) {
  const context = await request.newContext()
  const response = await context.post(`${apiUrl}/auth/login`, { data: { email, password: 'DemoPass123!' } })
  expect(response.ok()).toBeTruthy()
  const auth = await response.json()
  await context.dispose()
  await page.addInitScript(session => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

function futureDate(days = 7) {
  const value = new Date(); value.setDate(value.getDate() + days)
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
}

async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
}

test('coach previews and assigns a future Program replacement', async ({ page }) => {
  await credentialSession(page, 'coach@fitness.example.com')
  await page.goto('/coach/assignments')
  await expect(page.getByRole('heading', { name: 'Program assignments' })).toBeVisible()
  await page.getByLabel('Trainee').selectOption({ label: 'Arjun Trainee' })
  await page.getByLabel('Effective start date').fill(futureDate())
  await page.getByRole('button', { name: 'Preview schedule' }).click()
  await expect(page.getByText('Schedule preview')).toBeVisible()
  await expect(page.getByText('This changes an existing plan')).toBeVisible()
  await page.getByRole('button', { name: 'Review assignment' }).click()
  await expect(page.getByRole('dialog', { name: 'Confirm Program assignment' })).toBeVisible()
  await page.getByRole('button', { name: 'Confirm assignment' }).click()
  await expect(page.getByText('Upcoming replacement')).toBeVisible()
  await expect(page.getByText('Assignment history')).toBeVisible()
})

test('trainee sees current Program, today context, calendar, and executable workout details', async ({ page }) => {
  await credentialSession(page, 'trainee@fitness.example.com')
  await page.goto('/trainee/program')
  await expect(page.getByText('Current Program')).toBeVisible()
  await expect(page.getByRole('heading', { name: "Today's Workout" })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Workout Calendar' })).toBeVisible()
  const details = page.getByRole('button', { name: /View workout details/ }).first()
  if (await details.count()) {
    await details.click()
    await expect(page.getByRole('link', { name: /open workout|resume workout|view workout summary/i })).toBeVisible()
  }
})

test('demo coach and trainee can browse assignments but cannot mutate', async ({ page }) => {
  await page.goto('/demo')
  await page.getByRole('button', { name: 'View as Coach' }).click()
  await page.goto('/coach/assignments')
  await expect(page.getByRole('button', { name: 'Preview schedule' })).toBeDisabled()
  await expect(page.getByText('Assignment history')).toBeVisible()

  await page.getByRole('button', { name: 'Exit demo' }).first().click()
  await page.goto('/demo')
  await page.getByRole('button', { name: 'View as Trainee' }).click()
  await page.goto('/trainee/program')
  await expect(page.getByText('Current Program')).toBeVisible()
  await expect(page.getByRole('heading', { name: "Today's Workout" })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Workout Calendar' })).toBeVisible()

  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.reload()
    await expect(page.getByRole('heading', { name: 'Workout Calendar' })).toBeVisible()
    await expectNoOverflow(page)
  }
})
