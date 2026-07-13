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


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(user: User) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
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
