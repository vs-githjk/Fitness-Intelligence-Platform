"""Local filesystem storage provider.

Used for development, CI, and automated tests. Writes are atomic (temporary file
plus rename) so an interrupted write never leaves a corrupt object presented as an
active asset. Every resolved path is confined to the configured root to prevent
path traversal; the directory is deliberately never mounted as a public static
route — all reads go through the authorized media endpoint.
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import BinaryIO

from app.models import MediaStorageProviderKind
from app.storage.base import StorageError

_CHUNK_SIZE = 64 * 1024


class LocalStorageProvider:
    kind = MediaStorageProviderKind.LOCAL

    def __init__(self, root: str | os.PathLike[str]) -> None:
        self._root = Path(root).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def _resolve(self, key: str) -> Path:
        if not key or key.startswith("/") or "\\" in key or ".." in key.split("/"):
            raise StorageError("Unsafe storage key")
        candidate = (self._root / key).resolve()
        if candidate != self._root and self._root not in candidate.parents:
            raise StorageError("Storage key escapes the storage root")
        return candidate

    def write_stream(self, key: str, source: BinaryIO) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / f".{target.name}.{uuid.uuid4().hex}.tmp"
        try:
            with temporary.open("wb") as destination:
                while chunk := source.read(_CHUNK_SIZE):
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            os.replace(temporary, target)
        except OSError as exc:  # pragma: no cover - filesystem failure path
            temporary.unlink(missing_ok=True)
            raise StorageError(f"Could not write media object: {exc}") from exc

    def open_stream(self, key: str) -> Iterator[bytes]:
        target = self._resolve(key)
        if not target.is_file():
            raise StorageError("Media object is not stored")

        def iterator() -> Iterator[bytes]:
            with target.open("rb") as handle:
                while chunk := handle.read(_CHUNK_SIZE):
                    yield chunk

        return iterator()

    def exists(self, key: str) -> bool:
        try:
            return self._resolve(key).is_file()
        except StorageError:
            return False

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)
