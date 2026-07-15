import hashlib
import secrets
from datetime import UTC, datetime

from app.models import CoachInvite


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def hash_invite_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def invite_status(invite: CoachInvite, now: datetime | None = None) -> str:
    current = now or datetime.now(UTC)
    if invite.revoked_at is not None:
        return "revoked"
    if invite.used_at is not None:
        return "used"
    if aware_utc(invite.expires_at) <= current:
        return "expired"
    return "active"


def invite_out(invite: CoachInvite) -> dict:
    return {
        "id": invite.id,
        "intended_email": invite.intended_email,
        "status": invite_status(invite),
        "expires_at": invite.expires_at,
        "used_at": invite.used_at,
        "used_by_user_id": invite.used_by_user_id,
        "revoked_at": invite.revoked_at,
        "created_at": invite.created_at,
    }
