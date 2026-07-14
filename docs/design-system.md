# Fitness Intelligence design system

This document describes the design system implemented in the current frontend. It is a reference for extending the existing baseline-assessment experience without introducing visual or interaction patterns that the application does not yet use.

## Visual principles

The visual direction is **calm athletic intelligence**:

- Trustworthy structure comes from deep slate text, off-white page backgrounds, white surfaces, restrained indigo actions, and clear borders.
- Health information is presented as explainable coaching data, not as a diagnosis or a judgment of the person.
- Status color is reserved for meaning. Green indicates a genuinely positive state, amber indicates attention, orange-red indicates elevated concern, and red indicates critical or immediate safety guidance.
- Scores are prominent, but supporting explanations, component contributions, dates, and missing-data details remain available.
- Coach screens favor operational density and prioritization. Trainee screens favor a focused sequence and plain-language explanation.
- Decoration is restrained. The interface uses simple Lucide icons, two subtle shadow levels, and limited geometric decoration on the desktop authentication panel.

## Semantic color tokens

Colors are CSS custom properties in `frontend/src/index.css` and are mapped to Tailwind names in `frontend/tailwind.config.js`. Components should use the semantic Tailwind names or status variables, not introduce scattered literal colors.

| Token | RGB | Current use |
| --- | ---: | --- |
| `page` | `246 248 251` | Application background and focus-ring offset |
| `surface` | `255 255 255` | Cards, navigation, and controls |
| `elevated` | `250 251 253` | Secondary surfaces, hover states, and grouped content |
| `foreground` | `20 31 51` | Primary text and the dark Health Index surface |
| `secondary` | `64 78 101` | Body copy and secondary labels |
| `muted` | `100 116 139` | Captions, metadata, and supporting text |
| `border` | `217 224 234` | Default dividers and control borders |
| `primary` | `56 70 179` | Primary actions, active navigation, and emphasis |
| `primary-hover` | `42 53 151` | Primary-action hover state |
| `positive` | `34 122 88` | Completed, connected, or clearly favorable states |
| `info` | `37 99 168` | Neutral informational notices |
| `attention` | `168 91 12` | Review or incomplete states |
| `risk` | `180 67 39` | Elevated concern and open-notice states |
| `critical` | `176 38 55` | Urgent guidance, destructive action, and errors |
| `disabled` | `148 163 184` | Unavailable steps and controls |
| `focus` | `79 70 229` | Keyboard focus ring |

Each non-neutral status also has a pale background and border pair: `--status-positive-*`, `--status-info-*`, `--status-attention-*`, `--status-risk-*`, and `--status-critical-*`. These pairs are consumed by badges and notices so that status presentation includes foreground, background, and border treatment.

The current application sets `color-scheme: light`. The semantic indirection allows a future theme to replace values centrally, but dark mode is not currently implemented.

## Typography

The application uses one sans-serif stack: Inter when available, followed by system UI fonts. No web-font file is bundled, so the rendered face can fall back to the user's platform font.

The implemented hierarchy is:

- Health Index score: `text-7xl`, increasing to `text-8xl` from the small breakpoint, bold, tight tracking, and tabular numbers.
- Page title: `text-3xl`, increasing to `text-4xl` from the small breakpoint, bold.
- Major section title: generally `text-2xl` and semibold.
- Card title: generally `text-xl` and semibold.
- Metric value: `text-3xl`, bold, tight tracking, and tabular numbers.
- Body: `text-sm` or `text-base`, commonly with `leading-6` or `leading-7` for explanatory copy.
- Label: `text-sm` and semibold.
- Caption and metadata: `text-xs` using secondary or muted color.
- Eyebrow: `text-xs`, bold uppercase, with `0.14em` to `0.18em` tracking.

Use the `.metric-number` utility for scores and other values that need tabular alignment. Headings use slightly tightened letter spacing globally. Keep the number of font families at one unless a future brand decision explicitly changes it.

## Spacing, sizing, radius, and elevation

The UI follows Tailwind's 4px base spacing scale. Common patterns in the implementation are:

