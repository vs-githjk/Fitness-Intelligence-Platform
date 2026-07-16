import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.units import canonical_kilograms, quantize_measurement
from app.models import (
    ExerciseTrackingMode,
    ScheduledWorkoutStatus,
    User,
    WorkoutSession,
    WorkoutSessionEvent,
    WorkoutSessionEventType,
    WorkoutSessionExercise,
    WorkoutSessionExerciseStatus,
    WorkoutSessionStatus,
    WorkoutSetLog,
    WorkoutSetLogSource,
    WorkoutSetLogStatus,
    WorkoutTemplateSection,
)
from app.repositories.workout_sessions import WorkoutSessionRepository
from app.schemas import (
    WorkoutExerciseSkipRequest,
    WorkoutSessionCompleteRequest,
    WorkoutSessionEndIncompleteRequest,
    WorkoutSetActualData,
    WorkoutSetAddRequest,
    WorkoutSetUpdateRequest,
)

ACTUAL_FIELDS = (
    "actual_repetitions",
    "actual_load_original_value",
    "actual_load_original_unit",
    "actual_assistance_original_value",
    "actual_assistance_original_unit",
    "actual_duration_seconds",
    "actual_distance_value",
    "actual_distance_unit",
    "actual_rpe",
    "actual_rir",
)


def _error(status: int, code: str, message: str, **extra: object) -> HTTPException:
    return HTTPException(
        status_code=status,
        detail={"code": code, "message": message, **extra},
    )


def _event(
    db: Session,
    session: WorkoutSession,
    actor: User,
    event_type: WorkoutSessionEventType,
    payload: dict | None = None,
) -> None:
    session.events.append(
        WorkoutSessionEvent(
            event_type=event_type, actor_user_id=actor.id, payload=payload or {}
        )
    )


def _exercise_snapshot(source) -> dict:
    version = source.exercise_version
    return {
        "exercise_version_id": str(version.id),
        "name": version.name,
        "tracking_mode": version.tracking_mode.value,
        "safety_cues": version.safety_cues,
        "section": source.section.value,
        "display_order": source.display_order,
        "trainee_instructions": source.trainee_instructions,
    }


def _set_values(source, tracking_mode: ExerciseTrackingMode) -> dict:
    return {
        "source_prescription_id": source.id,
        "source": WorkoutSetLogSource.PRESCRIBED,
        "set_number": source.set_number,
        "set_type": source.set_type,
        "tracking_mode": tracking_mode,
        "planned_repetitions_min": source.repetitions_min,
        "planned_repetitions_max": source.repetitions_max,
        "planned_duration_seconds": source.target_duration_seconds,
        "planned_distance_value": source.target_distance_value,
        "planned_distance_unit": source.target_distance_unit,
        "planned_load_original_value": source.target_load_original_value,
        "planned_load_original_unit": source.target_load_original_unit,
        "planned_assistance_original_value": source.target_assistance_original_value,
        "planned_assistance_original_unit": source.target_assistance_original_unit,
        "planned_rpe": source.target_rpe,
        "planned_rir": source.target_rir,
        "planned_rest_seconds": source.rest_seconds,
        "planned_tempo": source.tempo,
        "planned_instructions": source.instructions,
        "status": WorkoutSetLogStatus.PLANNED,
        "revision": 1,
    }


def _set_out(item: WorkoutSetLog) -> dict:
    return {
        key: getattr(item, key)
        for key in (
            "id",
            "source_prescription_id",
            "source",
            "set_number",
            "set_type",
            "tracking_mode",
            "planned_repetitions_min",
            "planned_repetitions_max",
            "planned_duration_seconds",
            "planned_distance_value",
            "planned_distance_unit",
            "planned_load_original_value",
            "planned_load_original_unit",
            "planned_assistance_original_value",
            "planned_assistance_original_unit",
            "planned_rpe",
            "planned_rir",
            "planned_rest_seconds",
            "planned_tempo",
            "planned_instructions",
            *ACTUAL_FIELDS,
            "actual_load_canonical_kg",
            "actual_assistance_canonical_kg",
            "status",
            "completed_at",
            "revision",
        )
    }


