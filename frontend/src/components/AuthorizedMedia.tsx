import { useQuery } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { apiBlob } from '../api'
import { useAccountQueryScope } from '../auth'

// Renders media that lives behind an authorized route (the bearer token is required,
// so a bare `<img>`/`<video>` src cannot load it). The blob is fetched once, cached
// per identity scope, and exposed as an object URL. A failed fetch resolves to an
// explicit "media unavailable" state rather than a broken element.

type LoadState = 'loading' | 'ready' | 'error'

function useObjectUrl(src: string | null | undefined): { url: string | null; state: LoadState } {
  const scope = useAccountQueryScope()
  const query = useQuery({
    queryKey: [...scope, 'authorized-media', src ?? 'none'],
    queryFn: () => apiBlob(src as string),
    enabled: Boolean(src),
    retry: false,
    staleTime: 5 * 60 * 1000,
  })
  const [url, setUrl] = useState<string | null>(null)
  useEffect(() => {
    if (!query.data) {
      setUrl(null)
      return
    }
    const objectUrl = URL.createObjectURL(query.data)
    setUrl(objectUrl)
    return () => URL.revokeObjectURL(objectUrl)
  }, [query.data])
  if (!src) return { url: null, state: 'error' }
  if (query.isError) return { url: null, state: 'error' }
  return { url, state: url ? 'ready' : 'loading' }
}

function Unavailable({ label, className = '' }: { label: string; className?: string }) {
  return (
    <div className={`grid place-items-center rounded-xl border border-dashed bg-elevated p-4 text-center text-xs text-muted ${className}`} role="status">
      {label}
    </div>
  )
}

export function MediaImage({ src, alt, className = '' }: { src: string | null | undefined; alt: string; className?: string }) {
  const { url, state } = useObjectUrl(src)
  if (state === 'error') return <Unavailable label="Image unavailable" className={className} />
  if (state === 'loading') return <div className={`animate-pulse rounded-xl bg-elevated ${className}`} aria-label="Loading image" role="status" />
  return <img src={url as string} alt={alt} className={`rounded-xl object-cover ${className}`} />
}

export function MediaVideo({ src, className = '' }: { src: string | null | undefined; className?: string }) {
  const { url, state } = useObjectUrl(src)
  if (state === 'error') return <Unavailable label="Video unavailable" className={className} />
  if (state === 'loading') return <div className={`animate-pulse rounded-xl bg-elevated ${className}`} aria-label="Loading video" role="status" />
  return <video src={url as string} controls preload="metadata" className={`rounded-xl bg-black ${className}`} />
}
