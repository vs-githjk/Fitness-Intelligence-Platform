import os
import sqlite3
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from app.models import (
    CoachTraineeAssignment,
    ExerciseTrackingMode,
    Role,
    ScheduledWorkout,
    ScheduledWorkoutStatus,
    TraineeProfile,
    User,
    WorkoutSession,
    WorkoutSessionEvent,
    WorkoutTemplateVersion,
)
from app.security import WORKOUT_EXECUTION_DEMO_MUTATIONS, create_access_token, hash_password
from scripts.seed import (
    seed_exercise_library,
    seed_training_assignments,
    seed_training_programs,
    seed_workout_execution,
    seed_workout_templates,
)


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def execution_fixture(db: Session) -> tuple[User, User, list[ScheduledWorkout]]:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    trainee = User(
        email="execution@example.com",
        password_hash=hash_password("ExecutionPass123!"),
        first_name="Execution",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(trainee)
    db.flush()
    db.add_all(
        [
            TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"),
            CoachTraineeAssignment(coach_id=coach.id, trainee_id=trainee.id, status="active"),
        ]
    )
    db.commit()
    seed_exercise_library(db, coach)
    seed_workout_templates(db, coach)
    seed_training_programs(db, coach)
    seed_training_assignments(db, coach, [trainee], date.today(), include_future=False)
    workouts = list(
        db.scalars(
            select(ScheduledWorkout)
            .join(WorkoutTemplateVersion)
            .where(ScheduledWorkout.trainee_id == trainee.id)
            .order_by(WorkoutTemplateVersion.name, ScheduledWorkout.scheduled_date)
        ).all()
    )
    return coach, trainee, workouts


def start(client: TestClient, trainee: User, workout: ScheduledWorkout) -> dict:
    response = client.post(
        f"/api/v1/trainee/workouts/{workout.id}/start", headers=auth(trainee)
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_start_copies_immutable_graph_and_resumes_idempotently(
    client: TestClient, db: Session
) -> None:
    _, trainee, workouts = execution_fixture(db)
    session = start(client, trainee, workouts[0])
    assert session["status"] == "in_progress"
    assert session["scheduled_workout_status"] == "in_progress"
    assert session["exercises"]
    assert session["events"][0]["event_type"] == "session_started"
    assert "coach_notes" not in str(session)
    assert all(item["source"] == "prescribed" for item in session["exercises"][0]["sets"])

    workspace = client.get("/api/v1/trainee/program", headers=auth(trainee)).json()
    active_schedule = next(
        item for item in workspace["scheduled_workouts"] if item["id"] == str(workouts[0].id)
    )
    assert active_schedule["status"] == "in_progress"
    assert active_schedule["workout_session_id"] == session["id"]

    source_name = workouts[0].workout_template_version.exercises[0].exercise_version.name
    workouts[0].workout_template_version.exercises[0].exercise_version.name = "Changed later"
    db.commit()
    detail = client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}", headers=auth(trainee)
    ).json()
    assert detail["exercises"][0]["exercise_name"] == source_name

    resumed = start(client, trainee, workouts[0])
    assert resumed["id"] == session["id"]
    assert [item["id"] for item in resumed["exercises"]] == [
        item["id"] for item in session["exercises"]
    ]
    assert db.scalar(select(func.count(WorkoutSession.id))) == 1
    assert resumed["revision"] == session["revision"] + 1
    assert resumed["events"][-1]["event_type"] == "session_resumed"


def test_set_logging_units_added_sets_skips_conflict_and_completion(
    client: TestClient, db: Session
) -> None:
    _, trainee, workouts = execution_fixture(db)
    full_body = next(
        item for item in workouts if item.workout_template_version.name == "Full Body Strength"
    )
    session = start(client, trainee, full_body)
    load_exercise = next(
        item
        for item in session["exercises"]
        if item["tracking_mode"] == "repetitions_and_load"
    )
    target_set = load_exercise["sets"][0]
    saved = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{target_set['id']}",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "status": "completed",
            "actual_repetitions": 9,
            "actual_load_original_value": 22,
            "actual_load_original_unit": "lb",
            "actual_rpe": 7,
        },
    )
    assert saved.status_code == 200
    session = saved.json()
    stored = next(
        item
        for exercise in session["exercises"]
        for item in exercise["sets"]
        if item["id"] == target_set["id"]
    )
    assert Decimal(stored["actual_load_canonical_kg"]) == Decimal("9.979")

    conflict = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{target_set['id']}",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"] - 1,
            "status": "completed",
            "actual_repetitions": 10,
            "actual_load_original_value": 20,
            "actual_load_original_unit": "kg",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["detail"]["current_revision"] == session["revision"]

    added = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "idempotency_key": "added-set-0001",
            "workout_session_exercise_id": load_exercise["id"],
            "set_type": "back_off",
            "status": "planned",
        },
    )
    assert added.status_code == 200
    session = added.json()
    assert any(
        item["source"] == "trainee_added"
        for exercise in session["exercises"]
        for item in exercise["sets"]
    )
    repeated = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"] - 1,
            "idempotency_key": "added-set-0001",
            "workout_session_exercise_id": load_exercise["id"],
            "set_type": "back_off",
        },
    )
    assert repeated.status_code == 200
    assert repeated.json()["revision"] == session["revision"]

    for exercise in session["exercises"]:
        skipped = client.post(
            f"/api/v1/trainee/workout-sessions/{session['id']}/exercises/{exercise['id']}/skip",
            headers=auth(trainee),
            json={
                "expected_session_revision": session["revision"],
                "reason": "time_constraint",
                "note": "Synthetic test",
            },
        )
        assert skipped.status_code == 200
        session = skipped.json()
    completed = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/complete",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "actual_duration_minutes": 42,
            "session_rpe": 7,
            "trainee_note": "Finished safely.",
            "confirmed": True,
        },
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"
    immutable = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/end-incomplete",
        headers=auth(trainee),
        json={
            "expected_session_revision": completed.json()["revision"],
            "reason": "other",
        },
    )
    assert immutable.status_code == 409


