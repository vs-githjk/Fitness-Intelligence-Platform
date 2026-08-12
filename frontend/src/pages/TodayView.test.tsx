import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { CoachRelationship, DailyScore, DailyScoreComponent, HealthIndex, RiskFlag, ScheduledWorkout, TrainingAssignmentWorkspace, User } from '../types'
import { MorningBriefToday } from './TodayView'

const user: User = { id: 'u1', email: 't@e.com', first_name: 'Arjun', last_name: 'K', role: 'trainee', is_demo: false }
const TODAY = '2026-03-15'

function score(overrides: Partial<DailyScore> = {}): DailyScore {
  return {
    id: 's1',
    trainee_id: 'u1',
    daily_check_in_id: 'c1',
    local_date: TODAY,
    recovery_score: 76,
    activity_score: 52,
    nutrition_score: null,
    readiness_score: 84,
    readiness_state: 'maintain',
    scoring_version: 'daily-intelligence-v1',
    calculated_at: '',
    components: [
      {
        key: 'recent_training_load',
        group: 'readiness',
        raw_inputs: {},
        normalized_score: 82,
        weight: 30,
        contribution: 24,
        status: 'within_product_threshold',
        explanation: 'Load is within range.',
        missing: false,
      },
    ],
    missing_fields: [],
    recent_training_load: { window_days: 7, daily_loads: [], total: 0, tolerance_score: 100 },
    risk_flags: [],
    recommendations: [],
    ...overrides,
  }
}

function flag(overrides: Partial<RiskFlag>): RiskFlag {
  return {
    rule_key: 'k',
    severity: 'review',
    status: 'open',
    title: 'A concern',
    explanation: 'Why',
    recommended_action: 'Do this',
    triggering_inputs: {},
    rule_version: 'v1',
    triggered_at: '',
    ...overrides,
  }
}

