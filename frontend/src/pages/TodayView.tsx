// Morning Brief "Today" composition (Experience Cycle 1, Phase D).
//
// Presentational: it receives already-fetched data and derives presentation via
// the pure lib/today layer. The screen reads coach -> verdict -> why -> session
// -> action -> going well -> keep an eye on -> today's details.

import { ArrowRight, Pencil } from 'lucide-react'
import { Link } from 'react-router-dom'
import { CoachAttribution, CoachMessage } from '../components/coach'
import { GuidanceHero } from '../components/guidance'
import { SessionSlip, StatStrip } from '../components/session'
import { ctaClassName, DisclosureBlock, EvidenceRow, mbFocusRing, NoteLine, Score, SectionHeader } from '../components/ui'
import { componentPresentation } from '../lib/dailyComponents'
import {
  latestTrend,
  readinessPresentation,
  reasonLine,
  selectGoingWell,
  selectTodayWorkout,
  selectWatch,
  workoutContext,
} from '../lib/today'
import { CoachRelationship, DailyScore, DailyTrends, HealthIndex, TrainingAssignmentWorkspace, User } from '../types'

const DISCLAIMER = 'This is coaching guidance from your check-in, not medical advice.'

function greetingFor(name: string, now = new Date()): string {
  const hour = now.getHours()
  const part = hour < 12 ? 'morning' : hour < 18 ? 'afternoon' : 'evening'
  return `Good ${part}, ${name}`
}

function watchText(title: string, action: string): string {
  return `${title}. ${action}`
}

function TodayDetails({ score, trends, baseline }: { score: DailyScore; trends?: DailyTrends; baseline?: HealthIndex }) {
  return (
    <DisclosureBlock summary="Today's details">
      <div className="space-y-6">
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

        <div>
          <SectionHeader as="h3">Why today looks this way</SectionHeader>
          <div className="mt-2 space-y-3">
            {score.components.map((component) => {
              const { label, explanation } = componentPresentation(component.key)
              return (
                <div key={component.key}>
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-mb-body text-mb-ink">{label}</span>
                    <Score banded={false} value={component.missing ? null : component.normalized_score} />
                  </div>
                  {explanation && <p className="mt-0.5 text-mb-label text-mb-secondary">{explanation}</p>}
                </div>
              )
            })}
          </div>
        </div>

        {baseline && (
          <div>
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

export function MorningBriefToday({
  user,
  score,
  coach,
  workspace,
  trends,
  baseline,
}: {
  user: User
  score: DailyScore
  coach?: CoachRelationship
  workspace?: TrainingAssignmentWorkspace
  trends?: DailyTrends
  baseline?: HealthIndex
}) {
  const presentation = readinessPresentation(score.readiness_state)
  const workout = selectTodayWorkout(workspace)
  const goingWell = selectGoingWell(trends)
  const watch = selectWatch(score.risk_flags)
  const coachActive = coach?.assignment_status === 'active' && Boolean(coach.coach_name)
  const coachName = coachActive ? coach!.coach_name : undefined
  const coachAvatar = coachActive ? coach!.coach_avatar_url : undefined

  const session = workout ? (
    <SessionSlip
      variant="workout"
      name={workout.workout_template_version.name}
      context={workoutContext(workout)}
      stat={<StatStrip durationMinutes={workout.planned_duration_minutes} targetEffort={workout.target_session_rpe} />}
      coachMessage={<CoachMessage note={workout.trainee_instructions} name={coachName} avatarUrl={coachAvatar} demo={user.is_demo} />}
      action={
        workout.id ? (
          <Link to={`/trainee/workouts/${workout.id}`} className={ctaClassName('filled')}>
            Start workout
            <ArrowRight aria-hidden="true" className="size-4" />
          </Link>
        ) : undefined
      }
    />
  ) : undefined

  const editLink = user.is_demo ? undefined : (
    <Link
      to="/trainee/check-in"
      className={`inline-flex min-h-11 items-center gap-1.5 rounded-mb-control text-mb-label font-medium text-mb-secondary underline-offset-4 hover:text-mb-ink hover:underline ${mbFocusRing}`}
    >
      <Pencil aria-hidden="true" className="size-3.5" />
      Edit today's check-in
    </Link>
  )

  return (
    // The guidance lives on one centred ~640px spine (max-w-mb-guidance); on wider
    // desktops the extra width becomes whitespace, never a second column. The hero,
    // session, and evidence all inherit this readable measure.
    <div className="mx-auto w-full max-w-mb-guidance space-y-mb-section">
      <GuidanceHero
        atmosphere={presentation.atmosphere}
        attribution={coachActive ? <CoachAttribution variant="sender" name={coachName} avatarUrl={coachAvatar} demo={user.is_demo} /> : undefined}
        greeting={greetingFor(user.first_name)}
        verdict={presentation.verdict}
        reason={reasonLine(score.readiness_state)}
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
