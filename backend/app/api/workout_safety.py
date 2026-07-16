import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SafetyReportStatus, SafetyReviewAction, User
from app.schemas import (
    CoachWorkoutSafetyReportOut,
    WorkoutSafetyReportCreateRequest,
    WorkoutSafetyReportOut,
    WorkoutSafetyReviewRequest,
)
from app.security import ensure_not_demo, require_coach, require_trainee
from app.workout_safety_services import (
    create_safety_report,
    get_coach_safety_report,
    list_coach_safety_reports,
    list_trainee_safety_reports,
    review_safety_report,
)

router = APIRouter(tags=["workout safety"])


@router.post(
    "/trainee/workout-sessions/{session_id}/safety-reports",
    response_model=WorkoutSafetyReportOut,
    status_code=201,
)
def create_report(
    session_id: uuid.UUID,
    body: WorkoutSafetyReportCreateRequest,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return create_safety_report(db, trainee, session_id, body)


@router.get(
    "/trainee/workout-sessions/{session_id}/safety-reports",
    response_model=list[WorkoutSafetyReportOut],
)
def trainee_reports(
    session_id: uuid.UUID,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_trainee_safety_reports(db, trainee, session_id)


@router.get(
    "/coach/safety-reports", response_model=list[CoachWorkoutSafetyReportOut]
)
def coach_reports(
    status: SafetyReportStatus | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_coach_safety_reports(db, coach, status)


@router.get(
    "/coach/safety-reports/{report_id}",
    response_model=CoachWorkoutSafetyReportOut,
)
def coach_report_detail(
    report_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return get_coach_safety_report(db, coach, report_id)


def _review(
    db: Session,
    coach: User,
    report_id: uuid.UUID,
    action: SafetyReviewAction,
    body: WorkoutSafetyReviewRequest,
) -> dict:
    ensure_not_demo(coach)
    return review_safety_report(db, coach, report_id, action, body)


@router.post(
    "/coach/safety-reports/{report_id}/acknowledge",
    response_model=CoachWorkoutSafetyReportOut,
)
def acknowledge(
    report_id: uuid.UUID,
    body: WorkoutSafetyReviewRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return _review(db, coach, report_id, SafetyReviewAction.ACKNOWLEDGED, body)


@router.post(
    "/coach/safety-reports/{report_id}/resolve",
    response_model=CoachWorkoutSafetyReportOut,
)
def resolve(
    report_id: uuid.UUID,
    body: WorkoutSafetyReviewRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return _review(db, coach, report_id, SafetyReviewAction.RESOLVED, body)
