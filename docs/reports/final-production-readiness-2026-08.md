# Vytal — Final production readiness + founder launch preparation (2026-08)

This is the final pre-launch pass. It verifies the repository, completes production
configuration, researches current Indian law authoritatively, reconciles the age policy,
merges the finished product to `main`, and hands the founder an exact self-service deployment
runbook. **Claude did not deploy externally, provision infrastructure, touch DNS, or invent any
legal/domain fact.** Deployment is the founder's step.

**Deployment runbook:** [`docs/operations/production-launch.md`](../operations/production-launch.md).

---

## 1. Starting repository state

`feat/vytal-coach-programming-core` @ `4289569`, 28 commits ahead of `main` (`main == origin/main
== 2827da2`), clean tree. Diff vs main: 116 files, ~6.8k insertions.

## 2. Final pre-merge validation (gates)

- **Frontend:** `tsc` 0 · `eslint --max-warnings=0` 0 · **vitest 292** · `vite build` ✓.
- **Backend:** `ruff` 0 · full `pytest` green · alembic **single head** `20260814_0018`, reversible.
- **Browser (Playwright, system Chrome, branch build, isolated seeded DB):** programming + theme
  **6/6**, incl. the archive flow that previously failed.
- **Environment rendering (real browser, both modes):** `APP_ENV=production` → **no** STAGING
  indicator; `APP_ENV=staging` → indicator **present**. Verified by rendering `/login` under each
  mode, not by source inspection (§28/§38).

## 3. Local founder review

Run the current branch locally (no Docker), from the verified recipe:

```
# backend (fresh seeded SQLite on :8010)
cd backend && source .venv/bin/activate
rm -f e2e.db
APP_ENV=local DATABASE_URL=sqlite:///./e2e.db MIGRATION_DATABASE_URL=sqlite:///./e2e.db \
  JWT_SECRET=local-development-secret-change-me-123456 alembic upgrade head
APP_ENV=local DATABASE_URL=sqlite:///./e2e.db MIGRATION_DATABASE_URL=sqlite:///./e2e.db \
  JWT_SECRET=local-development-secret-change-me-123456 DEMO_MODE_ENABLED=true SEED_DEMO_DATA=true \
  python -m scripts.seed
APP_ENV=local DATABASE_URL=sqlite:///./e2e.db MIGRATION_DATABASE_URL=sqlite:///./e2e.db \
  JWT_SECRET=local-development-secret-change-me-123456 DEMO_MODE_ENABLED=true \
  CORS_ORIGINS=http://localhost:5176 uvicorn app.main:app --host 127.0.0.1 --port 8010
# frontend (another shell)
cd frontend && VITE_APP_ENV=local VITE_API_URL=http://localhost:8010/api/v1 \
  npx vite --host 127.0.0.1 --port 5176 --strictPort
```

Then open **http://localhost:5176**. Easiest login: the **Explore Demo** button on `/login`
(read-only coach or trainee), or the seeded coach `coach@fitness.example.com` / `DemoPass123!`.

- **Coach path:** `/login` → Overview → Programming → search "quads" → build a 5-exercise
  workout → add a custom exercise inline → Import (CSV/XLSX) → Settings.
- **Trainee path:** Today → open a workout → Workout Execution.

## 4. Legal / privacy / business research

Full research (India-focused, primary sources, all accessed **2026-08-15**) is summarized below.
This is research to inform professional review — **not legal advice**. Labels:
[VERIFIED LAW] / [GUIDANCE] / [BEST PRACTICE] / [RECOMMENDATION].

Key primary sources: DPDP Act 2023 text (dpdpa.com/indiankanoon); MeitY/PIB DPDP Rules 2025
notification; SPDI Rules 2011 (IT Act s.43A); CBIC-GST + Notification 10/2017-IGST; CERT-In 2022
Directions + FAQ (cert-in.org.in); MCA/ClearTax/Razorpay for proprietorship; TN Shops &
Establishments Act + GCC professional tax.

## 5. India privacy findings

