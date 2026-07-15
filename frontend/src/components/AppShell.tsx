import {
  CalendarCheck,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  TrendingUp,
  UserRound,
  Users,
} from 'lucide-react'
import { ReactNode } from 'react'
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { EnvironmentBanner } from './EnvironmentBanner'

const coachNav = [
  { to: '/coach/dashboard', label: 'Overview', icon: LayoutDashboard },
]
const traineeNav = [
  { to: '/trainee/today', label: 'Today', icon: CalendarCheck },
  { to: '/trainee/progress', label: 'Progress', icon: TrendingUp },
  { to: '/onboarding', label: 'Assessment', icon: ClipboardList },
]

function Brand({ compact = false }: { compact?: boolean }) {
  return <span className="flex items-center gap-3"><span className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary text-white"><ShieldCheck aria-hidden="true" className="size-5" /></span>{!compact && <span className="leading-tight"><span className="block text-[0.7rem] font-bold uppercase tracking-[0.18em] text-muted">Fitness</span><span className="block font-bold tracking-tight text-foreground">Intelligence</span></span>}</span>
}

function DesktopNav({ role }: { role: 'coach' | 'trainee' }) {
  const items = role === 'coach' ? coachNav : traineeNav
  return <nav aria-label={`${role} navigation`} className="mt-8 space-y-1">{items.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end className={({ isActive }) => `flex min-h-11 items-center gap-3 rounded-xl px-3 text-sm font-semibold transition-colors ${isActive ? 'bg-primary/8 text-primary' : 'text-secondary hover:bg-elevated hover:text-foreground'}`}><Icon aria-hidden="true" className="size-[1.125rem]" />{label}</NavLink>)}</nav>
}

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth(); const navigate = useNavigate(); const location = useLocation()
  if (!user) return children
  const role = user.role
  const detailContext = location.pathname.includes('/coach/trainees/')
  function signOut() { logout(); navigate('/login', { replace: true }) }
  return <div className="min-h-screen bg-page"><EnvironmentBanner inAppShell /><a href="#main-content" className="fixed left-3 top-3 z-50 -translate-y-24 rounded-lg bg-foreground px-4 py-2 text-sm font-semibold text-white transition-transform focus:translate-y-0">Skip to main content</a><aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r bg-surface px-4 py-5 lg:flex lg:flex-col"><Link to={role === 'coach' ? '/coach/dashboard' : '/trainee/today'} className="rounded-xl p-2"><Brand /></Link><DesktopNav role={role} />{role === 'coach' && <div className="mt-8 rounded-xl border bg-elevated p-4"><div className="flex items-center gap-2 text-sm font-semibold"><Users aria-hidden="true" className="size-4 text-primary" />Coach workspace</div><p className="mt-2 text-xs leading-5 text-muted">Review baselines, daily readiness, and patterns that need attention.</p></div>}<div className="mt-auto border-t pt-4"><div className="flex items-center gap-3 px-2"><span className="grid size-9 place-items-center rounded-full bg-primary/10 text-sm font-bold text-primary">{user.first_name[0]}{user.last_name[0]}</span><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{user.first_name} {user.last_name}</p><p className="truncate text-xs capitalize text-muted">{role}</p></div><button type="button" onClick={signOut} aria-label="Sign out" className="grid size-11 place-items-center rounded-xl text-muted hover:bg-elevated hover:text-foreground"><LogOut aria-hidden="true" className="size-[1.125rem]" /></button></div></div></aside><header className="sticky top-0 z-20 border-b bg-surface/95 backdrop-blur lg:hidden"><div className="flex min-h-16 items-center justify-between px-4 sm:px-6"><Link to={role === 'coach' ? '/coach/dashboard' : '/trainee/today'}><Brand compact /></Link><div className="flex items-center gap-2"><span className="max-w-36 truncate text-sm font-semibold">{user.first_name}</span><button type="button" onClick={signOut} aria-label="Sign out" className="grid size-11 place-items-center rounded-xl text-muted hover:bg-elevated"><LogOut aria-hidden="true" className="size-5" /></button></div></div></header><main id="main-content" tabIndex={-1} className={`mx-auto min-h-screen max-w-app px-4 py-6 sm:px-6 sm:py-8 lg:ml-64 lg:px-8 lg:py-10 xl:px-12 ${role === 'trainee' ? 'pb-24 lg:pb-10' : ''}`}>{detailContext && <p className="mb-4 text-xs font-semibold uppercase tracking-wider text-muted">Trainee record</p>}{children}</main><nav aria-label="Trainee navigation" className="safe-bottom fixed inset-x-0 bottom-0 z-30 border-t bg-surface/95 px-4 pt-2 backdrop-blur lg:hidden">{role === 'trainee' ? <div className="mx-auto grid max-w-sm grid-cols-3">{traineeNav.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} end className={({ isActive }) => `flex min-h-12 flex-col items-center justify-center gap-0.5 rounded-xl text-xs font-semibold ${isActive ? 'text-primary' : 'text-muted'}`}><Icon aria-hidden="true" className="size-5" />{label}</NavLink>)}</div> : <div className="mx-auto flex max-w-sm justify-center"><NavLink to="/coach/dashboard" className="flex min-h-12 items-center gap-2 rounded-xl px-5 text-sm font-semibold text-primary"><LayoutDashboard aria-hidden="true" className="size-5" />Overview</NavLink></div>}</nav></div>
}

export function ProfileMeta({ role }: { role: 'coach' | 'trainee' }) {
  return <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted"><UserRound aria-hidden="true" className="size-3.5" />{role === 'coach' ? 'Coach view' : 'Trainee view · assigned coach access'}</span>
}
