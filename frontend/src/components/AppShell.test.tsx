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

function renderWithQueryClient(children: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}>{children}</QueryClientProvider>)
}
