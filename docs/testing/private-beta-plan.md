# Synthetic private beta plan

This plan covers a small, invite-only evaluation of the staging product using fictional data only. It does not authorize real trainee, patient, coach-client, medical, or other personal health information.

The beta validates comprehension, navigation, accessibility, deterministic-score explanation, and operational readiness. It does not implement or begin Milestone 3 product modules.

See [Staging deployment](../deployment/staging.md), [Production readiness](../deployment/production-readiness.md), [Product guide](../product-guide.md), [Coach manual](../user-manual-coach.md), [Trainee manual](../user-manual-trainee.md), and [Roadmap](../roadmap.md).

## Objectives

- Confirm trainees can register with the synthetic invite, complete onboarding, understand the baseline, submit/edit today's check-in, and interpret real persisted trends.
- Confirm coaches can understand roster status, daily readiness, alerts, limited raw check-in summaries, and the separate onboarding baseline.
- Confirm testers understand that scores provide coaching support rather than diagnosis, treatment, medical clearance, or injury prediction.
- Find navigation, wording, accessibility, responsive-layout, empty-state, and recovery problems.
- Exercise staging deployment, monitoring, support, incident, rollback, and restore procedures.

The beta does not validate clinical outcomes, score efficacy, legal compliance, production scale, wearable accuracy, or future module demand through implemented features.

## Cohort

Use a named, manually approved cohort of no more than ten testers for the first round:

- Product/engineering maintainers who can observe operational behavior.
- Accessibility/usability reviewers.
- A small number of coach-domain reviewers working only with fictional personas.
- Trainee-experience reviewers working only with fictional responses.

Maintain the participant list in an access-restricted operational system, not this repository. Record participant name, approved role, synthetic account, invitation date, acknowledgement of the synthetic-only rule, and deprovisioning date.

Do not recruit real coach-client pairs for this round. Do not ask testers to copy their own health history into fictional fields.

## Account and access model

- Use only the approved staging Vercel and Render resources.
- Provision the approved fictional personas once after the staging migration using the reviewed staging-only procedure required by the deployment runbook.
- Create any additional account with a fictional name, unique test email alias, synthetic responses, and no real free-text health note.
- Do not share one coach browser session among participants.
- Do not publish the staging URL or invite value publicly.
- Remove or disable participant access at cohort exit.

The current single invite code and oldest-coach assignment are known limitations. They are acceptable only for this controlled synthetic cohort, not a real-data beta or production enrollment model.

## Entry criteria

All items require recorded evidence and a named approver:

### Release and infrastructure

- Exact release commit, version, and migration head selected.
- Backend/frontend automated checks pass on that commit.
- Staging uses separate Vercel, Render, and PostgreSQL resources.
- Database migration and controlled staging-only synthetic provisioning completed with approval.
- No seed or provisioning action runs during an ordinary web-service restart.
- Vercel direct-route fallback, Render provider port, HTTPS, health, and exact-origin CORS verified.
- Backup exists and an isolated staging restore exercise has succeeded.
- Frontend and backend rollback procedures have been tested.

### Product and authorization

