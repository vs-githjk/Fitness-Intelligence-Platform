import os
import sqlite3
import subprocess
import sys
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from app.domain.units import canonical_kilograms, canonical_meters
from app.models import (
    DistanceUnit,
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseTrackingMode,
    ExerciseVersion,
    ExerciseVersionStatus,
    User,
    WeightUnit,
    WorkoutSetPrescription,
    WorkoutTemplate,
    WorkoutTemplateExercise,
    WorkoutTemplateVersion,
    WorkoutTemplateVersionStatus,
)
from scripts.seed import seed_exercise_library, seed_workout_templates


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def published_version(db: Session, coach: User, mode: ExerciseTrackingMode) -> ExerciseVersion:
    version = db.scalar(
        select(ExerciseVersion)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(
            ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED,
            ExerciseVersion.tracking_mode == mode,
            (Exercise.scope == ExerciseScope.SYSTEM)
            | (Exercise.owner_coach_id == coach.id),
        )
        .order_by(Exercise.scope)
    )
    assert version is not None
    return version


def prescription(mode: ExerciseTrackingMode, **overrides: object) -> dict:
    values: dict = {
        ExerciseTrackingMode.REPETITIONS_AND_LOAD: {
            "repetitions_min": 8,
            "repetitions_max": 10,
            "target_load_original_value": "22",
            "target_load_original_unit": "lb",
            "target_rpe": "7",
            "rest_seconds": 90,
            "tempo": "3-1-1",
        },
        ExerciseTrackingMode.REPETITIONS_ONLY: {
            "repetitions_min": 10,
            "repetitions_max": 12,
            "target_rpe": "6",
            "target_rir": "3",
            "rest_seconds": 45,
            "tempo": "2-1-2",
        },
        ExerciseTrackingMode.DURATION: {
            "target_duration_seconds": 45,
            "target_rpe": "5",
            "rest_seconds": 30,
        },
        ExerciseTrackingMode.DISTANCE_AND_DURATION: {
            "target_duration_seconds": 900,
            "target_distance_value": "1.25",
            "target_distance_unit": "miles",
            "target_rpe": "5",
            "rest_seconds": 0,
        },
        ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS: {
            "repetitions_min": 5,
            "repetitions_max": 8,
            "target_assistance_original_value": "20",
            "target_assistance_original_unit": "kg",
            "target_rir": "2",
            "tempo": "2-1-2",
        },
    }[mode]
    values = {"set_number": 1, "set_type": "working", **values, **overrides}
    return values


def template_payload(
    exercise_version: ExerciseVersion,
    *,
    name: str = "API template",
    set_data: dict | None = None,
) -> dict:
    return {
        "name": name,
        "description": "Template authoring integration test.",
        "goal_tags": ["Strength", "general_health", "strength"],
        "estimated_duration_minutes": 45,
        "target_session_rpe": 7,
        "coach_notes": "Coach-only context.",
        "trainee_instructions": "Use controlled technique.",
        "exercises": [
            {
                "exercise_version_id": str(exercise_version.id),
                "section": "main",
                "display_order": 1,
                "coach_notes": "Exercise note.",
                "trainee_instructions": "Exercise instruction.",
                "sets": [set_data or prescription(exercise_version.tracking_mode)],
            }
        ],
    }


