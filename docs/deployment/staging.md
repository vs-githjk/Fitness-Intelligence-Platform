# Synthetic staging deployment

This runbook defines the intended Milestone 2C staging topology and the approvals needed to establish it. Staging is for synthetic demonstration and private-beta evaluation only. Do not enter real health information, production credentials, or regulated data.

No hosted URL or hosted screenshot is claimed by this document. Add hosted links and new screenshots only after a real deployment has been approved, completed, and verified.

Related documents:

- [Production readiness](production-readiness.md)
- [Private beta plan](../testing/private-beta-plan.md)
- [Roadmap](../roadmap.md)
- [Troubleshooting](../troubleshooting.md)
- [Security and compliance notes](../security.md)

## Topology

```text
Tester browser
    │ HTTPS
    ▼
Vercel staging project
    │ static React/Vite application
    │ HTTPS JSON requests to VITE_API_URL
    ▼
Render staging web service
    │ FastAPI authentication, authorization, scoring, and persistence
    │ private database connection
    ▼
Render managed PostgreSQL
```

Vercel serves the frontend only. It must not receive the database URL or backend signing secret. Render is the API trust boundary and must continue to enforce role, ownership, and active coach-assignment checks. PostgreSQL must not be called directly by a browser.

Use separate staging resources, credentials, domains, and data. Never connect staging to a future production database.

## Scope and data policy

Staging may contain only:

- Repository-provided synthetic demo personas and history.
- Additional clearly fictional test accounts created for an approved test case.
- Test notes that contain no real medical, identity, contact, employment, or payment information.

Staging must not contain real trainee assessments, real daily check-ins, real coach-client relationships, or copied production data. Seeded passwords are public demonstration values. Coach registration codes and generated trainee invitation tokens are secrets even when the resulting accounts contain only synthetic information.

The current seed creates known synthetic identities and rolling local-date history. It is idempotent for existing records on a given date, but running it on later dates can add newly shifted synthetic records. It is not a backup or a production provisioning mechanism.

## Environment matrix

| Setting | Local Docker | Staging frontend | Staging backend/database | Future production |
|---|---|---|---|---|
| Frontend host | `http://localhost:5175` | `https://<staging-frontend-project>.vercel.app` | Not applicable | Separate production domain/project |
| API host | `http://localhost:8000` | Browser calls the staging API | `https://<staging-api-service>.onrender.com` | Separate production API/service |
| Database | Compose PostgreSQL volume | Never exposed | Separate Render managed PostgreSQL | Separate managed PostgreSQL |
| Data class | Synthetic/local | Synthetic-only | Synthetic-only | Blocked pending production gates |
| Demo seed | Explicit `seed` tool with `SEED_DEMO_DATA=true` | None | Explicit approved one-off only; disabled for web startup | Never |
| Secrets | Local ignored configuration | Build-time public API URL only | Render secret store | Separate production secret store |
| CORS | `http://localhost:5175` | Exact staging origin | Allow exact staging frontend origin | Exact production origin |

## Variable ownership

Values below are placeholders. Do not paste real values into source control, tickets, screenshots, or documentation.

### Vercel frontend

| Variable | Example placeholder | Exposure | Notes |
|---|---|---|---|
| `VITE_API_URL` | `https://<staging-api-service>.onrender.com/api/v1` | Public, compiled into browser assets | Required at build time; changing it requires a frontend rebuild. |
| `VITE_APP_ENV` | `staging` | Public, compiled into browser assets | Enables strict hosted URL validation and the visible staging warning. |
| `VITE_APP_VERSION` | `0.4.1` | Public, compiled into browser assets | Release metadata shown in the staging warning. |

Vercel must not receive `DATABASE_URL`, `JWT_SECRET`, PostgreSQL credentials, or the backend invite value.

### Render backend

