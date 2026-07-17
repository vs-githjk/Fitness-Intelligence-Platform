"""Deterministic ``workout-load-v1`` engine.

Pure functions over plain input dataclasses. No database access, no FastAPI, and
no dependency on ``app.domain`` (Daily Intelligence). Every output value is
derived by an exact documented formula; missing inputs stay missing (``None``)
and are never silently coerced to zero.

Formulas (see ``docs/scoring/workout-load-v1.md``):

* planned_session_load  = planned_duration_minutes * target_session_rpe
* completed_session_load = actual_duration_minutes * session_rpe
* set_volume_kg          = actual_repetitions * actual_load_canonical_kg
* session_volume_kg      = sum of valid completed repetitions_and_load sets
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

CALCULATION_VERSION = "workout-load-v1"

# String values that mirror the persisted enums (kept as plain strings so the
# engine stays free of ORM imports and is trivially testable in isolation).
SOURCE_PRESCRIBED = "prescribed"
SOURCE_TRAINEE_ADDED = "trainee_added"

SET_STATUS_PLANNED = "planned"
SET_STATUS_COMPLETED = "completed"
SET_STATUS_SKIPPED = "skipped"

SET_TYPE_WORKING = "working"

MODE_REPETITIONS_AND_LOAD = "repetitions_and_load"
MODE_REPETITIONS_ONLY = "repetitions_only"
MODE_DURATION = "duration"
MODE_DISTANCE_AND_DURATION = "distance_and_duration"
MODE_BODYWEIGHT_OR_ASSISTED = "bodyweight_or_assisted_repetitions"

# Terminal session statuses eligible for a completed load / volume calculation.
TERMINAL_STATUSES = ("completed", "ended_incomplete", "safety_ended")

_VOLUME_QUANTUM = Decimal("0.001")


def _q(value: Decimal) -> Decimal:
    return value.quantize(_VOLUME_QUANTUM, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class SetInput:
    """A single logged set, decoupled from the ORM row."""

    source: str
    set_type: str
    tracking_mode: str
    status: str
    actual_repetitions: int | None = None
    actual_load_canonical_kg: Decimal | None = None
    actual_duration_seconds: int | None = None
    actual_distance_meters: Decimal | None = None

    @property
    def is_completed(self) -> bool:
        return self.status == SET_STATUS_COMPLETED

    @property
    def is_skipped(self) -> bool:
        return self.status == SET_STATUS_SKIPPED

    @property
    def is_working(self) -> bool:
        return self.set_type == SET_TYPE_WORKING

    @property
    def is_prescribed(self) -> bool:
        return self.source == SOURCE_PRESCRIBED

    @property
    def is_trainee_added(self) -> bool:
        return self.source == SOURCE_TRAINEE_ADDED


@dataclass(frozen=True)
class SessionExerciseInput:
    """One exercise within a session, with its logged sets."""

    status: str
    tracking_mode: str
    sets: tuple[SetInput, ...] = ()


@dataclass(frozen=True)
class SessionLoadInput:
    """All inputs required to compute a single session's load summary."""

    status: str
    planned_duration_minutes: int | None
    target_session_rpe: float | None
    actual_duration_minutes: int | None
    session_rpe: Decimal | float | None
    exercises: tuple[SessionExerciseInput, ...] = ()


@dataclass(frozen=True)
class LoadEngineResult:
    planned_session_load: float | None
    completed_session_load: float | None
    session_volume_kg: Decimal | None
    completed_repetitions: int
    completed_working_sets: int
    completed_prescribed_sets: int
    skipped_prescribed_sets: int
    completed_added_sets: int
    completed_exercises: int
    total_duration_seconds: int | None
    total_distance_meters: Decimal | None
    calculation_version: str = CALCULATION_VERSION
    calculation_payload: dict[str, Any] = field(default_factory=dict)


def _planned_session_load(
    planned_duration_minutes: int | None, target_session_rpe: float | None
) -> tuple[float | None, dict[str, Any]]:
    detail: dict[str, Any] = {
        "planned_duration_minutes": planned_duration_minutes,
        "target_session_rpe": target_session_rpe,
    }
    if planned_duration_minutes is None or target_session_rpe is None:
        detail["available"] = False
        detail["reason"] = "missing_planned_duration_or_target_rpe"
        return None, detail
    value = round(planned_duration_minutes * target_session_rpe, 2)
    detail["available"] = True
    detail["value"] = value
    return value, detail


