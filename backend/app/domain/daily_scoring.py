from dataclasses import asdict, dataclass
from typing import Any

from app.domain.scoring import SLEEP_RANGES, clamp, hydration_target_ml, steps_score

SCORING_VERSION = "daily-intelligence-v1"


@dataclass(frozen=True)
class DailyComponent:
    key: str
    group: str
    raw_inputs: dict[str, Any]
    normalized_score: float
    weight: float
    contribution: float
    status: str
    explanation: str
    missing: bool = False


def _component(
    key: str,
    group: str,
    score: float,
    weight: float,
    status: str,
    inputs: dict[str, Any],
    explanation: str,
    *,
    missing: bool = False,
) -> DailyComponent:
    normalized = clamp(score)
    return DailyComponent(
        key=key,
        group=group,
        raw_inputs=inputs,
        normalized_score=normalized,
        weight=round(weight, 2),
        contribution=round(normalized * weight / 100, 2),
        status=status,
        explanation=explanation,
        missing=missing,
    )


def sleep_duration_score(hours: float, goal: str) -> tuple[float, tuple[float, float]]:
    low, high = SLEEP_RANGES.get(goal, SLEEP_RANGES["general_health"])
    if low <= hours <= high:
        return 100.0, (low, high)
    if hours < low:
        return clamp(hours / low * 100), (low, high)
    return clamp(100 - (hours - high) * 12.5), (low, high)


def readiness_state(score: float) -> str:
    if score >= 80:
        return "ready_to_push"
    if score >= 60:
        return "maintain"
    if score >= 40:
        return "reduce_intensity"
    return "recovery_recommended"


def training_load(exercise_minutes: int | None, session_rpe: float | None) -> float:
    if exercise_minutes is None or session_rpe is None:
        return 0.0
    return round(exercise_minutes * session_rpe, 1)


def training_load_tolerance_score(seven_day_load: float) -> float:
    """No readiness penalty through 1,200 AU; progressively reduce above it."""
    return clamp(100 - max(0.0, seven_day_load - 1200) / 20)


