import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity,
  ArrowRight,
  BedDouble,
  CheckCircle2,
  ClipboardCheck,
  Droplets,
  Gauge,
  Pencil,
  Salad,
  Sparkles,
  TrendingUp,
  UserRoundCheck,
} from 'lucide-react'
import { ReactNode, useEffect, useState } from 'react'
import { FieldErrors, useForm, useWatch } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api'
import { useAccountQueryScope, useAuth } from '../auth'
import { AppShell, ProfileMeta } from '../components/AppShell'
import {
  Badge,
  Button,
  Card,
  Chip,
  Disclosure,
  EmptyState,
  ErrorState,
  Field,
  LoadingState,
  PageHeader,
  ProgressBar,
  SegmentedControl,
  SelectInput,
  StatusNotice,
  TextInput,
  toneForSeverity,
} from '../components/ui'
import { formatDate, titleize } from '../lib/format'
import { checkInSchema } from '../lib/dailyValidation'
import {
  DailyCheckIn,
  DailyCheckInData,
  DailyScore,
  DailyTrends,
  CoachRelationship,
  HealthIndex,
  TrendSeries,
} from '../types'

const defaults: DailyCheckInData = {
  sleep_hours: 7.5,
  sleep_quality: 3,
  wake_refreshed: false,
  soreness: 0,
  fatigue: 0,
  stress: 0,
  steps: 0,
  exercised: false,
  exercise_minutes: null,
  session_rpe: null,
  activity_types: [],
  water_liters: 0,
  calories_consumed: null,
  protein_grams: null,
  nutrition_adherence: null,
  overall_feeling: 'okay',
  note: null,
}
const activityOptions = ['walking', 'running', 'cycling', 'swimming', 'strength_training', 'yoga', 'sports', 'other']

function isMissing(error: unknown): boolean { return error instanceof ApiError && error.status === 404 }
function localDateLabel(value: string): string { return formatDate(`${value}T12:00:00`) }
function readinessTone(state: string) { return state === 'ready_to_push' ? 'positive' as const : state === 'maintain' ? 'info' as const : state === 'reduce_intensity' ? 'attention' as const : 'risk' as const }

function DailyMetric({ label, value, detail, icon: Icon, tone = 'primary' }: { label: string; value: string | number; detail: string; icon: typeof Activity; tone?: 'primary' | 'positive' | 'attention' | 'risk' }) {
  return <Card><div className="flex items-start justify-between gap-3"><div><p className="text-sm font-semibold text-secondary">{label}</p><p className="metric-number mt-2 text-3xl font-bold">{value}</p><p className="mt-1 text-xs text-muted">{detail}</p></div><span className={`grid size-10 place-items-center rounded-xl ${tone === 'positive' ? 'bg-[rgb(var(--status-positive-bg))] text-positive' : tone === 'attention' ? 'bg-[rgb(var(--status-attention-bg))] text-attention' : tone === 'risk' ? 'bg-[rgb(var(--status-risk-bg))] text-risk' : 'bg-primary/10 text-primary'}`}><Icon aria-hidden="true" className="size-5" /></span></div></Card>
}

function initials(name?: string | null): string {
  const parts = name?.trim().split(/\s+/).filter(Boolean) ?? []
  return parts.length ? parts.slice(0, 2).map(part => part[0]).join('').toUpperCase() : 'C'
}

