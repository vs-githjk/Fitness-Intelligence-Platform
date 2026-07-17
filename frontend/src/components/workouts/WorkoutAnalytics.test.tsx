import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { WorkoutLoadWeek } from '../../types'
import {
  AdherenceTrend,
  LOAD_DISCLAIMER,
  StatusDistribution,
  VolumeTrend,
  WeeklyLoadChart,
  classificationLabel,
} from './WorkoutAnalytics'

afterEach(cleanup)

const week = (overrides: Partial<WorkoutLoadWeek> = {}): WorkoutLoadWeek => ({
  week_start_local_date: '2026-07-13',
  timezone: 'Asia/Kolkata',
  planned_session_load_total: 400,
  completed_session_load_total: 360,
  difference: -40,
  ratio: 0.9,
  completed_count: 3,
  partial_count: 1,
  skipped_count: 0,
  missed_count: 1,
  resistance_volume_kg: '1200.000',
  unavailable_planned_load_count: 0,
  unavailable_completed_load_count: 1,
  ...overrides,
})

describe('Workout analytics charts', () => {
  it('renders weekly planned vs completed with an accessible data table and missing shown, not zeroed', () => {
    render(<WeeklyLoadChart weeks={[week()]} />)
    expect(screen.getByRole('img', { name: /planned versus completed load/i })).toBeInTheDocument()
    // the "unavailable" completed count surfaces as text, never coerced to 0
    expect(screen.getByText(/0 planned \/ 1 completed/i)).toBeInTheDocument()
  })

  it('shows status distribution with text labels, not colour alone', () => {
    render(
      <StatusDistribution
        counts={{ completed: 3, partial: 1, ordinary_skipped: 0, safety_skipped: 2, missed: 1, pending: 0 }}
      />,
    )
    expect(screen.getByText('Completed')).toBeInTheDocument()
    expect(screen.getByText('Wellbeing skip')).toBeInTheDocument()
    expect(screen.getByText('Missed')).toBeInTheDocument()
  })

  it('renders volume dash for weeks without resistance volume rather than zero', () => {
    render(<VolumeTrend weeks={[week(), week({ week_start_local_date: '2026-07-20', resistance_volume_kg: null })]} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('shows N/A for a week with no eligible workouts in the adherence trend', () => {
    render(
      <AdherenceTrend
        weeks={[week({ completed_count: 0, partial_count: 0, skipped_count: 0, missed_count: 0 })]}
      />,
    )
    expect(screen.getByText('N/A')).toBeInTheDocument()
  })

  it('uses neutral recorded-best terminology, never PR wording', () => {
    expect(classificationLabel('safety_skipped')).toBe('Wellbeing skip')
    expect(classificationLabel('ordinary_skipped')).toBe('Skipped')
    expect(LOAD_DISCLAIMER).toMatch(/not a medical measure/i)
    // Guard against forbidden terminology sneaking into shared copy.
    expect(LOAD_DISCLAIMER.toLowerCase()).not.toContain('personal record')
    expect(LOAD_DISCLAIMER.toLowerCase()).not.toContain(' pr ')
  })
})
