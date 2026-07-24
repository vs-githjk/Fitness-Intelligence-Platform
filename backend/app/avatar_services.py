"""Avatar and cross-user profile services.

Builds the profile-photo experience on top of the Phase 2 media subsystem without
bypassing it: uploads, replacements, and deletions all flow through
``media_services`` so validation, checksums, opaque storage keys, and lifecycle
rules are reused verbatim. The only additions here are the identity concerns the
media layer deliberately leaves out:

* binding a user's ACTIVE avatar to their shared ``UserProfile`` record, and
* delivering that avatar to related accounts (self, or an assigned coach/trainee)
  through a relationship-authorized route rather than the owner-only media route.

Cross-account access is indistinguishable from "not found" (404), consistent with
the platform-wide discovery rule.
"""

import uuid
from collections.abc import Iterator
from typing import BinaryIO

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.media_services import (
    replace_media,
    soft_delete_media,
    upload_media,
)
from app.models import (
    CoachTraineeAssignment,
    MediaAsset,
    MediaLifecycleStatus,
    MediaPurpose,
    User,
    UserProfile,
)
from app.profile_services import get_or_create_user_profile
from app.storage.base import StorageError, StorageProvider


def _not_found() -> HTTPException:
    # Uniform 404 so a missing avatar and an unauthorized view are indistinguishable.
    return HTTPException(
        status_code=404,
        detail={"code": "profile_not_found", "message": "Profile not found."},
    )


def avatar_content_url(user_id: uuid.UUID) -> str:
    """Relationship-authorized delivery path for a user's current avatar."""
    return f"/users/{user_id}/avatar/content"


def get_active_avatar(db: Session, user_id: uuid.UUID) -> MediaAsset | None:
    """The user's current avatar asset, or None. Defensive against stale references."""
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user_id))
    if profile is None or profile.avatar_media_id is None:
        return None
    asset = db.get(MediaAsset, profile.avatar_media_id)
    if (
        asset is None
        or asset.owner_user_id != user_id
        or asset.purpose is not MediaPurpose.AVATAR
        or asset.lifecycle_status is not MediaLifecycleStatus.ACTIVE
    ):
        return None
    return asset


def avatar_url_for(db: Session, user_id: uuid.UUID) -> str | None:
    """Delivery URL if the user has a current avatar, else None (show initials)."""
    return avatar_content_url(user_id) if get_active_avatar(db, user_id) else None


def set_avatar(
    db: Session,
    storage: StorageProvider,
    user: User,
    *,
    source: BinaryIO,
    filename: str | None,
    declared_content_type: str | None,
) -> MediaAsset:
    """Upload a new avatar, replacing any current one, and point the profile at it.

    New bytes are written before the prior asset is transitioned, so a mid-flight
    failure never leaves the owner without a usable avatar. When a current active
    avatar exists it is marked REPLACED (never orphaned); otherwise a fresh asset is
    created. The caller is responsible for demo protection.
    """
    profile = get_or_create_user_profile(db, user)
    current = get_active_avatar(db, user.id)
    if current is not None:
        new_asset = replace_media(
            db,
            storage,
            current.id,
            user,
            source=source,
            filename=filename,
            declared_content_type=declared_content_type,
        )
    else:
        new_asset = upload_media(
            db,
            storage,
            owner=user,
            uploader=user,
            source=source,
            filename=filename,
            declared_content_type=declared_content_type,
            purpose=MediaPurpose.AVATAR,
        )
    profile.avatar_media_id = new_asset.id
    db.add(profile)
    db.commit()
    db.refresh(new_asset)
    return new_asset


def remove_avatar(db: Session, user: User) -> None:
    """Detach and soft-delete the current avatar. Idempotent; never purges bytes."""
    profile = get_or_create_user_profile(db, user)
    media_id = profile.avatar_media_id
    if media_id is None:
        return
    # Clear the reference first and persist it, so the profile never points at a
    # soft-deleted asset even if the media transition is a no-op.
    profile.avatar_media_id = None
    db.add(profile)
    db.commit()
    soft_delete_media(db, media_id, user)


def assert_can_view_profile(
    db: Session, viewer: User, target_user_id: uuid.UUID
) -> None:
    """Allow self, or either side of an active coach/trainee assignment. Else 404."""
    if viewer.id == target_user_id:
        return
    related = db.scalar(
        select(CoachTraineeAssignment.id).where(
            CoachTraineeAssignment.status == "active",
            or_(
                and_(
                    CoachTraineeAssignment.coach_id == viewer.id,
                    CoachTraineeAssignment.trainee_id == target_user_id,
                ),
                and_(
                    CoachTraineeAssignment.coach_id == target_user_id,
                    CoachTraineeAssignment.trainee_id == viewer.id,
                ),
            ),
        )
    )
    if not related:
        raise _not_found()


def open_avatar_content(
    db: Session,
    storage: StorageProvider,
    viewer: User,
    target_user_id: uuid.UUID,
) -> tuple[MediaAsset, Iterator[bytes]]:
    """Authorized avatar delivery for a related user (self, coach, or trainee)."""
    assert_can_view_profile(db, viewer, target_user_id)
    asset = get_active_avatar(db, target_user_id)
    if asset is None:
        raise _not_found()
    try:
        stream = storage.open_stream(asset.storage_key)
    except StorageError as exc:
        raise _not_found() from exc
    return asset, stream


def public_profile_view(db: Session, viewer: User, target_user_id: uuid.UUID) -> dict:
    """Assemble a related user's shareable profile card. Enforces relationship auth."""
    assert_can_view_profile(db, viewer, target_user_id)
    target = db.get(User, target_user_id)
    if target is None:
        raise _not_found()
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == target_user_id)
    )
    return {
        "user_id": target.id,
        "role": target.role,
        "full_name": f"{target.first_name} {target.last_name}",
        "preferred_display_name": profile.preferred_display_name if profile else None,
        "headline": profile.headline if profile else None,
        "bio": profile.bio if profile else None,
        "coaching_specialties": (profile.coaching_specialties or []) if profile else [],
        "years_of_experience": profile.years_of_experience if profile else None,
        "certifications_text": profile.certifications_text if profile else None,
        "training_goals": profile.training_goals if profile else None,
        "avatar_url": avatar_url_for(db, target_user_id),
    }