export function CoachRelationshipCard({ relationship, loading = false, error = false, demo = false }: { relationship?: CoachRelationship; loading?: boolean; error?: boolean; demo?: boolean }) {
  if (loading) return <Card as="section" aria-labelledby="coach-relationship-heading" className="p-4"><h2 id="coach-relationship-heading" className="font-semibold">Your coach</h2><p className="mt-1 text-sm text-muted" role="status">Loading coach details…</p></Card>
  if (error) return <Card as="section" aria-labelledby="coach-relationship-heading" className="p-4"><h2 id="coach-relationship-heading" className="font-semibold">Your coach</h2><p className="mt-1 text-sm text-muted">Coach details are temporarily unavailable.</p></Card>

  const active = relationship?.assignment_status === 'active'
  if (!active) {
    const inactive = relationship?.assignment_status && relationship.assignment_status !== 'unassigned'
    return <Card as="section" aria-labelledby="coach-relationship-heading" className="p-4"><div className="flex min-w-0 items-center gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-full bg-primary/10 text-primary"><UserRoundCheck aria-hidden="true" className="size-5" /></span><div className="min-w-0"><h2 id="coach-relationship-heading" className="font-semibold">Your coach</h2><p className="mt-0.5 text-sm text-muted">{inactive ? 'Your previous coach relationship is no longer active.' : 'No coach is currently assigned.'}</p></div></div></Card>
  }

  const name = relationship.coach_name?.trim() || 'Assigned coach'
  return <Card as="section" aria-labelledby="coach-relationship-heading" className="p-4"><div className="flex min-w-0 flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div className="flex min-w-0 items-center gap-3"><span aria-hidden="true" className="grid size-10 shrink-0 place-items-center rounded-full bg-primary/10 text-sm font-bold text-primary">{initials(relationship.coach_name)}</span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><h2 id="coach-relationship-heading" className="font-semibold">{demo ? 'Synthetic demo coach' : 'Your coach'}</h2><Badge tone={demo ? 'info' : 'positive'}>{demo ? 'Demo' : 'Connected'}</Badge></div><p className="mt-0.5 truncate text-sm font-medium">{name}</p>{relationship.coach_email && <a href={`mailto:${relationship.coach_email}`} aria-label={`Email ${name} outside FitIntel 360`} className="block break-all text-sm text-primary underline-offset-4 hover:underline">{relationship.coach_email}</a>}</div></div><p className="max-w-md text-xs leading-5 text-muted sm:text-right">{demo ? 'This is sample information from the read-only demo workspace.' : 'Connected through your current coaching assignment.'}</p></div></Card>
}

