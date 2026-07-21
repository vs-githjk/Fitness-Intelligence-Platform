from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.profile_services import (
    get_or_create_user_preferences,
    get_or_create_user_profile,
    update_user_preferences,
    update_user_profile,
)
from app.schemas import (
    UserPreferencesOut,
    UserPreferencesUpdate,
    UserProfileOut,
    UserProfileUpdate,
)
from app.security import ensure_not_demo, get_current_user

router = APIRouter(prefix="/me", tags=["identity"])


@router.get("/profile", response_model=UserProfileOut)
def read_profile(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> User:
    return get_or_create_user_profile(db, user)


@router.put("/profile", response_model=UserProfileOut)
def write_profile(
    body: UserProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    ensure_not_demo(user)
    return update_user_profile(db, user, body)


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