def test_create_replace_publish_revision_archive_and_immutability(
    client: TestClient, db: Session
) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    seed_exercise_library(db, coach)
    exercise_version = published_version(
        db, coach, ExerciseTrackingMode.REPETITIONS_AND_LOAD
    )
    headers = auth(login(client, coach.email, "CoachPass123!"))

    created = client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(exercise_version),
    )
    assert created.status_code == 201, created.text
    template_id = created.json()["id"]
    draft = created.json()["draft_version"]
    assert draft["version_number"] == 1
    assert draft["draft_revision"] == 1
    assert draft["goal_tags"] == ["general_health", "strength"]
    stored_set = draft["exercises"][0]["sets"][0]
    assert Decimal(stored_set["target_load_original_value"]) == Decimal("22.000")
    assert Decimal(stored_set["target_load_canonical_kg"]) == Decimal("9.979")

    replacement = template_payload(
        exercise_version,
        name="Updated API template",
        set_data={**prescription(exercise_version.tracking_mode), "repetitions_max": 12},
    )
    updated = client.put(
        f"/api/v1/coach/workout-templates/{template_id}/draft",
        headers=headers,
        json={**replacement, "expected_draft_revision": 1},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["draft_version"]["draft_revision"] == 2
    assert updated.json()["draft_version"]["exercises"][0]["sets"][0][
        "repetitions_max"
    ] == 12
    stale = client.put(
        f"/api/v1/coach/workout-templates/{template_id}/draft",
        headers=headers,
        json={**replacement, "expected_draft_revision": 1},
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "workout_template_draft_conflict"

    published = client.post(
        f"/api/v1/coach/workout-templates/{template_id}/publish", headers=headers
    )
    assert published.status_code == 200, published.text
    published_v1 = published.json()["published_version"]
    assert published.json()["draft_version"] is None
    assert len(published_v1["content_hash"]) == 64
    assert client.post(
        f"/api/v1/coach/workout-templates/{template_id}/publish", headers=headers
    ).json()["published_version"]["id"] == published_v1["id"]

    version_id = uuid.UUID(published_v1["id"])
    exercise_id = uuid.UUID(published_v1["exercises"][0]["id"])
    set_id = uuid.UUID(published_v1["exercises"][0]["sets"][0]["id"])
    immutable_values = (
        db.get(WorkoutTemplateVersion, version_id).name,
        db.get(WorkoutTemplateExercise, exercise_id).exercise_version_id,
        db.get(WorkoutSetPrescription, set_id).repetitions_max,
    )
    assert client.put(
        f"/api/v1/coach/workout-templates/{template_id}/draft",
        headers=headers,
        json={**replacement, "expected_draft_revision": 2},
    ).status_code == 409

    revision = client.post(
        f"/api/v1/coach/workout-templates/{template_id}/revisions", headers=headers
    )
    assert revision.status_code == 201
    assert revision.json()["draft_version"]["version_number"] == 2
    assert revision.json()["draft_version"]["name"] == published_v1["name"]
    duplicate_draft = client.post(
        f"/api/v1/coach/workout-templates/{template_id}/revisions", headers=headers
    )
    assert duplicate_draft.status_code == 409

    changed = client.put(
        f"/api/v1/coach/workout-templates/{template_id}/draft",
        headers=headers,
        json={**replacement, "name": "Version two", "expected_draft_revision": 1},
    )
    assert changed.status_code == 200
    assert (
        db.get(WorkoutTemplateVersion, version_id).name,
        db.get(WorkoutTemplateExercise, exercise_id).exercise_version_id,
        db.get(WorkoutSetPrescription, set_id).repetitions_max,
    ) == immutable_values

    archived = client.post(
        f"/api/v1/coach/workout-templates/{template_id}/archive", headers=headers
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"
    active_list = client.get("/api/v1/coach/workout-templates", headers=headers)
    assert all(item["id"] != template_id for item in active_list.json()["items"])
    archived_list = client.get(
        "/api/v1/coach/workout-templates?status=archived", headers=headers
    )
    assert any(item["id"] == template_id for item in archived_list.json()["items"])
    assert client.post(
        f"/api/v1/coach/workout-templates/{template_id}/archive", headers=headers
    ).status_code == 200
    assert client.post(
        f"/api/v1/coach/workout-templates/{template_id}/publish", headers=headers
    ).status_code == 409


@pytest.mark.parametrize("mode", list(ExerciseTrackingMode))
def test_each_tracking_mode_accepts_only_compatible_fields(
    client: TestClient, db: Session, mode: ExerciseTrackingMode
) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    seed_exercise_library(db, coach)
    version = published_version(db, coach, mode)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    valid = client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(version, name=f"Valid {mode.value}"),
    )
    assert valid.status_code == 201, valid.text
    if mode == ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS:
        stored = valid.json()["draft_version"]["exercises"][0]["sets"][0]
        assert Decimal(stored["target_assistance_canonical_kg"]) == Decimal("20.000")
        assert stored["target_load_canonical_kg"] is None

    prohibited = {
        ExerciseTrackingMode.REPETITIONS_AND_LOAD: {"target_duration_seconds": 30},
        ExerciseTrackingMode.REPETITIONS_ONLY: {
            "target_load_original_value": 10,
            "target_load_original_unit": "kg",
        },
        ExerciseTrackingMode.DURATION: {"repetitions_min": 5, "repetitions_max": 5},
        ExerciseTrackingMode.DISTANCE_AND_DURATION: {"target_rir": 2},
        ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS: {
            "target_load_original_value": 10,
            "target_load_original_unit": "kg",
        },
    }[mode]
    invalid_set = {**prescription(mode), **prohibited}
    invalid = client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(version, name=f"Invalid {mode.value}", set_data=invalid_set),
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "tracking_mode_mismatch"

    required_fields = {
        ExerciseTrackingMode.REPETITIONS_AND_LOAD: ("repetitions_min", "repetitions_max"),
        ExerciseTrackingMode.REPETITIONS_ONLY: ("repetitions_min", "repetitions_max"),
        ExerciseTrackingMode.DURATION: ("target_duration_seconds",),
        ExerciseTrackingMode.DISTANCE_AND_DURATION: (
            "target_distance_value",
            "target_distance_unit",
        ),
        ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS: (
            "repetitions_min",
            "repetitions_max",
        ),
    }[mode]
    missing_required = prescription(mode)
    for field in required_fields:
        missing_required.pop(field)
    missing = client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(
            version,
            name=f"Missing required {mode.value}",
            set_data=missing_required,
        ),
    )
    assert missing.status_code == 422
    assert missing.json()["detail"]["code"] == "tracking_mode_mismatch"


def test_ordering_visibility_and_exercise_selection_rules(
    client: TestClient, db: Session
) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    other = db.scalar(select(User).where(User.email == "other@example.com"))
    assert coach is not None and other is not None
    seed_exercise_library(db, coach)
    seed_exercise_library(db, other)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    other_headers = auth(login(client, other.email, "OtherPass123!"))
    system = published_version(db, coach, ExerciseTrackingMode.REPETITIONS_AND_LOAD)
    own_private = db.scalar(
        select(ExerciseVersion)
        .join(Exercise)
        .where(
            Exercise.owner_coach_id == coach.id,
            ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED,
        )
    )
    foreign_private = db.scalar(
        select(ExerciseVersion)
        .join(Exercise)
        .where(
            Exercise.owner_coach_id == other.id,
            ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED,
        )
    )
    assert own_private is not None and foreign_private is not None

    own_template_id = None
    for version, expected in ((system, 201), (own_private, 201), (foreign_private, 422)):
        response = client.post(
            "/api/v1/coach/workout-templates",
            headers=headers,
            json=template_payload(version, name=f"Selection {version.id}"),
        )
        assert response.status_code == expected, response.text
        if version.id == own_private.id:
            own_template_id = response.json()["id"]

    invalid_order = template_payload(system, name="Invalid order")
    invalid_order["exercises"][0]["display_order"] = 2
    response = client.post(
        "/api/v1/coach/workout-templates", headers=headers, json=invalid_order
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_exercise_order"

    invalid_sets = template_payload(system, name="Invalid set order")
    invalid_sets["exercises"][0]["sets"][0]["set_number"] = 2
    response = client.post(
        "/api/v1/coach/workout-templates", headers=headers, json=invalid_sets
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_set_order"

    unpublished_root = Exercise(
        scope=ExerciseScope.COACH_PRIVATE,
        owner_coach_id=coach.id,
        slug="unpublished-selection",
        status=ExerciseStatus.ACTIVE,
    )
    unpublished = ExerciseVersion(
        exercise=unpublished_root,
        version_number=1,
        status=ExerciseVersionStatus.DRAFT,
        name="Unpublished",
        description=None,
        instructions="Not selectable.",
        tracking_mode=ExerciseTrackingMode.REPETITIONS_ONLY,
        category="strength",
        movement_pattern="push",
        equipment=[],
        primary_muscle_groups=["chest"],
        secondary_muscle_groups=[],
        unilateral=False,
        safety_cues=[],
    )
    db.add(unpublished_root)
    db.commit()
    assert client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(unpublished, name="Unpublished rejected"),
    ).status_code == 422

    own_root = db.get(Exercise, own_private.exercise_id)
    own_root.status = ExerciseStatus.ARCHIVED
    db.commit()
    assert own_template_id is not None
    publish_revalidation = client.post(
        f"/api/v1/coach/workout-templates/{own_template_id}/publish",
        headers=headers,
    )
    assert publish_revalidation.status_code == 422
    assert publish_revalidation.json()["detail"]["code"] == (
        "exercise_version_not_selectable"
    )
    assert client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(own_private, name="Archived rejected"),
    ).status_code == 422

    created = client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(system, name="Hidden template"),
    ).json()
    assert client.get(
        f"/api/v1/coach/workout-templates/{created['id']}", headers=other_headers
    ).status_code == 404


