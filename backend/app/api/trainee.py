from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TraineeProfile, User
from app.schemas import ProfileOut, ProfileUpdate
from app.security import require_trainee

router = APIRouter(prefix="/trainee", tags=["trainee"])


@router.get("/profile", response_model=ProfileOut)
def get_profile(
    user: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> TraineeProfile:
    return db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == user.id))


@router.put("/profile", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate, user: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> TraineeProfile:
    profile = db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == user.id))
    for key, value in body.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
