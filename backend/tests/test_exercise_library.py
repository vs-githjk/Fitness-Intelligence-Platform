import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.orm import Session

from app.exercise_services import exercise_content_hash
from app.models import (
    Exercise,
    ExerciseScope,
    ExerciseTrackingMode,
    ExerciseVersion,
    ExerciseVersionStatus,
    Role,
    User,
)
from scripts.seed import PRIVATE_EXERCISES, SYSTEM_EXERCISES, seed_exercise_library


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def exercise_payload(
    *,
    slug: str = "coach-custom-row",
    name: str = "Coach custom row",
    tracking_mode: str = "repetitions_and_load",
) -> dict:
    return {
        "slug": slug,
        "name": name,
        "description": "Private exercise used by one coach.",
        "instructions": "Use a controlled range and record only completed repetitions.",
        "tracking_mode": tracking_mode,
        "category": "strength",
        "movement_pattern": "horizontal pull",
        "equipment": ["cable machine"],
        "primary_muscle_groups": ["back"],
        "secondary_muscle_groups": ["biceps"],
        "unilateral": False,
        "safety_cues": ["Stop if the movement causes unusual discomfort."],
        "image_url": "https://assets.example.com/exercises/row.jpg",
        "thumbnail_url": "https://assets.example.com/exercises/row-thumb.jpg",
    }


def draft_payload(**overrides: object) -> dict:
    payload = exercise_payload()
    payload.pop("slug")
    payload.update(overrides)
    return payload


