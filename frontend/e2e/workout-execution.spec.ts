import { APIRequestContext, expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

type Auth = { access_token: string; user: unknown }
type Scheduled = { id: string; status: string; workout_session_id: string | null; workout_template_version: { name: string } }
type Workspace = { scheduled_workouts: Scheduled[] }

async function credentialSession(page: Page, email: string): Promise<Auth> {
  const context = await request.newContext()
  const response = await context.post(`${apiUrl}/auth/login`, { data: { email, password: 'DemoPass123!' } })
  expect(response.ok()).toBeTruthy()
  const auth = await response.json() as Auth
  await context.dispose()
  await page.addInitScript(session => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
  return auth
}

async function authenticatedApi(auth: Auth): Promise<APIRequestContext> {
  return request.newContext({ extraHTTPHeaders: { Authorization: `Bearer ${auth.access_token}` } })
}

async function workspace(api: APIRequestContext): Promise<Workspace> {
  const response = await api.get(`${apiUrl}/trainee/program`)
  expect(response.ok()).toBeTruthy()
  return response.json() as Promise<Workspace>
}

async function saveFirstVisibleSet(page: Page) {
  const repetitions = page.getByLabel('Actual repetitions').first()
  if (await repetitions.count()) await repetitions.fill('8')
  const load = page.getByLabel('External load').first()
  if (await load.count()) {
    await load.fill('20')
    await page.getByLabel('Load unit').first().selectOption('kg')
  }
  const duration = page.getByLabel('Duration (seconds)').first()
  if (await duration.count()) await duration.fill('45')
  const distance = page.getByLabel('Distance', { exact: true }).first()
  if (await distance.count()) {
    await distance.fill('1')
    await page.getByLabel('Distance unit').first().selectOption('kilometers')
  }
  await page.getByRole('button', { name: 'Save completed set' }).first().click()
  await expect(page.getByText('Saved', { exact: true }).first()).toBeVisible()
}

async function expectNoOverflow(page: Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
}

test('trainee starts, logs, resumes, completes, and ends another workout incomplete', async ({ page }) => {
  const auth = await credentialSession(page, 'trainee@fitness.example.com')
  const api = await authenticatedApi(auth)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/trainee/today')
  await expect(page.getByText('Training readiness', { exact: true })).toBeVisible()

  let data = await workspace(api)
  const scheduled = data.scheduled_workouts.find(item => item.status === 'scheduled' && item.workout_template_version.name === 'Full Body Strength')
    ?? data.scheduled_workouts.find(item => item.status === 'scheduled')
  expect(scheduled).toBeTruthy()
  await page.goto(`/trainee/workouts/${scheduled!.id}`)
  await page.getByRole('button', { name: 'Start workout' }).click()
  await expect(page.getByText(/Exercise 1 of \d+/)).toBeVisible()
  const progress = await page.getByText(/Exercise 1 of \d+/).textContent()
  const exerciseCount = Number(progress?.match(/of (\d+)/)?.[1])
  expect(exerciseCount).toBeGreaterThan(1)

  await saveFirstVisibleSet(page)
  const beforeAdded = await page.getByRole('button', { name: 'Skip set' }).count()
  await page.getByRole('button', { name: 'Add set' }).click()
  await expect(page.getByRole('button', { name: 'Skip set' })).toHaveCount(beforeAdded + 1)
  await page.getByRole('button', { name: 'Skip set' }).last().click()
  await expect(page.getByText(/sets resolved/)).toBeVisible()

  data = await workspace(api)
  const active = data.scheduled_workouts.find(item => item.id === scheduled!.id)
  expect(active?.status).toBe('in_progress')
  const repeated = await api.post(`${apiUrl}/trainee/workouts/${scheduled!.id}/start`)
  expect(repeated.ok()).toBeTruthy()
  expect((await repeated.json()).id).toBe(active?.workout_session_id)
  await page.reload()
  await expect(page.getByText(/Session revision/)).toBeVisible()
  await expectNoOverflow(page)

  await page.getByRole('button', { name: 'Skip exercise' }).click()
  for (let index = 2; index <= exerciseCount; index += 1) {
    await page.getByRole('button', { name: 'Next' }).click()
    await expect(page.getByText(`Exercise ${index} of ${exerciseCount}`)).toBeVisible()
    if (index === 2) await saveFirstVisibleSet(page)
    await page.getByRole('button', { name: 'Skip exercise' }).click()
  }
  await page.getByLabel('Actual duration (minutes)').fill('42')
  await page.getByLabel('Session RPE (0–10)').fill('7')
  await page.getByLabel('Trainee note').fill('Synthetic end-to-end completion.')
  await page.getByLabel('I confirm this workout is ready to complete.').check()
  await page.getByRole('button', { name: 'Complete workout' }).click()
  await expect(page.getByText('Workout completed')).toBeVisible()
  await expect(page.getByText('This execution is now immutable.')).toBeVisible()

  data = await workspace(api)
  const another = data.scheduled_workouts.find(item => item.status === 'scheduled' && item.id !== scheduled!.id)
  expect(another).toBeTruthy()
  await page.goto(`/trainee/workouts/${another!.id}`)
  await page.getByRole('button', { name: 'Start workout' }).click()
  await page.getByRole('button', { name: 'End workout incomplete' }).click()
  await expect(page.getByText('Workout ended incomplete')).toBeVisible()
  await api.dispose()
})

test('demo execution is read-only, role-protected, and mobile-safe', async ({ page }) => {
  await page.goto('/demo')
  await page.getByRole('button', { name: 'View as Trainee' }).click()
  const unauthenticated = await request.newContext()
  const demoResponse = await unauthenticated.post(`${apiUrl}/auth/demo-session`, { data: { role: 'trainee' } })
  expect(demoResponse.ok()).toBeTruthy()
  const demoAuth = await demoResponse.json() as Auth
  await unauthenticated.dispose()
  const api = await authenticatedApi(demoAuth)
  const data = await workspace(api)
  const active = data.scheduled_workouts.find(item => item.status === 'in_progress')
  expect(active).toBeTruthy()
  await page.goto(`/trainee/workouts/${active!.id}`)
  await expect(page.getByText('Demo workspace — changes are disabled.')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Add set' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'End workout incomplete' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Save completed set' }).first()).toBeDisabled()

  const scheduled = data.scheduled_workouts.find(item => item.status === 'scheduled')
  expect(scheduled).toBeTruthy()
  const denied = await api.post(`${apiUrl}/trainee/workouts/${scheduled!.id}/start`)
  expect(denied.status()).toBe(403)
  expect(await denied.json()).toMatchObject({ detail: { code: 'demo_read_only' } })
  await api.dispose()

  for (const width of [320, 390]) {
    await page.setViewportSize({ width, height: 844 })
    await page.reload()
    await expect(page.getByText('Demo workspace — changes are disabled.')).toBeVisible()
    await expectNoOverflow(page)
  }

  await page.getByRole('button', { name: 'Exit demo' }).first().click()
  await credentialSession(page, 'coach@fitness.example.com')
  await page.goto(`/trainee/workouts/${active!.id}`)
  await expect(page).toHaveURL(/\/coach\/dashboard$/)
})
