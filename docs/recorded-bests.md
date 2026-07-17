# Recorded bests

Recorded bests report the highest values a trainee has recorded in the selected
reporting range. They are descriptive, not motivational claims or medical
measures.

## Terminology

Only these labels are used, under the heading **Recorded best**:

- Highest recorded load
- Highest recorded repetitions
- Highest recorded volume

The product never uses "PR", "personal record", "lifetime best", or
"all-time best".

## Scope

Recorded bests search **all available completed compatible workout history**
for the authenticated trainee — they are not bounded to the 7/14/30-day range
used by the load and adherence charts. The query uses an indexed `row_number()`
window aggregation so the database selects one best row per exercise; no
unbounded history is materialized in application memory.

## Rules

- Only **completed sets** in **completed terminal sessions** are considered.
- Comparison is by stable **Exercise root** (`ExerciseVersion.exercise_id`), so
  results survive exercise re-versioning. The source `ExerciseVersion` is
  retained for auditability.
- Comparisons respect compatible tracking modes:
  - **Highest recorded load** and **Highest recorded volume**:
    `repetitions_and_load` only.
  - **Highest recorded repetitions**: `repetitions_and_load`,
    `repetitions_only`, and `bodyweight_or_assisted_repetitions`.
- Assistance values are excluded.
- Demo data is isolated from normal-user calculations by account scope.

## Audit fields

Each recorded best includes the source date, scheduled workout, session, set
number, source exercise version, the original value and unit, and the canonical
kilograms where relevant.
