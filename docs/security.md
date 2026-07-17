# Security and compliance notes

The first milestone's trust boundary is the FastAPI service and PostgreSQL database. The browser is untrusted: role checks, assignment checks, input validation, and snapshot ownership are all enforced server-side.

Implemented controls include bcrypt password hashing, signed expiring JWT access tokens, strict request schemas/ranges, a restricted CORS allowlist, server-side coach assignment checks, UUID identifiers, foreign keys/uniqueness constraints, UTC audit-friendly timestamps, and environment-based secrets. Normal application code does not log access tokens or health request bodies.

## Controlled public demo boundary

Public demo access is an authentication convenience for explicitly seeded synthetic users, not an authorization bypass. `DEMO_MODE_ENABLED` defaults to false, must be deliberately enabled in local or staging environments, and is rejected by production configuration validation. The backend resolves configured users that are both active and marked `is_demo`, then issues an ordinary short-lived role-bearing JWT. No password or hardcoded token is sent to the frontend.

Demo coach and trainee requests continue through the normal role and active-assignment authorization paths. A shared backend guard rejects persistent demo mutations with `403 demo_read_only`, including profile, onboarding, daily check-in, coach-invitation, programming, assignment, and every workout-execution change. A centralized route inventory test prevents a workout mutation from being added without demo coverage. Frontend disabled controls and banners are explanatory only; they are not the security boundary.

Workout execution reads and writes use trainee-owned queries, so unrelated session and set IDs are not discoverable through direct identifier changes. Start locks the scheduled workout and a unique constraint permits only one session per schedule row. Every later mutation requires the current session revision; a stale write returns `409` without overwriting newer data. Terminal sessions and their prescription snapshots are immutable through the API. Coach-only template notes are excluded from trainee execution payloads, while bounded session events provide an append-only operational history.

Workout safety content is immutable and coach acknowledgement/resolution history is append-only.
Trainee ownership and active coach-assignment joins prevent cross-account discovery; coach review
notes are absent from trainee responses. Critical report creation atomically persists the report,
terminal session state, partial schedule state, and safety events. Safety mutations are part of the
centralized demo inventory. Readiness captures a unique immutable copy of an eligible persisted
Daily Score snapshot, or explicit unavailability, and cannot mutate Daily Intelligence or workout
content.

Normal web startup never provisions demo records. The explicit seed command is separately gated by `SEED_DEMO_DATA=true`; production rejects seeding. The public demo is synthetic-only and is not authorization to collect real personal or health data.

Daily check-ins add self-reported recovery, activity, nutrition-compliance, feeling, and an optional 500-character note. Notes and raw check-in values are not intentionally written to normal application logs. Trainees can create or edit only their current timezone-local date; coach endpoints are read-only and require an active assignment. List endpoints are date-bounded, while detailed calculation payloads remain limited to the authorized trainee or assigned coach. Local dates are stored explicitly so historical records are not reinterpreted after timezone or daylight-saving changes.

JWTs are stored in browser local storage for this local milestone. A production hardening pass should prefer an appropriately protected secure, HttpOnly, SameSite cookie or a rigorously designed token/refresh flow, add CSRF controls as applicable, revocation and rotation, rate limiting, breached-password controls, MFA for coaches, account recovery, and security event logging.

Collected onboarding data is sensitive. Production readiness also requires encryption in transit and verified at rest, managed key/secrets systems, audit logs, tenant and support-access controls, retention/deletion/export workflows, consent, backup and incident-response procedures, dependency/container scanning, monitoring, penetration testing, and vendor/legal review.

## Registration and invitation controls

Coach registration is invitation-only and requires `COACH_REGISTRATION_CODE`, which is read only by the backend and compared using a timing-safe comparison. Missing configuration disables the route. Do not expose this value through `VITE_*`, Vercel, logs, screenshots, or support messages.

Trainee invitations use cryptographically random tokens. The database stores only SHA-256 hashes; the raw token is returned once at creation. Invitations are coach-owned, single-use, expiring, revocable, and may be restricted to one email. PostgreSQL row locking serializes redemption, and user/profile/assignment/invitation consumption commit transactionally. Invitation query parameters are loaded into form state and removed from the visible URL; they must not be added to analytics or persisted in browser storage.

Current limitations remain significant: no application rate limiting, email verification, MFA, audit trail, invitation email delivery, or compromised-secret response workflow exists. These controls support synthetic staging evaluation and do not by themselves make the application ready for real health data.

This repository does not claim HIPAA, GDPR, or other legal compliance. HIPAA readiness additionally depends on policies, workforce training, risk analysis, BAAs, vendor controls, administrative/physical safeguards, and operating practice. Applicability must be determined by qualified counsel and compliance professionals.

## Workout Intelligence analytics authorization

The Phase 7B analytics endpoints are all read-only GETs. Trainees can read only their own analytics; coaches can read only trainees with an active `CoachTraineeAssignment`. An inactive assignment is denied, and cross-coach session discovery returns `404` (indistinguishable from a missing object) rather than confirming existence. Every protected React Query key includes the account identity scope, so login, logout, and demo transitions never render another identity's analytics, and an in-flight response cannot repopulate a new identity's cache. Demo accounts may inspect analytics; all mutations remain blocked, and Phase 7B adds no new mutation route.