def test_visibility_ownership_and_system_mutation_denial(
    client: TestClient, db: Session
) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    other = db.scalar(select(User).where(User.email == "other@example.com"))
    assert coach is not None and other is not None
    seed_exercise_library(db, coach)
    seed_exercise_library(db, other)
    coach_headers = auth(login(client, coach.email, "CoachPass123!"))
    other_headers = auth(login(client, other.email, "OtherPass123!"))

    visible = client.get("/api/v1/coach/exercises", headers=coach_headers)
    assert visible.status_code == 200
    assert len([item for item in visible.json() if item["scope"] == "system"]) == len(
        SYSTEM_EXERCISES
    )
    assert len(
        [item for item in visible.json() if item["scope"] == "coach_private"]
    ) == len(PRIVATE_EXERCISES)

    private = next(item for item in visible.json() if item["scope"] == "coach_private")
    assert client.get(
        f"/api/v1/coach/exercises/{private['id']}", headers=other_headers
    ).status_code == 404

    system = next(item for item in visible.json() if item["scope"] == "system")
    system_paths = [
        ("PUT", f"/api/v1/coach/exercises/{system['id']}/draft"),
        ("POST", f"/api/v1/coach/exercises/{system['id']}/publish"),
        ("POST", f"/api/v1/coach/exercises/{system['id']}/revisions"),
        ("POST", f"/api/v1/coach/exercises/{system['id']}/archive"),
    ]
    for method, path in system_paths:
        response = client.request(
            method,
            path,
            headers=coach_headers,
            json=draft_payload() if method == "PUT" else None,
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "system_exercise_read_only"


def test_private_draft_publish_revision_archive_lifecycle(
    client: TestClient, db: Session
) -> None:
    coach_headers = auth(login(client, "coach@example.com", "CoachPass123!"))
    created = client.post(
        "/api/v1/coach/exercises", headers=coach_headers, json=exercise_payload()
    )
    assert created.status_code == 201, created.text
    exercise_id = created.json()["id"]
    assert created.json()["draft_version"]["version_number"] == 1
    assert created.json()["published_version"] is None

    updated = client.put(
        f"/api/v1/coach/exercises/{exercise_id}/draft",
        headers=coach_headers,
        json=draft_payload(name="Updated private row"),
    )
    assert updated.status_code == 200
    assert updated.json()["draft_version"]["name"] == "Updated private row"

    published = client.post(
        f"/api/v1/coach/exercises/{exercise_id}/publish", headers=coach_headers
    )
    assert published.status_code == 200
    published_v1 = published.json()["published_version"]
    assert published_v1["status"] == "published"
    assert len(published_v1["content_hash"]) == 64
    assert published.json()["draft_version"] is None

    assert client.put(
        f"/api/v1/coach/exercises/{exercise_id}/draft",
        headers=coach_headers,
        json=draft_payload(name="Illegal direct edit"),
    ).status_code == 409

    revision = client.post(
        f"/api/v1/coach/exercises/{exercise_id}/revisions", headers=coach_headers
    )
    assert revision.status_code == 201
    assert revision.json()["draft_version"]["version_number"] == 2
    assert revision.json()["draft_version"]["name"] == published_v1["name"]

    changed_revision = client.put(
        f"/api/v1/coach/exercises/{exercise_id}/draft",
        headers=coach_headers,
        json=draft_payload(name="Version two row"),
    )
    assert changed_revision.status_code == 200
    stored_v1 = db.get(ExerciseVersion, uuid.UUID(published_v1["id"]))
    assert stored_v1 is not None
    assert stored_v1.name == "Updated private row"
    assert stored_v1.content_hash == published_v1["content_hash"]

    archived = client.post(
        f"/api/v1/coach/exercises/{exercise_id}/archive", headers=coach_headers
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    assert client.put(
        f"/api/v1/coach/exercises/{exercise_id}/draft",
        headers=coach_headers,
        json=draft_payload(),
    ).status_code == 409
    assert all(
        item["id"] != exercise_id
        for item in client.get("/api/v1/coach/exercises", headers=coach_headers).json()
    )
    history = client.get(
        "/api/v1/coach/exercises?include_archived=true", headers=coach_headers
    )
    assert any(item["id"] == exercise_id for item in history.json())


def test_tracking_modes_urls_filters_and_validation(client: TestClient, db: Session) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    seed_exercise_library(db, coach)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    expected = {item.value for item in ExerciseTrackingMode}
    stored = set(
        db.scalars(
            select(ExerciseVersion.tracking_mode).where(
                ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED
            )
        ).all()
    )
    assert expected <= {item.value for item in stored}

    filtered = client.get(
        "/api/v1/coach/exercises?tracking_mode=duration", headers=headers
    )
    assert filtered.status_code == 200
    assert all(
        (item["published_version"] or item["draft_version"])["tracking_mode"]
        == "duration"
        for item in filtered.json()
    )
    invalid_mode = client.post(
        "/api/v1/coach/exercises",
        headers=headers,
        json=exercise_payload(tracking_mode="timed"),
    )
    assert invalid_mode.status_code == 422
    insecure_image = client.post(
        "/api/v1/coach/exercises",
        headers=headers,
        json={**exercise_payload(slug="unsafe-image"), "image_url": "http://example.com/a.jpg"},
    )
    assert insecure_image.status_code == 422


def test_seed_is_idempotent_and_private_per_owner(db: Session) -> None:
    coaches = db.scalars(select(User).where(User.role == Role.COACH)).all()
    assert len(coaches) == 2
    for coach in coaches:
        seed_exercise_library(db, coach)
        seed_exercise_library(db, coach)
    assert db.scalar(
        select(func.count(Exercise.id)).where(Exercise.scope == ExerciseScope.SYSTEM)
    ) == len(SYSTEM_EXERCISES)
    assert db.scalar(
        select(func.count(Exercise.id)).where(Exercise.scope == ExerciseScope.COACH_PRIVATE)
    ) == len(PRIVATE_EXERCISES) * len(coaches)
    assert db.scalar(select(func.count(ExerciseVersion.id))) == len(SYSTEM_EXERCISES) + len(
        PRIVATE_EXERCISES
    ) * len(coaches)


def test_content_hash_is_deterministic() -> None:
    values = draft_payload()
    first = ExerciseVersion(
        exercise_id=uuid.uuid4(),
        version_number=1,
        status=ExerciseVersionStatus.DRAFT,
        **values,
    )
    second = ExerciseVersion(
        exercise_id=uuid.uuid4(),
        version_number=9,
        status=ExerciseVersionStatus.DRAFT,
        **values,
    )
    assert exercise_content_hash(first) == exercise_content_hash(second)
    second.name = "Different"
    assert exercise_content_hash(first) != exercise_content_hash(second)


@pytest.mark.parametrize("target", ["20260716_0005", "head"])
def test_exercise_migration_upgrade_and_downgrade(tmp_path: Path, target: str) -> None:
    database_path = tmp_path / f"exercise-{target}.db"
    environment = {
        **os.environ,
        "MIGRATION_DATABASE_URL": f"sqlite:///{database_path}",
    }
    backend_dir = Path(__file__).resolve().parents[1]

    def alembic(*arguments: str) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=backend_dir,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    # The initial revision uses live metadata. Remove the new tables it creates so
    # this test reproduces a real deployed 0004 database before applying 0005.
    alembic("upgrade", "20260716_0004")
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE exercise_versions"))
        connection.execute(text("DROP TABLE exercises"))
    alembic("upgrade", target)
    assert {"exercises", "exercise_versions"} <= set(inspect(engine).get_table_names())
    alembic("downgrade", "20260716_0004")
    assert "exercises" not in inspect(engine).get_table_names()
    assert "exercise_versions" not in inspect(engine).get_table_names()
    alembic("upgrade", "head")
    assert {"exercises", "exercise_versions"} <= set(inspect(engine).get_table_names())
