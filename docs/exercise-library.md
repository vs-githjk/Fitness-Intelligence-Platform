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
groups, unilateral context, safety cues, and richer instructional knowledge —
difficulty (`beginner`/`intermediate`/`advanced`), coaching cues, and common
mistakes. All knowledge is instructional and self-declared; none of it is medical
advice. The legacy optional HTTPS `image_url`/`thumbnail_url` fields are retained for
compatibility but are superseded by authored media (below).

## Exercise knowledge and media

Each version can carry authored media that reuses the platform media subsystem
(`MediaAsset` + `MediaService`) — there is no second upload pipeline. A version
references at most a **primary image**, an optional **secondary image**, and one
optional **demonstration video** (`ExerciseVersion.primary_image_media_id`,
`secondary_image_media_id`, `demonstration_video_media_id`, each a SET NULL FK to an
ACTIVE asset). Images accept JPEG/PNG/WEBP/GIF (≤5 MB); video accepts MP4/WEBM
(≤25 MB) with magic-byte signature validation. No transcoding, streaming protocol,
thumbnail generation, or external/YouTube embedding is performed — a file is stored
as-is and delivered through the same authorized route as images.

Media is authored **only on the editable draft**, so published versions stay
byte-for-byte immutable. Because a revision copies its parent's media references, an
asset shared by more than one version is never retired while any version still points
at it: replacing marks the detached asset `REPLACED`, removing soft-deletes it, but
only once it is truly orphaned. Media is part of the version content hash.

System (starter-library) exercises may carry demonstration media too; coaches see it
read-only. Delivery is authorized: `GET /api/v1/coach/exercises/{id}/media/{media_id}/content`
streams to any coach who can see the exercise, and returns `404` otherwise (unknown,
cross-coach, or a media id not belonging to that exercise). Trainee-facing exercise
media in the workout runner is a deferred follow-up (see
[deferred-features.md](deferred-features.md)).

## Coach API

All routes use `/api/v1/coach/exercises` and require the coach role.

- `GET /api/v1/coach/exercises`
- `POST /api/v1/coach/exercises`
- `GET /api/v1/coach/exercises/{exercise_id}`
- `PUT /api/v1/coach/exercises/{exercise_id}/draft`
- `POST /api/v1/coach/exercises/{exercise_id}/publish`
- `POST /api/v1/coach/exercises/{exercise_id}/revisions`
- `POST /api/v1/coach/exercises/{exercise_id}/archive`
- `PUT /api/v1/coach/exercises/{exercise_id}/media/{slot}` — upload/replace draft media
- `DELETE /api/v1/coach/exercises/{exercise_id}/media/{slot}` — remove draft media
- `GET /api/v1/coach/exercises/{exercise_id}/media/{media_id}/content` — authorized delivery

`{slot}` is `primary_image`, `secondary_image`, or `demonstration_video`. Media
mutations require an editable draft the coach owns (system exercises return
`system_exercise_read_only`; a published-only exercise returns `exercise_draft_missing`
until a revision is opened). List requests may filter by scope or exact tracking mode,
search names/slugs, and explicitly include archived owner-private history. Every
mutation rejects demo identities in the backend.

## Coach workspace

Open **Programming → Exercises** to browse published system exercises and coach-private
content. The library supports ownership, active/archive, tracking-mode, category, movement,
equipment, and text filters with bounded client-side pagination. System cards are always
read-only. A coach can create a private draft, save it explicitly, publish it after reviewing
the confirmation, create a revision from an immutable published version, or archive the root.

The editor preserves unsaved entries after validation or network failures and warns before
leaving a dirty form. Beyond the metadata fields it edits difficulty, coaching cues, and
common mistakes, and — on an editable draft — uploads/replaces/removes a primary image, an
optional secondary image, and a demonstration video with client-side type/size validation and
a live preview. A read-only **Preview** panel renders the image, video player, knowledge, and
safety notes with explicit loading, empty, and "media unavailable" states. Authorized media is
fetched as a blob and rendered through an object URL (a bare `<img>`/`<video>` src cannot carry
the bearer token). Demo coaches can browse the same synthetic library, but every mutation
control is disabled and the backend read-only guard remains authoritative.
