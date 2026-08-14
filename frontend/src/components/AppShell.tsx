import {
  CalendarCheck,
  CalendarRange,
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
import { ComponentType, ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { useAccountQueryScope, useAuth } from '../auth'
import { UserProfile } from '../types'
import { Avatar } from './Avatar'
import { EnvironmentBanner } from './EnvironmentBanner'
import { Wordmark } from './iron/Wordmark'
import { Eyebrow, HairRule } from './iron/Editorial'

type SubItem = { to: string; label: string }
type NavItem = {
  to: string
  label: string
  icon: ComponentType<{ className?: string; 'aria-hidden'?: boolean | 'true' | 'false' }>
  // A tab owns a set of routes; `match` decides the active tab so a relocated
  // destination (e.g. execution under Train) still lights its parent.
  match: (path: string) => boolean
  children?: SubItem[]
}

const coachNav: NavItem[] = [
  { to: '/coach/dashboard', label: 'Overview', icon: LayoutDashboard, match: (p) => p.startsWith('/coach/dashboard') || p.startsWith('/coach/trainees') },
  { to: '/coach/programming', label: 'Programming', icon: SquareCode, match: (p) => p.startsWith('/coach/programming') },
  { to: '/coach/assignments', label: 'Assignments', icon: CalendarRange, match: (p) => p.startsWith('/coach/assignments') },
  { to: '/coach/safety-reports', label: 'Safety', icon: ShieldAlert, match: (p) => p.startsWith('/coach/safety-reports') },
  { to: '/coach/invites', label: 'Invitations', icon: UserPlus, match: (p) => p.startsWith('/coach/invites') },
  { to: '/profile', label: 'Profile', icon: UserRound, match: (p) => p.startsWith('/profile') },
  { to: '/settings', label: 'Settings', icon: Settings, match: (p) => p.startsWith('/settings') },
]

// Coach navigation grouped into editorial sections — the "training studio" structure.
// Same warm-paper Iron Editorial language as the trainee, distinguished by labeled
// hairline groups (Studio / Oversight / Account) rather than a flat admin list. Slices
// reference the coachNav objects above so order stays the single source of truth.
const coachGroups: { label: string; items: NavItem[] }[] = [
  { label: 'Studio', items: coachNav.slice(0, 3) },
  { label: 'Oversight', items: coachNav.slice(3, 5) },
  { label: 'Account', items: coachNav.slice(5) },
]

// Four-tab trainee IA (Iron Editorial, C2.1). Consolidation, not deletion: every
// former destination stays reachable within its owning tab (see `children`). Execution
// (/trainee/workouts/:id) lives under Train; the analytics list (/trainee/workouts)
// lives under Progress — the matchers keep them distinct.
const traineeNav: NavItem[] = [
  {
    to: '/trainee/today',
    label: 'Today',
    icon: CalendarCheck,
    match: (p) => p.startsWith('/trainee/today') || p.startsWith('/trainee/check-in') || p === '/trainee/dashboard',
  },
  {
    to: '/trainee/program',
    label: 'Train',
    icon: Dumbbell,
    match: (p) => p.startsWith('/trainee/program') || p.startsWith('/trainee/workouts/'),
  },
  {
    to: '/trainee/progress',
    label: 'Progress',
    icon: TrendingUp,
    match: (p) => p.startsWith('/trainee/progress') || p === '/trainee/workouts',
    children: [
      { to: '/trainee/progress', label: 'Daily' },
      { to: '/trainee/workouts', label: 'Workouts' },
    ],
  },
  {
    to: '/profile',
    label: 'You',
    icon: UserRound,
    match: (p) => p.startsWith('/profile') || p.startsWith('/settings') || p.startsWith('/onboarding'),
    children: [
      { to: '/profile', label: 'Profile' },
      { to: '/onboarding', label: 'Assessment' },
      { to: '/settings', label: 'Settings' },
    ],
  },
]

function activeItem(items: NavItem[], pathname: string): NavItem | undefined {
  return items.find((item) => item.match(pathname))
}

function titleRole(role: string): string {
  return role.charAt(0).toUpperCase() + role.slice(1)
}

function isSubActive(pathname: string, to: string): boolean {
  return to === '/trainee/workouts' ? pathname === '/trainee/workouts' : pathname.startsWith(to)
}

// A single editorial nav row (ember left-rail + tick on the active tab). Shared by both
// roles so the coach and trainee shells speak one visual language.
function NavRow({ item, isActive }: { item: NavItem; isActive: boolean }) {
  const { to, label, icon: Icon } = item
  return (
    <Link to={to} aria-current={isActive ? 'page' : undefined} className={`relative flex min-h-11 items-center gap-3 rounded-mb-control px-3 text-mb-body font-semibold transition-colors duration-mb-micro ${isActive ? 'bg-mb-inset text-mb-ink' : 'text-mb-secondary hover:bg-mb-inset hover:text-mb-ink'}`}>
      {isActive && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-mb-ember" />}
      <Icon aria-hidden="true" className={`size-[1.125rem] ${isActive ? 'text-mb-ember' : ''}`} />
      {label}
    </Link>
  )
}

// Desktop sidebar navigation. Trainee = Iron Editorial 4-tab IA (indented secondary
// links under the active tab). Coach = the light "training studio" expression of the
// same system: editorial groups (Studio / Oversight / Account) under labeled hairlines.
function DesktopNav({ items, pathname, trainee }: { items: NavItem[]; pathname: string; trainee: boolean }) {
  const active = activeItem(items, pathname)
  if (!trainee) {
    return (
      <nav aria-label="coach navigation" className="mt-7 space-y-5">
        {coachGroups.map((group) => (
          <div key={group.label}>
            <HairRule label={group.label} className="mb-1.5 px-1" />
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <NavRow key={item.to} item={item} isActive={active?.to === item.to} />
              ))}
            </div>
          </div>
        ))}
      </nav>
    )
  }
  return (
    <nav aria-label="trainee navigation" className="mt-8 space-y-1">
      {items.map((item) => {
        const { to, label, icon: Icon } = item
        const isActive = active?.to === to
        return (
          <div key={to}>
            <Link to={to} aria-current={isActive ? 'page' : undefined} className={`relative flex min-h-11 items-center gap-3 rounded-mb-control px-3 text-mb-body font-semibold transition-colors ${isActive ? 'bg-mb-inset text-mb-ink' : 'text-mb-secondary hover:bg-mb-inset hover:text-mb-ink'}`}>
              {isActive && <span aria-hidden="true" className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-mb-ember" />}
              <Icon aria-hidden="true" className={`size-[1.125rem] ${isActive ? 'text-mb-ember' : ''}`} />
              {label}
            </Link>
            {isActive && item.children && item.children.length > 1 && (
              <div className="mb-1 mt-1 space-y-0.5 pl-11">
                {item.children.map((child) => (
                  <Link key={child.to} to={child.to} className={`block rounded-mb-control px-2 py-1.5 text-mb-label transition-colors ${isSubActive(pathname, child.to) ? 'text-mb-ember' : 'text-mb-muted hover:text-mb-ink'}`}>
                    {child.label}
                  </Link>
                ))}
              </div>
            )}
          </div>
        )
      })}
    </nav>
  )
}

// In-content secondary navigation for the active tab's children (mobile + desktop),
// so relocated destinations (Progress→Daily/Workouts, You→Profile/Assessment/Settings)
// stay one tap away without a cluttered top-level bar.
function SecondaryNav({ item, pathname }: { item: NavItem; pathname: string }) {
  if (!item.children || item.children.length < 2) return null
  // Mobile only — the desktop sidebar exposes these as indented sub-links.
  return (
    <nav aria-label={`${item.label} sections`} className="mb-6 flex flex-wrap gap-2 lg:hidden">
      {item.children.map((child) => {
        const active = isSubActive(pathname, child.to)
        return (
          <Link key={child.to} to={child.to} className={`inline-flex min-h-11 items-center rounded-full border px-4 text-mb-label font-medium transition-colors ${active ? 'border-mb-ember/40 bg-mb-ember/10 text-mb-ink' : 'border-mb-hairline text-mb-secondary hover:text-mb-ink'}`}>
            {child.label}
          </Link>
        )
      })}
    </nav>
  )
}

export function AppShell({ children, morningBrief = false }: { children: ReactNode; morningBrief?: boolean }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const scope = useAccountQueryScope()
  const profileQuery = useQuery({ queryKey: [...scope, 'me-profile'], queryFn: () => api<UserProfile>('/me/profile'), enabled: Boolean(user) })
  if (!user) return children
  const role = user.role
  const trainee = role === 'trainee'
  const items = trainee ? traineeNav : coachNav
  const active = activeItem(items, location.pathname)
  const fullName = `${user.first_name} ${user.last_name}`
  const avatarSrc = profileQuery.data?.avatar?.content_url
  const detailContext = location.pathname.includes('/coach/trainees/')
  function signOut() { logout(); navigate('/login', { replace: true }) }
  const exitLabel = user.is_demo ? 'Exit demo' : 'Sign out'

  // Bottom padding clears the fixed mobile bottom nav (one row of four items, ~64px)
  // plus the device safe area; released at lg where the nav is hidden.
  const navClearance = 'pb-[calc(7rem_+_env(safe-area-inset-bottom))] lg:pb-10'
  // One Iron Editorial ground for both roles: warm paper, true ink. Coach = the light
  // "training studio" expression, trainee = the same system with its 4-tab IA.
  const rootBg = 'bg-mb-page'
  const panel = 'border-mb-hairline bg-mb-surface'
  const mainBase = morningBrief
    ? `min-h-screen ${rootBg} px-4 pt-6 sm:px-6 sm:pt-8 lg:ml-64 lg:px-8 lg:pt-10 xl:px-12 ${navClearance}`
    : `mx-auto min-h-screen max-w-app px-4 pt-6 sm:px-6 sm:pt-8 lg:ml-64 lg:px-8 lg:pt-10 xl:px-12 ${navClearance}`

  const brandHome = trainee ? '/trainee/today' : '/coach/dashboard'

  return (
    <div className={`min-h-screen ${rootBg}`}>
      <EnvironmentBanner inAppShell />
      <a href="#main-content" className="fixed left-3 top-3 z-50 -translate-y-24 rounded-lg bg-foreground px-4 py-2 text-sm font-semibold text-white transition-transform focus:translate-y-0">Skip to main content</a>
      <aside className={`fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r px-4 py-5 lg:flex ${panel}`}>
        <Link to={brandHome} className="block rounded-mb-control px-2 py-1">
          <Wordmark size="md" />
          <Eyebrow className="mt-1.5 text-mb-muted">{trainee ? 'Strength intelligence' : 'Coaching studio'}</Eyebrow>
        </Link>
        <DesktopNav items={items} pathname={location.pathname} trainee={trainee} />
        {role === 'coach' && (
          <div className="mt-7">
            <HairRule className="mb-3" />
            <p className="flex items-center gap-2 px-1 font-structure text-mb-label font-semibold text-mb-ink"><Users aria-hidden="true" className="size-4 text-mb-ember" />Coach workspace</p>
            <p className="mt-1.5 px-1 font-structure text-mb-micro leading-5 text-mb-muted">Read health intelligence and author reusable training.</p>
          </div>
        )}
        <div className="mt-auto border-t border-mb-hairline pt-4">
          <div className="flex items-center gap-3 px-2">
            <Avatar name={fullName} src={avatarSrc} size="md" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-mb-ink">{user.first_name} {user.last_name}</p>
              <p className="truncate font-numeral text-[0.65rem] uppercase tracking-[0.18em] text-mb-muted">{user.is_demo ? `Demo · ${role}` : titleRole(role)}</p>
            </div>
            <button type="button" onClick={signOut} aria-label={exitLabel} className="inline-flex min-h-11 items-center gap-2 rounded-mb-control px-2 text-xs font-semibold text-mb-muted hover:bg-mb-inset hover:text-mb-ink">
              <LogOut aria-hidden="true" className="size-[1.125rem]" />{user.is_demo && <span>Exit</span>}
            </button>
          </div>
        </div>
      </aside>
      <header className="sticky top-0 z-20 border-b border-mb-hairline bg-mb-surface/95 backdrop-blur lg:hidden">
        <div className="flex min-h-16 items-center justify-between px-4 sm:px-6">
          <Link to={brandHome} aria-label="Vytal home"><Wordmark size="sm" /></Link>
          <div className="flex items-center gap-2">
            <Avatar name={fullName} src={avatarSrc} size="sm" />
            <span className="max-w-28 truncate text-sm font-semibold text-mb-ink">{user.first_name}</span>
            <button type="button" onClick={signOut} aria-label={exitLabel} className="inline-flex min-h-11 items-center gap-1.5 rounded-mb-control px-2 text-xs font-semibold text-mb-muted hover:bg-mb-inset">
              <LogOut aria-hidden="true" className="size-5" />{user.is_demo && <span>Exit demo</span>}
            </button>
          </div>
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className={mainBase}>
        {user.is_demo && (
          <div role="status" aria-label="Demo workspace" className="mb-6 rounded-mb-inset border border-mb-hairline bg-mb-inset px-4 py-3">
            <p className="font-numeral text-[0.65rem] uppercase tracking-[0.18em] text-mb-muted">Demo workspace · read-only</p>
            <p className="mt-1.5 text-sm text-mb-secondary">All people and health information shown here are synthetic — changes are disabled.</p>
          </div>
        )}
        {detailContext && <p className="mb-4 font-numeral text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-mb-muted">Trainee record</p>}
        {trainee && active && <SecondaryNav item={active} pathname={location.pathname} />}
        {children}
      </main>
      <nav aria-label={`${role} navigation`} className="safe-bottom fixed inset-x-0 bottom-0 z-30 border-t border-mb-hairline bg-mb-surface/95 px-2 pt-2 backdrop-blur lg:hidden">
        <div className={`mx-auto grid max-w-lg ${trainee ? 'grid-cols-4' : 'grid-cols-4 gap-y-1'}`}>
          {items.map((item) => {
            const isActive = active?.to === item.to
            const Icon = item.icon
            return (
              <Link key={item.to} to={item.to} aria-current={isActive ? 'page' : undefined} className={`relative flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-mb-control text-[0.65rem] font-semibold sm:text-xs ${isActive ? 'text-mb-ink' : 'text-mb-muted'}`}>
                {isActive && <span aria-hidden="true" className="absolute top-1 h-0.5 w-6 rounded-full bg-mb-ember" />}
                <Icon aria-hidden="true" className="size-5" />
                {item.label}
              </Link>
            )
          })}
        </div>
      </nav>
    </div>
  )
}

export function ProfileMeta({ role }: { role: 'coach' | 'trainee' }) {
  return <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted"><UserRound aria-hidden="true" className="size-3.5" />{role === 'coach' ? 'Coach view' : 'Trainee view · assigned coach access'}</span>
}
