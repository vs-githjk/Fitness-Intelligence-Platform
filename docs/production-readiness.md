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

1. **Durable media provider (Part 60).** Production config rejects `MEDIA_STORAGE_PROVIDER=local`
   (ephemeral filesystem). A production deploy needs an object-store provider (e.g. S3-compatible
   / Cloudflare R2) implemented behind the existing media abstraction, plus credentials. Until
   then, production media is a blocker. See [research/exercise-media-strategy.md](research/exercise-media-strategy.md).
2. **Canonical domain + DNS (Part 56).** Founder brand reference is `joinvytal`; the full hostname
   is not verified in the repo and must not be guessed. Set production `CORS_ORIGINS` /
   `TRUSTED_HOSTS` / `VITE_API_URL` from the real domain at cutover.
3. **Production secrets (Part 58).** Fresh `JWT_SECRET`, database URL + TLS, coach registration
   code, media credentials — distinct from local/staging, provided via the platform secret store
   (`sync:false`), never committed.
4. **Transactional email + self-service password reset (Parts 65–66).** No email provider is wired;
   reset is operator-assisted today. Self-service reset needs an email provider + token flow
   (hashed, expiring, single-use). Provider credentials are a launch input.
5. **Production topology in `render.yaml` (Parts 50, 53).** Only staging is defined today. A
   production web service + its own Postgres (never the staging DB) should be added once (1)–(3)
   are available, so the committed manifest cannot imply a deployable production that would fail
   config validation on media.
6. **Terms/Privacy acceptance record (Part 76).** Registration does not yet capture a versioned
   acceptance timestamp; add once the legal documents are counsel-approved and versioned.

## What a production cutover looks like (once inputs are met)

1. Provision production Postgres (TLS) and set secrets in the platform store.
2. Configure a durable media provider + credentials.
3. Set `APP_ENV=production`, HTTPS `CORS_ORIGINS`/`TRUSTED_HOSTS`, `VITE_APP_ENV=production`,
   `VITE_API_URL` to the real API origin; `API_DOCS_ENABLED=false`; demo disabled.
4. Run migrations (`alembic upgrade head`) then `python -m scripts.seed_library` (system content
   only). Do **not** run the demo seed.
5. Verify: no staging banner, security headers + HSTS present, `/health/ready` green, demo routes
   absent, cross-account requests 404.
