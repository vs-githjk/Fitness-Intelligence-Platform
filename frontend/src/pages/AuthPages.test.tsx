import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../auth'
import { DemoPage, ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from './AuthPages'

function renderPage(page: ReactNode) {
  return render(withQueryClient(<MemoryRouter><AuthProvider>{page}</AuthProvider></MemoryRouter>))
}

function withQueryClient(children: ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

class MemoryStorage implements Storage {
  private values = new Map<string, string>()
  get length() { return this.values.size }
  clear() { this.values.clear() }
  getItem(key: string) { return this.values.get(key) ?? null }
  key(index: number) { return [...this.values.keys()][index] ?? null }
  removeItem(key: string) { this.values.delete(key) }
  setItem(key: string, value: string) { this.values.set(key, value) }
}

beforeEach(() => vi.stubGlobal('localStorage', new MemoryStorage()))

afterEach(() => {
  cleanup()
  window.history.replaceState({}, '', '/')
  vi.unstubAllGlobals()
})

describe('role-aware registration', () => {
  it('asks for account type and shows only the selected role fields', () => {
    renderPage(<RegisterPage />)
    expect(screen.getByText('What type of account are you creating?')).toBeInTheDocument()
    expect(screen.queryByLabelText('Coach registration code')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /^Coach/ }))
    expect(screen.getByLabelText('Coach registration code')).toBeInTheDocument()
    expect(screen.queryByLabelText('Coach invitation code')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /^Trainee/ }))
    expect(screen.getByLabelText('Coach invitation code')).toBeInTheDocument()
    expect(screen.queryByLabelText('Coach registration code')).not.toBeInTheDocument()
  })

  it('loads a trainee invitation from the URL and removes it from the address bar', async () => {
    window.history.replaceState({}, '', '/register?role=trainee&invite=private-token')
    renderPage(<RegisterPage />)
    expect(screen.getByLabelText('Coach invitation code')).toHaveValue('private-token')
    await waitFor(() => expect(window.location.search).toBe(''))
  })

  it('does not ask for a role during login', () => {
    renderPage(<LoginPage />)
    // The front door now carries the typographic Iron Editorial wordmark (cover +
    // mobile), not the raster logo — both expose the "Vytal" accessible name.
    expect(screen.getAllByLabelText('Vytal')).toHaveLength(2)
    expect(screen.getByLabelText('Email address')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.queryByText('What type of account are you creating?')).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Explore Demo' })).toHaveAttribute('href', '/demo')
    // Self-service reset is now available from the login page.
    expect(screen.getByRole('link', { name: 'Reset it' })).toHaveAttribute('href', '/forgot-password')
  })

  it('routes a coach using the backend-owned role', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: 'token', token_type: 'bearer',
      user: { id: 'coach-id', email: 'coach@example.com', first_name: 'Test', last_name: 'Coach', role: 'coach' },
    }), { status: 200, headers: { 'Content-Type': 'application/json' } })))
    render(withQueryClient(<MemoryRouter initialEntries={['/login']}><AuthProvider><Routes><Route path="/login" element={<LoginPage />} /><Route path="/coach/dashboard" element={<p>Coach workspace</p>} /></Routes></AuthProvider></MemoryRouter>))
    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'coach@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'CoachPass123!' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Coach workspace')).toBeInTheDocument()
  })

  it('routes a trainee without an assessment to onboarding', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({
        access_token: 'token', token_type: 'bearer',
        user: { id: 'trainee-id', email: 'trainee@example.com', first_name: 'Test', last_name: 'Trainee', role: 'trainee' },
      }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: { code: 'not_started', message: 'No onboarding assessment has been started' } }), { status: 404, headers: { 'Content-Type': 'application/json' } }))
    vi.stubGlobal('fetch', fetchMock)
    render(withQueryClient(<MemoryRouter initialEntries={['/login']}><AuthProvider><Routes><Route path="/login" element={<LoginPage />} /><Route path="/onboarding" element={<p>Start onboarding</p>} /></Routes></AuthProvider></MemoryRouter>))
    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'trainee@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'TraineePass123!' } })
    fireEvent.click(screen.getByRole('button', { name: 'Sign in' }))
    expect(await screen.findByText('Start onboarding')).toBeInTheDocument()
  })
})

