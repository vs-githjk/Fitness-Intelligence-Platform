import { describe, expect, it } from 'vitest'
import { componentPresentation } from './dailyComponents'

// Every Daily Intelligence component key the engine can return in a DailyScore.
const KNOWN_KEYS = [
  'sleep_duration',
  'sleep_quality',
  'wake_refreshed',
  'fatigue',
  'soreness',
  'stress',
  'steps',
  'exercise_duration',
  'exercise_participation',
  'protein_compliance',
  'nutrition_adherence',
  'hydration_compliance',
  'recent_training_load',
]

// Frozen-spec removed vocabulary (docs/design/trainee-today.md §8) + machine casing.
const BANNED = [/compliance/i, /arbitrary units/i, /\b\w+_\w+\b/]

describe('componentPresentation', () => {
  it('maps every known component key to human label + explanation with no banned vocabulary', () => {
    for (const key of KNOWN_KEYS) {
      const { label, explanation } = componentPresentation(key)
      expect(label.length).toBeGreaterThan(0)
      expect(explanation.length).toBeGreaterThan(0)
      for (const pattern of BANNED) {
        expect(`${label} ${explanation}`).not.toMatch(pattern)
      }
    }
  })

  it('humanises an unrecognised future key and never emits a raw machine explanation', () => {
    const presentation = componentPresentation('some_future_signal')
    expect(presentation.label).toBe('Some Future Signal')
    expect(presentation.explanation).toBe('')
  })
})
