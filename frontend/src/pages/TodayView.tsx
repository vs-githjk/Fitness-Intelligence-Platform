// Morning Brief "Today" composition (Experience Cycle 1, Phases D + E).
//
// Presentational: it receives already-fetched data and derives presentation via
// the pure lib/today + lib/todayState layers. The checked-in screen reads coach ->
// verdict -> why -> session -> action -> going well -> keep an eye on -> today's
// details, and re-weights that same composition across the checked-in states
// (workout / completed / rest / plan-only) plus the demo and offline overlays.

import { ArrowRight, Pencil } from 'lucide-react'
import { Link } from 'react-router-dom'
import { CoachAttribution, CoachMessage } from '../components/coach'
import { GuidanceHero } from '../components/guidance'
import { SessionSlip, StatStrip } from '../components/session'
import { ctaClassName, DisclosureBlock, EvidenceRow, mbFocusRing, NoteLine, Score, SectionHeader, SystemBanner } from '../components/ui'
import { componentPresentation } from '../lib/dailyComponents'
import {
  greetingFor,
  latestTrend,
  readinessPresentation,
  reasonLine,
  selectGoingWell,
  selectWatch,
  workoutContext,
} from '../lib/today'
import { CheckedInPlan, relativeDay, resolveCheckedInPlan } from '../lib/todayState'
import { CoachRelationship, DailyScore, DailyTrends, HealthIndex, TrainingAssignmentWorkspace, User } from '../types'

const DISCLAIMER = 'This is coaching guidance from your check-in, not medical advice.'

// Join the concern title and its recommended action the way the frozen spec writes it
// (§8: "Soreness is a little high — ease into your warm-up") — an em dash, not a period,
// so a lower-cased action clause never reads as a broken second sentence.
function watchText(title: string, action: string): string {
  return `${title} — ${action}`
}

// Today's details — the one evidence disclosure (frozen §17). Two clear tiers, so it
// scans when curious and ignores when not: the four summary scores first, then the
// per-component mechanics visibly subordinate beneath a thin rule. Density is managed
// with hierarchy and rhythm only — no cards, no tiles, no invented grouping, and every
// deterministic explanation stays visible (never hidden behind a second disclosure).
function TodayDetails({ score, trends, baseline }: { score: DailyScore; trends?: DailyTrends; baseline?: HealthIndex }) {
  return (
    <DisclosureBlock summary="Today's details">
      <div className="space-y-7">
        <div>
          <SectionHeader as="h3">Your numbers today</SectionHeader>
          <div className="mt-1 divide-y divide-mb-hairline">
            <EvidenceRow banded={false} label="Recovery" value={score.recovery_score} trend={latestTrend(trends, 'recovery_score')} />
            <EvidenceRow banded={false} label="Training readiness" value={score.readiness_score} trend={latestTrend(trends, 'readiness_score')} />
            <EvidenceRow banded={false} label="Activity" value={score.activity_score} trend={latestTrend(trends, 'activity_score')} />
            <EvidenceRow
              banded={false}
              label="Nutrition"
              value={score.nutrition_score}
              unavailableLabel="Add nutrition targets to track this"
              trend={latestTrend(trends, 'nutrition_score')}
            />
          </div>
        </div>

        <div className="border-t border-mb-hairline pt-6">
          <SectionHeader as="h3">Why today looks this way</SectionHeader>
          <p className="mt-1 text-mb-micro text-mb-muted">The signals behind the numbers above — each scored deterministically from your check-in.</p>
          <dl className="mt-3 divide-y divide-mb-hairline">
            {score.components.map((component) => {
              const { label, explanation } = componentPresentation(component.key)
              return (
                <div key={component.key} className="py-2.5">
                  <div className="flex items-baseline justify-between gap-3">
                    <dt className="text-mb-body font-medium text-mb-ink">{label}</dt>
                    <dd className="shrink-0"><Score banded={false} value={component.missing ? null : component.normalized_score} /></dd>
                  </div>
                  {explanation && <p className="mt-0.5 text-mb-micro leading-5 text-mb-muted">{explanation}</p>}
                </div>
              )
            })}
          </dl>
        </div>

        {baseline && (
          <div className="border-t border-mb-hairline pt-6">
            <SectionHeader as="h3">Your starting point</SectionHeader>
            <div className="mt-1">
              <EvidenceRow banded label="Health Index" value={baseline.overall_score} word={baseline.band} />
            </div>
          </div>
        )}

        <p className="text-mb-micro text-mb-muted">{DISCLAIMER}</p>
      </div>
    </DisclosureBlock>
  )
}

// Rest and not-checked-in copy are FROZEN in docs/design/trainee-today.md §8/§9.
const REST_VERDICT = 'Take today off — on purpose.'
const REST_REASON = "You've earned it. Rest is when the work pays off."

// Build the session slot for a resolved plan. Returns undefined for plan_only so
// the slot collapses cleanly (no empty SessionSlip). The caller owns routing.
function planSession(
  plan: CheckedInPlan,
  ctx: { coachName?: string | null; coachAvatar?: string | null; isDemo: boolean; online: boolean; localToday?: string },
) {
  const coachMessage = (note: string | null) => (
    <CoachMessage note={note} name={ctx.coachName} avatarUrl={ctx.coachAvatar} demo={ctx.isDemo} />
  )
  if (plan.kind === 'workout') {
    const w = plan.workout
    return (
      <SessionSlip
        variant="workout"
        name={w.workout_template_version.name}
        context={workoutContext(w)}
        stat={<StatStrip durationMinutes={w.planned_duration_minutes} targetEffort={w.target_session_rpe} />}
        coachMessage={coachMessage(w.trainee_instructions)}
        action={w.id ? <StartAction id={w.id} online={ctx.online} demo={ctx.isDemo} /> : undefined}
      />
    )
  }
  if (plan.kind === 'completed') {
    const w = plan.workout
    return (
      <SessionSlip
        variant="done"
        name={w.workout_template_version.name}
        context={workoutContext(w)}
        coachMessage={coachMessage(w.trainee_instructions)}
      />
    )
  }
  if (plan.kind === 'rest') {
    const next = plan.nextUp
    const description =
      next && ctx.localToday
        ? `Next up: ${next.workout_template_version.name}, ${relativeDay(next.scheduled_date, ctx.localToday)}.`
        : undefined
    return <SessionSlip variant="rest" name="Rest day" description={description} />
  }
  return undefined // plan_only — the session slot collapses.
}