describe('self-service password reset', () => {
  it('confirms generically after a request (no account enumeration)', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'accepted', message: 'ok' }), { status: 202, headers: { 'Content-Type': 'application/json' } })))
    renderPage(<ForgotPasswordPage />)
    fireEvent.change(screen.getByLabelText('Email address'), { target: { value: 'someone@example.com' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))
    expect(await screen.findByText(/If an account exists for that address/i)).toBeInTheDocument()
  })

  it('shows an incomplete-link notice when no token is present', () => {
    render(withQueryClient(<MemoryRouter initialEntries={['/reset-password']}><AuthProvider><Routes><Route path="/reset-password" element={<ResetPasswordPage />} /></Routes></AuthProvider></MemoryRouter>))
    expect(screen.getByText('This link is incomplete')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Request a new link' })).toHaveAttribute('href', '/forgot-password')
  })

  it('rejects mismatched passwords before calling the API', () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    render(withQueryClient(<MemoryRouter initialEntries={['/reset-password?token=abc123def456ghi789']}><AuthProvider><Routes><Route path="/reset-password" element={<ResetPasswordPage />} /></Routes></AuthProvider></MemoryRouter>))
    fireEvent.change(screen.getByLabelText('New password'), { target: { value: 'BrandNewPass1' } })
    fireEvent.change(screen.getByLabelText('Confirm new password'), { target: { value: 'Different123' } })
    fireEvent.click(screen.getByRole('button', { name: 'Update password' }))
    expect(screen.getByText('The two passwords do not match.')).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })
})

describe('public demo entry', () => {
  it('starts a trainee demo and routes using the backend-owned role', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: 'demo-token', token_type: 'bearer',
      user: { id: 'demo-trainee', email: 'synthetic@example.invalid', first_name: 'Demo', last_name: 'Trainee', role: 'trainee', is_demo: true },
    }), { status: 200, headers: { 'Content-Type': 'application/json' } })))
    render(withQueryClient(<MemoryRouter initialEntries={['/demo']}><AuthProvider><Routes><Route path="/demo" element={<DemoPage />} /><Route path="/trainee/today" element={<p>Trainee demo workspace</p>} /></Routes></AuthProvider></MemoryRouter>))
    fireEvent.click(screen.getByRole('button', { name: 'View as Trainee' }))
    expect(await screen.findByText('Trainee demo workspace')).toBeInTheDocument()
    expect(JSON.parse(localStorage.getItem('user') ?? '{}')).toMatchObject({ role: 'trainee', is_demo: true })
  })

  it('starts a coach demo and routes to the coach workspace', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      access_token: 'demo-token', token_type: 'bearer',
      user: { id: 'demo-coach', email: 'synthetic@example.invalid', first_name: 'Demo', last_name: 'Coach', role: 'coach', is_demo: true },
    }), { status: 200, headers: { 'Content-Type': 'application/json' } })))
    render(withQueryClient(<MemoryRouter initialEntries={['/demo']}><AuthProvider><Routes><Route path="/demo" element={<DemoPage />} /><Route path="/coach/dashboard" element={<p>Coach demo workspace</p>} /></Routes></AuthProvider></MemoryRouter>))
    fireEvent.click(screen.getByRole('button', { name: 'View as Coach' }))
    expect(await screen.findByText('Coach demo workspace')).toBeInTheDocument()
  })

  it('shows a safe unavailable state without asking for credentials', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      detail: { code: 'demo_unavailable', message: 'The demo workspace is unavailable.' },
    }), { status: 503, headers: { 'Content-Type': 'application/json' } })))
    renderPage(<DemoPage />)
    expect(screen.queryByLabelText('Email address')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Password')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'View as Coach' }))
    expect(await screen.findByText('The demo workspace is unavailable.')).toBeInTheDocument()
  })
})
