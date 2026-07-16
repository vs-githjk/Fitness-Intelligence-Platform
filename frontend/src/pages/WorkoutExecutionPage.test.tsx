import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../auth'
import { TrainingAssignmentWorkspace, WorkoutSession } from '../types'
import { WorkoutExecutionPage } from './WorkoutExecutionPage'

class MemoryStorage implements Storage { private values = new Map<string, string>(); get length() { return this.values.size } clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null } key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) } setItem(key: string, value: string) { this.values.set(key, value) } }

beforeEach(() => setSession(false))
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

it('renders the scheduled state and starts an immutable execution', async () => {
  mockFetch((url, init) => url.endsWith('/trainee/program') ? ok(workspace()) : url.endsWith('/start') && init?.method === 'POST' ? ok(activeSession()) : ok(activeSession()))
  renderPage()
  expect(await screen.findByRole('heading', { name: 'Full Body Strength' })).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Start workout' }))
  expect(await screen.findByText('1 of 2 sets resolved')).toBeVisible()
  expect(screen.getAllByLabelText('Actual repetitions')).toHaveLength(2)
  expect(screen.getAllByLabelText('External load')).toHaveLength(2)
  expect(screen.getAllByLabelText('Load unit')).toHaveLength(2)
})

it('saves a set explicitly, adds a set, and keeps touch actions visible', async () => {
  const current = activeSession(); current.scheduled_workout_status = 'in_progress'
  const calls: string[] = []
  mockFetch((url, init) => { calls.push(`${init?.method ?? 'GET'} ${url}`); if (url.endsWith('/trainee/program')) return ok(workspace('in_progress', current.id)); if (url.includes('/workout-sessions/')) return ok(current); return ok(current) })
  renderPage()
  const repetitions = (await screen.findAllByLabelText('Actual repetitions'))[1]
  fireEvent.change(repetitions, { target: { value: '10' } })
  fireEvent.change(screen.getAllByLabelText('External load')[1], { target: { value: '20' } })
  fireEvent.change(screen.getAllByLabelText('Load unit')[1], { target: { value: 'kg' } })
  expect(screen.getByText('Unsaved changes')).toBeVisible()
  fireEvent.click(screen.getAllByRole('button', { name: 'Save completed set' })[1])
  await waitFor(() => expect(calls.some(value => value.startsWith('PUT'))).toBe(true))
  fireEvent.click(screen.getByRole('button', { name: 'Add set' }))
  await waitFor(() => expect(calls.some(value => value.startsWith('POST') && value.endsWith('/sets'))).toBe(true))
  expect(screen.getByRole('button', { name: 'Skip exercise' })).toBeVisible()
  expect(screen.getByRole('button', { name: 'End workout incomplete' })).toBeVisible()
})

it('preserves unsaved values and offers reload after a revision conflict', async () => {
  const current = activeSession()
  mockFetch((url, init) => { if (url.endsWith('/trainee/program')) return ok(workspace('in_progress', current.id)); if (init?.method === 'PUT') return error(409, { detail: { code: 'session_revision_conflict', message: 'Updated elsewhere', current_revision: 3 } }); return ok(current) })
  renderPage()
  const repetitions = (await screen.findAllByLabelText('Actual repetitions'))[1]
  fireEvent.change(repetitions, { target: { value: '12' } })
  fireEvent.change(screen.getAllByLabelText('External load')[1], { target: { value: '25' } })
  fireEvent.change(screen.getAllByLabelText('Load unit')[1], { target: { value: 'kg' } })
  fireEvent.click(screen.getAllByRole('button', { name: 'Save completed set' })[1])
  expect(await screen.findByText('Workout updated elsewhere')).toBeVisible()
  expect(repetitions).toHaveValue(12)
  expect(screen.getByRole('button', { name: 'Reload latest session' })).toBeVisible()
})

it('shows an immutable completion summary', async () => {
  setSession(true); const current = activeSession(); current.status = 'completed'; current.scheduled_workout_status = 'completed'; current.actual_duration_minutes = 40; current.session_rpe = '7.0'
  mockFetch(url => url.endsWith('/trainee/program') ? ok(workspace('completed', current.id)) : ok(current))
  renderPage()
  expect(await screen.findByText('Workout completed')).toBeVisible()
  expect(screen.getByText('This execution is now immutable.')).toBeVisible()
})

