# Public demo workspace

The public demo is an explicitly enabled, synthetic, read-only evaluation workspace. **Explore
Demo** requests a short-lived normal role-scoped session from the backend; no credential, invite,
registration secret, or prebuilt token is exposed to the browser.

The demo includes deterministic scheduled, resumable, completed, partial, paused-for-safety, and
safety-ended workout examples; fresh, stale, and unavailable readiness; and open, acknowledged,
and resolved reports. The coach can inspect the safety queue and append-only review history. These
examples are for inspection only. Inputs and mutation controls are disabled, the page states
**Demo workspace — changes are disabled**, and direct calls to every workout or safety mutation
return `403 demo_read_only`.

Normal startup never creates demo records. The explicit seed command remains environment-gated,
idempotent, synthetic-only, and prohibited by production configuration. Frontend disabled states
are explanatory; backend role, ownership, assignment, and demo guards remain the security boundary.
