import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { AuthProvider } from '../auth'
import { CoachInvitesPage } from './CoachInvitesPage'

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
  storage.setItem('access_token', 'coach-token')
  storage.setItem('user', JSON.stringify({ id: 'coach-1', email: 'coach@example.com', first_name: 'Test', last_name: 'Coach', role: 'coach', is_demo: false }))
  vi.stubGlobal('localStorage', storage)
})

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

it('explains optional email restriction and manual delivery without offering email sending', async () => {
  mockFetch(() => ok([]))
  renderPage()
  expect(await screen.findByLabelText('Restrict to trainee email (optional)')).toBeVisible()
  expect(screen.getByText(/does not send this invitation by email/i)).toBeVisible()
  expect(screen.getByText(/Leave it blank to allow any eligible trainee possessing the invitation/i)).toBeVisible()
  expect(screen.getByText(/Copy and share the generated link manually/i)).toBeVisible()
  expect(screen.queryByRole('button', { name: /send email/i })).not.toBeInTheDocument()
})

it('submits a blank restriction and exposes one-time manual copy actions', async () => {
  const bodies: unknown[] = []
  const clipboard = { writeText: vi.fn().mockResolvedValue(undefined) }
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: clipboard })
  mockFetch((url, init) => {
    if (init?.method === 'POST') {
      bodies.push(JSON.parse(String(init.body)))
      return ok({ id: 'invite-1', token: 'one-time-token', intended_email: null, expires_at: '2026-07-23T00:00:00Z' }, 201)
    }
    return ok([])
  })
  renderPage()
  await screen.findByLabelText('Restrict to trainee email (optional)')
  fireEvent.click(screen.getByRole('button', { name: 'Create invite' }))
  expect(await screen.findByText('Invitation created—copy it now')).toBeVisible()
  expect(screen.getByText(/shown only now and cannot be recovered after this page is refreshed/i)).toBeVisible()
  expect(bodies).toEqual([{ intended_email: null, expires_in_days: 7 }])

  fireEvent.click(screen.getByRole('button', { name: 'Copy invitation code' }))
  await waitFor(() => expect(clipboard.writeText).toHaveBeenCalledWith('one-time-token'))
  fireEvent.click(screen.getByRole('button', { name: 'Copy invitation link' }))
  await waitFor(() => expect(clipboard.writeText).toHaveBeenCalledWith(expect.stringContaining('#invite=one-time-token')))
  expect(screen.queryByRole('button', { name: /send email/i })).not.toBeInTheDocument()
})

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/coach/invites']}><AuthProvider><CoachInvitesPage /></AuthProvider></MemoryRouter></QueryClientProvider>)
}

function mockFetch(handler: (url: string, init?: RequestInit) => Response) {
  vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init))))
}

function ok(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } })
}
