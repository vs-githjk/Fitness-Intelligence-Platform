"""Provider-independent storage contract.

Application and domain code depend only on this ``StorageProvider`` protocol, never
on a concrete backend (local filesystem, S3, R2, Azure Blob). Provider
implementation modules are the only place a provider-specific SDK may be imported.
Storage keys are opaque and generated centrally by the media service; providers must
treat them as untrusted paths and refuse anything that escapes their storage root.
"""

from collections.abc import Iterator
from typing import BinaryIO, Protocol, runtime_checkable

from app.models import MediaStorageProviderKind


class StorageError(RuntimeError):
    """Raised for storage backend failures (write/read/delete/path safety)."""


@runtime_checkable
class StorageProvider(Protocol):
    """The minimal set of operations the media service actually requires.

    Delivery is handled by an authorized backend streaming endpoint, so no public
    URL resolution is part of the contract; that keeps every read behind server-side
    authorization instead of a guessable permanent URL.
    """

    kind: MediaStorageProviderKind

    def write_stream(self, key: str, source: BinaryIO) -> None:
        """Persist ``source`` at ``key`` atomically. Overwrites are not expected."""
        ...

    def open_stream(self, key: str) -> Iterator[bytes]:
        """Yield the object's bytes in chunks for streaming delivery."""
        ...

    def exists(self, key: str) -> bool:
        """Return whether an object is stored at ``key``."""
        ...

    def delete(self, key: str) -> None:
        """Remove the object at ``key``. Missing objects are not an error."""
        ...
