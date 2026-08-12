import { describe, expect, it } from 'vitest'
import { ScheduledWorkout, TrainingAssignment, TrainingAssignmentWorkspace } from '../types'
import { nextUpWorkout, relativeDay, resolveCheckedInPlan } from './todayState'

const TODAY = '2026-03-15'

function workout(overrides: Partial<ScheduledWorkout>): ScheduledWorkout {
  return {
    id: 'w1',
    workout_session_id: null,
    training_assignment_id: 'a1',
    workout_template_version_id: 'tv1',
    scheduled_date: TODAY,
    program_week_number: 3,
    program_week_label: 'Week 3',
    is_deload: false,
    weekday: 'monday',
    display_order: 0,
    required: true,
    planned_duration_minutes: 50,
    target_session_rpe: 7,
    trainee_instructions: null,
    status: 'scheduled',
    workout_template_version: {
      id: 'tv1',
      workout_template_id: 't1',
      version_number: 1,
      name: 'Lower Body Strength',
      goal_tags: [],
      estimated_duration_minutes: 50,
      target_session_rpe: 7,
      exercise_count: 5,
    },
    readiness_context: null,
    ...overrides,
  } as ScheduledWorkout
}

const assignment = { id: 'a1', program_name: 'Base', status: 'active' } as unknown as TrainingAssignment

function workspace(workouts: ScheduledWorkout[], current: TrainingAssignment | null = assignment): TrainingAssignmentWorkspace {
  return {
    timezone: 'UTC',
    local_today: TODAY,
    current_assignment: current,
    upcoming_assignment: null,
    assignment_history: [],
    history_events: [],
    scheduled_workouts: workouts,
  }
}

describe('resolveCheckedInPlan', () => {
  it('returns the actionable today workout, preferring it over a completed one', () => {
    const plan = resolveCheckedInPlan(
      workspace([workout({ id: 'done', status: 'completed', display_order: 0 }), workout({ id: 'go', status: 'scheduled', display_order: 1 })]),
    )
    expect(plan.kind).toBe('workout')
    expect(plan.kind === 'workout' && plan.workout.id).toBe('go')
  })

  it('returns completed when today has only a finished session (completed or partial)', () => {
    expect(resolveCheckedInPlan(workspace([workout({ status: 'completed' })])).kind).toBe('completed')
    expect(resolveCheckedInPlan(workspace([workout({ status: 'partial' })])).kind).toBe('completed')
  })

  it('returns a programmed rest day when today is empty but the program has sessions ahead', () => {
    const plan = resolveCheckedInPlan(
      workspace([workout({ id: 'future', scheduled_date: '2026-03-18', status: 'scheduled' })]),
    )
    expect(plan.kind).toBe('rest')
    expect(plan.kind === 'rest' && plan.nextUp?.id).toBe('future')
  })

  it('does NOT claim rest once the program has run out (lapsed program → plan_only)', () => {
    // The assignment stays ACTIVE forever after its last workout (no COMPLETED
    // status, null effective_end_date), so an empty today with only PAST sessions
    // is a finished program, not an authored rest day. Integrity: never invent rest.
    expect(
      resolveCheckedInPlan(workspace([workout({ id: 'past', scheduled_date: '2026-03-10', status: 'completed' })])).kind,
    ).toBe('plan_only')
  })

  it('does NOT claim rest when the only remaining sessions belong to a different (upcoming) assignment', () => {
    // A between-programs gap must not be dressed up as "you've earned it" rest.
    const plan = resolveCheckedInPlan(
      workspace([workout({ id: 'other', training_assignment_id: 'a2', scheduled_date: '2026-03-18', status: 'scheduled' })]),
    )
    expect(plan.kind).toBe('plan_only')
  })

  it('collapses to plan_only with no program, an absent workspace, or a skipped-only today', () => {
    expect(resolveCheckedInPlan(workspace([], null)).kind).toBe('plan_only')
    expect(resolveCheckedInPlan(undefined).kind).toBe('plan_only')
    // Program active but today's only session was skipped → not a programmed rest,
    // and no session ahead → guidance-only.
    expect(resolveCheckedInPlan(workspace([workout({ status: 'skipped' })])).kind).toBe('plan_only')
    expect(resolveCheckedInPlan(workspace([workout({ status: 'cancelled' })])).kind).toBe('plan_only')
  })

  it('ignores id-less workouts when choosing the actionable session', () => {
    expect(resolveCheckedInPlan(workspace([workout({ id: null, status: 'scheduled' })])).kind).not.toBe('workout')
  })
})

describe('nextUpWorkout', () => {
  it('picks the earliest future actionable session, ignoring past and non-actionable ones', () => {
    const next = nextUpWorkout(
      workspace([
        workout({ id: 'past', scheduled_date: '2026-03-10' }),
        workout({ id: 'far', scheduled_date: '2026-03-20' }),
        workout({ id: 'soon', scheduled_date: '2026-03-17' }),
        workout({ id: 'skip', scheduled_date: '2026-03-16', status: 'skipped' }),
      ]),
    )
    expect(next?.id).toBe('soon')
  })

  it('returns null without a workspace or future work', () => {
    expect(nextUpWorkout(undefined)).toBeNull()
    expect(nextUpWorkout(workspace([workout({ scheduled_date: '2026-03-10', status: 'completed' })]))).toBeNull()
  })
})

describe('relativeDay', () => {
  it('gives a truthful, deterministic phrase and never labels the past/today', () => {
    expect(relativeDay('2026-03-16', TODAY)).toBe('tomorrow')
    expect(relativeDay('2026-03-18', TODAY)).toBe('on Wednesday')
    expect(relativeDay('2026-03-23', TODAY)).toBe('next Monday')
    expect(relativeDay('2026-03-15', TODAY)).toBe('')
    expect(relativeDay('2026-03-10', TODAY)).toBe('')
  })
})
