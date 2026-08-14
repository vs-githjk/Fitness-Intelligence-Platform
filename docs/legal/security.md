# Security & Trust

**DRAFT — describes only controls that are implemented and verifiable. Last reviewed: `[EFFECTIVE_DATE]`.**

We build Vytal so coaches and trainees can trust it with their training data. This page
describes controls that are **actually in place today**. We deliberately do **not** claim
certifications or protections we have not implemented and verified.

## What we do

- **Encryption in transit.** Vytal is served over HTTPS/TLS in staging and production. In
  production, HTTP Strict Transport Security (HSTS) is enforced.
- **Password protection.** Passwords are stored only as salted bcrypt hashes — never in
  plain text.
- **Authenticated, role-scoped access.** Every request is authenticated (signed, expiring
  tokens) and authorized on the server by role (coach / trainee). Requests for another
  account's data return "not found" — one account cannot enumerate or read another's content.
- **Tenant boundaries.** A coach's private exercises and programming are visible only to that
  coach; a trainee can read only the specific, narrow fields required to perform assigned
  training.
- **Hardened response headers.** Responses set `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, a strict `Content-Security-Policy`, and a `no-referrer` policy.
- **Abuse throttling.** Authentication, registration, and import endpoints are rate-limited in
  our deployed environments to blunt brute-force and accidental floods.
- **Uploaded media is access-controlled.** Media is served only through an authenticated
  endpoint (never a public static path), with type and size limits enforced on upload.
- **Configuration safety.** Deployed environments fail to start if required security
  configuration (database TLS, non-default secrets, explicit allowed origins, docs disabled)
  is missing — misconfiguration cannot silently ship.
- **Auditability.** Each request is assigned an ID and recorded in structured logs for
  incident investigation.
- **Separation of demo data.** The public demo is read-only and is disabled entirely in
  production; demo accounts are never seeded into production.

## Reporting a vulnerability

If you believe you have found a security issue, please email `[SECURITY_EMAIL]` with details
and steps to reproduce. Please give us a reasonable opportunity to remediate before any public
disclosure. We do not currently operate a paid bug-bounty program.

## Your data rights

You can request access to, export of, correction of, or deletion of your data, and (for
trainees) withdrawal of consent to share health data with your coach. See the
[Privacy Policy](privacy-policy.md) for how to make a request and our response commitment.

## What we do not claim

To keep this page honest, Vytal does **not** currently claim: HIPAA compliance, SOC 2, ISO
27001, third-party penetration testing, 24/7 monitoring, or malware scanning of uploads. When
any of these becomes true and verifiable, it will be added here — not before.

## Known limitations (being addressed)

- Rate limiting is currently per-process; a shared store (for a strict global limit across
  multiple instances) is a planned improvement.
- Encryption-at-rest depends on our managed database/storage providers and is being verified;
  it is not asserted here until confirmed.
