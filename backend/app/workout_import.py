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
import zipfile
from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

from app.exercise_search import SearchableExercise, normalize, score_query

# Bounds (Part 61): keep imports small and predictable.
MAX_ROWS = 200
MAX_BYTES = 512 * 1024  # 512 KB of CSV text
MAX_XLSX_BYTES = 2 * 1024 * 1024  # 2 MB compressed .xlsx upload
# Decompression-bomb guards: a single member, the whole archive's uncompressed total, and
# the number of entries are all bounded so a tiny upload can't expand without limit.
MAX_XLSX_MEMBER_BYTES = 24 * 1024 * 1024
MAX_XLSX_TOTAL_UNCOMPRESSED = 48 * 1024 * 1024
MAX_XLSX_ENTRIES = 512
# A workout has a handful of columns; ignore anything past this so a cell reference like
# "XFD1" (column 16384) can't force a giant sparse row to be materialized.
MAX_XLSX_COLS = 64

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
    return _rows_to_parsed(rows)


def parse_xlsx(data: bytes) -> ParsedImport:
    """Parse a coach's .xlsx workbook into the same structured rows as CSV.

    Values-only and dependency-free: an .xlsx is a ZIP of XML, so we read cell values
    (and shared strings) with the standard library and never evaluate a formula or touch
    a macro (Part 36). Cached values of formula cells are used as-is; uncalculated
    formulas read as blank. Bounded by size and row count; never raises on bad data.
    """
    result = ParsedImport()
    if len(data) > MAX_XLSX_BYTES:
        result.errors.append("This file is too large to import. Keep it under 2 MB.")
        return result
    try:
        rows = _read_xlsx_matrix(data)
    except _XlsxError as exc:
        result.errors.append(str(exc))
        return result
    except Exception:  # malformed archive/XML — never leak internals to the coach
        result.errors.append(
            "We couldn't read this file as an .xlsx workbook. Re-export it, or use CSV."
        )
        return result
    return _rows_to_parsed(rows)


class _XlsxError(Exception):
    """A coach-friendly problem reading an .xlsx workbook."""


_SSML = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col_index(ref: str) -> int:
    """'A1' -> 0, 'B2' -> 1, 'AA3' -> 26. Falls back to 0 for a missing ref."""
    letters = "".join(ch for ch in ref if ch.isalpha())
    index = 0
    for ch in letters:
        index = index * 26 + (ord(ch.upper()) - ord("A") + 1)
    return max(0, index - 1)


def _trim_number(text: str) -> str:
    """Render a spreadsheet number without a spurious '.0' so '3.0' reps stays '3'."""
    try:
        number = float(text)
    except (TypeError, ValueError):
        return text
    return str(int(number)) if number.is_integer() else repr(number)


def _cell_value(cell: ET.Element, shared: list[str]) -> str:
    kind = cell.get("t")
    if kind == "s":  # shared string
        v = cell.find(f"{_SSML}v")
        if v is None or v.text is None:
            return ""
        try:
            index = int(v.text)
        except ValueError:
            return ""
        return shared[index] if 0 <= index < len(shared) else ""
    if kind == "inlineStr":
        inline = cell.find(f"{_SSML}is")
        return "".join(t.text or "" for t in inline.iter(f"{_SSML}t")) if inline is not None else ""
    # number, boolean, or the cached value of a formula cell (the <f> is never evaluated)
    v = cell.find(f"{_SSML}v")
    if v is None or v.text is None:
        return ""
    if kind == "b":
        return "1" if v.text == "1" else "0"
    if kind in (None, "n"):
        return _trim_number(v.text)
    return v.text


def _reject_dtd(raw: bytes) -> None:
    """Refuse any XML that declares a DTD or entities. Valid OOXML never does; rejecting
    it defuses XXE and internal-entity ("billion laughs") expansion before parsing. A DTD
    must precede the root element, so a bounded prefix scan is sufficient and cheap."""
    head = raw[:65536].lower()
    if b"<!doctype" in head or b"<!entity" in head:
        raise _XlsxError("This workbook contains unsupported XML and was not imported.")


def _parse_xml(raw: bytes) -> ET.Element:
    _reject_dtd(raw)
    return ET.fromstring(raw)


def _read_xlsx_bytes(zf: zipfile.ZipFile, name: str) -> bytes:
    info = zf.getinfo(name)
    if info.file_size > MAX_XLSX_MEMBER_BYTES:
        raise _XlsxError("This workbook is too large to import.")
    return zf.read(name)


def _guard_archive(zf: zipfile.ZipFile) -> None:
    infos = zf.infolist()
    if len(infos) > MAX_XLSX_ENTRIES:
        raise _XlsxError("This workbook has too many parts to import.")
    if sum(info.file_size for info in infos) > MAX_XLSX_TOTAL_UNCOMPRESSED:
        raise _XlsxError("This workbook is too large to import.")


def _read_xlsx_matrix(data: bytes) -> list[list[str]]:
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        _guard_archive(zf)
        names = set(zf.namelist())
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = _parse_xml(_read_xlsx_bytes(zf, "xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(f"{_SSML}t")) for si in root]
        sheets = sorted(
            n for n in names if n.startswith("xl/worksheets/") and n.endswith(".xml")
        )
        if not sheets:
            raise _XlsxError("This workbook has no worksheet to import.")
        root = _parse_xml(_read_xlsx_bytes(zf, sheets[0]))
    sheet_data = root.find(f"{_SSML}sheetData")
    if sheet_data is None:
        return []
    matrix: list[list[str]] = []
    for row in sheet_data.findall(f"{_SSML}row"):
        if len(matrix) > MAX_ROWS + 1:  # header + data; extra rows are ignored later
            break
        cells: dict[int, str] = {}
        for auto, cell in enumerate(row.findall(f"{_SSML}c")):
            ref = cell.get("r")
            column = _col_index(ref) if ref else auto
            if column >= MAX_XLSX_COLS:  # ignore far-right columns (e.g. a stray "XFD1")
                continue
            cells[column] = _cell_value(cell, shared)
        width = (max(cells) + 1) if cells else 0
        matrix.append([cells.get(i, "") for i in range(width)])
    return matrix


def _rows_to_parsed(rows: list[list[str]]) -> ParsedImport:
    """Shared row → structured-import logic for both CSV and XLSX matrices."""
    result = ParsedImport()
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
