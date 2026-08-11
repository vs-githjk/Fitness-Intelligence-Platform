// Presentation boundary for Daily Intelligence component keys (Experience
// Cycle 1, Phase D.1).
//
// The backend/domain keys and their raw explanations stay intact internally;
// this map is the ONLY place Today turns them into user-facing language. It keeps
// the frozen product vocabulary (docs/design/trainee-today.md §8): no snake_case,
// no machine-cased labels, no "compliance", no "arbitrary units", and no medical
// wording. Known Daily Intelligence keys never fall through to a generic
// titleize()/raw-explanation path; only an unrecognised future key does, and even
// then it gets a humanised label and no machine explanation.

import { titleize } from './format'

export type ComponentPresentation = { label: string; explanation: string }

const COMPONENT_PRESENTATION: Record<string, ComponentPresentation> = {
  sleep_duration: { label: 'Sleep duration', explanation: 'How your sleep length compared with your goal range.' },
  sleep_quality: { label: 'Sleep quality', explanation: 'How well you rated last night’s sleep.' },
  wake_refreshed: { label: 'Waking refreshed', explanation: 'Whether you woke up feeling refreshed.' },
  fatigue: { label: 'Fatigue', explanation: 'How tired you reported feeling today.' },
  soreness: { label: 'Soreness', explanation: 'How sore you reported feeling today.' },
  stress: { label: 'Stress', explanation: 'How much stress you reported today.' },
  steps: { label: 'Steps', explanation: 'Your step count for the day, scored on the usual activity bands.' },
  exercise_duration: {
    label: 'Exercise duration',
    explanation: 'How long you trained; extra time past an hour doesn’t add more credit.',
  },
  exercise_participation: {
    label: 'Exercise participation',
    explanation: 'Credit for training, with up to three activity types adding context.',
  },
  protein_compliance: {
    label: 'Protein intake',
    explanation: 'How your protein compared with your stored target, shown only when both a target and today’s intake exist.',
  },
  nutrition_adherence: {
    label: 'Nutrition plan',
    explanation: 'How closely you followed your nutrition plan, when you record it.',
  },
  hydration_compliance: {
    label: 'Hydration',
    explanation: 'How your water intake compared with your target for the day.',
  },
  recent_training_load: {
    label: 'Recent training load',
    explanation: 'Your recent training volume; it only eases your readiness once it climbs high.',
  },
}

export function componentPresentation(key: string): ComponentPresentation {
  return COMPONENT_PRESENTATION[key] ?? { label: titleize(key), explanation: '' }
}
