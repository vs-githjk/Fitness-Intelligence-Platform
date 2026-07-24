"""Cross-user identity API: viewing a related user's profile and avatar.

A user may view the profile and avatar of themselves or an account they share an
active coaching relationship with (in either direction). Every other target is
indistinguishable from "not found" (404). Avatar bytes are delivered here — behind a
relationship check — rather than through the owner-only media route, so a coach can
render an assigned trainee's photo without ever gaining access to the media itself.
"""

import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.avatar_services import open_avatar_content, public_profile_view
from app.database import get_db
from app.models import MediaAsset, User
from app.schemas import PublicProfileOut
from app.security import get_current_user
from app.storage import StorageProvider, get_storage_provider

router = APIRouter(prefix="/users", tags=["identity"])


def _content_disposition(asset: MediaAsset) -> str:
    if asset.original_filename:
        return f'inline; filename="{asset.original_filename}"'
    return "inline"


@router.get("/{user_id}/profile", response_model=PublicProfileOut)
def read_user_profile(
    user_id: uuid.UUID,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return public_profile_view(db, viewer, user_id)


@router.get("/{user_id}/avatar/content")
def read_user_avatar(
    user_id: uuid.UUID,
    viewer: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> StreamingResponse:
    asset, stream = open_avatar_content(db, storage, viewer, user_id)
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
