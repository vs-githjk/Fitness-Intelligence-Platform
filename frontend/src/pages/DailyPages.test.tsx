import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { TrendSeries } from '../types'
import { checkInSchema } from '../lib/dailyValidation'
import { TrendChart } from './DailyPages'

const valid = {
  sleep_hours: 7.5,
  sleep_quality: 4,
  wake_refreshed: true,
  soreness: 2,
  fatigue: 3,
  stress: 4,
  steps: 8000,
  exercised: false,
  exercise_minutes: null,
  session_rpe: null,
  activity_types: [],
  water_liters: 2.5,
  calories_consumed: null,
  protein_grams: null,
  nutrition_adherence: null,
  overall_feeling: 'good' as const,
  note: null,
}

describe('daily check-in validation', () => {
  it('requires conditional exercise fields', () => {
    const result = checkInSchema.safeParse({ ...valid, exercised: true })
    expect(result.success).toBe(false)
    if (!result.success) {
      expect(result.error.issues.map(issue => issue.path[0])).toEqual([
        'exercise_minutes',
        'session_rpe',
      ])
    }
  })

  it('accepts a complete atomic check-in and preserves optional missing data', () => {
    const result = checkInSchema.safeParse(valid)
    expect(result.success).toBe(true)
    if (result.success) expect(result.data.protein_grams).toBeNull()
  })
})

describe('trend accessibility', () => {
  it('renders an explicit empty state when all dates are missing', () => {
    const series: TrendSeries = {
      key: 'recovery_score',
      label: 'Recovery Score',
      unit: 'points',
      points: [
        { date: '2026-07-13', value: null, missing: true },
        { date: '2026-07-14', value: null, missing: true },
      ],
    }
    render(<TrendChart series={series} />)
    expect(screen.getByText('No recorded values in this range.')).toBeVisible()
  })

  it('labels a real trend without converting a missing date to zero', () => {
    const series: TrendSeries = {
      key: 'recovery_score',
      label: 'Recovery Score',
      unit: 'points',
      points: [
        { date: '2026-07-12', value: 80, missing: false },
        { date: '2026-07-13', value: null, missing: true },
        { date: '2026-07-14', value: 60, missing: false },
      ],
    }
    render(<TrendChart series={series} />)
    expect(screen.getByRole('img')).toHaveAccessibleName(
      'Recovery Score trend with 2 recorded values',
    )
    expect(screen.queryByTitle(/Jul 13.*0 points/)).not.toBeInTheDocument()
  })
})
