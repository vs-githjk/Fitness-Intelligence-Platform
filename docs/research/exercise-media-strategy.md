# Exercise-Media Sourcing Strategy

**Status:** Research / recommendation · **Date:** 2026-08-14 · **Author:** research pass
**Scope:** How Vytal should source exercise imagery and demonstration content legally and sustainably.

## Hard constraints (non-negotiable)

- **No scraping** competitor apps, sites, or media libraries.
- **No ingesting** copyrighted exercise videos/images from YouTube, Instagram, TikTok, etc. without explicit written rights.
- Every asset shipped must have **clear, documented usage rights** for commercial use inside a paid product.

---

## Feasible source options

| # | Option | Licensing posture | Cost/effort | Privacy | Suitability for Vytal |
|---|--------|-------------------|-------------|---------|-----------------------|
| 1 | **Commissioned owned illustrations** (work-for-hire artist/studio) | We own copyright outright via a work-for-hire / full IP-assignment contract. Cleanest rights. | **High** (upfront $; slow) | N/A (owned) | High. Best long-term brand fit; matches Iron Editorial + movement-glyph language. |
| 2 | **Internally produced demos** (film our own / coach-model shoots) | We own it; need signed model/talent releases for anyone on camera. | **Med–High** (studio, talent, editing time) | Model releases required; no third-party data. | High for flagship movements; slow to scale to full catalog. |
| 3 | **Licensed stock / exercise libraries** (WorkoutLabs, MoveKit, ExerciseAnimatic, GymVisual, Shutterstock/Getty) | License, not ownership. Terms vary sharply — see landmines. Some purpose-built for apps (good), generic stock has "primary value" restrictions (bad). | **Low–Med** | Vendor-supplied; no user data. | Med–High. Fastest catalog coverage; watch redistribution/API terms. |
| 4 | **Approved AI-generated artwork** (Adobe Firefly only, see note) | Firefly = IP-indemnified commercial use on paid plans, trained on licensed/PD data. Midjourney/OpenAI grant *use* but **no indemnity** (MJ) and no copyright ownership of AI portions. | **Low** | No user data if prompts are generic. | Med. Viable for *supplemental/atmospheric* art; risky as sole source of instructional accuracy. |
| 5 | **Coach-uploaded private media** (coach films their own cues) | Coach warrants they own/licensed it; Vytal takes a limited license via ToS. Liability shifts to uploader but must be enforced. | **Low** (infra only) | **High-sensitivity** — private per coach/trainee; must stay access-scoped, not global catalog. | High for personalization; must NOT be silently promoted into shared library. |
| 6 | **Structured no-media fallback** (existing movement glyphs + body-region map) | Fully owned, already in repo. Zero third-party risk. | **Low** (built) | N/A (owned) | High as universal baseline; degrades gracefully when no richer media exists. |

---

## Licensing concerns (landmines)

- **Generic stock photo/video "primary value" clause.** Shutterstock/Getty standard & even Enhanced licenses generally forbid uses where the licensed asset *is* the core value being distributed. An exercise **library** where the image is the product can breach this. Enhanced license raises indemnification ($250k on Shutterstock) and removes copy caps but still is not a redistribution/"app catalog" grant — confirm in writing before treating stock photos as the demo catalog. Purpose-built exercise vendors (below) are the safer path.
- **Purpose-built exercise vendors are licenses, not ownership.** WorkoutLabs full library ≈ $1,200/yr or ~$3,500 perpetual; app/API tier ≈ $195 setup + $50/mo. MoveKit sells per-pack **permanent** licenses (packs 104–412 exercises) with commercial use included and "stays yours permanently"; API "coming soon." ExerciseAnimatic ~ $329 bundle, ~$0.14/clip. Read each for **redistribution** limits: you may show assets *in* the app, but you typically cannot let users export/re-license them, and you never own them.
- **AI providers — ownership vs. use vs. indemnity are three different things.**
  - *Adobe Firefly:* only major provider offering **IP indemnification** on paid plans; trained on Adobe Stock/public-domain/licensed content (not scraped). Indemnity is **void** if you break the Gen-AI User Guidelines (no infringing prompts, no imitating trademarked styles/real people). **Preferred AI tool.**
  - *OpenAI (GPT image / DALL·E):* grants you output ownership + commercial use on all plans, but **no indemnification**.
  - *Midjourney:* paid plans grant broad commercial-use license but **no indemnity**, and post-Disney-suit / Thaler v. Perlmutter you **cannot claim copyright** over the AI-generated portions.
  - Across all: purely AI-generated images may not be copyrightable (human-authorship requirement), so competitors could reuse near-identical output — weak moat. Use AI for atmosphere, not as your defensible instructional catalog.
