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
  return auth
}

function futureDate(days = 10) {
  const value = new Date(); value.setDate(value.getDate() + days)
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
}

test('coach clones a starter program, edits, publishes, assigns, and the trainee gets a schedule', async ({ page }) => {
  test.slow()
  await credentialSession(page, 'coach@fitness.example.com')

  // Browse the starter library and open a program preview (read-only).
  await page.goto('/coach/programming/library')
  await expect(page.getByRole('heading', { name: 'Starter Library' })).toBeVisible()
  await expect(page.getByText('Starter Library — read-only')).toBeVisible()
  const card = page.locator('article', { hasText: 'Beginner Full-Body Strength' }).first()
  await card.getByRole('link', { name: /View details/ }).click()
  await expect(page.getByRole('heading', { name: 'Beginner Full-Body Strength' })).toBeVisible()
  await expect(page.getByText('Starter Library — read-only')).toBeVisible()

  // Clone into an editable coach draft.
  await page.getByRole('button', { name: 'Use this program' }).click()
  await expect(page.getByRole('dialog', { name: 'Use this starter program?' })).toBeVisible()
  await page.getByRole('button', { name: 'Create my draft' }).click()

  // Landed in the program editor on the new draft, attributed to the starter library.
  await expect(page).toHaveURL(/\/coach\/programming\/programs\/[0-9a-f-]+$/)
  await expect(page.getByText('Based on Starter Library')).toBeVisible()

  // Make a small allowed edit (rename) and save the draft.
  const uniqueName = `E2E Clone ${Date.now()}`
  const nameField = page.getByLabel('Name')
  await nameField.fill(uniqueName)
  await page.getByRole('button', { name: 'Save draft' }).click()
  await expect(page.getByText('Draft saved')).toBeVisible()

  // Publish the coach copy.
  await page.getByRole('button', { name: 'Review and publish' }).click()
  await page.getByRole('button', { name: 'Confirm publication' }).click()
  await expect(page.getByText(/Published .* Exact workout versions remain pinned/)).toBeVisible()

  // Assign the published copy to a seeded trainee.
  await page.goto('/coach/assignments')
  await expect(page.getByRole('heading', { name: 'Program assignments' })).toBeVisible()
  await page.getByLabel('Trainee').selectOption({ label: 'Arjun Trainee' })
  await page.getByLabel('Published Program version').selectOption({ label: `${uniqueName} · v1 · 4 weeks` })
  await page.getByLabel('Effective start date').fill(futureDate())
  await page.getByRole('button', { name: 'Preview schedule' }).click()
  await expect(page.getByText('Schedule preview')).toBeVisible()
  await page.getByRole('button', { name: 'Review assignment' }).click()
  await expect(page.getByRole('dialog', { name: 'Confirm Program assignment' })).toBeVisible()
  await page.getByRole('button', { name: 'Confirm assignment' }).click()
  await expect(page.getByText('Assignment history')).toBeVisible()

  // The trainee now has scheduled workouts from the assigned copy.
  const context = await request.newContext()
  const login = await context.post(`${apiUrl}/auth/login`, { data: { email: 'trainee@fitness.example.com', password: 'DemoPass123!' } })
  const traineeAuth = await login.json()
  const workspace = await context.get(`${apiUrl}/trainee/program`, { headers: { Authorization: `Bearer ${traineeAuth.access_token}` } })
  expect(workspace.ok()).toBeTruthy()
  expect((await workspace.json()).scheduled_workouts.length).toBeGreaterThan(0)
  await context.dispose()
})

test('demo coach can browse the starter library but cannot clone', async ({ page }) => {
  await page.goto('/demo')
  await page.getByRole('button', { name: 'View as Coach' }).click()
  await page.goto('/coach/programming/library')
  await expect(page.getByRole('heading', { name: 'Starter Library' })).toBeVisible()
  const useButton = page.getByRole('button', { name: 'Use this program' }).first()
  if (await useButton.count()) await expect(useButton).toBeDisabled()

  // No horizontal overflow at the smallest supported width.
  await page.setViewportSize({ width: 320, height: 800 })
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Starter Library' })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
})
