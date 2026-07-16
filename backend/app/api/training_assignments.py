import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import (
    TrainingAssignmentCreateRequest,
    TrainingAssignmentPreviewOut,
    TrainingAssignmentPreviewRequest,
    TrainingAssignmentWorkspaceOut,
)
from app.security import ensure_not_demo, require_coach, require_trainee
from app.training_assignment_services import (
    cancel_future_training_assignment,
    coach_assignment_workspace,
    create_training_assignment,
    preview_training_assignment,
    trainee_assignment_workspace,
)

router = APIRouter(tags=["training assignments"])


@router.get(
    "/coach/trainees/{trainee_id}/training-assignment",
    response_model=TrainingAssignmentWorkspaceOut,
)
def coach_workspace(
    trainee_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return coach_assignment_workspace(db, coach, trainee_id)


@router.post(
    "/coach/trainees/{trainee_id}/training-assignments/preview",
    response_model=TrainingAssignmentPreviewOut,
)
def preview(
    trainee_id: uuid.UUID,
    body: TrainingAssignmentPreviewRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return preview_training_assignment(db, coach, trainee_id, body)


@router.post(
    "/coach/trainees/{trainee_id}/training-assignments",
    response_model=TrainingAssignmentWorkspaceOut,
    status_code=201,
)
def create(
    trainee_id: uuid.UUID,
    body: TrainingAssignmentCreateRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_training_assignment(db, coach, trainee_id, body)


@router.post(
    "/coach/training-assignments/{assignment_id}/cancel",
    response_model=TrainingAssignmentWorkspaceOut,
)
def cancel(
    assignment_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return cancel_future_training_assignment(db, coach, assignment_id)


@router.get("/trainee/program", response_model=TrainingAssignmentWorkspaceOut)
def trainee_program(
    trainee: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> dict:
    return trainee_assignment_workspace(db, trainee)
