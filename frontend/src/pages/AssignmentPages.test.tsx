import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../auth'
import { ScheduledWorkout, TrainingAssignment, TrainingAssignmentWorkspace } from '../types'
import { CoachAssignmentPage, TraineeProgramPage } from './AssignmentPages'

class MemoryStorage implements Storage { private values = new Map<string, string>(); get length() { return this.values.size } clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null } key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) } setItem(key: string, value: string) { this.values.set(key, value) } }

beforeEach(() => setSession('coach', false))
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

it('previews and confirms a coach Program assignment', async () => {
  const calls: string[] = []
  mockFetch((url, init) => {
    calls.push(`${init?.method ?? 'GET'} ${url}`)
    if (url.endsWith('/coach/trainees')) return ok([{ trainee_id: 'trainee-1', name: 'Aarav Trainee' }])
    if (url.includes('/coach/training-programs?')) return ok({ items: [{ id: 'program-1', current_published_version_number: 1 }], page: 1, per_page: 100, total: 1 })
    if (url.endsWith('/coach/training-programs/program-1')) return ok(programDetail())
    if (url.endsWith('/training-assignment')) return ok(workspace())
    if (url.endsWith('/preview')) return ok({ timezone: 'Asia/Kolkata', effective_start_date: '2026-07-16', effective_end_date: '2026-08-06', program_name: 'Strength Foundation', program_version_number: 1, replaces_current: true, replaces_upcoming: false, workouts: [workout()] })
    if (url.endsWith('/training-assignments') && init?.method === 'POST') return ok(workspace(true), 201)
    return ok({})
  })
  renderPage(<CoachAssignmentPage />)
  expect(await screen.findByText('Create or replace assignment')).toBeVisible()
  await waitFor(() => expect(screen.getByLabelText('Trainee')).toHaveValue('trainee-1'))
  fireEvent.change(screen.getByLabelText('Effective start date'), { target: { value: '2026-07-16' } })
  fireEvent.click(screen.getByRole('button', { name: 'Preview schedule' }))
  expect(await screen.findByText('Schedule preview')).toBeVisible()
  expect(screen.getByText('This changes an existing plan')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Review assignment' }))
  expect(screen.getByRole('dialog', { name: 'Confirm Program assignment' })).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Confirm assignment' }))
  await waitFor(() => expect(calls.some(value => value.includes('POST') && value.endsWith('/training-assignments'))).toBe(true))
})

it('renders the trainee current Program, today, calendar, deload, and read-only details', async () => {
  setSession('trainee', false); mockFetch(() => ok(workspace(true))); renderPage(<TraineeProgramPage />)
  expect(await screen.findByRole('heading', { name: 'Strength Foundation' })).toBeVisible()
  expect(screen.getAllByRole('link', { name: 'Program' }).length).toBeGreaterThan(0)
  expect(screen.getByRole('heading', { name: "Today's Workout" })).toBeVisible()
  expect(screen.getByRole('heading', { name: 'Workout Calendar' })).toBeVisible()
  expect(screen.getAllByText('Coach-authored deload').length).toBeGreaterThan(0)
  fireEvent.click(screen.getByRole('button', { name: 'View workout details' }))
  expect(screen.getByRole('dialog', { name: 'Full Body Strength' })).toBeVisible()
  expect(screen.getByRole('link', { name: 'Open workout' })).toHaveAttribute('href', '/trainee/workouts/workout-1')
})

it('keeps assignment controls disabled for demo coaches', async () => {
  setSession('coach', true); mockFetch(url => {
    if (url.endsWith('/coach/trainees')) return ok([{ trainee_id: 'trainee-1', name: 'Demo Trainee' }])
    if (url.includes('/coach/training-programs?')) return ok({ items: [], page: 1, per_page: 100, total: 0 })
    if (url.endsWith('/training-assignment')) return ok(workspace(true))
    return ok({})
  }); renderPage(<CoachAssignmentPage />)
  expect(await screen.findByText('Demo workspace — changes are disabled')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Preview schedule' })).toBeDisabled()
  expect(screen.getByLabelText('Trainee')).toBeDisabled()
})

function renderPage(element: React.ReactNode) { const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } }); return render(<QueryClientProvider client={client}><MemoryRouter><AuthProvider>{element}</AuthProvider></MemoryRouter></QueryClientProvider>) }
function setSession(role: 'coach' | 'trainee', demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: `${role}-1`, email: `${role}@example.com`, first_name: demo ? 'Demo' : 'Test', last_name: role, role, is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }
function workout(): ScheduledWorkout { return { id: 'workout-1', training_assignment_id: 'assignment-1', workout_template_version_id: 'template-v1', scheduled_date: '2026-07-16', program_week_number: 1, program_week_label: 'Coach-authored deload', is_deload: true, weekday: 'thursday', display_order: 1, required: true, planned_duration_minutes: 50, target_session_rpe: 7, trainee_instructions: 'Move with control.', status: 'scheduled', workout_template_version: { id: 'template-v1', workout_template_id: 'template-1', version_number: 1, name: 'Full Body Strength', goal_tags: ['strength'], estimated_duration_minutes: 50, target_session_rpe: 7, exercise_count: 3 } } }
function assignment(status: 'active' | 'scheduled' = 'active'): TrainingAssignment { return { id: status === 'active' ? 'assignment-1' : 'assignment-2', coach_id: 'coach-1', trainee_id: 'trainee-1', training_program_version_id: 'program-v1', status, is_primary: true, effective_start_date: status === 'active' ? '2026-07-13' : '2026-08-10', effective_end_date: null, timezone: 'Asia/Kolkata', program_name: status === 'active' ? 'Strength Foundation' : 'Recovery Reset', program_version_number: 1, duration_weeks: 4, goal_tags: ['strength'], created_at: '2026-07-13T00:00:00Z', activated_at: status === 'active' ? '2026-07-13T00:00:00Z' : null, superseded_at: null, cancelled_at: null } }
function workspace(populated = false): TrainingAssignmentWorkspace { return { timezone: 'Asia/Kolkata', local_today: '2026-07-16', current_assignment: populated ? assignment('active') : null, upcoming_assignment: populated ? assignment('scheduled') : null, assignment_history: populated ? [assignment('scheduled'), assignment('active')] : [], history_events: [], scheduled_workouts: populated ? [workout()] : [] } }
function programDetail() { return { id: 'program-1', owner_coach_id: 'coach-1', status: 'active', current_published_version_id: 'program-v1', created_at: '2026-07-01T00:00:00Z', updated_at: '2026-07-01T00:00:00Z', archived_at: null, draft_version: null, published_version: { id: 'program-v1', training_program_id: 'program-1', version_number: 1, version_status: 'published', draft_revision: 1, name: 'Strength Foundation', description: null, goal_tags: ['strength'], duration_weeks: 4, coach_notes: null, trainee_instructions: null, content_hash: 'a'.repeat(64), created_by_user_id: 'coach-1', created_at: '2026-07-01T00:00:00Z', updated_at: '2026-07-01T00:00:00Z', published_at: '2026-07-01T00:00:00Z', weeks: [] }, versions: [] } }
