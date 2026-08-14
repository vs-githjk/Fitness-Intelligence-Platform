// Vytal body-region diagram (Iron Line family 3 — INTERIM, data-true).
//
// A geometric front/back figure that highlights the muscle REGIONS an exercise trains,
// driven strictly by the frozen §20 muscle→region map (see lib/muscles.ts). Primary
// movers fill ember; secondary movers fill ember at low opacity. It is deliberately a
// line-drawn geometric diagram — implementation artwork, never medically precise anatomy
// (§11, §20 precision law). Muscle strings outside the direct/broad map do not highlight
// here (they remain text chips elsewhere); the figure never invents a region.
//
// This is the interim variant; the commissioned Iron Line figure replaces it later without
// changing this component's contract.

import { classifyMuscles, type MuscleRegion } from '../../lib/muscles'

type Intensity = 'primary' | 'secondary' | undefined

type RegionRect = { x: number; y: number; w: number; h: number; r?: number }

// Region geometry within a single figure's local coordinates (0..90 wide, 0..200 tall).
// A region can appear on the front view, the back view, or both.
const FRONT: Partial<Record<MuscleRegion, RegionRect[]>> = {
  shoulders: [{ x: 20, y: 33, w: 11, h: 10, r: 3 }, { x: 59, y: 33, w: 11, h: 10, r: 3 }],
  chest: [{ x: 30, y: 41, w: 30, h: 15, r: 3 }],
  biceps: [{ x: 15, y: 45, w: 10, h: 17, r: 4 }, { x: 65, y: 45, w: 10, h: 17, r: 4 }],
  forearms: [{ x: 14, y: 74, w: 10, h: 22, r: 4 }, { x: 66, y: 74, w: 10, h: 22, r: 4 }],
  core: [{ x: 32, y: 57, w: 26, h: 31, r: 3 }],
  'hip-flexors': [{ x: 31, y: 89, w: 28, h: 10, r: 3 }],
  quadriceps: [{ x: 29, y: 100, w: 14, h: 42, r: 5 }, { x: 47, y: 100, w: 14, h: 42, r: 5 }],
  'lower-body': [{ x: 29, y: 100, w: 14, h: 42, r: 5 }, { x: 47, y: 100, w: 14, h: 42, r: 5 }],
}

const BACK: Partial<Record<MuscleRegion, RegionRect[]>> = {
  shoulders: [{ x: 20, y: 33, w: 11, h: 10, r: 3 }, { x: 59, y: 33, w: 11, h: 10, r: 3 }],
  back: [{ x: 30, y: 41, w: 30, h: 26, r: 3 }],
  torso: [{ x: 35, y: 41, w: 20, h: 46, r: 3 }],
  triceps: [{ x: 15, y: 45, w: 10, h: 18, r: 4 }, { x: 65, y: 45, w: 10, h: 18, r: 4 }],
  forearms: [{ x: 14, y: 74, w: 10, h: 22, r: 4 }, { x: 66, y: 74, w: 10, h: 22, r: 4 }],
  glutes: [{ x: 31, y: 90, w: 28, h: 15, r: 4 }],
  hamstrings: [{ x: 29, y: 106, w: 14, h: 38, r: 5 }, { x: 47, y: 106, w: 14, h: 38, r: 5 }],
  'lower-body': [{ x: 29, y: 106, w: 14, h: 38, r: 5 }, { x: 47, y: 106, w: 14, h: 38, r: 5 }],
}

// A calm geometric silhouette shared by both views (bone stroke, no fill).
function Silhouette() {
  return (
    <g fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinejoin="round" opacity={0.55}>
      <circle cx={45} cy={19} r={11} />
      <path d="M40 30 h10 v4 h-10 z" />
      {/* torso */}
      <path d="M28 34 h34 a4 4 0 0 1 4 4 v48 a6 6 0 0 1 -6 6 h-30 a6 6 0 0 1 -6 -6 v-48 a4 4 0 0 1 4 -4 z" />
      {/* arms */}
      <path d="M15 44 h10 v52 h-10 z" />
      <path d="M65 44 h10 v52 h-10 z" />
      {/* legs */}
      <path d="M29 98 h14 v88 h-14 z" />
      <path d="M47 98 h14 v88 h-14 z" />
    </g>
  )
}

function Figure({ view, active }: { view: 'front' | 'back'; active: Map<MuscleRegion, Intensity> }) {
  const geometry = view === 'front' ? FRONT : BACK
  return (
    <g>
      <Silhouette />
      {(Object.keys(geometry) as MuscleRegion[]).flatMap((region) => {
        const intensity = active.get(region)
        const rects = geometry[region] ?? []
        return rects.map((rect, index) => (
          <rect
            key={`${view}-${region}-${index}`}
            x={rect.x}
            y={rect.y}
            width={rect.w}
            height={rect.h}
            rx={rect.r ?? 2}
            className={
              intensity === 'primary'
                ? 'fill-mb-ember'
                : intensity === 'secondary'
                  ? 'fill-mb-ember/30'
                  : 'fill-mb-ember/[0.06]'
            }
          />
        ))
      })}
    </g>
  )
}

export function BodyMap({
  primary,
  secondary,
  className = '',
  showBack = true,
}: {
  primary?: string[] | null
  secondary?: string[] | null
  className?: string
  showBack?: boolean
}) {
  // Classify via the frozen §20 map; only direct/broad strings resolve to a region.
  const active = new Map<MuscleRegion, Intensity>()
  for (const muscle of classifyMuscles(secondary)) {
    if (muscle.region) active.set(muscle.region, 'secondary')
  }
  // Primary wins over secondary if a region is claimed by both.
  for (const muscle of classifyMuscles(primary)) {
    if (muscle.region) active.set(muscle.region, 'primary')
  }

  const trained = classifyMuscles(primary)
    .filter((m) => m.region)
    .map((m) => m.label)
  const summary = trained.length
    ? `Primary regions: ${trained.join(', ')}`
    : 'No mapped body region'

  return (
    <svg
      viewBox={showBack ? '0 0 200 200' : '0 0 90 200'}
      className={`text-mb-ink ${className}`}
      role="img"
      aria-label={summary}
    >
      <g transform="translate(0 4)">
        <Figure view="front" active={active} />
      </g>
      {showBack && (
        <g transform="translate(105 4)">
          <Figure view="back" active={active} />
        </g>
      )}
    </svg>
  )
}