def session_out(session: WorkoutSession) -> dict:
    scheduled = session.scheduled_workout
    template = scheduled.workout_template_version
    program = scheduled.assignment.program_version
    return {
        "id": session.id,
        "scheduled_workout_id": session.scheduled_workout_id,
        "status": session.status,
        "scheduled_workout_status": scheduled.status,
        "workout_name": template.name,
        "program_name": program.name,
        "program_version_number": program.version_number,
        "scheduled_date": scheduled.scheduled_date,
        "estimated_duration_minutes": scheduled.planned_duration_minutes,
        "target_session_rpe": scheduled.target_session_rpe,
        "trainee_instructions": scheduled.trainee_instructions,
        "started_at": session.started_at,
        "last_activity_at": session.last_activity_at,
        "completed_at": session.completed_at,
        "ended_at": session.ended_at,
        "actual_duration_minutes": session.actual_duration_minutes,
        "session_rpe": session.session_rpe,
        "trainee_note": session.trainee_note,
        "revision": session.revision,
        "exercises": [
            {
                "id": exercise.id,
                "source_workout_template_exercise_id": (
                    exercise.source_workout_template_exercise_id
                ),
                "exercise_version_id": exercise.exercise_version_id,
                "exercise_name": exercise.prescription_snapshot["name"],
                "tracking_mode": exercise.prescription_snapshot["tracking_mode"],
                "safety_cues": exercise.prescription_snapshot.get("safety_cues", []),
                "section": exercise.section,
                "display_order": exercise.display_order,
                "trainee_instructions": exercise.trainee_instructions,
                "prescription_snapshot": exercise.prescription_snapshot,
                "status": exercise.status,
                "skip_reason": exercise.skip_reason,
                "skip_note": exercise.skip_note,
                "sets": [_set_out(item) for item in exercise.sets],
            }
            for exercise in sorted(
                session.exercises,
                key=lambda item: (
                    {
                        WorkoutTemplateSection.WARM_UP: 0,
                        WorkoutTemplateSection.MAIN: 1,
                        WorkoutTemplateSection.COOL_DOWN: 2,
                    }[item.section],
                    item.display_order,
                    str(item.id),
                ),
            )
        ],
        "events": [
            {"id": event.id, "event_type": event.event_type, "created_at": event.created_at}
            for event in session.events
        ],
    }


def _owned_session(
    db: Session, trainee: User, session_id: uuid.UUID, *, lock: bool = True
) -> WorkoutSession:
    session = WorkoutSessionRepository(db).owned_session(trainee.id, session_id, lock=lock)
    if session is None:
        raise _error(404, "workout_session_not_found", "Workout session not found")
    return session


def _active(session: WorkoutSession) -> None:
    if session.status != WorkoutSessionStatus.IN_PROGRESS:
        raise _error(409, "workout_session_immutable", "Ended workout sessions cannot be changed")


def _revision(session: WorkoutSession, expected: int) -> None:
    if session.revision != expected:
        raise _error(
            409,
            "session_revision_conflict",
            "The workout was updated elsewhere. Reload the latest session before saving.",
            current_revision=session.revision,
        )


def _touch(session: WorkoutSession, now: datetime) -> None:
    session.revision += 1
    session.last_activity_at = now


