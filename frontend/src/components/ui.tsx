/* eslint-disable react-refresh/only-export-components -- semantic helpers belong with UI primitives */
import {
  AlertCircle,
  Check,
  ChevronDown,
  CircleAlert,
  Info,
  LoaderCircle,
  Search,
  ShieldAlert,
} from 'lucide-react'
import {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  useId,
} from 'react'

export type Tone = 'neutral' | 'positive' | 'info' | 'attention' | 'risk' | 'critical'

const tones: Record<Tone, string> = {
  neutral: 'border-border bg-elevated text-secondary',
  positive: 'border-[rgb(var(--status-positive-border))] bg-[rgb(var(--status-positive-bg))] text-positive',
  info: 'border-[rgb(var(--status-info-border))] bg-[rgb(var(--status-info-bg))] text-info',
  attention: 'border-[rgb(var(--status-attention-border))] bg-[rgb(var(--status-attention-bg))] text-attention',
  risk: 'border-[rgb(var(--status-risk-border))] bg-[rgb(var(--status-risk-bg))] text-risk',
  critical: 'border-[rgb(var(--status-critical-border))] bg-[rgb(var(--status-critical-bg))] text-critical',
}

export function toneForSeverity(severity: string): Tone {
  if (severity === 'urgent') return 'critical'
  if (severity === 'elevated') return 'risk'
  if (severity === 'review') return 'attention'
  return 'info'
}

export function toneForStatus(status: string): Tone {
  if (['excellent', 'optimal', 'complete', 'good', 'within_configured_range', 'balanced_pattern', 'meets_baseline', 'highly_active', 'active'].includes(status)) return 'positive'
  if (['moderate', 'partial', 'review', 'limited_data', 'somewhat_active', 'low_active'].includes(status)) return 'attention'
  if (['high', 'very_high', 'needs_attention', 'outside_configured_range', 'recovery_review'].includes(status)) return 'risk'
  return 'neutral'
}

