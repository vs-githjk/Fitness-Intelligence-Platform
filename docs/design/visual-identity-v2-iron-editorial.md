# Vytal Visual Identity v2 — Iron Editorial — Implementation Authority

> **Status:** CANONICAL · FROZEN (founder/product sign-off 2026-08-12).
> **Role:** the single design authority Experience Cycle 2 implements from.
> **Baseline:** application v0.5.0, Experience Cycle 1 closed and released to staging.
> **This is a design/governance authority, not an engineering design.** It defines
> the approved visual/product direction and its change control. It intentionally
> specifies **no** backend architecture; per-phase engineering designs (routes,
> schemas, component APIs) are produced during Cycle 2 and reviewed against this
> document.

## Authority and supersession

- This document **supersedes the earlier Iron Editorial visual exploration and
  convergence artifacts as design authority.** Those artifacts are historical
  context; where they differ from this document, this document is correct.
- It does **not** override the frozen per-screen, domain, scoring, or security
  authorities. Those remain binding exactly where this document says they remain
  binding, in particular:
  - [design/trainee-today.md](trainee-today.md) — Today content, hierarchy, and
    acceptance criteria (this document amends only Today's *visual presentation*, §14).
  - [decisions/README.md](../decisions/README.md) — ADR-0019 rest-day integrity
    remains binding; ADR-0019's *theming* decision (route-scoped dark, no in-app
    switch) is superseded in part by this freeze for the Cycle-2 destination (§8, §34).
  - [product-principles.md](../product-principles.md) — experience and boundary
    principles, the score/determinism laws, and all authorization/security boundaries.
  - [design-system.md](../design-system.md) — the **as-built v1** design system;
    accurate for v0.5.0 surfaces and superseded surface-by-surface as Cycle 2 migrates
    each screen. Do not read it as the forward direction.
- **Change control:** anything tagged `[FROZEN]` or `[LAW]` changes only by explicit
  founder/product decision, recorded in §36. Engineering may not promote or demote a
  statement's status on its own.

## How to read this document — status vocabulary

Every normative statement carries one status.

| Tag | Meaning | Who can change it |
| --- | --- | --- |
| `[FROZEN]` | Fixed product/visual decision. Implement as written; do not reinterpret. | Founder/product only. |
| `[FLEX]` | Implementation flexibility. The intent is fixed; the mechanism, exact values within stated bounds, or sequencing detail is engineering's call. | Engineering, within the stated intent. |
| `[FUTURE]` | Approved direction, not yet built and not in Cycle-2 scope unless listed in §32. | Enters scope via a future cycle plan. |
| `[DECISION]` | Requires an explicit future product decision before anyone acts on it. | Founder/product. Do not build speculatively. |

Blocks marked `[LAW]` are permanent product laws — stronger than frozen: they bind
every future cycle, not just this identity.

## Final clarifications applied at freeze (founder review)

Four clarifications were applied to the approved artifact at sign-off. They do **not**
reopen Iron Editorial; they resolve scope ambiguities and one factual correction. They
are encoded in the relevant sections and summarized here:

- **A — "Training should be seen" scope.** The law applies to core training/coaching
  surfaces. Utility/account surfaces (Settings, security, profile editing,
  privacy/preferences, admin utilities) express the identity through shell, type,
  color, spacing, and composition, and are **not required** to contain a training
  visualization. Premium Simplicity wins over forced decoration. (Encoded in §4.1, §21.)
- **B — C2.0 theme-preference boundary.** C2.0 prepares the theme-preference model and
  persistence and resolves Light/Dark/System semantics, **without** exposing a
  partially-functional user-facing theme that creates mixed-shell behavior; the
  user-facing control + app-wide shell migration land together in C2.1. **Reality
  correction:** durable per-user theme persistence already exists in the backend — a
  persisted `UserPreferences.theme` column (Alembic head 0017, ADR-0012) with
  `GET`/`PUT /preferences` — so **no new backend/schema/migration is required** for
  persistence; C2.0's work is frontend wiring + semantics. (Encoded in §8, §29, §32.)
- **C — Coach serif monogram exception.** The voice serif is reserved for genuine
  coach-authored prose. The designed coach **monogram** is the sole non-prose
  exception, functioning as an identity mark, never as manufactured coach speech. No
  other system-generated prose may use Coach Voice typography to imply human
  authorship. (Encoded in §10, §13.)
- **D — Iron Line commission does not block C2.0/C2.1.** The commissioned set is the
  desired final art system and runs as a parallel non-engineering track. C2.0 does not
  depend on it; C2.1 may use approved interim **data-true** typographic/diagrammatic
  variants. Generic fitness placeholders, stock clip-art, and fabricated decorative
  glyphs are **not** acceptable interim replacements. (Encoded in §11, §32.)

---

## Contents

1. Purpose & authority
2. North star
3. Immutable product principles
4. New visual/product laws
5. Registers: Calm / Live / Human
6. Information architecture
7. Trainee shell
8. Themes
9. Color tokens & semantic contract
10. Typography roles
11. Iron Line illustration system
12. Media system
13. Coach presence
14. Today
15. Workout Execution
16. Program
17. Check-in
18. Progress
19. Exercise Reference
20. Body-map mapping policy
21. Login / front door
22. Mobile behavior
23. Desktop behavior
24. Accessibility
25. Motion
26. Truthfulness & deterministic presentation
27. Copy & provenance language
28. No-media behavior
29. Currently-possible capability map
30. Approved enabling capability: trainee exercise/media read access
31. Known risks & debt
32. Experience Cycle 2 implementation order
33. PX acceptance criteria
34. Migration from v0.5.0 surfaces
35. Explicit anti-goals
36. Decision log / freeze summary

---

## 1. Purpose & authority

This document consolidates the approved Iron Editorial work — the Visual Identity
Exploration, the Iron Editorial Visual Convergence, and the founder/product sign-off of
2026-08-12 — into one implementation authority.

