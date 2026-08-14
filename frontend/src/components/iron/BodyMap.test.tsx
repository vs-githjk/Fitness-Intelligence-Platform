import { cleanup, render } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { BodyMap } from './BodyMap'

afterEach(cleanup)

describe('BodyMap', () => {
  it('summarizes the primary regions it maps for assistive tech', () => {
    const { getByRole } = render(<BodyMap primary={['quadriceps', 'glutes']} secondary={['core']} />)
    expect(getByRole('img')).toHaveAttribute('aria-label', 'Primary regions: quadriceps, glutes')
  })

  it('fills a region for a primary mover and a lighter fill for a secondary mover', () => {
    const { container } = render(<BodyMap primary={['chest']} secondary={['triceps']} />)
    // At least one region rect is filled at full ember (primary) and one at reduced (secondary).
    expect(container.querySelectorAll('.fill-mb-ember').length).toBeGreaterThan(0)
    expect(container.querySelectorAll('[class*="fill-mb-ember/30"]').length).toBeGreaterThan(0)
  })

  it('never highlights an unmapped (unknown) muscle string, only reports mapped ones', () => {
    // "calves" is outside the frozen §20 direct/broad map: it must not light a region.
    const { getByRole } = render(<BodyMap primary={['calves']} />)
    expect(getByRole('img')).toHaveAttribute('aria-label', 'No mapped body region')
  })

  it('renders a single figure when the back view is suppressed', () => {
    const { getByRole } = render(<BodyMap primary={['quadriceps']} showBack={false} />)
    expect(getByRole('img').getAttribute('viewBox')).toBe('0 0 90 200')
  })
})
