// Vytal brand mark (Iron Editorial). Typographic — retires the raster FitIntel 360
// logo. The coach shell uses this; the trainee shell uses <Wordmark>. Both express one
// identity: the athletic-display wordmark with ember as identity punctuation (§9, §21).

type BrandProps = {
  compact?: boolean
  dark?: boolean
  className?: string
}

export function Brand({ compact = false, dark = false, className = '' }: BrandProps) {
  if (compact) {
    // Monogram tile — the identity mark (a printer's mark, not a missing image, §28).
    // Ink ground with an ember V; reads on both the coach light shell and dark.
    return (
      <span
        aria-label="Vytal"
        className={`inline-flex size-10 items-center justify-center rounded-xl bg-mb-ink-0 ${dark ? 'ring-1 ring-white/15' : ''} ${className}`}
      >
        <span className="font-display text-xl uppercase leading-none tracking-tight text-mb-ember" aria-hidden="true">V</span>
      </span>
    )
  }
  return (
    <span aria-label="Vytal" className={`inline-flex items-baseline gap-1.5 ${className}`}>
      <span className="font-display text-3xl uppercase leading-none tracking-tight text-mb-ink" aria-hidden="true">Vytal</span>
      <span className="size-2 translate-y-[-0.05em] rounded-[1px] bg-mb-ember" aria-hidden="true" />
    </span>
  )
}
