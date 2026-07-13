# Security and compliance notes

The first milestone's trust boundary is the FastAPI service and PostgreSQL database. The browser is untrusted: role checks, assignment checks, input validation, and snapshot ownership are all enforced server-side.

Implemented controls include bcrypt password hashing, signed expiring JWT access tokens, strict request schemas/ranges, a restricted CORS allowlist, server-side coach assignment checks, UUID identifiers, foreign keys/uniqueness constraints, UTC audit-friendly timestamps, and environment-based secrets. Normal application code does not log access tokens or health request bodies.

JWTs are stored in browser local storage for this local milestone. A production hardening pass should prefer an appropriately protected secure, HttpOnly, SameSite cookie or a rigorously designed token/refresh flow, add CSRF controls as applicable, revocation and rotation, rate limiting, breached-password controls, MFA for coaches, account recovery, and security event logging.

Collected onboarding data is sensitive. Production readiness also requires encryption in transit and verified at rest, managed key/secrets systems, audit logs, tenant and support-access controls, retention/deletion/export workflows, consent, backup and incident-response procedures, dependency/container scanning, monitoring, penetration testing, and vendor/legal review.

This repository does not claim HIPAA, GDPR, or other legal compliance. HIPAA readiness additionally depends on policies, workforce training, risk analysis, BAAs, vendor controls, administrative/physical safeguards, and operating practice. Applicability must be determined by qualified counsel and compliance professionals.
