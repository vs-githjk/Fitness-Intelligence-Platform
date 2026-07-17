/* eslint-disable react-refresh/only-export-components -- shared analytics constants and components co-located intentionally */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api'
import { useAccountQueryScope } from '../../auth'
import {
  CoachSessionDetail,
  CoachSessionList,
  CoachSessionSummary,
  RecordedBestsResponse,
  WorkoutAdherenceResponse,
  WorkoutClassification,
  WorkoutLoadResponse,
  WorkoutLoadWeek,
} from '../../types'
import { Badge, Card, Disclosure, ErrorState, LoadingState, ProgressBar, SegmentedControl, StatusNotice } from '../ui'

export const LOAD_DISCLAIMER =
  'Training load summarizes workout duration and reported effort. It is not a medical measure.'

function weekLabel(iso: string): string {
  const [, month, day] = iso.split('-')
  return `${month}/${day}`
}

function pct(value: number | null): string {
  return value == null ? 'Unavailable' : `${value}%`
}

const STATE_COPY: Record<string, string> = {
  above_planned: 'Above planned',
  near_planned: 'Near planned',
  below_planned: 'Below planned',
  unavailable: 'Unavailable',
}

// --- Weekly planned vs completed load (grouped bars) ---
export function WeeklyLoadChart({ weeks }: { weeks: WorkoutLoadWeek[] }) {
  const values = weeks.flatMap(w => [w.planned_session_load_total, w.completed_session_load_total])
  const max = Math.max(1, ...values)
  if (!weeks.length) return <EmptyChart label="No scheduled workouts in this range." />
  return (
    <div>
      <div className="flex gap-3 text-xs" role="list" aria-label="Legend">
        <span role="listitem" className="inline-flex items-center gap-1"><span aria-hidden className="inline-block size-3 rounded-sm bg-[rgb(var(--color-border))]" />Planned</span>
        <span role="listitem" className="inline-flex items-center gap-1"><span aria-hidden className="inline-block size-3 rounded-sm bg-primary" />Completed</span>
      </div>
      <div className="mt-3 flex items-end gap-3 overflow-x-auto pb-2" role="img" aria-label={`Weekly planned versus completed load for ${weeks.length} weeks`}>
        {weeks.map(week => (
          <div key={week.week_start_local_date} className="flex min-w-14 flex-1 flex-col items-center gap-1">
            <div className="flex h-40 w-full items-end justify-center gap-1">
              <div className="w-1/2 rounded-t bg-[rgb(var(--color-border))]" style={{ height: `${(week.planned_session_load_total / max) * 100}%` }} title={`Planned ${week.planned_session_load_total}`} />
              <div className="w-1/2 rounded-t bg-primary" style={{ height: `${(week.completed_session_load_total / max) * 100}%` }} title={`Completed ${week.completed_session_load_total}`} />
            </div>
            <span className="text-[0.65rem] text-muted">{weekLabel(week.week_start_local_date)}</span>
          </div>
        ))}
      </div>
      <Disclosure summary="Accessible data table">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Weekly planned and completed session load</caption>
            <thead><tr className="border-b text-xs uppercase text-muted"><th className="py-2">Week</th><th className="py-2">Planned</th><th className="py-2">Completed</th><th className="py-2">Difference</th><th className="py-2">Volume (kg)</th><th className="py-2">Unavailable</th></tr></thead>
            <tbody>{weeks.map(week => (
              <tr key={week.week_start_local_date} className="border-b last:border-0">
                <td className="py-2">{week.week_start_local_date}</td>
                <td className="py-2">{week.planned_session_load_total}</td>
                <td className="py-2">{week.completed_session_load_total}</td>
                <td className="py-2">{week.difference > 0 ? '+' : ''}{week.difference}</td>
                <td className="py-2">{week.resistance_volume_kg ?? 'Unavailable'}</td>
                <td className="py-2">{week.unavailable_planned_load_count + week.unavailable_completed_load_count > 0 ? `${week.unavailable_planned_load_count} planned / ${week.unavailable_completed_load_count} completed` : 'None'}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </Disclosure>
    </div>
  )
}

// --- Workout status distribution (labelled bars, not colour-only) ---
const STATUS_ROWS: { key: keyof StatusCounts; label: string; tone: 'positive' | 'attention' | 'risk' | 'primary' }[] = [
  { key: 'completed', label: 'Completed', tone: 'positive' },
  { key: 'partial', label: 'Partial', tone: 'attention' },
  { key: 'ordinary_skipped', label: 'Skipped', tone: 'attention' },
  { key: 'safety_skipped', label: 'Safety-ended', tone: 'risk' },
  { key: 'missed', label: 'Missed', tone: 'risk' },
  { key: 'pending', label: 'Pending', tone: 'primary' },
]
interface StatusCounts { completed: number; partial: number; ordinary_skipped: number; safety_skipped: number; missed: number; pending: number }

export function StatusDistribution({ counts }: { counts: StatusCounts }) {
  const total = STATUS_ROWS.reduce((sum, row) => sum + counts[row.key], 0)
  if (!total) return <EmptyChart label="No required workouts in this range." />
  return (
    <div className="space-y-2" role="img" aria-label="Workout status distribution">
      {STATUS_ROWS.map(row => (
        <div key={row.key} className="grid grid-cols-[7rem_1fr_2rem] items-center gap-2 text-sm">
          <span className="text-muted">{row.label}</span>
          <ProgressBar value={total ? (counts[row.key] / total) * 100 : 0} tone={row.tone} label={`${row.label}: ${counts[row.key]} of ${total}`} />
          <span className="text-right font-semibold">{counts[row.key]}</span>
        </div>
      ))}
    </div>
  )
}

// --- Weekly adherence trend (completed / eligible per week) ---
export function AdherenceTrend({ weeks }: { weeks: WorkoutLoadWeek[] }) {
  if (!weeks.length) return <EmptyChart label="No weekly data in this range." />
  return (
    <div className="space-y-2">
      {weeks.map(week => {
        const eligible = week.completed_count + week.partial_count + week.skipped_count + week.missed_count
        const rate = eligible ? Math.round((week.completed_count / eligible) * 100) : null
        return (
          <div key={week.week_start_local_date} className="grid grid-cols-[5rem_1fr_4rem] items-center gap-2 text-sm">
            <span className="text-muted">{weekLabel(week.week_start_local_date)}</span>
            <ProgressBar value={rate ?? 0} tone={rate == null ? 'primary' : rate >= 80 ? 'positive' : rate >= 50 ? 'attention' : 'risk'} label={`Week of ${week.week_start_local_date}: ${rate == null ? 'no eligible workouts' : `${rate}% completed`}`} />
            <span className="text-right font-semibold">{rate == null ? 'N/A' : `${rate}%`}</span>
          </div>
        )
      })}
    </div>
  )
}

// --- Resistance-volume trend (only shown when any week has volume) ---
export function VolumeTrend({ weeks }: { weeks: WorkoutLoadWeek[] }) {
  const withVolume = weeks.filter(w => w.resistance_volume_kg != null)
  if (!withVolume.length) return <EmptyChart label="No resistance-training volume recorded in this range." />
  const max = Math.max(1, ...withVolume.map(w => Number(w.resistance_volume_kg)))
  return (
    <div>
      <div className="flex items-end gap-3 overflow-x-auto pb-2" role="img" aria-label="Weekly resistance volume in kilograms">
        {weeks.map(week => {
          const value = week.resistance_volume_kg == null ? null : Number(week.resistance_volume_kg)
          return (
            <div key={week.week_start_local_date} className="flex min-w-12 flex-1 flex-col items-center gap-1">
              <div className="flex h-32 w-full items-end justify-center">
                {value == null ? <span className="text-[0.6rem] text-muted">—</span> : <div className="w-2/3 rounded-t bg-primary" style={{ height: `${(value / max) * 100}%` }} title={`${value} kg`} />}
              </div>
              <span className="text-[0.65rem] text-muted">{weekLabel(week.week_start_local_date)}</span>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-muted">Weeks without repetitions-and-load work are shown as “—”, never zero.</p>
    </div>
  )
}

function EmptyChart({ label }: { label: string }) {
  return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted">{label}</div>
}

function statusCounts(adherence: WorkoutAdherenceResponse): StatusCounts {
  const c = adherence.completion
  return { completed: c.completed_count, partial: c.partial_count, ordinary_skipped: c.ordinary_skipped_count, safety_skipped: c.safety_skipped_count, missed: c.missed_count, pending: c.pending_count }
}

export function classificationLabel(value: WorkoutClassification): string {
  return ({ completed: 'Completed', partial: 'Partial', ordinary_skipped: 'Skipped', safety_skipped: 'Safety-ended', missed: 'Missed', pending: 'Pending', coach_cancelled: 'Cancelled', superseded_or_rescheduled: 'Rescheduled', optional: 'Optional' } as const)[value]
}

// --- Container: fetches and renders all Workout Intelligence for one identity ---
export function WorkoutIntelligencePanel({ basePath, keyPrefix }: { basePath: string; keyPrefix: string }) {
  const [days, setDays] = useState('30')
  const scope = useAccountQueryScope()
  const load = useQuery({ queryKey: [...scope, keyPrefix, 'load', basePath, days], queryFn: () => api<WorkoutLoadResponse>(`${basePath}/workout-load?days=${days}`) })
  const adherence = useQuery({ queryKey: [...scope, keyPrefix, 'adherence', basePath, days], queryFn: () => api<WorkoutAdherenceResponse>(`${basePath}/workout-adherence?days=${days}`) })
  const bests = useQuery({ queryKey: [...scope, keyPrefix, 'bests', basePath, days], queryFn: () => api<RecordedBestsResponse>(`${basePath}/recorded-bests?days=${days}`) })

  if (load.isLoading || adherence.isLoading || bests.isLoading) return <LoadingState label="Loading workout intelligence" />
  const error = load.error ?? adherence.error ?? bests.error
  if (error) return <ErrorState description={error.message} onRetry={() => { load.refetch(); adherence.refetch(); bests.refetch() }} />

  const loadData = load.data!
  const adherenceData = adherence.data!
  const bestsData = bests.data!
  const completion = adherenceData.completion
  const comparison = loadData.planned_vs_completed

  return (
    <section aria-labelledby="workout-intelligence-heading" className="space-y-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-wider text-primary">Workout Intelligence</p>
          <h2 id="workout-intelligence-heading" className="mt-1 text-2xl font-semibold">Training load & adherence</h2>
        </div>
        <div className="w-64"><SegmentedControl label="Analytics range" value={days} options={[{ value: '7', label: '7 days' }, { value: '14', label: '14 days' }, { value: '30', label: '30 days' }]} onChange={setDays} /></div>
      </div>

      <StatusNotice tone="info" title="About training load">{LOAD_DISCLAIMER}</StatusNotice>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card><p className="text-sm text-muted">Completion adherence</p><p className="metric-number mt-1 text-3xl font-bold">{pct(completion.completion_adherence_percentage)}</p><p className="mt-1 text-xs text-muted">{completion.completed_count} of {completion.eligible_required_count} required</p></Card>
        <Card><p className="text-sm text-muted">Prescribed-set adherence</p><p className="metric-number mt-1 text-3xl font-bold">{pct(adherenceData.prescribed_set_adherence.percentage)}</p><p className="mt-1 text-xs text-muted">{adherenceData.prescribed_set_adherence.completed_planned_working_sets} of {adherenceData.prescribed_set_adherence.planned_working_sets} working sets</p></Card>
        <Card><p className="text-sm text-muted">Exercise adherence</p><p className="metric-number mt-1 text-3xl font-bold">{pct(adherenceData.exercise_adherence.percentage)}</p><p className="mt-1 text-xs text-muted">{adherenceData.exercise_adherence.completed_exercises} of {adherenceData.exercise_adherence.planned_exercises} exercises</p></Card>
        <Card><p className="text-sm text-muted">Planned vs completed load</p><p className="metric-number mt-1 text-3xl font-bold">{comparison.completed ?? '—'}</p><Badge tone={comparison.state === 'unavailable' ? 'neutral' : comparison.state === 'near_planned' ? 'positive' : 'info'} className="mt-1">{STATE_COPY[comparison.state]}</Badge></Card>
      </div>

      {completion.safety_skipped_count > 0 && <StatusNotice tone="risk" title={`${completion.safety_skipped_count} safety-ended workout${completion.safety_skipped_count > 1 ? 's' : ''}`}>Safety-ended workouts remain in the adherence denominator and are reported separately from ordinary skips.</StatusNotice>}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card><h3 className="font-semibold">Weekly planned vs completed load</h3><div className="mt-4"><WeeklyLoadChart weeks={loadData.weeks} /></div></Card>
        <Card><h3 className="font-semibold">Workout status distribution</h3><div className="mt-4"><StatusDistribution counts={statusCounts(adherenceData)} /></div></Card>
        <Card><h3 className="font-semibold">Weekly adherence trend</h3><div className="mt-4"><AdherenceTrend weeks={loadData.weeks} /></div></Card>
        <Card><h3 className="font-semibold">Resistance-volume trend</h3><div className="mt-4"><VolumeTrend weeks={loadData.weeks} /></div></Card>
      </div>

      <Card>
        <h3 className="font-semibold">Recorded bests</h3>
        <p className="mt-1 text-xs text-muted">Highest values recorded within the selected range, from completed workouts only.</p>
        {bestsData.exercises.length ? (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <caption className="sr-only">Recorded bests by exercise</caption>
              <thead><tr className="border-b text-xs uppercase text-muted"><th className="py-2">Exercise</th><th className="py-2">Highest recorded load</th><th className="py-2">Highest recorded repetitions</th><th className="py-2">Highest recorded volume</th></tr></thead>
              <tbody>{bestsData.exercises.map(exercise => (
                <tr key={exercise.exercise_id} className="border-b last:border-0">
                  <td className="py-2 font-medium">{exercise.exercise_name}</td>
                  <td className="py-2">{exercise.highest_recorded_load ? `${exercise.highest_recorded_load.canonical_kg} kg${exercise.highest_recorded_load.original_unit && exercise.highest_recorded_load.original_unit !== 'kg' ? ` (${exercise.highest_recorded_load.original_value} ${exercise.highest_recorded_load.original_unit})` : ''}` : '—'}</td>
                  <td className="py-2">{exercise.highest_recorded_repetitions ? exercise.highest_recorded_repetitions.repetitions : '—'}</td>
                  <td className="py-2">{exercise.highest_recorded_volume ? `${exercise.highest_recorded_volume.value} kg` : '—'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : <div className="mt-4"><EmptyChart label="No recorded bests yet in this range." /></div>}
      </Card>
    </section>
  )
}

// --- Coach read-only session review ---
function CoachSessionRow({ session }: { session: CoachSessionSummary }) {
  const [open, setOpen] = useState(false)
  const scope = useAccountQueryScope()
  const detail = useQuery({
    queryKey: [...scope, 'coach-workout-session', session.workout_session_id],
    queryFn: () => api<CoachSessionDetail>(`/coach/workout-sessions/${session.workout_session_id}`),
    enabled: open,
  })
  return (
    <div className="border-b last:border-0">
      <button type="button" onClick={() => setOpen(v => !v)} aria-expanded={open} className="flex w-full items-center justify-between gap-3 py-3 text-left">
        <span>
          <span className="font-medium">{session.workout_name ?? 'Workout'}</span>
          <span className="ml-2 text-xs text-muted">{session.scheduled_date}</span>
        </span>
        <span className="flex items-center gap-2">
          {session.open_safety_report_count > 0 && <Badge tone="risk">{session.open_safety_report_count} safety</Badge>}
          <Badge tone={session.classification === 'completed' ? 'positive' : session.classification === 'safety_skipped' ? 'risk' : 'attention'}>{classificationLabel(session.classification)}</Badge>
        </span>
      </button>
      {open && (
        <div className="pb-4">
          {detail.isLoading ? <LoadingState label="Loading session" /> : detail.error ? <ErrorState description={detail.error.message} onRetry={() => detail.refetch()} /> : detail.data ? (
            <div className="space-y-3 rounded-xl bg-elevated p-4 text-sm">
              <dl className="grid gap-3 sm:grid-cols-3">
                <div><dt className="text-xs text-muted">Status</dt><dd className="font-semibold">{detail.data.status}</dd></div>
                <div><dt className="text-xs text-muted">Duration</dt><dd className="font-semibold">{detail.data.actual_duration_minutes ?? '—'} min</dd></div>
                <div><dt className="text-xs text-muted">Session RPE</dt><dd className="font-semibold">{detail.data.session_rpe ?? '—'}</dd></div>
                <div><dt className="text-xs text-muted">Planned load</dt><dd className="font-semibold">{detail.data.load_summary.planned_session_load ?? 'Unavailable'}</dd></div>
                <div><dt className="text-xs text-muted">Completed load</dt><dd className="font-semibold">{detail.data.load_summary.completed_session_load ?? 'Unavailable'}</dd></div>
                <div><dt className="text-xs text-muted">Volume (kg)</dt><dd className="font-semibold">{detail.data.load_summary.session_volume_kg ?? 'Unavailable'}</dd></div>
              </dl>
              <p className="text-xs text-muted">Comparison: {({ above_planned: 'Above planned', near_planned: 'Near planned', below_planned: 'Below planned', unavailable: 'Unavailable' } as const)[detail.data.planned_vs_completed.state]}</p>
              {detail.data.readiness_context && (
                <p className="text-xs text-muted">Readiness at start: {detail.data.readiness_context.available ? `${detail.data.readiness_context.readiness_score} (${detail.data.readiness_context.readiness_state})${detail.data.readiness_context.is_stale ? ' · stale' : ''}, source ${detail.data.readiness_context.source_local_date}` : 'Unavailable'}</p>
              )}
              {detail.data.safety_reports.length > 0 && (
                <StatusNotice tone="risk" title={`${detail.data.safety_reports.length} safety report${detail.data.safety_reports.length > 1 ? 's' : ''}`}>Read-only. Review and resolve safety reports from the Safety page.</StatusNotice>
              )}
              <p className="text-xs text-muted">This review is read-only. Completed data and immutable summaries cannot be edited.</p>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}

export function CoachWorkoutIntelligence({ traineeId }: { traineeId: string }) {
  const scope = useAccountQueryScope()
  const basePath = `/coach/trainees/${traineeId}`
  const sessions = useQuery({ queryKey: [...scope, 'coach-workout-sessions', traineeId], queryFn: () => api<CoachSessionList>(`${basePath}/workout-sessions?days=30`) })
  const openSafety = (sessions.data?.sessions ?? []).reduce((sum, s) => sum + s.open_safety_report_count, 0)
  return (
    <div className="space-y-5">
      {openSafety > 0 && <StatusNotice tone="risk" title={`${openSafety} open safety report${openSafety > 1 ? 's' : ''} across recent workouts`}>Safety information is surfaced before other analytics. Resolve reports from the Safety page.</StatusNotice>}
      <WorkoutIntelligencePanel basePath={basePath} keyPrefix="coach-workout-intel" />
      <Card>
        <h3 className="font-semibold">Recent workout sessions</h3>
        <p className="mt-1 text-xs text-muted">Read-only execution review. Expand a session for load, readiness, and safety context.</p>
        {sessions.isLoading ? <div className="mt-4"><LoadingState label="Loading sessions" /></div> : sessions.error ? <div className="mt-4"><ErrorState description={sessions.error.message} onRetry={() => sessions.refetch()} /></div> : sessions.data?.sessions.length ? (
          <div className="mt-3">{sessions.data.sessions.map(session => <CoachSessionRow key={session.workout_session_id} session={session} />)}</div>
        ) : <div className="mt-4"><EmptyChart label="No workout sessions in this range." /></div>}
      </Card>
    </div>
  )
}
