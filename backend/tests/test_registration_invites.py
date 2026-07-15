import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.invitations import hash_invite_token
from app.models import CoachInvite, CoachProfile, CoachTraineeAssignment, Role, User


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def registration_payload(email: str) -> dict[str, str]:
    return {
        "email": email,
        "password": "RegistrationPass123!",
        "first_name": "New",
        "last_name": "User",
    }


def test_coach_registration_is_protected_and_transactional(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "coach_registration_code", None)
    disabled = client.post(
        "/api/v1/auth/register/coach",
        json={**registration_payload("new-coach@example.com"), "registration_code": "anything"},
    )
    assert disabled.status_code == 400
    assert "anything" not in disabled.text

    monkeypatch.setattr(settings, "coach_registration_code", "private-coach-code")
    invalid = client.post(
        "/api/v1/auth/register/coach",
        json={**registration_payload("new-coach@example.com"), "registration_code": "wrong"},
    )
    assert invalid.status_code == 400

    created = client.post(
        "/api/v1/auth/register/coach",
        json={
            **registration_payload("new-coach@example.com"),
            "registration_code": "private-coach-code",
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["user"]["role"] == "coach"
    coach_id = uuid.UUID(created.json()["user"]["id"])
    profile = db.scalar(select(CoachProfile).where(CoachProfile.user_id == coach_id))
    assert profile is not None
    assert profile.display_name == "New User"
    assert "private-coach-code" not in created.text


def test_coach_invite_single_use_assignment_and_authorization(
    client: TestClient, db: Session
) -> None:
    coach_token = login(client, "coach@example.com", "CoachPass123!")
    created = client.post(
        "/api/v1/coach/invites",
        headers=auth(coach_token),
        json={"intended_email": "invited@example.com", "expires_in_days": 7},
    )
    assert created.status_code == 201, created.text
    token = created.json()["token"]
    invite_id = uuid.UUID(created.json()["id"])
    stored = db.scalar(select(CoachInvite).where(CoachInvite.id == invite_id))
    assert stored is not None
    assert stored.token_hash == hash_invite_token(token)
    assert token not in stored.token_hash

    listed = client.get("/api/v1/coach/invites", headers=auth(coach_token))
    assert listed.status_code == 200
    assert "token" not in listed.json()[0]
    assert listed.json()[0]["status"] == "active"

    wrong_email = client.post(
        "/api/v1/auth/register/trainee",
        json={**registration_payload("wrong@example.com"), "invite_code": token},
    )
    assert wrong_email.status_code == 400

    registered = client.post(
        "/api/v1/auth/register/trainee",
        json={**registration_payload("invited@example.com"), "invite_code": token},
    )
    assert registered.status_code == 201, registered.text
    trainee_id = uuid.UUID(registered.json()["user"]["id"])
    assignment = db.scalar(
        select(CoachTraineeAssignment).where(
            CoachTraineeAssignment.trainee_id == trainee_id
        )
    )
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert assignment is not None and coach is not None
    assert assignment.coach_id == coach.id
    assert assignment.status == "active"

    reused = client.post(
        "/api/v1/auth/register/trainee",
        json={**registration_payload("second@example.com"), "invite_code": token},
    )
    assert reused.status_code == 400
    assert client.get(
        "/api/v1/coach/invites", headers=auth(registered.json()["access_token"])
    ).status_code == 403

    used = client.get("/api/v1/coach/invites", headers=auth(coach_token)).json()
    used_invite = next(item for item in used if item["id"] == str(invite_id))
    assert used_invite["status"] == "used"
    assert used_invite["used_by_user_id"] == str(trainee_id)


def test_invite_revocation_expiration_and_owner_scope(client: TestClient, db: Session) -> None:
    coach_token = login(client, "coach@example.com", "CoachPass123!")
    other_token = login(client, "other@example.com", "OtherPass123!")
    created = client.post(
        "/api/v1/coach/invites",
        headers=auth(coach_token),
        json={"expires_in_days": 1},
    ).json()

    assert client.post(
        f"/api/v1/coach/invites/{created['id']}/revoke", headers=auth(other_token)
    ).status_code == 404
    revoked = client.post(
        f"/api/v1/coach/invites/{created['id']}/revoke", headers=auth(coach_token)
    )
    assert revoked.status_code == 200
    assert revoked.json()["status"] == "revoked"
    assert client.post(
        "/api/v1/auth/register/trainee",
        json={**registration_payload("revoked@example.com"), "invite_code": created["token"]},
    ).status_code == 400

    expired_token = "expired-test-token"
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    db.add(
        CoachInvite(
            coach_id=coach.id,
            token_hash=hash_invite_token(expired_token),
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )
    db.commit()
    expired = client.post(
        "/api/v1/auth/register/trainee",
        json={**registration_payload("expired@example.com"), "invite_code": expired_token},
    )
    assert expired.status_code == 400


def test_roles_are_backend_owned(client: TestClient) -> None:
    coach_token = login(client, "coach@example.com", "CoachPass123!")
    me = client.get("/api/v1/auth/me", headers=auth(coach_token))
    assert me.status_code == 200
    assert me.json()["role"] == Role.COACH.value

    attempt = client.post(
        "/api/v1/auth/register/trainee",
        json={**registration_payload("role@example.com"), "invite_code": "invalid", "role": "coach"},
    )
    assert attempt.status_code == 400


def test_trainee_registration_rolls_back_all_changes(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    coach_token = login(client, "coach@example.com", "CoachPass123!")
    created = client.post(
        "/api/v1/coach/invites",
        headers=auth(coach_token),
        json={"expires_in_days": 7},
    ).json()

    def fail_commit() -> None:
        raise RuntimeError("synthetic transaction failure")

    with monkeypatch.context() as scoped:
        scoped.setattr(db, "commit", fail_commit)
        failed = client.post(
            "/api/v1/auth/register/trainee",
            json={
                **registration_payload("rollback-registration@example.com"),
                "invite_code": created["token"],
            },
        )
    assert failed.status_code == 400
    assert db.scalar(
        select(User).where(User.email == "rollback-registration@example.com")
    ) is None
    invite = db.get(CoachInvite, uuid.UUID(created["id"]))
    assert invite is not None
    assert invite.used_at is None
    assert invite.used_by_user_id is None