- **Coach-uploaded media.** Require an explicit ToS clause: coach warrants ownership/rights, grants Vytal a limited license, indemnifies Vytal. Keep uploads **access-scoped** (coach + their trainees) and never auto-promote to the shared/global catalog without a rights review.
- **Model releases.** Any internally produced demo featuring a person needs a signed release covering app + marketing use.

---

## Recommended SHORT-TERM approach (0–3 months)

**Glyph-first baseline + one licensed purpose-built library + Firefly for atmosphere.**

1. **Universal baseline = existing owned movement glyphs + body-region map** (Option 6). Zero rights risk, already shipped, guarantees every exercise has *something*.
2. **License one purpose-built exercise library** for demonstration coverage of the common catalog — favor a **permanent per-pack license (e.g., MoveKit)** or WorkoutLabs to avoid recurring lock-in, after a written check that the license permits **display inside a paid app** and does **not** require redistribution rights we won't grant users. Budget: **low–med** ($150–$3,500 one-time depending on breadth).
3. **Adobe Firefly (paid, indemnified) for supplemental/atmospheric art only** (Option 4) — never as the source of anatomical/instructional accuracy. Keep prompt logs; follow Gen-AI guidelines to preserve indemnity.
4. **Stand up coach-uploaded private media** (Option 5) behind the ToS warranty + access-scoping, so coaches can personalize immediately without waiting on catalog work.
5. **Avoid generic Shutterstock/Getty as the catalog** in short term because of the "primary value" clause; only use for marketing-site imagery under an Enhanced license.

## Recommended LONG-TERM approach (6–18 months)

**Migrate to owned, on-brand, commissioned illustration/demo content; treat licensed + AI as bridges.**

1. **Commission owned exercise illustrations** (Option 1) under **work-for-hire / full IP assignment**, styled to Iron Editorial + the movement-glyph language. This becomes the defensible, brand-consistent core catalog we fully own.
2. **Internally produce demo clips** (Option 2) for flagship/high-value movements with proper model releases; owned, differentiated, marketing-reusable.
3. **Phase down licensed third-party libraries** as owned coverage grows (retire recurring fees; keep only where owned production isn't worth it).
4. **Keep glyphs + body-map as the permanent graceful fallback** and keep Firefly for atmosphere only.
5. **Governance:** maintain a per-asset rights register (source, license type, term, indemnity, redistribution scope) so every shipped image is auditable.

---

## Sources (accessed 2026-08-14)

- WorkoutLabs — Exercise & Yoga Illustration Licensing: https://workoutlabs.com/exercise-illustrations-licensing/
- MoveKit — Pricing / library & licensing: https://movekit.com/pricing · https://movekit.com/blog/best-exercise-animation-libraries-2026
- ExerciseAnimatic — Commercial license: https://www.exerciseanimatic.com/license
- Adobe Firefly — commercially safe AI / IP approach: https://business.adobe.com/products/firefly-business/firefly-ai-approach.html
- Adobe Firefly indemnification (Computerworld): https://www.computerworld.com/article/1628682/adobe-offers-copyright-indemnification-for-firefly-ai-based-image-app-users.html
- AI output ownership comparison (ChatGPT/Claude/Midjourney/Gemini): https://www.terms.law/2025/04/09/navigating-ai-platform-policies-who-owns-ai-generated-content/
- Midjourney commercial-use 2026 guide (Disney suit / Thaler cert denial): https://terms.law/2026/01/15/midjourney-commercial-use-rights-complete-2026-guide/
- Shutterstock vs Getty licensing & pricing 2026: https://photutorial.com/shutterstock-vs-getty-images/ · https://www.stockphotosecrets.com/buyers-guide/shutterstock-pricing.html
