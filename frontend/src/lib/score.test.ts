import { describe, expect, it } from 'vitest'
import {
  clampScore,
  formatScore,
  formatScoreDelta,
  isScoreMissing,
  roundScore,
  trendDirection,
} from './score'

describe('score formatting law (WORD -> INTEGER -> SHAPE)', () => {
  it('rounds 0-100 scores to integers for display', () => {
    expect(roundScore(76.4)).toBe(76)
    expect(roundScore(76.5)).toBe(77)
    expect(formatScore(32.2)).toBe('32')
  })

  it('never renders missing as zero', () => {
    expect(isScoreMissing(null)).toBe(true)
    expect(isScoreMissing(undefined)).toBe(true)
    expect(isScoreMissing(Number.NaN)).toBe(true)
    expect(isScoreMissing(0)).toBe(false)
    expect(formatScore(null)).toBe('Unavailable')
    expect(formatScore(undefined)).toBe('Unavailable')
    // A real zero is shown as zero; only missing renders as unavailable.
    expect(formatScore(0)).toBe('0')
  })

  it('supports custom unavailable copy for a metric', () => {
    expect(formatScore(null, 'Add nutrition targets to track this')).toBe(
      'Add nutrition targets to track this',
    )
  })

  it('clamps out-of-range values (for subordinate shape rendering only)', () => {
    expect(clampScore(-10)).toBe(0)
    expect(clampScore(140)).toBe(100)
    expect(clampScore(55)).toBe(55)
  })

  it('derives trend direction factually from the rounded delta', () => {
    expect(trendDirection(3)).toBe('up')
    expect(trendDirection(-2)).toBe('down')
    expect(trendDirection(0)).toBe('flat')
    expect(trendDirection(0.3)).toBe('flat')
  })

  it('formats signed score deltas', () => {
    expect(formatScoreDelta(3)).toBe('+3')
    expect(formatScoreDelta(0)).toBe('0')
    expect(formatScoreDelta(-2)).toBe('-2')
  })
})
