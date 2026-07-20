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
