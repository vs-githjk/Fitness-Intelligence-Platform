import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import React from 'react'
import { afterEach, expect, it, vi } from 'vitest'
import { accountQueryScope, AuthProvider } from '../../auth'
import { StarterLibrary, StarterLibraryProgram } from './StarterLibrary'

class MemoryStorage implements Storage { private v = new Map<string, string>(); get length() { return this.v.size } clear() { this.v.clear() } getItem(k: string) { return this.v.get(k) ?? null } key(i: number) { return [...this.v.keys()][i] ?? null } removeItem(k: string) { this.v.delete(k) } setItem(k: string, val: string) { this.v.set(k, val) } }

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

function setSession(demo = false) { const s = new MemoryStorage(); s.setItem('access_token', 't'); s.setItem('user', JSON.stringify({ id: 'coach-1', email: 'c@x.com', first_name: demo ? 'Demo' : 'Test', last_name: 'Coach', role: 'coach', is_demo: demo })); vi.stubGlobal('localStorage', s) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }

function summary(overrides = {}) { return { id: 'lib-1', name: 'Beginner Full-Body Strength', description: 'A four-week starting point.', level: 'beginner', duration_weeks: 4, sessions_per_week: 3, goal_tags: ['strength', 'beginner'], equipment_summary: ['dumbbell', 'bench'], published_version_id: 'v-1', ...overrides } }
function list() { return { items: [summary()], disclaimer: 'Starter programs are general templates for review.' } }
function detail() { return { ...summary(), coach_notes: null, trainee_instructions: 'Move with control.', disclaimer: 'General templates, not medical advice.', weeks: [{ week_number: 1, label: 'Week 1', is_deload: false, sessions: [{ weekday: 'monday', display_order: 1, required: true, template: { name: 'Full Body Foundation', estimated_duration_minutes: 35, exercises: [{ name: 'Bodyweight squat', category: 'strength', tracking_mode: 'repetitions_only', set_count: 2 }] } }] }] } }

function renderList(client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })) {
  render(<QueryClientProvider client={client}><MemoryRouter initialEntries={['/coach/programming/library']}><AuthProvider><Routes>
    <Route path="/coach/programming/library" element={<StarterLibrary />} />
    <Route path="/coach/programming/programs/:programId" element={<div>PROGRAM EDITOR</div>} />
  </Routes></AuthProvider></MemoryRouter></QueryClientProvider>)
  return client
}

it('lists starter programs with read-only starter labels and actions', async () => {
  setSession(); mockFetch(url => url.endsWith('/program-library') ? ok(list()) : ok({}))
  renderList()
  expect(await screen.findByText('Beginner Full-Body Strength')).toBeVisible()
  expect(screen.getByText('Starter Library — read-only')).toBeVisible()
  expect(screen.getAllByText('Starter').length).toBeGreaterThan(0)
  expect(screen.getByRole('link', { name: /View details/ })).toHaveAttribute('href', '/coach/programming/library/lib-1')
  expect(screen.getByRole('button', { name: 'Use this program' })).toBeEnabled()
})

it('shows a loading state, not empty', async () => {
  setSession()
  let resolve: (r: Response) => void = () => {}
  vi.stubGlobal('fetch', vi.fn(() => new Promise<Response>(r => { resolve = r })))
  renderList()
  expect(await screen.findByText('Loading starter programs')).toBeVisible()
  resolve(ok(list()))
})

it('shows an error state with retry', async () => {
  setSession(); mockFetch(() => new Response(JSON.stringify({ detail: { message: 'boom' } }), { status: 500, headers: { 'Content-Type': 'application/json' } }))
  renderList()
  expect(await screen.findByText('Starter Library unavailable')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Try again' })).toBeVisible()
})

it('shows an empty state when the library is not installed', async () => {
  setSession(); mockFetch(url => url.endsWith('/program-library') ? ok({ items: [], disclaimer: 'x' }) : ok({}))
  renderList()
  expect(await screen.findByText('No starter programs yet')).toBeVisible()
})

it('clones a starter program and navigates to the new draft editor', async () => {
  setSession()
  const calls: string[] = []
  mockFetch((url, init) => { calls.push(`${init?.method ?? 'GET'} ${url}`); if (url.endsWith('/program-library')) return ok(list()); if (url.endsWith('/program-library/lib-1/clone')) return ok({ id: 'new-prog' }, 201); return ok({}) })
  renderList()
  fireEvent.click(await screen.findByRole('button', { name: 'Use this program' }))
  expect(screen.getByRole('dialog', { name: 'Use this starter program?' })).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Create my draft' }))
  expect(await screen.findByText('PROGRAM EDITOR')).toBeVisible()
  expect(calls.some(c => c.startsWith('POST') && c.endsWith('/program-library/lib-1/clone'))).toBe(true)
})

it('surfaces a clone error without navigating', async () => {
  setSession()
  mockFetch((url, init) => { if (url.endsWith('/program-library')) return ok(list()); if (init?.method === 'POST') return new Response(JSON.stringify({ detail: { message: 'nope' } }), { status: 409, headers: { 'Content-Type': 'application/json' } }); return ok({}) })
  renderList()
  fireEvent.click(await screen.findByRole('button', { name: 'Use this program' }))
  fireEvent.click(screen.getByRole('button', { name: 'Create my draft' }))
  expect(await screen.findByText('Clone unsuccessful')).toBeVisible()
  expect(screen.queryByText('PROGRAM EDITOR')).toBeNull()
})

it('disables cloning for demo coaches', async () => {
  setSession(true); mockFetch(url => url.endsWith('/program-library') ? ok(list()) : ok({}))
  renderList()
  await screen.findByText('Beginner Full-Body Strength')
  expect(screen.getByRole('button', { name: 'Use this program' })).toBeDisabled()
})

it('stores library data under an identity-scoped query key', async () => {
  setSession(); mockFetch(url => url.endsWith('/program-library') ? ok(list()) : ok({}))
  const client = renderList()
  await screen.findByText('Beginner Full-Body Strength')
  const scope = accountQueryScope({ id: 'coach-1', email: 'c@x.com', first_name: 'Test', last_name: 'Coach', role: 'coach', is_demo: false })
  await waitFor(() => expect(client.getQueryData([...scope, 'starter-library'])).toBeTruthy())
  expect(client.getQueryData(['starter-library'])).toBeUndefined()
})

it('previews a starter program read-only with exercises and no edit controls', async () => {
  setSession()
  mockFetch(url => url.includes('/program-library/lib-1') ? ok(detail()) : ok({}))
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={['/coach/programming/library/lib-1']}><AuthProvider><Routes><Route path="/coach/programming/library/:programId" element={<StarterLibraryProgram />} /></Routes></AuthProvider></MemoryRouter></QueryClientProvider>)
  expect(await screen.findByRole('heading', { name: 'Beginner Full-Body Strength' })).toBeVisible()
  expect(screen.getByText('Full Body Foundation')).toBeVisible()
  expect(screen.getByText(/Bodyweight squat/)).toBeVisible()
  expect(screen.getByRole('button', { name: 'Use this program' })).toBeVisible()
  // Read-only: no draft-editing or destructive controls are present.
  expect(screen.queryByRole('button', { name: /Save|Publish|Delete|Archive/ })).toBeNull()
})
