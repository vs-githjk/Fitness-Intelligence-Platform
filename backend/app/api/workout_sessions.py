import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    WorkoutExerciseSkipRequest,
    WorkoutSessionCompleteRequest,
    WorkoutSessionEndIncompleteRequest,
    WorkoutSessionOut,
    WorkoutSetAddRequest,
    WorkoutSetUpdateRequest,
)
from app.security import ensure_not_demo, require_trainee
from app.workout_session_services import (
    add_set,
    complete_session,
    end_session_incomplete,
    get_active_session,
    get_session,
    skip_exercise,
    start_workout,
    update_set,
)

router = APIRouter(tags=["workout execution"])


@router.post(
    "/trainee/workouts/{scheduled_workout_id}/start",
    response_model=WorkoutSessionOut,
)
def start(
    scheduled_workout_id: uuid.UUID,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return start_workout(db, trainee, scheduled_workout_id)


@router.get(
    "/trainee/workout-sessions/active",
    response_model=WorkoutSessionOut | None,
)
def active(
    trainee: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> dict | None:
    return get_active_session(db, trainee)


@router.get(
    "/trainee/workout-sessions/{session_id}",
    response_model=WorkoutSessionOut,
)
def detail(
    session_id: uuid.UUID,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    return get_session(db, trainee, session_id)


@router.put(
    "/trainee/workout-sessions/{session_id}/sets/{set_id}",
    response_model=WorkoutSessionOut,
)
def save_set(
    session_id: uuid.UUID,
    set_id: uuid.UUID,
    body: WorkoutSetUpdateRequest,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return update_set(db, trainee, session_id, set_id, body)


@router.post(
    "/trainee/workout-sessions/{session_id}/sets",
    response_model=WorkoutSessionOut,
)
def create_set(
    session_id: uuid.UUID,
    body: WorkoutSetAddRequest,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return add_set(db, trainee, session_id, body)


@router.post(
    "/trainee/workout-sessions/{session_id}/exercises/{exercise_id}/skip",
    response_model=WorkoutSessionOut,
)
def skip_session_exercise(
    session_id: uuid.UUID,
    exercise_id: uuid.UUID,
    body: WorkoutExerciseSkipRequest,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return skip_exercise(db, trainee, session_id, exercise_id, body)


@router.post(
    "/trainee/workout-sessions/{session_id}/complete",
    response_model=WorkoutSessionOut,
)
def complete(
    session_id: uuid.UUID,
    body: WorkoutSessionCompleteRequest,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return complete_session(db, trainee, session_id, body)


@router.post(
    "/trainee/workout-sessions/{session_id}/end-incomplete",
    response_model=WorkoutSessionOut,
)
def end_incomplete(
    session_id: uuid.UUID,
    body: WorkoutSessionEndIncompleteRequest,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(trainee)
    return end_session_incomplete(db, trainee, session_id, body)
