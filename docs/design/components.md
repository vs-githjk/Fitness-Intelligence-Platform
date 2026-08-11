# Morning Brief component layer

The Morning Brief design system (see [../product-principles.md](../product-principles.md)
experience principles and the per-screen specs in this folder) is built in layers.
This document records the layers implemented so far and the rules that govern them.
It is a living reference for the components, not a product decision — the frozen
product decisions live in the per-screen specs.

Components are added to `frontend/src/components/ui.tsx` (the single component
library) and consume the `--mb-*` token system from `frontend/src/index.css` via
the Tailwind `mb-*` utilities. They are **additive**: the legacy components in the
same file are unchanged, so unmigrated surfaces stay visually stable. New Morning
Brief components must render correctly in both the light and dark resolved themes.

## Phase A — foundation (shipped)

Design tokens + dual-theme architecture + theme switching. See `index.css`
(`--mb-*` tokens, `:root[data-theme="dark"]`), `tailwind.config.js` (`mb-*`
utilities), and `theme.ts` / `theme-context.ts` / `ThemeProvider.tsx`. The app
defaults to the `light` preference so legacy surfaces are unchanged.

## Phase B — primitives + intelligence layer (shipped)

### The score law: WORD → INTEGER → SHAPE

Formatting helpers live in `frontend/src/lib/score.ts` and apply **only** to
0–100 band-interpreted product scores (Health Index, Recovery, Activity,
Nutrition, Readiness, Adherence, …). They must **not** be used for resistance
load, weight prescriptions, distance, durations, or any measurement where
precision matters — those keep their real values and their own formatting.

- `roundScore` / `formatScore` — integer display of a 0–100 score.
- `isScoreMissing` — missing is `null` / `undefined` / `NaN`.
- `trendDirection` / `formatScoreDelta` — factual signed direction of a delta.

Binding rules (enforced by the component contracts and covered by tests):

1. 0–100 scores display as **integers**; backend values are never mutated.
2. **Missing is never zero** — it renders as `Unavailable` or approved
   context-specific copy.
3. A score's **meaning/band comes from a backend-provided word**; components never
   infer or re-threshold a band from the raw number.
4. **No red** for body/readiness data — the score tone set is
   `neutral | positive | caution | info` only; red is unexpressible.
5. Trend direction is **factual** (arithmetic sign of the rounded delta), not an
   interpretation, and is legible without color.
6. Decorative shape (bars, dots) is **subordinate** to the word/value and never
   carries meaning alone.

### Primitives

| Component | Purpose | Key props | Accessibility |
| --- | --- | --- | --- |
| `PrimaryCTA` | the one prominent action on a surface | `variant` (`filled`/`ghost`/`text`), `loading`, standard button attrs | real `<button>`; visible focus; `disabled`+`aria-busy` while loading; label kept in place (no layout shift) |
| `SectionHeader` | quiet caps section label | `as` (`h2`/`h3`), `action` | renders a real heading; never competes with content |
| `NoteLine` | one line of guidance | `tone` (`success`/`caution`/`neutral`) | meaning carried by the sentence + an assistive-tech label; dot is decorative (`aria-hidden`) |
| `DisclosureBlock` | progressive disclosure of evidence | `summary`, `defaultOpen` | button trigger with `aria-expanded`/`aria-controls`; keyboard operable; content hidden when closed |
| `SystemBanner` | product/system-condition notice | `tone` (`info`/`demo`/`offline`), `title` | `role="status"`; tone set has **no** risk/error state — never for body-data warnings |

### Intelligence components

| Component | Purpose | Key props | Accessibility |
| --- | --- | --- | --- |
| `Score` | the score law as a component | `value` (nullable), **`word` (required)**, `tone` (explicit), `variant` (`row`/`hero`), `unavailableLabel` | word + value exposed as text; missing announced as text; decorative shape (none in this layer) |
| `TrendDelta` | factual direction + signed value of a score delta | `delta` | glyph + assistive-tech direction word + signed value; no color-only meaning |
| `EvidenceRow` | a labelled evidence row | `label`, `value`, `word`, `tone`, `trend`, `unavailableLabel` | composes `Score` (+ optional `TrendDelta`) |

