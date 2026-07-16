import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.exercise_services import (
    archive_exercise,
    create_exercise,
    create_revision,
    get_exercise,
    list_exercises,
    publish_draft,
    update_draft,
)
from app.models import ExerciseScope, ExerciseTrackingMode, User
from app.schemas import (
    ExerciseCreateRequest,
    ExerciseDetailOut,
    ExerciseDraftData,
    ExerciseSummaryOut,
)
from app.security import ensure_not_demo, require_coach

router = APIRouter(prefix="/coach/exercises", tags=["exercise library"])


@router.get("", response_model=list[ExerciseSummaryOut])
def exercises(
    include_archived: bool = Query(default=False),
    scope: ExerciseScope | None = Query(default=None),
    tracking_mode: ExerciseTrackingMode | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> list[dict]:
    return list_exercises(
        db,
        coach,
        include_archived=include_archived,
        scope=scope,
        tracking_mode=tracking_mode,
        search=search,
    )


@router.post("", response_model=ExerciseDetailOut, status_code=201)
def create(
    body: ExerciseCreateRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_exercise(db, coach, body)


@router.get("/{exercise_id}", response_model=ExerciseDetailOut)
def detail(
    exercise_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return get_exercise(db, coach, exercise_id)


@router.put("/{exercise_id}/draft", response_model=ExerciseDetailOut)
def put_draft(
    exercise_id: uuid.UUID,
    body: ExerciseDraftData,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return update_draft(db, coach, exercise_id, body)


@router.post("/{exercise_id}/publish", response_model=ExerciseDetailOut)
def publish(
    exercise_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return publish_draft(db, coach, exercise_id)


@router.post("/{exercise_id}/revisions", response_model=ExerciseDetailOut, status_code=201)
def revision(
    exercise_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_revision(db, coach, exercise_id)


@router.post("/{exercise_id}/archive", response_model=ExerciseDetailOut)
def archive(
    exercise_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return archive_exercise(db, coach, exercise_id)
