/* eslint-disable react-refresh/only-export-components -- small skip helpers co-located with the modal */
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api, ApiError } from '../../api'
import { useAccountQueryScope } from '../../auth'
import { ScheduledWorkout, WorkoutScheduleSkipResult, WorkoutSkipKind } from '../../types'
import { Badge, Button, Field, Modal, SegmentedControl, SelectInput, StatusNotice } from '../ui'

const ORDINARY_REASONS: { value: string; label: string }[] = [
  { value: 'time_constraint', label: 'Not enough time' },
  { value: 'schedule_conflict', label: 'Schedule conflict' },
  { value: 'equipment_unavailable', label: 'Equipment unavailable' },
  { value: 'travel', label: 'Travelling' },
  { value: 'coach_instruction', label: 'Coach instruction' },
  { value: 'other', label: 'Another reason' },
]
const SAFETY_REASONS: { value: string; label: string }[] = [
  { value: 'recovery_concern', label: 'Still recovering / need rest' },
  { value: 'pain_or_discomfort', label: 'Pain or unusual discomfort' },
  { value: 'illness_or_unwell', label: 'Feeling unwell' },
  { value: 'other_safety_concern', label: 'Another wellbeing reason' },
]

export function SkipWorkoutModal({
  workout,
  open,
  onClose,
  onSkipped,
}: {
  workout: ScheduledWorkout
  open: boolean
  onClose: () => void
  onSkipped?: (result: WorkoutScheduleSkipResult) => void
}) {
  const scope = useAccountQueryScope()
  const cache = useQueryClient()
  const [kind, setKind] = useState<WorkoutSkipKind>('ordinary')
  const [reason, setReason] = useState('time_constraint')
  const [note, setNote] = useState('')
  const [error, setError] = useState('')

  const reasons = kind === 'ordinary' ? ORDINARY_REASONS : SAFETY_REASONS

  function chooseKind(next: string) {
    const value = next as WorkoutSkipKind
    setKind(value)
    setReason(value === 'ordinary' ? ORDINARY_REASONS[0].value : SAFETY_REASONS[0].value)
  }

  const mutation = useMutation({
    mutationFn: () =>
      api<WorkoutScheduleSkipResult>(`/trainee/workouts/${workout.id}/skip`, {
        method: 'POST',
        body: JSON.stringify({ skip_kind: kind, reason, note: note.trim() || null }),
      }),
    onSuccess: async (result) => {
      setError('')
      await cache.invalidateQueries({ queryKey: [...scope, 'my-training-program'] })
      onSkipped?.(result)
      onClose()
    },
    onError: (caught) => setError(caught instanceof ApiError ? caught.message : 'The workout could not be skipped.'),
  })

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Skip this workout"
      description={`${workout.workout_template_version.name} · ${workout.scheduled_date}`}
    >
      <div className="space-y-5">
        {error && <StatusNotice tone="risk" title="Could not skip workout">{error}</StatusNotice>}

        <SegmentedControl
          label="Why are you skipping?"
          value={kind}
          options={[
            { value: 'ordinary', label: 'Everyday reason' },
            { value: 'safety', label: 'Wellbeing / safety' },
          ]}
          onChange={chooseKind}
        />

        <Field label="Reason">
          {({ id }) => (
            <SelectInput id={id} value={reason} onChange={(e) => setReason(e.target.value)}>
              {reasons.map((r) => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </SelectInput>
          )}
        </Field>

        <Field label="Note" optional help={`${note.length} of 500 characters`}>
          {({ id }) => (
            <textarea
              id={id}
              maxLength={500}
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="control mt-1.5 w-full py-3"
            />
          )}
        </Field>

        {kind === 'safety' ? (
          <StatusNotice tone="info" title="Looking after yourself">
            If you feel unwell or have pain or unusual symptoms, avoid exercising and seek appropriate
            professional guidance when needed. Wellbeing-related skips are reported separately in your
            adherence. This is not medical advice.
          </StatusNotice>
        ) : (
          <StatusNotice tone="info" title="What happens next">
            Skipping records this workout as skipped. You will not be able to start it afterward, but
            you can still view its details.
          </StatusNotice>
        )}

        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button variant="secondary" onClick={onClose}>Keep workout</Button>
          <Button variant="danger" loading={mutation.isPending} onClick={() => mutation.mutate()}>
            Confirm skip
          </Button>
        </div>
      </div>
    </Modal>
  )
}

export function skipDescriptor(kind: WorkoutSkipKind | null | undefined): { label: string; tone: 'attention' | 'risk' } {
  return kind === 'safety'
    ? { label: 'Wellbeing skip', tone: 'risk' }
    : { label: 'Skipped', tone: 'attention' }
}

export function SkipBadge({ kind }: { kind: WorkoutSkipKind | null | undefined }) {
  const { label, tone } = skipDescriptor(kind)
  return <Badge tone={tone}>{label}</Badge>
}
