# Architecture overview

This document describes the architecture as implemented in the repository at
version 0.5.0. It does not describe unbuilt future modules as though they exist;
planned work lives in [roadmap.md](roadmap.md) and `docs/planning/`.

## Frontend architecture

- React 18 + Vite + TypeScript + Tailwind, routed with `react-router-dom`.
- Server state via TanStack React Query; forms via React Hook Form + Zod.
- Role-aware navigation and layout in `AppShell`; pages under `src/pages/`,
  reusable UI under `src/components/`, shared types in `src/types.ts`.
- Environment/config is centralized in `src/env.ts`: `VITE_API_URL` and
  `VITE_APP_ENV` (`local`/`staging`/`production`), with the displayed release
  version compiled from `package.json`. Non-local builds require a non-local
  HTTPS API URL.
- **Identity-scoped cache:** every protected query key is prefixed with the
  account identity scope (`useAccountQueryScope()`). Login, logout, and demo
  transitions therefore never render or repopulate another identity's data.
- The browser is untrusted. It renders authorization outcomes; it does not
  enforce them. Disabled controls and banners are explanatory only.

## Backend layering

A modular monolith with strict layering:

1. **Routers** (`app/api/`) — HTTP concerns: request/response models, status
   codes, dependency wiring. No business logic.
2. **Services** (`app/*_services.py`) — own transactions and authorization
   helpers (ownership, role, active-assignment, revision/optimistic-concurrency,
   idempotency). All cross-entity invariants live here.
3. **Domain / analytics** — pure, deterministic functions with no database or
   framework imports:
   - `app/domain/` — Health Index and Daily Intelligence scoring.
   - `app/analytics/` — Workout Intelligence engines (`workout-load-v1`).
   These two packages are independent and must not import each other.

Pydantic v2 schemas (`app/schemas.py`) validate all input with strict ranges;
SQLAlchemy 2 ORM models live in `app/models.py`.

## Database and migrations

- PostgreSQL 16 in every non-test environment; SQLite is used only by the
  in-memory pytest suite.
- Alembic migrations are append-only, linear, and dual-path (SQLite
  `batch_alter_table` + PostgreSQL). Head is **20260716_0012**.
- Identifiers are UUIDs; foreign keys and uniqueness constraints protect
  integrity (e.g. one `WorkoutSession` per `ScheduledWorkout`, unique
  `(assessment_id, scoring_version)`, unique trainee/local-date daily records).
- Local dates are stored explicitly so history is not reinterpreted after
  timezone/DST changes.

## Authentication and roles

- Email/password with bcrypt hashing; signed, expiring JWT access tokens.
- Two roles: **coach** and **trainee**. Every protected endpoint checks role and
  object ownership server-side; coach access to a trainee additionally requires an
  active `CoachTraineeAssignment`.
- JWTs are held in browser local storage for the current milestone; a production
  hardening pass (see [security.md](security.md)) would move to a protected
  cookie/refresh design with rotation, revocation, MFA, and rate limiting.

## Invitations

- Coach registration is invitation-only, gated by a backend-only
  `COACH_REGISTRATION_CODE` (timing-safe comparison; missing config disables the
  route).
- Trainee invitations use cryptographically random tokens; only SHA-256 hashes are
  stored, the raw token is shown once, and invitations are coach-owned,
  single-use, expiring, revocable, and optionally email-restricted. Redemption is
  serialized with row locking and commits user/profile/assignment/invitation
  transactionally.

## Demo-mode architecture

- `DEMO_MODE_ENABLED` defaults false, is enabled deliberately in local/staging,
  and is rejected by production config validation.
- Demo login resolves explicitly seeded users that are both active and `is_demo`,
  issuing an ordinary short-lived role JWT — no password or hardcoded token
  reaches the frontend.
- A shared backend guard rejects every demo mutation with `403 demo_read_only`; a
  central route-inventory test in `app/security.py` prevents adding a mutation
  without demo coverage.
- Normal web startup never seeds. The explicit `seed` command is gated by
  `SEED_DEMO_DATA=true` and rejected in production.

## Health Index

Deterministic, versioned baseline score (`health-index-v1`) computed from an
immutable submitted onboarding assessment: per-component inputs, contributions,
recommendations, and separate risk-alert records are persisted. See
[scoring/health-index-v1.md](scoring/health-index-v1.md). It is coaching guidance,
not diagnosis or clearance.

## Daily Intelligence

Deterministic, versioned daily scoring (`daily-intelligence-v1`) over atomic
current-local-date check-ins (recovery, activity, nutrition compliance, feeling,
optional note), with bounded 7-/30-day trends and explicit missing-date gaps. See
[scoring/daily-intelligence-v1.md](scoring/daily-intelligence-v1.md). It is
distinct from the Health Index and never fabricates missing data.

## Workout Intelligence

- **Programming:** owned, versioned `Exercise`/`WorkoutTemplate`/`Program`
  entities; coaches author drafts and publish immutable versions. Programs pin
  exact template versions.
- **Assignment/scheduling:** one current and one optional future primary program
  assignment per trainee; trainee-local, date-only `ScheduledWorkout`s pin exact
  program and template versions, with cancellation and future supersession.
