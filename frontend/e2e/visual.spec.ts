import { expect, Page, request, test } from '@playwright/test'
import path from 'node:path'

const apiUrl = 'http://localhost:8000/api/v1'
const screenshots = path.resolve('../docs/screenshots')
const baseline = {
  age: 30, height_cm: 175, weight_kg: 75, selected_goal: 'general_health', target_weight_kg: 72,
  hydration_ml: 2400, sleep_hours: 7.5, sleep_quality: 4, wake_refreshed: true,
  daily_steps: 8500, activity_types: ['walking', 'strength_training'], activity_minutes_weekly: 180,
  workout_frequency_weekly: 3, average_rpe: 7, workout_duration_minutes: 50, perceived_recovery: 4,
  stress_level: 4, resting_heart_rate: 65, palpitations: false, shortness_of_breath: false, chest_pain: false,
  calorie_mode: 'maintenance', calorie_target: 2200, calorie_intake: 2100, protein_target_g: 110,
  protein_intake_g: 100, carbohydrate_intake_g: 250, healthy_fat_intake_g: 70, fruit_servings: 2,
  vegetable_servings: 3, fiber_g: 30, meal_consistency: 4,
}

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
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
  expect(overflow).toBeLessThanOrEqual(1)
}

test.beforeAll(async () => {
  const auth = await signIn('trainee@fitness.example.com')
  const context = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${auth.access_token}` } })
  const current = await context.get(`${apiUrl}/health-index/current`)
  if (current.status() === 404) {
    expect((await context.put(`${apiUrl}/assessments/onboarding`, { data: { responses: baseline } })).ok()).toBeTruthy()
    expect((await context.post(`${apiUrl}/assessments/onboarding/submit`)).ok()).toBeTruthy()
  }
  await context.dispose()

  const setup = await request.newContext()
  let riskAuthResponse = await setup.post(`${apiUrl}/auth/register`, { data: { email: 'risk-visual@example.com', password: 'VisualPass123!', first_name: 'Riley', last_name: 'Risk Review', invite_code: 'FIT-DEMO-2026' } })
  if (riskAuthResponse.status() === 409) riskAuthResponse = await setup.post(`${apiUrl}/auth/login`, { data: { email: 'risk-visual@example.com', password: 'VisualPass123!' } })
  expect(riskAuthResponse.ok()).toBeTruthy()
  const riskAuth = await riskAuthResponse.json()
  const riskContext = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${riskAuth.access_token}` } })
  if ((await riskContext.get(`${apiUrl}/health-index/current`)).status() === 404) {
    const riskData = { ...baseline, hydration_ml: 500, sleep_hours: 4, stress_level: 9, resting_heart_rate: 100, palpitations: true, shortness_of_breath: true, chest_pain: true, calorie_intake: 800, protein_intake_g: 30 }
    expect((await riskContext.put(`${apiUrl}/assessments/onboarding`, { data: { responses: riskData } })).ok()).toBeTruthy()
    expect((await riskContext.post(`${apiUrl}/assessments/onboarding/submit`)).ok()).toBeTruthy()
  }
  await riskContext.dispose()
  await setup.dispose()
})

test('public authentication layouts are responsive', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await page.getByLabel('Email address').focus()
  await page.keyboard.press('Tab')
  await expect(page.locator('input[name="password"]')).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button', { name: 'Show password' })).toBeFocused()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/login-desktop.png`, fullPage: true })

  await page.setViewportSize({ width: 375, height: 812 })
  await page.reload()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/login-mobile.png`, fullPage: true })
})

test('onboarding renders at desktop and mobile widths', async ({ page }) => {
  const context = await request.newContext()
  const registered = await context.post(`${apiUrl}/auth/register`, { data: { email: `visual-${Date.now()}@example.com`, password: 'VisualPass123!', first_name: 'Visual', last_name: 'Trainee', invite_code: 'FIT-DEMO-2026' } })
  expect(registered.ok()).toBeTruthy()
  const auth = await registered.json()
  await context.dispose()
  await setSession(page, auth)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/onboarding')
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/onboarding-desktop.png`, fullPage: true })
  await page.setViewportSize({ width: 375, height: 812 })
  await page.reload()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/onboarding-mobile.png`, fullPage: true })
  await page.getByRole('button', { name: 'Save and continue' }).click()
  await page.getByRole('button', { name: 'General health' }).click()
  await page.getByRole('button', { name: 'Save and continue' }).click()
  await expect(page.getByRole('heading', { name: 'Build your basic profile' })).toBeVisible()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Build your basic profile' })).toBeVisible()
  await page.goto('/trainee/dashboard')
  await expect(page.getByRole('heading', { name: 'No check-in yet today' })).toBeVisible()
})

test('trainee dashboard is responsive and contains real baseline', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/trainee/dashboard')
  await expect(page.getByText('Training readiness', { exact: true })).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/trainee-dashboard-mobile.png`, fullPage: true })
  await page.setViewportSize({ width: 1024, height: 900 })
  await page.reload()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/baseline-result.png`, fullPage: true })
})

test('coach overview and trainee detail transform across widths', async ({ page }) => {
  const auth = await signIn('coach@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/coach/dashboard')
  await expect(page.getByRole('heading', { name: 'Your coaching workspace' })).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/coach-dashboard-desktop.png`, fullPage: true })

  const context = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${auth.access_token}` } })
  const roster = await (await context.get(`${apiUrl}/coach/trainees`)).json()
  const scored = roster.find((trainee: { current_score: number | null }) => trainee.current_score !== null)
  await context.dispose()
  expect(scored).toBeTruthy()
  await page.goto(`/coach/trainees/${scored.trainee_id}`)
  await expect(page.getByText('Score contributors')).toBeVisible()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/trainee-detail-desktop.png`, fullPage: true })

  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/coach/dashboard')
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/coach-dashboard-mobile.png`, fullPage: true })

  await page.setViewportSize({ width: 768, height: 1024 })
  await page.reload()
  await expectNoOverflow(page)
  await page.screenshot({ path: `${screenshots}/coach-dashboard-tablet.png`, fullPage: true })
})

test('auth and empty-state boundaries remain actionable', async ({ page }) => {
  const traineeAuth = await signIn('trainee@fitness.example.com')
  await setSession(page, traineeAuth)
  await page.goto('/coach/dashboard')
  await expect(page).toHaveURL(/\/trainee\/today/)

  await page.addInitScript((user) => {
    localStorage.setItem('access_token', 'expired-token')
    localStorage.setItem('user', JSON.stringify(user))
  }, traineeAuth.user)
  await page.goto('/trainee/dashboard')
  await expect(page.getByText('Your session expired. Sign in again to continue.')).toBeVisible()

  const coachAuth = await signIn('coach@fitness.example.com')
  await setSession(page, coachAuth)
  await page.route('**/api/v1/coach/trainees', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.route('**/api/v1/coach/risk-alerts', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.goto('/coach/dashboard')
  await expect(page.getByRole('heading', { name: 'No assigned trainees' })).toBeVisible()
})

test('API outage shows retained-data guidance and retry', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  await setSession(page, auth)
  await page.route('**/api/v1/check-ins/today', route => route.abort())
  await page.goto('/trainee/today')
  await expect(page.getByRole('heading', { name: 'We could not load this page' })).toBeVisible()
  await expect(page.getByText(/entries remain on this page/i)).toBeVisible()
  await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible()
})
