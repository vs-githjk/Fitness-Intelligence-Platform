import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.exercise_media_services import (
    open_exercise_media_content,
    remove_exercise_media,
    set_exercise_media,
)
from app.exercise_services import (
    archive_exercise,
    create_exercise,
    create_revision,
    get_exercise,
    list_exercises,
    publish_draft,
    update_draft,
)
from app.models import ExerciseScope, ExerciseTrackingMode, MediaAsset, User
from app.schemas import (
    ExerciseCreateRequest,
    ExerciseDetailOut,
    ExerciseDraftData,
    ExerciseSummaryOut,
)
from app.security import ensure_not_demo, require_coach
from app.storage import StorageProvider, get_storage_provider

router = APIRouter(prefix="/coach/exercises", tags=["exercise library"])

MediaSlot = Literal["primary_image", "secondary_image", "demonstration_video"]


def _content_disposition(asset: MediaAsset) -> str:
    if asset.original_filename:
        return f'inline; filename="{asset.original_filename}"'
    return "inline"


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


@router.put("/{exercise_id}/media/{slot}", response_model=ExerciseDetailOut)
def upload_exercise_media(
    exercise_id: uuid.UUID,
    slot: MediaSlot,
    file: UploadFile = File(...),
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> dict:
    ensure_not_demo(coach)
    set_exercise_media(
        db,
        storage,
        coach,
        exercise_id,
        slot,
        source=file.file,
        filename=file.filename,
        declared_content_type=file.content_type,
    )
    return get_exercise(db, coach, exercise_id)


@router.delete("/{exercise_id}/media/{slot}", response_model=ExerciseDetailOut)
def delete_exercise_media(
    exercise_id: uuid.UUID,
    slot: MediaSlot,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> dict:
    ensure_not_demo(coach)
    remove_exercise_media(db, storage, coach, exercise_id, slot)
    return get_exercise(db, coach, exercise_id)


@router.get("/{exercise_id}/media/{media_id}/content")
def exercise_media_content(
    exercise_id: uuid.UUID,
    media_id: uuid.UUID,
    coach: User = Depends(require_coach),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> StreamingResponse:
    asset, stream = open_exercise_media_content(db, storage, coach, exercise_id, media_id)
    return StreamingResponse(
        stream,
        media_type=asset.content_type,
        headers={
            "Content-Disposition": _content_disposition(asset),
            "Content-Length": str(asset.byte_size),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
