import hashlib
import json
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import (
    ProgramSession,
    ProgramWeek,
    TrainingProgram,
    TrainingProgramStatus,
    TrainingProgramVersion,
    TrainingProgramVersionStatus,
    User,
    WorkoutTemplateVersion,
)
from app.repositories.training_programs import TrainingProgramRepository
from app.schemas import (
    ProgramSessionData,
    TrainingProgramCreateRequest,
    TrainingProgramDraftData,
    TrainingProgramDraftReplaceRequest,
)

PROGRAM_FIELDS = (
    "name",
    "description",
    "goal_tags",
    "duration_weeks",
    "coach_notes",
    "trainee_instructions",
)
WEEKDAY_ORDER = {
    name: index
    for index, name in enumerate(
        ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
    )
}


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def program_not_found() -> HTTPException:
    return _error(404, "training_program_not_found", "Training program not found")


def _conflict(code: str, message: str) -> HTTPException:
    return _error(409, code, message)


def _invalid(code: str, message: str) -> HTTPException:
    return _error(422, code, message)


def _draft(program: TrainingProgram) -> TrainingProgramVersion | None:
    return next(
        (item for item in program.versions if item.version_status == TrainingProgramVersionStatus.DRAFT),
        None,
    )


def _published(program: TrainingProgram) -> TrainingProgramVersion | None:
    if program.current_published_version_id is None:
        return None
    return next(
        (item for item in program.versions if item.id == program.current_published_version_id),
        None,
    )


def _owned_active_program(
    db: Session, coach: User, program_id: uuid.UUID
) -> TrainingProgram:
    program = TrainingProgramRepository(db).get_owned_for_update(coach.id, program_id)
    if program is None:
        raise program_not_found()
    if program.status == TrainingProgramStatus.ARCHIVED:
        raise _conflict("training_program_archived", "Archived programs cannot be changed")
    return program


def _validate_graph(
    repository: TrainingProgramRepository,
    coach: User,
    body: TrainingProgramDraftData,
) -> dict[uuid.UUID, WorkoutTemplateVersion]:
    resolved: dict[uuid.UUID, WorkoutTemplateVersion] = {}
    for week in body.weeks:
        if len(week.sessions) > 14:
            raise _invalid("program_week_slot_limit", "A program week may contain at most 14 workout slots")
        for session in week.sessions:
            version = resolved.get(session.workout_template_version_id)
            if version is None:
                version = repository.get_selectable_template_version(
                    coach.id, session.workout_template_version_id
                )
                if version is None:
                    raise _invalid(
                        "workout_template_version_not_selectable",
                        "Workout must reference an active, owned, published template version",
                    )
                resolved[session.workout_template_version_id] = version
    return resolved


def _replace_graph(
    db: Session,
    version: TrainingProgramVersion,
    body: TrainingProgramDraftData,
    *,
    increment_revision: bool,
) -> None:
    for field in PROGRAM_FIELDS:
        setattr(version, field, getattr(body, field))
    if version.weeks:
        version.weeks.clear()
        db.flush()
    for week_data in body.weeks:
        week = ProgramWeek(
            week_number=week_data.week_number,
            label=week_data.label,
            coach_notes=week_data.coach_notes,
            is_deload=week_data.is_deload,
        )
        week.sessions = [
            ProgramSession(**session.model_dump(mode="python"))
            for session in week_data.sessions
        ]
        version.weeks.append(week)
    if increment_revision:
        version.draft_revision += 1
    version.updated_at = datetime.now(UTC)


def training_program_content_hash(version: TrainingProgramVersion) -> str:
    weeks = []
    for week in sorted(version.weeks, key=lambda item: item.week_number):
        sessions = []
        for session in sorted(
            week.sessions,
            key=lambda item: (WEEKDAY_ORDER[item.weekday.value], item.display_order),
        ):
            sessions.append(
                {
                    "workout_template_version_id": str(session.workout_template_version_id),
                    "weekday": session.weekday.value,
                    "display_order": session.display_order,
                    "required": session.required,
                    "planned_duration_override_minutes": session.planned_duration_override_minutes,
                    "target_session_rpe_override": (
                        format(session.target_session_rpe_override, ".1f")
                        if session.target_session_rpe_override is not None
                        else None
                    ),
                    "coach_notes": session.coach_notes,
                    "trainee_instructions": session.trainee_instructions,
                }
            )
        weeks.append(
            {
                "week_number": week.week_number,
                "label": week.label,
                "coach_notes": week.coach_notes,
                "is_deload": week.is_deload,
                "sessions": sessions,
            }
        )
    payload = {
        "name": version.name,
        "description": version.description,
        "goal_tags": sorted(version.goal_tags),
        "duration_weeks": version.duration_weeks,
        "coach_notes": version.coach_notes,
        "trainee_instructions": version.trainee_instructions,
        "weeks": weeks,
    }
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()


