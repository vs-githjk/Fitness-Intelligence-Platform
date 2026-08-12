// Durable theme-preference persistence (Experience Cycle 2, C2.0).
//
// The backend already persists the preference: UserPreferences.theme (nullable
// String(20), Alembic head 0017 / ADR-0012) with GET/PUT /me/preferences. No backend
// change is required. These helpers are the frontend plumbing C2.1 will mount to
// hydrate the theme on login and to save an explicit user choice; nothing consumes
// them at runtime yet (the app stays visually stable in C2.0).
//
// PUT applies a partial update server-side (Pydantic exclude_unset), so sending only
// { theme } leaves timezone / units / locale untouched.

import { api } from '../api'
import { isThemePreference, ThemePreference } from '../theme'
import type { UserPreferences } from '../types'

export const PREFERENCES_PATH = '/me/preferences'

// The backend column accepts any <=20-char string, so a stored value may be null or
// an unrecognized legacy string. Parse defensively: unknown -> null ("no explicit
// preference"), so a bad stored value never forces an unintended theme.
export function parsePersistedTheme(value: string | null | undefined): ThemePreference | null {
  return isThemePreference(value) ? value : null
}

export async function fetchThemePreference(): Promise<ThemePreference | null> {
  const preferences = await api<UserPreferences>(PREFERENCES_PATH)
  return parsePersistedTheme(preferences.theme)
}

export async function persistThemePreference(
  preference: ThemePreference,
): Promise<UserPreferences> {
  return api<UserPreferences>(PREFERENCES_PATH, {
    method: 'PUT',
    body: JSON.stringify({ theme: preference }),
  })
}
