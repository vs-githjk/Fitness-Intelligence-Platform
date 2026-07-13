from typing import Any, Protocol


class RecommendationNarrator(Protocol):
    def narrate(self, structured_recommendations: list[dict[str, Any]]) -> list[str]: ...


class TemplateRecommendationNarrator:
    def narrate(self, structured_recommendations: list[dict[str, Any]]) -> list[str]:
        return [item["recommended_action"] for item in structured_recommendations]


def build_recommendations(
    score: dict[str, Any], risks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    by_key = {item["key"]: item for item in score["components"]}
    results: list[dict[str, Any]] = []
    hydration = by_key["hydration"]
    if hydration["normalized_score"] < 100:
        actual, target = hydration["raw_inputs"]["actual_ml"], hydration["raw_inputs"]["target_ml"]
        results.append(
            {
                "key": "close_hydration_gap",
                "category": "hydration",
                "priority": "medium",
                "trigger": "hydration_below_target",
                "recommended_action": f"Consider gradually adding up to {max(0, round(target - actual))} ml across the day to approach the configured target.",
                "supporting_calculation": {
                    "actual_ml": actual,
                    "target_ml": target,
                    "gap_ml": max(0, round(target - actual)),
                },
                "safety_text": "Do not force excessive water intake; individual needs vary.",
            }
        )
    sleep = by_key["sleep"]
    if sleep["normalized_score"] < 80:
        results.append(
            {
                "key": "sleep_consistency",
                "category": "sleep",
                "priority": "high",
                "trigger": "sleep_score_below_80",
                "recommended_action": "Aim for a more consistent sleep window within the configured range and review barriers with your coach.",
                "supporting_calculation": sleep["raw_inputs"],
                "safety_text": None,
            }
        )
    steps = by_key["daily_steps"]
    if steps["raw_inputs"]["daily_steps"] < 10000:
        current = steps["raw_inputs"]["daily_steps"]
        next_target = 5000 if current < 5000 else 7500 if current < 7500 else 10000
        results.append(
            {
                "key": "next_steps_band",
                "category": "activity",
                "priority": "medium",
                "trigger": "below_active_steps_band",
                "recommended_action": f"If appropriate for you, add about {next_target - current:,} daily steps to reach the next activity band.",
                "supporting_calculation": {"current_steps": current, "next_band": next_target},
                "safety_text": "Increase activity gradually and stop if concerning symptoms occur.",
            }
        )
    for risk in risks:
        results.append(
            {
                "key": f"review_{risk['rule_key']}",
                "category": "safety",
                "priority": "high" if risk["severity"] in ("elevated", "urgent") else "medium",
                "trigger": risk["rule_key"],
                "recommended_action": risk["recommended_action"],
                "supporting_calculation": risk["triggering_inputs"],
                "safety_text": "This platform does not provide a medical diagnosis.",
            }
        )
    return results[:6]
