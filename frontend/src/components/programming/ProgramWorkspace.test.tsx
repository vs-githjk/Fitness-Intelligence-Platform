import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../../auth'
import { ProgramTemplateVersionSummary, TrainingProgramDetail, TrainingProgramDraftData, TrainingProgramList, WorkoutTemplateDetail } from '../../types'
import { ProgramBuilder } from './ProgramBuilder'
import { ProgramLibrary } from './ProgramLibrary'
import { ProgramPreview } from './ProgramPreview'

class MemoryStorage implements Storage { private values = new Map<string, string>(); get length() { return this.values.size } clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null } key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) } setItem(key: string, value: string) { this.values.set(key, value) } }
const template: ProgramTemplateVersionSummary = { id: 'template-v1', workout_template_id: 'template-1', version_number: 1, name: 'Full Body Strength', goal_tags: ['strength'], estimated_duration_minutes: 50, target_session_rpe: 7, exercise_count: 3 }

beforeEach(() => setSession(false))
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('Program library', () => {
  it('filters programs by publication and goal and renders bounded summaries', async () => {
    const list: TrainingProgramList = { items: [summary('Strength draft', true, ['strength']), summary('Published endurance', false, ['endurance'])], page: 1, per_page: 100, total: 2 }
    mockFetch(() => ok(list)); renderWorkspace(<ProgramLibrary />, '/coach/programming/programs')
    expect(await screen.findByText('Strength draft')).toBeVisible(); expect(screen.getByText('Published endurance')).toBeVisible()
    expect(screen.getByRole('tab', { name: 'Programs' })).toHaveAttribute('aria-selected', 'true')
    fireEvent.change(screen.getByLabelText('Publication status'), { target: { value: 'draft' } })
    expect(screen.getByText('Strength draft')).toBeVisible(); expect(screen.queryByText('Published endurance')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Goal tag'), { target: { value: 'endurance' } })
    expect(screen.getByText('No programs match')).toBeVisible()
  })

  it('disables program creation for demo coaches', async () => {
    setSession(true); mockFetch(() => ok({ items: [], page: 1, per_page: 100, total: 0 })); renderWorkspace(<ProgramLibrary />, '/coach/programming/programs')
    expect(await screen.findByText('Create the first reusable multi-week program.')).toBeVisible()
    expect(screen.getByRole('button', { name: 'New program' })).toBeDisabled()
  })

  it('shows loading, empty, and archive confirmation states', async () => {
    let resolveList!: (response: Response) => void
    vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(resolve => { resolveList = resolve })))
    const view = renderWorkspace(<ProgramLibrary />, '/coach/programming/programs')
    expect(screen.getByText('Loading programs')).toBeVisible()
    resolveList(ok({ items: [], page: 1, per_page: 100, total: 0 }))
    expect(await screen.findByText('Create the first reusable multi-week program.')).toBeVisible()
    view.unmount()

    mockFetch((url, init) => init?.method === 'POST' ? ok(programDetail(programForm(), true)) : ok({ items: [summary('Archive me', true, ['strength'])], page: 1, per_page: 100, total: 1 }))
    renderWorkspace(<ProgramLibrary />, '/coach/programming/programs')
    fireEvent.click(await screen.findByRole('button', { name: 'Archive' }))
    expect(screen.getByRole('dialog', { name: 'Archive training program?' })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Archive program' }))
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/Archive me/archive'), expect.objectContaining({ method: 'POST' })))
  })
})