def start_workout(db: Session, trainee: User, scheduled_workout_id: uuid.UUID) -> dict:
    repository = WorkoutSessionRepository(db)
    scheduled = repository.owned_scheduled_workout(trainee.id, scheduled_workout_id, lock=True)
    if scheduled is None:
        raise _error(404, "scheduled_workout_not_found", "Scheduled workout not found")
    if scheduled.workout_session is not None:
        session = repository.owned_session(trainee.id, scheduled.workout_session.id, lock=True)
        assert session is not None
        if session.status != WorkoutSessionStatus.IN_PROGRESS:
            raise _error(409, "workout_already_ended", "This workout has already ended")
        now = datetime.now(UTC)
        _event(db, session, trainee, WorkoutSessionEventType.SESSION_RESUMED)
        _touch(session, now)
        db.commit()
        return session_out(repository.owned_session(trainee.id, session.id) or session)
    if scheduled.status != ScheduledWorkoutStatus.SCHEDULED:
        raise _error(
            409,
            "scheduled_workout_not_startable",
            "Only an available scheduled workout can be started",
        )
    now = datetime.now(UTC)
    session = WorkoutSession(
        scheduled_workout_id=scheduled.id,
        trainee_id=trainee.id,
        status=WorkoutSessionStatus.IN_PROGRESS,
        started_at=now,
        last_activity_at=now,
        revision=1,
        scheduled_workout=scheduled,
    )
    db.add(session)
    db.flush()
    for source_exercise in scheduled.workout_template_version.exercises:
        snapshot = WorkoutSessionExercise(
            workout_session_id=session.id,
            source_workout_template_exercise_id=source_exercise.id,
            exercise_version_id=source_exercise.exercise_version_id,
            section=source_exercise.section,
            display_order=source_exercise.display_order,
            trainee_instructions=source_exercise.trainee_instructions,
            prescription_snapshot=_exercise_snapshot(source_exercise),
            status=WorkoutSessionExerciseStatus.NOT_STARTED,
        )
        db.add(snapshot)
        db.flush()
        for source_set in source_exercise.sets:
            db.add(
                WorkoutSetLog(
                    workout_session_exercise_id=snapshot.id,
                    **_set_values(source_set, source_exercise.exercise_version.tracking_mode),
                )
            )
    scheduled.status = ScheduledWorkoutStatus.IN_PROGRESS
    _event(db, session, trainee, WorkoutSessionEventType.SESSION_STARTED)
    db.commit()
    return session_out(repository.owned_session(trainee.id, session.id) or session)


def get_session(db: Session, trainee: User, session_id: uuid.UUID) -> dict:
    return session_out(_owned_session(db, trainee, session_id, lock=False))


def get_active_session(db: Session, trainee: User) -> dict | None:
    session = WorkoutSessionRepository(db).active_session(trainee.id)
    return session_out(session) if session else None


def _present(body: WorkoutSetActualData, field: str) -> bool:
    return getattr(body, field) is not None


def _validate_actuals(
    body: WorkoutSetActualData, mode: ExerciseTrackingMode, status: WorkoutSetLogStatus
) -> None:
    if status == WorkoutSetLogStatus.SKIPPED:
        if any(_present(body, field) for field in ACTUAL_FIELDS):
            raise _error(422, "skipped_set_has_actuals", "Skipped sets cannot contain actual values")
        return
    if status == WorkoutSetLogStatus.PLANNED:
        if any(_present(body, field) for field in ACTUAL_FIELDS):
            raise _error(422, "planned_set_has_actuals", "Planned sets cannot contain actual values")
        return
    reps = _present(body, "actual_repetitions")
    load = _present(body, "actual_load_original_value")
    assistance = _present(body, "actual_assistance_original_value")
    duration = _present(body, "actual_duration_seconds")
    distance = _present(body, "actual_distance_value")
    rir = _present(body, "actual_rir")
    valid = False
    if mode == ExerciseTrackingMode.REPETITIONS_AND_LOAD:
        valid = reps and load and not any((assistance, duration, distance, rir))
    elif mode == ExerciseTrackingMode.REPETITIONS_ONLY:
        valid = reps and not any((load, assistance, duration, distance))
    elif mode == ExerciseTrackingMode.DURATION:
        valid = duration and not any((reps, load, assistance, distance, rir))
    elif mode == ExerciseTrackingMode.DISTANCE_AND_DURATION:
        valid = distance and duration and not any((reps, load, assistance, rir))
    elif mode == ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS:
        valid = reps and not any((load, duration, distance))
    if not valid:
        raise _error(
            422,
            "tracking_mode_mismatch",
            f"Actual set fields do not match {mode.value}",
        )


