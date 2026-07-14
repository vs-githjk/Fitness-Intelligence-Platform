import uuid
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

import app.daily_services as daily_services
from app.daily_services import local_today, save_today_check_in
from app.models import DailyCheckIn, DailyScoreSnapshot, User
from app.schemas import DailyCheckInData


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def daily_payload() -> dict:
    return {
        "sleep_hours": 7.5,
        "sleep_quality": 4,
        "wake_refreshed": True,
        "soreness": 3,
        "fatigue": 3,
        "stress": 4,
        "steps": 8200,
        "exercised": True,
        "exercise_minutes": 45,
        "session_rpe": 6,
        "activity_types": ["walking", "strength_training"],
        "water_liters": 2.4,
        "calories_consumed": 2100,
        "protein_grams": 100,
        "nutrition_adherence": 85,
        "overall_feeling": "good",
        "note": "Normal synthetic test note.",
    }


def register_trainee(client: TestClient, email: str = "daily@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "TraineePass123!",
            "first_name": "Daily",
            "last_name": "Trainee",
            "invite_code": "FIT-DEMO-2026",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_retrieve_edit_score_and_history(
    client: TestClient, complete_assessment: dict, db: Session
) -> None:
    registered = register_trainee(client)
    headers = auth(registered["access_token"])
    client.put(
        "/api/v1/assessments/onboarding",
        headers=headers,
        json={"responses": complete_assessment},
    )
    client.post("/api/v1/assessments/onboarding/submit", headers=headers)
    created = client.put("/api/v1/check-ins/today", headers=headers, json=daily_payload())
    assert created.status_code == 200, created.text
    check_in_id = created.json()["id"]
    assert client.get("/api/v1/check-ins/today", headers=headers).json()["id"] == check_in_id
    score_response = client.get("/api/v1/daily-scores/today", headers=headers)
    assert score_response.status_code == 200, score_response.text
    score = score_response.json()
    assert score["scoring_version"] == "daily-intelligence-v1"
    assert 0 <= score["readiness_score"] <= 100
    assert score["components"]
    edited_payload = {**daily_payload(), "steps": 10000, "note": "Edited today."}
    edited = client.put("/api/v1/check-ins/today", headers=headers, json=edited_payload)
    assert edited.status_code == 200
    assert edited.json()["id"] == check_in_id
    assert edited.json()["steps"] == 10000
    assert db.scalar(select(func.count(DailyCheckIn.id))) == 1
    assert db.scalar(select(func.count(DailyScoreSnapshot.id))) == 1
    assert len(client.get("/api/v1/check-ins?days=7", headers=headers).json()) == 1
    trends = client.get("/api/v1/daily-scores/trends?days=7", headers=headers)
    assert trends.status_code == 200
    recovery = next(item for item in trends.json()["series"] if item["key"] == "recovery_score")
    assert len(recovery["points"]) == 7
    assert sum(point["missing"] for point in recovery["points"]) == 6
    assert client.get("/api/v1/daily-scores?days=365", headers=headers).status_code == 422


def test_conditional_validation_and_unauthorized(client: TestClient) -> None:
    registered = register_trainee(client, "validation@example.com")
    payload = {**daily_payload(), "exercise_minutes": None}
    invalid = client.put(
        "/api/v1/check-ins/today", headers=auth(registered["access_token"]), json=payload
    )
    assert invalid.status_code == 422
    assert client.get("/api/v1/check-ins/today").status_code == 401


def test_timezone_date_resolution(client: TestClient, db: Session) -> None:
    registered = register_trainee(client, "timezone@example.com")
    trainee_id = uuid.UUID(registered["user"]["id"])
    headers = auth(registered["access_token"])
    updated = client.put(
        "/api/v1/trainee/profile",
        headers=headers,
        json={"timezone": "America/Los_Angeles"},
    )
    assert updated.status_code == 200
    local_date, timezone_name = local_today(
        db, trainee_id, datetime(2026, 7, 14, 2, 0, tzinfo=UTC)
    )
    assert str(local_date) == "2026-07-13"
    assert timezone_name == "America/Los_Angeles"
    invalid = client.put(
        "/api/v1/trainee/profile", headers=headers, json={"timezone": "Not/AZone"}
    )
    assert invalid.status_code == 422


def test_coach_assignment_protects_daily_history(client: TestClient) -> None:
    registered = register_trainee(client, "coach-daily@example.com")
    trainee_id = registered["user"]["id"]
    headers = auth(registered["access_token"])
    assert client.put("/api/v1/check-ins/today", headers=headers, json=daily_payload()).status_code == 200
    coach_headers = auth(login(client, "coach@example.com", "CoachPass123!"))
    assigned = client.get(
        f"/api/v1/coach/trainees/{trainee_id}/daily-scores?days=7",
        headers=coach_headers,
    )
    assert assigned.status_code == 200 and len(assigned.json()) == 1
    latest = client.get(
        f"/api/v1/coach/trainees/{trainee_id}/daily-score-latest",
        headers=coach_headers,
    )
    assert latest.status_code == 200
    assert latest.json()["recommendations"]
    other_headers = auth(login(client, "other@example.com", "OtherPass123!"))
    forbidden = client.get(
        f"/api/v1/coach/trainees/{trainee_id}/check-ins?days=7",
        headers=other_headers,
    )
    assert forbidden.status_code == 403
    forbidden_latest = client.get(
        f"/api/v1/coach/trainees/{trainee_id}/daily-score-latest",
        headers=other_headers,
    )
    assert forbidden_latest.status_code == 403


def test_check_in_transaction_rolls_back_when_scoring_fails(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    registered = register_trainee(client, "rollback@example.com")
    trainee = db.get(User, uuid.UUID(registered["user"]["id"]))

    def fail_scoring(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("synthetic scoring failure")

    monkeypatch.setattr(daily_services, "calculate_and_store_daily_score", fail_scoring)
    with pytest.raises(RuntimeError, match="synthetic scoring failure"):
        save_today_check_in(db, trainee, DailyCheckInData.model_validate(daily_payload()))
    assert db.scalar(select(func.count(DailyCheckIn.id))) == 0
