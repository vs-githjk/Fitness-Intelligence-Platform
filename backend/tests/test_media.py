import io
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.orm import Session

from app.config import settings
from app.media_services import (
    ALLOWED_TRANSITIONS,
    assert_transition,
    get_media_asset,
    open_media_content,
    purge_media,
    replace_media,
    soft_delete_media,
    upload_media,
)
from app.models import (
    MediaAsset,
    MediaLifecycleStatus,
    MediaPurpose,
    MediaStorageProviderKind,
    Role,
    TraineeProfile,
    User,
)
from app.security import MEDIA_DEMO_MUTATIONS
from app.storage import LocalStorageProvider, build_storage_provider, get_storage_provider
from app.storage.base import StorageError

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
GIF = b"GIF89a" + b"\x00" * 64
WEBP = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 64


# --------------------------------------------------------------------------- helpers


class FakeStorage:
    kind = MediaStorageProviderKind.LOCAL

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.fail_write = False

    def write_stream(self, key: str, source) -> None:
        if self.fail_write:
            raise StorageError("write failed")
        self.objects[key] = source.read()

    def open_stream(self, key: str):
        if key not in self.objects:
            raise StorageError("missing")
        payload = self.objects[key]

        def iterator():
            yield payload

        return iterator()

    def exists(self, key: str) -> bool:
        return key in self.objects

    def delete(self, key: str) -> None:
        self.objects.pop(key, None)


def _coach(db: Session) -> User:
    return db.scalar(select(User).where(User.email == "coach@example.com"))


def _other_coach(db: Session) -> User:
    return db.scalar(select(User).where(User.email == "other@example.com"))


