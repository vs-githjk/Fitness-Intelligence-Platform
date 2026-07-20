# Real-user testing guide

This guide governs controlled testing of FitIntel 360 with a small set of real
(non-demo) test users, running alongside ongoing development. It complements the
synthetic [private-beta plan](private-beta-plan.md); where that plan describes a
synthetic-only cohort, this guide covers the current small real-tester setup.

> This is not a production launch. The repository does not claim HIPAA, GDPR,
> SOC 2, medical-device, or other regulatory compliance. Do not collect real
> health data beyond what testing genuinely requires. See
> [product-principles.md](../product-principles.md) and [security.md](../security.md).

## Current test setup

- **One real coach test account.**
- **Four real trainee test accounts.**
- Testing occurs continuously while later milestones are developed.
- These test users are **distinct from the public demo accounts**. Demo accounts
  are public, synthetic, and read-only; test accounts are private real identities
  that can perform normal mutations.

## Goals of testing

- Exercise real end-to-end coach and trainee flows with genuine (not seeded)
  usage patterns.
- Surface usability, correctness, accessibility, and mobile issues before wider
  rollout.
- Validate that authorization, cache isolation, and demo protection hold under
  real multi-account use.
- Feed prioritized, well-formed feedback into triage (see
  [feedback-triage.md](feedback-triage.md)).

Testing does **not** authorize formula, schema, or security changes on its own,
and does not authorize new AI, medical, or autonomous behavior.

## Test-user onboarding

1. The coach registers with the backend-gated coach registration code (never
   shared in issues, screenshots, or chat) and signs in.
2. The coach creates single-use trainee invitations and shares each code/link
   privately with the intended tester (FitIntel 360 does not send invitation
   emails).
3. Each trainee redeems their own invitation, completes onboarding, and is
   assigned to the coach.
4. Set expectations up front (below) before any real data is entered.

## Data-handling rules for testers

- **Prefer synthetic or non-sensitive data.** Use realistic-but-invented values
  wherever a real value is not necessary for the test.
- **Do not enter unnecessary sensitive health information.** Only enter what a
  specific test actually requires.
- Self-reported values and self-entered credentials are **not verified**; do not
  treat them as authoritative.
- **No secrets in screenshots or issues** — no passwords, tokens, invitation
  codes, or the coach registration code.
- Remove or redact private data from any screenshot or log before sharing.

## Consent and expectation setting

Before a tester enters real information, make clear that:

- This is pre-release test software that may change or reset without notice.
- Entered content may exist in database backups and operational records.
- The product provides **no medical diagnosis and no medical clearance**; safety
  reports are reviewed asynchronously by the coach and are **not** continuously or
  urgently monitored.
- In a real emergency or for medical concerns, contact appropriate professional or
  emergency services — do not rely on this product.
- Data can be reset or the account offboarded on request (below).

## Supported testing scenarios

- Coach: registration/login, trainee invitation, roster, trainee detail,
  programming (exercises, templates, programs), assignment/scheduling, safety
  inbox and acknowledgement/resolution, read-only workout session review, and
  load/adherence/recorded-best analytics and explicit-skip visibility.
- Trainee: invitation redemption, onboarding, daily check-in, Today dashboard,
  scheduled workout calendar and detail, explicit ordinary and wellbeing skip,
  workout execution across the five tracking modes, resume, completion, incomplete
  ending, safety reporting, readiness display, and workout analytics.
- Cross-cutting: mobile layouts (320/390/768/desktop), keyboard/focus behavior,
  and identity transitions (login/logout, and confirming no stale data crosses
  identities).

## Account separation and safety

- **One identity per tester.** No credential sharing between testers.
- Testers see only their own data; a coach sees only trainees with an active
  assignment. Report immediately (as a P0) any case where one account can see
  another's data.
- Do not attempt to access another tester's records by guessing identifiers; if
  such access appears possible, stop and report it privately.

## Reporting issues and capturing reproductions

- File issues using the repository issue templates; classify severity per
  [feedback-triage.md](feedback-triage.md).
- Capture: role, environment, account type (demo/test), local date-time and
  timezone, page/flow, expected vs. actual behavior, exact reproduction steps,
  browser/device, and frequency.
- Attach screenshots only after removing private data; never attach secrets.
- Reference only IDs that are safe to share; never paste credentials or tokens.

## Destructive-action cautions

- Some actions are irreversible by design (completing or ending a workout,
  submitting a safety report, publishing a version). Terminal execution and
  submitted records are immutable — there is no post-completion correction.
- Treat "complete", "end incomplete", "submit", and "publish" as final during
  testing.

## Test-data reset and offboarding

- **Reset:** on request, a maintainer can reset a test user's data. Because
  historical execution is immutable, "reset" generally means provisioning a fresh
  test identity rather than editing history in place.
- **Offboarding:** on request, disable the account so it can no longer sign in and
  stop assigning new work to it.
- **Deletion:** authenticated self-service export/deletion workflows are a
  hardening-phase item and do not yet exist; deletion is currently a manual
  maintainer operation. Set tester expectations accordingly and record deletion
  requests until a supported workflow exists.

## Known limitations

- Local-storage JWTs; no rate limiting, email verification, MFA, or audit trail
  yet (see [security.md](../security.md)).
- No in-app messaging or notifications; coordinate out of band.
- No self-service export/deletion; no post-completion correction.
- Analytics windows are backward-looking; recorded bests use available completed
  history only.

## Emergency / support disclaimer

FitIntel 360 is not a medical or emergency service. It does not monitor users, and
safety reports are not watched in real time. For any medical concern, injury, or
emergency, testers should seek appropriate professional or emergency help
independently of this product.
