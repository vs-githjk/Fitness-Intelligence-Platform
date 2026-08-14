# Vytal — Flagship + Production pass report (2026-08)

Branch `feat/vytal-coach-programming-core` — **not merged / not pushed / not deployed**, ready
for founder review. This pass added **8 commits** on top of the prior 9 (17 ahead of `main`).
All gates green: **frontend** tsc 0 · eslint 0 · **vitest 281** · build ✓; **backend** ruff
clean · **pytest exit 0**.

## What shipped this pass

1. **Live 2026 market research** (Trainerize, TrueCoach, Everfit, TrainHeroic, TeamBuildr, PT
   Distinction, Hevy, Strong, Alpha Progression) + media-licensing + US privacy/legal research,
   with sources and access dates. Findings drove the build. `docs/research/`.
2. **Inline custom-exercise creation** — the add-exercise picker hosts a quick-create form that
   creates + publishes a private exercise and adds it to the workout without leaving the builder.
   (Closed the known Part 20 gap.)
3. **Tactile drag-and-drop builder** — pointer/HTML5 drag reorder of exercise cards (no new
   dependency), grip handle + drop highlight, keyboard Up/Down retained, reduced-motion honored;
   movement glyph on each card; **"Add set" copies the previous set** (Everfit/Hevy/Strong).
4. **Excel (.xlsx) workout import** — the clearest unmet migration path in the market. Values-only,
   dependency-free parsing (stdlib zip+XML; no formula/macro execution); shares CSV's matching +
   prescription mapping; bounded + friendly errors.
5. **Workout muscle-focus summary** — data-true "training should be seen" balance view (regions +
   primary set counts) from exercise metadata via the frozen §20 map; no invented volume.
6. **Security hardening** — response security headers (nosniff/frame-DENY/referrer/strict CSP,
   HSTS in deployed) + sliding-window rate limiting on auth/registration/invite/demo/import in
   deployed environments (429 + Retry-After).
7. **Legal first-drafts** — Privacy, Terms, Health & Fitness Disclaimer, a verified-controls-only
   Security/Trust page, and a Washington-MHMDA-style Consumer Health Data notice. No false
   compliance claims; company-specific inputs left as `[FOUNDER]`/`[COUNSEL]` placeholders.
8. **Production-readiness runbook** — documents the already-implemented env model, security posture,
   and system-vs-demo seeding split, plus the explicit external launch inputs.

## Acceptance — Coach Ease usability bar (Part 44), answered honestly

- Create a workout without training? **Yes** — search/add/drag-order/prescribe/save with plain
  language; the version machinery stays hidden.
- Find an exercise by name / muscle / equipment / movement? **Yes** (deterministic engine).
- Does "quads" behave naturally? **Yes** — synonym-aware, metadata-driven, no guessing.
- Create a private exercise **without leaving the builder**? **Yes** (new this pass).
- Reorder confidently? **Yes** — drag + keyboard, with a fallback that stays clear under
  reduced-motion.
- Reuse starter content quickly? **Yes** — 106/35/10 library, clone flows.
- Import existing programming? **Yes** — CSV **and** Excel, review-before-save.
- Prefer this over rebuilding in a spreadsheet? **Plausibly yes for programming** — and import
  removes the migration tax competitors leave in place.

## Market positioning (from research)

"Serious programming power + consumer usability" is **supported and genuinely unowned**:
competitors import clients but not workouts; muscle/equipment/body-map discovery is a wedge
(most rely on plain search, some demand exact spelling); several flagship tools are self-admittedly
dated. Reject (confirmed): marketplace, fake-AI auto-coach, everything-app bloat, gamification.

## Honest remaining gaps (each sizable; several need external inputs or a browser env)

- **Full browser Playwright E2E + ~30 visual-QA screenshots (Parts 45–48)** — NOT run this pass.
  New surfaces are covered by unit/component/API tests; the clean-build browser pass + screenshots
  remain the top validation task.
- **Motion system + animated background visuals (Parts 30–34)** — beyond the per-interaction motion
  added to the builder; not built.
- **Coach chrome migration + first-run/quick-start (Parts 39–42)** — not done.
- **Supersets/blocks in the builder (research table-stakes)** — deferred; needs a schema change.
- **Durable production media provider (S3/R2) (Part 60)** — required before a real production deploy;
  credentials are a launch input.
- **Transactional email + self-service password reset (Parts 65–66)** — provider is a launch input.
- **Public legal routes + footer + versioned Terms/Privacy acceptance (Parts 75–76)** — deferred so
  the product does not ship pages with unfilled `[FOUNDER]` placeholders; unblocks once company
  details are provided.
- **render.yaml production topology (Parts 50, 53)** — documented, not added, to avoid implying a
  deployable production that would fail config validation on media.
- **Library/template quality audit to ~130–160 (Parts 22–24)** — not revisited this pass.

## Frozen laws preserved

Coach Ease, guidance-over-metrics, determinism, immutable published history, one active primary
program, server-side authz (404 cross-account), demo read-only + disabled in production,
non-medical, no fake-AI / marketplace / trainee self-programming. No `Co-Authored-By` trailers.
