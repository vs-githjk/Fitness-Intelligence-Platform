# Design Specification — Trainee "Today"

- **Surface:** `TodayPage` at `/trainee/today` (aliased `/trainee/dashboard`).
- **Stream:** B — Product Experience. **Sprint:** 1.
- **Status:** Product-complete and **frozen**. Handed to design (Fable) for visual
  exploration; engineering implementation follows behind the four-review PX gate.
- **Change control:** product decisions here change only through an approved
  Decision Record ([../decisions/README.md](../decisions/README.md)); guardrails
  change only by revisiting [../product-principles.md](../product-principles.md).
  See [Rationale & change control](#rationale--change-control).
- **Governs / governed by:** applies the experience principles in
  [../product-principles.md](../product-principles.md) (Guidance over Metrics, One
  Dominant Answer, Coach First, Calm Intelligence, Premium Simplicity) to one
  screen. This document is the first entry in `docs/design/`, which holds the
  per-screen design specifications produced by Stream B.

> **How to read this document.** *Part I* fixes the experience intent (the feeling
> and the boundaries). *Part II* is the product specification: every product
> decision, made, so a designer explores presentation without making product
> choices. *Part III* defines acceptance, long-term evolution, and what may versus
> may never change. Fable varies only the presentation layer; everything in Parts I
> and II is a product decision.

---

# Part I — Experience intent

This part exists so a designer knows, before touching layout, what emotional
experience Today must create and what it must never become.

## Emotional goals

When a trainee opens Today, the intended felt experience is:

- **A small exhale.** "Okay — I know what today is." Relief and orientation, not
  scrutiny or homework.
- **Seen, not measured.** It should feel like a coach who knows them speaking, not a
  report card grading them.
- **Capable.** The day is framed around what they *can* do; it feels doable.
- **Trusting.** The guidance is confident and consistent, so they believe it and
  act on it.
- **On a hard day: reassured, not alarmed** — met with care and a clear, lighter
  plan. **On a good day: quietly encouraged** to go for it.

The daily emotional arc is always: *open → orient in one glance → feel guided →
act.* No anxiety spike, no decision fatigue.

## What it should feel like — and never feel like

**Should feel:** calm · athletic · intentional · trustworthy · premium · restrained
· human · coach-led · confident · effortless · glanceable.

**Must never feel:** clinical · alarming · busy · gamified · needy · judgmental ·
generic · robotic · cluttered · attention-seeking.

**Reference feeling:** a great coach's one-line morning text — warm, brief, certain.
**Anti-reference:** a medical dashboard, or a tracker's wall of notifications.

## Delight philosophy

Delight on Today is **quiet, earned, and truthful** — it comes from the right thing
being said at the right moment, never from decoration.

- **Earned** — acknowledge genuine accomplishment (a real streak, a completed
  session), never mere participation.
- **Truthful** — every encouraging or celebratory line reflects real data; never
  fabricated, never inflated.
- **Never manipulative** — no artificial urgency, no streak-anxiety ("don't lose
  your streak!"), no mechanics engineered to pull the user back.
- **Never gamified** — no points, badges, leaderboards, or confetti for its own
  sake.
- **Never guilt-based** — a missed day or a low readiness is met with matter-of-fact
  guidance and a path forward, never shame.

The highest form of delight here is the trainee thinking: *"this understands me and
makes my day easier."*

## Anti-goals — what Today must never become

Today must never become any of the following, regardless of how well-intentioned a
future proposal is:

- a **dashboard** — a grid of metrics to read and interpret;
- an **analytics page** — charts, trends, and historical exploration (those live in
  Progress);
- a **warning center / alert wall** — a stack of things wrong with the user;
- a **widget collection** — modular tiles competing with no dominant answer;
- a **medical report** — clinical language, diagnoses, or anything implying medical
  assessment;
- a **feed** — an endless scroll of cards or content;
- a **notification surface** — a place that nags, badges, or manufactures
  re-engagement;
- a **settings/config surface** — controls and toggles belong elsewhere.

If a future proposal makes Today resemble any of these, it is wrong by definition —
reject it or relocate it, even if the idea has merit on its own.

---

# Part II — Product specification

## 1. Product goals
1. Make **guidance the product**: on open, the trainee knows *what to do*, not *what
   their numbers are*.
2. Make the day's work **one tap away** from Today (it currently lives on a separate
   screen).
3. Make the experience feel like **guidance from the trainee's coach**, supported by
   explainable intelligence — never an algorithm's verdict.
4. **Reduce anxiety**: eliminate the alert wall; lead with confidence and what's
   going well.
5. Preserve every guardrail: determinism, explainability, Health Index / Daily
   Intelligence integrity, authorization, non-medical positioning.

## 2. User goals
The trainee (6am before work, or 10pm before bed) wants to answer, in seconds:
**What should I do today? · Why? · How hard should I train? · What's going well? ·
What should I be careful about?** Nothing on the screen may compete with those five
answers.

## 3. Screen objective
**One dominant answer:** *"Here is your plan for today, from your coach."* Every
other element exists to support, explain, or act on that plan. If an exploration
makes any secondary element rival the plan for attention, it violates this spec.

## 4. Information hierarchy (fixed — may not be reordered)
```
1  THE PLAN  (the single hero — greeting, verdict, why, workout, coach, primary action)
2  GOING WELL          — at most one line   (omit if nothing genuinely positive)
3  KEEP AN EYE ON      — at most one line   (omit if nothing to watch; "N more" collapses the rest)
4  ▸ TODAY'S DETAILS   — one disclosure, collapsed by default
```
Ranking is a product decision and is fixed. Screen-reader and DOM order match this
order. Fable controls *how* each level looks and how strongly it is weighted — not
*which* level dominates (level 1 always wins) nor the sequence.

## 5. Layout structure
- **Single vertical column, one reading path**, top to bottom. No multi-column
  competition among the five answers.
- **Above the fold on mobile:** the plan (level 1) and its primary action are
  reachable without hunting; levels 2–4 may fall below.
- **The plan is one contiguous unit** — greeting, verdict, reason, workout, coach
  attribution, and the primary action read as a single message. Whether that unit is
  one surface or subtly sectioned is Fable's to explore; that it reads as *one
  message* is fixed.
- Levels 2–3 are **text with a leading indicator, not containers.** Whitespace
  separates them.

## 6. Navigation
- **The day's workout launches from Today.** "Start workout" deep-links to the
  existing execution route `/trainee/workouts/:scheduledWorkoutId`. No new execution
  UI.
- **Editing the check-in is a quiet affordance** (a text link, e.g. "Edit today's
  check-in"), never a celebratory bar.
- Global nav (Today / Progress / Program) is **unchanged this sprint.** Program
  remains the full schedule; Today shows only *today's* session. (Later-sprint note,
  not now: reconsider whether Program needs equal nav weight once Today carries the
  workout.)
- Coach **contact details** (email) move off Today into profile; the coach's
  *presence* stays on Today (see §19).

## 7. Visual hierarchy (principles, not styles)
Fixed product intents; Fable chooses the visual means:
- The plan is the **single most prominent element.**
- **"Start workout" (or, when not checked in, "Check in") is the single
  highest-emphasis control** on the screen. No other button competes.
- The **readiness verdict is expressed as words first**; any number is subordinate
  evidence, never the focal point.
- Concern (level 3) is **calmer than** the plan and never louder than "Going well."
  One caution indicator maximum; no full-width warning wash.
- Color may **support** meaning but **never carries it alone** (the band word is
  always present).

## 8. Copy (final — may be set typographically, may not be rewritten)
Voice: a calm, competent coach texting you. Never clinical, never "software."

**Greeting (top of plan):** `Good morning, {first_name}` / `Good evening,
{first_name}` (time-of-day by local clock).

**Verdict headline — keyed to `readiness_state` (the one product-owned mapping):**

| `readiness_state` | Verdict headline |
| --- | --- |
| `ready_to_push` | **"Go for it today."** |
| `maintain` | **"Train as planned today."** |
| `reduce_intensity` | **"Ease off a little today."** |
| `recovery_recommended` | **"Let's keep it light today."** |

**How hard (from `target_session_rpe`):** "aim for a {n} out of 10 effort" — never
"RPE", never a raw field name.

**Workout line:** `{workout name} · {program_week_label}`, then `About
{planned_duration_minutes} minutes · aim for a {target_session_rpe} out of 10
effort`. Omit any null field rather than showing a placeholder.

**Coach note (verbatim, when `trainee_instructions` present):** shown in quotes,
attributed `— {coach_name}, your coach`.

**Rest day (no workout today):** headline **"Take today off — on purpose."** body
**"You've earned it. Rest is when the work pays off."** plus **"Next up: {next
workout name}, {relative day}."** Action **"Log how you feel →"**.

