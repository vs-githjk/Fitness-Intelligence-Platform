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

// The seeded coach has published Programs, so the empty state is exercised by stubbing
// the Programs list to empty. This keeps the P2 usability behavior deterministic
// without altering shared seed data. Assignment business rules are untouched.
async function stubEmptyPrograms(page: Page, total: number) {
  await page.route('**/api/v1/coach/training-programs?**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], page: 1, per_page: 100, total }),
    }),
  )
}

test('assignments explains the empty published-Program state and links to Programming', async ({ page }) => {
  await stubEmptyPrograms(page, 0)
  await credentialSession(page, 'coach@fitness.example.com')
  await page.goto('/coach/assignments')
  await expect(page.getByRole('heading', { name: 'Program assignments' })).toBeVisible()

  await expect(page.getByText('No programs yet.')).toBeVisible()
  await expect(page.getByText('Exercise → Workout Template → Program → Assignment')).toBeVisible()
  const link = page.getByRole('link', { name: 'Go to Programming → Programs' })
  await expect(link).toHaveAttribute('href', '/coach/programming/programs')
  // The empty state must not be mistaken for a working selector.
  await expect(page.getByRole('button', { name: 'Preview schedule' })).toBeDisabled()
  // The trainee selector and start date remain available.
  await expect(page.getByLabel('Trainee')).toBeVisible()
  await expect(page.getByLabel('Effective start date')).toBeVisible()

  // No horizontal overflow at the smallest supported width.
  await page.setViewportSize({ width: 320, height: 800 })
  await page.reload()
  await expect(page.getByText('No programs yet.')).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
})

test('assignments distinguishes unpublished Programs from none at all', async ({ page }) => {
  await stubEmptyPrograms(page, 3)
  await credentialSession(page, 'coach@fitness.example.com')
  await page.goto('/coach/assignments')
  await expect(page.getByText('No published programs available.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Preview schedule' })).toBeDisabled()
})
