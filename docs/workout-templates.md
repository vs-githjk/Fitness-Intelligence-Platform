# Workout template authoring

Workout templates are reusable, coach-owned prescription graphs. This backend-only
capability was introduced after the exercise library and does not create programs,
assignments, scheduled workouts, or trainee execution records.

## Version lifecycle

A `WorkoutTemplate` is the stable owner-scoped root. It can have one mutable draft
and any number of immutable published `WorkoutTemplateVersion` records. Creating a
revision clones the current published graph into a new draft. Archiving removes the
root from future active selection while retaining its complete history.

Draft updates use complete graph replacement. Clients must send the current
`expected_draft_revision`; a stale value returns HTTP 409 so two browser tabs cannot
silently overwrite each other. Root mutations are serialized in PostgreSQL so two
simultaneous requests cannot both pass the same revision check. Publication validates
the entire graph and replaces
the draft state with a published state. Repeating publication when no newer draft
exists returns the current published version without creating another version.

Every template exercise references an exact published `ExerciseVersion`. A coach
may select system exercises and their own active private exercises. Foreign private,
unpublished, and archived-root exercises are rejected without exposing ownership
details.

## Prescription units

Resistance and assistance accept `kg` or `lb`. The original value and unit are
retained and a Decimal canonical kilogram value is stored to three decimal places.
Assistance is stored separately and must never be treated as resistance volume.

Distance accepts `meters`, `kilometers`, or `miles`. The original distance is stored;
deterministic hashing also normalizes it to Decimal meters. Pace, calories, elevation,
heart-rate zones, and completed-set fields are outside this version.

## Tracking modes

Set fields are validated against the referenced exercise version:

- `repetitions_and_load`: requires repetitions; permits load, RPE, rest, and tempo.
- `repetitions_only`: requires repetitions; permits RPE, RIR, rest, and tempo.
- `duration`: requires duration; permits RPE and rest.
- `distance_and_duration`: requires distance and duration; permits RPE and rest.
- `bodyweight_or_assisted_repetitions`: requires repetitions; permits assistance,
  RPE, RIR, rest, and tempo.

Exercise display order is contiguous from one within each section. Set numbering is
contiguous from one within each exercise.

## Immutability and authorization

Publication hashes canonical template metadata, ordered exact exercise-version IDs,
exercise instructions, and every normalized set field. Timestamps and database child
IDs are excluded. Published metadata and child graphs have no mutation path.

All endpoints require a coach. Ownership predicates are centralized and foreign
template IDs return HTTP 404. Every mutation explicitly enforces the public-demo
read-only guard. There is no hard-delete or trainee template endpoint.
