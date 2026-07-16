# Training program authoring

A Program is a reusable, coach-owned multi-week training structure. A Program week is one fixed
Monday–Sunday week, and a workout slot is one planned workout occurrence inside that definition.
Published Program versions can be assigned and materialized as date-only trainee schedules.
Trainees cannot execute those workouts yet.

## Structure and v1 limits

Programs support 1–12 weeks, at most 14 workout slots per week, and at most 168 slots in total.
Every duration value produces exactly one contiguous `ProgramWeek` for each week number. An empty
weekday represents rest and does not create a fake workout record. A weekday can contain multiple
slots with an explicit contiguous order, and each slot is visibly Required or Optional.

Program definitions are timezone-neutral. Assignment converts their Monday–Sunday structure to
date-only scheduled workouts using the trainee profile timezone.

Goal tags reuse the existing goal vocabulary as coach-facing context. They do not generate,
select, or assign a program.

## Exact workout-version pinning

Every slot references one exact immutable published `WorkoutTemplateVersion`, never a template
root's current version. Publishing a newer template does not change an existing program. Coaches
may add only their own published templates whose roots remain active. An archived template can
remain visible through historical published programs but is unavailable for new draft content.

Optional slot overrides can replace the template's planned duration or target session RPE for
that occurrence. Coach notes remain private; trainee instructions appear in the preview.

## Draft, publication, and revision

`TrainingProgram` is the stable coach-owned root. It has at most one mutable draft and any number
of immutable published `TrainingProgramVersion` graphs. Draft saves replace the complete metadata,
week, and workout-slot graph. The client sends `expected_draft_revision`; a stale save returns
HTTP 409 and leaves both the newer server graph and the browser's local input intact.

Publication validates the complete graph, ownership and eligibility of every template version,
week coverage, weekday/order rules, and product limits. It then computes a deterministic SHA-256
hash over the canonical metadata, weeks, exact template-version IDs, ordering, required state,
overrides, and authored instructions. Timestamps, database child IDs, and draft revision counters
are excluded. The resulting published graph cannot be edited or returned to draft. Repeated
publication without a newer draft returns the current published version rather than duplicating it.

**Create revision** clones the latest published graph into a new mutable draft. **Archive** removes
the root from future active selection without deleting its versions or children.

## Coach builder and trainee preview

Open **Programming → Programs** to search and filter active or archived roots by publication state,
goal, and name. The builder provides explicit save state, 1–12 week duration control, week labels,
Monday–Sunday sections, accessible up/down ordering, per-slot context, publication review, revision,
and archive confirmation. On smaller screens the builder uses week disclosures, vertical weekday
sections, and separate Builder/Trainee preview controls.

The trainee preview shows program name, duration, goals, trainee instructions, week layout,
workout names, effective duration/RPE, Required/Optional status, and deload labels. It excludes all
coach notes and keeps technical publication details secondary.

## Coach-authored deloads

`is_deload` is an explicit coach-authored week flag. The builder and trainee preview say so
directly. The platform never creates a deload, reduces load or volume, chooses replacement
templates, or edits the program automatically. The coach remains responsible for selecting
appropriate workout content and overrides.

## Authorization and demo behavior

All endpoints require the coach role and scope roots to the authenticated owner; another coach's
identifier returns HTTP 404. Every create, draft-save, publish, revision, and archive endpoint also
enforces the backend demo read-only guard. Demo coaches can inspect deterministic synthetic
programs, while every mutation returns HTTP 403 and the interface disables its mutation controls.

See [Program assignment and scheduling](training-assignments.md) for effective dates, version
pinning, future replacement, and the read-only trainee calendar.
