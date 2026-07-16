type BrandProps = {
  compact?: boolean
  dark?: boolean
  className?: string
}

export function Brand({ compact = false, dark = false, className = '' }: BrandProps) {
  const source = compact
    ? `/brand/mark${dark ? '-dark' : ''}.svg`
    : `/brand/logo-horizontal${dark ? '-dark' : ''}.svg`
  return (
    <img
      src={source}
      alt="FitIntel 360"
      className={`${compact ? 'size-10' : 'h-12 w-auto'} ${className}`}
    />
  )
}
