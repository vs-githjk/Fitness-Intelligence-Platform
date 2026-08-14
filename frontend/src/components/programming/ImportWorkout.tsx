import { CheckCircle2, CircleHelp, Download, FileSpreadsheet, FileUp, Upload, X, XCircle } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api'
import { useAuth } from '../../auth'
import { ExerciseTrackingMode, ImportPreview, ImportPreviewRow, ImportRowRaw, WorkoutTemplateDetail } from '../../types'
import { MovementGlyph } from '../iron/MovementGlyph'
import { Badge, Button, Card, Field, SelectInput, StatusNotice, TextInput } from '../ui'
import { ProgrammingShell } from './ProgrammingShell'

const EXAMPLE_CSV = [
  'exercise,sets,reps,load,load_unit,rest_seconds,notes',
  'Goblet squat,3,8-10,20,kg,90,Keep the chest tall',
  'Push-up,3,10,,,60,',
  'Forearm plank,3,,,,45,Hold the position',
].join('\n')

const REP_MODES = new Set<ExerciseTrackingMode>([
  'repetitions_and_load', 'repetitions_only', 'bodyweight_or_assisted_repetitions',
])

// Mirrors the backend prescription mapping so a coach-chosen candidate for a
// needs-review row gets the right fields for its tracking mode.
function prescriptionFor(raw: ImportRowRaw, mode: ExerciseTrackingMode): Record<string, unknown> {
  const base: Record<string, unknown> = { set_type: 'working' }
  if (raw.rest_seconds != null) base.rest_seconds = raw.rest_seconds
  if (raw.notes) base.instructions = raw.notes
  if (REP_MODES.has(mode) && raw.reps_min != null && raw.reps_max != null) {
    base.repetitions_min = raw.reps_min
    base.repetitions_max = raw.reps_max
  }
  if (mode === 'repetitions_and_load' && raw.load != null) {
    base.target_load_original_value = raw.load
    base.target_load_original_unit = raw.load_unit ?? 'kg'
  }
  if (mode === 'duration' && raw.duration_seconds != null) {
    base.target_duration_seconds = raw.duration_seconds
  }
  if (mode === 'distance_and_duration') {
    if (raw.duration_seconds != null) base.target_duration_seconds = raw.duration_seconds
    if (raw.distance != null) {
      base.target_distance_value = raw.distance
      base.target_distance_unit = raw.distance_unit ?? 'kilometers'
    }
  }
  return base
}

const STATUS = {
  matched: { tone: 'positive' as const, icon: CheckCircle2, label: 'Matched' },
  needs_review: { tone: 'attention' as const, icon: CircleHelp, label: 'Needs review' },
  not_found: { tone: 'neutral' as const, icon: XCircle, label: 'No match' },
}