- Page gutters: 16px by default, 24px from 640px, 32px from 1024px, and 48px from 1280px.
- Page vertical padding: 24px by default, 32px from 640px, and 40px from 1024px.
- Section gaps: typically 24px to 32px.
- Card padding: 20px by default and 24px from 640px.
- Form and card-grid gaps: typically 12px, 16px, 20px, or 24px.
- Interactive controls: at least 44px (`min-h-11`) in the shared control and button patterns. Primary mobile navigation items use a 48px minimum height.
- Standard control and component radius: 12px (`rounded-xl`).
- Surface radius: 16px (`rounded-2xl`).
- Small nested radius: 8px (`rounded-lg`).
- Application content width: up to 90rem (1440px), with the desktop sidebar occupying 16rem.

The `surface` class supplies the default `card` shadow: a low-contrast one-pixel shadow plus a soft 30px ambient shadow. A stronger `raised` shadow is configured for exceptional elevated content, but the current shared card uses only `shadow-card`. Avoid adding extra elevation tiers without a specific layering need.

Safe-area padding is applied to the fixed mobile bottom navigation through `.safe-bottom`.

## Shared components

### Foundations

- `AppShell` provides the skip link, role-specific desktop and mobile navigation, user identity, sign-out control, content width, and responsive page gutters.
- `PageHeader` provides an optional eyebrow, the page `h1`, description, and trailing action.
- `Card` is the standard bordered surface and can render as a `section`, `article`, or `div`.
- `Button` supports primary, secondary, ghost, and danger variants plus loading and disabled states.
- `Badge` presents semantic status text using neutral, positive, informational, attention, risk, or critical tone.
- `StatusNotice` combines a semantic icon, title, explanatory content, and optional action.

### Forms and selection

- `Field` owns the visible label and optional/help/error copy, generates stable IDs, and supplies `aria-describedby` and invalid state to its control.
- `TextInput` and `SelectInput` share the 44px control pattern.
- `SearchField` includes a screen-reader label and native search input.
- `ChoiceCard` is used for fitness goals and exposes selection with `aria-pressed`, a check mark, text, border, and background.
- `Chip` is used for multi-select activities and also exposes `aria-pressed` state.
- `SegmentedControl` is used for short mutually exclusive choices such as waking refreshed and calorie approach.
- Onboarding `NumericField` composes `Field` and `TextInput`, displays a visible unit, and uses decimal input mode.

### Data and state

- `ProgressBar` clamps values to 0–100 and exposes progress-bar name, minimum, maximum, and current value.
- `LoadingState` combines a polite live status with decorative skeletons.
- `EmptyState` provides a title, explanatory copy, and optional action.
- `ErrorState` provides specific error copy and an optional retry action.
- `Disclosure` uses native `details` and `summary` for calculation and recommendation explanations.
- `HealthIndexSummary`, `ComponentBreakdown`, `ComponentRow`, `RecommendationsPanel`, `RecommendationCard`, `RiskPanel`, and `RiskAlertCard` form the explainable-score presentation.
- The coach roster has two deliberate renderings: a semantic desktop table and structured cards below the desktop breakpoint.

Prefer composing these components over recreating local card, status, field, or loading styles.

## Role navigation

### Coach

At 1024px and above, the coach sees a persistent 256px left sidebar with the product brand, an Overview destination, workspace context, user identity, and sign-out action. The current milestone has only one working coach navigation destination, so future modules are not shown.

Below 1024px, the sidebar becomes a sticky compact header. A fixed bottom navigation exposes the one working Overview destination. Trainee detail pages add a small `Trainee record` context label above the page content and an explicit link back to the overview.

### Trainee

At 1024px and above, the trainee uses the same shell structure with a role-specific sidebar containing Today, Progress, and Assessment.

Below 1024px, a compact header and three-item fixed bottom navigation expose Today, Progress, and Assessment. Main content receives additional bottom padding so it is not covered by the navigation. The navigation does not advertise plans, workouts, messages, or profile pages that are not implemented.

