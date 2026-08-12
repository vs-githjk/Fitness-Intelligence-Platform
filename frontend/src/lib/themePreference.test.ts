import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { UserPreferences } from '../types'

vi.mock('../api', () => ({ api: vi.fn() }))
import { api } from '../api'
import {
  fetchThemePreference,
  parsePersistedTheme,
  persistThemePreference,
  PREFERENCES_PATH,
} from './themePreference'

const mockApi = vi.mocked(api)

function preferencesWithTheme(theme: string | null): UserPreferences {
  return { theme } as unknown as UserPreferences
}

beforeEach(() => {
  mockApi.mockReset()
})

describe('parsePersistedTheme', () => {
  it('accepts the three known preferences', () => {
    expect(parsePersistedTheme('light')).toBe('light')
    expect(parsePersistedTheme('dark')).toBe('dark')
    expect(parsePersistedTheme('system')).toBe('system')
  })

  it('treats null, undefined, and unknown legacy strings as no preference', () => {
    expect(parsePersistedTheme(null)).toBeNull()
    expect(parsePersistedTheme(undefined)).toBeNull()
    expect(parsePersistedTheme('midnight')).toBeNull()
  })
})

describe('fetchThemePreference', () => {
  it('parses a valid stored theme', async () => {
    mockApi.mockResolvedValue(preferencesWithTheme('dark'))
    expect(await fetchThemePreference()).toBe('dark')
    expect(mockApi).toHaveBeenCalledWith(PREFERENCES_PATH)
  })

  it('returns null for an absent or unrecognized stored theme', async () => {
    mockApi.mockResolvedValue(preferencesWithTheme(null))
    expect(await fetchThemePreference()).toBeNull()
    mockApi.mockResolvedValue(preferencesWithTheme('twilight'))
    expect(await fetchThemePreference()).toBeNull()
  })
})

describe('persistThemePreference', () => {
  it('sends only the theme field via a partial PUT', async () => {
    mockApi.mockResolvedValue(preferencesWithTheme('light'))
    await persistThemePreference('light')
    expect(mockApi).toHaveBeenCalledWith(PREFERENCES_PATH, {
      method: 'PUT',
      body: JSON.stringify({ theme: 'light' }),
    })
  })
})
