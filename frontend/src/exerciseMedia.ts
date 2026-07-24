import { api, apiUpload } from './api'
import { ExerciseDetail } from './types'

// Exercise media client. Reuses the shared media transport (`apiUpload`) — no second
// upload pipeline — targeting the coach exercise media routes, which return the
// refreshed exercise detail so the editor updates in one round trip.

export type ExerciseMediaSlot = 'primary_image' | 'secondary_image' | 'demonstration_video'

export const EXERCISE_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
export const EXERCISE_VIDEO_TYPES = ['video/mp4', 'video/webm']
export const EXERCISE_IMAGE_MAX_BYTES = 5 * 1024 * 1024
export const EXERCISE_VIDEO_MAX_BYTES = 25 * 1024 * 1024

export function isVideoSlot(slot: ExerciseMediaSlot): boolean {
  return slot === 'demonstration_video'
}

export function acceptFor(slot: ExerciseMediaSlot): string {
  return (isVideoSlot(slot) ? EXERCISE_VIDEO_TYPES : EXERCISE_IMAGE_TYPES).join(',')
}

/** Human-readable client-side pre-check; the server remains the source of truth. */
export function validateExerciseMedia(slot: ExerciseMediaSlot, file: File): string | null {
  const video = isVideoSlot(slot)
  const types = video ? EXERCISE_VIDEO_TYPES : EXERCISE_IMAGE_TYPES
  const max = video ? EXERCISE_VIDEO_MAX_BYTES : EXERCISE_IMAGE_MAX_BYTES
  if (!types.includes(file.type)) {
    return video ? 'Choose an MP4 or WEBM video.' : 'Choose a JPEG, PNG, WEBP, or GIF image.'
  }
  if (file.size > max) {
    return video ? 'That video is larger than 25 MB.' : 'That image is larger than 5 MB.'
  }
  return null
}

export function setExerciseMedia(exerciseId: string, slot: ExerciseMediaSlot, file: File): Promise<ExerciseDetail> {
  const form = new FormData()
  form.append('file', file)
  return apiUpload<ExerciseDetail>(`/coach/exercises/${exerciseId}/media/${slot}`, form, { method: 'PUT' })
}

export function removeExerciseMedia(exerciseId: string, slot: ExerciseMediaSlot): Promise<ExerciseDetail> {
  return api<ExerciseDetail>(`/coach/exercises/${exerciseId}/media/${slot}`, { method: 'DELETE' })
}
