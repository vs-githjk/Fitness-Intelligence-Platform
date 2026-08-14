"""Workout import preview service.

Turns a coach's CSV into a review-before-save preview: it parses the rows, matches each
exercise name against the coach's own visible published library (deterministically, via
the shared search engine), and maps the numbers onto the correct set fields for the
matched exercise's tracking mode. It creates NOTHING — the coach resolves any unmatched
rows in the UI and then the normal workout-template create endpoint builds the draft.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.exercise_services import _representative_version, _searchable
from app.models import ExerciseVersionStatus, User
from app.repositories.exercises import ExerciseRepository
from app.workout_import import match_exercise, parse_csv, prescription_for


def _published_catalog(db: Session, coach: User):
    """Coach-visible exercises that have a published version (the only selectable ones),
    as (searchable, meta) keyed by root id."""
    searchables = []
    meta: dict[str, dict] = {}
    for exercise in ExerciseRepository(db).list_visible(coach.id):
        version = _representative_version(exercise)
        if version is None or version.status != ExerciseVersionStatus.PUBLISHED:
            continue
        candidate = _searchable(exercise, version)
        searchables.append(candidate)
        meta[candidate.key] = {
            "exercise_id": str(exercise.id),
            "exercise_version_id": str(version.id),
            "name": version.name,
            "tracking_mode": version.tracking_mode.value,
            "movement_pattern": version.movement_pattern,
        }
    return searchables, meta


def preview_workout_import(
    db: Session, coach: User, content: str, template_name: str | None = None
) -> dict:
    parsed = parse_csv(content)
    searchables, meta = _published_catalog(db, coach)

    rows_out: list[dict] = []
    counts = {"matched": 0, "needs_review": 0, "not_found": 0}
    for row in parsed.rows:
        if row.error:
            rows_out.append({
                "line": row.line, "exercise_name": row.exercise_name,
                "status": "not_found", "error": row.error, "sets": row.sets,
                "matched": None, "candidates": [], "prescription": None,
            })
            counts["not_found"] += 1
            continue
        result = match_exercise(row.exercise_name, searchables)
        matched = meta.get(result.exercise_id) if result.exercise_id else None
        candidates = [meta[key] for key in result.candidates if key in meta]
        prescription = prescription_for(
            row, matched["tracking_mode"] if matched else None
        ) if matched else None
        counts[result.status] = counts.get(result.status, 0) + 1
        rows_out.append({
            "line": row.line,
            "exercise_name": row.exercise_name,
            "status": result.status,
            "sets": row.sets,
            "matched": matched,
            "candidates": candidates,
            "prescription": prescription,
            "error": None,
        })

    return {
        "template_name": (template_name or "").strip() or "Imported workout",
        "file_errors": parsed.errors,
        "summary": {
            "total": len(rows_out),
            **counts,
        },
        "rows": rows_out,
    }
