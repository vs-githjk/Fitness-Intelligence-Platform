import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../../auth'
import { ExerciseSummary, ExerciseTrackingMode, ExerciseVersion, WorkoutTemplateDetail, WorkoutTemplateDraftData } from '../../types'
import { ExerciseEditor } from './ExerciseEditor'
import { ExerciseLibrary } from './ExerciseLibrary'
import { SetPrescriptionEditor } from './SetPrescriptionEditor'
import { TemplateBuilder } from './TemplateBuilder'
import { TemplateExerciseEditor, newPrescription } from './TemplateExerciseEditor'
import { TemplateLibrary } from './TemplateLibrary'
import { TraineePreview } from './TraineePreview'

class MemoryStorage implements Storage {
  private values = new Map<string, string>(); get length() { return this.values.size }
  clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null }
  key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) }
  setItem(key: string, value: string) { this.values.set(key, value) }
}

const goblet = version('v-load', 'Goblet squat', 'repetitions_and_load')
const plank = version('v-duration', 'Front plank', 'duration')
const exercises: ExerciseSummary[] = [
  root('system-load', 'system', goblet),
  root('private-duration', 'coach_private', plank),
]

beforeEach(() => setSession(false))
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('Programming exercise workspace', () => {
  it('filters system and private exercises and exposes metadata filters', async () => {
    mockFetch(() => ok(exercises))
    renderWorkspace(<ExerciseLibrary />, '/coach/programming/exercises')
    expect(await screen.findByText('Goblet squat')).toBeVisible()
    expect(screen.getByText('Front plank')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'My Exercises' }))
    expect(screen.queryByText('Goblet squat')).not.toBeInTheDocument()
    expect(screen.getByText('Front plank')).toBeVisible()
    fireEvent.change(screen.getByLabelText('Tracking mode'), { target: { value: 'repetitions_and_load' } })
    expect(screen.getByText('No exercises match')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Clear filters' }))
    fireEvent.change(screen.getByRole('searchbox', { name: 'Search exercises' }), { target: { value: 'goblet' } })
    expect(screen.getByText('Goblet squat')).toBeVisible()
    expect(screen.queryByText('Front plank')).not.toBeInTheDocument()
  })

  it('creates a private exercise draft with exact enum values and displays server errors', async () => {
    let requestBody: Record<string, unknown> | undefined
    mockFetch((_url, init) => { requestBody = JSON.parse(String(init?.body)); return new Response(JSON.stringify({ detail: { code: 'exercise_slug_conflict', message: 'Exercise already exists' } }), { status: 409, headers: { 'Content-Type': 'application/json' } }) })
    renderWorkspace(<ExerciseEditor />, '/coach/programming/exercises/new', '/coach/programming/exercises/:exerciseId')
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Coach row' } })
    fireEvent.change(screen.getByLabelText('Tracking mode'), { target: { value: 'repetitions_only' } })
    fireEvent.change(screen.getByLabelText('Instructions'), { target: { value: 'Pull with control.' } })
    fireEvent.change(screen.getByLabelText('Category'), { target: { value: 'strength' } })
    fireEvent.change(screen.getByLabelText('Movement pattern'), { target: { value: 'horizontal pull' } })
    fireEvent.change(screen.getByLabelText('Primary muscle groups'), { target: { value: 'back, biceps' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save draft' }))
    await screen.findByText('Exercise already exists')
    expect(requestBody).toMatchObject({ slug: 'coach-row', tracking_mode: 'repetitions_only', primary_muscle_groups: ['back', 'biceps'] })
    expect(screen.getByLabelText('Name')).toHaveValue('Coach row')
  })

  it('shows demo content while disabling every mutation control', async () => {
    setSession(true); mockFetch(() => ok(exercises))
    renderWorkspace(<ExerciseLibrary />, '/coach/programming/exercises')
    expect(await screen.findByText('Goblet squat')).toBeVisible()
    expect(screen.getByRole('button', { name: 'New exercise' })).toBeDisabled()
    expect(screen.getAllByText(/changes are disabled/i).length).toBeGreaterThan(0)
  })
})

describe('Tracking-mode prescription UI', () => {
  it.each([
    ['repetitions_and_load', 'Target load', 'Target RIR'],
    ['repetitions_only', 'Target RIR', 'Target load'],
    ['duration', 'Target duration (seconds)', 'Repetitions min'],
    ['distance_and_duration', 'Target distance', 'Target RIR'],
    ['bodyweight_or_assisted_repetitions', 'Target assistance', 'Target load'],
  ] as [ExerciseTrackingMode, string, string][])('shows only compatible fields for %s', (mode, shown, hidden) => {
    render(<SetPrescriptionEditor mode={mode} value={newPrescription(mode)} disabled={false} canMoveUp={false} canMoveDown={false} onChange={() => undefined} onRemove={() => undefined} onDuplicate={() => undefined} onMove={() => undefined} />)
    expect(screen.queryAllByLabelText(labelPattern(shown)).length).toBeGreaterThan(0)
    expect(screen.queryAllByLabelText(labelPattern(hidden))).toHaveLength(0)
  })

  it('shows the Decimal lb-to-kg conversion and assistance disclaimer', () => {
    const load = { ...newPrescription('repetitions_and_load'), target_load_original_value: 22, target_load_original_unit: 'lb' as const }
    const { rerender } = render(<SetPrescriptionEditor mode="repetitions_and_load" value={load} disabled={false} canMoveUp={false} canMoveDown={false} onChange={() => undefined} onRemove={() => undefined} onDuplicate={() => undefined} onMove={() => undefined} />)
    expect(screen.getByText('Canonical load: 9.979 kg')).toBeVisible()
    const assisted = { ...newPrescription('bodyweight_or_assisted_repetitions'), target_assistance_original_value: 20, target_assistance_original_unit: 'kg' as const }
    rerender(<SetPrescriptionEditor mode="bodyweight_or_assisted_repetitions" value={assisted} disabled={false} canMoveUp={false} canMoveDown={false} onChange={() => undefined} onRemove={() => undefined} onDuplicate={() => undefined} onMove={() => undefined} />)
    expect(screen.getByText('Assistance is not resistance volume.')).toBeVisible()
  })
})

describe('Workout-template workspace', () => {
  it('filters template summaries by draft and goal state', async () => {
    mockFetch(() => ok({ items: [summary('Draft strength', true, ['strength']), summary('Published recovery', false, ['recovery'])], page: 1, per_page: 100, total: 2 }))
    renderWorkspace(<TemplateLibrary />, '/coach/programming/templates')
    expect(await screen.findByText('Draft strength')).toBeVisible(); expect(screen.getByText('Published recovery')).toBeVisible()
    fireEvent.change(screen.getByLabelText('Publication status'), { target: { value: 'draft' } })
    expect(screen.getByText('Draft strength')).toBeVisible(); expect(screen.queryByText('Published recovery')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('Goal tag'), { target: { value: 'recovery' } })
    expect(screen.getByText('No templates match')).toBeVisible()
  })

  it('creates a complete replacement graph with explicit ordering', async () => {
    let saved: WorkoutTemplateDraftData | undefined
    mockFetch((url, init) => {
      if (url.includes('/coach/exercises')) return ok(exercises)
      if (url.includes('/coach/workout-templates') && init?.method === 'POST') { saved = JSON.parse(String(init.body)); return ok(templateDetail(saved!, true), 201) }
      return ok({})
    })
    renderWorkspace(<TemplateBuilder />, '/coach/programming/templates/new', '/coach/programming/templates/:templateId')
    fireEvent.change(await screen.findByLabelText('Name'), { target: { value: 'Full body test' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add exercise' }))
    const dialog = await screen.findByRole('dialog', { name: 'Add exercise to workout' })
    fireEvent.click(within(dialog).getByRole('button', { name: /Goblet squat/ }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Add to workout' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save draft' }))
    await waitFor(() => expect(saved).toBeDefined())
    expect(saved).toMatchObject({ name: 'Full body test', exercises: [{ exercise_version_id: 'v-load', section: 'main', display_order: 1, sets: [{ set_number: 1, repetitions_min: 8, repetitions_max: 10 }] }] })
  })

  it('preserves local changes and offers safe reload on a draft revision conflict', async () => {
    const detail = templateDetail(templateForm(), true)
    mockFetch((url, init) => {
      if (url.includes('/coach/exercises')) return ok(exercises)
      if (init?.method === 'PUT') return new Response(JSON.stringify({ detail: { code: 'workout_template_draft_conflict', message: 'Draft changed elsewhere' } }), { status: 409, headers: { 'Content-Type': 'application/json' } })
      return ok(detail)
    })
    renderWorkspace(<TemplateBuilder />, '/coach/programming/templates/t-1', '/coach/programming/templates/:templateId')
    const name = await screen.findByLabelText('Name'); fireEvent.change(name, { target: { value: 'My unsaved local name' } }); fireEvent.click(screen.getByRole('button', { name: 'Save draft' }))
    expect(await screen.findByRole('dialog', { name: 'Draft changed elsewhere' })).toBeVisible()
    expect(screen.getByLabelText('Name')).toHaveValue('My unsaved local name')
    expect(screen.getByText(/were not overwritten/i)).toBeVisible()
  })

  it('provides keyboard-accessible exercise and set ordering actions', () => {
    const onMove = vi.fn(); const onChange = vi.fn(); const exerciseData = templateForm().exercises[0]
    render(<TemplateExerciseEditor value={{ ...exerciseData, sets: [newPrescription('repetitions_and_load'), { ...newPrescription('repetitions_and_load'), set_number: 2 }] }} exercise={goblet} disabled={false} canMoveUp canMoveDown onChange={onChange} onRemove={() => undefined} onMove={onMove} />)
    fireEvent.click(screen.getByRole('button', { name: 'Move Goblet squat up' })); expect(onMove).toHaveBeenCalledWith(-1)
    fireEvent.click(screen.getByRole('button', { name: 'Move set 2 up' })); expect(onChange).toHaveBeenCalled()
  })

  it('renders trainee preview without coach-only notes', () => {
    const form = { ...templateForm(), coach_notes: 'SECRET COACH NOTE', trainee_instructions: 'Welcome trainee.', exercises: [{ ...templateForm().exercises[0], coach_notes: 'PRIVATE EXERCISE NOTE', trainee_instructions: 'Move steadily.' }] }
    render(<TraineePreview template={form} exercises={new Map([[goblet.id, goblet]])} />)
    expect(screen.getByText('Welcome trainee.')).toBeVisible(); expect(screen.getByText('Move steadily.')).toBeVisible(); expect(screen.getByText(goblet.instructions)).toBeVisible()
    expect(screen.queryByText('SECRET COACH NOTE')).not.toBeInTheDocument(); expect(screen.queryByText('PRIVATE EXERCISE NOTE')).not.toBeInTheDocument()
  })
})

function renderWorkspace(element: React.ReactNode, path: string, route = path) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={queryClient}><MemoryRouter initialEntries={[path]}><AuthProvider><Routes><Route path={route} element={element} /></Routes></AuthProvider></MemoryRouter></QueryClientProvider>)
}
function setSession(demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: 'coach-1', email: 'coach@example.com', first_name: demo ? 'Demo' : 'Test', last_name: 'Coach', role: 'coach', is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }
function version(id: string, name: string, tracking_mode: ExerciseTrackingMode): ExerciseVersion { return { id, exercise_id: `root-${id}`, version_number: 1, status: 'published', name, description: `${name} description`, instructions: `${name} instructions`, tracking_mode, category: tracking_mode === 'duration' ? 'core' : 'strength', movement_pattern: tracking_mode === 'duration' ? 'isometric' : 'squat', equipment: tracking_mode === 'duration' ? ['mat'] : ['dumbbell'], primary_muscle_groups: ['core'], secondary_muscle_groups: [], unilateral: false, safety_cues: ['Stop if technique changes.'], difficulty: null, coaching_cues: [], common_mistakes: [], primary_image: null, secondary_image: null, demonstration_video: null, image_url: null, thumbnail_url: null, content_hash: 'a'.repeat(64), created_by_user_id: null, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', published_at: '2026-07-16T00:00:00Z' } }
function root(id: string, scope: 'system' | 'coach_private', published_version: ExerciseVersion): ExerciseSummary { return { id, scope, owner_coach_id: scope === 'system' ? null : 'coach-1', slug: id, status: 'active', created_at: '2026-07-16T00:00:00Z', archived_at: null, published_version, draft_version: null } }
function templateForm(): WorkoutTemplateDraftData { return { name: 'Full body strength', description: 'Description', goal_tags: ['strength'], estimated_duration_minutes: 45, target_session_rpe: 7, coach_notes: 'Coach only', trainee_instructions: 'Train with control.', exercises: [{ exercise_version_id: goblet.id, section: 'main', display_order: 1, coach_notes: null, trainee_instructions: 'Move steadily.', sets: [newPrescription(goblet.tracking_mode)] }] } }
function templateDetail(form: WorkoutTemplateDraftData, draft: boolean): WorkoutTemplateDetail { const versionData = { id: draft ? 'tv-draft' : 'tv-published', workout_template_id: 't-1', version_number: 1, version_status: draft ? 'draft' as const : 'published' as const, draft_revision: 1, ...form, content_hash: draft ? null : 'b'.repeat(64), created_by_user_id: 'coach-1', created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', published_at: draft ? null : '2026-07-16T00:00:00Z', exercises: form.exercises.map((item, index) => ({ ...item, id: `te-${index}`, created_at: '2026-07-16T00:00:00Z', exercise_version: goblet, sets: item.sets.map((set, setIndex) => ({ ...set, id: `set-${setIndex}`, target_load_canonical_kg: null, target_assistance_canonical_kg: null, created_at: '2026-07-16T00:00:00Z' })) })) }; return { id: 't-1', owner_coach_id: 'coach-1', status: 'active', current_published_version_id: draft ? null : versionData.id, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', archived_at: null, draft_version: draft ? versionData : null, published_version: draft ? null : versionData, versions: [{ id: versionData.id, version_number: 1, version_status: versionData.version_status, draft_revision: 1, name: form.name, content_hash: versionData.content_hash, updated_at: versionData.updated_at, published_at: versionData.published_at }] } }
function summary(name: string, has_draft: boolean, goal_tags: string[]) { return { id: name, status: 'active' as const, name, goal_tags, estimated_duration_minutes: 45, target_session_rpe: 7, exercise_count: 2, current_published_version_number: has_draft ? null : 1, published_at: has_draft ? null : '2026-07-16T00:00:00Z', has_draft, created_at: '2026-07-16T00:00:00Z', updated_at: '2026-07-16T00:00:00Z', archived_at: null } }
function labelPattern(value: string) { return new RegExp(`^${value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`) }
