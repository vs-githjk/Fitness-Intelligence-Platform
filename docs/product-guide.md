# Fitness Intelligence Platform: Product Guide

## Who this guide is for

This guide introduces the current Fitness Intelligence Platform to trainees, coaches, product stakeholders, demo viewers, and developers joining the project. It describes what is available in the application today. It does not present roadmap ideas as working features.

For hands-on instructions, begin with [Getting started](getting-started.md), then use the [trainee manual](user-manual-trainee.md) or [coach manual](user-manual-coach.md).

> **Coaching support, not medical care:** The platform does not diagnose, treat, provide emergency care, or clear anyone to exercise. It does not replace a doctor, registered dietitian, physiotherapist, or qualified coach. Seek appropriate professional help for serious, current, worsening, or concerning symptoms, regardless of any score shown by the application.

## What the platform is

The Fitness Intelligence Platform is a coach–trainee fitness monitoring application. It brings together:

- a structured onboarding assessment;
- a deterministic baseline Health Index;
- daily check-ins;
- Recovery, Activity, Nutrition, and Training Readiness scores;
- date-based trends and review alerts;
- structured recommendations; and
- read-only coach oversight for assigned trainees.

It is more than a workout tracker. A workout tracker commonly records what happened during exercise. This platform also connects self-reported sleep, recovery, stress, movement, hydration, nutrition information, and recent training load so that a trainee and coach can have a more informed conversation.

The score calculations and alert rules are versioned and deterministic. The same validated inputs and scoring version produce the same result. No AI model is active in the current product, and AI does not create, change, or narrate scores or recommendations.

![The trainee Today page showing daily scores and a separate baseline reference](screenshots/manual/trainee-today-desktop.png)

## The problem it addresses

### For trainees

Beginning or maintaining a fitness routine can involve disconnected questions: How well am I recovering? Is stress affecting today’s training? How do sleep, activity, hydration, and nutrition fit together? Should I maintain today’s effort or consider recovery?

The platform turns submitted information into consistent coaching signals. It also keeps the onboarding baseline separate from daily observations, so a difficult day does not rewrite the trainee’s starting-point assessment.

### For coaches

Managing several trainees through separate notes and conversations makes it difficult to see who checked in, whose readiness is low, and which patterns merit review. The coach workspace gathers assigned trainees into one roster, summarizes current daily state, and provides baseline context and longitudinal detail.

The platform supports prioritization; it does not make decisions for the coach or replace professional judgment.

## How the current system works

```text
Demo invite and coach assignment
→ Trainee onboarding assessment
→ Deterministic baseline Health Index
→ Daily trainee check-ins
→ Deterministic daily scores
→ Gap-aware trends and rule-based alerts
→ Assigned coach review
→ Structured next actions
```

A protected coach can register with the backend-only coach registration code, then create an expiring single-use invitation. A trainee redeems that invitation and is transactionally assigned to its issuing coach. The trainee completes and submits onboarding, then can record one check-in for the current date in their saved IANA timezone. That entry can be edited until the local date changes. Past dates are read-only and cannot be entered retroactively.

The assigned coach can view the trainee’s baseline, daily scores, recent raw check-in summaries, trends, alerts, and recommendations. Other coaches are denied access unless they have an active assignment.

### Public demo workspace

The sign-in page offers **Explore Demo** as a separate entry from **Sign in** and **Create account**. A visitor chooses a coach or trainee view, and the backend issues a short-lived normal role-scoped session for a configured synthetic demo identity. No email, password, coach registration code, trainee invitation, or prebuilt JWT is exposed.

The demo coach has seven assigned fictional trainees representing improvement, low readiness, limited activity, hydration review, stress/sleep concern, missing check-ins, and stable high performance. The main demo trainee has a submitted baseline and a 21-local-date window with intentional gaps. Demo sessions are read-only: navigation and local UI exploration work, while persistent mutations are rejected by the backend. The visible demo banner states that all information is synthetic and changes are disabled.

