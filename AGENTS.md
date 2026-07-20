# AGENTS.md — Contributor and agent guidance

This file orients any contributor — Claude Code, Codex, other coding agents, and
humans — working in the FitIntel 360 repository. Read it before editing.

> The repository and its tests are the source of truth. This document summarizes
> conventions; when it disagrees with the code, the code wins and this file
> should be corrected in a documentation change.

## What FitIntel 360 is

FitIntel 360 is the user-facing brand for the Fitness Intelligence Platform: a
role-aware coaching web application that combines an explainable baseline Health
Index with deterministic daily recovery/activity/nutrition-compliance/readiness
and trend intelligence, plus a Workout Intelligence layer (programming,
scheduling, execution, safety reporting, readiness context, and read-only
training-load/adherence/recorded-best analytics).

It supports coaching decisions. It does **not** diagnose, treat, provide medical
clearance, or replace qualified medical care. This repository targets synthetic
staging and controlled test-user evaluation; it does not establish HIPAA, GDPR,
or any other regulatory compliance.

## Current release

- Application version: **0.5.0** (Workout Intelligence milestone, tag `v0.5.0`).
- Alembic head: **20260716_0012**.
- Version sources: backend `backend/app/__init__.py` (`__version__`), consumed by
  FastAPI/OpenAPI and `/health*`; frontend `frontend/package.json` (mirrored in
  `package-lock.json`), surfaced through `frontend/src/env.ts`. Keep all version
  sources aligned; the backend uses `dynamic = ["version"]` in `pyproject.toml`.

## Architecture (summary)

See [docs/architecture.md](docs/architecture.md) for the full picture.

```
frontend/  React 18 + Vite + TypeScript + Tailwind + Router + TanStack Query + RHF/Zod
    │ HTTPS/JSON + bearer access token
backend/   FastAPI routes → application services → pure domain/analytics code
    │ SQLAlchemy 2 + Alembic
database   PostgreSQL 16 (SQLite is used only by local unit/integration tests)
```

The backend is a modular monolith: route handlers own HTTP concerns, services own
transactions and authorization helpers, and `app/domain/` (daily/Health scoring)
and `app/analytics/` (Workout Intelligence) contain deterministic functions with
no database or framework dependencies. The two calculation packages are
independent and must not import each other.

## Important directories

| Path | Purpose |
| --- | --- |
| `backend/app/api/` | FastAPI routers (HTTP concerns only) |
| `backend/app/*_services.py` | Application services: transactions + authorization |
| `backend/app/domain/` | Pure Health Index / Daily Intelligence scoring |
| `backend/app/analytics/` | Pure Workout Intelligence engines (`workout-load-v1`) |
| `backend/app/models.py` | SQLAlchemy ORM models |
| `backend/app/schemas.py` | Pydantic v2 request/response schemas |
| `backend/app/security.py` | Auth helpers + demo mutation inventory |
| `backend/alembic/versions/` | Append-only migrations |
| `backend/scripts/` | `start`, `seed` entry points |
| `backend/tests/` | pytest suite (SQLite in-memory) |
| `frontend/src/` | React app (pages, components, hooks, types) |
| `frontend/e2e/` | Playwright specs |
| `docs/` | Product, scoring, operations, testing, planning docs |

## Standard development commands

Backend (create a local `backend/.venv`; it is gitignored):

```
cd backend && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/ruff check .
.venv/bin/python -m pytest
```

Migrations need env vars: `DATABASE_URL`/`MIGRATION_DATABASE_URL`, `APP_ENV=local`,
and `JWT_SECRET` of **at least 32 characters**. Then:

```
.venv/bin/alembic upgrade head | downgrade -1 | current | heads | check
```

Frontend:

```
cd frontend
npx tsc -b --pretty false     # typecheck
npx eslint .                  # lint (CI treats warnings as failures)
npx vitest run                # unit/component tests
npx vite build                # production build
```

## Docker workflow

`compose.yaml` runs `db`, `backend`, `frontend`, plus `migrate` and `seed` under
the `tools` profile. Fixed dev ports are 8000 (backend) and 5175 (frontend).

For an isolated end-to-end run, use a **separate compose project** so the dev DB
volume is never touched:

```
docker compose down                                   # stop dev, keep volume
docker compose -p fitintel-e2e down -v && ... build
docker compose -p fitintel-e2e up -d db               # wait healthy
docker compose -p fitintel-e2e --profile tools run --rm migrate
docker compose -p fitintel-e2e --profile tools run --rm -e SEED_DEMO_DATA=true seed
docker compose -p fitintel-e2e up -d backend frontend # wait healthy
cd frontend && rm -rf .playwright && npx playwright test
docker compose -p fitintel-e2e down -v                # teardown
docker compose up -d                                  # restore dev
```

Visual/daily Playwright specs regenerate `docs/screenshots/*.png`; run
`git checkout -- docs/screenshots/` before committing so they stay out of the
diff unless a screenshot change is intended.

## Migration conventions

- Append-only. **Never rewrite or edit an already-applied historical migration.**
- Named `YYYYMMDD_NNNN_slug.py` with bare `YYYYMMDD_NNNN` revision ids; each has a
  single linear `down_revision`.
- Dual-path: SQLite via `op.batch_alter_table`, PostgreSQL directly.
- Idempotent and additive where possible; new columns nullable. String enums use
  `native_enum=False`.
- Validate on both engines and run `alembic check` (no drift) before committing.

## Commit conventions

- Conventional-commit prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
  `test:`.
- **One logical change per commit.** A phase/milestone ships as exactly one
  coherent commit unless explicitly told otherwise.
- Do **not** add `Co-Authored-By` trailers or agent self-attribution.
- Do not mix product code with documentation-only or version-bump commits.

## Non-negotiable invariants

- **Immutable domain entities.** Terminal `WorkoutSession`s and their prescription
  snapshots, `WorkoutSafetyReport`s, `WorkoutLoadSummary`s, readiness contexts,
  submitted onboarding baselines, and published `ExerciseVersion`/
  `WorkoutTemplateVersion`/`ProgramVersion` records are immutable through the API.
  Do not add post-completion correction paths without an approved decision.
- **Authorization is server-side.** The browser is untrusted. Every read/write is
  scoped by role, ownership, and (for coaches) an active `CoachTraineeAssignment`.
  Cross-account discovery returns `404`, not a distinguishable error. Never weaken
  these checks.
- **Demo mutation protection.** Every new mutation endpoint must call
  `ensure_not_demo` and be registered in the central demo-mutation inventory in
  `app/security.py`; a route-inventory test enforces coverage. Demo accounts are
  read-only (`403 demo_read_only`).
- **Identity-scoped React Query cache.** Every protected query key must include the
  account identity scope (`useAccountQueryScope()`), so login/logout/demo
  transitions never render or repopulate another identity's data.
- **Deterministic calculations are versioned and documented.** Any scoring/analytics
  formula carries a version string (e.g. `workout-load-v1`) and a doc under
  `docs/scoring/` or an equivalent; missing data is shown explicitly, never
  fabricated or defaulted to `0`.

## Documentation expectations

- Prefer updating and consolidating existing docs over adding overlapping ones.
- Keep terminology consistent with [docs/domain-glossary.md](docs/domain-glossary.md).
- Reflect product boundaries from [docs/product-principles.md](docs/product-principles.md).
- Record accepted contracts in [docs/decisions/README.md](docs/decisions/README.md).
- Update [docs/roadmap.md](docs/roadmap.md) only when scope/ordering is approved.

## Release gates

Full detail in [docs/operations/release-runbook.md](docs/operations/release-runbook.md).
In short: pre-release audit → full backend/frontend gates → isolated Playwright →
version alignment → release notes → single release commit → push → deploy
(migrate, backend, verify, explicit seed, frontend) → hosted verification →
**tag only after hosted verification passes**.

## Prohibited shortcuts

- Do **not** rewrite historical migrations.
- Do **not** weaken backend authorization, invitation security, or demo protection.
- Do **not** add a mutation without demo-enforcement auditing.
- Do **not** remove the identity scope from a protected query key.
- Do **not** add AI, medical, or autonomous behavior merely because an agent is
  implementing an adjacent feature. AI/medical/adaptive behavior requires an
  explicit, approved decision.
- Do **not** push, deploy, or tag unless explicitly instructed to.
- Do **not** commit secrets, real credentials, tokens, or private hostnames.
