import { defineConfig } from '@playwright/test'
import { appUrl, isHostedRun } from './e2e/config'

export default defineConfig({
  testDir: './e2e',
  outputDir: '.playwright',
  timeout: 30_000,
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [['line'], ['junit', { outputFile: '.playwright/results.xml' }]] : 'line',
  testIgnore: isHostedRun ? [/daily\.spec\.ts/, /manual-docs\.spec\.ts/, /visual\.spec\.ts/] : /hosted-smoke\.spec\.ts/,
  use: {
    baseURL: appUrl,
    channel: process.env.PLAYWRIGHT_CHANNEL || (process.env.CI ? undefined : 'chrome'),
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
})
