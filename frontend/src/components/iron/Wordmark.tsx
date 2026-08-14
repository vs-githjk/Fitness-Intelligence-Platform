// Iron Editorial typographic wordmark (Vytal).
//
// The identity's own typography carries the brand: the athletic-display face for the
// VYTAL wordmark with ember as identity punctuation only (§9 — ember = training
// interaction AND identity; §21 — login uses ember only as punctuation). This retires
// the disconnected raster logo on the front door and trainee shell.
// Themeable through the mb tokens; on a fixed-ink cover pass an explicit bone class.

type Size = 'sm' | 'md' | 'lg'

const NAME_SIZE: Record<Size, string> = {
  sm: 'text-base',
  md: 'text-xl',
  lg: 'text-3xl sm:text-4xl',
}

const TICK_SIZE: Record<Size, string> = {
  sm: 'size-1',
  md: 'size-1.5',
  lg: 'size-2',
}

export function Wordmark({
  size = 'md',
  className = 'text-mb-ink',
}: {
  size?: Size
  // Color for the VYTAL mark; the ember tick is fixed identity punctuation.
  className?: string
}) {
  return (
    <span className="inline-flex items-baseline gap-1" aria-label="Vytal">
      <span className={`font-display uppercase leading-none tracking-tight ${NAME_SIZE[size]} ${className}`} aria-hidden="true">
        Vytal
      </span>
      {/* Ember tick — the identity punctuation, echoing the active-tab tick. */}
      <span className={`${TICK_SIZE[size]} translate-y-[-0.05em] rounded-[1px] bg-mb-ember`} aria-hidden="true" />
    </span>
  )
}
