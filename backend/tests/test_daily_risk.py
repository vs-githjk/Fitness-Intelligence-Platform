from datetime import date, timedelta

from app.domain.daily_risk import evaluate_daily_risks


def record(local_date: date, **overrides: object) -> dict:
    values = {
        "local_date": local_date,
        "sleep_hours": 7,
        "stress": 4,
        "fatigue": 3,
        "soreness": 2,
        "exercised": False,
        "exercise_minutes": None,
        "session_rpe": None,
        "steps": 7000,
        "water_liters": 2.5,
        "hydration_ratio": 0.9,
        "protein_grams": 100,
        "protein_ratio": 0.9,
        "recovery_score": 75,
    }
    return {**values, **overrides}


def score(**overrides: object) -> dict:
    return {
        "recovery_score": 70,
        "recent_training_load": {"total": 500},
        **overrides,
    }


def test_latest_and_consecutive_rules() -> None:
    start = date(2026, 7, 10)
    records = [
        record(start + timedelta(days=offset), sleep_hours=5.5, stress=8, fatigue=8)
        for offset in range(3)
    ]
    keys = {item["rule_key"] for item in evaluate_daily_risks(records, score())}
    assert {"sustained_sleep_below_6h", "sustained_stress_8_plus", "sustained_fatigue_8_plus"} <= keys


def test_missing_day_breaks_consecutive_pattern() -> None:
    records = [
        record(date(2026, 7, 10), sleep_hours=5.5),
        record(date(2026, 7, 12), sleep_hours=5.5),
        record(date(2026, 7, 13), sleep_hours=5.5),
    ]
    keys = {item["rule_key"] for item in evaluate_daily_risks(records, score())}
    assert "sustained_sleep_below_6h" not in keys


def test_high_load_low_recovery_and_decline() -> None:
    start = date(2026, 7, 10)
    records = [record(start + timedelta(days=offset), recovery_score=80) for offset in range(4)]
    result = evaluate_daily_risks(
        records, score(recovery_score=45, recent_training_load={"total": 1900})
    )
    keys = {item["rule_key"] for item in result}
    assert "high_load_low_recovery" in keys
    assert "recovery_decline_20" in keys
    assert all("dates" in item["triggering_inputs"] for item in result)
