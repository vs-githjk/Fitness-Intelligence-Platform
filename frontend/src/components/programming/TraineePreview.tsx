import { Clock3, Gauge, ShieldCheck } from 'lucide-react'
import { ExerciseVersion, WorkoutSetPrescriptionData, WorkoutTemplateDraftData, WorkoutTemplateSection } from '../../types'
import { Badge, Card } from '../ui'
import { sectionLabel } from './ProgrammingBadges'

const sections: WorkoutTemplateSection[] = ['warm_up', 'main', 'cool_down']

export function TraineePreview({ template, exercises }: { template: WorkoutTemplateDraftData; exercises: Map<string, ExerciseVersion> }) {
  return <div aria-label="Trainee workout preview" className="space-y-4"><div><p className="text-xs font-bold uppercase tracking-[0.14em] text-primary">Trainee preview</p><h2 className="mt-1 text-2xl font-semibold">{template.name || 'Untitled workout'}</h2><div className="mt-3 flex flex-wrap gap-2">{template.estimated_duration_minutes && <Badge tone="info"><Clock3 aria-hidden="true" className="mr-1 size-3" />{template.estimated_duration_minutes} min</Badge>}{template.target_session_rpe !== null && <Badge tone="attention"><Gauge aria-hidden="true" className="mr-1 size-3" />Target RPE {template.target_session_rpe}</Badge>}{template.goal_tags.map(tag => <Badge key={tag}>{tag.replaceAll('_', ' ')}</Badge>)}</div>{template.trainee_instructions && <p className="mt-4 text-sm leading-6 text-secondary">{template.trainee_instructions}</p>}</div>{sections.map(section => { const items = template.exercises.filter(item => item.section === section).sort((a, b) => a.display_order - b.display_order); if (!items.length) return null; return <section key={section} aria-labelledby={`preview-${section}`}><h3 id={`preview-${section}`} className="mb-3 text-lg font-semibold">{sectionLabel(section)}</h3><div className="space-y-3">{items.map(item => { const exercise = exercises.get(item.exercise_version_id); return <Card key={`${item.exercise_version_id}-${item.display_order}`} as="article" className="shadow-none"><h4 className="font-semibold">{exercise?.name ?? 'Exercise unavailable'}</h4>{item.trainee_instructions && <p className="mt-2 text-sm leading-6 text-secondary">{item.trainee_instructions}</p>}{exercise?.instructions && <p className="mt-2 text-sm leading-6 text-secondary">{exercise.instructions}</p>}<div className="mt-3 space-y-2">{item.sets.map(set => <div key={set.set_number} className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg bg-elevated px-3 py-2 text-sm"><span className="font-semibold">Set {set.set_number}</span><span>{prescriptionLabel(set)}</span>{set.rest_seconds !== null && <span className="text-muted">Rest {set.rest_seconds}s</span>}{set.instructions && <span className="w-full text-xs text-secondary">{set.instructions}</span>}</div>)}</div>{exercise?.safety_cues.length ? <div className="mt-3 flex gap-2 rounded-lg border border-[rgb(var(--status-attention-border))] bg-[rgb(var(--status-attention-bg))] p-3 text-xs leading-5 text-secondary"><ShieldCheck aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-attention" /><span>{exercise.safety_cues.join(' ')}</span></div> : null}</Card> })}</div></section> })}{!template.exercises.length && <p className="rounded-xl border border-dashed p-6 text-center text-sm text-muted">Add exercises to preview the trainee experience.</p>}</div>
}

function prescriptionLabel(set: WorkoutSetPrescriptionData) {
  const parts: string[] = []
  if (set.repetitions_min !== null) parts.push(set.repetitions_min === set.repetitions_max ? `${set.repetitions_min} reps` : `${set.repetitions_min}–${set.repetitions_max} reps`)
  if (set.target_duration_seconds !== null) parts.push(`${set.target_duration_seconds}s`)
  if (set.target_distance_value !== null) parts.push(`${set.target_distance_value} ${set.target_distance_unit}`)
  if (set.target_load_original_value !== null) parts.push(`${set.target_load_original_value} ${set.target_load_original_unit} load`)
  if (set.target_assistance_original_value !== null) parts.push(`${set.target_assistance_original_value} ${set.target_assistance_original_unit} assistance`)
  if (set.target_rpe !== null) parts.push(`RPE ${set.target_rpe}`)
  if (set.target_rir !== null) parts.push(`RIR ${set.target_rir}`)
  if (set.tempo) parts.push(`Tempo ${set.tempo}`)
  return parts.join(' · ') || 'Prescription pending'
}
