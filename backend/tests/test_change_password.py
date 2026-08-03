from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Role, User
from app.security import hash_password

COACH_EMAIL = "coach@example.com"
OLD_PASSWORD = "CoachPass123!"
NEW_PASSWORD = "BrandNewPass1"


def _login(client: TestClient, email: str, password: str):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def _token(client: TestClient, email: str = COACH_EMAIL, password: str = OLD_PASSWORD) -> str:
    response = _login(client, email, password)
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_change_password_updates_and_invalidates_old(client: TestClient) -> None:
    token = _token(client)
    response = client.put(
        "/api/v1/me/password",
        headers=_auth(token),
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 204, response.text

    assert _login(client, COACH_EMAIL, NEW_PASSWORD).status_code == 200
    assert _login(client, COACH_EMAIL, OLD_PASSWORD).status_code == 401


def test_change_password_wrong_current_rejected(client: TestClient) -> None:
    token = _token(client)
    response = client.put(
        "/api/v1/me/password",
        headers=_auth(token),
        json={"current_password": "WrongPassword1", "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_current_password"
    # Password unchanged: the original still works.
    assert _login(client, COACH_EMAIL, OLD_PASSWORD).status_code == 200


def test_change_password_same_as_current_rejected(client: TestClient) -> None:
    token = _token(client)
    response = client.put(
        "/api/v1/me/password",
        headers=_auth(token),
        json={"current_password": OLD_PASSWORD, "new_password": OLD_PASSWORD},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "password_unchanged"


def test_change_password_too_short_rejected(client: TestClient) -> None:
    token = _token(client)
    response = client.put(
        "/api/v1/me/password",
        headers=_auth(token),
        json={"current_password": OLD_PASSWORD, "new_password": "short"},
    )
    assert response.status_code == 422


def test_change_password_requires_authentication(client: TestClient) -> None:
    response = client.put(
        "/api/v1/me/password",
        json={"current_password": OLD_PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 401


def test_change_password_denied_for_demo(
    client: TestClient, db: Session, monkeypatch
) -> None:
    db.add(
        User(
            email=settings.demo_coach_email,
            password_hash=hash_password("DemoCoachPass1"),
            first_name="Demo",
            last_name="Coach",
            role=Role.COACH,
            is_demo=True,
        )
    )
    db.commit()
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    token = client.post(
        "/api/v1/auth/demo-session", json={"role": "coach"}
    ).json()["access_token"]

    # Empty body: the demo guard (a dependency) must fire before body validation.
    response = client.put("/api/v1/me/password", headers=_auth(token), json={})
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "demo_read_only"
