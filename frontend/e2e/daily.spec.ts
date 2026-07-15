import { expect, Page, request, test } from '@playwright/test'
import path from 'node:path'
import { apiUrl } from './config'
import { createTraineeInvite } from './registration-helpers'

const screenshots = path.resolve('../docs/screenshots')

async function signIn(email: string, password = 'DemoPass123!') {
  const context = await request.newContext()
  const response = await context.post(`${apiUrl}/auth/login`, { data: { email, password } })
  expect(response.ok()).toBeTruthy()
  const auth = await response.json()
  await context.dispose()
  return auth
}

async function setSession(page: Page, auth: { access_token: string; user: unknown }) {
  await page.addInitScript((session) => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
}

test('trainee can edit today, view scores, and inspect real trends', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/trainee/check-in')
  await expect(page.getByRole('heading', { name: /today’s check-in|how are you doing today/i })).toBeVisible()
  await page.getByLabel('Sleep duration').fill('7.8')
  await page.getByLabel('Steps').fill('9200')
  const submit = page.getByRole('button', { name: /check-in$/i })
  await submit.click()
  await expect(page.getByText(/check-in was (updated|submitted)/i)).toBeVisible()
  await page.goto('/trainee/today')
  await expect(page.getByText('Training readiness', { exact: true })).toBeVisible()
  await expect(page.getByText(/coaching guidance/i).first()).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/daily-today-mobile.png`, fullPage: true })
  await page.goto('/trainee/progress')
  await expect(page.getByRole('heading', { name: 'Longitudinal fitness intelligence' })).toBeVisible()
  await expect(page.getByText(/missing local dates remain gaps/i)).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/daily-progress-mobile.png`, fullPage: true })
})

test('conditional exercise validation preserves form input after API failure', async ({ page }) => {
  const context = await request.newContext()
  const email = `daily-form-${Date.now()}@example.com`
  const inviteCode = await createTraineeInvite(email)
  const registered = await context.post(`${apiUrl}/auth/register/trainee`, { data: { email, password: 'VisualPass123!', first_name: 'Form', last_name: 'Tester', invite_code: inviteCode } })
  expect(registered.ok()).toBeTruthy()
  const auth = await registered.json()
  await context.dispose()
  await setSession(page, auth)
  await page.goto('/trainee/check-in')
  await page.getByRole('button', { name: 'Yes' }).last().click()
  await page.getByRole('button', { name: 'Submit today’s check-in' }).click()
  await expect(page.getByText('Enter the exercise duration')).toBeVisible()
  await page.getByLabel('Exercise duration').fill('30')
  await page.getByLabel('Session RPE').fill('6')
  await page.getByLabel('Steps').fill('4321')
  await page.route('**/api/v1/check-ins/today', route => route.abort())
  await page.getByRole('button', { name: 'Submit today’s check-in' }).click()
  await expect(page.getByText(/entries remain on this page/i)).toBeVisible()
  await expect(page.getByLabel('Steps')).toHaveValue('4321')
})

test('coach sees latest readiness, longitudinal alerts, and trends', async ({ page }) => {
  const auth = await signIn('coach@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/coach/dashboard')
  await expect(page.getByRole('heading', { name: 'Today across your roster' })).toBeVisible()
  await expect(page.getByText('Low readiness', { exact: true })).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/daily-coach-dashboard-desktop.png`, fullPage: true })
  const api = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${auth.access_token}` } })
  const roster = await (await api.get(`${apiUrl}/coach/trainees`)).json()
  const trainee = roster.find((item: { latest_readiness_score: number | null }) => item.latest_readiness_score !== null)
  await api.dispose()
  expect(trainee).toBeTruthy()
  await page.goto(`/coach/trainees/${trainee.trainee_id}`)
  await expect(page.getByRole('heading', { name: 'Daily recovery and readiness' })).toBeVisible()
  await expect(page.getByText('Latest check-in', { exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Latest recommended actions' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Onboarding Health Index reference' })).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/daily-coach-trainee-desktop.png`, fullPage: true })
})

test('wrong roles and unassigned coach remain blocked', async ({ page }) => {
  const trainee = await signIn('trainee@fitness.example.com')
  await setSession(page, trainee)
  await page.goto('/coach/dashboard')
  await expect(page).toHaveURL(/\/trainee\/today/)
  const context = await request.newContext()
  const other = await context.post(`${apiUrl}/auth/login`, { data: { email: 'other@example.com', password: 'OtherPass123!' } })
  if (!other.ok()) { await context.dispose(); return }
  const otherAuth = await other.json()
  const assigned = await signIn('coach@fitness.example.com')
  const assignedContext = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${assigned.access_token}` } })
  const roster = await (await assignedContext.get(`${apiUrl}/coach/trainees`)).json()
  await assignedContext.dispose()
  const unauthorized = await context.get(`${apiUrl}/coach/trainees/${roster[0].trainee_id}/trends?days=7`, { headers: { Authorization: `Bearer ${otherAuth.access_token}` } })
  expect(unauthorized.status()).toBe(403)
  await context.dispose()
})
