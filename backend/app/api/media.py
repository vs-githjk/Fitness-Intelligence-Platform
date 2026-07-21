"""Foundational media API: upload, metadata, authorized delivery, soft delete.

Routes are thin HTTP adapters over the media service. They never touch files,
storage keys, providers, or lifecycle fields. Every mutation is demo-protected and
registered in the central media mutation inventory; delivery is always authorized.
"""

import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.media_services import (
    get_media_asset,
    open_media_content,
    soft_delete_media,
    upload_media,
)
from app.models import MediaAsset, MediaPurpose, User
from app.schemas import MediaAssetOut
from app.security import ensure_not_demo, get_current_user
from app.storage import StorageProvider, get_storage_provider

router = APIRouter(prefix="/media", tags=["media"])


def _content_disposition(asset: MediaAsset) -> str:
    if asset.original_filename:
        return f'inline; filename="{asset.original_filename}"'
    return "inline"


@router.post("", response_model=MediaAssetOut, status_code=status.HTTP_201_CREATED)
def upload_asset(
    file: UploadFile = File(...),
    purpose: MediaPurpose = Form(MediaPurpose.GENERIC),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> MediaAssetOut:
    ensure_not_demo(user)
    asset = upload_media(
        db,
        storage,
        owner=user,
        uploader=user,
        source=file.file,
        filename=file.filename,
        declared_content_type=file.content_type,
        purpose=purpose,
    )
    return MediaAssetOut.from_asset(asset)


@router.get("/{media_id}", response_model=MediaAssetOut)
def read_asset(
    media_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MediaAssetOut:
    return MediaAssetOut.from_asset(get_media_asset(db, media_id, user))


@router.get("/{media_id}/content")
def read_asset_content(
    media_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> StreamingResponse:
    asset, stream = open_media_content(db, storage, media_id, user)
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


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    media_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    ensure_not_demo(user)
    soft_delete_media(db, media_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
