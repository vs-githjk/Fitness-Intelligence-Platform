import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, CheckCircle2, ShieldAlert } from 'lucide-react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { useAccountQueryScope, useAuth } from '../auth'
import { AppShell } from '../components/AppShell'
import { Badge, Button, Card, EmptyState, ErrorState, Field, LoadingState, PageHeader, SelectInput, StatusNotice, TextArea } from '../components/ui'
import { CoachWorkoutSafetyReport, SafetyReportStatus } from '../types'

const title = (value: string) => value.replaceAll('_', ' ').replace(/^./, letter => letter.toUpperCase())
const dateTime = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

export function CoachSafetyReportsPage() {
  const { reportId } = useParams()
  return reportId ? <SafetyReportDetail reportId={reportId} /> : <SafetyReportQueue />
}

function SafetyReportQueue() {
  const scope = useAccountQueryScope()
  const [status, setStatus] = useState<'all' | SafetyReportStatus>('open')
  const query = useQuery({ queryKey: [...scope, 'coach-safety-reports', status], queryFn: () => api<CoachWorkoutSafetyReport[]>(`/coach/safety-reports${status === 'all' ? '' : `?status=${status}`}`) })
  return <AppShell><div className="space-y-6"><PageHeader eyebrow="Workout safety" title="Safety report queue" description="Review trainee-submitted workout safety reports. This queue is not continuously monitored and does not provide medical diagnosis." /><Card><Field label="Report status">{({ id }) => <SelectInput id={id} value={status} onChange={event => setStatus(event.target.value as 'all' | SafetyReportStatus)}><option value="open">Open</option><option value="acknowledged">Acknowledged</option><option value="resolved">Resolved</option><option value="all">All reports</option></SelectInput>}</Field></Card>{query.isLoading ? <LoadingState label="Loading safety reports" /> : query.error ? <ErrorState title="Safety reports unavailable" description={query.error.message} onRetry={() => query.refetch()} /> : query.data?.length ? <div className="grid gap-4 xl:grid-cols-2">{query.data.map(report => <Link key={report.id} to={`/coach/safety-reports/${report.id}`} className="rounded-2xl focus:outline-none focus:ring-2 focus:ring-primary"><Card as="article" className="h-full transition-colors hover:border-primary"><div className="flex flex-wrap items-center gap-2"><Badge tone={report.severity === 'severe' ? 'critical' : 'attention'}>{title(report.category)}</Badge><Badge tone={report.status === 'resolved' ? 'positive' : report.status === 'acknowledged' ? 'info' : 'attention'}>{report.status}</Badge></div><h2 className="mt-3 text-xl font-semibold">{report.trainee_name}</h2><p className="mt-1 text-sm text-secondary">{report.workout_name}{report.exercise_name ? ` · ${report.exercise_name}` : ''}</p><p className="mt-3 text-xs text-muted">Reported {dateTime(report.occurred_at)}</p>{report.note && <p className="mt-3 line-clamp-2 text-sm leading-6">{report.note}</p>}</Card></Link>)}</div> : <EmptyState icon={ShieldAlert} title="No reports in this view" description="Choose another status or return later." />}</div></AppShell>
}

