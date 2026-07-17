# Frequently asked questions

This FAQ covers the currently implemented Fitness Intelligence Platform. See the [Product guide](product-guide.md), [trainee user manual](user-manual-trainee.md), [coach user manual](user-manual-coach.md), [troubleshooting guide](troubleshooting.md), [Health Index v1](scoring/health-index-v1.md), [Daily Intelligence v1](scoring/daily-intelligence-v1.md), and [security notes](security.md) for more detail.

## Product and access

### Can I explore the application without an account?

Yes, when the environment owner has explicitly enabled and seeded the public demo. Select **Explore Demo** on sign-in and choose a synthetic coach or trainee workspace. No credentials are shown or required. Demo accounts are read-only and must not be used for personal or medical information.

### Why does Explore Demo say it is unavailable?

Demo authentication fails closed. The backend returns an unavailable state when `DEMO_MODE_ENABLED` is false or when the configured synthetic identity has not been explicitly seeded. Normal sign-in and account creation remain separate.

### Does the public demo weaken registration security?

No. The demo endpoint can authenticate only active database users marked as demo identities. Normal coaches still need the protected coach registration code, normal trainees still need a coach-specific single-use invitation, and normal role and coach-assignment authorization remains active.

### What does the platform do today?

It supports trainee registration, role-aware sign-in, coach assignment, onboarding, an immutable baseline Health Index, one atomic daily check-in for the trainee's current local date, daily recovery/activity/nutrition/readiness scores, bounded 7- or 30-day trends, deterministic recommendations and alerts, and read-only coach review.

### Is this a medical product or diagnosis?

No. The scores are deterministic coaching-support interpretations. They do not diagnose a condition, predict injury, provide medical clearance, or replace qualified medical care.

If severe or worsening chest pain or breathing difficulty is happening now, seek immediate professional medical help.

### Does a lower score mean I am unhealthy?

No. A score is a product interpretation of reported information under configured rules. It is not a judgment, diagnosis, or complete picture of health. Review the contributing information and use appropriate coach or professional guidance instead of chasing a number.

### What should I do if I report chest pain or breathing difficulty?

The onboarding form shows immediate safety guidance. Seek immediate professional medical help if chest pain or breathing difficulty is severe, worsening, or happening now. Do not wait for a coach response or rely on another favorable application score.

### What accounts are available in the local demo?

| Role | Email | Password |
|---|---|---|
| Coach | `coach@fitness.example.com` | `DemoPass123!` |
| Trainee with baseline and synthetic history | `trainee@fitness.example.com` | `DemoPass123!` |
| Trainee with no check-ins | `no-checkins@fitness.example.com` | `DemoPass123!` |

Seeded local demo identities can still be used directly. New registration uses a coach-specific, single-use invitation created from the coach workspace.

### Can a coach register from the registration page?

Yes, when the backend has a private `COACH_REGISTRATION_CODE`. Choose **Coach** during registration and enter that code. If the backend code is missing, coach registration is disabled. The platform does not verify professional credentials.

### Do I choose my role when signing in?

No. Login accepts only email and password. The backend-stored account role determines whether the coach workspace, trainee onboarding, or trainee dashboard opens.

### How does a trainee invitation work?

A signed-in coach creates an expiring, single-use invitation and shares its code or registration link manually through a trusted channel. Only a hash is stored, the raw secret is shown once, and redemption creates the coach assignment. The optional email field restricts redemption to an account using that email; it does not cause email delivery. Leaving it blank allows any eligible trainee possessing the secret to redeem it. Used, expired, revoked, and email-mismatched invitations cannot be redeemed. FitIntel 360 does not send invitation emails.

### Can a trainee contact their coach in FitIntel 360?

Today shows the current coach relationship, available coach name, and email. The email link opens the device's external email application. FitIntel 360 has no in-app messaging, does not promise an immediate response or continuous monitoring, and does not verify professional credentials or provide medical supervision.

### Why was I redirected after opening a page?

