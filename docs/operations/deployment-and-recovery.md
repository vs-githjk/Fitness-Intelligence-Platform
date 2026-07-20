# Deployment and recovery

Operational reference for the hosted staging topology and recovery decisions. This
document describes intentionally public repository configuration only; it contains
no secrets or private hostnames. Concrete provider values, secrets, and exact
domains live in the Render and Vercel dashboards — see
[../deployment/staging.md](../deployment/staging.md) for the ordered setup runbook
and env-var ownership.

## Topology

- **Backend — Render web service.** Docker service built from `./backend`
  (`render.yaml`), branch `main`, auto-deploy on `checksPass`. Pre-deploy command
  `alembic upgrade head`. Health check path `/health/ready`. Runs
  `python -m scripts.start`. `SEED_DEMO_DATA=false`, `API_DOCS_ENABLED=false`.
- **Database — Render PostgreSQL 16.** Managed instance; connection provided to the
  backend via `DATABASE_URL`/`MIGRATION_DATABASE_URL` (`fromDatabase`). `require`
  SSL.
- **Frontend — Vercel.** Static SPA (root `frontend`) with rewrite-to-`index.html`,
  security headers, and `noindex`. Built with `VITE_API_URL` (the Render HTTPS API
  base ending `/api/v1`) and `VITE_APP_ENV=staging`.

## Migration responsibility

- Migrations run **only** through Alembic as the Render backend pre-deploy command
  (`alembic upgrade head`), never on normal web startup.
- Migrations are append-only, additive, and dual-path; the current head is
  `20260716_0012`. Never rewrite applied history.

## Health endpoints

- `/health` and `/health/live` — liveness; report `{status, version}`.
- `/health/ready` — readiness (checks database); Render's health check path.
- After any deploy, confirm all three report the expected version and that the
  database migration head is correct.

## Demo seed command location

- Seeding is a separate, explicit operation: `python -m scripts.seed` (the Compose
  `seed` service under the `tools` profile), gated by `SEED_DEMO_DATA=true`.
- Production/staging config keeps `SEED_DEMO_DATA=false`; normal startup never
  seeds. Seeding is deterministic and idempotent — reseeding produces the same
  synthetic state. Never seed a real-user environment with demo data expecting it
  to overwrite real content.

## Environment-variable ownership

- **Backend-only (never sent to Vercel):** `DATABASE_URL`,
  `MIGRATION_DATABASE_URL`, `JWT_SECRET`, `COACH_REGISTRATION_CODE`,
  `DEMO_INVITE_CODE`, PostgreSQL credentials, and all pool/SSL tuning.
- **Frontend build-time (public, compiled into assets):** `VITE_API_URL`,
  `VITE_APP_ENV`. These are public by nature — never place secrets in `VITE_*`.
- **Boundary values:** `CORS_ORIGINS` (exact staging frontend origin) and
  `TRUSTED_HOSTS` (exact API host) are set in Render, never `*` in staging.

## Secret handling

- Secrets live only in provider dashboards. Do not commit them, print them, paste
  them into issues/screenshots, or share them with coding agents.
- The coach registration code and JWT secret are backend-only; exposing them
  weakens the coach-registration and token boundaries.

## Backup verification

- The managed PostgreSQL instance is the system of record. Confirm the provider's
  backup schedule is enabled and periodically exercise a restore into a scratch
  target to verify backups are usable (a backup that has never been restored is
  unproven).
- Backups may contain test-user-entered content; treat them as sensitive.

## Migration failure response

1. The pre-deploy migration failing **blocks the deploy** — the new backend does
   not go live. Treat this as a stop.
2. Inspect the migration logs; do not force-forward.
3. If the migration is faulty, fix it forward with a new append-only revision (do
   not edit the applied/failed historical revision) and redeploy.
4. If the database was left partially migrated, restore from a verified backup
   before retrying, and confirm `alembic current` matches expectations afterward.

## Backend rollback

- Redeploy the previous known-good backend build/commit on Render.
- Because migrations are additive, the previous backend generally runs against the
  newer schema; if a rollback requires a schema downgrade, treat it as a database
  decision (below), not an automatic step.

## Frontend rollback

- Roll back to the previous Vercel deployment. The frontend is static and
  decoupled; a frontend rollback does not change backend or database state. Ensure
  the rolled-back frontend still targets a compatible `VITE_API_URL`.

## Database restore decision boundaries

- Restore is a high-impact, last-resort action reserved for data corruption or a
  failed/partial migration that cannot be fixed forward.
- Prefer fix-forward (append-only migration, backend redeploy) over restore
  whenever data integrity allows.
- A restore discards data written after the backup point; for test-user
  environments, confirm the acceptable data-loss window with maintainers before
  restoring.

## Incident notes

- For a suspected security/privacy incident (P0), contain first (protect data and
  access), then diagnose — see
  [../testing/feedback-triage.md](../testing/feedback-triage.md).
- A dedicated private security-reporting route still needs to be established for
  this project; until then, report privately to a maintainer out of band. Do not
  invent a contact address.
- Record what happened, when, blast radius, containment, and follow-ups. Keep
  sensitive body content out of incident notes where practical.
