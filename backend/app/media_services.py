"""Media application service.

Owns every media rule so routes stay thin: file validation (size, MIME allowlist,
magic-byte signature), filename sanitization, SHA-256 checksums, opaque storage-key
generation, storage writes, metadata persistence, lifecycle transitions, and
authorization. Routes never touch files, providers, storage keys, or lifecycle
fields directly.

Security posture and limitations are documented in docs/decisions (ADR-0013/0014).
There is no malware scanning and no EXIF stripping in this phase; a passing MIME and
signature check does not make a file "safe", and delivery is always authorized and
never a public static route.
"""

import hashlib
import re
import tempfile
import unicodedata
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import BinaryIO

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.models import (
    MediaAsset,
    MediaLifecycleStatus,
    MediaPurpose,
    MediaVisibility,
    User,
)
from app.storage.base import StorageError, StorageProvider

_CHUNK = 64 * 1024
_SPOOL_THRESHOLD = 1024 * 1024

# Narrow Phase 2 allowlist: raster images only. SVG is excluded because it can carry
# active content; documents, archives, and scriptable formats are rejected.
ALLOWED_CONTENT_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)
# Demonstration videos: container formats only, no streaming/transcoding. The file is
# stored as-is and delivered through the same authorized route as images.
ALLOWED_VIDEO_CONTENT_TYPES: frozenset[str] = frozenset({"video/mp4", "video/webm"})
_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "video/mp4": "mp4",
    "video/webm": "webm",
}
# Purposes accepted by feature-mediated upload flows. Images cover avatars and
# exercise images; video is reserved for a single exercise demonstration clip.
IMAGE_PURPOSES: frozenset[MediaPurpose] = frozenset(
    {MediaPurpose.GENERIC, MediaPurpose.AVATAR, MediaPurpose.EXERCISE_IMAGE}
)
VIDEO_PURPOSES: frozenset[MediaPurpose] = frozenset({MediaPurpose.EXERCISE_VIDEO})
UPLOADABLE_PURPOSES: frozenset[MediaPurpose] = IMAGE_PURPOSES | VIDEO_PURPOSES

# Documented, enforced lifecycle transitions.
ALLOWED_TRANSITIONS: dict[MediaLifecycleStatus, frozenset[MediaLifecycleStatus]] = {
    MediaLifecycleStatus.ACTIVE: frozenset(
        {MediaLifecycleStatus.REPLACED, MediaLifecycleStatus.SOFT_DELETED}
    ),
    MediaLifecycleStatus.REPLACED: frozenset({MediaLifecycleStatus.SOFT_DELETED}),
    MediaLifecycleStatus.SOFT_DELETED: frozenset({MediaLifecycleStatus.PURGED}),
    MediaLifecycleStatus.PURGED: frozenset(),
}


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _not_found() -> HTTPException:
    # Uniform 404 for missing, gone, or cross-account assets so existence is not leaked.
    return _error(404, "media_not_found", "Media asset not found.")


def assert_transition(
    current: MediaLifecycleStatus, target: MediaLifecycleStatus
) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise _error(
            409,
            "media_invalid_transition",
            f"Cannot move media from {current.value} to {target.value}.",
        )


def _sanitize_filename(name: str | None) -> str | None:
    if not name:
        return None
    base = name.replace("\\", "/").split("/")[-1]
    base = unicodedata.normalize("NFKC", base)
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base).strip("._")
    return base[:255] or None


def _signature_matches(content_type: str, header: bytes) -> bool:
    if content_type == "image/jpeg":
        return header[:3] == b"\xff\xd8\xff"
    if content_type == "image/png":
        return header[:8] == b"\x89PNG\r\n\x1a\n"
    if content_type == "image/gif":
        return header[:6] in (b"GIF87a", b"GIF89a")
    if content_type == "image/webp":
        return header[:4] == b"RIFF" and header[8:12] == b"WEBP"
    if content_type == "video/mp4":
        # ISO base media format: a 'ftyp' box begins the file (after its 4-byte size).
        return header[4:8] == b"ftyp"
    if content_type == "video/webm":
        # Matroska/WebM starts with the EBML header magic.
        return header[:4] == b"\x1a\x45\xdf\xa3"
    return False


def _spool_and_hash(source: BinaryIO, max_bytes: int) -> tuple[BinaryIO, str, int, bytes]:
    """Stream ``source`` to a spooled temp file, capping size and hashing as we go."""
    spool: BinaryIO = tempfile.SpooledTemporaryFile(max_size=_SPOOL_THRESHOLD)
    hasher = hashlib.sha256()
    size = 0
    header = b""
    while chunk := source.read(_CHUNK):
        size += len(chunk)
        if size > max_bytes:
            spool.close()
            raise _error(
                413,
                "media_too_large",
                f"File exceeds the maximum size of {max_bytes} bytes.",
            )
        if len(header) < 16:
            header += chunk[: 16 - len(header)]
        hasher.update(chunk)
        spool.write(chunk)
    if size == 0:
        spool.close()
        raise _error(400, "media_empty", "The uploaded file is empty.")
    spool.seek(0)
    return spool, hasher.hexdigest(), size, header


def _authorize_owner(asset: MediaAsset, requester: User) -> None:
    # Phase 2: only the owner may read or mutate. Coach/trainee visibility rules are
    # deferred; cross-account access is indistinguishable from "not found".
    if asset.owner_user_id != requester.id:
        raise _not_found()


