"""Pure workout-import parsing, matching, and prescription mapping (no DB)."""

from app.exercise_search import SearchableExercise
from app.workout_import import (
    MATCHED,
    NEEDS_REVIEW,
    NOT_FOUND,
    ImportRow,
    match_exercise,
    parse_csv,
    prescription_for,
)


def _sx(key, name):
    return SearchableExercise(key=key, name=name)


CATALOG = [
    _sx("goblet", "Goblet squat"),
    _sx("bench", "Barbell bench press"),
    _sx("db_bench", "Dumbbell bench press"),
    _sx("plank", "Forearm plank"),
]


# --- parsing ---


def test_parse_reps_range_load_and_rest():
    parsed = parse_csv("exercise,sets,reps,load,rest\nGoblet squat,3,8-10,20kg,90")
    assert parsed.errors == []
    row = parsed.rows[0]
    assert row.exercise_name == "Goblet squat"
    assert row.sets == 3
    assert (row.reps_min, row.reps_max) == (8, 10)
    assert row.load == "20" and row.load_unit == "kg"
    assert row.rest_seconds == 90


def test_parse_header_aliases_and_single_rep_and_time_formats():
    parsed = parse_csv("name,weight,reps,duration\nPlank,,,1:30")
    row = parsed.rows[0]
    assert row.exercise_name == "Plank"
    assert row.duration_seconds == 90


def test_missing_exercise_column_is_a_friendly_file_error():
    parsed = parse_csv("sets,reps\n3,10")
    assert parsed.rows == []
    assert any("exercise" in e for e in parsed.errors)


def test_blank_exercise_name_is_a_row_error_not_a_crash():
    parsed = parse_csv("exercise,sets\n,3\nGoblet squat,3")
    assert parsed.rows[0].error is not None and parsed.rows[0].line == 1
    assert parsed.rows[1].exercise_name == "Goblet squat"


def test_row_and_size_limits():
    big = "exercise\n" + "\n".join(f"Ex {i}" for i in range(300))
    assert any("too many rows" in e for e in parse_csv(big).errors)
    assert any("too large" in e for e in parse_csv("exercise\n" + "x" * 600_000).errors)


# --- matching (deterministic, conservative) ---


def test_exact_name_is_matched():
    result = match_exercise("goblet squat", CATALOG)
    assert result.status == MATCHED and result.exercise_id == "goblet"


def test_ambiguous_name_needs_review_with_candidates():
    # "bench press" is not an exact name of either bench row -> the coach chooses.
    result = match_exercise("bench press", CATALOG)
    assert result.status == NEEDS_REVIEW
    assert set(result.candidates) >= {"bench", "db_bench"}


def test_unknown_name_is_not_found():
    assert match_exercise("zercher carry", CATALOG).status == NOT_FOUND


# --- prescription mapping per tracking mode ---


def test_prescription_reps_and_load():
    row = ImportRow(line=1, exercise_name="x", sets=3, reps_min=8, reps_max=10,
                    load="40", load_unit="kg", rest_seconds=90)
    p = prescription_for(row, "repetitions_and_load")
    assert p["repetitions_min"] == 8 and p["repetitions_max"] == 10
    assert p["target_load_original_value"] == "40" and p["target_load_original_unit"] == "kg"
    assert p["rest_seconds"] == 90


def test_prescription_duration_ignores_reps_and_load():
    row = ImportRow(line=1, exercise_name="x", sets=1, reps_min=8, reps_max=10,
                    load="40", duration_seconds=45)
    p = prescription_for(row, "duration")
    assert p == {"target_duration_seconds": 45}


def test_prescription_distance_and_duration():
    row = ImportRow(line=1, exercise_name="x", sets=1, duration_seconds=600,
                    distance="3.0", distance_unit="kilometers")
    p = prescription_for(row, "distance_and_duration")
    assert p["target_duration_seconds"] == 600
    assert p["target_distance_value"] == "3.0" and p["target_distance_unit"] == "kilometers"
