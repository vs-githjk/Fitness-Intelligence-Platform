import os
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Uuid,
    create_engine,
    func,
    inspect,
    select,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    CoachTraineeAssignment,
    Role,
    TraineeProfile,
    User,
    UserPreferences,
    UserProfile,
)
from app.security import IDENTITY_DEMO_MUTATIONS


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _coach_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "coach@example.com", "password": "CoachPass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _register_trainee(client: TestClient, email: str = "newtrainee@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register/trainee",
        json={
            "email": email,
            "password": "TraineePass123!",
            "first_name": "New",
            "last_name": "Trainee",
            "invite_code": "FIT-DEMO-2026",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _demo_trainee(db: Session) -> User:
    trainee = User(
        email=settings.demo_trainee_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Trainee",
        role=Role.TRAINEE,
        is_demo=True,
    )
    coach = User(
        email=settings.demo_coach_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Coach",
        role=Role.COACH,
        is_demo=True,
    )
    db.add_all([trainee, coach])
    db.flush()
    db.add(TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"))
    db.add(
        CoachTraineeAssignment(
            coach_id=coach.id, trainee_id=trainee.id, accepted_at=datetime.now(UTC)
        )
    )
    db.commit()
    return trainee


def test_get_profile_lazily_creates_for_existing_user(
    client: TestClient, db: Session
) -> None:
    token = _coach_token(client)
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert db.scalar(select(func.count(UserProfile.id))) == 0

    response = client.get("/api/v1/me/profile", headers=_auth(token))
    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == str(coach.id)
    assert body["preferred_display_name"] is None
    assert body["bio"] is None
    assert "created_at" in body and "updated_at" in body
    assert db.scalar(select(func.count(UserProfile.id))) == 1


def test_update_profile_persists_and_blanks_to_none(
    client: TestClient, db: Session
) -> None:
    token = _coach_token(client)
    update = client.put(
        "/api/v1/me/profile",
        headers=_auth(token),
        json={"preferred_display_name": "  Coach Cara  ", "bio": "Strength focus."},
    )
    assert update.status_code == 200
    assert update.json()["preferred_display_name"] == "Coach Cara"
    assert update.json()["bio"] == "Strength focus."

    reread = client.get("/api/v1/me/profile", headers=_auth(token))
    assert reread.json()["preferred_display_name"] == "Coach Cara"

    blanked = client.put(
        "/api/v1/me/profile", headers=_auth(token), json={"bio": "   "}
    )
    assert blanked.status_code == 200
    assert blanked.json()["bio"] is None
    # Untouched field remains.
    assert blanked.json()["preferred_display_name"] == "Coach Cara"


def test_preferences_defaults_and_partial_update(
    client: TestClient, db: Session
) -> None:
    token = _coach_token(client)
    defaults = client.get("/api/v1/me/preferences", headers=_auth(token))
    assert defaults.status_code == 200
    body = defaults.json()
    assert body["timezone"] == "UTC"
    assert body["weight_unit"] == "kg"
    assert body["distance_unit"] == "kilometers"
    assert body["locale"] == "en"
    assert body["theme"] is None
    assert body["privacy_settings"] == {}
    assert body["accessibility_settings"] == {}

    updated = client.put(
        "/api/v1/me/preferences",
        headers=_auth(token),
        json={"weight_unit": "lb", "distance_unit": "miles", "locale": "en-US"},
    )
    assert updated.status_code == 200
    assert updated.json()["weight_unit"] == "lb"
    assert updated.json()["distance_unit"] == "miles"
    assert updated.json()["locale"] == "en-US"

    # Partial update leaves other preferences intact.
    partial = client.put(
        "/api/v1/me/preferences", headers=_auth(token), json={"weight_unit": "kg"}
    )
    assert partial.json()["weight_unit"] == "kg"
    assert partial.json()["distance_unit"] == "miles"
    assert partial.json()["locale"] == "en-US"


def test_preferences_timezone_dual_writes_trainee_profile(
    client: TestClient, db: Session
) -> None:
    auth = _register_trainee(client)
    token = auth["access_token"]
    trainee_id = uuid.UUID(auth["user"]["id"])

    update = client.put(
        "/api/v1/me/preferences",
        headers=_auth(token),
        json={"timezone": "Asia/Kolkata"},
    )
    assert update.status_code == 200
    assert update.json()["timezone"] == "Asia/Kolkata"

    db.expire_all()
    trainee_profile = db.scalar(
        select(TraineeProfile).where(TraineeProfile.user_id == trainee_id)
    )
    assert trainee_profile.timezone == "Asia/Kolkata"
    legacy = client.get("/api/v1/trainee/profile", headers=_auth(token))
    assert legacy.json()["timezone"] == "Asia/Kolkata"


def test_coach_timezone_update_without_trainee_profile(client: TestClient) -> None:
    token = _coach_token(client)
    update = client.put(
        "/api/v1/me/preferences",
        headers=_auth(token),
        json={"timezone": "America/New_York"},
    )
    assert update.status_code == 200
    assert update.json()["timezone"] == "America/New_York"


def test_invalid_timezone_and_locale_rejected(client: TestClient) -> None:
    token = _coach_token(client)
    bad_tz = client.put(
        "/api/v1/me/preferences",
        headers=_auth(token),
        json={"timezone": "Not/AZone"},
    )
    assert bad_tz.status_code == 422
    bad_locale = client.put(
        "/api/v1/me/preferences",
        headers=_auth(token),
        json={"locale": "not a locale"},
    )
    assert bad_locale.status_code == 422


def test_identity_endpoints_require_authentication(client: TestClient) -> None:
    for method, path in (
        ("GET", "/api/v1/me/profile"),
        ("PUT", "/api/v1/me/profile"),
        ("GET", "/api/v1/me/preferences"),
        ("PUT", "/api/v1/me/preferences"),
    ):
        response = client.request(method, path, json={})
        assert response.status_code == 401, (method, path)


def test_identity_is_scoped_to_the_authenticated_user(
    client: TestClient, db: Session
) -> None:
    coach_token = _coach_token(client)
    trainee = _register_trainee(client)
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))

    client.put(
        "/api/v1/me/profile",
        headers=_auth(coach_token),
        json={"preferred_display_name": "Coach Only"},
    )
    trainee_profile = client.get(
        "/api/v1/me/profile", headers=_auth(trainee["access_token"])
    )
    # The trainee sees only their own record, never the coach's edit.
    assert trainee_profile.json()["user_id"] == trainee["user"]["id"]
    assert trainee_profile.json()["preferred_display_name"] is None
    coach_profile = client.get("/api/v1/me/profile", headers=_auth(coach_token))
    assert coach_profile.json()["user_id"] == str(coach.id)
    assert coach_profile.json()["preferred_display_name"] == "Coach Only"


