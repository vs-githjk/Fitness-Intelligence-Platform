"""Pure workout-import parsing, matching, and prescription mapping (no DB)."""

import io
import zipfile

from app.exercise_search import SearchableExercise
from app.workout_import import (
    MATCHED,
    MAX_XLSX_BYTES,
    NEEDS_REVIEW,
    NOT_FOUND,
    ImportRow,
    match_exercise,
    parse_csv,
    parse_xlsx,
    prescription_for,
)


def _xlsx(header: list[str], rows: list[list[str]]) -> bytes:
    """Build a minimal, valid .xlsx (shared strings + one sheet) for parser tests."""
    strings: list[str] = []
    index: dict[str, int] = {}

    def sid(text: str) -> int:
        if text not in index:
            index[text] = len(strings)
            strings.append(text)
        return index[text]

    def col(n: int) -> str:
        letters = ""
        n += 1
        while n:
            n, rem = divmod(n - 1, 26)
            letters = chr(65 + rem) + letters
        return letters

    body = ""
    for r, line in enumerate([header, *rows], start=1):
        cells = "".join(
            f'<c r="{col(c)}{r}" t="s"><v>{sid(val)}</v></c>'
            for c, val in enumerate(line)
        )
        body += f'<row r="{r}">{cells}</row>'
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    sheet = f'<?xml version="1.0"?><worksheet xmlns="{ns}"><sheetData>{body}</sheetData></worksheet>'
    si = "".join(f"<si><t>{s}</t></si>" for s in strings)
    shared = f'<?xml version="1.0"?><sst xmlns="{ns}">{si}</sst>'
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", shared)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


def test_parse_xlsx_matches_csv_semantics():
    data = _xlsx(
        ["Exercise", "Sets", "Reps", "Load", "Rest"],
        [["Goblet squat", "3", "8-10", "20kg", "90"]],
    )
    parsed = parse_xlsx(data)
    assert parsed.errors == []
    assert len(parsed.rows) == 1
    row = parsed.rows[0]
    assert row.exercise_name == "Goblet squat"
    assert (row.sets, row.reps_min, row.reps_max) == (3, 8, 10)
    assert (row.load, row.load_unit, row.rest_seconds) == ("20", "kg", 90)


def test_parse_xlsx_requires_exercise_header():
    parsed = parse_xlsx(_xlsx(["Sets", "Reps"], [["3", "8"]]))
    assert parsed.rows == []
    assert any("exercise" in e.lower() for e in parsed.errors)


def test_parse_xlsx_rejects_oversized_and_garbage():
    assert any("2 MB" in e for e in parse_xlsx(b"x" * (MAX_XLSX_BYTES + 1)).errors)
    assert any("xlsx" in e.lower() for e in parse_xlsx(b"not a zip").errors)


# --- adversarial .xlsx (Part 16) ---

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def _sheet(rows_xml: str) -> str:
    return f'<worksheet xmlns="{_NS}"><sheetData>{rows_xml}</sheetData></worksheet>'


def _inline(ref: str, text: str) -> str:
    return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'


def _book(sheet_xml: str | None, *, extra: dict[str, str] | None = None, with_sheet=True) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        if with_sheet and sheet_xml is not None:
            z.writestr("xl/worksheets/sheet1.xml", sheet_xml)
        for name, content in (extra or {}).items():
            z.writestr(name, content)
    return buf.getvalue()


def test_parse_xlsx_rejects_dtd_and_entities_xxe():
    # A DOCTYPE/ENTITY is never present in valid OOXML; it's the XXE / billion-laughs vector.
    evil = (
        '<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "boom">]>'
        + _sheet(_inline("A1", "exercise"))
    )
    parsed = parse_xlsx(_book(evil))
    assert parsed.rows == []
    assert any("unsupported xml" in e.lower() for e in parsed.errors)


def test_parse_xlsx_never_evaluates_formulas_uses_cached_value():
    sheet = _sheet(
        f'<row r="1">{_inline("A1", "exercise")}{_inline("B1", "reps")}</row>'
        f'<row r="2">{_inline("A2", "Goblet squat")}'
        '<c r="B2"><f>1+1</f><v>2</v></c></row>'
    )
    parsed = parse_xlsx(_book(sheet))
    assert parsed.errors == []
    assert (parsed.rows[0].reps_min, parsed.rows[0].reps_max) == (2, 2)


def test_parse_xlsx_ignores_far_right_columns():
    sheet = _sheet(
        f'<row r="1">{_inline("A1", "exercise")}{_inline("XFD1", "junk")}</row>'
        f'<row r="2">{_inline("A2", "Goblet squat")}</row>'
    )
    parsed = parse_xlsx(_book(sheet))  # must not materialize a 16k-wide row
    assert parsed.errors == []
    assert parsed.rows[0].exercise_name == "Goblet squat"


def test_parse_xlsx_friendly_error_on_malformed_xml():
    parsed = parse_xlsx(_book("<worksheet><sheetData><row></nope>"))
    assert parsed.rows == []
    assert any("xlsx" in e.lower() for e in parsed.errors)


def test_parse_xlsx_rejects_too_many_entries():
    extra = {f"xl/junk{i}.bin": "x" for i in range(600)}
    parsed = parse_xlsx(_book(_sheet(_inline("A1", "exercise")), extra=extra))
    assert any("too many parts" in e.lower() for e in parsed.errors)


def test_parse_xlsx_takes_first_sheet_only():
    first = _sheet(f'<row r="1">{_inline("A1", "exercise")}</row><row r="2">{_inline("A2", "Goblet squat")}</row>')
    second = _sheet(f'<row r="1">{_inline("A1", "exercise")}</row><row r="2">{_inline("A2", "Bench press")}</row>')
    parsed = parse_xlsx(_book(first, extra={"xl/worksheets/sheet2.xml": second}))
    assert [r.exercise_name for r in parsed.rows] == ["Goblet squat"]


def test_parse_xlsx_errors_when_no_worksheet():
    parsed = parse_xlsx(_book(None, extra={"xl/sharedStrings.xml": f'<sst xmlns="{_NS}"/>'}, with_sheet=False))
    assert any("worksheet" in e.lower() for e in parsed.errors)


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
