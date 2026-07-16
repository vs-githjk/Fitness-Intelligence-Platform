import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.daily_services import local_today
from app.models import (
    AssignmentHistory,
    AssignmentHistoryEvent,
    ProgramWeekday,
    ScheduledWorkout,
    ScheduledWorkoutStatus,
    TrainingAssignment,
    TrainingAssignmentStatus,
    TrainingProgramVersion,
    User,
)
from app.repositories.training_assignments import TrainingAssignmentRepository
from app.schemas import TrainingAssignmentCreateRequest, TrainingAssignmentPreviewRequest

DAY_OFFSET = {
    ProgramWeekday.MONDAY: 0,
    ProgramWeekday.TUESDAY: 1,
    ProgramWeekday.WEDNESDAY: 2,
    ProgramWeekday.THURSDAY: 3,
    ProgramWeekday.FRIDAY: 4,
    ProgramWeekday.SATURDAY: 5,
    ProgramWeekday.SUNDAY: 6,
}


def _error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"code": code, "message": message})


def _program_week_one_monday(start_date: date) -> date:
    return start_date + timedelta(days=(-start_date.weekday()) % 7)


def _template_summary(version) -> dict:
    return {
        "id": version.id,
        "workout_template_id": version.workout_template_id,
        "version_number": version.version_number,
        "name": version.name,
        "goal_tags": version.goal_tags,
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "target_session_rpe": version.target_session_rpe,
        "exercise_count": len(version.exercises),
    }


def _schedule_rows(program: TrainingProgramVersion, start_date: date) -> list[dict]:
    monday = _program_week_one_monday(start_date)
    rows = []
    for week in sorted(program.weeks, key=lambda item: item.week_number):
        week_monday = monday + timedelta(weeks=week.week_number - 1)
        for session in sorted(
            week.sessions,
            key=lambda item: (DAY_OFFSET[item.weekday], item.display_order),
        ):
            template = session.workout_template_version
            rows.append(
                {
                    "program_session_id": session.id,
                    "workout_template_version_id": template.id,
                    "scheduled_date": week_monday + timedelta(days=DAY_OFFSET[session.weekday]),
                    "program_week_number": week.week_number,
                    "program_week_label": week.label,
                    "is_deload": week.is_deload,
                    "weekday": session.weekday,
                    "display_order": session.display_order,
                    "required": session.required,
                    "planned_duration_minutes": session.planned_duration_override_minutes
                    or template.estimated_duration_minutes,
                    "target_session_rpe": (
                        session.target_session_rpe_override
                        if session.target_session_rpe_override is not None
                        else template.target_session_rpe
                    ),
                    "coach_notes": session.coach_notes,
                    "trainee_instructions": session.trainee_instructions
                    or template.trainee_instructions,
                    "status": ScheduledWorkoutStatus.SCHEDULED,
                    "workout_template_version": _template_summary(template),
                }
            )
    return rows


def _assignment_snapshot(assignment: TrainingAssignment) -> dict:
    program = assignment.program_version
    return {
        "assignment_id": str(assignment.id),
        "coach_id": str(assignment.coach_id),
        "trainee_id": str(assignment.trainee_id),
        "training_program_version_id": str(assignment.training_program_version_id),
        "program_name": program.name,
        "program_version_number": program.version_number,
        "status": assignment.status.value,
        "effective_start_date": assignment.effective_start_date.isoformat(),
        "effective_end_date": (
            assignment.effective_end_date.isoformat() if assignment.effective_end_date else None
        ),
        "timezone": assignment.timezone,
    }


def _record_history(
    db: Session,
    assignment: TrainingAssignment,
    event: AssignmentHistoryEvent,
    effective_date: date,
) -> None:
    db.add(
        AssignmentHistory(
            training_assignment_id=assignment.id,
            coach_id=assignment.coach_id,
            trainee_id=assignment.trainee_id,
            event_type=event,
            effective_date=effective_date,
            snapshot=_assignment_snapshot(assignment),
        )
    )


