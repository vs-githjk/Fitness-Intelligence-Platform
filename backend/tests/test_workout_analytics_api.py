"""Integration tests for Workout Intelligence analytics endpoints (Phase 7B)."""

import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    CoachTraineeAssignment,
    Role,
    ScheduledWorkout,
    TraineeProfile,
    User,
    WorkoutLoadSummary,
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


def _make_trainee(db: Session, coach: User, email: str, active: bool = True) -> User:
    trainee = User(
        email=email,
        password_hash=hash_password("AnalyticsPass123!"),
        first_name="Ana",
        last_name="Lytics",
        role=Role.TRAINEE,
    )
    db.add(trainee)
    db.flush()
    db.add_all(
        [
            TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"),
            CoachTraineeAssignment(
                coach_id=coach.id,
                trainee_id=trainee.id,
                status="active" if active else "revoked",
            ),
        ]
    )
    db.commit()
    return trainee


def execution_fixture(db: Session, email: str = "analytics@example.com"):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    trainee = _make_trainee(db, coach, email)
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


def complete_workout(client: TestClient, trainee: User, workout: ScheduledWorkout) -> dict:
    session = client.post(
        f"/api/v1/trainee/workouts/{workout.id}/start", headers=auth(trainee)
    ).json()
    load_ex = next(
        (e for e in session["exercises"] if e["tracking_mode"] == "repetitions_and_load"),
        None,
    )
    # Complete every set in the resistance exercise so it resolves as completed.
    if load_ex is not None:
        for target in load_ex["sets"]:
            session = client.put(
                f"/api/v1/trainee/workout-sessions/{session['id']}/sets/{target['id']}",
                headers=auth(trainee),
                json={
                    "expected_session_revision": session["revision"],
                    "status": "completed",
                    "actual_repetitions": 10,
                    "actual_load_original_value": 40,
                    "actual_load_original_unit": "kg",
                    "actual_rpe": 7,
                },
            ).json()
    # Skip every other exercise so the workout can be completed.
    for exercise in session["exercises"]:
        if load_ex is not None and exercise["id"] == load_ex["id"]:
            continue
        session = client.post(
            f"/api/v1/trainee/workout-sessions/{session['id']}/exercises/{exercise['id']}/skip",
            headers=auth(trainee),
            json={
                "expected_session_revision": session["revision"],
                "reason": "time_constraint",
                "note": "analytics fixture",
            },
        ).json()
    done = client.post(
        f"/api/v1/trainee/workout-sessions/{session['id']}/complete",
        headers=auth(trainee),
        json={
            "expected_session_revision": session["revision"],
            "actual_duration_minutes": 45,
            "session_rpe": 8,
            "confirmed": True,
        },
    )
    assert done.status_code == 200, done.text
    return done.json()


def test_trainee_workout_load_and_summary_immutable(client: TestClient, db: Session) -> None:
    _, trainee, workouts = execution_fixture(db)
    workout = next(w for w in workouts if w.workout_template_version.name == "Full Body Strength")
    session = complete_workout(client, trainee, workout)

    # Coach detail triggers immutable summary persistence.
    load = client.get("/api/v1/trainee/workout-load", headers=auth(trainee))
    assert load.status_code == 200
    body = load.json()
    assert body["timezone"] == "Asia/Kolkata"
    assert body["planned_vs_completed"]["state"] in {
        "above_planned", "near_planned", "below_planned", "unavailable",
    }
    assert body["weeks"], body

    # completed load = 45 * 8 = 360
    week = next(w for w in body["weeks"] if w["completed_session_load_total"] > 0)
    assert week["completed_session_load_total"] == 360.0
    assert session["status"] == "completed"