def test_registration_creates_identity_records(
    client: TestClient, db: Session
) -> None:
    auth = _register_trainee(client)
    trainee_id = uuid.UUID(auth["user"]["id"])
    assert db.scalar(
        select(UserProfile).where(UserProfile.user_id == trainee_id)
    ) is not None
    assert db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == trainee_id)
    ) is not None


def test_demo_identity_reads_allowed_but_mutations_blocked(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _demo_trainee(db)
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    token = client.post(
        "/api/v1/auth/demo-session", json={"role": "trainee"}
    ).json()["access_token"]

    profile = client.get("/api/v1/me/profile", headers=_auth(token))
    assert profile.status_code == 200
    preferences = client.get("/api/v1/me/preferences", headers=_auth(token))
    assert preferences.status_code == 200
    # Demo timezone reflects the seeded trainee profile without persisting a row.
    assert preferences.json()["timezone"] == "Asia/Kolkata"
    assert db.scalar(select(func.count(UserProfile.id))) == 0
    assert db.scalar(select(func.count(UserPreferences.id))) == 0

    for path in ("/api/v1/me/profile", "/api/v1/me/preferences"):
        denied = client.put(path, headers=_auth(token), json={})
        assert denied.status_code == 403, path
        assert denied.json()["detail"]["code"] == "demo_read_only"
    assert db.scalar(select(func.count(UserProfile.id))) == 0
    assert db.scalar(select(func.count(UserPreferences.id))) == 0


def test_identity_demo_mutation_inventory_matches_openapi(
    client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    documented = {
        (method.upper(), path)
        for path, methods in client.app.openapi()["paths"].items()
        for method in methods
        if method.lower() in {"post", "put", "patch", "delete"}
        and path.startswith("/api/v1/me/")
    }
    assert documented == IDENTITY_DEMO_MUTATIONS

    _demo_trainee(db)
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    token = client.post(
        "/api/v1/auth/demo-session", json={"role": "trainee"}
    ).json()["access_token"]
    for method, path in IDENTITY_DEMO_MUTATIONS:
        denied = client.request(method, path, headers=_auth(token), json={})
        assert denied.status_code == 403, (method, path)
        assert denied.json()["detail"]["code"] == "demo_read_only"


def _seed_user(bind, *, role: str, timezone: str | None) -> uuid.UUID:
    """Insert a pre-0013 user (and trainee profile) using core tables."""
    now = datetime.now(UTC)
    meta = MetaData()
    users = Table(
        "users",
        meta,
        Column("id", Uuid()),
        Column("email", String()),
        Column("password_hash", String()),
        Column("first_name", String()),
        Column("last_name", String()),
        Column("role", String()),
        Column("status", String()),
        Column("is_demo", String()),
        Column("created_at", DateTime(timezone=True)),
        Column("updated_at", DateTime(timezone=True)),
    )
    trainee_profiles = Table(
        "trainee_profiles",
        meta,
        Column("id", Uuid()),
        Column("user_id", Uuid()),
        Column("timezone", String()),
        Column("created_at", DateTime(timezone=True)),
        Column("updated_at", DateTime(timezone=True)),
    )
    user_id = uuid.uuid4()
    bind.execute(
        users.insert(),
        [
            {
                "id": user_id,
                "email": f"{role}-{user_id.hex[:8]}@example.com",
                "password_hash": "x",
                "first_name": "Seed",
                "last_name": role.title(),
                "role": role,
                "status": "active",
                "is_demo": False,
                "created_at": now,
                "updated_at": now,
            }
        ],
    )
    if timezone is not None:
        bind.execute(
            trainee_profiles.insert(),
            [
                {
                    "id": uuid.uuid4(),
                    "user_id": user_id,
                    "timezone": timezone,
                    "created_at": now,
                    "updated_at": now,
                }
            ],
        )
    return user_id


def test_identity_migration_backfill_upgrade_and_downgrade(tmp_path: Path) -> None:
    database_path = tmp_path / "identity.db"
    environment = {**os.environ, "MIGRATION_DATABASE_URL": f"sqlite:///{database_path}"}
    backend_dir = Path(__file__).resolve().parents[1]

    def alembic(*arguments: str) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            cwd=backend_dir,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    # Reproduce a real deployed 0012 database, where the identity tables do not
    # yet exist (the initial revision's live metadata otherwise creates them).
    alembic("upgrade", "20260716_0012")
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS user_preferences")
        connection.exec_driver_sql("DROP TABLE IF EXISTS user_profiles")
        trainee_id = _seed_user(connection, role="trainee", timezone="Asia/Kolkata")
        coach_id = _seed_user(connection, role="coach", timezone=None)

    alembic("upgrade", "head")
    tables = set(inspect(engine).get_table_names())
    assert {"user_profiles", "user_preferences"} <= tables

    prefs = Table(
        "user_preferences",
        MetaData(),
        Column("user_id", Uuid()),
        Column("timezone", String()),
    )
    profiles = Table(
        "user_profiles", MetaData(), Column("user_id", Uuid())
    )
    with engine.connect() as connection:
        profile_ids = set(connection.execute(select(profiles.c.user_id)).scalars())
        tz_by_user = {
            row.user_id: row.timezone
            for row in connection.execute(select(prefs.c.user_id, prefs.c.timezone))
        }
    # Every pre-existing user was backfilled exactly once.
    assert profile_ids == {trainee_id, coach_id}
    assert set(tz_by_user) == {trainee_id, coach_id}
    assert tz_by_user[trainee_id] == "Asia/Kolkata"
    assert tz_by_user[coach_id] == "UTC"

    # Downgrade removes the identity tables; re-upgrade restores and re-backfills.
    alembic("downgrade", "20260716_0012")
    assert "user_profiles" not in inspect(engine).get_table_names()
    assert "user_preferences" not in inspect(engine).get_table_names()
    alembic("upgrade", "head")
    with engine.connect() as connection:
        assert (
            connection.execute(select(func.count()).select_from(profiles)).scalar() == 2
        )
