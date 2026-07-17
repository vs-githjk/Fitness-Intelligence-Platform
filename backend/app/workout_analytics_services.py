"""ORM-facing Workout Intelligence analytics services (Phase 7B).

Bridges persisted execution data to the isolated ``app.analytics`` engines.
All history access is bounded by an explicit date range and eager-loaded to
avoid per-session / per-exercise / per-set query loops.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.analytics import (
    CALCULATION_VERSION,
    LoadEngineResult,
    SessionExerciseInput,
    SessionLoadInput,
    SetInput,
    compute_session_load,
)
from app.analytics.adherence import (
    ExerciseAdherenceInput,
    PrescribedSetInput,
    WorkoutClassificationInput,
    aggregate_completion,
    classify_workout,
    exercise_adherence,
    prescribed_set_adherence,
)
from app.analytics.weekly import (
    WeeklySessionInput,
    aggregate_weeks,
    compare_planned_completed,
)
from app.domain.units import canonical_meters
from app.models import (
    ExerciseVersion,
    ScheduledWorkout,
    TrainingAssignment,
    WorkoutLoadSummary,
    WorkoutSession,
    WorkoutSessionExercise,
    WorkoutSetLog,
)

TERMINAL_SESSION_STATUSES = ("completed", "ended_incomplete", "safety_ended")
_ALLOWED_RANGES = {7, 14, 30}


# --- timezone / range helpers -------------------------------------------


def resolve_timezone(name: str | None) -> ZoneInfo:
    try:
        return ZoneInfo(name or "UTC")
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def _local_date(tz: ZoneInfo, now: datetime | None = None) -> date:
    current = now or datetime.now(UTC)
    if current.tzinfo is None:
        current = current.replace(tzinfo=UTC)
    return current.astimezone(tz).date()


def report_timezone(db: Session, trainee_id: uuid.UUID) -> ZoneInfo:
    """The trainee's captured analytics timezone (most-recent assignment, else UTC)."""

    name = db.scalar(
        select(TrainingAssignment.timezone)
        .where(TrainingAssignment.trainee_id == trainee_id)
        .order_by(TrainingAssignment.created_at.desc())
        .limit(1)
    )
    return resolve_timezone(name)


def bounded_range(
    tz: ZoneInfo, days: int, end_date: date | None = None
) -> tuple[date, date]:
    if days not in _ALLOWED_RANGES:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_range", "message": "Range must be 7, 14, or 30 days"},
        )
    today = _local_date(tz)
    end = min(end_date or today, today)
    return end - timedelta(days=days - 1), end


# --- loading -------------------------------------------------------------


def load_scheduled_workouts(
    db: Session, trainee_id: uuid.UUID, start: date, end: date
) -> list[ScheduledWorkout]:
    """Eager-load every scheduled workout in range with its session tree."""

    return list(
        db.scalars(
            select(ScheduledWorkout)
            .where(
                ScheduledWorkout.trainee_id == trainee_id,
                ScheduledWorkout.scheduled_date >= start,
                ScheduledWorkout.scheduled_date <= end,
            )
            .order_by(ScheduledWorkout.scheduled_date, ScheduledWorkout.display_order)
            .options(
                selectinload(ScheduledWorkout.assignment),
                selectinload(ScheduledWorkout.workout_template_version),
                selectinload(ScheduledWorkout.workout_session)
                .selectinload(WorkoutSession.exercises)
                .selectinload(WorkoutSessionExercise.sets),
                selectinload(ScheduledWorkout.workout_session)
                .selectinload(WorkoutSession.exercises)
                .selectinload(WorkoutSessionExercise.exercise_version),
            )
        ).all()
    )


# --- engine input construction ------------------------------------------


def _distance_meters(set_log: WorkoutSetLog) -> Decimal | None:
    if set_log.actual_distance_value is None or set_log.actual_distance_unit is None:
        return None
    return canonical_meters(set_log.actual_distance_value, set_log.actual_distance_unit)


def _set_input(set_log: WorkoutSetLog) -> SetInput:
    return SetInput(
        source=set_log.source.value,
        set_type=set_log.set_type.value,
        tracking_mode=set_log.tracking_mode.value,
        status=set_log.status.value,
        actual_repetitions=set_log.actual_repetitions,
        actual_load_canonical_kg=set_log.actual_load_canonical_kg,
        actual_duration_seconds=set_log.actual_duration_seconds,
        actual_distance_meters=_distance_meters(set_log),
    )


