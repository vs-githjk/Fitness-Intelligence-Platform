# Daily Intelligence v1

`daily-intelligence-v1` is a deterministic, versioned product-scoring system for self-reported daily check-ins. It does not replace or modify `health-index-v1`. It is coaching guidance, not medical clearance, diagnosis, injury prediction, or an overtraining model.

All scores are clamped to 0–100. Components and aggregates are rounded to one decimal; contributions are rounded to two decimals. UTC timestamps record events, while the trainee's validated IANA timezone determines and permanently stores the local calendar date.

## Data completeness

Sleep, recovery, activity, water-intake, and overall-feeling inputs are required. Calories, protein intake, and nutrition-plan adherence are optional. Exercise duration and session RPE are required only when exercise is reported. The form saves atomically; there are no drafts. Today's record can be edited and rescored idempotently. Past dates are read-only.

No baseline or synthetic value is substituted for a missing daily response. Optional nutrition components are excluded and remaining weights are normalized to 100%. If no valid nutrition component exists, Daily Nutrition is unavailable rather than zero.

## Recovery Score

| Component | Weight | Mapping |
|---|---:|---|
| Sleep duration | 30% | 100 inside the baseline goal range; below range = `hours / lower bound × 100`; above range loses 12.5 points per excess hour |
| Sleep quality | 15% | `quality / 5 × 100` |
| Wake refreshed | 10% | Yes = 100; No = 40 |
| Fatigue | 15% | `100 − fatigue × 10` |
| Soreness | 15% | `100 − soreness × 10` |
| Stress | 15% | `100 − stress × 10` |

Goal sleep ranges reuse `health-index-v1`. Without a submitted goal, the general-health 7–9-hour range is used. This is a scoring configuration, not a medical sleep prescription.

## Activity Score

| Component | Weight | Mapping |
|---|---:|---|
| Steps | 50% | Existing bands: below 5,000 = 35; 5,000–7,499 = 55; 7,500–9,999 = 75; 10,000–12,499 = 90; 12,500+ = 100 |
| Exercise duration | 25% | `min(minutes, 60) / 60 × 100` |
| Participation and mix | 25% | No session = 30; session = 70 plus 10 for each of up to three activity types |

Duration credit stops at 60 minutes. Activity types add context and are not ranked, so the score does not imply that unlimited volume is better.

## Daily Nutrition Score

Base weights are hydration 50%, protein 30%, and self-reported adherence 20%. Available weights are normalized to 100%.

- Hydration: `water liters / stored baseline-derived target liters × 100`, capped at 100.
- Protein: `protein grams / stored baseline protein target × 100`, capped at 100. Both values must exist.
- Adherence: the optional reported 0–100 percentage is used directly.
- Calories are stored for context but do not affect v1 because no formal daily meal plan exists.

Unavailable targets are explicit in `missing_fields` and explanations. No target is invented.

## Training Readiness

Daily training load is `exercise minutes × session RPE`; no session produces zero load. The seven-day signal sums records on the current local date and previous six calendar dates. Missing days do not create fabricated records.

```text
load tolerance = 100                              when seven-day load <= 1,200 AU
load tolerance = 100 - (load - 1,200) / 20        above 1,200 AU, clamped to 0–100

readiness = Recovery Score × 70% + load tolerance × 30%
```

States are exact:

- 80–100: Ready to push
- 60–79.9: Maintain
- 40–59.9: Reduce intensity
- Below 40: Recovery recommended

## Longitudinal alert rules

`daily-risk-v1` evaluates patterns ending on the latest stored local date. Consecutive means adjacent stored calendar dates; a missing date breaks the sequence.

- Latest sleep below 5 hours
- Latest stress 9 or above
- Sleep below 6 hours for three consecutive check-ins
- Stress, fatigue, or soreness 8 or above for three consecutive check-ins
- Session RPE 9 or above on five consecutive calendar dates, with exercise reported on each date
- Seven-day load above 1,800 AU combined with Recovery below 50
- Hydration below 50% of a valid target for three consecutive check-ins
- Protein below 80% of a valid target for three consecutive check-ins
- Eight consecutive check-ins with no exercise and fewer than 5,000 steps
- Recovery at least 20 points below the preceding three-record average

Every alert stores its rule/version, severity, triggering dates and values, explanation, action, UTC creation time, status, and resolution time. An open rule points to the latest triggering snapshot and resolves when it no longer triggers. Language avoids diagnosing dehydration, injury, illness, or overtraining.

## Trends and versioning

Trend endpoints support bounded 7-, 14-, or 30-day periods. Each local date has a nullable value, explicit missing status, rolling average over the last seven recorded values, and difference from the previous recorded value. Missing dates remain gaps, never zero. Percentage changes are not calculated.

Snapshots retain the version, normalized components, contributions, missing fields, load payload, recommendations, and calculation time. Formula changes require a new version. The original Baseline Health Index remains immutable.
