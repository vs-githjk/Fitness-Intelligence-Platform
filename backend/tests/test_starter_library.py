import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.library_services import (
    clone_library_program,
    get_system_library_account,
)
from app.models import (
    Role,
    TraineeProfile,
    TrainingProgram,
    User,
    WorkoutTemplate,
)
from app.security import LIBRARY_DEMO_MUTATIONS
from scripts.library_content import (
    LIBRARY_EXERCISES,
    LIBRARY_PROGRAMS,
    LIBRARY_TEMPLATES,
    verify_library_content,
)
from scripts.seed_library import seed_starter_library


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _coach_token(client: TestClient, email: str = "coach@example.com", password: str = "CoachPass123!") -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _register_trainee(client: TestClient, email: str = "libtrainee@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register/trainee",
        json={
            "email": email,
            "password": "TraineePass123!",
            "first_name": "Lib",
            "last_name": "Trainee",
            "invite_code": "FIT-DEMO-2026",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def library(db: Session):
    seed_starter_library(db)
    return get_system_library_account(db)


# --------------------------------------------------------------------------- content


def test_library_content_is_valid() -> None:
    assert verify_library_content() == []


def test_library_content_counts_are_bounded() -> None:
    assert 25 <= len(LIBRARY_EXERCISES) <= 40
    assert 8 <= len(LIBRARY_TEMPLATES) <= 12
    assert 4 <= len(LIBRARY_PROGRAMS) <= 6


# --------------------------------------------------------------------------- seeding


def test_seed_is_idempotent_and_preserves_coach_content(client: TestClient, db: Session) -> None:
    # A pre-existing coach-owned program must never be touched by library seeding.
    seed_starter_library(db)
    programs_first = db.scalar(select(func.count(TrainingProgram.id)))
    templates_first = db.scalar(select(func.count(WorkoutTemplate.id)))
    library = get_system_library_account(db)
    assert library is not None and library.is_system and library.role == Role.COACH

    seed_starter_library(db)
    assert db.scalar(select(func.count(TrainingProgram.id))) == programs_first
    assert db.scalar(select(func.count(WorkoutTemplate.id))) == templates_first
    # Exactly one system account exists.
    assert db.scalar(select(func.count(User.id)).where(User.is_system.is_(True))) == 1


# --------------------------------------------------------------------------- browsing/authz


def test_coach_can_browse_and_preview(client: TestClient, db: Session, library: User) -> None:
    token = _coach_token(client)
    listing = client.get("/api/v1/program-library", headers=_auth(token))
    assert listing.status_code == 200
    body = listing.json()
    assert len(body["items"]) == len(LIBRARY_PROGRAMS)
    assert body["disclaimer"]
    first = body["items"][0]
    assert {"id", "name", "level", "duration_weeks", "sessions_per_week", "equipment_summary"} <= first.keys()

    detail = client.get(f"/api/v1/program-library/{first['id']}", headers=_auth(token))
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["weeks"]
    assert payload["weeks"][0]["sessions"][0]["template"]["exercises"]


def test_preview_unknown_returns_404(client: TestClient, db: Session, library: User) -> None:
    token = _coach_token(client)
    response = client.get(f"/api/v1/program-library/{uuid.uuid4()}", headers=_auth(token))
    assert response.status_code == 404


def test_trainee_cannot_access_library(client: TestClient, db: Session, library: User) -> None:
    trainee = _register_trainee(client)
    token = trainee["access_token"]
    assert client.get("/api/v1/program-library", headers=_auth(token)).status_code == 403
    program_id = clone_source_id(db)
    assert client.get(f"/api/v1/program-library/{program_id}", headers=_auth(token)).status_code == 403
    assert client.post(
        f"/api/v1/program-library/{program_id}/clone", headers=_auth(token)
    ).status_code == 403


def clone_source_id(db: Session) -> uuid.UUID:
    library = get_system_library_account(db)
    from app.repositories.training_programs import TrainingProgramRepository

    program = TrainingProgramRepository(db).list_owned_preview(library.id)[0]
    return program.id


def test_system_program_is_read_only_and_unassignable(
    client: TestClient, db: Session, library: User
) -> None:
    token = _coach_token(client)
    system_id = clone_source_id(db)
    # A coach cannot open, edit, publish, or archive system content through the coach API.
    assert client.get(f"/api/v1/coach/training-programs/{system_id}", headers=_auth(token)).status_code == 404
    assert client.post(
        f"/api/v1/coach/training-programs/{system_id}/publish", headers=_auth(token)
    ).status_code == 404
    # System programs never appear in the coach's own program list (assignment source).
    listing = client.get("/api/v1/coach/training-programs?per_page=100", headers=_auth(token))
    assert all(item["id"] != str(system_id) for item in listing.json()["items"])


# --------------------------------------------------------------------------- clone


def test_clone_creates_independent_coach_draft(
    client: TestClient, db: Session, library: User
) -> None:
    token = _coach_token(client)
    source_id = clone_source_id(db)
    coach = db.scalar(select(User).where(User.email == "coach@example.com"))

    response = client.post(f"/api/v1/program-library/{source_id}/clone", headers=_auth(token))
    assert response.status_code == 201, response.text
    clone = response.json()
    assert clone["id"] != str(source_id)
    assert clone["owner_coach_id"] == str(coach.id)
    assert clone["cloned_from_program_id"] == str(source_id)
    assert clone["draft_version"] is not None
    assert clone["published_version"] is None

    # Distinct coach-owned templates were created (referenced by the draft sessions).
    coach_templates = db.scalar(
        select(func.count(WorkoutTemplate.id)).where(WorkoutTemplate.owner_coach_id == coach.id)
    )
    assert coach_templates >= 1
    assert all(
        template.cloned_from_template_id is not None
        for template in db.scalars(
            select(WorkoutTemplate).where(WorkoutTemplate.owner_coach_id == coach.id)
        )
    )

    # The source program is unchanged and still owned by the library account.
    source = db.get(TrainingProgram, source_id)
    assert source.owner_coach_id == library.id
    assert source.cloned_from_program_id is None


def test_repeated_clone_creates_separate_drafts(
    client: TestClient, db: Session, library: User
) -> None:
    token = _coach_token(client)
    source_id = clone_source_id(db)
    first = client.post(f"/api/v1/program-library/{source_id}/clone", headers=_auth(token)).json()
    second = client.post(f"/api/v1/program-library/{source_id}/clone", headers=_auth(token)).json()
    assert first["id"] != second["id"]


def test_unrelated_coach_cannot_see_cloned_program(
    client: TestClient, db: Session, library: User
) -> None:
    owner_token = _coach_token(client)
    source_id = clone_source_id(db)
    clone = client.post(f"/api/v1/program-library/{source_id}/clone", headers=_auth(owner_token)).json()
    other_token = _coach_token(client, email="other@example.com", password="OtherPass123!")
    assert client.get(
        f"/api/v1/coach/training-programs/{clone['id']}", headers=_auth(other_token)
    ).status_code == 404


def test_clone_rolls_back_on_mid_copy_failure(
    db: Session, library: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.library_services as svc

    coach = db.scalar(select(User).where(User.email == "coach@example.com"))
    source_id = clone_source_id(db)

    original = svc._duplicate_template
    calls = {"n": 0}

    def flaky(db_, coach_, source):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("boom mid-copy")
        return original(db_, coach_, source)

    monkeypatch.setattr(svc, "_duplicate_template", flaky)
    before = db.scalar(select(func.count(TrainingProgram.id)).where(TrainingProgram.owner_coach_id == coach.id))
    with pytest.raises(RuntimeError):
        clone_library_program(db, coach, source_id)
    db.rollback()
    after = db.scalar(select(func.count(TrainingProgram.id)).where(TrainingProgram.owner_coach_id == coach.id))
    assert after == before  # nothing was committed


# --------------------------------------------------------------------------- publish + assign


def test_cloned_program_publishes_assigns_and_schedules(
    client: TestClient, db: Session, library: User
) -> None:
    token = _coach_token(client)
    trainee = _register_trainee(client)
    trainee_id = trainee["user"]["id"]
    source_id = clone_source_id(db)

    clone = client.post(f"/api/v1/program-library/{source_id}/clone", headers=_auth(token)).json()
    program_id = clone["id"]

    published = client.post(
        f"/api/v1/coach/training-programs/{program_id}/publish", headers=_auth(token)
    )
    assert published.status_code == 200, published.text
    version_id = published.json()["published_version"]["id"]

    # The published copy is now an eligible assignment source.
    programs = client.get("/api/v1/coach/training-programs?per_page=100", headers=_auth(token)).json()
    assert any(item["id"] == program_id for item in programs["items"])

    preview = client.post(
        f"/api/v1/coach/trainees/{trainee_id}/training-assignments/preview",
        headers=_auth(token),
        json={"training_program_version_id": version_id, "effective_start_date": "2026-07-27"},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["workouts"]

    assigned = client.post(
        f"/api/v1/coach/trainees/{trainee_id}/training-assignments",
        headers=_auth(token),
        json={"training_program_version_id": version_id, "effective_start_date": "2026-07-27"},
    )
    assert assigned.status_code in (200, 201), assigned.text

    workspace = client.get("/api/v1/trainee/program", headers=_auth(trainee["access_token"]))
    assert workspace.status_code == 200
    assert workspace.json()["scheduled_workouts"]


# --------------------------------------------------------------------------- demo


def _demo_coach(db: Session) -> None:
    coach = User(
        email=settings.demo_coach_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Coach",
        role=Role.COACH,
        is_demo=True,
    )
    trainee = User(
        email=settings.demo_trainee_email,
        password_hash="demo-login-disabled",
        first_name="Demo",
        last_name="Trainee",
        role=Role.TRAINEE,
        is_demo=True,
    )
    db.add_all([coach, trainee])
    db.flush()
    db.add(TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"))
    db.commit()


def test_demo_coach_can_browse_but_not_clone(
    client: TestClient, db: Session, library: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    _demo_coach(db)
    monkeypatch.setattr(settings, "demo_mode_enabled", True)
    token = client.post("/api/v1/auth/demo-session", json={"role": "coach"}).json()["access_token"]
    source_id = clone_source_id(db)

    assert client.get("/api/v1/program-library", headers=_auth(token)).status_code == 200
    denied = client.post(f"/api/v1/program-library/{source_id}/clone", headers=_auth(token))
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "demo_read_only"


def test_library_demo_inventory_matches_openapi(client: TestClient) -> None:
    documented = {
        (method.upper(), path)
        for path, methods in client.app.openapi()["paths"].items()
        for method in methods
        if method.lower() in {"post", "put", "patch", "delete"}
        and path.startswith("/api/v1/program-library")
    }
    assert documented == LIBRARY_DEMO_MUTATIONS
