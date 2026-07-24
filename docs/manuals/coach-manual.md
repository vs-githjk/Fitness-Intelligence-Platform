# FitIntel 360 — Coach manual

Welcome to FitIntel 360. This is your practical guide to running the app as a coach:
inviting trainees, reading their readiness and adherence, building training, and
assigning it. It reflects what the app does **today**. It is written for coaches, not
engineers — you never need to see code or use technical tools.

> **Coaching support, not medical care.** FitIntel 360 helps you make coaching
> decisions. It does **not** diagnose conditions, provide medical clearance, or
> replace a doctor, dietitian, physiotherapist, or other qualified professional. If a
> trainee reports pain, chest discomfort, breathing difficulty, dizziness, or any
> serious or worsening symptom, direct them to appropriate professional care
> regardless of anything the app shows.

This manual consolidates the coach-facing material for the platform. For deeper
reference on a single topic, the linked topic pages under `docs/` go further.

---

## 1. What FitIntel 360 does

FitIntel 360 connects a **coach** with their **trainees**.

- **Trainees** complete a one-time onboarding assessment, then check in daily
  (sleep, recovery, activity, nutrition, and how they feel). They see the training
  you assign, run each workout, and log what they actually did.
- **You, the coach**, see each trainee's baseline **Health Index**, their daily
  **readiness** trend, whether they are keeping up (**adherence**), and any
  **safety reports** they raise during a workout. You build **exercises**,
  **workout templates**, and **programs**, and assign a published program to a
  trainee so scheduled workouts appear on their calendar.

Everything is **explainable and deterministic**: scores come from the trainee's own
inputs using published rules, never from a hidden or predictive model. When data is
missing, the app says so — it never invents a number.

---

## 2. Signing in

1. Open the FitIntel 360 web address you were given and choose **Sign in**.
2. Enter your coach email and password. Use **Show password** if you need to check it.

**Trying the demo first?** From the sign-in screen you can choose **Explore Demo →
View as Coach**. The demo is a synthetic, read-only roster — a safe place to look
around. A banner marks it as demo, and any attempt to change data is blocked. Demo is
separate from your real coach account; your real login still uses your own email and
password.

**If sign-in fails:**

- Re-check the email and password (passwords are case-sensitive).
- Make sure you are using the exact web address you were given.
- If you were just invited as a coach, confirm your account was created (you register
  with a private coach code — see §4).
- If it still fails, report it (see §20). Never share your password in a message or
  screenshot.

---

## 3. Coach dashboard (Overview)

**Overview** is your home base. It summarizes your roster so you can see where to
spend attention:

- **Trainees** — everyone assigned to you.
- **Alerts** — trainees who may need a look (for example, a sharp readiness drop, a
  run of missed check-ins, or a submitted safety report). Alerts are prompts to
  review, **not diagnoses**.
- **Readiness** — a daily, trainee-reported signal combining recovery, activity, and
  related inputs. Use it to spot trends, not to make medical judgments.
- **Adherence** — how much of the assigned training a trainee is actually completing.
- **Recent activity** — the latest check-ins and completed workouts.
- **Missing check-ins / stale data** — where a trainee hasn't reported recently, so a
  low or absent score reflects *missing input*, not a problem you can act on blindly.

Open any trainee to see their detail view and history. Treat everything here as
context for a coaching conversation.

---

## 4. Managing trainees

You add trainees by **invitation** — the app never emails on your behalf, so you send
the invite through your own trusted channel.

1. Open **Invitations**.
2. Optionally restrict the invite to a specific trainee email (this limits who can
   redeem it; it does **not** send an email).
3. Choose an expiry (1, 3, 7, 14, or 30 days) and create the invitation.
4. Immediately use **Copy invitation link** or **Copy invitation code** — the raw
   value is shown once and cannot be recovered after you refresh. Share it privately.
5. Each invitation is **single-use** and expires. Once the trainee registers with it,
   they appear on your **Overview** roster.

You can see active, used, expired, and revoked invitations in the history, and revoke
any still-active invitation. Open a trainee from Overview to reach their details,
readiness, and history.

---

## 5. Assessments and the Health Index

