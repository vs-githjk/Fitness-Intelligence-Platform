import { APIRequestContext, expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

// Iron Editorial C2.1/C2.2 behaviours: app-wide theming (role defaults + explicit
// preference persistence), the four-tab trainee IA with relocated destinations still
// reachable, and the approved trainee exercise-knowledge read authorization boundary.

type Auth = { access_token: string; user: unknown }

async function signIn(email: string, password = 'DemoPass123!'): Promise<Auth> {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/login`, { data: { email, password } })
  expect(res.ok()).toBeTruthy()
  const auth = await res.json()
  await ctx.dispose()
  return auth
}

async function apiFor(auth: Auth): Promise<APIRequestContext> {
  return request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${auth.access_token}` } })
}

async function setSession(page: Page, auth: Auth) {
  await page.addInitScript((session) => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

test('trainee defaults to dark; an explicit Light preference wins app-wide and persists', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  const api = await apiFor(auth)
  // Capture the shared seed trainee's preference so we can restore it afterwards.
  const original = (await (await api.get(`${apiUrl}/me/preferences`)).json()).theme ?? null

  await setSession(page, auth)
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/trainee/today')
  // No explicit preference → the trainee role default is dark (§8).
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

  // An explicit Light preference wins over the role default and applies app-wide.
  await page.goto('/settings')
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
  await page.getByRole('button', { name: 'Light', exact: true }).click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')

  // Persisted per user: a reload (local + server reconcile) keeps Light everywhere.
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  await page.goto('/trainee/today')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')

  // Restore the shared seed trainee's original preference for other specs.
  expect((await api.put(`${apiUrl}/me/preferences`, { data: { theme: original } })).ok()).toBeTruthy()
  await api.dispose()
})

test('coach defaults to light', async ({ page }) => {
  const auth = await signIn('coach@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/coach/dashboard')
  await expect(page.getByRole('heading', { name: 'Your coaching workspace' })).toBeVisible()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
})

test('four-tab trainee IA keeps relocated destinations reachable', async ({ page }) => {
  const auth = await signIn('trainee@fitness.example.com')
  await setSession(page, auth)
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/trainee/today')

  const nav = page.getByRole('navigation', { name: 'trainee navigation' }).first()
  for (const label of ['Today', 'Train', 'Progress', 'You']) {
    await expect(nav.getByRole('link', { name: label, exact: true })).toBeVisible()
  }

  // Train owns program + execution.
  await nav.getByRole('link', { name: 'Train', exact: true }).click()
  await expect(page).toHaveURL(/\/trainee\/program/)

  // Progress owns Daily + the relocated Workouts analytics (reachable via its sub-nav).
  await nav.getByRole('link', { name: 'Progress', exact: true }).click()
  await expect(page).toHaveURL(/\/trainee\/progress/)
  await page.getByRole('link', { name: 'Workouts', exact: true }).first().click()
  await expect(page).toHaveURL(/\/trainee\/workouts$/)

  // You owns Profile / Assessment / Settings (all relocated under one tab).
  await nav.getByRole('link', { name: 'You', exact: true }).click()
  await expect(page).toHaveURL(/\/profile/)
  await page.getByRole('link', { name: 'Settings', exact: true }).first().click()
  await expect(page).toHaveURL(/\/settings/)
  await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible()
})

test('trainee exercise-knowledge read is authorized, published-only, and 404s otherwise', async () => {
  // A demo trainee is read-only with a pre-seeded in-progress session (no mutation, no
  // seed pollution). Demo users may read (§30).
  const anon = await request.newContext()
  const demoRes = await anon.post(`${apiUrl}/auth/demo-session`, { data: { role: 'trainee' } })
  expect(demoRes.ok()).toBeTruthy()
  const demo = await demoRes.json() as Auth
  await anon.dispose()

  const api = await apiFor(demo)
  const workspace = await (await api.get(`${apiUrl}/trainee/program`)).json()
  const active = workspace.scheduled_workouts.find((w: { workout_session_id: string | null }) => w.workout_session_id)
  expect(active).toBeTruthy()
  const session = await (await api.get(`${apiUrl}/trainee/workout-sessions/${active.workout_session_id}`)).json()
  const versionId = session.exercises[0].exercise_version_id

  // Authorized read returns the published knowledge subset (no draft internals leak).
  const ok = await api.get(`${apiUrl}/trainee/exercise-versions/${versionId}`)
  expect(ok.status()).toBe(200)
  const body = await ok.json()
  expect(body.movement_pattern).toBeTruthy()
  expect(Array.isArray(body.primary_muscle_groups)).toBeTruthy()
  expect(body).not.toHaveProperty('content_hash')
  expect(body).not.toHaveProperty('owner_coach_id')

  // An unknown / unauthorized version id is indistinguishable (404).
  const unknown = await api.get(`${apiUrl}/trainee/exercise-versions/00000000-0000-0000-0000-000000000000`)
  expect(unknown.status()).toBe(404)
  await api.dispose()

  // A coach cannot use the trainee route.
  const coach = await signIn('coach@fitness.example.com')
  const coachApi = await apiFor(coach)
  const forbidden = await coachApi.get(`${apiUrl}/trainee/exercise-versions/${versionId}`)
  expect(forbidden.status()).toBe(403)
  await coachApi.dispose()
})
