# Vytal — Founder production launch runbook

**You deploy Vytal yourself.** This document is the exact, ordered checklist. Claude prepared
the repository and configuration but does **not** provision infrastructure, create accounts,
touch DNS, or deploy. Nothing here contains a real secret — you generate and paste secrets
directly into Render/Vercel, never into a chat or a committed file.

**Launch model:** controlled, invite-only **one-coach beta**. No public registration, no billing.

**Three distinct states — know which one you are in:**
1. **Repository production-ready** — ✅ done (this branch, merged to `main`).
2. **Ready for founder deployment** — ✅ you can follow this runbook end-to-end.
3. **Actually deployed** — ❌ NO until you complete the steps below yourself.

---

## 0. What you must decide / obtain first (external inputs)

| Input | Needed for | Notes |
|---|---|---|
| A hosting account on **Render** | backend + Postgres | free/starter tiers work to start |
| A hosting account on **Vercel** | frontend | hobby tier works to start |
| An **object storage** bucket (Cloudflare **R2** recommended, or AWS S3) | exercise media | R2 has no egress fees; simplest for a beta |
| An **SMTP** provider (e.g. **Resend**, **Postmark**, **Brevo**, or AWS SES) | invites + password reset | free/low-volume tier is fine for one coach |
| Your **legal identity values** (see §7) | activating the Privacy Policy/Terms | for a solo beta this is *you personally* + a real address + a monitored inbox |
| The exact **production domain** (`joinvytal…`) | custom-domain cutover | **not required to launch** — you can run on the Render/Vercel default URLs first (§6) |

You do **not** need to incorporate a company, register for GST, or register a sole
proprietorship to run a **free** one-coach beta (see the legal summary in §7 and the full
research in the final report). You **do** need a live Privacy Policy because you handle health
data — that is why §7 is mandatory before the first real trainee.

---

## A. Backend + database (Render)

The repo already defines the production topology in [`render.yaml`](../../render.yaml) as
`vytal-api-production` (web service) + `vytal-db-production` (Postgres), **separate from staging**.

1. **Create the production Postgres** — Render → New → Postgres. Name it `vytal-db-production`
   (or match `render.yaml`). Region: pick one near you (e.g. Singapore). Choose a **paid**
   instance if you want automated daily backups (see §D). Do **not** reuse the staging DB.
2. **Create the backend web service** from `render.yaml` (Render → New → Blueprint, pointed at
   your repo/`production` branch) **or** manually as a Docker web service using
   `backend/Dockerfile`. `DATABASE_URL` and `MIGRATION_DATABASE_URL` bind automatically to the
   production DB via the blueprint.
3. **Set the environment variables** (Render dashboard → the service → Environment). The ones
   marked *you set* below are `sync:false` in the blueprint; the rest are already fixed or
   auto-generated:

   **Auto / fixed (already in `render.yaml`):** `APP_ENV=production`, `JWT_SECRET`
   (**Render auto-generates** a strong value — you do not create it), `DATABASE_URL`,
   `MIGRATION_DATABASE_URL`, `DEMO_MODE_ENABLED=false`, `SEED_DEMO_DATA=false`,
   `MEDIA_STORAGE_PROVIDER=s3`, `EMAIL_PROVIDER=smtp`, `API_DOCS_ENABLED=false`,
   `DATABASE_SSLMODE=require`, `ACCESS_TOKEN_MINUTES=60`, `PASSWORD_RESET_TOKEN_MINUTES=60`.

   **You set (secrets/domain):**
   - `CORS_ORIGINS` — the exact HTTPS origin of the frontend, e.g. `https://<your-vercel-app>.vercel.app` (comma-separated if more than one). Must be HTTPS, no `*`.
   - `TRUSTED_HOSTS` — the backend host, e.g. `vytal-api-production.onrender.com`.
   - `FRONTEND_BASE_URL` — the frontend origin (used in password-reset links), e.g. `https://<your-vercel-app>.vercel.app`.
   - `COACH_REGISTRATION_CODE` — a strong random string (see §C for how to generate). Keeps coach registration invite-only.
   - `MEDIA_S3_BUCKET`, `MEDIA_S3_REGION`, `MEDIA_S3_ENDPOINT_URL` (R2 only), `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` — from §B.
   - `EMAIL_FROM` (e.g. `Vytal <no-reply@yourdomain>`), `EMAIL_SMTP_HOST`, `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD` — from §E.

