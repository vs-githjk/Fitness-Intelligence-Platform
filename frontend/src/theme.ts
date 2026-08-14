// Morning Brief theme foundation (Experience Cycle 1, Phase A).
// Pure, framework-free helpers for resolving and persisting the theme
// preference. The React surface lives in ThemeProvider.tsx.
//
// The application currently ships light-only. The default preference is
// therefore 'light', which keeps every legacy surface rendering exactly as
// before. When migrated surfaces begin consuming the --mb-* tokens, the
// default can move to 'system' without any change to this module.

import type { Role } from './types'

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'vytal-theme'
// Retired brand key. Read once and migrated forward so the rename does not silently
// discard a user's saved theme preference (see getStoredThemePreference).
const LEGACY_THEME_STORAGE_KEY = 'fitintel-theme'
export const DEFAULT_THEME_PREFERENCE: ThemePreference = 'light'

const PREFERENCES: readonly ThemePreference[] = ['light', 'dark', 'system']

export function isThemePreference(value: unknown): value is ThemePreference {
  return typeof value === 'string' && (PREFERENCES as readonly string[]).includes(value)
}

export function prefersDark(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function resolveTheme(preference: ThemePreference): ResolvedTheme {
  if (preference === 'system') return prefersDark() ? 'dark' : 'light'
  return preference
}

// Iron Editorial role defaults (Experience Cycle 2, C2.0): trainee → dark,
// coach → light. This is the resolution mechanism the migrated shell (C2.1) will
// use; it is NOT yet wired into the live ThemeProvider, whose applied default stays
// 'light' (DEFAULT_THEME_PREFERENCE) so the current app is visually unchanged.
export function roleDefaultResolved(role: Role): ResolvedTheme {
  return role === 'trainee' ? 'dark' : 'light'
}

// Frozen precedence (visual-identity-v2 §8): explicit user preference > role default
// > OS. 'system' is the explicit opt-in to the OS; a null/absent preference falls to
// the role default (so a trainee with no stored choice resolves dark regardless of
// OS, a coach light). `osDark` is injected for deterministic testing.
export function resolveThemeForRole(
  preference: ThemePreference | null,
  role: Role,
  osDark: boolean = prefersDark(),
): ResolvedTheme {
  if (preference === 'light' || preference === 'dark') return preference
  if (preference === 'system') return osDark ? 'dark' : 'light'
  return roleDefaultResolved(role)
}

// Storage is dependency-injected (matching auth.ts's loadStoredUser) so the
// helpers are testable without relying on a real localStorage, and degrade
// safely when storage is unavailable (private mode, blocked cookies).
function defaultStorage(): Storage | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export function getStoredThemePreference(
  storage: Storage | null = defaultStorage(),
): ThemePreference | null {
  if (!storage) return null
  try {
    const raw = storage.getItem(THEME_STORAGE_KEY)
    if (isThemePreference(raw)) return raw
    // One-time migration from the retired brand key, so an existing user keeps their
    // saved theme across the Vytal rename instead of reverting to the role default.
    const legacy = storage.getItem(LEGACY_THEME_STORAGE_KEY)
    if (isThemePreference(legacy)) {
      try {
        storage.setItem(THEME_STORAGE_KEY, legacy)
        storage.removeItem(LEGACY_THEME_STORAGE_KEY)
      } catch {
        // Non-fatal: the value still applies for this session even if the copy fails.
      }
      return legacy
    }
    return null
  } catch {
    return null
  }
}

export function storeThemePreference(
  preference: ThemePreference,
  storage: Storage | null = defaultStorage(),
): void {
  if (!storage) return
  try {
    storage.setItem(THEME_STORAGE_KEY, preference)
  } catch {
    // Storage can be unavailable; the theme still applies for the session,
    // it simply is not persisted.
  }
}

export function applyResolvedTheme(
  resolved: ResolvedTheme,
  root: HTMLElement = document.documentElement,
): void {
  root.setAttribute('data-theme', resolved)
}
