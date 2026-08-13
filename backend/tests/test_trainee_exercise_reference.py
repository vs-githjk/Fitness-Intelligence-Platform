"""Trainee exercise-knowledge read capability (C2.2, §30).

Verifies the trainee-scoped delivery authorization walk: a trainee may read a published
exercise version only through a workout session they own; everything else is a 404, and
draft internals / ownership never leak. Demo trainees may read; coaches cannot use the
trainee route.
"""

import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CoachTraineeAssignment,
    ExerciseVersion,
    ExerciseVersionStatus,
    Role,
    ScheduledWorkout,
    TraineeProfile,
    User,
    WorkoutTemplateVersion,
)
from app.security import create_access_token, hash_password
from scripts.seed import (
    seed_exercise_library,
    seed_training_assignments,
    seed_training_programs,
    seed_workout_templates,
)


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def _make_trainee(db: Session, email: str) -> User:
    trainee = User(
        email=email,
        password_hash=hash_password("TraineePass123!"),
        first_name="Ref",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(trainee)
    db.flush()
    db.add(TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"))
    db.commit()
    return trainee


def _fixture(db: Session) -> tuple[User, User, list[ScheduledWorkout]]:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    trainee = _make_trainee(db, "reference@example.com")
    db.add(CoachTraineeAssignment(coach_id=coach.id, trainee_id=trainee.id, status="active"))
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


def _start(client: TestClient, trainee: User, workout: ScheduledWorkout) -> dict:
    response = client.post(f"/api/v1/trainee/workouts/{workout.id}/start", headers=auth(trainee))
    assert response.status_code == 200, response.text
    return response.json()


def test_trainee_reads_authorized_published_exercise_knowledge(client: TestClient, db: Session) -> None:
    _coach, trainee, workouts = _fixture(db)
    session = _start(client, trainee, workouts[0])
    version_id = session["exercises"][0]["exercise_version_id"]

    response = client.get(f"/api/v1/trainee/exercise-versions/{version_id}", headers=auth(trainee))
    assert response.status_code == 200, response.text
    body = response.json()

    # The approved presentation fields (§30) are present.
    for field in (
        "id",
        "exercise_id",
        "name",
        "movement_pattern",
        "equipment",
        "primary_muscle_groups",
        "secondary_muscle_groups",
        "difficulty",
        "instructions",
        "safety_cues",
        "coaching_cues",
        "common_mistakes",
        "tracking_mode",
    ):
        assert field in body, field
    assert body["id"] == version_id
    assert body["name"]
    assert body["movement_pattern"]
    assert isinstance(body["primary_muscle_groups"], list) and body["primary_muscle_groups"]

    # Draft internals / ownership / authoring never leak to the trainee.
    for leaked in ("content_hash", "owner_coach_id", "created_by_user_id", "draft_version", "scope"):
        assert leaked not in body, leaked


def test_cross_account_and_unknown_versions_return_404(client: TestClient, db: Session) -> None:
    _coach, trainee, workouts = _fixture(db)
    session = _start(client, trainee, workouts[0])
    version_id = session["exercises"][0]["exercise_version_id"]

    # A foreign trainee with no session referencing the version cannot read it.
    other = _make_trainee(db, "stranger@example.com")
    assert (
        client.get(f"/api/v1/trainee/exercise-versions/{version_id}", headers=auth(other)).status_code
        == 404
    )
    # An unknown version id is indistinguishable (also 404).
    assert (
        client.get(
            f"/api/v1/trainee/exercise-versions/{uuid.uuid4()}", headers=auth(trainee)
        ).status_code
        == 404
    )


def test_coach_cannot_use_trainee_exercise_route(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = _fixture(db)
    session = _start(client, trainee, workouts[0])
    version_id = session["exercises"][0]["exercise_version_id"]
    response = client.get(f"/api/v1/trainee/exercise-versions/{version_id}", headers=auth(coach))
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "forbidden"


def test_demo_trainee_may_read(client: TestClient, db: Session) -> None:
    _coach, trainee, workouts = _fixture(db)
    session = _start(client, trainee, workouts[0])
    version_id = session["exercises"][0]["exercise_version_id"]
    trainee.is_demo = True
    db.commit()
    # Reads are not demo-guarded (consistent with analytics) — demo trainees may inspect.
    assert (
        client.get(f"/api/v1/trainee/exercise-versions/{version_id}", headers=auth(trainee)).status_code
        == 200
    )


def test_unpublished_version_is_not_readable(client: TestClient, db: Session) -> None:
    _coach, trainee, workouts = _fixture(db)
    session = _start(client, trainee, workouts[0])
    version_id = session["exercises"][0]["exercise_version_id"]
    # Downgrade the referenced version to a draft (satisfying the publication-state CHECK).
    version = db.get(ExerciseVersion, uuid.UUID(version_id))
    assert version is not None
    version.status = ExerciseVersionStatus.DRAFT
    version.published_at = None
    version.content_hash = None
    db.commit()
    assert (
        client.get(f"/api/v1/trainee/exercise-versions/{version_id}", headers=auth(trainee)).status_code
        == 404
    )


def test_media_route_authz_returns_404_for_unreferenced_and_foreign(client: TestClient, db: Session) -> None:
    _coach, trainee, workouts = _fixture(db)
    session = _start(client, trainee, workouts[0])
    version_id = session["exercises"][0]["exercise_version_id"]
    # A media id not referenced by the version is a 404 (existence never confirmed).
    assert (
        client.get(
            f"/api/v1/trainee/exercise-versions/{version_id}/media/{uuid.uuid4()}/content",
            headers=auth(trainee),
        ).status_code
        == 404
    )
    # A foreign trainee cannot reach the version's media route at all.
    other = _make_trainee(db, "stranger2@example.com")
    assert (
        client.get(
            f"/api/v1/trainee/exercise-versions/{version_id}/media/{uuid.uuid4()}/content",
            headers=auth(other),
        ).status_code
        == 404
    )
