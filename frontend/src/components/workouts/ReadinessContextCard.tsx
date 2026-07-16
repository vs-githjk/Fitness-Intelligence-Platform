import { AlertTriangle, Gauge } from 'lucide-react'
import { WorkoutReadinessContext } from '../../types'
import { Badge, Card } from '../ui'

export function ReadinessContextCard({ context, compact = false }: { context?: WorkoutReadinessContext | null; compact?: boolean }) {
  if (!context) return null
  const source = context.source_local_date
    ? new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(`${context.source_local_date}T12:00:00`))
    : null
  const state = context.readiness_state?.replaceAll('_', ' ')
  return <Card className={compact ? 'shadow-none' : ''} as="section"><div className="flex items-start justify-between gap-3"><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><Gauge aria-hidden="true" className="size-5" /></span><div><p className="text-xs font-bold uppercase tracking-wider text-primary">Readiness context</p><h2 className="mt-1 text-lg font-semibold">{context.available ? `${context.readiness_score} · ${state}` : 'Readiness unavailable'}</h2></div></div>{context.is_stale ? <Badge tone="attention"><AlertTriangle aria-hidden="true" className="mr-1 size-3" />Stale</Badge> : context.available ? <Badge tone="positive">Fresh</Badge> : <Badge tone="neutral">Unavailable</Badge>}</div><p className="mt-3 text-sm leading-6 text-secondary">{context.guidance}</p>{source && <p className="mt-2 text-xs text-muted">Based on the latest Daily Intelligence snapshot on or before this workout: {source}{context.age_days !== null ? ` · ${context.age_days} day${context.age_days === 1 ? '' : 's'} old` : ''}.</p>}{context.scoring_version && <p className="mt-1 text-xs text-muted">Scoring version: {context.scoring_version}</p>}<p className="mt-2 text-xs font-medium text-muted">Context only — it does not automatically alter the prescribed workout.</p></Card>
}
