# Fitness Intelligence Platform

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
- Trainee routes: Today, atomic daily check-in, Progress, onboarding, and submitted-assessment review
- Coach routes: roster overview, daily completion/readiness review, longitudinal trainee detail, and baseline context

## Documentation

- [Product guide](docs/product-guide.md)
- [Getting started](docs/getting-started.md)
- [Trainee user manual](docs/user-manual-trainee.md)
- [Coach user manual](docs/user-manual-coach.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)
- [Health Index v1 scoring](docs/scoring/health-index-v1.md)
- [Daily Intelligence v1 scoring](docs/scoring/daily-intelligence-v1.md)
- [Security and compliance notes](docs/security.md)
- [Design system](docs/design-system.md)
- [User-manual screenshot index](docs/screenshots/manual/README.md)

## Start with Docker

1. Copy the example environment and replace development secrets for any shared environment:

   ```bash
   cp .env.example .env
   docker compose up --build
   ```

2. Open the frontend at <http://localhost:5175>, API docs at <http://localhost:8000/docs>, or health endpoint at <http://localhost:8000/health>.

The backend container applies Alembic migrations and runs the same-day idempotent demo seed before starting. Because daily history is relative to the current local date, starting on a later date can add the next set of dated demo records. PostgreSQL data lives in the named `fitness_postgres` volume and survives ordinary container restarts. `docker compose down -v` intentionally deletes that data.

## Demo identities

| Role | Email | Password |
|---|---|---|
| Trainee | `trainee@fitness.example.com` | `DemoPass123!` |
| Coach | `coach@fitness.example.com` | `DemoPass123!` |
| Trainee with no check-ins | `no-checkins@fitness.example.com` | `DemoPass123!` |

New trainee registration uses invite code `FIT-DEMO-2026` by default. The main trainee has deterministic synthetic daily history with a missing date, positive recovery, low readiness, and longitudinal alerts. The no-check-ins account demonstrates empty states.

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
DATABASE_URL=sqlite:///./fitness.db ../.venv/bin/python -m scripts.seed
DATABASE_URL=sqlite:///./fitness.db ../.venv/bin/uvicorn app.main:app --reload
```

Frontend (Node 22+):

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

| Variable | Purpose |
|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Compose database initialization |
| `DATABASE_URL` | SQLAlchemy connection string |
| `JWT_SECRET` | HS256 signing secret, minimum 32 characters |
| `ACCESS_TOKEN_MINUTES` | Access-token lifetime |
| `CORS_ORIGINS` | Comma-separated allowed browser origins |
| `VITE_API_URL` | Browser-visible versioned API base URL |
| `DEMO_INVITE_CODE` | Local first-milestone coach invite |

Never commit a real `.env` or production secret.

## Database and seed commands

```bash
cd backend
../.venv/bin/alembic upgrade head
../.venv/bin/alembic downgrade -1
../.venv/bin/python -m scripts.seed
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
docker compose config
docker compose up --build --wait
```

## API overview

- Auth: `POST /api/v1/auth/register`, `POST /login`, `GET /me`
- Trainee profile: `GET|PUT /api/v1/trainee/profile`
- Onboarding: `GET|PUT /api/v1/assessments/onboarding`, `POST /submit`
- Health Index: `GET /api/v1/health-index/current|history|{snapshot_id}`
- Daily check-ins: `GET|PUT /api/v1/check-ins/today`, bounded history, and date detail
- Daily intelligence: current score, bounded score history, and gap-aware trends under `/api/v1/daily-scores`
- Coach: roster summaries, assignment-protected check-ins/scores/trends, baseline alerts, and daily alerts

FastAPI publishes the exact OpenAPI contract at `/docs`. Coach endpoints enforce both role and active assignment; possession of a trainee UUID is insufficient.

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
- Workout and meal planning, wearables, notifications, messaging, exports, clinical reporting, and external AI narration remain later milestones.

See [Health Index v1](docs/scoring/health-index-v1.md), [Daily Intelligence v1](docs/scoring/daily-intelligence-v1.md), and [security notes](docs/security.md).
