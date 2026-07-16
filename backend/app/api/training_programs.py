import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TrainingProgramStatus, User
from app.schemas import (
    TrainingProgramCreateRequest,
    TrainingProgramDetailOut,
    TrainingProgramDraftReplaceRequest,
    TrainingProgramListOut,
)
from app.security import ensure_not_demo, require_coach
from app.training_program_services import (
    archive_training_program,
    create_training_program,
    create_training_program_revision,
    get_training_program,
    list_training_programs,
    publish_training_program_draft,
    replace_training_program_draft,
)

router = APIRouter(prefix="/coach/training-programs", tags=["training programs"])


@router.get("", response_model=TrainingProgramListOut)
def programs(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: TrainingProgramStatus | None = Query(default=TrainingProgramStatus.ACTIVE),
    goal_tag: str | None = Query(default=None, min_length=1, max_length=50),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return list_training_programs(
        db, coach, page=page, per_page=per_page, status=status, goal_tag=goal_tag, search=search
    )


@router.post("", response_model=TrainingProgramDetailOut, status_code=201)
def create(
    body: TrainingProgramCreateRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_training_program(db, coach, body)


@router.get("/{program_id}", response_model=TrainingProgramDetailOut)
def detail(
    program_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return get_training_program(db, coach, program_id)


@router.put("/{program_id}/draft", response_model=TrainingProgramDetailOut)
def put_draft(
    program_id: uuid.UUID,
    body: TrainingProgramDraftReplaceRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return replace_training_program_draft(db, coach, program_id, body)


@router.post("/{program_id}/publish", response_model=TrainingProgramDetailOut)
def publish(
    program_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return publish_training_program_draft(db, coach, program_id)


@router.post("/{program_id}/revisions", response_model=TrainingProgramDetailOut, status_code=201)
def revision(
    program_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_training_program_revision(db, coach, program_id)


@router.post("/{program_id}/archive", response_model=TrainingProgramDetailOut)
def archive(
    program_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return archive_training_program(db, coach, program_id)
