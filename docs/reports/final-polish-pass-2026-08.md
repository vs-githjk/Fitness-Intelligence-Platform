# Vytal — Final polish + production-activation foundation (2026-08)

Branch `feat/vytal-coach-programming-core` — **not merged / not pushed / not deployed**.
This pass closed the two largest gaps from the prior finalization report: the coach
experience looking like generic light SaaS, and the missing production-activation
foundation (email/reset, production topology). Verified in a real browser.

**Gates:** frontend tsc 0 · eslint 0 · vitest **292** · vite build ✓; backend ruff 0 ·
full pytest green; alembic single head `20260814_0018` with reversible up/down; browser
Playwright **6/6** (programming + theme) including the archive flow that previously failed.

## 1. Starting state

`8c8f232`, 24 commits ahead of `main` (== `origin/main` == `2827da2`), clean. The prior
report's honest verdict: coach chrome = "clean but generic light SaaS"; email/reset,
production topology, and the archive-toast race were open.

## 2. Coach-chrome changes (the P0)

The coach now renders in the **light "training studio" expression of Iron Editorial**, not
a separate SaaS skin. `AppShell` coach branch migrated off legacy tokens onto the warm-paper
`mb-*` system: the typographic **Vytal wordmark + "Coaching studio" eyebrow**; navigation
grouped into labeled editorial sections (**Studio / Oversight / Account**) under hairlines,
sharing the trainee's ember active-rail device (one `NavRow` for both roles); an editorial
identity footer with a mono role label; and mb-token mobile chrome. Coach stays **light by
default** (confirmed by the theme E2E). Screenshots reviewed: the shell reads clearly
editorial and ties the (already-clean) Overview body together.

## 3. Programming-Studio visual changes

`ProgrammingShell` became a real hero frame: a mono **"Programming Studio"** eyebrow + display
title over an **underline tab bar with an ember active mark** (replacing the pill/indigo
strip). An entrance settle animation (reduced-motion-safe).

## 4. Exercise-discovery changes (§6)

`ExerciseCard` migrated to editorial with an explicit scan hierarchy: movement glyph → name →
**the muscle it trains as the prominent lead line** → pattern → equipment. A "quads" search now
reads as quad-focused at a glance (verified in-browser). Filter chips + "New exercise" CTA use
the ember/indigo editorial treatment.

## 5. Builder visual changes (§7)

