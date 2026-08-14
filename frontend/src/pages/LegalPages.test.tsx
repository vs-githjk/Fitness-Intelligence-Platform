import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { HealthDisclaimerPage, LegalFooter, PrivacyPage, SecurityPage } from './LegalPages'

afterEach(cleanup)

function renderAt(node: React.ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>)
}

describe('Legal pages', () => {
  it('security page lists verified controls and an honest non-claim, never marketing fiction', () => {
    renderAt(<SecurityPage />)
    expect(screen.getByRole('heading', { name: 'Security & Trust', level: 1 })).toBeVisible()
    expect(screen.getByText(/salted bcrypt hashes/i)).toBeVisible()
    expect(screen.getByText(/does not currently claim HIPAA compliance, SOC 2/i)).toBeVisible()
  })

  it('privacy page describes the coaching-relationship sharing and shows the pending notice', () => {
    renderAt(<PrivacyPage />)
    expect(screen.getByRole('heading', { name: 'Privacy Policy', level: 1 })).toBeVisible()
    expect(screen.getByText(/withdraw consent, which ends the sharing/i)).toBeVisible()
    // Company details are unset in the repo, so a clear pending notice must appear and no
    // raw [FOUNDER] placeholder text may leak.
    expect(screen.getByText('Pending final details')).toBeVisible()
    expect(screen.queryByText(/\[FOUNDER\]/)).toBeNull()
  })

  it('health disclaimer is unambiguous about not being medical care', () => {
    renderAt(<HealthDisclaimerPage />)
    expect(screen.getByText(/not a medical device and does not provide medical advice/i)).toBeVisible()
  })

  it('footer links to every legal document', () => {
    renderAt(<LegalFooter />)
    const nav = screen.getByRole('navigation', { name: 'Legal' })
    for (const label of ['Privacy', 'Consumer Health Data', 'Terms', 'Health Disclaimer', 'Security']) {
      expect(within(nav).getByRole('link', { name: label })).toBeVisible()
    }
  })
})
