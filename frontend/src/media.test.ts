import { afterEach, expect, it, vi } from 'vitest'
import { ApiError } from './api'
import { deleteMedia, getMediaAsset, mediaAssetKey, uploadMedia } from './media'

class MemoryStorage implements Storage { private values = new Map<string, string>(); get length() { return this.values.size } clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null } key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) } setItem(key: string, value: string) { this.values.set(key, value) } }

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })

function withToken() { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); vi.stubGlobal('localStorage', storage) }
function captureFetch(response: Response) { const calls: Array<{ url: string; init?: RequestInit }> = []; vi.stubGlobal('fetch', vi.fn((url: RequestInfo | URL, init?: RequestInit) => { calls.push({ url: String(url), init }); return Promise.resolve(response) })); return calls }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }

const asset = { id: 'm1', owner_user_id: 'u1', uploader_user_id: 'u1', purpose: 'generic', visibility: 'private', lifecycle_status: 'active', content_type: 'image/png', byte_size: 10, checksum_sha256: 'x', original_filename: 'p.png', content_url: '/media/m1/content', created_at: '', updated_at: '', deleted_at: null, replaced_at: null }

it('uploadMedia sends multipart without forcing a JSON Content-Type and keeps auth', async () => {
  withToken()
  const calls = captureFetch(ok(asset, 201))
  await uploadMedia(new File([new Uint8Array([1, 2, 3])], 'p.png', { type: 'image/png' }), { purpose: 'avatar' })
  const { init } = calls[0]
  const headers = (init?.headers ?? {}) as Record<string, string>
  expect(headers['Content-Type']).toBeUndefined()
  expect(headers['content-type']).toBeUndefined()
  expect(headers.Authorization).toBe('Bearer test-token')
  expect(init?.method).toBe('POST')
  expect(init?.body).toBeInstanceOf(FormData)
  expect((init?.body as FormData).get('purpose')).toBe('avatar')
})

it('uploadMedia surfaces ApiError with standard error handling', async () => {
  withToken()
  captureFetch(new Response(JSON.stringify({ detail: { code: 'media_too_large', message: 'Too big' } }), { status: 413, headers: { 'Content-Type': 'application/json' } }))
  await expect(uploadMedia(new File(['x'], 'p.png', { type: 'image/png' }))).rejects.toBeInstanceOf(ApiError)
})

it('getMediaAsset reads JSON metadata for an asset', async () => {
  withToken()
  const calls = captureFetch(ok(asset))
  const result = await getMediaAsset('m1')
  expect(calls[0].url).toContain('/media/m1')
  expect(result.content_url).toBe('/media/m1/content')
})

it('deleteMedia issues a DELETE and tolerates a 204 no-content response', async () => {
  withToken()
  const calls = captureFetch(new Response(null, { status: 204 }))
  await expect(deleteMedia('m1')).resolves.toBeUndefined()
  expect(calls[0].init?.method).toBe('DELETE')
})

it('mediaAssetKey is identity-scoped so caches never leak across accounts', () => {
  const scope = ['account', 'coach-1']
  expect(mediaAssetKey(scope, 'm1')).toEqual(['account', 'coach-1', 'media-asset', 'm1'])
  expect(mediaAssetKey(['account', 'coach-2'], 'm1')).not.toEqual(mediaAssetKey(scope, 'm1'))
})
