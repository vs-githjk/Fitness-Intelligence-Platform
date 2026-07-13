from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import CoachTraineeAssignment, Role, TraineeProfile, User, utcnow
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    if body.invite_code != settings.demo_invite_code:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_invite", "message": "The coach invite code is invalid"},
        )
    email = body.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(
            status_code=409,
            detail={"code": "email_exists", "message": "An account with this email already exists"},
        )
    coach = db.scalar(
        select(User).where(User.role == Role.COACH).order_by(User.created_at).limit(1)
    )
    if coach is None:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "coach_unavailable",
                "message": "No coach is available for this invite",
            },
        )
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        first_name=body.first_name.strip(),
        last_name=body.last_name.strip(),
        role=Role.TRAINEE,
    )
    db.add(user)
    db.flush()
    db.add(TraineeProfile(user_id=user.id))
    db.add(CoachTraineeAssignment(coach_id=coach.id, trainee_id=user.id, accepted_at=utcnow()))
    db.commit()
    db.refresh(user)
    return {"access_token": create_access_token(user), "user": user}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Email or password is incorrect"},
        )
    return {"access_token": create_access_token(user), "user": user}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
