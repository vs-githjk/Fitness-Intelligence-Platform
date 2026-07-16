# Workout safety reporting

Workout safety reports are immutable trainee observations attached to an active workout session and,
when selected, its current exercise or set. They do not diagnose medical conditions, provide medical
clearance, or imply emergency or real-time coach monitoring. Safety reports are not monitored
continuously. Coaches must use professional judgment and appropriate escalation.

## Trainee behavior

An active trainee can submit exactly one of these categories: `pain`, `unusual_discomfort`,
`chest_discomfort`, `breathing_difficulty`, `dizziness_or_faintness`, `loss_of_balance`,
`equipment_or_environment`, or `other`, with a mild, moderate, or severe rating and an optional
500-character note. Submitted content cannot be edited or deleted.

Chest discomfort, breathing difficulty, and dizziness or faintness atomically end the session as
`safety_ended`, mark the scheduled workout partial, stop the linked exercise when present, and freeze
all further execution mutations. The displayed guidance is: “Stop exercising. If symptoms are severe,
worsening, or continue, seek urgent professional medical assistance.”

Pain and unusual discomfort pause the linked exercise. The trainee can view the report, skip that
exercise, or end the workout incomplete; there is no casual continue action. Loss of balance,
equipment/environment, and other reports do not automatically alter execution, Daily Intelligence,
readiness, assignments, programs, or future workouts. The interface still offers explicit skip and end
actions.

## Coach review and authorization

Only the actively assigned coach can discover a report. A coach can filter the queue, inspect the
trainee/workout/exercise context, and append acknowledgement or resolution records. Every review is a
new immutable `WorkoutSafetyReview`; prior history is never overwritten, and coach notes are excluded
from trainee responses. Reports cannot be reopened in this phase.

Trainees can report only on their own active sessions. Cross-trainee and cross-coach identifiers return
not found, role checks reject coach submission and trainee review, and every mutation applies the demo
read-only guard. Demo identities can inspect deterministic open, acknowledged, resolved, paused, and
safety-ended examples but cannot create or review them.

See [Workout execution](workout-execution.md), [Security](security.md), and
[Workout readiness context](workout-readiness-context.md).
