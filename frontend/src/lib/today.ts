// Morning Brief "Today" presentation derivations (Experience Cycle 1, Phase D).
//
// Pure functions that turn already-authoritative backend data into presentation
// choices. This layer selects and formats; it is NOT a second scoring engine and
// never derives a band from a raw number — readiness meaning always comes from the
// backend readiness_state.

import { DailyTrends, RiskFlag, ScheduledWorkout, TrainingAssignmentWorkspace } from '../types'

export type AtmosphereBand =
  | 'ready_to_push'
  | 'maintain'
  | 'reduce_intensity'
  | 'recovery_recommended'
  | 'neutral'

export type ReadinessPresentation = { verdict: string; atmosphere: AtmosphereBand }

// The ONE centralized mapping from the backend readiness_state to Morning Brief
// presentation semantics: frozen verdict copy + atmosphere band. No other part of
// Today maps readiness to presentation, so word/atmosphere can never drift apart.
const READINESS_PRESENTATION: Record<string, ReadinessPresentation> = {
  ready_to_push: { verdict: 'Go for it today.', atmosphere: 'ready_to_push' },
  maintain: { verdict: 'Train as planned today.', atmosphere: 'maintain' },
  reduce_intensity: { verdict: 'Ease off a little today.', atmosphere: 'reduce_intensity' },
  recovery_recommended: { verdict: "Let's keep it light today.", atmosphere: 'recovery_recommended' },
}

const FALLBACK_PRESENTATION: ReadinessPresentation = {
  verdict: "Here's your plan for today.",
  atmosphere: 'neutral',
}

export function readinessPresentation(readinessState: string): ReadinessPresentation {
  return READINESS_PRESENTATION[readinessState] ?? FALLBACK_PRESENTATION
}

// Deterministic, conservative reason line keyed on the backend readiness_state.
// Truthful (readiness is driven by recovery and recent load), product voice,
// non-medical, non-judgemental. No causal claims beyond what the state guarantees.
const REASON_LINES: Record<string, string> = {
  ready_to_push: 'Your recovery and recent training are lined up for a strong session.',
  maintain: "You're recovering steadily, so stick with the plan.",
  reduce_intensity: 'A few recovery signals are lower today, so keep the intensity easy.',
  recovery_recommended: 'Your recovery signals are low, so keep today gentle.',
}

const FALLBACK_REASON = 'Based on your latest check-in.'

export function reasonLine(readinessState: string): string {
  return REASON_LINES[readinessState] ?? FALLBACK_REASON
}

const ACTIONABLE_STATUSES: ReadonlyArray<ScheduledWorkout['status']> = ['scheduled', 'in_progress']

// Today's startable workout: an actionable, dated-for-today session with an id.
// Date semantics use the workspace's server-computed local_today, so selection
// never depends on the client clock (avoiding date flake).
export function selectTodayWorkout(
  workspace: TrainingAssignmentWorkspace | undefined,
): ScheduledWorkout | null {
  if (!workspace) return null
  const todays = workspace.scheduled_workouts
    .filter((workout) => workout.scheduled_date === workspace.local_today)
    .sort((a, b) => a.display_order - b.display_order)
  return todays.find((workout) => Boolean(workout.id) && ACTIONABLE_STATUSES.includes(workout.status)) ?? null
}

export function workoutContext(workout: ScheduledWorkout): string | undefined {
  if (workout.program_week_label) return workout.program_week_label
  if (workout.program_week_number) return `Week ${workout.program_week_number}`
  return undefined
}

// Most recent recorded change for a score series, or null when unavailable.
export function scoreTrend(trends: DailyTrends | undefined, seriesKey: string): number | null {
  const series = trends?.series.find((item) => item.key === seriesKey)
  if (!series) return null
  for (let index = series.points.length - 1; index >= 0; index -= 1) {
    const point = series.points[index]
    if (!point.missing && point.difference_from_previous != null) return point.difference_from_previous
  }
  return null
}

const GOING_WELL_SERIES: ReadonlyArray<{ key: string; label: string }> = [
  { key: 'recovery_score', label: 'Recovery' },
  { key: 'readiness_score', label: 'Training readiness' },
  { key: 'activity_score', label: 'Activity' },
  { key: 'nutrition_score', label: 'Nutrition' },
]

// One truthful positive: a score that genuinely rose since the last check-in.
// Returns null when nothing qualifies (positivity is never invented). No streaks.
export function selectGoingWell(trends: DailyTrends | undefined): string | null {
  if (!trends) return null
  for (const { key, label } of GOING_WELL_SERIES) {
    const delta = scoreTrend(trends, key)
    if (delta != null && delta > 0) return `${label} is up since your last check-in.`
  }
  return null
}

const SEVERITY_RANK: Record<string, number> = { urgent: 0, elevated: 1, review: 2, informational: 3 }

function severityRank(severity: string): number {
  return SEVERITY_RANK[severity] ?? Number.MAX_SAFE_INTEGER
}

// Highest-priority concern plus the remaining genuine notes, or null when calm.
export function selectWatch(
  riskFlags: RiskFlag[],
): { primary: RiskFlag; remaining: RiskFlag[] } | null {
  if (!riskFlags.length) return null
  const ordered = [...riskFlags].sort((a, b) => severityRank(a.severity) - severityRank(b.severity))
  return { primary: ordered[0], remaining: ordered.slice(1) }
}
