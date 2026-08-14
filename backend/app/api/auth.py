import hmac
import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.email import get_email_provider
from app.invitations import aware_utc, hash_invite_token, invite_status
from app.models import (
    CoachInvite,
    CoachProfile,
    CoachTraineeAssignment,
    PasswordResetToken,
    Role,
    TraineeProfile,
    User,
    UserPreferences,
    UserProfile,
)
from app.password_reset import build_reset_email, generate_reset_token, hash_reset_token
from app.schemas import (
    CoachRegisterRequest,
    DemoSessionRequest,
    GenericMessageResponse,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
    TokenResponse,
    TraineeRegisterRequest,
    UserOut,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password

logger = logging.getLogger(__name__)

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
        db.add(UserProfile(user_id=user.id))
        db.add(UserPreferences(user_id=user.id))
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
        db.add(UserProfile(user_id=user.id))
        db.add(UserPreferences(user_id=user.id))
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
        or user.is_demo
        or not verify_password(body.password, user.password_hash)
        or user.status != "active"
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Email or password is incorrect"},
        )
    return {"access_token": create_access_token(user), "user": user}


@router.post("/demo-session", response_model=TokenResponse)
def demo_session(body: DemoSessionRequest, db: Session = Depends(get_db)) -> dict:
    if not settings.demo_mode_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "demo_unavailable", "message": "The demo workspace is unavailable."},
        )
    email = (
        settings.demo_coach_email
        if body.role == Role.COACH
        else settings.demo_trainee_email
    )
    user = db.scalar(
        select(User).where(
            User.email == email,
            User.role == body.role,
            User.is_demo.is_(True),
            User.status == "active",
        )
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "demo_unavailable", "message": "The demo workspace is unavailable."},
        )
    return {
        "access_token": create_access_token(
            user, expires_minutes=settings.demo_session_minutes
        ),
        "user": user,
    }


def _deliver_reset_email(to: str, first_name: str, token: str, expires_minutes: int) -> None:
    # Runs after the response is sent. A delivery failure must never surface to the caller
    # (that would leak account existence) and must never log the token or the reset URL.
    try:
        get_email_provider().send(
            build_reset_email(
                to=to, first_name=first_name, token=token, expires_minutes=expires_minutes
            )
        )
    except Exception:
        logger.warning("Password reset email delivery failed", exc_info=False)


@router.post(
    "/password-reset/request", response_model=GenericMessageResponse, status_code=202
)
def request_password_reset(
    body: PasswordResetRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    # The response is identical whether or not an account exists, so this endpoint never
    # reveals which emails are registered (no account enumeration).
    generic = {
        "status": "accepted",
        "message": "If an account exists for that email, a reset link has been sent.",
    }
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.status != "active" or user.is_demo or user.is_system:
        return generic
    now = datetime.now(UTC)
    # One live token at a time: consume any outstanding tokens for this user.
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    token = generate_reset_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(token),
            expires_at=now + timedelta(minutes=settings.password_reset_token_minutes),
        )
    )
    db.commit()
    background.add_task(
        _deliver_reset_email,
        user.email,
        user.first_name,
        token,
        settings.password_reset_token_minutes,
    )
    return generic


@router.post("/password-reset/confirm", response_model=GenericMessageResponse)
def confirm_password_reset(
    body: PasswordResetConfirm, db: Session = Depends(get_db)
) -> dict:
    now = datetime.now(UTC)
    invalid = HTTPException(
        status_code=400,
        detail={
            "code": "invalid_reset_token",
            "message": "This reset link is invalid or has expired. Request a new one.",
        },
    )
    token_row = db.scalar(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == hash_reset_token(body.token))
        .with_for_update()
    )
    if (
        token_row is None
        or token_row.used_at is not None
        or aware_utc(token_row.expires_at) <= now
    ):
        raise invalid
    user = db.get(User, token_row.user_id)
    if user is None or user.status != "active" or user.is_demo:
        raise invalid
    user.password_hash = hash_password(body.new_password)
    # Single-use: consume this token and revoke any other outstanding tokens.
    db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    db.commit()
    return {
        "status": "reset",
        "message": "Your password has been updated. You can now sign in.",
    }


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
