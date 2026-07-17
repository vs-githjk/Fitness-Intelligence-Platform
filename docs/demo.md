# Public demo workspace

The public demo is an explicitly enabled, synthetic, read-only evaluation workspace. **Explore
Demo** requests a short-lived normal role-scoped session from the backend; no credential, invite,
registration secret, or prebuilt token is exposed to the browser.

The demo includes deterministic scheduled, resumable, completed, partial, paused-for-safety, and
safety-ended workout examples; fresh, stale, and unavailable readiness; and open, acknowledged,
and resolved reports. One demo trainee has a fully completed resistance workout with kg and lb sets,
producing recorded bests, resistance volume, and completed session load for the Workout Intelligence
analytics. The demo therefore exercises completed, partial (including a partial with zero completed sets and a
partial with some completed work), explicit ordinary and wellbeing-related pre-start skips, missed,
cancelled, superseded, and optional workout classifications, planned/completed and unavailable load,
and adherence variation. The skip examples prove that skipped requires an explicit persisted skip
state and that a started-and-ended session stays partial regardless of logged work. Demo trainees and the demo coach can inspect all read-only Workout Intelligence
analytics (training load, adherence, recorded bests, coach session review). The coach can inspect the
safety queue and append-only review history. These examples are for inspection only. Inputs and
mutation controls are disabled, the page states **Demo workspace — changes are disabled**, and direct
calls to every workout or safety mutation return `403 demo_read_only`. Phase 7B adds no new mutation
endpoints — every analytics route is a read-only GET.

Normal startup never creates demo records. The explicit seed command remains environment-gated,
idempotent, synthetic-only, and prohibited by production configuration. Frontend disabled states
are explanatory; backend role, ownership, assignment, and demo guards remain the security boundary.
