import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    SafetyCategory,
    SafetyReportStatus,
    SafetyReviewAction,
    ScheduledWorkoutStatus,
    User,
    WorkoutSafetyReport,
    WorkoutSafetyReview,
    WorkoutSessionEvent,
    WorkoutSessionEventType,
    WorkoutSessionExerciseStatus,
    WorkoutSessionStatus,
)
from app.repositories.workout_safety import WorkoutSafetyRepository
from app.repositories.workout_sessions import WorkoutSessionRepository
from app.schemas import WorkoutSafetyReportCreateRequest, WorkoutSafetyReviewRequest

CRITICAL_CATEGORIES = frozenset(
    {
        SafetyCategory.CHEST_DISCOMFORT,
        SafetyCategory.BREATHING_DIFFICULTY,
        SafetyCategory.DIZZINESS_OR_FAINTNESS,
    }
)
PAUSE_CATEGORIES = frozenset(
    {SafetyCategory.PAIN, SafetyCategory.UNUSUAL_DISCOMFORT}
)
FORCED_STOP_GUIDANCE = (
    "Stop exercising. If symptoms are severe, worsening, or continue, seek urgent "
    "professional medical assistance."
)
STANDARD_GUIDANCE = (
    "Stop or change the activity if needed. Safety reports are not monitored continuously, "
    "and the platform does not diagnose medical conditions."
)


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status, detail={"code": code, "message": message}
    )


def _event(session, actor: User, event_type: WorkoutSessionEventType, payload: dict) -> None:
    session.events.append(
        WorkoutSessionEvent(
            event_type=event_type, actor_user_id=actor.id, payload=payload
        )
    )


def _guidance(category: SafetyCategory) -> str:
    return FORCED_STOP_GUIDANCE if category in CRITICAL_CATEGORIES else STANDARD_GUIDANCE


def trainee_report_out(report: WorkoutSafetyReport) -> dict:
    exercise = report.workout_session_exercise
    return {
        "id": report.id,
        "workout_session_id": report.workout_session_id,
        "workout_session_exercise_id": report.workout_session_exercise_id,
        "workout_set_log_id": report.workout_set_log_id,
        "trainee_id": report.trainee_id,
        "category": report.category,
        "severity": report.severity,
        "note": report.note,
        "activity_stopped": report.activity_stopped,
        "occurred_at": report.occurred_at,
        "created_at": report.created_at,
        "status": report.status,
        "session_status": report.workout_session.status,
        "exercise_status": exercise.status if exercise else None,
        "guidance": _guidance(report.category),
    }


def coach_report_out(report: WorkoutSafetyReport, trainee: User) -> dict:
    session = report.workout_session
    exercise = report.workout_session_exercise
    return {
        **trainee_report_out(report),
        "trainee_name": f"{trainee.first_name} {trainee.last_name}",
        "trainee_email": trainee.email,
        "workout_name": session.scheduled_workout.workout_template_version.name,
        "scheduled_date": session.scheduled_workout.scheduled_date,
        "exercise_name": (
            exercise.prescription_snapshot.get("name") if exercise else None
        ),
        "reviews": [
            {
                "id": review.id,
                "coach_id": review.coach_id,
                "action": review.action,
                "note": review.note,
                "created_at": review.created_at,
            }
            for review in report.reviews
        ],
    }


