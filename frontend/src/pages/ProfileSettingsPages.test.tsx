import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import React from 'react'
import { afterEach, expect, it, vi } from 'vitest'
import { accountQueryScope, AuthProvider } from '../auth'
import { UserPreferences, UserProfile } from '../types'
import { ProfilePage, SettingsPage } from './ProfileSettingsPages'

class MemoryStorage implements Storage { private values = new Map<string, string>(); get length() { return this.values.size } clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null } key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) } setItem(key: string, value: string) { this.values.set(key, value) } }

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

function setSession(role: 'coach' | 'trainee', demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: `${role}-1`, email: `${role}@example.com`, first_name: demo ? 'Demo' : 'Test', last_name: role, role, is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }
function renderPage(element: React.ReactNode) { const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } }); render(<QueryClientProvider client={client}><MemoryRouter><AuthProvider>{element}</AuthProvider></MemoryRouter></QueryClientProvider>); return client }

function profile(overrides: Partial<UserProfile> = {}): UserProfile { return { id: 'profile-1', user_id: 'coach-1', preferred_display_name: 'Coach Cara', bio: 'Strength focus.', created_at: '2026-07-21T00:00:00Z', updated_at: '2026-07-21T00:00:00Z', ...overrides } }
function preferences(overrides: Partial<UserPreferences> = {}): UserPreferences { return { id: 'pref-1', user_id: 'coach-1', timezone: 'Asia/Kolkata', weight_unit: 'kg', distance_unit: 'kilometers', locale: 'en', theme: null, privacy_settings: {}, accessibility_settings: {}, created_at: '2026-07-21T00:00:00Z', updated_at: '2026-07-21T00:00:00Z', ...overrides } }

it('loads the profile, edits the display name, and saves it', async () => {
  setSession('coach', false)
  const bodies: string[] = []
  mockFetch((url, init) => {
    if (url.endsWith('/me/profile') && (init?.method ?? 'GET') === 'GET') return ok(profile())
    if (url.endsWith('/me/profile') && init?.method === 'PUT') { bodies.push(String(init?.body)); return ok(profile({ preferred_display_name: 'Coach Renamed' })) }
    return ok({})
  })
  renderPage(<ProfilePage />)
  const nameField = await screen.findByLabelText(/Preferred display name/)
  await waitFor(() => expect(nameField).toHaveValue('Coach Cara'))
  fireEvent.change(nameField, { target: { value: 'Coach Renamed' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }))
  await waitFor(() => expect(bodies.some(body => JSON.parse(body).preferred_display_name === 'Coach Renamed')).toBe(true))
  expect(await screen.findByText('Profile saved')).toBeVisible()
})

it('rejects an over-long display name before saving', async () => {
  setSession('coach', false)
  const calls: string[] = []
  mockFetch((url, init) => { calls.push(`${init?.method ?? 'GET'} ${url}`); if (url.endsWith('/me/profile')) return ok(profile()); return ok({}) })
  renderPage(<ProfilePage />)
  const nameField = await screen.findByLabelText(/Preferred display name/)
  await waitFor(() => expect(nameField).toHaveValue('Coach Cara'))
  fireEvent.input(nameField, { target: { value: 'x'.repeat(121) } })
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }))
  expect(await screen.findByText('Keep the display name under 120 characters')).toBeVisible()
  expect(calls.filter(call => call.startsWith('PUT'))).toHaveLength(0)
})

it('stores profile data under an identity-scoped query key', async () => {
  setSession('coach', false)
  mockFetch((url) => { if (url.endsWith('/me/profile')) return ok(profile()); return ok({}) })
  const client = renderPage(<ProfilePage />)
  await screen.findByLabelText(/Preferred display name/)
  const scope = accountQueryScope({ id: 'coach-1', email: 'coach@example.com', first_name: 'Test', last_name: 'coach', role: 'coach', is_demo: false })
  await waitFor(() => expect(client.getQueryData([...scope, 'me-profile'])).toBeTruthy())
  expect(client.getQueryData(['me-profile'])).toBeUndefined()
})

it('loads preferences and saves a changed weight unit', async () => {
  setSession('trainee', false)
  const bodies: string[] = []
  mockFetch((url, init) => {
    if (url.endsWith('/me/preferences') && (init?.method ?? 'GET') === 'GET') return ok(preferences({ user_id: 'trainee-1' }))
    if (url.endsWith('/me/preferences') && init?.method === 'PUT') { bodies.push(String(init?.body)); return ok(preferences({ user_id: 'trainee-1', weight_unit: 'lb' })) }
    return ok({})
  })
  renderPage(<SettingsPage />)
  const weightField = await screen.findByLabelText('Weight unit')
  await waitFor(() => expect(weightField).toHaveValue('kg'))
  fireEvent.change(weightField, { target: { value: 'lb' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save settings' }))
  await waitFor(() => expect(bodies.some(body => JSON.parse(body).weight_unit === 'lb')).toBe(true))
  expect(await screen.findByText('Settings saved')).toBeVisible()
})

it('disables identity edits for demo accounts', async () => {
  setSession('trainee', true)
  mockFetch((url) => { if (url.endsWith('/me/preferences')) return ok(preferences({ user_id: 'trainee-1' })); return ok({}) })
  renderPage(<SettingsPage />)
  expect(await screen.findByRole('button', { name: 'Save settings' })).toBeDisabled()
  expect(screen.getByRole('status', { name: 'Demo workspace' })).toBeVisible()
  expect(screen.getByLabelText('Weight unit')).toBeDisabled()
})
