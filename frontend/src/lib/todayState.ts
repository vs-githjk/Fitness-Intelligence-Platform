// Today state resolution (Experience Cycle 1, Phase E).
//
// One Today screen, many states. This is the single deterministic resolver for
// the *checked-in* body — given the already-fetched training workspace it decides
// which Morning Brief shape the day takes. The page-level gate (loading / error /
// offline / not-checked-in) lives in DailyPages and sits *above* this resolver;
// this layer only runs once we know the trainee has checked in.
//
// It reads the real domain model only (scheduled_workouts + status + local_today +
// current_assignment); it invents no session, no rest reason, and no next-up.

import { ScheduledWorkout, TrainingAssignmentWorkspace } from '../types'
import { selectTodayWorkout } from './today'

const ACTIONABLE_STATUSES: ReadonlyArray<ScheduledWorkout['status']> = ['scheduled', 'in_progress']
const COMPLETED_STATUSES: ReadonlyArray<ScheduledWorkout['status']> = ['completed', 'partial']

// The checked-in Today shape. `plan_only` = checked in with guidance to show but no
// session to launch (no active program, or today's only sessions are skipped/
// cancelled) — the session slot collapses cleanly, guidance is preserved.
export type CheckedInPlan =
  | { kind: 'workout'; workout: ScheduledWorkout }
  | { kind: 'completed'; workout: ScheduledWorkout }
  | { kind: 'rest'; nextUp: ScheduledWorkout | null }
  | { kind: 'plan_only' }

function todaysSessions(workspace: TrainingAssignmentWorkspace): ScheduledWorkout[] {
  return workspace.scheduled_workouts
    .filter((workout) => workout.scheduled_date === workspace.local_today)
    .sort((a, b) => a.display_order - b.display_order)
}

// The next launchable session after today (earliest future actionable one), or null.
export function nextUpWorkout(workspace: TrainingAssignmentWorkspace | undefined): ScheduledWorkout | null {
  if (!workspace) return null
  return (
    workspace.scheduled_workouts
      .filter(
        (workout) =>
          Boolean(workout.id) &&
          workout.scheduled_date > workspace.local_today &&
          ACTIONABLE_STATUSES.includes(workout.status),
      )
      .sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date) || a.display_order - b.display_order)[0] ?? null
  )
}

// True only when the CURRENT program still has a launchable session strictly
// after today — i.e. today falls *within* the program's materialized span. This
// is the rest-day integrity guard: the backend has no rest flag and no COMPLETED
// assignment status (an assignment stays ACTIVE forever after its last workout,
// and `effective_end_date` is null for a live assignment), so "active program +
// empty today" alone cannot tell a genuine mid-program rest day apart from a
// program that has simply run out. The materialized schedule is the authority —
// an empty weekday is a programmed rest day only while real sessions remain
// ahead. Past the last workout we must NOT invent "take today off on purpose".
function hasRemainingProgram(workspace: TrainingAssignmentWorkspace): boolean {
  const currentId = workspace.current_assignment?.id
  if (!currentId) return false
  return workspace.scheduled_workouts.some(
    (workout) =>
      workout.training_assignment_id === currentId &&
      Boolean(workout.id) &&
      workout.scheduled_date > workspace.local_today &&
      ACTIONABLE_STATUSES.includes(workout.status),
  )
}

export function resolveCheckedInPlan(workspace: TrainingAssignmentWorkspace | undefined): CheckedInPlan {
  // No workspace at all (absent, or an optional-query failure) → collapse the
  // session slot rather than fabricate a rest day we cannot substantiate.
  if (!workspace) return { kind: 'plan_only' }

  const workout = selectTodayWorkout(workspace)
  if (workout) return { kind: 'workout', workout }

  const today = todaysSessions(workspace)
  const completed = today.find((session) => COMPLETED_STATUSES.includes(session.status))
  if (completed) return { kind: 'completed', workout: completed }

  // No actionable and no completed session today. An empty schedule is a programmed
  // rest day ONLY while the active program still has sessions ahead of today (see
  // hasRemainingProgram). Anything else — no program, a lapsed/finished program, or
  // a day whose only sessions were skipped/cancelled — collapses to guidance-only
  // rather than claiming a coach-authored rest the domain cannot substantiate.
  if (today.length === 0 && hasRemainingProgram(workspace)) {
    return { kind: 'rest', nextUp: nextUpWorkout(workspace) }
  }
  return { kind: 'plan_only' }
}

const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']

// A deterministic, truthful relative-day phrase for a future scheduled date, e.g.
// "tomorrow" or "on Thursday". Both dates are server-local ISO date strings, so no
// client timezone maths is involved beyond a plain day difference.
export function relativeDay(scheduledDate: string, localToday: string): string {
  const start = Date.parse(`${localToday}T00:00:00Z`)
  const end = Date.parse(`${scheduledDate}T00:00:00Z`)
  if (Number.isNaN(start) || Number.isNaN(end)) return ''
  const days = Math.round((end - start) / 86_400_000)
  if (days <= 0) return ''
  if (days === 1) return 'tomorrow'
  const weekday = WEEKDAYS[new Date(end).getUTCDay()]
  return days < 7 ? `on ${weekday}` : `next ${weekday}`
}