The public demo does not replace normal account creation. Coaches still require the protected coach registration code, trainees still require a coach-specific invitation, and ordinary login continues to detect the role from the authenticated backend identity.

## Core concepts

### Baseline assessment

The onboarding assessment records a starting point across goal, profile, hydration, sleep, movement, training habits, stress, optional cardiovascular information, and nutrition. Required answers must be present before submission; optional answers are not invented when absent. A draft can be saved and resumed.

Once submitted, that assessment becomes an immutable baseline snapshot. Opening Assessment afterward shows the submitted responses. To create another baseline, the backend supports saving a new assessment draft, but the current routed trainee interface does not offer an ordinary “reassess” action.

### Health Index

The Health Index is a 0–100 baseline coaching score created from the submitted onboarding assessment. It combines ten weighted components: hydration, sleep, nutrition, stress, cardiovascular information, workout intensity, physical activity, daily steps, goal alignment, and assessment completion.

Use it as a structured starting point for discussion. It is not a measure of personal worth, fitness certification, diagnosis, or forecast of future health. Missing optional information is handled according to documented rules and can affect the result.

The current trainee Today page displays only a compact baseline reference: the overall Health Index and band. There is currently **no routed trainee screen for the full baseline component breakdown**. The assigned coach’s trainee-detail screen does show the full breakdown, contributions, review notices, recommendations, missing optional fields, and scoring version.

For exact formulas, see [Health Index v1](scoring/health-index-v1.md).

### Component score and contribution

A component score normalizes one area, such as sleep or hydration, to a 0–100 scale. Its weight controls how much it contributes to the overall Health Index. Stored explanations, input snapshots, status labels, and weighted contributions make the baseline auditable in the coach view.

### Assessment completion

Assessment completion is the baseline component that measures whether the required onboarding answers are present. Its inputs are the required goal, profile, hydration, sleep, movement, training, stress, and calorie-approach fields. Use it to confirm that the submitted baseline had the required information; submission requires all of those fields, so a submitted baseline receives full completion credit. It does not measure honesty, effort, health, or the quality of optional information.

### Daily check-in

The daily check-in is an atomic, one-to-two-minute form covering:

- sleep duration and quality, waking refreshed, soreness, fatigue, and stress;
- steps, whether exercise occurred, and conditional exercise details;
- water, optional calories, optional protein, and optional nutrition-plan adherence; and
- overall feeling and an optional short note.

The local-date entry is either saved completely or not saved. There are no check-in drafts. Today’s entry can be edited; past entries cannot.

### Recovery Score

Recovery is a 0–100 daily score based on sleep duration, sleep quality, waking refreshed, fatigue, soreness, and stress. Use it to understand which reported recovery factors may deserve attention that day. It does not detect illness, diagnose fatigue, or prove that exercise is safe.

### Activity Score

Activity is a 0–100 daily score based on step bands, exercise duration, and exercise participation/activity mix. Exercise-duration credit is capped, so the score does not suggest that unlimited exercise is better. It is a coaching signal, not a complete measure of training quality or fitness.

### Nutrition Score

Daily Nutrition is a 0–100 score calculated only from available valid components: hydration against a stored baseline-derived target, protein against a stored target when both target and intake exist, and optional self-reported adherence. Available weights are rebalanced. Calories are stored for context but do not affect the current daily score.

If no valid nutrition component can be calculated, the score is shown as unavailable rather than zero. The platform does not invent calorie or protein targets and does not create a meal plan.

### Training Readiness

Training Readiness combines the Recovery Score with a seven-local-date training-load signal. Training load is exercise minutes multiplied by session RPE. Missing dates do not create fabricated workouts.

Use readiness to guide a conversation about the day’s training approach:

