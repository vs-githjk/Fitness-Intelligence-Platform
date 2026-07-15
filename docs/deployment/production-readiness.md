# Production readiness

This document is a release gate, not a claim that Fitness Intelligence is production-ready. The current product is suitable for local development and, after the staging prerequisites are met, a synthetic-only staging beta. It must not be promoted for real health data merely because a Vercel, Render, or PostgreSQL deployment is technically reachable.

See [Synthetic staging deployment](staging.md), [Private beta plan](../testing/private-beta-plan.md), [Roadmap](../roadmap.md), and [Security and compliance notes](../security.md).

## Production topology

The intended topology remains:

```text
Production browser
    │ HTTPS
    ▼
Separate Vercel production project and domain
    │ HTTPS JSON API
    ▼
Separate Render production web service
    │ private connection
    ▼
Separate managed PostgreSQL production database
```

Production must not reuse staging projects, databases, secrets, domains, demo accounts, invite codes, backups, or provider access groups.

## Current production blockers

### Identity and session security

- JWTs are stored in browser local storage. Implement an appropriately protected secure, HttpOnly, SameSite cookie or a rigorously reviewed token/refresh design, with CSRF controls where applicable.
- No refresh, revocation, device/session management, or signing-key rotation workflow exists.
- No coach MFA, account recovery, email verification, or breached-password control exists.
- No application rate limiting or abuse protection exists.
- Coach-specific hashed invitations now replace shared-code/oldest-coach enrollment, but production still needs rate limiting, verified administrative coach enrollment, invitation audit events, abuse monitoring, and assignment lifecycle controls.
- Public demo mode must remain disabled in production, and no synthetic seed identities may be provisioned there.

### Privacy, governance, and compliance

- No consent record, privacy notice acceptance, acceptable-use record, or lawful-basis workflow exists.
- No authenticated data export, retention, deletion, or legal-hold workflow exists.
- No immutable audit trail records sensitive reads, changes, administrative access, or security events.
- Tenant/support access controls and staff operating procedures are not defined.
- No vendor/compliance review, BAA decision, data-processing agreement, or jurisdictional assessment is complete.
- Encryption in transit and at rest must be verified operationally, not assumed from provider defaults.

The repository does not claim HIPAA, GDPR, or other legal compliance. Applicability and required safeguards must be determined by qualified legal and compliance professionals.

### Reliability and operations

- Liveness and database-readiness endpoints exist, but external monitoring, alert routing, SLOs, and failure exercises are not configured in the repository.
- Migration, explicit synthetic staging seed, and web startup are separated; production always rejects the seed command.
- The first Alembic migration depends on live model metadata instead of a static historical schema.
- Unit/API fixtures use SQLite, while CI and release validation exercise a clean PostgreSQL migration; upgrade-from-previous-release and restore drills remain required.
- No documented service-level objectives, on-call rota, alert thresholds, status page, or incident commander process exists.
- Basic JSON request logs and `X-Request-ID` correlation exist, but security/audit event schemas, centralized retention/access rules, dashboards, and alerting do not.
- No verified managed backup/restore exercise is recorded.
- No load, resilience, dependency, container, dynamic security, or penetration test gate exists.

### Release integrity

- Package and API versions must align with the Git tag/release.
- CI exists, but required-check enforcement, protected deployment environments, changelog policy, provenance, and signed release approval remain operational gates.
- Frontend direct-route rewriting and backend provider-port behavior must be verified.
- Dependencies and runtime images need a repeatable update, lock, scanning, and provenance policy.

## Required production environment separation

| Control | Staging | Production requirement |
|---|---|---|
| Data | Synthetic only | Approved real-data classification and handling policy |
| Frontend | Staging Vercel project | Separate production project/domain/team access |
| API | Staging Render service | Separate production service and deployment approvals |
| Database | Staging PostgreSQL | Separate database, backups, PITR, restricted operator access |
| Secrets | Staging-only | Independently generated, rotated production secrets |
| CORS | Exact staging origin | Exact production origin; no broad preview wildcard |
| Accounts | Fictional testers | Controlled enrollment, verification, recovery, deprovisioning |
| Seed/provisioning | Controlled synthetic provisioning only | Prohibited |
| Logs | Synthetic operational logs | Approved redaction, access, retention, monitoring, audit policy |

The browser-visible `VITE_API_URL` is not a secret. Database URLs, signing keys, provider tokens, and administrative credentials are secrets and must remain in restricted provider stores.

## Go-live gates

Every item must have an owner, evidence link, reviewer, and approval date.

### Product and safety

- Product scope, claims, limitations, and safety language reviewed.
- Clinical/medical escalation wording reviewed by qualified stakeholders where required.
- No unimplemented feature is advertised as available.
- Baseline and daily intelligence remain clearly separated.
- Missing data remains explicit and is never fabricated.

### Security and privacy

