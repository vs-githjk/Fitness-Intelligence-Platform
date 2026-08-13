// Iron Editorial — movement-pattern glyphs (Experience Cycle 2).
//
// One line-drawn geometric mark per `movement_pattern` value, on one 32-grid with a
// 2px-class stroke in `currentColor`. These render *training information* — each glyph
// is chosen by the exercise's real `movement_pattern` field (§11 family 1, §4.2
// traceability), never as decoration. Used on session posters, execution headers,
// exercise-reference, and session slips.
//
// INTERIM STATUS (clarification D): these are the approved data-true typographic/
// diagrammatic interim variants. They are NOT the commissioned Iron Line art set and do
// not pretend to be — they are honest abstract vectors of the movement axis (bar path,
// load, direction). The 15 patterns below are the full starter-library coverage
// (source of truth: backend/scripts/library_content.py). An unmapped pattern falls back
// to a neutral bar-path node (no fabricated movement claim).

type Props = {
  pattern?: string | null
  className?: string
  strokeWidth?: number
}

// Normalize a raw movement_pattern string to a glyph key. Strings are by convention,
// not enums, so we lower/trim/space-collapse before lookup (never guess a mapping).
function normalize(pattern?: string | null): string {
  return (pattern ?? '').trim().toLowerCase().replace(/\s+/g, ' ')
}

// Each entry is the inner SVG geometry for a 0 0 32 32 viewBox. Abstract, structural,
// one visual family: a "load" element + a movement-axis/direction path.
const GLYPHS: Record<string, JSX.Element> = {
  squat: (
    <>
      <path d="M8 9h16" />
      <path d="M16 9v13" />
      <path d="M10 16l6 6 6-6" />
    </>
  ),
  hinge: (
    <>
      <path d="M7 24h7l11-13" />
      <path d="M14 24v-9" />
      <circle cx="14" cy="24" r="1.6" />
    </>
  ),
  'horizontal push': (
    <>
      <path d="M7 10v12" />
      <path d="M7 16h15" />
      <path d="M17 11l6 5-6 5" />
    </>
  ),
  'horizontal pull': (
    <>
      <path d="M25 10v12" />
      <path d="M25 16H10" />
      <path d="M15 11l-6 5 6 5" />
    </>
  ),
  'vertical push': (
    <>
      <path d="M9 25h14" />
      <path d="M16 25V10" />
      <path d="M10 15l6-6 6 6" />
    </>
  ),
  'vertical pull': (
    <>
      <path d="M8 8h16" />
      <path d="M16 8v14" />
      <path d="M11 17l5 5 5-5" />
    </>
  ),
  lunge: (
    <>
      <path d="M15 6v8" />
      <path d="M15 14l-7 12" />
      <path d="M15 14l7 12" />
    </>
  ),
  isometric: (
    <>
      <path d="M10 8v16" />
      <path d="M22 8v16" />
      <path d="M13 16h6" />
    </>
  ),
  'static stretch': (
    <>
      <path d="M8 11v10" />
      <path d="M24 11v10" />
      <path d="M8 16h16" />
    </>
  ),
  'spinal flow': (
    <path d="M13 6c7 4-7 7 0 11s-7 5 0 9" />
  ),
  hang: (
    <>
      <path d="M8 8h16" />
      <path d="M16 8v14" />
      <circle cx="16" cy="24" r="2.4" />
    </>
  ),
  rowing: (
    <>
      <path d="M6 16h20" />
      <path d="M11 12l-5 4 5 4" />
      <path d="M21 12l5 4-5 4" />
    </>
  ),
  cycling: (
    <>
      <circle cx="16" cy="18" r="7" />
      <path d="M16 18l4-8" />
      <circle cx="16" cy="18" r="1.4" />
    </>
  ),
  running: (
    <>
      <path d="M7 11l5 5-5 5" />
      <path d="M16 11l5 5-5 5" />
    </>
  ),
  walking: (
    <>
      <path d="M8 21l5-5 5 5 6-6" />
      <circle cx="8" cy="21" r="1.3" />
    </>
  ),
}

// Neutral fallback: a bar-path node. Honest for an unmapped pattern — it asserts
// "a training movement" without claiming a specific axis it cannot trace.
const FALLBACK = (
  <>
    <path d="M8 16h16" />
    <circle cx="16" cy="16" r="2.6" />
  </>
)

export function MovementGlyph({ pattern, className = '', strokeWidth = 2 }: Props) {
  const geometry = GLYPHS[normalize(pattern)] ?? FALLBACK
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className={className}
    >
      {geometry}
    </svg>
  )
}
