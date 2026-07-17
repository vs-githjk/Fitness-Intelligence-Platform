"""Unit tests for the isolated workout-load-v1 analytics engines."""

from datetime import date
from decimal import Decimal

from app.analytics import (
    CALCULATION_VERSION,
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
    week_start,
)


def _set(source, set_type, mode, status, reps=None, load=None, dur=None, dist=None):
    return SetInput(
        source=source,
        set_type=set_type,
        tracking_mode=mode,
        status=status,
        actual_repetitions=reps,
        actual_load_canonical_kg=load,
        actual_duration_seconds=dur,
        actual_distance_meters=dist,
    )


# --- planned / completed load -------------------------------------------


def test_planned_load_from_inputs():
    result = compute_session_load(
        SessionLoadInput("completed", 60, 7.0, None, None)
    )
    assert result.planned_session_load == 420.0


def test_completed_load_from_inputs():
    result = compute_session_load(
        SessionLoadInput("completed", None, None, 50, Decimal("8"))
    )
    assert result.completed_session_load == 400.0


def test_missing_planned_inputs_stay_unavailable():
    result = compute_session_load(SessionLoadInput("completed", None, 7.0, 50, Decimal("8")))
    assert result.planned_session_load is None
    assert result.calculation_payload["planned_session_load"]["available"] is False


def test_completed_load_requires_terminal_status():
    result = compute_session_load(SessionLoadInput("in_progress", 60, 7.0, 55, Decimal("8")))
    assert result.completed_session_load is None
    assert result.calculation_payload["completed_session_load"]["reason"] == "session_not_terminal"


def test_partial_and_safety_ended_are_terminal():
    for status in ("ended_incomplete", "safety_ended"):
        result = compute_session_load(SessionLoadInput(status, 60, 7.0, 30, Decimal("6")))
        assert result.completed_session_load == 180.0


# --- resistance volume ---------------------------------------------------


def test_resistance_volume_only_completed_repetitions_and_load():
    session = SessionLoadInput(
        "completed", 60, 7.0, 55, Decimal("8"),
        exercises=(
            SessionExerciseInput("completed", "repetitions_and_load", sets=(
                _set("prescribed", "working", "repetitions_and_load", "completed", 10, Decimal("100")),
                _set("prescribed", "working", "repetitions_and_load", "completed", 8, Decimal("50")),
                _set("prescribed", "working", "repetitions_and_load", "skipped"),
            )),
        ),
    )
    result = compute_session_load(session)
    assert result.session_volume_kg == Decimal("1400.000")


def test_volume_kg_lb_via_canonical():
    # 20 lb -> 9.072 kg already converted upstream to canonical kg.
    session = SessionLoadInput(
        "completed", 60, 7.0, 55, Decimal("8"),
        exercises=(
            SessionExerciseInput("completed", "repetitions_and_load", sets=(
                _set("prescribed", "working", "repetitions_and_load", "completed", 5, Decimal("9.072")),
            )),
        ),
    )
    assert compute_session_load(session).session_volume_kg == Decimal("45.360")


def test_volume_excludes_bodyweight_assistance_timed_distance():
    session = SessionLoadInput(
        "completed", 60, 7.0, 55, Decimal("8"),
        exercises=(
            SessionExerciseInput("completed", "bodyweight_or_assisted_repetitions", sets=(
                _set("prescribed", "working", "bodyweight_or_assisted_repetitions", "completed", 12),
            )),
            SessionExerciseInput("completed", "duration", sets=(
                _set("prescribed", "working", "duration", "completed", dur=60),
            )),
            SessionExerciseInput("completed", "distance_and_duration", sets=(
                _set("prescribed", "working", "distance_and_duration", "completed", dur=300, dist=Decimal("1000")),
            )),
            SessionExerciseInput("completed", "repetitions_only", sets=(
                _set("prescribed", "working", "repetitions_only", "completed", 15),
            )),
        ),
    )
    result = compute_session_load(session)
    assert result.session_volume_kg is None
    assert result.total_duration_seconds == 360
    assert result.total_distance_meters == Decimal("1000.000")


def test_factual_counts_prescribed_added_skipped():
    session = SessionLoadInput(
        "completed", 60, 7.0, 55, Decimal("8"),
        exercises=(
            SessionExerciseInput("completed", "repetitions_and_load", sets=(
                _set("prescribed", "working", "repetitions_and_load", "completed", 10, Decimal("100")),
                _set("prescribed", "working", "repetitions_and_load", "skipped"),
                _set("trainee_added", "working", "repetitions_and_load", "completed", 8, Decimal("40")),
                _set("prescribed", "warm_up", "repetitions_and_load", "completed", 5, Decimal("20")),
            )),
        ),
    )
    result = compute_session_load(session)
    assert result.completed_prescribed_sets == 2
    assert result.skipped_prescribed_sets == 1
    assert result.completed_added_sets == 1
    assert result.completed_working_sets == 2  # working type, completed
    assert result.completed_repetitions == 23
    assert result.completed_exercises == 1
    assert result.calculation_version == CALCULATION_VERSION


# --- classification ------------------------------------------------------


