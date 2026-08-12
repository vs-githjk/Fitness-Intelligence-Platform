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

## Phase D.1 — spec-conformance hardening (shipped)

A tightly scoped conformance pass over the Phase D checked-in Today (no new states,
no redesign):

- **Score law restored as a typed contract.** `Score`/`EvidenceRow` no longer take
  an optional `word`. They take a discriminated union — `{ banded: true; word }`
  (the backend interpretation is required; WORD → INTEGER cannot be dropped) or
  `{ banded: false }` (a neutral integer metric that *cannot* accept a word, so a
  band is never invented). Health Index renders `banded`; recovery/activity/
  nutrition and the component breakdown render `banded={false}`.
- **Product vocabulary at the presentation boundary.** `lib/dailyComponents.ts`
  maps every Daily Intelligence component key to approved human copy; Today no
  longer titleizes raw keys or surfaces raw explanations, so the frozen §8 removed
  vocabulary ("compliance", "arbitrary units", snake_case) can no longer leak.
  Domain keys are untouched.
- **Trend recency truthfulness.** `scoreTrend` is replaced by `latestTrend`, which
  returns a change only when the latest recorded point is present; "…up since your
  last check-in" can no longer be attached to an older pair. Going Well omits
  rather than overstate.
- **Guidance spine.** The checked-in Today composition is constrained to the
  existing `max-w-mb-guidance` (≈640px) centred measure; extra desktop width is
  whitespace, and the hero/session/evidence inherit the readable line length.
- **Mobile CTA rhythm.** The hero's session/action top margin is trimmed
  (`mt-6`→`mt-5`) so the primary action sits higher relative to the mobile fold and
  the fixed bottom nav, without compressing the screen or touching coach content.

## Phase E — complete Today state coverage (shipped)

Phase E completes the remaining approved Today states without redesigning Today.
There is still **one** Today screen: every state re-weights the same Morning Brief
composition (the hero, the SessionSlip variants, the evidence disclosure), so
spatial memory stays stable. No metric dashboards, warning walls, contact cards,
gamification, or medical framing return.

### New state components

| Component | Location | Purpose |
| --- | --- | --- |
| `StateSurface` | `ui.tsx` | one calm dominant Surface (heading + optional eyebrow/body + one action) for the invitation, error, and offline states — no red, no scaffolding, no metric grid |
| `GhostPlan` | `guidance.tsx` | the loading state, shaped like the plan (attribution → verdict → reason → session), `role="status"` with a human label; no metric-card skeleton, no shimmer, no spinner, no zeroed score |

The checked-in states reuse the existing `SessionSlip` **rest** and **done**
variants (Phase C) — Phase E only decides *which* variant renders.

### State resolver (`frontend/src/lib/todayState.ts`, pure, tested)

`resolveCheckedInPlan(workspace)` is the single deterministic resolver for the
checked-in body. It reads only the real domain model (`scheduled_workouts` +
`status` + `local_today` + `current_assignment`) and returns one of:

- `workout` — an actionable session today (preferred over everything);
- `completed` — today's only session(s) are finished (`completed`/`partial`);
- `rest` — an empty schedule today that is a genuine **programmed rest day**, plus
  the `nextUp` session;
- `plan_only` — checked in with guidance but no session to launch (no active
  program, a lapsed/finished program, an absent workspace, or a day whose only
  sessions were skipped/cancelled); the session slot collapses cleanly.

Also `nextUpWorkout` and `relativeDay` (a truthful "tomorrow" / "on Thursday").
Rest uses the frozen §8 copy and a **neutral** atmosphere so strong readiness never
reads as "override your rest"; every other state keeps the readiness verdict.

**Rest-day integrity (authored, not inferred).** The domain has no rest flag and no
rest session type — per the product model an empty weekday *is* a rest day
(`docs/user-manual-coach.md`, `docs/design/trainee-today.md`), and the full program
is materialized eagerly at assignment time, so within a program's date range an empty
today is authoritatively rest. But `TrainingAssignmentStatus` has **no `COMPLETED`
state**: an assignment stays `ACTIVE` indefinitely after its final workout, and
`effective_end_date` is `null` for a live assignment. "Active program + empty today"
therefore cannot by itself tell a genuine mid-program rest day apart from a program
that has simply run out. The resolver's `hasRemainingProgram` guard closes this: `rest`
is returned only while the **current** assignment still has an actionable session
strictly after today (the materialized schedule is the authority). Past the last
workout — a lapsed program, or a between-programs gap whose only future sessions belong
to an *upcoming* assignment — Today shows `plan_only`, never a fabricated
"take today off — on purpose." This is a Coach-First / authored-not-generated
requirement: Today never invents coach intent the domain cannot substantiate.

### Page-level state precedence + query boundaries (`DailyPages.TodayPage`)

Deterministic order: **offline-with-no-usable-data → loading → core error →
checked-in plan → invitation.** Demo and offline-with-data are overlays, not
separate pages.

Query classification (§11):

- **CORE** — `GET /daily-scores/today`. It *is* the plan/verdict, and its 404 is
  exactly the "not checked in" signal, so it alone drives loading / error / plan /
  invite. Only a **non-404** failure is an error; a 404 is the invitation.
- **OPTIONAL / enrichment** — `/trainee/program`, `/trainee/coach`,
  `/daily-scores/trends`, `/health-index/current`. Each may fail and simply collapse
  its slot (session → `plan_only`, coach attribution omitted, going-well omitted,
  Health Index row omitted). A failed garnish never turns Today into an error.

