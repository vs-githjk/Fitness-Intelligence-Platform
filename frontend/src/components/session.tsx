// Morning Brief athletic objects (Experience Cycle 1, Phase C).
//
// StatStrip and SessionSlip are presentational and reusable (Today, Execution,
// Programming, history). They contain no routing, no API calls, no auth state,
// and no score-law components — actions are provided compositionally.

import { Check } from 'lucide-react'
import { ReactNode } from 'react'

// The factual prescription layer inside an athletic object. Facts only — no
// readiness interpretation, no scores, no status colours, no fake precision.
// Missing optional facts collapse; an all-empty strip renders nothing.
// Extend by adding further legitimate facts (e.g. distance, load) as optional
// props — do not add speculative variants ahead of a real need.
export function StatStrip({
  durationMinutes,
  targetEffort,
  className = '',
}: {
  durationMinutes?: number | null
  targetEffort?: number | null
  className?: string
}) {
  const facts: { key: string; visible: string; spoken: string }[] = []
  if (durationMinutes != null) {
    facts.push({ key: 'duration', visible: `≈${durationMinutes} min`, spoken: `about ${durationMinutes} minutes` })
  }
  if (targetEffort != null) {
    facts.push({ key: 'effort', visible: `effort ${targetEffort}/10`, spoken: `target effort ${targetEffort} out of 10` })
  }
  if (!facts.length) return null

  return (
    <p className={`font-stat text-mb-label uppercase tracking-[0.04em] tabular-nums text-mb-secondary ${className}`}>
      {facts.map((fact, index) => (
        <span key={fact.key}>
          {index > 0 && <span aria-hidden="true"> · </span>}
          <span aria-hidden="true">{fact.visible}</span>
          <span className="sr-only">
            {fact.spoken}
            {index < facts.length - 1 ? ', ' : ''}
          </span>
        </span>
      ))}
    </p>
  )
}

export type SessionSlipVariant = 'workout' | 'rest' | 'done' | 'compact-row'

// The primary athletic object: a session as a physical, inset thing. Composes a
// name, optional context, a StatStrip, an optional CoachMessage, and an action —
// all supplied by the caller. Never owns routing or business logic.
export function SessionSlip({
  variant = 'workout',
  name,
  context,
  description,
  stat,
  coachMessage,
  action,
  className = '',
}: {
  variant?: SessionSlipVariant
  name: string
  context?: string
  description?: ReactNode
  stat?: ReactNode
  coachMessage?: ReactNode
  action?: ReactNode
  className?: string
}) {
  const surface = `rounded-mb-inset bg-mb-inset font-structure ${className}`

  // Compact row for schedule/history reuse — keeps the slip identity in a row.
  if (variant === 'compact-row') {
    return (
      <div className={`flex items-center justify-between gap-4 px-4 py-3 ${surface}`}>
        <div className="min-w-0">
          <p className="truncate text-mb-body font-semibold text-mb-ink">{name}</p>
          {context && <p className="text-mb-label text-mb-secondary">{context}</p>}
          {stat && <div className="mt-1">{stat}</div>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
    )
  }

  const isDone = variant === 'done'
  const isRest = variant === 'rest'
  return (
    <div className={`p-4 ${surface}`}>
      <div className="flex items-start gap-2">
        {isDone && <Check aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-mb-success" />}
        <div className="min-w-0 flex-1">
          <h3 className="text-mb-heading font-semibold text-mb-ink">
            {isDone && <span className="sr-only">Completed workout: </span>}
            {name}
          </h3>
          {context && <p className="mt-0.5 text-mb-label text-mb-secondary">{context}</p>}
        </div>
        {isDone && <span aria-hidden="true" className="text-mb-label font-medium text-mb-success">Done</span>}
      </div>

      {description && <div className="mt-2 text-mb-body text-mb-secondary">{description}</div>}
      {/* Rest is a legitimate programmed state — it never shows workout stats. */}
      {!isRest && stat && <div className="mt-3">{stat}</div>}
      {coachMessage && <div className="mt-3">{coachMessage}</div>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
