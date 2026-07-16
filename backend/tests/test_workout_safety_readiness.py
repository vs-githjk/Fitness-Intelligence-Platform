import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import (
    CoachTraineeAssignment,
    DailyCheckIn,
    DailyScoreSnapshot,
    Role,
    SafetyCategory,
    SafetySeverity,
    ScheduledWorkout,
    TraineeProfile,
    User,
    WorkoutReadinessContext,
    WorkoutSafetyReport,
    WorkoutSafetyReview,
    WorkoutSessionEvent,
    WorkoutSessionExercise,
    WorkoutSessionStatus,
    WorkoutTemplateVersion,
)
from app.schemas import WorkoutSafetyReportCreateRequest
from app.security import create_access_token, hash_password
from app.workout_readiness_services import readiness_preview
from app.workout_safety_services import create_safety_report
from scripts.seed import (
    seed_exercise_library,
    seed_training_assignments,
    seed_training_programs,
    seed_workout_execution,
    seed_workout_safety_examples,
    seed_workout_templates,
)


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user)}"}


def phase_fixture(db: Session) -> tuple[User, User, list[ScheduledWorkout]]:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    trainee = User(
        email="phase7a@example.com",
        password_hash=hash_password("PhaseSeven123!"),
        first_name="Safety",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(trainee)
    db.flush()
    db.add_all(
        [
            TraineeProfile(user_id=trainee.id, timezone="UTC"),
            CoachTraineeAssignment(
                coach_id=coach.id, trainee_id=trainee.id, status="active"
            ),
        ]
    )
    db.commit()
    seed_exercise_library(db, coach)
    seed_workout_templates(db, coach)
    seed_training_programs(db, coach)
    seed_training_assignments(
        db, coach, [trainee], date.today(), include_future=False
    )
    workouts = list(
        db.scalars(
            select(ScheduledWorkout)
            .join(WorkoutTemplateVersion)
            .where(ScheduledWorkout.trainee_id == trainee.id)
            .order_by(ScheduledWorkout.scheduled_date, ScheduledWorkout.display_order)
        ).all()
    )
    assert len(workouts) >= 4
    return coach, trainee, workouts


def add_snapshot(
    db: Session,
    trainee: User,
    local_date: date,
    *,
    score: float,
    calculated_at: datetime,
    version: str = "daily-intelligence-v1",
) -> DailyScoreSnapshot:
    check_in = db.scalar(
        select(DailyCheckIn).where(
            DailyCheckIn.trainee_id == trainee.id,
            DailyCheckIn.local_date == local_date,
        )
    )
    if check_in is None:
        check_in = DailyCheckIn(
            trainee_id=trainee.id,
            local_date=local_date,
            timezone="UTC",
            sleep_hours=7,
            sleep_quality=4,
            wake_refreshed=True,
            soreness=2,
            fatigue=2,
            stress=3,
            steps=8000,
            exercised=False,
            exercise_minutes=None,
            session_rpe=None,
            activity_types=[],
            water_liters=2,
            calories_consumed=None,
            protein_grams=None,
            nutrition_adherence=None,
            overall_feeling="good",
            note=None,
        )
        db.add(check_in)
        db.flush()
    snapshot = DailyScoreSnapshot(
        trainee_id=trainee.id,
        daily_check_in_id=check_in.id,
        local_date=local_date,
        recovery_score=score,
        activity_score=score,
        nutrition_score=None,
        readiness_score=score,
        readiness_state="maintain" if score >= 60 else "reduce_intensity",
        scoring_version=version,
        calculation_payload={},
        calculated_at=calculated_at,
    )
    db.add(snapshot)
    db.commit()
    return snapshot


def start(client: TestClient, trainee: User, workout: ScheduledWorkout) -> dict:
    response = client.post(
        f"/api/v1/trainee/workouts/{workout.id}/start", headers=auth(trainee)
    )
    assert response.status_code == 200, response.text
    return response.json()


def report(
    client: TestClient,
    trainee: User,
    session: dict,
    category: str,
    severity: str = "moderate",
) -> object:
    return client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/safety-reports",
        headers=auth(trainee),
        json={
            "workout_session_exercise_id": session["exercises"][0]["id"],
            "workout_set_log_id": session["exercises"][0]["sets"][0]["id"],
            "category": category,
            "severity": severity,
            "note": "Synthetic safety test.",
            "activity_stopped": True,
        },
    )


