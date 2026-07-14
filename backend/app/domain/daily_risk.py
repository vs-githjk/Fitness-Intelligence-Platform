from collections.abc import Callable
from datetime import timedelta
from typing import Any

RULE_VERSION = "daily-risk-v1"


def _flag(
    key: str,
    severity: str,
    title: str,
    explanation: str,
    action: str,
    records: list[dict[str, Any]],
    value_keys: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "rule_key": key,
        "severity": severity,
        "status": "open",
        "title": title,
        "explanation": explanation,
        "recommended_action": action,
        "triggering_inputs": {
            "dates": [str(item["local_date"]) for item in records],
            "values": [
                {key: item.get(key) for key in value_keys}
                for item in records
            ],
        },
        "rule_version": RULE_VERSION,
    }


def _trailing_calendar_sequence(
    records: list[dict[str, Any]],
    count: int,
    predicate: Callable[[dict[str, Any]], bool],
) -> list[dict[str, Any]]:
    if len(records) < count:
        return []
    tail = records[-count:]
    if not all(predicate(item) for item in tail):
        return []
    for previous, current in zip(tail, tail[1:], strict=False):
        if current["local_date"] != previous["local_date"] + timedelta(days=1):
            return []
    return tail


def evaluate_daily_risks(
    records: list[dict[str, Any]], score: dict[str, Any]
) -> list[dict[str, Any]]:
    """Evaluate only patterns ending on the latest stored local date."""
    if not records:
        return []
    records = sorted(records, key=lambda item: item["local_date"])
    latest = records[-1]
    flags: list[dict[str, Any]] = []
    if latest["sleep_hours"] < 5:
        flags.append(_flag("daily_sleep_below_5h", "review", "Very short sleep reported", "The latest check-in reports less than five hours of sleep.", "Prioritize recovery and discuss persistent sleep difficulty with your coach or an appropriate professional.", [latest], ("sleep_hours",)))
    if latest["stress"] >= 9:
        flags.append(_flag("daily_stress_9_plus", "elevated", "Very high stress reported", "The latest self-reported stress is at or above the configured review threshold.", "Consider reducing training intensity today and review available support with your coach.", [latest], ("stress",)))
    patterns = [
        ("sustained_sleep_below_6h", "Sustained low-sleep pattern", "sleep_hours", lambda item: item["sleep_hours"] < 6, "Review sleep opportunity and recovery across these consecutive days."),
        ("sustained_stress_8_plus", "Sustained high-stress pattern", "stress", lambda item: item["stress"] >= 8, "Consider reducing intensity and reviewing stress and recovery with your coach."),
        ("sustained_fatigue_8_plus", "Sustained fatigue pattern", "fatigue", lambda item: item["fatigue"] >= 8, "Use a lower-intensity approach and discuss sustained fatigue with your coach."),
        ("sustained_soreness_8_plus", "Sustained soreness pattern", "soreness", lambda item: item["soreness"] >= 8, "Consider active recovery and review persistent or worsening soreness with an appropriate professional."),
    ]
    for key, title, value_key, predicate, action in patterns:
        tail = _trailing_calendar_sequence(records, 3, predicate)
        if tail:
            flags.append(_flag(key, "elevated", title, "Three consecutive check-ins meet the configured review threshold.", action, tail, (value_key,)))
    high_rpe = _trailing_calendar_sequence(
        records,
        5,
        lambda item: item.get("exercised") and (item.get("session_rpe") or 0) >= 9,
    )
    if high_rpe:
        flags.append(_flag("five_high_rpe_days", "elevated", "Repeated very-high-effort sessions", "Five consecutive local dates report exercise at session RPE 9 or above.", "Consider reducing intensity and reviewing the recent session pattern with your coach.", high_rpe, ("exercise_minutes", "session_rpe")))
    if score["recent_training_load"]["total"] > 1800 and score["recovery_score"] < 50:
        flags.append(_flag("high_load_low_recovery", "elevated", "High recent load with low recovery", "The seven-day training-load signal is above 1,800 arbitrary units while Recovery is below 50.", "Consider reducing intensity and reviewing recovery before another demanding session.", [latest], ("exercise_minutes", "session_rpe")))
    hydration_tail = _trailing_calendar_sequence(
        records, 3, lambda item: item.get("hydration_ratio") is not None and item["hydration_ratio"] < 0.5
    )
    if hydration_tail:
        flags.append(_flag("sustained_hydration_below_50", "review", "Sustained low hydration reporting", "Hydration is below 50% of the stored baseline-derived target for three consecutive check-ins.", "Increase gradually toward the configured target; do not force excessive intake.", hydration_tail, ("water_liters", "hydration_ratio")))
    protein_tail = _trailing_calendar_sequence(
        records, 3, lambda item: item.get("protein_ratio") is not None and item["protein_ratio"] < 0.8
    )
    if protein_tail:
        flags.append(_flag("sustained_protein_below_80", "informational", "Repeated protein gap", "Protein is below 80% of the stored target for three consecutive recorded days.", "Review the stored target and intake pattern with an appropriate coach or nutrition professional.", protein_tail, ("protein_grams", "protein_ratio")))
    if len(records) >= 8:
        last_eight = records[-8:]
        complete_span = last_eight[-1]["local_date"] - last_eight[0]["local_date"] == timedelta(days=7)
        if complete_span and all(not item["exercised"] and item["steps"] < 5000 for item in last_eight):
            flags.append(_flag("no_recorded_activity_8_days", "review", "Recent activity review recommended", "Eight consecutive check-ins report no exercise and fewer than 5,000 steps.", "If appropriate, consider a short walk or discuss barriers to activity with your coach.", last_eight, ("steps", "exercised")))
    previous_scores = [item["recovery_score"] for item in records[-4:-1] if item.get("recovery_score") is not None]
    if len(previous_scores) == 3:
        previous_average = sum(previous_scores) / 3
        if previous_average - score["recovery_score"] >= 20:
            latest_with_delta = {**latest, "previous_recovery_average": round(previous_average, 1), "recovery_score": score["recovery_score"]}
            flags.append(_flag("recovery_decline_20", "review", "Recovery review recommended", "Recovery is at least 20 points below the previous three-record average.", "Use today's contributing metrics to review sleep, stress, fatigue and soreness with your coach.", [latest_with_delta], ("recovery_score", "previous_recovery_average")))
    return flags