- **This document wins conflicts** with the exploration/convergence artifacts.
- **It does not replace the frozen per-screen content specs.** `design/trainee-today.md`
  remains the authority on Today's content and hierarchy; §14 amends only visual
  presentation. ADR-0019 rest-day integrity remains binding.
- **It is a design authority, not an engineering design.** Backend routes, schemas, and
  component APIs are per-phase Cycle-2 engineering work, reviewed against this document.
- **Change control** per the table above; the log is §36.

## 2. North star — `[FROZEN]`

**Vytal should feel like premium strength-training software with serious
intelligence and a real coach behind it.**

Athletic energy originates in training, but its visual identity should permeate the
product. **Training should be seen, not merely described.**

The mechanism that keeps this honest: the athleticism comes from *rendering the training
data the product already owns* — movement, muscle, load, structure — inside an editorial
frame. Typography carries authority; the training data carries the athleticism. It is
never imported as decoration.

## 3. Immutable product principles — `[LAW]`

Unchanged by this identity; every Iron Editorial surface must still satisfy all of them.
Authority: [product-principles.md](../product-principles.md).

1. **Guidance over Metrics** — lead with what to do, never a wall of numbers.
2. **One Dominant Answer** — one question per screen.
3. **Coach First** — the human coach is the authority; the product amplifies, never
   replaces or impersonates them.
4. **Calm Intelligence** — no alarm walls; severity is metadata, not layout.
5. **Premium Simplicity** — restraint, hierarchy, finish over feature density.
6. **Determinism** — every score/verdict/interpretation traces to a documented rule; no
   inference, no invention; missing data stays missing (never zero, never guessed).
7. **Non-medical** — no diagnosis, no health claims, no anatomical/medical inference
   beyond what source data states.
8. **No fake coach / no AI voice** — coach-attributed words are the coach's verbatim
   words; the product never manufactures a human voice.

## 4. New visual/product laws — `[LAW]`

Added by this freeze; these bind every future screen and cycle.

1. **Training should be seen, not merely described.** Every major training/coaching
   surface carries at least one data-true training visual — movement glyph, week arc,
   load ghost, muscle region, or bar path (§11). **Scope (clarification A):**
   utility/account surfaces (Settings, security/password controls, profile editing,
   privacy/preferences, administrative utilities) may express Iron Editorial through
   shell, typography, color, spacing, and composition **without** being required to
   contain a training visualization. Traceability still applies to any athletic visual
   that *does* appear; Premium Simplicity wins over forced decoration.
2. **Traceability.** If a visual encodes training information, it must be traceable to a
   real field or documented rule. An athletic visual that cannot be traced to a real
   product/training fact is decoration and requires separate justification before
   shipping.
3. **Vocabulary separation.** Implementation vocabulary belongs in provenance. User
   intent belongs in product copy (§27).
4. **Authorship honesty.** Never make the coach appear to have authored an intent the
   underlying data does not prove (§16 is the primary application).
5. **No-media completeness.** "No media" is a first-class designed state, never missing
   chrome. Every composition works with zero photography and zero portraits (§28).

## 5. Register system: Calm / Live / Human — `[FROZEN]`

One product identity that changes emotional temperature by register. **Every future
screen specification must declare its register (or deliberate combination) before
anything else.**

| Register | Mode | Owns | Character |
| --- | --- | --- | --- |
| CALM | Deciding | Today · check-in · errors · recovery/reduce states · explanatory decision surfaces | Display verdicts, generous space, atmosphere whisper, indigo interactions. Ember only as identity punctuation. Cools further on recovery days. |
| LIVE | Training | Workout Execution · logging · rest timers · next-up training interaction | Instrument grammar: engineered numerals, large thumb targets, ember training actions, earned motion (§25). |
| HUMAN | The coach | Coach attribution · notes · commentary · bylines | Serif voice, byline/monogram system. Appears *inside* both other registers; the serif belongs to the coach alone. |

## 6. Information architecture — `[FROZEN]`

Top-level trainee navigation becomes four destinations. This is an IA consolidation,
**not feature deletion** — no currently reachable functionality is silently removed.

| Tab | Conceptual ownership |
| --- | --- |
| TODAY | Morning Brief · daily guidance · check-in entry / the daily decision loop |
| TRAIN | Current program · workouts · workout execution · exercise reference |
| PROGRESS | Training/fitness progress · recorded bests · trends and history |
| YOU | Baseline / assessment · profile · settings and preferences |

- `[FROZEN]` Mobile keeps exactly these four stable top-level destinations. The current
  7-item trainee nav (Today, Progress, Workouts, Program, Assessment, Profile, Settings —
  wrapping into two rows on mobile) is retired.
- `[FLEX]` Desktop may expose secondary navigation within these destinations (e.g. a
  TRAIN sub-nav for Program / Workouts / Reference). Internal routes may remain where
  useful — this governs the user-facing IA, not the router table.
- `[FLEX]` Where each existing screen lands within a tab (e.g. check-in as an overlay
  from TODAY or a route under it) is engineering's call, provided each item in the
  ownership table stays reachable within its tab in ≤ 2 taps.
- `[FROZEN]` Acceptance requirement carried into C2.1 (§33): a findability check with the
  real testing user, because Workouts / Assessment / Settings relocate.
- `[FLEX]` Coach-side IA is unchanged this freeze; coach navigation is restyled
  (tokens/type/theme), not restructured, in Cycle 2.

## 7. Trainee shell — `[FROZEN]`

- Dark-first (§8), ink ground, editorial masthead grammar, four-tab navigation (§6).
- **Mobile:** single-row bottom tab bar, four destinations, active tab marked with the
  ember tick (the one persistent ember element in Calm register). Safe-area aware. The
  single-row bar retires the Cycle-1 two-row-nav clearance debt.
- **Desktop:** persistent sidebar carrying the four destinations plus secondary items
  per §6; content column keeps an editorial measure (§23).
