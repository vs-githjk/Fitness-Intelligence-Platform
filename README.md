# FitIntel 360

FitIntel 360 is the user-facing brand for the Fitness Intelligence Platform repository.

A role-aware coaching application that combines an explainable baseline Health Index with deterministic daily recovery, activity, nutrition-compliance, readiness, and longitudinal trend intelligence.

The platform supports coaching decisions. It does not diagnose, treat, or replace qualified medical care. The architecture has privacy-conscious design goals, but this repository does not establish HIPAA, GDPR, or any other legal compliance.

## Architecture

```text
frontend/  React + Vite + TypeScript + Tailwind + Router + TanStack Query + RHF/Zod
    │ HTTPS/JSON + bearer access token
backend/   FastAPI routes → application services → pure scoring/risk domain code
    │ SQLAlchemy 2 + Alembic
database   PostgreSQL 16 (SQLite is used only by local unit/integration tests)
```

The backend is a modular monolith. Route handlers handle HTTP concerns, services own transactions and authorization helpers, and `app/domain` contains deterministic functions without database or framework dependencies. Assessment submissions store the overall snapshot, each component input/contribution, recommendations, and separate risk-alert records. A uniqueness constraint on `(assessment_id, scoring_version)` protects submission idempotency.

Important entities include `OnboardingAssessment`, `HealthIndexSnapshot`, `DailyCheckIn`, `DailyScoreSnapshot`, `DailyScoreComponent`, and the shared `RiskAlert`. Daily records use typed queryable columns and a unique trainee/local-date constraint.

## Product experience

The responsive interface uses role-specific navigation, reusable semantic components, accessible form feedback, resumable onboarding, explainable Health Index contributions, and a coach roster that transforms from a table to cards on smaller screens. The UI intentionally avoids diagnosis or treatment claims.

- [Design system and interaction rules](docs/design-system.md)
- [Desktop and mobile visual verification](docs/screenshots)
- Trainee routes: Today with current coach details, atomic daily check-in, Progress, onboarding, submitted-assessment review, assigned Program calendar, resumable workout execution, readiness context, workout safety reporting, and a read-only Workouts page with deterministic training-load, adherence, and recorded-best analytics
- Coach routes: roster overview, private single-use trainee invitations, longitudinal trainee review, read-only workout session review with training-load and adherence analytics, Programming authoring, and date-only Program assignment. FitIntel 360 does not deliver invitation emails; coaches copy and share the one-time code or link manually.
- Public demo: backend-issued, short-lived coach or trainee sessions over a deterministic synthetic workspace; demo users are read-only

## Documentation

Project guidance:

- [Contributor and agent guidance (AGENTS.md)](AGENTS.md)
- [Architecture overview](docs/architecture.md)
- [Product principles and boundaries](docs/product-principles.md)
- [Domain glossary](docs/domain-glossary.md)
- [Decision log](docs/decisions/README.md)
- [Deferred-feature register](docs/deferred-features.md)
- [Release notes: v0.5.0](docs/releases/v0.5.0.md)

Product and reference:

- [Product guide](docs/product-guide.md)
- [Getting started](docs/getting-started.md)
- [Trainee invitations](docs/trainee-invitations.md)
- [Trainee user manual](docs/user-manual-trainee.md)
- [Coach manual (send to coaches)](docs/manuals/coach-manual.md)
- [Coach user manual (screen reference)](docs/user-manual-coach.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Health Index v1 scoring](docs/scoring/health-index-v1.md)
- [Daily Intelligence v1 scoring](docs/scoring/daily-intelligence-v1.md)
- [Workout Load v1 analytics](docs/scoring/workout-load-v1.md)
- [Workout adherence](docs/workout-adherence.md)
- [Recorded bests](docs/recorded-bests.md)
- [Coach workout review](docs/coach-workout-review.md)
- [Exercise library](docs/exercise-library.md)
- [Workout templates](docs/workout-templates.md)
- [Training programs](docs/training-programs.md)
- [Program assignment and scheduling](docs/training-assignments.md)
- [Workout execution](docs/workout-execution.md)
- [Workout safety](docs/workout-safety.md)
- [Workout readiness context](docs/workout-readiness-context.md)
- [Public demo](docs/demo.md)
- [Security and compliance notes](docs/security.md)
- [Design system](docs/design-system.md)
- [User-manual screenshot index](docs/screenshots/manual/README.md)
- [Staging deployment runbook](docs/deployment/staging.md)
- [Production-readiness checklist](docs/deployment/production-readiness.md)
- [Release runbook](docs/operations/release-runbook.md)
- [Deployment and recovery](docs/operations/deployment-and-recovery.md)
- [Private-beta plan](docs/testing/private-beta-plan.md)
- [Real-user testing guide](docs/testing/real-user-testing.md)
- [Feedback and bug-triage process](docs/testing/feedback-triage.md)
- [Milestone 4 planning — Profile and Media Foundation](docs/planning/milestone-4-profile-media-foundation.md)
- [Roadmap](docs/roadmap.md)