it('disables every demo workout mutation control', async () => {
  setSession(true); const current = activeSession()
  mockFetch(url => url.endsWith('/trainee/program') ? ok(workspace('in_progress', current.id)) : ok(current))
  renderPage()
  expect(await screen.findByText('Demo workspace — changes are disabled.')).toBeVisible()
  await screen.findAllByRole('button', { name: 'Save completed set' })
  for (const name of ['Save completed set', 'Skip set']) {
    screen.getAllByRole('button', { name }).forEach(button => expect(button).toBeDisabled())
  }
  for (const name of ['Add set', 'Skip exercise', 'Complete workout', 'End workout incomplete']) {
    expect(screen.getByRole('button', { name })).toBeDisabled()
  }
  screen.getAllByLabelText('Actual repetitions').forEach(input => expect(input).toBeDisabled())
})

it.each([
  ['repetitions_only', ['Actual repetitions', 'RIR (optional)'], ['External load', 'Duration (seconds)']],
  ['duration', ['Duration (seconds)', 'RPE (optional)'], ['Actual repetitions', 'Distance']],
  ['distance_and_duration', ['Duration (seconds)', 'Distance', 'Distance unit'], ['Actual repetitions', 'External load']],
  ['bodyweight_or_assisted_repetitions', ['Actual repetitions', 'Assistance (optional)', 'Assistance unit'], ['External load', 'Duration (seconds)']],
] as const)('renders only %s tracking controls', async (mode, expected, excluded) => {
  const current = activeSession(); current.exercises[0].tracking_mode = mode
  current.exercises[0].sets.forEach(item => { item.tracking_mode = mode })
  mockFetch(url => url.endsWith('/trainee/program') ? ok(workspace('in_progress', current.id)) : ok(current))
  renderPage()
  for (const label of expected) expect((await screen.findAllByLabelText(label)).length).toBeGreaterThan(0)
  for (const label of excluded) expect(screen.queryByLabelText(label)).not.toBeInTheDocument()
})

it('skips work, intentionally ends incomplete, and renders the terminal summary', async () => {
  const current = activeSession(); const calls: string[] = []
  const ended = activeSession(); ended.status = 'ended_incomplete'; ended.scheduled_workout_status = 'partial'
  mockFetch((url, init) => {
    calls.push(`${init?.method ?? 'GET'} ${url}`)
    if (url.endsWith('/trainee/program')) return ok(workspace('in_progress', current.id))
    if (url.endsWith('/end-incomplete')) return ok(ended)
    return ok(current)
  })
  renderPage()
  fireEvent.click((await screen.findAllByRole('button', { name: 'Skip set' }))[1])
  await waitFor(() => expect(calls.some(value => value.startsWith('PUT'))).toBe(true))
  fireEvent.click(screen.getByRole('button', { name: 'Skip exercise' }))
  await waitFor(() => expect(calls.some(value => value.includes('/exercises/') && value.endsWith('/skip'))).toBe(true))
  fireEvent.click(screen.getByRole('button', { name: 'End workout incomplete' }))
  expect(await screen.findByText('Workout ended incomplete')).toBeVisible()
})

it('requires completion fields and explicit confirmation', async () => {
  const current = activeSession()
  mockFetch(url => url.endsWith('/trainee/program') ? ok(workspace('in_progress', current.id)) : ok(current))
  renderPage()
  const complete = await screen.findByRole('button', { name: 'Complete workout' })
  expect(complete).toBeDisabled()
  fireEvent.change(screen.getByLabelText('Actual duration (minutes)'), { target: { value: '40' } })
  fireEvent.change(screen.getByLabelText('Session RPE (0–10)'), { target: { value: '7' } })
  expect(complete).toBeDisabled()
  fireEvent.click(screen.getByLabelText('I confirm this workout is ready to complete.'))
  expect(complete).toBeEnabled()
})

it('shows an empty state for an unavailable schedule row', async () => {
  const empty = workspace(); empty.scheduled_workouts = []
  mockFetch(() => ok(empty))
  renderPage()
  expect(await screen.findByText('Workout not found')).toBeVisible()
})

