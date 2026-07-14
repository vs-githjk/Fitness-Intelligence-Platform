from typing import Any


def build_daily_recommendations(
    score: dict[str, Any], risks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    components = {item["key"]: item for item in score["components"]}
    results: list[dict[str, Any]] = []
    hydration = components.get("hydration_compliance")
    if hydration and not hydration["missing"] and hydration["normalized_score"] < 100:
        actual = hydration["raw_inputs"]["actual_liters"]
        target = hydration["raw_inputs"]["target_liters"]
        gap = round(max(0.0, target - actual), 1)
        results.append(
            {
                "key": "daily_hydration_gap",
                "category": "hydration",
                "priority": "medium",
                "trigger": "hydration_below_stored_target",
                "recommended_action": f"Consider gradually adding up to {gap:.1f} L across the rest of the day to approach the configured target.",
                "supporting_calculation": {
                    "actual_liters": actual,
                    "target_liters": target,
                    "gap_liters": gap,
                },
                "safety_text": "Do not force excessive water intake; individual needs vary.",
            }
        )
    sleep = components["sleep_duration"]
    if sleep["normalized_score"] < 80:
        results.append(
            {
                "key": "daily_sleep_opportunity",
                "category": "recovery",
                "priority": "high",
                "trigger": "sleep_duration_score_below_80",
                "recommended_action": "Prioritize an earlier or more consistent sleep opportunity tonight where practical.",
                "supporting_calculation": sleep["raw_inputs"],
                "safety_text": None,
            }
        )
    if score["readiness_state"] in {"reduce_intensity", "recovery_recommended"}:
        results.append(
            {
                "key": "adjust_training_intensity",
                "category": "training",
                "priority": "high",
                "trigger": score["readiness_state"],
                "recommended_action": "Consider a lower-intensity session or active recovery today and review the contributing metrics.",
                "supporting_calculation": {
                    "readiness_score": score["readiness_score"],
                    "recovery_score": score["recovery_score"],
                    "seven_day_load": score["recent_training_load"]["total"],
                },
                "safety_text": "Readiness is coaching guidance, not medical clearance or injury prediction.",
            }
        )
    steps = components["steps"]
    current_steps = steps["raw_inputs"]["steps"]
    if current_steps < 10000:
        next_band = 5000 if current_steps < 5000 else 7500 if current_steps < 7500 else 10000
        results.append(
            {
                "key": "daily_next_step_band",
                "category": "activity",
                "priority": "low",
                "trigger": "below_active_step_band",
                "recommended_action": f"If appropriate, a short walk could add about {next_band - current_steps:,} steps toward the next activity band.",
                "supporting_calculation": {
                    "current_steps": current_steps,
                    "next_band": next_band,
                },
                "safety_text": "Increase activity gradually and stop if concerning symptoms occur.",
            }
        )
    for risk in risks:
        results.append(
            {
                "key": f"daily_review_{risk['rule_key']}",
                "category": "safety",
                "priority": "high" if risk["severity"] == "elevated" else "medium",
                "trigger": risk["rule_key"],
                "recommended_action": risk["recommended_action"],
                "supporting_calculation": risk["triggering_inputs"],
                "safety_text": "This pattern is not a diagnosis or medical assessment.",
            }
        )
    return results[:6]