def calculate_daily_scores(
    data: dict[str, Any],
    baseline: dict[str, Any] | None,
    recent_check_ins: list[dict[str, Any]],
) -> dict[str, Any]:
    goal = (baseline or {}).get("selected_goal") or "general_health"
    duration, sleep_range = sleep_duration_score(data["sleep_hours"], goal)
    recovery_specs = [
        ("sleep_duration", duration, 30, {"hours": data["sleep_hours"], "target_range": sleep_range}, "Sleep duration is compared with the baseline goal range and capped at 100."),
        ("sleep_quality", data["sleep_quality"] / 5 * 100, 15, {"quality": data["sleep_quality"], "scale": [1, 5]}, "Sleep quality maps linearly from the 1–5 response."),
        ("wake_refreshed", 100 if data["wake_refreshed"] else 40, 10, {"wake_refreshed": data["wake_refreshed"]}, "Waking refreshed receives 100; no receives a conservative 40."),
        ("fatigue", 100 - data["fatigue"] * 10, 15, {"fatigue": data["fatigue"], "scale": [0, 10]}, "Fatigue is inverted from the 0–10 response."),
        ("soreness", 100 - data["soreness"] * 10, 15, {"soreness": data["soreness"], "scale": [0, 10]}, "Soreness is inverted from the 0–10 response."),
        ("stress", 100 - data["stress"] * 10, 15, {"stress": data["stress"], "scale": [0, 10]}, "Stress is inverted from the 0–10 response."),
    ]
    components: list[DailyComponent] = []
    for key, score, weight, inputs, explanation in recovery_specs:
        components.append(
            _component(
                key,
                "recovery",
                score,
                weight,
                "strong" if score >= 80 else "review" if score >= 60 else "needs_attention",
                inputs,
                explanation,
            )
        )
    recovery_score = clamp(sum(item.contribution for item in components))

    step_score, step_status = steps_score(data["steps"])
    duration_score = clamp(min(data.get("exercise_minutes") or 0, 60) / 60 * 100)
    if data["exercised"]:
        participation_score = min(100.0, 70 + min(len(data.get("activity_types", [])), 3) * 10)
        participation_status = "recorded"
    else:
        participation_score, participation_status = 30.0, "no_session"
    activity_components = [
        _component("steps", "activity", step_score, 50, step_status, {"steps": data["steps"]}, "Steps use the existing fixed activity bands."),
        _component("exercise_duration", "activity", duration_score, 25, "capped" if (data.get("exercise_minutes") or 0) >= 60 else "recorded", {"minutes": data.get("exercise_minutes"), "credit_cap_minutes": 60}, "Duration credit increases to 60 minutes and does not reward additional volume."),
        _component("exercise_participation", "activity", participation_score, 25, participation_status, {"exercised": data["exercised"], "activity_types": data.get("activity_types", [])}, "Participation receives base credit; up to three activity types add context without ranking modalities."),
    ]
    components.extend(activity_components)
    activity_score = clamp(sum(item.contribution for item in activity_components))

    nutrition_specs: list[tuple[str, float, float, dict[str, Any], str]] = []
    missing_fields: list[str] = []
    weight_kg, baseline_goal = (baseline or {}).get("weight_kg"), (baseline or {}).get("selected_goal")
    if weight_kg and baseline_goal:
        target_liters = hydration_target_ml(weight_kg, baseline_goal) / 1000
        nutrition_specs.append(("hydration_compliance", clamp(data["water_liters"] / target_liters * 100), 50, {"actual_liters": data["water_liters"], "target_liters": target_liters}, "Water intake is compared with the stored baseline weight-and-goal target."))
    else:
        missing_fields.append("hydration_target")
        components.append(_component("hydration_compliance", "nutrition", 0, 0, "unavailable", {"actual_liters": data["water_liters"], "target_liters": None}, "A stored baseline weight and goal are required; no target was invented.", missing=True))
    protein_target = (baseline or {}).get("protein_target_g")
    if protein_target and data.get("protein_grams") is not None:
        nutrition_specs.append(("protein_compliance", clamp(data["protein_grams"] / protein_target * 100), 30, {"actual_grams": data["protein_grams"], "target_grams": protein_target}, "Protein is compared only with a target already stored in the submitted baseline."))
    else:
        missing_fields.append("protein_compliance")
        components.append(_component("protein_compliance", "nutrition", 0, 0, "unavailable", {"actual_grams": data.get("protein_grams"), "target_grams": protein_target}, "Both a stored target and today's intake are required; no value was imputed.", missing=True))
    if data.get("nutrition_adherence") is not None:
        nutrition_specs.append(("nutrition_adherence", float(data["nutrition_adherence"]), 20, {"adherence_percent": data["nutrition_adherence"]}, "Self-reported plan adherence is used directly on the 0–100 scale."))
    else:
        missing_fields.append("nutrition_adherence")
        components.append(_component("nutrition_adherence", "nutrition", 0, 0, "unavailable", {"adherence_percent": None}, "Optional adherence was not reported and is excluded.", missing=True))
    available_weight = sum(item[2] for item in nutrition_specs)
    nutrition_score: float | None = None
    if available_weight:
        nutrition_components = []
        for key, score, base_weight, inputs, explanation in nutrition_specs:
            effective_weight = base_weight / available_weight * 100
            nutrition_components.append(_component(key, "nutrition", score, effective_weight, "on_track" if score >= 80 else "review" if score >= 60 else "needs_attention", inputs, explanation))
        components.extend(nutrition_components)
        nutrition_score = clamp(sum(item.contribution for item in nutrition_components))

    loads = [training_load(item.get("exercise_minutes"), item.get("session_rpe")) for item in recent_check_ins]
    seven_day_load = round(sum(loads), 1)
    load_score = training_load_tolerance_score(seven_day_load)
    components.append(_component("recent_training_load", "readiness", load_score, 30, "high_load_review" if load_score < 70 else "within_product_threshold", {"daily_loads": loads, "seven_day_load": seven_day_load, "no_penalty_through": 1200}, "Seven-day exercise minutes × session RPE does not reduce readiness through 1,200 arbitrary units, then applies a capped penalty."))
    readiness_score_value = clamp(recovery_score * 0.7 + load_score * 0.3)
    return {
        "recovery_score": recovery_score,
        "activity_score": activity_score,
        "nutrition_score": nutrition_score,
        "readiness_score": readiness_score_value,
        "readiness_state": readiness_state(readiness_score_value),
        "scoring_version": SCORING_VERSION,
        "components": [asdict(item) for item in components],
        "missing_fields": missing_fields,
        "recent_training_load": {
            "window_days": 7,
            "daily_loads": loads,
            "total": seven_day_load,
            "tolerance_score": load_score,
        },
    }
