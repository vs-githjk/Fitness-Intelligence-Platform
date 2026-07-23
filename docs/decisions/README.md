# Decision log

Lightweight record of major accepted product and platform contracts for FitIntel
360. These are the durable decisions that constrain future work; they are
implemented in the code and detailed in the linked documents. Do not rewrite
historical facts — supersede a decision with a new dated entry rather than editing
an accepted one.

## How to add a decision

Copy the template below, give it the next number, and fill it in. Keep it short —
one screen. Link to the authoritative doc or code rather than duplicating detail.

```
## ADR-NNNN — <title>

- **Status:** proposed | accepted | superseded (by ADR-XXXX)
- **Date:** YYYY-MM-DD
- **Context:** why this decision was needed.
- **Decision:** what was decided.
- **Consequences:** what this enables/constrains; follow-ups.
- **Alternatives considered:** options rejected and why.
```

Status values: **proposed** (under discussion), **accepted** (in force),
**superseded** (replaced — link the successor).

---

## Accepted contracts

The following contracts are **accepted** and in force as of v0.5.0. Each links to
its authoritative documentation.

## ADR-0001 — Deterministic, versioned scoring

- **Status:** accepted
- **Date:** 2026-07-20 (contract in force since the Health Index milestone)
- **Context:** coaching decisions require reproducible, explainable numbers, not
  opaque model output.
- **Decision:** all scores and analytics are deterministic functions of persisted
  inputs, each carrying a version string and a document; formula changes create a
  new version rather than editing an existing one; missing data is explicit.
- **Consequences:** enables auditability and provenance; requires a new versioned
  calculation + doc for any formula change. See
  [../scoring/health-index-v1.md](../scoring/health-index-v1.md),
  [../scoring/daily-intelligence-v1.md](../scoring/daily-intelligence-v1.md).
- **Alternatives considered:** heuristic/ML scoring — rejected for lack of
  explainability and safety risk.

## ADR-0002 — Versioned, immutable Programs and Templates

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** coaches iterate on exercises/templates/programs, but downstream
  schedules must remain stable.
- **Decision:** published Exercise/WorkoutTemplate/Program versions are immutable;
  new versions are created rather than edited; references pin exact versions.
- **Consequences:** publishing a newer version never mutates existing programs,
  schedules, or history. See [../training-programs.md](../training-programs.md),
  [../workout-templates.md](../workout-templates.md).
- **Alternatives considered:** mutable content — rejected as it would silently
  rewrite assigned work.

## ADR-0003 — Immutable historical execution

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** execution history must be trustworthy.
- **Decision:** terminal WorkoutSessions and their prescription snapshots are
  immutable through the API; revision-checked writes prevent stale overwrites.
- **Consequences:** no in-place edits to completed work; post-completion
  correction is deferred (ADR-0010 register). See
  [../workout-execution.md](../workout-execution.md).
- **Alternatives considered:** editable history — rejected for integrity.

## ADR-0004 — One active primary Program per trainee

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** trainees need a single unambiguous current plan.
- **Decision:** a trainee has one current (active) ProgramAssignment plus at most
  one scheduled future assignment; future assignments supersede rather than
  overlap.
- **Consequences:** unambiguous scheduling; supersession is explicit. See
  [../training-assignments.md](../training-assignments.md).
- **Alternatives considered:** multiple concurrent programs — rejected as
  ambiguous for scheduling and analytics.

## ADR-0005 — Explicit whole-workout skipping

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** a trainee needs a first-class way to decline a scheduled workout
  before starting, distinct from simply not doing it.
- **Decision:** a trainee-only, demo-protected `POST
  /api/v1/trainee/workouts/{id}/skip` records an ordinary or safety (wellbeing)
  skip with a bounded reason; a skip creates no WorkoutSession and no safety
  report.
- **Consequences:** "skipped" comes only from an explicit skip; enables accurate
  adherence. See [../workout-execution.md](../workout-execution.md) and
  [../workout-adherence.md](../workout-adherence.md).
- **Alternatives considered:** inferring skips from inactivity — rejected as
  ambiguous and destructive.