## Start with Docker

1. Build the images, apply migrations, and explicitly load the synthetic local demo:

   ```bash
   docker compose build
   docker compose --profile tools run --rm migrate
   docker compose --profile tools run --rm -e SEED_DEMO_DATA=true seed
   docker compose up --wait
   ```

2. Open the frontend at <http://localhost:5175>, API docs at <http://localhost:8000/docs>, or health endpoint at <http://localhost:8000/health>.

Migration, seed, and web startup are separate commands. The seed refuses to run unless a synthetic-data environment explicitly allows it; production always rejects it, and it is never part of a web replica's startup. Because daily history is relative to the current local date, seeding on a later date can add the next set of dated demo records. PostgreSQL data lives in the named `fitness_postgres` volume and survives ordinary container restarts. `docker compose down -v` intentionally deletes that data.

Compose has safe local-development fallbacks. If you maintain a personal `.env`, update it yourself from `.env.example`; never commit it or reuse local values in staging.

## Public demo and local test identities

Open **Explore Demo** from the sign-in page to enter a backend-controlled synthetic coach or trainee workspace without credentials. Public demo users receive normal role-scoped tokens, but the backend rejects persistent mutations. The demo indicator remains visible until **Exit demo** is selected.

The following credentialed identities are for explicitly seeded local development and automated testing only; they are not the public demo accounts and are not displayed by the frontend:

| Role | Email | Password |
|---|---|---|
| Trainee | `trainee@fitness.example.com` | `DemoPass123!` |
| Coach | `coach@fitness.example.com` | `DemoPass123!` |
| Trainee with no check-ins | `no-checkins@fitness.example.com` | `DemoPass123!` |

The seeded identities remain available for deterministic local testing. A clean database can instead bootstrap without seed data: register a coach with the backend-only coach registration code, create a single-use trainee invitation, then register the trainee with that invitation. The main seeded trainee has deterministic daily history with a missing date, positive recovery, low readiness, and longitudinal alerts.

## Manual smoke test

1. Start Compose and wait until `docker compose ps` shows all three services healthy.
2. Sign in as the demo trainee and open **Today**. Confirm Recovery, Activity, Nutrition, and Training Readiness are distinct from the Baseline Health Index.
3. Open **Edit today**, change a value, submit, refresh, and confirm the same local-date record and recalculated score remain.
4. Open **Progress**, switch between 7 and 30 days, and confirm the seeded missing date is a gap rather than zero.
5. Sign in as the coach. Confirm today-completion, low-readiness, and daily-alert summaries appear.
6. Open Arjun's record and review latest check-in data, daily trends, alerts, and the separate onboarding baseline. Confirm the coach cannot edit check-ins.
7. Sign in as the no-check-ins trainee to verify empty states. Then run `docker compose restart`, wait for health, and confirm Arjun's edited check-in persists.

## Local development

Backend (Python 3.12+):

```bash
python3 -m venv .venv
.venv/bin/pip install -e 'backend[dev]'
cd backend
DATABASE_URL=sqlite:///./fitness.db ../.venv/bin/alembic upgrade head
APP_ENV=local SEED_DEMO_DATA=true DATABASE_URL=sqlite:///./fitness.db ../.venv/bin/python -m scripts.seed
DATABASE_URL=sqlite:///./fitness.db ../.venv/bin/uvicorn app.main:app --reload
```

Frontend (Node 22.12+):

```bash
cd frontend
npm ci
npm run dev
```

## Environment variables

| Variable | Purpose |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose database initialization |
| `APP_ENV` | Runtime policy: `local`, `staging`, or `production` |
| `DATABASE_URL` | SQLAlchemy connection string |
| `MIGRATION_DATABASE_URL` | Optional direct database URL used only by Alembic |
| `JWT_SECRET` | HS256 signing secret, minimum 32 characters |
| `ACCESS_TOKEN_MINUTES` | Access-token lifetime |
| `CORS_ORIGINS` | Comma-separated allowed browser origins |
| `TRUSTED_HOSTS` | Comma-separated API hostnames accepted by the backend |
| `API_DOCS_ENABLED` | Enables `/docs`, `/redoc`, and `/openapi.json` when appropriate |
| `SEED_DEMO_DATA` | Explicit one-off synthetic seed gate; production always rejects it |
| `DEMO_MODE_ENABLED` | Explicitly enables backend-issued public demo sessions; defaults false and production rejects true |
| `DEMO_SESSION_MINUTES` | Short public-demo token lifetime, default 30 minutes |
| `LOG_LEVEL` | Backend stdout log level |
| `PORT` | Backend listener port; Render supplies this automatically |
| `DATABASE_SSLMODE`, `DATABASE_POOL_SIZE`, `DATABASE_MAX_OVERFLOW`, `DATABASE_POOL_TIMEOUT`, `DATABASE_POOL_RECYCLE`, `DATABASE_CONNECT_TIMEOUT` | Database TLS and conservative SQLAlchemy connection controls |
| `VITE_API_URL` | Browser-visible versioned API base URL |
| `VITE_APP_ENV` | Browser-visible environment label (`local`, `staging`, or `production`) |
| `DEMO_INVITE_CODE` | Deprecated local/synthetic compatibility value; normal registration uses coach-specific invitations |
| `COACH_REGISTRATION_CODE` | Backend-only code that enables invitation-only coach registration; never expose it to Vercel |

