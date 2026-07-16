import copy
import os
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.models import (
    ProgramSession,
    ProgramWeek,
    Role,
    TrainingProgramVersion,
    User,
    WorkoutTemplate,
    WorkoutTemplateStatus,
    WorkoutTemplateVersion,
    WorkoutTemplateVersionStatus,
)
from app.security import create_access_token, hash_password
from app.training_program_services import training_program_content_hash
from scripts.seed import (
    seed_exercise_library,
    seed_training_programs,
    seed_workout_templates,
)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def published_template(db: Session, coach: User) -> WorkoutTemplateVersion:
    version = db.scalar(
        select(WorkoutTemplateVersion)
        .join(
            WorkoutTemplate,
            WorkoutTemplate.id == WorkoutTemplateVersion.workout_template_id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == coach.id,
            WorkoutTemplate.status == WorkoutTemplateStatus.ACTIVE,
            WorkoutTemplateVersion.version_status == WorkoutTemplateVersionStatus.PUBLISHED,
        )
        .order_by(WorkoutTemplateVersion.version_number)
    )
    assert version is not None
    return version


def program_payload(template: WorkoutTemplateVersion, name: str = "Four week strength") -> dict:
    weeks = []
    for number in range(1, 5):
        sessions = [
            {
                "workout_template_version_id": str(template.id),
                "weekday": "monday",
                "display_order": 1,
                "required": True,
                "planned_duration_override_minutes": 50,
                "target_session_rpe_override": 7,
                "coach_notes": "Coach context",
                "trainee_instructions": "Move with control",
            }
        ]
        if number == 1:
            sessions.append(
                {
                    "workout_template_version_id": str(template.id),
                    "weekday": "monday",
                    "display_order": 2,
                    "required": False,
                    "planned_duration_override_minutes": None,
                    "target_session_rpe_override": None,
                    "coach_notes": None,
                    "trainee_instructions": "Optional technique work",
                }
            )
        weeks.append(
            {
                "week_number": number,
                "label": "Deload" if number == 4 else f"Build {number}",
                "coach_notes": "Coach-authored deload" if number == 4 else None,
                "is_deload": number == 4,
                "sessions": sessions,
            }
        )
    return {
        "name": name,
        "description": "A deterministic reusable training structure.",
        "goal_tags": ["strength", "general_health", "strength"],
        "duration_weeks": 4,
        "coach_notes": "Private program note",
        "trainee_instructions": "Complete required workouts first.",
        "weeks": weeks,
    }


def setup_program_data(db: Session) -> tuple[User, WorkoutTemplateVersion]:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    seed_exercise_library(db, coach)
    seed_workout_templates(db, coach)
    return coach, published_template(db, coach)


