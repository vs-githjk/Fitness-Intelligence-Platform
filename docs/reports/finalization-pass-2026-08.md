# Vytal — Finalization pass report (2026-08)

Branch `feat/vytal-coach-programming-core` — **not merged / not pushed / not deployed**. This
pass added focused production, security, legal, and validation work on top of the prior two
passes. Gates green: **frontend** tsc 0 · eslint 0 · **vitest 288** · build ✓; **backend** ruff
clean · full pytest green.

## 1. Browser E2E — actually run (the deferred "first gate")

A real browser stack was brought up from this branch (backend on an isolated seeded SQLite DB +
Vite dev server + system Chrome via Playwright 1.61) and the flagship specs were executed:

- **`programming.spec.ts`: 5/6 passed.** The passing tests exercise coach login, the programming
  home, deterministic **"quads" search**, opening the picker, adding exercises, **keyboard
  reorder**, save draft, publish, and create-revision — i.e. the surfaces this initiative changed
  all pass in a real browser.
- **`theme-and-ia.spec.ts`: passed** (coach light / trainee dark / preference persistence, 4-tab IA).
- **1 failure**, `coach publishes … archives`: after archiving a template that still has a draft,
  the transient "Template archived" toast is immediately overwritten by "Draft loaded" (the detail
  reload effect). The archive itself works (status shows **Archived**). The code path is untouched
  by this initiative — a **pre-existing minor toast race**, logged for a follow-up.

Founder-grade screenshots were captured and **reviewed** (not committed, per policy).

## 2. Honest visual findings (from the screenshots)

- **Public legal/trust pages: strong.** Genuinely editorial (Iron display headings, editorial
  eyebrows, honest "what we do not claim"), the pending-details gate renders, and no raw
  `[FOUNDER]` text leaks (inline "… pending" fallback).
- **Exercise discovery / "quads": works and is truthful** — 23 metadata-driven quad results (not
  name-only), movement glyphs on cards. Validates the quads law in-browser.
- **Coach chrome is clean but generic light SaaS** — standard sidebar + rounded white cards +
  indigo accents; competent, not embarrassing, but **not yet the distinctive Iron Editorial hero**
  the brief wants. Exercise cards read catalog-like (faint glyph tiles).
- **Workout builder: functional** — the new "Drag a card, or use Up/Down…" hint is live; drag +
  muscle-focus summary + inline custom exercise are wired and pass in tests.

**Conclusion:** the coach-chrome + motion + programming-visual-hero work (brief §9–13) is the
**largest genuine remaining item**. It is a multi-iteration visual effort that needs
screenshot-verified iteration to reach the "don't call it premium unless proven" bar; it was not
rushed in this pass.

## 3. Delivered this pass (commits)

| Area | What |
|---|---|
| XLSX security (§16) | Reject DTD/entities (XXE / billion-laughs), bound archive entries + total uncompressed, ignore far-right columns; 8 adversarial tests; formulas still never evaluated |
| Rate limiter (§17) | Memory sweeping for idle keys; spoof-resistant client IP (rightmost XFF behind a trusted proxy, off by default); still process-local by design (documented) |
| Media provider (§18–19) | S3/R2 provider behind the storage abstraction, private objects via the authorized streaming endpoint; boto3 lazy + optional extra; prod requires `MEDIA_S3_BUCKET`; fake-client tests |
| Legal routes (§21–22, 26) | Public `/privacy`, `/terms`, `/security`, `/health-disclaimer`, `/consumer-health-data` in the design system + auth footer; company config as the only founder input; pending-details gate; component tests |
| Environment (§27–28) | Tests proving production is never "staging" and the banner is **absent** (not CSS-hidden) outside staging |

## 4. Component reviews

- **XLSX architecture:** dependency-free stdlib zip+XML, values-only. Adversarially hardened
  (XXE/DTD rejected, bombs bounded, columns bounded, malformed → friendly error). Verdict: safe.
- **Rate limiter:** in-process sliding window; **multi-instance = limit×instances** (documented on
  the Security page as a shared-store follow-up). Client IP spoof-resistant behind one trusted
  proxy. Suitable as a first line for a single-instance controlled beta.
- **Media:** production-capable in code; **remaining launch input = a bucket + S3/R2 credentials.**
  Local stays default for dev/test.

## 5. NOT done this pass (honest)

- **Transactional email + self-service password reset (§20):** not built. Needs a token model +
  migration and an email-provider abstraction; provider credentials are a launch input.
- **Terms/Privacy acceptance record (§23):** not built (needs a migration + registration capture).
- **Coach chrome / Programming visual hero / motion system / animated backgrounds (§9–13):** not
  done — the largest remaining design effort (evidence: screenshots above).
- **Real production deploy + production smoke/visual/mobile (§40–43):** blocked on external inputs.
- **Monitoring / backups / restore drill / release automation (§35–39):** documented in
  [production-readiness.md](../production-readiness.md); not provisioned (needs the prod platform).

## 6. Scores (conservative /10)

| Dimension | Score | Dimension | Score |
|---|---|---|---|
| Engineering | 8 | Vytal identity | 6 |
| Coach usability | 7 | Mobile coach UX | 6 |
| Programming UX | 7 | Accessibility | 8 |
| Exercise discovery | 8 | Security readiness | 8 |
| Import UX | 8 | Operational readiness | 6 |
| Visual richness | 5 | Production readiness | 6 |
| Motion | 3 | Would a coach enjoy it? | 6 |
| — | — | Choose it over Sheets? | 7 |

## 7. Verdicts

- **MERGE READY:** engineering is coherent and green, but **hold** per standing instruction (and
  finish coach-chrome/motion + refresh the stale Docker e2e specs first).
- **PRODUCTION READY (technical):** **NOT YET** — blocked on the launch inputs in §8 (media
  credentials, domain, prod secrets), plus email/reset if self-service reset is required at launch.
- **PUBLIC COMMERCIAL LAUNCH READY:** **NO** — additionally requires legal counsel review and the
  founder legal inputs.

## 8. Consolidated founder / external inputs (the only blockers to production)

1. **Domain / DNS** — the full production hostname for `joinvytal` (do not invent a TLD).
2. **Legal identity** — registered entity name, mailing address, governing jurisdiction.
3. **Contacts** — working privacy, security, and support inboxes.
4. **Legal** — effective date + counsel review/approval of the drafts; age-policy decision
   (13/16/18 and whether under-18 trainees are supported).
5. **Cloud credentials** — production Postgres (TLS), a media bucket + S3/R2 keys (+ endpoint for
   R2), a fresh production `JWT_SECRET`, and the coach registration code.
6. **Transactional email provider** credentials (for invitations + self-service password reset).
7. **Go-ahead** to add the production `render.yaml` topology, deploy, and merge.
