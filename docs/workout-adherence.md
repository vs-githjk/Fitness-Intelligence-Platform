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
| `partial` | Session `ended_incomplete` with ≥1 completed set, or an active session whose completion window has elapsed |
| `ordinary_skipped` | Session `ended_incomplete` with zero completed sets (opened but nothing logged) |
| `safety_skipped` | Session `safety_ended` |
| `missed` | No session and the grace window has elapsed |
| `pending` | No session and still within the window, or an active session still inside the window |
| `coach_cancelled` | `ScheduledWorkout.status == cancelled` (excluded from denominator) |
| `superseded_or_rescheduled` | `ScheduledWorkout.status == superseded` (excluded from denominator) |
| `optional` | `ScheduledWorkout.required == false` (excluded from the required denominator, reported separately) |

**Current-schema note.** The execution schema has no dedicated "declined before
start" action, so `ordinary_skipped` is derived as a started session that was
ended incomplete with zero logged sets. `safety_skipped` is derived from
`safety_ended` sessions. This is derivation, not mutation, and is forward
compatible with an explicit skip action.

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
