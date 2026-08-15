/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_APP_ENV?: 'local' | 'staging' | 'production'
  // Legal/company identity — set at deploy (e.g. Vercel env) so the public legal pages
  // can be activated without a code change. All optional; blank keeps the pending gate on.
  readonly VITE_LEGAL_ENTITY?: string
  readonly VITE_LEGAL_ADDRESS?: string
  readonly VITE_LEGAL_JURISDICTION?: string
  readonly VITE_LEGAL_EFFECTIVE_DATE?: string
  readonly VITE_PRIVACY_EMAIL?: string
  readonly VITE_SECURITY_EMAIL?: string
  readonly VITE_SUPPORT_EMAIL?: string
  readonly VITE_MIN_AGE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
