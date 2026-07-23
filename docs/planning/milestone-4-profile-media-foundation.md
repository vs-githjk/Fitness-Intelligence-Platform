# Milestone 4 — Profile and Media Foundation (planning)

**Status: planning document; later phases not yet approved.** This document defines
scope and open questions so each approved phase can begin from a shared
understanding. It does not authorize unapproved code. Nothing here overrides
[../product-principles.md](../product-principles.md) or the
[decision log](../decisions/README.md).

## Delivery status

- **Phase 1 — Identity Foundation: complete.** Shared `UserProfile`/`UserPreferences`,
  `GET/PUT /api/v1/me/{profile,preferences}`, Profile and Settings pages. See ADR-0012.
- **Phase 2 — Media Infrastructure: complete.** Provider-independent `MediaAsset` +
  `MediaService` + `StorageProvider` (local), authorized upload/metadata/content/soft-
  delete, and reusable frontend media client infrastructure (no media UI exposed).
  Also resolved the P2 Assignments empty-state (ADR-0015). See ADR-0013/0014.
- **Phase 3 and later (avatars, exercise media, coach/trainee media integration):**
  **not approved.** Do not implement without an explicit approved decision.

### Related bounded enhancement (not a media phase)

- **Curated Workout Starter Library: complete.** A read-only, system-owned starter
  library with clone-to-edit, reusing the existing programming/publishing/assignment
  model. It is independent of the Profile/Media milestone. See ADR-0016 and
  [../programming-starter-library.md](../programming-starter-library.md). This did not
  begin any avatar/profile-media work.

## Problem statement

Coaches and trainees currently have no profile surface: no preferred display name,
no unit or timezone preference, and no way to attach identifying or instructional
media. Units and timezones are handled implicitly, and exercises have no visual
instruction. This limits usability and clarity, especially on mobile and for
newer trainees.

## Goals

- Give coaches and trainees a profile page with a preferred display name and basic
  profile metadata.
- Let each user set a display unit preference (e.g. kg/lb) and a timezone
  preference, applied consistently and explainably.
- Allow an optional profile photo through a secure upload/storage abstraction.
- Allow exercise instruction images and external exercise video links, authored by
  the owning coach and shown during programming/execution.
- Provide deterministic demo profile/media examples.

## Non-goals

Out of scope for Milestone 4 (see [../deferred-features.md](../deferred-features.md)):

- Direct workout-video uploads.
- Social feed, messaging, or notifications.
- AI image analysis, body-composition photo analysis, or meal-photo analysis.
- Credential verification.
- Wearable integrations and Nutrition Intelligence.
- Adaptive progression.

## Proposed domain model (draft)

- **UserProfile** (per user): preferred display name, optional bio/metadata, unit
  preference, timezone preference, optional profile-photo reference. Distinct from
  auth identity.
- **CoachProfileMetadata**: coach-specific public-to-assigned-trainees fields (e.g.
  display name, short description) — bounded, non-sensitive.
- **TraineePreferences**: trainee-specific display preferences (units, timezone,
  and any UI preferences), separate from health/onboarding data.
- **MediaAsset**: an abstraction over a stored file (profile photo, exercise
  instruction image) — owner, kind, storage key, content type, size, created-at,
  and soft-delete/lifecycle state. Never stores the binary in the primary DB row.
- **ExerciseInstructionMedia**: association of a MediaAsset (image) and/or an
  external video link to an ExerciseVersion, authored by the owning coach.

Open: whether media is versioned with the ExerciseVersion (immutability) or
attached to the Exercise root; see unresolved questions.

## Authorization

- A user may read/update only their own profile and preferences.
- A coach's profile metadata is visible to their assigned trainees (read-only);
  trainees do not edit coach profiles and vice versa.
- Media is owner-scoped: only the owning coach manages exercise instruction media;
  only the owning user manages their profile photo.
- All media reads go through authorized, ownership-checked endpoints or
  time-limited signed URLs — never public-by-default object storage.
- Demo accounts may view seeded profile/media examples but cannot mutate them
  (add every new mutation to the demo inventory).

## Privacy

- Profile photos and any free-text metadata are user-provided and unverified;
  never present them as verified identity.
- Collect only what the feature needs; keep bios bounded and non-sensitive.
- Strip EXIF/location metadata from uploaded images; validate content type and
  size server-side.
- External video links are user-provided; validate scheme/host and treat as
  untrusted (no autoplay of arbitrary embeds; prefer link-out or sandboxed embed).
- Deletion removes the media reference and schedules storage cleanup; document the
  retention/cleanup window.

## Storage architecture

- Introduce a storage abstraction (interface) with a local/dev implementation and
  a hosted object-storage implementation, so application code never hard-codes a
  provider.
- The primary database stores only metadata and a storage key, never binaries.
- Access via short-lived signed URLs or an authorized proxy endpoint; no
  public buckets.
- Enforce max size, allowed content types, and per-user quotas.

## Profile-photo lifecycle

