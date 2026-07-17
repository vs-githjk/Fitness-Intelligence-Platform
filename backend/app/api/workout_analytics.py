"""Workout Intelligence analytics API (Phase 7B).

All endpoints are read-only. Trainees see only their own analytics; coaches see
only actively assigned trainees. Demo accounts may inspect analytics.
"""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import require_coach, require_trainee
from app.services import assert_assignment
from app.workout_analytics_services import (
    bounded_range,
    coach_session_detail,
    coach_session_list,
    compute_adherence,
    compute_recorded_bests,
    compute_weekly_load,
    report_timezone,
)

trainee_router = APIRouter(prefix="/trainee", tags=["workout analytics"])
coach_router = APIRouter(prefix="/coach", tags=["workout analytics"])


def _range(db: Session, trainee_id: uuid.UUID, days: int, end_date: date | None):
    tz = report_timezone(db, trainee_id)
    return bounded_range(tz, days, end_date)


# --- trainee (Part I) ----------------------------------------------------


@trainee_router.get("/workout-load")
def trainee_workout_load(
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    start, end = _range(db, trainee.id, days, end_date)
    return compute_weekly_load(db, trainee.id, start, end)


@trainee_router.get("/workout-adherence")
def trainee_workout_adherence(
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    start, end = _range(db, trainee.id, days, end_date)
    return compute_adherence(db, trainee.id, start, end)


@trainee_router.get("/recorded-bests")
def trainee_recorded_bests(
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    start, end = _range(db, trainee.id, days, end_date)
    return compute_recorded_bests(db, trainee.id, start, end)


# --- coach read-only review (Part H) ------------------------------------


@coach_router.get("/trainees/{trainee_id}/workout-sessions")
def coach_trainee_sessions(
    trainee_id: uuid.UUID,
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    status: str | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    start, end = _range(db, trainee_id, days, end_date)
    return coach_session_list(db, trainee_id, start, end, status)


@coach_router.get("/workout-sessions/{session_id}")
def coach_workout_session_detail(
    session_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return coach_session_detail(db, coach.id, session_id)


@coach_router.get("/trainees/{trainee_id}/workout-load")
def coach_trainee_workout_load(
    trainee_id: uuid.UUID,
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    start, end = _range(db, trainee_id, days, end_date)
    return compute_weekly_load(db, trainee_id, start, end)


@coach_router.get("/trainees/{trainee_id}/workout-adherence")
def coach_trainee_workout_adherence(
    trainee_id: uuid.UUID,
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    start, end = _range(db, trainee_id, days, end_date)
    return compute_adherence(db, trainee_id, start, end)


@coach_router.get("/trainees/{trainee_id}/recorded-bests")
def coach_trainee_recorded_bests(
    trainee_id: uuid.UUID,
    days: int = Query(default=30),
    end_date: date | None = Query(default=None),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    assert_assignment(db, coach.id, trainee_id)
    start, end = _range(db, trainee_id, days, end_date)
    return compute_recorded_bests(db, trainee_id, start, end)
