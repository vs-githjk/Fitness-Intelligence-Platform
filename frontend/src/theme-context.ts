// Theme context + hook, kept separate from the provider component so
// ThemeProvider.tsx remains a clean component-only fast-refresh boundary.

import { createContext, useContext } from 'react'
import { ResolvedTheme, ThemePreference } from './theme'

export type ThemeContextValue = {
  // null = no explicit choice yet (the role default applies). The Settings control
  // surfaces this so it never misrepresents an unset preference as an explicit one.
  preference: ThemePreference | null
  resolved: ResolvedTheme
  setPreference: (preference: ThemePreference) => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)

// Safe default when no provider is present (e.g. a component rendered in isolation in a
// test). In the running app ThemeProvider always wraps, so this fallback is inert.
const DEFAULT_THEME_CONTEXT: ThemeContextValue = {
  preference: null,
  resolved: 'light',
  setPreference: () => {},
}

export function useTheme(): ThemeContextValue {
  return useContext(ThemeContext) ?? DEFAULT_THEME_CONTEXT
}