def _assignment_out(assignment: TrainingAssignment) -> dict:
    program = assignment.program_version
    return {
        "id": assignment.id,
        "coach_id": assignment.coach_id,
        "trainee_id": assignment.trainee_id,
        "training_program_version_id": assignment.training_program_version_id,
        "status": assignment.status,
        "is_primary": assignment.is_primary,
        "effective_start_date": assignment.effective_start_date,
        "effective_end_date": assignment.effective_end_date,
        "timezone": assignment.timezone,
        "program_name": program.name,
        "program_version_number": program.version_number,
        "duration_weeks": program.duration_weeks,
        "goal_tags": program.goal_tags,
        "created_at": assignment.created_at,
        "activated_at": assignment.activated_at,
        "superseded_at": assignment.superseded_at,
        "cancelled_at": assignment.cancelled_at,
    }


def _workout_out(workout: ScheduledWorkout) -> dict:
    return {
        "id": workout.id,
        "workout_session_id": (
            workout.workout_session.id if workout.workout_session is not None else None
        ),
        "training_assignment_id": workout.training_assignment_id,
        "workout_template_version_id": workout.workout_template_version_id,
        "scheduled_date": workout.scheduled_date,
        "program_week_number": workout.program_week_number,
        "program_week_label": workout.program_week_label,
        "is_deload": workout.is_deload,
        "weekday": workout.weekday,
        "display_order": workout.display_order,
        "required": workout.required,
        "planned_duration_minutes": workout.planned_duration_minutes,
        "target_session_rpe": workout.target_session_rpe,
        "trainee_instructions": workout.trainee_instructions,
        "status": workout.status,
        "workout_template_version": _template_summary(workout.workout_template_version),
    }


def _supersede_assignment(
    db: Session, assignment: TrainingAssignment, effective_date: date, now: datetime
) -> None:
    if assignment.status in (
        TrainingAssignmentStatus.SUPERSEDED,
        TrainingAssignmentStatus.CANCELLED,
    ):
        return
    assignment.status = TrainingAssignmentStatus.SUPERSEDED
    assignment.effective_end_date = max(
        assignment.effective_start_date, effective_date - timedelta(days=1)
    )
    assignment.superseded_at = now
    for workout in assignment.scheduled_workouts:
        if (
            workout.status == ScheduledWorkoutStatus.SCHEDULED
            and workout.scheduled_date >= effective_date
        ):
            workout.status = ScheduledWorkoutStatus.SUPERSEDED
            workout.superseded_at = now
    _record_history(db, assignment, AssignmentHistoryEvent.SUPERSEDED, effective_date)


def _reconcile(
    db: Session, assignments: list[TrainingAssignment], today: date, now: datetime
) -> None:
    upcoming = next(
        (
            item
            for item in assignments
            if item.status == TrainingAssignmentStatus.SCHEDULED
            and item.effective_start_date <= today
        ),
        None,
    )
    if upcoming is None:
        return
    active = next(
        (item for item in assignments if item.status == TrainingAssignmentStatus.ACTIVE), None
    )
    if active is not None:
        _supersede_assignment(db, active, upcoming.effective_start_date, now)
        # Release the partial unique active-primary slot before activating its replacement.
        db.flush()
    upcoming.status = TrainingAssignmentStatus.ACTIVE
    upcoming.activated_at = now
    _record_history(db, upcoming, AssignmentHistoryEvent.ACTIVATED, upcoming.effective_start_date)
    db.commit()


