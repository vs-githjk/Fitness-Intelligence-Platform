import { expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

async function coachSession(page: Page) {
  const context = await request.newContext()
  const response = await context.post(`${apiUrl}/auth/login`, { data: { email: 'coach@fitness.example.com', password: 'DemoPass123!' } })
  expect(response.ok()).toBeTruthy()
  const auth = await response.json()
  await context.dispose()
  await page.addInitScript(session => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

async function addWorkout(page: Page, weekIndex: number, name: string) {
  await page.locator('details').nth(weekIndex).getByRole('button', { name: 'Add workout' }).first().click()
  const picker = page.getByRole('dialog', { name: 'Add workout to program' })
  await picker.getByRole('button', { name: new RegExp(name) }).click()
  await picker.getByRole('button', { name: 'Add workout', exact: true }).click()
}

async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
}

test('coach publishes, revises, and archives an exact-version multi-week program', async ({ page }) => {
  await coachSession(page)
  const name = `E2E four week program ${Date.now()}`
  await page.goto('/coach/programming/programs')
  await expect(page.getByRole('heading', { name: 'Programs' })).toBeVisible()
  await expect(page.getByRole('tab', { name: 'Programs' })).toHaveAttribute('aria-selected', 'true')
  await page.getByRole('link', { name: 'New program' }).click()
  await page.getByLabel('Name').fill(name)
  await page.getByLabel('Goal tags').fill('strength, general_fitness')
  await page.getByLabel('Trainee instructions').fill('Follow the planned order and contact your coach if needed.')

  await addWorkout(page, 0, 'Full Body Strength')
  await addWorkout(page, 0, 'Recovery and Mobility')
  await page.getByLabel('Required workout').last().uncheck()
  await page.getByRole('button', { name: 'Move Recovery and Mobility up' }).click()
  await addWorkout(page, 1, 'Full Body Strength')
  await page.getByLabel('Coach-authored deload week').nth(3).check()

  await page.getByRole('button', { name: 'Save draft' }).click()
  await expect(page.getByText('Draft saved')).toBeVisible()
  const preview = page.locator('[aria-label="Trainee program preview"]').first()
  await expect(preview.getByText(name)).toBeVisible()
  await expect(preview.getByText('Optional')).toBeVisible()
  await expect(preview.getByText('Coach-authored deload')).toBeVisible()

  await page.getByRole('button', { name: 'Review and publish' }).click()
  await expect(page.getByRole('dialog', { name: 'Review and publish program' })).toBeVisible()
  await page.getByRole('button', { name: 'Confirm publication' }).click()
  await expect(page.getByText(/Immutable published version 1/)).toBeVisible()
  await expect(page.getByLabel('Name')).toBeDisabled()
  await page.getByRole('button', { name: 'Create revision' }).click()
  await expect(page.getByRole('button', { name: 'Save draft' })).toBeVisible()
  await page.getByRole('button', { name: 'Archive' }).click()
  await expect(page.getByRole('dialog', { name: 'Archive training program?' })).toBeVisible()
  await page.getByRole('button', { name: 'Archive program' }).click()
  await expect(page.getByText('Program archived')).toBeVisible()
})

test('program workspace is read-only in demo and responsive at supported widths', async ({ page }) => {
  await page.goto('/demo')
  await page.getByRole('button', { name: 'View as Coach' }).click()

  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/coach/programming/programs')
    await expect(page.getByRole('heading', { name: 'Programs' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'New program' })).toBeDisabled()
    await expectNoOverflow(page)
  }
})
