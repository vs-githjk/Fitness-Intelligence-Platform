import pytest

from app.domain.risk import evaluate_risks


@pytest.mark.parametrize(
    ("field", "value", "rule"),
    [
        ("sleep_hours", 4.99, "sleep_below_5h"),
        ("stress_level", 9, "stress_9_plus"),
        ("resting_heart_rate", 96, "resting_hr_above_95"),
        ("chest_pain", True, "reported_chest_pain"),
        ("shortness_of_breath", True, "reported_shortness_of_breath"),
        ("palpitations", True, "reported_palpitations"),
    ],
)
def test_risk_boundaries(complete_assessment: dict, field: str, value: object, rule: str) -> None:
    complete_assessment[field] = value
    assert rule in {item["rule_key"] for item in evaluate_risks(complete_assessment)}


def test_boundary_values_do_not_trigger(complete_assessment: dict) -> None:
    complete_assessment.update(sleep_hours=5, stress_level=8, resting_heart_rate=95)
    keys = {item["rule_key"] for item in evaluate_risks(complete_assessment)}
    assert "sleep_below_5h" not in keys
    assert "stress_9_plus" not in keys
    assert "resting_hr_above_95" not in keys


def test_urgent_symptom_language_is_not_diagnostic(complete_assessment: dict) -> None:
    complete_assessment["chest_pain"] = True
    alert = next(item for item in evaluate_risks(complete_assessment) if item["rule_key"] == "reported_chest_pain")
    assert alert["severity"] == "urgent"
    assert "not a diagnosis" in alert["explanation"].lower()
    assert "immediate professional medical help" in alert["recommended_action"].lower()