export function Button({
  variant = 'primary',
  loading = false,
  className = '',
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger'; loading?: boolean }) {
  const variants = {
    primary: 'bg-primary text-white hover:bg-primary-hover',
    secondary: 'border border-border bg-surface text-foreground hover:bg-elevated hover:border-secondary/40',
    ghost: 'text-secondary hover:bg-elevated hover:text-foreground',
    danger: 'bg-critical text-white hover:bg-critical/90',
  }
  return (
    <button
      className={`inline-flex min-h-11 items-center justify-center gap-2 rounded-xl px-4 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:bg-disabled/20 disabled:text-muted ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && <LoaderCircle aria-hidden="true" className="size-4 animate-spin" />}
      {children}
    </button>
  )
}

export function Card({ className = '', children, as: Element = 'section' }: { className?: string; children: ReactNode; as?: 'section' | 'article' | 'div' }) {
  return <Element className={`surface p-5 sm:p-6 ${className}`}>{children}</Element>
}

export function Badge({ children, tone = 'neutral', className = '' }: { children: ReactNode; tone?: Tone; className?: string }) {
  return <span className={`inline-flex min-h-6 items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold leading-5 ${tones[tone]} ${className}`}>{children}</span>
}

export function ProgressBar({ value, label, tone = 'primary', className = '' }: { value: number; label: string; tone?: 'primary' | 'positive' | 'attention' | 'risk'; className?: string }) {
  const fills = { primary: 'bg-primary', positive: 'bg-positive', attention: 'bg-attention', risk: 'bg-risk' }
  const safeValue = Math.max(0, Math.min(100, value))
  return (
    <div className={className}>
      <div className="h-2 overflow-hidden rounded-full bg-border/70" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={100} aria-valuenow={safeValue}>
        <div className={`h-full rounded-full ${fills[tone]}`} style={{ width: `${safeValue}%` }} />
      </div>
    </div>
  )
}

export function StatusNotice({ tone = 'info', title, children, action, className = '' }: { tone?: Tone; title: string; children: ReactNode; action?: ReactNode; className?: string }) {
  const icons = { neutral: Info, positive: Check, info: Info, attention: CircleAlert, risk: AlertCircle, critical: ShieldAlert }
  const Icon = icons[tone]
  return (
    <div className={`rounded-xl border p-4 ${tones[tone]} ${className}`}>
      <div className="flex gap-3">
        <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-foreground">{title}</p>
          <div className="mt-1 text-sm leading-6 text-secondary">{children}</div>
          {action && <div className="mt-3">{action}</div>}
        </div>
      </div>
    </div>
  )
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return (
    <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-3xl">
        {eyebrow && <p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">{eyebrow}</p>}
        <h1 className="mt-1 text-3xl font-bold leading-tight sm:text-4xl">{title}</h1>
        {description && <p className="mt-2 max-w-2xl text-sm leading-6 text-secondary sm:text-base">{description}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </header>
  )
}

export function Field({ label, help, error, optional, children, id: providedId }: { label: string; help?: string; error?: string; optional?: boolean; children: (props: { id: string; describedBy?: string; invalid: boolean }) => ReactNode; id?: string }) {
  const generatedId = useId(); const id = providedId ?? generatedId
  const helpId = help ? `${id}-help` : undefined; const errorId = error ? `${id}-error` : undefined
  const describedBy = [helpId, errorId].filter(Boolean).join(' ') || undefined
  return (
    <div>
      <label htmlFor={id} className="flex items-baseline justify-between gap-3 text-sm font-semibold text-foreground">
        <span>{label}</span>{optional && <span className="text-xs font-normal text-muted">Optional</span>}
      </label>
      {children({ id, describedBy, invalid: Boolean(error) })}
      {help && <p id={helpId} className="mt-1.5 text-xs leading-5 text-muted">{help}</p>}
      {error && <p id={errorId} className="mt-1.5 flex items-center gap-1.5 text-xs font-medium text-critical"><AlertCircle aria-hidden="true" className="size-3.5" />{error}</p>}
    </div>
  )
}

export function TextInput({ className = '', ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={`control mt-1.5 w-full ${props['aria-invalid'] ? 'border-critical' : ''} ${className}`} {...props} />
}

export function SelectInput({ className = '', children, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={`control mt-1.5 w-full ${props['aria-invalid'] ? 'border-critical' : ''} ${className}`} {...props}>{children}</select>
}

export function SearchField({ value, onChange, label = 'Search' }: { value: string; onChange: (value: string) => void; label?: string }) {
  const id = useId()
  return <div className="relative min-w-0 flex-1"><label htmlFor={id} className="sr-only">{label}</label><Search aria-hidden="true" className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted" /><input id={id} type="search" value={value} onChange={(event) => onChange(event.target.value)} placeholder={label} className="control w-full pl-10" /></div>
}

export function ChoiceCard({ selected, title, description, onClick }: { selected: boolean; title: string; description?: string; onClick: () => void }) {
  return <button type="button" aria-pressed={selected} onClick={onClick} className={`relative min-h-24 rounded-xl border p-4 text-left transition-colors ${selected ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'border-border bg-surface hover:border-secondary/50 hover:bg-elevated'}`}><span className="block pr-8 font-semibold text-foreground">{title}</span>{description && <span className="mt-1 block text-sm leading-5 text-muted">{description}</span>}<span className={`absolute right-4 top-4 grid size-5 place-items-center rounded-full border ${selected ? 'border-primary bg-primary text-white' : 'border-border'}`}>{selected && <Check aria-hidden="true" className="size-3.5" />}</span></button>
}

export function Chip({ selected, children, onClick }: { selected: boolean; children: ReactNode; onClick: () => void }) {
  return <button type="button" aria-pressed={selected} onClick={onClick} className={`inline-flex min-h-11 items-center gap-2 rounded-full border px-4 text-sm font-medium transition-colors ${selected ? 'border-primary bg-primary/5 text-primary' : 'border-border bg-surface text-secondary hover:border-secondary/50'}`}>{selected && <Check aria-hidden="true" className="size-4" />}{children}</button>
}

export function SegmentedControl({ label, value, options, onChange }: { label: string; value?: string; options: { value: string; label: string }[]; onChange: (value: string) => void }) {
  return <fieldset><legend className="text-sm font-semibold">{label}</legend><div className="mt-1.5 grid grid-cols-2 gap-1 rounded-xl bg-elevated p-1">{options.map(option => <button type="button" key={option.value} aria-pressed={value === option.value} onClick={() => onChange(option.value)} className={`min-h-10 rounded-lg px-3 text-sm font-semibold transition-colors ${value === option.value ? 'bg-surface text-primary shadow-sm' : 'text-secondary hover:text-foreground'}`}>{option.label}</button>)}</div></fieldset>
}

export function Disclosure({ summary, children, defaultOpen = false }: { summary: ReactNode; children: ReactNode; defaultOpen?: boolean }) {
  return <details open={defaultOpen} className="group"><summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 rounded-lg text-sm font-semibold text-primary"><span>{summary}</span><ChevronDown aria-hidden="true" className="size-4 transition-transform group-open:rotate-180" /></summary><div className="pt-3">{children}</div></details>
}

export function Skeleton({ className = '' }: { className?: string }) { return <div aria-hidden="true" className={`animate-pulse rounded-lg bg-border/70 ${className}`} /> }

export function LoadingState({ label = 'Loading' }: { label?: string }) {
  return <div role="status" aria-live="polite" className="space-y-4"><span className="sr-only">{label}</span><Skeleton className="h-8 w-48" /><Skeleton className="h-36 w-full" /><div className="grid gap-4 sm:grid-cols-3"><Skeleton className="h-28" /><Skeleton className="h-28" /><Skeleton className="h-28" /></div></div>
}

export function EmptyState({ icon: Icon = Info, title, description, action }: { icon?: typeof Info; title: string; description: string; action?: ReactNode }) {
  return <Card className="py-12 text-center"><span className="mx-auto grid size-12 place-items-center rounded-2xl bg-primary/8 text-primary"><Icon aria-hidden="true" className="size-6" /></span><h2 className="mt-4 text-xl font-semibold">{title}</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-secondary">{description}</p>{action && <div className="mt-5">{action}</div>}</Card>
}

export function ErrorState({ title = 'We could not load this page', description, onRetry }: { title?: string; description: string; onRetry?: () => void }) {
  return <Card className="py-10 text-center"><AlertCircle aria-hidden="true" className="mx-auto size-7 text-risk" /><h2 className="mt-3 text-xl font-semibold">{title}</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-secondary">{description}</p>{onRetry && <Button variant="secondary" className="mt-5" onClick={onRetry}>Try again</Button>}</Card>
}
