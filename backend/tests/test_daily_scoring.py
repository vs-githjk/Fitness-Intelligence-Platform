from copy import deepcopy

import pytest

from app.domain.daily_scoring import (
    calculate_daily_scores,
    readiness_state,
    sleep_duration_score,
    training_load,
    training_load_tolerance_score,
)


@pytest.fixture
def daily_data() -> dict:
    return {
        "sleep_hours": 8,
        "sleep_quality": 4,
        "wake_refreshed": True,
        "soreness": 2,
        "fatigue": 2,
        "stress": 3,
        "steps": 8500,
        "exercised": True,
        "exercise_minutes": 45,
        "session_rpe": 6,
        "activity_types": ["strength_training"],
        "water_liters": 2.5,
        "protein_grams": 100,
        "nutrition_adherence": 80,
    }


@pytest.fixture
def baseline() -> dict:
    return {
        "weight_kg": 75,
        "selected_goal": "general_health",
        "protein_target_g": 110,
    }


def test_recovery_boundaries_and_inversion(daily_data: dict, baseline: dict) -> None:
    strong = calculate_daily_scores(daily_data, baseline, [daily_data])
    strained_data = {**daily_data, "fatigue": 10, "soreness": 10, "stress": 10}
    strained = calculate_daily_scores(strained_data, baseline, [strained_data])
    assert 0 <= strained["recovery_score"] < strong["recovery_score"] <= 100
    assert sleep_duration_score(8, "general_health")[0] == 100
    assert sleep_duration_score(4, "general_health")[0] < 100


@pytest.mark.parametrize(
    ("score", "state"),
    [(80, "ready_to_push"), (79.9, "maintain"), (60, "maintain"), (59.9, "reduce_intensity"), (40, "reduce_intensity"), (39.9, "recovery_recommended")],
)
def test_readiness_state_boundaries(score: float, state: str) -> None:
    assert readiness_state(score) == state


def test_activity_caps_and_step_boundaries(daily_data: dict, baseline: dict) -> None:
    long_session = calculate_daily_scores(
        {**daily_data, "steps": 4999, "exercise_minutes": 600}, baseline, [daily_data]
    )
    capped_session = calculate_daily_scores(
        {**daily_data, "steps": 4999, "exercise_minutes": 60}, baseline, [daily_data]
    )
    assert long_session["activity_score"] == capped_session["activity_score"]
    at_band = calculate_daily_scores({**daily_data, "steps": 5000}, baseline, [daily_data])
    assert at_band["activity_score"] > capped_session["activity_score"]


def test_hydration_and_missing_nutrition_are_explicit(daily_data: dict, baseline: dict) -> None:
    complete = calculate_daily_scores(daily_data, baseline, [daily_data])
    missing = calculate_daily_scores(
        {**daily_data, "protein_grams": None, "nutrition_adherence": None},
        None,
        [daily_data],
    )
    hydration = next(
        item for item in complete["components"] if item["key"] == "hydration_compliance"
    )
    assert hydration["raw_inputs"]["target_liters"] == 2.625
    assert missing["nutrition_score"] is None
    assert set(missing["missing_fields"]) == {
        "hydration_target",
        "protein_compliance",
        "nutrition_adherence",
    }


def test_training_load_and_determinism(daily_data: dict, baseline: dict) -> None:
    assert training_load(45, 6) == 270
    assert training_load_tolerance_score(1200) == 100
    assert training_load_tolerance_score(3200) == 0
    first = calculate_daily_scores(deepcopy(daily_data), baseline, [daily_data] * 7)
    second = calculate_daily_scores(deepcopy(daily_data), baseline, [daily_data] * 7)
    assert first == second
    assert all(0 <= first[key] <= 100 for key in ("recovery_score", "activity_score", "readiness_score"))
    assert first["nutrition_score"] is not None and 0 <= first["nutrition_score"] <= 100