def _workspace(
    db: Session, trainee_id: uuid.UUID, coach_id: uuid.UUID | None = None
) -> dict:
    today, timezone = local_today(db, trainee_id)
    repository = TrainingAssignmentRepository(db)
    repository.lock_timeline(trainee_id)
    assignments = repository.assignments_for_trainee(trainee_id, coach_id)
    _reconcile(db, assignments, today, datetime.now(UTC))
    if assignments:
        assignments = repository.assignments_for_trainee(trainee_id, coach_id)
    current = next(
        (item for item in assignments if item.status == TrainingAssignmentStatus.ACTIVE), None
    )
    upcoming = next(
        (item for item in assignments if item.status == TrainingAssignmentStatus.SCHEDULED), None
    )
    visible_assignment_ids = {
        item.id for item in (current, upcoming) if item is not None
    }
    # Execution states must remain in the current Program payload so route refreshes can resume
    # the existing session and terminal summaries remain reachable from the calendar.
    workouts = [
        workout
        for assignment in assignments
        if assignment.id in visible_assignment_ids
        for workout in assignment.scheduled_workouts
    ]
    events = sorted(
        [event for assignment in assignments for event in assignment.history],
        key=lambda item: item.created_at,
        reverse=True,
    )
    return {
        "timezone": timezone,
        "local_today": today,
        "current_assignment": _assignment_out(current) if current else None,
        "upcoming_assignment": _assignment_out(upcoming) if upcoming else None,
        "assignment_history": [_assignment_out(item) for item in assignments],
        "history_events": [
            {
                "id": item.id,
                "training_assignment_id": item.training_assignment_id,
                "event_type": item.event_type,
                "effective_date": item.effective_date,
                "snapshot": item.snapshot,
                "created_at": item.created_at,
            }
            for item in events
        ],
        "scheduled_workouts": [
            _workout_out(item)
            for item in sorted(workouts, key=lambda value: (value.scheduled_date, value.display_order))
        ],
    }


def preview_training_assignment(
    db: Session,
    coach: User,
    trainee_id: uuid.UUID,
    body: TrainingAssignmentPreviewRequest,
) -> dict:
    repository = TrainingAssignmentRepository(db)
    if repository.lock_active_roster_relationship(coach.id, trainee_id) is None:
        raise _error(403, "not_assigned", "This trainee is not assigned to the current coach")
    program = repository.selectable_program_version(
        coach.id, body.training_program_version_id
    )
    if program is None:
        raise _error(404, "training_program_version_not_found", "Published Program version not found")
    today, timezone = local_today(db, trainee_id)
    if body.effective_start_date < today:
        raise _error(422, "assignment_start_in_past", "Start date cannot be before the trainee's local date")
    assignments = repository.assignments_for_trainee(trainee_id, coach.id)
    rows = _schedule_rows(program, body.effective_start_date)
    if not rows:
        raise _error(422, "program_has_no_workouts", "A Program must contain workouts before assignment")
    return {
        "timezone": timezone,
        "effective_start_date": body.effective_start_date,
        "effective_end_date": max(item["scheduled_date"] for item in rows),
        "program_name": program.name,
        "program_version_number": program.version_number,
        "replaces_current": any(item.status == TrainingAssignmentStatus.ACTIVE for item in assignments),
        "replaces_upcoming": any(
            item.status == TrainingAssignmentStatus.SCHEDULED for item in assignments
        ),
        "workouts": [
            {
                key: value
                for key, value in row.items()
                if key not in {"program_session_id", "coach_notes"}
            }
            for row in rows
        ],
    }


