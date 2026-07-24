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
| Nutrition media | Milestone 5, not approved | Avatars (ADR-0017) and exercise media (ADR-0018) are the media-consuming features so far |
| Video streaming / transcoding / thumbnails | Exercise video is stored and delivered as-is (ADR-0018) | No HLS/DASH, no re-encode, no generated poster/thumbnail |
| External / YouTube exercise embedding | No external media hosts (ADR-0018) | The legacy `image_url`/`thumbnail_url` fields remain but are superseded by uploads |
| Trainee-facing exercise media in the workout runner | Needs runner UX + a trainee-scoped delivery authorization walk (ADR-0018) | Exercise media is coach-scoped this phase |
| Credential verification | Self-entered data is not verified (glossary) | Certifications are plain text; do not present self-reported data as verified |
| Public profiles / profile search / discovery / sharing | No public surface or social graph approved (ADR-0017) | Profiles are visible only to self and an active coach/trainee relationship |
| Profile document uploads / license validation | Verification and document handling not designed (ADR-0017) | Certifications remain plain text only |
| Avatar cropping / rotation / filters / thumbnails | Chose the minimal reuse of media validation (ADR-0017) | Client preview only; server stores the uploaded image as-is |
| Advanced medical or injury functionality | No diagnosis/clearance; safety not monitored | Hard product boundary |
| Coach-to-coach library sharing / marketplace | Out of scope for the curated starter library (ADR-0016) | The starter library is one-way clone-to-edit, not sharing |
| Ratings / reviews / likes / comments on programs | Social features not approved | No community layer on starter or coach content |
| Starter-library synchronization engine | Clones are independent snapshots (ADR-0016) | Updating starter content never alters existing coach copies |
| AI-generated or personalized programs | Requires an approved AI decision + review | Starter content is curated and static, never generated or personalized |

If you believe an item should move from deferred to planned, open a feature
proposal (issue template) and record the accepted decision in the decision log —
do not begin implementation first.
