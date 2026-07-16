# Product and platform roadmap

This roadmap communicates sequence, dependencies, and gates. It is not a delivery-date commitment and does not present future modules as working features. Milestone 2C adds deployment, testing, private-beta, and production-readiness documentation only; it does not implement Milestone 3.

Current product behavior is documented in the [Product guide](product-guide.md). Deployment and release gates are in [Synthetic staging deployment](deployment/staging.md), [Production readiness](deployment/production-readiness.md), and [Synthetic private beta plan](testing/private-beta-plan.md).

## Principles

- Keep scoring deterministic, explainable, versioned, and auditable.
- Never fabricate missing health, activity, nutrition, or trend data.
- Preserve baseline Health Index and daily intelligence as distinct concepts.
- Treat product alerts as coaching/safety guidance, not diagnosis or medical clearance.
- Add backend authorization and data lifecycle controls before exposing new UI actions.
- Ship no module merely as empty navigation or mock production data.
- Require security, privacy, operational, and accessibility gates proportional to the data/action risk.

## Current delivered scope

The repository currently implements:

- Email/password authentication and coach/trainee roles.
- Invite-based trainee registration and active assignment to a coach.
- Persistent multi-step onboarding and immutable submitted baseline.
- Versioned deterministic Health Index components, recommendations, and risk notices.
- Atomic current-local-date daily check-ins and deterministic daily intelligence.
- Bounded 7-/30-day persisted trends with explicit missing-date gaps.
- Read-only coach roster and assigned-trainee longitudinal review.
- Responsive, accessible-oriented role experiences and local documentation.
- PostgreSQL/Alembic persistence, Docker Compose, and automated backend/frontend tests.

Known current limits include local-storage JWTs, local/demo enrollment, no coach mutations, no roster search/filter/sort or dedicated attention queue, limited raw daily fields in coach view, and no alert-resolution UI.

## Milestone 2C — deployment and synthetic beta readiness

### Documentation deliverables

- Staging topology and ordered deployment runbook.
- Production-readiness gates and blocker register.
- Synthetic-only private-beta cohort, support, incident, feedback, and data plan.
- Sequenced roadmap with explicit dependencies and security gates.

### Platform readiness implemented in the repository

- Migration, explicit synthetic seed, and web startup are separate; production rejects seeding.
- Backend startup honors the provider port, with liveness and database-readiness probes.
- Vercel single-page-app routing and a Render service/database Blueprint are defined.
- CI covers backend, clean PostgreSQL migrations, frontend checks, and Compose builds.
- Application/API/package metadata is aligned to `0.4.2`; backend health and OpenAPI metadata use the centralized `app.__version__` source.
- Demo credentials and invite guidance are gated by client environment.
- Role-aware registration, backend-protected coach bootstrap, and coach-specific single-use trainee invitations.
- Requests carry `X-Request-ID` correlation and sanitized structured operational logs.

## Milestone 2E — public demo experience

- Separate **Explore Demo** entry with coach and trainee role choice; normal login has no role selector.
- Backend-controlled, short-lived demo sessions for explicitly configured synthetic identities.
- Seven deterministic coach-roster scenarios and a 21-local-date trainee history with intentional missing dates.
- Persistent `is_demo` identity marker and backend-enforced read-only mutation guard.
- Explicit environment gate that defaults off and is rejected in production.
- Normal startup remains seed-free; deterministic demo provisioning is an approved one-off operation.
- Normal protected coach registration and coach-specific trainee invitations remain unchanged.

### Operational work required to complete staging

- Approve provider accounts, plans, region, repository access, secrets, and exact domains.
- Run the Blueprint pre-deploy migration and approved one-off synthetic staging seed.
- Verify the final Vercel/Render CORS and trusted-host configuration.
- Run and record the hosted smoke suite, monitoring checks, rollback, backup, and restore exercise.
- Keep the initial live-metadata Alembic revision as known technical debt; do not rewrite applied history. Add an append-only reconciliation revision only if a verified schema difference is found.

### Exit gate

Milestone 2C exits when a selected release is verified locally, an approved synthetic staging deployment completes, the staging smoke suite passes, backup/restore and rollback are exercised, and the synthetic private-beta entry criteria are signed. Documentation alone does not satisfy this operational gate.

## Hardening phase — before any real-data beta

This phase takes priority over new product modules if real personal or health data is proposed.

### Identity and access

- Replace local-storage-only session design with a reviewed protected session/token architecture.
- Add refresh/revocation, key rotation, session/device controls, recovery, email verification, and coach MFA.
- Add rate limits, email verification, MFA, administrative enrollment controls, invite audit events, and assignment transfer/removal workflows around the coach-specific invitation model.
- Add rate limiting, abuse protection, and security-event monitoring.

### Privacy and lifecycle

- Consent, privacy notice acceptance, data classification, and acceptable-use records.
- Authenticated export, deletion, retention, and support-access workflows.
- Immutable audit events for sensitive reads and changes.
- Vendor/legal review and jurisdiction-specific requirements.

### Reliability and delivery

- Static append-only migrations tested on PostgreSQL upgrade paths.
- Readiness checks, structured logs, correlation IDs, metrics, and alerting.
- Managed backup/PITR plus recurring restore tests.
- CI security/dependency/container scanning, load/resilience testing, and penetration testing.
- Incident response, on-call ownership, release/rollback automation with manual production approval.

### Gate