def _completed_session_load(
    status: str,
    actual_duration_minutes: int | None,
    session_rpe: Decimal | float | None,
) -> tuple[float | None, dict[str, Any]]:
    detail: dict[str, Any] = {
        "status": status,
        "actual_duration_minutes": actual_duration_minutes,
        "session_rpe": float(session_rpe) if session_rpe is not None else None,
    }
    if status not in TERMINAL_STATUSES:
        detail["available"] = False
        detail["reason"] = "session_not_terminal"
        return None, detail
    if actual_duration_minutes is None or session_rpe is None:
        detail["available"] = False
        detail["reason"] = "missing_actual_duration_or_session_rpe"
        return None, detail
    value = round(actual_duration_minutes * float(session_rpe), 2)
    detail["available"] = True
    detail["value"] = value
    return value, detail


def compute_session_load(session: SessionLoadInput) -> LoadEngineResult:
    """Return the deterministic load summary for a single session."""

    planned_load, planned_detail = _planned_session_load(
        session.planned_duration_minutes, session.target_session_rpe
    )
    completed_load, completed_detail = _completed_session_load(
        session.status, session.actual_duration_minutes, session.session_rpe
    )

    volume = Decimal("0")
    volume_set_count = 0
    completed_repetitions = 0
    completed_working_sets = 0
    completed_prescribed_sets = 0
    skipped_prescribed_sets = 0
    completed_added_sets = 0
    total_duration_seconds = 0
    duration_set_count = 0
    total_distance = Decimal("0")
    distance_set_count = 0

    for exercise in session.exercises:
        for set_input in exercise.sets:
            if set_input.is_prescribed and set_input.is_skipped:
                skipped_prescribed_sets += 1
            if not set_input.is_completed:
                continue
            if set_input.is_prescribed:
                completed_prescribed_sets += 1
            if set_input.is_trainee_added:
                completed_added_sets += 1
            if set_input.is_working:
                completed_working_sets += 1
            if set_input.actual_repetitions is not None:
                completed_repetitions += set_input.actual_repetitions
            # Resistance volume: completed repetitions_and_load sets only.
            if (
                set_input.tracking_mode == MODE_REPETITIONS_AND_LOAD
                and set_input.actual_repetitions is not None
                and set_input.actual_load_canonical_kg is not None
            ):
                volume += Decimal(set_input.actual_repetitions) * set_input.actual_load_canonical_kg
                volume_set_count += 1
            if set_input.actual_duration_seconds is not None:
                total_duration_seconds += set_input.actual_duration_seconds
                duration_set_count += 1
            if set_input.actual_distance_meters is not None:
                total_distance += set_input.actual_distance_meters
                distance_set_count += 1

    completed_exercises = sum(
        1 for exercise in session.exercises if exercise.status == "completed"
    )

    session_volume = _q(volume) if volume_set_count else None
    duration_total = total_duration_seconds if duration_set_count else None
    distance_total = _q(total_distance) if distance_set_count else None

    payload: dict[str, Any] = {
        "calculation_version": CALCULATION_VERSION,
        "planned_session_load": planned_detail,
        "completed_session_load": completed_detail,
        "resistance_volume": {
            "session_volume_kg": str(session_volume) if session_volume is not None else None,
            "contributing_sets": volume_set_count,
            "rule": "completed repetitions_and_load sets only; "
            "excludes assistance, bodyweight, timed, distance, skipped and planned sets",
        },
        "factual_metrics": {
            "completed_repetitions": completed_repetitions,
            "completed_working_sets": completed_working_sets,
            "completed_prescribed_sets": completed_prescribed_sets,
            "skipped_prescribed_sets": skipped_prescribed_sets,
            "completed_added_sets": completed_added_sets,
            "completed_exercises": completed_exercises,
            "total_duration_seconds": duration_total,
            "total_distance_meters": str(distance_total) if distance_total is not None else None,
        },
    }

    return LoadEngineResult(
        planned_session_load=planned_load,
        completed_session_load=completed_load,
        session_volume_kg=session_volume,
        completed_repetitions=completed_repetitions,
        completed_working_sets=completed_working_sets,
        completed_prescribed_sets=completed_prescribed_sets,
        skipped_prescribed_sets=skipped_prescribed_sets,
        completed_added_sets=completed_added_sets,
        completed_exercises=completed_exercises,
        total_duration_seconds=duration_total,
        total_distance_meters=distance_total,
        calculation_payload=payload,
    )