| Score | State | Practical interpretation |
|---:|---|---|
| 80–100 | Ready to push | Reported recovery and recent load support the most positive product state. |
| 60–79.9 | Maintain | A steady approach may be appropriate based on the submitted data. |
| 40–59.9 | Reduce intensity | Consider a lower-intensity approach and review the contributing factors. |
| Below 40 | Recovery recommended | Consider recovery-focused activity and review the contributing factors. |

Readiness is not medical or professional clearance, injury prediction, or an overtraining diagnosis. A user should never ignore symptoms because readiness looks favorable.

For the complete daily rules, see [Daily Intelligence v1](scoring/daily-intelligence-v1.md).

### Trends

Progress charts cover Recovery, Activity, Nutrition, Readiness, sleep duration, stress, and steps. The interface currently offers 7- or 30-day views; the API also supports 14 days. A missing check-in remains a visible gap, never a fabricated zero. Each recorded value can be compared with the previous recorded value, while the underlying trend response also carries a rolling average over the last seven recorded values.

### Alert

Alerts are deterministic review signals. Baseline severities can be `informational`, `review`, `elevated`, or `urgent`; daily alerts use `informational`, `review`, and `elevated`. Daily rules include current high stress or very short sleep and configured multi-day patterns involving recovery, stress, fatigue, soreness, effort, load, hydration, protein, or low recorded activity.

An alert is not a diagnosis. “Urgent” baseline guidance is reserved for reported chest discomfort or breathing difficulty and advises immediate professional medical help if symptoms are severe, worsening, or happening now. A favorable score must not override symptoms.

Open daily rules resolve automatically after a later calculation no longer triggers them. Baseline alerts currently have no user-facing resolve action.

### Recommendation

Recommendations are structured templates generated from score thresholds and triggered rules. They can include a hydration gap, sleep opportunity, the next step band, training-intensity review, or an alert-specific action. Priority and safety text help users decide what to discuss. They are not personalized treatment, meal plans, or workout prescriptions.

### Coach assignment

An assignment is the server-enforced relationship that allows a coach to view a trainee. Knowing a trainee’s identifier is not enough. Redeeming a coach-specific invitation creates the assignment; invites expire, can be revoked, and cannot be reused. The application does not currently include assignment transfer or removal controls.

## Health Index interpretation

| Score | Implemented band |
|---:|---|
| 90–100 | Elite |
| 80–89.9 | Excellent |
| 70–79.9 | Good |
| 60–69.9 | Average |
| 40–59.9 | Needs Improvement |
| Below 40 | High Risk |

These are product labels, not clinical classifications. “High Risk” does not diagnose a condition, and “Elite” does not mean a person is free from medical risk. The score reflects the submitted baseline data and documented handling of missing optional fields. Daily scores never replace or recalculate the baseline Health Index.

## Explainability and deterministic rules

The backend stores versioned score snapshots, normalized components, contributions, input snapshots, explanations, missing-field information, recommendations, and triggered rules. This supports review of how a result was produced.

In the currently routed interface:

- trainees can expand “How today’s scores were calculated” to see daily components and explanations;
- trainees see current daily review signals and recommended next actions;
- trainees see only a compact overall baseline reference on Today; and
- assigned coaches can see the full baseline breakdown and detailed latest daily context.

Deterministic calculations are used so that score behavior is repeatable, testable, and versioned. No generative AI is active. A future narration interface exists as a code extension point, but it is not connected to the user experience and must not be treated as a current feature.

## Current capabilities

### Trainee capabilities

- Register with a coach-created single-use invitation and sign in.
- Complete, save, resume, review, acknowledge, and submit onboarding.
- View submitted assessment responses through Assessment.
- See the overall baseline Health Index and band as a reference on Today.
- Submit or edit the current timezone-local date’s check-in.
- View Recovery, Activity, Nutrition, Readiness, alerts, recommendations, and daily calculation explanations.
- View gap-aware 7- or 30-day progress charts and accessible data tables.
- Sign out.

### Coach capabilities

