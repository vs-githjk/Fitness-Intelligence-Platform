"""S3-compatible storage provider — behavior verified against an in-memory fake client
(no boto3 / no network). Real S3/R2 I/O is exercised only with production credentials."""

import io

import pytest

from app.models import MediaStorageProviderKind
from app.storage.base import StorageError
from app.storage.s3 import S3StorageProvider


class FakeS3:
    """Minimal stand-in for a boto3 S3 client covering the calls the provider makes."""

    def __init__(self) -> None:
        self.store: dict[tuple[str, str], bytes] = {}

    def upload_fileobj(self, fileobj, Bucket, Key):  # noqa: N803 - boto3 kwarg names
        self.store[(Bucket, Key)] = fileobj.read()

    def get_object(self, Bucket, Key):  # noqa: N803
        if (Bucket, Key) not in self.store:
            raise KeyError("NoSuchKey")
        return {"Body": io.BytesIO(self.store[(Bucket, Key)])}

    def head_object(self, Bucket, Key):  # noqa: N803
        if (Bucket, Key) not in self.store:
            raise KeyError("NoSuchKey")

    def delete_object(self, Bucket, Key):  # noqa: N803
        self.store.pop((Bucket, Key), None)


def test_roundtrip_write_read_exists_delete():
    fake = FakeS3()
    provider = S3StorageProvider(bucket="b", client=fake)
    assert provider.kind == MediaStorageProviderKind.S3
    provider.write_stream("media/exercise/x.bin", io.BytesIO(b"hello bytes"))
    assert provider.exists("media/exercise/x.bin") is True
    assert b"".join(provider.open_stream("media/exercise/x.bin")) == b"hello bytes"
    provider.delete("media/exercise/x.bin")
    assert provider.exists("media/exercise/x.bin") is False
    provider.delete("media/exercise/x.bin")  # idempotent — no error on missing


def test_requires_a_bucket():
    with pytest.raises(StorageError):
        S3StorageProvider(bucket=None, client=FakeS3())


def test_rejects_unsafe_keys():
    provider = S3StorageProvider(bucket="b", client=FakeS3())
    for bad in ("../escape", "/absolute", "a\\b", "x/../y"):
        with pytest.raises(StorageError):
            provider.write_stream(bad, io.BytesIO(b"x"))


def test_open_missing_object_raises_storage_error():
    provider = S3StorageProvider(bucket="b", client=FakeS3())
    with pytest.raises(StorageError):
        list(provider.open_stream("does/not/exist"))


def test_factory_selects_s3(monkeypatch):
    from app.config import settings
    from app.storage import build_storage_provider

    monkeypatch.setattr(settings, "media_storage_provider", "s3", raising=False)
    monkeypatch.setattr(settings, "media_s3_bucket", "b", raising=False)
    # No boto3 client is created because we don't perform I/O here; construction with a
    # real client would require boto3. Assert the factory routes to the s3 branch by
    # verifying it raises only if boto3 is unavailable, else returns an S3 provider.
    try:
        provider = build_storage_provider(settings)
    except StorageError as exc:
        assert "boto3" in str(exc)
    else:
        assert provider.kind == MediaStorageProviderKind.S3