def _upload(db: Session, storage, owner: User, uploader: User | None = None, data: bytes = PNG,
            content_type: str = "image/png", filename: str | None = "photo.png",
            purpose: MediaPurpose = MediaPurpose.GENERIC) -> MediaAsset:
    return upload_media(
        db,
        storage,
        owner=owner,
        uploader=uploader or owner,
        source=io.BytesIO(data),
        filename=filename,
        declared_content_type=content_type,
        purpose=purpose,
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _coach_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "coach@example.com", "password": "CoachPass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _other_coach_token(client: TestClient) -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "OtherPass123!"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageProvider:
    return LocalStorageProvider(tmp_path / "media")


@pytest.fixture
def media_client(client: TestClient, storage: LocalStorageProvider) -> TestClient:
    client.app.dependency_overrides[get_storage_provider] = lambda: storage
    return client


# --------------------------------------------------------------------- storage provider


def test_local_provider_write_read_exists_delete(tmp_path: Path) -> None:
    provider = LocalStorageProvider(tmp_path / "root")
    key = "generic/user/abc.png"
    provider.write_stream(key, io.BytesIO(PNG))
    assert provider.exists(key)
    assert b"".join(provider.open_stream(key)) == PNG
    provider.delete(key)
    assert not provider.exists(key)
    provider.delete(key)  # missing delete is not an error


def test_local_provider_write_is_atomic_no_temp_left(tmp_path: Path) -> None:
    provider = LocalStorageProvider(tmp_path / "root")
    provider.write_stream("generic/u/a.png", io.BytesIO(PNG))
    leftovers = [p.name for p in (provider.root / "generic" / "u").iterdir() if p.name.endswith(".tmp")]
    assert leftovers == []


@pytest.mark.parametrize("bad_key", ["../escape.png", "/etc/passwd", "a/../../b.png", "back\\slash"])
def test_local_provider_rejects_path_traversal(tmp_path: Path, bad_key: str) -> None:
    provider = LocalStorageProvider(tmp_path / "root")
    with pytest.raises(StorageError):
        provider.write_stream(bad_key, io.BytesIO(PNG))
    assert provider.exists(bad_key) is False


def test_local_provider_open_missing_raises(tmp_path: Path) -> None:
    provider = LocalStorageProvider(tmp_path / "root")
    with pytest.raises(StorageError):
        list(provider.open_stream("generic/u/missing.png"))


def test_provider_factory_rejects_unimplemented(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "media_storage_provider", "s3")
    with pytest.raises(StorageError):
        build_storage_provider(settings)


# ------------------------------------------------------------------------- media service


def test_upload_persists_active_asset_with_checksum(db: Session, storage: LocalStorageProvider) -> None:
    import hashlib

    asset = _upload(db, storage, _coach(db))
    assert asset.lifecycle_status is MediaLifecycleStatus.ACTIVE
    assert asset.byte_size == len(PNG)
    assert asset.checksum_sha256 == hashlib.sha256(PNG).hexdigest()
    assert asset.content_type == "image/png"
    assert asset.storage_provider is MediaStorageProviderKind.LOCAL
    assert asset.storage_key.startswith(f"generic/{_coach(db).id}/")
    assert storage.exists(asset.storage_key)


def test_upload_sanitizes_filename(db: Session, storage: LocalStorageProvider) -> None:
    asset = _upload(db, storage, _coach(db), filename="../../etc/pa ss?wd.png")
    assert asset.original_filename is not None
    assert "/" not in asset.original_filename and ".." not in asset.original_filename
    assert " " not in asset.original_filename


def test_upload_rejects_empty_file(db: Session, storage: LocalStorageProvider) -> None:
    with pytest.raises(Exception) as excinfo:
        _upload(db, storage, _coach(db), data=b"")
    assert excinfo.value.status_code == 400
    assert db.scalar(select(func.count(MediaAsset.id))) == 0


def test_upload_rejects_oversize(db: Session, storage: LocalStorageProvider, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "media_max_bytes", 8)
    with pytest.raises(Exception) as excinfo:
        _upload(db, storage, _coach(db), data=PNG)
    assert excinfo.value.status_code == 413
    assert db.scalar(select(func.count(MediaAsset.id))) == 0


def test_upload_rejects_disallowed_mime(db: Session, storage: LocalStorageProvider) -> None:
    with pytest.raises(Exception) as excinfo:
        _upload(db, storage, _coach(db), data=b"<svg></svg>", content_type="image/svg+xml", filename="x.svg")
    assert excinfo.value.status_code == 415


def test_upload_rejects_signature_mismatch(db: Session, storage: LocalStorageProvider) -> None:
    with pytest.raises(Exception) as excinfo:
        _upload(db, storage, _coach(db), data=b"not a real png" + b"\x00" * 20, content_type="image/png")
    assert excinfo.value.status_code == 415
    assert db.scalar(select(func.count(MediaAsset.id))) == 0


def test_upload_rejects_non_uploadable_purpose(db: Session, storage: LocalStorageProvider) -> None:
    with pytest.raises(Exception) as excinfo:
        _upload(db, storage, _coach(db), purpose=MediaPurpose.EXERCISE_IMAGE)
    assert excinfo.value.status_code == 400


def test_storage_write_failure_leaves_no_active_row(db: Session) -> None:
    fake = FakeStorage()
    fake.fail_write = True
    with pytest.raises(Exception) as excinfo:
        _upload(db, fake, _coach(db))
    assert excinfo.value.status_code == 502
    assert db.scalar(select(func.count(MediaAsset.id))) == 0


def test_db_failure_cleans_up_stored_bytes(db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeStorage()
    original_commit = db.commit

    def boom() -> None:
        raise RuntimeError("commit failed")

    monkeypatch.setattr(db, "commit", boom)
    with pytest.raises(RuntimeError):
        _upload(db, fake, _coach(db))
    monkeypatch.setattr(db, "commit", original_commit)
    # No orphaned bytes and no active row.
    assert fake.objects == {}
    assert db.scalar(select(func.count(MediaAsset.id))) == 0


def test_owner_can_read_unrelated_user_gets_404(db: Session, storage: LocalStorageProvider) -> None:
    asset = _upload(db, storage, _coach(db))
    assert get_media_asset(db, asset.id, _coach(db)).id == asset.id
    with pytest.raises(Exception) as excinfo:
        get_media_asset(db, asset.id, _other_coach(db))
    assert excinfo.value.status_code == 404


def test_content_retrieval_returns_bytes(db: Session, storage: LocalStorageProvider) -> None:
    asset = _upload(db, storage, _coach(db))
    read_asset, stream = open_media_content(db, storage, asset.id, _coach(db))
    assert read_asset.id == asset.id
    assert b"".join(stream) == PNG


def test_soft_delete_is_idempotent_and_hides_asset(db: Session, storage: LocalStorageProvider) -> None:
    asset = _upload(db, storage, _coach(db))
    deleted = soft_delete_media(db, asset.id, _coach(db))
    assert deleted.lifecycle_status is MediaLifecycleStatus.SOFT_DELETED
    assert deleted.deleted_at is not None
    # Bytes remain until purge.
    assert storage.exists(asset.storage_key)
    # Repeated delete succeeds without error and stays soft-deleted.
    again = soft_delete_media(db, asset.id, _coach(db))
    assert again.lifecycle_status is MediaLifecycleStatus.SOFT_DELETED
    # A soft-deleted asset is no longer visible through the default read.
    with pytest.raises(Exception) as excinfo:
        get_media_asset(db, asset.id, _coach(db))
    assert excinfo.value.status_code == 404


def test_replacement_transitions_prior_asset(db: Session, storage: LocalStorageProvider) -> None:
    original = _upload(db, storage, _coach(db))
    replacement = replace_media(
        db, storage, original.id, _coach(db),
        source=io.BytesIO(JPEG), filename="new.jpg", declared_content_type="image/jpeg",
    )
    db.refresh(original)
    assert original.lifecycle_status is MediaLifecycleStatus.REPLACED
    assert original.replaced_at is not None
    assert original.replaced_by_media_id == replacement.id
    assert replacement.lifecycle_status is MediaLifecycleStatus.ACTIVE
    assert replacement.content_type == "image/jpeg"


def test_purge_only_from_soft_deleted(db: Session, storage: LocalStorageProvider) -> None:
    asset = _upload(db, storage, _coach(db))
    # Cannot purge an active asset.
    with pytest.raises(Exception) as excinfo:
        purge_media(db, storage, asset.id)
    assert excinfo.value.status_code == 409
    soft_delete_media(db, asset.id, _coach(db))
    purged = purge_media(db, storage, asset.id)
    assert purged.lifecycle_status is MediaLifecycleStatus.PURGED
    assert purged.purged_at is not None
    assert not storage.exists(asset.storage_key)


def test_lifecycle_transition_table_is_enforced() -> None:
    assert ALLOWED_TRANSITIONS[MediaLifecycleStatus.PURGED] == frozenset()
    with pytest.raises(HTTPException):
        assert_transition(MediaLifecycleStatus.ACTIVE, MediaLifecycleStatus.PURGED)
    # Valid transitions do not raise.
    assert_transition(MediaLifecycleStatus.ACTIVE, MediaLifecycleStatus.SOFT_DELETED)
    assert_transition(MediaLifecycleStatus.SOFT_DELETED, MediaLifecycleStatus.PURGED)


# ------------------------------------------------------------------------------- API


def test_api_upload_and_metadata_hide_storage_key(media_client: TestClient) -> None:
    token = _coach_token(media_client)
    response = media_client.post(
        "/api/v1/media",
        headers=_auth(token),
        files={"file": ("photo.png", PNG, "image/png")},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert "storage_key" not in body
    assert body["content_type"] == "image/png"
    assert body["byte_size"] == len(PNG)
    assert body["content_url"] == f"/media/{body['id']}/content"
    assert body["lifecycle_status"] == "active"

    meta = media_client.get(f"/api/v1/media/{body['id']}", headers=_auth(token))
    assert meta.status_code == 200
    assert "storage_key" not in meta.json()


def test_api_content_delivery_headers(media_client: TestClient) -> None:
    token = _coach_token(media_client)
    created = media_client.post(
        "/api/v1/media", headers=_auth(token), files={"file": ("p.png", PNG, "image/png")}
    ).json()
    content = media_client.get(f"/api/v1/media/{created['id']}/content", headers=_auth(token))
    assert content.status_code == 200
    assert content.headers["content-type"].startswith("image/png")
    assert "inline" in content.headers["content-disposition"]
    assert content.content == PNG


def test_api_requires_authentication(media_client: TestClient) -> None:
    assert media_client.post("/api/v1/media", files={"file": ("p.png", PNG, "image/png")}).status_code == 401
    random_id = uuid.uuid4()
    assert media_client.get(f"/api/v1/media/{random_id}").status_code == 401
    assert media_client.delete(f"/api/v1/media/{random_id}").status_code == 401


def test_api_cross_user_access_is_404(media_client: TestClient) -> None:
    owner_token = _coach_token(media_client)
    created = media_client.post(
        "/api/v1/media", headers=_auth(owner_token), files={"file": ("p.png", PNG, "image/png")}
    ).json()
    intruder = _other_coach_token(media_client)
    assert media_client.get(f"/api/v1/media/{created['id']}", headers=_auth(intruder)).status_code == 404
    assert media_client.get(f"/api/v1/media/{created['id']}/content", headers=_auth(intruder)).status_code == 404
    assert media_client.delete(f"/api/v1/media/{created['id']}", headers=_auth(intruder)).status_code == 404


def test_api_delete_then_content_gone(media_client: TestClient) -> None:
    token = _coach_token(media_client)
    created = media_client.post(
        "/api/v1/media", headers=_auth(token), files={"file": ("p.png", PNG, "image/png")}
    ).json()
    assert media_client.delete(f"/api/v1/media/{created['id']}", headers=_auth(token)).status_code == 204
    # Idempotent second delete.
    assert media_client.delete(f"/api/v1/media/{created['id']}", headers=_auth(token)).status_code == 204
    assert media_client.get(f"/api/v1/media/{created['id']}", headers=_auth(token)).status_code == 404
    assert media_client.get(f"/api/v1/media/{created['id']}/content", headers=_auth(token)).status_code == 404


def test_api_rejects_bad_signature(media_client: TestClient) -> None:
    token = _coach_token(media_client)
    response = media_client.post(
        "/api/v1/media",
        headers=_auth(token),
        files={"file": ("evil.png", b"MZ not an image", "image/png")},
    )
    assert response.status_code == 415


# ------------------------------------------------------------------------------- demo


def _demo_trainee(db: Session) -> None:
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
    db.commit()


def test_demo_can_read_but_not_mutate(media_client: TestClient, db: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    _demo_trainee(db)
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    token = media_client.post("/api/v1/auth/demo-session", json={"role": "trainee"}).json()["access_token"]

    # A demo GET of an unknown asset is a normal 404 (not a demo block).
    assert media_client.get(f"/api/v1/media/{uuid.uuid4()}", headers=_auth(token)).status_code == 404
    # Mutations are demo-blocked with the established code.
    upload = media_client.post(
        "/api/v1/media", headers=_auth(token), files={"file": ("p.png", PNG, "image/png")}
    )
    assert upload.status_code == 403
    assert upload.json()["detail"]["code"] == "demo_read_only"
    delete = media_client.delete(f"/api/v1/media/{uuid.uuid4()}", headers=_auth(token))
    assert delete.status_code == 403
    assert delete.json()["detail"]["code"] == "demo_read_only"
    assert db.scalar(select(func.count(MediaAsset.id))) == 0


def test_media_demo_inventory_matches_openapi(media_client: TestClient) -> None:
    documented = {
        (method.upper(), path)
        for path, methods in media_client.app.openapi()["paths"].items()
        for method in methods
        if method.lower() in {"post", "put", "patch", "delete"}
        and path.startswith("/api/v1/media")
    }
    assert documented == MEDIA_DEMO_MUTATIONS


# --------------------------------------------------------------------------- migration


def test_media_migration_upgrade_and_downgrade(tmp_path: Path) -> None:
    database_path = tmp_path / "media.db"
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

    # Simulate a deployed database at 0013 where media_assets does not yet exist.
    alembic("upgrade", "20260721_0013")
    engine = create_engine(f"sqlite:///{database_path}")
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TABLE IF EXISTS media_assets")
    assert "media_assets" not in inspect(engine).get_table_names()

    alembic("upgrade", "head")
    assert "media_assets" in inspect(engine).get_table_names()

    alembic("downgrade", "20260721_0013")
    assert "media_assets" not in inspect(engine).get_table_names()

    alembic("upgrade", "head")
    assert "media_assets" in inspect(engine).get_table_names()
