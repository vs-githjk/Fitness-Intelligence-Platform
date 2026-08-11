import { describe, expect, it } from 'vitest'
import { DailyTrends, RiskFlag, ScheduledWorkout, TrainingAssignmentWorkspace } from '../types'
import {
  readinessPresentation,
  reasonLine,
  scoreTrend,
  selectGoingWell,
  selectTodayWorkout,
  selectWatch,
  workoutContext,
} from './today'

// A fixed date used for both scheduled_date and local_today, so selection never
// depends on the real clock (no date-flake).
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

function workspace(workouts: ScheduledWorkout[]): TrainingAssignmentWorkspace {
  return {
    timezone: 'UTC',
    local_today: TODAY,
    current_assignment: null,
    upcoming_assignment: null,
    assignment_history: [],
    history_events: [],
    scheduled_workouts: workouts,
  }
}

function trend(key: string, points: Array<{ value: number | null; diff: number | null }>): DailyTrends {
  return {
    start_date: TODAY,
    end_date: TODAY,
    timezone: 'UTC',
    series: [
      {
        key,
        label: key,
        unit: 'points',
        points: points.map((point, index) => ({
          date: `2026-03-${10 + index}`,
          value: point.value,
          missing: point.value == null,
          rolling_average: null,
          difference_from_previous: point.diff,
        })),
      },
    ],
  }
}

function flag(overrides: Partial<RiskFlag>): RiskFlag {
  return {
    rule_key: 'k',
    severity: 'review',
    status: 'open',
    title: 'T',
    explanation: 'E',
    recommended_action: 'A',
    triggering_inputs: {},
    rule_version: 'v1',
    triggered_at: '',
    ...overrides,
  }
}

describe('readinessPresentation (the one centralized mapping)', () => {
  it('maps each backend state to the frozen verdict and its atmosphere band', () => {
    expect(readinessPresentation('ready_to_push')).toEqual({ verdict: 'Go for it today.', atmosphere: 'ready_to_push' })
    expect(readinessPresentation('maintain')).toEqual({ verdict: 'Train as planned today.', atmosphere: 'maintain' })
    expect(readinessPresentation('reduce_intensity')).toEqual({ verdict: 'Ease off a little today.', atmosphere: 'reduce_intensity' })
    expect(readinessPresentation('recovery_recommended')).toEqual({ verdict: "Let's keep it light today.", atmosphere: 'recovery_recommended' })
  })

  it('falls back to a neutral presentation for an unknown state', () => {
    const presentation = readinessPresentation('some_future_state')
    expect(presentation.atmosphere).toBe('neutral')
    expect(presentation.verdict).toMatch(/plan for today/i)
  })
})

describe('reasonLine', () => {
  it('gives a non-empty deterministic sentence per state and a conservative fallback', () => {
    for (const state of ['ready_to_push', 'maintain', 'reduce_intensity', 'recovery_recommended']) {
      expect(reasonLine(state).length).toBeGreaterThan(0)
    }
    expect(reasonLine('maintain')).toMatch(/plan/i)
    expect(reasonLine('unknown')).toMatch(/latest check-in/i)
  })
})

describe('selectTodayWorkout', () => {
  it("selects today's actionable workout by display order, excluding other dates", () => {
    const selected = selectTodayWorkout(
      workspace([
        workout({ id: 'past', scheduled_date: '2026-03-14' }),
        workout({ id: 'future', scheduled_date: '2026-03-16' }),
        workout({ id: 'today-2', display_order: 2 }),
        workout({ id: 'today-1', display_order: 1 }),
      ]),
    )
    expect(selected?.id).toBe('today-1')
  })

  it('excludes completed/skipped and id-less workouts, and empty/absent workspaces', () => {
    expect(selectTodayWorkout(workspace([workout({ id: 'c', status: 'completed' })]))).toBeNull()
    expect(selectTodayWorkout(workspace([workout({ id: 's', status: 'skipped' })]))).toBeNull()
    expect(selectTodayWorkout(workspace([workout({ id: null })]))).toBeNull()
    expect(selectTodayWorkout(workspace([]))).toBeNull()
    expect(selectTodayWorkout(undefined)).toBeNull()
  })
})

describe('workoutContext', () => {
  it('prefers the label, falls back to the week number, else undefined', () => {
    expect(workoutContext(workout({ program_week_label: 'Week 3' }))).toBe('Week 3')
    expect(workoutContext(workout({ program_week_label: null, program_week_number: 4 }))).toBe('Week 4')
    expect(workoutContext(workout({ program_week_label: null, program_week_number: 0 }))).toBeUndefined()
  })
})

describe('scoreTrend and selectGoingWell', () => {
  it('returns the latest recorded difference and ignores missing tails', () => {
    expect(
      scoreTrend(trend('recovery_score', [{ value: 60, diff: null }, { value: 63, diff: 3 }, { value: null, diff: null }]), 'recovery_score'),
    ).toBe(3)
    expect(scoreTrend(trend('recovery_score', []), 'nope')).toBeNull()
    expect(scoreTrend(undefined, 'recovery_score')).toBeNull()
  })

  it('selects a truthful positive trend (preferring recovery), else nothing', () => {
    expect(selectGoingWell(trend('recovery_score', [{ value: 60, diff: null }, { value: 63, diff: 3 }]))).toMatch(/Recovery is up/)
    expect(selectGoingWell(trend('recovery_score', [{ value: 63, diff: null }, { value: 60, diff: -3 }]))).toBeNull()
    expect(selectGoingWell(undefined)).toBeNull()
  })
})

describe('selectWatch', () => {
  it('picks the highest-severity concern and returns the remainder in order', () => {
    const result = selectWatch([
      flag({ rule_key: 'a', severity: 'review' }),
      flag({ rule_key: 'b', severity: 'elevated' }),
      flag({ rule_key: 'c', severity: 'informational' }),
    ])
    expect(result?.primary.rule_key).toBe('b')
    expect(result?.remaining.map((item) => item.rule_key)).toEqual(['a', 'c'])
  })

  it('returns null when there are no concerns', () => {
    expect(selectWatch([])).toBeNull()
  })
})
