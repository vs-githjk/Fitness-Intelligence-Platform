import { Archive, ArrowLeft, CheckCircle2, CopyPlus, Save } from 'lucide-react'
import { FormEvent, useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../api'
import { useAccountQueryScope, useAuth } from '../../auth'
import { ExerciseDetail, ExerciseDraftData, ExerciseTrackingMode } from '../../types'
import { Badge, Button, Card, Field, LoadingState, Modal, SelectInput, StatusNotice, TextArea, TextInput } from '../ui'
import { ProgrammingShell } from './ProgrammingShell'
import { PublicationBadge, TrackingModeBadge } from './ProgrammingBadges'

const modes: { value: ExerciseTrackingMode; label: string; help: string }[] = [
  { value: 'repetitions_and_load', label: 'Repetitions and load', help: 'Prescribe a repetition range with optional external resistance.' },
  { value: 'repetitions_only', label: 'Repetitions only', help: 'Prescribe repetitions without resistance or assistance.' },
  { value: 'duration', label: 'Duration', help: 'Prescribe time-based efforts.' },
  { value: 'distance_and_duration', label: 'Distance and duration', help: 'Prescribe both distance and time.' },
  { value: 'bodyweight_or_assisted_repetitions', label: 'Bodyweight or assisted repetitions', help: 'Prescribe repetitions with optional assistance.' },
]
const empty: ExerciseDraftData = { name: '', description: null, instructions: '', tracking_mode: 'repetitions_and_load', category: '', movement_pattern: '', equipment: [], primary_muscle_groups: [], secondary_muscle_groups: [], unilateral: false, safety_cues: [], image_url: null, thumbnail_url: null }

export function ExerciseEditor() {
  const { exerciseId } = useParams(); const isNew = exerciseId === 'new'; const { user } = useAuth(); const navigate = useNavigate(); const cache = useQueryClient()
  const scope = useAccountQueryScope()
  const query = useQuery({ queryKey: [...scope, 'programming-exercise', exerciseId], queryFn: () => api<ExerciseDetail>(`/coach/exercises/${exerciseId}`), enabled: !isNew })
  const [form, setForm] = useState<ExerciseDraftData>(empty); const [dirty, setDirty] = useState(false); const [saving, setSaving] = useState(false); const [saveState, setSaveState] = useState('Not saved')
  const [error, setError] = useState(''); const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({}); const [publishOpen, setPublishOpen] = useState(false); const [archiveOpen, setArchiveOpen] = useState(false)
  const loaded = useRef('')
  const detail = query.data; const editableVersion = detail?.draft_version; const visibleVersion = editableVersion ?? detail?.published_version
  const immutable = Boolean(detail && (!editableVersion || detail.scope === 'system' || detail.status === 'archived'))

  useEffect(() => {
    if (isNew || !visibleVersion || loaded.current === visibleVersion.id) return
    loaded.current = visibleVersion.id
    setForm(copyDraft(visibleVersion)); setDirty(false); setSaveState(editableVersion ? 'Draft loaded' : 'Published version')
  }, [editableVersion, isNew, visibleVersion])
  useEffect(() => { const warn = (event: BeforeUnloadEvent) => { if (dirty) { event.preventDefault(); event.returnValue = '' } }; window.addEventListener('beforeunload', warn); return () => window.removeEventListener('beforeunload', warn) }, [dirty])

  const change = useCallback(<K extends keyof ExerciseDraftData>(key: K, value: ExerciseDraftData[K]) => { setForm(current => ({ ...current, [key]: value })); setDirty(true); setSaveState('Unsaved changes') }, [])
  function leave() { if (!dirty || window.confirm('Discard unsaved exercise changes?')) navigate('/coach/programming/exercises') }
  function apiFailure(caught: unknown, fallback: string) { if (caught instanceof ApiError) { setError(caught.message); setFieldErrors(caught.details.fields ?? {}) } else setError(fallback) }
  async function save(event: FormEvent) {
    event.preventDefault(); if (immutable || user?.is_demo) return
    setSaving(true); setError(''); setFieldErrors({}); setSaveState('Saving…')
    try {
      const next = isNew
        ? await api<ExerciseDetail>('/coach/exercises', { method: 'POST', body: JSON.stringify({ slug: slugify(form.name), ...form }) })
        : await api<ExerciseDetail>(`/coach/exercises/${exerciseId}/draft`, { method: 'PUT', body: JSON.stringify(form) })
      cache.setQueryData([...scope, 'programming-exercise', next.id], next); await cache.invalidateQueries({ queryKey: [...scope, 'programming-exercises'] })
      loaded.current = next.draft_version?.id ?? ''; setDirty(false); setSaveState('Draft saved')
      if (isNew) navigate(`/coach/programming/exercises/${next.id}`, { replace: true })
    } catch (caught) { setSaveState('Save failed'); apiFailure(caught, 'The exercise draft could not be saved.') }
    finally { setSaving(false) }
  }
  async function action(path: string, success: string) {
    setSaving(true); setError('')
    try { const next = await api<ExerciseDetail>(`/coach/exercises/${exerciseId}/${path}`, { method: 'POST' }); cache.setQueryData([...scope, 'programming-exercise', exerciseId], next); await cache.invalidateQueries({ queryKey: [...scope, 'programming-exercises'] }); loaded.current = ''; setDirty(false); setSaveState(success); setPublishOpen(false); setArchiveOpen(false) }
    catch (caught) { apiFailure(caught, 'The exercise action could not be completed.') }
    finally { setSaving(false) }
  }

  if (!isNew && query.isLoading) return <ProgrammingShell title="Exercise" description="Loading exercise details."><LoadingState /></ProgrammingShell>
  if (!isNew && query.error) return <ProgrammingShell title="Exercise unavailable" description="The exercise could not be opened."><StatusNotice tone="risk" title="Exercise unavailable">{query.error.message}</StatusNotice></ProgrammingShell>
  return <ProgrammingShell title={isNew ? 'Create private exercise' : visibleVersion?.name ?? 'Exercise'} description={detail?.scope === 'system' ? 'System exercises are published references and cannot be changed.' : 'Build a private exercise draft, then publish an immutable version.'} action={<Button variant="secondary" onClick={leave}><ArrowLeft aria-hidden="true" className="size-4" />Back to library</Button>}>
    {user?.is_demo && <StatusNotice tone="info" title="Demo workspace — changes are disabled">Exercise content is available for review only.</StatusNotice>}
    {error && <StatusNotice tone="risk" title="Exercise action unsuccessful"><p>{error}</p>{Object.keys(fieldErrors).length > 0 && <ul className="mt-2 list-disc pl-5">{Object.entries(fieldErrors).map(([field, message]) => <li key={field}><a href={`#exercise-${field.replaceAll('.', '-')}`} className="underline">{message}</a></li>)}</ul>}</StatusNotice>}
    {detail && <div className="flex flex-wrap gap-2"><Badge tone={detail.scope === 'system' ? 'info' : 'neutral'}>{detail.scope === 'system' ? 'System · read-only' : 'Private'}</Badge>{visibleVersion && <TrackingModeBadge mode={visibleVersion.tracking_mode} />}<PublicationBadge draft={Boolean(detail.draft_version)} published={Boolean(detail.published_version)} />{detail.status === 'archived' && <Badge tone="neutral">Archived</Badge>}</div>}
    {detail?.published_version && detail.draft_version && <StatusNotice tone="info" title={`Revising published version ${detail.published_version.version_number}`}>This draft is version {detail.draft_version.version_number}. Publishing creates a new immutable version and preserves the earlier content.</StatusNotice>}
    <form onSubmit={save} className="space-y-6"><Card><div className="grid gap-5 lg:grid-cols-2"><Field label="Name" error={fieldErrors.name} id="exercise-name">{props => <TextInput {...props} value={form.name} disabled={immutable} onChange={event => change('name', event.target.value)} />}</Field><Field label="Tracking mode" help={modes.find(item => item.value === form.tracking_mode)?.help} error={fieldErrors.tracking_mode} id="exercise-tracking_mode">{props => <SelectInput {...props} value={form.tracking_mode} disabled={immutable} onChange={event => change('tracking_mode', event.target.value as ExerciseTrackingMode)}>{modes.map(mode => <option key={mode.value} value={mode.value}>{mode.label}</option>)}</SelectInput>}</Field><Field label="Description" optional error={fieldErrors.description} id="exercise-description">{props => <TextArea {...props} value={form.description ?? ''} disabled={immutable} onChange={event => change('description', nullable(event.target.value))} />}</Field><Field label="Instructions" help="Describe setup and execution clearly for future trainee-facing use." error={fieldErrors.instructions} id="exercise-instructions">{props => <TextArea {...props} value={form.instructions} disabled={immutable} onChange={event => change('instructions', event.target.value)} />}</Field><Field label="Category" error={fieldErrors.category} id="exercise-category">{props => <TextInput {...props} value={form.category} disabled={immutable} onChange={event => change('category', event.target.value)} />}</Field><Field label="Movement pattern" error={fieldErrors.movement_pattern} id="exercise-movement_pattern">{props => <TextInput {...props} value={form.movement_pattern} disabled={immutable} onChange={event => change('movement_pattern', event.target.value)} />}</Field><ListField label="Equipment" help="Comma-separated; leave blank for none." value={form.equipment} disabled={immutable} onChange={value => change('equipment', value)} /><ListField label="Primary muscle groups" help="At least one is required." value={form.primary_muscle_groups} disabled={immutable} error={fieldErrors.primary_muscle_groups} onChange={value => change('primary_muscle_groups', value)} /><ListField label="Secondary muscle groups" value={form.secondary_muscle_groups} disabled={immutable} onChange={value => change('secondary_muscle_groups', value)} /><ListField label="Safety cues" help="Separate concise cues with commas." value={form.safety_cues} disabled={immutable} onChange={value => change('safety_cues', value)} /><Field label="Image URL" optional help="Public HTTPS images only. Video is not supported." error={fieldErrors.image_url} id="exercise-image_url">{props => <TextInput {...props} type="url" value={form.image_url ?? ''} disabled={immutable} onChange={event => change('image_url', nullable(event.target.value))} />}</Field><Field label="Thumbnail URL" optional help="Public HTTPS images only." error={fieldErrors.thumbnail_url} id="exercise-thumbnail_url">{props => <TextInput {...props} type="url" value={form.thumbnail_url ?? ''} disabled={immutable} onChange={event => change('thumbnail_url', nullable(event.target.value))} />}</Field><label className="flex min-h-11 items-center gap-3 rounded-xl border p-3 text-sm font-semibold"><input type="checkbox" checked={form.unilateral} disabled={immutable} onChange={event => change('unilateral', event.target.checked)} className="size-5" />Unilateral exercise</label></div></Card>
      <div className="sticky bottom-20 z-10 flex flex-col gap-3 rounded-2xl border bg-surface/95 p-4 shadow-card backdrop-blur sm:flex-row sm:items-center lg:bottom-4"><p aria-live="polite" className="min-w-0 flex-1 text-sm font-semibold text-secondary">{saveState}</p>{!immutable && <Button type="submit" loading={saving} disabled={user?.is_demo}><Save aria-hidden="true" className="size-4" />Save draft</Button>}{detail?.draft_version && <Button type="button" disabled={saving || dirty || user?.is_demo} onClick={() => setPublishOpen(true)}><CheckCircle2 aria-hidden="true" className="size-4" />Review and publish</Button>}{detail && !detail.draft_version && detail.published_version && detail.scope === 'coach_private' && detail.status === 'active' && <Button type="button" disabled={saving || user?.is_demo} onClick={() => action('revisions', 'Revision draft created')}><CopyPlus aria-hidden="true" className="size-4" />Create revision</Button>}{detail?.scope === 'coach_private' && detail.status === 'active' && <Button type="button" variant="danger" disabled={saving || user?.is_demo} onClick={() => setArchiveOpen(true)}><Archive aria-hidden="true" className="size-4" />Archive</Button>}</div>
    </form>
    {detail?.published_version && !detail.draft_version && <Card><h2 className="text-lg font-semibold">Immutable published version {detail.published_version.version_number}</h2><p className="mt-2 text-sm text-secondary">Published {new Date(detail.published_version.published_at!).toLocaleString()}. Create a revision to make changes without altering this history.</p><details className="mt-3"><summary className="min-h-11 cursor-pointer py-3 text-sm font-semibold text-primary">Technical details</summary><code className="block overflow-x-auto rounded-lg bg-elevated p-3 text-xs">{detail.published_version.content_hash}</code></details></Card>}
    <Modal open={publishOpen} onClose={() => setPublishOpen(false)} title="Publish exercise version?" description="Publishing makes this draft immutable. Future changes require a new revision."><dl className="grid gap-3 rounded-xl bg-elevated p-4 text-sm sm:grid-cols-2"><div><dt className="text-muted">Exercise</dt><dd className="font-semibold">{form.name}</dd></div><div><dt className="text-muted">Tracking</dt><dd className="font-semibold">{modes.find(item => item.value === form.tracking_mode)?.label}</dd></div></dl><div className="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"><Button variant="secondary" onClick={() => setPublishOpen(false)}>Keep editing</Button><Button loading={saving} onClick={() => action('publish', 'Published successfully')}>Confirm publication</Button></div></Modal>
    <Modal open={archiveOpen} onClose={() => setArchiveOpen(false)} title="Archive this exercise?" description="It will disappear from active selection but remain readable for historical published workouts."><div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"><Button variant="secondary" onClick={() => setArchiveOpen(false)}>Cancel</Button><Button variant="danger" loading={saving} onClick={() => action('archive', 'Exercise archived')}>Archive exercise</Button></div></Modal>
  </ProgrammingShell>
}

function copyDraft(value: ExerciseDraftData): ExerciseDraftData { return { ...value, equipment: [...value.equipment], primary_muscle_groups: [...value.primary_muscle_groups], secondary_muscle_groups: [...value.secondary_muscle_groups], safety_cues: [...value.safety_cues] } }
function nullable(value: string) { return value.trim() || null }
function slugify(value: string) { return value.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'private-exercise' }
function ListField({ label, help, value, disabled, error, onChange }: { label: string; help?: string; value: string[]; disabled: boolean; error?: string; onChange: (value: string[]) => void }) { return <Field label={label} help={help} error={error}>{props => <TextInput {...props} value={value.join(', ')} disabled={disabled} onChange={event => onChange(event.target.value.split(',').map(item => item.trim()).filter(Boolean))} />}</Field> }
