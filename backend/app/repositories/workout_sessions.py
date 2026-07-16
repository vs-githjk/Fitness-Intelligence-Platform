import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    ScheduledWorkout,
    TrainingAssignment,
    WorkoutSession,
    WorkoutSessionExercise,
    WorkoutSessionStatus,
    WorkoutSetLog,
    WorkoutTemplateExercise,
    WorkoutTemplateVersion,
)


def _scheduled_options():
    return (
        joinedload(ScheduledWorkout.workout_template_version)
        .selectinload(WorkoutTemplateVersion.exercises)
        .selectinload(WorkoutTemplateExercise.sets),
        joinedload(ScheduledWorkout.workout_template_version)
        .selectinload(WorkoutTemplateVersion.exercises)
        .joinedload(WorkoutTemplateExercise.exercise_version),
        joinedload(ScheduledWorkout.assignment).joinedload(TrainingAssignment.program_version),
    )


def _session_options():
    return (
        joinedload(WorkoutSession.scheduled_workout)
        .joinedload(ScheduledWorkout.workout_template_version),
        joinedload(WorkoutSession.scheduled_workout)
        .joinedload(ScheduledWorkout.assignment)
        .joinedload(TrainingAssignment.program_version),
        selectinload(WorkoutSession.exercises).joinedload(
            WorkoutSessionExercise.exercise_version
        ),
        selectinload(WorkoutSession.exercises).selectinload(WorkoutSessionExercise.sets),
        selectinload(WorkoutSession.events),
    )


class WorkoutSessionRepository:
    """Ownership-scoped execution graph queries and row locks."""

    def __init__(self, db: Session):
        self.db = db

    def owned_scheduled_workout(
        self, trainee_id: uuid.UUID, scheduled_workout_id: uuid.UUID, *, lock: bool = False
    ) -> ScheduledWorkout | None:
        statement = (
            select(ScheduledWorkout)
            .options(*_scheduled_options())
            .where(
                ScheduledWorkout.id == scheduled_workout_id,
                ScheduledWorkout.trainee_id == trainee_id,
            )
        )
        if lock:
            locked = self.db.scalar(
                select(ScheduledWorkout.id)
                .where(
                    ScheduledWorkout.id == scheduled_workout_id,
                    ScheduledWorkout.trainee_id == trainee_id,
                )
                .with_for_update()
            )
            if locked is None:
                return None
        return self.db.scalar(statement)

    def owned_session(
        self, trainee_id: uuid.UUID, session_id: uuid.UUID, *, lock: bool = False
    ) -> WorkoutSession | None:
        statement = (
            select(WorkoutSession)
            .options(*_session_options())
            .where(WorkoutSession.id == session_id, WorkoutSession.trainee_id == trainee_id)
        )
        if lock:
            locked = self.db.scalar(
                select(WorkoutSession.id)
                .where(
                    WorkoutSession.id == session_id,
                    WorkoutSession.trainee_id == trainee_id,
                )
                .with_for_update()
            )
            if locked is None:
                return None
        return self.db.scalar(statement)

    def active_session(self, trainee_id: uuid.UUID) -> WorkoutSession | None:
        return self.db.scalar(
            select(WorkoutSession)
            .options(*_session_options())
            .where(
                WorkoutSession.trainee_id == trainee_id,
                WorkoutSession.status == WorkoutSessionStatus.IN_PROGRESS,
            )
            .order_by(WorkoutSession.last_activity_at.desc())
            .limit(1)
        )

    def owned_set(
        self, trainee_id: uuid.UUID, session_id: uuid.UUID, set_id: uuid.UUID
    ) -> WorkoutSetLog | None:
        return self.db.scalar(
            select(WorkoutSetLog)
            .join(WorkoutSessionExercise)
            .join(WorkoutSession)
            .where(
                WorkoutSetLog.id == set_id,
                WorkoutSession.id == session_id,
                WorkoutSession.trainee_id == trainee_id,
            )
        )

    def owned_exercise(
        self, trainee_id: uuid.UUID, session_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> WorkoutSessionExercise | None:
        return self.db.scalar(
            select(WorkoutSessionExercise)
            .join(WorkoutSession)
            .options(selectinload(WorkoutSessionExercise.sets))
            .where(
                WorkoutSessionExercise.id == exercise_id,
                WorkoutSession.id == session_id,
                WorkoutSession.trainee_id == trainee_id,
            )
        )
