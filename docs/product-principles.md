# Product principles and boundaries

These principles constrain every feature, calculation, and piece of copy in
FitIntel 360. They are binding product contracts, not aspirations. When a proposed
change conflicts with a principle, the change needs an explicit approved decision
(see [decisions/README.md](decisions/README.md)) — not a silent exception.

They fall into two groups. **Experience principles** govern how the product
presents guidance — what leads, what supports, and what is removed. **Boundary
principles** constrain what the product may compute, claim, store, or automate. A
change that satisfies every boundary can still fail the experience principles, and
is not shippable until it passes both; the Product Experience review evaluates the
experience principles explicitly.

## Experience principles

These govern how every screen, recommendation, and piece of copy is designed —
what leads, what supports, and what is removed. They are as binding as the
boundaries below and are checked explicitly in the Product Experience review.
Worked, per-screen applications of these principles live under
[design/](design/) — e.g. [design/trainee-today.md](design/trainee-today.md).

### Visual identity

The frozen visual identity is
[design/visual-identity-v2-iron-editorial.md](design/visual-identity-v2-iron-editorial.md)
(Iron Editorial, approved 2026-08-12). Its north star: **FitIntel should feel like
premium strength-training software with serious intelligence and a real coach behind it —
training should be seen, not merely described.** That document carries the binding visual/
product laws (training seen not described; implementation vocabulary vs. user intent;
visual traceability; authorship honesty; no-media completeness) and the Calm / Live /
Human register system, and it is the design authority for Experience Cycle 2. It refines
presentation; it does not relax any boundary principle below.

### Guidance over metrics

- **Guidance is the product; metrics justify it.** Users open FitIntel 360 to learn
  what to do, not to read numbers. Every screen leads with a recommendation or next
  action; scores, charts, and breakdowns exist to explain and support it.
- **Guidance wins conflicts.** When presenting more metrics competes with presenting
  clearer guidance, guidance takes precedence.
- **Evidence stays available, never dominant.** No number is hidden — provenance and
  component breakdowns remain reachable, consistent with the calculation-integrity
  boundary below — but supporting evidence must not out-weigh the recommendation it
  justifies. Prefer progressive disclosure over competition.

### One dominant answer

- **One primary question per screen.** Each screen answers a single most-important
  question, and a user should grasp that answer within about five seconds.
- **Hierarchy enforces the answer.** Visual weight, order, and emphasis reinforce the
  one takeaway; everything else is visibly secondary.
- **Competing sections are a smell.** If multiple sections claim equal attention, the
  screen is answering too many questions — reduce, combine, or progressively
  disclose until one answer dominates.

### Coach first

- **The coach is the expert; the software amplifies them.** Recommendations are
  framed as guidance from the trainee's coach, supported by explainable
  intelligence — never as advice from an algorithm, and never in a way that appears
  to replace the coach. This is the experiential half of the coaching-model boundary
  ([Coaching model](#coaching-model)); apply those autonomy limits rather than
  restating them.
- **Surface coach intent first.** Where a coach has authored intent — an assigned
  program, a workout's trainee instructions, a target effort — present it before
  system-generated explanation. Reuse existing coach-authored, deterministic content;
  do not invent a coach voice the coach did not write, and do not add AI to
  manufacture one.

### Calm intelligence

- **Reduce anxiety, don't manufacture it.** The interface is confident, supportive,
  and professional — not warning-heavy. Avoid alert fatigue: cap and rank concerns
  rather than stacking them.
- **Every concern carries an action.** A problem is never surfaced without a clear,
  calm next step.
- **Reinforce what is going well.** Where it is genuinely true, acknowledge progress
  before highlighting what needs attention. Positive reinforcement is deterministic
  too — surfaced from real inputs, never fabricated.

### Premium simplicity

- **Remove before adding.** New cards, sections, metrics, or controls must clearly
  improve a decision to earn a place. Before adding UI, first ask what existing
  element can be removed instead.
- **Restraint is a feature.** Whitespace is a primary layout tool; not every element
  needs its own container. Simple is the default; complexity must be justified.

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
