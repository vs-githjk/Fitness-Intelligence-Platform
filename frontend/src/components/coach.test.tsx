import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import { initialsFrom } from '../avatar'
import { CoachAttribution, CoachMessage } from './coach'

afterEach(() => {
  cleanup()
  document.documentElement.removeAttribute('data-theme')
})

describe('CoachAttribution', () => {
  it('renders a sender row with name, relationship and an initials avatar', () => {
    render(<CoachAttribution variant="sender" name="Jordan Ellis" />)
    expect(screen.getByText('Jordan Ellis')).toBeInTheDocument()
    expect(screen.getByText('your coach')).toBeInTheDocument()
    expect(screen.getByText(initialsFrom('Jordan Ellis'))).toBeInTheDocument()
  })

  it('renders inline attribution with a decorative dash', () => {
    render(<CoachAttribution variant="inline" name="Jordan Ellis" />)
    expect(screen.getByText('Jordan Ellis')).toBeInTheDocument()
    expect(screen.getByText(/, your coach/)).toBeInTheDocument()
  })

  it('renders a compact byline', () => {
    render(<CoachAttribution variant="byline" name="Jordan Ellis" />)
    expect(screen.getByText('Jordan Ellis')).toBeInTheDocument()
  })

  it('falls back to initials when no photo is provided, keeping the name present', () => {
    render(<CoachAttribution name="Sam Okafor" />)
    expect(screen.getByText('Sam Okafor')).toBeInTheDocument()
    expect(screen.getByText(initialsFrom('Sam Okafor'))).toBeInTheDocument()
  })

  it('shows a demo tag in the demo workspace', () => {
    render(<CoachAttribution variant="sender" name="Jordan Ellis" demo />)
    expect(screen.getByText('Demo')).toBeInTheDocument()
  })

  it('collapses to nothing when the coach is absent', () => {
    const { container } = render(<CoachAttribution name={null} />)
    expect(container).toBeEmptyDOMElement()
    cleanup()
    const { container: blank } = render(<CoachAttribution name="   " />)
    expect(blank).toBeEmptyDOMElement()
  })

  it('suppresses the relationship line when relationship is empty', () => {
    render(<CoachAttribution variant="sender" name="Jordan Ellis" relationship="" />)
    expect(screen.queryByText('your coach')).toBeNull()
  })
})

describe('CoachMessage', () => {
  it('renders verbatim content in the serif voice with attribution', () => {
    render(<CoachMessage note="Focus on control on the way down." name="Jordan Ellis" />)
    const quote = screen.getByText('Focus on control on the way down.')
    expect(quote.tagName.toLowerCase()).toBe('blockquote')
    expect(quote).toHaveClass('font-voice')
    expect(screen.getByText('Jordan Ellis')).toBeInTheDocument()
  })

  it('wraps long content without truncation', () => {
    const long = 'Keep the tempo controlled and honest. '.repeat(12).trim()
    render(<CoachMessage note={long} name="Jordan Ellis" />)
    expect(screen.getByText(long)).toBeInTheDocument()
  })

  it('collapses completely when the note is absent (no empty quote chrome)', () => {
    const { container } = render(<CoachMessage note={null} name="Jordan Ellis" />)
    expect(container).toBeEmptyDOMElement()
    expect(container.querySelector('blockquote')).toBeNull()
  })

  it('renders the quote without attribution when no name is given', () => {
    render(<CoachMessage note="Great work today." />)
    expect(screen.getByText('Great work today.')).toBeInTheDocument()
    expect(screen.queryByText(/your coach/)).toBeNull()
  })
})