def test_readiness_latest_lookup_staleness_unavailable_and_tie_break(
    db: Session,
) -> None:
    _, trainee, workouts = phase_fixture(db)
    scheduled = workouts[-1]
    assert readiness_preview(db, scheduled)["available"] is False
    source_date = scheduled.scheduled_date - timedelta(days=2)
    earlier = add_snapshot(
        db,
        trainee,
        source_date,
        score=45,
        calculated_at=datetime(2026, 7, 14, 8, tzinfo=UTC),
        version="daily-intelligence-v1",
    )
    latest = add_snapshot(
        db,
        trainee,
        source_date,
        score=72,
        calculated_at=datetime(2026, 7, 14, 9, tzinfo=UTC),
        version="daily-intelligence-v1-recalculation",
    )
    future = add_snapshot(
        db,
        trainee,
        scheduled.scheduled_date + timedelta(days=1),
        score=99,
        calculated_at=datetime(2026, 7, 18, 9, tzinfo=UTC),
    )
    preview = readiness_preview(db, scheduled)
    assert preview["daily_score_snapshot_id"] == latest.id
    assert preview["daily_score_snapshot_id"] not in {earlier.id, future.id}
    assert preview["readiness_score"] == 72
    assert preview["age_days"] == 2
    assert preview["is_stale"] is True


@pytest.mark.parametrize("age,stale", [(0, False), (1, False), (2, True)])
def test_readiness_age_boundaries(db: Session, age: int, stale: bool) -> None:
    _, trainee, workouts = phase_fixture(db)
    scheduled = workouts[-1]
    add_snapshot(
        db,
        trainee,
        scheduled.scheduled_date - timedelta(days=age),
        score=68,
        calculated_at=datetime.now(UTC),
    )
    preview = readiness_preview(db, scheduled)
    assert preview["age_days"] == age
    assert preview["is_stale"] is stale


def test_start_captures_immutable_readiness_without_changing_prescription(
    client: TestClient, db: Session
) -> None:
    _, trainee, workouts = phase_fixture(db)
    scheduled = workouts[-1]
    snapshot = add_snapshot(
        db,
        trainee,
        scheduled.scheduled_date,
        score=74,
        calculated_at=datetime.now(UTC),
    )
    target_rpe = scheduled.target_session_rpe
    session = start(client, trainee, scheduled)
    context = session["readiness_context"]
    assert context["available"] is True
    assert context["readiness_score"] == 74
    assert context["age_days"] == 0
    assert context["captured_at"] is not None
    assert session["target_session_rpe"] == target_rpe

    snapshot.readiness_score = 20
    snapshot.readiness_state = "recovery_recommended"
    snapshot.calculated_at = datetime.now(UTC) + timedelta(hours=1)
    db.commit()
    stored = client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}", headers=auth(trainee)
    ).json()
    assert stored["readiness_context"]["readiness_score"] == 74
    assert stored["readiness_context"]["readiness_state"] == "maintain"
    assert db.scalar(select(func.count(WorkoutReadinessContext.id))) == 1


def test_start_captures_immutable_unavailable_readiness(
    client: TestClient, db: Session
) -> None:
    _, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[-1])
    assert session["readiness_context"]["available"] is False
    assert session["readiness_context"]["readiness_score"] is None


