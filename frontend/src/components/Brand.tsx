type BrandProps = {
  compact?: boolean
  dark?: boolean
  className?: string
}

export function Brand({ compact = false, dark = false, className = '' }: BrandProps) {
  const source = compact
    ? '/brand/fitintel360-mark.png'
    : '/brand/fitintel360-logo.png'
  return (
    <img
      src={source}
      alt="FitIntel 360"
      className={`${compact ? 'size-10' : 'h-20 w-auto rounded-xl'} object-contain ${dark ? 'ring-1 ring-white/15' : ''} ${className}`}
      width={compact ? 500 : 530}
      height={compact ? 500 : 570}
    />
  )
}
