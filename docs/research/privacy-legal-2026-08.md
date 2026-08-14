# Vytal — US Privacy & Legal Obligations Research (August 2026)

**Purpose:** Map the CURRENT US privacy/legal landscape for Vytal, a NON-MEDICAL health/fitness-adjacent
SaaS where coaches program training for trainees. This is engineering/product research to let Vytal
describe **only obligations it actually meets**. It is **not legal advice** and does **not** establish
compliance. Every "external launch gate" below requires actual counsel and/or founder corporate input.

**Vytal data inventory (as scoped):** accounts, coach/trainee profiles, fitness assessments & baseline
inputs, readiness check-ins, workout history & performance, safety reports, media uploads, invitations,
audit/security logs. Explicitly non-medical (no diagnosis, no treatment).

**Research date / access date for all sources below:** 2026-08-14.

---

## 1. HIPAA — Does it apply to Vytal? (Almost certainly NOT — verify with counsel)

HIPAA obligations attach only to **covered entities** (health plans, health care clearinghouses, and
health care providers that transmit health information electronically in connection with a HIPAA standard
transaction) and their **business associates**. A direct-to-consumer fitness coaching platform that is
not acting on behalf of a covered entity is generally outside HIPAA.

- Source (HHS, Covered Entities & Business Associates):
  https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html — accessed 2026-08-14.

**Vytal analysis:** Vytal is not a health plan, clearinghouse, or provider running HIPAA transactions, and
coaches are fitness professionals, not covered providers. Vytal therefore is very likely **NOT** subject
to HIPAA. **Caveat (counsel to confirm):** if Vytal ever contracts to provide services *on behalf of* a
covered entity (e.g., a clinic, PT practice, or health plan pushes patients through Vytal), it could become
a **business associate** and trigger HIPAA + a Business Associate Agreement. **Do NOT market Vytal as
"HIPAA compliant."** Being non-HIPAA does not mean unregulated — the FTC and state laws below fill the gap.

---

## 2. FTC Health Breach Notification Rule (HBNR) — the primary federal hook

The HBNR (16 CFR Part 318) applies to **non-HIPAA** vendors of personal health records (PHRs), PHR-related
entities, and their service providers. The 2024 amendments (effective **July 29, 2024**) explicitly modernized
it to cover **health apps and similar technologies**.

- Final rule / FTC announcement:
  https://www.ftc.gov/news-events/news/press-releases/2024/04/ftc-finalizes-changes-health-breach-notification-rule — accessed 2026-08-14.
- Rule landing page: https://www.ftc.gov/legal-library/browse/rules/health-breach-notification-rule — accessed 2026-08-14.
- Compliance guidance: https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0 — accessed 2026-08-14.

**Coverage trigger — the "multiple sources" test (critical for Vytal):** A "personal health record" is an
electronic record of identifiable health information that **"has the technical capacity to draw information
from multiple sources"** and is managed/controlled by or for the individual. FTC guidance is explicit that
an app is covered if it has the technical capacity to draw health info through an **API** (e.g., syncing with
a fitness tracker or another app) in addition to user-entered data.

**Vytal analysis:**
- **Today (manual-entry only, no wearable/third-party sync):** Vytal collects health-ish data from a single
  source (the user). A single-source app arguably does **not** meet the "multiple sources" PHR definition, so
  HBNR may not yet be triggered — **but this is a fact-specific legal call for counsel**, not a self-certification.
- **The moment M6 Wearables ships** (Apple Health / Google Fit / device APIs), Vytal gains "technical capacity to
  draw from multiple sources" and is **very likely a HBNR-covered vendor of PHRs.** Treat HBNR readiness as a
  **hard gate for the wearables milestone.**

**What HBNR requires on a breach** (once covered): notify affected individuals **without unreasonable delay,
no later than 60 calendar days** after discovery; notify the **FTC** (at the same time as individuals if the
breach affects **500+** individuals); and provide **media** notice for breaches affecting 500+ residents of a
state/jurisdiction. "Breach" includes unauthorized disclosures, not just security intrusions. Notices must
include expanded content (what happened, data involved, contact info, mitigation steps).

---

## 3. State consumer-health-data (CHD) laws — the sharpest edge for a fitness app

These are **standalone health-data laws separate from the comprehensive privacy laws** in §4. They are broad,
consent-first, and (WA) carry a **private right of action**.

