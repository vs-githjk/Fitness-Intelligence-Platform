export const appUrl = process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:5175'
export const apiUrl = process.env.PLAYWRIGHT_API_URL ?? 'http://localhost:8000/api/v1'
export const systemApiUrl = apiUrl.replace(/\/api\/v1\/?$/, '')
export const isHostedRun = process.env.PLAYWRIGHT_HOSTED === 'true'
  || !/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?/i.test(appUrl)