describe('Program builder', () => {
  it('changes duration, marks a deload, pins a template version, and saves the complete graph', async () => {
    let saved: TrainingProgramDraftData | undefined
    mockFetch((url, init) => {
      if (url.includes('/coach/workout-templates?')) return ok({ items: [templateListSummary()], page: 1, per_page: 100, total: 1 })
      if (url.endsWith('/coach/workout-templates/template-1')) return ok(templateDetail())
      if (url.endsWith('/coach/training-programs') && init?.method === 'POST') { saved = JSON.parse(String(init.body)); return ok(programDetail(saved!, true), 201) }
      return ok({})
    })
    renderWorkspace(<ProgramBuilder />, '/coach/programming/programs/new', '/coach/programming/programs/:programId')
    fireEvent.change(await screen.findByLabelText('Name'), { target: { value: 'Four week test' } })
    fireEvent.change(screen.getByLabelText('Duration (weeks)'), { target: { value: '3' } })
    expect(screen.getAllByText('Week 3').length).toBeGreaterThan(0); expect(screen.queryAllByText('Week 4')).toHaveLength(0)
    fireEvent.click(screen.getAllByLabelText('Coach-authored deload week', { selector: 'input' }).at(-1)!)
    fireEvent.click(screen.getAllByRole('button', { name: 'Add workout' })[0])
    const dialog = await screen.findByRole('dialog', { name: 'Add workout to program' })
    fireEvent.click(within(dialog).getByRole('button', { name: /Full Body Strength/ }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add workout' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save draft' }))
    await waitFor(() => expect(saved).toBeDefined())
    expect(saved).toMatchObject({ name: 'Four week test', duration_weeks: 3, weeks: [{ week_number: 1, sessions: [{ workout_template_version_id: 'template-v1', weekday: 'monday', display_order: 1, required: true }] }, { week_number: 2 }, { week_number: 3, is_deload: true }] })
  })

  it('preserves local edits after an optimistic concurrency conflict', async () => {
    const detail = programDetail(programForm(), true)
    mockFetch((url, init) => {
      if (url.includes('/coach/workout-templates?')) return ok({ items: [], page: 1, per_page: 100, total: 0 })
      if (init?.method === 'PUT') return new Response(JSON.stringify({ detail: { code: 'training_program_draft_conflict', message: 'Draft changed elsewhere' } }), { status: 409, headers: { 'Content-Type': 'application/json' } })
      return ok(detail)
    })
    renderWorkspace(<ProgramBuilder />, '/coach/programming/programs/program-1', '/coach/programming/programs/:programId')
    const name = await screen.findByLabelText('Name'); fireEvent.change(name, { target: { value: 'Unsaved local program' } }); fireEvent.click(screen.getByRole('button', { name: 'Save draft' }))
    expect(await screen.findByRole('dialog', { name: 'Program draft changed elsewhere' })).toBeVisible()
    expect(screen.getByLabelText('Name')).toHaveValue('Unsaved local program')
    expect(screen.getByText(/were not overwritten/i)).toBeVisible()
    expect(screen.getByText('Loaded revision 1; latest server revision 1.')).toBeVisible()
  })

  it('provides required toggles and keyboard session ordering controls', async () => {
    const form = programForm(); form.weeks[0].sessions.push({ ...form.weeks[0].sessions[0], display_order: 2, required: false })
    mockFetch(url => url.includes('/coach/workout-templates?') ? ok({ items: [], page: 1, per_page: 100, total: 0 }) : ok(programDetail(form, true)))
    renderWorkspace(<ProgramBuilder />, '/coach/programming/programs/program-1', '/coach/programming/programs/:programId')
    expect((await screen.findAllByLabelText('Required workout'))[1]).not.toBeChecked()
    fireEvent.click(screen.getAllByRole('button', { name: 'Move Full Body Strength up' })[1])
    expect(screen.getByText('Unsaved changes')).toBeVisible()
  })

  it('reviews publication and renders a published program as immutable', async () => {
    let detail = programDetail(programForm(), true)
    mockFetch((url, init) => {
      if (url.includes('/coach/workout-templates?')) return ok({ items: [], page: 1, per_page: 100, total: 0 })
      if (url.endsWith('/publish') && init?.method === 'POST') { detail = programDetail(programForm(), false); return ok(detail) }
      return ok(detail)
    })
    renderWorkspace(<ProgramBuilder />, '/coach/programming/programs/program-1', '/coach/programming/programs/:programId')
    fireEvent.click(await screen.findByRole('button', { name: 'Review and publish' }))
    expect(screen.getByRole('dialog', { name: 'Review and publish program' })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Confirm publication' }))
    expect(await screen.findByText(/Immutable published version 1/)).toBeVisible()
    expect(screen.getByLabelText('Name')).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Create revision' })).toBeVisible()
  })
})