| Variable | Example placeholder | Secret? | Notes |
|---|---|---:|---|
| `APP_ENV` | `staging` | No | Activates deployed-environment validation. |
| `DATABASE_URL` | `postgresql+psycopg://<user>:<password>@<private-host>/<database>` | Yes | Use the Render database's private connection details and the installed psycopg driver form. |
| `MIGRATION_DATABASE_URL` | `<managed-staging-migration-url>` | Yes | May equal `DATABASE_URL` for the initial staging topology; keep ownership explicit. |
| `JWT_SECRET` | `<generated-random-secret-at-least-32-characters>` | Yes | Generate in the provider; never reuse local or production values. Rotation invalidates existing tokens. |
| `ACCESS_TOKEN_MINUTES` | `<approved-staging-token-lifetime>` | No | Use an explicitly reviewed value rather than inheriting a local convenience default. |
| `CORS_ORIGINS` | `https://<staging-frontend-project>.vercel.app` | No | Exact browser origin, with no path and normally no trailing slash. |
| `TRUSTED_HOSTS` | `<staging-api-service>.onrender.com` | No | Exact API host names; never use `*` in staging. |
| `COACH_REGISTRATION_CODE` | `<unique-staging-coach-bootstrap-secret>` | Yes | Backend-only invitation gate for coach registration. Set directly in Render; never expose to Vercel. Missing configuration disables coach registration. |
| `DEMO_INVITE_CODE` | `<local-or-seed-compatibility-value>` | Treat as restricted | Deprecated for normal registration; retained only for explicit synthetic compatibility where needed. |
| `SEED_DEMO_DATA` | `false` | No | Keep the web service false. Override to true only for an approved one-off staging seed command. |
| `API_DOCS_ENABLED` | `false` | No | OpenAPI UI is disabled in deployed environments by current validation. |
| `LOG_LEVEL` | `INFO` | No | Do not enable payload-oriented debug logging. |
| `DATABASE_SSLMODE` | `require` | No | Staging validation requires database TLS. |
| `DATABASE_POOL_SIZE` | `<reviewed-small-pool-size>` | No | Size against the managed database connection limit. |
| `DATABASE_MAX_OVERFLOW` | `<reviewed-overflow-limit>` | No | Keep aggregate service connections within the database plan. |
| `DATABASE_POOL_TIMEOUT` | `<reviewed-timeout-seconds>` | No | Bounded wait for a pooled connection. |
| `DATABASE_POOL_RECYCLE` | `<reviewed-recycle-seconds>` | No | Recycles long-lived connections. |
| `DATABASE_CONNECT_TIMEOUT` | `<reviewed-connect-timeout-seconds>` | No | Bounded initial connection time. |
| `PORT` | Provider supplied | No | The service command must bind to `0.0.0.0` and the provider-supplied port. |

`POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` are Compose initialization variables. They are not a substitute for the managed staging `DATABASE_URL`.

## Manual account and approval actions

These actions cannot be completed by repository code alone:

1. A repository administrator authorizes the Render and Vercel GitHub applications for the correct repository.
2. A Render account owner selects the region and plan, creates the staging PostgreSQL database, and accepts the cost and retention settings.
3. A Render administrator creates or approves the web service and enters backend variables in Render's secret/environment controls.
4. A Vercel administrator creates the staging project with `frontend` as its root, enters `VITE_API_URL`, and approves the first deployment.
5. A GitHub administrator configures required checks, deployment environments, and any provider integration permissions.
6. A release owner manually approves the first migration and the controlled creation of synthetic beta accounts.
7. A domain owner approves any custom-domain and DNS changes. A custom domain is optional for staging.

### Clean-database bootstrap without seed data

1. Set a unique `COACH_REGISTRATION_CODE` directly in Render and redeploy the backend after migrations succeed.
2. Choose **Coach** on `/register` and create the first synthetic coach account with that code.
3. Open **Invitations**, create a short-lived invitation, and copy the one-time link.
4. Sign out and register a synthetic trainee through the link.
5. Confirm the invite becomes used, cannot be reused, and the trainee appears only in the issuing coach's roster.

Do not place the coach code in shell history, committed files, browser variables, screenshots, or test reports. The registration and invitation workflow still uses synthetic information only.

Never place provider tokens or database credentials in GitHub-tracked files.

## Prerequisites and current repository constraints

Before approving staging:

- All backend and frontend verification commands must pass on the release commit.
- The release commit and version must be recorded.
- The frontend host must support a single-page-application fallback so direct routes return `index.html`.
- The backend start command must honor the provider port.
- Database migration and web startup must be independently controllable.
- The public demo credentials shown by the frontend must be acceptable for a synthetic-only deployment or hidden by an implemented environment-specific control.
- The example signing-secret placeholder must be replaced with a valid generated provider secret.

