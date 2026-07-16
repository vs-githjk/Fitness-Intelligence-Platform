// @ts-expect-error Vitest runs in Node; the browser bundle intentionally omits Node typings.
import { existsSync, readFileSync } from 'node:fs'
import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { Brand } from './Brand'

afterEach(cleanup)

describe('FitIntel 360 branding', () => {
  it('uses the approved full logo with intrinsic dimensions and accessible text', () => {
    render(<Brand />)
    expect(screen.getByAltText('FitIntel 360')).toHaveAttribute(
      'src',
      '/brand/fitintel360-logo.png',
    )
    expect(screen.getByAltText('FitIntel 360')).toHaveAttribute('width', '530')
    expect(screen.getByAltText('FitIntel 360')).toHaveAttribute('height', '570')
  })

  it('uses the legible Fi monogram in compact navigation', () => {
    render(<Brand compact />)
    expect(screen.getByAltText('FitIntel 360')).toHaveAttribute(
      'src',
      '/brand/fitintel360-mark.png',
    )
    expect(screen.getByAltText('FitIntel 360')).toHaveClass('size-10')
  })

  it('provides existing document icons, title, and manifest assets', () => {
    const html = readFileSync('index.html', 'utf8')
    expect(html).toContain('<title>FitIntel 360</title>')
    for (const asset of [
      'favicon.ico',
      'favicon-16.png',
      'favicon-32.png',
      'favicon-48.png',
      'apple-touch-icon.png',
      'icon-192.png',
      'icon-512.png',
      'brand/fitintel360-source.png',
      'brand/fitintel360-logo.png',
      'brand/fitintel360-mark.png',
    ]) {
      expect(existsSync(`public/${asset}`), `${asset} should exist`).toBe(true)
    }
    expect(html).toContain('href="/favicon-16.png"')
    expect(html).toContain('href="/favicon-32.png"')
    expect(html).toContain('href="/favicon-48.png"')
    expect(html).toContain('href="/apple-touch-icon.png"')

    const manifest = JSON.parse(
      readFileSync('public/site.webmanifest', 'utf8'),
    ) as { name: string; icons: Array<{ src: string; sizes: string }> }
    expect(manifest.name).toBe('FitIntel 360')
    expect(manifest.icons).toEqual(expect.arrayContaining([
      expect.objectContaining({ src: '/icon-192.png', sizes: '192x192' }),
      expect.objectContaining({ src: '/icon-512.png', sizes: '512x512' }),
    ]))
  })
})