- **Readiness atmosphere** remains the shell's whisper layer: the established band tint
  (gold/blue/amber/violet) at whisper opacity, never a component color. Cycle-1
  calibration (≈0.09 light / 0.14 dark, edge variants) carries forward as the starting
  point; `[FLEX]` exact alpha may be re-tuned for the dark shell within "whisper, never
  surface."
- **Environment indicators** (staging micro-bar, demo tag) persist as quiet mono-face
  metadata, never banners.
- `[FLEX]` Component mechanics (composition with the existing `AppShell`, token namespace
  strategy) are engineering's call — see §34.

## 8. Themes — `[FROZEN]`

| Rule | Decision |
| --- | --- |
| Trainee default | Dark. |
| Coach default | Light. |
| User preference | Light / Dark / System. Explicit preference always wins over role default and OS. |
| Persistence | Preference is remembered per user via the **existing** `UserPreferences.theme` column and `GET`/`PUT /preferences` (see §29 — no new backend required). |
| Light theme character | The "print edition": warm paper/bone ground, true ink, same editorial hierarchy, same training visual language, same glyphs. **Not an inverted dark theme.** |
| Architecture destination | App-wide theming. **Do not retain the current light-chrome/dark-content seam** (route-scoped dark on Today) as the destination architecture — it was a Cycle-1 transitional state (§34). |
| Gym Mode | Execution's dark-first treatment is a **respectful default, not a forced override**. Explicit Light is respected everywhere, including execution. Theme/Gym-Mode behavior is clearly labeled; the choice is remembered (§15). |

**Sequencing (clarification B):**

- **C2.0** — prepare/resolve the theme-preference model and Light/Dark/System semantics
  and wire persistence to the existing endpoint. **Do not** expose a partially-functional
  user-facing theme that creates mixed-shell behavior.
- **C2.1** — expose/activate the user-facing Light / Dark / System control **together
  with** app-wide shell/chrome migration; eliminate the route-scoped Today seam.

`[FLEX]` Whether Gym Mode is "execution follows the app theme" or a distinct labeled
execution preference is an implementation decision — the frozen constraints are:
dark by default, explicit light wins, labeled, remembered, never trapping the user.

## 9. Color tokens & semantic contract — `[FROZEN]`

**Ground system** (dark reference / light "paper"):

| Token | Value | Role |
| --- | --- | --- |
| ink-0 | `#0B0C0F` | page (dark) |
| ink-1 | `#14161B` | surface (dark) |
| ink-2 | `#1C1F26` | inset (dark) |
| bone | `#ECEAE2` | text on ink |
| bone-2 | `#A9A8A0` | muted on ink |
| paper | `#F5F2EB` | page (light) |

**Semantic accents:**

| Token | Value | Means | Never means |
| --- | --- | --- | --- |
| EMBER | `#FF5A28` dark · `#E8430F` light | Training interaction and identity only — Start, log-set, live progress, next-up, program covers, best endpoints, active-tab tick. | Body risk · health/body-score state · warning · error. |
| INDIGO | `#8B87F0` dark · `#4A44C9` light | General interaction: links, focus, non-training actions. Continuity with every unmigrated screen. | Training identity. |
| GOLD | `#D9A84E` (dark ref) | Caution (incl. deload labeling, difficulty accents). | Error, training action. |
| ROSE | `#E07B72` (dark ref) | Error. Deliberately muted, kept legibly distinct from ember. | Body-score banding (body data is never red). |
| SUCCESS | `#57B98E` (dark ref) | Completion/confirmation. Semantically separate. | — |
| ATMOSPHERE | band gold/blue/amber/violet | Readiness whisper layer (Cycle-1 role, unchanged). | Component/surface color. |

`[FLEX]` Light-context values for gold/rose/success and the full derived ramp (hovers,
borders, tints) are token-design work, bound by §24 contrast and the contract above. The
six semantic roles and the ember/indigo/paper/ink-bone anchor values are frozen.

**Canonical action contract — accessibility correction `[FROZEN]`:** **Ember actions use
an ink/dark foreground by default.** The convergence mockup's white-on-`#E8430F`
light-mode CTA is **not** canonical — it fails the release contrast standard for normal
text. White foreground is permitted only where the exact tested background/font-size/
weight combination independently meets the required threshold (§24).

## 10. Typography roles — `[FROZEN]`

| Role | Production-safe (first-class) | Licensed upgrade (optional) | Used for · rules |
| --- | --- | --- | --- |
| ATHLETIC DISPLAY | Archivo Black / Archivo Expanded (SIL OFL, variable) | Druk-class / Right Grotesk Tall | Verdicts, screen titles, exercise names, program covers, major training identity. Uppercase, tight tracking, never below ~24px. |
| STRUCTURE / UI | Inter (already shipped) | Söhne | Standard product language, labels, navigation, explanatory text. |
| COACH VOICE | Source Serif 4 (SIL OFL) | Signifier / Tiempos Text | **Genuine coach-authored prose only.** Retires the accidental Georgia fallback. See the monogram exception below. |
| ENGINEERED NUMERALS | IBM Plex Mono (SIL OFL), tabular figures | Söhne Mono | Loads, reps, timers, dates/provenance where appropriate, Live-register instrumentation, eyebrows. |

- `[FROZEN]` The production-safe stack is first-class: **the identity must survive
  without paid fonts.** Licensed typography is an upgrade, never a blocker.
- `[FROZEN]` **Coach serif monogram exception (clarification C):** the voice serif is
  reserved for genuine coach-authored prose. The designed coach **monogram** is the sole
  non-prose exception — an identity mark, not manufactured coach speech or conversational
  content. No other system-generated prose may use Coach Voice typography to imply human
  authorship.
- `[FLEX]` Type scale values, loading strategy (self-hosting, subsetting, fallback
  metrics), and weight selection within each role.

## 11. Iron Line illustration system — `[FROZEN]`

Vytal's owned illustration direction: line-drawn, geometric, on one grid, in the
identity's grade. It represents *training information*. Three families:

1. **Movement-pattern glyphs** — one mark per `movement_pattern` value; the starter
   library requires **15** for full coverage (source of truth:
   `backend/scripts/library_content.py`). Used on session slips, exercise cards,
   execution headers, posters.
2. **Data diagrams** — recipe-driven: week arcs, load ghosts, bar-path motifs,
   session-density marks. Each recipe binds to named fields/rules (§26).
3. **Body / anatomical-region figure** — one commissioned front/rear figure with ~12
   addressable regions driven by the §20 map. Regions fill ember (primary) / ~25% ember
   (secondary). Anatomy as data visualization, never gym-poster anatomy, never medical
   illustration.

**Traceability law (restated):** an athletic visual that cannot be traced to a real
product/training fact is decoration and requires separate justification. Do not ship
dumbbell clip-art, random lightning, mascots, cartoon trainers, or generic gym
ornamentation.

- `[FROZEN]` **Commission does not block engineering (clarification D).** The
  commissioned set is the desired final art system and runs as a parallel
  non-engineering track. C2.0 does not depend on it. Commission order: the 15 pattern
  glyphs + the body figure first, gated on review — the set is load-bearing (§31).
- `[FLEX]` Interim before the commissioned set lands: **data-true** typographic/diagram
  variants of the same components. Generic fitness placeholders, stock clip-art, and
  fabricated decorative glyphs are **not** acceptable interim.
- `[FLEX]` Stroke weight, corner grid, exact glyph drawings — art direction within
  "2px-class bone stroke, geometric, one grid."

## 12. Media system — `[FROZEN]`

- Real coach portraits when genuinely uploaded; the designed monogram fallback when
  absent (§13, §28).
- Exercise demo media in Reference and Execution (delivery depends on §30).
- Graded, owned training/environment photography when available. Photography is always
  optional; every composition works without it (§28).

**The media test:** if the image could be used unchanged in a generic supplement
advertisement, reject it. Prefer movement over posing · environment over physique ·
equipment/material detail · actual training effort · real coach presence.

**Autoplay rules `[FROZEN]`:** never with sound · never on Today · never on Check-in ·
never full-screen unrequested · short muted previews only where specifically useful and
reduced-motion/bandwidth aware · execution demo media defaults tap-to-play.

`[FLEX]` Grade recipe, media formats, storage/CDN strategy. `[FUTURE]` A produced
photography/video library (C2.6 begins maturation; a full library is beyond Cycle 2).

## 13. Coach presence — `[FROZEN]`

- The **byline component** is the coach's standard appearance: name + role attribution,
  portrait when uploaded, serif-monogram tile with ember baseline rule when not. Swapping
  portrait ↔ monogram changes nothing else on the page.
- The monogram fallback reads as a printer's mark, not a missing image — it is the
  mandatory no-media state (§28) and matches the real current staging state (the coach
  has no uploaded portrait). Per clarification C, the monogram is an identity mark, not
  manufactured coach speech.
- Coach words render in the voice serif, verbatim, quoted/attributed, and only genuinely
  authored words ever appear there (§3.8, §4.4, §10).
- Human register may appear inside Calm and Live surfaces; it never becomes a fake
  conversational UI.
- Existing component laws carry forward: no verification rings/dots, demo attribution
  tagged, null coach content collapses (never placeholder-quoted).

## 14. Today — `[FROZEN]` · register: Calm (+ Human byline)

**Today = Editorial structure + readiness-weighted Athletic Presence.** The Cycle-1
content spec ([design/trainee-today.md](trainee-today.md): coach → verdict → why →
session → action → going-well → watch → details; frozen verdict map; one disclosure;
missing ≠ zero) remains in force. This freeze changes the *session object's visual
weight* by readiness band:

| Readiness band | Session object treatment |
| --- | --- |
| READY_TO_PUSH · MAINTAIN | Generated session poster — the stronger athletic training object: duotone grade, movement glyph(s) at poster scale, bar-path/structure motif, all derived from real session fields (name, week position, duration, effort, movement patterns). |
| REDUCE_INTENSITY · RECOVERY_RECOMMENDED · REST | Quieter SessionSlip treatment. The shell cools; ember surface area visibly shrinks (the Calm test). |

**Immovable under readiness change:** verdict hierarchy · coach authorship · primary
action position and meaning · guidance-over-metrics. **The visual temperature changes.
The product truth does not.**

- `[FROZEN]` Poster media derives from real session/program facts (§26 Generated Poster
  Law). No random fitness decoration.
- `[FROZEN]` Rest-day truth (ADR-0019) unchanged: rest renders only when the program
  truthfully continues (`hasRemainingProgram`); rest carries no fake stats; the rest
  action stays the quiet Edit affordance.
- `[FLEX]` Poster composition recipe details, portrait-vs-monogram byline variant,
  whether the poster upgrades in place from Cycle-1's SessionSlip or replaces it.

## 15. Workout Execution — `[FROZEN]` · register: Live (+ Human cues)

The convergence execution frames are the target direction.

- One movement at a time. The **set log is the protagonist**.
- Previous performance visible as *factual reference* (ghosted last-time numbers) —
  reference, not target-shaming.
- Exercise demo/reference supports rather than dominates; real coach cue where present
  (serif, verbatim).
- Large thumb-friendly set controls; session progress visible; next-set/next-movement
  context where truthful.
- **Rest timer is a full interaction state**, not a toast — countdown in engineered
  numerals, next-up context, skippable.
- **Safety entry remains permanently calm** — Calm register embedded inside Live; never
  gamified, never buried.
- No gamification (§35).

**Gym Mode:** dark-first default per §8 — labeled, remembered, explicit Light respected.

`[FLEX]` Control ergonomics, timer defaults, exact layout — bound by the principles above
and §24 target sizes. `[FUTURE]` In-execution knowledge/media display depends on §30
landing (C2.2).

## 16. Program — `[FROZEN]` · register: Calm (+ Human authorship)

- **Generated program identity/cover** from existing facts (name, split, weeks,
  sessions/week, movement-pattern composition). Same Generated Poster Law (§26).
