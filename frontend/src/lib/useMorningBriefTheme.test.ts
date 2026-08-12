import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useMorningBriefTheme } from './useMorningBriefTheme'
import { THEME_STORAGE_KEY } from '../theme'

function mockMatchMedia(matches: boolean) {
  vi.stubGlobal('matchMedia', (query: string) => ({
    matches,
    media: query,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    onchange: null,
    dispatchEvent: () => false,
  }))
}

function mockStorage() {
  const map = new Map<string, string>()
  vi.stubGlobal('localStorage', {
    getItem: (k: string) => (map.has(k) ? map.get(k)! : null),
    setItem: (k: string, v: string) => void map.set(k, v),
    removeItem: (k: string) => void map.delete(k),
    clear: () => map.clear(),
    key: () => null,
    length: 0,
  })
}

beforeEach(mockStorage)
afterEach(() => vi.unstubAllGlobals())

describe('useMorningBriefTheme', () => {
  it('follows the OS when there is no stored preference', () => {
    mockMatchMedia(true)
    expect(renderHook(() => useMorningBriefTheme()).result.current).toBe('dark')
    mockMatchMedia(false)
    expect(renderHook(() => useMorningBriefTheme()).result.current).toBe('light')
  })

  it('follows the OS when the stored preference is system', () => {
    window.localStorage.setItem(THEME_STORAGE_KEY, 'system')
    mockMatchMedia(true)
    expect(renderHook(() => useMorningBriefTheme()).result.current).toBe('dark')
  })

  it('honors an explicit light/dark preference over the OS', () => {
    mockMatchMedia(true) // OS dark
    window.localStorage.setItem(THEME_STORAGE_KEY, 'light')
    expect(renderHook(() => useMorningBriefTheme()).result.current).toBe('light')
    window.localStorage.setItem(THEME_STORAGE_KEY, 'dark')
    mockMatchMedia(false) // OS light
    expect(renderHook(() => useMorningBriefTheme()).result.current).toBe('dark')
  })
})
