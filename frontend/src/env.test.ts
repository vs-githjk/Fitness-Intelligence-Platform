import { describe, expect, it } from 'vitest'
import { loadStoredUser } from './auth'
import { createAppConfig } from './env'

describe('client environment contract', () => {
  it('keeps the localhost API fallback only for local builds', () => {
    expect(createAppConfig({ VITE_APP_ENV: 'local' }).apiUrl).toBe(
      'http://localhost:8000/api/v1',
    )
  })

  it('requires a non-local HTTPS API for staging', () => {
    expect(() => createAppConfig({ VITE_APP_ENV: 'staging' })).toThrow(/VITE_API_URL is required/)
    expect(() =>
      createAppConfig({
        VITE_APP_ENV: 'staging',
        VITE_API_URL: 'http://localhost:8000/api/v1',
      }),
    ).toThrow(/non-local HTTPS URL/)
    expect(
      createAppConfig({
        VITE_APP_ENV: 'staging',
        VITE_API_URL: 'https://fitness-api-staging.example.com/api/v1/',
      }).apiUrl,
    ).toBe('https://fitness-api-staging.example.com/api/v1')
  })
})

class MemoryStorage implements Storage {
  private values = new Map<string, string>()
  get length() { return this.values.size }
  clear() { this.values.clear() }
  getItem(key: string) { return this.values.get(key) ?? null }
  key(index: number) { return [...this.values.keys()][index] ?? null }
  removeItem(key: string) { this.values.delete(key) }
  setItem(key: string, value: string) { this.values.set(key, value) }
}

describe('stored session validation', () => {

  it('clears a partial session instead of redirecting away from sign-in', () => {
    const storage = new MemoryStorage()
    storage.setItem('user', JSON.stringify({ id: 'stale' }))
    expect(loadStoredUser(storage)).toBeNull()
    expect(storage.getItem('user')).toBeNull()
    expect(storage.getItem('access_token')).toBeNull()
  })
})