def create_training_assignment(
    db: Session,
    coach: User,
    trainee_id: uuid.UUID,
    body: TrainingAssignmentCreateRequest,
    *,
    allow_past: bool = False,
) -> dict:
    repository = TrainingAssignmentRepository(db)
    if repository.lock_active_roster_relationship(coach.id, trainee_id) is None:
        raise _error(403, "not_assigned", "This trainee is not assigned to the current coach")
    program = repository.selectable_program_version(
        coach.id, body.training_program_version_id
    )
    if program is None:
        raise _error(404, "training_program_version_not_found", "Published Program version not found")
    today, timezone = local_today(db, trainee_id)
    if not allow_past and body.effective_start_date < today:
        raise _error(422, "assignment_start_in_past", "Start date cannot be before the trainee's local date")
    assignments = repository.assignments_for_trainee(trainee_id, coach.id)
    if not _schedule_rows(program, body.effective_start_date):
        raise _error(422, "program_has_no_workouts", "A Program must contain workouts before assignment")
    now = datetime.now(UTC)
    current = next(
        (item for item in assignments if item.status == TrainingAssignmentStatus.ACTIVE), None
    )
    upcoming = next(
        (item for item in assignments if item.status == TrainingAssignmentStatus.SCHEDULED), None
    )
    if upcoming is not None:
        _supersede_assignment(db, upcoming, body.effective_start_date, now)
        db.flush()
    status = (
        TrainingAssignmentStatus.ACTIVE
        if body.effective_start_date <= today
        else TrainingAssignmentStatus.SCHEDULED
    )
    if current is not None:
        if status == TrainingAssignmentStatus.ACTIVE:
            _supersede_assignment(db, current, body.effective_start_date, now)
            db.flush()
        else:
            current.effective_end_date = max(
                current.effective_start_date,
                body.effective_start_date - timedelta(days=1),
            )
            for workout in current.scheduled_workouts:
                if (
                    workout.status == ScheduledWorkoutStatus.SCHEDULED
                    and workout.scheduled_date >= body.effective_start_date
                ):
                    workout.status = ScheduledWorkoutStatus.SUPERSEDED
                    workout.superseded_at = now
    assignment = TrainingAssignment(
        coach_id=coach.id,
        trainee_id=trainee_id,
        training_program_version_id=program.id,
        status=status,
        is_primary=True,
        effective_start_date=body.effective_start_date,
        timezone=timezone,
        activated_at=now if status == TrainingAssignmentStatus.ACTIVE else None,
        program_version=program,
    )
    db.add(assignment)
    db.flush()
    for row in _schedule_rows(program, body.effective_start_date):
        db.add(
            ScheduledWorkout(
                training_assignment_id=assignment.id,
                trainee_id=trainee_id,
                **{key: value for key, value in row.items() if key != "workout_template_version"},
            )
        )
    _record_history(db, assignment, AssignmentHistoryEvent.ASSIGNED, body.effective_start_date)
    _record_history(
        db,
        assignment,
        AssignmentHistoryEvent.ACTIVATED
        if status == TrainingAssignmentStatus.ACTIVE
        else AssignmentHistoryEvent.SCHEDULED,
        body.effective_start_date,
    )
    db.commit()
    return _workspace(db, trainee_id, coach.id)


def cancel_future_training_assignment(
    db: Session, coach: User, assignment_id: uuid.UUID
) -> dict:
    repository = TrainingAssignmentRepository(db)
    assignment = repository.owned_assignment(coach.id, assignment_id, lock=True)
    if assignment is None:
        raise _error(404, "training_assignment_not_found", "Training assignment not found")
    if assignment.status != TrainingAssignmentStatus.SCHEDULED:
        raise _error(409, "training_assignment_not_future", "Only a future assignment can be cancelled")
    if repository.lock_active_roster_relationship(coach.id, assignment.trainee_id) is None:
        raise _error(403, "not_assigned", "This trainee is not assigned to the current coach")
    now = datetime.now(UTC)
    assignment.status = TrainingAssignmentStatus.CANCELLED
    assignment.cancelled_at = now
    for workout in assignment.scheduled_workouts:
        if workout.status == ScheduledWorkoutStatus.SCHEDULED:
            workout.status = ScheduledWorkoutStatus.CANCELLED
            workout.cancelled_at = now
    _record_history(
        db, assignment, AssignmentHistoryEvent.CANCELLED, assignment.effective_start_date
    )
    db.commit()
    return _workspace(db, assignment.trainee_id, coach.id)


def coach_assignment_workspace(db: Session, coach: User, trainee_id: uuid.UUID) -> dict:
    if TrainingAssignmentRepository(db).lock_active_roster_relationship(
        coach.id, trainee_id
    ) is None:
        raise _error(403, "not_assigned", "This trainee is not assigned to the current coach")
    return _workspace(db, trainee_id, coach.id)


def trainee_assignment_workspace(db: Session, trainee: User) -> dict:
    return _workspace(db, trainee.id)