4. **Migrations + system seed run automatically on deploy.** The blueprint's
   `preDeployCommand` is `alembic upgrade head && python -m scripts.seed_library` — this creates
   the schema and installs the **system** starter library (100+ exercises, templates, programs)
   **only**. It never seeds demo/fake users. If deploying manually instead of via blueprint, run
   that same command as your release/pre-deploy step.
5. **The service refuses to start if misconfigured** — production fails fast unless Postgres (not
   SQLite), a non-default `JWT_SECRET`, HTTPS `CORS_ORIGINS`, explicit `TRUSTED_HOSTS`, TLS,
   real SMTP host + sender, and an HTTPS `FRONTEND_BASE_URL` are all present. This is by design.
6. **Health checks:** `GET /health/ready` (readiness, checks the DB) and `GET /health/live`
   (liveness). The blueprint uses `/health/ready`.

⚠️ **Never run `python -m scripts.seed`** (the demo seed) in production — it is refused by config,
but do not attempt it. Only `scripts.seed_library` is production-safe.

---

## B. Object storage for media (Cloudflare R2 recommended)

Vytal serves media through an **authorized streaming endpoint** — objects stay **private**, there
are no public/pre-signed URLs. Local disk is development-only.

1. Create a bucket (Cloudflare R2: Dashboard → R2 → Create bucket, e.g. `vytal-media-prod`).
2. Create an **API token / access key** scoped to that bucket → gives an Access Key ID + Secret.
3. In Render backend env, set: `MEDIA_S3_BUCKET=vytal-media-prod`, `MEDIA_S3_REGION=auto`
   (R2) or your AWS region, `MEDIA_S3_ENDPOINT_URL=https://<accountid>.r2.cloudflarestorage.com`
   (**R2 only — leave unset for AWS S3**), `AWS_ACCESS_KEY_ID=…`, `AWS_SECRET_ACCESS_KEY=…`.
4. Keep the bucket **private** (no public access). Vytal signs/streams reads through the API.
5. The backend Docker image installs the `boto3` extra; no code change needed.

---

## C. Coach registration code + JWT secret (secrets)

- **JWT secret:** with the blueprint, Render **auto-generates** `JWT_SECRET` — you do nothing.
  If you ever set it manually, generate a strong value locally and paste it into Render only:
  `openssl rand -base64 48` (never commit it, never paste it into chat).
- **Coach registration code:** generate one and set `COACH_REGISTRATION_CODE` in Render:
  `openssl rand -base64 24`. This is the private code the coach needs to create their account
  (see §F). Keep it out of logs and out of the repo.

---

## D. Database backups

Render **managed Postgres provides automated daily backups on paid instances**; point-in-time
recovery and longer retention depend on the plan. **Verify the exact backup/retention/PITR terms
of the specific Render Postgres plan you choose at signup** — do not assume the free tier backs
up. A real coach's data must not be disposable: pick a plan with automated backups, confirm the
retention window, and note the restore procedure from Render's dashboard before onboarding the
coach.

---

## E. Transactional email (SMTP)

Needed for **trainee invitations** and **password reset**. Without it those emails silently do
not send (the app still works otherwise; password reset still issues tokens but can't deliver
them).

