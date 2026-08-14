"""Self-service password reset flow (POST /auth/password-reset/request + /confirm).

Complements the operator CLI in scripts/reset_password.py (see test_reset_password.py):
this is the user-facing, token-based, no-enumeration flow.
"""

from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlsplit

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.email.base import EmailMessage
from app.models import PasswordResetToken, Role, User
from app.password_reset import generate_reset_token, hash_reset_token
from app.security import hash_password

REQUEST = "/api/v1/auth/password-reset/request"
CONFIRM = "/api/v1/auth/password-reset/confirm"
LOGIN = "/api/v1/auth/login"


class _Recorder:
    """A fake email provider that captures messages instead of delivering them."""

    def __init__(self) -> None:
        self.messages: list[EmailMessage] = []

    def send(self, message: EmailMessage) -> None:
        self.messages.append(message)


def _patch_email(monkeypatch) -> _Recorder:
    recorder = _Recorder()
    monkeypatch.setattr("app.api.auth.get_email_provider", lambda: recorder)
    return recorder


def _token_from(message: EmailMessage) -> str:
    for word in message.text_body.split():
        if "reset-password?token=" in word:
            return parse_qs(urlsplit(word).query)["token"][0]
    raise AssertionError("no reset link found in the email body")


def _count_tokens(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(PasswordResetToken))


def test_request_stores_only_a_hash_and_emails_a_link(client, db, monkeypatch) -> None:
    recorder = _patch_email(monkeypatch)
    response = client.post(REQUEST, json={"email": "coach@example.com"})
    assert response.status_code == 202
    assert "if an account exists" in response.json()["message"].lower()

    assert len(recorder.messages) == 1
    token = _token_from(recorder.messages[0])
    rows = db.scalars(select(PasswordResetToken)).all()
    assert len(rows) == 1
    # The raw token is never persisted — only its SHA-256 hash.
    assert rows[0].token_hash == hash_reset_token(token)
    assert token not in rows[0].token_hash


def test_confirm_updates_password_and_is_single_use(client, monkeypatch) -> None:
    recorder = _patch_email(monkeypatch)
    client.post(REQUEST, json={"email": "coach@example.com"})
    token = _token_from(recorder.messages[0])

    confirmed = client.post(CONFIRM, json={"token": token, "new_password": "BrandNewPass1"})
    assert confirmed.status_code == 200

    assert client.post(LOGIN, json={"email": "coach@example.com", "password": "BrandNewPass1"}).status_code == 200
    assert client.post(LOGIN, json={"email": "coach@example.com", "password": "CoachPass123!"}).status_code == 401

    # The token cannot be replayed.
    replay = client.post(CONFIRM, json={"token": token, "new_password": "YetAnother9"})
    assert replay.status_code == 400


def test_unknown_email_is_generic_and_creates_nothing(client, db, monkeypatch) -> None:
    recorder = _patch_email(monkeypatch)
    unknown = client.post(REQUEST, json={"email": "nobody@example.com"})
    known = client.post(REQUEST, json={"email": "coach@example.com"})
    # Identical response body — no account enumeration.
    assert unknown.status_code == known.status_code == 202
    assert unknown.json() == known.json()
    # The unknown address produced neither a token nor an email.
    assert _count_tokens(db) == 1
    assert [m.to for m in recorder.messages] == ["coach@example.com"]


def test_requesting_again_consumes_the_previous_token(client, db, monkeypatch) -> None:
    recorder = _patch_email(monkeypatch)
    client.post(REQUEST, json={"email": "coach@example.com"})
    first = _token_from(recorder.messages[0])
    client.post(REQUEST, json={"email": "coach@example.com"})
    second = _token_from(recorder.messages[1])

    # The first token no longer works; only the most recent one does.
    assert client.post(CONFIRM, json={"token": first, "new_password": "BrandNewPass1"}).status_code == 400
    assert client.post(CONFIRM, json={"token": second, "new_password": "BrandNewPass1"}).status_code == 200


def test_expired_token_is_rejected(client, db) -> None:
    user = db.scalar(select(User).where(User.email == "coach@example.com"))
    token = generate_reset_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(token),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    db.commit()
    response = client.post(CONFIRM, json={"token": token, "new_password": "BrandNewPass1"})
    assert response.status_code == 400


def test_invalid_token_is_rejected(client) -> None:
    response = client.post(CONFIRM, json={"token": "z" * 40, "new_password": "BrandNewPass1"})
    assert response.status_code == 400


def test_demo_account_receives_no_reset_token(client, db, monkeypatch) -> None:
    recorder = _patch_email(monkeypatch)
    db.add(
        User(
            email="demo.coach@example.com",
            password_hash=hash_password("DemoPass1234"),
            first_name="Demo",
            last_name="Coach",
            role=Role.COACH,
            is_demo=True,
        )
    )
    db.commit()
    response = client.post(REQUEST, json={"email": "demo.coach@example.com"})
    assert response.status_code == 202
    assert recorder.messages == []
    assert _count_tokens(db) == 0