- **Coach presence:** the program is visibly authored by the coach (byline), because it
  truthfully is.
- **Clear week position** ("Week 2 of 4"; week-arc diagram bound to computable
  structure).
- **Mobile: week/session list**, not a compressed seven-column roster.
- **Designed rest state** and **designed deload state** — both first-class, neither an
  empty gap. Deload labels verbatim from the authored flag.
- **Current / next session hierarchy**; provenance demoted to the footer layer (§27).

**Copy truth law:** program language may communicate only **explicitly authored facts**
or **deterministically provable structure/data**. Do not invent intent — "heaviest
week", "peak week", "recovery block" — unless actually represented in the model or
mathematically established by approved product rules. Week-arc heights bind to computable
load or session counts only.

## 17. Check-in — `[FROZEN]` · register: Calm

The ritual model: **approximately three human groups, one decision group at a time**,
ending in the verdict reveal (check-in and Today are one loop, not a form and a redirect).

| Input type | Control |
| --- | --- |
| 0–10 discrete exact | Two-row chip scale where appropriate (44px+ targets at 320px, one tap, radiogroup semantics). |
| 1–5 | Suitable single-row discrete control. |
| Yes / no | Large segmented controls. |
| Sleep hours | Preserves the exact supported values (no lossy slider). |
| Steps | Numeric where appropriate. |

- `[LAW]` Deterministic scoring requirements unchanged. Missing remains missing.
- `[LAW]` **Yesterday: never prefilled, never silently carried. The user must explicitly
  answer today.** This is a data-integrity law.
- `[FLEX]` The under-scale yesterday *marker* is approved for implementation
  exploration/testing but is **not permanently immutable** — if user testing shows
  anchoring or confusion, the presentation may be revised without touching the law above.
- `[FLEX]` Group composition/ordering and sheet/route mechanics, within "≈3 groups, one
  at a time, verdict payoff."

## 18. Progress — `[FROZEN]` · register: Calm

**Progress tells the story of getting stronger. It is not a KPI dashboard.**

- Use: recorded bests · real lift trajectories · training rhythm/history · deterministic
  interpretations where documented rules genuinely support them · **rest represented as
  keeping the program, not as absence**.
- Never: streak anxiety · badges · points · engagement bait · a failure-KPI wall.
- `[LAW]` Every generated interpretation maps to a documented deterministic rule; if the
  rule cannot truthfully fire, the interpretation is omitted (the Going-Well discipline,
  applied to Progress).
- Chart language upgraded to real editorial data-diagram grammar (§11 family 2): axes/
  context where needed, emphasized endpoints, tabular numerals — retiring axis-less
  squiggle rows.

`[FLEX]` Which trajectories/rules ship first in C2.5, chart implementation. `[DECISION]`
Any *new* interpretation rule (a deterministic reading not already in the analytics
engine) is a product decision, not a styling choice.

## 19. Exercise Reference — `[FROZEN]` · register: Calm (+ Human cues)

The **reference-first model**: understanding, not shopping. Trainee Exercise Reference
may present: exercise name · movement pattern · equipment · difficulty · primary/
secondary muscles · anatomical mapping where deterministic (§20) · media · coaching
cues · common mistakes.

**Boundary:** reference and understanding, **not self-programming** — no autonomous
substitutions, no exercise marketplace, no workout picker. Read-only, published-version
content only (§30).

`[FUTURE]` Authoring-side discovery (filter by pattern/muscle/equipment inside coach
Programming) reuses the same vocabulary map later; not Cycle-2 scope.

## 20. Body-map mapping policy — `[FROZEN]`

The exercise model already carries sufficient muscle metadata for the starter library
(`ExerciseVersion.primary_muscle_groups / secondary_muscle_groups`, strings by
convention — §29). A **deterministic presentation mapping** translates known muscle
strings to anatomical regions. No schema change.

**Precision law:** **never imply anatomical precision that the source value does not
contain.** No medical or anatomical inference.

| Source value class | Treatment |
| --- | --- |
| Direct (11 strings) | quadriceps · glutes · hamstrings · chest · triceps · back · shoulders · biceps · core · forearms · hip flexors → each maps 1:1 to its canonical region. |
| Broad (3 strings) | "lower body" · "legs" → explicitly broad whole-lower-body group. "spine" → broad mid-back/torso band. Broad stays visibly broad — **never silently translated into a more precise claim**. |
| Unknown / coach free-text | Remains visible as a text chip · produces **no anatomical highlight** · is never guessed. |

- `[FLEX]` The map lives in the frontend presentation layer (~30-line vocabulary→region
  table; precedent: `frontend/src/.../dailyComponents.ts`); exact region count around ~12
  follows the commissioned figure.
- `[FUTURE]` Authoring-side vocabulary suggestions (so coach-entered strings converge on
  mappable values) — recommended follow-up so the map doesn't decay (§31); not Cycle-2
  scope.

## 21. Login / front door — `[FROZEN]` · register: Calm

- The front door carries the identity: ink/paper ground per theme, athletic-display
  wordmark treatment, editorial hierarchy, quiet form.
- By the §9 contract, signing in is a **non-training action → indigo interaction**; ember
  appears only as identity punctuation, if at all.
- No stock photography, no physique imagery, nothing the media test (§12) would reject.
  The front door must be complete with zero media (§28).
- Demo/registration entries stay honest and quiet (existing invite/demo flows restyled,
  not redesigned; the auth screen never displays demo credentials, and public demo mode
  stays disabled in production — unchanged security posture).
- Per clarification A, this account/entry surface is not required to carry a training
  visualization; a single Iron Line diagram may appear as identity signature only if it
  is a real recipe, not decoration. `[FLEX]` exact composition.

## 22. Mobile behavior — `[FROZEN]`

- Four stable top-level destinations (§6); single-row bottom bar; safe-area insets
  respected; content never trapped under fixed chrome (clearance ≥ nav height remains an
  e2e invariant).
- Touch targets ≥ 44px on all primary interactions; check-in chip scales hold 44px+ at
  320px width.
