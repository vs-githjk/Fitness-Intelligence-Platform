# Health Index v1

Version identifier: `health-index-v1`. Risk rule version: `onboarding-risk-v1`. Assessment schema: `onboarding-v1`.

This score is a configurable coaching interpretation, not a medical diagnosis. Given the same validated inputs and version, calculation is deterministic. Each snapshot stores raw inputs, normalized score, weight, weighted contribution, status/explanation, missing optional fields, triggered rules, and recommendations.

## Overall formula

Each component is normalized to `[0, 100]`. Values are rounded to one decimal; weighted contributions are rounded to two decimals.

```text
weighted contribution = normalized score × component weight / 100
overall score = clamp(round(sum(weighted contributions), 1), 0, 100)
```

| Component | Weight |
|---|---:|
| Hydration | 10 |
| Sleep | 15 |
| Nutrition | 15 |
| Stress | 10 |
| Cardiovascular | 10 |
| Workout intensity | 10 |
| Physical activity | 10 |
| Daily steps | 10 |
| Goal alignment | 5 |
| Assessment completion | 5 |
| **Total** | **100** |

Bands: `90–100 Elite`, `80–89.9 Excellent`, `70–79.9 Good`, `60–69.9 Average`, `40–59.9 Needs Improvement`, and below 40 `High Risk`. These are product labels, not diagnoses.

## Component rules

### Hydration

Target is body weight multiplied by: general health `35 ml/kg`, fat loss `40`, muscle gain `45`, strength `40`, endurance `50`, or athletic performance `45`.

```text
ratio = actual daily ml / target ml
score = clamp(ratio × 100)
```

Status is `high` below 60%, `moderate` from 60% to below 80%, `good` from 80% to below 100%, and `excellent` at or above 100%. Credit is capped; recommendations warn against forcing excessive intake.

### Sleep

Goal ranges in hours: fat loss `7.5–9`, muscle gain `8–9`, strength `7.5–8.5`, endurance `8–10`, general health `7–9`, athletic performance `8–10`.

Within the range, duration is 100. Below it, `hours / lower bound × 100`. Above it, subtract `12.5` points for every hour above the upper bound. Duration is clamped. Final score is `60% duration + 25% quality/5 + 15% wake-refreshed`, where wake-refreshed is 100 for yes and 40 for no.

### Nutrition

Available values are averaged; optional missing values are excluded:

- calorie compliance: `100 - abs(1 - intake/entered target) × 100`, clamped;
- protein compliance: `intake/entered target × 100`, clamped;
- fruit: `servings/2 × 100`, clamped;
- vegetables: `servings/3 × 100`, clamped;
- consistency: `rating/5 × 100`.

If none is available the explicit v1 limited-data score is 50. The application does not create a calorie prescription.

### Stress

`score = clamp(100 - self-reported stress × 10)`. Status: 0–3 low, 4–6 moderate, 7–8 high, 9–10 very high.

### Cardiovascular

With no resting heart rate, score 60 and `limited_data`. A reported 50–80 bpm scores 90; 40–49 or 81–95 scores 70; other validated values score 45. Symptoms do not alter this component silently: they become separate risk flags. Reference ranges are not clinical classifications.

### Workout intensity

Zero weekly sessions scores 30. Otherwise frequency supplies up to 60 points (`min(frequency/3, 1) × 60`). Average RPE 4–8 supplies 40 points, below 4 supplies 25, and above 8 supplies 20 with a `recovery_review` status. This describes a reported training-load pattern; it does not detect clinical overtraining.

### Physical activity

`score = clamp(weekly activity minutes / 150 × 100)`. Activity names are retained for explanation, but do not change credit.

### Daily steps

| Steps | Score | Status |
|---:|---:|---|
| `<5,000` | 35 | Sedentary |
| `5,000–7,499` | 55 | Low Active |
| `7,500–9,999` | 75 | Somewhat Active |
| `10,000–12,499` | 90 | Active |
| `≥12,500` | 100 | Highly Active |

### Goal alignment and completion

A supported goal with the required baseline profile receives 100 v1 goal-alignment credit. Progress/outcome alignment is deferred. Assessment completion is `present required fields / 14 × 100`; submission requires all 14, so submitted baselines receive 100.

## Missing data

Required data prevents submission when absent. Optional resting heart rate and nutrition fields are returned in `missing_fields`. They are never fabricated. Limited-data defaults are explicit in component inputs and explanations.

## Onboarding risk rules

| Rule | Trigger | Severity |
|---|---|---|
| `sleep_below_5h` | sleep `<5 h` | review |
| `stress_9_plus` | stress `≥9` | elevated |
| `reported_palpitations` | reported true | elevated |
| `reported_chest_pain` | reported true | urgent |
| `reported_shortness_of_breath` | reported true | urgent |
| `resting_hr_above_95` | RHR `>95 bpm` | review |
| `hydration_below_50_percent` | ratio `<0.5` | review |
| `calorie_below_50_percent` | intake/entered target `<0.5` | elevated |
| `protein_below_0_8_g_kg` | intake `<0.8 g/kg` | informational |

“Urgent” is reserved for reported chest discomfort or breathing difficulty and advises immediate professional medical help if severe, worsening, or current. Alerts say explicitly that they are not diagnoses. Longitudinal rules—no activity for seven days and RPE above threshold for five consecutive days—are deferred until daily data exists.

## Recommendation templates

V1 creates structured templates for hydration gap in milliliters, sleep consistency, steps needed for the next band, and each risk-rule action. An isolated `RecommendationNarrator` protocol permits future language narration without allowing AI to change data, rules, or prescriptions.

## Versioning

Any formula, threshold, weight, band, or material explanation change requires a new immutable identifier (for example `health-index-v2`). Existing snapshots keep their original payload/version. Recalculation under a new version should create a new snapshot, never overwrite history.
