from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CoachTraineeAssignment, User


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_full_registration_assessment_and_authorization_flow(client: TestClient, complete_assessment: dict) -> None:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "trainee@example.com", "password": "TraineePass123!", "first_name": "Test", "last_name": "Trainee", "invite_code": "FIT-DEMO-2026"},
    )
    assert registered.status_code == 201, registered.text
    trainee_token = registered.json()["access_token"]
    trainee_id = registered.json()["user"]["id"]

    coach_relationship = client.get("/api/v1/trainee/coach", headers=auth(trainee_token))
    assert coach_relationship.status_code == 200
    assert coach_relationship.json() == {
        "assignment_status": "active",
        "coach_id": coach_relationship.json()["coach_id"],
        "coach_name": "Test Coach",
        "coach_email": "coach@example.com",
        "coach_avatar_url": None,
    }

    assert client.get("/api/v1/coach/trainees", headers=auth(trainee_token)).status_code == 403
    saved = client.put("/api/v1/assessments/onboarding", headers=auth(trainee_token), json={"responses": complete_assessment})
    assert saved.status_code == 200, saved.text
    assert saved.json()["status"] == "draft"

    submitted = client.post("/api/v1/assessments/onboarding/submit", headers=auth(trainee_token))
    assert submitted.status_code == 200, submitted.text
    health = submitted.json()
    assert 0 <= health["overall_score"] <= 100
    assert health["scoring_version"] == "health-index-v1"
    assert len(health["components"]) == 10

    repeat = client.post("/api/v1/assessments/onboarding/submit", headers=auth(trainee_token))
    assert repeat.status_code == 200
    assert repeat.json()["id"] == health["id"]
    assert client.get("/api/v1/health-index/current", headers=auth(trainee_token)).json()["id"] == health["id"]

    coach_token = login(client, "coach@example.com", "CoachPass123!")
    roster = client.get("/api/v1/coach/trainees", headers=auth(coach_token))
    assert roster.status_code == 200
    assert [item["trainee_id"] for item in roster.json()] == [trainee_id]
    summary = roster.json()[0]
    assert summary["selected_goal"] == "general_health"
    assert summary["assessment_updated_at"] is not None
    assert summary["baseline_calculated_at"] is not None
    detail = client.get(f"/api/v1/coach/trainees/{trainee_id}", headers=auth(coach_token))
    assert detail.status_code == 200
    assert detail.json()["assessment"]["id"] == saved.json()["id"]
    assert detail.json()["assessment"]["status"] == "submitted"
    assert detail.json()["assessment"]["responses"]["selected_goal"] == "general_health"

    assert client.get("/api/v1/trainee/coach", headers=auth(coach_token)).status_code == 403

    other_token = login(client, "other@example.com", "OtherPass123!")
    forbidden = client.get(f"/api/v1/coach/trainees/{trainee_id}", headers=auth(other_token))
    assert forbidden.status_code == 403


def test_incomplete_submission_returns_field_errors(client: TestClient) -> None:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": "draft@example.com", "password": "TraineePass123!", "first_name": "Draft", "last_name": "Trainee", "invite_code": "FIT-DEMO-2026"},
    ).json()
    headers = auth(registered["access_token"])
    responses = {"activity_types": [], "palpitations": False, "shortness_of_breath": False, "chest_pain": False}
    assert client.put("/api/v1/assessments/onboarding", headers=headers, json={"responses": responses}).status_code == 200
    submitted = client.post("/api/v1/assessments/onboarding/submit", headers=headers)
    assert submitted.status_code == 422
    assert "weight_kg" in submitted.json()["detail"]["fields"]


def test_inactive_account_cannot_login(client: TestClient, db: Session) -> None:
    user = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert user is not None
    user.status = "inactive"
    db.commit()
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "coach@example.com", "password": "CoachPass123!"},
    )
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


def test_trainee_coach_endpoint_reports_inactive_relationship(
    client: TestClient, db: Session
) -> None:
    registered = client.post(
        "/api/v1/auth/register",
        json={
            "email": "inactive-relationship@example.com",
            "password": "TraineePass123!",
            "first_name": "Inactive",
            "last_name": "Relationship",
            "invite_code": "FIT-DEMO-2026",
        },
    )
    assert registered.status_code == 201, registered.text
    trainee_id = registered.json()["user"]["id"]
    assignment = db.scalar(
        select(CoachTraineeAssignment).where(
            CoachTraineeAssignment.trainee_id == UUID(trainee_id)
        )
    )
    assert assignment is not None
    assignment.status = "inactive"
    db.commit()

    relationship = client.get(
        "/api/v1/trainee/coach",
        headers=auth(registered.json()["access_token"]),
    )
    assert relationship.status_code == 200
    assert relationship.json() == {
        "assignment_status": "inactive",
        "coach_id": relationship.json()["coach_id"],
        "coach_name": "Test Coach",
        "coach_email": "coach@example.com",
        "coach_avatar_url": None,
    }
