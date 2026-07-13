from dataclasses import asdict, dataclass
from typing import Any

SCORING_VERSION = "health-index-v1"
WEIGHTS = {
    "hydration": 10,
    "sleep": 15,
    "nutrition": 15,
    "stress": 10,
    "cardiovascular": 10,
    "workout_intensity": 10,
    "physical_activity": 10,
    "daily_steps": 10,
    "goal_alignment": 5,
    "assessment_completion": 5,
}
HYDRATION_ML_PER_KG = {
    "general_health": 35,
    "fat_loss": 40,
    "muscle_gain": 45,
    "strength": 40,
    "endurance": 50,
    "athletic_performance": 45,
}
SLEEP_RANGES = {
    "fat_loss": (7.5, 9),
    "muscle_gain": (8, 9),
    "strength": (7.5, 8.5),
    "endurance": (8, 10),
    "general_health": (7, 9),
    "athletic_performance": (8, 10),
}


@dataclass(frozen=True)
class Component:
    key: str
    raw_inputs: dict[str, Any]
    normalized_score: float
    weight: float
    weighted_contribution: float
    status: str
    explanation: str


def clamp(value: float) -> float:
    return round(max(0.0, min(100.0, value)), 1)


def hydration_target_ml(weight_kg: float, goal: str) -> float:
    return round(weight_kg * HYDRATION_ML_PER_KG[goal])


def hydration_score(actual_ml: float, target_ml: float) -> tuple[float, str]:
    ratio = actual_ml / target_ml if target_ml else 0
    status = (
        "high"
        if ratio < 0.6
        else "moderate"
        if ratio < 0.8
        else "good"
        if ratio < 1
        else "excellent"
    )
    return clamp(ratio * 100), status


def sleep_score(hours: float, quality: int, refreshed: bool, goal: str) -> tuple[float, str]:
    low, high = SLEEP_RANGES[goal]
    if low <= hours <= high:
        duration = 100
    elif hours < low:
        duration = clamp(hours / low * 100)
    else:
        duration = clamp(100 - (hours - high) * 12.5)
    score = clamp(duration * 0.6 + quality / 5 * 100 * 0.25 + (100 if refreshed else 40) * 0.15)
    status = "optimal" if score >= 80 else "review" if score >= 60 else "needs_attention"
    return score, status


def steps_score(steps: int) -> tuple[float, str]:
    if steps < 5000:
        return 35.0, "sedentary"
    if steps < 7500:
        return 55.0, "low_active"
    if steps < 10000:
        return 75.0, "somewhat_active"
    if steps < 12500:
        return 90.0, "active"
    return 100.0, "highly_active"


def stress_score(stress: int) -> tuple[float, str]:
    score = clamp(100 - stress * 10)
    status = (
        "low"
        if stress <= 3
        else "moderate"
        if stress <= 6
        else "high"
        if stress <= 8
        else "very_high"
    )
    return score, status


def component(
    key: str, score: float, status: str, inputs: dict[str, Any], explanation: str
) -> Component:
    score = clamp(score)
    weight = WEIGHTS[key]
    return Component(
        key, inputs, score, weight, round(score * weight / 100, 2), status, explanation
    )


