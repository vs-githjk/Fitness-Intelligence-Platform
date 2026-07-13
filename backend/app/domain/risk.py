from datetime import UTC, datetime
from typing import Any

from app.domain.scoring import hydration_target_ml

RULE_VERSION = "onboarding-risk-v1"


def flag(
    key: str, severity: str, title: str, explanation: str, action: str, inputs: dict[str, Any]
) -> dict[str, Any]:
    return {
        "rule_key": key,
        "severity": severity,
        "status": "open",
        "title": title,
        "explanation": explanation,
        "recommended_action": action,
        "triggering_inputs": inputs,
        "rule_version": RULE_VERSION,
        "triggered_at": datetime.now(UTC),
    }


def evaluate_risks(data: dict[str, Any]) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    if data["sleep_hours"] < 5:
        flags.append(
            flag(
                "sleep_below_5h",
                "review",
                "Very short reported sleep",
                "Reported average sleep is below the configured five-hour threshold.",
                "Review sleep and recovery habits with your coach; consider qualified professional guidance if this persists.",
                {"sleep_hours": data["sleep_hours"]},
            )
        )
    if data["stress_level"] >= 9:
        flags.append(
            flag(
                "stress_9_plus",
                "elevated",
                "Very high reported stress",
                "Self-reported stress meets the configured review threshold.",
                "Reduce training demands where appropriate and consider support from a qualified professional.",
                {"stress_level": data["stress_level"]},
            )
        )
    symptom_action = "Seek immediate professional medical help if symptoms are severe, worsening, or happening now."
    for field, title in (
        ("chest_pain", "Chest discomfort reported"),
        ("shortness_of_breath", "Breathing difficulty reported"),
    ):
        if data.get(field):
            flags.append(
                flag(
                    f"reported_{field}",
                    "urgent",
                    title,
                    f"The onboarding response reports {title.lower()}. This flag is not a diagnosis.",
                    symptom_action,
                    {field: True},
                )
            )
    if data.get("palpitations"):
        flags.append(
            flag(
                "reported_palpitations",
                "elevated",
                "Palpitations reported",
                "The onboarding response reports palpitations; this is not a diagnosis.",
                "Pause and discuss this response with a qualified healthcare professional before intense exercise.",
                {"palpitations": True},
            )
        )
    rhr = data.get("resting_heart_rate")
    if rhr is not None and rhr > 95:
        flags.append(
            flag(
                "resting_hr_above_95",
                "review",
                "Resting heart rate outside configured range",
                "Reported resting heart rate is above the configured 95 bpm review threshold.",
                "Recheck under consistent resting conditions and discuss persistent readings with a qualified professional.",
                {"resting_heart_rate": rhr, "threshold": 95},
            )
        )
    target = hydration_target_ml(data["weight_kg"], data["selected_goal"])
    if data["hydration_ml"] / target < 0.5:
        flags.append(
            flag(
                "hydration_below_50_percent",
                "review",
                "Low reported hydration",
                "Reported hydration is below 50% of the configured weight-and-goal target.",
                "Increase gradually toward the configured target; do not force excessive intake.",
                {"actual_ml": data["hydration_ml"], "target_ml": target},
            )
        )
    if (
        data.get("calorie_target")
        and data.get("calorie_intake") is not None
        and data["calorie_intake"] / data["calorie_target"] < 0.5
    ):
        flags.append(
            flag(
                "calorie_below_50_percent",
                "elevated",
                "Very low reported calorie intake",
                "Reported intake is below 50% of the entered target.",
                "Review the entries and discuss adequate fueling with a qualified coach or nutrition professional.",
                {
                    "calorie_intake": data["calorie_intake"],
                    "calorie_target": data["calorie_target"],
                },
            )
        )
    if (
        data.get("protein_intake_g") is not None
        and data["protein_intake_g"] < 0.8 * data["weight_kg"]
    ):
        flags.append(
            flag(
                "protein_below_0_8_g_kg",
                "informational",
                "Protein below configured baseline",
                "Reported protein is below the configured 0.8 g/kg baseline.",
                "Review protein intake and individual needs with an appropriate professional.",
                {
                    "protein_intake_g": data["protein_intake_g"],
                    "baseline_g": round(0.8 * data["weight_kg"], 1),
                },
            )
        )
    return flags
