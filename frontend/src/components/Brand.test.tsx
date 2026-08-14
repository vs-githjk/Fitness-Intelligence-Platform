// @ts-expect-error Vitest runs in Node; the browser bundle intentionally omits Node typings.
import { existsSync, readFileSync } from 'node:fs'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { Brand } from './Brand'

afterEach(cleanup)

describe('Vytal branding', () => {
  it('renders the typographic wordmark with accessible text (no raster logo)', () => {
    const { container } = render(<Brand />)
    expect(screen.getByLabelText('Vytal')).toBeInTheDocument()
    // The identity is typographic — the retired FitIntel raster logo is gone.
    expect(container.querySelector('img')).toBeNull()
  })

  it('renders the compact monogram tile in navigation', () => {
    render(<Brand compact />)
    expect(screen.getByLabelText('Vytal')).toHaveClass('size-10')
  })

  it('carries the Vytal title, icons, and manifest metadata', () => {
    const html = readFileSync('index.html', 'utf8')
    expect(html).toContain('<title>Vytal</title>')
    expect(html).not.toContain('FitIntel')
    for (const asset of [
      'favicon.ico',
      'favicon-16.png',
      'favicon-32.png',
      'favicon-48.png',
      'apple-touch-icon.png',
      'icon-192.png',
      'icon-512.png',
    ]) {
      expect(existsSync(`public/${asset}`), `${asset} should exist`).toBe(true)
    }
    expect(html).toContain('href="/favicon-16.png"')
    expect(html).toContain('href="/apple-touch-icon.png"')

    const manifest = JSON.parse(
      readFileSync('public/site.webmanifest', 'utf8'),
    ) as { name: string; icons: Array<{ src: string; sizes: string }> }
    expect(manifest.name).toBe('Vytal')
    expect(manifest.icons).toEqual(expect.arrayContaining([
      expect.objectContaining({ src: '/icon-192.png', sizes: '192x192' }),
      expect.objectContaining({ src: '/icon-512.png', sizes: '512x512' }),
    ]))
  })
})
