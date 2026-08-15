// Company / legal identity used by the public legal pages. These are the ONLY founder/counsel
// inputs the legal surfaces need, and they are DEPLOY-TIME CONFIGURATION (read from VITE_* env),
// so the founder can activate the legal pages at cutover without a code change. They are
// intentionally empty until provided — the pages render with a clear "pending final details"
// notice while any required value is blank, and must not be presented as final to the public
// until COMPANY_LEGAL_COMPLETE is true and counsel has reviewed the wording. Do not invent an
// entity name, address, jurisdiction, domain, or contact.

const env = import.meta.env
function val(value: string | undefined): string {
  return (value ?? '').trim()
}

export const COMPANY = {
  product: 'Vytal',
  legalEntity: val(env.VITE_LEGAL_ENTITY), // registered operator/company name
  address: val(env.VITE_LEGAL_ADDRESS), // mailing address for legal + privacy contact
  jurisdiction: val(env.VITE_LEGAL_JURISDICTION), // governing law / venue (counsel decision)
  privacyEmail: val(env.VITE_PRIVACY_EMAIL), // working privacy inbox
  securityEmail: val(env.VITE_SECURITY_EMAIL), // working security inbox
  supportEmail: val(env.VITE_SUPPORT_EMAIL), // working support inbox
  effectiveDate: val(env.VITE_LEGAL_EFFECTIVE_DATE), // publication date (counsel decision)
  // Minimum age. Default 18 — under India's DPDP Act a "child" is under 18 and needs verifiable
  // parental consent, which Vytal has no machinery for, so the safe default is adults-only.
  // Overridable via VITE_MIN_AGE only once the corresponding consent machinery/legal basis exists.
  minAge: Number(val(env.VITE_MIN_AGE)) || 18,
} as const

// True only when every value required to present the policies as final is filled in.
export const COMPANY_LEGAL_COMPLETE = Boolean(
  COMPANY.legalEntity && COMPANY.address && COMPANY.jurisdiction &&
  COMPANY.privacyEmail && COMPANY.securityEmail && COMPANY.effectiveDate,
)

// Render a value, or a neutral inline fallback while it is pending (never shows a placeholder).
export function orPending(value: string, label: string): string {
  return value.trim() ? value : `— ${label} pending —`
}
