/* eslint-disable react-refresh/only-export-components -- semantic helpers belong with UI primitives */
import {
  AlertCircle,
  ArrowDown,
  ArrowUp,
  Check,
  ChevronDown,
  CircleAlert,
  Info,
  LoaderCircle,
  Minus,
  Search,
  ShieldAlert,
  WifiOff,
} from 'lucide-react'
import {
  ButtonHTMLAttributes,
  forwardRef,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
  useEffect,
  useId,
  useRef,
  useState,
} from 'react'
import { isScoreMissing, roundScore, ScoreTone, trendDirection } from '../lib/score'

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

export const TextInput = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean; describedBy?: string }>(function TextInput({ className = '', invalid, describedBy, ...props }, ref) {
  const ariaInvalid = props['aria-invalid'] || invalid || undefined
  return <input ref={ref} className={`control mt-1.5 w-full ${ariaInvalid ? 'border-critical' : ''} ${className}`} {...props} aria-describedby={props['aria-describedby'] ?? describedBy} aria-invalid={ariaInvalid} />
})

export const SelectInput = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement> & { invalid?: boolean; describedBy?: string }>(function SelectInput({ className = '', children, invalid, describedBy, ...props }, ref) {
  const ariaInvalid = props['aria-invalid'] || invalid || undefined
  return <select ref={ref} className={`control mt-1.5 w-full ${ariaInvalid ? 'border-critical' : ''} ${className}`} {...props} aria-describedby={props['aria-describedby'] ?? describedBy} aria-invalid={ariaInvalid}>{children}</select>
})

export const TextArea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean; describedBy?: string }>(function TextArea({ className = '', invalid, describedBy, ...props }, ref) {
  const ariaInvalid = props['aria-invalid'] || invalid || undefined
  return <textarea ref={ref} className={`control mt-1.5 min-h-28 w-full resize-y py-3 ${ariaInvalid ? 'border-critical' : ''} ${className}`} {...props} aria-describedby={props['aria-describedby'] ?? describedBy} aria-invalid={ariaInvalid} />
})

