"""Deterministic, synonym-aware exercise search and ranking.

Pure and framework-free (no DB, no FastAPI) so it is unit-testable in isolation and
carries no ownership/authorization logic — visibility is enforced upstream by the
repository. Coaches should be able to type ``quads`` and reliably find every exercise
whose real metadata involves the quadriceps, ``dumbbell quads`` to get the intersection,
or ``pull`` to get pulling movements, without learning a query syntax (Coach Ease).

The matching is entirely deterministic: a reviewed synonym layer maps colloquial terms to
the canonical vocabulary the library actually uses, and an explicit ranking orders results
(exact name > name prefix > name tokens > primary muscle > secondary muscle > movement
pattern > equipment > category/difficulty > substring). No anatomical guessing beyond the
reviewed relationships below; unknown terms fall back to substring matching over the name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# --- normalization ---------------------------------------------------------------------

_WS = re.compile(r"\s+")


def normalize(value: str | None) -> str:
    """Lowercase, fold hyphens/underscores to spaces, and collapse whitespace."""
    if not value:
        return ""
    return _WS.sub(" ", value.lower().replace("-", " ").replace("_", " ")).strip()


# --- reviewed synonym vocabulary -------------------------------------------------------
# Aliases map a colloquial term to a single canonical string used in exercise metadata.
# Groups expand a broad term to every canonical string it truthfully covers (a broad
# request stays broad — it is not narrowed to a single precise claim).

_MUSCLE_ALIASES: dict[str, str] = {
    "quad": "quadriceps", "quads": "quadriceps", "quadricep": "quadriceps",
    "quadriceps": "quadriceps", "thigh": "quadriceps", "thighs": "quadriceps",
    "ham": "hamstrings", "hams": "hamstrings", "hamstring": "hamstrings",
    "hamstrings": "hamstrings",
    "glute": "glutes", "glutes": "glutes", "gluteal": "glutes", "butt": "glutes",
    "booty": "glutes",
    "calf": "calves", "calves": "calves",
    "chest": "chest", "pec": "chest", "pecs": "chest", "pectoral": "chest",
    "pectorals": "chest",
    "lat": "lats", "lats": "lats", "latissimus": "lats",
    "trap": "traps", "traps": "traps", "trapezius": "traps",
    "upper back": "upper back", "rhomboid": "upper back", "rhomboids": "upper back",
    "rear delt": "upper back", "rear delts": "upper back",
    "shoulder": "shoulders", "shoulders": "shoulders", "delt": "shoulders",
    "delts": "shoulders", "deltoid": "shoulders", "deltoids": "shoulders",
    "bicep": "biceps", "biceps": "biceps", "bis": "biceps",
    "tricep": "triceps", "triceps": "triceps", "tris": "triceps",
    "core": "core", "ab": "core", "abs": "core", "abdominal": "core",
    "abdominals": "core",
    "oblique": "obliques", "obliques": "obliques",
    "forearm": "forearms", "forearms": "forearms", "grip": "forearms",
    "hip flexor": "hip flexors", "hip flexors": "hip flexors",
    "adductor": "adductors", "adductors": "adductors", "inner thigh": "adductors",
    "lower back": "lower back", "erector": "lower back", "erectors": "lower back",
    "spinal erectors": "lower back",
}

_MUSCLE_GROUPS: dict[str, tuple[str, ...]] = {
    "back": ("back", "lats", "upper back", "lower back", "traps"),
    "legs": ("quadriceps", "hamstrings", "glutes", "calves", "hip flexors", "adductors"),
    "lower body": ("quadriceps", "hamstrings", "glutes", "calves", "hip flexors",
                   "adductors"),
    "arms": ("biceps", "triceps", "forearms"),
    "upper body": ("chest", "back", "lats", "upper back", "shoulders", "biceps",
                   "triceps", "forearms", "traps"),
    "posterior chain": ("hamstrings", "glutes", "lower back", "back"),
}

_EQUIPMENT_ALIASES: dict[str, str] = {
    "dumbbell": "dumbbell", "dumbbells": "dumbbell", "dumbell": "dumbbell",
    "db": "dumbbell",
    "barbell": "barbell", "bb": "barbell", "ez bar": "barbell", "ez-bar": "barbell",
    "kettlebell": "kettlebell", "kettlebells": "kettlebell", "kb": "kettlebell",
    "kettle bell": "kettlebell",
    "cable": "cable", "cables": "cable", "cable machine": "cable",
    "machine": "machine",
    "band": "resistance band", "bands": "resistance band",
    "resistance band": "resistance band", "resistance bands": "resistance band",
    "bench": "bench",
    "pull up station": "pull-up station", "pull-up station": "pull-up station",
    "pullup": "pull-up station", "pull up": "pull-up station",
    "pull-up bar": "pull-up station", "chin up": "pull-up station",
    "chinup": "pull-up station", "pull up bar": "pull-up station",
    "dip station": "dip station", "dip": "dip station", "dips": "dip station",
    "box": "box", "plyo box": "box",
    "medicine ball": "medicine ball", "med ball": "medicine ball",
    "smith machine": "smith machine",
    "treadmill": "treadmill",
    "stationary bike": "stationary bike", "bike": "stationary bike",
    "rowing machine": "rowing machine", "rower": "rowing machine",
    "exercise mat": "exercise mat", "mat": "exercise mat", "squat rack": "squat rack",
    "rack": "squat rack",
}
# The empty-equipment (bodyweight) request is matched specially against `equipment == []`.
_BODYWEIGHT_TERMS = frozenset({"bodyweight", "body weight", "bw", "no equipment", "none"})

_PATTERN_GROUPS: dict[str, tuple[str, ...]] = {
    "push": ("horizontal push", "vertical push"),
    "press": ("horizontal push", "vertical push"),
    "pull": ("horizontal pull", "vertical pull"),
    "row": ("horizontal pull",),
    "squat": ("squat",),
    "hinge": ("hinge",),
    "lunge": ("lunge",),
    "carry": ("carry",),
    "rotation": ("rotation", "anti-rotation"),
    "anti rotation": ("anti-rotation",),
    "isometric": ("isometric",),
}

# Multi-word phrases recognized as a single token before whitespace splitting.
_PHRASES: tuple[str, ...] = tuple(sorted(
    {
        p for p in (
            *(_k for _k in _MUSCLE_ALIASES if " " in _k),
            *(_k for _k in _MUSCLE_GROUPS if " " in _k),
            *(_k for _k in _EQUIPMENT_ALIASES if " " in _k),
            *(_k for _k in _PATTERN_GROUPS if " " in _k),
            *(_t for _t in _BODYWEIGHT_TERMS if " " in _t),
        )
    },
    key=len,
    reverse=True,
))


@dataclass(frozen=True)
class ExpandedTerm:
    raw: str
    muscles: frozenset[str]
    equipment: frozenset[str]
    patterns: frozenset[str]
    bodyweight: bool


def expand_term(term: str) -> ExpandedTerm:
    """Expand one normalized term into the canonical muscles/equipment/patterns it names."""
    muscles: set[str] = set()
    if term in _MUSCLE_ALIASES:
        muscles.add(_MUSCLE_ALIASES[term])
    if term in _MUSCLE_GROUPS:
        muscles.update(_MUSCLE_GROUPS[term])
    equipment: set[str] = set()
    if term in _EQUIPMENT_ALIASES:
        equipment.add(_EQUIPMENT_ALIASES[term])
    patterns: set[str] = set()
    if term in _PATTERN_GROUPS:
        patterns.update(_PATTERN_GROUPS[term])
    return ExpandedTerm(
        raw=term,
        muscles=frozenset(muscles),
        equipment=frozenset(equipment),
        patterns=frozenset(patterns),
        bodyweight=term in _BODYWEIGHT_TERMS,
    )


def tokenize(raw: str) -> list[str]:
    """Split a normalized query into terms, keeping known multi-word phrases intact."""
    remaining = f" {normalize(raw)} "
    tokens: list[str] = []
    for phrase in _PHRASES:
        pad = f" {phrase} "
        while pad in remaining:
            remaining = remaining.replace(pad, " ", 1)
            tokens.append(phrase)
    tokens.extend(w for w in remaining.split() if w)
    return tokens


@dataclass(frozen=True)
class SearchableExercise:
    """The searchable projection of an exercise's representative version."""

    key: str
    name: str
    description: str | None = None
    category: str | None = None
    movement_pattern: str | None = None
    difficulty: str | None = None
    tracking_mode: str | None = None
    equipment: tuple[str, ...] = ()
    primary_muscles: tuple[str, ...] = ()
    secondary_muscles: tuple[str, ...] = ()
    # Precomputed normalized forms, filled in __post_init__ (kept private).
    _name: str = field(default="", compare=False)
    _equipment: frozenset[str] = field(default=frozenset(), compare=False)
    _primary: frozenset[str] = field(default=frozenset(), compare=False)
    _secondary: frozenset[str] = field(default=frozenset(), compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_name", normalize(self.name))
        object.__setattr__(self, "_equipment",
                           frozenset(normalize(e) for e in self.equipment if e))
        object.__setattr__(self, "_primary",
                           frozenset(normalize(m) for m in self.primary_muscles if m))
        object.__setattr__(self, "_secondary",
                           frozenset(normalize(m) for m in self.secondary_muscles if m))


# Rank weights — explicit so ordering is auditable and stable.
_RANK_EXACT_NAME = 1000
_RANK_NAME_PREFIX = 820
_RANK_NAME_TOKENS = 660
_FIELD_NAME_TOKEN = 60
_FIELD_PATTERN = 46
_FIELD_PRIMARY = 50
_FIELD_SECONDARY = 34
_FIELD_EQUIPMENT = 30
_FIELD_META = 20
_FIELD_SUBSTRING = 14
_FACET_ONLY_BASE = 100
_SUBSTRING_FALLBACK = 120


def _equipment_matches(expanded: ExpandedTerm, sx: SearchableExercise) -> bool:
    if expanded.bodyweight and not sx._equipment:
        return True
    return bool(expanded.equipment & sx._equipment)


def _token_field_score(term: str, sx: SearchableExercise) -> int:
    """Best single-field contribution of one query term to one exercise (0 = no match)."""
    expanded = expand_term(term)
    name_tokens = sx._name.split()
    if any(nt == term or nt.startswith(term) for nt in name_tokens):
        return _FIELD_NAME_TOKEN
    if expanded.muscles & sx._primary:
        return _FIELD_PRIMARY
    if expanded.patterns and normalize(sx.movement_pattern) in expanded.patterns:
        return _FIELD_PATTERN
    if expanded.muscles & sx._secondary:
        return _FIELD_SECONDARY
    if _equipment_matches(expanded, sx):
        return _FIELD_EQUIPMENT
    if term and (term == normalize(sx.category) or term == normalize(sx.difficulty)):
        return _FIELD_META
    if term and term in sx._name:
        return _FIELD_SUBSTRING
    return 0


def _facet_passes(sx: SearchableExercise, *, muscle: str | None, equipment: str | None,
                  movement_pattern: str | None, difficulty: str | None) -> bool:
    if muscle:
        exp = expand_term(normalize(muscle))
        wanted = exp.muscles or {normalize(muscle)}
        if not (wanted & (sx._primary | sx._secondary)):
            return False
    if equipment:
        exp = expand_term(normalize(equipment))
        if not (_equipment_matches(exp, sx)
                or normalize(equipment) in sx._equipment):
            return False
    if movement_pattern:
        exp = expand_term(normalize(movement_pattern))
        wanted = exp.patterns or {normalize(movement_pattern)}
        if normalize(sx.movement_pattern) not in wanted:
            return False
    if difficulty and normalize(difficulty) != normalize(sx.difficulty):
        return False
    return True


def score_query(sx: SearchableExercise, query: str) -> int | None:
    """Deterministic relevance of one exercise to a free-text query. None = no match."""
    raw = normalize(query)
    if not raw:
        return _FACET_ONLY_BASE
    if sx._name == raw:
        return _RANK_EXACT_NAME
    if sx._name.startswith(raw):
        return _RANK_NAME_PREFIX
    tokens = tokenize(raw)
    candidates: list[int] = []
    name_tokens = set(sx._name.split())
    if tokens and all(any(nt == t or nt.startswith(t) for nt in name_tokens)
                      for t in tokens):
        candidates.append(_RANK_NAME_TOKENS)
    # Intersection (AND) matching: every term must land somewhere on the exercise.
    if tokens:
        per_term = [_token_field_score(t, sx) for t in tokens]
        if all(s > 0 for s in per_term):
            candidates.append(300 + min(sum(per_term), 300))
    if candidates:
        return max(candidates)
    if raw in sx._name or (sx.description and raw in normalize(sx.description)):
        return _SUBSTRING_FALLBACK
    return None


def rank_exercises(
    items: list[SearchableExercise],
    *,
    query: str | None = None,
    muscle: str | None = None,
    equipment: str | None = None,
    movement_pattern: str | None = None,
    difficulty: str | None = None,
) -> list[SearchableExercise]:
    """Filter by facets, score by query, and return a deterministically ordered subset.

    With no query and no facets the input order is preserved (caller's default order).
    """
    if not any((query and query.strip(), muscle, equipment, movement_pattern, difficulty)):
        return list(items)
    scored: list[tuple[int, str, SearchableExercise]] = []
    for sx in items:
        if not _facet_passes(sx, muscle=muscle, equipment=equipment,
                             movement_pattern=movement_pattern, difficulty=difficulty):
            continue
        rank = score_query(sx, query or "")
        if rank is None:
            continue
        scored.append((rank, sx._name, sx))
    scored.sort(key=lambda row: (-row[0], row[1], row[2].key))
    return [row[2] for row in scored]
