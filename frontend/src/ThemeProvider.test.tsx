import { afterEach, describe, expect, it, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from './auth'
import { ThemeProvider } from './ThemeProvider'
import { THEME_STORAGE_KEY } from './theme'

// The server reconciliation is exercised separately (themePreference.test); here we
// verify the role-aware application to the document root.
vi.mock('./lib/themePreference', () => ({
  fetchThemePreference: vi.fn(async () => null),
  persistThemePreference: vi.fn(async () => ({})),
}))

function memoryStorage(): Storage {
  const map = new Map<string, string>()
  return {
    get length() { return map.size },
    clear: () => map.clear(),
    getItem: (key) => (map.has(key) ? map.get(key)! : null),
    key: (index) => Array.from(map.keys())[index] ?? null,
    removeItem: (key) => { map.delete(key) },
    setItem: (key, value) => { map.set(key, String(value)) },
  }
}

function signIn(role: 'trainee' | 'coach'): Storage {
  const storage = memoryStorage()
  storage.setItem('access_token', 'token')
  storage.setItem('user', JSON.stringify({ id: 'u', email: 'e@x.io', first_name: 'A', last_name: 'B', role, is_demo: false }))
  vi.stubGlobal('localStorage', storage)
  return storage
}

function renderThemed() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AuthProvider>
          <ThemeProvider><div /></ThemeProvider>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

function appliedTheme(): string | null {
  return document.documentElement.getAttribute('data-theme')
}

afterEach(() => {
  vi.unstubAllGlobals()
  document.documentElement.removeAttribute('data-theme')
})

describe('ThemeProvider role-aware application', () => {
  it('applies dark for a trainee with no explicit preference', async () => {
    signIn('trainee')
    renderThemed()
    await waitFor(() => expect(appliedTheme()).toBe('dark'))
  })

  it('applies light for a coach with no explicit preference', async () => {
    signIn('coach')
    renderThemed()
    await waitFor(() => expect(appliedTheme()).toBe('light'))
  })

  it('honors an explicit stored light preference, overriding the trainee default', async () => {
    const storage = signIn('trainee')
    storage.setItem(THEME_STORAGE_KEY, 'light')
    renderThemed()
    await waitFor(() => expect(appliedTheme()).toBe('light'))
  })
})
