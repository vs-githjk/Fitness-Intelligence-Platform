# Workout Load v1

`workout-load-v1` is a deterministic, versioned engine for Workout Intelligence
analytics. It is fully independent from `health-index-v1` and
`daily-intelligence-v1`: it does not import, modify, or reuse any Daily
Intelligence or Health Index scoring code, and those systems are unchanged.

Training load summarizes workout duration and reported effort. **It is not a
medical measure.** The engine does not diagnose, does not predict injury, does
not model overtraining, and never modifies programs, workouts, schedules, sets,
loads, progression, readiness, or deload weeks.

The engine lives in `backend/app/analytics/` as pure functions over plain input
dataclasses (no database, no FastAPI). The ORM-facing bridge is
`backend/app/workout_analytics_services.py`.

## Missing-data principle

A missing input stays missing (`null`) and is never coerced to zero. Every
output carries an explainable `calculation_payload` describing the inputs used
and, when a value is unavailable, the reason.

## Session load

```
planned_session_load   = planned_duration_minutes × target_session_rpe
completed_session_load = actual_duration_minutes × session_rpe
```

Planned inputs use this priority, and are never inferred:

1. `ScheduledWorkout` overrides (`planned_duration_minutes`, `target_session_rpe`)
2. Pinned `WorkoutTemplateVersion` defaults (`estimated_duration_minutes`, `target_session_rpe`)

If either value is absent the planned load is **unavailable**, not zero.

`completed_session_load` is calculated only for a terminal session
(`completed`, `ended_incomplete`, `safety_ended`) and only when both
`actual_duration_minutes` and `session_rpe` exist. Session RPE is never
inferred.

## Resistance volume

```
set_volume_kg     = actual_repetitions × actual_load_canonical_kg
session_volume_kg = Σ valid completed-set volumes
```

Only completed sets in the `repetitions_and_load` tracking mode contribute.
Volume **excludes** skipped sets, incomplete sets, assistance values,
bodyweight-only work, repetitions-only work, timed work, distance work, and
planned-only values. If no set qualifies, `session_volume_kg` is unavailable,
not zero.

The engine never applies unilateral multipliers, bodyweight estimates, 1RM
calculations, calorie estimates, acute/chronic workload ratios, or injury-risk
calculations.

## Independent factual metrics

Reported alongside load, never combined into a single composite score:

- completed prescribed sets
- skipped prescribed sets
- completed trainee-added sets
- completed repetitions
- completed working sets
- completed exercises
- total duration (seconds, summed over completed timed sets)
- total distance (canonical meters, summed over completed distance sets)

## Immutable load summary

`WorkoutLoadSummary` persists one row per terminal session per calculation
version (`workout-load-v1`). Content is immutable after creation. Because
terminal sessions are themselves immutable, recalculation is idempotent — the
existing row is returned unchanged. There is no mutation endpoint for summary
content. Active (non-terminal) sessions may be previewed without persistence.

Uniqueness is enforced by `uq_workout_load_summary_session_version`.

## kg / lb

Loads are stored with their original value and unit plus a canonical
`actual_load_canonical_kg` (3-decimal, `0.45359237` kg per lb). Volume and
cross-unit comparisons always use the canonical kilograms. Distance is
converted to canonical meters for `total_distance_meters`.