When a trainee onboards, they complete a structured **assessment** (measurements,
habits, sleep, activity, nutrition, and related questions). From it the app computes a
baseline **Health Index**.

- The Health Index is an **explainable baseline snapshot** built from the trainee's
  own answers, with visible component scores.
- Use it to understand a starting point and to frame goals — **not** as a medical
  assessment, a diagnosis, or clearance to train.
- It does not update itself daily; day-to-day signal comes from check-ins (§6).

Never treat the Health Index as a verdict on someone's health. It is a conversation
starter grounded in what the trainee told you.

---

## 6. Daily check-ins and readiness

Each day a trainee can submit a **check-in**: sleep, recovery, activity, nutrition
compliance, stress, and how they feel. From these the app derives daily **readiness**
and related sub-scores.

- Readiness is a **high-level, deterministic** summary of the day's inputs. It helps
  you notice trends ("readiness has been sliding all week").
- **Missing or stale data** is shown as missing — the app will not fill a gap with a
  guess or a zero. A blank is "no check-in", not "bad day".
- **The app never changes a workout automatically.** It does not auto-progress,
  auto-deload, or reschedule based on readiness. Any change to training is **your**
  coaching decision.

Interpret trends over days, not single points, and combine them with what you know
about the trainee.

---

## 7. Programming overview — the required chain

Assigning training in FitIntel 360 follows a fixed, layered chain. **Every layer must
be published before the next can use it**, and you assign a *whole program*, never a
loose exercise:

```
Exercise  →  Workout Template  →  Program  →  Assignment  →  Trainee's scheduled workouts
```

A plain-language example:

- **Exercise:** *Goblet Squat* — a single movement, with instructions and how it's
  tracked.
- **Workout Template:** *Lower Body Day* — a reusable session that includes published
  exercises like the Goblet Squat, with sets and targets.
- **Program:** *Four-Week Beginner Strength Plan* — a multi-week plan that places
  published templates on specific days.
- **Assignment:** give that **published** program to a specific trainee, starting on a
  date you choose.

Once assigned, the trainee sees their scheduled workouts on their calendar.

> **The single most common confusion:** creating just an *Exercise* is **not** enough
> to assign anything. Until you have a **published Program** (which needs a published
> Template, which needs published Exercises), the assignment screen has nothing to
> offer. See §11, §12, and §16.

---

## 8. Exercises

Exercises are the building blocks.

1. In **Programming → Exercises**, create an exercise.
2. Give it a name, safe instructions, and a **tracking mode** (for example
   repetitions and load, repetitions only, duration, or distance and duration).
3. It starts as a **draft**. Review it, then **publish** it.
4. Only a **published** exercise can be added to a published template.

Keep instructions clear and safety-minded; trainees rely on them during a workout. A
draft exercise is a work in progress and won't be usable downstream until published.

### Exercise knowledge

Beyond the basics, an exercise can hold richer coaching knowledge so it becomes a
reference, not just a name:

- **Difficulty** — Beginner, Intermediate, or Advanced. This is an instructional
  label to guide selection; it is **not** a medical or fitness rating.
- **Coaching cues** — short prompts you'd give while someone performs the movement.
- **Common mistakes** — frequent errors to watch for.
- **Safety cues** — reminders to keep the movement safe.

Keep all of this instructional and general. Do not enter medical claims or promises.

### Exercise media (images and video)

On an editable **draft**, the **Media** section lets you add:

- a **primary image** (the main still),
- an optional **secondary image** (a second angle), and
- one optional **demonstration video**.

Images accept JPEG, PNG, WEBP, or GIF up to 5 MB; video accepts MP4 or WEBM up to
25 MB. Choose a file to see a preview, then **Upload**. Use **Replace** to swap a
file or **Remove** to take it down. The read-only **Preview** panel shows how the
exercise looks with its media and knowledge, with clear "No image yet" / "No video
yet" placeholders when empty.

Media is part of the **published version**: once you publish, its images and video
are frozen with that version. To change media later, create a **revision** (which
copies the current media), edit the draft, and publish again — earlier published
versions and any workouts already built from them are never altered.

**System exercise limitations.** Starter Library and other system exercises are
read-only: you can view their knowledge and demonstration media, but you cannot edit
them or change their media. To customize one, clone it (or build your own private
exercise) and add your own media there.

