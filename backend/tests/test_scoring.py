import pytest

from app.domain.scoring import (
    WEIGHTS,
    calculate_health_index,
    hydration_score,
    hydration_target_ml,
    interpretation_band,
    sleep_score,
    steps_score,
    stress_score,
)
from app.schemas import REQUIRED_ASSESSMENT_FIELDS


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("general_health", 3500),
        ("fat_loss", 4000),
        ("muscle_gain", 4500),
        ("strength", 4000),
        ("endurance", 5000),
        ("athletic_performance", 4500),
    ],
)
def test_hydration_target_by_goal(goal: str, expected: float) -> None:
    assert hydration_target_ml(100, goal) == expected


@pytest.mark.parametrize(
    ("ratio", "score", "status"),
    [(0.59, 59, "high"), (0.6, 60, "moderate"), (0.8, 80, "good"), (1, 100, "excellent"), (1.5, 100, "excellent")],
)
def test_hydration_ratio_boundaries(ratio: float, score: float, status: str) -> None:
    assert hydration_score(ratio * 1000, 1000) == (score, status)


@pytest.mark.parametrize(
    ("steps", "score", "status"),
    [(4999, 35, "sedentary"), (5000, 55, "low_active"), (7500, 75, "somewhat_active"), (10000, 90, "active"), (12500, 100, "highly_active")],
)
def test_step_boundaries(steps: int, score: float, status: str) -> None:
    assert steps_score(steps) == (score, status)


def test_sleep_uses_duration_quality_and_refreshment() -> None:
    optimal, _ = sleep_score(8, 5, True, "general_health")
    poor_quality, _ = sleep_score(8, 1, False, "general_health")
    too_short, _ = sleep_score(4.9, 5, True, "general_health")
    assert optimal == 100
    assert poor_quality < optimal
    assert too_short < optimal


def test_stress_is_inverted_and_capped() -> None:
    assert stress_score(0) == (100, "low")
    assert stress_score(10) == (0, "very_high")


@pytest.mark.parametrize(
    ("score", "band"),
    [(90, "Elite"), (80, "Excellent"), (70, "Good"), (60, "Average"), (40, "Needs Improvement"), (39.9, "High Risk")],
)
def test_interpretation_bands(score: float, band: str) -> None:
    assert interpretation_band(score) == band


def test_weighted_score_is_deterministic_and_auditable(complete_assessment: dict) -> None:
    first = calculate_health_index(complete_assessment, REQUIRED_ASSESSMENT_FIELDS)
    second = calculate_health_index(complete_assessment, REQUIRED_ASSESSMENT_FIELDS)
    assert first == second
    assert sum(WEIGHTS.values()) == 100
    assert 0 <= first["overall_score"] <= 100
    assert len(first["components"]) == 10
    assert all("weighted_contribution" in item for item in first["components"])


def test_missing_optional_data_is_explicit(complete_assessment: dict) -> None:
    complete_assessment["resting_heart_rate"] = None
    complete_assessment["protein_target_g"] = None
    result = calculate_health_index(complete_assessment, REQUIRED_ASSESSMENT_FIELDS)
    assert "resting_heart_rate" in result["missing_fields"]
    assert "protein_target_g" in result["missing_fields"]