- [VERIFIED LAW] **DPDP Act 2023** is notified but its **substantive obligations are phased**;
  the final **DPDP Rules 2025** were notified mid-Nov 2025, and the compliance core (notice
  standards, security, breach, children's verifiable consent, rights + grievance timelines) binds
  **~May 2027**. There is **no small-business exemption**; size only ever escalates duties.
- [VERIFIED LAW] **Health/fitness data is "sensitive personal data" under the currently-operative
  IT Act s.43A + SPDI Rules 2011** — which **already** require a **published privacy policy +
  consent** for anyone handling it online. So "DPDP isn't enforced until 2027" does **not** mean
  nothing applies now: a Privacy Policy + consent are effectively **required now**.
- [VERIFIED LAW] DPDP uses a single "personal data" category (no GDPR-style special tier); the
  practical bar is still high-care consent, minimisation, security, rights.
- [VERIFIED LAW] Ordinary Data Fiduciaries need **no DPO** and no DPIA; only a government-notified
  **Significant Data Fiduciary** does. One published contact + a grievance mechanism suffice.

## 6. Business-registration findings

- [VERIFIED LAW] **No incorporation is legally mandatory** to run a free beta. A solo founder
  operates as a **sole proprietor = the individual** (personal PAN); India has **no central
  proprietorship registration**. LLP/Pvt Ltd is optional (liability/fundraising).
- [VERIFIED LAW] **TN Shops & Establishments** realistically triggers on the **first employee /
  commercial premises** (fact-specific — confirm locally). **Professional tax** is **nil** below
  ₹21,000 half-yearly income.

## 7. GST / tax-registration findings

- [VERIFIED LAW] Services GST threshold is **₹20 lakh** aggregate turnover; **Tamil Nadu is a
  normal state** (₹20 lakh, not ₹10 lakh). **No mandatory pre-revenue registration** — a free
  product has no taxable turnover.
- [VERIFIED LAW] **Interstate supply of services does not force early registration**
  (Notification 10/2017-IGST preserves the ₹20 lakh benefit). **Export of services is zero-rated**
  (needs an **LUT/RFD-11** once registered; still counts toward the threshold). OIDAR mainly
  burdens *foreign* providers, not an India-based founder.

## 8. Minor / age findings

- [VERIFIED LAW] DPDP **§2(f): "child" = under 18** — flat, no reduced-age option — and **§9**
  requires **verifiable parental consent** and bans behavioural tracking/targeted ads to children.
  A general fitness app is **not** within the Fourth-Schedule healthcare/education carve-outs.
- Vytal has **no guardian-consent machinery**.

## 9. Recommended immediate beta age policy

[RECOMMENDATION] **Adults only, 18+.** Implemented this pass: `minAge` default **18** (env-
overridable only when machinery exists) and the onboarding assessment age floor raised **16 → 18**;
legal copy states 18+. Operationally the coach invites adults only.

## 10. Requirements to support 15/16-year-old trainees later

[VERIFIED LAW] Would require: a **verifiable parental/guardian consent** flow (verify the parent
per Rule 10), child↔guardian account linkage, **suppression of behavioural tracking/targeted ads**
for child accounts, a "no detrimental effect" feature review, and age-appropriate consent UX. This
is a meaningful build — **defer** until deliberately targeting minors. Do **not** lower `VITE_MIN_AGE`
before it exists.

## 11. Legal-entity / operator findings

[VERIFIED LAW/RECOMMENDATION] Vytal can truthfully run a **free** controlled beta operated **by
the founder personally** (sole proprietor). The Privacy Policy/Terms operator is then **the
individual** + a real address + a monitored inbox. Formalizing an entity is a **pre-charging /
fundraising** decision, not a beta blocker.

## 12. Governing-law status

[RECOMMENDATION] India baseline; a provisional clause naming the individual operator with Chennai
courts is defensible — but **do not hard-code it**: it depends on the entity decision and interacts
with the Consumer Protection Act 2019 / E-Commerce Rules 2020. It is env-driven
(`VITE_LEGAL_JURISDICTION`) and should be **counsel-finalized** before commercial launch.

## 13–17. Legal-document requirements (this beta)

| Document | Status | Basis |
|---|---|---|
| **Privacy Policy** | **REQUIRED NOW** | Health data = SPDI under operative IT Act/SPDI Rules |
| **Consent capture at signup** | **REQUIRED NOW** (conceptually) | SPDI Rule 5 / DPDP s.6 |
| **Terms of Service** | **STRONGLY RECOMMENDED NOW** (provisional) | contractual; counsel before commercial |
| **Health/Fitness Disclaimer** | **STRONGLY RECOMMENDED NOW** | liability mitigation |
| **Security page** | content REQUIRED NOW; standalone page recommended | SPDI Rule 4 disclosure |
| **Consumer-health-data notice** | **NOT NECESSARY** (Indian law) | US-style construct; revisit if targeting US |
| **Cookie notice** | **NOT NECESSARY** (Indian law) | required only if targeting EU/UK |

All these pages exist in the app behind the legal-config gate; the founder activates them by
setting the `VITE_LEGAL_*` values. A **recorded, versioned acceptance record** is deliberately
**not** built (building it against pending/placeholder policies is forbidden and meaningless) — it
is the top pre-broader-launch legal-engineering item, to be built against finalized, counsel-
reviewed policies.

## 18. Contact-email recommendation

[RECOMMENDATION] **One monitored role-inbox** (e.g. a single address used for `VITE_PRIVACY_EMAIL`
= `VITE_SECURITY_EMAIL` = `VITE_SUPPORT_EMAIL`) is sufficient for a one-coach beta, provided it is
genuinely monitored and a human/role is named. Split roles before commercial scale. Use a
role-based alias, not a personal Gmail, to make that split painless later.

## 19. Counsel review required

Final Privacy Policy / Terms / disclaimer wording; the governing-law clause (tied to entity +
consumer law); the DPDP readiness plan toward ~May 2027; under-18 architecture if/when pursued.

## 20. CA / accountant review required (before charging)

GST timing at ₹20 lakh + SAC classification + LUT for exports; entity choice; TN Shops Act +
professional-tax enrolment at first income/employee; EPF/ESI + TDS at first hire.

## 21–25. Infrastructure answers (audited in code)

| Item | Exists in code? | Needed for prod? | Founder creates later w/o code change? | External account? | What to create |
|---|---|---|---|---|---|
| **Production Postgres** | topology in `render.yaml` (`vytal-db-production`, separate from staging) | **Yes** | Yes | Render | a paid Render Postgres (for backups) |
| **S3/R2 media** | provider + authorized streaming + tests | **Yes** | Yes | Cloudflare R2 / AWS | a private bucket + access key |
| **SMTP** | provider abstraction (stdlib SMTP), reset/invite wired | **Yes** (for email delivery) | Yes | Resend/Postmark/Brevo/SES | account + verified sender + creds |
| **JWT secret** | required, fail-fast if weak | **Yes** | **Auto** (`generateValue` in blueprint) | none | nothing — Render generates it |
| **Coach registration code** | enforced, invite-only | **Yes** | Yes | none | `openssl rand -base64 24` → set in Render |

Recommended providers for a one-coach beta: **Render** (backend + Postgres), **Vercel**
(frontend), **Cloudflare R2** (media, no egress fees), **Resend/Postmark** (email). Avoid
enterprise overengineering.

## 26. Production topology readiness

`render.yaml` defines a **distinct** `vytal-api-production` + `vytal-db-production` (never the
staging DB), `APP_ENV=production`, S3 media, SMTP, demo off, `branch: production`, **manual**
deploys, release = `alembic upgrade head && python -m scripts.seed_library` (system content only).
All domain/secret values are `sync:false`. Staging is independently preserved.

## 27. Production configuration contract

Startup **fails fast** in a deployed env unless: Postgres (not SQLite), non-default `JWT_SECRET`,
HTTPS `CORS_ORIGINS`, explicit `TRUSTED_HOSTS`, DB TLS, `API_DOCS_ENABLED=false`, durable media,
real SMTP host + non-localhost `EMAIL_FROM`, HTTPS `FRONTEND_BASE_URL`, non-default demo invite
code, and (production) demo/seed disabled. Unresolved **legal metadata does not crash anything** —
it is frontend build config that gates the legal pages truthfully, and local dev is unaffected.

## 28. Staging behaviour / 29. Production-mode behaviour

Proven in a real browser (§2): staging shows the STAGING indicator; production shows none — driven
solely by `VITE_APP_ENV`, not CSS/hostname. Covered additionally by `env.test.ts` +
`EnvironmentBanner.test.tsx`.

## 30. System / demo seed separation

`scripts.seed_library` = system content (100+ exercises, 35+ templates, 10+ programs), idempotent,
**no demo users**. `scripts.seed` (demo) is gated behind `SEED_DEMO_DATA=true` and **refused in
production** by both `ensure_seed_allowed` and the config validator. The production release runs
**only** the library seed. The founder cannot accidentally run "seed everything" in production.

## 31. Password-reset readiness

Hashed-at-rest, expiring, single-use tokens; generic no-enumeration response; prior tokens
consumed; demo/system/inactive excluded; rate-limited; never logs the token/URL. Frontend
`/forgot-password` + `/reset-password`. **Founder action for real delivery:** configure SMTP (§E
of the runbook).

## 32. Media readiness

S3/R2 provider behind the storage abstraction; private objects via the authorized streaming
endpoint; fake-client contract tests (roundtrip, unsafe-key rejection, missing object, factory
selection) + media API tests (upload/read/delete/authorization/MIME/limits). Full end-to-end vs a
live bucket needs the founder's credentials.

## 33. Security readiness

Security headers + HSTS (deployed) + strict CSP; CORS/hosts validated; login/registration/invite/
import + password-reset rate limits; adversarial XLSX hardening (XXE/bomb/bounds); media
authorization + cross-account 404; bcrypt; no frontend secrets; no tokens in logs. No certification
is claimed.

## 34. Rate-limiter assessment

**Process-local** sliding window (per-instance). Single instance: correct. Multi-instance: limit ×
instances. Spoof-resistant client IP behind one trusted proxy; idle-key memory sweeping; resets on
restart. **For a one-coach beta at one replica this is sufficient** — documented scaling debt: do
not scale the production service horizontally without a shared-store/edge limiter (noted in the
Security page, runbook, and a `render.yaml` comment).

## 35. Monitoring readiness

Structured request logging with request IDs + environment/version; frontend error boundary. A
hosted error-monitoring vendor is optional and credential-gated; not required to run.

## 36. Backup guidance

Render managed Postgres provides automated daily backups **on paid instances**; PITR/retention
depend on plan. **Verify the exact terms of the chosen plan at signup** and confirm the restore
procedure before onboarding the coach (runbook §D). Do not run the coach's data on an un-backed-up
free tier.

## 37. Migration / release procedure

Ordered flow in the runbook: provision DB → configure backend env → deploy (preDeploy runs
`alembic upgrade head && scripts.seed_library`, one-off instance, no multi-instance race) → verify
`/health/ready` → deploy frontend → verify CORS + env → onboard coach → smoke → domain later.

## 38. Deployment runbook location

[`docs/operations/production-launch.md`](../operations/production-launch.md).

## 39. Post-deploy smoke checklist

In the runbook §H (env / auth / coach / media / trainee / legal).

## 40. Domain-cutover instructions

Runbook §G — Vercel domain + optional API subdomain + update origins/CORS/`FRONTEND_BASE_URL` +
email DNS (SPF/DKIM/DMARC) + verify HTTPS + re-smoke. **No code change needed** (`env.ts` throws on
a bad `VITE_API_URL`; origins are all config).

## 41. Remaining FitIntel / debug / placeholder references

- `FitIntel` appears **only** in a `Brand.tsx` comment and a `Brand.test.tsx` assertion that it is
  **not** rendered — zero user-facing leakage; none in the production bundle.
- `[FOUNDER]` appears **only** as code comments in `company.ts`; the values are empty strings behind
  the pending-gate, which never renders a placeholder. None in the bundle.
- `example.com` in the bundle is the input placeholder `you@example.com`; `localhost:8000` is the
  **local-only** `VITE_API_URL` fallback — `env.ts` throws unless a non-local HTTPS URL is set for
  a non-local build, so production cannot ship localhost.

## 42. Files changed (this pass)

- Age policy: `backend/app/schemas.py` (age floor 16→18), `frontend/src/config/company.ts`
  (env-driven, minAge default 18), `frontend/src/vite-env.d.ts`, `frontend/src/pages/LegalPages.tsx`
  (age copy).
- Docs: `docs/operations/production-launch.md` (new runbook), this report.

## 43. Dependencies / 44. Migrations

**No dependencies added.** **No new migrations** (single head `20260814_0018` from the prior pass).

## 45–48. Merge result / main / origin / version

See the merge section at the end of this pass. Version stays **0.5.0** (repo bumps version only at
an actual release/tag per existing governance; recommended release tag `v0.6.0` at the founder's
deploy — not created now since nothing is deployed).

## 49. Remaining founder inputs / external credentials / counsel decisions

- **Inputs:** production domain (later); legal identity values (operator name = you, address,
  jurisdiction, effective date, contact inbox); age policy already set (18+).
- **Credentials:** Render Postgres; R2/S3 bucket + keys; SMTP account + creds; coach registration
  code (you generate). JWT auto-generated.
- **Counsel/CA:** finalize legal docs + governing-law clause (lawyer); GST/entity/tax at charging
  (CA).

---

## §49 exact questions

- **A. Feature branch merged?** Yes (see merge section).
- **B. main pushed?** Yes.
- **C. Repo prepared for a TRUE production env separate from staging?** Yes — distinct service + DB
  + config in `render.yaml`; staging preserved.
- **D. Render/Vercel resources the founder must create:** Render production Postgres + backend
  service; a Cloudflare R2 (or S3) bucket; an SMTP account; a Vercel frontend project.
- **E. Production env vars the founder must set:** backend `CORS_ORIGINS`, `TRUSTED_HOSTS`,
  `FRONTEND_BASE_URL`, `COACH_REGISTRATION_CODE`, `MEDIA_S3_BUCKET/REGION/ENDPOINT_URL`,
  `AWS_ACCESS_KEY_ID/SECRET`, `EMAIL_FROM/SMTP_HOST/USERNAME/PASSWORD`; frontend `VITE_APP_ENV=
  production`, `VITE_API_URL`, `VITE_LEGAL_*` + contact emails (+ optional `VITE_MIN_AGE`). JWT
  auto-generated.
- **F. `APP_ENV=production` shows NO staging indicator?** Yes — verified in a real browser.
- **G. `APP_ENV=staging` still shows STAGING?** Yes — verified in a real browser.
- **H. Production DB guaranteed separate from staging?** Yes — distinct `vytal-db-production`
  resource; staging DB never referenced by the production service.
- **I. System-only seed ready + demo contamination prevented?** Yes — release runs
  `scripts.seed_library` only; demo seed refused in production.
- **J. Will "quads" work immediately after deploy?** Yes — it relies on the system seed + the
  deterministic search engine, both included.
- **K. Coach can build/save workouts immediately?** Yes.
- **L. Custom exercises immediately?** Yes.
- **M. CSV/XLSX import production-ready?** Yes (hardened + tested).
- **N. Trainee Workout Execution production-ready?** Yes.
- **O. For real password-reset email:** configure SMTP (`EMAIL_SMTP_*` + `EMAIL_FROM`).
- **P. For durable media:** create a private R2/S3 bucket + set `MEDIA_S3_*` + `AWS_*`.
- **Q. Register a company/business before this beta?** No — a free one-coach beta needs no
  incorporation/GST/proprietorship registration.
- **R. Privacy/legal docs actually needed now?** Privacy Policy + consent (health data = SPDI);
  Terms + health disclaimer strongly recommended. Activate via the legal env values.
- **S. Recommended immediate age policy?** Adults only, 18+ (implemented).
- **T. To support younger trainees:** build verifiable guardian consent + tracking suppression +
  child-account linkage (see §10) — deferred.
- **U. Founder must do before deploying:** create the Render/Vercel/R2/SMTP resources + set env +
  fill legal values; follow the runbook.
- **V. Before charging:** GST at ₹20 lakh, entity/CA decision, LUT for exports, counsel-finalized
  docs.
- **W. Lawyer:** legal-doc wording + governing law + DPDP plan + under-18 (if pursued).
- **X. CA/accountant:** GST/entity/tax/payroll at charging/hiring.
- **Y. Is Vytal ready for the founder to deploy manually?** Yes.
- **Z. Another major app-code pass needed before the first coach can use it?** No — deployment is
  operational config + credentials only.

---

## §50 conservative scores (/10)

| Dimension | Score | Dimension | Score |
|---|---|---|---|
| Engineering quality | 8 | Operational readiness | 8 |
| Coach usability | 8 | Repository production readiness | 9 |
| Programming experience | 8 | Founder-deployment readiness | 9 |
| Exercise discovery | 8 | Controlled-beta readiness | 8 |
| Vytal visual identity | 8 | Broad commercial legal readiness | 4 |
| Mobile usability | 7 | Would the real coach enjoy using this? | 8 |
| Security readiness | 8 | Feels like a real product, not a staging project? | 8 |

## §42 readiness classification

1. **Repository production ready** — ✅ YES.
2. **Ready for founder deployment** — ✅ YES.
3. **Ready for founder-only production test** — ✅ YES (once resources created).
4. **Ready for controlled one-coach beta** — ✅ YES, after the founder activates the Privacy
   Policy (legal env values) and configures SMTP/media/DB per the runbook.
5. **Ready for additional invite-only coaches** — ✅ YES (same model scales to a few coaches).
6. **Ready for broad public / commercial launch** — ❌ NO — needs counsel-finalized legal docs,
   recorded consent acceptance, entity/GST decisions at charging, and (if targeting minors/EU/US)
   additional machinery.

**ACTUALLY DEPLOYED: NO** — deployment is the founder's manual step, by design.

## Final founder checklist

The single ordered checklist to deploy is in
[`docs/operations/production-launch.md`](../operations/production-launch.md) ("One-screen ordered
checklist"). Never paste real secrets into chat or commit them.
