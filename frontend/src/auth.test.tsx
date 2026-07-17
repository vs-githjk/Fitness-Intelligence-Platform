import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  accountQueryScope,
  AuthProvider,
  useAuth,
} from './auth'
import { User } from './types'

class MemoryStorage implements Storage {
  private values = new Map<string, string>()
  get length() { return this.values.size }
  clear() { this.values.clear() }
  getItem(key: string) { return this.values.get(key) ?? null }
  key(index: number) { return [...this.values.keys()][index] ?? null }
  removeItem(key: string) { this.values.delete(key) }
  setItem(key: string, value: string) { this.values.set(key, value) }
}

function account(
  id: string,
  role: 'coach' | 'trainee',
  isDemo = false,
): User {
  return {
    id,
    email: `${id}@example.invalid`,
    first_name: isDemo ? 'Demo' : 'Test',
    last_name: role === 'coach' ? 'Coach' : 'Trainee',
    role,
    is_demo: isDemo,
  }
}

function setStoredSession(user: User): void {
  const storage = new MemoryStorage()
  storage.setItem('access_token', `token-${user.id}`)
  storage.setItem('user', JSON.stringify(user))
  vi.stubGlobal('localStorage', storage)
}

function TransitionHarness({ target }: { target: User }) {
  const { user, setSession, logout } = useAuth()
  return <div>
    <p>Current identity: {user?.id ?? 'signed-out'}</p>
    <button type="button" onClick={logout}>Sign out</button>
    <button type="button" onClick={() => setSession({
      access_token: `token-${target.id}`,
      token_type: 'bearer',
      user: target,
    })}>Sign in target</button>
  </div>
}

function renderTransition(client: QueryClient, target: User) {
  return render(<QueryClientProvider client={client}>
    <AuthProvider><TransitionHarness target={target} /></AuthProvider>
  </QueryClientProvider>)
}

afterEach(() => {
  cleanup()
  vi.unstubAllGlobals()
})

describe('account query identity scope', () => {
  it('includes user ID, role, and demo status without tokens', () => {
    expect(accountQueryScope(account('coach-a', 'coach'))).toEqual([
      'account', 'coach-a', 'coach', 'standard',
    ])
    expect(accountQueryScope(account('demo-trainee', 'trainee', true))).toEqual([
      'account', 'demo-trainee', 'trainee', 'demo',
    ])
    expect(accountQueryScope(null)).toEqual([
      'account', 'signed-out', 'no-role', 'standard',
    ])
  })

  it.each([
    ['real coach to demo coach', account('coach-a', 'coach'), account('demo-coach', 'coach', true)],
    ['demo coach to real coach', account('demo-coach', 'coach', true), account('coach-a', 'coach')],
    ['coach A to coach B', account('coach-a', 'coach'), account('coach-b', 'coach')],
    ['real trainee to demo trainee', account('trainee-a', 'trainee'), account('demo-trainee', 'trainee', true)],
    ['demo trainee to real trainee', account('demo-trainee', 'trainee', true), account('trainee-a', 'trainee')],
    ['trainee A to trainee B', account('trainee-a', 'trainee'), account('trainee-b', 'trainee')],
    ['coach to trainee role transition', account('coach-a', 'coach'), account('trainee-a', 'trainee')],
  ])('purges protected data across %s', (_name, previous, target) => {
    setStoredSession(previous)
    const client = new QueryClient()
    const previousKey = [...accountQueryScope(previous), 'dashboard']
    client.setQueryData(previousKey, { private: previous.id })
    client.setQueryData(['public', 'release'], '0.5.0')

    renderTransition(client, target)
    expect(screen.getByText(`Current identity: ${previous.id}`)).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    expect(screen.getByText('Current identity: signed-out')).toBeVisible()
    expect(client.getQueryData(previousKey)).toBeUndefined()
    expect(client.getQueryData(['public', 'release'])).toBe('0.5.0')

    fireEvent.click(screen.getByRole('button', { name: 'Sign in target' }))
    expect(screen.getByText(`Current identity: ${target.id}`)).toBeVisible()
    expect(client.getQueryData(previousKey)).toBeUndefined()
  })

  it('purges expired-session data before another identity signs in', async () => {
    const previous = account('expired-trainee', 'trainee')
    const target = account('coach-b', 'coach')
    setStoredSession(previous)
    const client = new QueryClient()
    const previousKey = [...accountQueryScope(previous), 'trainee-coach']
    client.setQueryData(previousKey, { private: previous.id })
    renderTransition(client, target)

    localStorage.removeItem('access_token')
    localStorage.removeItem('user')
    window.dispatchEvent(new CustomEvent('session-expired'))
    await waitFor(() => expect(screen.getByText('Current identity: signed-out')).toBeVisible())
    expect(client.getQueryData(previousKey)).toBeUndefined()

    fireEvent.click(screen.getByRole('button', { name: 'Sign in target' }))
    expect(screen.getByText(`Current identity: ${target.id}`)).toBeVisible()
  })

  it('prevents an old coach-relationship response from repopulating another trainee cache', async () => {
    const previous = account('trainee-a', 'trainee')
    const target = account('demo-trainee', 'trainee', true)
    setStoredSession(previous)
    const client = new QueryClient()
    const previousKey = [...accountQueryScope(previous), 'trainee-coach']
    let resolveRequest!: (value: { coach_name: string }) => void
    const response = new Promise<{ coach_name: string }>(resolve => { resolveRequest = resolve })
    const request = client.fetchQuery({ queryKey: previousKey, queryFn: () => response })
      .catch(() => undefined)

    renderTransition(client, target)
    fireEvent.click(screen.getByRole('button', { name: 'Sign out' }))
    fireEvent.click(screen.getByRole('button', { name: 'Sign in target' }))
    resolveRequest({ coach_name: 'Private coach' })
    await request

    expect(client.getQueryData(previousKey)).toBeUndefined()
    expect(client.getQueryData([...accountQueryScope(target), 'trainee-coach'])).toBeUndefined()
  })
})