export function Modal({ open, title, description, children, onClose, size = 'md' }: { open: boolean; title: string; description?: string; children: ReactNode; onClose: () => void; size?: 'md' | 'lg' | 'xl' }) {
  const panel = useRef<HTMLDivElement>(null)
  const previousFocus = useRef<HTMLElement | null>(null)
  useEffect(() => {
    if (!open) return
    previousFocus.current = document.activeElement as HTMLElement | null
    const frame = window.requestAnimationFrame(() => panel.current?.querySelector<HTMLElement>('button, input, select, textarea, [href]')?.focus())
    function keydown(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
      if (event.key !== 'Tab' || !panel.current) return
      const controls = [...panel.current.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href], [tabindex]:not([tabindex="-1"])')]
      if (!controls.length) return
      const first = controls[0]; const last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
    }
    document.addEventListener('keydown', keydown)
    return () => { window.cancelAnimationFrame(frame); document.removeEventListener('keydown', keydown); previousFocus.current?.focus() }
  }, [onClose, open])
  if (!open) return null
  const widths = { md: 'max-w-lg', lg: 'max-w-3xl', xl: 'max-w-6xl' }
  return <div className="fixed inset-0 z-50 grid items-end bg-foreground/45 p-0 sm:items-center sm:p-6" onMouseDown={event => { if (event.target === event.currentTarget) onClose() }}><div ref={panel} role="dialog" aria-modal="true" aria-labelledby="modal-title" aria-describedby={description ? 'modal-description' : undefined} className={`max-h-[92vh] w-full overflow-y-auto rounded-t-2xl border bg-surface p-5 shadow-xl sm:mx-auto sm:rounded-2xl sm:p-6 ${widths[size]}`}><div className="pr-10"><h2 id="modal-title" className="text-2xl font-semibold">{title}</h2>{description && <p id="modal-description" className="mt-2 text-sm leading-6 text-secondary">{description}</p>}</div><div className="mt-5">{children}</div></div></div>
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

/* ============================================================
   Morning Brief primitives + intelligence layer (Experience Cycle 1, Phase B).
   These consume the --mb-* token system (see index.css) and render correctly
   in both Morning Brief light and dark contexts. They are additive: the legacy
   components above are unchanged, so unmigrated surfaces stay visually stable.
   ============================================================ */

export type { ScoreTone } from '../lib/score'

export const mbFocusRing =
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mb-action focus-visible:ring-offset-2 focus-visible:ring-offset-mb-surface'

const ctaVariants = {
  filled: 'bg-mb-action text-white hover:bg-mb-action-hover active:translate-y-px',
  ghost: 'border border-mb-hairline text-mb-ink hover:bg-mb-inset active:translate-y-px',
  text: 'text-mb-action underline-offset-4 hover:underline',
}

// Shared CTA styling so a router Link can be rendered as the primary action with
// correct link semantics, without coupling this presentational library to a router.
export function ctaClassName(variant: 'filled' | 'ghost' | 'text' = 'filled', className = '') {
  return `relative inline-flex min-h-12 items-center justify-center gap-2 rounded-mb-control px-5 font-structure text-mb-body font-semibold transition duration-mb-micro ease-mb-standard disabled:cursor-not-allowed disabled:opacity-60 ${mbFocusRing} ${ctaVariants[variant]} ${className}`
}

// The one prominent action on a surface. Filled variant is the single primary;
// ghost/text are secondary. Loading locks the label in place (no layout shift).
export function PrimaryCTA({
  variant = 'filled',
  loading = false,
  className = '',
  children,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'filled' | 'ghost' | 'text'; loading?: boolean }) {
  return (
    <button
      className={ctaClassName(variant, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      <span className={`inline-flex items-center gap-2 ${loading ? 'invisible' : ''}`}>{children}</span>
      {loading && <LoaderCircle aria-hidden="true" className="absolute size-5 animate-spin" />}
    </button>
  )
}

// Quiet caps section label; never competes with the content it introduces.
export function SectionHeader({ children, action, as: Element = 'h2', className = '' }: { children: ReactNode; action?: ReactNode; as?: 'h2' | 'h3'; className?: string }) {
  return (
    <div className={`flex items-baseline justify-between gap-3 ${className}`}>
      <Element className="font-structure text-mb-label font-semibold uppercase tracking-[0.06em] text-mb-secondary">{children}</Element>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  )
}

export type NoteTone = 'success' | 'caution' | 'neutral'

// A single line of positive/caution/neutral guidance. Meaning is carried by the
// sentence (and an assistive-tech label); the dot is decorative only.
export function NoteLine({ tone = 'neutral', children, className = '' }: { tone?: NoteTone; children: ReactNode; className?: string }) {
  const dot = { success: 'bg-mb-success', caution: 'bg-mb-caution', neutral: 'bg-mb-muted' }
  const srLabel = { success: 'Going well', caution: 'Keep an eye on', neutral: 'Note' }
  return (
    <p className={`flex gap-2.5 font-structure text-mb-body text-mb-ink ${className}`}>
      <span aria-hidden="true" className={`mt-[0.5rem] size-1.5 shrink-0 rounded-full ${dot[tone]}`} />
      <span className="min-w-0"><span className="sr-only">{srLabel[tone]}: </span>{children}</span>
    </p>
  )
}

// Progressive disclosure for supporting evidence. Answers never live here.
export function DisclosureBlock({ summary, children, defaultOpen = false, className = '' }: { summary: ReactNode; children: ReactNode; defaultOpen?: boolean; className?: string }) {
  const [open, setOpen] = useState(defaultOpen)
  const id = useId()
  const contentId = `${id}-content`
  return (
    <div className={className}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={contentId}
        onClick={() => setOpen(value => !value)}
        className={`flex min-h-11 w-full items-center justify-between gap-3 rounded-mb-control font-structure text-mb-body font-medium text-mb-secondary transition-colors duration-mb-micro hover:text-mb-ink ${mbFocusRing}`}
      >
        <span>{summary}</span>
        <ChevronDown aria-hidden="true" className={`size-4 transition-transform duration-mb-structural ${open ? 'rotate-180' : ''}`} />
      </button>
      <div id={contentId} hidden={!open} className="pt-3">{open && children}</div>
    </div>
  )
}

export type SystemBannerTone = 'info' | 'demo' | 'offline'

// Product/system-condition notice (offline, demo, maintenance). NEVER used for
// body-data warnings — its tone set contains no risk/error state by design.
export function SystemBanner({ tone = 'info', title, children, className = '' }: { tone?: SystemBannerTone; title: string; children?: ReactNode; className?: string }) {
  const Icon = tone === 'offline' ? WifiOff : Info
  return (
    <div role="status" className={`flex items-start gap-3 rounded-mb-inset bg-mb-inset px-4 py-3 font-structure text-mb-label text-mb-secondary ${className}`}>
      <Icon aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-mb-muted" />
      <div className="min-w-0">
        <p className="font-semibold text-mb-ink">{title}</p>
        {children && <p className="mt-0.5">{children}</p>}
      </div>
    </div>
  )
}

// A calm, single-surface Today state (invitation / error / offline). It is the
// same dominant Surface as GuidanceHero, re-weighted to one message + one action,
// so the screen's spatial memory stays stable across states. No red, no scaffolding,
// no metric grid — one heading, optional body, and at most one primary action.
export function StateSurface({
  icon: Icon,
  eyebrow,
  title,
  body,
  action,
  secondaryAction,
  className = '',
}: {
  icon?: typeof Info
  eyebrow?: string
  title: string
  body?: ReactNode
  action?: ReactNode
  secondaryAction?: ReactNode
  className?: string
}) {
  const headingId = useId()
  return (
    <section
      aria-labelledby={headingId}
      className={`rounded-mb-surface border border-mb-hairline bg-mb-surface p-mb-pad-surface shadow-mb-surface font-structure ${className}`}
    >
      {Icon && (
        <span className="grid size-11 place-items-center rounded-mb-inset bg-mb-inset text-mb-secondary">
          <Icon aria-hidden="true" className="size-5" />
        </span>
      )}
      {eyebrow && <p className={`${Icon ? 'mt-4 ' : ''}text-mb-label text-mb-secondary`}>{eyebrow}</p>}
      <h1 id={headingId} className={`${eyebrow ? 'mt-1 ' : Icon ? 'mt-4 ' : ''}text-balance text-mb-display text-mb-ink`}>
        {title}
      </h1>
      {body && <p className="mt-3 max-w-mb-measure text-mb-body-lg text-mb-secondary">{body}</p>}
      {action && <div className="mt-6">{action}</div>}
      {secondaryAction && <div className="mt-3">{secondaryAction}</div>}
    </section>
  )
}

const scoreWordClass: Record<ScoreTone, string> = {
  neutral: 'text-mb-secondary',
  positive: 'text-mb-success',
  caution: 'text-mb-caution',
  info: 'text-mb-info',
}

// The score law as a component: WORD (from the backend band) then INTEGER.
// The band/tone is NEVER derived from the number. The contract is a discriminated
// union so the law is enforced at compile time:
//   - a BANDED score MUST carry the backend interpretation `word` (WORD → INTEGER);
//   - an UNBANDED metric declares `banded: false` and simply cannot accept a word,
//     so a band is never invented for a metric the backend does not interpret.
type ScoreBase = {
  value: number | null | undefined
  variant?: 'row' | 'hero'
  unavailableLabel?: string
  className?: string
}
export type ScoreProps = ScoreBase & ({ banded: true; word: string; tone?: ScoreTone } | { banded: false })

export function Score(props: ScoreProps) {
  const { value, variant = 'row', unavailableLabel = 'Unavailable', className = '' } = props
  const word = props.banded ? props.word : undefined
  const tone: ScoreTone = props.banded ? props.tone ?? 'neutral' : 'neutral'
  const missing = isScoreMissing(value)
  const display = missing ? unavailableLabel : String(roundScore(value as number))
  if (variant === 'hero') {
    return (
      <div className={`font-structure ${className}`}>
        {word && <p className={`text-mb-label font-medium uppercase tracking-[0.04em] ${scoreWordClass[tone]}`}>{word}</p>}
        <p className={`mt-1 text-mb-display-xl tabular-nums ${missing ? 'text-mb-muted' : 'text-mb-ink'}`}>{display}</p>
      </div>
    )
  }
  return (
    <span className={`inline-flex items-baseline gap-2 font-structure ${className}`}>
      {word && <span className={`text-mb-label font-medium ${scoreWordClass[tone]}`}>{word}</span>}
      <span className={`text-mb-body font-semibold tabular-nums ${missing ? 'text-mb-muted' : 'text-mb-ink'}`}>{display}</span>
    </span>
  )
}

// Factual direction + signed integer of a 0-100 score delta. Direction is
// conveyed by glyph and an assistive-tech label, never by color alone.
export function TrendDelta({ delta, className = '' }: { delta: number; className?: string }) {
  const direction = trendDirection(delta)
  const rounded = roundScore(delta)
  const Arrow = direction === 'up' ? ArrowUp : direction === 'down' ? ArrowDown : Minus
  const srLabel = direction === 'up' ? 'up' : direction === 'down' ? 'down' : 'no change'
  const display = rounded > 0 ? `+${rounded}` : String(rounded)
  return (
    <span className={`inline-flex items-center gap-1 font-structure text-mb-label tabular-nums text-mb-secondary ${className}`}>
      <Arrow aria-hidden="true" className="size-3.5" />
      <span className="sr-only">{srLabel} </span>
      <span>{display}</span>
    </span>
  )
}

// A labelled evidence row: metric name + Score (+ optional TrendDelta). It carries
// the same banded/unbanded discriminated contract as `Score`, so an evidence row
// for a backend-banded metric must supply the word and a neutral metric cannot.
type EvidenceBase = {
  label: string
  value: number | null | undefined
  trend?: number | null
  unavailableLabel?: string
  className?: string
}
export type EvidenceRowProps = EvidenceBase & ({ banded: true; word: string; tone?: ScoreTone } | { banded: false })

export function EvidenceRow(props: EvidenceRowProps) {
  const { label, value, trend, unavailableLabel = 'Unavailable', className = '' } = props
  return (
    <div className={`flex items-center justify-between gap-4 py-3 font-structure ${className}`}>
      <span className="text-mb-body text-mb-secondary">{label}</span>
      <span className="flex items-center gap-3">
        {props.banded ? (
          <Score banded value={value} word={props.word} tone={props.tone} unavailableLabel={unavailableLabel} />
        ) : (
          <Score banded={false} value={value} unavailableLabel={unavailableLabel} />
        )}
        {trend != null && <TrendDelta delta={trend} />}
      </span>
    </div>
  )
}
