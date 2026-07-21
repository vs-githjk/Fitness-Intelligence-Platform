"""Storage provider factory and public contract.

The factory is the single place that maps configuration to a concrete provider. Only
providers that are fully implemented are selectable at runtime; selecting an
unimplemented provider fails fast with a clear error rather than pretending to work.
"""

from functools import lru_cache

from app.config import Settings, settings
from app.storage.base import StorageError, StorageProvider
from app.storage.local import LocalStorageProvider

__all__ = [
    "LocalStorageProvider",
    "StorageError",
    "StorageProvider",
    "build_storage_provider",
    "get_storage_provider",
]


def build_storage_provider(config: Settings) -> StorageProvider:
    provider = config.media_storage_provider.strip().lower()
    if provider == "local":
        return LocalStorageProvider(config.media_local_root)
    # S3/R2/Azure providers are reserved but not implemented in this phase. Failing
    # here keeps configuration honest instead of silently dropping uploads.
    raise StorageError(
        f"MEDIA_STORAGE_PROVIDER '{config.media_storage_provider}' is not implemented; "
        "only 'local' is supported in this release."
    )


@lru_cache
def _cached_provider() -> StorageProvider:
    return build_storage_provider(settings)


def get_storage_provider() -> StorageProvider:
    """FastAPI dependency returning the process-wide storage provider."""
    return _cached_provider()
