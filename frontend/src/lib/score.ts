// Morning Brief score/display formatting — the WORD -> INTEGER -> SHAPE law
// (Experience Cycle 1, Phase B).
//
// These helpers apply ONLY to 0-100 band-interpreted product scores
// (Health Index, Recovery, Activity, Nutrition, Readiness, Adherence, ...).
// They must NOT be used for resistance load, weight prescriptions, distance,
// durations, or other coaching measurements where precision matters — those
// keep their real values and their own formatting.
//
// The band/meaning of a score always comes from a backend-provided
// interpretation field. Nothing here infers a band from a raw number.

export type ScoreTone = 'neutral' | 'positive' | 'caution' | 'info'

const MIN_SCORE = 0
const MAX_SCORE = 100

export function isScoreMissing(value: number | null | undefined): boolean {
  return value == null || Number.isNaN(value)
}

/** Round a 0-100 score for display. Never applied to non-score measurements. */
export function roundScore(value: number): number {
  return Math.round(value)
}

export function clampScore(value: number): number {
  return Math.max(MIN_SCORE, Math.min(MAX_SCORE, value))
}

/** Integer display of a 0-100 score; missing renders as the provided copy. */
export function formatScore(value: number | null | undefined, unavailableLabel = 'Unavailable'): string {
  return isScoreMissing(value) ? unavailableLabel : String(roundScore(value as number))
}

export type TrendDirection = 'up' | 'flat' | 'down'

/** Factual arithmetic direction of a rounded score delta (not an interpretation). */
export function trendDirection(delta: number): TrendDirection {
  const rounded = roundScore(delta)
  if (rounded > 0) return 'up'
  if (rounded < 0) return 'down'
  return 'flat'
}

/** Signed integer display of a score delta, e.g. "+3", "0", "-2". */
export function formatScoreDelta(delta: number): string {
  const rounded = roundScore(delta)
  return rounded > 0 ? `+${rounded}` : String(rounded)
}
