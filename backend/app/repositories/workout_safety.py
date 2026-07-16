import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import (
    CoachTraineeAssignment,
    DailyScoreSnapshot,
    ScheduledWorkout,
    User,
    WorkoutSafetyReport,
    WorkoutSession,
    WorkoutSessionExercise,
    WorkoutSetLog,
)


def _report_options():
    return (
        joinedload(WorkoutSafetyReport.workout_session)
        .joinedload(WorkoutSession.scheduled_workout)
        .joinedload(ScheduledWorkout.workout_template_version),
        joinedload(WorkoutSafetyReport.workout_session_exercise).joinedload(
            WorkoutSessionExercise.exercise_version
        ),
        selectinload(WorkoutSafetyReport.reviews),
    )


class WorkoutSafetyRepository:
    """Ownership-scoped safety, review, and readiness queries."""

    def __init__(self, db: Session):
        self.db = db

    def latest_readiness_snapshot(
        self, trainee_id: uuid.UUID, on_or_before: date
    ) -> DailyScoreSnapshot | None:
        return self.db.scalar(
            select(DailyScoreSnapshot)
            .where(
                DailyScoreSnapshot.trainee_id == trainee_id,
                DailyScoreSnapshot.local_date <= on_or_before,
            )
            .order_by(
                DailyScoreSnapshot.local_date.desc(),
                DailyScoreSnapshot.calculated_at.desc(),
            )
            .limit(1)
        )

    def session_exercise(
        self, session_id: uuid.UUID, exercise_id: uuid.UUID
    ) -> WorkoutSessionExercise | None:
        return self.db.scalar(
            select(WorkoutSessionExercise).where(
                WorkoutSessionExercise.id == exercise_id,
                WorkoutSessionExercise.workout_session_id == session_id,
            )
        )

    def session_set(
        self, session_id: uuid.UUID, set_id: uuid.UUID
    ) -> WorkoutSetLog | None:
        return self.db.scalar(
            select(WorkoutSetLog)
            .join(WorkoutSessionExercise)
            .where(
                WorkoutSetLog.id == set_id,
                WorkoutSessionExercise.workout_session_id == session_id,
            )
        )

    def trainee_reports(
        self, trainee_id: uuid.UUID, session_id: uuid.UUID
    ) -> list[WorkoutSafetyReport]:
        return list(
            self.db.scalars(
                select(WorkoutSafetyReport)
                .options(*_report_options())
                .where(
                    WorkoutSafetyReport.trainee_id == trainee_id,
                    WorkoutSafetyReport.workout_session_id == session_id,
                )
                .order_by(WorkoutSafetyReport.created_at.desc())
            ).all()
        )

    def coach_reports(
        self, coach_id: uuid.UUID, status: str | None = None
    ) -> list[tuple[WorkoutSafetyReport, User]]:
        statement = (
            select(WorkoutSafetyReport, User)
            .options(*_report_options())
            .join(User, User.id == WorkoutSafetyReport.trainee_id)
            .join(
                CoachTraineeAssignment,
                CoachTraineeAssignment.trainee_id == WorkoutSafetyReport.trainee_id,
            )
            .where(
                CoachTraineeAssignment.coach_id == coach_id,
                CoachTraineeAssignment.status == "active",
            )
            .order_by(WorkoutSafetyReport.created_at.desc())
        )
        if status is not None:
            statement = statement.where(WorkoutSafetyReport.status == status)
        return list(self.db.execute(statement).unique().all())

    def coach_report(
        self, coach_id: uuid.UUID, report_id: uuid.UUID, *, lock: bool = False
    ) -> tuple[WorkoutSafetyReport, User] | None:
        if lock:
            allowed = self.db.scalar(
                select(WorkoutSafetyReport.id)
                .join(
                    CoachTraineeAssignment,
                    CoachTraineeAssignment.trainee_id == WorkoutSafetyReport.trainee_id,
                )
                .where(
                    WorkoutSafetyReport.id == report_id,
                    CoachTraineeAssignment.coach_id == coach_id,
                    CoachTraineeAssignment.status == "active",
                )
                .with_for_update()
            )
            if allowed is None:
                return None
        return self.db.execute(
            select(WorkoutSafetyReport, User)
            .options(*_report_options())
            .join(User, User.id == WorkoutSafetyReport.trainee_id)
            .join(
                CoachTraineeAssignment,
                CoachTraineeAssignment.trainee_id == WorkoutSafetyReport.trainee_id,
            )
            .where(
                WorkoutSafetyReport.id == report_id,
                CoachTraineeAssignment.coach_id == coach_id,
                CoachTraineeAssignment.status == "active",
            )
        ).unique().one_or_none()
