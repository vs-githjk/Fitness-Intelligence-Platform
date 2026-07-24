import hashlib
import json
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseVersion,
    ExerciseVersionStatus,
    MediaAsset,
    MediaLifecycleStatus,
    User,
)
from app.repositories.exercises import ExerciseRepository
from app.schemas import ExerciseCreateRequest, ExerciseDraftData

VERSION_FIELDS = (
    "name",
    "description",
    "instructions",
    "tracking_mode",
    "category",
    "movement_pattern",
    "equipment",
    "primary_muscle_groups",
    "secondary_muscle_groups",
    "unilateral",
    "safety_cues",
    "difficulty",
    "coaching_cues",
    "common_mistakes",
    "image_url",
    "thumbnail_url",
)
# Authored media references travel with the version content but are managed through
# dedicated upload endpoints, not the JSON draft body, so they are kept separate.
MEDIA_FIELDS = (
    "primary_image_media_id",
    "secondary_image_media_id",
    "demonstration_video_media_id",
)


def exercise_not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "exercise_not_found", "message": "Exercise not found"},
    )


def _conflict(code: str, message: str) -> HTTPException:
    return HTTPException(status_code=409, detail={"code": code, "message": message})


def _version_values(source: ExerciseDraftData | ExerciseVersion) -> dict:
    if isinstance(source, ExerciseDraftData):
        return source.model_dump(mode="python")
    return {field: getattr(source, field) for field in VERSION_FIELDS}


def _apply_version_values(version: ExerciseVersion, source: ExerciseDraftData) -> None:
    for field, value in _version_values(source).items():
        setattr(version, field, value)


def exercise_content_hash(version: ExerciseVersion) -> str:
    payload = {
        field: (
            getattr(version, field).value
            if hasattr(getattr(version, field), "value")
            else getattr(version, field)
        )
        for field in VERSION_FIELDS
    }
    # Authored media is part of the immutable content snapshot, keyed by asset id.
    for field in MEDIA_FIELDS:
        value = getattr(version, field)
        payload[field] = str(value) if value is not None else None
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _published_versions(exercise: Exercise) -> list[ExerciseVersion]:
    return sorted(
        (item for item in exercise.versions if item.status == ExerciseVersionStatus.PUBLISHED),
        key=lambda item: item.version_number,
        reverse=True,
    )


def _draft_version(exercise: Exercise) -> ExerciseVersion | None:
    return next(
        (item for item in exercise.versions if item.status == ExerciseVersionStatus.DRAFT),
        None,
    )


def _media_out(exercise_id: uuid.UUID, asset: MediaAsset | None) -> dict | None:
    """Serialize an authored media asset with an authorized delivery URL, or None."""
    if asset is None or asset.lifecycle_status != MediaLifecycleStatus.ACTIVE:
        return None
    return {
        "id": asset.id,
        "purpose": asset.purpose,
        "content_type": asset.content_type,
        "byte_size": asset.byte_size,
        "original_filename": asset.original_filename,
        "content_url": f"/coach/exercises/{exercise_id}/media/{asset.id}/content",
    }


def version_out(version: ExerciseVersion) -> dict:
    values = {field: getattr(version, field) for field in VERSION_FIELDS}
    # These knowledge lists are nullable in storage (older/seeded rows may hold NULL);
    # present them as empty lists so the response contract stays stable.
    for field in ("coaching_cues", "common_mistakes"):
        if values[field] is None:
            values[field] = []
    return {
        "id": version.id,
        "exercise_id": version.exercise_id,
        "version_number": version.version_number,
        "status": version.status.value,
        **values,
        "primary_image": _media_out(version.exercise_id, version.primary_image),
        "secondary_image": _media_out(version.exercise_id, version.secondary_image),
        "demonstration_video": _media_out(
            version.exercise_id, version.demonstration_video
        ),
        "content_hash": version.content_hash,
        "created_by_user_id": version.created_by_user_id,
        "created_at": version.created_at,
        "updated_at": version.updated_at,
        "published_at": version.published_at,
    }


def exercise_out(exercise: Exercise, *, detail: bool = False) -> dict:
    published = _published_versions(exercise)
    draft = _draft_version(exercise)
    result = {
        "id": exercise.id,
        "scope": exercise.scope,
        "owner_coach_id": exercise.owner_coach_id,
        "slug": exercise.slug,
        "status": exercise.status,
        "created_at": exercise.created_at,
        "archived_at": exercise.archived_at,
        "published_version": version_out(published[0]) if published else None,
        "draft_version": version_out(draft) if draft else None,
    }
    if detail:
        result["versions"] = [version_out(item) for item in published] + (
            [version_out(draft)] if draft else []
        )
    return result