export function TodayPage() {
  const { user } = useAuth()
  const scope = useAccountQueryScope()
  const checkIn = useQuery({ queryKey: [...scope, 'daily-check-in-today'], queryFn: () => api<DailyCheckIn>('/check-ins/today'), retry: false })
  const score = useQuery({ queryKey: [...scope, 'daily-score-today'], queryFn: () => api<DailyScore>('/daily-scores/today'), retry: false })
  const baseline = useQuery({ queryKey: [...scope, 'health-current'], queryFn: () => api<HealthIndex>('/health-index/current'), retry: false })
  const coach = useQuery({ queryKey: [...scope, 'trainee-coach'], queryFn: () => api<CoachRelationship>('/trainee/coach'), retry: false })
  if (checkIn.isLoading || score.isLoading || baseline.isLoading) return <AppShell><LoadingState label="Loading today's fitness intelligence" /></AppShell>
  if (checkIn.error && !isMissing(checkIn.error)) return <AppShell><ErrorState description={checkIn.error.message} onRetry={() => checkIn.refetch()} /></AppShell>
  const complete = Boolean(checkIn.data && score.data)
  return <AppShell><div className="space-y-8"><PageHeader eyebrow="Today" title={complete ? `Your state for ${localDateLabel(checkIn.data!.local_date)}` : 'Check in with your day'} description="A one-to-two minute reflection turns today’s recovery, movement, and compliance into explainable coaching signals." action={<ProfileMeta role="trainee" />} /><CoachRelationshipCard relationship={coach.data} loading={coach.isLoading} error={Boolean(coach.error)} demo={Boolean(user?.is_demo)} />{!complete ? <EmptyState icon={ClipboardCheck} title="No check-in yet today" description="Your daily scores remain unavailable until you submit real information. Missing data is never displayed as zero." action={<Link to="/trainee/check-in" className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-white">Complete today’s check-in<ArrowRight aria-hidden="true" className="size-4" /></Link>} /> : <><div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border bg-surface p-4"><div className="flex items-center gap-3"><span className="grid size-10 place-items-center rounded-xl bg-[rgb(var(--status-positive-bg))] text-positive"><CheckCircle2 aria-hidden="true" className="size-5" /></span><div><p className="font-semibold">Today’s check-in is complete</p><p className="text-sm text-muted">You can edit it until your local day changes.</p></div></div><Link to="/trainee/check-in" className="inline-flex min-h-11 items-center gap-2 rounded-xl border px-4 text-sm font-semibold text-primary"><Pencil aria-hidden="true" className="size-4" />Edit today</Link></div><section aria-label="Daily score summary" className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><DailyMetric label="Recovery" value={score.data!.recovery_score} detail="Sleep, fatigue, soreness, stress" icon={BedDouble} tone={score.data!.recovery_score >= 80 ? 'positive' : score.data!.recovery_score >= 60 ? 'attention' : 'risk'} /><DailyMetric label="Training readiness" value={score.data!.readiness_score} detail={titleize(score.data!.readiness_state)} icon={Gauge} tone={score.data!.readiness_score >= 80 ? 'positive' : score.data!.readiness_score >= 60 ? 'attention' : 'risk'} /><DailyMetric label="Activity" value={score.data!.activity_score} detail="Steps and capped exercise credit" icon={Activity} /><DailyMetric label="Nutrition" value={score.data!.nutrition_score ?? '—'} detail={score.data!.nutrition_score == null ? 'Insufficient configured targets' : 'Available inputs reweighted'} icon={Salad} /></section><StatusNotice tone={readinessTone(score.data!.readiness_state)} title={titleize(score.data!.readiness_state)}>This state is practical coaching guidance based on today’s inputs and recent load. It is not medical clearance or injury prediction.</StatusNotice>{score.data!.risk_flags.length > 0 && <section aria-labelledby="daily-alerts"><h2 id="daily-alerts" className="mb-3 text-xl font-semibold">Current review signals</h2><div className="space-y-3">{score.data!.risk_flags.map(alert => <StatusNotice key={alert.rule_key} tone={toneForSeverity(alert.severity)} title={alert.title}>{alert.explanation}<span className="mt-2 block font-medium">Next action: {alert.recommended_action}</span></StatusNotice>)}</div></section>}<section aria-labelledby="daily-recommendations"><h2 id="daily-recommendations" className="mb-3 text-xl font-semibold">Recommended next actions</h2><div className="grid gap-3 lg:grid-cols-2">{score.data!.recommendations.map(item => <Card key={item.key}><div className="flex items-center justify-between gap-3"><Badge tone={item.priority === 'high' ? 'attention' : 'info'}>{titleize(item.category)}</Badge><span className="text-xs text-muted">{titleize(item.priority)} priority</span></div><p className="mt-3 text-sm font-medium leading-6">{item.recommended_action}</p>{item.safety_text && <p className="mt-2 text-xs leading-5 text-muted">{item.safety_text}</p>}</Card>)}</div></section><Card><Disclosure summary="How today’s scores were calculated"><div className="space-y-4">{score.data!.components.map(component => <div key={component.key} className="border-b pb-4 last:border-0"><div className="flex items-center justify-between gap-3"><p className="font-semibold">{titleize(component.key)}</p><span className="metric-number text-sm font-bold">{component.missing ? 'Unavailable' : component.normalized_score}</span></div>{!component.missing && <ProgressBar value={component.normalized_score} label={`${titleize(component.key)} ${component.normalized_score} of 100`} className="mt-2" />}<p className="mt-2 text-xs leading-5 text-muted">{component.explanation}</p></div>)}</div></Disclosure></Card></>}{baseline.data ? <Card><div className="flex items-center justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wider text-primary">Baseline reference</p><h2 className="mt-1 text-xl font-semibold">Health Index {baseline.data.overall_score}</h2><p className="mt-1 text-sm text-secondary">Your onboarding baseline remains separate and is never overwritten by daily check-ins.</p></div><Badge tone="neutral">{baseline.data.band}</Badge></div></Card> : !isMissing(baseline.error) && baseline.error ? <StatusNotice tone="info" title="Baseline temporarily unavailable">Daily information remains available independently.</StatusNotice> : null}</div></AppShell>
}

function NumberField({ name, label, unit, min, max, optional, register, errors }: { name: keyof DailyCheckInData; label: string; unit?: string; min: number; max: number; optional?: boolean; register: ReturnType<typeof useForm<DailyCheckInData>>['register']; errors: FieldErrors<DailyCheckInData> }) {
  const message = errors[name]?.message as string | undefined
  return <Field id={name} label={label} optional={optional} error={message}>{({ id, describedBy, invalid }) => <div className="relative"><TextInput id={id} type="number" inputMode="decimal" step="any" min={min} max={max} {...register(name)} aria-describedby={describedBy} aria-invalid={invalid} className={unit ? 'pr-20' : ''} />{unit && <span className="pointer-events-none absolute bottom-3 right-3 text-sm text-muted">{unit}</span>}</div>}</Field>
}

function FormSection({ title, description, icon: Icon, children }: { title: string; description: string; icon: typeof Activity; children: ReactNode }) {
  return <Card><div className="flex gap-3 border-b pb-4"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><Icon aria-hidden="true" className="size-5" /></span><div><h2 className="text-xl font-semibold">{title}</h2><p className="mt-1 text-sm text-muted">{description}</p></div></div><div className="mt-6">{children}</div></Card>
}

export function CheckInPage() {
  const queryClient = useQueryClient(); const [message, setMessage] = useState(''); const [apiError, setApiError] = useState('')
  const scope = useAccountQueryScope()
  const existing = useQuery({ queryKey: [...scope, 'daily-check-in-today'], queryFn: () => api<DailyCheckIn>('/check-ins/today'), retry: false })
  const form = useForm<DailyCheckInData>({ resolver: zodResolver(checkInSchema), defaultValues: defaults, mode: 'onBlur' })
  const { register, control, setValue, reset, handleSubmit, formState: { errors } } = form
  const values = useWatch({ control }) as DailyCheckInData
  useEffect(() => { if (existing.data) reset({ ...defaults, ...existing.data }) }, [existing.data, reset])
  const mutation = useMutation({ mutationFn: (data: DailyCheckInData) => api<DailyCheckIn>('/check-ins/today', { method: 'PUT', body: JSON.stringify(data) }), onSuccess: async () => { setApiError(''); setMessage(existing.data ? 'Today’s check-in was updated.' : 'Today’s check-in was submitted and scored.'); await Promise.all([queryClient.invalidateQueries({ queryKey: [...scope, 'daily-check-in-today'] }), queryClient.invalidateQueries({ queryKey: [...scope, 'daily-score-today'] }), queryClient.invalidateQueries({ queryKey: [...scope, 'daily-trends'] })]); window.scrollTo({ top: 0, behavior: 'smooth' }) }, onError: (error) => setApiError(error.message) })
  if (existing.isLoading) return <AppShell><LoadingState label="Loading today's check-in" /></AppShell>
  if (existing.error && !isMissing(existing.error)) return <AppShell><ErrorState description={existing.error.message} onRetry={() => existing.refetch()} /></AppShell>
  const selectedActivities = values.activity_types ?? []
  return <AppShell><form onSubmit={handleSubmit(data => mutation.mutate(data))} className="mx-auto max-w-4xl space-y-6"><PageHeader eyebrow="Daily check-in" title={existing.data ? 'Edit today’s check-in' : 'How are you doing today?'} description="One short form, saved atomically. Past check-ins remain read-only and missing optional values are never invented." action={<Badge tone={existing.data ? 'positive' : 'neutral'}>{existing.data ? 'Submitted today' : 'Not submitted'}</Badge>} />{message && <StatusNotice tone="positive" title="Check-in saved">{message}<Link to="/trainee/today" className="mt-2 inline-flex items-center gap-1 font-semibold text-primary">View today’s scores<ArrowRight aria-hidden="true" className="size-4" /></Link></StatusNotice>}{apiError && <StatusNotice tone="risk" title="We could not save your check-in">{apiError} Your valid entries remain on this page; try again.</StatusNotice>}<FormSection title="Sleep and recovery" description="Reflect on the previous night and how your body feels now." icon={BedDouble}><div className="grid gap-5 sm:grid-cols-2"><NumberField name="sleep_hours" label="Sleep duration" unit="hours" min={0} max={16} register={register} errors={errors} /><NumberField name="sleep_quality" label="Sleep quality" unit="1–5" min={1} max={5} register={register} errors={errors} /><NumberField name="soreness" label="Soreness" unit="0–10" min={0} max={10} register={register} errors={errors} /><NumberField name="fatigue" label="Fatigue" unit="0–10" min={0} max={10} register={register} errors={errors} /><NumberField name="stress" label="Stress" unit="0–10" min={0} max={10} register={register} errors={errors} /><SegmentedControl label="Did you wake refreshed?" value={String(values.wake_refreshed)} options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} onChange={value => setValue('wake_refreshed', value === 'true', { shouldDirty: true })} /></div></FormSection><FormSection title="Movement and training" description="Exercise volume is capped in scoring; more is not always better." icon={Activity}><div className="grid gap-5 sm:grid-cols-2"><NumberField name="steps" label="Steps" unit="steps" min={0} max={100000} register={register} errors={errors} /><SegmentedControl label="Did you exercise?" value={String(values.exercised)} options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} onChange={value => setValue('exercised', value === 'true', { shouldDirty: true, shouldValidate: true })} /></div>{values.exercised && <div className="mt-6 space-y-5"><div className="grid gap-5 sm:grid-cols-2"><NumberField name="exercise_minutes" label="Exercise duration" unit="minutes" min={1} max={600} register={register} errors={errors} /><NumberField name="session_rpe" label="Session RPE" unit="0–10" min={0} max={10} register={register} errors={errors} /></div><fieldset><legend className="text-sm font-semibold">Activity types</legend><div className="mt-3 flex flex-wrap gap-2">{activityOptions.map(item => <Chip key={item} selected={selectedActivities.includes(item)} onClick={() => setValue('activity_types', selectedActivities.includes(item) ? selectedActivities.filter(value => value !== item) : [...selectedActivities, item], { shouldDirty: true })}>{titleize(item)}</Chip>)}</div></fieldset></div>}</FormSection><FormSection title="Nutrition and hydration" description="Optional nutrition values are scored only when real configured targets exist." icon={Droplets}><div className="grid gap-5 sm:grid-cols-2"><NumberField name="water_liters" label="Water intake" unit="liters" min={0} max={12} register={register} errors={errors} /><NumberField name="calories_consumed" label="Calories consumed" unit="kcal" min={0} max={10000} optional register={register} errors={errors} /><NumberField name="protein_grams" label="Protein consumed" unit="grams" min={0} max={500} optional register={register} errors={errors} /><NumberField name="nutrition_adherence" label="Nutrition-plan adherence" unit="0–100%" min={0} max={100} optional register={register} errors={errors} /></div></FormSection><FormSection title="Overall feeling" description="Keep notes short and avoid unnecessary medical details." icon={Sparkles}><div className="grid gap-5 sm:grid-cols-2"><Field id="overall_feeling" label="How do you feel overall?" error={errors.overall_feeling?.message}>{({ id, describedBy, invalid }) => <SelectInput id={id} {...register('overall_feeling')} aria-describedby={describedBy} aria-invalid={invalid}><option value="very_poor">Very poor</option><option value="poor">Poor</option><option value="okay">Okay</option><option value="good">Good</option><option value="excellent">Excellent</option></SelectInput>}</Field><Field id="note" label="Short note" optional help={`${values.note?.length ?? 0} of 500 characters`} error={errors.note?.message}>{({ id, describedBy, invalid }) => <textarea id={id} maxLength={500} rows={4} {...register('note')} aria-describedby={describedBy} aria-invalid={invalid} className="control mt-1.5 w-full py-3" />}</Field></div></FormSection><Card className="sticky bottom-20 z-10 flex flex-col gap-3 bg-surface/95 backdrop-blur sm:flex-row sm:items-center sm:justify-between lg:bottom-4"><div><p className="font-semibold">{existing.data ? 'Update today only' : 'Submit and calculate'}</p><p className="text-xs text-muted">Scores are deterministic and use versioned rules.</p></div><Button type="submit" loading={mutation.isPending} className="sm:min-w-52">{existing.data ? 'Update today’s check-in' : 'Submit today’s check-in'}</Button></Card></form></AppShell>
}

