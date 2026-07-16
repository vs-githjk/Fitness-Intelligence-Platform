# Workout readiness context

Readiness context connects an existing persisted Daily Intelligence snapshot to a scheduled workout
without changing either system. It never rewrites Daily Intelligence, changes a prescription, blocks a
start, recommends an automatic deload, or provides medical clearance.

For a scheduled workout, the system selects `DailyScoreSnapshot` rows for the trainee whose local date
is on or before the scheduled local date. It chooses the latest eligible local date, then the latest
calculation timestamp on that date. If none exists, readiness is explicitly unavailable; no score is
invented and execution remains available.

Age is the scheduled local date minus the source local date. Zero- and one-day-old contexts are fresh;
two or more days are stale. The response exposes score, state, source local date, calculation timestamp,
scoring version, age, and availability/staleness.

Scheduled-workout responses provide a computed preview. Starting the workout copies that exact context
into a unique `WorkoutReadinessContext` linked to both the schedule and session, including an explicit
unavailable record when necessary. The capture is immutable, so later check-in edits or score
recalculations cannot rewrite workout history.

The required user guidance is: “Readiness is contextual guidance based on your latest available daily
check-in. It does not provide medical clearance and does not change this workout automatically.” Demo
data includes fresh, stale, and unavailable examples.

See [Daily Intelligence v1](scoring/daily-intelligence-v1.md),
[Training assignments](training-assignments.md), and [Workout execution](workout-execution.md).