**Going well (level 2, one line, only if true):** e.g. *"You've checked in {n} days
running."* / *"Sleep is trending up this week."* Rendered only when the underlying
data supports it.

**Keep an eye on (level 3, one line):** the single highest-severity concern in coach
language, e.g. *"Soreness is a little high — ease into your warm-up."* Collapsed
remainder labeled **"{n} more notes."**

**Disclaimer (say once, quietly, inside Today's details):** *"This is coaching
guidance from your check-in, not medical advice."* It appears nowhere else.

**Removed vocabulary (must not appear in UI):** "readiness score/state" as a raw
label, "risk flags", "review signals", "recommended next actions", "arbitrary
units", "compliance", "reflection", "insufficient configured targets", any
`snake_case` or machine-cased label.

## 9. Empty states
- **Not checked in yet (primary empty state):** the whole screen collapses to one
  warm invitation — greeting + **"Let's plan your day."** + *"Two minutes on how you
  slept and moved, and I'll tell you exactly how to train today."* + one primary
  action **"Start check-in →"**. No metrics, no coach card, no empty scaffolding.
  (Backend: `/daily-scores/today` and `/check-ins/today` both 404.)
- **No coach assigned / inactive:** the plan still renders from Daily Intelligence;
  coach attribution simply omits (no broken "your coach" element). The workout
  section shows only if an assignment exists.
- **No workout scheduled today but checked in:** the rest-day plan (§8), not an empty
  slot.
- **No positives to show:** the "Going well" line is absent — never a hollow
  placeholder.

## 10. Loading states
- One **calm, full-screen loading state** with a human label (e.g. "Getting today
  ready…") while the plan's data resolves.
- **Do not show a partial skeleton of the old metric grid** — the previous
  structure must not flash. A skeleton, if explored, reflects the *new* hierarchy (a
  plan-shaped placeholder), never a grid of numbers.
- Never show `0` or a spinner *inside* a score position while loading (missing ≠
  zero — a guardrail).

## 11. Error states
- If the plan's core data fails (a non-404 error), show one **calm, recoverable
  error** with a plain-language message and a **Retry** action. No stack of red
  banners.
- Partial failures degrade gracefully: if the coach lookup or trends fail but the
  plan resolves, render the plan and silently omit the missing support rather than
  blocking the screen.

## 12. Mobile behavior (primary form factor)
- Single column; the **plan and its primary action are the priority above the
  fold.** Levels 2–4 stack below in reading order.
- **No horizontal page scrolling.** Any wide element (e.g. a detail table inside the
  disclosure) scrolls within its own container.
- Tap targets ≥ 44px; the primary action is thumb-reachable.

## 13. Desktop behavior
- The same single reading path, centered in a comfortable measure — **do not spread
  the five answers into columns** to fill width. Width is absorbed by whitespace, not
  by manufacturing parallel sections.
- The plan may occupy a larger, calmer canvas; secondary levels remain visibly
  subordinate.

## 14. Accessibility considerations (requirements)
- **Semantic structure:** one top-level intent (the plan/verdict); levels 2–4 are
  properly nested headings; DOM order = the five-answer order.
- **The verdict and every score have a text equivalent** — never conveyed by color
  or shape alone. Any ring/gauge must expose value and band as text to assistive
  tech.
- **Color contrast** meets WCAG AA in every visual direction, for the verdict states
  and the caution indicator.
- **Visible focus states** on the primary action, the edit affordance, the
  disclosure toggle, and the "N more notes" control.
- **`prefers-reduced-motion` honored** — all celebration/animation degrade to
  instant, legible states.
- **The primary action is a real, labeled, keyboard-first control.**

## 15. Animation philosophy
- Motion clarifies state change (check-in saved, workout completed) — never
  decorative density.
- **Celebration is subtle** (§18): a brief, tasteful acknowledgment, never
  confetti-spam.
- Everything respects reduced-motion and never blocks reading the plan.
- Default to *less* motion; added animation must justify itself against "does this
  reduce friction or just add flourish?"

## 16. Interaction philosophy
- **One primary action per state** (Start workout / Check in / Log how you feel).
- **Progressive disclosure** for all evidence (§17). The calm surface is default;
  depth is opt-in.
- Today is a **read-and-launch** surface, not a data-entry surface — no heavy forms,
  no destructive actions here.
- Editing today's check-in is possible but visually quiet.

## 17. Progressive disclosure
- **Exactly one disclosure** on the checked-in screen: **"Today's details"**,
  collapsed by default, containing (a) the four scores as integers, (b) the
  per-component breakdown with explanations, and (c) the single disclaimer.
- The "Keep an eye on" line reveals additional concerns via **"{n} more notes"** —
  collapsed by default.
- Nothing that answers the five primary questions is ever hidden behind disclosure;
  only *evidence* is.

## 18. Motivation strategy (deterministic, never fabricated)
- Motivation = **truthful reflection of real data**, surfaced from existing
  endpoints: check-in streak, workout-completion streak, an improving trend
  direction, genuinely strong component statuses.
- Framing is **capability, not risk** ("Go for it today", "You've earned it").
- If nothing true is positive today, motivation is simply absent — no manufactured
  cheer.
- The **workout as forward momentum** is itself the core motivator: naming today's
  session and making Start the biggest action frames the day around *doing*.

## 19. Coach presence
Coach presence is **felt as authorship of the plan**, and it is honest because the
coach genuinely authored the substance:
- The plan is framed as **coming from the coach** — their name and face anchor it
  (`coach_name`, `coach_avatar_url`).
- When the coach wrote a workout note (`trainee_instructions`), it appears
  **verbatim, in quotes, attributed** — real coach voice, zero fabrication.
- The **workout is the coach's prescription** (they assigned the program, set the
  effort target, chose the week) — naming it is the coach speaking through structure.
- **No invented coach quotes. No AI voice.** With no coach note, the deterministic
  reason line stands on its own in warm language, and the coach's face still anchors
  the plan as *"your plan with {coach}."*
- Coach *contact* (email) is not on Today — presence ≠ a contact card.

## 20. Existing backend data mapping (no new endpoints)

| Element | Source (existing) |
| --- | --- |
| Greeting | `user.first_name` + local clock |
| Verdict headline | `DailyScoreOut.readiness_state` → §8 map |
| How hard | `readiness_state` + `ScheduledWorkoutOut.target_session_rpe` |
| Reason ("why") | `readiness_state` + trend direction from `/daily-scores/trends` |
| Workout name / week / duration | `GET /trainee/program` → `scheduled_workouts[]` where `scheduled_date == local_today`; `workout_template_version.name`, `program_week_label`, `planned_duration_minutes`, `target_session_rpe` |
| Coach's real note | `scheduled_workout.trainee_instructions` |
| Coach face / name | `GET /trainee/coach` (`coach_name`, `coach_avatar_url`) |
| Start / completed / rest state | `/trainee/workouts/:id`; `scheduled_workout.status`; absence of a today entry ⇒ rest |
| "Next up" (rest day) | next future entry in `scheduled_workouts[]` |
| Going well | strong `components[]` statuses + streaks from `/daily-scores` history and `scheduled_workouts` |
| Keep an eye on | highest-`severity` item of `DailyScoreOut.risk_flags[]`; remainder collapsed |
| Today's details — scores | `recovery_score`, `readiness_score`, `activity_score`, `nutrition_score` (nullable → "Add nutrition targets to track this") |
| Today's details — breakdown | `components[]` (`normalized_score`, `weight`, `explanation`) |
| Disclaimer | static string (§8) |
| Not-checked-in state | `/daily-scores/today` + `/check-ins/today` both 404 |

## 21. Existing backend logic reused
- **Daily Intelligence v1** (`daily-intelligence-v1`) — recovery/activity/nutrition/
  readiness scoring, the four `readiness_state` bands (≥80 / ≥60 / ≥40 / <40),
  `risk_flags`, `recommendations`, `components`. Consumed as-is.
- **Workout scheduling / assignment** — `scheduled_workouts` and their
  coach-authored fields. Consumed as-is.
- **Health Index v1** — baseline reference (may appear inside Today's details or move
  off-screen; product-optional, §23). Never recomputed.
- Existing execution route and authorization. Unchanged.

## 22. No new backend logic introduced
- Presentation-only: **no new scoring, thresholds, endpoints, or persisted fields.**
- The verdict/intensity mapping is a **display mapping over the engine's existing
  `readiness_state`** — the client must **not** recompute or re-threshold scores.
- Streaks and trend direction are **read-only derivations over existing endpoint
  data** for display; deterministic, adding no backend logic.
- Positive/negative surfacing selects from data the engine already returns; it never
  invents a signal.

## 23. Open implementation questions (for engineering, not Fable)
1. **Reason-line composition:** compute the one-sentence "why" client-side from
   `readiness_state` + top component/trend now, or add a thin read-only
   `/daily-scores/today/summary` later to keep phrasing authoritative server-side?
   (Leaning: client-side for v1, consolidate later.)
2. **Streak source:** derive from `/daily-scores` history + `scheduled_workouts`
   client-side, or precompute later?
3. **Baseline (Health Index):** keep inside "Today's details", or remove from Today
   entirely and let Progress own it? (Default = inside details, low prominence.)
4. **Completed-workout state:** copy/treatment when the day's workout is already done
   (a loop-closing "done" state on Today).

None of these block Fable.

## 24. Explicit constraints for Fable
**Fable explores freely:** overall visual direction (including a possible dark
treatment for a dawn/dusk product), whether the plan is one surface or subtly
sectioned, the verdict's visual form (typographic, ring, gauge — provided the band
word stays primary), how coach presence is rendered, spacing/type/color systems, the
celebration moment, and loading/skeleton treatment.