- **Execution:** resumable `WorkoutSession`s with immutable prescription
  snapshots, five tracking modes, explicit set logging, per-exercise skipping,
  completion, and intentional incomplete ending. Every mutation requires the
  current session revision; stale writes return `409`.
- **Analytics (`workout-load-v1`, read-only):** planned/completed session load,
  resistance volume, weekly planned/completed load, adherence, recorded bests, and
  immutable per-session `WorkoutLoadSummary` records; plus read-only coach session
  review. Analytics never modify programs, schedules, sets, loads, readiness, or
  deloads and draw no medical conclusions. See
  [scoring/workout-load-v1.md](scoring/workout-load-v1.md),
  [workout-adherence.md](workout-adherence.md),
  [recorded-bests.md](recorded-bests.md), and
  [coach-workout-review.md](coach-workout-review.md).

## Immutable versioning

Published `ExerciseVersion`, `WorkoutTemplateVersion`, and `ProgramVersion`
records are immutable; new versions are created rather than edited, and downstream
references pin exact versions so publishing a newer version never mutates existing
programs, schedules, or history.

## Readiness context

At execution start the app captures an immutable copy of an eligible persisted
Daily Score snapshot (or explicit unavailability). Readiness is contextual
information only: it cannot mutate Daily Intelligence or workout content, and it
provides no medical clearance and gates no exercise.

## Safety reporting

Trainee-submitted `WorkoutSafetyReport`s are immutable; coach
`WorkoutSafetyReview` acknowledgement/resolution history is append-only. Critical
reports atomically persist the report, terminal session state, partial schedule
state, and safety events. Safety mutations are in the demo inventory. Safety
reports are reviewed asynchronously by the coach and are **not** continuously or
urgently monitored.

## Analytics authorization

All Workout Intelligence analytics endpoints are read-only GETs. Trainees read
only their own data; coaches read only trainees with an active assignment;
inactive assignments are denied and cross-coach discovery returns `404`. Demo
accounts may inspect analytics but perform no mutations. The one mutation in this
area — the explicit whole-workout skip (`POST /api/v1/trainee/workouts/{id}/skip`)
— enforces trainee ownership, rejects the coach role, rejects non-scheduled/
started statuses, and is demo-protected.

## Deployment topology

- **Backend + database:** Render — a Docker web service (`./backend`) with
  pre-deploy `alembic upgrade head`, health check `/health/ready`, and a managed
  PostgreSQL 16 instance. `SEED_DEMO_DATA=false`; seeding is a separate explicit
  operation.
- **Frontend:** Vercel — static SPA build with rewrite-to-`index.html`, security
  headers, and `noindex`. `VITE_API_URL` points at the Render HTTPS API.
- **CI:** GitHub Actions runs backend (ruff + pytest), migrations (clean
  PostgreSQL upgrade/current/check), frontend (typecheck/lint/test/build), and
  Compose config/build. Render auto-deploys on `checksPass`.
- Details and env-var ownership: [deployment/staging.md](deployment/staging.md),
  [operations/deployment-and-recovery.md](operations/deployment-and-recovery.md).

## Major security boundaries

- Trust boundary is the FastAPI service + PostgreSQL; the browser is untrusted.
- Vercel serves only static assets and never receives `DATABASE_URL`,
  `JWT_SECRET`, PostgreSQL credentials, or `COACH_REGISTRATION_CODE`.
- Server-side role/ownership/active-assignment enforcement on every request;
  `404` for cross-account discovery.
- Demo read-only guard + central inventory test.
- Immutable historical records and revision-checked writes.

See [security.md](security.md) for the full control list and known limitations.

## Domain relationship overview

```
Coach ──owns──> Exercise ──> ExerciseVersion
  │                              ▲ (pinned)
  ├──owns──> WorkoutTemplate ──> WorkoutTemplateVersion ──> WorkoutTemplateExercise ──> WorkoutSetPrescription
  │                                        ▲ (pinned)
  ├──owns──> Program ──> ProgramVersion ──(references)──> WorkoutTemplateVersion
  │                          │
  └──assigns──> ProgramAssignment (one active + one optional future) ──> Trainee
                     │
                     └──generates──> ScheduledWorkout (trainee-local date, version-pinned)
                                          │
                          ┌───────────────┼─────────────────────────┐
                          │               │                         │
                    WorkoutSession   (explicit skip)          (cancelled/superseded)
                    │  (immutable snapshot of prescriptions)
                    ├──> WorkoutSetLog / WorkoutSessionExercise / WorkoutSessionEvent
                    ├──> WorkoutReadinessContext (immutable copy of Daily Score)
                    ├──> WorkoutSafetyReport (immutable) ──> WorkoutSafetyReview (append-only)
                    └──> WorkoutLoadSummary (immutable, per version)

Trainee ──> OnboardingAssessment (immutable) ──> HealthIndexSnapshot ──> components/recommendations/RiskAlert
Trainee ──> DailyCheckIn (unique per local date) ──> DailyScoreSnapshot ──> DailyScoreComponent
```
