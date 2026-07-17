import { expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

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

test('trainee views workout progress with load, adherence and recorded bests', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  await setSession(page, auth)
  await page.goto('/trainee/workouts')
  await expect(page.getByRole('heading', { name: 'Workout progress' })).toBeVisible()
  await expect(page.getByText(/Training load summarizes workout duration and reported effort/i)).toBeVisible()
  await expect(page.getByText('Completion adherence')).toBeVisible()
  await expect(page.getByText('Prescribed-set adherence')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Weekly planned vs completed load' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Recorded bests' })).toBeVisible()
  // Neutral terminology only.
  await expect(page.getByText(/personal record/i)).toHaveCount(0)
})

test('trainee sees an explicit missing-data state, never a fake zero', async ({ page }) => {
  const auth = await signIn('no-checkins@fitness.example.com')
  await setSession(page, auth)
  await page.goto('/trainee/workouts')
  await expect(page.getByRole('heading', { name: 'Workout progress' })).toBeVisible()
  // With no completed resistance work the volume trend and recorded bests show explicit empty copy.
  await expect(page.getByText(/No resistance-training volume recorded|No recorded bests yet/i).first()).toBeVisible()
})

test('coach reviews a trainee workout session with load and recorded bests', async ({ page }) => {
  const auth = await signIn('coach@fitness.example.com')
  await setSession(page, auth)
  await page.goto('/coach/dashboard')
  await page.getByRole('link', { name: /Review/i }).first().click()
  await expect(page).toHaveURL(/\/coach\/trainees\//)
  await expect(page.getByRole('heading', { name: 'Training load & adherence' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Recent workout sessions' })).toBeVisible()
  // Expand the first session to see read-only review details.
  const sessionToggle = page.getByRole('button', { expanded: false }).filter({ hasText: /Completed|Partial|Skipped|Safety/ }).first()
  await sessionToggle.click()
  await expect(page.getByText(/read-only/i).first()).toBeVisible()
})

async function demoSession(role: 'coach' | 'trainee') {
  const context = await request.newContext()
  const response = await context.post(`${apiUrl}/auth/demo-session`, { data: { role } })
  expect(response.ok()).toBeTruthy()
  const auth = await response.json()
  await context.dispose()
  return auth
}

test('demo trainee and coach can inspect workout analytics read-only', async ({ page }) => {
  const trainee = await demoSession('trainee')
  await setSession(page, trainee)
  await page.goto('/trainee/workouts')
  await expect(page.getByRole('heading', { name: 'Workout progress' })).toBeVisible()
  await expect(page.getByRole('status', { name: 'Demo workspace' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Recorded bests' })).toBeVisible()
})

test('demo coach can inspect a trainee workout intelligence read-only', async ({ page }) => {
  const coach = await demoSession('coach')
  await setSession(page, coach)
  await page.goto('/coach/dashboard')
  await page.getByRole('link', { name: /Review/i }).first().click()
  await expect(page.getByRole('heading', { name: 'Training load & adherence' })).toBeVisible()
  await expect(page.getByRole('status', { name: 'Demo workspace' })).toBeVisible()
})

test('mobile trainee analytics has no horizontal overflow at 320px', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/trainee/workouts')
  await expect(page.getByRole('heading', { name: 'Workout progress' })).toBeVisible()
  await expectNoOverflow(page)
})

test('cross-coach workout session discovery is denied', async () => {
  // Coach reads their own trainee's session id, then a foreign coach is denied.
  const coach = await signIn('coach@fitness.example.com')
  const ctx = await request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${coach.access_token}` } })
  const trainees = await (await ctx.get(`${apiUrl}/coach/trainees`)).json() as Array<{ trainee_id: string }>
  const sessions = await (await ctx.get(`${apiUrl}/coach/trainees/${trainees[0].trainee_id}/workout-sessions`)).json() as { sessions: Array<{ workout_session_id: string }> }
  await ctx.dispose()
  const sessionId = sessions.sessions[0]?.workout_session_id
  expect(sessionId).toBeTruthy()

  // A demo coach (different identity, not assigned) must get 404.
  const demoCtx = await request.newContext()
  const demoAuth = await (await demoCtx.post(`${apiUrl}/auth/demo-session`, { data: { role: 'coach' } })).json()
  const denied = await demoCtx.get(`${apiUrl}/coach/workout-sessions/${sessionId}`, { headers: { Authorization: `Bearer ${demoAuth.access_token}` } })
  expect(denied.status()).toBe(404)
  await demoCtx.dispose()
})
