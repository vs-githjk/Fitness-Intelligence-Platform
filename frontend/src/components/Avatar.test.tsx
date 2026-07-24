import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { initialsFrom } from '../avatar'
import { Avatar } from './Avatar'

afterEach(() => cleanup())

describe('initialsFrom', () => {
  it('takes first and last initials', () => expect(initialsFrom('Maya Coach')).toBe('MC'))
  it('handles a single name', () => expect(initialsFrom('Cher')).toBe('CH'))
  it('collapses extra whitespace', () => expect(initialsFrom('  Ana   Beth  Cruz ')).toBe('AC'))
  it('falls back for empty input', () => expect(initialsFrom('')).toBe('?'))
  it('falls back for nullish input', () => expect(initialsFrom(null)).toBe('?'))
})

describe('Avatar', () => {
  it('renders initials with no providers when there is no photo URL', () => {
    // Deliberately rendered bare: the initials path must not require query/auth context.
    render(<Avatar name="Tara Trainee" />)
    expect(screen.getByText('TT')).toBeInTheDocument()
    expect(screen.queryByRole('img')).toBeNull()
  })
})
