"""Avatar lifecycle, professional profile fields, and cross-user profile access.

Exercises the People & Identity experience end to end through the API: setting,
replacing, and removing an avatar (built on the media subsystem), the extended
profile fields, and the relationship-scoped delivery that lets an assigned coach and
trainee see each other's profile and photo while everyone else gets a 404.
"""

import io
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.avatar_services import get_active_avatar, set_avatar
from app.models import (
    CoachTraineeAssignment,
    MediaAsset,
    MediaLifecycleStatus,
    MediaPurpose,
    Role,
    TraineeProfile,
    User,
    UserProfile,
)
from app.security import create_access_token, hash_password
from app.storage import LocalStorageProvider, get_storage_provider

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64


# --------------------------------------------------------------------------- fixtures


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageProvider:
    return LocalStorageProvider(tmp_path / "media")


@pytest.fixture
def avatar_client(client: TestClient, storage: LocalStorageProvider) -> TestClient:
    client.app.dependency_overrides[get_storage_provider] = lambda: storage
    return client


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _coach(db: Session) -> User:
    return db.scalar(select(User).where(User.email == "coach@example.com"))


def _other_coach(db: Session) -> User:
    return db.scalar(select(User).where(User.email == "other@example.com"))


def _token(user: User) -> str:
    return create_access_token(user)


def _make_trainee(
    db: Session, email: str = "tara@example.com", active: bool = True
) -> User:
    coach = _coach(db)
    trainee = User(
        email=email,
        password_hash=hash_password("TraineePass123!"),
        first_name="Tara",
        last_name="Trainee",
        role=Role.TRAINEE,
    )
    db.add(trainee)
    db.flush()
    db.add(TraineeProfile(user_id=trainee.id, timezone="UTC"))
    db.add(
        CoachTraineeAssignment(
            coach_id=coach.id,
            trainee_id=trainee.id,
            status="active" if active else "cancelled",
            accepted_at=datetime.now(UTC),
        )
    )
    db.commit()
    return trainee


def _put_avatar(
    client: TestClient, token: str, data: bytes = PNG, content_type: str = "image/png"
):
    return client.put(
        "/api/v1/me/avatar",
        headers=_auth(token),
        files={"file": ("photo.png", data, content_type)},
    )


# ------------------------------------------------------------------- avatar lifecycle


def test_upload_sets_avatar_and_profile_reference(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    response = _put_avatar(avatar_client, token)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["purpose"] == "avatar"
    assert body["lifecycle_status"] == "active"
    assert body["content_url"] == f"/media/{body['id']}/content"
    assert "storage_key" not in body

    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == _coach(db).id))
    assert str(profile.avatar_media_id) == body["id"]

    reread = avatar_client.get("/api/v1/me/profile", headers=_auth(token))
    assert reread.json()["avatar"]["id"] == body["id"]


def test_replace_avatar_marks_old_replaced_and_never_orphans(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    first = _put_avatar(avatar_client, token, data=PNG).json()
    second = _put_avatar(avatar_client, token, data=JPEG, content_type="image/jpeg").json()
    assert first["id"] != second["id"]

    old = db.get(MediaAsset, uuid.UUID(first["id"]))
    new = db.get(MediaAsset, uuid.UUID(second["id"]))
    db.refresh(old)
    db.refresh(new)
    assert old.lifecycle_status is MediaLifecycleStatus.REPLACED
    assert old.replaced_by_media_id == new.id
    assert new.lifecycle_status is MediaLifecycleStatus.ACTIVE

    # Exactly one active avatar, and the profile points at it.
    active = db.scalars(
        select(MediaAsset).where(
            MediaAsset.owner_user_id == _coach(db).id,
            MediaAsset.lifecycle_status == MediaLifecycleStatus.ACTIVE,
        )
    ).all()
    assert [a.id for a in active] == [new.id]
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == _coach(db).id))
    assert profile.avatar_media_id == new.id


def test_remove_avatar_soft_deletes_and_clears_reference(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    created = _put_avatar(avatar_client, token).json()

    deleted = avatar_client.delete("/api/v1/me/avatar", headers=_auth(token))
    assert deleted.status_code == 204

    asset = db.get(MediaAsset, uuid.UUID(created["id"]))
    db.refresh(asset)
    assert asset.lifecycle_status is MediaLifecycleStatus.SOFT_DELETED
    assert asset.deleted_at is not None
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == _coach(db).id))
    assert profile.avatar_media_id is None

    assert avatar_client.get("/api/v1/me/avatar", headers=_auth(token)).json() is None
    assert avatar_client.get("/api/v1/me/profile", headers=_auth(token)).json()["avatar"] is None


