"""End-to-end workout-import preview: parse + match against the coach library."""

import base64
import io
import zipfile

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def _xlsx_b64(header: list[str], rows: list[list[str]]) -> str:
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    strings: list[str] = []
    body = ""
    for r, line in enumerate([header, *rows], start=1):
        cells = ""
        for c, val in enumerate(line):
            if val not in strings:
                strings.append(val)
            cells += f'<c r="{chr(65 + c)}{r}" t="s"><v>{strings.index(val)}</v></c>'
        body += f'<row r="{r}">{cells}</row>'
    sheet = f'<worksheet xmlns="{ns}"><sheetData>{body}</sheetData></worksheet>'
    shared = f'<sst xmlns="{ns}">' + "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("xl/sharedStrings.xml", shared)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _login(client: TestClient, email: str, password: str) -> str:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _publish(client, headers, *, slug, name, tracking_mode="repetitions_and_load"):
    payload = {
        "slug": slug, "name": name, "description": "Import fixture.",
        "instructions": "Move with control.", "tracking_mode": tracking_mode,
        "category": "strength", "movement_pattern": "squat", "equipment": ["dumbbell"],
        "primary_muscle_groups": ["quadriceps"], "secondary_muscle_groups": [],
        "unilateral": False, "safety_cues": ["Stop if it hurts."],
    }
    created = client.post("/api/v1/coach/exercises", json=payload, headers=headers)
    assert created.status_code == 201, created.text
    published = client.post(
        f"/api/v1/coach/exercises/{created.json()['id']}/publish", headers=headers
    )
    assert published.status_code == 200, published.text


def test_preview_matches_known_exercises_and_flags_unknown(client: TestClient, db: Session):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    assert coach is not None
    headers = _auth(_login(client, coach.email, "CoachPass123!"))
    _publish(client, headers, slug="zz-import-squat", name="Zz Import Squat")

    csv = (
        "exercise,sets,reps,load,rest\n"
        "Zz Import Squat,3,8-10,40,90\n"
        "Totally Unknown Move,3,10,,60\n"
    )
    res = client.post("/api/v1/coach/workout-imports/preview",
                      json={"content": csv, "template_name": "My import"}, headers=headers)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["template_name"] == "My import"
    assert body["summary"]["total"] == 2

    matched = next(r for r in body["rows"] if r["exercise_name"] == "Zz Import Squat")
    assert matched["status"] == "matched"
    assert matched["matched"]["exercise_version_id"]
    assert matched["prescription"]["repetitions_min"] == 8
    assert matched["prescription"]["target_load_original_value"] == "40"
    assert matched["sets"] == 3

    unknown = next(r for r in body["rows"] if r["exercise_name"] == "Totally Unknown Move")
    assert unknown["status"] == "not_found"
    assert unknown["matched"] is None


def test_preview_accepts_an_xlsx_workbook(client: TestClient, db: Session):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    headers = _auth(_login(client, coach.email, "CoachPass123!"))
    _publish(client, headers, slug="zz-xlsx-squat", name="Zz Xlsx Squat")
    content = _xlsx_b64(["exercise", "sets", "reps", "load"], [["Zz Xlsx Squat", "3", "8-10", "40"]])
    res = client.post(
        "/api/v1/coach/workout-imports/preview",
        json={"content": content, "template_name": "Sheet import", "format": "xlsx"},
        headers=headers,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["summary"]["total"] == 1
    matched = body["rows"][0]
    assert matched["status"] == "matched"
    assert matched["prescription"]["repetitions_min"] == 8
    assert matched["prescription"]["target_load_original_value"] == "40"


def test_preview_reports_a_friendly_error_for_a_missing_exercise_column(
    client: TestClient, db: Session
):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    headers = _auth(_login(client, coach.email, "CoachPass123!"))
    res = client.post("/api/v1/coach/workout-imports/preview",
                      json={"content": "sets,reps\n3,10"}, headers=headers)
    assert res.status_code == 200
    assert res.json()["file_errors"]
    assert res.json()["rows"] == []


def test_preview_never_matches_another_coachs_private_exercise(
    client: TestClient, db: Session
):
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    other = db.scalar(select(User).where(User.email == "other@example.com"))
    assert coach is not None and other is not None
    coach_headers = _auth(_login(client, coach.email, "CoachPass123!"))
    other_headers = _auth(_login(client, other.email, "OtherPass123!"))
    _publish(client, coach_headers, slug="secret-import-lift", name="Secret Import Lift")

    csv = "exercise,sets,reps\nSecret Import Lift,3,10\n"
    res = client.post("/api/v1/coach/workout-imports/preview",
                      json={"content": csv}, headers=other_headers)
    assert res.status_code == 200
    assert res.json()["rows"][0]["status"] == "not_found"