- No horizontal page scroll at 320px and up; wide content scrolls within its own
  container.
- Program renders as week/session list (§16); execution controls are thumb-reachable
  (§15).
- Display type scales down without dropping below its ~24px floor (§10) — below that, the
  role falls back to Structure/UI type, not a smaller display face.

## 23. Desktop behavior — `[FROZEN]`

- Sidebar navigation with the four destinations; secondary navigation may be exposed
  within them (§6).
- Editorial measure: reading/deciding surfaces keep a bounded content column — desktop is
  not "mobile stretched wide," and never a dashboard grid of cards for its own sake.
- Larger canvas is spent on the identity (poster scale, diagrams, side-by-side reference)
  rather than on more simultaneous metrics — One Dominant Answer holds at every width.
- Coach-side desktop surfaces keep their current structure this cycle, restyled (§6 note).

## 24. Accessibility — `[FROZEN]`

**Accessibility beats aesthetic purity.** Release standard remains WCAG 2.1 AA:

- Text contrast ≥ 4.5:1 (normal) / 3:1 (large); non-text UI contrast ≥ 3:1 — in **both
  themes**, measured on the actual token values.
- The ember action contract (§9) applies: ink/dark foreground by default; white only
  where the tested combination independently passes.
- State is never color-only: readiness, difficulty, deload, errors always carry a textual
  or structural signal alongside color.
- Visible keyboard focus everywhere (indigo focus ring convention); logical heading
  order; landmarks; the verdict remains a real `h1`.
- Reduced motion: every §25 behavior collapses; no state is motion-only.
- Discrete inputs expose real semantics (radiogroup etc.); screen-reader spoken forms
  preserved (StatStrip/session patterns carry forward).
- Dark theme is held to the same standard as light — dark-first makes dark contrast a
  release gate, not an afterthought.

## 25. Motion — `[FROZEN]`

- **Calm register keeps the existing approved budget:** settle / expand / breathe / check
  (Cycle-1 tokens and durations carry forward).
- **Live register earns more:** log-set press → tick + thread advance; rest countdown
  ticking in the mono face; timer→set transition as one slide.
- All motion collapses under `prefers-reduced-motion`; no state is motion-only; **nothing
  ambient** — motion always answers an interaction.
- Autoplay rules per §12.

`[FLEX]` Durations/easings for the new Live behaviors, matching the established token
approach.

## 26. Truthfulness & deterministic presentation — `[LAW]`

- **Score law unchanged:** WORD → INTEGER → SHAPE; integer display; band words come from
  the engine, never re-thresholded in presentation; missing ≠ zero (explicit unavailable
  copy); no red on body data; banded vs. unbanded contract preserved (unbanded scores
  render integer-only, no invented word).
- **Frozen verdict map unchanged** (authority: `design/trainee-today.md` + the
  centralized readiness presentation map). Iron Editorial restyles the verdict; it never
  rewrites it.
- **Interpretation rule:** any generated reading must name its deterministic rule; if the
  rule can't truthfully fire, the element is absent — never approximated.

**Generated poster law:** the session/program poster system must not become randomized
wallpaper. Variation derives from actual training structure where possible: movement-
pattern composition, session structure, program split, week position, exercise ordering,
session density, actual planned load/progression where available and truthfully computed.
**Different training may produce different visual rhythm. The same underlying training
produces stable visual identity.** No random decoration merely to manufacture variety.

## 27. Copy & provenance language — `[LAW]`

- **Implementation vocabulary belongs in provenance. User intent belongs in product
  copy.** Timestamps-with-UTC, version ids, snake_case-derived labels, "atomically",
  engine jargon → the quiet mono provenance layer, never headlines or body copy.
- Banned in user-facing copy (existing law): compliance-flavored language, medical
  framing, repeated disclaimers (say it once), invented coach intent, invented program
  intent (§16).
- Deterministic labels render verbatim from their authored source (deload flag → the
  authored label), not paraphrased into stronger claims.
- Proposed copy is marked proposed until product approves it — never silently canonized.
- C2.5 includes the copy de-leak sweep (Assessment's titleized snake_case, unit labels
  like "Hydration Ml", timezone leakage) — §32.

## 28. No-media behavior — `[FROZEN]`

The identity was never built on media, so it provably does not collapse without it.

| Absent media | Designed state |
| --- | --- |
| Coach portrait | Serif monogram tile + ember baseline rule byline (§13). Never a grey silhouette. |
| Exercise media | Movement-pattern glyph + structured knowledge (pattern, muscles, cues) carries the card; body-map region where deterministic. |
| Program photography | Generated cover from real structure (§16) — the default, not the fallback. |
| Session poster imagery | Generated poster from session facts (§14); photography may later replace the background *inside the same object*. |

No layout reserves an empty slot for media that isn't there; compositions are complete in
their no-media form.

## 29. Currently-possible capability map

What the identity can render *today* from real data, verified against the repository at
v0.5.0 — versus what is genuinely future.