@pytest.mark.parametrize(
    "category",
    ["chest_discomfort", "breathing_difficulty", "dizziness_or_faintness"],
)
def test_critical_reports_force_terminal_safety_end(
    client: TestClient, db: Session, category: str
) -> None:
    _, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[0])
    created = report(client, trainee, session, category)
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["session_status"] == "safety_ended"
    assert payload["exercise_status"] == "safety_stopped"
    assert payload["activity_stopped"] is True
    assert "seek urgent professional medical assistance" in payload["guidance"]

    stored = client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}", headers=auth(trainee)
    ).json()
    assert stored["status"] == "safety_ended"
    assert stored["scheduled_workout_status"] == "partial"
    assert {item["event_type"] for item in stored["events"]} >= {
        "safety_report_submitted",
        "session_safety_ended",
    }
    denied = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/"
        f"{session['exercises'][0]['sets'][0]['id']}",
        headers=auth(trainee),
        json={"expected_session_revision": stored["revision"], "status": "skipped"},
    )
    assert denied.status_code == 409


def test_pain_pauses_exercise_until_skip_or_end(
    client: TestClient, db: Session
) -> None:
    _, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[0])
    created = report(client, trainee, session, "pain")
    assert created.status_code == 201
    assert created.json()["exercise_status"] == "paused_for_safety"
    latest = client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}", headers=auth(trainee)
    ).json()
    set_denied = client.put(
        f"/api/v1/trainee/workout-sessions/{session['id']}/sets/"
        f"{session['exercises'][0]['sets'][0]['id']}",
        headers=auth(trainee),
        json={"expected_session_revision": latest["revision"], "status": "skipped"},
    )
    assert set_denied.status_code == 409
    skipped = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/exercises/"
        f"{session['exercises'][0]['id']}/skip",
        headers=auth(trainee),
        json={
            "expected_session_revision": latest["revision"],
            "reason": "discomfort",
        },
    )
    assert skipped.status_code == 200
    assert skipped.json()["exercises"][0]["status"] == "skipped"


def test_other_report_preserves_execution_and_validates_input_and_ownership(
    client: TestClient, db: Session
) -> None:
    coach, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[0])
    created = report(client, trainee, session, "equipment_or_environment", "mild")
    assert created.status_code == 201
    assert created.json()["session_status"] == "in_progress"
    assert created.json()["exercise_status"] != "paused_for_safety"

    invalid = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/safety-reports",
        headers=auth(trainee),
        json={"category": "diagnosis", "severity": "extreme", "note": "x" * 501},
    )
    assert invalid.status_code == 422
    other = User(
        email="unrelated-trainee@example.com",
        password_hash=hash_password("Unrelated123!"),
        first_name="Other",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(other)
    db.commit()
    denied = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/safety-reports",
        headers=auth(other),
        json={"category": "other", "severity": "mild"},
    )
    assert denied.status_code == 404
    assert client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/safety-reports",
        headers=auth(coach),
        json={"category": "other", "severity": "mild"},
    ).status_code == 403


def test_coach_review_is_append_only_scoped_and_hidden_from_trainee(
    client: TestClient, db: Session
) -> None:
    coach, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[0])
    report_id = report(client, trainee, session, "loss_of_balance").json()["id"]
    queue = client.get("/api/v1/coach/safety-reports", headers=auth(coach))
    assert queue.status_code == 200
    assert [item["id"] for item in queue.json()] == [report_id]
    assert client.get(
        "/api/v1/coach/safety-reports?status=resolved", headers=auth(coach)
    ).json() == []

    acknowledged = client.post(
        f"/api/v1/coach/safety-reports/{report_id}/acknowledge",
        headers=auth(coach),
        json={"note": "Reviewed privately."},
    )
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
    resolved = client.post(
        f"/api/v1/coach/safety-reports/{report_id}/resolve",
        headers=auth(coach),
        json={"note": "External follow-up completed."},
    )
    assert resolved.status_code == 200
    assert [item["action"] for item in resolved.json()["reviews"]] == [
        "acknowledged",
        "resolved",
    ]
    trainee_view = client.get(
        f"/api/v1/trainee/workout-sessions/{session['id']}/safety-reports",
        headers=auth(trainee),
    ).json()
    assert "reviews" not in trainee_view[0]
    assert "Reviewed privately" not in str(trainee_view)

    other_coach = db.scalar(select(User).where(User.email == "other@example.com"))
    assert other_coach is not None
    assert client.get(
        f"/api/v1/coach/safety-reports/{report_id}", headers=auth(other_coach)
    ).status_code == 404
    assignment = db.scalar(
        select(CoachTraineeAssignment).where(
            CoachTraineeAssignment.coach_id == coach.id,
            CoachTraineeAssignment.trainee_id == trainee.id,
        )
    )
    assert assignment is not None
    assignment.status = "inactive"
    db.commit()
    assert client.get(
        f"/api/v1/coach/safety-reports/{report_id}", headers=auth(coach)
    ).status_code == 404
    assert db.scalar(select(func.count(WorkoutSafetyReview.id))) == 2