**Fable must NOT change:** business logic; information architecture or the fixed
hierarchy/order (§4); deterministic calculations, the `readiness_state` bands, or any
score value (display as integers; never recompute); authorization, Health Index, or
Daily Intelligence logic; coach-first philosophy or non-medical positioning
(disclaimer exactly once); explainability (the breakdown stays reachable); the final
copy (§8, may set typographically, not rewrite); the rule that **guidance leads and
metrics support**; the rule that **one action dominates** and **no more than one
caution indicator** shows at the surface.

**Deliverables requested of Fable:** light and dark comps, mobile-first + desktop,
for all four states — (a) not checked in, (b) workout day, (c) rest day, (d) workout
completed — plus loading and error treatments, and token proposals (reconcile the
three existing blues to one; propose a green and a single amber; a dark palette).

---

# Part III — Acceptance & evolution

## Experience success criteria (product acceptance)

A build of Today is not acceptable unless, with real data, a representative trainee:

1. States today's recommendation within about **five seconds** of opening.
2. Knows exactly what to do (start workout / rest / check in) **without scrolling**
   on mobile.
3. **Recognizes the guidance is from their coach** without being told.
4. Can answer **all five questions** (what / why / how hard / going well / watch)
   after a brief look.
5. Points to the **guidance — not a number** — as the most prominent thing.
6. Reports feeling **"clear" or "calm,"** not "overwhelmed" or "judged."
7. Reaches the day's workout in **one tap.**
8. Finds any supporting number within **one interaction** (the single disclosure) —
   evidence available, not absent.

