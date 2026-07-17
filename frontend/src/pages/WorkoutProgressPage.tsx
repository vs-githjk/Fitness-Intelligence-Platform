import { AppShell, ProfileMeta } from '../components/AppShell'
import { PageHeader } from '../components/ui'
import { WorkoutIntelligencePanel } from '../components/workouts/WorkoutAnalytics'

export function WorkoutProgressPage() {
  return (
    <AppShell>
      <div className="space-y-8">
        <PageHeader
          eyebrow="Workouts"
          title="Workout progress"
          description="Deterministic, explainable analytics from your completed workouts. Missing data stays missing — it is never treated as zero."
          action={<ProfileMeta role="trainee" />}
        />
        <WorkoutIntelligencePanel basePath="/trainee" keyPrefix="trainee-workout-intel" />
      </div>
    </AppShell>
  )
}
