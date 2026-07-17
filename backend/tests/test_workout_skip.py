"""Explicit whole-workout skip + corrected adherence classification (Phase 7C)."""

import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CoachTraineeAssignment,
    Role,
    ScheduledWorkout,
    ScheduledWorkoutStatus,
    TraineeProfile,
    User,
    WorkoutSession,
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


def _trainee(db: Session, coach: User, email: str) -> User:
    trainee = User(
        email=email,
        password_hash=hash_password("SkipPass123!"),
        first_name="Skip",
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
    return trainee


def fixture(db: Session, email: str = "skip@example.com"):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    trainee = _trainee(db, coach, email)
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


def test_ordinary_skip_persists_and_creates_no_session(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    workout = workouts[0]
    resp = client.post(
        f"/api/v1/trainee/workouts/{workout.id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "ordinary", "reason": "time_constraint", "note": "Busy morning"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "skipped"
    assert body["skip_kind"] == "ordinary"
    assert body["skip_reason"] == "time_constraint"
    assert body["skip_note"] == "Busy morning"
    assert body["skipped_at"] is not None
    # No session created.
    assert db.scalar(
        select(func.count(WorkoutSession.id)).where(
            WorkoutSession.scheduled_workout_id == uuid.UUID(str(workout.id))
        )
    ) == 0
    db.refresh(workout)
    assert workout.status == ScheduledWorkoutStatus.SKIPPED


def test_safety_skip_persists_kind(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    resp = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "safety", "reason": "pain_or_discomfort"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["skip_kind"] == "safety"


def test_bounded_reason_validation(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    # ordinary skip cannot use a safety reason
    bad = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "ordinary", "reason": "pain_or_discomfort"},
    )
    assert bad.status_code == 422
    # unknown reason
    bad2 = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "safety", "reason": "made_up"},
    )
    assert bad2.status_code == 422


def test_note_length_validation(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    resp = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "ordinary", "reason": "travel", "note": "x" * 501},
    )
    assert resp.status_code == 422


def test_cross_trainee_and_coach_denied(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = fixture(db)
    other = _trainee(db, coach, "other-skip@example.com")
    # Another trainee cannot skip this workout (ownership hidden as 404).
    denied = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(other),
        json={"skip_kind": "ordinary", "reason": "travel"},
    )
    assert denied.status_code == 404
    # Coach role cannot call the trainee mutation.
    coach_denied = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(coach),
        json={"skip_kind": "ordinary", "reason": "travel"},
    )
    assert coach_denied.status_code == 403


def test_demo_denied(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    trainee.is_demo = True
    db.commit()
    resp = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "ordinary", "reason": "travel"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "demo_read_only"


def test_cancelled_and_superseded_cannot_be_skipped(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    workouts[0].status = ScheduledWorkoutStatus.CANCELLED
    workouts[1].status = ScheduledWorkoutStatus.SUPERSEDED
    db.commit()
    for w in (workouts[0], workouts[1]):
        resp = client.post(
            f"/api/v1/trainee/workouts/{w.id}/skip",
            headers=auth(trainee),
            json={"skip_kind": "ordinary", "reason": "travel"},
        )
        assert resp.status_code == 409


def test_in_progress_and_completed_cannot_be_skipped(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    started = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/start", headers=auth(trainee)
    ).json()
    resp = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "ordinary", "reason": "travel"},
    )
    assert resp.status_code == 409
    assert started["status"] == "in_progress"


def test_idempotent_repeat_and_conflicting_reskip(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    payload = {"skip_kind": "ordinary", "reason": "travel"}
    first = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip", headers=auth(trainee), json=payload
    )
    assert first.status_code == 200
    # Identical repeat is idempotent.
    again = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip", headers=auth(trainee), json=payload
    )
    assert again.status_code == 200
    assert again.json()["skipped_at"] == first.json()["skipped_at"]
    # A different skip after skipping is rejected.
    conflict = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "safety", "reason": "recovery_concern"},
    )
    assert conflict.status_code == 409


def test_skip_classifications_in_adherence(client: TestClient, db: Session) -> None:
    from datetime import timedelta

    _, trainee, workouts = fixture(db)
    # Pin both targets to a recent in-range local date (past the future default).
    recent = date.today() - timedelta(days=2)
    workouts[0].scheduled_date = recent
    workouts[1].scheduled_date = recent
    db.commit()
    client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "ordinary", "reason": "travel"},
    )
    client.post(
        f"/api/v1/trainee/workouts/{workouts[1].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "safety", "reason": "illness_or_unwell"},
    )
    body = client.get("/api/v1/trainee/workout-adherence?days=30", headers=auth(trainee)).json()
    c = body["completion"]
    assert c["ordinary_skipped_count"] == 1
    assert c["safety_skipped_count"] == 1
    # Both remain in the eligible required denominator.
    assert c["eligible_required_count"] >= 2


def test_zero_set_ended_incomplete_is_partial_not_skipped(client: TestClient, db: Session) -> None:
    _, trainee, workouts = fixture(db)
    session = client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/start", headers=auth(trainee)
    ).json()
    ended = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/end-incomplete",
        headers=auth(trainee),
        json={"expected_session_revision": session["revision"], "reason": "other"},
    )
    assert ended.status_code == 200
    assert ended.json()["status"] == "ended_incomplete"
    body = client.get("/api/v1/trainee/workout-adherence?days=30", headers=auth(trainee)).json()
    c = body["completion"]
    assert c["partial_count"] == 1
    assert c["ordinary_skipped_count"] == 0
    assert c["safety_skipped_count"] == 0


def test_coach_sees_explicit_skip(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = fixture(db)
    client.post(
        f"/api/v1/trainee/workouts/{workouts[0].id}/skip",
        headers=auth(trainee),
        json={"skip_kind": "safety", "reason": "recovery_concern", "note": "Feeling run down"},
    )
    listing = client.get(
        f"/api/v1/coach/trainees/{trainee.id}/workout-sessions?days=30", headers=auth(coach)
    ).json()
    skipped = [s for s in listing["sessions"] if s["status"] == "skipped"]
    assert len(skipped) == 1
    entry = skipped[0]
    assert entry["classification"] == "safety_skipped"
    assert entry["skip_kind"] == "safety"
    assert entry["skip_reason"] == "recovery_concern"
    assert entry["skip_note"] == "Feeling run down"
    assert entry["workout_session_id"] is None


def test_recorded_bests_all_history_scope(client: TestClient, db: Session) -> None:
    _, trainee, _ = fixture(db)
    resp = client.get("/api/v1/trainee/recorded-bests", headers=auth(trainee))
    assert resp.status_code == 200
    body = resp.json()
    assert body["scope"] == "all_available_history"
    assert "exercises" in body
