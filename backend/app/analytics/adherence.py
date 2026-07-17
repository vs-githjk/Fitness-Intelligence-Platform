"""Deterministic workout-adherence classification and aggregation.

Pure functions. Classification is derived from persisted execution data rather
than destructively mutating historical rows. See ``docs/workout-adherence.md``
for the exact rules, denominator, and the current-schema derivation notes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

# Primary workout classifications.
COMPLETED = "completed"
PARTIAL = "partial"
ORDINARY_SKIPPED = "ordinary_skipped"
SAFETY_SKIPPED = "safety_skipped"
MISSED = "missed"
PENDING = "pending"

# Exclusions (not part of the required denominator).
COACH_CANCELLED = "coach_cancelled"
SUPERSEDED_OR_RESCHEDULED = "superseded_or_rescheduled"
OPTIONAL = "optional"

# ScheduledWorkout.status values.
SCHED_CANCELLED = "cancelled"
SCHED_SUPERSEDED = "superseded"
SCHED_SKIPPED = "skipped"

# Explicit skip kinds.
SKIP_ORDINARY = "ordinary"
SKIP_SAFETY = "safety"

# WorkoutSession.status values.
SESSION_COMPLETED = "completed"
SESSION_ENDED_INCOMPLETE = "ended_incomplete"
SESSION_SAFETY_ENDED = "safety_ended"
SESSION_IN_PROGRESS = "in_progress"

# One full local calendar grace day: "missed" begins at 00:00 on the second
# local date after the scheduled date.
GRACE_DAYS = 2


@dataclass(frozen=True)
class WorkoutClassificationInput:
    """Everything needed to classify one ScheduledWorkout, timezone-resolved.

    ``skip_kind`` is the persisted explicit-skip kind ("ordinary"/"safety"),
    present only when ``scheduled_status`` is "skipped".
    """

    scheduled_local_date: date
    today_local_date: date
    required: bool
    scheduled_status: str
    session_status: str | None
    skip_kind: str | None = None


def classify_workout(item: WorkoutClassificationInput) -> str:
    """Return one classification label for a single scheduled workout.

    Skipped is derived only from an explicit persisted pre-start skip — never
    from zero completed sets, ended-incomplete status, session duration, or
    session RPE availability. A started session that ends incomplete (including
    a safety-ended session) is always partial.
    """

    if item.scheduled_status == SCHED_CANCELLED:
        return COACH_CANCELLED
    if item.scheduled_status == SCHED_SUPERSEDED:
        return SUPERSEDED_OR_RESCHEDULED
    if not item.required:
        return OPTIONAL

    if item.scheduled_status == SCHED_SKIPPED:
        return SAFETY_SKIPPED if item.skip_kind == SKIP_SAFETY else ORDINARY_SKIPPED

    window_elapsed = item.today_local_date >= item.scheduled_local_date + timedelta(days=GRACE_DAYS)

    if item.session_status is None:
        return MISSED if window_elapsed else PENDING
    if item.session_status == SESSION_COMPLETED:
        return COMPLETED
    if item.session_status in (SESSION_ENDED_INCOMPLETE, SESSION_SAFETY_ENDED):
        # A started-and-ended session is always partial, regardless of how much
        # (or how little) was logged.
        return PARTIAL
    if item.session_status == SESSION_IN_PROGRESS:
        # An active session whose allowed completion window has elapsed is a
        # safely-derived partial; otherwise it is still pending.
        return PARTIAL if window_elapsed else PENDING
    return PENDING


# Classifications that are excluded from the eligible required denominator.
EXCLUDED_FROM_DENOMINATOR = frozenset({COACH_CANCELLED, SUPERSEDED_OR_RESCHEDULED, OPTIONAL})


@dataclass(frozen=True)
class CompletionAdherence:
    eligible_required_count: int
    completed_count: int
    partial_count: int
    ordinary_skipped_count: int
    safety_skipped_count: int
    missed_count: int
    pending_count: int
    coach_cancelled_count: int
    superseded_or_rescheduled_count: int
    optional_count: int
    completion_adherence_percentage: float | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "eligible_required_count": self.eligible_required_count,
            "completed_count": self.completed_count,
            "partial_count": self.partial_count,
            "ordinary_skipped_count": self.ordinary_skipped_count,
            "safety_skipped_count": self.safety_skipped_count,
            "missed_count": self.missed_count,
            "pending_count": self.pending_count,
            "coach_cancelled_count": self.coach_cancelled_count,
            "superseded_or_rescheduled_count": self.superseded_or_rescheduled_count,
            "optional_count": self.optional_count,
            "completion_adherence_percentage": self.completion_adherence_percentage,
        }


def aggregate_completion(labels: list[str]) -> CompletionAdherence:
    """Aggregate classification labels into completion-adherence counts."""

    counts = {
        COMPLETED: 0,
        PARTIAL: 0,
        ORDINARY_SKIPPED: 0,
        SAFETY_SKIPPED: 0,
        MISSED: 0,
        PENDING: 0,
        COACH_CANCELLED: 0,
        SUPERSEDED_OR_RESCHEDULED: 0,
        OPTIONAL: 0,
    }
    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    eligible = sum(
        count for label, count in counts.items() if label not in EXCLUDED_FROM_DENOMINATOR
    )
    percentage: float | None
    if eligible <= 0:
        percentage = None
    else:
        raw = counts[COMPLETED] / eligible * 100
        percentage = round(max(0.0, min(100.0, raw)), 1)

    return CompletionAdherence(
        eligible_required_count=eligible,
        completed_count=counts[COMPLETED],
        partial_count=counts[PARTIAL],
        ordinary_skipped_count=counts[ORDINARY_SKIPPED],
        safety_skipped_count=counts[SAFETY_SKIPPED],
        missed_count=counts[MISSED],
        pending_count=counts[PENDING],
        coach_cancelled_count=counts[COACH_CANCELLED],
        superseded_or_rescheduled_count=counts[SUPERSEDED_OR_RESCHEDULED],
        optional_count=counts[OPTIONAL],
        completion_adherence_percentage=percentage,
    )


# --- Set adherence -------------------------------------------------------


@dataclass(frozen=True)
class PrescribedSetInput:
    """A prescribed set within an eligible executed session (added sets excluded)."""

    set_type: str
    status: str


def prescribed_set_adherence(sets: list[PrescribedSetInput]) -> dict[str, Any]:
    """Prescribed working-set adherence. Trainee-added sets must be excluded upstream."""

    working = [s for s in sets if s.set_type == "working"]
    planned = len(working)
    completed = sum(1 for s in working if s.status == "completed")
    if planned <= 0:
        percentage: float | None = None
    else:
        percentage = round(min(100.0, completed / planned * 100), 1)
    return {
        "planned_working_sets": planned,
        "completed_planned_working_sets": completed,
        "percentage": percentage,
    }


# --- Exercise adherence --------------------------------------------------


@dataclass(frozen=True)
class ExerciseAdherenceInput:
    """A prescribed exercise within an eligible executed session.

    ``status`` is the session-exercise status; ``prescribed_working_completed``
    counts completed prescribed working sets; ``prescribed_any_completed``
    counts completed prescribed sets of any type; ``has_prescribed_working``
    indicates whether the exercise prescribes any working sets at all.
    """

    status: str
    prescribed_working_completed: int
    prescribed_any_completed: int
    has_prescribed_working: bool


def exercise_completed(exercise: ExerciseAdherenceInput) -> bool:
    """One documented rule across all five tracking modes.

    An exercise counts as completed when at least one prescribed working set is
    completed. For exercises that prescribe no working sets, it counts as
    completed when at least one prescribed set (of any type) is completed.
    Skipped / safety-stopped exercises never count as completed.
    """

    if exercise.status in ("skipped", "safety_stopped"):
        return False
    if exercise.has_prescribed_working:
        return exercise.prescribed_working_completed > 0
    return exercise.prescribed_any_completed > 0


def exercise_adherence(exercises: list[ExerciseAdherenceInput]) -> dict[str, Any]:
    planned = len(exercises)
    completed = sum(1 for ex in exercises if exercise_completed(ex))
    if planned <= 0:
        percentage: float | None = None
    else:
        percentage = round(min(100.0, completed / planned * 100), 1)
    return {
        "planned_exercises": planned,
        "completed_exercises": completed,
        "percentage": percentage,
    }