These are acceptance criteria for the Product Experience review gate, validated by
observation and usability testing — not analytics dashboards.

## Long-term vision — how Today evolves

Today is FitIntel 360's **primary guidance surface**, and it remains so as the
platform grows. Future capability milestones (Stream A) feed **into** Today; they do
not spawn competing surfaces:

- **Nutrition Intelligence (M5)** deepens the "why" and may add a nutrition dimension
  to the day's guidance — inside the one plan, not a second card war.
- **Wearables (M6)** enrich the inputs behind readiness (sleep, HRV, and the like),
  improving the *accuracy* of the same verdict, largely invisibly. Today shows better
  guidance, not more gauges.
- **Adaptive Coaching (M7)** lets the coach's intent adjust deterministically — the
  plan becomes more responsive, still framed as the coach's.
- **AI Coach (M8)** may compose the narrative and explanation more fluently — always
  deterministic, explainable, non-fabricated, and in the coach's service, never
  replacing the coach.

The invariant across all of them: **every new capability must make the single daily
plan clearer or more accurate — never turn Today back into a dashboard.** New data
strengthens the answer; it does not add competing answers. A capability that seems to
"need its own space on Today" should first be asked whether it can instead improve
the existing plan.

## Rationale & change control

This section exists so that someone inheriting the product in two–five years
understands not only *what* was decided but *why*, and knows what they may safely
change.

