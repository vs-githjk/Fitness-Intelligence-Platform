"""Operator CLI to reset a login account's password.

An internal maintenance tool for the controlled test-user stage. It sets a new
password on an existing account so an operator can hand it to the user
out-of-band (there is no email/notification channel yet). It is deliberately
NOT a public endpoint and creates no browser-facing surface or account-
enumeration risk: it can only be run from a trusted shell with database access.

Demo accounts (read-only) and the non-login system library account are refused.

Usage:
    python -m scripts.reset_password --email someone@example.com
    python -m scripts.reset_password --email someone@example.com --password 'NewSecret123'

With no --password, a strong random password is generated and printed once so
it can be relayed to the user; treat it as temporary.
"""

from __future__ import annotations

import argparse
import secrets
import sys

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128
# token_urlsafe(18) yields ~24 URL-safe characters, comfortably within policy.
GENERATED_PASSWORD_BYTES = 18


class PasswordResetError(Exception):
    """Raised when a password reset cannot be performed."""


def reset_password(db: Session, email: str, new_password: str | None = None) -> tuple[User, str]:
    """Set a new password for the account matching ``email`` (case-insensitive).

    Returns the affected user and the plaintext password that was set. When
    ``new_password`` is ``None`` a policy-compliant random password is generated.
    Raises :class:`PasswordResetError` for a missing email, an unknown account,
    a demo/system account, or a password outside the length policy.
    """
    normalized = email.strip().lower()
    if not normalized:
        raise PasswordResetError("An email address is required.")

    user = db.scalar(select(User).where(func.lower(User.email) == normalized))
    if user is None:
        raise PasswordResetError(f"No account found for {email!r}.")
    if user.is_demo:
        raise PasswordResetError("Demo accounts are read-only; their password cannot be reset.")
    if user.is_system:
        raise PasswordResetError("The system library account has no login and cannot be reset.")

    if new_password is None:
        new_password = secrets.token_urlsafe(GENERATED_PASSWORD_BYTES)
    if not MIN_PASSWORD_LENGTH <= len(new_password) <= MAX_PASSWORD_LENGTH:
        raise PasswordResetError(
            f"Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters."
        )

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    return user, new_password


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reset a Vytal login account's password (operator tool)."
    )
    parser.add_argument("--email", required=True, help="Email of the account to reset.")
    parser.add_argument(
        "--password",
        help=(
            f"New password ({MIN_PASSWORD_LENGTH}-{MAX_PASSWORD_LENGTH} characters). "
            "If omitted, a strong random password is generated and printed."
        ),
    )
    args = parser.parse_args(argv)

    with SessionLocal() as db:
        try:
            user, password = reset_password(db, args.email, args.password)
        except PasswordResetError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        email = user.email
        role = user.role.value

    print(f"Password reset for {email} (role={role}).")
    if args.password is None:
        print(f"Temporary password: {password}")
        print("Relay this out-of-band; the user should treat it as temporary.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
