import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  applyResolvedTheme,
  DEFAULT_THEME_PREFERENCE,
  getStoredThemePreference,
  isThemePreference,
  resolveTheme,
  storeThemePreference,
  THEME_STORAGE_KEY,
} from './theme'

// In-memory Storage so tests do not depend on the runtime's localStorage,
// which is a non-persisting stub under this jsdom/node build.
function createMemoryStorage(): Storage {
  const map = new Map<string, string>()
  return {
    get length() {
      return map.size
    },
    clear: () => map.clear(),
    getItem: (key) => (map.has(key) ? map.get(key)! : null),
    key: (index) => Array.from(map.keys())[index] ?? null,
    removeItem: (key) => {
      map.delete(key)
    },
    setItem: (key, value) => {
      map.set(key, String(value))
    },
  }
}

function mockPrefersDark(matches: boolean) {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches: query.includes('dark') ? matches : false,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
  }))
}

afterEach(() => {
  vi.unstubAllGlobals()
  document.documentElement.removeAttribute('data-theme')
})

describe('theme foundation', () => {
  it('ships light-only by default so legacy surfaces are unchanged', () => {
    expect(DEFAULT_THEME_PREFERENCE).toBe('light')
  })

  it('validates theme preferences', () => {
    expect(isThemePreference('light')).toBe(true)
    expect(isThemePreference('dark')).toBe(true)
    expect(isThemePreference('system')).toBe(true)
    expect(isThemePreference('midnight')).toBe(false)
    expect(isThemePreference(null)).toBe(false)
  })

  it('resolves explicit preferences directly', () => {
    expect(resolveTheme('light')).toBe('light')
    expect(resolveTheme('dark')).toBe('dark')
  })

  it('resolves the system preference from the OS setting', () => {
    mockPrefersDark(true)
    expect(resolveTheme('system')).toBe('dark')
    mockPrefersDark(false)
    expect(resolveTheme('system')).toBe('light')
  })

  it('round-trips a stored preference and ignores invalid values', () => {
    const storage = createMemoryStorage()
    expect(getStoredThemePreference(storage)).toBeNull()
    storeThemePreference('dark', storage)
    expect(getStoredThemePreference(storage)).toBe('dark')
    storage.setItem(THEME_STORAGE_KEY, 'not-a-theme')
    expect(getStoredThemePreference(storage)).toBeNull()
  })

  it('degrades safely when storage is unavailable', () => {
    expect(getStoredThemePreference(null)).toBeNull()
    expect(() => storeThemePreference('dark', null)).not.toThrow()
  })

  it('applies the resolved theme to the document root', () => {
    applyResolvedTheme('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    applyResolvedTheme('light')
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
  })
})