def _apply_actuals(item: WorkoutSetLog, body: WorkoutSetActualData) -> None:
    for field in ACTUAL_FIELDS:
        value = getattr(body, field)
        if isinstance(value, Decimal):
            value = quantize_measurement(value)
        setattr(item, field, value)
    item.actual_load_canonical_kg = (
        canonical_kilograms(item.actual_load_original_value, item.actual_load_original_unit)
        if item.actual_load_original_value is not None
        and item.actual_load_original_unit is not None
        else None
    )
    item.actual_assistance_canonical_kg = (
        canonical_kilograms(
            item.actual_assistance_original_value, item.actual_assistance_original_unit
        )
        if item.actual_assistance_original_value is not None
        and item.actual_assistance_original_unit is not None
        else None
    )


def _refresh_exercise_status(exercise: WorkoutSessionExercise) -> None:
    if exercise.status == WorkoutSessionExerciseStatus.SKIPPED:
        return
    statuses = {item.status for item in exercise.sets}
    if statuses and WorkoutSetLogStatus.PLANNED not in statuses:
        exercise.status = WorkoutSessionExerciseStatus.COMPLETED
    elif statuses != {WorkoutSetLogStatus.PLANNED}:
        exercise.status = WorkoutSessionExerciseStatus.IN_PROGRESS
    else:
        exercise.status = WorkoutSessionExerciseStatus.NOT_STARTED


def update_set(
    db: Session,
    trainee: User,
    session_id: uuid.UUID,
    set_id: uuid.UUID,
    body: WorkoutSetUpdateRequest,
) -> dict:
    session = _owned_session(db, trainee, session_id)
    _active(session)
    _revision(session, body.expected_session_revision)
    item = WorkoutSessionRepository(db).owned_set(trainee.id, session.id, set_id)
    if item is None:
        raise _error(404, "workout_set_not_found", "Workout set not found")
    if item.session_exercise.status == WorkoutSessionExerciseStatus.SKIPPED:
        raise _error(409, "exercise_already_skipped", "Skipped exercises cannot be changed")
    status = WorkoutSetLogStatus(body.status)
    _validate_actuals(body, item.tracking_mode, status)
    old_status = item.status
    _apply_actuals(item, body)
    item.status = status
    item.completed_at = datetime.now(UTC) if status == WorkoutSetLogStatus.COMPLETED else None
    item.revision += 1
    _refresh_exercise_status(item.session_exercise)
    now = datetime.now(UTC)
    _touch(session, now)
    event_type = (
        WorkoutSessionEventType.SET_SKIPPED
        if status == WorkoutSetLogStatus.SKIPPED
        else WorkoutSessionEventType.SET_COMPLETED
        if status == WorkoutSetLogStatus.COMPLETED and old_status != status
        else WorkoutSessionEventType.SET_UPDATED
    )
    _event(db, session, trainee, event_type, {"set_id": str(item.id)})
    db.commit()
    return session_out(_owned_session(db, trainee, session.id, lock=False))


def add_set(
    db: Session, trainee: User, session_id: uuid.UUID, body: WorkoutSetAddRequest
) -> dict:
    session = _owned_session(db, trainee, session_id)
    _active(session)
    exercise = WorkoutSessionRepository(db).owned_exercise(
        trainee.id, session.id, body.workout_session_exercise_id
    )
    if exercise is None:
        raise _error(404, "workout_exercise_not_found", "Workout exercise not found")
    existing = next(
        (item for item in exercise.sets if item.idempotency_key == body.idempotency_key), None
    )
    if existing is not None:
        return session_out(session)
    _revision(session, body.expected_session_revision)
    if exercise.status == WorkoutSessionExerciseStatus.SKIPPED:
        raise _error(409, "exercise_already_skipped", "Skipped exercises cannot receive new sets")
    status = WorkoutSetLogStatus(body.status)
    mode = exercise.exercise_version.tracking_mode
    _validate_actuals(body, mode, status)
    item = WorkoutSetLog(
        workout_session_exercise_id=exercise.id,
        source=WorkoutSetLogSource.TRAINEE_ADDED,
        idempotency_key=body.idempotency_key,
        set_number=max((value.set_number for value in exercise.sets), default=0) + 1,
        set_type=body.set_type,
        tracking_mode=mode,
        status=status,
        completed_at=datetime.now(UTC) if status == WorkoutSetLogStatus.COMPLETED else None,
        revision=1,
    )
    _apply_actuals(item, body)
    exercise.sets.append(item)
    db.flush()
    _refresh_exercise_status(exercise)
    _touch(session, datetime.now(UTC))
    _event(db, session, trainee, WorkoutSessionEventType.SET_ADDED, {"set_id": str(item.id)})
    db.commit()
    return session_out(_owned_session(db, trainee, session.id, lock=False))


