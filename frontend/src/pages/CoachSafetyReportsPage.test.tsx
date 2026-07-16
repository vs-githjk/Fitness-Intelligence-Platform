import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../auth'
import { CoachWorkoutSafetyReport } from '../types'
import { CoachSafetyReportsPage } from './CoachSafetyReportsPage'

class MemoryStorage implements Storage { private values = new Map<string, string>(); get length() { return this.values.size } clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null } key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) } setItem(key: string, value: string) { this.values.set(key, value) } }

beforeEach(() => setSession(false))
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

it('lists assigned-trainee reports and filters with an identity-scoped query', async () => {
  const calls: string[] = []
  mockFetch(url => { calls.push(url); return ok([report()]) })
  renderRoute('/coach/safety-reports')
  expect(await screen.findByRole('heading', { name: 'Aarav Trainee' })).toBeVisible()
  expect(screen.getByText('Chest discomfort')).toBeVisible()
  fireEvent.change(screen.getByLabelText('Report status'), { target: { value: 'resolved' } })
  await waitFor(() => expect(calls.some(value => value.endsWith('/coach/safety-reports?status=resolved'))).toBe(true))
})

it('shows report detail and appends acknowledge and resolve review actions', async () => {
  let current = report()
  const actions: string[] = []
  mockFetch((url, init) => {
    if (init?.method === 'POST') {
      actions.push(url)
      const resolved = url.endsWith('/resolve')
      current = { ...current, status: resolved ? 'resolved' : 'acknowledged', reviews: [...current.reviews, { id: `review-${current.reviews.length}`, coach_id: 'coach-1', action: resolved ? 'resolved' : 'acknowledged', note: 'Followed up', created_at: '2026-07-16T09:00:00Z' }] }
    }
    return ok(current)
  })
  renderRoute('/coach/safety-reports/report-1')
  expect(await screen.findByText('Safety reports are not monitored continuously. The platform does not diagnose medical conditions. Use professional judgment and appropriate escalation.')).toBeVisible()
  fireEvent.change(screen.getByLabelText(/Internal coach note/), { target: { value: 'Followed up' } })
  fireEvent.click(screen.getByRole('button', { name: 'Acknowledge' }))
  expect(await screen.findByText('Report acknowledged.')).toBeVisible()
  expect(screen.getByText('Followed up')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Resolve report' }))
  expect(await screen.findByText('Report resolved.')).toBeVisible()
  expect(actions.some(value => value.endsWith('/acknowledge'))).toBe(true)
  expect(actions.some(value => value.endsWith('/resolve'))).toBe(true)
})

it('keeps coach review mutations disabled in demo mode', async () => {
  setSession(true)
  mockFetch(() => ok(report()))
  renderRoute('/coach/safety-reports/report-1')
  expect(await screen.findByRole('button', { name: 'Acknowledge' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Resolve report' })).toBeDisabled()
  expect(screen.getByLabelText(/Internal coach note/)).toBeDisabled()
})

function renderRoute(path: string) { const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } }); return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={[path]}><AuthProvider><Routes><Route path="/coach/safety-reports" element={<CoachSafetyReportsPage />} /><Route path="/coach/safety-reports/:reportId" element={<CoachSafetyReportsPage />} /></Routes></AuthProvider></MemoryRouter></QueryClientProvider>) }
function setSession(demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: 'coach-1', email: 'coach@example.com', first_name: 'Coach', last_name: 'User', role: 'coach', is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown) { return new Response(JSON.stringify(value), { status: 200, headers: { 'Content-Type': 'application/json' } }) }
function report(): CoachWorkoutSafetyReport { return { id: 'report-1', workout_session_id: 'session-1', workout_session_exercise_id: 'exercise-1', workout_set_log_id: null, trainee_id: 'trainee-1', category: 'chest_discomfort', severity: 'severe', note: 'Symptoms during the second set.', activity_stopped: true, occurred_at: '2026-07-16T08:12:00Z', created_at: '2026-07-16T08:12:00Z', status: 'open', session_status: 'safety_ended', exercise_status: 'safety_stopped', guidance: 'Stop exercising.', trainee_name: 'Aarav Trainee', trainee_email: 'aarav@example.com', workout_name: 'Full Body Strength', scheduled_date: '2026-07-16', exercise_name: 'Goblet Squat', reviews: [] } }