## ADR-0006 — Workout load analytics (`workout-load-v1`)

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** coaches and trainees benefit from deterministic training-load and
  adherence views.
- **Decision:** an isolated, pure analytics engine computes planned/completed
  session load, resistance volume, weekly load, and adherence, versioned
  `workout-load-v1`, read-only, never mutating training data or drawing medical
  conclusions.
- **Consequences:** analytics are reproducible bookkeeping, not a medical measure.
  See [../scoring/workout-load-v1.md](../scoring/workout-load-v1.md).
- **Alternatives considered:** coupling analytics into execution services —
  rejected to keep calculations pure and independent from daily scoring.

## ADR-0007 — Adherence classification rules

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** consistent, non-destructive workout status semantics.
- **Decision:** classification is derived at read time; `partial` = started then
  ended incomplete or safety-ended (even with zero sets); `skipped` = explicit
  skip only; `missed` = no session/skip past a two-local-day grace; eligible
  denominator excludes cancelled/superseded/optional; safety skips are counted but
  reported separately.
- **Consequences:** absence of logged sets never downgrades a started session to
  skipped. See [../workout-adherence.md](../workout-adherence.md).
- **Alternatives considered:** treating zero-set sessions as skipped — rejected as
  misleading.

## ADR-0008 — All-history Recorded best

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** "best" must be well-defined and honest.
- **Decision:** a recorded best is the best recorded compatible completed
  performance across a trainee's available completed history (scope
  `all_available_history`), not a bounded window and not a lifetime/all-time/PR
  claim.
- **Consequences:** wording avoids PR/personal-record/lifetime. See
  [../recorded-bests.md](../recorded-bests.md).
- **Alternatives considered:** a bounded reporting window — rejected as it would
  hide earlier bests and mislead.

## ADR-0009 — Safety-reporting boundaries

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** safety features must not imply monitored/urgent care.
- **Decision:** trainee safety reports are immutable and coach
  acknowledgement/resolution is append-only; reports are reviewed asynchronously
  and are not continuously monitored; a wellbeing skip is not a safety report.
- **Consequences:** copy must avoid monitoring/emergency implications. See
  [../workout-safety.md](../workout-safety.md).
- **Alternatives considered:** presenting safety review as real-time monitoring —
  rejected as unsafe and untrue.

## ADR-0010 — Readiness-context immutability

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** readiness shown during execution must be a stable record.
- **Decision:** at workout start the app captures an immutable copy of an eligible
  Daily Score snapshot (or explicit unavailability); readiness cannot mutate Daily
  Intelligence or workout content and provides no medical clearance.
- **Consequences:** readiness is contextual information only. See
  [../workout-readiness-context.md](../workout-readiness-context.md).
- **Alternatives considered:** live-recomputing readiness — rejected; a captured
  record must not change after the fact.

## ADR-0011 — Demo read-only behavior

- **Status:** accepted
- **Date:** 2026-07-20
- **Context:** a public demo must be safe and non-destructive.
- **Decision:** demo identities are synthetic and read-only; a shared backend guard
  returns `403 demo_read_only` for every mutation, and a central route-inventory
  test enforces coverage for new mutations.
- **Consequences:** every new mutation must be added to the demo inventory. See
  [../demo.md](../demo.md) and [../security.md](../security.md).
- **Alternatives considered:** frontend-only demo restrictions — rejected; the
  browser is not the security boundary.

## ADR-0012 — Shared identity and preferences layer

- **Status:** accepted
- **Date:** 2026-07-21
- **Context:** Milestone 4 needs a role-agnostic identity foundation that future
  work (media, nutrition, wearables, reports) can reuse without redesign, without
  disturbing the existing role-specific profiles or daily/workout behavior.
- **Decision:** add one-to-one `UserProfile` (preferred display name, bio) and
  `UserPreferences` (timezone, weight/distance units, locale, and
  theme/privacy/accessibility placeholders) records with
  `GET/PUT /api/v1/me/{profile,preferences}` scoped to the authenticated user.
  `CoachProfile`/`TraineeProfile` are unchanged. `UserPreferences.timezone` is the
  canonical timezone and is kept in sync with the retained `TraineeProfile.timezone`
  for backward compatibility; preferences change presentation only.
