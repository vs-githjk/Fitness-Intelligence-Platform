# Program assignment and workout scheduling

A `TrainingAssignment` connects one authorized coach, trainee, and exact immutable
`TrainingProgramVersion`. Each generated `ScheduledWorkout` pins the exact
`WorkoutTemplateVersion` from its Program slot. Neither assignment nor schedule generation ever
resolves a root's latest version.

## Effective dates and timezone behavior

The coach chooses an effective date interpreted in the trainee profile's IANA timezone. Program
week 1 begins on the first Monday on or after that date; later weeks remain fixed Monday–Sunday.
Schedules contain dates only—there are no clock times or UTC conversions for workout occurrence.
The assignment stores a timezone snapshot so its original scheduling context remains explicit.

## Current and future assignments

A trainee can have at most one active primary assignment and one scheduled future primary
assignment. Partial unique database indexes enforce both invariants, while the service locks the
active coach–trainee relationship during creation or cancellation.

Creating a future replacement preserves the current assignment until its effective date. Only
current workouts on or after that date become `superseded`; earlier rows remain unchanged. If a
different future replacement already exists, it and its schedule become superseded. A future
assignment can be cancelled, which marks its future schedule `cancelled` without deleting it.
Trainee-local reads activate a due future assignment and preserve an immutable
`AssignmentHistory` event snapshot.

## Coach and trainee experiences

**Assignments** lets a coach choose an assigned trainee, published Program version, and effective
date; preview the generated weeks; confirm replacement warnings; inspect current/upcoming state;
review history; and cancel a future replacement. Foreign trainees and Program versions remain
inaccessible. Every mutation enforces demo read-only protection.

**Program** gives a trainee a current Program, current week, today workout/rest context, future
weeks, rest days, deload labels, Required/Optional status, and workout details. Eligible scheduled
workouts can be opened for execution. Their lifecycle extends through `in_progress`, `completed`,
or `partial`; `cancelled` and `superseded` entries remain historical and cannot start. Session
execution never changes the pinned Program, template version, scheduled local date, or assignment
timezone snapshot. Adherence, readiness capture, training load, missed-state automation, and
safety reports remain deferred. See [Workout execution](workout-execution.md).
