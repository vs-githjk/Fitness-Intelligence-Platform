/* eslint-disable react-refresh/only-export-components -- provider and hook form one auth boundary */
import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { AuthResponse, Role, User } from './types'

interface AuthContextValue {
  user: User | null
  sessionMessage: string
  setSession: (auth: AuthResponse) => void
  clearSessionMessage: () => void
  logout: () => void
}
const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    try { return JSON.parse(localStorage.getItem('user') ?? 'null') }
    catch { return null }
  })
  const [sessionMessage, setSessionMessage] = useState('')

  useEffect(() => {
    const expired = () => { setUser(null); setSessionMessage('Your session expired. Sign in again to continue.') }
    window.addEventListener('session-expired', expired)
    return () => window.removeEventListener('session-expired', expired)
  }, [])

  const value = useMemo<AuthContextValue>(() => ({
    user,
    sessionMessage,
    setSession(auth) {
      localStorage.setItem('access_token', auth.access_token)
      localStorage.setItem('user', JSON.stringify(auth.user))
      setSessionMessage('')
      setUser(auth.user)
    },
    clearSessionMessage() { setSessionMessage('') },
    logout() {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      setUser(null)
    },
  }), [sessionMessage, user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('AuthProvider missing')
  return value
}

export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { user } = useAuth(); const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (user.role !== role) return <Navigate to={user.role === 'coach' ? '/coach/dashboard' : '/trainee/today'} replace />
  return children
}