def list_exercises(
    db: Session,
    coach: User,
    *,
    include_archived: bool = False,
    scope: ExerciseScope | None = None,
    tracking_mode=None,
    search: str | None = None,
) -> list[dict]:
    items = ExerciseRepository(db).list_visible(
        coach.id,
        include_archived=include_archived,
        scope=scope,
        tracking_mode=tracking_mode,
        search=search,
    )
    return [exercise_out(item) for item in items]


def get_exercise(db: Session, coach: User, exercise_id: uuid.UUID) -> dict:
    exercise = ExerciseRepository(db).get_visible(coach.id, exercise_id)
    if exercise is None:
        raise exercise_not_found()
    return exercise_out(exercise, detail=True)


def _owned_mutable_exercise(
    db: Session, coach: User, exercise_id: uuid.UUID
) -> Exercise:
    exercise = ExerciseRepository(db).get_visible(coach.id, exercise_id)
    if exercise is None:
        raise exercise_not_found()
    if exercise.scope == ExerciseScope.SYSTEM:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "system_exercise_read_only",
                "message": "System exercises are read-only",
            },
        )
    if exercise.status == ExerciseStatus.ARCHIVED:
        raise _conflict("exercise_archived", "Archived exercises cannot be changed")
    return exercise


def create_exercise(db: Session, coach: User, body: ExerciseCreateRequest) -> dict:
    repository = ExerciseRepository(db)
    if repository.get_private_by_slug(coach.id, body.slug):
        raise _conflict("exercise_slug_conflict", "You already have an exercise with this slug")
    exercise = Exercise(
        scope=ExerciseScope.COACH_PRIVATE,
        owner_coach_id=coach.id,
        slug=body.slug,
        status=ExerciseStatus.ACTIVE,
    )
    draft = ExerciseVersion(
        exercise=exercise,
        version_number=1,
        status=ExerciseVersionStatus.DRAFT,
        created_by_user_id=coach.id,
    )
    _apply_version_values(draft, ExerciseDraftData.model_validate(body.model_dump()))
    try:
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        exercise = repository.get_visible(coach.id, exercise.id)
        return exercise_out(exercise, detail=True)
    except IntegrityError as exc:
        db.rollback()
        raise _conflict(
            "exercise_slug_conflict", "You already have an exercise with this slug"
        ) from exc


def update_draft(
    db: Session, coach: User, exercise_id: uuid.UUID, body: ExerciseDraftData
) -> dict:
    exercise = _owned_mutable_exercise(db, coach, exercise_id)
    draft = _draft_version(exercise)
    if draft is None:
        raise _conflict(
            "exercise_draft_missing", "Create a revision before editing a published exercise"
        )
    _apply_version_values(draft, body)
    draft.updated_at = datetime.now(UTC)
    db.commit()
    return get_exercise(db, coach, exercise.id)


def publish_draft(db: Session, coach: User, exercise_id: uuid.UUID) -> dict:
    exercise = _owned_mutable_exercise(db, coach, exercise_id)
    draft = _draft_version(exercise)
    if draft is None:
        raise _conflict("exercise_draft_missing", "No draft is available to publish")
    now = datetime.now(UTC)
    draft.status = ExerciseVersionStatus.PUBLISHED
    draft.content_hash = exercise_content_hash(draft)
    draft.published_at = now
    draft.updated_at = now
    db.commit()
    return get_exercise(db, coach, exercise.id)


def create_revision(db: Session, coach: User, exercise_id: uuid.UUID) -> dict:
    exercise = _owned_mutable_exercise(db, coach, exercise_id)
    if _draft_version(exercise) is not None:
        raise _conflict("exercise_draft_exists", "This exercise already has a draft")
    published = _published_versions(exercise)
    if not published:
        raise _conflict("exercise_unpublished", "Publish the initial draft first")
    draft = ExerciseVersion(
        version_number=ExerciseRepository(db).next_version_number(exercise.id),
        status=ExerciseVersionStatus.DRAFT,
        created_by_user_id=coach.id,
        **_version_values(published[0]),
        # Carry authored media forward; the copy shares the same immutable assets
        # until the coach explicitly replaces or removes one on the new draft.
        **{field: getattr(published[0], field) for field in MEDIA_FIELDS},
    )
    exercise.versions.append(draft)
    db.commit()
    return get_exercise(db, coach, exercise.id)


def archive_exercise(db: Session, coach: User, exercise_id: uuid.UUID) -> dict:
    exercise = ExerciseRepository(db).get_visible(coach.id, exercise_id)
    if exercise is None:
        raise exercise_not_found()
    if exercise.scope == ExerciseScope.SYSTEM:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "system_exercise_read_only",
                "message": "System exercises are read-only",
            },
        )
    if exercise.status == ExerciseStatus.ACTIVE:
        exercise.status = ExerciseStatus.ARCHIVED
        exercise.archived_at = datetime.now(UTC)
        db.commit()
    return get_exercise(db, coach, exercise.id)
