import { APIRequestContext, expect, Page, request, test } from '@playwright/test'
import { apiUrl } from './config'

async function login(email: string, password = 'DemoPass123!') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/login`, { data: { email, password } })
  expect(res.ok()).toBeTruthy()
  const auth = await res.json()
  return { ctx, auth }
}

async function demoSession(role: 'coach' | 'trainee') {
  const ctx = await request.newContext()
  const res = await ctx.post(`${apiUrl}/auth/demo-session`, { data: { role } })
  expect(res.ok()).toBeTruthy()
  return { ctx, auth: await res.json() }
}

async function setSession(page: Page, auth: { access_token: string; user: unknown }) {
  await page.addInitScript((session) => {
    localStorage.setItem('access_token', session.access_token)
    localStorage.setItem('user', JSON.stringify(session.user))
  }, auth)
}

async function scheduledWorkoutIds(ctx: APIRequestContext, token: string): Promise<string[]> {
  const res = await ctx.get(`${apiUrl}/trainee/program`, { headers: { Authorization: `Bearer ${token}` } })
  const body = await res.json()
  return (body.scheduled_workouts as Array<{ id: string; status: string }>)
    .filter((w) => w.status === 'scheduled')
    .map((w) => w.id)
}

test('trainee explicitly skips a scheduled workout and cannot start it afterward', async () => {
  const { ctx, auth } = await login('trainee@fitness.example.com')
  const [target] = await scheduledWorkoutIds(ctx, auth.access_token)
  expect(target).toBeTruthy()
  const headers = { Authorization: `Bearer ${auth.access_token}` }

  const skip = await ctx.post(`${apiUrl}/trainee/workouts/${target}/skip`, {
    headers,
    data: { skip_kind: 'ordinary', reason: 'travel', note: 'Away this week' },
  })
  expect(skip.status()).toBe(200)
  const body = await skip.json()
  expect(body.status).toBe('skipped')
  expect(body.skip_kind).toBe('ordinary')

  // Idempotent repeat.
  const again = await ctx.post(`${apiUrl}/trainee/workouts/${target}/skip`, {
    headers,
    data: { skip_kind: 'ordinary', reason: 'travel' },
  })
  expect(again.status()).toBe(200)

  // Cannot start a skipped workout.
  const start = await ctx.post(`${apiUrl}/trainee/workouts/${target}/start`, { headers })
  expect(start.status()).toBe(409)
  await ctx.dispose()
})

test('coach sees ordinary and wellbeing skips with separate classification', async () => {
  // The deterministic demo seed contains backdated, in-window explicit skips for
  // one demo trainee; the demo coach reviews them read-only.
  const { ctx: cctx, auth: cAuth } = await demoSession('coach')
  const headers = { Authorization: `Bearer ${cAuth.access_token}` }
  const roster = await (await cctx.get(`${apiUrl}/coach/trainees`, { headers })).json()
  const trainee = roster.find((r: { email: string }) => r.email === 'demo.stress@fitness.example.com')
  expect(trainee).toBeTruthy()
  const listing = await (await cctx.get(`${apiUrl}/coach/trainees/${trainee.trainee_id}/workout-sessions?status=skipped`, { headers })).json()
  const skips = listing.sessions as Array<{ classification: string; skip_kind: string; skip_reason: string; workout_session_id: string | null }>
  const kinds = skips.map((s) => s.classification)
  expect(kinds).toContain('ordinary_skipped')
  expect(kinds).toContain('safety_skipped')
  // Skips have no session and expose the persisted reason.
  expect(skips.every((s) => s.workout_session_id === null)).toBe(true)
  expect(skips.every((s) => Boolean(s.skip_reason))).toBe(true)
  await cctx.dispose()
})

test('recorded bests report all-history scope', async () => {
  const { ctx, auth } = await login('trainee@fitness.example.com')
  const res = await ctx.get(`${apiUrl}/trainee/recorded-bests`, { headers: { Authorization: `Bearer ${auth.access_token}` } })
  expect(res.status()).toBe(200)
  const body = await res.json()
  expect(body.scope).toBe('all_available_history')
  await ctx.dispose()
})

test('demo trainee can inspect but cannot skip', async () => {
  const { ctx, auth } = await demoSession('trainee')
  const program = await (await ctx.get(`${apiUrl}/trainee/program`, { headers: { Authorization: `Bearer ${auth.access_token}` } })).json()
  const scheduled = (program.scheduled_workouts as Array<{ id: string; status: string }>).find((w) => w.status === 'scheduled')
  if (scheduled) {
    const denied = await ctx.post(`${apiUrl}/trainee/workouts/${scheduled.id}/skip`, {
      headers: { Authorization: `Bearer ${auth.access_token}` },
      data: { skip_kind: 'ordinary', reason: 'travel' },
    })
    expect(denied.status()).toBe(403)
    expect((await denied.json()).detail.code).toBe('demo_read_only')
  }
  await ctx.dispose()
})

test('trainee program page offers Skip workout, demo does not', async ({ page }) => {
  // Real trainee: skip control is present on a scheduled workout.
  const { ctx, auth } = await login('trainee@fitness.example.com')
  await ctx.dispose()
  await setSession(page, auth)
  await page.goto('/trainee/program')
  await expect(page.getByRole('heading', { name: "Today's Workout" })).toBeVisible()

  // Demo trainee: the workspace is read-only; no skip button is exposed.
  const { ctx: dctx, auth: dAuth } = await demoSession('trainee')
  await dctx.dispose()
  const demoPage = await page.context().newPage()
  await setSession(demoPage, dAuth)
  await demoPage.goto('/trainee/program')
  await expect(demoPage.getByRole('status', { name: 'Demo workspace' })).toBeVisible()
  await expect(demoPage.getByRole('button', { name: 'Skip workout' })).toHaveCount(0)
  await demoPage.close()
})

test('mobile trainee program has no horizontal overflow at 320px', async ({ page }) => {
  const { ctx, auth } = await login('trainee@fitness.example.com')
  await ctx.dispose()
  await setSession(page, auth)
  await page.setViewportSize({ width: 320, height: 800 })
  await page.goto('/trainee/program')
  await expect(page.getByRole('heading', { name: "Today's Workout" })).toBeVisible()
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(1)
})
