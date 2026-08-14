import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

// The banner keys off the explicit environment (appConfig.isStaging), never hostname or CSS.
const mockEnv = vi.hoisted(() => ({ appConfig: { isStaging: true, appVersion: '9.9.9' } }))
vi.mock('../env', () => mockEnv)

import { EnvironmentBanner } from './EnvironmentBanner'

afterEach(cleanup)

describe('EnvironmentBanner', () => {
  it('renders the staging indicator only in the staging environment', () => {
    mockEnv.appConfig.isStaging = true
    render(<EnvironmentBanner />)
    expect(screen.getByRole('status', { name: 'Staging environment' })).toBeVisible()
  })

  it('renders NOTHING in production — the marker is absent, not CSS-hidden', () => {
    mockEnv.appConfig.isStaging = false
    const { container } = render(<EnvironmentBanner />)
    expect(screen.queryByRole('status', { name: 'Staging environment' })).toBeNull()
    expect(container).toBeEmptyDOMElement()
  })
})
