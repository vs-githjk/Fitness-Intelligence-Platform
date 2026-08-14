# Vytal legal documents — DRAFTS

These are **product-accurate first drafts** written from Vytal's actual data flows and
implemented behavior (see [[privacy-legal-2026-08]] research). They describe **only what the
product actually does** and make **no compliance claims** that are not backed by an
implemented, verifiable control.

> **LEGAL COUNSEL REVIEW REQUIRED BEFORE BROAD COMMERCIAL LAUNCH.**
> These drafts are engineering/product work product, not legal advice. A qualified attorney
> must review them before Vytal is offered publicly for commercial use.

## Distinction the drafts preserve

- **Technically production-ready** — the application can run in a true production environment
  with hardened configuration. This is an engineering state.
- **Legally cleared for broad public commercial launch** — requires the counsel review and the
  founder/corporate inputs flagged below. This is a separate gate.

The staging → production transition is **not** blocked on the second gate; a closed production
soft-launch can proceed once the first gate and the founder inputs are met.

## External inputs the drafts must NOT invent (fill before publishing)

| Placeholder | Who provides | Notes |
|---|---|---|
| `[LEGAL_ENTITY]` | Founder | Registered company name |
| `[JURISDICTION]` | Founder + counsel | Governing law / venue |
| `[CONTACT_ADDRESS]` | Founder | Physical/mailing address for legal + privacy contact |
| `[PRIVACY_EMAIL]` / `[SECURITY_EMAIL]` / `[SUPPORT_EMAIL]` | Founder | Working inboxes |
| `[EFFECTIVE_DATE]` | Founder/counsel | Publication date |
| Canonical domain | Founder / DNS | Do not invent a `joinvytal` TLD |

## Documents

- [privacy-policy.md](privacy-policy.md)
- [consumer-health-data.md](consumer-health-data.md) — Washington MHMDA-style notice (top risk; counsel to confirm applicability)
- [terms-of-service.md](terms-of-service.md)
- [health-fitness-disclaimer.md](health-fitness-disclaimer.md)
- [security.md](security.md) — public Trust/Security page content (only verified controls)

## Counsel checklist (from the research)

- [ ] Confirm HIPAA does **not** apply (Vytal is not a covered entity/business associate).
- [ ] Confirm Washington My Health My Data Act applicability + the private-right-of-action posture.
- [ ] Per-state consumer-health-data + general privacy applicability matrix.
- [ ] FTC Health Breach Notification Rule readiness (becomes a hard gate before Wearables/M6 multi-source sync).
- [ ] Sub-processor DPAs (hosting/database/media providers).
- [ ] Decision on ever serving under-18 trainees (COPPA); today a 13+ age gate is assumed.
