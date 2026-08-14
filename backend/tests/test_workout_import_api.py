"""End-to-end workout-import preview: parse + match against the coach library."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _publish(client, headers, *, slug, name, tracking_mode="repetitions_and_load"):
    payload = {
        "slug": slug, "name": name, "description": "Import fixture.",
        "instructions": "Move with control.", "tracking_mode": tracking_mode,
        "category": "strength", "movement_pattern": "squat", "equipment": ["dumbbell"],
        "primary_muscle_groups": ["quadriceps"], "secondary_muscle_groups": [],
        "unilateral": False, "safety_cues": ["Stop if it hurts."],
    }
    created = client.post("/api/v1/coach/exercises", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    published = client.post(
        f"/api/v1/coach/exercises/{created.json()['id']}/publish", headers=headers
    )
    assert published.status_code == 200, published.text


def test_preview_matches_known_exercises_and_flags_unknown(client: TestClient, db: Session):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    headers = _auth(_login(client, coach.email, "CoachPass123!"))
    _publish(client, headers, slug="zz-import-squat", name="Zz Import Squat")

    csv = (
        "exercise,sets,reps,load,rest\n"
        "Zz Import Squat,3,8-10,40,90\n"
        "Totally Unknown Move,3,10,,60\n"
    )
    res = client.post("/api/v1/coach/workout-imports/preview",
                      json={"content": csv, "template_name": "My import"}, headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["template_name"] == "My import"
    assert body["summary"]["total"] == 2

    matched = next(r for r in body["rows"] if r["exercise_name"] == "Zz Import Squat")
    assert matched["status"] == "matched"
    assert matched["matched"]["exercise_version_id"]
    assert matched["prescription"]["repetitions_min"] == 8
    assert matched["prescription"]["target_load_original_value"] == "40"
    assert matched["sets"] == 3

    unknown = next(r for r in body["rows"] if r["exercise_name"] == "Totally Unknown Move")
    assert unknown["status"] == "not_found"
    assert unknown["matched"] is None


def test_preview_reports_a_friendly_error_for_a_missing_exercise_column(
    client: TestClient, db: Session
):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    headers = _auth(_login(client, coach.email, "CoachPass123!"))
    res = client.post("/api/v1/coach/workout-imports/preview",
                      json={"content": "sets,reps\n3,10"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["file_errors"]
    assert res.json()["rows"] == []


def test_preview_never_matches_another_coachs_private_exercise(
    client: TestClient, db: Session
):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    other = db.scalar(select(User).where(User.email == "other@example.com"))
    assert coach is not None and other is not None
    coach_headers = _auth(_login(client, coach.email, "CoachPass123!"))
    other_headers = _auth(_login(client, other.email, "OtherPass123!"))
    _publish(client, coach_headers, slug="secret-import-lift", name="Secret Import Lift")

    csv = "exercise,sets,reps\nSecret Import Lift,3,10\n"
    res = client.post("/api/v1/coach/workout-imports/preview",
                      json={"content": csv}, headers=other_headers)
    assert res.status_code == 200
    assert res.json()["rows"][0]["status"] == "not_found"
