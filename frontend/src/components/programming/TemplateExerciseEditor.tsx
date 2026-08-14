/* eslint-disable react-refresh/only-export-components -- the default prescription factory belongs with its editor */
import { ArrowDown, ArrowUp, GripVertical, Plus, Trash2 } from 'lucide-react'
import { DragEvent } from 'react'
import { ExerciseTrackingMode, ExerciseVersion, WorkoutSetPrescriptionData, WorkoutTemplateExerciseData, WorkoutTemplateSection } from '../../types'
import { MovementGlyph } from '../iron/MovementGlyph'
import { Badge, Button, Field, SelectInput, TextArea } from '../ui'
import { sectionLabel, TrackingModeBadge } from './ProgrammingBadges'
import { SetPrescriptionEditor } from './SetPrescriptionEditor'

type DragProps = { draggable: boolean; onDragStart: (event: DragEvent) => void; onDragEnd: () => void; onDragOver: (event: DragEvent) => void; onDrop: (event: DragEvent) => void; isDragging: boolean; isOver: boolean }

export function TemplateExerciseEditor({ value, exercise, disabled, canMoveUp, canMoveDown, onChange, onRemove, onMove, drag }: { value: WorkoutTemplateExerciseData; exercise?: ExerciseVersion; disabled: boolean; canMoveUp: boolean; canMoveDown: boolean; onChange: (value: WorkoutTemplateExerciseData) => void; onRemove: () => void; onMove: (direction: -1 | 1) => void; drag?: DragProps }) {
  const mode = exercise?.tracking_mode ?? 'repetitions_only'; const patch = (next: Partial<WorkoutTemplateExerciseData>) => onChange({ ...value, ...next })
  function updateSet(index: number, next: WorkoutSetPrescriptionData) { const sets = value.sets.map((item, current) => current === index ? next : item); patch({ sets: renumber(sets) }) }
  function removeSet(index: number) { patch({ sets: renumber(value.sets.filter((_, current) => current !== index)) }) }
  function duplicateSet(index: number) { const sets = [...value.sets]; sets.splice(index + 1, 0, { ...sets[index] }); patch({ sets: renumber(sets) }) }
  function moveSet(index: number, direction: -1 | 1) { const target = index + direction; if (target < 0 || target >= value.sets.length) return; const sets = [...value.sets]; [sets[index], sets[target]] = [sets[target], sets[index]]; patch({ sets: renumber(sets) }) }
  // "Add set" copies the previous set's prescription (matching Everfit/Hevy/Strong) so the
  // coach edits a delta rather than re-entering every field; the first set uses defaults.
  function addSet() { const last = value.sets[value.sets.length - 1]; patch({ sets: renumber([...value.sets, last ? { ...last } : newPrescription(mode)]) }) }
  const dnd = drag && !disabled
  return <article
    draggable={dnd ? drag!.draggable : undefined}
    onDragStart={dnd ? drag!.onDragStart : undefined}
    onDragEnd={dnd ? drag!.onDragEnd : undefined}
    onDragOver={dnd ? drag!.onDragOver : undefined}
    onDrop={dnd ? drag!.onDrop : undefined}
    className={`rounded-2xl border bg-elevated/60 p-4 motion-safe:transition-shadow sm:p-5 ${dnd && drag!.isDragging ? 'opacity-50' : ''} ${dnd && drag!.isOver ? 'ring-2 ring-primary' : ''}`}
  ><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div className="flex min-w-0 items-start gap-3">{dnd && <span aria-hidden="true" title="Drag to reorder" className="mt-1 cursor-grab text-muted active:cursor-grabbing"><GripVertical className="size-5" /></span>}<span className="grid size-10 shrink-0 place-items-center rounded-lg bg-surface text-secondary"><MovementGlyph pattern={exercise?.movement_pattern ?? ''} className="size-6" strokeWidth={1.75} /></span><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><Badge tone="neutral">{sectionLabel(value.section)} {value.display_order}</Badge>{exercise && <TrackingModeBadge mode={exercise.tracking_mode} />}</div><h3 className="mt-2 text-lg font-semibold">{exercise?.name ?? 'Exercise unavailable'}</h3><p className="mt-1 text-xs text-muted">Exact exercise version {exercise?.version_number ?? '—'}</p></div></div>{!disabled && <div className="flex flex-wrap gap-1"><Button type="button" variant="ghost" disabled={!canMoveUp} onClick={() => onMove(-1)} aria-label={`Move ${exercise?.name ?? 'exercise'} up`}><ArrowUp aria-hidden="true" className="size-4" />Up</Button><Button type="button" variant="ghost" disabled={!canMoveDown} onClick={() => onMove(1)} aria-label={`Move ${exercise?.name ?? 'exercise'} down`}><ArrowDown aria-hidden="true" className="size-4" />Down</Button><Button type="button" variant="ghost" onClick={onRemove}><Trash2 aria-hidden="true" className="size-4" />Remove</Button></div>}</div><div className="mt-5 grid gap-4 lg:grid-cols-3"><Field label="Workout section">{({ id, describedBy, invalid }) => <SelectInput id={id} aria-describedby={describedBy} aria-invalid={invalid} value={value.section} disabled={disabled} onChange={event => patch({ section: event.target.value as WorkoutTemplateSection })}><option value="warm_up">Warm-up</option><option value="main">Main</option><option value="cool_down">Cool-down</option></SelectInput>}</Field><Field label="Coach notes" optional>{({ id, describedBy, invalid }) => <TextArea id={id} aria-describedby={describedBy} aria-invalid={invalid} value={value.coach_notes ?? ''} disabled={disabled} className="min-h-24" onChange={event => patch({ coach_notes: event.target.value || null })} />}</Field><Field label="Trainee instructions" optional>{({ id, describedBy, invalid }) => <TextArea id={id} aria-describedby={describedBy} aria-invalid={invalid} value={value.trainee_instructions ?? ''} disabled={disabled} className="min-h-24" onChange={event => patch({ trainee_instructions: event.target.value || null })} />}</Field></div><div className="mt-5 space-y-4">{value.sets.map((set, index) => <SetPrescriptionEditor key={`${set.set_number}-${index}`} mode={mode} value={set} disabled={disabled} canMoveUp={index > 0} canMoveDown={index < value.sets.length - 1} onChange={next => updateSet(index, next)} onRemove={() => removeSet(index)} onDuplicate={() => duplicateSet(index)} onMove={direction => moveSet(index, direction)} />)}{!disabled && <Button type="button" variant="secondary" onClick={addSet}><Plus aria-hidden="true" className="size-4" />Add set</Button>}</div></article>
}

function renumber(sets: WorkoutSetPrescriptionData[]) { return sets.map((item, index) => ({ ...item, set_number: index + 1 })) }
export function newPrescription(mode: ExerciseTrackingMode): WorkoutSetPrescriptionData {
  const base: WorkoutSetPrescriptionData = { set_number: 1, set_type: 'working', repetitions_min: null, repetitions_max: null, target_duration_seconds: null, target_distance_value: null, target_distance_unit: null, target_load_original_value: null, target_load_original_unit: null, target_assistance_original_value: null, target_assistance_original_unit: null, target_rpe: null, target_rir: null, rest_seconds: null, tempo: null, instructions: null }
  if (mode === 'duration') return { ...base, target_duration_seconds: 30 }
  if (mode === 'distance_and_duration') return { ...base, target_duration_seconds: 600, target_distance_value: 1, target_distance_unit: 'kilometers' }
  return { ...base, repetitions_min: 8, repetitions_max: 10 }
}
