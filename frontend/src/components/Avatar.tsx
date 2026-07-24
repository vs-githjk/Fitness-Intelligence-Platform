import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { apiBlob } from '../api'
import { initialsFrom } from '../avatar'
import { useAccountQueryScope } from '../auth'

// A single, consistent identity avatar used everywhere a person appears. Photos are
// delivered through authorized routes that require the bearer token, so they cannot
// be loaded with a bare `<img src>`; the blob is fetched here and rendered via an
// object URL. When no photo URL is provided the shared initials fallback is shown
// with zero data dependencies, so it renders anywhere. The image is decorative: the
// person's name is always rendered adjacent, so it carries an empty alt.

const SIZES = {
  sm: 'size-8 text-[0.65rem]',
  md: 'size-9 text-sm',
  lg: 'size-12 text-base',
  xl: 'size-24 text-2xl',
} as const

export type AvatarSize = keyof typeof SIZES

function AvatarInitials({ name, size, className }: { name: string | null | undefined; size: AvatarSize; className: string }) {
  return (
    <span
      aria-hidden="true"
      className={`grid shrink-0 place-items-center rounded-full bg-primary/10 font-bold text-primary ${SIZES[size]} ${className}`}
    >
      {initialsFrom(name)}
    </span>
  )
}

/** Fetch an authorized avatar and expose it as a lifecycle-managed object URL. */
function useAvatarObjectUrl(src: string): string | null {
  const scope = useAccountQueryScope()
  const query = useQuery({
    queryKey: [...scope, 'avatar-blob', src],
    queryFn: () => apiBlob(src),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  useEffect(() => {
    if (!query.data) {
      setObjectUrl(null)
      return
    }
    const url = URL.createObjectURL(query.data)
    setObjectUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [query.data])
  return objectUrl
}

function AvatarImage({ name, src, size, className }: { name: string | null | undefined; src: string; size: AvatarSize; className: string }) {
  const url = useAvatarObjectUrl(src)
  if (!url) return <AvatarInitials name={name} size={size} className={className} />
  return <img src={url} alt="" className={`${SIZES[size]} shrink-0 rounded-full object-cover ${className}`} />
}

export function Avatar({
  name,
  src,
  size = 'md',
  className = '',
}: {
  name: string | null | undefined
  src?: string | null
  size?: AvatarSize
  className?: string
}) {
  // Only reach for the query/auth context when there is actually a photo to load.
  if (src) return <AvatarImage name={name} src={src} size={size} className={className} />
  return <AvatarInitials name={name} size={size} className={className} />
}