### 3a. Washington My Health My Data Act (MHMDA) — RCW 19.373 — HIGHEST RISK
- Statute: https://app.leg.wa.gov/RCW/default.aspx?cite=19.373&full=true — accessed 2026-08-14.
- WA AG hub: https://www.atg.wa.gov/protecting-washingtonians-personal-health-data-and-privacy — accessed 2026-08-14.

"Consumer health data" = information linked/linkable to a consumer that identifies past/present/future
**physical or mental health status**, and the enumerated list expressly includes **"bodily functions, vital
signs, symptoms, or measurements,"** biometric data, precise location tied to health services, and **data
derived or extrapolated** from non-health data. **Fitness assessments, readiness check-ins, body measurements,
and workout-performance metrics plausibly fall within "bodily functions / measurements" and derived-data** —
so Vytal should assume MHMDA **can apply** to its Washington users.

Key MHMDA obligations:
- **Separate, distinct "Consumer Health Data Privacy Policy"** linked prominently on the homepage; it may
  contain **only** MHMDA-required content and must **not** be merged into the general privacy policy.
- **Consent before collection/sharing**; **valid, separate authorization before any sale**; right to **withdraw** consent.
- Consumer rights to **access**, **delete**, and **confirm whether data was shared/sold**, honored **within 45 days**.
- **Data minimization / access restriction** (limit internal + processor access to what's necessary).
- **Enforcement:** violations are per se Washington Consumer Protection Act violations — enforceable by the AG
  **and via a PRIVATE RIGHT OF ACTION** (litigation exposure; this is what makes MHMDA the top compliance risk).

### 3b. Nevada SB 370 (NRS 603A consumer health data) — effective March 31, 2024
- Overview via WA/CT/NV summaries; confirm text with counsel. Requires **prior affirmative consent** to collect/
  share/sell CHD; **no private right of action** (AG-only; deceptive-trade-practice, civil penalties up to
  ~$5,000/violation); bans geofencing near health facilities. Applies to NV consumers' health data.

### 3c. Connecticut CHD amendments (SB 3) — operative July 1, 2023
- Adds consumer-health-data consent + geofencing rules on top of the Connecticut Data Privacy Act; **AG-only** enforcement.

### 3d. 2025–2026 developments (landscape is shifting — re-check before launch)
- **No new comprehensive state privacy law was enacted in 2025** (first gap in ~5 years).
- **New York** Health Information Privacy Act (S.929) was **VETOED Dec 19, 2025**; bills are being re-introduced in
  2026 — watch NY.
- Federal **Health Information Privacy Reform Act (S.3097)**, introduced Nov 4, 2025, would extend baselines to
  wearables/health apps — **not law**, monitor only.
- Sources: https://www.healthlawadvisor.com/nevada-joins-washington-and-connecticut-to-protect-consumer-health-data-privacy
  and https://www.multistate.us/insider/2026/2/4/all-of-the-comprehensive-privacy-laws-that-take-effect-in-2026 — accessed 2026-08-14
  (secondary/tracking sources; verify against statute text before relying).

---

## 4. Comprehensive state privacy laws (CCPA/CPRA + ~19 others)

### California CCPA/CPRA — the baseline to design to
- CA AG: https://oag.ca.gov/privacy/ccpa — accessed 2026-08-14.
- CPPA (agency) + 2026 updates: https://cppa.ca.gov/regulations/ and
  https://cppa.ca.gov/pdf/things_to_know_before_2026_updates.pdf — accessed 2026-08-14.

Consumer rights: **know/access, delete, correct, opt-out of sale/sharing** (incl. cross-context behavioral
advertising), and **limit use of Sensitive Personal Information (SPI)**. **Health data is SPI**, triggering the
"Limit the Use of My Sensitive Personal Information" control and heightened handling. New CPPA regulations
(cybersecurity audits, risk assessments, automated-decisionmaking) took effect **Jan 1, 2026** — relevant if
Vytal adds AI-driven decisions (M8 AI Coach). Applies only if Vytal meets CCPA business thresholds (revenue/
volume), **which most early-stage startups do not yet meet — counsel to confirm applicability.**

### The other ~19 comprehensive laws (VA-model family)
Colorado, Connecticut, Virginia, Utah, Oregon, Texas, Montana, Delaware, Iowa, Nebraska, New Hampshire,
New Jersey, Minnesota, Maryland, Tennessee, Indiana, Kentucky, Rhode Island, plus CA. Most treat health data
as **sensitive** (opt-in consent or sale restrictions). "Broad" states (CA, CO, CT, DE, MD, NH, NJ, OR, RI, UT)
define health data widely enough to plausibly cover **fitness metrics**; "narrow" states tie it to formal
diagnoses. **Design to the strictest (CA + broad states + MHMDA) and you cover the field.**

---

## 5. Breach notification (general state laws)

Independent of HBNR, **all 50 states + DC** have data-breach notification statutes covering personal information
(name + SSN, financial acct, and in many states **health/medical info** and account credentials). Requirements:
notify affected residents (and often the state AG) without unreasonable delay; some states impose fixed deadlines
(e.g., 30–45 days) and consumer-reporting-agency notice above thresholds. WA AG breach page:
https://www.atg.wa.gov/washington-s-data-breach-notification-laws — accessed 2026-08-14.
**Vytal needs a written incident-response + breach-notification runbook** that satisfies HBNR **and** the
strictest applicable state deadlines. (Exact per-state matrix = counsel task.)

---

## 6. Minors' data — COPPA + state minor rules

- FTC COPPA amendments finalized **April 22, 2025**: expanded "personal information" to include **biometric and
  government identifiers**, requires **separate verifiable parental consent** for third-party disclosure/targeted
  ads, and bars retaining kids' data longer than necessary.
  https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data — accessed 2026-08-14.
- **Vytal analysis:** COPPA applies to under-13 users. Simplest launch posture is a **hard 13+ (or 16+/18+)
  minimum age with attestation at signup** so Vytal is not "directed to children" and does not knowingly collect
  under-13 data. Note: trainees could be minors coached by an adult — if Vytal ever intends to serve under-18
  athletes, that requires a dedicated parental-consent design + counsel review (state minor-privacy laws, e.g.
  CA and others, add teen protections above COPPA).

---

## 7. Cookies / tracking / analytics

- If Vytal uses third-party analytics, ad pixels, or session-replay: several states require **opt-out of
  sale/sharing** and honoring **Global Privacy Control (GPC)** signals; MHMDA/NV/CT may treat sharing of health-
  adjacent data via trackers as regulated **collection/sharing requiring consent**. The FTC has brought
  enforcement actions against health apps for disclosing health data to ad platforms via pixels.
- **Safest launch posture:** first-party analytics only, **no third-party ad/marketing pixels on any screen that
  touches health/fitness data**, and a cookie/tracking disclosure in the privacy policy. If any third-party
  tracker is added later, it becomes a consent/GPC engineering task.

---

## 8. Data subject rights (access / deletion / correction) — build the mechanism

Across HBNR-adjacent expectations, MHMDA, CCPA, and the VA-family laws, Vytal should implement a **verified
data-rights request flow**: access/export, deletion, correction, and (for CHD/SPI) withdraw-consent / limit-use,
honored within the **shortest applicable deadline (treat 45 days as the ceiling; MHMDA = 45)**, free of charge
(up to twice/year), with identity verification and an audit trail. Vytal's existing audit/security logs support
the recordkeeping side of this.

---

## 9. Coach ↔ trainee data-sharing model — Vytal-specific design notes

This is the highest-nuance area and needs explicit product + legal treatment:
- The coach sees the trainee's health-adjacent data (assessments, readiness, workout history, safety reports).
  Under MHMDA/CHD laws, moving CHD from trainee to coach is **"sharing/collection"** that should rest on the
  **trainee's informed consent**, surfaced at invitation/onboarding.
- The **invitation flow** is the natural consent capture point: the trainee should affirmatively agree to share
  their training data with their specific coach, with clear scope and a way to **revoke** (which must actually
  cut coach access — ties to the access-restriction/minimization duty).
- Coaches are **processors/independent recipients**, not the platform; document the relationship and restrict
  coach access to trainees who consented to them (Vytal's existing per-coach scoping supports this).
- Safety reports and media uploads about a trainee are sensitive; deletion/retention rules must cover them.

---

## Vytal-specific obligations checklist (what to actually build/publish for a US soft-launch)

- [ ] **Public privacy policy** describing exactly what Vytal collects, why, retention, and third parties (only
      what truly exists — no aspirational claims).
- [ ] **Do NOT claim "HIPAA compliant."** State plainly that Vytal is a non-medical fitness product.
- [ ] **Standalone MHMDA "Consumer Health Data Privacy Policy"** (separate homepage link, MHMDA-only content) —
      required the moment Vytal has Washington users; safest to publish at launch.
- [ ] **Consent capture at trainee onboarding/invitation** for collecting and sharing health-adjacent data with
      the coach; store consent + timestamp; provide **withdraw consent** that revokes coach access.
- [ ] **No sale of data**, and **no third-party ad/marketing pixels** on health-data screens; honor **GPC** if any
      opt-out-eligible sharing exists.
- [ ] **Data-rights request flow**: access/export, delete, correct, withdraw-consent — verified, free, ≤45 days.
- [ ] **Age gate** (13+ minimum, attested) so Vytal is not COPPA-"directed to children"; block under-13 signups.
- [ ] **Written incident-response + breach-notification runbook** meeting HBNR (60-day / FTC / media) and strictest
      state deadlines; wire it to Vytal's audit/security logs.
- [ ] **Data-minimization / access-restriction** enforced in code (coach access limited to consented trainees;
      internal access on need-to-know).
- [ ] **HBNR readiness treated as a hard gate BEFORE M6 Wearables** ships (multi-source sync = likely HBNR-covered PHR).
- [ ] **Retention & deletion policy** covering profiles, assessments, readiness, workout history, safety reports,
      and media uploads.

---

## EXTERNAL LAUNCH GATES (blockers requiring counsel or founder/corporate input — Vytal cannot self-answer these)

1. **[COUNSEL] Statutory applicability determinations** — Is Vytal a HBNR "vendor of PHR" today (single-source
   question)? Which state CHD laws (WA/NV/CT) and comprehensive laws attach given Vytal's user footprint and
   revenue/volume thresholds? Only counsel can render these.
2. **[COUNSEL] MHMDA private-right-of-action exposure** — draft the compliant standalone CHD policy + consent
   architecture; this is the top litigation risk and must be lawyer-reviewed before WA launch.
3. **[FOUNDER/CORPORATE] Legal entity name, jurisdiction of formation, registered contact address** — required to
   name the data controller in every policy. **Not yet known — must NOT be invented.**
4. **[FOUNDER] Physical/business address + privacy contact email/DPO** — required in privacy policy and breach notices.
5. **[FOUNDER] Product decision on minors** — will Vytal ever serve under-18 trainees? If yes → COPPA/parental-
   consent design + counsel review; if no → confirm 13+/18+ age gate policy.
6. **[COUNSEL] Sub-processor / vendor list + DPAs** — hosting (Render/Vercel per repo), storage, email/invitations,
   analytics; each needs a data-processing agreement and disclosure.
7. **[COUNSEL] Breach-notification per-state deadline matrix** and template notices.
8. **[COUNSEL] Business-Associate risk check** — confirm no current or planned arrangement makes Vytal a HIPAA
   business associate (e.g., partnerships with clinics/PTs/health plans).
9. **[COUNSEL, pre-M8] Automated-decisionmaking / AI review** — CPPA ADMT rules (eff. Jan 1, 2026) and risk-
   assessment duties apply if the AI Coach makes or informs significant decisions.
10. **[MONITOR] Legislative watch** — NY health-data bill (re-introduced 2026), federal S.3097, and any new state
    CHD laws; re-run this research before each major release.

---

### Sources (all accessed 2026-08-14)
- HHS HIPAA covered entities: https://www.hhs.gov/hipaa/for-professionals/covered-entities/index.html
- FTC HBNR final rule: https://www.ftc.gov/news-events/news/press-releases/2024/04/ftc-finalizes-changes-health-breach-notification-rule
- FTC HBNR rule page: https://www.ftc.gov/legal-library/browse/rules/health-breach-notification-rule
- FTC HBNR compliance guide: https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0
- WA MHMDA statute (RCW 19.373): https://app.leg.wa.gov/RCW/default.aspx?cite=19.373&full=true
- WA AG health-data hub: https://www.atg.wa.gov/protecting-washingtonians-personal-health-data-and-privacy
- WA AG breach law: https://www.atg.wa.gov/washington-s-data-breach-notification-laws
- CA AG CCPA: https://oag.ca.gov/privacy/ccpa
- CPPA regulations + 2026 updates: https://cppa.ca.gov/regulations/ ; https://cppa.ca.gov/pdf/things_to_know_before_2026_updates.pdf
- FTC COPPA 2025 amendments: https://www.ftc.gov/news-events/news/press-releases/2025/01/ftc-finalizes-changes-childrens-privacy-rule-limiting-companies-ability-monetize-kids-data
- MultiState 2026 privacy-law tracker (secondary): https://www.multistate.us/insider/2026/2/4/all-of-the-comprehensive-privacy-laws-that-take-effect-in-2026
- Epstein Becker CHD-law summary (secondary): https://www.healthlawadvisor.com/nevada-joins-washington-and-connecticut-to-protect-consumer-health-data-privacy
