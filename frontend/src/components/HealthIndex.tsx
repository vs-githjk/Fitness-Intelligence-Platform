import {
  Activity,
  Apple,
  BedDouble,
  Brain,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Droplets,
  Dumbbell,
  Footprints,
  HeartPulse,
  Target,
  type LucideIcon,
} from 'lucide-react'
import { ComponentScore, HealthIndex, Recommendation, RiskFlag } from '../types'
import { formatDate, titleize } from '../lib/format'
import { Badge, Card, Disclosure, ProgressBar, StatusNotice, toneForSeverity, toneForStatus } from './ui'

const componentIcons: Record<string, LucideIcon> = {
  hydration: Droplets,
  sleep: BedDouble,
  nutrition: Apple,
  stress: Brain,
  cardiovascular: HeartPulse,
  workout_intensity: Dumbbell,
  physical_activity: Activity,
  daily_steps: Footprints,
  goal_alignment: Target,
  assessment_completion: ClipboardCheck,
}

function bandSummary(band: string): string {
  const summaries: Record<string, string> = {
    Elite: 'Your reported baseline is strong across most measured components.',
    Excellent: 'Your baseline shows several strong foundations with focused opportunities to refine.',
    Good: 'Your baseline is broadly positive, with a few clear areas to prioritize next.',
    Average: 'Your baseline identifies practical areas where consistent changes may help.',
    'Needs Improvement': 'Several reported components have room for improvement. Start with the highest-priority actions.',
    'High Risk': 'This product score is low across several configured components. It is not a medical diagnosis.',
  }
  return summaries[band] ?? 'This baseline reflects the information provided during onboarding.'
}

export function HealthIndexSummary({ health, label = 'Assessment baseline' }: { health: HealthIndex; label?: string }) {
  return <Card className="relative overflow-hidden bg-foreground text-white"><div className="absolute inset-y-0 right-0 w-1.5 bg-primary" aria-hidden="true" /><div className="relative"><div className="flex flex-wrap items-center justify-between gap-3"><p className="text-xs font-bold uppercase tracking-[0.16em] text-white/70">{label}</p><Badge tone="info" className="border-white/20 bg-white/10 text-white">{health.band}</Badge></div><div className="mt-8 flex flex-wrap items-end gap-x-4 gap-y-2"><span className="metric-number text-7xl font-bold leading-none sm:text-8xl">{health.overall_score}</span><span className="pb-1.5 text-lg font-medium text-white/60">out of 100</span></div><p className="mt-5 max-w-xl text-base leading-7 text-white/80">{bandSummary(health.band)}</p><div className="mt-7 flex flex-wrap gap-x-5 gap-y-2 text-xs text-white/60"><span className="inline-flex items-center gap-1.5"><CalendarDays aria-hidden="true" className="size-4" />Calculated {formatDate(health.calculated_at)}</span><span>Based on onboarding responses</span></div></div></Card>
}

export function ComponentRow({ component }: { component: ComponentScore }) {
  const Icon = componentIcons[component.key] ?? Activity
  const tone = toneForStatus(component.status)
  return <div className="border-b py-4 last:border-b-0"><div className="flex items-start gap-3"><span className="mt-0.5 grid size-9 shrink-0 place-items-center rounded-xl bg-elevated text-secondary"><Icon aria-hidden="true" className="size-[1.125rem]" /></span><div className="min-w-0 flex-1"><div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="font-semibold">{titleize(component.key)}</h3><p className="mt-0.5 text-xs text-muted">Weight {component.weight}% · contributes {component.weighted_contribution} points</p></div><div className="flex items-center gap-2"><Badge tone={tone}>{titleize(component.status)}</Badge><span className="metric-number text-lg font-bold">{component.normalized_score}</span></div></div><ProgressBar value={component.normalized_score} label={`${titleize(component.key)} score: ${component.normalized_score} out of 100`} tone={tone === 'positive' ? 'positive' : tone === 'risk' || tone === 'critical' ? 'risk' : tone === 'attention' ? 'attention' : 'primary'} className="mt-3" /><p className="mt-2 text-sm leading-6 text-secondary">{component.explanation}</p></div></div></div>
}

export function ComponentBreakdown({ components }: { components: ComponentScore[] }) {
  return <Card><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-[0.14em] text-primary">Score contributors</p><h2 className="mt-1 text-xl font-semibold">How each component contributed</h2></div><p className="text-xs text-muted">Score × weight = contribution</p></div><div className="mt-4">{components.map(component => <ComponentRow key={component.key} component={component} />)}</div></Card>
}