### Best practices

- Use a clear image that shows the key position; add a short video for movements that
  are hard to describe in words.
- Write two or three focused coaching cues rather than a long paragraph.
- List the mistakes you actually correct most often.
- Publish only when the knowledge and media are ready — remember they freeze into the
  version.

---

## 9. Workout Templates

A template is a **reusable single session** — not a whole plan.

1. In **Programming → Templates**, create a template.
2. Add **published** exercises to its sections (for example warm-up, main, cool-down).
3. Set sets, repetitions, load or duration targets, and rest as appropriate for each
   exercise's tracking mode.
4. Save as a **draft**, then **publish** when it's ready.
5. Only a **published** template can be placed into a published program.

Think of a template as "one day's workout" that you can reuse across programs and
weeks.

---

## 10. Programs

A program is a **multi-week plan** made of templates.

1. In **Programming → Programs**, create a program and set its length in weeks.
2. Add **published** templates to specific weekdays within each week.
3. Save as a **draft**, then **publish**.
4. A **published program version is immutable** — it is a fixed, dependable snapshot,
   which is what lets assignments stay stable for the trainee.
5. To change a published program later, create a **new revision (draft)**, edit it,
   and publish it as a new version. Existing assignments keep their original version
   until you assign the new one.

Only published program versions can be assigned (§11).

---

## 11. Assignments

This is where a program reaches a trainee.