1. Create an account with a low-volume provider (Resend / Postmark / Brevo / AWS SES).
2. Verify a sender address (and later your domain — see §G for DNS).
3. Get SMTP credentials (host, port 587, username, password/API key).
4. Set in Render backend env: `EMAIL_SMTP_HOST`, `EMAIL_SMTP_PORT=587` (already default),
   `EMAIL_SMTP_USERNAME`, `EMAIL_SMTP_PASSWORD`, `EMAIL_FROM` (e.g. `Vytal <no-reply@yourdomain>`).
5. Test with the forgot-password flow after deploy (§H).

---

## F. Frontend (Vercel)

1. Import the repo into Vercel; set the **root directory** to `frontend/`. Framework: Vite.
   Build command `npm run build`, output `dist` (Vercel auto-detects). `frontend/vercel.json`
   already sets SPA rewrites + security headers.
2. **Environment variables** (Vercel → Project → Settings → Environment Variables, Production):
   - `VITE_APP_ENV=production` — makes the app production (no STAGING banner). **Required.**
   - `VITE_API_URL=https://<render-backend-host>/api/v1` — the production API base. **Required**,
     must be a **non-local HTTPS** URL (the build throws otherwise).
   - **Legal identity (activates the Privacy Policy/Terms — see §7):** `VITE_LEGAL_ENTITY`,
     `VITE_LEGAL_ADDRESS`, `VITE_LEGAL_JURISDICTION`, `VITE_LEGAL_EFFECTIVE_DATE`,
     `VITE_PRIVACY_EMAIL`, `VITE_SECURITY_EMAIL`, `VITE_SUPPORT_EMAIL`. Until all are set, the
     legal pages show a truthful "pending final details" notice (they never show placeholders).
   - `VITE_MIN_AGE` — optional; **defaults to 18** (adults-only). Do not lower it without the
     guardian-consent machinery described in §7.
3. Deploy. Note the Vercel URL — put it into the backend `CORS_ORIGINS` and `FRONTEND_BASE_URL`
   (§A) and redeploy the backend if you set those after the frontend existed.
4. **`X-Robots-Tag: noindex, nofollow`** in `vercel.json` is correct for staging. For a public
   production site you'll usually want it indexable — decide this and adjust before public launch
   (not required for a private one-coach beta).

---

## G. Custom domain (later — not required to launch)

Vytal runs on the Render/Vercel default URLs today. When you're ready to attach `joinvytal…`:
1. Vercel → Domains → add the frontend domain; follow the DNS records Vercel shows.
2. (Optional) Add a custom API subdomain in Render; update `VITE_API_URL` to it.
3. Update backend `CORS_ORIGINS`, `TRUSTED_HOSTS`, `FRONTEND_BASE_URL` to the new origins; redeploy.
4. Add the **email domain DNS** (SPF/DKIM/DMARC from your SMTP provider) so mail from your domain
   delivers.
5. Verify HTTPS is issued, then re-run the smoke test (§H). **No application code change is needed.**

---

## H. Post-deploy smoke test (run after your deploy)

**Environment**
- [ ] Open the app — **no STAGING banner** anywhere.
- [ ] No demo accounts/data exist (you never ran the demo seed).
- [ ] `GET /health/ready` returns `{"status":"ready"}`.

**Auth**
- [ ] Register the real coach with the `COACH_REGISTRATION_CODE` (§F below), sign in, sign out.
- [ ] Invalid login is rejected.
- [ ] Forgot-password → the reset email arrives (confirms SMTP), the link resets the password.

**Coach**
- [ ] Overview loads. Programming loads.
- [ ] Search **"quads"** returns quad-focused exercises (proves the system seed loaded).
- [ ] Create a workout template; add 5 exercises; reorder; edit a prescription; save; publish.
- [ ] Create a custom exercise inline in the picker.
- [ ] CSV import and XLSX import both work.
- [ ] Settings loads.

**Media**
- [ ] Upload an exercise image; view it; remove it (proves R2/S3 wiring).

**Trainee** (optional — invite a test trainee you control)
- [ ] Today loads; start a workout; log a set; rest timer; complete.

