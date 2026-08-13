import { describe, expect, it } from 'vitest'
import { classifyMuscle, classifyMuscles } from './muscles'

describe('muscle vocabulary → region precision law (§20)', () => {
  it('maps the 11 direct strings 1:1 to a region', () => {
    for (const value of ['quadriceps', 'glutes', 'hamstrings', 'chest', 'triceps', 'back', 'shoulders', 'biceps', 'core', 'forearms', 'hip flexors']) {
      const result = classifyMuscle(value)
      expect(result.precision).toBe('direct')
      expect(result.region).not.toBeNull()
      expect(result.label).toBe(value)
    }
  })

  it('keeps the broad strings visibly broad, never narrowed to a precise claim', () => {
    expect(classifyMuscle('lower body')).toMatchObject({ precision: 'broad', region: 'lower-body' })
    expect(classifyMuscle('legs')).toMatchObject({ precision: 'broad', region: 'lower-body' })
    expect(classifyMuscle('spine')).toMatchObject({ precision: 'broad', region: 'torso' })
  })

  it('treats unknown / coach free-text as plain text with no highlight, never guessed', () => {
    const result = classifyMuscle('rotator cuff-ish thing')
    expect(result.precision).toBe('unknown')
    expect(result.region).toBeNull()
    expect(result.label).toBe('rotator cuff-ish thing')
  })

  it('normalizes case and whitespace without altering the displayed label', () => {
    expect(classifyMuscle('  Glutes ')).toMatchObject({ precision: 'direct', label: 'Glutes' })
  })

  it('filters blanks and preserves order in classifyMuscles', () => {
    expect(classifyMuscles(['chest', '', '  ', 'lats'])).toEqual([
      { label: 'chest', precision: 'direct', region: 'chest' },
      { label: 'lats', precision: 'unknown', region: null },
    ])
    expect(classifyMuscles(null)).toEqual([])
  })
})