def upload_media(
    db: Session,
    storage: StorageProvider,
    *,
    owner: User,
    uploader: User,
    source: BinaryIO,
    filename: str | None,
    declared_content_type: str | None,
    purpose: MediaPurpose = MediaPurpose.GENERIC,
    visibility: MediaVisibility = MediaVisibility.PRIVATE,
) -> MediaAsset:
    if purpose not in UPLOADABLE_PURPOSES:
        raise _error(400, "media_invalid_purpose", "Unsupported media purpose.")
    if visibility is not MediaVisibility.PRIVATE:
        # The generic endpoint never widens visibility; broader sharing is a later,
        # relationship-mediated concern.
        raise _error(400, "media_invalid_visibility", "Only private media is supported.")
    is_video = purpose in VIDEO_PURPOSES
    allowed_types = ALLOWED_VIDEO_CONTENT_TYPES if is_video else ALLOWED_CONTENT_TYPES
    max_bytes = settings.media_max_video_bytes if is_video else settings.media_max_bytes
    content_type = (declared_content_type or "").split(";")[0].strip().lower()
    if content_type not in allowed_types:
        raise _error(
            415,
            "media_unsupported_type",
            "Only MP4 or WEBM videos are accepted."
            if is_video
            else "Only JPEG, PNG, WEBP, or GIF images are accepted.",
        )

    spool, checksum, size, header = _spool_and_hash(source, max_bytes)
    try:
        if not _signature_matches(content_type, header):
            raise _error(
                415,
                "media_signature_mismatch",
                "File contents do not match the declared image type.",
            )
        extension = _EXTENSIONS[content_type]
        storage_key = f"{purpose.value}/{owner.id}/{uuid.uuid4().hex}.{extension}"
        try:
            storage.write_stream(storage_key, spool)
        except StorageError as exc:
            raise _error(502, "media_storage_error", "Could not store the file.") from exc
    finally:
        spool.close()

    asset = MediaAsset(
        owner_user_id=owner.id,
        uploader_user_id=uploader.id,
        purpose=purpose,
        visibility=visibility,
        lifecycle_status=MediaLifecycleStatus.ACTIVE,
        storage_provider=storage.kind,
        storage_key=storage_key,
        content_type=content_type,
        byte_size=size,
        checksum_sha256=checksum,
        original_filename=_sanitize_filename(filename),
    )
    db.add(asset)
    try:
        db.commit()
    except Exception:
        # Never leave an active row without bytes, or bytes without a row.
        db.rollback()
        storage.delete(storage_key)
        raise
    db.refresh(asset)
    return asset


def get_media_asset(
    db: Session,
    media_id: uuid.UUID,
    requester: User,
    *,
    include_inactive: bool = False,
) -> MediaAsset:
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise _not_found()
    _authorize_owner(asset, requester)
    if not include_inactive and asset.lifecycle_status in {
        MediaLifecycleStatus.SOFT_DELETED,
        MediaLifecycleStatus.PURGED,
    }:
        raise _not_found()
    return asset


def open_media_content(
    db: Session,
    storage: StorageProvider,
    media_id: uuid.UUID,
    requester: User,
) -> tuple[MediaAsset, Iterator[bytes]]:
    asset = get_media_asset(db, media_id, requester)
    try:
        stream = storage.open_stream(asset.storage_key)
    except StorageError as exc:
        raise _not_found() from exc
    return asset, stream


def soft_delete_media(
    db: Session, media_id: uuid.UUID, requester: User
) -> MediaAsset:
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise _not_found()
    _authorize_owner(asset, requester)
    if asset.lifecycle_status is MediaLifecycleStatus.PURGED:
        raise _not_found()
    if asset.lifecycle_status is MediaLifecycleStatus.SOFT_DELETED:
        # Idempotent: deleting an already-deleted asset succeeds without change.
        return asset
    assert_transition(asset.lifecycle_status, MediaLifecycleStatus.SOFT_DELETED)
    asset.lifecycle_status = MediaLifecycleStatus.SOFT_DELETED
    asset.deleted_at = datetime.now(UTC)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def replace_media(
    db: Session,
    storage: StorageProvider,
    media_id: uuid.UUID,
    requester: User,
    *,
    source: BinaryIO,
    filename: str | None,
    declared_content_type: str | None,
) -> MediaAsset:
    """Upload a replacement and mark the prior asset REPLACED.

    Not exposed on the API in this phase; provided for Phase 3 (e.g. avatar swaps).
    The new bytes are written before the old row is transitioned, so a failure never
    leaves the owner without a usable asset. Object storage and the database cannot
    share one transaction; the small window is documented and bounded.
    """
    current = get_media_asset(db, media_id, requester)
    if current.lifecycle_status is not MediaLifecycleStatus.ACTIVE:
        raise _error(409, "media_not_active", "Only an active asset can be replaced.")
    replacement = upload_media(
        db,
        storage,
        owner=requester,
        uploader=requester,
        source=source,
        filename=filename,
        declared_content_type=declared_content_type,
        purpose=current.purpose,
        visibility=current.visibility,
    )
    assert_transition(current.lifecycle_status, MediaLifecycleStatus.REPLACED)
    current.lifecycle_status = MediaLifecycleStatus.REPLACED
    current.replaced_at = datetime.now(UTC)
    current.replaced_by_media_id = replacement.id
    db.add(current)
    db.commit()
    db.refresh(replacement)
    return replacement


def purge_media(
    db: Session, storage: StorageProvider, media_id: uuid.UUID
) -> MediaAsset:
    """Physically remove bytes for a soft-deleted asset. Service-level only.

    No API surface exposes purge in this phase; it exists so later retention jobs can
    reclaim storage. Guarded so only SOFT_DELETED assets can be purged.
    """
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise _not_found()
    assert_transition(asset.lifecycle_status, MediaLifecycleStatus.PURGED)
    storage.delete(asset.storage_key)
    asset.lifecycle_status = MediaLifecycleStatus.PURGED
    asset.purged_at = datetime.now(UTC)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset
