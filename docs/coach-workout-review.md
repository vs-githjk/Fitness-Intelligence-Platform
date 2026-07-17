# Coach workout review

Coaches have **read-only** review of the workout execution of their actively
assigned trainees. Review never edits logs, reopens sessions, alters immutable
summaries or safety-report content, or modifies completed data.

## What a coach can inspect

For each session: scheduled workout, assignment/program/template versions,
session status, start/end timestamps, actual duration, session RPE, exercises,
planned prescriptions, actual set values, skipped sets, skipped exercises,
trainee-added sets, trainee notes, immutable readiness context (with source
date and staleness), safety reports and their review status, the immutable load
summary, and the neutral planned-versus-completed comparison.

Safety information is surfaced before less-urgent analytics.

## Endpoints

All require an **active** `CoachTraineeAssignment`. Cross-coach object discovery
is prevented: a session belonging to a trainee who is not actively assigned to
the requesting coach returns **404** (indistinguishable from a missing object),
never 403.

| Method | Path |
|---|---|
| GET | `/api/v1/coach/trainees/{trainee_id}/workout-sessions` |
| GET | `/api/v1/coach/workout-sessions/{session_id}` |
| GET | `/api/v1/coach/trainees/{trainee_id}/workout-load` |
| GET | `/api/v1/coach/trainees/{trainee_id}/workout-adherence` |
| GET | `/api/v1/coach/trainees/{trainee_id}/recorded-bests` |

Trainee-facing equivalents (`/api/v1/trainee/workout-load`,
`/workout-adherence`, `/recorded-bests`) return only the calling trainee's own
analytics.

All ranges are bounded to 7, 14, or 30 days (with an optional `end_date`); an
invalid range returns 422 `invalid_range`.

## Neutral planned-versus-completed comparison

The comparison state is one of `above_planned`, `near_planned`,
`below_planned`, or `unavailable` (within 10% of planned is "near"). The
language is deliberately neutral — being above or below planned is not
automatically good or bad, and the platform draws no medical conclusion.

## Authorization and cache isolation

- Trainees see only their own analytics; coaches see only actively assigned
  trainees; an inactive assignment is denied.
- All protected React Query keys include the account identity scope, so
  login/logout/demo transitions never show prior analytics and old in-flight
  responses cannot repopulate a new identity's cache.
- Demo accounts may inspect analytics; all mutations remain disabled. Phase 7B
  adds no new mutation endpoints — every analytics endpoint is a read-only GET.
