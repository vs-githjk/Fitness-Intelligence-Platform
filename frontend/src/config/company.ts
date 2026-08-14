// Company / legal identity used by the public legal pages. These are the ONLY founder/counsel
// inputs the legal surfaces need. They are intentionally empty until provided — the pages render
// with a clear "pending final details" notice while any required value is blank, and must not be
// presented as final to the public until COMPANY_LEGAL_COMPLETE is true and counsel has reviewed
// the wording. Do not invent an entity name, address, jurisdiction, domain, or contact.

export const COMPANY = {
  product: 'Vytal',
  legalEntity: '', // [FOUNDER] registered company name
  address: '', // [FOUNDER] mailing address for legal + privacy contact
  jurisdiction: '', // [FOUNDER/COUNSEL] governing law / venue
  privacyEmail: '', // [FOUNDER] working privacy inbox
  securityEmail: '', // [FOUNDER] working security inbox
  supportEmail: '', // [FOUNDER] working support inbox
  effectiveDate: '', // [FOUNDER/COUNSEL] publication date
  minAge: 13, // assumed; [FOUNDER/COUNSEL] confirm, and decide whether under-18 trainees are supported
} as const

// True only when every value required to present the policies as final is filled in.
export const COMPANY_LEGAL_COMPLETE = Boolean(
  COMPANY.legalEntity && COMPANY.address && COMPANY.jurisdiction &&
  COMPANY.privacyEmail && COMPANY.securityEmail && COMPANY.effectiveDate,
)

// Render a value, or a neutral inline fallback while it is pending (never shows "[FOUNDER]").
export function orPending(value: string, label: string): string {
  return value.trim() ? value : `— ${label} pending —`
}