Active desktop and mobile links use primary color and a visible active treatment. Navigation containers have role-specific accessible labels.

## Responsive rules

The implementation supports viewports from 320px upward. Its active Tailwind breakpoints are 640px (`sm`), 1024px (`lg`), and 1280px (`xl`).

- Below 640px, page content and forms are a single prioritized stream. Button groups in onboarding stack vertically, with Back ordered after the primary actions visually through the column-reverse layout.
- From 640px, common form groups and summary blocks can use two columns, cards gain 24px padding, and onboarding actions return to a horizontal arrangement.
- Below 1024px, both role sidebars are replaced by the compact header and fixed bottom navigation. The coach roster renders structured cards instead of compressing a table.
- From 1024px, the persistent sidebar, coach roster table, onboarding step rail, and denser nutrition form layout become available.
- From 1280px, portfolio metrics can occupy four columns and Health Index sections use asymmetric two-column layouts.
- The app content is capped at 1440px. Health Index grids use `minmax(0, ...)` and components use wrapping/min-width controls to limit overflow from long values and labels.
- Authentication is a focused single column below 1024px and a split contextual/form layout from 1024px.
- The onboarding step rail is hidden below 1024px and replaced by named percentage progress. Completed steps in the desktop rail can be revisited; future steps remain disabled.

Do not introduce horizontal scrolling as a normal small-screen interaction. Preserve the table-to-card transformation for new coach roster fields.

## Accessibility practices

The current implementation includes the following practices:

- A keyboard-visible skip link targets the focusable main content region.
- All links, buttons, inputs, selects, text areas, and summaries receive a two-pixel `focus-visible` ring with an offset.
- Shared buttons and controls use approximately 44px minimum targets; mobile navigation uses 48px targets.
- Icons that duplicate visible text are hidden from assistive technology. Icon-only sign-out and password-visibility controls have accessible names.
- Navigation uses semantic `nav` elements and `NavLink` active-state behavior. The assessment rail marks the active item with `aria-current="step"`.
- Fields connect labels, help, and error messages with generated IDs, `aria-describedby`, and `aria-invalid`.
- Related choice inputs use `fieldset` and `legend`; custom choice cards and chips expose `aria-pressed`.
- Onboarding validates the current section before continuing, focuses the step heading after a step change, and focuses its alert summary when validation fails.
- Saving is described through a polite live region. Assessment loading is represented by a polite status. Submit and save controls expose busy/disabled behavior.
- Progress bars expose accessible labels and numeric progress values.
- The coach roster table includes a caption, column-header scopes, a screen-reader action header, and specific accessible names for row actions.
- Native `details`/`summary` provides keyboard-accessible disclosure without a custom dialog model.
- Status presentation combines text, iconography, border, and background; it does not depend on hue alone.
- A `prefers-reduced-motion: reduce` rule reduces animation, transition, and smooth-scroll duration globally.
- Print styles remove navigation and the page background.

When extending the product, retain visible focus, explicit control names, linked error copy, and non-color status cues. Do not add hover-only explanations or drag-only controls.

## Health Index and data-visualization conventions

The baseline remains a single immutable snapshot. Daily Intelligence adds restrained historical lines and compact coach progress rows only when persisted daily data exists.

- The overall Health Index is shown as a large numeric value out of 100, accompanied by an interpretation band, plain-language summary, calculation date, and source context.
- Component scores use horizontal progress bars plus an exact score, text status, configured weight, weighted contribution, and explanation.
- Calculation version, calculation date, and optional missing fields are placed in a disclosure so they remain available without dominating the default view.
- Recommendations are sorted with high priority first and limited to four in the main panel. Each can disclose why it was recommended.
- Risk notices remain visible near the score. On coach trainee-detail pages, important notices also appear before profile metrics and the full score view.
- Exact values remain in text. Color and bar length are supporting cues, not the only way to understand a score.
- Historical charts use real longitudinal data, include units and time range, and provide a readable empty state and table alternative. Missing dates create visible gaps and are never plotted as zero or connected across the gap. A single baseline is never presented as a trend.
- Daily readiness uses the existing positive, informational, attention, and risk semantics. Ordinary low scores are not styled as critical emergencies.
- Baseline Health Index and daily intelligence use separate headings and explanatory copy.

