# Product principles and boundaries

These principles constrain every feature, calculation, and piece of copy in
FitIntel 360. They are binding product contracts, not aspirations. When a proposed
change conflicts with a principle, the change needs an explicit approved decision
(see [decisions/README.md](decisions/README.md)) — not a silent exception.

## Coaching model

- **Coach-assisted, not autonomous.** The product surfaces structured, explainable
  information to support a human coach's decisions. It does not coach
  autonomously, and it does not take training or health actions on a user's
  behalf.
- **Coaches remain responsible for authored Programs.** Programs, templates, and
  schedules are coach-authored artifacts. The platform records and versions them;
  it does not generate or alter them automatically.
- **No autonomous adjustment from readiness or analytics.** Readiness context and
  analytics never change programs, schedules, sets, loads, progression, or deload
  weeks. Any future automated rule requires an approved, deterministic,
  clearly-communicated design.

## Calculation integrity

- **Deterministic and explainable.** Every score and analytic is a deterministic
  function of persisted inputs, reproducible from the same data.
- **Versioned.** Each calculation carries a version string (e.g.
  `health-index-v1`, `daily-intelligence-v1`, `workout-load-v1`) and a
  corresponding document. Changing a formula means a new version, not an in-place
  edit.
- **User-visible provenance.** Results show what they were computed from and which
  version produced them. No black-box numbers.
- **Explicit missing-data behavior.** Absent inputs are shown as unavailable — never
  fabricated, interpolated, or silently defaulted to `0`.

## Medical boundaries

- **No medical diagnosis.** The product does not diagnose conditions or interpret
  symptoms clinically.
- **No medical clearance.** Readiness context does not authorize, gate, or prohibit
  exercise, and must never be presented as clearance to train.
- **Safety reports are not continuously monitored.** They are asynchronous records
  reviewed by the assigned coach; they do not trigger urgent or emergency
  response. Copy must not imply monitored urgent care.
- **Readiness is contextual information.** It is informational context captured at a
  point in time, nothing more.
- **Training load is not a medical measure.** It is deterministic bookkeeping
  derived from prescribed and recorded workout data.

## Data and history

- **Immutable historical execution.** Terminal workout sessions, prescription
  snapshots, safety reports, load summaries, readiness contexts, and submitted
  baselines are immutable through the product. Post-completion correction is a
  deferred, unapproved slice.
- **Immutable versioning of authored content.** Published exercise, template, and
  program versions are immutable; downstream references pin exact versions.

## Privacy and testing

- **Privacy by default.** Collect only what a feature needs; minimize sensitive
  fields; keep self-reported notes and raw health values out of normal logs;
  scope every read/write by identity server-side.
- **Synthetic data whenever possible.** Public demo identities are synthetic.
  Controlled real-user testing should still prefer synthetic or non-sensitive
  data; testers must not enter unnecessary sensitive health information. See
  [testing/real-user-testing.md](testing/real-user-testing.md).
- **No unsupported compliance claims.** The repository does not claim HIPAA, GDPR,
  SOC 2, or medical-device compliance. Do not add such claims without verified
  evidence.

## Terminology discipline

Use the vocabulary in [domain-glossary.md](domain-glossary.md) consistently. In
particular:

- Program content is a **coaching plan**, never a *medical prescription*.
- Use **recorded best**, never *PR*, *personal record*, *lifetime*, or *all-time*.
- Self-entered credentials and self-reported data are **not verified**; never
  present them as verified.