- Threat model and data-flow inventory approved.
- Authentication/session blockers above closed.
- Authorization tests cover role, ownership, and active coach assignment.
- Rate limiting, monitoring, audit events, and incident response tested.
- Consent, privacy, retention, deletion, export, and support-access processes tested.
- Secrets rotation and emergency revocation exercised.
- Dependency/container scans and penetration test findings resolved or explicitly accepted.

### Database and recovery

- Static, append-only migration history validated on fresh and previous-version PostgreSQL databases.
- Pre-deploy migration is separate from web startup.
- Backup policy and point-in-time recovery configured.
- Restore exercise succeeds into an isolated database.
- Destructive downgrade behavior is documented; rollback favors compatible application rollback or restore.
- Capacity, connections, storage growth, and slow queries are monitored.

### Delivery and operations

- CI required checks pass on the exact release commit.
- Vercel and Render production deployments require manual environment approval.
- Release SHA/version is visible in deployment metadata and operational logs.
- Liveness and database readiness checks exist.
- UTC structured logs include a non-sensitive request/correlation ID.
- Alerts route to a staffed responder with severity and escalation rules.
- Frontend, backend, configuration, and database rollback drills have succeeded.
- Production smoke tests and post-deploy observation window are defined.

### Legal and organizational

- Terms, privacy notice, acceptable use, data-processing terms, and support expectations published.
- HIPAA/GDPR/local applicability decision documented by qualified counsel.
- Vendor review and agreements completed.
- Staff access, training, joiner/mover/leaver process, and incident duties documented.
- Production go/no-go is signed by product, engineering, security/privacy, and legal/compliance owners as applicable.

## Migration policy

1. Never edit an applied production migration.
2. Use append-only revisions with explicit upgrade operations and reviewed downgrade/restore implications.
3. Test a fresh database and an upgrade from the prior released revision using the production PostgreSQL major version.
4. Back up before a risky migration and verify the backup can be restored.
5. Run migration as one approved release action before the new application accepts traffic.
6. Do not run the synthetic seed in production.
7. Record release SHA, old/new revision, start/end time, approver, and result.
8. On failure, stop deployment and assess forward-fix, compatible application rollback, or database restore. Do not reflexively downgrade.

## Backup and restore requirements

- Define recovery point and recovery time objectives before selecting provider retention.
- Enable managed backups and point-in-time recovery where the approved plan requires it.
- Encrypt backups and restrict restore/export permission.
- Monitor backup failures.
- Perform scheduled restores into isolated resources.
- Validate user, assessment, check-in, score, alert, authorization, and migration-revision integrity.
- Record evidence and securely destroy temporary restoration resources.

## Observability and correlation

Production logging must be designed around minimization:

- UTC timestamp, severity, service, environment, release SHA, route template, method, status, latency, and correlation ID.
- Internal user/tenant identifiers only when necessary and approved; avoid email addresses.
- Never log passwords, JWTs, invite codes, authorization headers, free-text notes, assessment bodies, check-in bodies, calculation input snapshots, or database URLs.
- Separate security/audit events from ordinary diagnostic logs and apply approved retention/access rules.

The API accepts or generates `X-Request-ID`, returns it to the client, and includes it in sanitized request/error logs. Production verification must confirm proxy propagation, validation, uniqueness expectations, log ingestion, retention, access control, and support tooling. Provider request identifiers may assist investigation but do not replace the application identifier.

Monitoring should cover:

- Liveness, readiness, latency, error rate, and saturation.
- Database availability, connections, storage, backup, replication/PITR, and slow queries.
- Authentication failures, authorization denials, unusual registration activity, and rate-limit events.
- Migration and deployment success/failure.
- Frontend build/runtime errors without health payload capture.
- Alert-delivery health for operational alerts, distinct from product risk alerts.

## Deployment and rollback approval

Production deployment requires manual authorization in GitHub, Vercel, and Render. Automation may prepare artifacts and checks but must not bypass the protected environment approver.

Rollback order:

1. Restrict access and establish incident command.
2. Preserve logs and confirm current release/database revision.
3. Roll back Vercel for frontend-only regressions.
4. Roll back Render application code only when schema-compatible.
5. Correct environment configuration through audited provider controls.
6. Restore a verified backup for incompatible schema/data corruption, following the approved recovery plan.
7. Run smoke and integrity checks before reopening.

## Production evidence packet

Before go-live, assemble:

- Approved architecture and data-flow diagram.
- Threat model and privacy/security reviews.
- Release commit/tag/changelog and dependency inventory.
- CI, security, migration, load, accessibility, and smoke results.
- Backup/restore and rollback drill evidence.
- Environment-variable inventory with secret values omitted.
- Provider access review.
- Incident, support, retention/deletion/export, and consent procedures.
- Signed go/no-go record.

Hosted screenshots are optional product evidence and must use approved non-sensitive accounts. They are not proof of security, correctness, compliance, or production readiness.