Routes are role-protected. A coach is redirected to the coach overview; a trainee is redirected to Today. An expired token ends the browser session and asks the user to sign in again.

## Scores and data

### What is the difference between the Health Index and daily readiness?

The Health Index is an immutable onboarding baseline calculated by `health-index-v1`. Daily intelligence is calculated from a local-date check-in using `daily-intelligence-v1`. Daily observations never overwrite or recalculate the baseline.

### Why is a score or chart unavailable?

The interface does not invent missing information. Daily scores require a submitted check-in. Nutrition can be unavailable when the required real targets or inputs do not exist. A trend needs recorded daily values. Missing dates remain gaps rather than zero.

### Why is a component marked incomplete or limited?

Required onboarding information must be present before submission, but optional information can remain absent. A component can therefore report limited data, and the calculation details list missing optional fields. The scoring engine uses only the documented fallback or available inputs; it does not fabricate an answer.

### Why did a recommendation change?

Daily recommendations are recalculated when today's check-in is created or edited. A changed input, recent training-load window, newly met pattern rule, or resolved daily alert can change the applicable deterministic templates. The scoring version identifies which rule set produced the result.

### Can the trainee edit today's check-in?

Yes. After submission, choose **Edit today**, then **Update today’s check-in**. The existing local-date record is updated and deterministically rescored. Past dates are read-only, and check-in drafts are not implemented.

### Can a submitted onboarding assessment be changed?

No. Submitted responses are locked for auditability. Starting a new assessment version is deferred.

### Why can the check-in date differ between users?

The trainee profile's validated IANA timezone determines the current local date. The stored local date is preserved and is not reinterpreted after timezone or daylight-saving changes.

### Are missing days counted as zero?

No. Trend lines break across missing dates. Tables say **Missing**, and rolling comparisons use recorded values according to the documented rules.

### Are score changes generated by AI?

No. Current scores, alerts, and recommendations use versioned deterministic rules. External AI narration is not implemented.

### How are scores calculated?

The application applies versioned, deterministic weights, mappings, thresholds, and missing-data rules. Daily calculation explanations are visible to the trainee, and the assigned coach can inspect the full baseline contributors. Technical details are documented in [Health Index v1](scoring/health-index-v1.md) and [Daily Intelligence v1](scoring/daily-intelligence-v1.md).

## Coach experience

### What can a coach see?

A coach can see assigned-roster summaries, check-in completion, latest readiness, open daily-alert counts, the baseline score, assigned trainee daily score history/trends, current recommendations, daily alerts, baseline alerts, and the baseline Health Index.

### Can any coach see a trainee profile?

No. The backend requires an active coach–trainee assignment for every trainee-specific coach route. Directly changing a trainee identifier in the URL does not bypass that check.

### Can a coach see every raw check-in field?

No. The current trainee-detail interface shows only sleep, stress/fatigue, and steps in **Latest check-in**. **Recent raw check-in summaries** shows date, sleep, stress, steps, and overall feeling. Other submitted raw fields and the note are not displayed in the coach UI.

### Can a coach edit trainee data?

No. Coach daily and baseline endpoints are read-only. There are no coach controls to edit check-ins, onboarding responses, profiles, scores, recommendations, or assignments.

### Where are roster search, filters, and sorting?

They are not implemented. There is no search, filter, sort, pagination, or selectable-row control and no dedicated attention-queue control. Coaches review the server-provided roster and use **Review** or **Review trainee**.

### Can a coach resolve or dismiss an alert?

No. There is no alert-resolution UI. Daily alert state is maintained by deterministic rules during scoring; baseline notices remain attached to their immutable snapshot.

### Why does the dashboard show only four alert cards?

The overview intentionally displays at most four current daily-alert cards. Use **Review trainee** on a displayed card or review roster records directly. There is no separate all-alerts page in the current UI.

### Does “Missing today” mean the trainee failed?

No. It means no check-in exists for that trainee's current local date. The interface explicitly frames this as neutral context for a supportive follow-up.