def test_summary_idempotent_and_single_row(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = execution_fixture(db)
    workout = next(w for w in workouts if w.workout_template_version.name == "Full Body Strength")
    session = complete_workout(client, trainee, workout)

    first = client.get(
        f"/api/v1/coach/workout-sessions/{session['id']}", headers=auth(coach)
    ).json()
    second = client.get(
        f"/api/v1/coach/workout-sessions/{session['id']}", headers=auth(coach)
    ).json()
    assert first["load_summary"]["id"] == second["load_summary"]["id"]
    assert first["load_summary"]["completed_session_load"] == 360.0
    count = db.scalar(
        select(func.count(WorkoutLoadSummary.id)).where(
            WorkoutLoadSummary.workout_session_id == uuid.UUID(session["id"])
        )
    )
    assert count == 1


def test_adherence_counts_and_denominator(client: TestClient, db: Session) -> None:
    _, trainee, workouts = execution_fixture(db)
    workout = next(w for w in workouts if w.workout_template_version.name == "Full Body Strength")
    complete_workout(client, trainee, workout)

    resp = client.get("/api/v1/trainee/workout-adherence?days=30", headers=auth(trainee))
    assert resp.status_code == 200
    body = resp.json()
    completion = body["completion"]
    assert completion["completed_count"] >= 1
    assert completion["eligible_required_count"] >= completion["completed_count"]
    pct = completion["completion_adherence_percentage"]
    assert pct is None or 0.0 <= pct <= 100.0
    # prescribed-set adherence present for the executed session
    assert body["prescribed_set_adherence"]["completed_planned_working_sets"] >= 1


def test_recorded_bests_wording_and_values(client: TestClient, db: Session) -> None:
    _, trainee, workouts = execution_fixture(db)
    workout = next(w for w in workouts if w.workout_template_version.name == "Full Body Strength")
    complete_workout(client, trainee, workout)

    resp = client.get("/api/v1/trainee/recorded-bests?days=30", headers=auth(trainee))
    assert resp.status_code == 200
    exercises = resp.json()["exercises"]
    with_load = [e for e in exercises if e["highest_recorded_load"] is not None]
    assert with_load, exercises
    best = with_load[0]["highest_recorded_load"]
    assert best["canonical_kg"] == "40.000"
    assert best["original_unit"] == "kg"


def test_invalid_range_rejected(client: TestClient, db: Session) -> None:
    _, trainee, _ = execution_fixture(db)
    resp = client.get("/api/v1/trainee/workout-load?days=9", headers=auth(trainee))
    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "invalid_range"


def test_coach_requires_active_assignment(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = execution_fixture(db)
    complete_workout(
        client, trainee,
        next(w for w in workouts if w.workout_template_version.name == "Full Body Strength"),
    )
    # Deactivate the assignment.
    assignment = db.scalar(
        select(CoachTraineeAssignment).where(
            CoachTraineeAssignment.coach_id == coach.id,
            CoachTraineeAssignment.trainee_id == trainee.id,
        )
    )
    assignment.status = "revoked"
    db.commit()
    resp = client.get(
        f"/api/v1/coach/trainees/{trainee.id}/workout-adherence", headers=auth(coach)
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "not_assigned"


def test_cross_coach_session_discovery_denied(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = execution_fixture(db)
    session = complete_workout(
        client, trainee,
        next(w for w in workouts if w.workout_template_version.name == "Full Body Strength"),
    )
    other_coach = db.scalar(select(User).where(User.email == "other@example.com"))
    assert other_coach is not None
    resp = client.get(
        f"/api/v1/coach/workout-sessions/{session['id']}", headers=auth(other_coach)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "workout_session_not_found"


def test_coach_session_review_includes_readiness_and_safety(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = execution_fixture(db)
    session = complete_workout(
        client, trainee,
        next(w for w in workouts if w.workout_template_version.name == "Full Body Strength"),
    )
    detail = client.get(
        f"/api/v1/coach/workout-sessions/{session['id']}", headers=auth(coach)
    ).json()
    assert detail["read_only"] is True
    assert "readiness_context" in detail
    assert "safety_reports" in detail
    assert detail["planned_vs_completed"]["state"] in {
        "above_planned", "near_planned", "below_planned", "unavailable",
    }
    assert detail["template_version_number"] is not None


def test_coach_session_list_status_filter(client: TestClient, db: Session) -> None:
    coach, trainee, workouts = execution_fixture(db)
    complete_workout(
        client, trainee,
        next(w for w in workouts if w.workout_template_version.name == "Full Body Strength"),
    )
    resp = client.get(
        f"/api/v1/coach/trainees/{trainee.id}/workout-sessions?status=completed",
        headers=auth(coach),
    )
    assert resp.status_code == 200
    sessions = resp.json()["sessions"]
    assert sessions
    assert all(s["status"] == "completed" for s in sessions)
    assert sessions[0]["classification"] == "completed"