export function TrendChart({ series }: { series: TrendSeries }) {
  const recorded = series.points.filter(point => point.value != null)
  if (!recorded.length) return <div className="rounded-xl border border-dashed p-6 text-center text-sm text-muted">No recorded values in this range.</div>
  const values = recorded.map(point => point.value as number); const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1
  const coords = series.points.map((point, index) => ({ ...point, x: series.points.length === 1 ? 50 : index / (series.points.length - 1) * 100, y: point.value == null ? null : 86 - ((point.value - min) / range) * 68 }))
  const segments: string[] = []; let current = ''
  coords.forEach(point => { if (point.y == null) { if (current) segments.push(current); current = '' } else current += `${current ? ' L' : 'M'} ${point.x} ${point.y}` }); if (current) segments.push(current)
  return <div><svg viewBox="0 0 100 100" role="img" aria-label={`${series.label} trend with ${recorded.length} recorded values`} className="h-44 w-full overflow-visible"><line x1="0" y1="86" x2="100" y2="86" stroke="rgb(var(--color-border))" strokeWidth="1" />{segments.map((path, index) => <path key={index} d={path} fill="none" stroke="rgb(var(--color-primary))" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />)}{coords.filter(point => point.y != null).map(point => <circle key={point.date} cx={point.x} cy={point.y!} r="2" fill="rgb(var(--color-primary))"><title>{localDateLabel(point.date)}: {point.value} {series.unit}</title></circle>)}</svg><div className="flex justify-between text-xs text-muted"><span>{localDateLabel(series.points[0].date)}</span><span>{localDateLabel(series.points.at(-1)!.date)}</span></div></div>
}

