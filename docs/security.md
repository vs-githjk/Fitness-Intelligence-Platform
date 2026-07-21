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

## Real test accounts and test-data handling

Controlled real-user testing now runs alongside development with one real coach
test account and four real trainee test accounts. These are private test
identities, distinct from the public demo accounts. Operational guidance is in
[testing/real-user-testing.md](testing/real-user-testing.md); the privacy rules
below are binding.

- **Demo accounts are public synthetic accounts** (`is_demo`, read-only). **Real
  test accounts are private test identities** that can perform normal mutations.
  Do not conflate them.
- **Use synthetic data whenever possible.** Collect only the information a specific
  test requires; do not enter unnecessary sensitive health information.
- **No secrets in screenshots or issues** — no passwords, tokens, invitation codes,
  or the coach registration code. Redact private data before sharing any
  screenshot or log.
- **No test-user passwords in documentation.** Credentials are never committed.
- **Do not share production/staging database exports with coding agents** or paste
  them into issues.
- **Role and assignment isolation apply to test users too:** a trainee sees only
  their own data; a coach sees only trainees with an active assignment. Cross-
  account visibility is a P0.
- **Deletion and offboarding:** self-service export/deletion is a hardening-phase
  item and does not yet exist. Offboarding disables sign-in; deletion is a manual
  maintainer operation until a supported workflow ships. Record deletion requests
  until then.
- **Backups may contain test-entered content** and must be treated as sensitive.
- **Logs avoid sensitive body content** (self-reported notes and raw health values
  are not intentionally logged); keep it that way when adding endpoints.

These practices support controlled testing with synthetic-first data. They do not,
by themselves, make the application ready for real health data, and this
repository still makes no HIPAA/GDPR/SOC 2/medical-device compliance claim.

## Workout Intelligence analytics authorization

The Phase 7B analytics endpoints are all read-only GETs. Trainees can read only their own analytics; coaches can read only trainees with an active `CoachTraineeAssignment`. An inactive assignment is denied, and cross-coach session discovery returns `404` (indistinguishable from a missing object) rather than confirming existence. Every protected React Query key includes the account identity scope, so login, logout, and demo transitions never render another identity's analytics, and an in-flight response cannot repopulate a new identity's cache. Demo accounts may inspect analytics; all mutations remain blocked. The one Phase 7C mutation — the explicit trainee whole-workout skip (`POST /api/v1/trainee/workouts/{id}/skip`) — enforces trainee ownership, rejects the coach role, rejects non-scheduled/started statuses, calls backend demo protection (403 for demo), and is listed in the central workout-execution demo-mutation inventory.

## Media handling

The Milestone 4 media subsystem is infrastructure only; no media feature is exposed to users yet. Its security posture:

- **Authorization.** Uploads, metadata reads, content delivery, and deletes are authenticated and **owner-scoped**. A user may only access their own assets; cross-account access returns `404` (existence is never confirmed). No role — including coach — has broad access to another user's media. Mutations (`POST /api/v1/media`, `DELETE /api/v1/media/{id}`) call backend demo protection (403 `demo_read_only`) and are listed in the central `MEDIA_DEMO_MUTATIONS` inventory, enforced by an OpenAPI-derived completeness test.
- **Upload validation.** A narrow raster allowlist (`image/jpeg`, `image/png`, `image/webp`, `image/gif`) is enforced by both declared MIME and **magic-byte signature**; the browser-supplied Content-Type is not trusted alone. SVG and executable/archive/HTML/scriptable formats are rejected. Empty files are rejected and uploads are size-capped (`MEDIA_MAX_BYTES`, default 5 MiB) by streaming rather than buffering unbounded input. Every upload gets a SHA-256 checksum; original filenames are sanitized.
- **Storage-key secrecy and path safety.** Storage keys are opaque, server-generated (`{purpose}/{owner}/{uuid}.{ext}`) and **never** exposed in API responses. The local provider confines every path to its configured root and rejects traversal (`..`, absolute paths, backslashes); writes are atomic (temp file plus rename).
- **Delivery.** Content is streamed through the authorized `GET /api/v1/media/{id}/content` route after an ownership check, with `Content-Disposition: inline`, `X-Content-Type-Options: nosniff`, and `Cache-Control: private, no-store`. The storage directory is never a public static route and there are no guessable permanent URLs.
- **Lifecycle.** User-facing deletes are **soft** (`soft_deleted`); bytes are removed only by a service-level **purge**. Soft-deleted and purged assets are hidden from reads.
- **Known limitations (documented, not overstated).** There is **no malware scanning** and **no EXIF stripping** in this phase — a passing MIME/signature check does not make a file "safe". Local storage is ephemeral: production startup rejects local media; staging may use it because it is synthetic and no media feature is user-exposed. A durable object store must be configured before any media-consuming feature ships to production. See ADR-0013/0014.
