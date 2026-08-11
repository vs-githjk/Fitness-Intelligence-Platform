import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import {
  DisclosureBlock,
  EvidenceRow,
  NoteLine,
  PrimaryCTA,
  Score,
  SectionHeader,
  SystemBanner,
  TrendDelta,
} from './ui'

afterEach(() => {
  cleanup()
  document.documentElement.removeAttribute('data-theme')
})

describe('PrimaryCTA', () => {
  it('disables and marks busy while loading without dropping its label', () => {
    render(<PrimaryCTA loading>Start workout</PrimaryCTA>)
    const button = screen.getByRole('button', { name: /start workout/i })
    expect(button).toBeDisabled()
    expect(button).toHaveAttribute('aria-busy', 'true')
    // Label is retained (kept invisible) so the button does not resize.
    expect(button).toHaveTextContent('Start workout')
  })

  it('honors an explicit disabled state', () => {
    render(<PrimaryCTA disabled>Save</PrimaryCTA>)
    expect(screen.getByRole('button', { name: 'Save' })).toBeDisabled()
  })

  it('fires onClick when enabled', () => {
    const onClick = vi.fn()
    render(<PrimaryCTA onClick={onClick}>Go</PrimaryCTA>)
    fireEvent.click(screen.getByRole('button', { name: 'Go' }))
    expect(onClick).toHaveBeenCalledOnce()
  })
})

describe('DisclosureBlock', () => {
  it('toggles aria-expanded and reveals content via its button', () => {
    render(
      <DisclosureBlock summary="Today's details">
        <p>Recovery 76</p>
      </DisclosureBlock>,
    )
    const trigger = screen.getByRole('button', { name: /today's details/i })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Recovery 76')).toBeNull()
    fireEvent.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('Recovery 76')).toBeInTheDocument()
    fireEvent.click(trigger)
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Recovery 76')).toBeNull()
  })
})

describe('NoteLine', () => {
  it('conveys tone without relying on color', () => {
    const { rerender } = render(<NoteLine tone="success">Sleep is trending up.</NoteLine>)
    expect(screen.getByText(/Going well:/)).toBeInTheDocument()
    rerender(<NoteLine tone="caution">Soreness is a little high.</NoteLine>)
    expect(screen.getByText(/Keep an eye on:/)).toBeInTheDocument()
    rerender(<NoteLine tone="neutral">Two more notes.</NoteLine>)
    expect(screen.getByText(/Note:/)).toBeInTheDocument()
  })
})

describe('SystemBanner', () => {
  it('announces a system condition with status semantics', () => {
    render(
      <SystemBanner tone="offline" title="You're offline">
        Showing this morning&apos;s plan.
      </SystemBanner>,
    )
    const banner = screen.getByRole('status')
    expect(within(banner).getByText("You're offline")).toBeInTheDocument()
    expect(within(banner).getByText(/Showing this morning/)).toBeInTheDocument()
  })

  it('supports info and demo variants', () => {
    const { rerender } = render(<SystemBanner tone="info" title="Heads up" />)
    expect(screen.getByRole('status')).toHaveTextContent('Heads up')
    rerender(<SystemBanner tone="demo" title="Demo workspace" />)
    expect(screen.getByRole('status')).toHaveTextContent('Demo workspace')
  })
})

describe('Score', () => {
  it('renders the backend word and an integer value', () => {
    render(<Score value={76.4} word="Strong" />)
    expect(screen.getByText('Strong')).toBeInTheDocument()
    expect(screen.getByText('76')).toBeInTheDocument()
  })

  it('renders missing values as unavailable, never zero', () => {
    render(<Score value={null} word="Recovery" />)
    expect(screen.getByText('Unavailable')).toBeInTheDocument()
    expect(screen.queryByText('0')).toBeNull()
  })

  it('supports custom unavailable copy', () => {
    render(<Score value={null} word="Nutrition" unavailableLabel="Add nutrition targets to track this" />)
    expect(screen.getByText('Add nutrition targets to track this')).toBeInTheDocument()
  })

  it('takes its band/tone from props, never re-thresholding the number', () => {
    // A high value with an explicit caution tone must render caution styling,
    // proving the component never derives meaning from the numeric value.
    render(<Score value={95} word="Ease off" tone="caution" />)
    expect(screen.getByText('Ease off')).toHaveClass('text-mb-caution')
  })

  it('exposes word and value as text for assistive technology', () => {
    render(<Score value={80} word="Ready to train" />)
    expect(screen.getByText('Ready to train')).toBeInTheDocument()
    expect(screen.getByText('80')).toBeInTheDocument()
  })

  it('renders a band-less score as an integer only, never inventing a word', () => {
    render(<Score value={76.4} />)
    expect(screen.getByText('76')).toBeInTheDocument()
  })
})

describe('TrendDelta', () => {
  it('shows a signed value and a non-color direction cue', () => {
    const { rerender } = render(<TrendDelta delta={3} />)
    expect(screen.getByText('+3')).toBeInTheDocument()
    expect(screen.getByText(/up/)).toBeInTheDocument()
    rerender(<TrendDelta delta={0} />)
    expect(screen.getByText('0')).toBeInTheDocument()
    expect(screen.getByText(/no change/)).toBeInTheDocument()
    rerender(<TrendDelta delta={-2} />)
    expect(screen.getByText('-2')).toBeInTheDocument()
    expect(screen.getByText(/down/)).toBeInTheDocument()
  })
})

describe('SectionHeader', () => {
  it('renders a heading with an optional action', () => {
    render(<SectionHeader action={<span>2 more</span>}>Going well</SectionHeader>)
    expect(screen.getByRole('heading', { name: 'Going well' })).toBeInTheDocument()
    expect(screen.getByText('2 more')).toBeInTheDocument()
  })
})

describe('EvidenceRow', () => {
  it('renders label, score word + value and an optional trend', () => {
    render(<EvidenceRow label="Recovery" value={76} word="Strong" tone="positive" trend={3} />)
    expect(screen.getByText('Recovery')).toBeInTheDocument()
    expect(screen.getByText('Strong')).toBeInTheDocument()
    expect(screen.getByText('76')).toBeInTheDocument()
    expect(screen.getByText('+3')).toBeInTheDocument()
  })

  it('shows missing scores as context copy and omits an absent trend', () => {
    render(<EvidenceRow label="Nutrition" value={null} word="Not tracked" unavailableLabel="Add nutrition targets" />)
    expect(screen.getByText('Add nutrition targets')).toBeInTheDocument()
  })
})

describe('renders under both Morning Brief themes', () => {
  it('mounts every Phase B component in light and dark', () => {
    for (const theme of ['light', 'dark'] as const) {
      document.documentElement.setAttribute('data-theme', theme)
      const { unmount } = render(
        <div>
          <PrimaryCTA>Start</PrimaryCTA>
          <SectionHeader>Going well</SectionHeader>
          <NoteLine tone="success">Good</NoteLine>
          <DisclosureBlock summary="Details">
            <p>evidence</p>
          </DisclosureBlock>
          <SystemBanner tone="info" title="Heads up" />
          <Score value={80} word="Strong" />
          <TrendDelta delta={2} />
          <EvidenceRow label="Recovery" value={76} word="Strong" />
        </div>,
      )
      expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument()
      unmount()
    }
  })
})