Editorial mobile Builder/Preview toggle, a rewritten empty state ("No exercises yet — Search
the library and add a published exercise…"), and an editorial save/status bar with the
save-state as the prominent line. The interior form fields still use the shared `Card`/`Button`
primitives (honest remaining debt — see §remaining).

## 6. Motion system

The `mb-settle/expand/breathe/check` keyframes + `--mb-dur-*` budget already existed with a
global `prefers-reduced-motion` collapse. This pass **applied** them to the coach surfaces
(studio entrance settle, micro transitions on nav/tabs/cards). It did **not** add the full
per-interaction choreography (add/remove/reorder/publish reveals) from brief §11 — that remains
the largest deferred visual item.

## 7. Background visuals

Not added this pass. The movement-glyph/Iron-Line motif already carries training identity on the
login cover and cards; a broader ambient background layer (§12) was intentionally not rushed.

## 8. Reduced-motion

Honored globally (index.css) — all `animate-mb-*` collapse; new coach animations use
`motion-reduce:animate-none`. State is never conveyed by motion alone.

## 9. Archive-toast race — root cause & fix (§19)

**Root cause:** a publish/revision/archive action set `loaded.current=''` to force a detail
reload; the load `useEffect` then re-ran and reset `saveState` to its default ("Draft loaded"),
clobbering the action's confirmation ("Template archived"). **Fix:** a `preserveSaveState` ref,
set by the action, tells the reload to keep the action's message once. Applied consistently to
`TemplateBuilder`, `ProgramBuilder`, and `ExerciseEditor`. Regression test added; the
previously-failing browser test now passes.

## 10. Playwright results

Real browser (system Chrome), branch build, isolated seeded SQLite backend on a spare port,
vite dev calling it directly: **`programming.spec.ts` 2/2 + `theme-and-ia.spec.ts` 4/4 = 6/6.**
The archive step inside `programming.spec.ts` (the prior known failure) now passes.

## 11. Screenshots captured & reviewed

Coach Overview, Programming exercises, "quads" search, Workout Templates, empty builder, login,
forgot-password, coach mobile "quads" — desktop (1440) + mobile (390). Honest read: the coach
now looks like considered coaching software, not a dashboard template.

## 12. Visual self-review (§23, not graded generously)

- Generic SaaS? **Largely resolved** for the shell + Programming + discovery + Overview. Real
  editorial identity (wordmark, mono eyebrows, grouped nav, ember training accents, muscle-lead
  cards, warm paper).
- Programming the best coach screen? **Yes**, it now reads as the flagship.
- Builder easier than a spreadsheet? **Yes** for structure; interior set-prescription rows are
  functional but still the plainest surface.
- Honest remaining tells: the **legacy pill Badges** (blue/green) on cards are the main palette
  inconsistency; the builder's interior form and some filter panels still use shared legacy
  primitives; no ambient background layer yet.

## 13. Email architecture (§25, 27, 28)

`app/email/`: `EmailMessage` + `EmailProvider` protocol; `ConsoleEmailProvider` (local preview,
never selected in a deployed env); `SmtpEmailProvider` (stdlib `smtplib`, **no new dependency**,
STARTTLS, credentials injected from env); an env-selected factory. No vendor secret in the repo.
Tokens/URLs are never logged.

## 14. Password-reset implementation (§26)

`PasswordResetToken` (only the SHA-256 **hash** stored; expiry + single-use). `POST
/auth/password-reset/request` returns a **generic no-enumeration** response, consumes prior
tokens, excludes demo/system/inactive, and delivers via `BackgroundTasks`. `/confirm` validates
hash + expiry + single-use, sets the new hash, and consumes outstanding tokens. Both
rate-limited. Frontend `/forgot-password` + `/reset-password` pages in the front door; login now
links to self-service reset. The operator CLI remains.

## 15. Email external input needed

An SMTP provider: **host + username/password + a real `EMAIL_FROM`** (and the production
`FRONTEND_BASE_URL` for links). Nothing else.

## 16. Consent / acceptance implementation

**Not built this pass.** The public legal routes + pending-details gate exist; a *versioned
Terms/Privacy acceptance record* (§29-30) still needs a migration + registration capture, and is
gated on counsel-approved, versioned documents. Documented, not invented.

## 17. Legal config status

Unchanged and correct: company values live in `frontend/src/config/company.ts`; the pending-gate
prevents any `[FOUNDER]`/`[COUNSEL]` placeholder from shipping. Values remain founder inputs.

## 18. Age-policy status

**Deliberately undecided** — a required founder/legal input (13/16/18; whether under-18 trainees
are supported). Not chosen in code.

## 19. Production topology (§34-36)

`render.yaml` now defines a fully distinct **`vytal-api-production`** web service +
**`vytal-db-production`** Postgres (never the staging DB): `APP_ENV=production`, durable S3/R2
media, SMTP email, demo off, `branch: production` with **manual** deploys, release command
`alembic upgrade head && python -m scripts.seed_library` (system content only). Every
domain/secret value is `sync:false` — no domain/TLD invented, no secret embedded.

## 20. Staging topology

Unchanged (`fitness-intelligence-api-staging` + its DB). Staging still shows the STAGING banner
(truthful, not CSS); production resolves `production` and shows none.

## 21. System / demo seed separation (§35)

Already enforced and preserved: `scripts.seed_library` = system content (idempotent, no demo);
`scripts.seed` (demo) is gated behind `SEED_DEMO_DATA=true` and **refused in production** by both
`ensure_seed_allowed` and the config validator. The production release runs only the library seed.

## 22. Media-provider validation (§37)

S3/R2 provider (behind the storage abstraction, private objects via the authorized streaming
endpoint) with fake-client contract tests; production config requires `MEDIA_S3_BUCKET`. Full
end-to-end against a live bucket needs credentials (launch input).

## 23. Rate-limiter production behavior (§39)

In-process sliding window — **correct only at one replica** (limit × replicas otherwise).
Documented on the Security page, in the runbook, and in a `render.yaml` comment: do not scale the
production service horizontally without a shared-store/edge limiter. Client-IP is spoof-resistant
behind one trusted proxy. Appropriate for a single-instance controlled beta.

## 24. Monitoring

Structured request logging with request IDs + environment/version already present; a frontend
error boundary exists. A hosted error/monitoring provider integration remains a credential-gated
launch item (not wired this pass).

## 25. Backup / runbook validation (§41)

`docs/production-readiness.md` reconciled with the new reality (email/reset + production topology
now IMPLEMENTED; refreshed cutover steps; the vercel `noindex` reconsideration; the single-replica
rate-limiter note). No doc now describes infrastructure that does not exist.

## 26. Security regression

Backend suite green including auth/registration/invite/import rate limits, XLSX hardening, headers,
media auth, cross-account 404, and the new reset flow (hash-at-rest, single-use, expiry, no
enumeration, demo excluded). No secret or token is logged.

## 27. Accessibility

Nav uses `aria-current`; tabs `role="tab"`/`aria-selected`; ember is never the sole state signal
(word/label always present); reset pages use the shared labeled `Field`/`PasswordField` with
error wiring; focus-visible rings via `mbFocusRing`; keyboard reorder remains the drag fallback
(E2E-verified). Full contrast/axe sweep of every new surface not run this pass.

## 28. Performance

Deterministic search + `useDeferredValue`; no new animation loops (settle is one-shot); build
unchanged in shape. No layout jank observed in the captured surfaces.

## 29-32. Gate results

Frontend: `tsc` 0 · `eslint --max-warnings=0` 0 · `vitest` 292 passed · `vite build` ✓.
Backend: `ruff` 0 · full `pytest` green · alembic single head, reversible.
E2E: 6/6 (programming + theme) in system Chrome from branch build.

## 33. Files changed (by area)

- **Coach chrome:** `frontend/src/components/AppShell.tsx`,
  `components/programming/ProgrammingShell.tsx`, `components/programming/ExerciseLibrary.tsx`,
  `components/programming/TemplateBuilder.tsx`.
- **Archive-race fix:** `TemplateBuilder.tsx`, `ProgramBuilder.tsx`, `ExerciseEditor.tsx`,
  `ProgrammingWorkspace.test.tsx`.
- **Email/reset (backend):** `app/email/{base,console,smtp,__init__}.py`, `app/password_reset.py`,
  `app/api/auth.py`, `app/config.py`, `app/models.py`, `app/main.py`, `app/schemas.py`,
  `alembic/versions/20260814_0018_password_reset_tokens.py`,
  `tests/test_password_reset_flow.py`, `tests/test_email_provider.py`, `tests/test_deployment.py`.
- **Reset (frontend):** `pages/AuthPages.tsx`, `App.tsx`, `pages/AuthPages.test.tsx`.
- **Production topology / docs:** `render.yaml`, `docs/production-readiness.md`, this report.

## 34. Dependencies

**None added.** SMTP uses stdlib `smtplib`; S3 stays the pre-existing optional `boto3` extra.

## 35. Migrations

`20260814_0018_password_reset_tokens` — additive; creates one table (hash + expiry + single-use);
reversible; single head.

## 36. Commits (this pass)

`cf9e656` coach chrome + Programming + archive fix · `f5956ce` email + self-service reset ·
`9dd7a10` production topology + runbook · (this report).

## 37. Final branch / main state

`feat/vytal-coach-programming-core`, clean tree, **28 commits ahead** of `main`
(`main == origin == 2827da2`). **Not merged, not pushed, not deployed** (per standing instruction).

## 38. Remaining external founder inputs (the only production blockers)

1. **Domain / DNS** — the production hostname for `joinvytal` (do not invent the TLD).
2. **Legal** — registered entity, address, jurisdiction, effective date + counsel review;
   **age-policy decision**.
3. **Contacts** — working privacy, security, support inboxes.
4. **Cloud** — production Postgres (TLS), media bucket + S3/R2 keys (+ endpoint for R2), fresh
   `JWT_SECRET`, coach registration code.
5. **SMTP provider** — host + credentials + real sender.
6. **Go-ahead** to create the `production` branch, deploy, and merge.

## 39. MERGE READY?

**Engineering: yes** (coherent, green, E2E-verified). **Hold to merge** per the standing
instruction, pending founder visual review of the coach chrome. Recommend refreshing the
Docker-based daily/visual e2e specs (if still stale) before merge.

## 40. TECHNICALLY PRODUCTION READY?

**Not yet — but only external inputs remain.** All independent engineering for production
activation is now in place (env separation, distinct topology, durable media, transactional
email + self-service reset, seed separation, security). Supplying the §38 inputs is what unblocks
a real production deploy — no further major feature-implementation pass is required.

## Conservative scores (/10)

| Dimension | Score | Dimension | Score |
|---|---|---|---|
| Engineering | 8 | Vytal identity | 8 |
| Coach usability | 8 | Mobile coach UX | 7 |
| Programming UX | 8 | Accessibility | 8 |
| Exercise discovery | 8 | Security readiness | 8 |
| Builder | 7 | Production technical readiness | 8 |
| Visual richness | 7 | Would a non-technical coach enjoy this? | 8 |
| Motion | 5 | Would they use it instead of Google Sheets? | 8 |

## A–F

- **A. Coach looks like Vytal, not generic SaaS?** Largely **yes** — the shell, Programming,
  discovery, and Overview now read editorial. Residual tells: legacy pill badges, some interior
  builder/filter primitives, no ambient background yet.
- **B. Programming + Execution clearly the two flagships?** **Yes.**
- **C. Any known failing E2E test?** **No** — 6/6, including the previously-failing archive flow.
- **D. Independent engineering still needed before production activation?** **No major item.**
  Optional polish: consent-acceptance record, deeper per-interaction motion, badge/interior
  editorial cleanup, a hosted monitoring integration.
- **E. Exact founder/legal/credential inputs required?** §38 above.
- **F. Once supplied, deployable without another major feature pass?** **Yes.**
