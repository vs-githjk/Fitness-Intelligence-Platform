import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    CoachTraineeAssignment,
    ProgramSession,
    ProgramWeek,
    ScheduledWorkout,
    TrainingAssignment,
    TrainingProgram,
    TrainingProgramStatus,
    TrainingProgramVersion,
    TrainingProgramVersionStatus,
    WorkoutTemplateVersion,
)


def _assignment_options():
    return (
        selectinload(TrainingAssignment.program_version)
        .selectinload(TrainingProgramVersion.weeks)
        .selectinload(ProgramWeek.sessions)
        .selectinload(ProgramSession.workout_template_version)
        .selectinload(WorkoutTemplateVersion.exercises)
    )


class TrainingAssignmentRepository:
    """Centralize roster authorization, ownership, and assignment locking."""

    def __init__(self, db: Session):
        self.db = db

    def lock_active_roster_relationship(
        self, coach_id: uuid.UUID, trainee_id: uuid.UUID
    ) -> CoachTraineeAssignment | None:
        return self.db.scalar(
            select(CoachTraineeAssignment)
            .where(
                CoachTraineeAssignment.coach_id == coach_id,
                CoachTraineeAssignment.trainee_id == trainee_id,
                CoachTraineeAssignment.status == "active",
            )
            .with_for_update()
        )

    def selectable_program_version(
        self, coach_id: uuid.UUID, version_id: uuid.UUID
    ) -> TrainingProgramVersion | None:
        return self.db.scalar(
            select(TrainingProgramVersion)
            .options(
                selectinload(TrainingProgramVersion.weeks)
                .selectinload(ProgramWeek.sessions)
                .selectinload(ProgramSession.workout_template_version)
                .selectinload(WorkoutTemplateVersion.exercises)
            )
            .join(
                TrainingProgram,
                TrainingProgram.id == TrainingProgramVersion.training_program_id,
            )
            .where(
                TrainingProgramVersion.id == version_id,
                TrainingProgramVersion.version_status
                == TrainingProgramVersionStatus.PUBLISHED,
                TrainingProgram.owner_coach_id == coach_id,
                TrainingProgram.status == TrainingProgramStatus.ACTIVE,
            )
        )

    def assignments_for_trainee(
        self, trainee_id: uuid.UUID, coach_id: uuid.UUID | None = None
    ) -> list[TrainingAssignment]:
        statement = (
            select(TrainingAssignment)
            .options(
                _assignment_options(),
                selectinload(TrainingAssignment.scheduled_workouts)
                .selectinload(ScheduledWorkout.workout_template_version)
                .selectinload(WorkoutTemplateVersion.exercises),
                selectinload(TrainingAssignment.scheduled_workouts).selectinload(
                    ScheduledWorkout.readiness_context
                ),
                selectinload(TrainingAssignment.history),
            )
            .where(TrainingAssignment.trainee_id == trainee_id)
            .order_by(TrainingAssignment.effective_start_date.desc(), TrainingAssignment.created_at.desc())
        )
        if coach_id is not None:
            statement = statement.where(TrainingAssignment.coach_id == coach_id)
        return list(self.db.scalars(statement).all())

    def lock_timeline(self, trainee_id: uuid.UUID) -> None:
        """Serialize local-date activation and replacement for one trainee timeline."""
        list(
            self.db.scalars(
                select(TrainingAssignment.id)
                .where(TrainingAssignment.trainee_id == trainee_id)
                .order_by(TrainingAssignment.id)
                .with_for_update()
            ).all()
        )

    def owned_assignment(
        self, coach_id: uuid.UUID, assignment_id: uuid.UUID, *, lock: bool = False
    ) -> TrainingAssignment | None:
        statement = (
            select(TrainingAssignment)
            .options(
                _assignment_options(),
                selectinload(TrainingAssignment.scheduled_workouts)
                .selectinload(ScheduledWorkout.workout_template_version)
                .selectinload(WorkoutTemplateVersion.exercises),
                selectinload(TrainingAssignment.scheduled_workouts).selectinload(
                    ScheduledWorkout.readiness_context
                ),
                selectinload(TrainingAssignment.history),
            )
            .where(
                TrainingAssignment.id == assignment_id,
                TrainingAssignment.coach_id == coach_id,
            )
        )
        if lock:
            statement = statement.with_for_update()
        return self.db.scalar(statement)
