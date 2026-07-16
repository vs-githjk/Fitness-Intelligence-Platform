import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, WorkoutTemplateStatus
from app.schemas import (
    WorkoutTemplateCreateRequest,
    WorkoutTemplateDetailOut,
    WorkoutTemplateDraftReplaceRequest,
    WorkoutTemplateListOut,
)
from app.security import ensure_not_demo, require_coach
from app.workout_template_services import (
    archive_workout_template,
    create_workout_template,
    create_workout_template_revision,
    get_workout_template,
    list_workout_templates,
    publish_workout_template_draft,
    replace_workout_template_draft,
)

router = APIRouter(prefix="/coach/workout-templates", tags=["workout templates"])


@router.get("", response_model=WorkoutTemplateListOut)
def templates(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status: WorkoutTemplateStatus | None = Query(default=WorkoutTemplateStatus.ACTIVE),
    goal_tag: str | None = Query(default=None, min_length=1, max_length=50),
    search: str | None = Query(default=None, min_length=1, max_length=100),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return list_workout_templates(
        db,
        coach,
        page=page,
        per_page=per_page,
        status=status,
        goal_tag=goal_tag,
        search=search,
    )


@router.post("", response_model=WorkoutTemplateDetailOut, status_code=201)
def create(
    body: WorkoutTemplateCreateRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_workout_template(db, coach, body)


@router.get("/{template_id}", response_model=WorkoutTemplateDetailOut)
def detail(
    template_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    return get_workout_template(db, coach, template_id)


@router.put("/{template_id}/draft", response_model=WorkoutTemplateDetailOut)
def put_draft(
    template_id: uuid.UUID,
    body: WorkoutTemplateDraftReplaceRequest,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return replace_workout_template_draft(db, coach, template_id, body)


@router.post("/{template_id}/publish", response_model=WorkoutTemplateDetailOut)
def publish(
    template_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return publish_workout_template_draft(db, coach, template_id)


@router.post(
    "/{template_id}/revisions",
    response_model=WorkoutTemplateDetailOut,
    status_code=201,
)
def revision(
    template_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return create_workout_template_revision(db, coach, template_id)


@router.post("/{template_id}/archive", response_model=WorkoutTemplateDetailOut)
def archive(
    template_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
) -> dict:
    ensure_not_demo(coach)
    return archive_workout_template(db, coach, template_id)