**Why guidance-first.** Users open a coaching product to know what to do; the prior
metric-led Today created anxiety and buried the day's actual workout on another
screen. (Product Principles: Guidance over Metrics, One Dominant Answer.)

**Why coach-led framing.** FitIntel amplifies a human coach; guidance that reads as
algorithmic erodes the product's core value and trust. (Coach First.)

**Why the alert wall was removed.** Alert fatigue trained users to ignore the screen;
calm, ranked, actionable concerns get read. (Calm Intelligence.)

**Why one disclosure and heavy removal.** Premium products remove more than they add;
evidence must remain available but subordinate. (Premium Simplicity.)

**Fixed — product decisions (change only via an approved Decision Record):**
- The five questions and their order (§4).
- Guidance dominates; one dominant answer; one primary action.
- Coach-led framing; deterministic, non-fabricated content; non-medical positioning.
- The final UI copy (§8) and the `readiness_state` → verdict mapping.
- The data mapping (§20) and the "no new backend logic" boundary (§22).

**Flexible — Fable and engineering vary freely:**
- Visual language, color, type, spacing, light/dark.
- Whether the plan is one surface or subtly sectioned; the verdict's visual form.
- Motion and the celebration treatment.
- Loading / skeleton presentation.

**Must never change — guardrails (cannot be waived by a Decision Record alone; they
trace to [../product-principles.md](../product-principles.md)):**
- Determinism, explainability, and immutability of history.
- Authorization and identity scoping.
- Non-medical positioning.
- Missing data is never shown as zero or fabricated.
- The [anti-goals](#anti-goals--what-today-must-never-become): Today never becomes a
  dashboard, analytics page, warning center, or medical report.

**Change process.** Propose changes to *Fixed* items through `docs/decisions` (a
Decision Record referencing this spec). *Must-never-change* items require revisiting
`docs/product-principles.md` itself. *Flexible* items need no record — that is the
space this specification deliberately hands to design.