def test_program_lifecycle_concurrency_pinning_and_immutability(
    client: TestClient, db: Session
) -> None:
    coach, template = setup_program_data(db)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    payload = program_payload(template)
    created = client.post("/api/v1/coach/training-programs", headers=headers, json=payload)
    assert created.status_code == 201, created.text
    program_id = created.json()["id"]
    draft = created.json()["draft_version"]
    assert draft["duration_weeks"] == 4
    assert len(draft["weeks"]) == 4
    assert draft["weeks"][3]["is_deload"] is True
    assert draft["weeks"][0]["sessions"][1]["required"] is False
    assert draft["weeks"][0]["sessions"][0]["workout_template_version_id"] == str(template.id)
    assert draft["weeks"][0]["sessions"][0]["workout_template_version"]["name"] == template.name

    replacement = copy.deepcopy(payload)
    replacement["name"] = "Updated four week strength"
    updated = client.put(
        f"/api/v1/coach/training-programs/{program_id}/draft",
        headers=headers,
        json={**replacement, "expected_draft_revision": 1},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["draft_version"]["draft_revision"] == 2
    stale = client.put(
        f"/api/v1/coach/training-programs/{program_id}/draft",
        headers=headers,
        json={**payload, "expected_draft_revision": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "training_program_draft_conflict"

    published = client.post(
        f"/api/v1/coach/training-programs/{program_id}/publish", headers=headers
    )
    assert published.status_code == 200, published.text
    version = published.json()["published_version"]
    assert len(version["content_hash"]) == 64
    version_id = uuid.UUID(version["id"])
    week_id = uuid.UUID(version["weeks"][0]["id"])
    session_id = uuid.UUID(version["weeks"][0]["sessions"][0]["id"])
    immutable = (
        db.get(TrainingProgramVersion, version_id).name,
        db.get(ProgramWeek, week_id).is_deload,
        db.get(ProgramSession, session_id).workout_template_version_id,
    )
    assert client.post(
        f"/api/v1/coach/training-programs/{program_id}/publish", headers=headers
    ).json()["published_version"]["id"] == version["id"]
    assert client.put(
        f"/api/v1/coach/training-programs/{program_id}/draft",
        headers=headers,
        json={**payload, "expected_draft_revision": 2},
    ).status_code == 409
    revision = client.post(
        f"/api/v1/coach/training-programs/{program_id}/revisions", headers=headers
    )
    assert revision.status_code == 201
    assert revision.json()["draft_version"]["version_number"] == 2
    assert revision.json()["draft_version"]["weeks"][0]["sessions"][0][
        "workout_template_version_id"
    ] == str(template.id)
    assert client.post(
        f"/api/v1/coach/training-programs/{program_id}/revisions", headers=headers
    ).status_code == 409
    assert immutable == (
        db.get(TrainingProgramVersion, version_id).name,
        db.get(ProgramWeek, week_id).is_deload,
        db.get(ProgramSession, session_id).workout_template_version_id,
    )
    archived = client.post(
        f"/api/v1/coach/training-programs/{program_id}/archive", headers=headers
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"


@pytest.mark.parametrize(
    ("mutate", "expected"),
    [
        (lambda body: body.update(duration_weeks=0), 422),
        (lambda body: body["weeks"].pop(), 422),
        (lambda body: body["weeks"][0]["sessions"][0].update(weekday="noday"), 422),
        (lambda body: body["weeks"][0]["sessions"][1].update(display_order=3), 422),
    ],
)
def test_program_graph_validation(
    client: TestClient, db: Session, mutate, expected: int
) -> None:
    coach, template = setup_program_data(db)
    body = program_payload(template)
    mutate(body)
    response = client.post(
        "/api/v1/coach/training-programs",
        headers=auth(login(client, coach.email, "CoachPass123!")),
        json=body,
    )
    assert response.status_code == expected


def test_foreign_unpublished_and_archived_template_versions_are_rejected(
    client: TestClient, db: Session
) -> None:
    coach, template = setup_program_data(db)
    other = db.scalar(select(User).where(User.email == "other@example.com"))
    assert other is not None
    seed_exercise_library(db, other)
    seed_workout_templates(db, other)
    foreign = published_template(db, other)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    body = program_payload(foreign)
    assert client.post("/api/v1/coach/training-programs", headers=headers, json=body).status_code == 422

    draft_template = db.scalar(
        select(WorkoutTemplateVersion)
        .join(
            WorkoutTemplate,
            WorkoutTemplate.id == WorkoutTemplateVersion.workout_template_id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == coach.id,
            WorkoutTemplateVersion.version_status == WorkoutTemplateVersionStatus.DRAFT,
        )
    )
    assert draft_template is not None
    assert client.post(
        "/api/v1/coach/training-programs",
        headers=headers,
        json=program_payload(draft_template),
    ).status_code == 422
    template.workout_template.status = WorkoutTemplateStatus.ARCHIVED
    db.commit()
    assert client.post(
        "/api/v1/coach/training-programs", headers=headers, json=program_payload(template)
    ).status_code == 422


def test_program_cross_coach_hiding_and_demo_mutation_denial(
    client: TestClient, db: Session
) -> None:
    coach, template = setup_program_data(db)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    created = client.post(
        "/api/v1/coach/training-programs", headers=headers, json=program_payload(template)
    ).json()
    other_headers = auth(login(client, "other@example.com", "OtherPass123!"))
    assert client.get(
        f"/api/v1/coach/training-programs/{created['id']}", headers=other_headers
    ).status_code == 404
    demo = User(
        email="program-demo@example.com",
        password_hash=hash_password("DemoProgram123!"),
        first_name="Demo",
        last_name="Coach",
        role=Role.COACH,
        is_demo=True,
    )
    db.add(demo)
    db.commit()
    demo_headers = auth(create_access_token(demo))
    assert client.post(
        "/api/v1/coach/training-programs",
        headers=demo_headers,
        json=program_payload(template),
    ).status_code == 403
    for suffix in ("publish", "revisions", "archive"):
        assert client.post(
            f"/api/v1/coach/training-programs/{created['id']}/{suffix}",
            headers=demo_headers,
        ).status_code == 403
    assert client.put(
        f"/api/v1/coach/training-programs/{created['id']}/draft",
        headers=demo_headers,
        json={**program_payload(template), "expected_draft_revision": 1},
    ).status_code == 403


def test_program_hash_is_deterministic_and_list_summaries_are_complete(
    client: TestClient, db: Session
) -> None:
    coach, template = setup_program_data(db)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    created = client.post(
        "/api/v1/coach/training-programs", headers=headers, json=program_payload(template)
    ).json()
    version = db.get(TrainingProgramVersion, uuid.UUID(created["draft_version"]["id"]))
    assert version is not None
    assert training_program_content_hash(version) == training_program_content_hash(version)
    client.post(f"/api/v1/coach/training-programs/{created['id']}/publish", headers=headers)
    listing = client.get(
        "/api/v1/coach/training-programs?goal_tag=strength&search=four&page=1&per_page=10",
        headers=headers,
    )
    assert listing.status_code == 200
    summary = listing.json()["items"][0]
    assert summary["duration_weeks"] == 4
    assert summary["workout_slot_count"] == 5
    assert summary["deload_week_count"] == 1
    assert summary["published_at"] is not None


def test_program_seed_is_idempotent(db: Session) -> None:
    coach, _template = setup_program_data(db)
    seed_training_programs(db, coach)
    first = list(db.scalars(select(TrainingProgramVersion)).all())
    seed_training_programs(db, coach)
    second = list(db.scalars(select(TrainingProgramVersion)).all())
    assert len(first) == len(second) == 2
    assert sum(item.version_status.value == "published" for item in second) == 1
    published = next(item for item in second if item.version_status.value == "published")
    assert len(published.weeks) == 4
    assert published.weeks[3].is_deload is True


def test_training_program_migration_upgrade_downgrade_and_check(tmp_path: Path) -> None:
    database_path = tmp_path / "training-program.db"
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

    # Revision 0001 uses live metadata, so remove the Phase 4 tables to reproduce
    # the schema that was actually released at revision 0006.
    alembic("upgrade", "20260716_0006")
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=OFF")
    for table in (
        "program_sessions",
        "program_weeks",
        "training_programs",
        "training_program_versions",
    ):
        connection.execute(f"DROP TABLE {table}")
    connection.commit()
    connection.close()

    alembic("upgrade", "20260716_0007")
    engine = create_engine(f"sqlite:///{database_path}")
    assert PROGRAM_TABLE_NAMES <= set(inspect(engine).get_table_names())
    alembic("current")
    alembic("downgrade", "20260716_0006")
    assert not PROGRAM_TABLE_NAMES.intersection(inspect(engine).get_table_names())
    alembic("upgrade", "head")
    assert PROGRAM_TABLE_NAMES <= set(inspect(engine).get_table_names())
    alembic("check")


PROGRAM_TABLE_NAMES = {
    "training_programs",
    "training_program_versions",
    "program_weeks",
    "program_sessions",
}