it('trainee program preview shows deload and optional context without coach notes', () => {
  const form = programForm(); form.coach_notes = 'SECRET PROGRAM NOTE'; form.weeks[0].coach_notes = 'SECRET WEEK NOTE'; form.weeks[0].sessions[0].coach_notes = 'SECRET SESSION NOTE'; form.weeks[0].sessions[0].required = false; form.weeks[0].is_deload = true
  render(<ProgramPreview program={form} templates={new Map([[template.id, template]])} />)
  expect(screen.getAllByText('Coach-authored deload').length).toBeGreaterThan(0); expect(screen.getByText('Optional')).toBeVisible(); expect(screen.getAllByText('Complete carefully.').length).toBeGreaterThan(0)
  expect(screen.queryByText('SECRET PROGRAM NOTE')).not.toBeInTheDocument(); expect(screen.queryByText('SECRET WEEK NOTE')).not.toBeInTheDocument(); expect(screen.queryByText('SECRET SESSION NOTE')).not.toBeInTheDocument()
})

function renderWorkspace(element: React.ReactNode, path: string, route = path) { const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } }); return render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[path]}><AuthProvider><Routes><Route path={route} element={element} /></Routes></AuthProvider></MemoryRouter></QueryClientProvider>) }
function setSession(demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: 'coach-1', email: 'coach@example.com', first_name: demo ? 'Demo' : 'Test', last_name: 'Coach', role: 'coach', is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }
function programForm(): TrainingProgramDraftData { return { name: 'Four Week Foundation', description: 'Description', goal_tags: ['strength'], duration_weeks: 4, coach_notes: 'Coach only', trainee_instructions: 'Complete carefully.', weeks: [1, 2, 3, 4].map(number => ({ week_number: number, label: number === 4 ? 'Deload' : null, coach_notes: null, is_deload: number === 4, sessions: number === 1 ? [{ workout_template_version_id: template.id, weekday: 'monday', display_order: 1, required: true, planned_duration_override_minutes: null, target_session_rpe_override: null, coach_notes: null, trainee_instructions: 'Complete carefully.' }] : [] })) } }
function programDetail(form: TrainingProgramDraftData, draft: boolean): TrainingProgramDetail { const version = { id: draft ? 'program-v-draft' : 'program-v-published', training_program_id: 'program-1', version_number: 1, version_status: draft ? 'draft' as const : 'published' as const, draft_revision: 1, ...form, content_hash: draft ? null : 'c'.repeat(64), created_by_user_id: 'coach-1', created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', published_at: draft ? null : '2026-07-16T00:00:00Z', weeks: form.weeks.map(week => ({ ...week, id: `week-${week.week_number}`, created_at: '2026-07-16T00:00:00Z', sessions: week.sessions.map((session, index) => ({ ...session, id: `session-${week.week_number}-${index}`, workout_template_version: template, created_at: '2026-07-16T00:00:00Z' })) })) }; return { id: 'program-1', owner_coach_id: 'coach-1', status: 'active', current_published_version_id: draft ? null : version.id, cloned_from_program_id: null, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', archived_at: null, draft_version: draft ? version : null, published_version: draft ? null : version, versions: [{ id: version.id, version_number: 1, version_status: version.version_status, draft_revision: 1, name: form.name, content_hash: version.content_hash, updated_at: version.updated_at, published_at: version.published_at }] } }
function summary(name: string, has_draft: boolean, goals: string[]) { return { id: name, status: 'active' as const, name, goal_tags: goals, duration_weeks: 4, workout_slot_count: 8, deload_week_count: 1, current_published_version_number: has_draft ? null : 1, published_at: has_draft ? null : '2026-07-16T00:00:00Z', has_draft, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', archived_at: null } }
function templateListSummary() { return { id: 'template-1', status: 'active', name: template.name, goal_tags: template.goal_tags, estimated_duration_minutes: 50, target_session_rpe: 7, exercise_count: 3, current_published_version_number: 1, published_at: '2026-07-16T00:00:00Z', has_draft: false, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', archived_at: null } }
function templateDetail() { return { id: 'template-1', owner_coach_id: 'coach-1', status: 'active', current_published_version_id: template.id, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', archived_at: null, draft_version: null, published_version: { id: template.id, workout_template_id: 'template-1', version_number: 1, version_status: 'published', draft_revision: 1, name: template.name, description: null, goal_tags: template.goal_tags, estimated_duration_minutes: 50, target_session_rpe: 7, coach_notes: null, trainee_instructions: null, content_hash: 'a'.repeat(64), created_by_user_id: 'coach-1', created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', published_at: '2026-07-16T00:00:00Z', exercises: [{ id: 'e1' }, { id: 'e2' }, { id: 'e3' }] }, versions: [] } as unknown as WorkoutTemplateDetail }