def test_tracking_mode_validation_end_incomplete_and_start_rejections(
    client: TestClient, db: Session
) -> None:
    _, trainee, workouts = execution_fixture(db)
    recovery = next(
        item for item in workouts if item.workout_template_version.name == "Recovery and Mobility"
    )
    session = start(client, trainee, recovery)
    duration_set = next(
        item
        for exercise in session["exercises"]
        for item in exercise["sets"]
        if item["tracking_mode"] == "duration"
    )
    invalid = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{duration_set['id']}",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "status": "completed",
            "actual_duration_seconds": 30,
            "actual_repetitions": 5,
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "tracking_mode_mismatch"
    ended = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/end-incomplete",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "reason": "recovery_concern",
            "note": "Synthetic recovery concern.",
        },
    )
    assert ended.status_code == 200
    assert ended.json()["status"] == "ended_incomplete"
    assert ended.json()["scheduled_workout_status"] == "partial"

    blocked = workouts[-1]
    blocked.status = ScheduledWorkoutStatus.CANCELLED
    db.commit()
    response = client.post(
        f"/api/v1/trainee/workouts/{blocked.id}/start", headers=auth(trainee)
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    ("mode", "actuals", "prohibited"),
    [
        (
            ExerciseTrackingMode.REPETITIONS_AND_LOAD,
            {
                "actual_repetitions": 8,
                "actual_load_original_value": 40,
                "actual_load_original_unit": "kg",
                "actual_rpe": 7,
            },
            {"actual_duration_seconds": 30},
        ),
        (
            ExerciseTrackingMode.REPETITIONS_ONLY,
            {"actual_repetitions": 12, "actual_rir": 2},
            {
                "actual_repetitions": 12,
                "actual_load_original_value": 5,
                "actual_load_original_unit": "kg",
            },
        ),
        (
            ExerciseTrackingMode.DURATION,
            {"actual_duration_seconds": 45, "actual_rpe": 4},
            {"actual_duration_seconds": 45, "actual_repetitions": 3},
        ),
        (
            ExerciseTrackingMode.DISTANCE_AND_DURATION,
            {
                "actual_distance_value": 1.5,
                "actual_distance_unit": "kilometers",
                "actual_duration_seconds": 480,
            },
            {
                "actual_distance_value": 1.5,
                "actual_distance_unit": "kilometers",
                "actual_duration_seconds": 480,
                "actual_rir": 1,
            },
        ),
        (
            ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
            {
                "actual_repetitions": 6,
                "actual_assistance_original_value": 22,
                "actual_assistance_original_unit": "lb",
                "actual_rir": 1,
            },
            {
                "actual_repetitions": 6,
                "actual_load_original_value": 5,
                "actual_load_original_unit": "kg",
            },
        ),
    ],
)
def test_every_tracking_mode_accepts_only_compatible_actuals(
    client: TestClient,
    db: Session,
    mode: ExerciseTrackingMode,
    actuals: dict,
    prohibited: dict,
) -> None:
    _, trainee, workouts = execution_fixture(db)
    workout = next(
        item
        for item in workouts
        if any(
            exercise.exercise_version.tracking_mode == mode
            for exercise in item.workout_template_version.exercises
        )
    )
    session = start(client, trainee, workout)
    exercise = next(item for item in session["exercises"] if item["tracking_mode"] == mode.value)
    target_set = exercise["sets"][0]
    invalid = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{target_set['id']}",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "status": "completed",
            **prohibited,
        },
    )
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "tracking_mode_mismatch"
    unchanged = client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}", headers=auth(trainee)
    ).json()
    assert unchanged["revision"] == session["revision"]

    saved = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{target_set['id']}",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "status": "completed",
            **actuals,
        },
    )
    assert saved.status_code == 200, saved.text
    stored = next(
        item
        for item in saved.json()["exercises"]
        if item["id"] == exercise["id"]
    )["sets"][0]
    if mode == ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS:
        assert Decimal(stored["actual_assistance_canonical_kg"]) == Decimal("9.979")
        assert stored["actual_load_canonical_kg"] is None


