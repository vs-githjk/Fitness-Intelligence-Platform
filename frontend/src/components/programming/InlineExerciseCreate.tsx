import { Sparkles, X } from 'lucide-react'
import { FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../../api'
import { ExerciseDetail, ExerciseDraftData, ExerciseTrackingMode, ExerciseVersion } from '../../types'
import { Button, Field, SelectInput, StatusNotice, TextArea, TextInput } from '../ui'

// Vocabulary aligned with the deterministic search synonyms + the frozen §20 muscle→region
// map, so a coach-created exercise is immediately findable by muscle ("quads") and pattern.
const MOVEMENT_PATTERNS = ['squat', 'hinge', 'lunge', 'horizontal push', 'vertical push', 'horizontal pull', 'vertical pull', 'carry', 'rotation', 'isolation', 'core', 'gait']
const MUSCLES = ['quadriceps', 'hamstrings', 'glutes', 'chest', 'back', 'shoulders', 'biceps', 'triceps', 'core', 'forearms', 'hip flexors', 'calves']
const CATEGORIES = ['strength', 'hypertrophy', 'conditioning', 'mobility', 'core', 'power']
const TRACKING: { value: ExerciseTrackingMode; label: string }[] = [
  { value: 'repetitions_and_load', label: 'Reps + load' },
  { value: 'repetitions_only', label: 'Reps only' },
  { value: 'bodyweight_or_assisted_repetitions', label: 'Bodyweight / assisted' },
  { value: 'duration', label: 'Hold for time' },
  { value: 'distance_and_duration', label: 'Distance + time' },
]

type Quick = { name: string; movement_pattern: string; primary_muscle: string; equipment: string; tracking_mode: ExerciseTrackingMode; category: string; instructions: string; secondary_muscle: string }
const emptyQuick: Quick = { name: '', movement_pattern: '', primary_muscle: '', equipment: '', tracking_mode: 'repetitions_and_load', category: 'strength', instructions: '', secondary_muscle: '' }

function slugify(value: string) { return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'private-exercise' }
function csv(value: string) { return value.split(',').map(item => item.trim()).filter(Boolean) }

// Compact create-and-publish flow used inside the add-exercise picker. The coach never
// leaves the builder: on success the new published version is handed straight back to be
// added. Advanced authoring (media, cues, mistakes) stays available on the full editor.
export function InlineExerciseCreate({ initialName = '', onCancel, onCreated }: { initialName?: string; onCancel: () => void; onCreated: (detail: ExerciseDetail, version: ExerciseVersion) => void }) {
  const [form, setForm] = useState<Quick>({ ...emptyQuick, name: initialName })
  const [more, setMore] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const set = <K extends keyof Quick>(key: K, value: Quick[K]) => setForm(current => ({ ...current, [key]: value }))

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true); setError(''); setFieldErrors({})
    const draft: ExerciseDraftData = {
      name: form.name.trim(),
      description: null,
      instructions: form.instructions.trim() || `${form.name.trim()} — coach-created exercise.`,
      tracking_mode: form.tracking_mode,
      category: form.category.trim() || 'strength',
      movement_pattern: form.movement_pattern.trim(),
      equipment: csv(form.equipment),
      primary_muscle_groups: csv(form.primary_muscle),
      secondary_muscle_groups: csv(form.secondary_muscle),
      unilateral: false,
      safety_cues: [],
      difficulty: null,
      coaching_cues: [],
      common_mistakes: [],
      image_url: null,
      thumbnail_url: null,
    }
    try {
      const created = await api<ExerciseDetail>('/coach/exercises', { method: 'POST', body: JSON.stringify({ slug: slugify(form.name), ...draft }) })
      // Publish immediately so the exercise can be added to a workout (templates reference
      // exact published versions). This is a deterministic clerical step — no invented content.
      const published = await api<ExerciseDetail>(`/coach/exercises/${created.id}/publish`, { method: 'POST' })
      const version = published.published_version
      if (!version) throw new ApiError(500, { message: 'The exercise was created but could not be published.' })
      onCreated(published, version)
    } catch (caught) {
      if (caught instanceof ApiError) { setError(caught.message); setFieldErrors(caught.details.fields ?? {}) }
      else setError('The exercise could not be created.')
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="rounded-2xl border border-primary/40 bg-primary/[0.03] p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2"><Sparkles aria-hidden="true" className="size-4 text-primary" /><h3 className="text-base font-semibold">Create a custom exercise</h3></div>
        <button type="button" onClick={onCancel} aria-label="Cancel custom exercise" className="grid size-8 place-items-center rounded-lg text-muted hover:bg-elevated hover:text-foreground"><X aria-hidden="true" className="size-4" /></button>
      </div>
      <p className="mt-1 text-xs text-muted">It becomes a private, published exercise and is added to this workout right away. You can add media and cues later from the exercise editor.</p>
      {error && <div className="mt-3"><StatusNotice tone="risk" title="Could not create exercise">{error}</StatusNotice></div>}
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Field label="Name" error={fieldErrors.name}>{props => <TextInput {...props} value={form.name} autoFocus onChange={event => set('name', event.target.value)} />}</Field>
        <Field label="Movement" help="e.g. squat, hinge, horizontal push" error={fieldErrors.movement_pattern}>{props => <><TextInput {...props} list="quick-movements" value={form.movement_pattern} onChange={event => set('movement_pattern', event.target.value)} /><datalist id="quick-movements">{MOVEMENT_PATTERNS.map(item => <option key={item} value={item} />)}</datalist></>}</Field>
        <Field label="Primary muscle" help="Drives muscle search (e.g. quads → quadriceps)" error={fieldErrors.primary_muscle_groups}>{props => <><TextInput {...props} list="quick-muscles" value={form.primary_muscle} onChange={event => set('primary_muscle', event.target.value)} /><datalist id="quick-muscles">{MUSCLES.map(item => <option key={item} value={item} />)}</datalist></>}</Field>
        <Field label="Equipment" optional help="Comma-separated; blank = bodyweight" error={fieldErrors.equipment}>{props => <TextInput {...props} value={form.equipment} onChange={event => set('equipment', event.target.value)} placeholder="dumbbell, bench" />}</Field>
        <Field label="Tracking" error={fieldErrors.tracking_mode}>{props => <SelectInput {...props} value={form.tracking_mode} onChange={event => set('tracking_mode', event.target.value as ExerciseTrackingMode)}>{TRACKING.map(mode => <option key={mode.value} value={mode.value}>{mode.label}</option>)}</SelectInput>}</Field>
        <Field label="Category" help="e.g. strength, conditioning" error={fieldErrors.category}>{props => <><TextInput {...props} list="quick-categories" value={form.category} onChange={event => set('category', event.target.value)} /><datalist id="quick-categories">{CATEGORIES.map(item => <option key={item} value={item} />)}</datalist></>}</Field>
      </div>
      {more && <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Field label="Secondary muscles" optional help="Comma-separated" error={fieldErrors.secondary_muscle_groups}>{props => <TextInput {...props} list="quick-muscles" value={form.secondary_muscle} onChange={event => set('secondary_muscle', event.target.value)} />}</Field>
        <Field label="Instructions" optional help="How to set up and execute" error={fieldErrors.instructions}>{props => <TextArea {...props} value={form.instructions} onChange={event => set('instructions', event.target.value)} />}</Field>
      </div>}
      {!more && <button type="button" onClick={() => setMore(true)} className="mt-3 text-sm font-semibold text-primary hover:underline">Add secondary muscles & instructions</button>}
      <div className="mt-5 flex flex-col-reverse items-stretch gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs text-muted">Need cues, media, or difficulty? <Link to="/coach/programming/exercises/new" className="font-semibold text-primary hover:underline">Open the full editor</Link>.</p>
        <div className="flex flex-col-reverse gap-2 sm:flex-row">
          <Button type="button" variant="secondary" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={busy} disabled={!form.name.trim() || !form.movement_pattern.trim() || !form.primary_muscle.trim()}>Create & add</Button>
        </div>
      </div>
    </form>
  )
}
