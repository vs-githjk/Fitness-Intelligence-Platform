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
    OnboardingAssessment,
    RiskAlert,
    Role,
    TraineeProfile,
    User,
)
from app.security import ALGORITHM
from scripts.seed import DEMO_SCENARIOS, seed_public_demo_workspace


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


def test_demo_mutations_are_rejected_and_normal_mutations_still_work(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _demo_users(db)
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
    for response in (profile, assessment, check_in, invite):
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
