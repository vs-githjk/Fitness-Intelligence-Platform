# Release runbook

The end-to-end process for shipping a FitIntel 360 release. v0.5.0 (Workout
Intelligence) is used as the completed worked example; the steps apply to any
version. Do not treat v0.5.0 as the only supported version.

> Guardrails: one logical release commit; **tag only after hosted verification**;
> never rewrite historical migrations; never weaken authorization or demo
> protection; do not push/deploy/tag unless explicitly instructed. See
> [../../AGENTS.md](../../AGENTS.md).

## 0. Pre-release audit

- Confirm branch, `git status` clean, and `HEAD == origin/main`.
- Confirm the intended commits are present and the working tree contains only
  intended changes (`git diff --check`).
- Confirm version sources and Alembic head match expectations.

## 1. Version alignment

Update every version source together:

- Backend `backend/app/__init__.py` (`__version__`) — drives FastAPI/OpenAPI and
  `/health*`.
- Frontend `frontend/package.json` and the mirrored `package-lock.json` root
  version — surfaced via `frontend/src/env.ts`.
- Any version-assertion tests (`backend/tests/test_deployment.py`, frontend
  `hosted-smoke` expectation, docs that state the current version).

Verify no stale previous-version "current release" references remain (dependency
versions that merely coincide are fine).

## 2. Migration validation

- Local SQLite and PostgreSQL: `alembic upgrade head`, `downgrade -1`, re-upgrade,
  `current`, `heads`, `check` (expect "No new upgrade operations detected").
- Confirm the new migration(s) are additive and dual-path; confirm no historical
  migration was modified.
- Confirm the upgrade path works from the previously deployed head.

## 3. Full automated tests

- Backend: `ruff check .` and full `pytest` (includes version-centralization,
  health/version, authorization, and demo-mutation-inventory tests).
- Frontend: `tsc` typecheck, `eslint` (warnings fail), `vitest`, and `vite build`
  (verify title, favicon, and `/assets/` paths).

## 4. Isolated Playwright (required)

Run the **entire** Playwright suite once against a disposable database/volume
using a separate compose project (never the dev DB), following the isolated e2e
procedure in [../../AGENTS.md](../../AGENTS.md): clean migration, deterministic
seed, healthy stack, full run. Report passed/skipped/failed; do not use a
selective rerun as the final result. Revert regenerated `docs/screenshots/*.png`.

## 5. Release notes

Add `docs/releases/vX.Y.Z.md`: summary, trainee/coach capabilities, scope,
migration/upgrade notes, known limitations, deferred features, and all required
disclaimers (no medical clearance; safety reports not continuously monitored; load
not a medical measure; no automatic progression/deload; recorded best =
best recorded compatible completed performance in available history;
post-completion correction deferred). Update the changelog if one exists.

## 6. Release commit

Create exactly one commit `chore: prepare FitIntel 360 vX.Y.Z release` containing
only version updates, release notes, changelog, documentation alignment, and any
narrow release-blocking fixes (with focused tests) found in the audit. No new
product features. No `Co-Authored-By` trailer.

## 7. Push

When explicitly instructed and all local validation passes, push the release
commit to `origin/main`. This triggers CI; Render auto-deploys on `checksPass` and
Vercel deploys on git integration.

## 8. Deployment order

1. **Database migration** — Render runs `alembic upgrade head` as the backend
   pre-deploy command.
2. **Backend** — deploys and must pass the `/health/ready` health check.
3. **Backend verification** — hosted `/health`, `/health/live`, `/health/ready`
   report the new version; migration head is correct; login, demo-session, normal
   mutation protection, and demo mutation `403` all work.
4. **Explicit demo seed** — only via the approved explicit seed command (staging
   sets `SEED_DEMO_DATA=false`; normal startup never seeds). Verify idempotency if
   safe.
5. **Frontend** — deploys after the backend is healthy; verify title/logo/favicon,
   SPA refresh routing, correct API endpoint, and no CORS/mixed-content errors.

## 9. Hosted verification

Run hosted smoke and product verification against the deployed environment using
synthetic/seeded identities only — never real health data. Cover public/auth,
trainee, coach, security (cross-role protection, demo mutation `403`, unauthorized
object access, cache isolation), and infrastructure (health green, correct
version, no repeated backend exceptions, no critical console errors). Record exact
pass/fail.

## 10. Tag — only after verification

Only after the release commit is pushed, deployment succeeds, hosted verification
passes, version and migration head are confirmed, the working tree is clean, and
`origin/main == HEAD`: create an annotated tag `vX.Y.Z` on the release commit with
message `FitIntel 360 vX.Y.Z — <milestone>` and push it. Do not create the tag
before hosted verification. Do not move or recreate an existing tag.

## Rollback decision points

- Backend health fails after deploy → stop before frontend rollout; investigate;
  redeploy the previous known-good backend if needed.
- Migration fails → see
  [deployment-and-recovery.md](deployment-and-recovery.md#migration-failure-response).
  Do not force-forward blindly.
- Hosted verification finds a release-blocking defect → stop, diagnose, make one
  focused hotfix commit, validate locally, push, redeploy, rerun affected hosted
  checks, then rerun the full hosted smoke set before tagging.

## Post-release monitoring

- Watch health endpoints, backend logs (no repeated exceptions), and frontend
  console for critical errors.
- Confirm the reported version remains correct across backend and frontend.
- Track any tester-reported P0/P1 issues per
  [../testing/feedback-triage.md](../testing/feedback-triage.md).

## Patch-release process

For a P0/P1 hotfix: branch or work from `main` as instructed, make one focused
fix commit with a focused test, run the relevant gates (full suite if executable
code changed; targeted checks for narrow fixes), bump the patch version if the
change is user-facing, follow the same push → deploy → verify → tag order, and
record the fix in the release notes/changelog.

## Worked example — v0.5.0

- Version aligned 0.4.2 → 0.5.0 across backend/frontend/tests/docs.
- Migrations validated on SQLite and PostgreSQL through head `20260716_0012`
  (additive only).
- Backend ruff + full pytest, frontend tsc/eslint/vitest/build, and the full
  isolated Playwright suite all green.
- Single release commit `chore: prepare FitIntel 360 v0.5.0 release`
  (`5306167`) pushed.
- Hosted backend and frontend verified (health reports 0.5.0; login, demo,
  workout, analytics, cache isolation, and demo protection checked).
- Annotated tag `v0.5.0` — "FitIntel 360 v0.5.0 — Workout Intelligence" — created
  on the release commit only after hosted verification.
