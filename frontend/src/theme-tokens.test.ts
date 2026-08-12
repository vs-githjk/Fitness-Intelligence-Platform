import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import fonts from './fonts.ts?raw'

// Verifies the Iron Editorial token substrate (C2.0) at the source of truth: the CSS
// custom properties in index.css and the font imports in fonts.ts. These are
// foundation invariants (frozen anchor values, the ember semantic contract, the
// production-safe type roles), not visual/screenshot assertions. index.css is read
// from disk because vitest mocks `.css` imports to empty (even with ?raw); fonts.ts
// is a real module, so ?raw returns its source. The path is resolved from the vitest
// working directory (the frontend package root, where the suite always runs).
const css = readFileSync('src/index.css', 'utf8')

function tokenValues(name: string): string[] {
  const re = new RegExp(`--${name}:\\s*([^;]+);`, 'g')
  const out: string[] = []
  let match: RegExpExecArray | null
  while ((match = re.exec(css))) out.push(match[1].trim())
  return out
}

describe('Iron Editorial ember contract', () => {
  it('defines ember in both theme contexts with the frozen anchor values', () => {
    const ember = tokenValues('mb-ember')
    expect(ember).toContain('232 67 15') // #E8430F light
    expect(ember).toContain('255 90 40') // #FF5A28 dark
  })

  it('defines an ink/dark on-ember foreground (the default action contract)', () => {
    expect(tokenValues('mb-on-ember')).toContain('11 12 15')
  })

  it('never reuses ember as an error or caution (body-risk) value', () => {
    const ember = new Set(tokenValues('mb-ember'))
    const semantic = [...tokenValues('mb-error'), ...tokenValues('mb-caution')]
    for (const value of semantic) expect(ember.has(value)).toBe(false)
  })
})

describe('canonical frozen anchor palette', () => {
  const anchors: Record<string, string> = {
    'mb-ink-0': '11 12 15',
    'mb-ink-1': '20 22 27',
    'mb-ink-2': '28 31 38',
    'mb-bone': '236 234 226',
    'mb-bone-muted': '169 168 160',
    'mb-paper': '245 242 235',
    'mb-indigo-dark': '139 135 240',
  }
  for (const [token, value] of Object.entries(anchors)) {
    it(`--${token} is ${value}`, () => {
      expect(tokenValues(token)).toContain(value)
    })
  }
})

describe('light and dark token output both exist', () => {
  it('emits a dark override block and a light re-assert block', () => {
    expect(css).toContain(":root[data-theme='dark']")
    expect(css).toContain("[data-theme='light']")
  })
})

describe('production-safe typographic roles', () => {
  it('resolves each role to its intended production-safe stack', () => {
    expect(tokenValues('mb-font-display')[0]).toContain('Archivo Black')
    expect(tokenValues('mb-font-coach')[0]).toContain('Source Serif 4')
    expect(tokenValues('mb-font-numeral')[0]).toContain('IBM Plex Mono')
  })

  it('keeps coach voice and numeral roles distinct', () => {
    expect(tokenValues('mb-font-coach')[0]).not.toEqual(tokenValues('mb-font-numeral')[0])
  })

  it('bundles the intended OFL faces (build actually loads them)', () => {
    expect(fonts).toContain('@fontsource/archivo-black')
    expect(fonts).toContain('@fontsource/source-serif-4')
    expect(fonts).toContain('@fontsource/ibm-plex-mono')
  })
})
