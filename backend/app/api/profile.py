"""Shared identity API: profile, preferences, and the self-service avatar.

Profile and preference handlers stay thin over the identity services. The avatar
handlers add the profile-photo experience on top of the media subsystem: upload (and
replace) through ``POST``, current metadata through the profile payload, and removal
through ``DELETE``. Every mutation is demo-protected and registered in the central
identity mutation inventory.
"""

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.avatar_services import get_active_avatar, remove_avatar, set_avatar
from app.database import get_db
from app.models import User, UserProfile
from app.profile_services import (
    get_or_create_user_preferences,
    get_or_create_user_profile,
    update_user_preferences,
    update_user_profile,
)
from app.schemas import (
    MediaAssetOut,
    UserPreferencesOut,
    UserPreferencesUpdate,
    UserProfileOut,
    UserProfileUpdate,
)
from app.security import ensure_not_demo, get_current_user
from app.storage import StorageProvider, get_storage_provider

router = APIRouter(prefix="/me", tags=["identity"])


def _profile_out(db: Session, profile: UserProfile) -> UserProfileOut:
    """Serialize a profile with its current avatar metadata attached."""
    out = UserProfileOut.model_validate(profile)
    asset = get_active_avatar(db, profile.user_id)
    out.avatar = MediaAssetOut.from_asset(asset) if asset is not None else None
    return out


@router.get("/profile", response_model=UserProfileOut)
def read_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> UserProfileOut:
    return _profile_out(db, get_or_create_user_profile(db, user))


@router.put("/profile", response_model=UserProfileOut)
def write_profile(
    body: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfileOut:
    ensure_not_demo(user)
    return _profile_out(db, update_user_profile(db, user, body))


@router.get("/avatar", response_model=MediaAssetOut | None)
def read_avatar(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> MediaAssetOut | None:
    asset = get_active_avatar(db, user.id)
    return MediaAssetOut.from_asset(asset) if asset is not None else None


@router.put("/avatar", response_model=MediaAssetOut, status_code=status.HTTP_200_OK)
def upload_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageProvider = Depends(get_storage_provider),
) -> MediaAssetOut:
    ensure_not_demo(user)
    asset = set_avatar(
        db,
        storage,
        user,
        source=file.file,
        filename=file.filename,
        declared_content_type=file.content_type,
    )
    return MediaAssetOut.from_asset(asset)


@router.delete("/avatar", status_code=status.HTTP_204_NO_CONTENT)
def delete_avatar(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    ensure_not_demo(user)
    remove_avatar(db, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/preferences", response_model=UserPreferencesOut)
def read_preferences(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    return get_or_create_user_preferences(db, user)


@router.put("/preferences", response_model=UserPreferencesOut)
def write_preferences(
    body: UserPreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    ensure_not_demo(user)
    return update_user_preferences(db, user, body)
