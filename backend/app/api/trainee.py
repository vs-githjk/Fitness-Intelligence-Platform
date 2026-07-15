from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CoachTraineeAssignment, TraineeProfile, User
from app.schemas import ProfileOut, ProfileUpdate, TraineeCoachOut
from app.security import ensure_not_demo, require_trainee

router = APIRouter(prefix="/trainee", tags=["trainee"])


@router.get("/coach", response_model=TraineeCoachOut)
def get_coach(user: User = Depends(require_trainee), db: Session = Depends(get_db)) -> dict:
    assignment = db.scalar(
        select(CoachTraineeAssignment)
        .where(CoachTraineeAssignment.trainee_id == user.id)
        .order_by(CoachTraineeAssignment.created_at.desc())
        .limit(1)
    )
    if assignment is None:
        return {"assignment_status": "unassigned"}
    coach = db.get(User, assignment.coach_id)
    return {
        "assignment_status": assignment.status,
        "coach_id": coach.id if coach else None,
        "coach_name": f"{coach.first_name} {coach.last_name}" if coach else None,
        "coach_email": coach.email if coach else None,
    }


@router.get("/profile", response_model=ProfileOut)
def get_profile(
    user: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> TraineeProfile:
    return db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == user.id))


@router.put("/profile", response_model=ProfileOut)
def update_profile(
    body: ProfileUpdate, user: User = Depends(require_trainee), db: Session = Depends(get_db)
) -> TraineeProfile:
    ensure_not_demo(user)
    profile = db.scalar(select(TraineeProfile).where(TraineeProfile.user_id == user.id))
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