export function ProgressPage() {
  const [days, setDays] = useState('7')
  const scope = useAccountQueryScope()
  const trends = useQuery({ queryKey: [...scope, 'daily-trends', days], queryFn: () => api<DailyTrends>(`/daily-scores/trends?days=${days}`) })
  if (trends.isLoading) return <AppShell><LoadingState label="Loading progress trends" /></AppShell>
  if (trends.error) return <AppShell><ErrorState description={trends.error.message} onRetry={() => trends.refetch()} /></AppShell>
  const data = trends.data!
  return <AppShell><div className="space-y-7"><PageHeader eyebrow="Progress" title="Longitudinal fitness intelligence" description={`Real recorded values in ${data.timezone}. Missing local dates remain gaps rather than becoming fake zeroes.`} action={<div className="w-56"><SegmentedControl label="Trend range" value={days} options={[{ value: '7', label: '7 days' }, { value: '30', label: '30 days' }]} onChange={setDays} /></div>} />{data.series.every(series => series.points.every(point => point.missing)) ? <EmptyState icon={TrendingUp} title="No trend data yet" description="Complete a daily check-in to begin building real historical trends." action={<Link to="/trainee/check-in" className="inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-white">Complete a check-in</Link>} /> : <div className="grid gap-5 xl:grid-cols-2">{data.series.map(series => <Card key={series.key}><div className="flex items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-primary">{series.unit}</p><h2 className="mt-1 text-xl font-semibold">{series.label}</h2></div><Badge>{series.points.filter(point => !point.missing).length} recorded</Badge></div><div className="mt-5"><TrendChart series={series} /></div><Disclosure summary="Accessible data table"><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead><tr className="border-b text-xs uppercase text-muted"><th className="py-2">Local date</th><th className="py-2">Value</th><th className="py-2">Change</th></tr></thead><tbody>{series.points.map(point => <tr key={point.date} className="border-b last:border-0"><td className="py-2">{localDateLabel(point.date)}</td><td className="py-2">{point.missing ? 'Missing' : `${point.value} ${series.unit}`}</td><td className="py-2">{point.difference_from_previous == null ? '—' : `${point.difference_from_previous > 0 ? '+' : ''}${point.difference_from_previous}`}</td></tr>)}</tbody></table></div></Disclosure></Card>)}</div>}<StatusNotice tone="info" title="Baseline and daily trends remain separate">Daily observations do not recalculate or overwrite your onboarding Health Index.</StatusNotice></div></AppShell>
}
