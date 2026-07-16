import { Dumbbell, LayoutTemplate } from 'lucide-react'
import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { AppShell } from '../AppShell'
import { PageHeader } from '../ui'

const tabs = [
  { to: '/coach/programming/exercises', label: 'Exercises', icon: Dumbbell },
  { to: '/coach/programming/templates', label: 'Workout Templates', icon: LayoutTemplate },
]

export function ProgrammingShell({ children, title, description, action }: { children: ReactNode; title: string; description: string; action?: ReactNode }) {
  const location = useLocation()
  return <AppShell><div className="space-y-6"><PageHeader eyebrow="Programming" title={title} description={description} action={action} /><nav aria-label="Programming sections" className="overflow-x-auto"><div role="tablist" aria-label="Programming workspace" className="inline-flex min-w-full gap-1 rounded-xl border bg-surface p-1 sm:min-w-0">{tabs.map(({ to, label, icon: Icon }) => { const active = location.pathname.startsWith(to); return <Link key={to} to={to} role="tab" aria-selected={active} className={`inline-flex min-h-11 flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-4 text-sm font-semibold sm:flex-none ${active ? 'bg-primary text-white' : 'text-secondary hover:bg-elevated hover:text-foreground'}`}><Icon aria-hidden="true" className="size-4" />{label}</Link> })}</div></nav>{children}</div></AppShell>
}