The backend container starts only the web process, while the Render blueprint declares `alembic upgrade head` as its pre-deploy action. The seed command is separate, requires `SEED_DEMO_DATA=true`, permits an approved synthetic-only staging run, and always rejects production.

The valid public environment values are `local`, `staging`, and `production`; backend tests additionally use `test`. Compose and Vite both use `local`.

The initial migration imports live model metadata, which remains migration-history technical debt. The current history must pass a clean PostgreSQL upgrade and `alembic check` before staging. Do not rewrite a revision that has been applied remotely; use a reviewed append-only reconciliation migration if later drift is found.

## Ordered deployment workflow

### 1. Freeze and verify the release candidate

1. Select a commit on the protected release branch.
2. Confirm the working tree is clean.
3. Run backend tests and Ruff.
4. Run frontend type checking, build, lint, and unit tests.
5. Run end-to-end tests against disposable local synthetic data.
6. Record the commit SHA, application version, migration head, test results, approver, and intended staging window.

Do not deploy directly from an unreviewed working tree.

### 2. Create the staging database

1. The Render owner creates a PostgreSQL database dedicated to staging.
2. Record provider backup/retention behavior without copying credentials into the repository.
3. Attach its private connection information to the staging backend as `DATABASE_URL`.
4. Confirm no production or personal data source is connected.

### 3. Configure the backend without opening beta access

1. Connect the GitHub repository to the Render staging service.
2. Configure the backend root/build method and the variables above.
3. Configure `/health/ready` as the Render health check.
4. Keep tester access closed until migration, synthetic provisioning, and smoke tests pass.

Use `/health/live` for process liveness and `/health/ready` for database readiness. Authenticated database smoke tests remain required because readiness alone does not verify application queries or authorization.

### 4. Migrate once, with approval

1. Capture the database's current revision.
2. Review the upgrade path and downgrade behavior.
3. Take or confirm a provider backup when the database is not empty.
4. Run `alembic upgrade head` once as an approved release/pre-deploy action.
5. Confirm the expected head with `alembic current`.
6. Stop on any error. Do not seed or start accepting testers after a partial migration.

Do not automatically run `alembic downgrade`. The daily-intelligence downgrade deletes daily-only alerts and drops the daily tables.

### 5. Provision synthetic staging data once

1. Confirm in writing that the database is synthetic-only.
2. Keep the web service at `APP_ENV=staging` and `SEED_DEMO_DATA=false`.
3. Obtain release-owner approval for a reviewed staging-only provisioning procedure.
4. In an approved Render shell or one-off job, run `SEED_DEMO_DATA=true python -m scripts.seed` once after migration. Do not change `APP_ENV=staging`.
5. Verify the created identities and synthetic history against the beta account register.
6. Restore/confirm the web service value remains `SEED_DEMO_DATA=false`. Do not use provisioning as a restart hook, scheduled task, backup restore, or production setup step.

### 6. Start and verify the backend

1. Start Uvicorn on `0.0.0.0` using the provider port.
2. Confirm HTTPS `GET /health` returns 200.
3. Review startup logs for migration, connection, or settings errors.
4. Sign in with a synthetic trainee and coach through the API to prove database connectivity.
5. Confirm secrets and health payloads are not printed in logs.

### 7. Deploy the frontend

1. Connect the GitHub repository to the Vercel staging project.
2. Select `frontend` as the project root.
3. Use install command `npm ci`, build command `npm run build`, and output directory `dist`.
4. Set `VITE_API_URL` to the verified Render HTTPS API base ending in `/api/v1`, `VITE_APP_ENV=staging`, and `VITE_APP_VERSION=0.4.1`.
5. Build and deploy the selected commit.
6. Confirm the SPA fallback works for direct route requests.
7. If the final Vercel origin differs from the planned origin, update backend `CORS_ORIGINS` exactly and redeploy the backend before testing.

### 8. Run the staging smoke suite

Record results, timestamp, release SHA, browser, frontend URL, API URL, and tester. Do not record passwords or health payloads.

#### Availability and routing

- Frontend root loads over HTTPS.
- API `/health/live` returns 200 over HTTPS and includes the expected application version.
- API `/health/ready` returns 200 and reports ready after a database query.
- A browser request from the Vercel origin reaches the Render API without a CORS error.