- **Consequences:** an additive migration backfills existing users; new mutations
  are demo-protected and inventory-listed (`IDENTITY_DEMO_MUTATIONS`); values are
  self-declared and never verified. This is the base for later Milestone 4 slices
  (avatars, media). See [../architecture.md](../architecture.md) and
  [../planning/milestone-4-profile-media-foundation.md](../planning/milestone-4-profile-media-foundation.md).
- **Alternatives considered:** extending `CoachProfile`/`TraineeProfile` in place —
  rejected as it would duplicate cross-role fields and couple identity to role;
  making preferences timezone the only source — rejected to avoid changing
  daily/workout local-date behavior in this phase.

## ADR-0013 — Provider-independent media storage with authorized delivery

- **Status:** accepted
- **Date:** 2026-07-21
- **Context:** Later Milestone 4 work (avatars, exercise media) and future features
  (nutrition images, reports) need to store binary files. Coupling the app to a
  specific backend (local disk, S3, R2, Azure) or to public static URLs would be
  hard to change and hard to secure.
- **Decision:** introduce a provider-independent media subsystem —
  `routes → MediaService → StorageProvider protocol → provider implementation`.
  Only provider implementation modules may import provider SDKs. `MediaAsset` stores
  metadata only (never bytes) with an opaque, server-generated `storage_key` that is
  never exposed through the API. Delivery is always authorized: content is streamed
  through `GET /api/v1/media/{id}/content` after an ownership check; the local
  storage root is never mounted as a public static route and no guessable permanent
  URLs are issued. A `LocalStorageProvider` is fully implemented; a factory fails
  fast for unimplemented providers.
- **Consequences:** the app never depends on a cloud SDK; cloud providers (S3/R2 as
  S3-compatible, Azure) are reserved and rejected until implemented. Uploads validate
  size, a MIME allowlist, and magic-byte signatures, generate SHA-256 checksums, and
  sanitize filenames. Cross-account access returns `404`; mutations are demo-protected
  (`MEDIA_DEMO_MUTATIONS`). See [../architecture.md](../architecture.md).
- **Alternatives considered:** mounting local media as `StaticFiles` — rejected as it
  bypasses authorization and leaks storage layout; signed local URLs — deferred in
  favor of the simpler, fully-authorized streaming route.

## ADR-0014 — Media lifecycle, image-validation posture, and local-vs-hosted policy

- **Status:** accepted
- **Date:** 2026-07-21
- **Context:** Media needs a safe lifecycle, an honest statement of what validation
  does and does not guarantee, and a rule for where bytes may live in each
  environment. Render's filesystem is ephemeral, so local storage is unsafe for
  durable production media.
- **Decision:**
  - **Lifecycle:** `active → replaced → soft_deleted → purged`, enforced by the
    service. A user-facing delete is a **soft delete** (bytes retained); physical
    removal happens only via a service-level **purge** from `soft_deleted`. No
    admin purge endpoint is exposed in this phase.
  - **Image validation (Option B — narrower):** validate magic-byte signatures for a
    small raster allowlist (JPEG/PNG/WEBP/GIF) and reject SVG and scriptable formats.
    **Do not** introduce Pillow yet; server-side EXIF stripping and thumbnail
    generation are explicitly deferred to a later hardening/profile-media phase.
    Signature + MIME checks do not make a file "safe"; there is **no** malware
    scanning.
  - **Local-vs-hosted:** `local` is the only runtime-selectable provider. Production
    startup **rejects** local media (ephemeral filesystem); staging may keep local
    media because it is synthetic, disposable, and no media feature is user-exposed
    yet. Phase 2 is locally complete and must not be deployed with local media on
    ephemeral infrastructure once media-consuming features ship.
