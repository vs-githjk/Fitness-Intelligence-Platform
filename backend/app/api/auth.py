import hmac
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.invitations import hash_invite_token, invite_status
from app.models import (
    CoachInvite,
    CoachProfile,
    CoachTraineeAssignment,
    Role,
    TraineeProfile,
    User,
)
from app.schemas import (
    CoachRegisterRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    TraineeRegisterRequest,
    UserOut,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["authentication"])


def registration_error(code: str = "registration_unavailable", status_code: int = 400) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": "Registration could not be completed with the supplied details",
        },
    )


def ensure_email_available(db: Session, email: str) -> None:
    if db.scalar(select(User.id).where(User.email == email)):
        raise registration_error("registration_conflict", 409)


@router.post("/register/coach", response_model=TokenResponse, status_code=201)
def register_coach(body: CoachRegisterRequest, db: Session = Depends(get_db)) -> dict:
    configured_code = settings.coach_registration_code
    if configured_code is None or not hmac.compare_digest(
        body.registration_code.encode("utf-8"), configured_code.encode("utf-8")
    ):
        raise registration_error()
    email = body.email.lower()
    try:
        ensure_email_available(db, email)
        user = User(
            email=email,
            password_hash=hash_password(body.password),
            first_name=body.first_name.strip(),
            last_name=body.last_name.strip(),
            role=Role.COACH,
        )
        db.add(user)
        db.flush()
        db.add(
            CoachProfile(
                user_id=user.id,
                display_name=f"{user.first_name} {user.last_name}".strip(),
                credentials_text=None,
            )
        )
        db.commit()
        db.refresh(user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise registration_error() from exc
    return {"access_token": create_access_token(user), "user": user}


@router.post("/register/trainee", response_model=TokenResponse, status_code=201)
def register_trainee(body: TraineeRegisterRequest, db: Session = Depends(get_db)) -> dict:
    email = body.email.lower()
    now = datetime.now(UTC)
    try:
        ensure_email_available(db, email)
        invite = db.scalar(
            select(CoachInvite)
            .where(CoachInvite.token_hash == hash_invite_token(body.invite_code))
            .with_for_update()
        )
        if (
            invite is None
            or invite_status(invite, now) != "active"
            or (invite.intended_email is not None and invite.intended_email != email)
        ):
            raise registration_error("invalid_invite")
        coach = db.get(User, invite.coach_id)
        if coach is None or coach.role != Role.COACH or coach.status != "active":
            raise registration_error("invalid_invite")
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
        db.add(
            CoachTraineeAssignment(
                coach_id=coach.id,
                trainee_id=user.id,
                accepted_at=now,
            )
        )
        invite.used_at = now
        invite.used_by_user_id = user.id
        db.commit()
        db.refresh(user)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise registration_error() from exc
    return {"access_token": create_access_token(user), "user": user}


@router.post("/register", response_model=TokenResponse, status_code=201, deprecated=True)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    """Compatibility alias for clients that predate role-aware registration."""
    return register_trainee(body, db)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if (
        user is None
        or not verify_password(body.password, user.password_hash)
        or user.status != "active"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Email or password is incorrect"},
        )
    return {"access_token": create_access_token(user), "user": user}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
