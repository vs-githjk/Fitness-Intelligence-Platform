"""Exercise authored media: upload, replace, remove, authorization, and lifecycle.

Exercises the coach-facing exercise media surface end to end through the API and
verifies the invariants that keep published versions immutable: a shared asset is
never retired while another version still references it, and system exercises stay
read-only while their media is still deliverable to any coach who can see them.
"""

import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.media_services import upload_media
from app.models import (
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseVersion,
    ExerciseVersionStatus,
    MediaAsset,
    MediaLifecycleStatus,
    MediaPurpose,
    Role,
    User,
    utcnow,
)
from app.storage import LocalStorageProvider, get_storage_provider
from scripts.seed import seed_exercise_library

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
MP4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 48
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 48


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageProvider:
    return LocalStorageProvider(tmp_path / "media")


@pytest.fixture
def ex_client(client: TestClient, storage: LocalStorageProvider) -> TestClient:
    client.app.dependency_overrides[get_storage_provider] = lambda: storage
    return client


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _payload(slug: str = "coach-media-ex") -> dict:
    return {
        "slug": slug,
        "name": "Coach media exercise",
        "instructions": "Move through a controlled range and record completed repetitions.",
        "tracking_mode": "repetitions_only",
        "category": "strength",
        "movement_pattern": "horizontal pull",
        "primary_muscle_groups": ["back"],
    }


def _create_draft(client: TestClient, token: str, slug: str = "coach-media-ex") -> str:
    res = client.post("/api/v1/coach/exercises", headers=_auth(token), json=_payload(slug))
    assert res.status_code == 201, res.text
    return res.json()["id"]


def _put_media(client, token, exercise_id, slot, data=PNG, content_type="image/png"):
    return client.put(
        f"/api/v1/coach/exercises/{exercise_id}/media/{slot}",
        headers=_auth(token),
        files={"file": (f"{slot}.bin", data, content_type)},
    )


# --------------------------------------------------------------------- upload + linkage


def test_upload_images_and_video_link_to_the_draft_version(
    ex_client: TestClient, db: Session
) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)

    primary = _put_media(ex_client, token, exercise_id, "primary_image", PNG, "image/png")
    assert primary.status_code == 200, primary.text
    draft = primary.json()["draft_version"]
    assert draft["primary_image"]["purpose"] == "exercise_image"
    assert draft["primary_image"]["content_type"] == "image/png"
    media_id = draft["primary_image"]["id"]
    assert draft["primary_image"]["content_url"] == (
        f"/coach/exercises/{exercise_id}/media/{media_id}/content"
    )

    secondary = _put_media(ex_client, token, exercise_id, "secondary_image", JPEG, "image/jpeg")
    assert secondary.json()["draft_version"]["secondary_image"]["content_type"] == "image/jpeg"

    video = _put_media(ex_client, token, exercise_id, "demonstration_video", MP4, "video/mp4")
    assert video.status_code == 200, video.text
    demo = video.json()["draft_version"]["demonstration_video"]
    assert demo["purpose"] == "exercise_video"
    assert demo["content_type"] == "video/mp4"

    # The bytes stream back through the authorized delivery route.
    content = ex_client.get(
        f"/api/v1/coach/exercises/{exercise_id}/media/{media_id}/content", headers=_auth(token)
    )
    assert content.status_code == 200
    assert content.headers["content-type"] == "image/png"
    assert content.content == PNG


def test_webm_video_is_accepted(ex_client: TestClient, db: Session) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)
    res = _put_media(ex_client, token, exercise_id, "demonstration_video", WEBM, "video/webm")
    assert res.status_code == 200, res.text


def test_image_slot_rejects_video_and_bad_signature(
    ex_client: TestClient, db: Session
) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)
    # A video type on an image slot is unsupported.
    assert _put_media(ex_client, token, exercise_id, "primary_image", MP4, "video/mp4").status_code == 415
    # A declared image whose bytes are not that image fails the signature check.
    assert _put_media(ex_client, token, exercise_id, "primary_image", b"not-an-image", "image/png").status_code == 415
    # A video slot rejects a declared image type.
    assert _put_media(ex_client, token, exercise_id, "demonstration_video", PNG, "image/png").status_code == 415


