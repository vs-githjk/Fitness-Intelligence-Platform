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

async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
}

test('coach publishes a private exercise and a versioned workout template', async ({ page }) => {
  await coachSession(page)
  const suffix = Date.now()
  const exerciseName = `E2E split squat ${suffix}`
  const templateName = `E2E strength session ${suffix}`

  await page.goto('/coach/programming/exercises')
  await expect(page.getByRole('heading', { name: 'Exercise library' })).toBeVisible()
  await page.getByRole('link', { name: 'New exercise' }).click()
  await page.getByLabel('Name').fill(exerciseName)
  await page.getByLabel('Instructions').fill('Stand tall and lower under control.')
  await page.getByLabel('Category').fill('strength')
  await page.getByLabel('Movement pattern').fill('squat')
  await page.getByLabel('Equipment').fill('dumbbell')
  await page.getByLabel('Primary muscle groups').fill('quadriceps, glutes')
  await page.getByLabel('Safety cues').fill('Keep knee aligned, Maintain balance')
  await page.getByRole('button', { name: 'Save draft' }).click()
  await expect(page.getByText('Draft saved')).toBeVisible()
  await page.getByRole('button', { name: 'Review and publish' }).click()
  await expect(page.getByRole('dialog', { name: 'Publish exercise version?' })).toBeVisible()
  await page.getByRole('button', { name: 'Confirm publication' }).click()
  await expect(page.getByText(/Immutable published version 1/)).toBeVisible()
  await expect(page.getByLabel('Name')).toBeDisabled()

  await page.goto('/coach/programming/templates')
  await page.getByRole('link', { name: 'New template' }).click()
  await page.getByLabel('Name').fill(templateName)
  await page.getByLabel('Goal tags').fill('strength, lower_body')
  await page.getByLabel('Estimated duration (minutes)').fill('45')
  await page.getByLabel('Target session RPE').fill('7')
  await page.getByRole('button', { name: 'Add exercise' }).click()
  await page.getByLabel('Search selectable exercises').fill(exerciseName)
  await page.getByRole('button', { name: new RegExp(exerciseName) }).click()
  await page.getByRole('button', { name: 'Add to workout' }).click()
  await page.getByLabel('Repetitions min').fill('8')
  await page.getByLabel('Repetitions max').fill('10')
  await page.getByLabel(/^Target load/).first().fill('22')
  await page.getByLabel('Target load unit').selectOption('lb')
  await page.getByLabel('Coach notes').last().fill('Private coaching detail')
  await page.getByLabel('Trainee instructions').last().fill('Use a controlled tempo')
  await page.getByRole('button', { name: 'Add exercise' }).click()
  await page.getByLabel('Search selectable exercises').fill('Front plank')
  await page.getByRole('button', { name: /Front plank/ }).click()
  await page.getByRole('button', { name: 'Add to workout' }).click()
  await page.getByLabel('Target duration (seconds)').fill('45')
  await page.getByRole('button', { name: `Move ${exerciseName} down` }).click()
  await page.getByRole('button', { name: 'Save draft' }).click()
  await expect(page.getByText('Draft saved')).toBeVisible()
  await expect(page.locator('[aria-label="Trainee workout preview"]').getByText('Private coaching detail')).toHaveCount(0)
  await expect(page.locator('[aria-label="Trainee workout preview"]').getByText('Front plank')).toBeVisible()
  await page.getByRole('button', { name: 'Review and publish' }).click()
  await expect(page.getByRole('dialog', { name: 'Review and publish workout' })).toBeVisible()
  await page.getByRole('button', { name: 'Confirm publication' }).click()
  await expect(page.getByText(/Immutable published version 1/)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Create revision' })).toBeVisible()
  await page.getByRole('button', { name: 'Create revision' }).click()
  await expect(page.getByRole('button', { name: 'Save draft' })).toBeVisible()
  await page.getByRole('button', { name: 'Archive' }).click()
  await page.getByRole('button', { name: 'Archive template' }).click()
  await expect(page.getByText('Template archived')).toBeVisible()
})

test('Programming workspace is read-only in demo and responsive at supported widths', async ({ page }) => {
  await page.goto('/demo')
  await page.getByRole('button', { name: 'View as Coach' }).click()
  await page.goto('/coach/programming/exercises')
  await expect(page.getByRole('button', { name: 'New exercise' })).toBeDisabled()
  await expect(page.getByText(/changes are disabled/i).first()).toBeVisible()
  await page.goto('/coach/programming/templates')
  await expect(page.getByRole('button', { name: 'New template' })).toBeDisabled()

  for (const width of [320, 390, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 900 })
    await page.goto('/coach/programming/exercises')
    await expect(page.getByRole('heading', { name: 'Exercise library' })).toBeVisible()
    await expectNoOverflow(page)
    await page.goto('/coach/programming/templates')
    await expect(page.getByRole('heading', { name: 'Workout templates' })).toBeVisible()
    await expectNoOverflow(page)
  }
})
