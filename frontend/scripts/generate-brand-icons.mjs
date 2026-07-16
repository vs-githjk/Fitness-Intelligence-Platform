import { chromium } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const svg = await readFile(path.join(root, 'public/brand/mark.svg'))
const source = `data:image/svg+xml;base64,${svg.toString('base64')}`
const outputs = [
  ['public/icon-512.png', 512],
  ['public/icon-192.png', 192],
  ['public/apple-touch-icon.png', 180],
  ['public/favicon-48.png', 48],
]

const browser = await chromium.launch()
try {
  for (const [filename, size] of outputs) {
    const page = await browser.newPage({ viewport: { width: size, height: size } })
    await page.setContent(`<img src="${source}" alt="" style="display:block;width:${size}px;height:${size}px">`)
    await page.locator('img').screenshot({ path: path.join(root, filename) })
    await page.close()
  }
} finally {
  await browser.close()
}
