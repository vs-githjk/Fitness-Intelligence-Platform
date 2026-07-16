from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import ScheduledWorkout, WorkoutReadinessContext, WorkoutSession
from app.repositories.workout_safety import WorkoutSafetyRepository

READINESS_GUIDANCE = (
    "Readiness is contextual guidance based on your latest available daily check-in. "
    "It does not provide medical clearance and does not change this workout automatically."
)


def readiness_out(context: WorkoutReadinessContext) -> dict:
    return {
        "id": context.id,
        "scheduled_workout_id": context.scheduled_workout_id,
        "workout_session_id": context.workout_session_id,
        "daily_score_snapshot_id": context.daily_score_snapshot_id,
        "available": context.is_available,
        "readiness_score": context.readiness_score,
        "readiness_state": context.readiness_state,
        "source_local_date": context.source_local_date,
        "calculation_timestamp": context.calculation_timestamp,
        "scoring_version": context.scoring_version,
        "age_days": context.age_days,
        "is_stale": context.is_stale,
        "captured_at": context.captured_at,
        "guidance": READINESS_GUIDANCE,
    }


def readiness_preview(db: Session, scheduled: ScheduledWorkout) -> dict:
    if scheduled.readiness_context is not None:
        return readiness_out(scheduled.readiness_context)
    snapshot = WorkoutSafetyRepository(db).latest_readiness_snapshot(
        scheduled.trainee_id, scheduled.scheduled_date
    )
    if snapshot is None:
        return {
            "id": None,
            "scheduled_workout_id": scheduled.id,
            "workout_session_id": None,
            "daily_score_snapshot_id": None,
            "available": False,
            "readiness_score": None,
            "readiness_state": None,
            "source_local_date": None,
            "calculation_timestamp": None,
            "scoring_version": None,
            "age_days": None,
            "is_stale": None,
            "captured_at": None,
            "guidance": READINESS_GUIDANCE,
        }
    age_days = (scheduled.scheduled_date - snapshot.local_date).days
    return {
        "id": None,
        "scheduled_workout_id": scheduled.id,
        "workout_session_id": None,
        "daily_score_snapshot_id": snapshot.id,
        "available": True,
        "readiness_score": snapshot.readiness_score,
        "readiness_state": snapshot.readiness_state,
        "source_local_date": snapshot.local_date,
        "calculation_timestamp": snapshot.calculated_at,
        "scoring_version": snapshot.scoring_version,
        "age_days": age_days,
        "is_stale": age_days >= 2,
        "captured_at": None,
        "guidance": READINESS_GUIDANCE,
    }


def capture_readiness_context(
    db: Session, session: WorkoutSession, captured_at: datetime | None = None
) -> WorkoutReadinessContext:
    if session.readiness_context is not None:
        return session.readiness_context
    preview = readiness_preview(db, session.scheduled_workout)
    context = WorkoutReadinessContext(
        scheduled_workout_id=session.scheduled_workout_id,
        workout_session_id=session.id,
        trainee_id=session.trainee_id,
        daily_score_snapshot_id=preview["daily_score_snapshot_id"],
        is_available=preview["available"],
        readiness_score=preview["readiness_score"],
        readiness_state=preview["readiness_state"],
        source_local_date=preview["source_local_date"],
        calculation_timestamp=preview["calculation_timestamp"],
        scoring_version=preview["scoring_version"],
        age_days=preview["age_days"],
        is_stale=preview["is_stale"],
        captured_at=captured_at or datetime.now(UTC),
    )
    session.readiness_context = context
    db.add(context)
    db.flush()
    return context
