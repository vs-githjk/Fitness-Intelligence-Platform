import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Role, User
from app.security import hash_password, verify_password
from scripts.reset_password import (
    MIN_PASSWORD_LENGTH,
    PasswordResetError,
    reset_password,
)

COACH_EMAIL = "coach@example.com"
OLD_PASSWORD = "CoachPass123!"


def _add_user(db: Session, *, email: str, is_demo: bool = False, is_system: bool = False) -> User:
    user = User(
        email=email,
        password_hash=hash_password("InitialPass123"),
        first_name="Test",
        last_name="User",
        role=Role.COACH,
        is_demo=is_demo,
        is_system=is_system,
    )
    db.add(user)
    db.commit()
    return user


def test_reset_sets_new_password_and_invalidates_old(db: Session) -> None:
    user, password = reset_password(db, COACH_EMAIL, "BrandNewPass1")

    assert password == "BrandNewPass1"
    refreshed = db.scalar(select(User).where(User.email == COACH_EMAIL))
    assert verify_password("BrandNewPass1", refreshed.password_hash)
    assert not verify_password(OLD_PASSWORD, refreshed.password_hash)
    assert user.id == refreshed.id


def test_reset_generates_compliant_password_when_omitted(db: Session) -> None:
    user, password = reset_password(db, COACH_EMAIL)

    assert len(password) >= MIN_PASSWORD_LENGTH
    assert verify_password(password, user.password_hash)


def test_reset_is_case_insensitive(db: Session) -> None:
    _, password = reset_password(db, "COACH@Example.com", "MixedCasePass1")

    refreshed = db.scalar(select(User).where(User.email == COACH_EMAIL))
    assert verify_password("MixedCasePass1", refreshed.password_hash)


def test_reset_unknown_email_raises(db: Session) -> None:
    with pytest.raises(PasswordResetError, match="No account found"):
        reset_password(db, "nobody@example.com", "SomePassword1")


def test_reset_blank_email_raises(db: Session) -> None:
    with pytest.raises(PasswordResetError, match="email address is required"):
        reset_password(db, "   ", "SomePassword1")


def test_reset_rejects_short_password(db: Session) -> None:
    with pytest.raises(PasswordResetError, match="between"):
        reset_password(db, COACH_EMAIL, "short")


def test_reset_refuses_demo_account(db: Session) -> None:
    _add_user(db, email="demo@example.com", is_demo=True)
    with pytest.raises(PasswordResetError, match="Demo accounts"):
        reset_password(db, "demo@example.com", "SomePassword1")


def test_reset_refuses_system_account(db: Session) -> None:
    _add_user(db, email="system@example.com", is_system=True)
    with pytest.raises(PasswordResetError, match="system library account"):
        reset_password(db, "system@example.com", "SomePassword1")