# --------------------------------------------------------------------- replace + remove


def test_replace_marks_old_replaced_and_keeps_one_active(
    ex_client: TestClient, db: Session
) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)
    first_id = _put_media(ex_client, token, exercise_id, "primary_image").json()["draft_version"]["primary_image"]["id"]
    second_id = _put_media(ex_client, token, exercise_id, "primary_image", JPEG, "image/jpeg").json()["draft_version"]["primary_image"]["id"]
    assert first_id != second_id

    old = db.get(MediaAsset, uuid.UUID(first_id))
    new = db.get(MediaAsset, uuid.UUID(second_id))
    db.refresh(old)
    assert old.lifecycle_status is MediaLifecycleStatus.REPLACED
    assert old.replaced_by_media_id == new.id
    assert new.lifecycle_status is MediaLifecycleStatus.ACTIVE
    # The old asset's bytes are no longer delivered.
    assert ex_client.get(
        f"/api/v1/coach/exercises/{exercise_id}/media/{first_id}/content", headers=_auth(token)
    ).status_code == 404


def test_remove_soft_deletes_and_detaches(ex_client: TestClient, db: Session) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)
    media_id = _put_media(ex_client, token, exercise_id, "primary_image").json()["draft_version"]["primary_image"]["id"]

    removed = ex_client.delete(
        f"/api/v1/coach/exercises/{exercise_id}/media/primary_image", headers=_auth(token)
    )
    assert removed.status_code == 200
    assert removed.json()["draft_version"]["primary_image"] is None
    asset = db.get(MediaAsset, uuid.UUID(media_id))
    db.refresh(asset)
    assert asset.lifecycle_status is MediaLifecycleStatus.SOFT_DELETED
    # Idempotent: removing again is a no-op success.
    assert ex_client.delete(
        f"/api/v1/coach/exercises/{exercise_id}/media/primary_image", headers=_auth(token)
    ).status_code == 200


# --------------------------------------------------- immutability across a revision


def test_published_version_media_survives_draft_edits(
    ex_client: TestClient, db: Session
) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)
    original_id = _put_media(ex_client, token, exercise_id, "primary_image").json()["draft_version"]["primary_image"]["id"]
    # Publish, then open a revision that copies the media reference.
    ex_client.post(f"/api/v1/coach/exercises/{exercise_id}/publish", headers=_auth(token))
    revised = ex_client.post(f"/api/v1/coach/exercises/{exercise_id}/revisions", headers=_auth(token))
    assert revised.json()["draft_version"]["primary_image"]["id"] == original_id

    # Replace on the draft; the published version's asset must stay ACTIVE (shared).
    _put_media(ex_client, token, exercise_id, "primary_image", JPEG, "image/jpeg")
    original = db.get(MediaAsset, uuid.UUID(original_id))
    db.refresh(original)
    assert original.lifecycle_status is MediaLifecycleStatus.ACTIVE

    detail = ex_client.get(f"/api/v1/coach/exercises/{exercise_id}", headers=_auth(token)).json()
    published = next(v for v in detail["versions"] if v["status"] == "published")
    assert published["primary_image"]["id"] == original_id
    # And the shared original is still deliverable through the published version.
    assert ex_client.get(
        f"/api/v1/coach/exercises/{exercise_id}/media/{original_id}/content", headers=_auth(token)
    ).status_code == 200


# --------------------------------------------------------------------- authorization


def test_media_requires_an_editable_draft(ex_client: TestClient, db: Session) -> None:
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)
    ex_client.post(f"/api/v1/coach/exercises/{exercise_id}/publish", headers=_auth(token))
    # No draft after publishing → cannot change media until a revision is opened.
    res = _put_media(ex_client, token, exercise_id, "primary_image")
    assert res.status_code == 409
    assert res.json()["detail"]["code"] == "exercise_draft_missing"


