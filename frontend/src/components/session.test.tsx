import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import coachSource from './coach.tsx?raw'
import sessionSource from './session.tsx?raw'
import { SessionSlip, StatStrip } from './session'
import { CoachAttribution, CoachMessage } from './coach'
import { PrimaryCTA } from './ui'

afterEach(() => {
  cleanup()
  document.documentElement.removeAttribute('data-theme')
})

describe('StatStrip', () => {
  it('renders duration and effort as accessible facts', () => {
    render(<StatStrip durationMinutes={50} targetEffort={7} />)
    expect(screen.getByText(/about 50 minutes/)).toBeInTheDocument()
    expect(screen.getByText(/target effort 7 out of 10/)).toBeInTheDocument()
  })

  it('collapses a missing optional fact', () => {
    render(<StatStrip durationMinutes={40} />)
    expect(screen.getByText(/about 40 minutes/)).toBeInTheDocument()
    expect(screen.queryByText(/target effort/)).toBeNull()
  })

  it('renders nothing when no facts are present', () => {
    const { container } = render(<StatStrip />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('SessionSlip', () => {
  it('renders a workout with name, context, stat, coach note and a composed action', () => {
    render(
      <SessionSlip
        variant="workout"
        name="Lower Body Strength"
        context="Week 3"
        stat={<StatStrip durationMinutes={50} targetEffort={7} />}
        coachMessage={<CoachMessage note="Nice control." name="Jordan Ellis" />}
        action={<PrimaryCTA>Start workout</PrimaryCTA>}
      />,
    )
    expect(screen.getByRole('heading', { name: 'Lower Body Strength' })).toBeInTheDocument()
    expect(screen.getByText('Week 3')).toBeInTheDocument()
    expect(screen.getByText(/about 50 minutes/)).toBeInTheDocument()
    expect(screen.getByText('Nice control.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start workout' })).toBeInTheDocument()
  })

  it('renders a workout without a coach note', () => {
    render(<SessionSlip variant="workout" name="Upper Body Push" />)
    expect(screen.getByRole('heading', { name: 'Upper Body Push' })).toBeInTheDocument()
  })

  it('renders a rest variant and never shows workout stats', () => {
    render(
      <SessionSlip
        variant="rest"
        name="Rest day"
        description="You've earned it."
        stat={<StatStrip durationMinutes={50} />}
      />,
    )
    expect(screen.getByRole('heading', { name: 'Rest day' })).toBeInTheDocument()
    expect(screen.getByText("You've earned it.")).toBeInTheDocument()
    expect(screen.queryByText(/about 50 minutes/)).toBeNull()
  })

  it('announces the completed state and never strikes the name', () => {
    render(<SessionSlip variant="done" name="Lower Body Strength" />)
    const heading = screen.getByRole('heading')
    expect(heading).toHaveTextContent('Completed workout: Lower Body Strength')
    expect(heading.className).not.toMatch(/line-through/)
  })

  it('renders a compact row with a disabled composed action', () => {
    render(
      <SessionSlip
        variant="compact-row"
        name="Lower Body Strength"
        context="Mon"
        stat={<StatStrip durationMinutes={50} />}
        action={<PrimaryCTA disabled>Start</PrimaryCTA>}
      />,
    )
    expect(screen.getByText('Lower Body Strength')).toBeInTheDocument()
    expect(screen.getByText('Mon')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
  })
})

describe('Phase C components stay presentational', () => {
  it('do not import router, api client, auth state, or score-threshold logic', () => {
    for (const src of [coachSource, sessionSource]) {
      expect(src).not.toMatch(/from ['"][^'"]*react-router/)
      expect(src).not.toMatch(/from ['"]\.\.\/api['"]/)
      expect(src).not.toMatch(/from ['"]\.\.\/auth['"]/)
      expect(src).not.toMatch(/threshold|readinessTone/)
    }
  })
})

describe('renders under both Morning Brief themes', () => {
  it('mounts Phase C components in light and dark', () => {
    for (const theme of ['light', 'dark'] as const) {
      document.documentElement.setAttribute('data-theme', theme)
      const { unmount } = render(
        <div>
          <StatStrip durationMinutes={50} targetEffort={7} />
          <CoachAttribution variant="sender" name="Jordan Ellis" />
          <SessionSlip
            variant="workout"
            name="Lower Body Strength"
            context="Week 3"
            stat={<StatStrip durationMinutes={50} targetEffort={7} />}
            coachMessage={<CoachMessage note="Nice control." name="Jordan Ellis" />}
            action={<PrimaryCTA>Start</PrimaryCTA>}
          />
          <SessionSlip variant="rest" name="Rest day" description="Earned it." />
          <SessionSlip variant="done" name="Lower Body Strength" />
          <SessionSlip variant="compact-row" name="Lower Body Strength" context="Mon" />
        </div>,
      )
      expect(screen.getByRole('button', { name: 'Start' })).toBeInTheDocument()
      unmount()
    }
  })
})
