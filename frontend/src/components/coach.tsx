// Morning Brief voice layer (Experience Cycle 1, Phase C).
//
// Human authorship, rendered explicitly. These components are presentational and
// reusable anywhere a coach speaks (Today, coach detail, future messaging). They
// contain no routing, no API calls, and no application auth state — the coach
// avatar is delegated to the shared, canonical `Avatar` component.

import { Avatar, AvatarSize } from './Avatar'

function DemoTag() {
  return (
    <span className="rounded-mb-tag bg-mb-inset px-1.5 py-0.5 text-mb-micro font-semibold uppercase tracking-[0.04em] text-mb-secondary">
      Demo
    </span>
  )
}

export type CoachAttributionVariant = 'sender' | 'inline' | 'byline'

// The reusable authorship marker: a person (avatar + name), never a status
// widget — no rings, no presence dots, no verification, no invented title.
// Not interactive. Absent coach collapses to nothing.
export function CoachAttribution({
  name,
  avatarUrl,
  variant = 'inline',
  relationship = 'your coach',
  demo = false,
  className = '',
}: {
  name: string | null | undefined
  avatarUrl?: string | null
  variant?: CoachAttributionVariant
  relationship?: string
  demo?: boolean
  className?: string
}) {
  const displayName = name?.trim()
  if (!displayName) return null // absent coach → clean collapse

  const size: AvatarSize = variant === 'sender' ? 'md' : 'sm'
  const avatar = <Avatar name={displayName} src={avatarUrl} size={size} />

  if (variant === 'sender') {
    return (
      <div className={`flex items-center gap-3 font-structure ${className}`}>
        {avatar}
        <div className="min-w-0">
          <p className="flex items-center gap-2 text-mb-body font-semibold text-mb-ink">
            <span className="truncate">{displayName}</span>
            {demo && <DemoTag />}
          </p>
          {relationship && <p className="text-mb-label text-mb-secondary">{relationship}</p>}
        </div>
      </div>
    )
  }

  if (variant === 'byline') {
    return (
      <span className={`inline-flex items-center gap-2 font-structure ${className}`}>
        {avatar}
        <span className="text-mb-label font-medium text-mb-ink">{displayName}</span>
        {demo && <DemoTag />}
      </span>
    )
  }

  // inline (default) — e.g. attribution beneath a coach message.
  return (
    <span className={`inline-flex items-center gap-2 font-structure text-mb-label text-mb-secondary ${className}`}>
      {avatar}
      <span>
        <span aria-hidden="true">— </span>
        <span className="font-medium text-mb-ink">{displayName}</span>
        {relationship && <span>, {relationship}</span>}
      </span>
      {demo && <DemoTag />}
    </span>
  )
}

// Verbatim human-authored coach content. Renders in the serif voice token —
// SERIF = HUMAN-AUTHORED. Product-generated and AI/system text must never use
// this component. An absent/blank note collapses completely (no empty chrome).
export function CoachMessage({
  note,
  name,
  avatarUrl,
  demo = false,
  className = '',
}: {
  note: string | null | undefined
  name?: string | null
  avatarUrl?: string | null
  demo?: boolean
  className?: string
}) {
  const content = note?.trim()
  if (!content) return null // no note → no quote chrome at all

  return (
    <figure className={`border-l-2 border-mb-muted/40 pl-4 font-structure ${className}`}>
      <blockquote className="whitespace-pre-line font-voice text-mb-body-lg leading-relaxed text-mb-ink">
        {content}
      </blockquote>
      {name?.trim() && (
        <figcaption className="mt-2">
          <CoachAttribution variant="inline" name={name} avatarUrl={avatarUrl} demo={demo} />
        </figcaption>
      )}
    </figure>
  )
}
