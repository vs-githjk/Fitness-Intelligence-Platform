# Exercise library domain

The exercise library is the first Workout Intelligence domain slice. It does not schedule,
assign, prescribe, or record workouts, and it does not affect the Health Index or Daily
Intelligence engines.

## Ownership and visibility

- System exercises are visible to every authenticated coach and are read-only.
- Coach-private exercises are visible only to their owning coach.
- Requests from another coach return the same not-found response as an unknown identifier.
- Archived private exercises remain directly readable by their owner and may be included in
  library history, but cannot be changed or selected for new content in future modules.
- Trainee access is intentionally absent until an exercise is referenced by an authorized
  assigned workout.

The database enforces the system/private owner relationship and separate slug namespaces.
System slugs are unique globally; private slugs are unique per coach.

## Immutable versions

A newly created private exercise receives version 1 as its only mutable draft. Publishing
stores a deterministic content hash and makes every published field immutable through the
exercise service. Further changes require cloning the latest published version into one new
draft. A partial unique index permits at most one draft per exercise.

The persisted tracking modes are exactly:

- `repetitions_and_load`
- `repetitions_only`
- `duration`
- `distance_and_duration`
- `bodyweight_or_assisted_repetitions`

Versions also store category, movement pattern, equipment, primary and secondary muscle
groups, unilateral context, safety cues, and optional HTTPS image and thumbnail references.
The platform does not host or accept video or animation fields.

## Coach API

All routes use `/api/v1/coach/exercises` and require the coach role.

- `GET /api/v1/coach/exercises`
- `POST /api/v1/coach/exercises`
- `GET /api/v1/coach/exercises/{exercise_id}`
- `PUT /api/v1/coach/exercises/{exercise_id}/draft`
- `POST /api/v1/coach/exercises/{exercise_id}/publish`
- `POST /api/v1/coach/exercises/{exercise_id}/revisions`
- `POST /api/v1/coach/exercises/{exercise_id}/archive`

List requests may filter by scope or exact tracking mode, search names/slugs, and explicitly
include archived owner-private history. Every mutation rejects demo identities in the backend.
