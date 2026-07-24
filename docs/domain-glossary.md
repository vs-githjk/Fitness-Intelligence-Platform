# Domain glossary

Consistent definitions for FitIntel 360 domain terms. Use these terms — and only
these meanings — in code, UI copy, docs, and issues. See
[product-principles.md](product-principles.md) for the boundaries behind them.

## Roles and users

- **Coach** — a user who authors exercises, templates, and programs, invites and
  reviews trainees, and reads (read-only) trainee analytics and safety reports for
  trainees with an active assignment.
- **Trainee** — a user assigned to a coach who onboards, checks in daily, executes
  scheduled workouts, and views their own analytics.
- **Demo user** — a public, synthetic identity (`is_demo`) used for the read-only
  Explore Demo experience. Demo accounts can inspect but cannot mutate (`403
  demo_read_only`).
- **Test user** — a private, real (non-demo) identity used for controlled
  product testing (currently one coach and four trainees). Distinct from demo
  users; test users can perform normal mutations. See
  [testing/real-user-testing.md](testing/real-user-testing.md).
- **Production user** — a real end user of a future production deployment. No such
  users exist yet; real-health-data collection is gated by unmet
  security/privacy/legal requirements.

## Identity records

- **UserProfile** — a role-agnostic identity record, one-to-one with a user:
  preferred display name, bio, professional fields surfaced for coaches (headline,
  coaching specialties, years of experience, plain-text certifications), a trainee
  training-goals field, and a reference to the current avatar. Shared across roles;
  self-declared and **never verified**. Distinct from `CoachProfile`/`TraineeProfile`.
- **Avatar** — a user's profile photo: an `AVATAR`-purpose `MediaAsset` referenced by
  `UserProfile.avatar_media_id`. Uploaded/replaced/removed through
  `/api/v1/me/avatar` (reusing the media subsystem) and delivered to the owner or an
  active coach/trainee relationship through an authorized route
  (`/api/v1/users/{id}/avatar/content`); never a public URL.
- **UserPreferences** — a role-agnostic preference record, one-to-one with a user:
  timezone, weight unit, distance unit, locale, and theme/privacy/accessibility
  placeholders. Preferences change presentation only; they never alter recorded
  data. `UserPreferences.timezone` is the canonical timezone preference.
- **MediaAsset** — a metadata record for one stored binary object (image). Holds the
  owner, uploader, purpose, visibility, lifecycle status, storage provider, opaque
  storage key, content type, size, SHA-256 checksum, and sanitized filename. Bytes
  live in a storage provider, never in the database or in an API response.
- **StorageProvider** — the provider-independent contract (`write`, `open`, `exists`,
  `delete`) behind which media bytes are stored. `LocalStorageProvider` is the only
  implemented backend; cloud providers are reserved.
- **Media lifecycle** — `active → replaced → soft_deleted → purged`. A user-facing
  delete is a **soft delete**; bytes are removed only by a service-level **purge**.
- **Media visibility** — who may read an asset (`private`, `coach_trainee`,
  `exercise`). Enforced server-side by the media service; Phase 2 self-service
  uploads are `private` and owner-only.

## Starter library

- **Starter library** — a curated, read-only set of system-owned Programs (with their
  Templates and Exercises) that coaches browse and clone. Not a marketplace or shared
  coach library.
- **System library account** — the single non-login `is_system` coach account that
  owns starter Templates and Programs. Starter Exercises use `Exercise.scope = system`.
- **Clone (starter)** — the coach action that creates an independent, coach-owned
  **draft** Program from a starter Program, duplicating its Templates into coach-owned
  published Templates and referencing the system Exercises. The source is never
  changed and the copy never re-syncs (`cloned_from_program_id` /
  `cloned_from_template_id` record attribution only).

## Programming entities

- **Exercise** — a coach-owned exercise root (stable lineage identity).
- **ExerciseVersion** — an immutable published version of an Exercise; downstream
  references pin an exact version.
- **WorkoutTemplate** — a coach-owned reusable workout root.
- **WorkoutTemplateVersion** — an immutable published version of a template,
  containing ordered exercises and set prescriptions.
- **Program** — a coach-owned multi-week training program root.
- **ProgramVersion** — an immutable published version of a Program, referencing
  exact WorkoutTemplateVersions across ordered weekday slots (with rest days,
  optional/required context, and coach-authored deloads).
- **ProgramAssignment** — assignment of a ProgramVersion to a trainee. A trainee
  has one current (active) assignment and optionally one scheduled future
  assignment.
- **ScheduledWorkout** — a trainee-local, date-only planned workout materialized
  from a ProgramVersion, pinning exact program and template versions. Statuses
  include scheduled, completed, partial (via its session), skipped, cancelled, and
  superseded.

## Execution entities

- **WorkoutSession** — a trainee's execution of a ScheduledWorkout, created at
  start with an immutable snapshot of prescriptions. Terminal sessions are
  immutable. Terminal states: completed, ended-incomplete, safety-ended.
- **WorkoutSafetyReport** — an immutable trainee-submitted safety concern raised
  during execution.
- **WorkoutSafetyReview** — append-only coach acknowledgement/resolution history
  for a safety report. It is not created by a skip.
- **Readiness Context** — an immutable copy of an eligible persisted Daily Score
  snapshot (or explicit unavailability) captured at workout start. Contextual
  information only; no medical clearance.
- **WorkoutLoadSummary** — an immutable, one-row-per-terminal-session-per-
  calculation-version record of computed load for analytics.

## Adherence and status terms

- **adherence** — the read-time classification of scheduled workouts across a
  reporting window. Derived, never a destructive mutation of history.
- **partial** — a workout whose session started and then ended incomplete or was
  safety-ended. Always partial, even with zero logged sets; absence of logged sets
  never downgrades a started session to skipped.
- **skipped** — a workout the trainee explicitly skipped before starting, via the
  explicit skip endpoint. Skips create no WorkoutSession.
- **safety-skipped** — an explicit pre-start skip of kind `safety` (surfaced as a
  *wellbeing* skip in trainee UI). It is a skip, **not** a WorkoutSafetyReport, and
  is reported separately from ordinary skips. It creates no safety report.
- **missed** — no session and no explicit skip past a two-local-day grace window.
- **recorded best** — the best recorded compatible completed performance in a
  trainee's available completed history (highest recorded load, repetitions, or
  volume for an exercise across its stable lineage). Scope is
  `all_available_history`.

## Prohibited or discouraged terminology

- Do **not** call Program content a *medical prescription*, *prescription*, or
  *clearance*. It is a coaching plan.
- Do **not** use *PR*, *personal record*, *lifetime*, or *all-time* where the
  product means **recorded best**.
- Do **not** describe readiness as *cleared to train* or a *medical assessment*.
- Do **not** present self-entered credentials or self-reported values as
  *verified*.
- Do **not** describe safety reports as *monitored* or *emergency* support.