### Usage rules

- Use **one `PrimaryCTA` (filled)** per surface; secondary actions are `ghost`/`text`.
- `Score`/`EvidenceRow` **require an explicit `word`** and take `tone` only as an
  explicit prop — pass the backend interpretation; never derive it client-side.
- Do not apply score rounding to load/weight/distance/duration values.
- `SystemBanner` is for system conditions only; body-data concerns use `NoteLine`
  (`caution`) inside the screen's guidance hierarchy.
- The "N more notes" pattern is composed from a `DisclosureBlock` wrapping
  additional `NoteLine`s (no separate component in this layer).

## Phase C — voice + athletic objects (shipped)

Voice (`frontend/src/components/coach.tsx`) and athletic objects
(`frontend/src/components/session.tsx`). Presentational and reusable outside Today;
they contain no routing, API, auth, or score-law logic (verified by a source-scan
test). They consume the `--mb-*` tokens and render in both resolved themes.

### Voice

| Component | Purpose | Variants | Accessibility |
| --- | --- | --- | --- |
| `CoachAttribution` | reusable human-authorship marker — a person, not a status widget | `sender`, `inline`, `byline`; optional `demo` tag | name always present even if imagery fails; decorative dash `aria-hidden`; avatar delegates to the shared `Avatar` (empty alt, name adjacent) |
| `CoachMessage` | verbatim human-authored content in the serif voice (SERIF = HUMAN) | with / without attribution | semantic `figure`/`blockquote`/`figcaption`; absent or blank note collapses with no empty chrome |

Laws: only real coach-authored content uses `CoachMessage`; product- and
AI-generated text never do. No status rings, presence dots, verification, or
invented titles. An absent coach collapses to nothing. Not interactive on guidance
surfaces.

### Athletic objects

| Component | Purpose | Variants | Accessibility |
| --- | --- | --- | --- |
| `StatStrip` | factual prescription facts inside an athletic object | duration, target effort (extensible via further optional props) | compact visual text + a spoken `sr-only` form; missing facts collapse; an empty strip renders nothing |
| `SessionSlip` | the primary athletic object — an inset session | `workout`, `rest`, `done`, `compact-row` | done state is announced ("Completed workout: …"); the name is never struck through |

Laws: `StatStrip` carries facts only — no readiness/score, no status colors, no
red, no fake precision, no re-thresholding. `SessionSlip` is an **Inset** object (no
new elevation level) that composes `name`, optional `context`/`description`,
`StatStrip`, `CoachMessage`, and an **action slot** — the caller supplies the
semantic button/link, so the object never owns routing. Rest is a legitimate
programmed state with no fake stats and no guilt/medical framing; done is calm
closure with no confetti, badges, or points.

### Intended future reuse

- `CoachAttribution` / `CoachMessage` → Today, coach trainee-detail, programming
  notes, future messaging, adaptive-coaching intent, the AI-vs-human boundary.
- `StatStrip` / `SessionSlip` → Today, Workout Execution header, Programming
  schedule and history rows (`compact-row`).

### Non-responsibilities

These objects do not fetch data, navigate, resolve auth, format scores, or apply
readiness interpretation. Which action and which data appear is decided at the
later screen-assembly phase.

## Phase D — composition + the checked-in Today (shipped)