def test_demo_guards_all_safety_mutations(
    client: TestClient, db: Session
) -> None:
    coach, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[0])
    report_id = report(client, trainee, session, "other").json()["id"]
    trainee.is_demo = True
    coach.is_demo = True
    db.commit()
    denied = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/safety-reports",
        headers=auth(trainee),
        json={"category": "other", "severity": "mild"},
    )
    assert denied.status_code == 403
    for action in ("acknowledge", "resolve"):
        response = client.post(
            f"/api/v1/coach/safety-reports/{report_id}/{action}",
            headers=auth(coach),
            json={},
        )
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "demo_read_only"

    assert db.scalar(select(func.count(WorkoutSafetyReport.id))) == 1
    assert db.scalar(select(func.count(WorkoutSessionEvent.id))) >= 2


def test_safety_report_transaction_rolls_back_atomically(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _, trainee, workouts = phase_fixture(db)
    session = start(client, trainee, workouts[0])

    def fail_commit() -> None:
        raise RuntimeError("synthetic commit failure")

    monkeypatch.setattr(db, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="synthetic commit failure"):
        create_safety_report(
            db,
            trainee,
            uuid.UUID(session["id"]),
            WorkoutSafetyReportCreateRequest(
                workout_session_exercise_id=session["exercises"][0]["id"],
                category=SafetyCategory.CHEST_DISCOMFORT,
                severity=SafetySeverity.SEVERE,
                activity_stopped=True,
            ),
        )
    assert db.scalar(select(func.count(WorkoutSafetyReport.id))) == 0
    assert db.scalar(select(func.count(WorkoutSessionEvent.id))) == 1


def test_safety_demo_seed_is_idempotent(db: Session) -> None:
    coach, trainee, _ = phase_fixture(db)
    seed_workout_execution(db, trainee)
    seed_workout_safety_examples(db, coach, trainee)
    first_reports = db.scalar(select(func.count(WorkoutSafetyReport.id)))
    first_reviews = db.scalar(select(func.count(WorkoutSafetyReview.id)))
    seed_workout_safety_examples(db, coach, trainee)
    assert first_reports == 4
    assert first_reviews == 3
    assert db.scalar(select(func.count(WorkoutSafetyReport.id))) == first_reports
    assert db.scalar(select(func.count(WorkoutSafetyReview.id))) == first_reviews

    critical = db.scalar(
        select(WorkoutSafetyReport).where(
            WorkoutSafetyReport.category == SafetyCategory.CHEST_DISCOMFORT
        )
    )
    paused = db.scalar(
        select(WorkoutSessionExercise).where(
            WorkoutSessionExercise.status == "paused_for_safety"
        )
    )
    assert critical is not None and paused is not None
    critical.workout_session.status = WorkoutSessionStatus.ENDED_INCOMPLETE
    critical.workout_session.scheduled_workout.status = "partial"
    critical.workout_session_exercise.status = "skipped"
    paused.status = "skipped"
    db.execute(delete(WorkoutSafetyReview))
    db.execute(delete(WorkoutSafetyReport))
    db.commit()

    seed_workout_safety_examples(db, coach, trainee)
    assert db.scalar(select(func.count(WorkoutSafetyReport.id))) == 4
    assert db.scalar(select(func.count(WorkoutSafetyReview.id))) == 3
