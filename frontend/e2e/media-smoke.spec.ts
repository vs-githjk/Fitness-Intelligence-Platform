import { APIRequestContext, expect, request, test } from '@playwright/test'
import { apiUrl } from './config'

// 1x1 transparent PNG.
const PNG = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
  'base64',
)

async function login(context: APIRequestContext, email: string): Promise<string> {
  const response = await context.post(`${apiUrl}/auth/login`, { data: { email, password: 'DemoPass123!' } })
  expect(response.ok()).toBeTruthy()
  return (await response.json()).access_token
}

test('media API: authorized upload, metadata, content, and soft delete', async () => {
  const context = await request.newContext()
  const token = await login(context, 'coach@fitness.example.com')
  const authHeaders = { Authorization: `Bearer ${token}` }

  const upload = await context.post(`${apiUrl}/media`, {
    headers: authHeaders,
    multipart: { file: { name: 'smoke.png', mimeType: 'image/png', buffer: PNG }, purpose: 'generic' },
  })
  expect(upload.status()).toBe(201)
  const asset = await upload.json()
  expect(asset.storage_key).toBeUndefined()
  expect(asset.content_type).toBe('image/png')
  expect(asset.lifecycle_status).toBe('active')
  expect(asset.content_url).toBe(`/media/${asset.id}/content`)

  const meta = await context.get(`${apiUrl}/media/${asset.id}`, { headers: authHeaders })
  expect(meta.status()).toBe(200)
  expect((await meta.json()).storage_key).toBeUndefined()

  const content = await context.get(`${apiUrl}/media/${asset.id}/content`, { headers: authHeaders })
  expect(content.status()).toBe(200)
  expect(content.headers()['content-type']).toContain('image/png')
  expect((await content.body()).length).toBe(PNG.length)

  const removed = await context.delete(`${apiUrl}/media/${asset.id}`, { headers: authHeaders })
  expect(removed.status()).toBe(204)
  const gone = await context.get(`${apiUrl}/media/${asset.id}`, { headers: authHeaders })
  expect(gone.status()).toBe(404)

  await context.dispose()
})

test('media API: mutations are blocked for demo accounts', async () => {
  const context = await request.newContext()
  const demo = await context.post(`${apiUrl}/auth/demo-session`, { data: { role: 'trainee' } })
  expect(demo.ok()).toBeTruthy()
  const token = (await demo.json()).access_token
  const blocked = await context.post(`${apiUrl}/media`, {
    headers: { Authorization: `Bearer ${token}` },
    multipart: { file: { name: 'x.png', mimeType: 'image/png', buffer: PNG } },
  })
  expect(blocked.status()).toBe(403)
  expect((await blocked.json()).detail.code).toBe('demo_read_only')
  await context.dispose()
})
