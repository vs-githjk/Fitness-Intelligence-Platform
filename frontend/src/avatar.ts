import { api, apiUpload } from './api'
import { MediaAsset } from './types'

// Avatar client helpers. These reuse the Phase 2 media transport (`apiUpload`) and
// never build a second upload pipeline: the same multipart request the media
// endpoint accepts is sent to the identity avatar route with a PUT.

export const AVATAR_MAX_BYTES = 5 * 1024 * 1024
export const AVATAR_ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
export const AVATAR_ACCEPT_ATTR = AVATAR_ACCEPTED_TYPES.join(',')

/** A human-readable client-side pre-check; the server remains the source of truth. */
export function validateAvatarFile(file: File): string | null {
  if (!AVATAR_ACCEPTED_TYPES.includes(file.type)) {
    return 'Choose a JPEG, PNG, WEBP, or GIF image.'
  }
  if (file.size > AVATAR_MAX_BYTES) {
    return 'That image is larger than 5 MB. Choose a smaller file.'
  }
  return null
}

/** Two-letter initials fallback shown when a person has no photo. */
export function initialsFrom(name: string | null | undefined): string {
  const parts = (name ?? '').trim().split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

export function setAvatar(file: File): Promise<MediaAsset> {
  const form = new FormData()
  form.append('file', file)
  return apiUpload<MediaAsset>('/me/avatar', form, { method: 'PUT' })
}

export function removeAvatar(): Promise<void> {
  return api<void>('/me/avatar', { method: 'DELETE' })
}
