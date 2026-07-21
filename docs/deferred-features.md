# Deferred-feature register

Capabilities that are intentionally **not** built. This register exists so agents
and contributors do not implement them opportunistically.

> **"Deferred" does not mean approved.** A deferred item is out of scope until it
> is explicitly scoped, approved, and sequenced (see [roadmap.md](roadmap.md) and
> [decisions/README.md](decisions/README.md)). Do not implement any item here as a
> side effect of adjacent work.

| Feature | Why deferred | Notes |
| --- | --- | --- |
| Post-completion corrections | Historical execution is immutable (ADR-0003) | Would need an approved, audited correction contract |
| Automated progression | Coaches own programming (product principles) | Any rule must be approved, deterministic, and communicated |
| Automated deload generation | Same as above | Deloads are coach-authored today |
| AI coaching / narration | Requires explicit approved decision + privacy/red-team review | Never add AI merely because an agent is implementing a feature |
| Meal-photo interpretation | Image analysis + nutrition scope not approved | Also a medical/scope concern |
| Wearable integrations | Provider/vendor, consent, and scoring-version review needed | Milestone 6 candidate, not approved |
| Messaging | Delivery/vendor, moderation, retention, and abuse controls needed | No in-app messaging exists |
| Notifications | Consent, preferences, quiet hours, delivery semantics needed | No notifications exist |
| PDF workout import | Parsing/provenance/authorization not designed | Out of scope |
| Direct video upload | Storage, moderation, and safety concerns | Milestone 4 explicitly excludes workout-video uploads |
| Media EXIF stripping / thumbnails | Chose narrower validation (ADR-0014) | Deferred to a later profile-media/hardening phase; not implemented |
| Media malware scanning | Vendor/integration and cost review needed | Not implemented; signature+MIME checks are not a safety guarantee |
| Cloud media provider (S3/R2/Azure) | Only the local provider is implemented (ADR-0013) | Contract reserved; factory rejects unimplemented providers; required before production media |
| Media-consuming features (avatars, exercise media) | Milestone 4 later phases, not approved | Phase 2 built only the provider-independent media foundation |
| Credential verification | Self-entered data is not verified (glossary) | Do not present self-reported data as verified |
| Advanced medical or injury functionality | No diagnosis/clearance; safety not monitored | Hard product boundary |

If you believe an item should move from deferred to planned, open a feature
proposal (issue template) and record the accepted decision in the decision log —
do not begin implementation first.