def test_remove_avatar_is_idempotent_when_absent(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    assert avatar_client.delete("/api/v1/me/avatar", headers=_auth(token)).status_code == 204
    assert avatar_client.delete("/api/v1/me/avatar", headers=_auth(token)).status_code == 204


def test_get_avatar_null_when_none(avatar_client: TestClient, db: Session) -> None:
    token = _token(_coach(db))
    assert avatar_client.get("/api/v1/me/avatar", headers=_auth(token)).json() is None


def test_avatar_rejects_non_image_content(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    response = _put_avatar(avatar_client, token, data=b"MZ definitely not an image")
    assert response.status_code == 415
    # A rejected upload never leaves a dangling reference.
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == _coach(db).id))
    assert profile is None or profile.avatar_media_id is None


def test_avatar_endpoints_require_authentication(avatar_client: TestClient) -> None:
    assert avatar_client.get("/api/v1/me/avatar").status_code == 401
    assert avatar_client.delete("/api/v1/me/avatar").status_code == 401
    assert avatar_client.put(
        "/api/v1/me/avatar", files={"file": ("p.png", PNG, "image/png")}
    ).status_code == 401


# --------------------------------------------------------------- professional fields


def test_profile_update_persists_professional_fields(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    response = avatar_client.put(
        "/api/v1/me/profile",
        headers=_auth(token),
        json={
            "preferred_display_name": "Coach Cara",
            "headline": "  Strength & conditioning  ",
            "bio": "15 years in the gym.",
            "coaching_specialties": [" Powerlifting ", "Mobility", "Powerlifting", "  "],
            "years_of_experience": 15,
            "certifications_text": "NASM-CPT, CSCS",
            "training_goals": "ignored-for-coach-but-accepted",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["headline"] == "Strength & conditioning"
    # Trimmed, de-duplicated, blanks dropped.
    assert body["coaching_specialties"] == ["Powerlifting", "Mobility"]
    assert body["years_of_experience"] == 15
    assert body["certifications_text"] == "NASM-CPT, CSCS"

    reread = avatar_client.get("/api/v1/me/profile", headers=_auth(token)).json()
    assert reread["coaching_specialties"] == ["Powerlifting", "Mobility"]


def test_profile_update_validates_bounds(
    avatar_client: TestClient, db: Session
) -> None:
    token = _token(_coach(db))
    too_many_years = avatar_client.put(
        "/api/v1/me/profile", headers=_auth(token), json={"years_of_experience": 200}
    )
    assert too_many_years.status_code == 422
    long_specialty = avatar_client.put(
        "/api/v1/me/profile",
        headers=_auth(token),
        json={"coaching_specialties": ["x" * 61]},
    )
    assert long_specialty.status_code == 422


def test_trainee_can_set_training_goals(avatar_client: TestClient, db: Session) -> None:
    trainee = _make_trainee(db)
    token = _token(trainee)
    response = avatar_client.put(
        "/api/v1/me/profile",
        headers=_auth(token),
        json={"training_goals": "Run a sub-25 5K"},
    )
    assert response.status_code == 200
    assert response.json()["training_goals"] == "Run a sub-25 5K"


# ------------------------------------------------------------ cross-user profile view


def test_coach_and_trainee_can_view_each_other(
    avatar_client: TestClient, db: Session
) -> None:
    trainee = _make_trainee(db)
    coach = _coach(db)
    coach_token, trainee_token = _token(coach), _token(trainee)

    # Both upload avatars and set some profile fields.
    _put_avatar(avatar_client, coach_token)
    _put_avatar(avatar_client, trainee_token)
    avatar_client.put(
        "/api/v1/me/profile",
        headers=_auth(coach_token),
        json={"headline": "Head coach", "coaching_specialties": ["Hypertrophy"]},
    )

    # Coach views the trainee's profile + avatar.
    prof = avatar_client.get(
        f"/api/v1/users/{trainee.id}/profile", headers=_auth(coach_token)
    )
    assert prof.status_code == 200
    assert prof.json()["role"] == "trainee"
    assert prof.json()["full_name"] == "Tara Trainee"
    assert prof.json()["avatar_url"] == f"/users/{trainee.id}/avatar/content"
    img = avatar_client.get(
        f"/api/v1/users/{trainee.id}/avatar/content", headers=_auth(coach_token)
    )
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/png"
    assert img.content == PNG

    # Trainee views the coach's profile + avatar.
    coach_prof = avatar_client.get(
        f"/api/v1/users/{coach.id}/profile", headers=_auth(trainee_token)
    )
    assert coach_prof.status_code == 200
    assert coach_prof.json()["headline"] == "Head coach"
    assert coach_prof.json()["coaching_specialties"] == ["Hypertrophy"]
    assert (
        avatar_client.get(
            f"/api/v1/users/{coach.id}/avatar/content", headers=_auth(trainee_token)
        ).status_code
        == 200
    )


def test_unrelated_user_gets_404_for_profile_and_avatar(
    avatar_client: TestClient, db: Session
) -> None:
    trainee = _make_trainee(db)
    _put_avatar(avatar_client, _token(trainee))
    stranger_token = _token(_other_coach(db))  # no assignment to this trainee

    assert (
        avatar_client.get(
            f"/api/v1/users/{trainee.id}/profile", headers=_auth(stranger_token)
        ).status_code
        == 404
    )
    assert (
        avatar_client.get(
            f"/api/v1/users/{trainee.id}/avatar/content", headers=_auth(stranger_token)
        ).status_code
        == 404
    )


def test_cancelled_assignment_is_not_a_relationship(
    avatar_client: TestClient, db: Session
) -> None:
    trainee = _make_trainee(db, active=False)
    _put_avatar(avatar_client, _token(trainee))
    coach_token = _token(_coach(db))
    assert (
        avatar_client.get(
            f"/api/v1/users/{trainee.id}/profile", headers=_auth(coach_token)
        ).status_code
        == 404
    )


def test_avatar_content_404_when_target_has_no_avatar(
    avatar_client: TestClient, db: Session
) -> None:
    trainee = _make_trainee(db)
    coach_token = _token(_coach(db))
    # Related, but no photo set → still a plain 404 (no distinguishable signal).
    assert (
        avatar_client.get(
            f"/api/v1/users/{trainee.id}/avatar/content", headers=_auth(coach_token)
        ).status_code
        == 404
    )
    # The profile itself is still viewable.
    assert (
        avatar_client.get(
            f"/api/v1/users/{trainee.id}/profile", headers=_auth(coach_token)
        ).status_code
        == 200
    )


# --------------------------------------------------------- avatar_url on list payloads


def test_roster_and_relationship_payloads_carry_avatar_url(
    avatar_client: TestClient, db: Session
) -> None:
    trainee = _make_trainee(db)
    coach = _coach(db)
    coach_token, trainee_token = _token(coach), _token(trainee)

    # Before any photo: null everywhere.
    roster = avatar_client.get("/api/v1/coach/trainees", headers=_auth(coach_token)).json()
    assert roster[0]["avatar_url"] is None
    rel = avatar_client.get("/api/v1/trainee/coach", headers=_auth(trainee_token)).json()
    assert rel["coach_avatar_url"] is None

    # After photos: URLs point at the relationship-authorized route.
    _put_avatar(avatar_client, trainee_token)
    _put_avatar(avatar_client, coach_token)
    roster = avatar_client.get("/api/v1/coach/trainees", headers=_auth(coach_token)).json()
    assert roster[0]["avatar_url"] == f"/users/{trainee.id}/avatar/content"
    detail = avatar_client.get(
        f"/api/v1/coach/trainees/{trainee.id}", headers=_auth(coach_token)
    ).json()
    assert detail["avatar_url"] == f"/users/{trainee.id}/avatar/content"
    rel = avatar_client.get("/api/v1/trainee/coach", headers=_auth(trainee_token)).json()
    assert rel["coach_avatar_url"] == f"/users/{coach.id}/avatar/content"


# ------------------------------------------------------------------- service internals


def test_set_avatar_service_reuses_media_and_transitions(
    db: Session, storage: LocalStorageProvider
) -> None:
    coach = _coach(db)
    first = set_avatar(
        db, storage, coach,
        source=io.BytesIO(PNG), filename="a.png", declared_content_type="image/png",
    )
    assert first.purpose is MediaPurpose.AVATAR
    assert get_active_avatar(db, coach.id).id == first.id

    second = set_avatar(
        db, storage, coach,
        source=io.BytesIO(JPEG), filename="b.jpg", declared_content_type="image/jpeg",
    )
    db.refresh(first)
    assert first.lifecycle_status is MediaLifecycleStatus.REPLACED
    assert get_active_avatar(db, coach.id).id == second.id
    # No orphaned active assets.
    assert db.scalar(
        select(func.count(MediaAsset.id)).where(
            MediaAsset.owner_user_id == coach.id,
            MediaAsset.lifecycle_status == MediaLifecycleStatus.ACTIVE,
        )
    ) == 1
