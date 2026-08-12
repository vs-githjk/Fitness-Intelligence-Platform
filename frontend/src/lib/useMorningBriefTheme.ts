// Route-scoped theme resolution for the Morning Brief "Today" surface
// (Experience Cycle 1, final polish).
//
// Today is the only fully migrated (--mb-* token) surface, so its dark rendering is
// scoped to its own content region via a `data-theme` attribute rather than the
// document root — a global flip would strand Morning Brief primitives (e.g.
// SessionSlip) that are reused on unmigrated, light-only legacy screens.
//
// Resolution: an explicit stored app preference ('light' | 'dark') wins; otherwise
// Today follows the operating system's `prefers-color-scheme`. There is no in-app
// theme switch (adding one would expand scope), so in practice dark Today is reached
// by a trainee whose device is in dark mode. The OS snapshot is read synchronously,
// so the correct theme is present on first paint — no flash.

import { useSyncExternalStore } from 'react'
import { getStoredThemePreference, prefersDark, ResolvedTheme } from '../theme'

function subscribeOsScheme(onChange: () => void): () => void {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return () => {}
  const query = window.matchMedia('(prefers-color-scheme: dark)')
  query.addEventListener('change', onChange)
  return () => query.removeEventListener('change', onChange)
}

export function useMorningBriefTheme(): ResolvedTheme {
  const osDark = useSyncExternalStore(subscribeOsScheme, prefersDark, () => false)
  const stored = getStoredThemePreference()
  // An explicit light/dark choice is honored everywhere; 'system' or no stored
  // preference means Today tracks the OS.
  if (stored === 'light' || stored === 'dark') return stored
  return osDark ? 'dark' : 'light'
}
