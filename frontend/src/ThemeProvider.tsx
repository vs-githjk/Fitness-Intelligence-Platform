// Morning Brief theme switching infrastructure (Experience Cycle 1, Phase A).
// Applies the resolved theme to <html data-theme="…"> and exposes it via
// context. Defaults to 'light' so the current single-theme app is unchanged;
// migrated surfaces will later move the default to 'system'.
//
// The context and the `useTheme` hook live in ./theme-context so this file
// exports only the component (clean fast-refresh boundary).

import { ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { ThemeContext, ThemeContextValue } from './theme-context'
import {
  applyResolvedTheme,
  DEFAULT_THEME_PREFERENCE,
  getStoredThemePreference,
  prefersDark,
  ResolvedTheme,
  resolveTheme,
  storeThemePreference,
  ThemePreference,
} from './theme'

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(
    () => getStoredThemePreference() ?? DEFAULT_THEME_PREFERENCE,
  )
  const [resolved, setResolved] = useState<ResolvedTheme>(() => resolveTheme(preference))

  // Apply the resolved theme to the document root whenever the preference changes.
  useEffect(() => {
    const next = resolveTheme(preference)
    setResolved(next)
    applyResolvedTheme(next)
  }, [preference])

  // Track OS changes only while following the system preference.
  useEffect(() => {
    if (preference !== 'system' || typeof window === 'undefined' || typeof window.matchMedia !== 'function') return
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => {
      const next: ResolvedTheme = prefersDark() ? 'dark' : 'light'
      setResolved(next)
      applyResolvedTheme(next)
    }
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [preference])

  const setPreference = useCallback((next: ThemePreference) => {
    storeThemePreference(next)
    setPreferenceState(next)
  }, [])

  const value = useMemo<ThemeContextValue>(
    () => ({ preference, resolved, setPreference }),
    [preference, resolved, setPreference],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