def test_hash_determinism_list_filters_and_decimal_conversions(
    client: TestClient, db: Session
) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    seed_exercise_library(db, coach)
    version = published_version(db, coach, ExerciseTrackingMode.REPETITIONS_AND_LOAD)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    created = client.post(
        "/api/v1/coach/workout-templates",
        headers=headers,
        json=template_payload(version, name="Hash stable"),
    ).json()
    template_id = created["id"]
    published = client.post(
        f"/api/v1/coach/workout-templates/{template_id}/publish", headers=headers
    ).json()
    first_hash = published["published_version"]["content_hash"]
    client.post(
        f"/api/v1/coach/workout-templates/{template_id}/revisions", headers=headers
    )
    second = client.post(
        f"/api/v1/coach/workout-templates/{template_id}/publish", headers=headers
    ).json()
    assert second["published_version"]["content_hash"] == first_hash

    listing = client.get(
        "/api/v1/coach/workout-templates?goal_tag=strength&search=hash&page=1&per_page=1",
        headers=headers,
    )
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    assert listing.json()["items"][0]["name"] == "Hash stable"
    assert canonical_kilograms(Decimal("22"), WeightUnit.LB) == Decimal("9.979")
    assert canonical_kilograms(Decimal("10"), WeightUnit.KG) == Decimal("10.000")
    assert canonical_meters(Decimal("1"), DistanceUnit.MILES) == Decimal("1609.344")


