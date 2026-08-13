// Iron Editorial composition primitives (Experience Cycle 2).
//
// Small, shared devices that carry the editorial voice through TYPE, RULE and SPACE
// rather than more cards (§7 "over-carding" anti-goal; §35). Used across the shell,
// Today, execution, and reference so the identity is recognizable before content is read.

import { ReactNode } from 'react'

// The engineered-numeral eyebrow: a quiet mono, uppercase, wide-tracked kicker. The
// single most recognizable Iron Editorial label device. Defaults to the ember accent
// where it marks a training/identity context; pass a className to recolor for calm/meta.
export function Eyebrow({
  children,
  className = 'text-mb-ember',
}: {
  children: ReactNode
  className?: string
}) {
  return (
    <p className={`font-numeral text-[0.7rem] font-semibold uppercase tracking-[0.22em] ${className}`}>
      {children}
    </p>
  )
}

// A labeled hairline rule — an editorial section divider that gives dark grounds visible
// rhythm and layering without wrapping content in another rounded rectangle. The optional
// label rides the rule in the mono meta voice.
export function HairRule({
  label,
  className = '',
}: {
  label?: ReactNode
  className?: string
}) {
  if (!label) {
    return <hr className={`border-0 border-t border-mb-hairline ${className}`} />
  }
  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <span className="font-numeral text-[0.65rem] font-medium uppercase tracking-[0.2em] text-mb-muted">{label}</span>
      <span aria-hidden="true" className="h-px flex-1 bg-mb-hairline" />
    </div>
  )
}
