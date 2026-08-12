// Morning Brief composition shells (Experience Cycle 1, Phase D).
//
// AtmosphereCanvas renders the whisper-level readiness background; GuidanceHero is
// the single dominant Surface that composes the day's one answer. Both are
// presentational — they receive an already-resolved band and slots, and own no
// business logic. Reusable beyond Today (e.g. a future Coach Dashboard hero).

import { ReactNode, useId } from 'react'
import { AtmosphereBand } from '../lib/today'

const BAND_VAR: Record<Exclude<AtmosphereBand, 'neutral'>, string> = {
  ready_to_push: '--mb-atm-gold',
  maintain: '--mb-atm-blue',
  reduce_intensity: '--mb-atm-amber',
  recovery_recommended: '--mb-atm-violet',
}

// Decorative, non-semantic background. It receives a resolved band (never a raw
// score), maps it to the approved atmosphere token, and renders a whisper-level
// tint. Meaning is always carried by the words, never by this layer.
export function AtmosphereCanvas({ band, className = '' }: { band: AtmosphereBand; className?: string }) {
  if (band === 'neutral') {
    return <div aria-hidden="true" className={`pointer-events-none absolute inset-0 ${className}`} />
  }
  const token = BAND_VAR[band]
  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none absolute inset-0 ${className}`}
      style={{
        background: `radial-gradient(120% 130% at 28% 0%, rgb(var(${token}) / var(--mb-atm-alpha)), transparent 68%)`,
        boxShadow: `inset 0 1px 0 0 rgb(var(${token}) / var(--mb-atm-edge-alpha))`,
      }}
    />
  )
}

// The loading state, shaped like the plan it precedes (Experience Cycle 1, Phase E).
// A calm, plan-shaped placeholder — NOT the old metric-card grid, no shimmer, no
// spinner, and no zeroed score. The visual is decorative; the human label is what
// assistive tech announces.
export function GhostPlan({ label = 'Getting today ready…' }: { label?: string }) {
  const bar = 'rounded-mb-control bg-mb-inset'
  const chip = 'rounded-mb-control bg-mb-surface'
  return (
    <div role="status" aria-live="polite" aria-busy="true" className="mx-auto w-full max-w-mb-guidance">
      <span className="sr-only">{label}</span>
      <section
        aria-hidden="true"
        className="rounded-mb-surface border border-mb-hairline bg-mb-surface p-mb-pad-surface shadow-mb-surface font-structure animate-mb-breathe motion-reduce:animate-none"
      >
        <div className="flex items-center gap-3">
          <div className="size-10 rounded-full bg-mb-inset" />
          <div className="space-y-1.5">
            <div className={`h-3 w-24 ${bar}`} />
            <div className={`h-2.5 w-16 ${bar}`} />
          </div>
        </div>
        <div className={`mt-5 h-3 w-28 ${bar}`} />
        <div className={`mt-3 h-8 w-3/4 ${bar}`} />
        <div className={`mt-2 h-8 w-1/2 ${bar}`} />
        <div className={`mt-4 h-3.5 w-full ${bar}`} />
        <div className={`mt-2 h-3.5 w-2/3 ${bar}`} />
        <div className="mt-5 rounded-mb-inset bg-mb-inset p-4">
          <div className={`h-4 w-40 ${chip}`} />
          <div className={`mt-2 h-3 w-24 ${chip}`} />
          <div className={`mt-4 h-11 w-40 ${chip}`} />
        </div>
      </section>
    </div>
  )
}

// The composition shell for the dominant answer. It composes an authorship slot,
// greeting, verdict (words-first), reason, a session slot, and action slots. It
// contains no Score, no raw readiness number, no alert stack, and no competing
// cards — it is the single dominant Surface on the screen.
export function GuidanceHero({
  atmosphere,
  attribution,
  greeting,
  verdict,
  reason,
  session,
  action,
  secondaryAction,
  className = '',
}: {
  atmosphere: AtmosphereBand
  attribution?: ReactNode
  greeting: string
  verdict: string
  reason?: string
  session?: ReactNode
  action?: ReactNode
  secondaryAction?: ReactNode
  className?: string
}) {
  const headingId = useId()
  return (
    <section
      aria-labelledby={headingId}
      className={`relative overflow-hidden rounded-mb-surface border border-mb-hairline bg-mb-surface p-mb-pad-surface shadow-mb-surface font-structure ${className}`}
    >
      <AtmosphereCanvas band={atmosphere} />
      <div className="relative">
        {attribution && <div className="mb-4">{attribution}</div>}
        <p className="text-mb-label text-mb-secondary">{greeting}</p>
        {/* Athletic display role (Iron Editorial §10): the verdict is the one place the
            display face leads. Uppercase + tight tracking; the accessible text is
            unchanged (CSS transform only). */}
        <h1 id={headingId} className="mt-1 text-balance font-display uppercase tracking-tight text-mb-display text-mb-ink sm:text-mb-display-xl">
          {verdict}
        </h1>
        {reason && <p className="mt-3 max-w-mb-measure text-mb-body-lg text-mb-secondary">{reason}</p>}
        {/* mt-5 (not mt-6): keep the reason→session rhythm generous but trim the
            excess that pushed the primary action toward/under the mobile fold. */}
        {session && <div className="mt-5">{session}</div>}
        {action && <div className="mt-5">{action}</div>}
        {secondaryAction && <div className="mt-3">{secondaryAction}</div>}
      </div>
    </section>
  )
}