def test_template_seed_is_idempotent_and_represents_all_modes(db: Session) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    seed_exercise_library(db, coach)
    seed_workout_templates(db, coach)
    seed_workout_templates(db, coach)
    roots = db.scalar(
        select(func.count(WorkoutTemplate.id)).where(
            WorkoutTemplate.owner_coach_id == coach.id
        )
    )
    published = db.scalar(
        select(func.count(WorkoutTemplateVersion.id))
        .join(
            WorkoutTemplate,
            WorkoutTemplateVersion.workout_template_id == WorkoutTemplate.id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == coach.id,
            WorkoutTemplateVersion.version_status == WorkoutTemplateVersionStatus.PUBLISHED,
        )
    )
    drafts = db.scalar(
        select(func.count(WorkoutTemplateVersion.id))
        .join(
            WorkoutTemplate,
            WorkoutTemplateVersion.workout_template_id == WorkoutTemplate.id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == coach.id,
            WorkoutTemplateVersion.version_status == WorkoutTemplateVersionStatus.DRAFT,
        )
    )
    modes = set(
        db.scalars(
            select(ExerciseVersion.tracking_mode)
            .join(
                WorkoutTemplateExercise,
                WorkoutTemplateExercise.exercise_version_id == ExerciseVersion.id,
            )
            .join(
                WorkoutTemplateVersion,
                WorkoutTemplateExercise.workout_template_version_id
                == WorkoutTemplateVersion.id,
            )
            .join(
                WorkoutTemplate,
                WorkoutTemplateVersion.workout_template_id == WorkoutTemplate.id,
            )
            .where(
                WorkoutTemplate.owner_coach_id == coach.id,
                WorkoutTemplateVersion.version_status
                == WorkoutTemplateVersionStatus.PUBLISHED,
            )
        ).all()
    )
    assert roots == 3
    assert published == 2
    assert drafts == 1
    assert modes == set(ExerciseTrackingMode)


def test_workout_template_migration_upgrade_and_downgrade(tmp_path: Path) -> None:
    database_path = tmp_path / "workout-template.db"
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

    # Revision 0001 uses live metadata. Remove Phase 2 tables to reproduce an
    # actually deployed 0005 database before applying the append-only migration.
    alembic("upgrade", "20260716_0005")
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=OFF")
    for table in (
        "workout_set_prescriptions",
        "workout_template_exercises",
        "workout_templates",
        "workout_template_versions",
    ):
        connection.execute(f"DROP TABLE {table}")
    connection.commit()
    connection.close()

    alembic("upgrade", "20260716_0006")
    engine = create_engine(f"sqlite:///{database_path}")
    assert TABLE_NAMES <= set(inspect(engine).get_table_names())
    alembic("current")
    alembic("check")
    alembic("downgrade", "20260716_0005")
    assert not TABLE_NAMES.intersection(inspect(engine).get_table_names())
    alembic("upgrade", "head")
    assert TABLE_NAMES <= set(inspect(engine).get_table_names())


TABLE_NAMES = {
    "workout_templates",
    "workout_template_versions",
    "workout_template_exercises",
    "workout_set_prescriptions",
}