- Sign in to a role-specific workspace.
- View today-completion, missing-today, low-readiness, and open-daily-alert counts.
- View assigned trainees in a desktop table or mobile cards.
- Review each trainee’s latest daily scores, check-in summary, recommendations, 7- or 30-day history, and selected trends.
- Review the full onboarding Health Index, component contributions, baseline recommendations, missing optional fields, and safety notices.
- Read assigned-trainee daily check-in history, including submitted notes through the authorized API, although the current coach detail UI’s summary table does not display note text.
- Sign out.

### Shared platform capabilities

- Role-aware bearer-token authentication and server-side authorization.
- Active coach-assignment enforcement.
- Validated input ranges and conditional daily exercise fields.
- Versioned deterministic scoring and rule-based alerts.
- Timezone-local daily records and UTC event timestamps.
- PostgreSQL persistence in the Docker setup, with SQLite used in tests.
- Responsive, keyboard-conscious web layouts with mobile navigation and accessible trend tables.

## Safety, privacy, and compliance limits

The application is an early product and demonstration environment. It uses bcrypt password hashing, expiring signed access tokens, role checks, assignment checks, restricted CORS, opaque identifiers, and database foreign-key and uniqueness constraints. It does not intentionally log access tokens or health request bodies.

Those controls do **not** establish legal compliance. This repository does not claim HIPAA, GDPR, or other regulatory compliance. Production use would require independent legal and security work, including appropriate policies, agreements, consent, audit logging, retention/deletion/export workflows, managed secrets, key rotation, verified encryption, backup and recovery, security monitoring, incident response, penetration testing, and vendor review.

For this local milestone, the access token is stored in browser local storage. Avoid using real health information, shared devices, or production credentials. Assigned coaches can view sensitive baseline and daily information. See [Security and compliance notes](security.md) for the current trust boundary and production gaps.

The quality of every score and recommendation depends on the quality and completeness of submitted information. Manual entry is the only current source of health and activity data.

## Current limitations and deferred features

The following are not available in the current application:

- a routed trainee view of the full baseline component breakdown;
- editing or deleting a submitted baseline through the current UI;
- past-date check-in entry or correction, check-in drafts, or bulk import;
- coach editing of trainee data;
- coach account self-registration or assignment management;
- password reset, account recovery, refresh-token rotation, revocation controls, or MFA;
- workout-program building or workout planning;
- meal-plan or nutrition-plan creation;
- wearables and external health-data integrations;
- messaging, notifications, or reminders;
- exports, clinical reports, or formal audit logs;
- consent, retention, deletion, and data-portability workflows;
- active AI narration, an AI coach, predictive injury detection, or computer vision; and
- native iOS or Android applications. The current product is a responsive web application.

## Technology overview

The responsive frontend uses React, TypeScript, Vite, Tailwind CSS, routing, query management, and validated forms. FastAPI provides versioned JSON endpoints, authentication, and authorization. SQLAlchemy models and Alembic migrations support PostgreSQL; tests use an in-memory SQLite database.

The scoring and risk modules are pure deterministic Python functions separated from the web routes and database transactions. Backend tests cover major score boundaries, registration and onboarding, role/assignment protection, daily create-and-edit behavior, trends, timezone handling, and transaction rollback. Frontend component and end-to-end tests cover important daily and visual flows. Docker Compose packages the frontend, backend, and PostgreSQL services for local use.

Developers can find startup and verification commands in the root [README](../README.md).

## Continue reading

- [Getting started](getting-started.md)
- [Trainee user manual](user-manual-trainee.md)
- [Coach user manual](user-manual-coach.md)
- [Frequently asked questions](faq.md)
- [Troubleshooting](troubleshooting.md)
- [Health Index v1](scoring/health-index-v1.md)
- [Daily Intelligence v1](scoring/daily-intelligence-v1.md)
- [Security and compliance notes](security.md)
- [Design system](design-system.md)
