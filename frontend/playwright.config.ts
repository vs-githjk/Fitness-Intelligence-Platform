import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  outputDir: '.playwright',
  timeout: 30_000,
  fullyParallel: false,
  reporter: 'line',
  use: {
    baseURL: 'http://localhost:5175',
    channel: 'chrome',
    headless: true,
    trace: 'retain-on-failure',
  },
})