function renderPage() { const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } }); return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/trainee/workouts/workout-1']}><AuthProvider><Routes><Route path="/trainee/workouts/:scheduledWorkoutId" element={<WorkoutExecutionPage />} /></Routes></AuthProvider></MemoryRouter></QueryClientProvider>) }
function setSession(demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: 'trainee-1', email: 'trainee@example.com', first_name: demo ? 'Demo' : 'Test', last_name: 'Trainee', role: 'trainee', is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown) { return new Response(JSON.stringify(value), { status: 200, headers: { 'Content-Type': 'application/json' } }) }
function error(status: number, value: unknown) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }
function workspace(status: 'scheduled' | 'in_progress' | 'completed' = 'scheduled', sessionId: string | null = null): TrainingAssignmentWorkspace { return { timezone: 'Asia/Kolkata', local_today: '2026-07-16', current_assignment: { id: 'assignment-1', coach_id: 'coach-1', trainee_id: 'trainee-1', training_program_version_id: 'program-v1', status: 'active', is_primary: true, effective_start_date: '2026-07-13', effective_end_date: null, timezone: 'Asia/Kolkata', program_name: 'Strength Foundation', program_version_number: 1, duration_weeks: 4, goal_tags: ['strength'], created_at: '2026-07-13T00:00:00Z', activated_at: '2026-07-13T00:00:00Z', superseded_at: null, cancelled_at: null }, upcoming_assignment: null, assignment_history: [], history_events: [], scheduled_workouts: [{ id: 'workout-1', workout_session_id: sessionId, training_assignment_id: 'assignment-1', workout_template_version_id: 'template-v1', scheduled_date: '2026-07-16', program_week_number: 1, program_week_label: null, is_deload: false, weekday: 'thursday', display_order: 1, required: true, planned_duration_minutes: 50, target_session_rpe: 7, trainee_instructions: 'Move with control.', status, workout_template_version: { id: 'template-v1', workout_template_id: 'template-1', version_number: 1, name: 'Full Body Strength', goal_tags: ['strength'], estimated_duration_minutes: 50, target_session_rpe: 7, exercise_count: 1 } }] } }
function activeSession(): WorkoutSession { return { id: 'session-1', scheduled_workout_id: 'workout-1', status: 'in_progress', scheduled_workout_status: 'in_progress', workout_name: 'Full Body Strength', program_name: 'Strength Foundation', program_version_number: 1, scheduled_date: '2026-07-16', estimated_duration_minutes: 50, target_session_rpe: 7, trainee_instructions: 'Move with control.', started_at: '2026-07-16T08:00:00Z', last_activity_at: '2026-07-16T08:10:00Z', completed_at: null, ended_at: null, actual_duration_minutes: null, session_rpe: null, trainee_note: null, revision: 2, events: [{ id: 'event-1', event_type: 'session_started', created_at: '2026-07-16T08:00:00Z' }], exercises: [{ id: 'exercise-1', source_workout_template_exercise_id: 'source-exercise-1', exercise_version_id: 'exercise-v1', exercise_name: 'Goblet Squat', tracking_mode: 'repetitions_and_load', safety_cues: ['Keep a stable stance.'], section: 'main', display_order: 1, trainee_instructions: 'Move with control.', prescription_snapshot: { name: 'Goblet Squat' }, status: 'in_progress', skip_reason: null, skip_note: null, sets: [{ id: 'set-1', source_prescription_id: 'prescription-1', source: 'prescribed', set_number: 1, set_type: 'working', tracking_mode: 'repetitions_and_load', planned_repetitions_min: 8, planned_repetitions_max: 10, planned_duration_seconds: null, planned_distance_value: null, planned_distance_unit: null, planned_load_original_value: '35.000', planned_load_original_unit: 'lb', planned_assistance_original_value: null, planned_assistance_original_unit: null, planned_rpe: '7.0', planned_rir: null, planned_rest_seconds: 90, planned_tempo: '3-1-1', planned_instructions: null, actual_repetitions: 9, actual_load_original_value: '22.000', actual_load_original_unit: 'lb', actual_load_canonical_kg: '9.979', actual_assistance_original_value: null, actual_assistance_original_unit: null, actual_assistance_canonical_kg: null, actual_duration_seconds: null, actual_distance_value: null, actual_distance_unit: null, actual_rpe: '7.0', actual_rir: null, status: 'completed', completed_at: '2026-07-16T08:10:00Z', revision: 2 }, { id: 'set-2', source_prescription_id: 'prescription-2', source: 'prescribed', set_number: 2, set_type: 'working', tracking_mode: 'repetitions_and_load', planned_repetitions_min: 8, planned_repetitions_max: 10, planned_duration_seconds: null, planned_distance_value: null, planned_distance_unit: null, planned_load_original_value: '35.000', planned_load_original_unit: 'lb', planned_assistance_original_value: null, planned_assistance_original_unit: null, planned_rpe: '7.0', planned_rir: null, planned_rest_seconds: 90, planned_tempo: '3-1-1', planned_instructions: null, actual_repetitions: null, actual_load_original_value: null, actual_load_original_unit: null, actual_load_canonical_kg: null, actual_assistance_original_value: null, actual_assistance_original_unit: null, actual_assistance_canonical_kg: null, actual_duration_seconds: null, actual_distance_value: null, actual_distance_unit: null, actual_rpe: null, actual_rir: null, status: 'planned', completed_at: null, revision: 1 }] }] } }