def create_safety_report(
    db: Session,
    trainee: User,
    session_id: uuid.UUID,
    body: WorkoutSafetyReportCreateRequest,
) -> dict:
    session = WorkoutSessionRepository(db).owned_session(
        trainee.id, session_id, lock=True
    )
    if session is None:
        raise _error(404, "workout_session_not_found", "Workout session not found")
    if session.status != WorkoutSessionStatus.IN_PROGRESS:
        raise _error(
            409, "workout_session_immutable", "Ended workout sessions cannot be changed"
        )
    repository = WorkoutSafetyRepository(db)
    exercise = None
    set_log = None
    if body.workout_session_exercise_id is not None:
        exercise = repository.session_exercise(
            session.id, body.workout_session_exercise_id
        )
        if exercise is None:
            raise _error(
                404, "workout_exercise_not_found", "Workout exercise not found"
            )
    if body.workout_set_log_id is not None:
        set_log = repository.session_set(session.id, body.workout_set_log_id)
        if set_log is None:
            raise _error(404, "workout_set_not_found", "Workout set not found")
        if exercise is not None and set_log.workout_session_exercise_id != exercise.id:
            raise _error(
                422,
                "safety_report_reference_mismatch",
                "The selected set does not belong to the selected exercise",
            )
        exercise = exercise or set_log.session_exercise

    now = datetime.now(UTC)
    category = SafetyCategory(body.category)
    forced_stop = category in CRITICAL_CATEGORIES
    report = WorkoutSafetyReport(
        workout_session_id=session.id,
        workout_session_exercise_id=exercise.id if exercise else None,
        workout_set_log_id=set_log.id if set_log else None,
        trainee_id=trainee.id,
        category=category,
        severity=body.severity,
        note=body.note,
        activity_stopped=forced_stop or body.activity_stopped,
        occurred_at=body.occurred_at or now,
        created_at=now,
        status=SafetyReportStatus.OPEN,
        workout_session=session,
        workout_session_exercise=exercise,
        workout_set_log=set_log,
    )
    db.add(report)
    db.flush()
    _event(
        session,
        trainee,
        WorkoutSessionEventType.SAFETY_REPORT_SUBMITTED,
        {"report_id": str(report.id), "category": category.value},
    )

    if forced_stop:
        if exercise is not None:
            exercise.status = WorkoutSessionExerciseStatus.SAFETY_STOPPED
        session.status = WorkoutSessionStatus.SAFETY_ENDED
        session.ended_at = now
        session.scheduled_workout.status = ScheduledWorkoutStatus.PARTIAL
        _event(
            session,
            trainee,
            WorkoutSessionEventType.SESSION_SAFETY_ENDED,
            {"report_id": str(report.id), "category": category.value},
        )
    elif category in PAUSE_CATEGORIES and exercise is not None:
        exercise.status = WorkoutSessionExerciseStatus.PAUSED_FOR_SAFETY
        _event(
            session,
            trainee,
            WorkoutSessionEventType.EXERCISE_PAUSED_FOR_SAFETY,
            {"report_id": str(report.id), "exercise_id": str(exercise.id)},
        )
    session.revision += 1
    session.last_activity_at = now
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    stored = repository.trainee_reports(trainee.id, session.id)[0]
    return trainee_report_out(stored)


def list_trainee_safety_reports(
    db: Session, trainee: User, session_id: uuid.UUID
) -> list[dict]:
    session = WorkoutSessionRepository(db).owned_session(
        trainee.id, session_id, lock=False
    )
    if session is None:
        raise _error(404, "workout_session_not_found", "Workout session not found")
    return [
        trainee_report_out(item)
        for item in WorkoutSafetyRepository(db).trainee_reports(
            trainee.id, session_id
        )
    ]


def list_coach_safety_reports(
    db: Session, coach: User, status: SafetyReportStatus | None
) -> list[dict]:
    return [
        coach_report_out(report, trainee)
        for report, trainee in WorkoutSafetyRepository(db).coach_reports(
            coach.id, status.value if status else None
        )
    ]


def get_coach_safety_report(
    db: Session, coach: User, report_id: uuid.UUID
) -> dict:
    result = WorkoutSafetyRepository(db).coach_report(coach.id, report_id)
    if result is None:
        raise _error(404, "safety_report_not_found", "Safety report not found")
    return coach_report_out(*result)


def review_safety_report(
    db: Session,
    coach: User,
    report_id: uuid.UUID,
    action: SafetyReviewAction,
    body: WorkoutSafetyReviewRequest,
) -> dict:
    repository = WorkoutSafetyRepository(db)
    result = repository.coach_report(coach.id, report_id, lock=True)
    if result is None:
        raise _error(404, "safety_report_not_found", "Safety report not found")
    report, trainee = result
    if report.status == SafetyReportStatus.RESOLVED and action == SafetyReviewAction.ACKNOWLEDGED:
        raise _error(409, "safety_report_resolved", "Resolved reports cannot be acknowledged")
    review = WorkoutSafetyReview(
        workout_safety_report_id=report.id,
        coach_id=coach.id,
        action=action,
        note=body.note,
    )
    report.reviews.append(review)
    report.status = (
        SafetyReportStatus.ACKNOWLEDGED
        if action == SafetyReviewAction.ACKNOWLEDGED
        else SafetyReportStatus.RESOLVED
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    stored = repository.coach_report(coach.id, report.id)
    assert stored is not None
    return coach_report_out(stored[0], trainee)
