import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ProgramSession,
    ProgramWeek,
    TrainingProgram,
    TrainingProgramVersion,
    WorkoutTemplate,
    WorkoutTemplateStatus,
    WorkoutTemplateVersion,
    WorkoutTemplateVersionStatus,
)


def _program_graph_options():
    return selectinload(TrainingProgram.versions).selectinload(
        TrainingProgramVersion.weeks
    ).selectinload(ProgramWeek.sessions).options(
        selectinload(ProgramSession.workout_template_version).selectinload(
            WorkoutTemplateVersion.exercises
        )
    )


class TrainingProgramRepository:
    """Centralize program ownership and template-version eligibility predicates."""

    def __init__(self, db: Session):
        self.db = db

    def list_owned(self, coach_id: uuid.UUID) -> list[TrainingProgram]:
        return list(
            self.db.scalars(
                select(TrainingProgram)
                .options(_program_graph_options())
                .where(TrainingProgram.owner_coach_id == coach_id)
                .order_by(TrainingProgram.updated_at.desc(), TrainingProgram.id)
            ).all()
        )

    def get_owned(self, coach_id: uuid.UUID, program_id: uuid.UUID) -> TrainingProgram | None:
        return self.db.scalar(
            select(TrainingProgram)
            .options(_program_graph_options())
            .where(
                TrainingProgram.id == program_id,
                TrainingProgram.owner_coach_id == coach_id,
            )
        )

    def get_owned_for_update(
        self, coach_id: uuid.UUID, program_id: uuid.UUID
    ) -> TrainingProgram | None:
        return self.db.scalar(
            select(TrainingProgram)
            .options(_program_graph_options())
            .where(
                TrainingProgram.id == program_id,
                TrainingProgram.owner_coach_id == coach_id,
            )
            .with_for_update()
        )

    def next_version_number(self, program_id: uuid.UUID) -> int:
        highest = self.db.scalar(
            select(func.max(TrainingProgramVersion.version_number)).where(
                TrainingProgramVersion.training_program_id == program_id
            )
        )
        return int(highest or 0) + 1

    def get_selectable_template_version(
        self, coach_id: uuid.UUID, version_id: uuid.UUID
    ) -> WorkoutTemplateVersion | None:
        return self.db.scalar(
            select(WorkoutTemplateVersion)
            .options(selectinload(WorkoutTemplateVersion.exercises))
            .join(
                WorkoutTemplate,
                WorkoutTemplate.id == WorkoutTemplateVersion.workout_template_id,
            )
            .where(
                WorkoutTemplateVersion.id == version_id,
                WorkoutTemplateVersion.version_status
                == WorkoutTemplateVersionStatus.PUBLISHED,
                WorkoutTemplate.owner_coach_id == coach_id,
                WorkoutTemplate.status == WorkoutTemplateStatus.ACTIVE,
            )
        )
