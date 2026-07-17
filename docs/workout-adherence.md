# Workout adherence

Workout adherence is deterministic and derived from persisted execution data.
It never destructively mutates historical rows: "missed" and other states are
computed at read time. Adherence is descriptive analytics, not a medical
measure and not automated coaching — it never changes programs, schedules, or
progression.

## Classification

Each scheduled workout is classified once, using the `ScheduledWorkout`
captured IANA timezone (from its `TrainingAssignment.timezone`):

| Classification | Rule |
|---|---|
| `completed` | Session explicitly completed |
| `partial` | Session `ended_incomplete` **or** `safety_ended` (regardless of how much was logged), or an active session whose completion window has elapsed |
| `ordinary_skipped` | Explicit pre-start whole-workout skip with `skip_kind = ordinary` |
| `safety_skipped` | Explicit pre-start whole-workout skip with `skip_kind = safety` |
| `missed` | No session, no explicit skip, and the grace window has elapsed |
| `pending` | No session/skip and still within the window, or an active session still inside the window |
| `coach_cancelled` | `ScheduledWorkout.status == cancelled` (excluded from denominator) |
| `superseded_or_rescheduled` | `ScheduledWorkout.status == superseded` (excluded from denominator) |
| `optional` | `ScheduledWorkout.required == false` (excluded from the required denominator, reported separately) |

**Skipped is explicit only.** A workout is skipped only when the trainee
explicitly skips it before starting (see the skip endpoint below). Skipped is
**never** derived from zero completed sets, zero logged work, `ended_incomplete`
status, session duration, or session-RPE availability. A started session that
ends incomplete — including one where nothing was logged, and including a
`safety_ended` session — is always **partial**.

## Explicit whole-workout skip

`POST /api/v1/trainee/workouts/{scheduled_workout_id}/skip` records a pre-start
skip. Only a scheduled, not-started occurrence may be skipped (cancelled,
superseded, completed, partial, already-skipped, and in-progress workouts are
rejected with 409). It creates no `WorkoutSession` and persists `skip_kind`
(`ordinary` / `safety`), a bounded `reason`, an optional note (≤500 chars), and
a skipped timestamp. Repeating an identical skip is idempotent. The mutation is
a trainee-only action that enforces ownership and backend demo protection; a
coach cannot perform it.

Bounded reasons — ordinary: `time_constraint`, `schedule_conflict`,
`equipment_unavailable`, `travel`, `coach_instruction`, `other`. Safety-related:
`recovery_concern`, `pain_or_discomfort`, `illness_or_unwell`,
`other_safety_concern`. A safety-related skip is not a confirmed injury or
illness and does not create a `WorkoutSafetyReport`.

## Completion window

- The window is the scheduled local date plus **one full local calendar grace day**.
- `missed` begins at 00:00 on the **second** local date after the scheduled date.
- All local-date maths use the workout's captured IANA timezone.

## Eligible denominator

```
eligible_required = required scheduled workouts in range
                    − coach_cancelled
                    − superseded_or_rescheduled
```

Optional workouts are excluded from the required denominator and reported in
`optional_count`. Safety skips remain in the denominator and are reported
separately in `safety_skipped_count`.

```
completion_adherence_percentage = completed_count / eligible_required × 100
```

- No partial credit — only `completed` counts in the numerator.
- No denominator means **unavailable** (`null`), never 0%.
- The percentage is bounded 0–100 and reported alongside every count and the
  denominator.

## Prescribed-set adherence

```
planned_working_sets           = all prescribed working sets in eligible executed sessions
completed_planned_working_sets = completed prescribed working sets
percentage                     = completed / planned × 100   (capped at 100)
```

Trainee-added sets never increase adherence (excluded from numerator and
denominator). No denominator means unavailable.

## Exercise adherence

One documented rule across all five tracking modes:

> An exercise counts as completed when at least one prescribed **working** set
> is completed. For exercises that prescribe no working sets, it counts as
> completed when at least one prescribed set of any type is completed. Skipped
> or safety-stopped exercises never count as completed.

Behavior by mode:

| Tracking mode | Completed when |
|---|---|
| `repetitions_and_load` | ≥1 prescribed working set completed |
| `repetitions_only` | ≥1 prescribed working set completed |
| `bodyweight_or_assisted_repetitions` | ≥1 prescribed working set completed |
| `duration` | ≥1 prescribed working set completed; if none prescribed, ≥1 prescribed set completed |
| `distance_and_duration` | ≥1 prescribed working set completed; if none prescribed, ≥1 prescribed set completed |

The denominator is the prescribed exercises in eligible executed sessions.