**Legal**
- [ ] Once you set the legal env values, `/privacy`, `/terms`, `/security` show real details (no
      "pending" notice, no placeholders).

---

## First real coach onboarding (§F flow)

1. In Render, confirm `COACH_REGISTRATION_CODE` is set (§C).
2. Send the coach the frontend URL + the registration code (share the code privately, not by
   email if avoidable).
3. Coach opens `/register`, chooses **Coach**, enters name/email/password + the registration code.
4. Coach signs in; you can verify the account/role in the coach Overview.
5. The coach invites trainees from **Invitations** (single-use invite links). No public
   registration is enabled.

---

## §7. Legal / privacy — what you must do before the first real trainee

Full research with sources is in [`docs/reports/final-production-readiness-2026-08.md`](../reports/final-production-readiness-2026-08.md).
Summary of what is **mandatory now** vs later:

**Mandatory before a real trainee enters health data (because fitness/health data is
"sensitive personal data" under India's currently-operative IT Act / SPDI Rules):**
- [ ] **Activate the Privacy Policy** by setting the `VITE_LEGAL_*` + contact env values (§F).
      For a free solo beta the "operator" is **you, personally** (no company needed); use a real
      mailing address and a monitored inbox.
- [ ] **Capture consent at signup** conceptually — the auth pages already link to the policies;
      before broader launch, add a recorded acceptance (deferred — see below).
- [ ] Keep the beta **18+** (already enforced as the default and the assessment floor).

**Not required for a free one-coach beta:** company incorporation, GST registration, sole-
proprietorship registration, a consumer-health-data notice, or a cookie banner (Indian law).

**CERT-In basics (cheap, do now):** point servers at NIC/NPL NTP time; keep ≥180-day logs; know
the 6-hour incident-reporting duty (`incident@cert-in.org.in`).

**Needs a professional before you rely on it:** a lawyer to finalize the Privacy Policy / Terms /
health-disclaimer wording and the **governing-law clause** (don't hard-code Tamil Nadu — counsel
ties it to your entity + consumer-protection law); a CA/accountant **before you start charging**
(GST timing at ₹20 lakh turnover, entity choice, export-of-services LUT).

**Deferred engineering (before broader/commercial launch, not now):** a recorded, versioned
Terms/Privacy **acceptance record** (build it only against finalized, counsel-reviewed policies —
not against pending values); a hard date-of-birth **18+ gate at signup**; guardian-consent
machinery **if** you ever decide to support under-18 trainees.

---

## One-screen ordered checklist

1. Create production Postgres on Render (paid tier for backups).
2. Create the backend service (blueprint or Docker); confirm it binds the production DB.
3. Set backend env: `CORS_ORIGINS`, `TRUSTED_HOSTS`, `FRONTEND_BASE_URL`, `COACH_REGISTRATION_CODE`.
4. Create an R2/S3 bucket; set `MEDIA_S3_*` + `AWS_*` keys.
5. Create an SMTP account; set `EMAIL_SMTP_*` + `EMAIL_FROM`.
6. Deploy backend → migrations + **system-only** seed run automatically.
7. Verify `GET /health/ready`.
8. Create the Vercel frontend (root `frontend/`); set `VITE_APP_ENV=production`, `VITE_API_URL`,
   and the `VITE_LEGAL_*` + contact values.
9. Deploy frontend; put its URL into backend `CORS_ORIGINS`/`FRONTEND_BASE_URL`; redeploy backend.
10. Confirm **no STAGING banner** and **no demo data**.
11. Set `COACH_REGISTRATION_CODE`; invite/register the first real coach.
12. Smoke test: "quads" search, build+save a workout, custom exercise, CSV/XLSX import, media
    upload, forgot-password email.
13. Later: attach the `joinvytal` domain, update origins/CORS + email DNS, re-smoke.
14. Begin the controlled one-coach beta.