| Capability | Status | Reality |
| --- | --- | --- |
| Movement/muscle/equipment metadata | EXISTS | `ExerciseVersion.movement_pattern`, `equipment[]`, `primary_muscle_groups[]` (required), `secondary_muscle_groups[]` (`models.py:568–571`); 100% coverage across the 28-exercise starter library; strings by convention, not enums. |
| Coaching cues · common mistakes · difficulty | EXISTS | On `ExerciseVersion` (ADR-0018), populated for the starter library — real serif-cue/mistakes content available now. |
| Exercise media references | EXISTS (model) | Media fields exist on the exercise model (ADR-0018); **actual asset coverage** for the starter library must be verified at C2.2 — design must not assume assets exist. |
| Readiness verdicts, bands, atmosphere | EXISTS | Deterministic engine + frozen verdict map + Cycle-1 atmosphere layer. |
| Program structure for covers/arcs | EXISTS | Name, weeks, sessions/week, ordering, authored deload flag, prescriptions — enough for generated covers, week arcs, density marks. |
| History for load ghosts / bests / rhythm | EXISTS | `workout-load-v1` engine, all-history recorded best, adherence/skip rules, session history. |
| **Theme preference persistence** | **EXISTS (backend)** | Persisted `UserPreferences.theme` column (Alembic head 0017, ADR-0012) + `GET`/`PUT /preferences` (`backend/app/api/profile.py`). **No new backend/schema/migration required.** Frontend does not yet consume it — C2.0/C2.1 frontend wiring. |
| Trainee access to exercise knowledge/media in execution & reference | APPROVED — TO BUILD | The one genuine gap: the trainee session payload currently exposes only `exercise_name`, `tracking_mode`, `safety_cues`, `prescription_snapshot`. §30 records the approved need; lands in C2.2. |
| Iron Line commissioned set | FUTURE (commission) | 15 glyphs + body figure + diagram recipes — external commission, gated on review (§11); interim data-true variants allowed. |
| Owned photography/video library | FUTURE | C2.6 begins maturation; composition never depends on it (§28). |
| Coach-side vocabulary suggestions / authoring discovery | FUTURE | Keep the §20 map from decaying / reuse it in Programming; not Cycle-2 scope. |

## 30. Approved enabling capability: trainee exercise/media read access — APPROVED

**Product need (approved):** a narrow, trainee-readable surface for the exercise
knowledge required by Workout Execution and Exercise Reference.

**Required presentation fields:** exercise name · movement pattern · equipment ·
difficulty · primary/secondary muscle groups (feeding the §20 map) · coaching cues ·
common mistakes · exercise media references.

**Boundaries (frozen):**

- **Read-only.** Published-version content integrity preserved; authorization preserved;
  server-side protections never weakened (demo stays read-only; cross-account discovery
  returns 404). This builds on ADR-0018's deferred "trainee-scoped delivery
  authorization walk."
- Grants **no** program authoring, exercise authoring, autonomous substitution, workout
  generation, or coach-private editing access.

`[FLEX]` Per sign-off, this specification defines **no backend architecture** — route
shape, payload design, versioning, and caching are the C2.2 engineering design, reviewed
against these boundaries and AGENTS.md's authorization/demo invariants.

## 31. Known risks & debt

**Identity risks (accepted with mitigations):**

- **Generated posters at scale:** many programs share few patterns → wallpaper sameness.
  Mitigation: recipe varies by real structure (§26); photography upgrade path inside the
  same object.
- **Illustration commission quality is load-bearing.** Mitigation: commission glyphs +
  body figure first, gate on review (§11).
- **Coach free-text muscle metadata won't map** → text-chip fallback exists, but
  authoring suggestions should follow or the map decays (`[FUTURE]`).
- **Legacy-screen contrast during migration:** unmigrated light screens inside a dark
  shell look dated mid-cycle. Mitigation: sequencing keeps the window short — shell +
  Today first (§32, §34).
- **4-tab findability:** Workouts/Assessment/Settings relocate — real-user findability
  check is a C2.1 acceptance criterion (§33).

**Existing engineering debt (pre-freeze, still open):**

- App-wide dark pending chrome migration (resolved by C2.1; §34).
- `workout-execution.spec.ts:114` date-sensitive flake (pre-existing).
- Evidence grouping in Today's details (deferred from Cycle 1).

## 32. Experience Cycle 2 implementation order — `[FROZEN]` (sequence) · `[DECISION]` (start)

The phase sequence is frozen; **starting C2.0 still requires explicit go-ahead** (Cycle 2
has not begun). Each phase is a mergeable, gated unit per §33.

| Phase | Scope | Spec sections |
| --- | --- | --- |
| C2.0 | **Identity foundation** — v2 tokens (color/type/motion), production-safe type stack loading, theme-preference model + Light/Dark/System semantics wired to the existing `GET`/`PUT /preferences` endpoint, copy/provenance sweep groundwork. No user-facing theme control and no layout change yet (clarification B). | §8–§10, §25, §27, §29 |
| C2.1 | **Shell + IA + app-wide theming** — four-tab trainee IA, dark-first trainee shell, light "print edition", chrome migration off the route-scoped seam, activation of the user-facing Light/Dark/System control, Today re-skin incl. readiness-weighted poster (interim data-true variant until the commissioned set lands). Real-user findability check. | §6–§8, §14, §22–§23 |
| C2.2 | **Execution / Gym Mode** — Live register, set-log protagonist, full-state rest timer, ghosted history, + the approved trainee exercise/media read capability (engineering design per §30). | §15, §30 |
| C2.3 | **Program identity** — generated covers, week arcs, mobile week-list, designed rest/deload states, copy-truth enforcement, provenance demotion. | §16 |
| C2.4 | **Check-in ritual** — three groups, chip scales, control set, verdict-reveal loop, yesterday marker (testable). | §17 |
| C2.5 | **Progress + Reference** — story-of-strength Progress, deterministic interpretations, exercise reference + body map (§20 map + commissioned figure), Assessment/copy de-leak. | §18–§20, §27 |
| C2.6 | **Media maturation** — demo media delivery polish, grade recipes, photography guidelines, poster background upgrade path. | §12 |

**Parallel track (non-engineering):** commission Iron Line — 15 glyphs + body figure
first, gated on review — starting immediately, so C2.1's poster and C2.5's body map can
adopt the real set without resequencing (clarification D).

## 33. PX acceptance criteria — `[FROZEN]`

Every Cycle-2 phase passes all of these before merge (the existing 4-review PX gate
continues to apply):

1. **Register declared** — the phase's screens name their register(s) (§5) in the phase
   doc.
2. **Truthfulness audit** — every training visual and generated line names its source
   field/rule (§4.2, §26); no invented intent (§16, §27).
3. **Both themes** — light and dark reviewed and tested; contrast measured per §24
   including the ember foreground contract.
4. **No-media review** — every new surface demonstrated in its zero-media state (§28).
5. **Accessibility gate** — §24 in full.
6. **Mobile invariants** — 320px no-horizontal-scroll, clearance ≥ fixed-nav height
   (structural e2e assertion), 44px targets.
