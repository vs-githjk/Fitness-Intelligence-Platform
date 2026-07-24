from datetime import UTC, datetime

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.models import (
    AssessmentStatus,
    CoachTraineeAssignment,
    DailyCheckIn,
    DailyScoreSnapshot,
    Exercise,
    ExerciseScope,
    ExerciseVersionStatus,
    OnboardingAssessment,
    RiskAlert,
    Role,
    TraineeProfile,
    User,
    WorkoutReadinessContext,
    WorkoutSafetyReport,
    WorkoutTemplate,
)
from app.security import ALGORITHM
from scripts.seed import (
    DEMO_SCENARIOS,
    seed_exercise_library,
    seed_public_demo_workspace,
    seed_workout_templates,
)


def _demo_users(db: Session) -> tuple[User, User]:
    coach = User(
        email=settings.demo_coach_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Coach",
        role=Role.COACH,
        is_demo=True,
    )
    trainee = User(
        email=settings.demo_trainee_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Trainee",
        role=Role.TRAINEE,
        is_demo=True,
    )
    db.add_all([coach, trainee])
    db.flush()
    db.add(TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"))
    db.add(
        CoachTraineeAssignment(
            coach_id=coach.id,
            trainee_id=trainee.id,
            accepted_at=datetime.now(UTC),
        )
    )
    db.commit()
    return coach, trainee


def _demo_session(client: TestClient, role: str) -> dict:
    response = client.post("/api/v1/auth/demo-session", json={"role": role})
    assert response.status_code == 200, response.text
    return response.json()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_demo_mode_disabled_and_invalid_role(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "demo_mode_enabled", False)
    disabled = client.post("/api/v1/auth/demo-session", json={"role": "trainee"})
    assert disabled.status_code == 503
    assert disabled.json()["detail"]["code"] == "demo_unavailable"
    invalid = client.post("/api/v1/auth/demo-session", json={"role": "administrator"})
    assert invalid.status_code == 422


def test_missing_demo_account_is_unavailable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    response = client.post("/api/v1/auth/demo-session", json={"role": "coach"})
    assert response.status_code == 503
    assert settings.demo_coach_email not in response.text


def test_demo_sessions_use_normal_roles_and_short_lived_tokens(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    coach, trainee = _demo_users(db)
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    monkeypatch.setattr(settings, "demo_session_minutes", 15)

    coach_session = _demo_session(client, "coach")
    trainee_session = _demo_session(client, "trainee")
    assert coach_session["user"] == {
        "id": str(coach.id),
        "email": coach.email,
        "first_name": "Demo",
        "last_name": "Coach",
        "role": "coach",
        "is_demo": True,
    }
    assert trainee_session["user"]["id"] == str(trainee.id)
    assert trainee_session["user"]["is_demo"] is True

    relationship = client.get(
        "/api/v1/trainee/coach",
        headers=_auth(trainee_session["access_token"]),
    )
    assert relationship.status_code == 200
    assert relationship.json() == {
        "assignment_status": "active",
        "coach_id": str(coach.id),
        "coach_name": "Demo Coach",
        "coach_email": coach.email,
        "coach_avatar_url": None,
    }

    payload = jwt.decode(
        coach_session["access_token"], settings.jwt_secret, algorithms=[ALGORITHM]
    )
    assert 14 * 60 <= payload["exp"] - payload["iat"] <= 15 * 60
    assert client.get(
        "/api/v1/coach/trainees", headers=_auth(trainee_session["access_token"])
    ).status_code == 403
    assert client.get(
        "/api/v1/trainee/profile", headers=_auth(coach_session["access_token"])
    ).status_code == 403


def test_demo_coach_roster_contains_only_assigned_synthetic_trainees(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    demo_coach, demo_trainee = _demo_users(db)
    normal_coach = User(
        email="normal-coach@example.com",
        password_hash="not-used",
        first_name="Normal",
        last_name="Coach",
        role=Role.COACH,
    )
    normal_trainee = User(
        email="normal-trainee@example.com",
        password_hash="not-used",
        first_name="Normal",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add_all([normal_coach, normal_trainee])
    db.flush()
    db.add(TraineeProfile(user_id=normal_trainee.id, timezone="UTC"))
    db.add(
        CoachTraineeAssignment(
            coach_id=normal_coach.id,
            trainee_id=normal_trainee.id,
            accepted_at=datetime.now(UTC),
        )
    )
    db.commit()
    monkeypatch.setattr(settings, "demo_mode_enabled", True)

    demo_token = _demo_session(client, "coach")["access_token"]
    roster = client.get("/api/v1/coach/trainees", headers=_auth(demo_token))

    assert roster.status_code == 200
    assert {item["trainee_id"] for item in roster.json()} == {str(demo_trainee.id)}
    assert all(item["trainee_id"] != str(normal_trainee.id) for item in roster.json())
    assert demo_coach.id != normal_coach.id


def test_demo_mutations_are_rejected_and_normal_mutations_still_work(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    demo_coach, _ = _demo_users(db)
    seed_exercise_library(db, demo_coach)
    seed_workout_templates(db, demo_coach)
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    coach_token = _demo_session(client, "coach")["access_token"]
    trainee_token = _demo_session(client, "trainee")["access_token"]

    profile = client.put(
        "/api/v1/trainee/profile",
        headers=_auth(trainee_token),
        json={"timezone": "UTC"},
    )
    assessment = client.put(
        "/api/v1/assessments/onboarding",
        headers=_auth(trainee_token),
        json={"responses": {}},
    )
    check_in = client.put(
        "/api/v1/check-ins/today",
        headers=_auth(trainee_token),
        json={
            "sleep_hours": 7.5,
            "sleep_quality": 4,
            "wake_refreshed": True,
            "soreness": 2,
            "fatigue": 2,
            "stress": 3,
            "steps": 8000,
            "exercised": False,
            "activity_types": [],
            "water_liters": 2.3,
            "overall_feeling": "good",
        },
    )
    invite = client.post(
        "/api/v1/coach/invites",
        headers=_auth(coach_token),
        json={"expires_in_days": 1},
    )
    exercise_payload = {
        "slug": "demo-mutation",
        "name": "Demo mutation",
        "description": None,
        "instructions": "This otherwise-valid content must not be saved.",
        "tracking_mode": "repetitions_only",
        "category": "strength",
        "movement_pattern": "push",
        "equipment": [],
        "primary_muscle_groups": ["chest"],
        "secondary_muscle_groups": [],
        "unilateral": False,
        "safety_cues": [],
        "image_url": None,
        "thumbnail_url": None,
    }
    system_exercise = db.scalar(
        select(Exercise).where(Exercise.scope == ExerciseScope.SYSTEM)
    )
    assert system_exercise is not None
    exercise_create = client.post(
        "/api/v1/coach/exercises",
        headers=_auth(coach_token),
        json=exercise_payload,
    )
    exercise_draft = client.put(
        f"/api/v1/coach/exercises/{system_exercise.id}/draft",
        headers=_auth(coach_token),
        json={key: value for key, value in exercise_payload.items() if key != "slug"},
    )
    exercise_publish = client.post(
        f"/api/v1/coach/exercises/{system_exercise.id}/publish",
        headers=_auth(coach_token),
    )
    exercise_revision = client.post(
        f"/api/v1/coach/exercises/{system_exercise.id}/revisions",
        headers=_auth(coach_token),
    )
    exercise_archive = client.post(
        f"/api/v1/coach/exercises/{system_exercise.id}/archive",
        headers=_auth(coach_token),
    )
    exercise_version = next(
        version
        for version in system_exercise.versions
        if version.status == ExerciseVersionStatus.PUBLISHED
    )
    template = db.scalar(
        select(WorkoutTemplate).where(
            WorkoutTemplate.owner_coach_id == demo_coach.id
        )
    )
    assert template is not None
    template_payload = {
        "name": "Blocked demo template",
        "description": None,
        "goal_tags": ["strength"],
        "estimated_duration_minutes": 30,
        "target_session_rpe": 6,
        "coach_notes": None,
        "trainee_instructions": None,
        "exercises": [
            {
                "exercise_version_id": str(exercise_version.id),
                "section": "main",
                "display_order": 1,
                "coach_notes": None,
                "trainee_instructions": None,
                "sets": [
                    {
                        "set_number": 1,
                        "set_type": "working",
                        "repetitions_min": 8,
                        "repetitions_max": 10,
                        "target_load_original_value": 10,
                        "target_load_original_unit": "kg",
                    }
                ],
            }
        ],
    }
    template_create = client.post(
        "/api/v1/coach/workout-templates",
        headers=_auth(coach_token),
        json=template_payload,
    )
    template_draft = client.put(
        f"/api/v1/coach/workout-templates/{template.id}/draft",
        headers=_auth(coach_token),
        json={**template_payload, "expected_draft_revision": 1},
    )
    template_publish = client.post(
        f"/api/v1/coach/workout-templates/{template.id}/publish",
        headers=_auth(coach_token),
    )
    template_revision = client.post(
        f"/api/v1/coach/workout-templates/{template.id}/revisions",
        headers=_auth(coach_token),
    )
    template_archive = client.post(
        f"/api/v1/coach/workout-templates/{template.id}/archive",
        headers=_auth(coach_token),
    )
    for response in (
        profile,
        assessment,
        check_in,
        invite,
        exercise_create,
        exercise_draft,
        exercise_publish,
        exercise_revision,
        exercise_archive,
        template_create,
        template_draft,
        template_publish,
        template_revision,
        template_archive,
    ):
        assert response.status_code == 403
        assert response.json()["detail"] == {
            "code": "demo_read_only",
            "message": "Demo accounts are read-only.",
        }

    normal_coach = client.post(
        "/api/v1/auth/login",
        json={"email": "coach@example.com", "password": "CoachPass123!"},
    ).json()
    allowed = client.post(
        "/api/v1/coach/invites",
        headers=_auth(normal_coach["access_token"]),
        json={"expires_in_days": 1},
    )
    assert allowed.status_code == 201


def test_public_demo_seed_is_idempotent_and_scenario_rich(db: Session) -> None:
    config = Settings(
        _env_file=None,
        app_env="test",
        seed_demo_data=True,
        demo_mode_enabled=True,
    )
    now = datetime(2026, 7, 16, 8, tzinfo=UTC)
    seed_public_demo_workspace(db, config, now)

    demo_user_count = db.scalar(select(func.count(User.id)).where(User.is_demo.is_(True)))
    assignment_count = db.scalar(
        select(func.count(CoachTraineeAssignment.id)).join(
            User, CoachTraineeAssignment.trainee_id == User.id
        ).where(User.is_demo.is_(True))
    )
    submitted_count = db.scalar(
        select(func.count(OnboardingAssessment.id))
        .join(User, OnboardingAssessment.trainee_id == User.id)
        .where(User.is_demo.is_(True), OnboardingAssessment.status == AssessmentStatus.SUBMITTED)
    )
    check_in_count = db.scalar(
        select(func.count(DailyCheckIn.id))
        .join(User, DailyCheckIn.trainee_id == User.id)
        .where(User.is_demo.is_(True))
    )
    score_count = db.scalar(
        select(func.count(DailyScoreSnapshot.id))
        .join(User, DailyScoreSnapshot.trainee_id == User.id)
        .where(User.is_demo.is_(True))
    )
    alert_count = db.scalar(
        select(func.count(RiskAlert.id))
        .join(User, RiskAlert.trainee_id == User.id)
        .where(User.is_demo.is_(True), RiskAlert.status == "open")
    )
    primary_alert_count = db.scalar(
        select(func.count(RiskAlert.id))
        .join(User, RiskAlert.trainee_id == User.id)
        .where(
            User.email == config.demo_trainee_email,
            User.is_demo.is_(True),
            RiskAlert.status == "open",
        )
    )

    assert demo_user_count == len(DEMO_SCENARIOS) + 1
    assert assignment_count == len(DEMO_SCENARIOS)
    assert submitted_count == len(DEMO_SCENARIOS)
    assert check_in_count is not None and 100 <= check_in_count < 147
    assert score_count == check_in_count
    assert alert_count is not None and alert_count >= 1
    assert primary_alert_count is not None and primary_alert_count >= 1
    safety_statuses = set(
        db.scalars(select(WorkoutSafetyReport.status).join(User).where(User.is_demo.is_(True))).all()
    )
    assert safety_statuses == {"open", "acknowledged", "resolved"}
    assert db.scalar(select(func.count(WorkoutSafetyReport.id))) == 4
    readiness_availability = set(
        db.scalars(
            select(WorkoutReadinessContext.is_available)
            .join(User)
            .where(User.is_demo.is_(True))
        ).all()
    )
    assert readiness_availability == {True, False}

    first_counts = (demo_user_count, assignment_count, submitted_count, check_in_count)
    seed_public_demo_workspace(db, config, now)
    second_counts = (
        db.scalar(select(func.count(User.id)).where(User.is_demo.is_(True))),
        db.scalar(
            select(func.count(CoachTraineeAssignment.id)).join(
                User, CoachTraineeAssignment.trainee_id == User.id
            ).where(User.is_demo.is_(True))
        ),
        db.scalar(
            select(func.count(OnboardingAssessment.id))
            .join(User, OnboardingAssessment.trainee_id == User.id)
            .where(User.is_demo.is_(True), OnboardingAssessment.status == AssessmentStatus.SUBMITTED)
        ),
        db.scalar(
            select(func.count(DailyCheckIn.id))
            .join(User, DailyCheckIn.trainee_id == User.id)
            .where(User.is_demo.is_(True))
        ),
    )
    assert second_counts == first_counts
    assert db.scalar(select(func.count(WorkoutSafetyReport.id))) == 4
