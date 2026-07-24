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

// jsdom lacks object-URL support used by the avatar preview and image render.
URL.createObjectURL = vi.fn(() => 'blob:preview')
URL.revokeObjectURL = vi.fn()

function setSession(role: 'coach' | 'trainee', demo: boolean) { const storage = new MemoryStorage(); storage.setItem('access_token', 'test-token'); storage.setItem('user', JSON.stringify({ id: `${role}-1`, email: `${role}@example.com`, first_name: demo ? 'Demo' : 'Test', last_name: role, role, is_demo: demo })); vi.stubGlobal('localStorage', storage) }
function mockFetch(handler: (url: string, init?: RequestInit) => Response) { vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => Promise.resolve(handler(String(input), init)))) }
function ok(value: unknown, status = 200) { return new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } }) }
function renderPage(element: React.ReactNode) { const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } }); render(<QueryClientProvider client={client}><MemoryRouter><AuthProvider>{element}</AuthProvider></MemoryRouter></QueryClientProvider>); return client }

function profile(overrides: Partial<UserProfile> = {}): UserProfile { return { id: 'profile-1', user_id: 'coach-1', preferred_display_name: 'Coach Cara', bio: 'Strength focus.', headline: null, coaching_specialties: null, years_of_experience: null, certifications_text: null, training_goals: null, avatar: null, created_at: '2026-07-21T00:00:00Z', updated_at: '2026-07-21T00:00:00Z', ...overrides } }
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

it('lets a coach edit professional fields and sends specialties as an array', async () => {
  setSession('coach', false)
  const bodies: string[] = []
  mockFetch((url, init) => {
    if (url.endsWith('/me/profile') && (init?.method ?? 'GET') === 'GET') return ok(profile())
    if (url.endsWith('/me/profile') && init?.method === 'PUT') { bodies.push(String(init?.body)); return ok(profile()) }
    return ok({})
  })
  renderPage(<ProfilePage />)
  const headline = await screen.findByLabelText(/Headline/)
  fireEvent.change(headline, { target: { value: 'Strength coach' } })
  fireEvent.change(screen.getByLabelText(/Specialties/), { target: { value: 'Powerlifting, Mobility, Powerlifting' } })
  fireEvent.change(screen.getByLabelText(/Years of experience/), { target: { value: '12' } })
  // Live chip preview de-duplicates and trims.
  expect(await screen.findByTestId('specialty-preview')).toHaveTextContent('Powerlifting')
  fireEvent.click(screen.getByRole('button', { name: 'Save profile' }))
  await waitFor(() => expect(bodies.length).toBe(1))
  const payload = JSON.parse(bodies[0])
  expect(payload.headline).toBe('Strength coach')
  expect(payload.coaching_specialties).toEqual(['Powerlifting', 'Mobility'])
  expect(payload.years_of_experience).toBe(12)
})

it('shows trainees a training-goals field, not coach-only fields', async () => {
  setSession('trainee', false)
  mockFetch((url) => { if (url.endsWith('/me/profile')) return ok(profile({ user_id: 'trainee-1' })); return ok({}) })
  renderPage(<ProfilePage />)
  expect(await screen.findByLabelText(/working toward/)).toBeInTheDocument()
  expect(screen.queryByLabelText(/Specialties/)).toBeNull()
  expect(screen.queryByLabelText(/Years of experience/)).toBeNull()
})

it('uploads a chosen profile photo', async () => {
  setSession('coach', false)
  let puts = 0
  mockFetch((url, init) => {
    if (url.endsWith('/me/profile')) return ok(profile())
    if (url.endsWith('/me/avatar') && init?.method === 'PUT') { puts += 1; return ok({ id: 'media-1' }) }
    return ok({})
  })
  renderPage(<ProfilePage />)
  const input = await screen.findByLabelText('Choose a profile photo')
  fireEvent.change(input, { target: { files: [new File([new Uint8Array([1, 2, 3])], 'me.png', { type: 'image/png' })] } })
  expect(await screen.findByTestId('avatar-preview')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Upload photo' }))
  expect(await screen.findByText('Your photo was updated.')).toBeVisible()
  expect(puts).toBe(1)
})

it('rejects an unsupported avatar file before upload', async () => {
  setSession('coach', false)
  mockFetch((url) => { if (url.endsWith('/me/profile')) return ok(profile()); return ok({}) })
  renderPage(<ProfilePage />)
  const input = await screen.findByLabelText('Choose a profile photo')
  fireEvent.change(input, { target: { files: [new File(['x'], 'notes.pdf', { type: 'application/pdf' })] } })
  expect(await screen.findByText(/Choose a JPEG, PNG, WEBP, or GIF/)).toBeVisible()
  expect(screen.queryByRole('button', { name: 'Upload photo' })).toBeNull()
})

it('removes an existing profile photo', async () => {
  setSession('coach', false)
  let deletes = 0
  mockFetch((url, init) => {
    if (url.endsWith('/me/profile')) return ok(profile({ avatar: { id: 'media-1', owner_user_id: 'coach-1', uploader_user_id: 'coach-1', purpose: 'avatar', visibility: 'private', lifecycle_status: 'active', content_type: 'image/png', byte_size: 10, checksum_sha256: 'x', original_filename: 'me.png', content_url: '/media/media-1/content', created_at: 'x', updated_at: 'x', deleted_at: null, replaced_at: null } }))
    if (url.endsWith('/media/media-1/content')) return ok({})
    if (url.endsWith('/me/avatar') && init?.method === 'DELETE') { deletes += 1; return new Response(null, { status: 204 }) }
    return ok({})
  })
  renderPage(<ProfilePage />)
  fireEvent.click(await screen.findByRole('button', { name: 'Remove' }))
  expect(await screen.findByText('Your photo was removed.')).toBeVisible()
  expect(deletes).toBe(1)
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
