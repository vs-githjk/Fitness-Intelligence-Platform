// Theme context + hook, kept separate from the provider component so
// ThemeProvider.tsx remains a clean component-only fast-refresh boundary.

import { createContext, useContext } from 'react'
import { ResolvedTheme, ThemePreference } from './theme'

export type ThemeContextValue = {
  preference: ThemePreference
  resolved: ResolvedTheme
  setPreference: (preference: ThemePreference) => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)

export function useTheme(): ThemeContextValue {
  const value = useContext(ThemeContext)
  if (!value) throw new Error('useTheme must be used within a ThemeProvider')
  return value
}