def _cls(**kw):
    defaults = dict(
        scheduled_local_date=date(2026, 7, 1),
        today_local_date=date(2026, 7, 10),
        required=True,
        scheduled_status="scheduled",
        session_status=None,
        skip_kind=None,
    )
    defaults.update(kw)
    return classify_workout(WorkoutClassificationInput(**defaults))


def test_classify_completed():
    assert _cls(session_status="completed") == "completed"


def test_classify_ended_incomplete_is_always_partial():
    # Zero completed sets no longer downgrades to skipped — a started session
    # that ends incomplete is always partial.
    assert _cls(session_status="ended_incomplete") == "partial"


def test_classify_safety_ended_session_is_partial():
    # A safety-ended session is partial, not safety_skipped.
    assert _cls(session_status="safety_ended") == "partial"


def test_classify_explicit_skip_kinds():
    assert _cls(scheduled_status="skipped", skip_kind="ordinary") == "ordinary_skipped"
    assert _cls(scheduled_status="skipped", skip_kind="safety") == "safety_skipped"


def test_classify_missed_after_grace_and_pending_within_window():
    assert _cls(scheduled_local_date=date(2026, 7, 1), today_local_date=date(2026, 7, 3)) == "missed"
    assert _cls(scheduled_local_date=date(2026, 7, 1), today_local_date=date(2026, 7, 2)) == "pending"


def test_classify_active_session_window_elapsed_is_partial():
    assert _cls(session_status="in_progress", today_local_date=date(2026, 7, 3)) == "partial"


def test_classify_exclusions():
    assert _cls(scheduled_status="cancelled") == "coach_cancelled"
    assert _cls(scheduled_status="superseded") == "superseded_or_rescheduled"
    assert _cls(required=False) == "optional"


def test_completion_percentage_and_denominator():
    labels = [
        "completed", "completed", "partial", "missed",
        "optional", "coach_cancelled", "superseded_or_rescheduled",
    ]
    agg = aggregate_completion(labels)
    assert agg.eligible_required_count == 4
    assert agg.completed_count == 2
    assert agg.completion_adherence_percentage == 50.0
    assert agg.optional_count == 1


def test_completion_no_denominator_is_unavailable():
    agg = aggregate_completion(["optional", "coach_cancelled"])
    assert agg.eligible_required_count == 0
    assert agg.completion_adherence_percentage is None


def test_completion_percentage_bounds():
    agg = aggregate_completion(["completed"] * 3)
    assert agg.completion_adherence_percentage == 100.0


# --- set / exercise adherence -------------------------------------------


def test_prescribed_set_adherence_excludes_added():
    sets = [
        PrescribedSetInput("working", "completed"),
        PrescribedSetInput("working", "completed"),
        PrescribedSetInput("working", "skipped"),
        PrescribedSetInput("warm_up", "completed"),  # not working -> ignored
    ]
    result = prescribed_set_adherence(sets)
    assert result == {
        "planned_working_sets": 3,
        "completed_planned_working_sets": 2,
        "percentage": round(2 / 3 * 100, 1),
    }


def test_prescribed_set_adherence_no_denominator():
    assert prescribed_set_adherence([])["percentage"] is None


def test_exercise_adherence_rule():
    exercises = [
        ExerciseAdherenceInput("completed", 1, 2, True),   # working completed -> yes
        ExerciseAdherenceInput("completed", 0, 3, True),   # working prescribed but none done -> no
        ExerciseAdherenceInput("completed", 0, 1, False),  # no working, any completed -> yes
        ExerciseAdherenceInput("skipped", 5, 5, True),     # skipped -> no
    ]
    result = exercise_adherence(exercises)
    assert result["planned_exercises"] == 4
    assert result["completed_exercises"] == 2
    assert result["percentage"] == 50.0


# --- weekly & comparison -------------------------------------------------


def test_week_start_is_monday():
    assert week_start(date(2026, 7, 16)) == date(2026, 7, 13)  # Thu -> Mon


def test_aggregate_weeks_missing_not_zero():
    sessions = [
        WeeklySessionInput(date(2026, 7, 13), "completed", 300.0, 280.0, Decimal("1000")),
        WeeklySessionInput(date(2026, 7, 14), "missed", 200.0, None, None),
        WeeklySessionInput(date(2026, 7, 20), "completed", None, 150.0, None),
    ]
    weeks = aggregate_weeks(sessions, "Asia/Kolkata")
    assert len(weeks) == 2
    first = weeks[0]
    assert first["week_start_local_date"] == date(2026, 7, 13)
    assert first["planned_session_load_total"] == 500.0
    assert first["completed_session_load_total"] == 280.0
    assert first["unavailable_completed_load_count"] == 1
    assert first["resistance_volume_kg"] == "1000"
    assert first["missed_count"] == 1
    second = weeks[1]
    assert second["unavailable_planned_load_count"] == 1
    assert second["resistance_volume_kg"] is None


def test_compare_planned_completed_states():
    assert compare_planned_completed(300.0, 305.0)["state"] == "near_planned"
    assert compare_planned_completed(300.0, 400.0)["state"] == "above_planned"
    assert compare_planned_completed(300.0, 100.0)["state"] == "below_planned"
    assert compare_planned_completed(None, 100.0)["state"] == "unavailable"
    assert compare_planned_completed(300.0, None)["state"] == "unavailable"
