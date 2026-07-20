# Feedback and bug-triage process

How tester feedback and bug reports are classified, reported, and acted on during
controlled real-user testing. Pairs with
[real-user-testing.md](real-user-testing.md).

> Feedback informs the backlog. It does **not** by itself authorize changes to
> deterministic formulas, database schema, or security/authorization behavior.
> Those require an explicit approved decision (see
> [../decisions/README.md](../decisions/README.md)).

## Severity levels

### P0 — critical
- Privacy or security incident.
- Unauthorized access to another account's data.
- Data corruption.
- Critical outage (primary product unavailable).

### P1 — high
- A primary flow is unusable.
- A materially incorrect result (e.g. wrong analytics classification or score).
- A coach or trainee operation is blocked.

### P2 — medium
- A non-critical functional defect.
- A confusing workflow.
- A degraded mobile or accessibility experience.

### P3 — low
- A suggestion.
- A cosmetic issue.
- A future enhancement.

## Required report fields

- Reporter role (coach / trainee / maintainer).
- Environment (local / staging / other).
- Account type (public demo / private test).
- Date and time with timezone.
- Page or flow.
- Expected behavior.
- Actual behavior.
- Reproduction steps.
- Screenshots **with private data removed** (never include secrets).
- Browser and device.
- Suggested severity.
- Frequency (always / intermittent / once).
- Related IDs only when safe to share (never credentials or tokens).

## Triage behavior

- **P0 stops feature work.** Contain first (protect data and access), then
  diagnose and remediate. Follow the incident guidance in
  [../operations/deployment-and-recovery.md](../operations/deployment-and-recovery.md).
- **P1 enters immediate patch assessment.** Evaluate for a focused patch release
  per the [release runbook](../operations/release-runbook.md).
- **P2 enters the stabilization backlog.** Scheduled alongside ongoing milestone
  work; may be batched.
- **P3 enters the product-discovery backlog.** Considered during milestone scoping;
  never auto-approved.

The continuous stabilization/tester-feedback track runs in parallel with roadmap
milestones; P0/P1 issues may interrupt milestone work.

## What feedback does not authorize

- It does not authorize changing a scoring/analytics formula (that needs a new
  versioned calculation and documentation).
- It does not authorize schema redesigns or rewriting historical migrations.
- It does not authorize weakening authorization, invitation security, or demo
  protection.
- It does not authorize adding AI, medical, or autonomous features.

## Privacy in triage

- Keep sensitive body content out of issues and logs.
- Redact screenshots and quoted values before attaching.
- Do not share production/staging database exports with coding agents or paste
  them into issues.
- Route suspected security/privacy incidents through the security-concern process
  (see the security issue template) rather than a public bug report.