Run the repository's read-only hosted smoke project after both URLs are final:

```bash
cd frontend
PLAYWRIGHT_BASE_URL=https://<staging-frontend-project>.vercel.app \
PLAYWRIGHT_API_URL=https://<staging-api-service>.onrender.com/api/v1 \
npm run test:e2e
```

When `PLAYWRIGHT_BASE_URL` is hosted, Playwright excludes the mutating local/demo suites and runs only `hosted-smoke.spec.ts`. Do not supply beta passwords on the command line.
- Direct navigation and refresh work for `/login`, `/register`, `/onboarding`, `/trainee/today`, `/trainee/check-in`, `/trainee/progress`, `/coach/dashboard`, and an assigned trainee-detail route.
- An unknown authenticated route shows the application not-found state rather than a provider 404.

#### Authentication and authorization

- Synthetic trainee and coach sign-in succeed.
- Invalid credentials receive the expected neutral error.
- An expired or invalid stored token ends the client session.
- A trainee cannot use coach API endpoints or remain on coach routes.
- A coach cannot use trainee-only endpoints or remain on trainee routes.
- An unassigned coach receives 403 for another trainee's protected detail/history endpoint. Provision a fictional unassigned coach only when this test is explicitly planned.

#### Persistence and scoring

- Submit or edit the synthetic trainee's current local-date check-in.
- Refresh and confirm the same record and recalculated daily score remain.
- Confirm missing trend dates remain gaps.
- Confirm baseline and daily scores remain separate.
- Restart/redeploy the backend without seeding and confirm the edited record remains.
- Confirm the coach sees the corresponding read-only state and cannot edit trainee data or resolve an alert.

### 9. Open the synthetic private beta

Open access only after the release owner signs the smoke record and confirms the [private beta entry criteria](../testing/private-beta-plan.md#entry-criteria). Send testers the data restriction and support path before credentials.

## Logs, monitoring, and correlation

At minimum, staging needs:

- Render service availability and restart notifications.
- Database capacity, connection, and backup visibility.
- Vercel build/deployment failure notifications.
- API 5xx rate and latency monitoring.
- Authentication failure and authorization-denial counts without logging passwords, tokens, notes, or health payloads.

The API accepts a valid non-sensitive `X-Request-ID` or generates one, returns it as `X-Request-ID`, and emits JSON request-completion/failure events with route, method, status, duration, version, and request ID. Verify this behavior after deployment. Never put an email address, token, invite code, database identifier, or health value in a supplied request ID.

Provider request identifiers can supplement `X-Request-ID` during investigation but do not replace it. Product risk alerts are not operational monitoring alerts.

## Rollback

1. Close tester access and announce the incident through the beta support channel.
2. Preserve logs and timestamps without copying health payloads.
3. Determine whether the failure is frontend-only, backend-code-only, configuration, or schema/data related.
4. For frontend-only failure, promote the last verified Vercel deployment.
5. For backend-code failure with a compatible schema, deploy the last verified Render image/commit.
6. For bad environment configuration, restore the last reviewed values through provider controls and redeploy.
7. Do not downgrade the database automatically. Restore from a verified backup when an irreversible migration or data corruption requires it.
8. Repeat the full smoke suite before reopening access.

Document who approved the rollback, the release SHAs before and after, database revision, backup used if any, and follow-up owner.

## Backup and restore exercise

Before beta and after any migration strategy change:

1. Confirm the provider backup policy and retention.
2. Create an approved staging backup.
3. Restore it into a new isolated staging database, never over the only copy.
4. Point a temporary backend service at the restored database using separate secrets.
5. Run health, authentication, authorization, baseline, check-in, and trend smoke tests.
6. Record recovery time, recovery point, migration revision, and discrepancies.
7. Destroy the temporary restored resource after the exercise according to the synthetic-data retention decision.

A backup is not verified until a restore exercise succeeds.

## Hosted evidence

After an actual deploy, create a dated verification record containing approved staging URLs, release SHA, migration revision, smoke results, and incident/support contacts. Hosted screenshots may then be captured from synthetic accounts and clearly labeled with environment, date, route, viewport, and release SHA. Until then, use the repository's [local manual screenshot index](../screenshots/manual/README.md); do not label local captures as hosted staging evidence.
