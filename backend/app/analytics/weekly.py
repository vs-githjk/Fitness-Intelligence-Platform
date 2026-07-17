"""Weekly load aggregation (Part E) and planned-vs-completed comparison (Part F).

Pure functions. Weeks are Monday–Sunday buckets keyed by the workout's captured
local date. Missing values are never treated as zero: they are summed only when
available and separately counted as unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

# Neutral comparison states (Part F). No value judgement is implied.
ABOVE_PLANNED = "above_planned"
NEAR_PLANNED = "near_planned"
BELOW_PLANNED = "below_planned"
UNAVAILABLE = "unavailable"

# "Near" band: within 10% of planned.
NEAR_BAND = 0.10


def week_start(local_date: date) -> date:
    """Monday of the ISO week containing ``local_date``."""

    return local_date - timedelta(days=local_date.weekday())


@dataclass(frozen=True)
class WeeklySessionInput:
    local_date: date
    classification: str
    planned_session_load: float | None
    completed_session_load: float | None
    resistance_volume_kg: Decimal | None


def aggregate_weeks(
    sessions: list[WeeklySessionInput], timezone: str
) -> list[dict[str, Any]]:
    """Aggregate sessions into Monday–Sunday weekly buckets, sorted ascending."""

    buckets: dict[date, dict[str, Any]] = {}
    for item in sessions:
        start = week_start(item.local_date)
        bucket = buckets.setdefault(
            start,
            {
                "week_start_local_date": start,
                "timezone": timezone,
                "planned_session_load_total": 0.0,
                "completed_session_load_total": 0.0,
                "resistance_volume_kg": Decimal("0"),
                "_has_volume": False,
                "completed_count": 0,
                "partial_count": 0,
                "skipped_count": 0,
                "missed_count": 0,
                "unavailable_planned_load_count": 0,
                "unavailable_completed_load_count": 0,
            },
        )
        if item.planned_session_load is not None:
            bucket["planned_session_load_total"] += item.planned_session_load
        else:
            bucket["unavailable_planned_load_count"] += 1
        if item.completed_session_load is not None:
            bucket["completed_session_load_total"] += item.completed_session_load
        else:
            bucket["unavailable_completed_load_count"] += 1
        if item.resistance_volume_kg is not None:
            bucket["resistance_volume_kg"] += item.resistance_volume_kg
            bucket["_has_volume"] = True
        if item.classification == "completed":
            bucket["completed_count"] += 1
        elif item.classification == "partial":
            bucket["partial_count"] += 1
        elif item.classification in ("ordinary_skipped", "safety_skipped"):
            bucket["skipped_count"] += 1
        elif item.classification == "missed":
            bucket["missed_count"] += 1

    weeks: list[dict[str, Any]] = []
    for start in sorted(buckets):
        bucket = buckets[start]
        planned = round(bucket["planned_session_load_total"], 2)
        completed = round(bucket["completed_session_load_total"], 2)
        difference = round(completed - planned, 2)
        ratio = round(completed / planned, 3) if planned > 0 else None
        volume = bucket.pop("_has_volume")
        weeks.append(
            {
                "week_start_local_date": bucket["week_start_local_date"],
                "timezone": bucket["timezone"],
                "planned_session_load_total": planned,
                "completed_session_load_total": completed,
                "difference": difference,
                "ratio": ratio,
                "completed_count": bucket["completed_count"],
                "partial_count": bucket["partial_count"],
                "skipped_count": bucket["skipped_count"],
                "missed_count": bucket["missed_count"],
                "resistance_volume_kg": (
                    str(bucket["resistance_volume_kg"]) if volume else None
                ),
                "unavailable_planned_load_count": bucket["unavailable_planned_load_count"],
                "unavailable_completed_load_count": bucket["unavailable_completed_load_count"],
            }
        )
    return weeks


def compare_planned_completed(
    planned: float | None, completed: float | None
) -> dict[str, Any]:
    """Neutral planned-vs-completed comparison (Part F)."""

    if planned is None or completed is None:
        return {
            "planned": planned,
            "completed": completed,
            "absolute_difference": None,
            "ratio": None,
            "state": UNAVAILABLE,
        }
    difference = round(completed - planned, 2)
    ratio = round(completed / planned, 3) if planned > 0 else None
    if planned <= 0:
        state = UNAVAILABLE
    elif abs(completed - planned) <= NEAR_BAND * planned:
        state = NEAR_PLANNED
    elif completed > planned:
        state = ABOVE_PLANNED
    else:
        state = BELOW_PLANNED
    return {
        "planned": round(planned, 2),
        "completed": round(completed, 2),
        "absolute_difference": abs(difference),
        "ratio": ratio,
        "state": state,
    }
