import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseVersion,
    ExerciseVersionStatus,
    WorkoutTemplate,
    WorkoutTemplateExercise,
    WorkoutTemplateVersion,
)


def _template_graph_options():
    return selectinload(WorkoutTemplate.versions).selectinload(
        WorkoutTemplateVersion.exercises
    ).options(
        selectinload(WorkoutTemplateExercise.sets),
        selectinload(WorkoutTemplateExercise.exercise_version),
    )


class WorkoutTemplateRepository:
    """Centralize coach ownership and exercise-selection visibility predicates."""

    def __init__(self, db: Session):
        self.db = db

    def list_owned(self, coach_id: uuid.UUID) -> list[WorkoutTemplate]:
        return list(
            self.db.scalars(
                select(WorkoutTemplate)
                .options(_template_graph_options())
                .where(WorkoutTemplate.owner_coach_id == coach_id)
                .order_by(WorkoutTemplate.updated_at.desc(), WorkoutTemplate.id)
            ).all()
        )

    def get_owned(
        self, coach_id: uuid.UUID, template_id: uuid.UUID
    ) -> WorkoutTemplate | None:
        return self.db.scalar(
            select(WorkoutTemplate)
            .options(_template_graph_options())
            .where(
                WorkoutTemplate.id == template_id,
                WorkoutTemplate.owner_coach_id == coach_id,
            )
        )

    def get_owned_for_update(
        self, coach_id: uuid.UUID, template_id: uuid.UUID
    ) -> WorkoutTemplate | None:
        """Serialize root mutations so draft revision checks are race-safe."""
        return self.db.scalar(
            select(WorkoutTemplate)
            .options(_template_graph_options())
            .where(
                WorkoutTemplate.id == template_id,
                WorkoutTemplate.owner_coach_id == coach_id,
            )
            .with_for_update()
        )

    def next_version_number(self, template_id: uuid.UUID) -> int:
        highest = self.db.scalar(
            select(func.max(WorkoutTemplateVersion.version_number)).where(
                WorkoutTemplateVersion.workout_template_id == template_id
            )
        )
        return int(highest or 0) + 1

    def get_selectable_exercise_version(
        self, coach_id: uuid.UUID, exercise_version_id: uuid.UUID
    ) -> ExerciseVersion | None:
        return self.db.scalar(
            select(ExerciseVersion)
            .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
            .where(
                ExerciseVersion.id == exercise_version_id,
                ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED,
                Exercise.status == ExerciseStatus.ACTIVE,
                or_(
                    Exercise.scope == ExerciseScope.SYSTEM,
                    Exercise.owner_coach_id == coach_id,
                ),
            )
        )
