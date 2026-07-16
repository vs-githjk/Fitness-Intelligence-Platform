import os
import sqlite3
import subprocess
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from app.models import (
    AssignmentHistory,
    CoachTraineeAssignment,
    Role,
    ScheduledWorkout,
    ScheduledWorkoutStatus,
    TraineeProfile,
    TrainingAssignment,
    TrainingAssignmentStatus,
    TrainingProgram,
    TrainingProgramVersion,
    TrainingProgramVersionStatus,
    User,
)
from app.schemas import TrainingAssignmentCreateRequest
from app.security import create_access_token, hash_password
from app.training_assignment_services import (
    _reconcile,
    create_training_assignment,
)
from scripts.seed import (
    seed_exercise_library,
    seed_training_assignments,
    seed_training_programs,
    seed_workout_templates,
)


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def setup_assignment_data(
    db: Session, timezone: str = "Asia/Kolkata"
) -> tuple[User, User, TrainingProgramVersion]:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    trainee = User(
        email=f"assignment-{uuid.uuid4()}@example.com",
        password_hash=hash_password("TraineePass123!"),
        first_name="Assigned",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(trainee)
    db.flush()
    db.add(TraineeProfile(user_id=trainee.id, timezone=timezone))
    db.add(
        CoachTraineeAssignment(
            coach_id=coach.id,
            trainee_id=trainee.id,
            accepted_at=datetime.now(UTC),
        )
    )
    db.commit()
    seed_exercise_library(db, coach)
    seed_workout_templates(db, coach)
    seed_training_programs(db, coach)
    program = db.scalar(
        select(TrainingProgramVersion)
        .join(
            TrainingProgram,
            TrainingProgram.id == TrainingProgramVersion.training_program_id,
        )
        .where(
            TrainingProgram.owner_coach_id == coach.id,
            TrainingProgramVersion.version_status == TrainingProgramVersionStatus.PUBLISHED,
        )
    )
    assert program is not None
    return coach, trainee, program


def local_date(timezone: str) -> date:
    return datetime.now(UTC).astimezone(ZoneInfo(timezone)).date()


def test_assignment_preview_creation_schedule_and_exact_version_pinning(
    client: TestClient, db: Session
) -> None:
    timezone = "Pacific/Kiritimati"
    coach, trainee, program = setup_assignment_data(db, timezone)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    start = local_date(timezone)
    body = {
        "training_program_version_id": str(program.id),
        "effective_start_date": start.isoformat(),
    }
    preview = client.post(
        f"/api/v1/coach/trainees/{trainee.id}/training-assignments/preview",
        headers=headers,
        json=body,
    )
    assert preview.status_code == 200, preview.text
    preview_data = preview.json()
    first_monday = start + timedelta(days=(-start.weekday()) % 7)
    assert preview_data["timezone"] == timezone
    assert preview_data["workouts"][0]["scheduled_date"] == first_monday.isoformat()
    assert preview_data["workouts"][0]["weekday"] == "monday"
    optional = next(item for item in preview_data["workouts"] if not item["required"])
    assert optional["display_order"] == 2

    created = client.post(
        f"/api/v1/coach/trainees/{trainee.id}/training-assignments",
        headers=headers,
        json=body,
    )
    assert created.status_code == 201, created.text
    workspace = created.json()
    assert workspace["current_assignment"]["training_program_version_id"] == str(program.id)
    assert workspace["current_assignment"]["status"] == "active"
    stored = db.scalar(
        select(ScheduledWorkout).where(ScheduledWorkout.trainee_id == trainee.id)
    )
    assert stored is not None
    assert stored.workout_template_version_id == program.weeks[0].sessions[0].workout_template_version_id
    assert len(workspace["history_events"]) == 2


def test_future_replacement_supersedes_only_future_schedule_and_can_be_cancelled(
    client: TestClient, db: Session
) -> None:
    coach, trainee, program = setup_assignment_data(db)
    headers = auth(login(client, coach.email, "CoachPass123!"))
    today = local_date("Asia/Kolkata")
    endpoint = f"/api/v1/coach/trainees/{trainee.id}/training-assignments"
    assert client.post(
        endpoint,
        headers=headers,
        json={
            "training_program_version_id": str(program.id),
            "effective_start_date": today.isoformat(),
        },
    ).status_code == 201
    future = today + timedelta(days=10)
    replacement = client.post(
        endpoint,
        headers=headers,
        json={
            "training_program_version_id": str(program.id),
            "effective_start_date": future.isoformat(),
        },
    )
    assert replacement.status_code == 201, replacement.text
    data = replacement.json()
    assert data["current_assignment"]["status"] == "active"
    assert data["upcoming_assignment"]["status"] == "scheduled"
    assert data["current_assignment"]["effective_end_date"] == (
        future - timedelta(days=1)
    ).isoformat()
    old = db.get(TrainingAssignment, uuid.UUID(data["current_assignment"]["id"]))
    assert old is not None
    assert any(
        item.status == ScheduledWorkoutStatus.SUPERSEDED
        for item in old.scheduled_workouts
        if item.scheduled_date >= future
    )
    assert all(
        item.status == ScheduledWorkoutStatus.SCHEDULED
        for item in old.scheduled_workouts
        if item.scheduled_date < future
    )
    cancel = client.post(
        f"/api/v1/coach/training-assignments/{data['upcoming_assignment']['id']}/cancel",
        headers=headers,
    )
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["upcoming_assignment"] is None
    cancelled = db.get(
        TrainingAssignment, uuid.UUID(data["upcoming_assignment"]["id"])
    )
    assert cancelled is not None
    assert cancelled.status == TrainingAssignmentStatus.CANCELLED
    assert all(
        item.status == ScheduledWorkoutStatus.CANCELLED
        for item in cancelled.scheduled_workouts
    )


def test_future_assignment_activates_once_on_trainee_local_date(
    db: Session,
) -> None:
    coach, trainee, program = setup_assignment_data(db)
    today = local_date("Asia/Kolkata")
    seed_training_assignments(db, coach, [trainee], today, include_future=False)
    current = db.scalar(
        select(TrainingAssignment).where(
            TrainingAssignment.trainee_id == trainee.id,
            TrainingAssignment.status == TrainingAssignmentStatus.ACTIVE,
        )
    )
    assert current is not None
    future_date = today + timedelta(days=7)
    create_training_assignment(
        db,
        coach,
        trainee.id,
        TrainingAssignmentCreateRequest(
            training_program_version_id=program.id,
            effective_start_date=future_date,
        ),
    )
    assignments = list(
        db.scalars(
            select(TrainingAssignment).where(TrainingAssignment.trainee_id == trainee.id)
        ).all()
    )
    _reconcile(db, assignments, future_date, datetime.now(UTC))
    active = [item for item in assignments if item.status == TrainingAssignmentStatus.ACTIVE]
    assert len(active) == 1
    assert active[0].effective_start_date == future_date
    assert current.status == TrainingAssignmentStatus.SUPERSEDED


def test_assignment_authorization_demo_guard_and_trainee_read_only(
    client: TestClient, db: Session
) -> None:
    coach, trainee, program = setup_assignment_data(db)
    coach_headers = auth(login(client, coach.email, "CoachPass123!"))
    today = local_date("Asia/Kolkata")
    create = client.post(
        f"/api/v1/coach/trainees/{trainee.id}/training-assignments",
        headers=coach_headers,
        json={
            "training_program_version_id": str(program.id),
            "effective_start_date": today.isoformat(),
        },
    )
    assert create.status_code == 201
    trainee_headers = auth(create_access_token(trainee))
    trainee_view = client.get("/api/v1/trainee/program", headers=trainee_headers)
    assert trainee_view.status_code == 200
    assert trainee_view.json()["current_assignment"]["trainee_id"] == str(trainee.id)
    other_headers = auth(login(client, "other@example.com", "OtherPass123!"))
    assert client.get(
        f"/api/v1/coach/trainees/{trainee.id}/training-assignment",
        headers=other_headers,
    ).status_code == 403

    demo = User(
        email="assignment-demo@example.com",
        password_hash=hash_password("DemoAssignment123!"),
        first_name="Demo",
        last_name="Coach",
        role=Role.COACH,
        is_demo=True,
    )
    db.add(demo)
    db.commit()
    demo_headers = auth(create_access_token(demo))
    valid_body = {
        "training_program_version_id": str(program.id),
        "effective_start_date": today.isoformat(),
    }
    for suffix in ("preview", ""):
        path = f"/api/v1/coach/trainees/{trainee.id}/training-assignments"
        if suffix:
            path += f"/{suffix}"
        assert client.post(path, headers=demo_headers, json=valid_body).status_code == 403
    assignment_id = create.json()["current_assignment"]["id"]
    assert client.post(
        f"/api/v1/coach/training-assignments/{assignment_id}/cancel",
        headers=demo_headers,
    ).status_code == 403


def test_assignment_history_and_seed_are_immutable_and_idempotent(db: Session) -> None:
    coach, trainee, _program = setup_assignment_data(db)
    today = local_date("Asia/Kolkata")
    seed_training_assignments(db, coach, [trainee], today, include_future=True)
    assignments = list(
        db.scalars(select(TrainingAssignment).where(TrainingAssignment.trainee_id == trainee.id))
    )
    events = list(
        db.scalars(select(AssignmentHistory).where(AssignmentHistory.trainee_id == trainee.id))
    )
    seed_training_assignments(db, coach, [trainee], today, include_future=True)
    assert len(
        list(db.scalars(select(TrainingAssignment).where(TrainingAssignment.trainee_id == trainee.id)))
    ) == len(assignments)
    assert len(
        list(db.scalars(select(AssignmentHistory).where(AssignmentHistory.trainee_id == trainee.id)))
    ) == len(events)
    assert all(item.snapshot["training_program_version_id"] for item in events)


def test_training_assignment_migration_upgrade_downgrade_and_check(tmp_path: Path) -> None:
    database_path = tmp_path / "training-assignment.db"
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

    alembic("upgrade", "20260716_0007")
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys=OFF")
    for table in ("assignment_history", "scheduled_workouts", "training_assignments"):
        connection.execute(f"DROP TABLE {table}")
    connection.commit()
    connection.close()
    alembic("upgrade", "20260716_0008")
    engine = create_engine(f"sqlite:///{database_path}")
    assert ASSIGNMENT_TABLES <= set(inspect(engine).get_table_names())
    alembic("downgrade", "20260716_0007")
    assert not ASSIGNMENT_TABLES.intersection(inspect(engine).get_table_names())
    alembic("upgrade", "head")
    alembic("check")


ASSIGNMENT_TABLES = {"training_assignments", "scheduled_workouts", "assignment_history"}
