"""Curated starter-library service: browse, preview, and clone-to-edit.

The starter library is a small set of read-only, system-owned Programs (with their
Templates and Exercises). It is owned by a single non-login ``is_system`` account, so
existing owner-scoping makes it read-only to every coach automatically and keeps it
out of the assignment selector (a coach can only assign programs they own).

The only mutation is a transactional clone: a coach turns a starter Program into an
independent, coach-owned draft. The clone duplicates the referenced system Templates
into coach-owned published Templates and references the read-only system Exercises
directly (coach content may reference system exercise versions). The source is never
modified, and the copy never re-syncs with the source.
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    ProgramSession,
    ProgramWeek,
    TrainingProgram,
    TrainingProgramStatus,
    TrainingProgramVersion,
    TrainingProgramVersionStatus,
    User,
    WorkoutSetPrescription,
    WorkoutTemplate,
    WorkoutTemplateExercise,
    WorkoutTemplateStatus,
    WorkoutTemplateVersion,
    WorkoutTemplateVersionStatus,
)
from app.repositories.training_programs import TrainingProgramRepository
from app.schemas import ProgramSessionData, WorkoutSetPrescriptionData
from app.training_program_services import (
    PROGRAM_FIELDS,
    WEEKDAY_ORDER,
    get_training_program,
)
from app.workout_template_services import (
    SECTION_ORDER,
    TEMPLATE_FIELDS,
    workout_template_content_hash,
)

# Stable, non-login identity for the account that owns the curated starter library.
SYSTEM_LIBRARY_EMAIL = "system.library@fitintel.internal"
SYSTEM_LIBRARY_DISPLAY_NAME = "FitIntel Starter Library"

_LEVELS = ("beginner", "intermediate", "advanced")
PREVIEW_DISCLAIMER = (
    "Starter Programs are general templates for review, not personalized or medical "
    "advice. Review and adjust before assigning, and have trainees stop any movement "
    "that causes pain."
)


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def library_not_found() -> HTTPException:
    # Uniform 404 so an unavailable library and a missing program are indistinguishable.
    return _error(404, "library_program_not_found", "Starter Program not found")


def get_system_library_account(db: Session) -> User | None:
    return db.scalar(select(User).where(User.is_system.is_(True)))


def _published(program: TrainingProgram) -> TrainingProgramVersion | None:
    if program.current_published_version_id is None:
        return None
    return next(
        (
            item
            for item in program.versions
            if item.id == program.current_published_version_id
        ),
        None,
    )


def _level(goal_tags: list[str]) -> str:
    lowered = {tag.lower() for tag in goal_tags}
    for level in _LEVELS:
        if level in lowered:
            return level
    return "general"


def _equipment_summary(version: TrainingProgramVersion) -> list[str]:
    equipment: set[str] = set()
    for week in version.weeks:
        for session in week.sessions:
            for exercise in session.workout_template_version.exercises:
                for item in exercise.exercise_version.equipment or []:
                    normalized = str(item).strip().lower()
                    if normalized and normalized not in {"none", "bodyweight"}:
                        equipment.add(normalized)
    return sorted(equipment)


def _sessions_per_week(version: TrainingProgramVersion) -> int:
    return max((len(week.sessions) for week in version.weeks), default=0)


def _program_summary(program: TrainingProgram, version: TrainingProgramVersion) -> dict:
    return {
        "id": program.id,
        "name": version.name,
        "description": version.description,
        "level": _level(version.goal_tags),
        "duration_weeks": version.duration_weeks,
        "sessions_per_week": _sessions_per_week(version),
        "goal_tags": version.goal_tags,
        "equipment_summary": _equipment_summary(version),
        "published_version_id": version.id,
    }


def list_library_programs(db: Session) -> dict:
    library = get_system_library_account(db)
    if library is None:
        return {"items": [], "disclaimer": PREVIEW_DISCLAIMER}
    items = []
    for program in TrainingProgramRepository(db).list_owned_preview(library.id):
        published = _published(program)
        if published is None:
            continue
        items.append(_program_summary(program, published))
    return {"items": items, "disclaimer": PREVIEW_DISCLAIMER}


def _exercise_preview(exercise: WorkoutTemplateExercise) -> dict:
    version = exercise.exercise_version
    return {
        "name": version.name,
        "category": version.category,
        "tracking_mode": version.tracking_mode,
        "set_count": len(exercise.sets),
    }


def _template_preview(version: WorkoutTemplateVersion) -> dict:
    exercises = sorted(
        version.exercises,
        key=lambda item: (SECTION_ORDER[item.section], item.display_order),
    )
    return {
        "name": version.name,
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "exercises": [_exercise_preview(exercise) for exercise in exercises],
    }


def get_library_program(db: Session, program_id: uuid.UUID) -> dict:
    library = get_system_library_account(db)
    if library is None:
        raise library_not_found()
    program = TrainingProgramRepository(db).get_owned_preview(library.id, program_id)
    if program is None:
        raise library_not_found()
    published = _published(program)
    if published is None:
        raise library_not_found()
    weeks = []
    for week in sorted(published.weeks, key=lambda item: item.week_number):
        sessions = sorted(
            week.sessions,
            key=lambda item: (WEEKDAY_ORDER[item.weekday.value], item.display_order),
        )
        weeks.append(
            {
                "week_number": week.week_number,
                "label": week.label,
                "is_deload": week.is_deload,
                "sessions": [
                    {
                        "weekday": session.weekday,
                        "display_order": session.display_order,
                        "required": session.required,
                        "template": _template_preview(session.workout_template_version),
                    }
                    for session in sessions
                ],
            }
        )
    return {
        **_program_summary(program, published),
        "coach_notes": published.coach_notes,
        "trainee_instructions": published.trainee_instructions,
        "weeks": weeks,
        "disclaimer": PREVIEW_DISCLAIMER,
    }


def _duplicate_template(
    db: Session, coach: User, source: WorkoutTemplateVersion
) -> WorkoutTemplateVersion:
    """Copy a system template version into a coach-owned, published template.

    Exercise references are preserved as-is: they point at read-only system exercise
    versions, which coach content is permitted to reference.
    """
    now = datetime.now(UTC)
    template = WorkoutTemplate(
        owner_coach_id=coach.id,
        status=WorkoutTemplateStatus.ACTIVE,
        cloned_from_template_id=source.workout_template_id,
    )
    version = WorkoutTemplateVersion(
        workout_template=template,
        version_number=1,
        version_status=WorkoutTemplateVersionStatus.PUBLISHED,
        draft_revision=1,
        created_by_user_id=coach.id,
        published_at=now,
        **{field: getattr(source, field) for field in TEMPLATE_FIELDS},
    )
    for exercise in source.exercises:
        clone = WorkoutTemplateExercise(
            exercise_version_id=exercise.exercise_version_id,
            section=exercise.section,
            display_order=exercise.display_order,
            coach_notes=exercise.coach_notes,
            trainee_instructions=exercise.trainee_instructions,
        )
        clone.sets = [
            WorkoutSetPrescription(
                **{
                    key: getattr(item, key)
                    for key in WorkoutSetPrescriptionData.model_fields
                },
                target_load_canonical_kg=item.target_load_canonical_kg,
                target_assistance_canonical_kg=item.target_assistance_canonical_kg,
            )
            for item in sorted(exercise.sets, key=lambda current: current.set_number)
        ]
        version.exercises.append(clone)
    version.content_hash = workout_template_content_hash(version)
    db.add(template)
    db.flush()
    template.current_published_version_id = version.id
    return version


def clone_library_program(
    db: Session, coach: User, program_id: uuid.UUID
) -> dict:
    """Create an independent coach-owned draft Program from a starter Program.

    Transactional: everything is built in the session and committed once, so a
    mid-copy failure leaves no partial graph. The source Program is never mutated,
    the copy is a draft, and nothing is published or assigned automatically.
    """
    library = get_system_library_account(db)
    if library is None:
        raise library_not_found()
    source = TrainingProgramRepository(db).get_owned_preview(library.id, program_id)
    if source is None:
        raise library_not_found()
    source_version = _published(source)
    if source_version is None:
        raise library_not_found()

    # Duplicate each distinct referenced system template once into a coach template.
    template_map: dict[uuid.UUID, uuid.UUID] = {}
    for week in source_version.weeks:
        for session in week.sessions:
            source_template_version = session.workout_template_version
            if source_template_version.id not in template_map:
                coach_version = _duplicate_template(db, coach, source_template_version)
                template_map[source_template_version.id] = coach_version.id

    program = TrainingProgram(
        owner_coach_id=coach.id,
        status=TrainingProgramStatus.ACTIVE,
        cloned_from_program_id=source.id,
    )
    version = TrainingProgramVersion(
        training_program=program,
        version_number=1,
        version_status=TrainingProgramVersionStatus.DRAFT,
        draft_revision=1,
        created_by_user_id=coach.id,
        **{field: getattr(source_version, field) for field in PROGRAM_FIELDS},
    )
    for week in sorted(source_version.weeks, key=lambda item: item.week_number):
        week_clone = ProgramWeek(
            week_number=week.week_number,
            label=week.label,
            coach_notes=week.coach_notes,
            is_deload=week.is_deload,
        )
        week_clone.sessions = [
            ProgramSession(
                **{
                    field: getattr(session, field)
                    for field in ProgramSessionData.model_fields
                    if field != "workout_template_version_id"
                },
                workout_template_version_id=template_map[
                    session.workout_template_version_id
                ],
            )
            for session in week.sessions
        ]
        version.weeks.append(week_clone)

    db.add(program)
    db.commit()
    return get_training_program(db, coach, program.id)