// The primary action. It is a genuinely disabled control (never a live link) when the
// action truly cannot proceed — offline (starting a workout needs a connection) or in
// the read-only demo (the server enforces 403, so the UI must not invite a mutation it
// already knows will be refused). Both are truthful, not decorative.
function StartAction({ id, online, demo = false }: { id: string; online: boolean; demo?: boolean }) {
  if (demo || !online) {
    const label = demo ? 'Start workout — disabled in the read-only demo' : 'Start workout — unavailable offline'
    return (
      <button type="button" disabled aria-label={label} className={ctaClassName('filled')}>
        Start workout
        <ArrowRight aria-hidden="true" className="size-4" />
      </button>
    )
  }
  return (
    <Link to={`/trainee/workouts/${id}`} className={ctaClassName('filled')}>
      Start workout
      <ArrowRight aria-hidden="true" className="size-4" />
    </Link>
  )
}

export function MorningBriefToday({
  user,
  score,
  coach,
  workspace,
  trends,
  baseline,
  online = true,
}: {
  user: User
  score: DailyScore
  coach?: CoachRelationship
  workspace?: TrainingAssignmentWorkspace
  trends?: DailyTrends
  baseline?: HealthIndex
  online?: boolean
}) {
  const plan = resolveCheckedInPlan(workspace)
  const presentation = readinessPresentation(score.readiness_state)
  const goingWell = selectGoingWell(trends)
  const watch = selectWatch(score.risk_flags)
  const coachActive = coach?.assignment_status === 'active' && Boolean(coach.coach_name)
  const coachName = coachActive ? coach!.coach_name : undefined
  const coachAvatar = coachActive ? coach!.coach_avatar_url : undefined

  // A programmed rest day is coach/program intent, not a readiness verdict: it uses
  // the frozen rest copy and a neutral atmosphere so strong readiness never reads as
  // "override your rest". Every other checked-in state keeps the readiness verdict.
  const isRest = plan.kind === 'rest'
  const atmosphere = isRest ? 'neutral' : presentation.atmosphere
  const verdict = isRest ? REST_VERDICT : presentation.verdict
  const reason = isRest ? REST_REASON : reasonLine(score.readiness_state)

  const session = planSession(plan, {
    coachName,
    coachAvatar,
    isDemo: user.is_demo,
    online,
    localToday: workspace?.local_today,
  })

  const editLink = user.is_demo ? undefined : (
    <Link
      to="/trainee/check-in"
      className={`inline-flex min-h-11 scroll-mb-40 items-center gap-1.5 rounded-mb-control text-mb-label font-medium text-mb-secondary underline-offset-4 hover:text-mb-ink hover:underline lg:scroll-mb-0 ${mbFocusRing}`}
    >
      <Pencil aria-hidden="true" className="size-3.5" />
      Edit today's check-in
    </Link>
  )

  return (
    // The guidance lives on one centred ~640px spine (max-w-mb-guidance); on wider
    // desktops the extra width becomes whitespace, never a second column. The hero,
    // session, and evidence all inherit this readable measure.
    <div className="mx-auto w-full max-w-mb-guidance space-y-mb-section animate-mb-settle motion-reduce:animate-none">
      {/* The demo condition is already announced app-wide by AppShell's banner; Today
          adds the coach "Demo" attribution tag and disables editing rather than
          stacking a second banner. Offline is Today-specific, so it lives here. */}
      {!online && (
        <SystemBanner tone="offline" title="You’re offline">
          Showing the plan already loaded on this device. It may be out of date, and starting a workout needs a connection.
        </SystemBanner>
      )}
      <GuidanceHero
        atmosphere={atmosphere}
        attribution={coachActive ? <CoachAttribution variant="sender" name={coachName} avatarUrl={coachAvatar} demo={user.is_demo} /> : undefined}
        greeting={greetingFor(user.first_name)}
        verdict={verdict}
        reason={reason}
        session={session}
        secondaryAction={editLink}
      />

      {(goingWell || watch) && (
        <div className="space-y-mb-section-tight">
          {goingWell && (
            <div className="space-y-2">
              <SectionHeader>Going well</SectionHeader>
              <NoteLine tone="success">{goingWell}</NoteLine>
            </div>
          )}
          {watch && (
            <div className="space-y-2">
              <SectionHeader>Keep an eye on</SectionHeader>
              <NoteLine tone="caution">{watchText(watch.primary.title, watch.primary.recommended_action)}</NoteLine>
              {watch.remaining.length > 0 && (
                <DisclosureBlock summary={`${watch.remaining.length} more ${watch.remaining.length === 1 ? 'note' : 'notes'}`}>
                  <div className="space-y-3">
                    {watch.remaining.map((flag) => (
                      <NoteLine key={flag.rule_key} tone="caution">
                        {watchText(flag.title, flag.recommended_action)}
                      </NoteLine>
                    ))}
                  </div>
                </DisclosureBlock>
              )}
            </div>
          )}
        </div>
      )}

      <TodayDetails score={score} trends={trends} baseline={baseline} />
    </div>
  )
}