1. Open **Assignments**.
2. Choose the **trainee**.
3. Choose a **published Program version** from the selector.
4. Choose the **effective start date** (week 1 begins on the first Monday on or after
   the trainee's local date).
5. Use **Preview schedule** to see the exact dated workouts that will be created.
6. **Review** and **confirm**. If the trainee already has a plan, only *future*
   workouts are replaced; past history is preserved.

After you confirm, the trainee sees their scheduled workouts on their **Program**
calendar.

**Why the "Published Program version" selector can look empty.** It only lists
**published** programs. If you've only created an exercise — or your template or
program is still a draft — there is nothing to assign yet, and the app now shows a
short explanation with a link straight to **Programming → Programs**. Creating an
Exercise alone never fills this selector; you must build and **publish** the full
chain in §7. See §16 for the step-by-step fix.

Business rules that never change: you can only assign a **published Program version**
(never a lone exercise or template); publishing rules, version eligibility, schedule
preview, effective-date handling, and active-program replacement all work exactly as
before — the empty-state text is only a clearer explanation, not a rule change.

---

## 12. Starter Library — the fastest way to start

Building your first program from scratch takes time. The **Starter Library** gives you
ready-made starter programs you can copy and make your own.

**What it is.** A small, curated set of general starter programs (with their workout
templates and exercises), open to every coach. It is **read-only**: you cannot edit,
delete, or assign the starter content directly, and it is not a marketplace or a shared
library of other coaches' work. Think of it as a set of well-organized examples you can
copy.

**How to browse.** Open **Programming → Starter Library**. Each card shows the program's
level, length in weeks, sessions per week, and a short equipment summary. Choose **View
details** to preview the full weekly layout, the workout for each day, and the exercises
inside — all read-only.

**How to use one.** On a starter program, choose **Use this program**. This creates
**your own editable draft copy** in **Programming → Programs**. Two things to know:

- The copy is **yours** — you can rename it, change weeks, swap exercises, and adjust
  sets and targets, exactly like a program you built yourself.
- The copy is **independent**. Changing your copy never changes the original starter
  program, and if the starter library is updated later, **your copy is not changed**.

**Then follow the normal steps.** A copied program starts as a **draft**. It is not
published and not assigned automatically. To use it with a trainee:

1. Review and edit the draft as needed.
2. **Publish** it (this creates a fixed, dependable version).
3. **Assign** the published program to a trainee (see §11).

A program copied from the Starter Library shows a small **"Based on Starter Library"**
label so you can tell where it came from.

**Quick workflow.**

```
Starter Library  →  Use this program  →  Review / edit draft  →  Publish  →  Assign to trainee
```

You never have to use the Starter Library — you can still build everything from scratch
in Programming. It is simply a faster starting point.

---

## 13. Workout completion and coach review

When a trainee runs a workout, each session ends in one of these states:

- **Completed** — the session was finished.
- **Partial** — started and ended without completing everything.
- **Skipped** — the trainee chose to skip a scheduled workout before starting. A skip
  can be an ordinary skip or a **wellbeing/safety** skip.
- **Missed** — a required workout whose date passed without being done.

**Adherence** compares what was completed against what was *required*, so optional
work and legitimate skips are treated fairly rather than punishing the trainee.

FitIntel 360 also distinguishes two different ideas you'll see in review:

- **Training load / session effort** — a relative sense of how demanding a session
  was.
- **Resistance volume** — the amount of resistance work performed.

These are **separate** and are shown as read-only analytics; the app does not turn
them into medical measures or automatic program changes.

If a trainee raises a **safety report** during a workout, review it promptly in your
safety area, acknowledge it, and follow up appropriately. Safety-related skips are a
signal to check in with the person, not just a data point.

---

## 14. Demo mode

Demo mode (**Explore Demo**) is a synthetic, **read-only** workspace:

- You can browse a fictional roster, programs, and history.
- You **cannot** create, edit, invite, assign, or delete anything — the app blocks
  changes and shows a demo banner.
- Nothing you do in demo affects real accounts.

Use demo to learn the interface or to show someone how it works. **Never enter real
personal or health information into demo.**

---

## 15. Common mistakes

- **Exercise left as a draft** — publish it, or templates can't use it.
- **Template left as a draft** — publish it, or programs can't use it.
- **Program left as a draft** — publish it, or you can't assign it.
- **Empty "Published Program version" selector** — you don't yet have a published
  program; build and publish the chain (§7, §16), or start from the Starter Library (§12).
- **Expecting to edit a starter program** — you can't; starter content is read-only.
  Choose **Use this program** to get your own editable draft, then edit that (§12).
- **A copied program stays a draft** — that's expected; publish it before assigning.
- **Trainee hasn't finished onboarding** — some scores won't appear until they do.
- **Missing daily check-ins** — a blank readiness is "no data", not a problem to act
  on.
- **Trying to edit a published version directly** — published versions are immutable;
  create a new revision instead (§10).
- **Expected data not showing** — check you're looking at the right trainee, date, or
  week; schedules are date-based and trainee-local.
- **Entering real sensitive health details in demo mode** — don't; demo is synthetic.

---

## 16. Troubleshooting

**Symptom → likely cause → action.**

**"Published Program version" dropdown is empty.**
- *Likely causes:* you only created an Exercise; no Workout Template exists; no
  Program exists; the Program is still a draft; or a temporary loading/connection
  error.
- *Action:* follow the chain **Exercise → Template → Program → Assignment** and make
  sure **each required layer is published**. Use the **Go to Programming → Programs**
  link in the empty state. If you expected a published program, refresh and retry. If
  a genuinely published program still doesn't appear, report it (§20).

**A trainee doesn't appear on my roster.**
- *Likely cause:* the invitation wasn't redeemed, expired, or was already used.
- *Action:* check Invitations history; issue a fresh invite if needed.

**A trainee's readiness or scores are blank.**
- *Likely cause:* onboarding incomplete or no recent check-in.
- *Action:* confirm they onboarded and are checking in; a blank means missing input.

**Preview schedule is disabled.**
- *Likely cause:* no trainee selected, no published program selected, or no start date.
- *Action:* pick all three; if no program can be selected, see the empty-selector
  entry above.

**Something looks broken or a page won't load.**
- *Action:* refresh; if it persists, report it with what you were doing (§20).

**I cannot edit a starter program.**
- *Likely cause:* starter programs are read-only by design.
- *Action:* open the program and choose **Use this program** to create your own
  editable draft, then edit that copy (§12).

**The copied program does not appear in Assignments.**
- *Likely cause:* your copy is still a draft; only published programs can be assigned.
- *Action:* open your copy in **Programming → Programs**, review it, and **Publish** it.

**I cloned a program but it is still a draft.**
- *Likely cause:* that is expected — copying never publishes automatically.
- *Action:* publish the draft when you are ready to assign it.

**I changed my copy, but the starter program did not change.**
- *Likely cause:* copies are independent by design; edits never flow back to the starter.
- *Action:* nothing needed — this is intended. Starter updates also never change your copy.

**I do not see the Starter Library.**
- *Likely cause:* the starter library has not been installed for this workspace.
- *Action:* you can build programs from scratch in **Programming → Programs**; report it
  if you expected starter content to be available.

**A "Use this program" (clone) action failed.**
- *Likely cause:* a temporary connection or server error; no partial copy is created.
- *Action:* retry; if it keeps failing, report it (§20). Your programs are unaffected.

---

## 17. Safe and appropriate use

- FitIntel 360 **supports** coaching decisions; it does not make them for you.
- It does **not** diagnose medical conditions or provide medical clearance.
- Use your professional judgment; scores are inputs, not instructions.
- While testing, avoid entering unnecessary sensitive personal or health data.
- Never share passwords, invitation codes, or secrets in screenshots, messages, or
  issue reports.
- For any serious, current, or worsening symptom a trainee reports, direct them to
  appropriate professional care.

---

## 18. Quick-start checklist

1. Sign in to your coach account.
2. Open **Invitations**, create an invite, and share the link/code privately.
3. Confirm the trainee appears on **Overview** after they register and onboard.
4. In **Programming**, create and **publish**: an **Exercise**, then a **Template**
   using it, then a **Program** using the template.
5. Open **Assignments**, pick the trainee and your **published Program**, choose a
   start date, **preview**, and **confirm**.
6. Check that the trainee can see their scheduled workouts.
7. Review readiness, adherence, and any safety reports over the following days.

---

## 19. Your professional profile and photo

Your profile is how you present yourself to the trainees you coach. It is
self-declared — nothing is verified — and you can change it anytime without
administrator approval. Open it from **Profile** in the navigation.

### Editing your profile information

On the **Profile** page you can set:

- **Preferred display name** — how your name is shown across FitIntel 360. Defaults
  to your account name when empty.
- **Headline** — a short professional tagline (for example, "Strength & conditioning
  coach").
- **Coaching philosophy** — a longer description of how you coach and who you work
  best with. Avoid sensitive personal or health details.
- **Specialties** — a comma-separated list (for example, "Powerlifting, Mobility,
  Fat loss"). They appear as tags; duplicates and extra spaces are cleaned up.
- **Years of experience** — a whole number from 0 to 80.
- **Certifications** — plain text, shown exactly as you type it. Certifications are
  **not** verified or validated.

Make your changes and choose **Save profile**. A confirmation appears; your entries
stay on the page if a save fails so nothing is lost.

### Uploading and changing your photo

In the **Profile photo** card:

1. Choose **Add photo** (or **Replace photo** if you already have one) and pick a
   **JPEG, PNG, WEBP, or GIF up to 5 MB**.
2. A preview appears. Choose **Upload photo** to save it, or **Cancel** to discard.
3. To take your photo down, choose **Remove**. It is removed immediately.

Replacing a photo swaps it cleanly — the previous image is retired, never left
behind. Your photo appears next to your name in the navigation and everywhere your
identity is shown.

### How trainees see your profile

Your assigned trainees see your photo, display name, headline, coaching philosophy,
specialties, experience, and certifications on their **Today** page. Trainees who are
not assigned to you cannot see your profile or photo at all. You, in turn, see each
assigned trainee's photo on your roster and on their record.

### Recommended practices

- Use a clear, professional headshot so trainees recognize you.
- Keep your headline short and specific.
- List specialties that match the trainees you take on.
- Write certifications plainly and honestly — they are self-declared and unverified,
  so don't imply endorsement the platform does not provide.

## 20. Giving feedback

Your feedback shapes the app. Please report:

- **Blockers** — anything that stops you from getting your job done.
- **Confusing UX** — anything unclear or that looks broken.
- **Incorrect data** — a number or state that seems wrong.
- **Suggestions** — improvements you'd like to see.

When you report something, include what you were doing, what you expected, and what
happened (a screenshot helps — but never include passwords or codes). The team
triages by urgency: work-stopping problems first, then confusing or incorrect
behavior, then smaller polish and ideas. You don't need to label the severity
yourself — just describe the impact and we'll prioritize it.

Thank you for helping test and improve FitIntel 360.