def skip_exercise(
    db: Session,
    trainee: User,
    session_id: uuid.UUID,
    exercise_id: uuid.UUID,
    body: WorkoutExerciseSkipRequest,
) -> dict:
    session = _owned_session(db, trainee, session_id)
    _active(session)
    _revision(session, body.expected_session_revision)
    exercise = WorkoutSessionRepository(db).owned_exercise(
        trainee.id, session.id, exercise_id
    )
    if exercise is None:
        raise _error(404, "workout_exercise_not_found", "Workout exercise not found")
    exercise.status = WorkoutSessionExerciseStatus.SKIPPED
    exercise.skip_reason = body.reason
    exercise.skip_note = body.note
    now = datetime.now(UTC)
    for item in exercise.sets:
        if item.status == WorkoutSetLogStatus.PLANNED:
            item.status = WorkoutSetLogStatus.SKIPPED
            item.revision += 1
    _touch(session, now)
    _event(
        db,
        session,
        trainee,
        WorkoutSessionEventType.EXERCISE_SKIPPED,
        {"exercise_id": str(exercise.id), "reason": body.reason},
    )
    db.commit()
    return session_out(_owned_session(db, trainee, session.id, lock=False))


def complete_session(
    db: Session, trainee: User, session_id: uuid.UUID, body: WorkoutSessionCompleteRequest
) -> dict:
    session = _owned_session(db, trainee, session_id)
    _active(session)
    _revision(session, body.expected_session_revision)
    if any(
        exercise.status
        not in (WorkoutSessionExerciseStatus.COMPLETED, WorkoutSessionExerciseStatus.SKIPPED)
        for exercise in session.exercises
    ):
        raise _error(
            422,
            "workout_not_resolved",
            "Complete or explicitly skip every exercise before completing the workout",
        )
    now = datetime.now(UTC)
    session.status = WorkoutSessionStatus.COMPLETED
    session.completed_at = now
    session.actual_duration_minutes = body.actual_duration_minutes
    session.session_rpe = body.session_rpe
    session.trainee_note = body.trainee_note.strip() or None if body.trainee_note else None
    session.scheduled_workout.status = ScheduledWorkoutStatus.COMPLETED
    _touch(session, now)
    _event(db, session, trainee, WorkoutSessionEventType.SESSION_COMPLETED)
    db.commit()
    return session_out(_owned_session(db, trainee, session.id, lock=False))


def end_session_incomplete(
    db: Session,
    trainee: User,
    session_id: uuid.UUID,
    body: WorkoutSessionEndIncompleteRequest,
) -> dict:
    session = _owned_session(db, trainee, session_id)
    _active(session)
    _revision(session, body.expected_session_revision)
    now = datetime.now(UTC)
    session.status = WorkoutSessionStatus.ENDED_INCOMPLETE
    session.ended_at = now
    session.trainee_note = body.note.strip() or None if body.note else None
    session.scheduled_workout.status = ScheduledWorkoutStatus.PARTIAL
    _touch(session, now)
    _event(
        db,
        session,
        trainee,
        WorkoutSessionEventType.SESSION_ENDED_INCOMPLETE,
        {"reason": body.reason},
    )
    db.commit()
    return session_out(_owned_session(db, trainee, session.id, lock=False))
