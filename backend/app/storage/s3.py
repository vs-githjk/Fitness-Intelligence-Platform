"""S3-compatible storage provider (AWS S3 / Cloudflare R2) for durable production media.

Objects are private: nothing here returns a public or pre-signed URL. Delivery stays behind
the authorized streaming endpoint (``open_stream``), exactly like the local provider, so
media authorization is unchanged when moving from local to S3.

``boto3`` is imported lazily so the dependency is only required when this provider is actually
selected (``MEDIA_STORAGE_PROVIDER=s3``); local/dev/test never import it. Credentials come from
boto3's standard environment credential chain (e.g. ``AWS_ACCESS_KEY_ID`` /
``AWS_SECRET_ACCESS_KEY``) — never from application config or the repo. For R2, set an
``endpoint_url`` and the account's S3 access keys.
"""

from collections.abc import Iterator
from typing import Any, BinaryIO

from app.models import MediaStorageProviderKind
from app.storage.base import StorageError

_CHUNK_SIZE = 64 * 1024


def _validate_key(key: str) -> str:
    # Keys are generated centrally, but treat them as untrusted: no absolute paths, no
    # traversal, no backslashes. Mirrors the local provider's guarantee.
    if not key or key.startswith("/") or "\\" in key or ".." in key.split("/"):
        raise StorageError("Unsafe storage key")
    return key


class S3StorageProvider:
    kind = MediaStorageProviderKind.S3

    def __init__(
        self, *, bucket: str | None, region: str | None = None,
        endpoint_url: str | None = None, client: Any = None,
    ) -> None:
        if not bucket:
            raise StorageError("MEDIA_S3_BUCKET is required for the s3 storage provider")
        self._bucket = bucket
        self._client = client if client is not None else self._build_client(region, endpoint_url)

    @staticmethod
    def _build_client(region: str | None, endpoint_url: str | None) -> Any:
        try:
            import boto3  # lazy: only needed when the s3 provider is selected
        except ImportError as exc:  # pragma: no cover - exercised only without boto3 installed
            raise StorageError(
                "The s3 storage provider requires boto3; install it in the production image."
            ) from exc
        return boto3.client("s3", region_name=region, endpoint_url=endpoint_url)

    def write_stream(self, key: str, source: BinaryIO) -> None:
        try:
            self._client.upload_fileobj(source, self._bucket, _validate_key(key))
        except StorageError:
            raise
        except Exception as exc:  # noqa: BLE001 - normalize any SDK error to StorageError
            raise StorageError(f"Could not write media object: {exc}") from exc

    def open_stream(self, key: str) -> Iterator[bytes]:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=_validate_key(key))
        except StorageError:
            raise
        except Exception as exc:  # noqa: BLE001 - missing object or SDK error
            raise StorageError("Media object is not stored") from exc
        body = response["Body"]

        def iterator() -> Iterator[bytes]:
            try:
                while chunk := body.read(_CHUNK_SIZE):
                    yield chunk
            finally:
                close = getattr(body, "close", None)
                if callable(close):
                    close()

        return iterator()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=_validate_key(key))
            return True
        except StorageError:
            return False
        except Exception:  # noqa: BLE001 - not found or access error -> treat as absent
            return False

    def delete(self, key: str) -> None:
        # S3 delete is idempotent; a missing object is not an error.
        self._client.delete_object(Bucket=self._bucket, Key=_validate_key(key))
