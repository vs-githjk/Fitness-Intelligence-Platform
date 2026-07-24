import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { ExerciseVersion } from '../../types'
import { ExerciseMediaManager } from './ExerciseMediaManager'
import { ExercisePreview } from './ExercisePreview'

class MemoryStorage implements Storage { private v = new Map<string, string>(); get length() { return this.v.size } clear() { this.v.clear() } getItem(k: string) { return this.v.get(k) ?? null } key(i: number) { return [...this.v.keys()][i] ?? null } removeItem(k: string) { this.v.delete(k) } setItem(k: string, val: string) { this.v.set(k, val) } }

afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals() })

URL.createObjectURL = vi.fn(() => 'blob:preview')
URL.revokeObjectURL = vi.fn()

function version(overrides: Partial<ExerciseVersion> = {}): ExerciseVersion {
  return {
    id: 'v1', exercise_id: 'e1', version_number: 1, status: 'draft',
    name: 'Goblet squat', description: 'A squat variation.', instructions: 'Squat with control.',
    tracking_mode: 'repetitions_and_load', category: 'strength', movement_pattern: 'squat',
    equipment: ['dumbbell'], primary_muscle_groups: ['quadriceps'], secondary_muscle_groups: ['core'],
    unilateral: false, safety_cues: ['Stop if it hurts.'], difficulty: 'beginner',
    coaching_cues: ['Chest tall.'], common_mistakes: ['Heels lifting.'],
    primary_image: null, secondary_image: null, demonstration_video: null,
    image_url: null, thumbnail_url: null, content_hash: null, created_by_user_id: null,
    created_at: 'x', updated_at: 'x', published_at: null,
    ...overrides,
  }
}

function withClient(node: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })
  render(<QueryClientProvider client={client}>{node}</QueryClientProvider>)
}

it('preview renders knowledge fields and empty media states', () => {
  render(<QueryClientProvider client={new QueryClient()}><ExercisePreview version={version()} /></QueryClientProvider>)
  expect(screen.getByText('Beginner')).toBeInTheDocument()
  expect(screen.getByText('Chest tall.')).toBeInTheDocument()
  expect(screen.getByText('Heels lifting.')).toBeInTheDocument()
  expect(screen.getByText('No image yet')).toBeInTheDocument()
  expect(screen.getByText('No video yet')).toBeInTheDocument()
})

it('uploads a chosen exercise image', async () => {
  const storage = new MemoryStorage(); storage.setItem('access_token', 't')
  vi.stubGlobal('localStorage', storage)
  let puts = 0
  vi.stubGlobal('fetch', vi.fn((url: string, init?: RequestInit) => {
    if (String(url).endsWith('/coach/exercises/e1/media/primary_image') && init?.method === 'PUT') {
      puts += 1
      return Promise.resolve(new Response(JSON.stringify({ id: 'e1' }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    }
    return Promise.resolve(new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }))
  }))
  const onChanged = vi.fn()
  withClient(<ExerciseMediaManager exerciseId="e1" version={version()} disabled={false} onChanged={onChanged} />)

  const input = screen.getByLabelText('Choose primary image')
  fireEvent.change(input, { target: { files: [new File([new Uint8Array([1, 2])], 'a.png', { type: 'image/png' })] } })
  expect(await screen.findByTestId('media-preview-primary_image')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Upload' }))
  await waitFor(() => expect(onChanged).toHaveBeenCalled())
  expect(puts).toBe(1)
})

it('rejects an unsupported exercise media type before upload', () => {
  vi.stubGlobal('localStorage', new MemoryStorage())
  withClient(<ExerciseMediaManager exerciseId="e1" version={version()} disabled={false} onChanged={vi.fn()} />)
  const input = screen.getByLabelText('Choose demonstration video')
  fireEvent.change(input, { target: { files: [new File(['x'], 'a.png', { type: 'image/png' })] } })
  expect(screen.getByText('Choose an MP4 or WEBM video.')).toBeInTheDocument()
})

it('disables media controls when read-only', () => {
  vi.stubGlobal('localStorage', new MemoryStorage())
  withClient(<ExerciseMediaManager exerciseId="e1" version={version()} disabled onChanged={vi.fn()} />)
  expect(screen.getByText('Media is read-only here')).toBeInTheDocument()
  screen.getAllByRole('button', { name: 'Add' }).forEach(button => expect(button).toBeDisabled())
})
