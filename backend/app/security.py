import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Role, User

ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)

# Central inventory used to keep every workout-execution mutation visibly demo-protected.
WORKOUT_EXECUTION_DEMO_MUTATIONS = frozenset(
    {
        ("POST", "/api/v1/trainee/workouts/{scheduled_workout_id}/start"),
        ("POST", "/api/v1/trainee/workouts/{scheduled_workout_id}/skip"),
        ("PUT", "/api/v1/trainee/workout-sessions/{session_id}/sets/{set_id}"),
        ("POST", "/api/v1/trainee/workout-sessions/{session_id}/sets"),
        (
            "POST",
            "/api/v1/trainee/workout-sessions/{session_id}/exercises/{exercise_id}/skip",
        ),
        ("POST", "/api/v1/trainee/workout-sessions/{session_id}/complete"),
        ("POST", "/api/v1/trainee/workout-sessions/{session_id}/end-incomplete"),
        ("POST", "/api/v1/trainee/workout-sessions/{session_id}/safety-reports"),
        ("POST", "/api/v1/coach/safety-reports/{report_id}/acknowledge"),
        ("POST", "/api/v1/coach/safety-reports/{report_id}/resolve"),
    }
)

# Central inventory of shared identity mutations that must stay demo-protected.
IDENTITY_DEMO_MUTATIONS = frozenset(
    {
        ("PUT", "/api/v1/me/profile"),
        ("PUT", "/api/v1/me/preferences"),
        ("PUT", "/api/v1/me/avatar"),
        ("DELETE", "/api/v1/me/avatar"),
    }
)

# Central inventory of media mutations that must stay demo-protected.
MEDIA_DEMO_MUTATIONS = frozenset(
    {
        ("POST", "/api/v1/media"),
        ("DELETE", "/api/v1/media/{media_id}"),
    }
)

# Central inventory of starter-library mutations that must stay demo-protected.
LIBRARY_DEMO_MUTATIONS = frozenset(
    {
        ("POST", "/api/v1/program-library/{program_id}/clone"),
    }
)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user: User, expires_minutes: int | None = None) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "iat": now,
            "exp": now + timedelta(
                minutes=expires_minutes or settings.access_token_minutes
            ),
        },
        settings.jwt_secret,
        algorithm=ALGORITHM,
    )


def unauthorized(message: str = "Authentication required") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": "unauthorized", "message": message},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise unauthorized("Invalid or expired access token") from exc
    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise unauthorized("Account is unavailable")
    return user


def require_role(role: Role):
    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != role:
            raise HTTPException(
                status_code=403,
                detail={"code": "forbidden", "message": f"{role.value.title()} access required"},
            )
        return user

    return dependency


require_trainee = require_role(Role.TRAINEE)
require_coach = require_role(Role.COACH)


def ensure_not_demo(user: User) -> None:
    if user.is_demo:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "demo_read_only",
                "message": "Demo accounts are read-only.",
            },
        )
