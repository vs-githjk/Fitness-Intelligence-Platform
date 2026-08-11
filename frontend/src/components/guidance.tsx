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
        <h1 id={headingId} className="mt-1 text-balance text-mb-display text-mb-ink sm:text-mb-display-xl">
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