function withWorkout(overrides: Partial<ScheduledWorkout> = {}): TrainingAssignmentWorkspace {
  const workout = {
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
  return {
    timezone: 'UTC',
    local_today: TODAY,
    current_assignment: null,
    upcoming_assignment: null,
    assignment_history: [],
    history_events: [],
    scheduled_workouts: [workout],
  }
}

function renderToday(props: Partial<Parameters<typeof MorningBriefToday>[0]> & { score: DailyScore }) {
  return render(
    <MemoryRouter>
      <MorningBriefToday user={user} {...props} />
    </MemoryRouter>,
  )
}

afterEach(() => {
  cleanup()
  document.documentElement.removeAttribute('data-theme')
})

describe('MorningBriefToday', () => {
  it.each([
    ['ready_to_push', 'Go for it today.'],
    ['maintain', 'Train as planned today.'],
    ['reduce_intensity', 'Ease off a little today.'],
    ['recovery_recommended', "Let's keep it light today."],
  ])('leads with the frozen verdict as the dominant heading for %s', (state, verdict) => {
    renderToday({ score: score({ readiness_state: state }) })
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(verdict)
  })

  it('greets the trainee and shows guidance, not the old metric grid or warning wall', () => {
    const { container } = renderToday({ score: score() })
    expect(screen.getByText(/good (morning|afternoon|evening), Arjun/i)).toBeInTheDocument()
    expect(container.querySelector('.metric-number')).toBeNull()
    expect(screen.queryByText('Recommended next actions')).toBeNull()
    expect(screen.queryByText('Current review signals')).toBeNull()
  })

  it('composes exactly one Start Workout link to the execution route', () => {
    renderToday({ score: score(), workspace: withWorkout() })
    const start = screen.getByRole('link', { name: /start workout/i })
    expect(start).toHaveAttribute('href', '/trainee/workouts/w1')
    expect(screen.getAllByRole('link', { name: /start workout/i })).toHaveLength(1)
  })

  it('shows coach authorship and the verbatim note when a coach is assigned', () => {
    const coach: CoachRelationship = { assignment_status: 'active', coach_name: 'Jordan Ellis' }
    renderToday({ score: score(), coach, workspace: withWorkout({ trainee_instructions: 'Focus on control.' }) })
    expect(screen.getAllByText('Jordan Ellis').length).toBeGreaterThan(0)
    expect(screen.getByText('Focus on control.')).toBeInTheDocument()
  })

  it('omits the coach note when trainee_instructions is absent', () => {
    renderToday({ score: score(), workspace: withWorkout({ trainee_instructions: null }) })
    expect(screen.queryByText('Focus on control.')).toBeNull()
  })

  it('surfaces the highest-priority concern and collapses the rest — no warning stack', () => {
    renderToday({
      score: score({
        risk_flags: [flag({ rule_key: 'a', severity: 'review', title: 'Lower concern' }), flag({ rule_key: 'b', severity: 'elevated', title: 'Top concern' })],
      }),
    })
    expect(screen.getByRole('heading', { name: /keep an eye on/i })).toBeInTheDocument()
    expect(screen.getByText(/Top concern/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /1 more note/i })).toBeInTheDocument()
  })

  it('keeps evidence one interaction away with exactly one disclaimer and missing shown as missing', () => {
    renderToday({ score: score({ nutrition_score: null }) })
    expect(screen.queryByText(/not medical advice/i)).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /today's details/i }))
    expect(screen.getAllByText(/not medical advice/i)).toHaveLength(1)
    expect(screen.getByText('Add nutrition targets to track this')).toBeInTheDocument()
    expect(screen.getByText('Recovery')).toBeInTheDocument()
    expect(screen.getByText('Training readiness')).toBeInTheDocument()
  })

  it('never renders banned product vocabulary in the details, only human component labels', () => {
    const components: DailyScoreComponent[] = [
      { key: 'recent_training_load', group: 'readiness', raw_inputs: {}, normalized_score: 100, weight: 30, contribution: 30, status: 'within_product_threshold', explanation: 'Load does not reduce readiness through 1,200 arbitrary units.', missing: false },
      { key: 'protein_compliance', group: 'nutrition', raw_inputs: {}, normalized_score: 0, weight: 0, contribution: 0, status: 'unavailable', explanation: 'raw explanation', missing: true },
      { key: 'hydration_compliance', group: 'nutrition', raw_inputs: {}, normalized_score: 57, weight: 100, contribution: 57, status: 'needs_attention', explanation: 'raw explanation', missing: false },
    ]
    const { container } = renderToday({ score: score({ components }) })
    fireEvent.click(screen.getByRole('button', { name: /today's details/i }))
    const text = container.textContent ?? ''
    expect(text).not.toMatch(/compliance/i)
    expect(text).not.toMatch(/arbitrary units/i)
    expect(text).not.toMatch(/\w+_\w+/) // no snake_case leaks
    // Approved human labels replace the raw keys.
    expect(screen.getByText('Recent training load')).toBeInTheDocument()
    expect(screen.getByText('Protein intake')).toBeInTheDocument()
    expect(screen.getByText('Hydration')).toBeInTheDocument()
  })

  it('renders the baseline Health Index as an explicitly banded score, carrying its band word', () => {
    const baseline: HealthIndex = {
      id: 'h1', trainee_id: 'u1', assessment_id: 'a1', overall_score: 90, band: 'Excellent',
      scoring_version: 'health-index-v1', calculated_at: '', components: [], missing_fields: [], risk_flags: [], recommendations: [],
    }
    renderToday({ score: score(), baseline })
    fireEvent.click(screen.getByRole('button', { name: /today's details/i }))
    expect(screen.getByText('Health Index')).toBeInTheDocument()
    expect(screen.getByText('Excellent')).toBeInTheDocument()
    expect(screen.getByText('90')).toBeInTheDocument()
  })

  it('constrains the guidance to the centred ~640px spine (no full-width stretch)', () => {
    const { container } = renderToday({ score: score(), workspace: withWorkout() })
    expect(container.querySelector('.max-w-mb-guidance')).not.toBeNull()
  })

  it('renders under both Morning Brief themes', () => {
    for (const theme of ['light', 'dark'] as const) {
      document.documentElement.setAttribute('data-theme', theme)
      const { unmount } = renderToday({ score: score(), workspace: withWorkout() })
      expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
      unmount()
    }
  })
})

const restWorkspace = (nextDate: string | null): TrainingAssignmentWorkspace => ({
  timezone: 'UTC',
  local_today: TODAY,
  current_assignment: { id: 'a1', program_name: 'Base' } as unknown as TrainingAssignmentWorkspace['current_assignment'],
  upcoming_assignment: null,
  assignment_history: [],
  history_events: [],
  scheduled_workouts: nextDate
    ? [
        {
          ...withWorkout().scheduled_workouts[0],
          id: 'next',
          scheduled_date: nextDate,
          status: 'scheduled',
          workout_template_version: { ...withWorkout().scheduled_workouts[0].workout_template_version, name: 'Full Body Strength' },
        },
      ]
    : [],
})

describe('MorningBriefToday — Phase E states', () => {
  it('renders a programmed rest day with frozen copy, next-up, and no Start action', () => {
    renderToday({ score: score(), workspace: restWorkspace('2026-03-16') })
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Take today off — on purpose.')
    expect(screen.getByText(/You've earned it\. Rest is when the work pays off\./)).toBeInTheDocument()
    expect(screen.getByText(/Next up: Full Body Strength, tomorrow\./)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /start workout/i })).toBeNull()
  })

  it('renders a completed workout as a calm done state with no Start action', () => {
    renderToday({ score: score(), workspace: withWorkout({ status: 'completed' }) })
    // Verdict still leads; the session is closed, not shouting Start.
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Train as planned today.')
    expect(screen.getByText('Lower Body Strength')).toBeInTheDocument()
    expect(screen.getByText(/Completed workout:/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /start workout/i })).toBeNull()
  })

  it('collapses the session cleanly when there is no program (plan-only), keeping guidance', () => {
    renderToday({ score: score({ readiness_state: 'ready_to_push' }) }) // no workspace
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Go for it today.')
    expect(screen.queryByRole('link', { name: /start workout/i })).toBeNull()
    expect(screen.queryByText(/Rest day/)).toBeNull()
    // Still one interaction to evidence.
    expect(screen.getByRole('button', { name: /today's details/i })).toBeInTheDocument()
  })

  it('marks demo authorship and hides the edit affordance for demo users', () => {
    // The demo *condition* is announced app-wide by AppShell; Today owns the coach
    // "Demo" attribution tag and disables editing (no second demo banner here).
    const coach: CoachRelationship = { assignment_status: 'active', coach_name: 'Maya Coach' }
    render(
      <MemoryRouter>
        <MorningBriefToday user={{ ...user, is_demo: true }} score={score()} coach={coach} workspace={withWorkout()} />
      </MemoryRouter>,
    )
    expect(screen.getAllByText('Demo').length).toBeGreaterThan(0)
    expect(screen.queryByRole('link', { name: /edit today's check-in/i })).toBeNull()
    // Start is presented truthfully: a disabled control, not a live link that would
    // only meet a server 403. The UI never invites a mutation it knows is refused.
    expect(screen.queryByRole('link', { name: /start workout/i })).toBeNull()
    expect(screen.getByRole('button', { name: /start workout/i })).toBeDisabled()
  })

  it('when offline, shows an offline banner and disables Start rather than linking', () => {
    renderToday({ score: score(), workspace: withWorkout(), online: false })
    expect(screen.getByText(/You’re offline/)).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: /start workout/i })).toBeNull()
    const start = screen.getByRole('button', { name: /start workout/i })
    expect(start).toBeDisabled()
  })

  it('degrades gracefully when coach, trends, and Health Index are all absent', () => {
    renderToday({ score: score({ nutrition_score: null }), workspace: withWorkout() })
    // Core plan still renders; going-well omitted; no crash.
    expect(screen.getByRole('link', { name: /start workout/i })).toBeInTheDocument()
    expect(screen.queryByText(/is up since your last check-in/)).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /today's details/i }))
    expect(screen.getByText('Add nutrition targets to track this')).toBeInTheDocument()
    expect(screen.queryByText('Health Index')).toBeNull()
  })
})
