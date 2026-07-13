/* eslint-disable react-refresh/only-export-components -- provider and hook form one auth boundary */
import { createContext, ReactNode, useContext, useMemo, useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { AuthResponse, Role, User } from './types'

interface AuthContextValue { user: User | null; setSession: (auth: AuthResponse) => void; logout: () => void }
const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => { try { return JSON.parse(localStorage.getItem('user') ?? 'null') } catch { return null } })
  const value = useMemo(() => ({ user, setSession(auth: AuthResponse) { localStorage.setItem('access_token', auth.access_token); localStorage.setItem('user', JSON.stringify(auth.user)); setUser(auth.user) }, logout() { localStorage.removeItem('access_token'); localStorage.removeItem('user'); setUser(null) } }), [user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('AuthProvider missing'); return value }
export function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { user } = useAuth(); const location = useLocation()
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (user.role !== role) return <Navigate to={user.role === 'coach' ? '/coach/dashboard' : '/trainee/dashboard'} replace />
  return children
}
