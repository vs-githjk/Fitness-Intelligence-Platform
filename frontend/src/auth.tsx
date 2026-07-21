/* eslint-disable react-refresh/only-export-components -- provider and hook form one auth boundary */
import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react'
import { QueryClient, useQueryClient } from '@tanstack/react-query'
import { Navigate, useLocation } from 'react-router-dom'
import { AuthResponse, Role, User } from './types'

export const accountQueryRoot = ['account'] as const

export function accountQueryScope(user: User | null) {
  return [
    ...accountQueryRoot,
    user?.id ?? 'signed-out',
    user?.role ?? 'no-role',
    user?.is_demo ? 'demo' : 'standard',
  ] as const
}

export function removeAccountQueries(queryClient: QueryClient): void {
  void queryClient.cancelQueries({ queryKey: accountQueryRoot })
  queryClient.removeQueries({ queryKey: accountQueryRoot })
}

interface AuthContextValue {
  user: User | null
  sessionMessage: string
  setSession: (auth: AuthResponse) => void
  clearSessionMessage: () => void
  logout: () => void
}
const AuthContext = createContext<AuthContextValue | null>(null)

function clearStoredSession(storage: Storage): void {
  storage.removeItem('access_token')
  storage.removeItem('user')
}

function isUser(value: unknown): value is User {
  if (!value || typeof value !== 'object') return false
  const candidate = value as Partial<User>
  return typeof candidate.id === 'string'
    && typeof candidate.email === 'string'
    && typeof candidate.first_name === 'string'
    && typeof candidate.last_name === 'string'
    && (candidate.role === 'coach' || candidate.role === 'trainee')
}

export function loadStoredUser(storage: Storage): User | null {
  try {
    const token = storage.getItem('access_token')
    const rawUser = storage.getItem('user')
    if (!token || !rawUser) {
      clearStoredSession(storage)
      return null
    }
    const parsed: unknown = JSON.parse(rawUser)
    if (!isUser(parsed)) {
      clearStoredSession(storage)
      return null
    }
    return { ...parsed, is_demo: parsed.is_demo === true }
  } catch {
    clearStoredSession(storage)
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [user, setUser] = useState<User | null>(() => loadStoredUser(localStorage))
  const [sessionMessage, setSessionMessage] = useState('')

  useEffect(() => {
    const expired = () => {
      removeAccountQueries(queryClient)
      setUser(null)
      setSessionMessage('Your session expired. Sign in again to continue.')
    }
    window.addEventListener('session-expired', expired)
    return () => window.removeEventListener('session-expired', expired)
  }, [queryClient])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    sessionMessage,
    setSession(auth) {
      removeAccountQueries(queryClient)
      localStorage.setItem('access_token', auth.access_token)
      localStorage.setItem('user', JSON.stringify(auth.user))
      setSessionMessage('')
      setUser(auth.user)
    },
    clearSessionMessage() { setSessionMessage('') },
    logout() {
      removeAccountQueries(queryClient)
      clearStoredSession(localStorage)
      setUser(null)
    },
  }), [queryClient, sessionMessage, user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider missing')
  return value
}

export function useAccountQueryScope() {
  const { user } = useAuth()
  return useMemo(
    () => accountQueryScope(user),
    [user],
  )
}

export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { user } = useAuth(); const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (user.role !== role) return <Navigate to={user.role === 'coach' ? '/coach/dashboard' : '/trainee/today'} replace />
  return children
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useAuth(); const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return children
}