Upload (validate type/size, strip metadata) → store → reference on UserProfile →
serve via authorized/signed access → replace (supersede prior asset) → delete
(remove reference, schedule storage cleanup). A user always has an accessible
default/placeholder when no photo is set.

## External media-link lifecycle

Add (validate scheme/host) → associate with the ExerciseVersion/root → display as
an authorized outbound link or sandboxed embed → edit/remove. Links are validated
but not fetched/scraped server-side by default.

## Exercise instruction media

- Owning coach attaches image asset(s) and/or an external video link to an
  exercise.
- Shown in the programming workspace and in trainee execution where helpful,
  responsively and with accessible alternatives.
- Decide versioning behavior (unresolved questions) to preserve immutability
  guarantees.

## Coach-profile metadata

Bounded fields (display name, short description) visible to assigned trainees;
non-sensitive; no contact details that would imply out-of-band or monitored
support.

## Trainee preferences

Display-only preferences (units, timezone, UI options) stored separately from
health/onboarding data; changing a display unit must not alter stored canonical
values, only presentation, with clear provenance.

## Units and timezone preferences

- Continue storing canonical values (e.g. loads in canonical kg, dates as explicit
  local dates); preferences affect display and input assistance only.
- A unit preference never rewrites historical stored values; conversions are
  presentation-time and reversible.
- Timezone preference clarifies local-date behavior already used by daily/workout
  scheduling; it must not retroactively reinterpret stored local dates.

## Accessibility

- Profile forms and media controls fully keyboard-operable with visible focus and
  labels.
- Every image has a meaningful text alternative; instruction media is not the sole
  carrier of essential information.
- Responsive at 320/390/768/desktop with no horizontal overflow; media scales
  within its container.

## Demo behavior

- Deterministic seed adds synthetic profile metadata, a placeholder/synthetic
  profile photo, and example exercise instruction media (image + external link)
  for demo identities.
- All demo profile/media mutations return `403 demo_read_only`.

## Migration expectations

- New tables for profile/preferences/media and an association for exercise
  instruction media; all additive, append-only, dual-path (SQLite batch +
  PostgreSQL), following existing naming conventions after the current head.
- No changes to existing historical migrations; new columns nullable where added
  to existing tables.

## API surface (draft)

- `GET/PUT /api/v1/me/profile` and `GET/PUT /api/v1/me/preferences`.
- Profile-photo upload/replace/delete endpoints (authorized, demo-protected).
- Coach exercise instruction media endpoints (owner-scoped, demo-protected).
- Read endpoints for a coach's public profile metadata to assigned trainees.
- Media access via signed URL or authorized proxy. Every mutation is
  demo-protected and inventory-listed.

## Frontend areas

- New profile and preferences pages for both roles; entry point in AppShell/nav.
- Media upload/preview components with accessible states (loading/empty/error).
- Exercise instruction media display in programming and execution surfaces.
- Identity-scoped React Query keys for all new reads.

## Testing strategy

- Backend: unit tests for storage abstraction, validation (type/size/metadata
  stripping, link validation), authorization (owner-only, coach/trainee
  visibility, cross-account `404`), and demo-mutation-inventory coverage.
- Frontend: component tests for profile/preferences forms and media components;
  unit-preference presentation without mutating canonical values.
- Playwright: profile edit, unit/timezone preference, profile-photo upload/replace/
  delete, exercise instruction media authoring/display, demo read-only denial, and
  mobile layouts.
- Migration cycle and idempotent demo reseed validated on SQLite and PostgreSQL.

## Rollout strategy

- Additive migration; feature can ship behind a clear, reviewed scope.
- Follow the [release runbook](../operations/release-runbook.md): full gates,
  isolated Playwright, version bump, release notes, single commit, deploy order,
  hosted verification, tag after verification.

## Unresolved questions

- Is exercise instruction media pinned to an ExerciseVersion (preserving
  immutability) or attached to the Exercise root (mutable presentation)? How does
  that interact with programs that pinned an earlier version?
- Which hosted object-storage provider, and what signed-URL lifetime and quota
  limits?
- Sandboxed embed vs. link-out for external video, and the allowed host list.
- Retention/cleanup window for deleted media, and whether hard-delete or
  soft-delete is the default.
- Do timezone preferences change any existing scheduling behavior, or only display?

## Acceptance criteria

- Both roles can view/edit their profile and preferences; changes are
  identity-scoped and authorized.
- Unit and timezone preferences change presentation only; canonical stored values
  are unchanged and provenance is clear.
- Optional profile photo can be uploaded, replaced, and deleted through the secure
  storage abstraction; no public bucket access.
- Coaches can attach exercise instruction images and external video links, shown
  accessibly to assigned trainees; ownership is enforced.
- All new mutations are demo-protected and inventory-listed; demo shows
  deterministic examples and denies mutations.
- Accessibility and responsive checks pass; migrations are additive and validated;
  the full release gate passes before any deploy.
