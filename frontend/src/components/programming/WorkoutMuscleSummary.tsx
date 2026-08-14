import { ExerciseVersion, WorkoutTemplateExerciseData } from '../../types'
import { classifyMuscles, MuscleRegion } from '../../lib/muscles'
import { BodyMap } from '../iron/BodyMap'

// A data-true "training should be seen" summary of a workout: which body regions it trains
// and how many sets land on each (primary movers). It reads only the exercises' own muscle
// metadata through the frozen §20 map — no invented volume, no anatomical guessing. Muscle
// strings outside the direct/broad map simply don't count here (they stay text elsewhere),
// exactly as the BodyMap never highlights an unknown region.

const REGION_LABEL: Record<MuscleRegion, string> = {
  quadriceps: 'Quads', glutes: 'Glutes', hamstrings: 'Hamstrings', chest: 'Chest',
  triceps: 'Triceps', back: 'Back', shoulders: 'Shoulders', biceps: 'Biceps',
  core: 'Core', forearms: 'Forearms', 'hip-flexors': 'Hip flexors',
  'lower-body': 'Lower body', torso: 'Torso',
}

export function WorkoutMuscleSummary({ exercises, versions }: { exercises: WorkoutTemplateExerciseData[]; versions: Map<string, ExerciseVersion> }) {
  const primaryStrings: string[] = []
  const secondaryStrings: string[] = []
  const setsByRegion = new Map<MuscleRegion, number>()

  for (const item of exercises) {
    const version = versions.get(item.exercise_version_id)
    if (!version) continue
    const sets = item.sets.length
    primaryStrings.push(...version.primary_muscle_groups)
    secondaryStrings.push(...version.secondary_muscle_groups)
    for (const muscle of classifyMuscles(version.primary_muscle_groups)) {
      if (muscle.region) setsByRegion.set(muscle.region, (setsByRegion.get(muscle.region) ?? 0) + sets)
    }
  }

  const ranked = [...setsByRegion.entries()].sort((a, b) => b[1] - a[1] || REGION_LABEL[a[0]].localeCompare(REGION_LABEL[b[0]]))
  if (!ranked.length) return null
  const max = ranked[0][1]

  return (
    <section aria-label="Muscle focus" className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold">Muscle focus</h3>
        <p className="mt-1 text-sm text-secondary">Primary working sets by region across this workout.</p>
      </div>
      <BodyMap primary={primaryStrings} secondary={secondaryStrings} className="mx-auto h-36 w-full max-w-xs" />
      <dl className="space-y-2">
        {ranked.map(([region, count]) => (
          <div key={region} className="grid grid-cols-[6.5rem_1fr_2rem] items-center gap-2">
            <dt className="truncate text-sm font-medium">{REGION_LABEL[region]}</dt>
            <div className="h-2 overflow-hidden rounded-full bg-elevated" aria-hidden="true">
              <div className="h-full rounded-full bg-mb-ember motion-safe:transition-all" style={{ width: `${Math.round((count / max) * 100)}%` }} />
            </div>
            <dd className="text-right text-sm tabular-nums text-secondary">{count}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}
