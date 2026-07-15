import { appConfig } from '../env'

export function EnvironmentBanner({ inAppShell = false }: { inAppShell?: boolean }) {
  if (!appConfig.isStaging) return null
  return <div role="status" aria-label="Staging environment" className="relative z-40 border-b border-[rgb(var(--status-attention-border))] bg-[rgb(var(--status-attention-bg))] px-4 py-2 text-center text-xs font-semibold text-attention"><div className={inAppShell ? 'lg:pl-64' : ''}>Staging environment · Use synthetic test data only · Data may be reset · Not for medical care <span className="whitespace-nowrap">(v{appConfig.appVersion})</span></div></div>
}