def _template_summary(version: WorkoutTemplateVersion) -> dict:
    return {
        "id": version.id,
        "workout_template_id": version.workout_template_id,
        "version_number": version.version_number,
        "name": version.name,
        "goal_tags": version.goal_tags,
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "target_session_rpe": version.target_session_rpe,
        "exercise_count": len(version.exercises),
    }


def _version_out(version: TrainingProgramVersion) -> dict:
    return {
        "id": version.id,
        "training_program_id": version.training_program_id,
        "version_number": version.version_number,
        "version_status": version.version_status.value,
        "draft_revision": version.draft_revision,
        **{field: getattr(version, field) for field in PROGRAM_FIELDS},
        "content_hash": version.content_hash,
        "created_by_user_id": version.created_by_user_id,
        "created_at": version.created_at,
        "updated_at": version.updated_at,
        "published_at": version.published_at,
        "weeks": [
            {
                "id": week.id,
                "week_number": week.week_number,
                "label": week.label,
                "coach_notes": week.coach_notes,
                "is_deload": week.is_deload,
                "created_at": week.created_at,
                "sessions": [
                    {
                        "id": session.id,
                        **{
                            field: getattr(session, field)
                            for field in ProgramSessionData.model_fields
                        },
                        "workout_template_version": _template_summary(
                            session.workout_template_version
                        ),
                        "created_at": session.created_at,
                    }
                    for session in sorted(
                        week.sessions,
                        key=lambda item: (
                            WEEKDAY_ORDER[item.weekday.value],
                            item.display_order,
                        ),
                    )
                ],
            }
            for week in sorted(version.weeks, key=lambda item: item.week_number)
        ],
    }


def training_program_detail_out(program: TrainingProgram) -> dict:
    draft = _draft(program)
    published = _published(program)
    versions = sorted(program.versions, key=lambda item: item.version_number, reverse=True)
    return {
        "id": program.id,
        "owner_coach_id": program.owner_coach_id,
        "status": program.status,
        "current_published_version_id": program.current_published_version_id,
        "cloned_from_program_id": program.cloned_from_program_id,
        "created_at": program.created_at,
        "updated_at": program.updated_at,
        "archived_at": program.archived_at,
        "draft_version": _version_out(draft) if draft else None,
        "published_version": _version_out(published) if published else None,
        "versions": [
            {
                "id": item.id,
                "version_number": item.version_number,
                "version_status": item.version_status.value,
                "draft_revision": item.draft_revision,
                "name": item.name,
                "content_hash": item.content_hash,
                "updated_at": item.updated_at,
                "published_at": item.published_at,
            }
            for item in versions
        ],
    }


def get_training_program(db: Session, coach: User, program_id: uuid.UUID) -> dict:
    program = TrainingProgramRepository(db).get_owned(coach.id, program_id)
    if program is None:
        raise program_not_found()
    return training_program_detail_out(program)


def list_training_programs(
    db: Session,
    coach: User,
    *,
    page: int,
    per_page: int,
    status: TrainingProgramStatus | None,
    goal_tag: str | None,
    search: str | None,
) -> dict:
    items = []
    normalized_tag = goal_tag.strip().lower() if goal_tag else None
    normalized_search = search.strip().lower() if search else None
    for program in TrainingProgramRepository(db).list_owned(coach.id):
        if status is not None and program.status != status:
            continue
        draft = _draft(program)
        published = _published(program)
        selected = draft or published
        if selected is None:
            continue
        if normalized_tag and normalized_tag not in selected.goal_tags:
            continue
        if normalized_search and normalized_search not in (
            f"{selected.name} {selected.description or ''}".lower()
        ):
            continue
        items.append(
            {
                "id": program.id,
                "status": program.status,
                "name": selected.name,
                "goal_tags": selected.goal_tags,
                "duration_weeks": selected.duration_weeks,
                "workout_slot_count": sum(len(week.sessions) for week in selected.weeks),
                "deload_week_count": sum(week.is_deload for week in selected.weeks),
                "current_published_version_number": published.version_number if published else None,
                "published_at": published.published_at if published else None,
                "has_draft": draft is not None,
                "created_at": program.created_at,
                "updated_at": program.updated_at,
                "archived_at": program.archived_at,
            }
        )
    total = len(items)
    start = (page - 1) * per_page
    return {"items": items[start : start + per_page], "page": page, "per_page": per_page, "total": total}


