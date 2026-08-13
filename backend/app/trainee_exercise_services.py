"""Trainee exercise-knowledge read access (Experience Cycle 2, C2.2).

The approved enabling capability (§30): a narrow, read-only surface that lets a trainee
read the exercise knowledge and media they need for Workout Execution and Exercise
Reference. It completes the trainee-scoped delivery authorization walk deferred in
ADR-0018.

Authorization walk (mirrors the ownership-scoped `404`-on-cross-account pattern used
throughout trainee execution): a trainee may read an ``ExerciseVersion`` only when they
own a ``WorkoutSession`` whose snapshot references that version. Anything else — an
unknown id, a foreign trainee's session, a draft version, an unreferenced media id —
returns `404`, never confirming existence. Published versions only; read-only; no
authoring, substitution, or catalog access is granted. Demo trainees may read (no
mutation occurs), consistent with analytics.
"""

import uuid
from collections.abc import Iterator

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ExerciseVersion,
    ExerciseVersionStatus,
    MediaAsset,
    MediaLifecycleStatus,
    User,
    WorkoutSession,
    WorkoutSessionExercise,
)
from app.storage.base import StorageError, StorageProvider

# The three media reference columns on ExerciseVersion (image / image / video).
_MEDIA_COLUMNS: tuple[str, ...] = (
    "primary_image_media_id",
    "secondary_image_media_id",
    "demonstration_video_media_id",
)

# Non-list knowledge fields copied verbatim into the read view.
_SCALAR_FIELDS: tuple[str, ...] = (
    "name",
    "description",
    "tracking_mode",
    "category",
    "movement_pattern",
    "unilateral",
    "difficulty",
    "instructions",
)
_LIST_FIELDS: tuple[str, ...] = (
    "equipment",
    "primary_muscle_groups",
    "secondary_muscle_groups",
    "safety_cues",
    "coaching_cues",
    "common_mistakes",
)


def _not_found() -> HTTPException:
    # Uniform 404 — existence is never confirmed for an unauthorized/unknown version.
    return HTTPException(
        status_code=404,
        detail={"code": "exercise_version_not_found", "message": "Exercise not found."},
    )


def _media_not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "exercise_media_not_found", "message": "Exercise media not found."},
    )


def _authorized_version(
    db: Session, trainee: User, exercise_version_id: uuid.UUID
) -> ExerciseVersion:
    """The published version the trainee is authorized to read, or 404.

    Authorization = the trainee owns a workout session that references this version.
    """
    referenced = db.scalar(
        select(WorkoutSessionExercise.id)
        .join(WorkoutSession, WorkoutSessionExercise.workout_session_id == WorkoutSession.id)
        .where(
            WorkoutSessionExercise.exercise_version_id == exercise_version_id,
            WorkoutSession.trainee_id == trainee.id,
        )
        .limit(1)
    )
    if referenced is None:
        raise _not_found()
    version = db.get(ExerciseVersion, exercise_version_id)
    # Assigned sessions snapshot published versions; refuse anything else defensively.
    if version is None or version.status is not ExerciseVersionStatus.PUBLISHED:
        raise _not_found()
    return version


def _media_out(exercise_version_id: uuid.UUID, asset: MediaAsset | None) -> dict | None:
    """Serialize a media asset with a trainee-scoped delivery URL, or None when absent
    or not active. The opaque storage key is never exposed."""
    if asset is None or asset.lifecycle_status is not MediaLifecycleStatus.ACTIVE:
        return None
    return {
        "id": asset.id,
        "purpose": asset.purpose,
        "content_type": asset.content_type,
        "byte_size": asset.byte_size,
        "original_filename": asset.original_filename,
        "content_url": f"/trainee/exercise-versions/{exercise_version_id}/media/{asset.id}/content",
    }


def _knowledge_out(version: ExerciseVersion) -> dict:
    payload: dict = {"id": version.id, "exercise_id": version.exercise_id}
    for field in _SCALAR_FIELDS:
        payload[field] = getattr(version, field)
    for field in _LIST_FIELDS:
        # coaching_cues / common_mistakes are nullable in storage — present [] not null.
        payload[field] = getattr(version, field) or []
    payload["primary_image"] = _media_out(version.id, version.primary_image)
    payload["secondary_image"] = _media_out(version.id, version.secondary_image)
    payload["demonstration_video"] = _media_out(version.id, version.demonstration_video)
    return payload


def get_trainee_exercise_knowledge(
    db: Session, trainee: User, exercise_version_id: uuid.UUID
) -> dict:
    return _knowledge_out(_authorized_version(db, trainee, exercise_version_id))


def open_trainee_exercise_media(
    db: Session,
    storage: StorageProvider,
    trainee: User,
    exercise_version_id: uuid.UUID,
    media_id: uuid.UUID,
) -> tuple[MediaAsset, Iterator[bytes]]:
    """Authorized delivery: stream a media asset referenced by a version the trainee may
    read. The media id must belong to that version; everything else is a 404."""
    version = _authorized_version(db, trainee, exercise_version_id)
    referenced = {
        getattr(version, column)
        for column in _MEDIA_COLUMNS
        if getattr(version, column) is not None
    }
    if media_id not in referenced:
        raise _media_not_found()
    asset = db.get(MediaAsset, media_id)
    if asset is None or asset.lifecycle_status is not MediaLifecycleStatus.ACTIVE:
        raise _media_not_found()
    try:
        stream = storage.open_stream(asset.storage_key)
    except StorageError as exc:
        raise _media_not_found() from exc
    return asset, stream
