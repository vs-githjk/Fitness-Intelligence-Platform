# Curated starter library

The starter library is a small, curated set of read-only, system-owned Programs (with
their Templates and Exercises) that coaches can browse and **clone** into their own
editable drafts. It reuses the existing programming, publishing, versioning, and
assignment model — there is no parallel content model. See ADR-0016.

## Ownership

- Starter **Exercises** use the existing `Exercise.scope = system` model (nullable
  owner), so they are visible to every coach and referable by coach content.
- Starter **Templates and Programs** are owned by a single non-login account marked
  `User.is_system = true` (a `coach`-role account that cannot log in). Because the
  existing services scope every read/write by owner, system content is:
  - **browse-only** through the dedicated library endpoints,
  - **read-only** to coaches (a coach's `get_owned(...)` never returns it → `404`),
  - **never directly assignable** (a coach can only assign programs they own, so
    system programs never appear in the assignment selector).

This keeps each table on its *established* ownership model rather than adding a new
one: Exercises already use nullable-owner + scope; Templates/Programs already use a
required owner.

## Clone-to-edit

`POST /api/v1/program-library/{program_id}/clone` (coach-only, demo-protected,
transactional) creates an **independent coach-owned draft**:

```
system Program version
    → new coach-owned draft Program (cloned_from_program_id set)
        → for each referenced system Template: a new coach-owned PUBLISHED Template
          (cloned_from_template_id set), copying sets/targets/ordering exactly
        → system Exercise versions are referenced directly (not duplicated)
```

- The source is never modified; the copy never re-syncs with the source.
- The Program copy is a **draft**; nothing is published or assigned automatically.
- The referenced system Templates are duplicated (so the coach can customize sessions)
  and published (so the draft Program can reference them, per the domain rule that
  program sessions reference published, owned template versions). System Exercises are
  referenced rather than duplicated, because coach content may reference system
  exercise versions.

The coach then reviews/edits the draft, publishes it, and assigns it through the
existing workflow.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/program-library` | Browse starter Programs (summaries + disclaimer). |
| GET | `/api/v1/program-library/{id}` | Read-only preview (weeks, templates, exercises). |
| POST | `/api/v1/program-library/{id}/clone` | Clone into a coach-owned draft. |

All are coach-only. The clone is registered in `LIBRARY_DEMO_MUTATIONS` and returns
`403 demo_read_only` for demo accounts. There are no update or delete routes for
system content.

## Seeding and updates

- Install/update with `python -m scripts.seed_library` (explicit operator command;
  never runs at application startup). It is idempotent and non-destructive.
- Development/demo seeding (`python -m scripts.seed`) also installs the library so it
  is browsable locally, in staging, and in Playwright.
- Content is defined in `backend/scripts/library_content.py` with stable seed keys and
  a static `verify_library_content()` check; the seeder builds content through the
  normal services, so it passes the same validation as coach-created content.
- To revise starter content later, add a **new** item (new name/key) or publish a new
  system version — never mutate a published starter version. Existing coach clones are
  independent snapshots and are unaffected. There is no synchronization engine.

## Boundaries

Not a marketplace, community library, or coach-to-coach sharing. No ratings, reviews,
likes, comments, paid content, external import, media, or AI generation. Starter
content is general and carries a review/general-use disclaimer; it makes no medical,
rehabilitation, or personalization claims.