def _planned_inputs(scheduled: ScheduledWorkout) -> tuple[int | None, float | None]:
    """Input priority: ScheduledWorkout overrides, then template version defaults."""

    template = scheduled.workout_template_version
    duration = scheduled.planned_duration_minutes
    if duration is None and template is not None:
        duration = template.estimated_duration_minutes
    rpe = scheduled.target_session_rpe
    if rpe is None and template is not None:
        rpe = template.target_session_rpe
    return duration, rpe


def _session_load_input(scheduled: ScheduledWorkout, session: WorkoutSession) -> SessionLoadInput:
    duration, rpe = _planned_inputs(scheduled)
    exercises = tuple(
        SessionExerciseInput(
            status=ex.status.value,
            tracking_mode=ex.exercise_version.tracking_mode.value,
            sets=tuple(_set_input(s) for s in ex.sets),
        )
        for ex in session.exercises
    )
    return SessionLoadInput(
        status=session.status.value,
        planned_duration_minutes=duration,
        target_session_rpe=rpe,
        actual_duration_minutes=session.actual_duration_minutes,
        session_rpe=session.session_rpe,
        exercises=exercises,
    )


# --- load summary persistence (Part B) ----------------------------------


def _result_to_summary(session_id: uuid.UUID, result: LoadEngineResult) -> WorkoutLoadSummary:
    return WorkoutLoadSummary(
        workout_session_id=session_id,
        calculation_version=result.calculation_version,
        planned_session_load=result.planned_session_load,
        completed_session_load=result.completed_session_load,
        session_volume_kg=result.session_volume_kg,
        completed_repetitions=result.completed_repetitions,
        completed_working_sets=result.completed_working_sets,
        completed_prescribed_sets=result.completed_prescribed_sets,
        skipped_prescribed_sets=result.skipped_prescribed_sets,
        completed_added_sets=result.completed_added_sets,
        completed_exercises=result.completed_exercises,
        total_duration_seconds=result.total_duration_seconds,
        total_distance_meters=result.total_distance_meters,
        calculation_payload=result.calculation_payload,
        calculated_at=datetime.now(UTC),
    )


def get_or_create_load_summary(
    db: Session, scheduled: ScheduledWorkout, session: WorkoutSession
) -> WorkoutLoadSummary:
    """Idempotent immutable summary for a terminal session.

    Returns the existing row unchanged if one exists; otherwise computes and
    persists exactly one summary for the session/version pair.
    """

    if session.status.value not in TERMINAL_SESSION_STATUSES:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "session_not_terminal",
                "message": "Load summaries are only generated for terminal sessions",
            },
        )
    existing = db.scalar(
        select(WorkoutLoadSummary).where(
            WorkoutLoadSummary.workout_session_id == session.id,
            WorkoutLoadSummary.calculation_version == CALCULATION_VERSION,
        )
    )
    if existing is not None:
        return existing
    result = compute_session_load(_session_load_input(scheduled, session))
    summary = _result_to_summary(session.id, result)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary


def preview_load_summary(scheduled: ScheduledWorkout, session: WorkoutSession) -> dict:
    """Non-persisted preview (used for active sessions)."""

    result = compute_session_load(_session_load_input(scheduled, session))
    return _summary_dict_from_result(session.id, result, persisted=False)


def _summary_dict(summary: WorkoutLoadSummary) -> dict:
    return {
        "id": summary.id,
        "workout_session_id": summary.workout_session_id,
        "calculation_version": summary.calculation_version,
        "planned_session_load": summary.planned_session_load,
        "completed_session_load": summary.completed_session_load,
        "session_volume_kg": (
            str(summary.session_volume_kg) if summary.session_volume_kg is not None else None
        ),
        "completed_repetitions": summary.completed_repetitions,
        "completed_working_sets": summary.completed_working_sets,
        "completed_prescribed_sets": summary.completed_prescribed_sets,
        "skipped_prescribed_sets": summary.skipped_prescribed_sets,
        "completed_added_sets": summary.completed_added_sets,
        "completed_exercises": summary.completed_exercises,
        "total_duration_seconds": summary.total_duration_seconds,
        "total_distance_meters": (
            str(summary.total_distance_meters)
            if summary.total_distance_meters is not None
            else None
        ),
        "calculation_payload": summary.calculation_payload,
        "calculated_at": summary.calculated_at,
        "persisted": True,
    }