def test_execution_authorization_demo_inventory_and_event_history(
    client: TestClient, db: Session
) -> None:
    coach, trainee, workouts = execution_fixture(db)
    other = User(
        email="other-execution@example.com",
        password_hash=hash_password("OtherExecution123!"),
        first_name="Other",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(other)
    db.commit()
    session = start(client, trainee, workouts[0])
    assert client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}", headers=auth(other)
    ).status_code == 404
    assert client.post(
        f"/api/v1/trainee/workouts/{workouts[1].id}/start", headers=auth(coach)
    ).status_code == 403

    trainee.is_demo = True
    db.commit()
    exercise = session["exercises"][0]
    target_set = exercise["sets"][0]
    mutations = [
        ("POST", f"/api/v1/trainee/workouts/{workouts[1].id}/start", None),
        (
            "PUT",
            f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{target_set['id']}",
            {
                "expected_session_revision": session["revision"],
                "status": "skipped",
            },
        ),
        (
            "POST",
            f"/api/v1/trainee/workout-sessions/{session['id']}/sets",
            {
                "expected_session_revision": session["revision"],
                "idempotency_key": "demo-denied-set",
                "workout_session_exercise_id": exercise["id"],
                "set_type": "working",
            },
        ),
        (
            "POST",
            f"/api/v1/trainee/workout-sessions/{session['id']}/exercises/{exercise['id']}/skip",
            {
                "expected_session_revision": session["revision"],
                "reason": "other",
            },
        ),
        (
            "POST",
            f"/api/v1/trainee/workout-sessions/{session['id']}/complete",
            {
                "expected_session_revision": session["revision"],
                "actual_duration_minutes": 30,
                "session_rpe": 5,
                "confirmed": True,
            },
        ),
        (
            "POST",
            f"/api/v1/trainee/workout-sessions/{session['id']}/end-incomplete",
            {
                "expected_session_revision": session["revision"],
                "reason": "other",
            },
        ),
    ]
    for method, path, payload in mutations:
        denied = client.request(method, path, headers=auth(trainee), json=payload)
        assert denied.status_code == 403, (method, path, denied.text)
        assert denied.json()["detail"]["code"] == "demo_read_only"

    documented = {
        (method.upper(), path)
        for path, methods in client.app.openapi()["paths"].items()
        for method in methods
        if method.lower() in {"post", "put", "patch", "delete"}
        and ("workout-sessions" in path or path.endswith("/start"))
    }
    assert documented == WORKOUT_EXECUTION_DEMO_MUTATIONS
    assert db.scalar(select(func.count(WorkoutSessionEvent.id))) >= 1


def test_execution_seed_is_deterministic_and_idempotent(
    db: Session,
) -> None:
    _, trainee, _ = execution_fixture(db)
    seed_workout_execution(db, trainee)
    before = (
        db.scalar(select(func.count(WorkoutSession.id))),
        db.scalar(select(func.count(WorkoutSessionEvent.id))),
        tuple(
            db.scalars(
                select(WorkoutSession.status)
                .where(WorkoutSession.trainee_id == trainee.id)
                .order_by(WorkoutSession.started_at)
            ).all()
        ),
    )
    seed_workout_execution(db, trainee)
    after = (
        db.scalar(select(func.count(WorkoutSession.id))),
        db.scalar(select(func.count(WorkoutSessionEvent.id))),
        tuple(
            db.scalars(
                select(WorkoutSession.status)
                .where(WorkoutSession.trainee_id == trainee.id)
                .order_by(WorkoutSession.started_at)
            ).all()
        ),
    )
    assert before == after
    assert set(before[2]) == {"in_progress", "completed", "ended_incomplete"}


def test_workout_execution_migration_upgrade_downgrade_and_check(tmp_path: Path) -> None:
    database_path = tmp_path / "workout-execution.db"
    environment = {**os.environ, "MIGRATION_DATABASE_URL": f"sqlite:///{database_path}"}
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

    alembic("upgrade", "20260716_0008")
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=OFF")
    for table in (
        "workout_session_events",
        "workout_set_logs",
        "workout_session_exercises",
        "workout_sessions",
    ):
        connection.execute(f"DROP TABLE {table}")
    connection.commit()
    connection.close()
    alembic("upgrade", "head")
    db_engine = create_engine(f"sqlite:///{database_path}")
    engine_tables = set(inspect(db_engine).get_table_names())
    assert {"workout_sessions", "workout_session_exercises", "workout_set_logs", "workout_session_events"} <= engine_tables
    alembic("downgrade", "20260716_0008")
    assert "workout_sessions" not in inspect(db_engine).get_table_names()
    alembic("upgrade", "head")
    alembic("current")
    alembic("check")