def calculate_health_index(data: dict[str, Any], required_fields: list[str]) -> dict[str, Any]:
    goal = data["selected_goal"]
    target = hydration_target_ml(data["weight_kg"], goal)
    hs, hstatus = hydration_score(data["hydration_ml"], target)
    ss, sstatus = sleep_score(
        data["sleep_hours"], data["sleep_quality"], data["wake_refreshed"], goal
    )
    stscore, ststatus = stress_score(data["stress_level"])
    dscore, dstatus = steps_score(data["daily_steps"])

    minutes = data["activity_minutes_weekly"]
    activity_score = clamp(minutes / 150 * 100)
    activity_status = "meets_baseline" if minutes >= 150 else "below_baseline"

    frequency, rpe = data["workout_frequency_weekly"], data["average_rpe"]
    if frequency == 0:
        workout_score, workout_status = 30, "inactive"
    else:
        frequency_credit = min(frequency / 3, 1) * 60
        intensity_credit = 40 if 4 <= rpe <= 8 else 25 if rpe < 4 else 20
        workout_score = frequency_credit + intensity_credit
        workout_status = (
            "balanced_pattern"
            if 4 <= rpe <= 8
            else "recovery_review"
            if rpe > 8
            else "light_pattern"
        )

    rhr = data.get("resting_heart_rate")
    if rhr is None:
        cardio_score, cardio_status = 60, "limited_data"
    elif 50 <= rhr <= 80:
        cardio_score, cardio_status = 90, "within_configured_range"
    elif 40 <= rhr < 50 or 80 < rhr <= 95:
        cardio_score, cardio_status = 70, "review_range"
    else:
        cardio_score, cardio_status = 45, "outside_configured_range"

    nutrition_items: list[float] = []
    if data.get("calorie_target") and data.get("calorie_intake") is not None:
        ratio = data["calorie_intake"] / data["calorie_target"]
        nutrition_items.append(clamp(100 - abs(1 - ratio) * 100))
    if data.get("protein_target_g") and data.get("protein_intake_g") is not None:
        nutrition_items.append(clamp(data["protein_intake_g"] / data["protein_target_g"] * 100))
    if data.get("fruit_servings") is not None:
        nutrition_items.append(clamp(data["fruit_servings"] / 2 * 100))
    if data.get("vegetable_servings") is not None:
        nutrition_items.append(clamp(data["vegetable_servings"] / 3 * 100))
    if data.get("meal_consistency") is not None:
        nutrition_items.append(data["meal_consistency"] / 5 * 100)
    nutrition_score = (
        round(sum(nutrition_items) / len(nutrition_items), 1) if nutrition_items else 50
    )
    nutrition_status = (
        "good"
        if nutrition_score >= 80
        else "partial"
        if nutrition_score >= 60
        else "needs_attention"
    )

    present = sum(data.get(field) is not None for field in required_fields)
    completion = clamp(present / len(required_fields) * 100)
    components = [
        component(
            "hydration",
            hs,
            hstatus,
            {
                "actual_ml": data["hydration_ml"],
                "target_ml": target,
                "ratio": round(data["hydration_ml"] / target, 3),
            },
            f"Reported intake is {round(data['hydration_ml'] / target * 100)}% of the configured {target:.0f} ml target.",
        ),
        component(
            "sleep",
            ss,
            sstatus,
            {
                "hours": data["sleep_hours"],
                "quality": data["sleep_quality"],
                "wake_refreshed": data["wake_refreshed"],
                "recommended_range": [SLEEP_RANGES[goal][0], SLEEP_RANGES[goal][1]],
            },
            "Duration contributes 60%, quality 25%, and waking refreshed 15%.",
        ),
        component(
            "nutrition",
            nutrition_score,
            nutrition_status,
            {
                k: data.get(k)
                for k in (
                    "calorie_target",
                    "calorie_intake",
                    "protein_target_g",
                    "protein_intake_g",
                    "fruit_servings",
                    "vegetable_servings",
                    "meal_consistency",
                )
            },
            "Available nutrition compliance ratios are averaged; missing optional measures are shown and excluded.",
        ),
        component(
            "stress",
            stscore,
            ststatus,
            {"stress_level": data["stress_level"]},
            "Self-reported stress is inverted linearly from the 0–10 scale.",
        ),
        component(
            "cardiovascular",
            cardio_score,
            cardio_status,
            {"resting_heart_rate": rhr},
            "Resting heart rate is compared with configured reference bands; this is not a diagnosis.",
        ),
        component(
            "workout_intensity",
            workout_score,
            workout_status,
            {"frequency_weekly": frequency, "average_rpe": rpe},
            "Frequency contributes 60 points and reported intensity pattern contributes 40 points.",
        ),
        component(
            "physical_activity",
            activity_score,
            activity_status,
            {"minutes_weekly": minutes, "activity_types": data.get("activity_types", [])},
            "Weekly minutes are compared with the configured 150-minute baseline.",
        ),
        component(
            "daily_steps",
            dscore,
            dstatus,
            {"daily_steps": data["daily_steps"]},
            "Daily steps use fixed activity-band mappings.",
        ),
        component(
            "goal_alignment",
            100,
            "complete",
            {"selected_goal": goal},
            "A supported goal and sufficient baseline profile receive v1 completion credit.",
        ),
        component(
            "assessment_completion",
            completion,
            "complete" if completion == 100 else "incomplete",
            {"completed_required": present, "total_required": len(required_fields)},
            "Required onboarding field completion percentage.",
        ),
    ]
    total = round(sum(item.weighted_contribution for item in components), 1)
    missing = [
        key
        for key in (
            "resting_heart_rate",
            "calorie_target",
            "calorie_intake",
            "protein_target_g",
            "protein_intake_g",
            "fruit_servings",
            "vegetable_servings",
            "fiber_g",
            "meal_consistency",
        )
        if data.get(key) is None
    ]
    return {
        "overall_score": clamp(total),
        "band": interpretation_band(total),
        "scoring_version": SCORING_VERSION,
        "components": [asdict(item) for item in components],
        "missing_fields": missing,
    }


def interpretation_band(score: float) -> str:
    if score >= 90:
        return "Elite"
    if score >= 80:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 60:
        return "Average"
    if score >= 40:
        return "Needs Improvement"
    return "High Risk"