def _summary_dict_from_result(
    session_id: uuid.UUID, result: LoadEngineResult, persisted: bool
) -> dict:
    return {
        "id": None,
        "workout_session_id": session_id,
        "calculation_version": result.calculation_version,
        "planned_session_load": result.planned_session_load,
        "completed_session_load": result.completed_session_load,
        "session_volume_kg": (
            str(result.session_volume_kg) if result.session_volume_kg is not None else None
        ),
        "completed_repetitions": result.completed_repetitions,
        "completed_working_sets": result.completed_working_sets,
        "completed_prescribed_sets": result.completed_prescribed_sets,
        "skipped_prescribed_sets": result.skipped_prescribed_sets,
        "completed_added_sets": result.completed_added_sets,
        "completed_exercises": result.completed_exercises,
        "total_duration_seconds": result.total_duration_seconds,
        "total_distance_meters": (
            str(result.total_distance_meters)
            if result.total_distance_meters is not None
            else None
        ),
        "calculation_payload": result.calculation_payload,
        "calculated_at": None,
        "persisted": persisted,
    }


# --- classification / adherence (Parts C, D) ----------------------------


def _classify(scheduled: ScheduledWorkout, now: datetime | None = None) -> str:
    tz = resolve_timezone(scheduled.assignment.timezone if scheduled.assignment else None)
    session = scheduled.workout_session
    return classify_workout(
        WorkoutClassificationInput(
            scheduled_local_date=scheduled.scheduled_date,
            today_local_date=_local_date(tz, now),
            required=scheduled.required,
            scheduled_status=scheduled.status.value,
            session_status=session.status.value if session else None,
            skip_kind=scheduled.skip_kind.value if scheduled.skip_kind else None,
        )
    )


def compute_adherence(
    db: Session, trainee_id: uuid.UUID, start: date, end: date, now: datetime | None = None
) -> dict:
    workouts = load_scheduled_workouts(db, trainee_id, start, end)
    labels = [_classify(w, now) for w in workouts]
    completion = aggregate_completion(labels)

    # Set & exercise adherence over eligible executed (terminal) sessions.
    prescribed_sets: list[PrescribedSetInput] = []
    exercises: list[ExerciseAdherenceInput] = []
    for workout in workouts:
        session = workout.workout_session
        if session is None or session.status.value not in TERMINAL_SESSION_STATUSES:
            continue
        for ex in session.exercises:
            working_completed = 0
            any_completed = 0
            has_working = False
            for s in ex.sets:
                if s.source.value != "prescribed":
                    continue
                if s.set_type.value == "working":
                    has_working = True
                    prescribed_sets.append(
                        PrescribedSetInput(set_type="working", status=s.status.value)
                    )
                    if s.status.value == "completed":
                        working_completed += 1
                if s.status.value == "completed":
                    any_completed += 1
            exercises.append(
                ExerciseAdherenceInput(
                    status=ex.status.value,
                    prescribed_working_completed=working_completed,
                    prescribed_any_completed=any_completed,
                    has_prescribed_working=has_working,
                )
            )

    return {
        "start_date": start,
        "end_date": end,
        "completion": completion.as_dict(),
        "prescribed_set_adherence": prescribed_set_adherence(prescribed_sets),
        "exercise_adherence": exercise_adherence(exercises),
    }


# --- weekly load & planned-vs-completed (Parts E, F) --------------------


def compute_weekly_load(
    db: Session, trainee_id: uuid.UUID, start: date, end: date, now: datetime | None = None
) -> dict:
    tz = report_timezone(db, trainee_id)
    workouts = load_scheduled_workouts(db, trainee_id, start, end)
    weekly_inputs: list[WeeklySessionInput] = []
    total_planned = 0.0
    total_completed = 0.0
    planned_available = False
    completed_available = False
    for workout in workouts:
        session = workout.workout_session
        classification = _classify(workout, now)
        planned_load = None
        completed_load = None
        volume = None
        if session is not None:
            result = compute_session_load(_session_load_input(workout, session))
            planned_load = result.planned_session_load
            completed_load = result.completed_session_load
            volume = result.session_volume_kg
        else:
            duration, rpe = _planned_inputs(workout)
            planned_load = (
                round(duration * rpe, 2) if duration is not None and rpe is not None else None
            )
        if planned_load is not None:
            total_planned += planned_load
            planned_available = True
        if completed_load is not None:
            total_completed += completed_load
            completed_available = True
        weekly_inputs.append(
            WeeklySessionInput(
                local_date=workout.scheduled_date,
                classification=classification,
                planned_session_load=planned_load,
                completed_session_load=completed_load,
                resistance_volume_kg=volume,
            )
        )

    weeks = aggregate_weeks(weekly_inputs, tz.key)
    comparison = compare_planned_completed(
        round(total_planned, 2) if planned_available else None,
        round(total_completed, 2) if completed_available else None,
    )
    return {
        "start_date": start,
        "end_date": end,
        "timezone": tz.key,
        "weeks": weeks,
        "planned_vs_completed": comparison,
    }