export function ImportWorkout() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [content, setContent] = useState('')
  const [format, setFormat] = useState<'csv' | 'xlsx'>('csv')
  const [fileName, setFileName] = useState<string | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  // line -> chosen exercise_version_id, '' (unresolved) or 'skip'.
  const [choice, setChoice] = useState<Record<number, string>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function runPreview() {
    setBusy(true); setError(null)
    try {
      const result = await api<ImportPreview>('/coach/workout-imports/preview', {
        method: 'POST', body: JSON.stringify({ content, template_name: name, format }),
      })
      setPreview(result)
      setName(prev => prev || result.template_name)
      const next: Record<number, string> = {}
      for (const row of result.rows) {
        next[row.line] = row.status === 'matched' && row.matched
          ? row.matched.exercise_version_id
          : row.status === 'not_found' ? 'skip' : ''
      }
      setChoice(next)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Preview failed')
    } finally {
      setBusy(false)
    }
  }

  const isXlsx = (file: File) => /\.xlsx$/i.test(file.name) || file.type.includes('spreadsheetml')

  async function onFile(file: File | undefined) {
    if (!file) return
    setName(prev => prev || file.name.replace(/\.(csv|xlsx)$/i, ''))
    if (isXlsx(file)) {
      const bytes = new Uint8Array(await file.arrayBuffer())
      let binary = ''
      for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000))
      setContent(btoa(binary)); setFormat('xlsx'); setFileName(file.name)
    } else {
      setContent(await file.text()); setFormat('csv'); setFileName(null)
    }
  }

  function pasteCsv(value: string) { setContent(value); setFormat('csv'); setFileName(null) }
  function clearFile() { setContent(''); setFormat('csv'); setFileName(null) }

  const resolvable = useMemo(() => {
    if (!preview) return []
    return preview.rows
      .map(row => ({ row, versionId: choice[row.line] }))
      .filter((entry): entry is { row: ImportPreviewRow; versionId: string } =>
        Boolean(entry.versionId) && entry.versionId !== 'skip')
  }, [preview, choice])

  async function createDraft() {
    if (!resolvable.length) return
    setBusy(true); setError(null)
    try {
      const exercises = resolvable.map(({ row, versionId }, index) => {
        const exercise = row.matched?.exercise_version_id === versionId
          ? row.matched
          : row.candidates.find(c => c.exercise_version_id === versionId)!
        const single = row.matched?.exercise_version_id === versionId && row.prescription
          ? { set_type: 'working', ...row.prescription }
          : prescriptionFor(row.raw, exercise.tracking_mode)
        return {
          exercise_version_id: versionId, section: 'main', display_order: index + 1,
          coach_notes: null, trainee_instructions: null,
          sets: Array.from({ length: row.sets }, (_, i) => ({ set_number: i + 1, ...single })),
        }
      })
      const created = await api<WorkoutTemplateDetail>('/coach/workout-templates', {
        method: 'POST',
        body: JSON.stringify({ name: name.trim() || 'Imported workout', goal_tags: [], exercises }),
      })
      navigate(`/coach/programming/templates/${created.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create the workout draft')
    } finally {
      setBusy(false)
    }
  }

  return <ProgrammingShell title="Import a workout" description="Bring a workout you already have as a CSV or Excel file. Nothing is created until you review the matches and confirm.">
    <Card className="space-y-4">
      <Field id="import-name" label="Workout name">
        {({ id }) => <TextInput id={id} value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Lower Body Strength" />}
      </Field>
      <div className="grid gap-3 sm:grid-cols-[auto_1fr] sm:items-center">
        <label className="inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border bg-surface px-4 text-sm font-semibold hover:bg-elevated">
          <FileUp aria-hidden="true" className="size-4" />Choose CSV or Excel file
          <input type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" className="sr-only" onChange={e => onFile(e.target.files?.[0])} />
        </label>
        <a href={`data:text/csv;charset=utf-8,${encodeURIComponent(EXAMPLE_CSV)}`} download="vytal-workout-template.csv" className="inline-flex items-center gap-2 text-sm font-semibold text-primary">
          <Download aria-hidden="true" className="size-4" />Download example template
        </a>
      </div>
      {format === 'xlsx'
        ? <div className="flex items-center justify-between gap-3 rounded-xl border bg-elevated px-4 py-3">
            <span className="flex min-w-0 items-center gap-2 text-sm font-semibold"><FileSpreadsheet aria-hidden="true" className="size-5 shrink-0 text-primary" /><span className="truncate">{fileName}</span><Badge tone="info">Excel</Badge></span>
            <button type="button" onClick={clearFile} aria-label="Remove file" className="grid size-8 shrink-0 place-items-center rounded-lg text-muted hover:bg-surface hover:text-foreground"><X aria-hidden="true" className="size-4" /></button>
          </div>
        : <Field id="import-content" label="Or paste CSV rows" help="Columns: exercise (required), sets, reps, load, load_unit, duration, distance, distance_unit, rest_seconds, notes.">
            {({ id, describedBy }) => <textarea id={id} aria-describedby={describedBy} value={content} onChange={e => pasteCsv(e.target.value)} rows={5} className="w-full rounded-xl border bg-surface p-3 font-mono text-xs" placeholder={EXAMPLE_CSV} />}
          </Field>}
      <div className="flex justify-end">
        <Button onClick={runPreview} loading={busy && !preview} disabled={!content.trim()}><Upload aria-hidden="true" className="size-4" />Preview import</Button>
      </div>
    </Card>

    {error && <StatusNotice tone="risk" title="Import problem">{error}</StatusNotice>}

    {preview && <Card className="space-y-4">
      {preview.file_errors.length > 0 && <StatusNotice tone="attention" title="Check the file">{preview.file_errors.join(' ')}</StatusNotice>}
      {preview.rows.length > 0 && <>
        <p className="text-sm text-secondary" aria-live="polite">
          {preview.summary.matched} matched · {preview.summary.needs_review} to review · {preview.summary.not_found} not found
        </p>
        <ul className="space-y-2">
          {preview.rows.map(row => <ImportRow key={row.line} row={row} value={choice[row.line] ?? ''} onChange={value => setChoice(prev => ({ ...prev, [row.line]: value }))} />)}
        </ul>
        <div className="flex flex-col gap-2 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-secondary">{resolvable.length} exercise{resolvable.length === 1 ? '' : 's'} will be added to a new draft.</p>
          <Button onClick={createDraft} loading={busy && Boolean(preview)} disabled={!resolvable.length || user?.is_demo} title={user?.is_demo ? 'Demo workspace — changes are disabled' : undefined}>
            Create workout draft
          </Button>
        </div>
      </>}
    </Card>}
  </ProgrammingShell>
}

function ImportRow({ row, value, onChange }: { row: ImportPreviewRow; value: string; onChange: (value: string) => void }) {
  const status = STATUS[row.status]
  const StatusIcon = status.icon
  const repText = row.raw.reps_min != null ? (row.raw.reps_min === row.raw.reps_max ? `${row.raw.reps_min}` : `${row.raw.reps_min}–${row.raw.reps_max}`) : null
  const detail = [repText && `${repText} reps`, row.raw.load && `${row.raw.load}${row.raw.load_unit ?? ''}`, row.raw.duration_seconds && `${row.raw.duration_seconds}s`].filter(Boolean).join(' · ')
  return <li className="rounded-xl border bg-surface p-3">
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
      <Badge tone={status.tone}><StatusIcon aria-hidden="true" className="mr-1 size-3" />{status.label}</Badge>
      <span className="font-semibold">{row.exercise_name}</span>
      <span className="text-xs text-muted">{row.sets} set{row.sets === 1 ? '' : 's'}{detail && ` · ${detail}`}</span>
    </div>
    {row.matched && row.status === 'matched' && <p className="mt-2 flex items-center gap-2 text-sm text-secondary"><MovementGlyph pattern={row.matched.movement_pattern} className="size-5" strokeWidth={1.75} />Matched to <span className="font-medium">{row.matched.name}</span></p>}
    {row.status === 'needs_review' && <div className="mt-2"><SelectInput aria-label={`Choose an exercise for ${row.exercise_name}`} className="mt-0" value={value} onChange={e => onChange(e.target.value)}><option value="">Choose a match…</option>{row.candidates.map(c => <option key={c.exercise_version_id} value={c.exercise_version_id}>{c.name}</option>)}<option value="skip">Skip this row</option></SelectInput></div>}
    {row.status === 'not_found' && <p className="mt-2 text-sm text-muted">{row.error ?? 'No exercise in your library matches this name. It will be skipped — add it manually or create a custom exercise.'}</p>}
  </li>
}
