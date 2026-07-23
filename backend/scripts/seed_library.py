"""Install or update the curated starter library.

This is an explicit operator command; it never runs automatically at application
startup. It is idempotent and non-destructive:

- Re-running it creates no duplicate Exercises, Templates, or Programs.
- It never modifies coach-owned copies cloned from starter content.
- It never touches real user accounts, assignments, or demo data.

The starter library is owned by a single non-login ``is_system`` account, which keeps
it read-only to coaches and out of the assignment selector. To revise starter content
later, add a new item (new name/key) rather than mutating a published version, so
existing coach copies stay independent.

Usage:

    python -m scripts.seed_library
"""

import logging

from sqlalchemy import select

from app.database import SessionLocal
from app.library_services import SYSTEM_LIBRARY_EMAIL
from app.models import (
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseVersion,
    ExerciseVersionStatus,
    Role,
    TrainingProgram,
    TrainingProgramVersion,
    User,
    WorkoutTemplate,
    WorkoutTemplateVersion,
    WorkoutTemplateVersionStatus,
)
from app.schemas import TrainingProgramCreateRequest, WorkoutTemplateCreateRequest
from app.training_program_services import (
    create_training_program,
    publish_training_program_draft,
)
from app.workout_template_services import (
    create_workout_template,
    publish_workout_template_draft,
)
from scripts.library_content import (
    EXERCISE_SLUG_BY_KEY,
    LIBRARY_EXERCISES,
    LIBRARY_PROGRAMS,
    LIBRARY_TEMPLATES,
    verify_library_content,
)
from scripts.seed import _seed_exercise

logger = logging.getLogger("fitness_intelligence.seed_library")


def _library_account(db) -> User:
    account = db.scalar(select(User).where(User.is_system.is_(True)))
    if account is None:
        account = User(
            email=SYSTEM_LIBRARY_EMAIL,
            # Login is impossible: the hash never matches any password.
            password_hash="system-account-login-disabled",
            first_name="Starter",
            last_name="Library",
            role=Role.COACH,
            is_system=True,
        )
        db.add(account)
        db.flush()
    return account


def _seed_library_exercises(db) -> None:
    for specification in LIBRARY_EXERCISES:
        payload = {key: value for key, value in specification.items() if key != "key"}
        _seed_exercise(db, specification=payload, scope=ExerciseScope.SYSTEM)
    db.commit()


def _system_exercise_version_id(db, slug: str) -> str:
    version = db.scalar(
        select(ExerciseVersion)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(
            Exercise.scope == ExerciseScope.SYSTEM,
            Exercise.slug == slug,
            Exercise.status == ExerciseStatus.ACTIVE,
            ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED,
        )
    )
    if version is None:
        raise RuntimeError(f"Starter exercise is missing: {slug}")
    return str(version.id)


def _template_exists(db, library: User, name: str) -> bool:
    return db.scalar(
        select(WorkoutTemplate.id)
        .join(
            WorkoutTemplateVersion,
            WorkoutTemplateVersion.workout_template_id == WorkoutTemplate.id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == library.id,
            WorkoutTemplateVersion.name == name,
        )
    ) is not None


def _seed_library_templates(db, library: User) -> None:
    for template in LIBRARY_TEMPLATES:
        if _template_exists(db, library, template["name"]):
            continue
        payload = {
            "name": template["name"],
            "description": template["description"],
            "goal_tags": template["goal_tags"],
            "estimated_duration_minutes": template["estimated_duration_minutes"],
            "target_session_rpe": template["target_session_rpe"],
            "coach_notes": template["coach_notes"],
            "trainee_instructions": template["trainee_instructions"],
            "exercises": [
                {
                    "exercise_version_id": _system_exercise_version_id(
                        db, EXERCISE_SLUG_BY_KEY[slot["exercise_key"]]
                    ),
                    "section": slot["section"],
                    "display_order": slot["display_order"],
                    "coach_notes": slot["coach_notes"],
                    "trainee_instructions": slot["trainee_instructions"],
                    "sets": slot["sets"],
                }
                for slot in template["exercises"]
            ],
        }
        created = create_workout_template(
            db, library, WorkoutTemplateCreateRequest.model_validate(payload)
        )
        publish_workout_template_draft(db, library, created["id"])


def _published_template_version_id(db, library: User, name: str) -> str:
    version = db.scalar(
        select(WorkoutTemplateVersion)
        .join(
            WorkoutTemplate,
            WorkoutTemplate.id == WorkoutTemplateVersion.workout_template_id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == library.id,
            WorkoutTemplateVersion.name == name,
            WorkoutTemplateVersion.version_status == WorkoutTemplateVersionStatus.PUBLISHED,
        )
    )
    if version is None:
        raise RuntimeError(f"Starter template is missing: {name}")
    return str(version.id)


def _template_name_by_key(key: str) -> str:
    for template in LIBRARY_TEMPLATES:
        if template["key"] == key:
            return template["name"]
    raise RuntimeError(f"Unknown starter template key: {key}")


def _program_exists(db, library: User, name: str) -> bool:
    return db.scalar(
        select(TrainingProgram.id)
        .join(
            TrainingProgramVersion,
            TrainingProgramVersion.training_program_id == TrainingProgram.id,
        )
        .where(
            TrainingProgram.owner_coach_id == library.id,
            TrainingProgramVersion.name == name,
        )
    ) is not None


def _seed_library_programs(db, library: User) -> None:
    for program in LIBRARY_PROGRAMS:
        if _program_exists(db, library, program["name"]):
            continue
        payload = {
            "name": program["name"],
            "description": program["description"],
            "goal_tags": program["goal_tags"],
            "duration_weeks": program["duration_weeks"],
            "coach_notes": program["coach_notes"],
            "trainee_instructions": program["trainee_instructions"],
            "weeks": [
                {
                    "week_number": week["week_number"],
                    "label": week["label"],
                    "coach_notes": week["coach_notes"],
                    "is_deload": week["is_deload"],
                    "sessions": [
                        {
                            "workout_template_version_id": _published_template_version_id(
                                db, library, _template_name_by_key(session["template_key"])
                            ),
                            "weekday": session["weekday"],
                            "display_order": session["display_order"],
                            "required": session["required"],
                            "planned_duration_override_minutes": session[
                                "planned_duration_override_minutes"
                            ],
                            "target_session_rpe_override": session["target_session_rpe_override"],
                            "coach_notes": session["coach_notes"],
                            "trainee_instructions": session["trainee_instructions"],
                        }
                        for session in week["sessions"]
                    ],
                }
                for week in program["weeks"]
            ],
        }
        created = create_training_program(
            db, library, TrainingProgramCreateRequest.model_validate(payload)
        )
        publish_training_program_draft(db, library, created["id"])


def seed_starter_library(db=None) -> None:
    """Idempotently install/update the curated starter library.

    Pass an existing session to seed within a larger orchestration (e.g. dev seed);
    otherwise a session is opened here.
    """
    problems = verify_library_content()
    if problems:
        raise RuntimeError("Starter library content is invalid: " + "; ".join(problems))

    if db is not None:
        _seed_all(db)
        return
    with SessionLocal() as owned:
        _seed_all(owned)


def _seed_all(db) -> None:
    library = _library_account(db)
    db.commit()
    _seed_library_exercises(db)
    _seed_library_templates(db, library)
    _seed_library_programs(db, library)
    db.commit()
    logger.info(
        "Starter library ready: %d exercises, %d templates, %d programs",
        len(LIBRARY_EXERCISES),
        len(LIBRARY_TEMPLATES),
        len(LIBRARY_PROGRAMS),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_starter_library()
