# Workout template authoring

Workout templates are reusable, coach-owned workout graphs. The coach Programming
workspace provides their authoring interface. Published versions can be pinned inside
[training programs](training-programs.md), whose exact versions can then generate
[date-only assignments](training-assignments.md). Templates do not create trainee execution records.

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

## Coach authoring workspace

Open **Programming → Templates** to filter active or archived templates by publication state,
goal, and name. The builder edits metadata and an ordered Warm-up, Main, and Cool-down graph.
Its exercise picker includes only published, active system exercises and the current coach's
published private exercises. Each set editor reveals only fields valid for the exercise's
tracking mode and shows the canonical kilogram conversion when a load is entered in pounds.

Saving replaces the complete draft graph and includes its expected revision. If another tab
wins the revision race, the conflict dialog preserves local changes until the coach explicitly
reloads the server draft. Publishing requires a review confirmation and locks the published
graph; subsequent editing starts with **Create revision**. The trainee preview shows exactly
the content a trainee schedule may consume and deliberately excludes coach notes. Assignment
materializes exact versions into scheduled workouts. Starting one creates a separate immutable
execution snapshot; later template revisions do not alter its session or set logs. See
[Workout execution](workout-execution.md).

Program references never follow a template root's current version. Publishing a newer template
therefore does not rewrite existing program history. Archived template roots remain readable
through already-published programs but cannot be added to a new or replacement program draft.