7. **Determinism unchanged** — no scoring/verdict/engine change rides in on a visual
   phase.
8. **Full validation** — frontend tsc / eslint (0 warnings) / vitest / build, backend
   ruff / pytest, isolated e2e green; screenshots regenerated where specs own them.
9. **C2.1 special:** findability check with the real testing user on the 4-tab IA
   (§6, §31).
10. **Copy status** — any proposed copy is explicitly approved or explicitly deferred;
    nothing marked proposed ships as silent canon (§27).

## 34. Migration from v0.5.0 surfaces

- **Theme architecture:** Cycle 1's route-scoped dark (`data-theme` on `<main>` via
  `useMorningBriefTheme`) is explicitly transitional. C2.1 migrates chrome + routes to
  app-wide theming with the §8 preference model; the light-chrome/dark-content seam is
  removed, not preserved. This supersedes ADR-0019's *theming* decision (the rejection of
  app-wide dark / in-app switch on scope grounds); ADR-0019's rest-day integrity rulings
  remain binding. `[FLEX]` mechanism.
- **Tokens:** the Cycle-1 `--mb-*` layer is the seed of the v2 system. `[FLEX]` whether
  v2 extends the `mb-` namespace or introduces a successor with aliases — frozen
  constraint: one token system at the end of C2.1 for migrated surfaces; no third
  parallel palette; legacy `--color-*` retires per-surface as screens migrate.
- **Morning Brief components** (Score, EvidenceRow, SessionSlip, CoachAttribution/
  CoachMessage, DisclosureBlock, GuidanceHero…) carry forward as the component seed —
  Iron Editorial restyles and extends them; their contracts/laws (§26) do not regress.
- **Navigation:** the 7-item two-row trainee nav retires at C2.1; its clearance debt and
  the underlying Tailwind calc gotcha die with it (the structural clearance e2e assertion
  stays).
- **Unmigrated screens** keep functioning on the legacy system during the window;
  sequencing minimizes the mixed period (§31). Coach surfaces restyle without structural
  change this cycle.
- **Frozen content specs** (Today content spec, ADR-0019 rest integrity, score law)
  migrate untouched — presentation changes only where this document explicitly says so.
- **As-built references:** [design-system.md](../design-system.md) and
  [design/components.md](components.md) describe v0.5.0 as-built; each phase supersedes
  the relevant parts and updates `components.md`; per-screen specs gain a register header.

## 35. Explicit anti-goals — `[LAW]`

- No gamification: streaks, badges, points, leaderboards, engagement bait, dopamine-
  manufacturing completion celebrations.
- No social layer, no marketplace, no workout picker / trainee self-programming.
- No AI-coach behavior, no fake conversational persona, no manufactured coach voice.
- No stock physique/supplement-ad imagery (§12 media test), no mascots, no clip-art, no
  random athletic decoration.
- No neon "cyber-fitness" palette drift; no lime/chartreuse accent.
- No medical framing, no anatomical precision beyond source data, no body-data alarm
  states.
- No KPI dashboard as a product surface; no alert walls; no repeated disclaimers.
- No dark patterns around theme (forced dark), motion (ambient churn), or media
  (autoplay with sound).
- No scoring/engine changes smuggled in as visual work; no capability work (M5+) inside
  Cycle 2.

## 36. Decision log / freeze summary

| Date | Decision | Status |
| --- | --- | --- |
| 2026-08-12 | Iron Editorial = canonical FitIntel visual direction (north star, registers, palette, type roles, Iron Line, media system, per-surface directions §14–§21). | FROZEN |
| 2026-08-12 | Four-tab trainee IA: TODAY / TRAIN / PROGRESS / YOU (consolidation, not deletion). | FROZEN |
| 2026-08-12 | Trainee exercise-knowledge/media read access — product need approved, read-only, fields per §30; backend design deferred to C2.2 engineering. | APPROVED |
| 2026-08-12 | Muscle vocabulary → body-region presentation mapping with the precision law (broad stays broad; unknown = text, no highlight, never guessed). | APPROVED |
| 2026-08-12 | Ember action foreground correction: ink/dark by default; white only where independently contrast-proven (overrides the convergence mockup's light-mode CTA). | FROZEN |
| 2026-08-12 | Clarification A — "training seen" scope excludes required visuals on utility/account surfaces. | FROZEN |
| 2026-08-12 | Clarification B — C2.0 prepares theme persistence/semantics (no user-facing control); C2.1 activates it with app-wide migration. Persistence path already exists in the backend (no new backend). | FROZEN |
| 2026-08-12 | Clarification C — coach monogram is the sole non-prose Coach-Voice exception; an identity mark, not manufactured speech. | FROZEN |
| 2026-08-12 | Clarification D — Iron Line commission is a parallel track; does not block C2.0/C2.1; interim must be data-true, never generic placeholder. | FROZEN |
| 2026-08-12 | Yesterday-marker presentation: approved for exploration/testing, revisable on evidence; the never-prefill law is permanent. | FLEX (law fixed) |
| 2026-08-12 | Gym Mode = dark-first default, labeled, remembered, explicit light wins. | FROZEN |
| 2026-08-12 | New product laws (§4): training seen not described · provenance/copy separation · visual traceability · authorship honesty · no-media completeness. | LAW |
| 2026-08-12 | C2.0–C2.6 sequence frozen as the Cycle-2 shape; **Cycle 2 start not yet authorized**. | DECISION PENDING |
| 2026-08-06 | Trainee Today content spec frozen (`design/trainee-today.md`) — presentation amended by §14 only. | FROZEN (prior) |
| 2026-08-12 | ADR-0019 rest-day integrity; score law; frozen verdict map. ADR-0019 theming decision superseded in part (§8, §34). | LAW (prior) |

---

*Design authority only. This document introduces no code and no repository behavior
change. No Experience Cycle 2 implementation begins until explicitly authorized.*