The browser-visible release version is compiled from `frontend/package.json`; it is not configured through an environment variable.

Never commit a real `.env` or production secret.

## Database and seed commands

```bash
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/alembic downgrade -1
APP_ENV=local SEED_DEMO_DATA=true ../.venv/bin/python -m scripts.seed
```

The migration history can recreate a clean schema. Production deployments should use a managed PostgreSQL backup/restore policy and run migrations as a separate release step rather than in every web replica.

## Verification commands

```bash
cd backend
../.venv/bin/pytest
../.venv/bin/ruff check app alembic scripts tests

cd ../frontend
npm run typecheck
npm run build
npm run lint
npm run test
# Requires the Compose frontend/API to be running and a local Chrome installation.
npm run test:e2e

cd ..
docker compose --env-file .env.example config
docker compose build
docker compose --profile tools run --rm migrate
docker compose --profile tools run --rm -e SEED_DEMO_DATA=true seed
docker compose up --wait
```

## API overview

- Auth: `POST /api/v1/auth/register/coach`, `POST /register/trainee`, `POST /login`, `POST /demo-session`, `GET /me` (`POST /register` remains a deprecated trainee alias)
- Trainee profile: `GET|PUT /api/v1/trainee/profile`
- Onboarding: `GET|PUT /api/v1/assessments/onboarding`, `POST /submit`
- Health Index: `GET /api/v1/health-index/current|history|{snapshot_id}`
- Daily check-ins: `GET|PUT /api/v1/check-ins/today`, bounded history, and date detail
- Daily intelligence: current score, bounded score history, and gap-aware trends under `/api/v1/daily-scores`
- Coach: private invitation creation/list/revocation, roster summaries, assignment-protected check-ins/scores/trends, baseline alerts, and daily alerts
- Coach programming: owned exercise, workout-template, and training-program draft/publish/revise/archive endpoints under `/api/v1/coach`
- Training assignment: coach preview/create/history/cancel-future APIs and the trainee Program schedule
- Workout execution: trainee-owned start/resume, set logging, exercise skip, completion, intentional incomplete ending, immutable readiness context, and append-only safety APIs; assigned coaches have a scoped safety review queue

When API documentation is enabled, FastAPI publishes the exact OpenAPI contract at `/docs`. Coach endpoints enforce both role and active assignment; possession of a trainee UUID is insufficient. Operational probes are available at `/health/live` and `/health/ready`, with `/health` retained for compatibility.

## Security, privacy, and compliance limits

Implemented safeguards include bcrypt password hashing, short-lived signed access tokens, role and object authorization, validated inputs/ranges, restricted CORS, opaque UUID identifiers, database constraints, safe client error states, environment-based secrets, and no intentional logging of tokens or health payloads.

This remains an early product. Before production use it needs TLS termination, managed secrets and key rotation, encryption-at-rest verification, immutable audit logs, rate limiting and abuse controls, refresh/revocation strategy, account recovery, consent records, data retention/deletion jobs, backups and disaster recovery, dependency scanning, penetration testing, incident response, vendor review, BAAs where applicable, and legal review for GDPR/HIPAA and local requirements. `TraineeProfile` is the deliberate extension point for an authenticated deletion workflow; deletion UI/audit is deferred.

## Assumptions and deferred features

- Goal alignment v1 gives completion credit to a supported selected goal with the required profile.
- Missing optional cardiovascular data receives a documented neutral-limited score rather than being silently ignored.
- Calorie targets are entered/assigned; this milestone does not medically prescribe or estimate them.
- The assessment payload is a validated JSON structure for flexibility; profile fields needed for querying are also typed columns.
- Manual onboarding and daily check-ins are the only health-data providers.
- Check-in drafts and past-date corrections are not implemented; submission is atomic and only today's local-date record is editable.
- Workout load/adherence analytics, completed-session coach analytics, post-completion correction, meal planning, wearables, notifications, messaging, exports, clinical reporting, and external AI narration remain later milestones.

See [Health Index v1](docs/scoring/health-index-v1.md), [Daily Intelligence v1](docs/scoring/daily-intelligence-v1.md), and [security notes](docs/security.md).