# --- recorded bests (Part G) --------------------------------------------

_LOAD_MODES = ("repetitions_and_load",)
_REP_MODES = (
    "repetitions_and_load",
    "repetitions_only",
    "bodyweight_or_assisted_repetitions",
)


def _completed_set_base_query(trainee_id: uuid.UUID):
    """Completed sets in completed sessions for one trainee, with lineage joined.

    Uses the trainee/status/exercise indexes; the caller adds a window function
    so the database — not the application — selects the best row per exercise.
    """

    return (
        select(
            ExerciseVersion.exercise_id.label("root_id"),
            ExerciseVersion.name.label("exercise_name"),
            ExerciseVersion.tracking_mode.label("tracking_mode"),
            ExerciseVersion.id.label("exercise_version_id"),
            WorkoutSetLog.set_number.label("set_number"),
            WorkoutSetLog.actual_repetitions.label("actual_repetitions"),
            WorkoutSetLog.actual_load_canonical_kg.label("actual_load_canonical_kg"),
            WorkoutSetLog.actual_load_original_value.label("actual_load_original_value"),
            WorkoutSetLog.actual_load_original_unit.label("actual_load_original_unit"),
            WorkoutSession.id.label("workout_session_id"),
            ScheduledWorkout.id.label("scheduled_workout_id"),
            ScheduledWorkout.scheduled_date.label("source_date"),
        )
        .join(
            WorkoutSessionExercise,
            WorkoutSetLog.workout_session_exercise_id == WorkoutSessionExercise.id,
        )
        .join(WorkoutSession, WorkoutSessionExercise.workout_session_id == WorkoutSession.id)
        .join(ScheduledWorkout, WorkoutSession.scheduled_workout_id == ScheduledWorkout.id)
        .join(ExerciseVersion, WorkoutSessionExercise.exercise_version_id == ExerciseVersion.id)
        .where(
            WorkoutSession.trainee_id == trainee_id,
            WorkoutSession.status == "completed",
            WorkoutSetLog.status == "completed",
        )
    )


def _best_rows(db: Session, trainee_id: uuid.UUID, modes, value_col):
    """One representative row per Exercise root maximizing ``value_col``.

    The best row is chosen in SQL via ``row_number()`` (ties broken by earliest
    date, then set number), so no unbounded history is materialized in memory.
    """

    ranked = (
        _completed_set_base_query(trainee_id)
        .add_columns(
            func.row_number()
            .over(
                partition_by=ExerciseVersion.exercise_id,
                order_by=(
                    value_col.desc(),
                    ScheduledWorkout.scheduled_date.asc(),
                    WorkoutSetLog.set_number.asc(),
                ),
            )
            .label("rn")
        )
        .where(
            ExerciseVersion.tracking_mode.in_(modes),
            value_col.is_not(None),
        )
        .subquery()
    )
    return db.execute(select(ranked).where(ranked.c.rn == 1)).mappings().all()


