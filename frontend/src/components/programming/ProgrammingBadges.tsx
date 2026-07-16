/* eslint-disable react-refresh/only-export-components -- labels and badge primitives share one domain vocabulary */
import { Badge } from '../ui'
import { ExerciseTrackingMode, WorkoutTemplateStatus } from '../../types'
import { titleize } from '../../lib/format'

const trackingLabels: Record<ExerciseTrackingMode, string> = {
  repetitions_and_load: 'Reps + load',
  repetitions_only: 'Repetitions',
  duration: 'Duration',
  distance_and_duration: 'Distance + duration',
  bodyweight_or_assisted_repetitions: 'Bodyweight / assisted',
}

export function TrackingModeBadge({ mode }: { mode: ExerciseTrackingMode }) {
  return <Badge tone="info">{trackingLabels[mode]}</Badge>
}

export function TemplateStatusBadge({ status, hasDraft }: { status: WorkoutTemplateStatus; hasDraft?: boolean }) {
  if (status === 'archived') return <Badge tone="neutral">Archived</Badge>
  return <Badge tone={hasDraft ? 'attention' : 'positive'}>{hasDraft ? 'Draft available' : 'Published'}</Badge>
}

export function PublicationBadge({ draft, published }: { draft: boolean; published: boolean }) {
  if (draft) return <Badge tone="attention">Draft</Badge>
  if (published) return <Badge tone="positive">Published</Badge>
  return <Badge tone="neutral">Unpublished</Badge>
}

export function trackingModeLabel(mode: ExerciseTrackingMode) { return trackingLabels[mode] }
export function sectionLabel(value: string) { return titleize(value.replace('_', ' ')) }