- **Consequences:** deletes are reversible until purge; retention/cleanup jobs can
  reclaim storage later; the validation limits are documented in
  [../security.md](../security.md) and must not be overstated. Enabling a
  media-consuming feature in production requires configuring a durable provider first.
- **Alternatives considered:** hard delete on the API — rejected (irreversible, loses
  audit trail); Pillow decode/normalize/EXIF-strip now — deferred to avoid a
  dependency used only speculatively; failing staging on local media — rejected to
  avoid breaking active synthetic testing.

## ADR-0015 — Assignment empty-state clarifies the publish chain (P2)

- **Status:** accepted
- **Date:** 2026-07-21
- **Context:** Real-user testing surfaced a P2 usability issue: the Assignments page
  showed an empty "Published Program version" selector when a coach had no published
  programs (for example, after creating only an Exercise). The behavior was correct —
  only a published Program can be assigned — but looked broken.
- **Decision:** distinguish loading, error, and two empty states — no Programs exist
  vs. Programs exist but none are published — and explain the
  `Exercise → Workout Template → Program → Assignment` chain with a link to
  Programming. This is presentation only. Assignment business rules (publishing,
  version eligibility, preview, effective dates, active-program replacement) are
  unchanged.
- **Consequences:** the empty selector is no longer mistaken for a failure; loading is
  not shown as empty and API errors are not shown as "no programs". Recorded as a
  resolved P2 usability finding, not a business-logic change. See
  [../testing/feedback-triage.md](../testing/feedback-triage.md).

## ADR-0016 — Curated starter library: system-owned, read-only, clone-to-edit

- **Status:** accepted
- **Date:** 2026-07-23
- **Context:** A new coach must build every Exercise, Template, and Program before
  assigning anything. A curated starter library lowers that setup cost, but shared
  starter content must never be editable, deletable, or directly assignable by a
  coach, and it must reuse the existing programming/publishing/assignment model
  rather than adding a parallel one.
- **Decision:**
  - **System ownership.** Starter Templates and Programs are owned by a single
    non-login `is_system` account; starter Exercises keep the existing
    `scope = system` model. Each table therefore keeps its *established* ownership
    model (Exercise: nullable-owner + scope; Template/Program: non-nullable owner),
    and existing owner-scoping makes system content read-only automatically (a
    coach's `get_owned(...)` returns nothing → `404`) and keeps it out of the
    assignment selector (a coach can only assign programs they own).
  - **Clone-to-edit.** The one mutation, `POST /api/v1/program-library/{id}/clone`,
    transactionally creates an independent coach-owned **draft** Program. It
    duplicates each referenced system Template into a coach-owned **published**
    Template and references the read-only system Exercise versions directly (coach
    content may reference system exercise versions). The source is never modified;
    the copy never re-syncs. Nothing is published or assigned automatically — the
    coach reviews, publishes, then assigns via the existing workflow.
  - **Attribution.** `training_programs.cloned_from_program_id` and
    `workout_templates.cloned_from_template_id` (nullable, self-referential) record
    the snapshot source for a "Based on Starter Library" label and audit; they never
    imply synchronization.
  - **Seeding.** An idempotent operator command (`python -m scripts.seed_library`)
    installs/updates the library through the normal application services, so seeded
    content passes exactly the same validation as coach-created content. Content is
    keyed by stable seed keys and by name-within-the-system-account. Revisions add a
    new item rather than mutating a published version, so existing coach copies stay
    independent.
- **Consequences:** no parallel programming model; no schema relaxation on tables
  holding real coach data (only additive `users.is_system` + two nullable attribution
  columns); clone is demo-protected (`LIBRARY_DEMO_MUTATIONS`); the library is not a
  marketplace or shared coach library and has no sync engine. See
  [../architecture.md](../architecture.md) and
  [../programming-starter-library.md](../programming-starter-library.md).
- **Alternatives considered:** generalizing `scope` onto Template/Program tables —
  rejected as it would relax `NOT NULL`/constraints on tables holding real coach
  programs and complicate program validation (system programs referencing system
  templates); a coach-to-coach sharing marketplace — out of scope and explicitly
  deferred.