def compute_recorded_bests(db: Session, trainee_id: uuid.UUID) -> dict:
    """Highest recorded load / repetitions / volume per stable Exercise root.

    Searches all available completed compatible workout history for the trainee
    (not a bounded window). Only completed sets in completed sessions; assistance
    is excluded; comparison is by stable Exercise root within compatible tracking
    modes; demo data is isolated by the per-trainee filter.
    """

    volume_col = WorkoutSetLog.actual_repetitions * WorkoutSetLog.actual_load_canonical_kg
    bests: dict = {}

    def _record(row):
        return bests.setdefault(
            row["root_id"],
            {
                "exercise_id": row["root_id"],
                "exercise_name": row["exercise_name"],
                "tracking_mode": row["tracking_mode"].value
                if hasattr(row["tracking_mode"], "value")
                else row["tracking_mode"],
                "highest_recorded_load": None,
                "highest_recorded_repetitions": None,
                "highest_recorded_volume": None,
            },
        )

    def _base(row):
        return {
            "source_date": row["source_date"],
            "scheduled_workout_id": row["scheduled_workout_id"],
            "workout_session_id": row["workout_session_id"],
            "set_number": row["set_number"],
            "exercise_version_id": row["exercise_version_id"],
        }

    for row in _best_rows(db, trainee_id, _LOAD_MODES, WorkoutSetLog.actual_load_canonical_kg):
        unit = row["actual_load_original_unit"]
        _record(row)["highest_recorded_load"] = {
            "value": float(row["actual_load_canonical_kg"]),
            "canonical_kg": str(row["actual_load_canonical_kg"]),
            "original_value": (
                str(row["actual_load_original_value"])
                if row["actual_load_original_value"] is not None
                else None
            ),
            "original_unit": unit.value if hasattr(unit, "value") else unit,
            **_base(row),
        }

    for row in _best_rows(db, trainee_id, _REP_MODES, WorkoutSetLog.actual_repetitions):
        _record(row)["highest_recorded_repetitions"] = {
            "value": row["actual_repetitions"],
            "repetitions": row["actual_repetitions"],
            **_base(row),
        }

    for row in _best_rows(db, trainee_id, _LOAD_MODES, volume_col):
        _record(row)["highest_recorded_volume"] = {
            "value": float(row["actual_repetitions"] * row["actual_load_canonical_kg"]),
            "repetitions": row["actual_repetitions"],
            "canonical_kg": str(row["actual_load_canonical_kg"]),
            **_base(row),
        }

    exercises = sorted(bests.values(), key=lambda item: item["exercise_name"])
    return {"scope": "all_available_history", "exercises": exercises}


# --- coach read-only session review (Part H) -----------------------------


def _session_summary(scheduled: ScheduledWorkout, session: WorkoutSession, now=None) -> dict:
    template = scheduled.workout_template_version
    program = scheduled.assignment.program_version if scheduled.assignment else None
    result = compute_session_load(_session_load_input(scheduled, session))
    return {
        "workout_session_id": session.id,
        "scheduled_workout_id": scheduled.id,
        "scheduled_date": scheduled.scheduled_date,
        "workout_name": template.name if template else None,
        "program_name": program.name if program else None,
        "program_version_number": program.version_number if program else None,
        "status": session.status.value,
        "classification": _classify(scheduled, now),
        "started_at": session.started_at,
        "completed_at": session.completed_at,
        "ended_at": session.ended_at,
        "actual_duration_minutes": session.actual_duration_minutes,
        "session_rpe": str(session.session_rpe) if session.session_rpe is not None else None,
        "planned_session_load": result.planned_session_load,
        "completed_session_load": result.completed_session_load,
        "session_volume_kg": (
            str(result.session_volume_kg) if result.session_volume_kg is not None else None
        ),
        "open_safety_report_count": sum(
            1 for report in session.safety_reports if report.status.value == "open"
        ),
        "skip_kind": None,
        "skip_reason": None,
        "skip_note": None,
        "skipped_at": None,
    }


def _skip_summary(scheduled: ScheduledWorkout, now=None) -> dict:
    """Read-only summary for an explicitly skipped workout (no session exists)."""

    template = scheduled.workout_template_version
    program = scheduled.assignment.program_version if scheduled.assignment else None
    duration, rpe = _planned_inputs(scheduled)
    planned = round(duration * rpe, 2) if duration is not None and rpe is not None else None
    return {
        "workout_session_id": None,
        "scheduled_workout_id": scheduled.id,
        "scheduled_date": scheduled.scheduled_date,
        "workout_name": template.name if template else None,
        "program_name": program.name if program else None,
        "program_version_number": program.version_number if program else None,
        "status": "skipped",
        "classification": _classify(scheduled, now),
        "started_at": None,
        "completed_at": None,
        "ended_at": None,
        "actual_duration_minutes": None,
        "session_rpe": None,
        "planned_session_load": planned,
        "completed_session_load": None,
        "session_volume_kg": None,
        "open_safety_report_count": 0,
        "skip_kind": scheduled.skip_kind.value if scheduled.skip_kind else None,
        "skip_reason": scheduled.skip_reason,
        "skip_note": scheduled.skip_note,
        "skipped_at": scheduled.skipped_at,
    }