export function RecommendationCard({ recommendation, index }: { recommendation: Recommendation; index: number }) {
  const isHigh = recommendation.priority === 'high'
  return <article className="rounded-xl border bg-surface p-4"><div className="flex items-start gap-3"><span className={`grid size-8 shrink-0 place-items-center rounded-full text-sm font-bold ${isHigh ? 'bg-attention text-white' : 'bg-primary/10 text-primary'}`}>{index + 1}</span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><p className="text-xs font-bold uppercase tracking-wider text-muted">{titleize(recommendation.category)}</p><Badge tone={isHigh ? 'attention' : 'info'}>{titleize(recommendation.priority)} priority</Badge></div><p className="mt-2 text-sm font-medium leading-6 text-foreground">{recommendation.recommended_action}</p><Disclosure summary="Why this is recommended"><p className="text-sm leading-6 text-secondary">Triggered by {titleize(recommendation.trigger)}. This action is based on the structured calculation for your submitted baseline.</p>{recommendation.safety_text && <p className="mt-2 text-xs leading-5 text-muted">{recommendation.safety_text}</p>}</Disclosure></div></div></article>
}

export function RecommendationsPanel({ recommendations }: { recommendations: Recommendation[] }) {
  const sorted = [...recommendations].sort((a, b) => Number(b.priority === 'high') - Number(a.priority === 'high')).slice(0, 4)
  return <Card><div className="flex items-start gap-3"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><Target aria-hidden="true" className="size-5" /></span><div><h2 className="text-xl font-semibold">Priority actions</h2><p className="mt-1 text-sm leading-6 text-secondary">Start with the actions most directly supported by this baseline.</p></div></div>{sorted.length ? <div className="mt-5 space-y-3">{sorted.map((recommendation, index) => <RecommendationCard key={recommendation.key} recommendation={recommendation} index={index} />)}</div> : <div className="mt-5 flex items-center gap-3 rounded-xl bg-[rgb(var(--status-positive-bg))] p-4 text-sm text-positive"><CheckCircle2 aria-hidden="true" className="size-5" />No priority recommendations were generated for this baseline.</div>}</Card>
}

export function RiskAlertCard({ alert }: { alert: RiskFlag }) {
  const tone = toneForSeverity(alert.severity)
  const titlePrefix = alert.severity === 'urgent' ? 'Immediate safety guidance' : alert.severity === 'elevated' ? 'Elevated concern' : alert.severity === 'review' ? 'Coach review suggested' : 'For your information'
  return <StatusNotice tone={tone} title={`${titlePrefix}: ${alert.title}`}><p>{alert.explanation}</p><p className="mt-2 font-semibold text-foreground">Next step: {alert.recommended_action}</p><p className="mt-2 text-xs text-muted">Rule {alert.rule_version} · {formatDate(alert.triggered_at)}</p></StatusNotice>
}

export function RiskPanel({ alerts, coachView = false }: { alerts: RiskFlag[]; coachView?: boolean }) {
  return <Card><h2 className="text-xl font-semibold">Review notices</h2><p className="mt-1 text-sm leading-6 text-secondary">{coachView ? 'Review these reported inputs with the trainee. They are not medical diagnoses.' : 'These notices highlight reported inputs that may deserve attention.'}</p>{alerts.length ? <div className="mt-5 space-y-3">{alerts.map(alert => <RiskAlertCard key={alert.rule_key} alert={alert} />)}</div> : <div className="mt-5 flex items-center gap-3 rounded-xl bg-[rgb(var(--status-positive-bg))] p-4 text-sm text-positive"><CheckCircle2 aria-hidden="true" className="size-5" />No onboarding review rules were triggered.</div>}</Card>
}

export function HealthIndexView({ health, coachView = false }: { health: HealthIndex; coachView?: boolean }) {
  return <div className="space-y-6"><section aria-label="Health Index summary" className="grid gap-6 xl:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]"><HealthIndexSummary health={health} /><RiskPanel alerts={health.risk_flags} coachView={coachView} /></section><section aria-label="Recommendations and contributors" className="grid items-start gap-6 xl:grid-cols-[minmax(20rem,0.75fr)_minmax(0,1.25fr)]"><RecommendationsPanel recommendations={health.recommendations} /><ComponentBreakdown components={health.components} /></section><Card><Disclosure summary="Calculation and missing-data details"><dl className="grid gap-4 text-sm sm:grid-cols-3"><div><dt className="text-muted">Scoring version</dt><dd className="mt-1 font-semibold">{health.scoring_version}</dd></div><div><dt className="text-muted">Calculation date</dt><dd className="mt-1 font-semibold">{formatDate(health.calculated_at)}</dd></div><div><dt className="text-muted">Missing optional fields</dt><dd className="mt-1 font-semibold">{health.missing_fields.length ? health.missing_fields.map(titleize).join(', ') : 'None'}</dd></div></dl><p className="mt-4 text-xs leading-5 text-muted">The Health Index is a deterministic coaching-support score. It is not a medical diagnosis and does not replace qualified medical care.</p></Disclosure></Card></div>
}
