import { ExerciseVersion } from '../../types'
import { MediaImage, MediaVideo } from '../AuthorizedMedia'
import { Badge, Card } from '../ui'
import { TrackingModeBadge } from './ProgrammingBadges'

const DIFFICULTY_TONE = { beginner: 'positive', intermediate: 'info', advanced: 'attention' } as const

function titleCase(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function LabelList({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null
  return (
    <div>
      <h3 className="text-xs font-bold uppercase tracking-wider text-muted">{title}</h3>
      <ul className="mt-2 space-y-1.5 text-sm leading-6 text-secondary">
        {items.map((item, index) => <li key={`${item}-${index}`} className="flex gap-2"><span aria-hidden="true" className="text-primary">•</span><span>{item}</span></li>)}
      </ul>
    </div>
  )
}

/** Read-only knowledge-and-media view — the coach-facing exercise detail. */
export function ExercisePreview({ version }: { version: ExerciseVersion }) {
  const chips = version.equipment
  const muscles = [...version.primary_muscle_groups.map(m => ({ m, primary: true })), ...version.secondary_muscle_groups.map(m => ({ m, primary: false }))]
  return (
    <Card as="section" className="space-y-6">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="mr-1 text-lg font-semibold">Preview</h2>
        <TrackingModeBadge mode={version.tracking_mode} />
        {version.difficulty && <Badge tone={DIFFICULTY_TONE[version.difficulty]}>{titleCase(version.difficulty)}</Badge>}
        <Badge tone="neutral">{titleCase(version.movement_pattern)}</Badge>
        {version.unilateral && <Badge tone="neutral">Unilateral</Badge>}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <figure className="space-y-2">
          <figcaption className="text-xs font-bold uppercase tracking-wider text-muted">Primary image</figcaption>
          {version.primary_image
            ? <MediaImage src={version.primary_image.content_url} alt={`${version.name} demonstration`} className="aspect-video w-full" />
            : <div className="grid aspect-video w-full place-items-center rounded-xl border border-dashed bg-elevated text-xs text-muted">No image yet</div>}
        </figure>
        <figure className="space-y-2">
          <figcaption className="text-xs font-bold uppercase tracking-wider text-muted">Demonstration video</figcaption>
          {version.demonstration_video
            ? <MediaVideo src={version.demonstration_video.content_url} className="aspect-video w-full" />
            : <div className="grid aspect-video w-full place-items-center rounded-xl border border-dashed bg-elevated text-xs text-muted">No video yet</div>}
        </figure>
      </div>
      {version.secondary_image && (
        <figure className="space-y-2">
          <figcaption className="text-xs font-bold uppercase tracking-wider text-muted">Secondary image</figcaption>
          <MediaImage src={version.secondary_image.content_url} alt={`${version.name} secondary view`} className="aspect-video w-full max-w-sm" />
        </figure>
      )}

      {version.description && <p className="text-sm leading-6 text-secondary">{version.description}</p>}

      <div>
        <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Instructions</h3>
        <p className="mt-2 whitespace-pre-line text-sm leading-6">{version.instructions}</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2">
        <LabelList title="Coaching cues" items={version.coaching_cues} />
        <LabelList title="Common mistakes" items={version.common_mistakes} />
        <LabelList title="Safety notes" items={version.safety_cues} />
        <div className="space-y-4">
          {chips.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Equipment</h3>
              <div className="mt-2 flex flex-wrap gap-2">{chips.map(item => <Badge key={item} tone="neutral">{item}</Badge>)}</div>
            </div>
          )}
          {muscles.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Muscles</h3>
              <div className="mt-2 flex flex-wrap gap-2">{muscles.map(({ m, primary }) => <Badge key={m} tone={primary ? 'info' : 'neutral'}>{m}</Badge>)}</div>
            </div>
          )}
        </div>
      </div>
    </Card>
  )
}
