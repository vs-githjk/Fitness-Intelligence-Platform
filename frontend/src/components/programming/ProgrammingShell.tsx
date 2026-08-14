import { CalendarRange, Dumbbell, FileUp, LayoutTemplate, Library } from 'lucide-react'
import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { AppShell } from '../AppShell'
import { Eyebrow } from '../iron/Editorial'

const tabs = [
  { to: '/coach/programming/exercises', label: 'Exercises', icon: Dumbbell },
  { to: '/coach/programming/templates', label: 'Workout Templates', icon: LayoutTemplate },
  { to: '/coach/programming/programs', label: 'Programs', icon: CalendarRange },
  { to: '/coach/programming/import', label: 'Import', icon: FileUp },
  { to: '/coach/programming/library', label: 'Starter Library', icon: Library },
]

// The Programming Studio frame — the coach flagship. An editorial masthead (mono
// eyebrow + display title) over an underline tab bar with an ember active mark, so the
// studio reads as authored training space, not an admin tab strip.
export function ProgrammingShell({ children, title, description, action }: { children: ReactNode; title: string; description: string; action?: ReactNode }) {
  const location = useLocation()
  return (
    <AppShell>
      <div className="space-y-6 animate-mb-settle motion-reduce:animate-none">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-3xl">
            <Eyebrow>Programming Studio</Eyebrow>
            <h1 className="mt-2 text-mb-title tracking-tight text-mb-ink sm:text-mb-display">{title}</h1>
            {description && <p className="mt-2 max-w-2xl font-structure text-mb-body-lg text-mb-secondary">{description}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
        <nav aria-label="Programming sections" className="overflow-x-auto border-b border-mb-hairline">
          <div role="tablist" aria-label="Programming workspace" className="inline-flex min-w-full gap-1 sm:min-w-0 sm:gap-3">
            {tabs.map(({ to, label, icon: Icon }) => {
              const active = location.pathname.startsWith(to)
              return (
                <Link
                  key={to}
                  to={to}
                  role="tab"
                  aria-selected={active}
                  className={`group inline-flex min-h-11 flex-1 items-center justify-center gap-2 whitespace-nowrap border-b-2 px-3 pb-2.5 font-structure text-mb-body font-semibold transition-colors duration-mb-micro sm:flex-none ${active ? 'border-mb-ember text-mb-ink' : 'border-transparent text-mb-secondary hover:text-mb-ink'}`}
                >
                  <Icon aria-hidden="true" className={`size-4 ${active ? 'text-mb-ember' : 'text-mb-muted group-hover:text-mb-secondary'}`} />
                  {label}
                </Link>
              )
            })}
          </div>
        </nav>
        {children}
      </div>
    </AppShell>
  )
}
