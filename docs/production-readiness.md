# Vytal production readiness (Parts 50–60)

Status as of this pass. Distinguishes **technically production-ready** (engineering) from
**cleared for broad public commercial launch** (needs counsel + founder inputs — see
[legal/README.md](legal/README.md)).

## Environment model — IMPLEMENTED

`APP_ENV` selects `local` | `test` | `staging` | `production` (`app/config.py`). Provenance is
**truthful**, not cosmetic:

- The frontend staging banner renders only when `VITE_APP_ENV=staging` — production resolves
  `production` and shows no banner; it is not hidden by CSS or hostname.
- `config.secure_deployed_environment` makes a deployed app **fail to start** unless:
  PostgreSQL (not SQLite), a non-default `JWT_SECRET`, explicit **HTTPS** `CORS_ORIGINS`,
  explicit `TRUSTED_HOSTS` (no `*`), `API_DOCS_ENABLED=false`, database TLS
  (`sslmode=require`+), and a non-default demo invite code.
- Production additionally forbids `SEED_DEMO_DATA`, `DEMO_MODE_ENABLED`, and a `local` media
  provider.

## Security posture — IMPLEMENTED

- Security headers on every response; HSTS in deployed environments; strict CSP (docs exempt in
  local only). See `app/security_headers.py`.
- Rate limiting on auth/registration/invite/demo/import endpoints in deployed environments. See
  `app/rate_limit.py`. **Follow-up:** shared-store limiter for a strict multi-instance global
  limit (documented on the Security page).
- Server-side authorization with 404 on cross-account; tenant boundaries enforced in code.
- Bcrypt password hashing; signed, expiring tokens; per-handler demo-write protection.

## Seeding split — IMPLEMENTED (Part 54)

- **System content** (curated exercise/template/program library): `python -m scripts.seed_library`
  (`seed_starter_library`) — idempotent, seeds a system library account, **no demo users**. Safe
  for production.
- **Demo data** (demo coach/trainee, synthetic histories): `scripts/seed.py`, gated behind
  `SEED_DEMO_DATA=true` and **refused in production** by config. Never mixed with system content.

## Launch inputs still required (Parts 53, 56, 60, 65–66)

These are external inputs; they are intentionally **not invented** in the repo.

1. **Durable media provider (Part 60) — IMPLEMENTED; credentials are the launch input.** An
   S3-compatible provider (AWS S3 / Cloudflare R2) is implemented behind the storage abstraction
   (`app/storage/s3.py`), selected by `MEDIA_STORAGE_PROVIDER=s3`, delivering media through the
   same authorized streaming endpoint (private objects, no public/pre-signed URLs). boto3 is an
   optional extra (`pip install .[s3]`); production config requires `MEDIA_S3_BUCKET`. Remaining
   launch input: **a bucket + S3/R2 credentials** (via boto3's env chain — `AWS_ACCESS_KEY_ID` /
   `AWS_SECRET_ACCESS_KEY`, and `MEDIA_S3_ENDPOINT_URL` for R2). See
   [research/exercise-media-strategy.md](research/exercise-media-strategy.md).
2. **Canonical domain + DNS (Part 56).** Founder brand reference is `joinvytal`; the full hostname
   is not verified in the repo and must not be guessed. Set production `CORS_ORIGINS` /
   `TRUSTED_HOSTS` / `VITE_API_URL` from the real domain at cutover.
3. **Production secrets (Part 58).** Fresh `JWT_SECRET`, database URL + TLS, coach registration
   code, media credentials — distinct from local/staging, provided via the platform secret store
   (`sync:false`), never committed.
4. **Transactional email + self-service password reset (Parts 65–66) — IMPLEMENTED; SMTP
   credentials are the launch input.** An email provider seam (`app/email/`) selects
   `console` (local preview) or `smtp` (stdlib `smtplib`, no new dependency) by environment;
   a deployed environment **must not** use `console` and requires `EMAIL_SMTP_HOST`, a real
   `EMAIL_FROM`, and an HTTPS `FRONTEND_BASE_URL` (fail-fast). Self-service reset
   (`POST /auth/password-reset/request` + `/confirm`, `/forgot-password` + `/reset-password`
   pages) issues hashed, expiring, single-use tokens with a generic no-enumeration response,
   rate-limited, never logging the token. The operator CLI (`scripts/reset_password.py`)
   remains. Remaining launch input: **an SMTP provider (host + credentials + sender)**.
5. **Production topology in `render.yaml` (Parts 50, 53) — IMPLEMENTED.** A distinct
   `vytal-api-production` web service + its own `vytal-db-production` Postgres (never the
   staging DB) are defined alongside staging: `APP_ENV=production`, durable S3/R2 media,
   SMTP email, demo off, `branch: production` with **manual** deploys, and a release command
   that runs `alembic upgrade head && python -m scripts.seed_library` (system content only,
   never the demo seed). Every value that encodes the (undecided) domain or a secret is
   `sync:false` — set in the dashboard at cutover; the manifest invents no domain/TLD.
6. **Terms/Privacy acceptance record (Part 76).** Registration does not yet capture a versioned
   acceptance timestamp; add once the legal documents are counsel-approved and versioned.

## What a production cutover looks like (once inputs are met)

The `vytal-api-production` service + `vytal-db-production` blueprint in `render.yaml` encodes
most of this; the steps below are the human inputs and verification.

1. Create the `production` branch and provision the production Postgres (its own instance, TLS).
2. Configure the media bucket + S3/R2 credentials (`MEDIA_S3_BUCKET`/`_REGION`/`_ENDPOINT_URL`,
   `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`).
3. Configure the SMTP provider (`EMAIL_SMTP_HOST`/`_USERNAME`/`_PASSWORD`, real `EMAIL_FROM`).
4. Set the domain-derived values from the real hostname: `CORS_ORIGINS`, `TRUSTED_HOSTS`,
   `FRONTEND_BASE_URL` (backend) and `VITE_APP_ENV=production` + `VITE_API_URL` (frontend);
   set a fresh `JWT_SECRET` and the coach registration code. `API_DOCS_ENABLED=false`; demo off.
5. The release command runs migrations then `python -m scripts.seed_library` (system content
   only) — **never** the demo seed (config refuses it in production).
6. Reconsider the frontend `X-Robots-Tag: noindex, nofollow` in `frontend/vercel.json` — correct
   for staging, but a public production site is usually indexable (a founder/marketing decision).
7. Verify: no staging banner, security headers + HSTS present, `/health/ready` green, demo routes
   absent, cross-account requests 404, and a password-reset request delivers a real email.

**Scale note:** the in-process rate limiter is correct only at one replica. Do not scale the
production service horizontally without first moving to a shared-store (or edge) limiter.
