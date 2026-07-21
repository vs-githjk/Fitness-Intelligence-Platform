import { QueryKey } from '@tanstack/react-query'
import { api, apiUpload } from './api'
import { MediaAsset, MediaPurpose } from './types'

// Reusable, identity-scoped media client infrastructure. Phase 2 exposes no media
// UI; these helpers exist so later phases (avatars, exercise media) share one typed,
// authenticated, cache-isolated access path instead of re-inventing it per feature.

export function mediaAssetKey(scope: readonly unknown[], mediaId: string): QueryKey {
  return [...scope, 'media-asset', mediaId]
}

export function uploadMedia(file: File, options: { purpose?: MediaPurpose } = {}): Promise<MediaAsset> {
  const form = new FormData()
  form.append('file', file)
  if (options.purpose) form.append('purpose', options.purpose)
  return apiUpload<MediaAsset>('/media', form)
}

export function getMediaAsset(mediaId: string): Promise<MediaAsset> {
  return api<MediaAsset>(`/media/${encodeURIComponent(mediaId)}`)
}

export function deleteMedia(mediaId: string): Promise<void> {
  return api<void>(`/media/${encodeURIComponent(mediaId)}`, { method: 'DELETE' })
}