def coach_session_list(
    db: Session,
    trainee_id: uuid.UUID,
    start: date,
    end: date,
    status: str | None = None,
    now=None,
) -> dict:
    """List a trainee's workout sessions and explicit skips for read-only review."""

    workouts = load_scheduled_workouts(db, trainee_id, start, end)
    sessions = []
    for workout in workouts:
        session = workout.workout_session
        if session is not None:
            if status is not None and session.status.value != status:
                continue
            sessions.append(_session_summary(workout, session, now))
        elif workout.status.value == "skipped":
            if status is not None and status != "skipped":
                continue
            sessions.append(_skip_summary(workout, now))
    # Most recent first, with open safety reports surfaced by later sorting in the UI.
    sessions.sort(key=lambda item: item["scheduled_date"], reverse=True)
    return {"start_date": start, "end_date": end, "sessions": sessions}


def _load_session_for_review(db: Session, session_id: uuid.UUID) -> WorkoutSession | None:
    return db.scalar(
        select(WorkoutSession)
        .where(WorkoutSession.id == session_id)
        .options(
            selectinload(WorkoutSession.scheduled_workout).selectinload(
                ScheduledWorkout.assignment
            ),
            selectinload(WorkoutSession.scheduled_workout).selectinload(
                ScheduledWorkout.workout_template_version
            ),
            selectinload(WorkoutSession.exercises).selectinload(WorkoutSessionExercise.sets),
            selectinload(WorkoutSession.exercises).selectinload(
                WorkoutSessionExercise.exercise_version
            ),
            selectinload(WorkoutSession.readiness_context),
            selectinload(WorkoutSession.safety_reports),
            selectinload(WorkoutSession.events),
        )
    )


def coach_session_detail(db: Session, coach_id: uuid.UUID, session_id: uuid.UUID) -> dict:
    """Full read-only review payload with cross-coach discovery prevention.

    Returns 404 (not 403) when the session's trainee is not actively assigned to
    the requesting coach, so foreign objects are indistinguishable from missing.
    """

    from app.models import CoachTraineeAssignment, User
    from app.workout_safety_services import coach_report_out
    from app.workout_session_services import session_out

    session = _load_session_for_review(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "workout_session_not_found", "message": "Workout session not found"},
        )
    active = db.scalar(
        select(CoachTraineeAssignment.id).where(
            CoachTraineeAssignment.coach_id == coach_id,
            CoachTraineeAssignment.trainee_id == session.trainee_id,
            CoachTraineeAssignment.status == "active",
        )
    )
    if not active:
        raise HTTPException(
            status_code=404,
            detail={"code": "workout_session_not_found", "message": "Workout session not found"},
        )

    trainee = db.get(User, session.trainee_id)
    scheduled = session.scheduled_workout
    assignment = scheduled.assignment
    program = assignment.program_version if assignment else None
    base = session_out(session)

    load_summary: dict
    comparison: dict
    if session.status.value in TERMINAL_SESSION_STATUSES:
        summary = get_or_create_load_summary(db, scheduled, session)
        load_summary = _summary_dict(summary)
        comparison = compare_planned_completed(
            summary.planned_session_load, summary.completed_session_load
        )
    else:
        result = compute_session_load(_session_load_input(scheduled, session))
        load_summary = _summary_dict_from_result(session.id, result, persisted=False)
        comparison = compare_planned_completed(
            result.planned_session_load, result.completed_session_load
        )

    base.update(
        {
            "trainee_id": session.trainee_id,
            "trainee_name": f"{trainee.first_name} {trainee.last_name}" if trainee else None,
            "training_assignment_id": assignment.id if assignment else None,
            "program_version_id": program.id if program else None,
            "program_version_number": program.version_number if program else None,
            "template_version_id": scheduled.workout_template_version_id,
            "template_version_number": (
                scheduled.workout_template_version.version_number
                if scheduled.workout_template_version
                else None
            ),
            "classification": _classify(scheduled),
            "load_summary": load_summary,
            "planned_vs_completed": comparison,
            "safety_reports": [
                coach_report_out(report, trainee) for report in session.safety_reports
            ],
            "read_only": True,
        }
    )
    return base
