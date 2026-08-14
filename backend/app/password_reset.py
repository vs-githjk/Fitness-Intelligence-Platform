"""Self-service password reset — token generation, hashing, and the reset email.

The opaque token is returned once (in the email link) and only its SHA-256 hash is ever
persisted. Nothing here logs the token or the reset URL.
"""

import hashlib
import secrets

from app.config import settings
from app.email.base import EmailMessage


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def reset_link(token: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/reset-password?token={token}"


def build_reset_email(*, to: str, first_name: str, token: str, expires_minutes: int) -> EmailMessage:
    link = reset_link(token)
    greeting = first_name.strip() or "there"
    text_body = (
        f"Hi {greeting},\n\n"
        "We received a request to reset the password for your Vytal account. "
        f"Open the link below within {expires_minutes} minutes to choose a new password:\n\n"
        f"{link}\n\n"
        "If you did not request this, you can ignore this email — your password will not "
        "change and no one can use the link without your inbox.\n\n"
        "— Vytal"
    )
    return EmailMessage(to=to, subject="Reset your Vytal password", text_body=text_body)