Connectivity is read truthfully via `useOnlineStatus` (`navigator.onLine` +
online/offline events; **no** persistence layer is added). Offline behaviour:
if usable in-session data exists it stays visible under an offline `SystemBanner`
and the Start action is a genuinely **disabled** button (starting a workout needs a
connection); with no usable data (e.g. a reload while offline) the offline
`StateSurface` shows. The demo condition is already announced app-wide by
`AppShell`'s banner, so Today adds the coach "Demo" attribution tag and disables
editing rather than stacking a second banner.

### Unresolved copy dependencies (not silently resolved)

- **Completed-workout copy** is an open item in the frozen spec (§23 #4). Phase E
  ships the stable done state (SessionSlip `done`, no Start, coach note retained,
  readiness verdict kept for spatial memory) but invents no new completion copy.
- **Rest-day primary action.** The frozen §8 lists "Log how you feel →", which
  assumes a not-yet-logged day; a checked-in rest day has already logged, so Today
  shows the quiet "Edit today's check-in" affordance instead of implying a re-log.

## Final polish — release readiness (shipped)

The last Trainee Today phase. No redesign, no new hierarchy — the same one screen,
finished. Copy decisions are recorded in [ADR-0019](../decisions/README.md).

### Route-scoped dark theme

Today renders **first-class dark** (real `--mb-*` dark tokens, not inverted light).
Dark is scoped to the Today content region via `data-theme` on `<main>`
(`AppShell morningBrief` mode) rather than the document root, because Morning Brief
primitives (e.g. `SessionSlip`) are reused on unmigrated, light-only legacy screens —
a global flip would strand them. `useMorningBriefTheme` resolves the region's theme:
an explicit stored preference wins, otherwise it follows the OS `prefers-color-scheme`
(read synchronously, so no flash). There is **no in-app theme switch** (that would
expand scope), so dark is reached today by a trainee whose device is in dark mode.
- **User-reachable now:** dark Today for OS-dark trainees. **Not reachable:** an
  in-app toggle, and dark on any non-Today / legacy surface.
- **Protected:** the shared chrome (sidebar / mobile header / bottom nav) and all
  legacy `--color-*` surfaces stay light. The CSS dark block matches
  `:root[data-theme='dark'], [data-theme='dark']`; a `[data-theme='light']` block
  re-asserts light so a light region survives under a dark ancestor.
- The morningBrief `<main>` is a full-bleed `--mb-page` canvas framed by the light
  chrome — a controlled migration state until the chrome itself migrates.

### Atmosphere calibration (both themes)

The whisper tint was almost invisible at light α 0.06. Light is now α **0.09** with a
0.10 edge-light; dark is α **0.14** with a 0.28 edge (dark reads stronger). Each band
keeps a distinct emotional temperature (gold = capable, blue = steady, amber = ease
off, violet = care) but the WORD always carries meaning — the gradient is decorative,
never status-loud, amber never alarming, gold never celebratory. Programmed rest stays
**neutral** (no atmosphere) so strong readiness never reads as "override your rest".

### Approved motion budget (`tailwind.config.js` keyframes)

Only the approved motion, all collapsing to instant under `prefers-reduced-motion`
(global reset + `motion-reduce:animate-none`), and no state ever carried by motion:
- `mb-settle` — one entrance per screen (fade + 8px rise) on the Today spine / hero.
- `mb-expand` — inline disclosure expansion.
- `mb-breathe` — the GhostPlan loading breathe (opacity only, **no shimmer**).
- `mb-check` — a one-time completed-session check settle, plus a subdued success
  edge-light on the done slip (quiet, once — no confetti, no ambient loop).

### Today's Details density

Two clear tiers under the one disclosure: the four summary scores, then the
per-component mechanics beneath a thin rule (a `<dl>` ledger with aligned scores and
subordinated `text-mb-micro` explanations). Density is managed by **hierarchy and
rhythm only** — no cards, no tiles, no invented taxonomy, and every deterministic
explanation stays visible (nothing hidden behind a second disclosure).

### Demo Start (truthful read-only)

The demo backend enforces `403` on starting a workout, so Today no longer offers a
live Start link that would only meet that refusal: for demo users `StartAction`
renders a **disabled** control (same pattern as offline), consistent with the app-wide
"changes are disabled" demo banner. Server enforcement is unchanged; no fake execution.

### Mobile fixed-nav clearance

`<main>` bottom padding is `calc(6rem + env(safe-area-inset-bottom))` and `html` carries
`scroll-padding-bottom` of the nav height, so no interactive control is trapped beneath
the fixed bottom nav and keyboard focus never lands obscured (verified by a real pointer
click on the end-of-screen disclosure at 320 / 390×700 / 390×844).

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
- **Band-less scores (Phase D → D.1).** Only readiness/Health Index have a backend
  band; recovery, activity, and nutrition scores do not. Phase D first expressed
  this with an optional `word`; Phase D.1 hardened it into a discriminated
  `banded` union so a band is impossible to invent *and* impossible to omit where
  one exists (see the Phase D.1 section above).
- **Reason line + Going Well (Phase D).** The reason is a deterministic per-state
  sentence (a conservative, truthful fallback; richer trend-composed reasons are
  deferred). Going Well surfaces one genuinely positive score trend since the last
  check-in, or nothing — no streaks, no invented positives.
- **Deferred Today states unchanged (Phase D).** The not-checked-in invitation
  (including its baseline Health Index reference), loading, and error branches are
  kept exactly as before so those deferred states stay stable.
