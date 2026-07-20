# Decision log

Lightweight record of major accepted product and platform contracts for FitIntel
360. These are the durable decisions that constrain future work; they are
implemented in the code and detailed in the linked documents. Do not rewrite
historical facts — supersede a decision with a new dated entry rather than editing
an accepted one.

## How to add a decision

Copy the template below, give it the next number, and fill it in. Keep it short —
one screen. Link to the authoritative doc or code rather than duplicating detail.

```
## ADR-NNNN — <title>

- **Status:** proposed | accepted | superseded (by ADR-XXXX)
- **Date:** YYYY-MM-DD
- **Context:** why this decision was needed.
- **Decision:** what was decided.
- **Consequences:** what this enables/constrains; follow-ups.
- **Alternatives considered:** options rejected and why.
```

Status values: **proposed** (under discussion), **accepted** (in force),
**superseded** (replaced — link the successor).

---

## Accepted contracts

The following contracts are **accepted** and in force as of v0.5.0. Each links to
its authoritative documentation.

## ADR-0001 — Deterministic, versioned scoring

- **Status:** accepted
- **Date:** 2026-07-20 (contract in force since the Health Index milestone)
- **Context:** coaching decisions require reproducible, explainable numbers, not
  opaque model output.
- **Decision:** all scores and analytics are deterministic functions of persisted
  inputs, each carrying a version string and a document; formula changes create a
  new version rather than editing an existing one; missing data is explicit.
- **Consequences:** enables auditability and provenance; requires a new versioned
  calculation + doc for any formula change. See
  [../scoring/health-index-v1.md](../scoring/health-index-v1.md),
  [../scoring/daily-intelligence-v1.md](../scoring/daily-intelligence-v1.md).
- **Alternatives considered:** heuristic/ML scoring — rejected for lack of
  explainability and safety risk.

## ADR-0002 — Versioned, immutable Programs and Templates

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** coaches iterate on exercises/templates/programs, but downstream
  schedules must remain stable.
- **Decision:** published Exercise/WorkoutTemplate/Program versions are immutable;
  new versions are created rather than edited; references pin exact versions.
- **Consequences:** publishing a newer version never mutates existing programs,
  schedules, or history. See [../training-programs.md](../training-programs.md),
  [../workout-templates.md](../workout-templates.md).
- **Alternatives considered:** mutable content — rejected as it would silently
  rewrite assigned work.

## ADR-0003 — Immutable historical execution

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** execution history must be trustworthy.
- **Decision:** terminal WorkoutSessions and their prescription snapshots are
  immutable through the API; revision-checked writes prevent stale overwrites.
- **Consequences:** no in-place edits to completed work; post-completion
  correction is deferred (ADR-0010 register). See
  [../workout-execution.md](../workout-execution.md).
- **Alternatives considered:** editable history — rejected for integrity.

## ADR-0004 — One active primary Program per trainee

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** trainees need a single unambiguous current plan.
- **Decision:** a trainee has one current (active) ProgramAssignment plus at most
  one scheduled future assignment; future assignments supersede rather than
  overlap.
- **Consequences:** unambiguous scheduling; supersession is explicit. See
  [../training-assignments.md](../training-assignments.md).
- **Alternatives considered:** multiple concurrent programs — rejected as
  ambiguous for scheduling and analytics.

## ADR-0005 — Explicit whole-workout skipping

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** a trainee needs a first-class way to decline a scheduled workout
  before starting, distinct from simply not doing it.
- **Decision:** a trainee-only, demo-protected `POST
  /api/v1/trainee/workouts/{id}/skip` records an ordinary or safety (wellbeing)
  skip with a bounded reason; a skip creates no WorkoutSession and no safety
  report.
- **Consequences:** "skipped" comes only from an explicit skip; enables accurate
  adherence. See [../workout-execution.md](../workout-execution.md) and
  [../workout-adherence.md](../workout-adherence.md).
- **Alternatives considered:** inferring skips from inactivity — rejected as
  ambiguous and destructive.

## ADR-0006 — Workout load analytics (`workout-load-v1`)

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** coaches and trainees benefit from deterministic training-load and
  adherence views.
- **Decision:** an isolated, pure analytics engine computes planned/completed
  session load, resistance volume, weekly load, and adherence, versioned
  `workout-load-v1`, read-only, never mutating training data or drawing medical
  conclusions.
- **Consequences:** analytics are reproducible bookkeeping, not a medical measure.
  See [../scoring/workout-load-v1.md](../scoring/workout-load-v1.md).
- **Alternatives considered:** coupling analytics into execution services —
  rejected to keep calculations pure and independent from daily scoring.

## ADR-0007 — Adherence classification rules

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** consistent, non-destructive workout status semantics.
- **Decision:** classification is derived at read time; `partial` = started then
  ended incomplete or safety-ended (even with zero sets); `skipped` = explicit
  skip only; `missed` = no session/skip past a two-local-day grace; eligible
  denominator excludes cancelled/superseded/optional; safety skips are counted but
  reported separately.
- **Consequences:** absence of logged sets never downgrades a started session to
  skipped. See [../workout-adherence.md](../workout-adherence.md).
- **Alternatives considered:** treating zero-set sessions as skipped — rejected as
  misleading.

## ADR-0008 — All-history Recorded best

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** "best" must be well-defined and honest.
- **Decision:** a recorded best is the best recorded compatible completed
  performance across a trainee's available completed history (scope
  `all_available_history`), not a bounded window and not a lifetime/all-time/PR
  claim.
- **Consequences:** wording avoids PR/personal-record/lifetime. See
  [../recorded-bests.md](../recorded-bests.md).
- **Alternatives considered:** a bounded reporting window — rejected as it would
  hide earlier bests and mislead.

## ADR-0009 — Safety-reporting boundaries

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** safety features must not imply monitored/urgent care.
- **Decision:** trainee safety reports are immutable and coach
  acknowledgement/resolution is append-only; reports are reviewed asynchronously
  and are not continuously monitored; a wellbeing skip is not a safety report.
- **Consequences:** copy must avoid monitoring/emergency implications. See
  [../workout-safety.md](../workout-safety.md).
- **Alternatives considered:** presenting safety review as real-time monitoring —
  rejected as unsafe and untrue.

## ADR-0010 — Readiness-context immutability

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** readiness shown during execution must be a stable record.
- **Decision:** at workout start the app captures an immutable copy of an eligible
  Daily Score snapshot (or explicit unavailability); readiness cannot mutate Daily
  Intelligence or workout content and provides no medical clearance.
- **Consequences:** readiness is contextual information only. See
  [../workout-readiness-context.md](../workout-readiness-context.md).
- **Alternatives considered:** live-recomputing readiness — rejected; a captured
  record must not change after the fact.

## ADR-0011 — Demo read-only behavior

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** a public demo must be safe and non-destructive.
- **Decision:** demo identities are synthetic and read-only; a shared backend guard
  returns `403 demo_read_only` for every mutation, and a central route-inventory
  test enforces coverage for new mutations.
- **Consequences:** every new mutation must be added to the demo inventory. See
  [../demo.md](../demo.md) and [../security.md](../security.md).
- **Alternatives considered:** frontend-only demo restrictions — rejected; the
  browser is not the security boundary.