function SafetyReportDetail({ reportId }: { reportId: string }) {
  const { user } = useAuth()
  const scope = useAccountQueryScope()
  const cache = useQueryClient()
  const [note, setNote] = useState('')
  const [message, setMessage] = useState('')
  const query = useQuery({ queryKey: [...scope, 'coach-safety-report', reportId], queryFn: () => api<CoachWorkoutSafetyReport>(`/coach/safety-reports/${reportId}`) })
  const review = useMutation({
    mutationFn: (action: 'acknowledge' | 'resolve') => api<CoachWorkoutSafetyReport>(`/coach/safety-reports/${reportId}/${action}`, { method: 'POST', body: JSON.stringify({ note: note || null }) }),
    onSuccess: value => { cache.setQueryData([...scope, 'coach-safety-report', reportId], value); void cache.invalidateQueries({ queryKey: [...scope, 'coach-safety-reports'] }); setNote(''); setMessage(`Report ${value.status}.`) },
    onError: caught => setMessage(caught instanceof Error ? caught.message : 'The report review could not be saved.'),
  })
  if (query.isLoading) return <AppShell><LoadingState label="Loading safety report" /></AppShell>
  if (query.error || !query.data) return <AppShell><ErrorState title="Safety report unavailable" description={query.error?.message ?? 'Report not found'} onRetry={() => query.refetch()} /></AppShell>
  const report = query.data
  return <AppShell><div className="mx-auto max-w-4xl space-y-5"><Link to="/coach/safety-reports" className="inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-primary"><ArrowLeft aria-hidden="true" className="size-4" />Back to safety queue</Link><PageHeader eyebrow="Workout safety report" title={report.trainee_name} description={`${report.workout_name} · ${report.scheduled_date}`} /><StatusNotice tone="attention" title="Coach review context">Safety reports are not monitored continuously. The platform does not diagnose medical conditions. Use professional judgment and appropriate escalation.</StatusNotice><Card><div className="flex flex-wrap items-center gap-2"><Badge tone={report.severity === 'severe' ? 'critical' : 'attention'}>{title(report.category)}</Badge><Badge tone={report.status === 'resolved' ? 'positive' : report.status === 'acknowledged' ? 'info' : 'attention'}>{report.status}</Badge><Badge tone="neutral">{report.severity}</Badge></div><dl className="mt-5 grid gap-4 sm:grid-cols-2"><Metric label="Trainee" value={`${report.trainee_name} · ${report.trainee_email}`} /><Metric label="Reported" value={dateTime(report.occurred_at)} /><Metric label="Exercise" value={report.exercise_name ?? 'Session-level report'} /><Metric label="Activity stopped" value={report.activity_stopped ? 'Yes' : 'No'} /><Metric label="Session status" value={title(report.session_status)} /><Metric label="Exercise status" value={report.exercise_status ? title(report.exercise_status) : 'Not linked'} /></dl>{report.note && <div className="mt-5 rounded-xl bg-elevated p-4"><p className="text-xs font-bold uppercase tracking-wider text-muted">Trainee note</p><p className="mt-2 text-sm leading-6">{report.note}</p></div>}<p className="mt-4 text-sm leading-6 text-secondary">{report.guidance}</p></Card><Card><h2 className="text-xl font-semibold">Review history</h2>{report.reviews.length ? <ol className="mt-4 space-y-3">{report.reviews.map(item => <li key={item.id} className="rounded-xl border p-3"><div className="flex items-center justify-between gap-3"><Badge tone={item.action === 'resolved' ? 'positive' : 'info'}>{item.action}</Badge><span className="text-xs text-muted">{dateTime(item.created_at)}</span></div>{item.note && <p className="mt-2 text-sm leading-6">{item.note}</p>}</li>)}</ol> : <p className="mt-3 text-sm text-muted">No coach reviews yet.</p>}</Card><Card><h2 className="text-xl font-semibold">Add coach review</h2><Field label="Internal coach note" optional help="This note appears only in the coach review history.">{({ id, describedBy }) => <TextArea id={id} aria-describedby={describedBy} maxLength={500} value={note} disabled={Boolean(user?.is_demo) || review.isPending || report.status === 'resolved'} onChange={event => setNote(event.target.value)} />}</Field>{message && <p role="status" className="mb-3 text-sm font-semibold text-secondary">{message}</p>}<div className="flex flex-wrap gap-3"><Button variant="secondary" disabled={Boolean(user?.is_demo) || report.status !== 'open'} loading={review.isPending} onClick={() => review.mutate('acknowledge')}><CheckCircle2 aria-hidden="true" className="size-4" />Acknowledge</Button><Button disabled={Boolean(user?.is_demo) || report.status === 'resolved'} loading={review.isPending} onClick={() => review.mutate('resolve')}>Resolve report</Button></div>{user?.is_demo && <p className="mt-3 text-xs text-muted">Review actions are disabled in the demo workspace.</p>}</Card></div></AppShell>
}

function Metric({ label, value }: { label: string; value: string }) { return <div><dt className="text-xs text-muted">{label}</dt><dd className="mt-1 font-semibold">{value}</dd></div> }
