import {
  CalendarCheck,
  CalendarRange,
  ClipboardList,
  Dumbbell,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldAlert,
  SquareCode,
  TrendingUp,
  UserRound,
  UserPlus,
  Users,
} from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { ReactNode } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAccountQueryScope, useAuth } from '../auth'
import { UserProfile } from '../types'
import { Avatar } from './Avatar'
import { Brand } from './Brand'
import { EnvironmentBanner } from './EnvironmentBanner'

const coachNav = [
  { to: '/coach/dashboard', label: 'Overview', icon: LayoutDashboard },
  { to: '/coach/programming', label: 'Programming', icon: SquareCode },
  { to: '/coach/assignments', label: 'Assignments', icon: CalendarRange },
  { to: '/coach/safety-reports', label: 'Safety', icon: ShieldAlert },
  { to: '/coach/invites', label: 'Invitations', icon: UserPlus },
  { to: '/profile', label: 'Profile', icon: UserRound },
  { to: '/settings', label: 'Settings', icon: Settings },
]
const traineeNav = [
  { to: '/trainee/today', label: 'Today', icon: CalendarCheck },
  { to: '/trainee/progress', label: 'Progress', icon: TrendingUp },
  { to: '/trainee/workouts', label: 'Workouts', icon: Dumbbell },
  { to: '/trainee/program', label: 'Program', icon: CalendarRange },
  { to: '/onboarding', label: 'Assessment', icon: ClipboardList },
  { to: '/profile', label: 'Profile', icon: UserRound },
  { to: '/settings', label: 'Settings', icon: Settings },
]

function DesktopNav({ role }: { role: 'coach' | 'trainee' }) {
  const items = role === 'coach' ? coachNav : traineeNav
  return <nav aria-label={`${role} navigation`} className="mt-8 space-y-1">{items.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to !== '/coach/programming'} className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition-colors ${isActive ? 'bg-primary/8 text-primary' : 'text-secondary hover:bg-elevated hover:text-foreground'}`}><Icon aria-hidden="true" className="size-[1.125rem]" />{label}</NavLink>)}</nav>
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth(); const navigate = useNavigate(); const location = useLocation()
  const scope = useAccountQueryScope()
  // Shared with the profile page's query key, so the shell reuses that cache entry.
  const profileQuery = useQuery({ queryKey: [...scope, 'me-profile'], queryFn: () => api<UserProfile>('/me/profile'), enabled: Boolean(user) })
  if (!user) return children
  const role = user.role
  const fullName = `${user.first_name} ${user.last_name}`
  const avatarSrc = profileQuery.data?.avatar?.content_url
  const detailContext = location.pathname.includes('/coach/trainees/')
  function signOut() { logout(); navigate('/login', { replace: true }) }
  const exitLabel = user.is_demo ? 'Exit demo' : 'Sign out'
  return <div className="min-h-screen bg-page"><EnvironmentBanner inAppShell /><a href="#main-content" className="fixed left-3 top-3 z-50 -translate-y-24 rounded-lg bg-foreground px-4 py-2 text-sm font-semibold text-white transition-transform focus:translate-y-0">Skip to main content</a><aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-surface px-4 py-5 lg:flex lg:flex-col"><Link to={role === 'coach' ? '/coach/dashboard' : '/trainee/today'} className="rounded-xl p-2"><Brand /></Link><DesktopNav role={role} />{role === 'coach' && <div className="mt-8 rounded-xl border bg-elevated p-4"><div className="flex items-center gap-2 text-sm font-semibold"><Users aria-hidden="true" className="size-4 text-primary" />Coach workspace</div><p className="mt-2 text-xs leading-5 text-muted">Review health intelligence and author reusable programming.</p></div>}<div className="mt-auto border-t pt-4"><div className="flex items-center gap-3 px-2"><Avatar name={fullName} src={avatarSrc} size="md" /><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{user.first_name} {user.last_name}</p><p className="truncate text-xs capitalize text-muted">{role}{user.is_demo ? ' demo' : ''}</p></div><button type="button" onClick={signOut} aria-label={exitLabel} className="inline-flex min-h-11 items-center gap-2 rounded-xl px-2 text-xs font-semibold text-muted hover:bg-elevated hover:text-foreground"><LogOut aria-hidden="true" className="size-[1.125rem]" />{user.is_demo && <span>Exit</span>}</button></div></div></aside><header className="sticky top-0 z-20 border-b bg-surface/95 backdrop-blur lg:hidden"><div className="flex min-h-16 items-center justify-between px-4 sm:px-6"><Link to={role === 'coach' ? '/coach/dashboard' : '/trainee/today'} aria-label="FitIntel 360 home"><Brand compact /></Link><div className="flex items-center gap-2"><Avatar name={fullName} src={avatarSrc} size="sm" /><span className="max-w-28 truncate text-sm font-semibold">{user.first_name}</span><button type="button" onClick={signOut} aria-label={exitLabel} className="inline-flex min-h-11 items-center gap-1.5 rounded-xl px-2 text-xs font-semibold text-muted hover:bg-elevated"><LogOut aria-hidden="true" className="size-5" />{user.is_demo && <span>Exit demo</span>}</button></div></div></header><main id="main-content" tabIndex={-1} className="mx-auto min-h-screen max-w-app px-4 pb-24 pt-6 sm:px-6 sm:pt-8 lg:ml-64 lg:px-8 lg:pb-10 lg:pt-10 xl:px-12">{user.is_demo && <div role="status" aria-label="Demo workspace" className="mb-6 rounded-xl border border-[rgb(var(--status-info-border))] bg-[rgb(var(--status-info-bg))] px-4 py-3 text-sm text-info"><p className="font-semibold text-foreground">Demo workspace — changes are disabled.</p><p className="mt-1 text-xs text-secondary">All people and health information shown here are synthetic.</p></div>}{detailContext && <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted">Trainee record</p>}{children}</main><nav aria-label={`${role} navigation`} className="safe-bottom fixed inset-x-0 bottom-0 z-30 border-t bg-surface/95 px-2 pt-2 backdrop-blur lg:hidden"><div className="mx-auto grid max-w-lg grid-cols-4">{(role === 'trainee' ? traineeNav : coachNav).map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end={to !== '/coach/programming'} className={({ isActive }) => `flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl text-[0.65rem] font-semibold sm:text-xs ${isActive ? 'text-primary' : 'text-muted'}`}><Icon aria-hidden="true" className="size-5" />{label}</NavLink>)}</div></nav></div>
}

export function ProfileMeta({ role }: { role: 'coach' | 'trainee' }) {
  return <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted"><UserRound aria-hidden="true" className="size-3.5" />{role === 'coach' ? 'Coach view' : 'Trainee view · assigned coach access'}</span>
}
