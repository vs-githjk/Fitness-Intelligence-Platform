import { expect, Page, request, test } from '@playwright/test'
import { mkdirSync } from 'node:fs'
import path from 'node:path'
import { apiUrl } from './config'
import { createTraineeInvite } from './registration-helpers'

const screenshots = path.resolve('../docs/screenshots/manual')

mkdirSync(screenshots, { recursive: true })

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

async function continueOnboarding(page: Page) {
  await page.getByRole('button', { name: 'Save and continue' }).click()
}

test('capture public access and complete trainee onboarding', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/login')
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/login-desktop.png`, fullPage: true })

  const email = `manual-guide-${Date.now()}@example.com`
  const inviteCode = await createTraineeInvite(email)
  await page.goto('/register')
  await expect(page.getByRole('heading', { name: 'Create your account' })).toBeVisible()
  await page.getByRole('button', { name: /^Trainee/ }).click()
  await page.screenshot({ path: `${screenshots}/registration-desktop.png`, fullPage: true })

  await page.getByLabel('First name').fill('Manual')
  await page.getByLabel('Last name').fill('Guide')
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Create a password').fill('ManualGuide123!')
  await page.getByLabel('Coach invitation code').fill(inviteCode)
  await page.getByRole('button', { name: 'Create trainee account' }).click()
  await expect(page).toHaveURL(/\/onboarding/)

  await continueOnboarding(page)
  await expect(page.getByRole('heading', { name: 'Choose your fitness goal' })).toBeVisible()
  await page.setViewportSize({ width: 375, height: 812 })
  await page.screenshot({ path: `${screenshots}/trainee-onboarding-goal-mobile.png`, fullPage: true })
  await page.getByRole('button', { name: /General health/ }).click()
  await continueOnboarding(page)

  await page.getByLabel('Age').fill('31')
  await page.getByLabel('Height').fill('176')
  await page.getByLabel('Current weight').fill('75')
  await page.getByLabel('Target weight').fill('72')
  await continueOnboarding(page)

  await page.getByLabel('Typical daily water intake').fill('2500')
  await continueOnboarding(page)

  await page.getByLabel('Average sleep duration').fill('7.5')
  await page.getByLabel('Sleep quality').fill('4')
  await page.getByRole('button', { name: 'Yes' }).click()
  await continueOnboarding(page)

  await page.getByLabel('Typical daily steps').fill('8500')
  await page.getByLabel('Activity each week').fill('180')
  await page.getByRole('button', { name: 'Walking' }).click()
  await page.getByRole('button', { name: 'Strength Training' }).click()
  await continueOnboarding(page)

  await page.getByLabel('Workouts each week').fill('3')
  await page.getByLabel('Average effort').fill('7')
  await page.getByLabel('Typical workout duration').fill('50')
  await page.getByLabel('Perceived recovery').fill('4')
  await continueOnboarding(page)

  await page.getByLabel('Current stress level').fill('4')
  await continueOnboarding(page)

  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.getByLabel('Resting heart rate').fill('64')
  await page.screenshot({ path: `${screenshots}/trainee-onboarding-cardio-desktop.png`, fullPage: true })
  await continueOnboarding(page)

  await page.getByRole('button', { name: 'Maintenance' }).click()
  await page.getByLabel('Entered calorie target').fill('2200')
  await page.getByLabel('Estimated intake').fill('2150')
  await page.getByLabel('Protein target').fill('110')
  await page.getByLabel('Protein intake').fill('105')
  await page.getByLabel('Fruit').fill('2')
  await page.getByLabel('Vegetables').fill('3')
  await page.getByLabel('Fiber').fill('30')
  await page.getByLabel('Meal consistency').fill('4')
  await continueOnboarding(page)

  await expect(page.getByRole('heading', { name: 'Review your assessment' })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/trainee-onboarding-review-desktop.png`, fullPage: true })
  await page.getByText('I confirm these answers are accurate').click()
  await page.getByRole('button', { name: 'Calculate my baseline' }).click()
  await expect(page).toHaveURL(/\/trainee\/dashboard/)
  await expect(page.getByText(/Health Index/)).toBeVisible()
  await page.screenshot({ path: `${screenshots}/trainee-baseline-reference-desktop.png`, fullPage: true })
})

test('capture implemented trainee and coach daily workflows', async ({ page }) => {
  const trainee = await signIn('trainee@fitness.example.com')
  await setSession(page, trainee)

  await page.setViewportSize({ width: 375, height: 812 })
  await page.goto('/trainee/check-in')
  await expect(page.getByRole('heading', { name: /today’s check-in|how are you doing today/i })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/trainee-daily-check-in-mobile.png`, fullPage: true })

  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/trainee/today')
  await expect(page.getByText('Training readiness', { exact: true })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/trainee-today-desktop.png`, fullPage: true })
  await page.goto('/trainee/progress')
  await expect(page.getByRole('heading', { name: 'Longitudinal fitness intelligence' })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/trainee-progress-desktop.png`, fullPage: true })

  const coach = await signIn('coach@fitness.example.com')
  await page.evaluate(() => localStorage.clear())
  await setSession(page, coach)
  const context = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${coach.access_token}` } })
  const fullRoster = await (await context.get(`${apiUrl}/coach/trainees`)).json()
  const seededRoster = fullRoster.filter((item: { email: string }) =>
    ['trainee@fitness.example.com', 'no-checkins@fitness.example.com'].includes(item.email),
  )
  const arjun = seededRoster.find((item: { email: string }) => item.email === 'trainee@fitness.example.com')
  await context.dispose()
  expect(arjun).toBeTruthy()
  await page.route('**/api/v1/coach/trainees', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify(seededRoster),
  }))
  await page.goto('/coach/dashboard')
  await expect(page.getByRole('heading', { name: 'Your coaching workspace' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Today across your roster' })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/coach-dashboard-desktop.png`, fullPage: true })

  await page.setViewportSize({ width: 375, height: 812 })
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Trainees and latest state' })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/coach-roster-mobile.png`, fullPage: true })

  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto(`/coach/trainees/${arjun.trainee_id}`)
  await expect(page.getByRole('heading', { name: 'Daily recovery and readiness' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Onboarding Health Index reference' })).toBeVisible()
  await page.screenshot({ path: `${screenshots}/coach-trainee-detail-desktop.png`, fullPage: true })
})

test('capture an expired-session boundary', async ({ page }) => {
  const trainee = await signIn('trainee@fitness.example.com')
  await page.addInitScript((user) => {
    localStorage.setItem('access_token', 'expired-documentation-token')
    localStorage.setItem('user', JSON.stringify(user))
  }, trainee.user)
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.goto('/trainee/today')
  await expect(page.getByText('Your session expired. Sign in again to continue.')).toBeVisible()
  await page.screenshot({ path: `${screenshots}/session-expired-desktop.png`, fullPage: true })
})
