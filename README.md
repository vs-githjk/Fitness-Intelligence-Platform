# Fitness Intelligence Platform

A role-aware coaching application that turns a trainee's onboarding assessment into an explainable, deterministic baseline Health Index. The first milestone supports registration, coach assignment, draft onboarding, transactional submission, auditable score snapshots, deterministic review flags, and trainee/coach dashboards.

The platform supports coaching decisions. It does not diagnose, treat, or replace qualified medical care. The architecture is designed with a **HIPAA-ready design goal**, but code alone does not establish HIPAA or any other legal compliance.

## Architecture

```text
frontend/  React + Vite + TypeScript + Tailwind + Router + TanStack Query + RHF/Zod
    │ HTTPS/JSON + bearer access token
backend/   FastAPI routes → application services → pure scoring/risk domain code
    │ SQLAlchemy 2 + Alembic
database   PostgreSQL 16 (SQLite is used only by local unit/integration tests)
```

The backend is a modular monolith. Route handlers handle HTTP concerns, services own transactions and authorization helpers, and `app/domain` contains deterministic functions without database or framework dependencies. Assessment submissions store the overall snapshot, each component input/contribution, recommendations, and separate risk-alert records. A uniqueness constraint on `(assessment_id, scoring_version)` protects submission idempotency.

Important entities are `User`, `CoachProfile`, `TraineeProfile`, `CoachTraineeAssignment`, `OnboardingAssessment`, `HealthIndexSnapshot`, `ScoreComponentSnapshot`, and `RiskAlert`. UUID primary keys, foreign keys, uniqueness constraints, and query indexes are defined in the schema.

## Start with Docker

1. Copy the example environment and replace development secrets for any shared environment:

   ```bash
   cp .env.example .env
   docker compose up --build
   ```

2. Open the frontend at <http://localhost:5173>, API docs at <http://localhost:8000/docs>, or health endpoint at <http://localhost:8000/health>.

The backend container applies Alembic migrations and runs the idempotent demo seed before starting. PostgreSQL data lives in the named `fitness_postgres` volume and survives ordinary container restarts. `docker compose down -v` intentionally deletes that data.

## Demo identities

| Role | Email | Password |
|---|---|---|
| Trainee | `trainee@fitness.example.com` | `DemoPass123!` |
| Coach | `coach@fitness.example.com` | `DemoPass123!` |

New trainee registration uses invite code `FIT-DEMO-2026` by default. Self-registration never creates a coach account. The demo invite associates a trainee with the first seeded active coach; production invite-token hashing and lifecycle management are intentionally deferred.

## Manual smoke test

1. Start Compose and wait until `docker compose ps` shows all three services healthy.
2. Sign in as the demo trainee (or register another trainee with the demo invite).
3. Select **Start onboarding**, complete each metric-unit step, and use **Save & next**. Refresh after a save and confirm the draft resumes.
4. Review and submit. Confirm the dashboard shows a 0–100 Health Index, band, ten component contributions, recommendations, and any review notices.
5. Sign out and sign in as the coach.
6. Confirm only assigned trainees appear; open the submitted trainee and compare the score and baseline date.
7. Refresh both views. Then run `docker compose restart`, wait for healthy services, and confirm the same snapshot remains.

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

cd ..
docker compose config
docker compose up --build --wait
```

## API overview

- Auth: `POST /api/v1/auth/register`, `POST /login`, `GET /me`
- Trainee profile: `GET|PUT /api/v1/trainee/profile`
- Onboarding: `GET|PUT /api/v1/assessments/onboarding`, `POST /submit`
- Health Index: `GET /api/v1/health-index/current|history|{snapshot_id}`
- Coach: `GET /api/v1/coach/trainees`, trainee detail/Health Index, and open risk alerts

FastAPI publishes the exact OpenAPI contract at `/docs`. Coach endpoints enforce both role and active assignment; possession of a trainee UUID is insufficient.

## Security, privacy, and compliance limits

Implemented safeguards include bcrypt password hashing, short-lived signed access tokens, role and object authorization, validated inputs/ranges, restricted CORS, opaque UUID identifiers, database constraints, safe client error states, environment-based secrets, and no intentional logging of tokens or health payloads.

This remains an early product. Before production use it needs TLS termination, managed secrets and key rotation, encryption-at-rest verification, immutable audit logs, rate limiting and abuse controls, refresh/revocation strategy, account recovery, consent records, data retention/deletion jobs, backups and disaster recovery, dependency scanning, penetration testing, incident response, vendor review, BAAs where applicable, and legal review for GDPR/HIPAA and local requirements. `TraineeProfile` is the deliberate extension point for an authenticated deletion workflow; deletion UI/audit is deferred.

## Assumptions and deferred features

- Goal alignment v1 gives completion credit to a supported selected goal with the required profile.
- Missing optional cardiovascular data receives a documented neutral-limited score rather than being silently ignored.
- Calorie targets are entered/assigned; this milestone does not medically prescribe or estimate them.
- The assessment payload is a validated JSON structure for flexibility; profile fields needed for querying are also typed columns.
- Manual onboarding is the only health data provider.
- Daily check-ins/history trends, workout and meal planning, wearables, notifications, messaging, exports, clinical reporting, and external AI narration are later milestones.

See [Health Index v1](docs/scoring/health-index-v1.md) for exact formulas and [security notes](docs/security.md) for the threat-boundary summary.
