"""Deterministic exercise search/ranking (pure engine, no DB)."""

from app.exercise_search import (
    SearchableExercise,
    expand_term,
    normalize,
    rank_exercises,
    score_query,
    tokenize,
)


def _ex(key, name, *, pattern=None, equipment=(), primary=(), secondary=(),
        category="strength", difficulty="beginner", description=None):
    return SearchableExercise(
        key=key, name=name, movement_pattern=pattern, equipment=tuple(equipment),
        primary_muscles=tuple(primary), secondary_muscles=tuple(secondary),
        category=category, difficulty=difficulty, description=description,
    )


LIBRARY = [
    _ex("goblet_squat", "Goblet Squat", pattern="squat", equipment=["dumbbell"],
        primary=["quadriceps", "glutes"], secondary=["core"]),
    _ex("back_squat", "Barbell Back Squat", pattern="squat", equipment=["barbell"],
        primary=["quadriceps", "glutes"], difficulty="intermediate"),
    _ex("walking_lunge", "Dumbbell Walking Lunge", pattern="lunge",
        equipment=["dumbbell"], primary=["quadriceps", "glutes"],
        secondary=["hamstrings"]),
    _ex("rdl", "Barbell Romanian Deadlift", pattern="hinge", equipment=["barbell"],
        primary=["hamstrings", "glutes"], secondary=["lower back"]),
    _ex("db_rdl", "Dumbbell Romanian Deadlift", pattern="hinge", equipment=["dumbbell"],
        primary=["hamstrings", "glutes"]),
    _ex("pullup", "Pull-Up", pattern="vertical pull", equipment=["pull-up station"],
        primary=["lats"], secondary=["biceps"]),
    _ex("bb_row", "Barbell Row", pattern="horizontal pull", equipment=["barbell"],
        primary=["back"], secondary=["biceps", "lats"]),
    _ex("db_bench", "Dumbbell Bench Press", pattern="horizontal push",
        equipment=["dumbbell", "bench"], primary=["chest"],
        secondary=["triceps", "shoulders"]),
    _ex("pushup", "Push-Up", pattern="horizontal push", equipment=[],
        primary=["chest"], secondary=["triceps", "core"]),
]


def _keys(query=None, **facets):
    return [sx.key for sx in rank_exercises(LIBRARY, query=query, **facets)]


# --- normalization / tokenization ---


def test_normalize_folds_case_and_hyphens():
    assert normalize("Pull-Up") == "pull up"
    assert normalize("  DUMBBELL   Row ") == "dumbbell row"


def test_tokenize_keeps_known_phrases():
    assert tokenize("dumbbell hip flexors") == ["hip flexors", "dumbbell"]
    assert tokenize("resistance band row") == ["resistance band", "row"]


# --- the core requirement: "quads" works ---


def test_quads_returns_every_quadriceps_exercise():
    keys = set(_keys("quads"))
    assert keys == {"goblet_squat", "back_squat", "walking_lunge"}


def test_quad_singular_and_full_name_are_equivalent():
    assert set(_keys("quad")) == set(_keys("quads")) == set(_keys("quadriceps"))


def test_dumbbell_quads_returns_the_intersection():
    # Only exercises that are BOTH dumbbell AND quads.
    assert set(_keys("dumbbell quads")) == {"goblet_squat", "walking_lunge"}


def test_hamstrings_ranks_primary_above_secondary():
    keys = _keys("hamstrings")
    assert set(keys) == {"rdl", "db_rdl", "walking_lunge"}
    # walking_lunge only has hamstrings as a secondary mover, so it ranks last.
    assert keys[-1] == "walking_lunge"


def test_pull_matches_pulling_patterns_not_pushes():
    keys = set(_keys("pull"))
    assert keys == {"pullup", "bb_row"}
    assert "pushup" not in keys and "db_bench" not in keys


def test_muscle_synonyms_map_to_canonical_vocabulary():
    assert set(_keys("pecs")) == {"db_bench", "pushup"}
    assert set(_keys("delts")) == {"db_bench"}  # shoulders only appear on the bench press
    assert set(_keys("glutes")) >= {"goblet_squat", "rdl"}


def test_equipment_synonyms():
    assert set(_keys("db bench")) == {"db_bench"}
    assert "back_squat" in set(_keys("bb squat"))


# --- ranking order ---


def test_exact_name_ranks_first():
    ranked = rank_exercises(LIBRARY, query="Goblet Squat")
    assert ranked[0].key == "goblet_squat"
    assert score_query(LIBRARY[0], "Goblet Squat") == 1000


def test_name_prefix_beats_metadata_match():
    ranked = _keys("pull")
    assert ranked[0] == "pullup"  # name-prefix (820) over bb_row's pattern match


# --- facet filters (compose) ---


def test_muscle_facet_filters():
    assert set(_keys(muscle="glutes")) == {
        "goblet_squat", "back_squat", "walking_lunge", "rdl", "db_rdl",
    }


def test_back_facet_is_broad_but_truthful():
    # "back" broadly covers lats/upper back/lower back, so the pulls qualify and the
    # RDL qualifies too (its secondary mover is the lower back) — broad stays broad.
    assert set(_keys(muscle="back")) == {"pullup", "bb_row", "rdl"}


def test_bodyweight_equipment_facet_matches_empty_equipment():
    assert _keys(equipment="bodyweight") == ["pushup"]


def test_movement_pattern_facet():
    assert set(_keys(movement_pattern="hinge")) == {"rdl", "db_rdl"}


def test_difficulty_facet():
    assert _keys(difficulty="intermediate") == ["back_squat"]


def test_facets_compose_with_query():
    # quads, dumbbell only -> intersection again, via a facet this time.
    assert set(_keys("quads", equipment="dumbbell")) == {"goblet_squat", "walking_lunge"}


# --- edges ---


def test_empty_query_and_no_facets_preserves_input_order():
    assert [sx.key for sx in rank_exercises(LIBRARY)] == [sx.key for sx in LIBRARY]


def test_unknown_term_falls_back_to_substring_then_nothing():
    assert _keys("romanian") == ["rdl", "db_rdl"]  # substring/name-token of the name
    assert _keys("zercher") == []  # matches no field -> excluded, not an error


def test_expand_term_is_deterministic_and_reviewed():
    assert expand_term("quads").muscles == frozenset({"quadriceps"})
    assert expand_term("push").patterns == frozenset({"horizontal push", "vertical push"})
    assert expand_term("bw").bodyweight is True
