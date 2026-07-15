export type AppEnvironment = 'local' | 'staging' | 'production'

interface ClientEnvironment {
  readonly DEV?: boolean
  readonly VITE_API_URL?: string
  readonly VITE_APP_ENV?: string
  readonly VITE_APP_VERSION?: string
}

export interface AppConfig {
  apiUrl: string
  appEnv: AppEnvironment
  appVersion: string
  isLocal: boolean
  isStaging: boolean
}

const LOCAL_API_URL = 'http://localhost:8000/api/v1'
const APP_ENVIRONMENTS = new Set<AppEnvironment>(['local', 'staging', 'production'])

function isLocalHostname(hostname: string): boolean {
  const normalized = hostname.toLowerCase().replace(/^\[|\]$/g, '')
  return normalized === 'localhost' || normalized === '0.0.0.0' || normalized === '::1' || normalized.startsWith('127.')
}

export function createAppConfig(environment: ClientEnvironment): AppConfig {
  const appEnvValue = environment.VITE_APP_ENV?.trim() || 'local'
  if (!APP_ENVIRONMENTS.has(appEnvValue as AppEnvironment)) {
    throw new Error('VITE_APP_ENV must be one of: local, staging, production')
  }
  const appEnv = appEnvValue as AppEnvironment
  const configuredApiUrl = environment.VITE_API_URL?.trim()
  if (!configuredApiUrl && appEnv !== 'local') {
    throw new Error(`VITE_API_URL is required when VITE_APP_ENV=${appEnv}`)
  }

  const apiUrlValue = configuredApiUrl || LOCAL_API_URL
  let parsedApiUrl: URL
  try {
    parsedApiUrl = new URL(apiUrlValue)
  } catch {
    throw new Error('VITE_API_URL must be an absolute URL')
  }
  if (!['http:', 'https:'].includes(parsedApiUrl.protocol)) {
    throw new Error('VITE_API_URL must use HTTP or HTTPS')
  }
  if (appEnv !== 'local' && (parsedApiUrl.protocol !== 'https:' || isLocalHostname(parsedApiUrl.hostname))) {
    throw new Error(`VITE_API_URL must be a non-local HTTPS URL when VITE_APP_ENV=${appEnv}`)
  }

  return {
    apiUrl: apiUrlValue.replace(/\/+$/, ''),
    appEnv,
    appVersion: environment.VITE_APP_VERSION?.trim() || '0.4.2',
    isLocal: appEnv === 'local',
    isStaging: appEnv === 'staging',
  }
}

export const appConfig = createAppConfig(import.meta.env)