def test_system_exercise_media_is_read_only(ex_client: TestClient, db: Session) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    seed_exercise_library(db, coach)
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    system = db.scalar(select(Exercise).where(Exercise.scope == ExerciseScope.SYSTEM))
    res = _put_media(ex_client, token, str(system.id), "primary_image")
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "system_exercise_read_only"


def test_cross_coach_media_is_hidden(ex_client: TestClient, db: Session) -> None:
    owner = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, owner)
    media_id = _put_media(ex_client, owner, exercise_id, "primary_image").json()["draft_version"]["primary_image"]["id"]

    other = _login(ex_client, "other@example.com", "OtherPass123!")
    # Another coach cannot edit or even see the private exercise or its media.
    assert _put_media(ex_client, other, exercise_id, "primary_image").status_code == 404
    assert ex_client.get(
        f"/api/v1/coach/exercises/{exercise_id}/media/{media_id}/content", headers=_auth(other)
    ).status_code == 404
    # An unrelated media id under a visible exercise is also a 404 (no leakage).
    assert ex_client.get(
        f"/api/v1/coach/exercises/{exercise_id}/media/{uuid.uuid4()}/content", headers=_auth(owner)
    ).status_code == 404


def test_demo_cannot_edit_exercise_media(
    ex_client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import settings

    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    exercise_id = _create_draft(ex_client, token)

    demo = User(
        email=settings.demo_coach_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Coach",
        role=Role.COACH,
        is_demo=True,
    )
    db.add(demo)
    db.commit()
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    demo_token = ex_client.post(
        "/api/v1/auth/demo-session", json={"role": "coach"}
    ).json()["access_token"]

    upload = _put_media(ex_client, demo_token, exercise_id, "primary_image")
    assert upload.status_code == 403
    assert upload.json()["detail"]["code"] == "demo_read_only"
    delete = ex_client.delete(
        f"/api/v1/coach/exercises/{exercise_id}/media/primary_image", headers=_auth(demo_token)
    )
    assert delete.status_code == 403
    assert db.scalar(select(func.count(MediaAsset.id))) == 0
    assert coach is not None


# ---------------------------------------------- system exercises may carry media


def test_system_exercise_can_carry_and_deliver_media(
    ex_client: TestClient, db: Session, storage: LocalStorageProvider
) -> None:
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    # A system exercise version authored with a demonstration image (as the seed does).
    exercise = Exercise(
        scope=ExerciseScope.SYSTEM,
        owner_coach_id=None,
        slug="system-demo-media",
        status=ExerciseStatus.ACTIVE,
    )
    db.add(exercise)
    db.flush()
    version = ExerciseVersion(
        exercise_id=exercise.id,
        version_number=1,
        status=ExerciseVersionStatus.PUBLISHED,
        name="System demo",
        instructions="Perform the movement with control.",
        tracking_mode="repetitions_only",
        category="strength",
        movement_pattern="squat",
        primary_muscle_groups=["quadriceps"],
        published_at=utcnow(),
        content_hash="x" * 64,
    )
    db.add(version)
    db.flush()
    asset = upload_media(
        db, storage, owner=coach, uploader=coach,
        source=io.BytesIO(PNG), filename="demo.png",
        declared_content_type="image/png", purpose=MediaPurpose.EXERCISE_IMAGE,
    )
    version.primary_image_media_id = asset.id
    db.commit()

    token = _login(ex_client, "coach@example.com", "CoachPass123!")
    # A coach can see the system exercise and stream its demonstration media.
    detail = ex_client.get(f"/api/v1/coach/exercises/{exercise.id}", headers=_auth(token))
    assert detail.json()["published_version"]["primary_image"]["id"] == str(asset.id)
    content = ex_client.get(
        f"/api/v1/coach/exercises/{exercise.id}/media/{asset.id}/content", headers=_auth(token)
    )
    assert content.status_code == 200
    assert content.content == PNG
