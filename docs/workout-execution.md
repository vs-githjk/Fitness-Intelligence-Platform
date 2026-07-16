# Resumable trainee workout execution

Workout execution turns one eligible `ScheduledWorkout` into one trainee-owned immutable execution
graph. It does not modify the published template, Program, assignment, or date-only schedule
metadata. This phase intentionally excludes safety reports, readiness capture, load/adherence
analytics, coach review, and post-completion corrections.

## Lifecycle and snapshots

`POST /api/v1/trainee/workouts/{scheduled_workout_id}/start` locks the owned schedule row. It either
returns the existing session or creates a `WorkoutSession`, ordered `WorkoutSessionExercise`
snapshots, prescribed `WorkoutSetLog` rows, and a `session_started` event in one transaction. The
unique scheduled-workout constraint prevents duplicate sessions. Cancelled, superseded, completed,
and partial workouts cannot start.

The execution graph copies the exact exercise version, trainee-visible instructions, safety cues,
order, set type, and planned prescription. Coach-only notes are not copied into trainee responses.
Future source changes cannot alter active or historical execution. Schedule transitions are:

- `scheduled` → `in_progress` when started;
- `in_progress` → `completed` after confirmed complete resolution; or
- `in_progress` → `partial` after an intentional incomplete ending.

Completed and ended-incomplete sessions are terminal and immutable through the API.

## Explicit saves and concurrency

Typing does not persist a set. Each set save, set addition, exercise skip, completion, or incomplete
ending supplies `expected_session_revision`. Every successful mutation increments the session
revision and appends a bounded event. A stale revision returns `409 session_revision_conflict` with
the current revision and does not overwrite data. The browser keeps local unsaved values and offers
an explicit reload; there is no automatic merge or offline synchronization.

Trainee-added sets use an idempotency key and remain separate from prescribed rows. Skipping a set
requires no actual values. Skipping an exercise requires a bounded reason and marks its remaining
planned sets skipped while preserving the original prescription.

## Tracking modes and units

| Mode | Required actual values | Optional | Prohibited |
|---|---|---|---|
| `repetitions_and_load` | repetitions, external load, kg/lb | RPE | assistance, duration, distance, RIR |
| `repetitions_only` | repetitions | RPE, RIR | load, assistance, duration, distance |
| `duration` | seconds | RPE | repetitions, load, assistance, distance, RIR |
| `distance_and_duration` | distance, distance unit, seconds | RPE | repetitions, load, assistance, RIR |
| `bodyweight_or_assisted_repetitions` | repetitions | kg/lb assistance, RPE, RIR | external load, duration, distance |

Original kg/lb values and units are retained. A centralized Decimal helper also stores canonical
kilograms for load or assistance. Assistance is never counted as external resistance load. Workout
load is not calculated in this phase.

## Completion and resume

Reopening a Program workout with a session ID loads the saved graph. Starting the same schedule
again returns the same active session and records a resume event; it never duplicates the graph.
Normal completion requires every exercise to be completed or explicitly skipped, actual duration,
session RPE, and confirmation. Ending incomplete requires a bounded reason and preserves all work
already logged. Both outcomes show an immutable trainee summary.

## Authorization and demo

Every endpoint requires the trainee role and ownership-scoped schedule/session/set queries. Direct
foreign IDs are denied without disclosing the object. Coaches cannot mutate execution. All six
mutation routes invoke the backend demo guard and are checked against a centralized inventory;
synthetic demo users can inspect examples but receive `403 demo_read_only` for changes.

## Time behavior and current limits

Scheduled occurrence remains a date in the assignment's trainee timezone snapshot; execution does
not add a local clock time. Session/activity/event timestamps are UTC instants. Changing a profile
timezone later does not reinterpret the pinned scheduled date.

There are no safety reports, readiness context, load or adherence summaries, coach session-review
API, missed-workout automation, offline sync, automatic conflict merge, or post-completion edits.