The first phase to visibly change a product screen: the checked-in Trainee Today
now renders the Morning Brief hierarchy (coach → verdict → why → session → action →
going well → keep an eye on → today's details). Loading, error, and not-checked-in
states are intentionally unchanged (their redesign is a later phase).

### Composition shells (`frontend/src/components/guidance.tsx`)

| Component | Purpose | Rules |
| --- | --- | --- |
| `AtmosphereCanvas` | whisper-level readiness background | receives a resolved band (never a score), maps it to the atmosphere token, renders a decorative `aria-hidden` tint; both themes; neutral supported; never carries meaning alone |
| `GuidanceHero` | the single dominant Surface for the one answer | composes attribution / greeting / verdict / reason / session / action slots; verdict is words-first; contains no `Score` and no raw readiness number; a labelled region |

### Presentation derivations (`frontend/src/lib/today.ts`, pure)

`readinessPresentation` is the **one** centralized mapping from the backend
`readiness_state` to Morning Brief presentation (frozen verdict + atmosphere band) —
so word and atmosphere can never drift. Also: `reasonLine`, `selectTodayWorkout`
(server `local_today`, actionable + id only), `workoutContext`, `scoreTrend`,
`selectGoingWell`, `selectWatch`. It selects and formats; it is not a scoring
engine and never derives a band from a number.

### Assembly

`MorningBriefToday` (`frontend/src/pages/TodayView.tsx`) composes the above with the
Phase B/C primitives, wired to existing data (`/daily-scores/today`, `/trainee/coach`,
`/trainee/program`, `/daily-scores/trends`, `/health-index/current`) — no new
endpoints. The Start action is a router `Link` to `/trainee/workouts/:id` styled via
the new exported `ctaClassName` (so `ui.tsx` stays router-free). `Score`/`EvidenceRow`
gained an **optional `word`**: recovery/activity/nutrition have no backend band, so
they render as an integer only — a band is never invented.

## Deviations / decisions forced by repository reality

- **Additive over in-place evolution.** `Button`, `Disclosure`, and `StatusNotice`
  were left unchanged rather than re-pointed at `--mb-*` tokens, because that would
  visually change every unmigrated screen. New `mb` components are added alongside.
- **Tree-shaken until consumed.** The Phase B components are exported and tested but
  not yet imported by any screen, so Rollup omits them from the app bundle until a
  surface uses them (Phase C). Only the small `mb-*` CSS utilities are emitted now.
- **Navigation-CTA link semantics** (e.g. a "Start workout" link styled as a CTA)
  are composed at screen-assembly time (Phase C); `PrimaryCTA` is the `<button>`
  primitive with the full loading/disabled/focus contract.
- **Shape tier** (subordinate bars) is composed where needed rather than baked into
  `Score`, keeping the law (shape never carries meaning alone) impossible to break.
- **Coach avatar reuse (Phase C).** `CoachAttribution` composes the shared `Avatar`
  (the canonical person component that encapsulates authorized image loading) rather
  than reinventing it; `Avatar`'s internals are still legacy-token based and will
  migrate with `Avatar` in a later cycle.
- **Quote-rule color (Phase C).** `CoachMessage` uses a neutral `border-mb-muted/40`
  left rule instead of the comp's fixed `indigo-900` — the latter is invisible on the
  dark theme and would overload the action-indigo. The serif (`font-voice`) carries
  the "human voice" signal per the law, so no new token was required.
- **Attribution avatar size (Phase C).** Attribution reuses `Avatar`'s existing
  `sm`/`md` sizes rather than adding a 24px size, to avoid modifying a shared
  component that other surfaces render.
- **Band-less scores (Phase D).** Only readiness has a backend band; recovery,
  activity, and nutrition scores do not. Rather than invent bands, `Score`/
  `EvidenceRow` render those as an integer with no word — the score law forbids a
  derived band, so a band-less number simply omits the word.
- **Reason line + Going Well (Phase D).** The reason is a deterministic per-state
  sentence (a conservative, truthful fallback; richer trend-composed reasons are
  deferred). Going Well surfaces one genuinely positive score trend since the last
  check-in, or nothing — no streaks, no invented positives.
- **Deferred Today states unchanged (Phase D).** The not-checked-in invitation
  (including its baseline Health Index reference), loading, and error branches are
  kept exactly as before so those deferred states stay stable.
