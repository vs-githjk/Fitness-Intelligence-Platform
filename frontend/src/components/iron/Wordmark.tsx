// Iron Editorial typographic wordmark (Experience Cycle 2).
//
// Replaces the disconnected raster-logo treatment on the front door and trainee shell
// with the identity's own typography: the athletic-display face for FITINTEL, the
// engineered-numeral face for the "360", ember as identity punctuation only (§9 — ember
// = training interaction AND identity; §21 — login uses ember only as punctuation).
// Themeable through the mb tokens; on a fixed-ink cover pass an explicit bone class.

type Size = 'sm' | 'md' | 'lg'

const NAME_SIZE: Record<Size, string> = {
  sm: 'text-base',
  md: 'text-xl',
  lg: 'text-3xl sm:text-4xl',
}

const NUM_SIZE: Record<Size, string> = {
  sm: 'text-[0.6rem]',
  md: 'text-xs',
  lg: 'text-sm',
}

export function Wordmark({
  size = 'md',
  className = 'text-mb-ink',
}: {
  size?: Size
  // Color for the FITINTEL mark; ember "360" is fixed identity punctuation.
  className?: string
}) {
  return (
    <span className="inline-flex items-baseline gap-1.5" aria-label="FitIntel 360">
      <span className={`font-display uppercase leading-none tracking-tight ${NAME_SIZE[size]} ${className}`} aria-hidden="true">
        Fitintel
      </span>
      <span className={`font-numeral font-semibold leading-none tracking-tight text-mb-ember ${NUM_SIZE[size]}`} aria-hidden="true">
        360
      </span>
    </span>
  )
}
