"""End-to-end coach exercise search: synonym-aware ranking + preserved authorization."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _create_published(client, headers, *, slug, name, movement_pattern, equipment,
                      primary, secondary=()):
    payload = {
        "slug": slug,
        "name": name,
        "description": "Search fixture.",
        "instructions": "Move with control and record completed work.",
        "tracking_mode": "repetitions_and_load",
        "category": "strength",
        "movement_pattern": movement_pattern,
        "equipment": list(equipment),
        "primary_muscle_groups": list(primary),
        "secondary_muscle_groups": list(secondary),
        "unilateral": False,
        "safety_cues": ["Stop if the movement causes unusual discomfort."],
    }
    created = client.post("/api/v1/coach/exercises", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    exercise_id = created.json()["id"]
    published = client.post(
        f"/api/v1/coach/exercises/{exercise_id}/publish", headers=headers
    )
    assert published.status_code == 200, published.text
    return exercise_id


def _names(client, headers, **params):
    res = client.get("/api/v1/coach/exercises", params=params, headers=headers)
    assert res.status_code == 200, res.text
    names = []
    for item in res.json():
        version = item["published_version"] or item["draft_version"]
        names.append(version["name"])
    return names


def test_search_matches_muscle_synonyms_and_facets(client: TestClient, db: Session):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    headers = auth(login(client, coach.email, "CoachPass123!"))

    _create_published(client, headers, slug="zz-alpha-press", name="Zz Alpha Press",
                      movement_pattern="horizontal push", equipment=["dumbbell"],
                      primary=["chest"], secondary=["triceps"])
    _create_published(client, headers, slug="zz-beta-squat", name="Zz Beta Squat",
                      movement_pattern="squat", equipment=["barbell"],
                      primary=["quadriceps"], secondary=["glutes"])

    # A colloquial muscle term finds the exercise by its real metadata, not its name.
    pecs = _names(client, headers, search="pecs")
    assert "Zz Alpha Press" in pecs
    assert "Zz Beta Squat" not in pecs

    quads = _names(client, headers, search="quads")
    assert "Zz Beta Squat" in quads
    assert "Zz Alpha Press" not in quads

    # Facets compose and are synonym-aware.
    assert "Zz Alpha Press" in _names(client, headers, muscle="chest")
    assert "Zz Alpha Press" in _names(client, headers, equipment="dumbbell")
    assert "Zz Beta Squat" not in _names(client, headers, equipment="dumbbell")


def test_search_never_leaks_a_private_exercise_across_coaches(
    client: TestClient, db: Session
):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    other = db.scalar(select(User).where(User.email == "other@example.com"))
    assert coach is not None and other is not None
    coach_headers = auth(login(client, coach.email, "CoachPass123!"))
    other_headers = auth(login(client, other.email, "OtherPass123!"))

    _create_published(client, coach_headers, slug="secret-adductor-lift",
                      name="Secret Adductor Lift", movement_pattern="hinge",
                      equipment=["cable"], primary=["adductors"])

    # The owner finds it by muscle synonym; another coach never does, through any facet.
    assert "Secret Adductor Lift" in _names(client, coach_headers, search="inner thigh")
    assert "Secret Adductor Lift" not in _names(client, other_headers, search="inner thigh")
    assert "Secret Adductor Lift" not in _names(client, other_headers, muscle="adductors")
    assert "Secret Adductor Lift" not in _names(client, other_headers, search="Secret Adductor")