- Full staging smoke suite in the [deployment runbook](../deployment/staging.md#8-run-the-staging-smoke-suite) passes.
- Trainee/coach role boundaries and active-assignment object authorization pass.
- Empty, loading, validation, API failure, expired-session, and no-data states have been reviewed.
- Current limitations are visible in tester materials: no coach mutations, no search/filter/sort/attention-queue control, limited raw daily fields in coach view, and no alert-resolution UI.
- Baseline and daily intelligence are visibly separate.

### Safety and data handling

- Every tester receives and acknowledges the synthetic-only policy.
- Tester materials state that the product does not diagnose, treat, provide medical clearance, or replace qualified medical care.
- Immediate safety wording is present for severe or worsening chest pain or breathing difficulty.
- Support and incident contacts have named owners and tested notification paths.
- Logs have been reviewed to confirm they do not intentionally contain tokens or health payloads.
- The localStorage JWT limitation is disclosed: testers must use a dedicated non-shared browser profile/device and sign out after testing.

Do not open the beta if any entry criterion is unresolved.

## Tester briefing

Before issuing access, send:

1. The staging URL and assigned synthetic role/account through the approved private channel.
2. A clear instruction not to enter real personal or health information.
3. The product safety statement and immediate-help wording.
4. The test window and expected time commitment.
5. Links to the appropriate user manual and FAQ.
6. The support channel, incident channel, and feedback form.
7. Instructions to avoid screenshots containing credentials and to sign out after each session.
8. A reminder that private-beta access does not establish legal compliance or authorization for real-world coaching use.

Use placeholders until operational owners approve real destinations:

- Support: `<private-beta-support-channel>`
- Urgent security/privacy report: `<private-beta-incident-channel>`
- Feedback form: `<private-beta-feedback-form>`
- Beta owner: `<private-beta-owner>`
- Technical incident lead: `<technical-incident-lead>`

Do not publish personal phone numbers or provider credentials in repository documentation.

## Test journeys

### Trainee journey

1. Open a direct login or registration route and confirm it loads.
2. Register a fictional trainee or use the assigned synthetic account.
3. Complete onboarding through review and acknowledgement.
4. Explain, in the tester's own words, the Health Index, contributor weights, recommendations, notices, missing-data detail, and non-diagnostic limitation.
5. Submit today's fictional check-in.
6. Explain Recovery, Activity, Nutrition, Readiness, and their separation from the baseline.
7. Edit today's check-in and confirm the same local-date record persists after refresh.
8. Review 7- and 30-day trends and identify a missing-date gap.
9. Exercise validation, API-retry, expired-session, and keyboard navigation paths.

### Coach journey

1. Sign in as the assigned synthetic coach.
2. Explain Checked in today, Missing today, Low readiness, and Open daily alerts.
3. Review the roster at desktop and mobile widths.
4. Open an assigned fictional trainee.
5. Change the history range between 7 and 30 days.
6. Review current alerts, recommendations, daily score summaries, limited raw check-in summaries, trends, and the baseline.
7. Confirm the coach cannot edit trainee data, resolve alerts, add notes, search/filter/sort, or create a custom attention queue.
8. Confirm an unassigned coach cannot retrieve another trainee's protected data when that test persona is available.

### Operational journey

1. Confirm health and authenticated database behavior.
2. Observe sanitized logs for a test request without copying payloads.
3. Restart the backend without seeding and verify persistence.
4. Exercise a frontend rollback or temporary test deployment rollback.
5. Confirm provider notifications reach the designated technical owner.

## Feedback collection

Use the approved private form. Do not request health values or screenshots of filled assessments/check-ins.

Collect:

- Tester role and fictional account identifier.
- Task attempted and whether it was completed.
- Route/device/browser/viewport.
- What the tester expected and observed.
- Wording or score explanation that was unclear.
- Keyboard, screen-reader, contrast, touch-target, or responsive issue.
- Error message and UTC time.
- `X-Request-ID` from the affected response when available, plus any provider request identifier.
- Severity selected from the definitions below.

Do not collect passwords, access tokens, invite codes, free-text health notes, full assessment responses, or database identifiers.

## Support model

### Response priorities

| Priority | Example | Initial action |
|---|---|---|
| P0 | Suspected data exposure, unauthorized trainee access, harmful safety wording, or compromised credentials | Close beta access, notify incident leads immediately, preserve sanitized evidence. |
| P1 | Authentication outage, data loss/corruption, migration failure, or most core journeys unavailable | Stop affected testing and begin technical incident process. |
| P2 | Core task blocked for one role with a workaround unavailable | Acknowledge in the agreed support window and assign an owner. |
| P3 | Wording, visual, responsive, or usability issue with a workaround | Triage into beta findings. |

Actual response-time commitments must be set by the named beta owner before invitations. Do not promise an unstated 24/7 service.

### Support boundaries

- Support helps with synthetic staging access and product use only.
- Support must not interpret scores medically or provide emergency advice beyond approved safety wording.
- Coaches/testers must not use the beta for real clients.
- Feature requests are recorded but do not expand the beta scope.

## Incident process

1. Reporter stops the affected journey and contacts `<private-beta-incident-channel>`.
2. Incident lead records UTC time, environment, release SHA, affected route/role, observed impact, and a non-sensitive provider/request identifier if available.
3. Do not paste tokens, credentials, assessment/check-in bodies, or screenshots containing sensitive fields.
4. For suspected unauthorized access or data exposure, close beta access and rotate/revoke affected credentials as supported.
5. For safety-language concerns, suspend the affected flow until product/safety review.
6. Preserve provider logs under approved access and retention rules.
7. Decide frontend rollback, backend rollback, configuration correction, or database restore using the staging runbook.
8. Repeat smoke and authorization checks before reopening.
9. Document cause, impact, resolution, follow-up owner, and tester communication.

Because current JWTs are stored in local storage and have no refresh/revocation system, rotating `JWT_SECRET` invalidates all current tokens and requires every tester to sign in again. This is a coarse staging containment action, not a production session-management strategy.

## Data handling and retention

- Staging is synthetic-only and must not be populated from production exports.
- Use fictional names, email aliases, measurements, symptoms, notes, and coach relationships.
- Minimize free text; do not enter real conditions, events, or contact details.
- Limit Vercel, Render, GitHub, database, log, and support-system access to the approved team.
- Do not download database dumps to unmanaged devices.
- Define a beta retention end date before opening access.
- At exit, revoke tester access and either delete the staging resources/data or document why a limited synthetic environment remains.
- Verify deletion according to provider behavior, including backup-retention limitations.

## Exit criteria

The first cohort closes when all are true or when the beta owner stops it for safety/security reasons:

- Every tester is accounted for and access is revoked or explicitly extended.
- Planned trainee, coach, authorization, and operational journeys have recorded outcomes.
- No unresolved P0 or P1 finding remains.
- P2/P3 findings are triaged with owner, priority, and target milestone or explicit rejection.
- Score/safety wording confusion has been reviewed.
- Backup/restore and rollback evidence remains valid for the closing release.
- Logs, feedback, screenshots, and provider artifacts have been reviewed for accidental sensitive content.
- Staging data retention/deletion decision is executed and recorded.
- A written beta summary states what was learned without claiming production readiness, clinical validity, or compliance.

Passing this synthetic beta is not authorization for a real-data beta. The [production-readiness gates](../deployment/production-readiness.md#go-live-gates) remain separate.

## Stop conditions

Immediately pause the beta for:

- Unauthorized access across trainee/coach boundaries.
- Accidental entry or exposure of real personal/health data.
- Compromised shared credentials or provider access.
- Data corruption or unexplained loss.
- Safety wording that could delay urgent professional help or imply diagnosis/clearance.
- Provider, database, or migration instability that makes evidence unreliable.
- Loss of an incident/support owner during the active test window.
