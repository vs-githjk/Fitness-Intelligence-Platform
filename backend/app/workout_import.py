"""Structured workout import — deterministic CSV parsing, exercise matching, and
prescription mapping.

Pure and framework-free (no DB, no FastAPI). A coach can bring a workout they already
have as a simple CSV; this module parses it into rows, maps each row's numbers onto the
correct set fields for the matched exercise's tracking mode, and matches the exercise
NAME against the coach's library deterministically. Nothing here creates content — the
service builds a preview and the coach confirms before anything becomes a draft (Coach
Ease + review-before-save).

Matching is conservative on purpose (no silent fuzzy matches): an exact normalized name
match is MATCHED; anything else is NEEDS_REVIEW with ranked candidates for the coach to
choose; no candidate at all is NOT_FOUND (search manually, create custom, or skip).
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from app.exercise_search import SearchableExercise, normalize, score_query

# Bounds (Part 61): keep imports small and predictable.
MAX_ROWS = 200
MAX_BYTES = 512 * 1024  # 512 KB of CSV text

# Canonical import columns and the header aliases coaches might reasonably use.
_COLUMN_ALIASES: dict[str, str] = {
    "exercise": "exercise", "name": "exercise", "movement": "exercise",
    "sets": "sets", "set": "sets",
    "reps": "reps", "rep": "reps", "repetitions": "reps",
    "load": "load", "weight": "load", "resistance": "load",
    "load_unit": "load_unit", "weight_unit": "load_unit", "unit": "load_unit",
    "duration": "duration", "time": "duration", "seconds": "duration",
    "duration_seconds": "duration",
    "distance": "distance",
    "distance_unit": "distance_unit",
    "rest": "rest_seconds", "rest_seconds": "rest_seconds", "rest_sec": "rest_seconds",
    "notes": "notes", "note": "notes", "comment": "notes", "cue": "notes",
}

MATCHED = "matched"
NEEDS_REVIEW = "needs_review"
NOT_FOUND = "not_found"


@dataclass
class ImportRow:
    line: int  # 1-based data row number (excludes the header), for coach-facing errors
    exercise_name: str
    sets: int
    reps_min: int | None = None
    reps_max: int | None = None
    load: str | None = None  # kept as string; the schema parses the decimal
    load_unit: str | None = None
    duration_seconds: int | None = None
    distance: str | None = None
    distance_unit: str | None = None
    rest_seconds: int | None = None
    notes: str | None = None
    error: str | None = None  # a coach-friendly problem with this row, if any


@dataclass
class ParsedImport:
    rows: list[ImportRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)  # whole-file problems


def _parse_int(value: str) -> int | None:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None


def _parse_reps(value: str) -> tuple[int | None, int | None]:
    """Accept '8', '8-10', '8 to 10', '8x'. Returns (min, max)."""
    text = value.lower().replace("to", "-").replace("x", "")
    parts = [p for p in (chunk.strip() for chunk in text.split("-")) if p]
    nums = [_parse_int(p) for p in parts]
    nums = [n for n in nums if n is not None]
    if not nums:
        return None, None
    if len(nums) == 1:
        return nums[0], nums[0]
    return min(nums[0], nums[1]), max(nums[0], nums[1])


def _parse_time(value: str) -> int | None:
    """Accept '30', '90s', '1:30' (m:ss), '0:45'. Returns seconds."""
    text = value.strip().lower().rstrip("s").strip()
    if ":" in text:
        chunks = text.split(":")
        try:
            minutes, seconds = int(chunks[0]), int(chunks[1])
        except (ValueError, IndexError):
            return None
        return minutes * 60 + seconds
    return _parse_int(text)


def _split_load(value: str) -> tuple[str | None, str | None]:
    """From '40', '40kg', '40 lb' return (numeric_string, unit_or_None)."""
    text = value.strip().lower()
    if not text:
        return None, None
    unit = None
    if "kg" in text:
        unit = "kg"
    elif "lb" in text or "lbs" in text:
        unit = "lb"
    number = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    return (number or None), unit


def parse_csv(content: str) -> ParsedImport:
    """Parse coach CSV text into structured rows. Never raises on bad data — it records
    coach-friendly errors per row / per file instead."""
    result = ParsedImport()
    if len(content.encode("utf-8", errors="ignore")) > MAX_BYTES:
        result.errors.append("This file is too large to import. Keep it under 512 KB.")
        return result
    text = content.lstrip("﻿")  # strip a UTF-8 BOM if present
    reader = csv.reader(io.StringIO(text))
    try:
        rows = list(reader)
    except csv.Error:
        result.errors.append("We couldn't read this file as CSV. Check the formatting.")
        return result
    rows = [r for r in rows if any(cell.strip() for cell in r)]
    if not rows:
        result.errors.append("The file is empty.")
        return result
    header = [_COLUMN_ALIASES.get(cell.strip().lower()) for cell in rows[0]]
    if "exercise" not in header:
        result.errors.append(
            "Add a header row with at least an 'exercise' column "
            "(other columns: sets, reps, load, load_unit, duration, distance, "
            "distance_unit, rest_seconds, notes)."
        )
        return result
    data_rows = rows[1:]
    if len(data_rows) > MAX_ROWS:
        result.errors.append(f"This import has too many rows (limit {MAX_ROWS}).")
        return result

    for index, raw in enumerate(data_rows, start=1):
        cells = {header[i]: raw[i].strip() for i in range(len(raw))
                 if i < len(header) and header[i]}
        name = cells.get("exercise", "")
        if not name:
            row = ImportRow(line=index, exercise_name="", sets=1,
                           error=f"Row {index} has no exercise name.")
            result.rows.append(row)
            continue
        reps_min, reps_max = _parse_reps(cells.get("reps", ""))
        load, inline_unit = _split_load(cells.get("load", ""))
        load_unit = (cells.get("load_unit") or inline_unit or ("kg" if load else None))
        distance = cells.get("distance") or None
        distance_unit = cells.get("distance_unit") or ("kilometers" if distance else None)
        sets = _parse_int(cells.get("sets", "")) or 1
        row = ImportRow(
            line=index,
            exercise_name=name,
            sets=max(1, min(sets, 20)),
            reps_min=reps_min,
            reps_max=reps_max,
            load=load,
            load_unit=load_unit,
            duration_seconds=_parse_time(cells.get("duration", "")),
            distance=distance,
            distance_unit=distance_unit,
            rest_seconds=_parse_time(cells.get("rest_seconds", "")),
            notes=cells.get("notes") or None,
        )
        result.rows.append(row)
    return result


@dataclass
class RowMatch:
    status: str
    exercise_id: str | None = None  # the exercise root id when a single clear match
    candidates: list[str] = field(default_factory=list)  # ranked candidate ids for review


def match_exercise(name: str, catalog: list[SearchableExercise]) -> RowMatch:
    """Deterministically match a CSV exercise name against the coach's library.

    Exact normalized-name match => MATCHED. Otherwise the ranked candidates are offered
    for the coach to choose (NEEDS_REVIEW), or NOT_FOUND when nothing is close. Never
    silently picks among ambiguous names.
    """
    target = normalize(name)
    if not target:
        return RowMatch(status=NOT_FOUND)
    exact = [sx for sx in catalog if normalize(sx.name) == target]
    if len(exact) == 1:
        return RowMatch(status=MATCHED, exercise_id=exact[0].key)
    if len(exact) > 1:
        return RowMatch(status=NEEDS_REVIEW, candidates=[sx.key for sx in exact])
    scored = sorted(
        ((score_query(sx, name), sx) for sx in catalog),
        key=lambda pair: (-(pair[0] or 0), normalize(pair[1].name)),
    )
    candidates = [sx.key for score, sx in scored if score is not None][:5]
    if not candidates:
        return RowMatch(status=NOT_FOUND)
    return RowMatch(status=NEEDS_REVIEW, candidates=candidates)


def prescription_for(row: ImportRow, tracking_mode: str | None) -> dict:
    """Map a parsed row onto the set fields appropriate for the exercise tracking mode.

    Returns a single set's fields; the service repeats it `row.sets` times. Only fields
    valid for the mode are emitted so the existing set-prescription validation accepts it.
    """
    base: dict = {}
    if row.rest_seconds is not None:
        base["rest_seconds"] = row.rest_seconds
    if row.notes:
        base["instructions"] = row.notes[:2000]
    mode = tracking_mode or ""
    if mode == "repetitions_and_load":
        _apply_reps(base, row)
        if row.load is not None:
            base["target_load_original_value"] = row.load
            base["target_load_original_unit"] = (row.load_unit or "kg")
    elif mode == "repetitions_only":
        _apply_reps(base, row)
    elif mode == "bodyweight_or_assisted_repetitions":
        _apply_reps(base, row)
    elif mode == "duration":
        if row.duration_seconds is not None:
            base["target_duration_seconds"] = row.duration_seconds
    elif mode == "distance_and_duration":
        if row.duration_seconds is not None:
            base["target_duration_seconds"] = row.duration_seconds
        if row.distance is not None:
            base["target_distance_value"] = row.distance
            base["target_distance_unit"] = (row.distance_unit or "kilometers")
    return base


def _apply_reps(base: dict, row: ImportRow) -> None:
    if row.reps_min is not None and row.reps_max is not None:
        base["repetitions_min"] = row.reps_min
        base["repetitions_max"] = row.reps_max