No real-data beta begins until the applicable [production-readiness gates](deployment/production-readiness.md#go-live-gates) have named owners and approval evidence.

## Milestone 3 — Workout Intelligence foundations in progress

The repository now includes the owned, immutable exercise library, coach workout-template
authoring workspace, and versioned multi-week program builder. System/private ownership,
deterministic seed content, exact version pinning, complete-graph draft replacement, conflict
detection, coach-authored deload context, and demo read-only enforcement are implemented.

Assignments, scheduling, trainee execution, set logging, safety reports, load and adherence
analytics, and readiness context remain future slices. The items below are candidates,
not enabled routes or commitments unless explicitly marked implemented.

### Coach workflow operations

Potential outcomes:

- Roster search, filter, sort, and pagination.
- A real attention queue with defined membership and timestamps.
- Alert acknowledgement/resolution with state transitions and audit history.
- Coach notes with explicit visibility and retention rules.

Dependencies and gates:

- Server-side query/filter contracts and scale limits.
- Object authorization for every action.
- Optimistic-concurrency/idempotency behavior.
- Audit log, actor identity, timestamps, reversal/correction rules.
- Notification semantics before any action implies a message was sent.
- Accessibility for tables, filters, dialogs, and mobile transformations.

### Workout programming

Implemented foundation:

- Coach-created, versioned exercises and reusable workout templates.
- Coach-created 1–12 week programs with exact template-version pins, ordered weekday slots,
  required/optional context, explicit rest days, coach-authored deloads, and trainee preview.
- Trainee-facing template and program previews without assignment or execution.

Potential next outcomes:

- Program and ad-hoc workout assignment to trainees.
- Scheduled sessions, completion, and coaching review.

Dependencies and gates:

- Exercise/content model, versioning, ownership, and assignment state.
- Clear distinction between coaching plan and medical prescription.
- Injury/symptom safety language and escalation review.
- Edit history, cancellation, timezone scheduling, and authorization.
- No automatic readiness-based workout change without an approved deterministic rule and explicit user communication.

### Nutrition planning

Potential outcomes:

- Coach-entered targets or plan structures and trainee compliance context.

Dependencies and gates:

- Professional-scope and jurisdiction review.
- Provenance for targets; no fabricated calorie/macronutrient prescription.
- Allergies/preferences/sensitive-data minimization decisions.
- Versioned plans, audit history, consent, and export/deletion handling.
- Safety review before generating any action from intake data.

### Messaging and notifications

Potential outcomes:

- Coach-trainee messaging and selected operational reminders.

Dependencies and gates:

- Delivery provider/vendor review and data-processing terms.
- Message authorization, retention/deletion/export, abuse/reporting, blocking, moderation, and audit rules.
- Notification preferences, consent, quiet hours, timezone, retry/deduplication, and delivery status.
- No sensitive health details in lock-screen, email subject, or push preview by default.
- Emergency-use disclaimer; messaging must not imply monitored urgent care.

### Wearable and external data integrations

Potential outcomes:

- User-authorized imports from selected providers.

Dependencies and gates:

- OAuth/token security, revocation, provider/vendor review, data licenses, and consent.
- Source provenance, units, timezone, deduplication, backfill, and deletion propagation.
- Clear conflict handling between manual and imported values.
- Scoring-version change and validation before imported data affects a score.
- Explicit unavailable/stale states; no fabricated continuity.

### Exports and reporting

Potential outcomes:

- User-requested personal export and limited coach-authorized reports.

Dependencies and gates:

- Authorization, purpose limitation, redaction, watermarking, expiry, audit, and secure delivery.
- Retention/deletion/legal review.
- Accessibility and exact formula/version context.
- No clinical-report label or diagnostic interpretation without separate approval.

### AI-assisted narration

Potential outcomes:

- Optional plain-language narration of already structured deterministic results.

Dependencies and gates:

- AI may not invent values, alter scores/rules, diagnose, prescribe, or override safety text.
- Model/vendor privacy and data-use review, minimization, consent, audit, evaluation, and fallback.
- Grounding exclusively in authorized structured data with source/version display.
- Red-team testing for medical claims, prompt injection, leakage, bias, and unsafe reassurance.
- Human review for coach-facing content where required.

## Production and scale phase

This phase begins only after the product scope and real-data authorization are approved.

- Separate production provider accounts/resources, domains, secrets, databases, backups, and access groups.
- Formal SLOs, capacity planning, database/query optimization, incident management, and disaster recovery.
- Privacy/security/compliance operating program with recurring reviews.
- Controlled releases, feature flags, cohort rollout, data migrations, rollback, and post-deploy monitoring.
- Customer support, status communication, service terms, privacy notice, and data-rights operations.

Passing a synthetic beta or deploying to hosted infrastructure does not satisfy this phase.

## Deferred until explicitly approved

- Native mobile applications or PWA packaging.
- Automated clinical decisions or medical diagnosis.
- Injury prediction, treatment recommendations, or medical clearance.
- Autonomous workout/nutrition adjustment from readiness.
- Marketplace, billing, insurance, employer, or clinical-system integrations.
- Any use of real health data before security/privacy/legal gates.

## Roadmap governance

For each proposed milestone, record:

- User problem and non-goals.
- Data classification and new trust boundaries.
- API/domain model and authorization changes.
- Scoring/risk version impact.
- Accessibility/responsive plan.
- Security, privacy, safety, legal, and vendor dependencies.
- Migration, seed/test-fixture, observability, backup, rollback, and support changes.
- Entry/exit criteria, owner, reviewer, evidence, and release decision.

Update this roadmap only when scope or ordering is approved. Do not mark a candidate delivered until working code, authorization, tests, documentation, and operational evidence exist.
