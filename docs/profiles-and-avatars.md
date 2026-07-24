# Profiles and avatars

FitIntel 360 exposes a polished, user-facing profile experience built directly on
the existing identity (`UserProfile`/`UserPreferences`) and media (`MediaAsset`)
infrastructure. This phase adds no new storage subsystem and no second upload
pipeline — it surfaces what already exists through role-aware pages and a single,
consistent avatar used across the product.

Profiles are **self-declared and never verified**. There is no credential
verification, document upload, license validation, public profile, profile search,
or social graph. Those are explicitly out of scope (see
[deferred-features.md](deferred-features.md)).

## The profile record

Professional and personal fields live on the shared, role-agnostic `UserProfile`
row (one-to-one with `User`), alongside the existing `preferred_display_name` and
`bio`. Migration `20260724_0016` adds them, all nullable and additive:

| Field | Surfaced for | Notes |
| --- | --- | --- |
| `preferred_display_name` | both | Falls back to the account name when empty. |
| `bio` | both | Coaching philosophy for coaches; a short bio for trainees. |
| `headline` | coach | Short professional tagline. |
| `coaching_specialties` | coach | List of short labels; trimmed and de-duplicated. |
| `years_of_experience` | coach | Whole number, 0–80. |
| `certifications_text` | coach | **Plain text only.** Not parsed, not verified. |
| `training_goals` | trainee | Helps the coach tailor programming. |
| `avatar_media_id` | both | FK to the current ACTIVE avatar `MediaAsset` (SET NULL). |

The legacy `CoachProfile`/`TraineeProfile` records are untouched. The UI renders the
role-appropriate subset; the server accepts the union and applies the fields that
are sent.

## Avatars on top of the media subsystem

Avatars reuse `MediaService` verbatim — the same validation (JPEG/PNG/WEBP/GIF,
5&nbsp;MB cap, magic-byte signature), SHA-256 checksum, opaque server-generated
storage key, and lifecycle (`active → replaced → soft_deleted → purged`). No storage
keys are ever exposed.

Self-service endpoints (all demo-protected, in `IDENTITY_DEMO_MUTATIONS`):

- `GET /api/v1/me/avatar` — current avatar metadata, or `null`.
- `PUT /api/v1/me/avatar` — upload (multipart `file`). If a current avatar exists it
  is marked `REPLACED` and linked (`replaced_by_media_id`) before the profile pointer
  moves — bytes are written before the old row is transitioned, so a mid-flight
  failure never leaves the owner without a usable photo, and media is never orphaned.
- `DELETE /api/v1/me/avatar` — clears the profile reference and soft-deletes the
  asset. Idempotent; bytes are retained until an explicit purge.

The current avatar is also embedded in `GET /api/v1/me/profile` (`avatar` field) so
the profile page and the app shell load it in one request.

## Authorized, relationship-scoped delivery

Avatar images require the bearer token, so a bare `<img src>` cannot load them. The
frontend fetches the blob through an authorized route and renders it via an object
URL (`apiBlob` → `Avatar` component), falling back to initials on any 404.

Two delivery routes exist, deliberately:

- **Owner-only** `GET /api/v1/media/{id}/content` (unchanged from Phase 2). Used for
  a user's own avatar via its `content_url`.
- **Relationship-scoped** `GET /api/v1/users/{user_id}/avatar/content`. Streams a
  *related* user's avatar — the viewer themselves, or either side of an **active**
  `CoachTraineeAssignment`. Every other target is a plain `404`, indistinguishable
  from "no photo". This keeps the generic media route owner-only while letting a
  coach render an assigned trainee's photo (and vice versa) without gaining access to
  the media resource itself. `GET /api/v1/users/{user_id}/profile` returns the same
  relationship-scoped profile card.

To avoid a burst of 404s when rendering lists, the roster
(`CoachTraineeSummary.avatar_url`), the trainee-detail payload, and the trainee's
coach view (`TraineeCoachOut.coach_avatar_url`) carry the delivery URL directly —
`null` when no photo is set, so the client shows initials without a request.

Avatars are stored `PRIVATE`; the identity layer's relationship check — not the
stored visibility flag — is the delivery authority. See
[decisions/README.md](decisions/README.md) ADR-0017.

## Where avatars appear

One shared `Avatar` component (initials fallback, deterministic styling) is used in
the app shell (sidebar + mobile header), the coach dashboard alerts and roster, the
trainee-detail header, the assignment trainee selector, the trainee's "Your coach"
cards, and the profile page. Programming ownership is shown as scope badges
(System / Private), not as a person, so no avatar is attached there.

## What each role can do

- **Coaches** maintain a professional profile — photo, headline, coaching
  philosophy, specialties, years of experience, and plain-text certifications —
  with no administrator approval. Assigned trainees see it on their Today page.
- **Trainees** upload a photo, set a display name and bio, and describe their
  training goals. Their assigned coach can see their profile and photo.
