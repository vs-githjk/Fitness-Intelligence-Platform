"""Exercise media authoring and delivery.

Attaches images and a demonstration video to an exercise's editable draft version by
reusing the media subsystem verbatim (validation, checksum, opaque storage key,
lifecycle). The only exercise-specific rules live here:

* media is edited on the **draft** version only — published versions are immutable,
  so their referenced assets are never mutated; and
* an asset shared by more than one version (a draft copies its parent's references on
  revision) is never retired while another version still points at it, which keeps
  every published version's content byte-for-byte stable.

Delivery is authorized through the coach exercise route: any coach who can see the
exercise (system or their own) may stream its media; every other request is a 404.
"""

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import BinaryIO

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.exercise_services import _draft_version, _owned_mutable_exercise, exercise_not_found
from app.media_services import assert_transition, upload_media
from app.models import (
    Exercise,
    ExerciseVersion,
    MediaAsset,
    MediaLifecycleStatus,
    MediaPurpose,
    User,
)
from app.repositories.exercises import ExerciseRepository
from app.storage.base import StorageError, StorageProvider

# slot -> (ExerciseVersion column, upload purpose)
MEDIA_SLOTS: dict[str, tuple[str, MediaPurpose]] = {
    "primary_image": ("primary_image_media_id", MediaPurpose.EXERCISE_IMAGE),
    "secondary_image": ("secondary_image_media_id", MediaPurpose.EXERCISE_IMAGE),
    "demonstration_video": ("demonstration_video_media_id", MediaPurpose.EXERCISE_VIDEO),
}
MEDIA_COLUMNS: tuple[str, ...] = (
    "primary_image_media_id",
    "secondary_image_media_id",
    "demonstration_video_media_id",
)


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "exercise_media_not_found", "message": "Exercise media not found."},
    )


def _conflict(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=409, detail={"code": code, "message": message})


def _editable_draft(db: Session, coach: User, exercise_id: uuid.UUID) -> ExerciseVersion:
    """The coach's own, active, editable draft version. Enforces the immutability rule."""
    exercise = _owned_mutable_exercise(db, coach, exercise_id)
    draft = _draft_version(exercise)
    if draft is None:
        raise _conflict(
            "exercise_draft_missing",
            "Create a revision before changing media on a published exercise.",
        )
    return draft


def _asset_referenced_elsewhere(db: Session, media_id: uuid.UUID) -> bool:
    """True if any exercise version still references this asset (across all slots)."""
    return db.scalar(
        select(ExerciseVersion.id)
        .where(
            or_(
                ExerciseVersion.primary_image_media_id == media_id,
                ExerciseVersion.secondary_image_media_id == media_id,
                ExerciseVersion.demonstration_video_media_id == media_id,
            )
        )
        .limit(1)
    ) is not None


def _retire_if_orphaned(
    db: Session, media_id: uuid.UUID | None, *, replaced_by: uuid.UUID | None
) -> None:
    """Retire a detached asset only when no other version still references it.

    ``replaced_by`` set marks it REPLACED (a swap); otherwise it is SOFT_DELETED (a
    removal). Callers must already have committed the detach, so this reads the
    current reference state.
    """
    if media_id is None or _asset_referenced_elsewhere(db, media_id):
        return
    asset = db.get(MediaAsset, media_id)
    if asset is None or asset.lifecycle_status is not MediaLifecycleStatus.ACTIVE:
        return
    target = (
        MediaLifecycleStatus.REPLACED
        if replaced_by is not None
        else MediaLifecycleStatus.SOFT_DELETED
    )
    assert_transition(asset.lifecycle_status, target)
    asset.lifecycle_status = target
    if replaced_by is not None:
        asset.replaced_at = datetime.now(UTC)
        asset.replaced_by_media_id = replaced_by
    else:
        asset.deleted_at = datetime.now(UTC)
    db.add(asset)
    db.commit()


def set_exercise_media(
    db: Session,
    storage: StorageProvider,
    coach: User,
    exercise_id: uuid.UUID,
    slot: str,
    *,
    source: BinaryIO,
    filename: str | None,
    declared_content_type: str | None,
) -> ExerciseVersion:
    """Upload media into a draft slot, retiring any prior asset it replaces."""
    column, purpose = MEDIA_SLOTS[slot]
    draft = _editable_draft(db, coach, exercise_id)
    previous_id: uuid.UUID | None = getattr(draft, column)
    new_asset = upload_media(
        db,
        storage,
        owner=coach,
        uploader=coach,
        source=source,
        filename=filename,
        declared_content_type=declared_content_type,
        purpose=purpose,
    )
    setattr(draft, column, new_asset.id)
    db.add(draft)
    db.commit()
    if previous_id is not None and previous_id != new_asset.id:
        _retire_if_orphaned(db, previous_id, replaced_by=new_asset.id)
    db.refresh(draft)
    return draft


def remove_exercise_media(
    db: Session,
    storage: StorageProvider,
    coach: User,
    exercise_id: uuid.UUID,
    slot: str,
) -> ExerciseVersion:
    """Detach a draft slot and soft-delete the asset if nothing else uses it."""
    column, _purpose = MEDIA_SLOTS[slot]
    draft = _editable_draft(db, coach, exercise_id)
    previous_id: uuid.UUID | None = getattr(draft, column)
    if previous_id is None:
        return draft  # idempotent
    setattr(draft, column, None)
    db.add(draft)
    db.commit()
    _retire_if_orphaned(db, previous_id, replaced_by=None)
    db.refresh(draft)
    return draft


def open_exercise_media_content(
    db: Session,
    storage: StorageProvider,
    coach: User,
    exercise_id: uuid.UUID,
    media_id: uuid.UUID,
) -> tuple[MediaAsset, Iterator[bytes]]:
    """Authorized delivery: stream media the coach can see for a visible exercise."""
    exercise: Exercise | None = ExerciseRepository(db).get_visible(coach.id, exercise_id)
    if exercise is None:
        raise exercise_not_found()
    referenced = {
        getattr(version, column)
        for version in exercise.versions
        for column in MEDIA_COLUMNS
        if getattr(version, column) is not None
    }
    if media_id not in referenced:
        raise _not_found()
    asset = db.get(MediaAsset, media_id)
    if asset is None or asset.lifecycle_status is not MediaLifecycleStatus.ACTIVE:
        raise _not_found()
    try:
        stream = storage.open_stream(asset.storage_key)
    except StorageError as exc:
        raise _not_found() from exc
    return asset, stream
