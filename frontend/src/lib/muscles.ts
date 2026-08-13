// Muscle vocabulary → anatomical-region presentation mapping (§20, FROZEN precision law).
//
// A deterministic presentation mapping from the exercise model's muscle strings (by
// convention, not enums) to a precision class. The precision law is binding:
//   never imply anatomical precision the source value does not contain.
//
//   - DIRECT (11 known strings): map 1:1 to a canonical region.
//   - BROAD  ("lower body" / "legs" → whole lower body; "spine" → mid-back/torso band):
//            stays VISIBLY broad — never silently narrowed to a precise claim.
//   - UNKNOWN / coach free-text: shown as plain text, NO anatomical highlight, never guessed.
//
// This lives in the presentation layer (no schema change) and feeds the eventual §11
// body figure (C2.5); today it drives chip styling so the three precision classes read
// differently. No medical or anatomical inference beyond the source value.

export type MusclePrecision = 'direct' | 'broad' | 'unknown'

export type MuscleRegion =
  | 'quadriceps'
  | 'glutes'
  | 'hamstrings'
  | 'chest'
  | 'triceps'
  | 'back'
  | 'shoulders'
  | 'biceps'
  | 'core'
  | 'forearms'
  | 'hip-flexors'
  | 'lower-body'
  | 'torso'

export type ClassifiedMuscle = {
  // The exact source string, preserved verbatim for display (never re-cased into a claim).
  label: string
  precision: MusclePrecision
  // Canonical region for a future body figure; null when unknown (no highlight).
  region: MuscleRegion | null
}

// The 11 direct strings, each 1:1 to its canonical region.
const DIRECT: Record<string, MuscleRegion> = {
  quadriceps: 'quadriceps',
  glutes: 'glutes',
  hamstrings: 'hamstrings',
  chest: 'chest',
  triceps: 'triceps',
  back: 'back',
  shoulders: 'shoulders',
  biceps: 'biceps',
  core: 'core',
  forearms: 'forearms',
  'hip flexors': 'hip-flexors',
}

// The 3 broad strings. They map to an explicitly broad region and MUST stay broad.
const BROAD: Record<string, MuscleRegion> = {
  'lower body': 'lower-body',
  legs: 'lower-body',
  spine: 'torso',
}

function normalize(raw: string): string {
  return raw.trim().toLowerCase().replace(/\s+/g, ' ')
}

export function classifyMuscle(raw: string): ClassifiedMuscle {
  const key = normalize(raw)
  if (key in DIRECT) return { label: raw.trim(), precision: 'direct', region: DIRECT[key] }
  if (key in BROAD) return { label: raw.trim(), precision: 'broad', region: BROAD[key] }
  return { label: raw.trim(), precision: 'unknown', region: null }
}

export function classifyMuscles(raw: string[] | null | undefined): ClassifiedMuscle[] {
  return (raw ?? []).filter((value) => value && value.trim().length > 0).map(classifyMuscle)
}
