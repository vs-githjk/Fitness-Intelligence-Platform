// Morning Brief theme foundation (Experience Cycle 1, Phase A).
// Pure, framework-free helpers for resolving and persisting the theme
// preference. The React surface lives in ThemeProvider.tsx.
//
// The application currently ships light-only. The default preference is
// therefore 'light', which keeps every legacy surface rendering exactly as
// before. When migrated surfaces begin consuming the --mb-* tokens, the
// default can move to 'system' without any change to this module.

export type ThemePreference = 'light' | 'dark' | 'system'
export type ResolvedTheme = 'light' | 'dark'

export const THEME_STORAGE_KEY = 'fitintel-theme'
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
    return isThemePreference(raw) ? raw : null
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
