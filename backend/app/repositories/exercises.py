import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseTrackingMode,
    ExerciseVersion,
)


class ExerciseRepository:
    """Keep exercise visibility predicates centralized to prevent ownership leaks."""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _version_media_loader():
        # Eager-load authored media so serialization never lazy-loads per version.
        versions = selectinload(Exercise.versions)
        return (
            versions.selectinload(ExerciseVersion.primary_image),
            versions.selectinload(ExerciseVersion.secondary_image),
            versions.selectinload(ExerciseVersion.demonstration_video),
        )

    @staticmethod
    def _visible_to(coach_id: uuid.UUID):
        return or_(
            Exercise.scope == ExerciseScope.SYSTEM,
            Exercise.owner_coach_id == coach_id,
        )

    def list_visible(
        self,
        coach_id: uuid.UUID,
        *,
        include_archived: bool = False,
        scope: ExerciseScope | None = None,
        tracking_mode: ExerciseTrackingMode | None = None,
        search: str | None = None,
    ) -> list[Exercise]:
        query = (
            select(Exercise)
            .options(selectinload(Exercise.versions), *self._version_media_loader())
            .where(self._visible_to(coach_id))
        )
        if not include_archived:
            query = query.where(Exercise.status == ExerciseStatus.ACTIVE)
        if scope is not None:
            query = query.where(Exercise.scope == scope)
        if tracking_mode is not None:
            query = query.where(
                Exercise.versions.any(ExerciseVersion.tracking_mode == tracking_mode)
            )
        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Exercise.slug.ilike(pattern),
                    Exercise.versions.any(ExerciseVersion.name.ilike(pattern)),
                )
            )
        return list(
            self.db.scalars(
                query.order_by(Exercise.scope.desc(), Exercise.slug).distinct()
            ).all()
        )

    def get_visible(self, coach_id: uuid.UUID, exercise_id: uuid.UUID) -> Exercise | None:
        return self.db.scalar(
            select(Exercise)
            .options(selectinload(Exercise.versions), *self._version_media_loader())
            .where(Exercise.id == exercise_id, self._visible_to(coach_id))
        )

    def get_system_by_slug(self, slug: str) -> Exercise | None:
        return self.db.scalar(
            select(Exercise)
            .options(selectinload(Exercise.versions))
            .where(Exercise.scope == ExerciseScope.SYSTEM, Exercise.slug == slug)
        )

    def get_private_by_slug(self, coach_id: uuid.UUID, slug: str) -> Exercise | None:
        return self.db.scalar(
            select(Exercise)
            .options(selectinload(Exercise.versions))
            .where(
                Exercise.scope == ExerciseScope.COACH_PRIVATE,
                Exercise.owner_coach_id == coach_id,
                Exercise.slug == slug,
            )
        )

    def next_version_number(self, exercise_id: uuid.UUID) -> int:
        highest = self.db.scalar(
            select(func.max(ExerciseVersion.version_number)).where(
                ExerciseVersion.exercise_id == exercise_id
            )
        )
        return int(highest or 0) + 1
