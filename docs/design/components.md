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
