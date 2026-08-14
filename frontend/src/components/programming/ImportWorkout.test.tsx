import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AuthProvider } from '../../auth'
import { ImportWorkout } from './ImportWorkout'

class MemoryStorage implements Storage {
  private values = new Map<string, string>(); get length() { return this.values.size }
  clear() { this.values.clear() } getItem(key: string) { return this.values.get(key) ?? null }
  key(index: number) { return [...this.values.keys()][index] ?? null } removeItem(key: string) { this.values.delete(key) }
  setItem(key: string, value: string) { this.values.set(key, value) }
}

const rawZero = { reps_min: null, reps_max: null, load: null, load_unit: null, duration_seconds: null, distance: null, distance_unit: null, rest_seconds: null, notes: null }
const PREVIEW = {
  template_name: 'Imported workout', file_errors: [],
  summary: { total: 3, matched: 1, needs_review: 1, not_found: 1 },
  rows: [
    { line: 1, exercise_name: 'Goblet squat', status: 'matched', sets: 3, matched: { exercise_id: 'e1', exercise_version_id: 'v1', name: 'Goblet squat', tracking_mode: 'repetitions_and_load', movement_pattern: 'squat' }, candidates: [], prescription: { repetitions_min: 8, repetitions_max: 10, rest_seconds: 90 }, raw: { ...rawZero, reps_min: 8, reps_max: 10, load: '20', load_unit: 'kg', rest_seconds: 90 }, error: null },
    { line: 2, exercise_name: 'Bench', status: 'needs_review', sets: 3, matched: null, candidates: [{ exercise_id: 'e2', exercise_version_id: 'v2', name: 'Barbell bench press', tracking_mode: 'repetitions_and_load', movement_pattern: 'horizontal push' }, { exercise_id: 'e3', exercise_version_id: 'v3', name: 'Dumbbell bench press', tracking_mode: 'repetitions_and_load', movement_pattern: 'horizontal push' }], prescription: null, raw: { ...rawZero, reps_min: 8, reps_max: 10, load: '40', load_unit: 'kg', rest_seconds: 90 }, error: null },
    { line: 3, exercise_name: 'Totally unknown', status: 'not_found', sets: 3, matched: null, candidates: [], prescription: null, raw: rawZero, error: 'No match' },
  ],
}

function setSession() {
  const storage = new MemoryStorage()
  storage.setItem('access_token', 'test-token')
  storage.setItem('user', JSON.stringify({ id: 'coach-1', email: 'coach@example.com', first_name: 'Test', last_name: 'Coach', role: 'coach', is_demo: false }))
  vi.stubGlobal('localStorage', storage)
}

beforeEach(setSession)
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('ImportWorkout', () => {
  it('previews, lets the coach resolve a match, and creates a draft from resolved rows only', async () => {
    let createBody: { exercises: Array<{ exercise_version_id: string; sets: unknown[] }> } | undefined
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.includes('/workout-imports/preview')) return Promise.resolve(new Response(JSON.stringify(PREVIEW), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      if (url.includes('/coach/workout-templates')) { createBody = JSON.parse(String(init?.body)); return Promise.resolve(new Response(JSON.stringify({ id: 't-new' }), { status: 201, headers: { 'Content-Type': 'application/json' } })) }
      return Promise.resolve(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }))
    }))

    render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={['/coach/programming/import']}><AuthProvider><Routes>
      <Route path="/coach/programming/import" element={<ImportWorkout />} />
      <Route path="/coach/programming/templates/:id" element={<p>Builder for draft</p>} />
    </Routes></AuthProvider></MemoryRouter></QueryClientProvider>)

    fireEvent.change(screen.getByLabelText('Or paste CSV rows'), { target: { value: 'exercise,sets\nGoblet squat,3' } })
    fireEvent.click(screen.getByRole('button', { name: 'Preview import' }))

    expect(await screen.findByText('1 matched · 1 to review · 1 not found')).toBeVisible()
    expect(screen.getAllByText('Goblet squat').length).toBeGreaterThan(0)

    // Resolve the needs-review row to a candidate.
    fireEvent.change(screen.getByLabelText('Choose an exercise for Bench'), { target: { value: 'v2' } })
    await waitFor(() => expect(screen.getByText('2 exercises will be added to a new draft.')).toBeVisible())

    fireEvent.click(screen.getByRole('button', { name: 'Create workout draft' }))
    expect(await screen.findByText('Builder for draft')).toBeVisible()

    expect(createBody!.exercises).toHaveLength(2)
    expect(createBody!.exercises.map(e => e.exercise_version_id)).toEqual(['v1', 'v2'])
    expect(createBody!.exercises[0].sets).toHaveLength(3)
  })
})
