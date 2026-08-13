"""Trainee exercise-reference routes (Experience Cycle 2, C2.2).

Read-only exercise knowledge and media for Workout Execution and Exercise Reference,
authorized through a workout session the trainee owns (see
``app.trainee_exercise_services``). No mutations — no demo guard is required, and demo
trainees may read.
"""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import MediaAsset, User
from app.schemas import TraineeExerciseKnowledgeOut
from app.security import require_trainee
from app.storage import StorageProvider, get_storage_provider
from app.trainee_exercise_services import (
    get_trainee_exercise_knowledge,
    open_trainee_exercise_media,
)

router = APIRouter(prefix="/trainee/exercise-versions", tags=["trainee exercise reference"])


def _content_disposition(asset: MediaAsset) -> str:
    if asset.original_filename:
        return f'inline; filename="{asset.original_filename}"'
    return "inline"


@router.get("/{exercise_version_id}", response_model=TraineeExerciseKnowledgeOut)
def exercise_knowledge(
    exercise_version_id: uuid.UUID,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
) -> dict:
    return get_trainee_exercise_knowledge(db, trainee, exercise_version_id)


@router.get("/{exercise_version_id}/media/{media_id}/content")
def exercise_media_content(
    exercise_version_id: uuid.UUID,
    media_id: uuid.UUID,
    trainee: User = Depends(require_trainee),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> StreamingResponse:
    asset, stream = open_trainee_exercise_media(
        db, storage, trainee, exercise_version_id, media_id
    )
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