## Features and operations

### Are workouts, meal plans, messages, or wearables available?

Coaches can author versioned exercise-library content, reusable workout templates, and
multi-week programs, then assign a published Program version on a trainee-local date. Trainees can
start, explicitly log, resume, complete, or intentionally end those scheduled workouts incomplete.
Trainees can also view immutable readiness context and submit workout safety reports; assigned
coaches can acknowledge or resolve those reports. Coach completed-session analytics,
load/adherence analytics, meal planning, wearables, notifications,
messaging, exports, clinical reporting, and external AI narration remain deferred.

### Is there a native mobile application?

No. The current product is a responsive web application. It adapts its navigation and roster layout for smaller browser screens, but there is no iOS or Android application.

### Can a coach create workouts or meal plans?

Coaches can create reusable workout templates from published system or private exercises and
assemble them into 1–12 week programs. Programs pin exact published template versions and can
mark required, optional, rest, and coach-authored deload context. Coaches can preview and create
date-only Program schedules, but cannot record or correct trainee sessions or create meal plans. Trainee health records remain
read-only to coaches.

### Can I resume a workout after closing the page?

Yes. Each scheduled workout has at most one execution session. Reopening its Program detail loads
the same saved session and revision. Only an explicit per-set save is persisted; unsaved field
changes may be lost on refresh. Completed and ended-incomplete sessions cannot be reopened.

### Does readiness change my workout or provide medical clearance?

No. It is an immutable copy of the latest eligible Daily Intelligence snapshot on or before the
scheduled local date. Fresh means zero or one day old; stale means two or more days old. Unavailable
means no eligible snapshot exists. It never blocks start or changes sets, loads, schedules, or Programs.

### Are workout safety reports monitored immediately?

No. Safety reports are not monitored continuously, and the platform does not diagnose medical
conditions. Critical categories end the workout and display escalation guidance; pain or unusual
discomfort pauses the exercise. The assigned coach can later append acknowledgement or resolution.

### Can I enter kilograms or pounds?

Yes, for external load or assistance fields that the exercise tracking mode supports. The original
value and unit remain visible and the backend also stores a deterministic Decimal kilogram value.
Assistance is not treated as external resistance load.

### Can I close Docker?

Yes. Stopping Compose or quitting Docker Desktop stops the running application but does not intentionally delete the named PostgreSQL volume. Start Docker again and run `docker compose up --wait` from the repository root. Never add `-v` if you want to retain the database.

### What deletes local Docker data?

`docker compose down -v` deletes the named PostgreSQL volume and all application data stored there. See [Troubleshooting](troubleshooting.md#reset-the-local-demo) before using it.

### What URLs should I use?

- Docker frontend: <http://localhost:5175>
- Local Vite frontend: <http://localhost:5175>
- API: <http://localhost:8000>
- OpenAPI: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>

Docker and local Vite use the same frontend port, so run only one of them at a time. The backend defaults to allowing browser requests from port 5175.

### Is the repository HIPAA or GDPR compliant?

No compliance claim is made. Production readiness depends on technical, legal, organizational, vendor, and operational safeguards that are outside this local milestone. See [Security and compliance notes](security.md).

### What is the Workouts page / training load?

The Workouts page shows deterministic, read-only analytics from completed workouts: training load (`duration × reported effort`), completion, prescribed-set and exercise adherence, weekly planned-versus-completed load, and recorded bests. Training load summarizes workout duration and reported effort. It is not a medical measure, does not predict injury, and never changes your program, schedule, sets, or loads. Missing values are shown as unavailable and never treated as zero. See [Workout Load v1](scoring/workout-load-v1.md).

### Does "recorded best" mean a personal record?

No. Recorded bests are simply the highest load, repetitions, and volume you recorded within the selected 7-, 14-, or 30-day range from completed workouts. The product deliberately avoids "PR", "personal record", "lifetime best", and "all-time best" wording. See [Recorded bests](recorded-bests.md).
