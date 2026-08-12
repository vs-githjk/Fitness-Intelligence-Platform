import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../auth'
import { AppShell } from './AppShell'

class MemoryStorage implements Storage {
  private values = new Map<string, string>()
  get length() { return this.values.size }
  clear() { this.values.clear() }
  getItem(key: string) { return this.values.get(key) ?? null }
  key(index: number) { return [...this.values.keys()][index] ?? null }
  removeItem(key: string) { this.values.delete(key) }
  setItem(key: string, value: string) { this.values.set(key, value) }
}

beforeEach(() => {
  const storage = new MemoryStorage()
  storage.setItem('access_token', 'demo-token')
  storage.setItem('user', JSON.stringify({
    id: 'demo-id', email: 'demo@synthetic.invalid', first_name: 'Demo', last_name: 'Trainee', role: 'trainee', is_demo: true,
  }))
  vi.stubGlobal('localStorage', storage)
})

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

describe('demo workspace shell', () => {
  it('shows the read-only indicator and exits without retaining the session', () => {
    renderWithQueryClient(<MemoryRouter initialEntries={['/trainee/today']}><AuthProvider><Routes><Route path="/trainee/today" element={<AppShell><p>Demo content</p></AppShell>} /><Route path="/login" element={<p>Signed out</p>} /></Routes></AuthProvider></MemoryRouter>)
    expect(screen.getByRole('status', { name: 'Demo workspace' })).toHaveTextContent('changes are disabled')
    fireEvent.click(screen.getAllByRole('button', { name: 'Exit demo' })[0])
    expect(screen.getByText('Signed out')).toBeInTheDocument()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('renders Today on the Iron Editorial mb-page ground without a route-scoped theme (C2.1)', () => {
    // The Cycle-1 seam is retired: theme is resolved once and applied to <html> by
    // ThemeProvider, so <main> carries no per-surface data-theme. morningBrief now only
    // selects the full-bleed mb-page layout.
    renderWithQueryClient(<MemoryRouter initialEntries={['/trainee/today']}><AuthProvider><AppShell morningBrief><p>Today content</p></AppShell></AuthProvider></MemoryRouter>)
    const main = document.getElementById('main-content')!
    expect(main).not.toHaveAttribute('data-theme')
    expect(main.className).toContain('bg-mb-page')
  })

  it('never stamps a per-main data-theme (theme is global)', () => {
    renderWithQueryClient(<MemoryRouter initialEntries={['/trainee/progress']}><AuthProvider><AppShell><p>Legacy content</p></AppShell></AuthProvider></MemoryRouter>)
    expect(document.getElementById('main-content')!).not.toHaveAttribute('data-theme')
  })

  it('adds responsive coach Programming navigation without future Programs', () => {
    const storage = new MemoryStorage()
    storage.setItem('access_token', 'coach-token')
    storage.setItem('user', JSON.stringify({ id: 'coach-id', email: 'coach@example.com', first_name: 'Test', last_name: 'Coach', role: 'coach', is_demo: false }))
    vi.stubGlobal('localStorage', storage)
    renderWithQueryClient(<MemoryRouter initialEntries={['/coach/programming/exercises']}><AuthProvider><AppShell><p>Programming content</p></AppShell></AuthProvider></MemoryRouter>)
    expect(screen.getAllByAltText('FitIntel 360')).toHaveLength(2)
    const programming = screen.getAllByRole('link', { name: 'Programming' })
    expect(programming).toHaveLength(2)
    expect(programming.every(link => link.getAttribute('aria-current') === 'page')).toBe(true)
    expect(screen.queryByRole('link', { name: 'Programs' })).not.toBeInTheDocument()
  })
})

describe('four-tab trainee IA (C2.1)', () => {
  function shell(entry: string) {
    return renderWithQueryClient(<MemoryRouter initialEntries={[entry]}><AuthProvider><AppShell><p>content</p></AppShell></AuthProvider></MemoryRouter>)
  }

  it('exposes exactly the four top-level trainee destinations', () => {
    shell('/trainee/today')
    for (const label of ['Today', 'Train', 'Progress', 'You']) {
      expect(screen.getAllByRole('link', { name: label }).length).toBeGreaterThan(0)
    }
    // Retired top-level items (they now live inside a tab, not on the primary bar).
    expect(screen.queryByRole('link', { name: 'Assessment' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Workouts' })).not.toBeInTheDocument()
  })

  it('keeps Workouts reachable under Progress', () => {
    shell('/trainee/progress')
    expect(screen.getAllByRole('link', { name: 'Workouts' })[0]).toHaveAttribute('href', '/trainee/workouts')
    expect(screen.getAllByRole('link', { name: 'Daily' })[0]).toHaveAttribute('href', '/trainee/progress')
  })

  it('keeps Assessment, Profile, and Settings reachable under You', () => {
    shell('/settings')
    expect(screen.getAllByRole('link', { name: 'Assessment' })[0]).toHaveAttribute('href', '/onboarding')
    expect(screen.getAllByRole('link', { name: 'Profile' })[0]).toHaveAttribute('href', '/profile')
    expect(screen.getAllByRole('link', { name: 'Settings' })[0]).toHaveAttribute('href', '/settings')
  })

  it('marks the owning tab active for a relocated route (execution under Train)', () => {
    shell('/trainee/workouts/w1')
    const trainActive = screen.getAllByRole('link', { name: 'Train' }).some((l) => l.getAttribute('aria-current') === 'page')
    expect(trainActive).toBe(true)
  })
})

function renderWithQueryClient(children: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{children}</QueryClientProvider>)
}
