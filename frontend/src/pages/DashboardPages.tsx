import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError } from '../api'
import { ScoreView, Shell, StateCard } from '../components'
import { HealthIndex, TraineeDetail, TraineeSummary } from '../types'

export function TraineeDashboard() {
  const query = useQuery({ queryKey: ['health-current'], queryFn: () => api<HealthIndex>('/health-index/current'), retry: false })
  return <Shell>{query.isLoading ? <StateCard title="Loading baseline">Retrieving your persisted health index…</StateCard> : query.error ? (query.error instanceof ApiError && query.error.status === 404 ? <StateCard title="Your baseline is not ready"><p>Complete onboarding to calculate your explainable Health Index.</p><Link className="btn-primary mt-5" to="/onboarding">Start onboarding</Link></StateCard> : <StateCard title="Could not load dashboard">{query.error.message}</StateCard>) : <><div className="mb-6"><p className="eyebrow">Trainee dashboard</p><h1 className="mt-2 text-3xl font-black">Your baseline, explained</h1><p className="mt-2 text-black/60">A deterministic snapshot based on the onboarding information you supplied.</p></div><ScoreView health={query.data!}/></>}</Shell>
}

export function CoachDashboard() {
  const query = useQuery({ queryKey: ['coach-trainees'], queryFn: () => api<TraineeSummary[]>('/coach/trainees') })
  return <Shell><div className="mb-6"><p className="eyebrow">Coach workspace</p><h1 className="mt-2 text-3xl font-black">Assigned trainees</h1><p className="mt-2 text-black/60">Only active assignments are visible here.</p></div>{query.isLoading ? <StateCard title="Loading roster">Retrieving assigned trainees…</StateCard> : query.error ? <StateCard title="Could not load roster">{query.error.message}</StateCard> : !query.data?.length ? <StateCard title="No assigned trainees">New accepted assignments will appear here.</StateCard> : <div className="grid gap-4">{query.data.map(t => <Link to={`/coach/trainees/${t.trainee_id}`} key={t.trainee_id} className="card grid items-center gap-4 transition hover:-translate-y-0.5 hover:shadow-md sm:grid-cols-[1fr_auto_auto_auto]"><div><h2 className="text-lg font-bold">{t.name}</h2><p className="text-sm text-black/50">{t.email}</p></div><div><p className="text-xs font-bold uppercase text-black/40">Assessment</p><p className="capitalize">{t.assessment_status.replace('_',' ')}</p></div><div><p className="text-xs font-bold uppercase text-black/40">Health index</p><p className="font-bold">{t.current_score ?? '—'} {t.band && <span className="font-normal text-black/50">· {t.band}</span>}</p></div><div className={t.open_alerts ? 'text-coral' : 'text-moss'}><p className="text-xs font-bold uppercase">Open notices</p><p className="text-xl font-black">{t.open_alerts}</p></div></Link>)}</div>}</Shell>
}

export function CoachTraineePage() {
  const { traineeId } = useParams(); const query = useQuery({ queryKey: ['coach-trainee', traineeId], queryFn: () => api<TraineeDetail>(`/coach/trainees/${traineeId}`), enabled: !!traineeId, retry: false })
  return <Shell><Link className="text-sm font-bold text-moss" to="/coach/dashboard">← Back to trainees</Link>{query.isLoading ? <div className="mt-5"><StateCard title="Loading trainee">Retrieving the assigned trainee…</StateCard></div> : query.error ? <div className="mt-5"><StateCard title="Unable to show trainee">{query.error.message}</StateCard></div> : <><div className="my-6"><p className="eyebrow">Assigned trainee</p><h1 className="mt-2 text-3xl font-black">{query.data!.trainee.first_name} {query.data!.trainee.last_name}</h1><p className="mt-1 text-black/50">{query.data!.trainee.email} · Assessment {query.data!.assessment_status}</p></div>{query.data!.health_index ? <ScoreView health={query.data!.health_index} coachView /> : <StateCard title="No baseline yet">This trainee has not submitted the onboarding assessment.</StateCard>}</>}</Shell>
}