def create_training_program(
    db: Session, coach: User, body: TrainingProgramCreateRequest
) -> dict:
    repository = TrainingProgramRepository(db)
    _validate_graph(repository, coach, body)
    program = TrainingProgram(owner_coach_id=coach.id, status=TrainingProgramStatus.ACTIVE)
    version = TrainingProgramVersion(
        training_program=program,
        version_number=1,
        version_status=TrainingProgramVersionStatus.DRAFT,
        draft_revision=1,
        created_by_user_id=coach.id,
    )
    _replace_graph(db, version, body, increment_revision=False)
    db.add(program)
    db.commit()
    return get_training_program(db, coach, program.id)


def replace_training_program_draft(
    db: Session,
    coach: User,
    program_id: uuid.UUID,
    body: TrainingProgramDraftReplaceRequest,
) -> dict:
    program = _owned_active_program(db, coach, program_id)
    draft = _draft(program)
    if draft is None:
        raise _conflict("training_program_draft_missing", "Create a revision before editing a published program")
    if draft.draft_revision != body.expected_draft_revision:
        raise _conflict("training_program_draft_conflict", "The draft changed since it was loaded; reload before saving")
    _validate_graph(TrainingProgramRepository(db), coach, body)
    _replace_graph(db, draft, body, increment_revision=True)
    program.updated_at = datetime.now(UTC)
    db.commit()
    return get_training_program(db, coach, program.id)


def _stored_draft_data(version: TrainingProgramVersion) -> TrainingProgramDraftData:
    return TrainingProgramDraftData.model_validate(
        {
            **{field: getattr(version, field) for field in PROGRAM_FIELDS},
            "weeks": [
                {
                    "week_number": week.week_number,
                    "label": week.label,
                    "coach_notes": week.coach_notes,
                    "is_deload": week.is_deload,
                    "sessions": [
                        {field: getattr(session, field) for field in ProgramSessionData.model_fields}
                        for session in week.sessions
                    ],
                }
                for week in version.weeks
            ],
        }
    )


def publish_training_program_draft(
    db: Session, coach: User, program_id: uuid.UUID
) -> dict:
    program = _owned_active_program(db, coach, program_id)
    draft = _draft(program)
    if draft is None:
        if _published(program) is not None:
            return training_program_detail_out(program)
        raise _conflict("training_program_draft_missing", "No draft is available to publish")
    _validate_graph(TrainingProgramRepository(db), coach, _stored_draft_data(draft))
    now = datetime.now(UTC)
    draft.content_hash = training_program_content_hash(draft)
    draft.version_status = TrainingProgramVersionStatus.PUBLISHED
    draft.published_at = now
    draft.updated_at = now
    program.current_published_version_id = draft.id
    program.updated_at = now
    db.commit()
    return get_training_program(db, coach, program.id)


def _clone_version(
    source: TrainingProgramVersion, coach_id: uuid.UUID
) -> TrainingProgramVersion:
    clone = TrainingProgramVersion(
        version_number=source.version_number + 1,
        version_status=TrainingProgramVersionStatus.DRAFT,
        draft_revision=1,
        created_by_user_id=coach_id,
        **{field: getattr(source, field) for field in PROGRAM_FIELDS},
    )
    for week in source.weeks:
        week_clone = ProgramWeek(
            week_number=week.week_number,
            label=week.label,
            coach_notes=week.coach_notes,
            is_deload=week.is_deload,
        )
        week_clone.sessions = [
            ProgramSession(
                **{field: getattr(session, field) for field in ProgramSessionData.model_fields}
            )
            for session in week.sessions
        ]
        clone.weeks.append(week_clone)
    return clone


def create_training_program_revision(
    db: Session, coach: User, program_id: uuid.UUID
) -> dict:
    program = _owned_active_program(db, coach, program_id)
    if _draft(program) is not None:
        raise _conflict("training_program_draft_exists", "This program already has a draft")
    published = _published(program)
    if published is None:
        raise _conflict("training_program_unpublished", "Publish the initial draft first")
    clone = _clone_version(published, coach.id)
    clone.version_number = TrainingProgramRepository(db).next_version_number(program.id)
    program.versions.append(clone)
    program.updated_at = datetime.now(UTC)
    db.commit()
    return get_training_program(db, coach, program.id)


def archive_training_program(
    db: Session, coach: User, program_id: uuid.UUID
) -> dict:
    program = TrainingProgramRepository(db).get_owned(coach.id, program_id)
    if program is None:
        raise program_not_found()
    if program.status == TrainingProgramStatus.ACTIVE:
        now = datetime.now(UTC)
        program.status = TrainingProgramStatus.ARCHIVED
        program.archived_at = now
        program.updated_at = now
        db.commit()
    return get_training_program(db, coach, program.id)