## Status and severity meanings

The application maps backend values to user-facing semantic tones.

### Risk severity

| Backend severity | Tone | User-facing prefix | Meaning |
| --- | --- | --- | --- |
| `urgent` | Critical | Immediate safety guidance | The interface presents immediate professional-safety guidance without making a diagnosis. |
| `elevated` | Risk | Elevated concern | A reported input deserves elevated attention. |
| `review` | Attention | Coach review suggested | The information should be reviewed with the coach. |
| Other/informational | Information | For your information | Context is useful but is not styled as urgent. |

Coach review queues sort these levels in the same order: urgent, elevated, review, informational.

### Component status

Known favorable statuses such as `excellent`, `optimal`, `complete`, `good`, `balanced_pattern`, and `meets_baseline` use the positive tone. Intermediate or review statuses such as `moderate`, `partial`, `limited_data`, and activity statuses from `somewhat_active` through `low_active` use attention. States including `high`, `very_high`, `needs_attention`, `outside_configured_range`, and `recovery_review` use risk. Unrecognized statuses remain neutral rather than being assigned an unsupported meaning.

Assessment status uses positive for submitted, attention for draft, and neutral for other states. Open notices use risk; a clear notice count uses positive.

## Approved microcopy

Use calm, specific language that states what happened, whether data remains available, and what the person can do next. Current approved examples include:

- “Your progress was saved.”
- “We could not save this step. Your entries remain on this page; try again.”
- “Check this section.”
- “Save and continue.”
- “Calculate my baseline.”
- “This baseline is visible to [coach], your assigned coach.”
- “No baseline yet.”
- “No onboarding review rules were triggered.”
- “Coach review suggested.”
- “Seek immediate professional medical help if chest pain or breathing difficulty is severe, worsening, or happening now.”
- “The Health Index is a deterministic coaching-support score. It is not a medical diagnosis and does not replace qualified medical care.”
- “No changes or trends are invented from a single baseline.”

Avoid diagnostic, shame-based, or absolute language such as “unhealthy,” “you failed,” “you are overtrained,” or “you have a medical condition.”

## Current-scope limits

- The application is light-mode only. Dark-mode values and a theme switch are not implemented.
- The product supports baseline onboarding plus manual daily check-ins and bounded longitudinal trends. Workouts, nutrition plans, wearables, messages, and notifications remain unimplemented.
- Coach navigation contains Overview; trainee navigation contains Today, Progress, and Assessment.
- Submitted assessments are locked. Starting a new assessment version is explicitly deferred.
- Data visualization includes numeric summaries, status badges, exact contribution text, progress bars, restrained trend lines, and accessible data tables.
- The shared system does not currently include a modal, drawer, toast, or confirmation-dialog component because current flows do not require them.
- Inter is requested through the font stack but is not bundled by the frontend.
- The CSS establishes a minimum document width of 320px; narrower viewports are outside the implemented target.
- The authentication screen displays local demo credentials. That content is appropriate to the current demo environment and should be removed or gated before a production deployment.

## Source locations

- Tokens and global behavior: `frontend/src/index.css`
- Tailwind semantic mapping: `frontend/tailwind.config.js`
- Shared primitives: `frontend/src/components/ui.tsx`
- Role-aware shell and navigation: `frontend/src/components/AppShell.tsx`
- Health Index presentation: `frontend/src/components/HealthIndex.tsx`
- Authentication patterns: `frontend/src/pages/AuthPages.tsx`
- Assessment patterns: `frontend/src/pages/OnboardingPage.tsx`
- Coach and trainee dashboards: `frontend/src/pages/DashboardPages.tsx`
- Daily trainee experience: `frontend/src/pages/DailyPages.tsx`
- Daily coach experience: `frontend/src/components/DailyCoach.tsx`
