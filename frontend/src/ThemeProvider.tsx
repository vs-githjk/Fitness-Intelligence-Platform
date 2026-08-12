// Unified theme controller (Experience Cycle 2, C2.1).
//
// One source of truth: this provider resolves the role-aware theme and applies it to
// the document root (<html data-theme="…">), so the whole trainee experience — shell,
// Today, and not-yet-migrated content pages — shares one coherent resolved theme. The
// Cycle-1 route-scoped dark seam (data-theme on the Today <main>) is retired.
//
// Precedence (visual-identity-v2 §8): explicit user preference > role default
// (trainee dark / coach light) > OS. Mounted inside AuthProvider so the role is known;
// AuthProvider hydrates the user synchronously from localStorage, and the stored
// preference is read synchronously, so the correct theme is applied on first paint —
// no flash. localStorage is the fast local source; the server (/me/preferences) is the
// durable cross-device backup, reconciled after sign-in.

import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { useAuth } from './auth'
import { fetchThemePreference, persistThemePreference } from './lib/themePreference'
import { ThemeContext, ThemeContextValue } from './theme-context'
import {
  applyResolvedTheme,
  getStoredThemePreference,
  prefersDark,
  resolveTheme,
  resolveThemeForRole,
  storeThemePreference,
  ThemePreference,
} from './theme'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const role = user?.role
  const [preference, setPreferenceState] = useState<ThemePreference | null>(() => getStoredThemePreference())
  const [osDark, setOsDark] = useState<boolean>(() => prefersDark())

  // Track OS changes (only affects the resolution when preference === 'system').
  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => setOsDark(query.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  const resolved = useMemo(
    () => (role ? resolveThemeForRole(preference, role, osDark) : resolveTheme(preference ?? 'light')),
    [preference, role, osDark],
  )

  useEffect(() => {
    applyResolvedTheme(resolved)
  }, [resolved])

  // Reconcile with the durable server preference after sign-in. Adopt the server value
  // when present (functional update avoids a dependency on `preference`, so this runs
  // once per identity change, not on every local change).
  useEffect(() => {
    if (!user) return
    let cancelled = false
    fetchThemePreference()
      .then((serverPref) => {
        if (cancelled || !serverPref) return
        storeThemePreference(serverPref)
        setPreferenceState((prev) => (prev === serverPref ? prev : serverPref))
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [user])

  const setPreference = useCallback((next: ThemePreference) => {
    storeThemePreference(next)
    setPreferenceState(next)
    // Best-effort durable persistence; the theme already applied locally.
    persistThemePreference(next).catch(() => {})
  }, [])

  const value = useMemo<ThemeContextValue>(
    () => ({ preference, resolved, setPreference }),
    [preference, resolved, setPreference],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
