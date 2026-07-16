import hashlib
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.domain.units import canonical_kilograms, canonical_meters, quantize_measurement
from app.models import (
    ExerciseTrackingMode,
    ExerciseVersion,
    User,
    WorkoutSetPrescription,
    WorkoutTemplate,
    WorkoutTemplateExercise,
    WorkoutTemplateSection,
    WorkoutTemplateStatus,
    WorkoutTemplateVersion,
    WorkoutTemplateVersionStatus,
)
from app.repositories.workout_templates import WorkoutTemplateRepository
from app.schemas import (
    WorkoutSetPrescriptionData,
    WorkoutTemplateCreateRequest,
    WorkoutTemplateDraftData,
    WorkoutTemplateDraftReplaceRequest,
    WorkoutTemplateExerciseData,
)

TEMPLATE_FIELDS = (
    "name",
    "description",
    "goal_tags",
    "estimated_duration_minutes",
    "target_session_rpe",
    "coach_notes",
    "trainee_instructions",
)
SECTION_ORDER = {
    WorkoutTemplateSection.WARM_UP: 0,
    WorkoutTemplateSection.MAIN: 1,
    WorkoutTemplateSection.COOL_DOWN: 2,
}


def _error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def template_not_found() -> HTTPException:
    return _error(404, "workout_template_not_found", "Workout template not found")


def _conflict(code: str, message: str) -> HTTPException:
    return _error(409, code, message)


def _invalid(code: str, message: str) -> HTTPException:
    return _error(422, code, message)


def _draft(template: WorkoutTemplate) -> WorkoutTemplateVersion | None:
    return next(
        (
            version
            for version in template.versions
            if version.version_status == WorkoutTemplateVersionStatus.DRAFT
        ),
        None,
    )


def _published(template: WorkoutTemplate) -> WorkoutTemplateVersion | None:
    if template.current_published_version_id is None:
        return None
    return next(
        (
            version
            for version in template.versions
            if version.id == template.current_published_version_id
        ),
        None,
    )


def _owned_active_template(db: Session, coach: User, template_id: uuid.UUID) -> WorkoutTemplate:
    template = WorkoutTemplateRepository(db).get_owned_for_update(coach.id, template_id)
    if template is None:
        raise template_not_found()
    if template.status == WorkoutTemplateStatus.ARCHIVED:
        raise _conflict(
            "workout_template_archived", "Archived workout templates cannot be changed"
        )
    return template


def _validate_contiguous_orders(exercises: list[WorkoutTemplateExerciseData]) -> None:
    section_orders: dict[WorkoutTemplateSection, list[int]] = defaultdict(list)
    for exercise in exercises:
        section_orders[exercise.section].append(exercise.display_order)
        set_numbers = [item.set_number for item in exercise.sets]
        if sorted(set_numbers) != list(range(1, len(set_numbers) + 1)):
            raise _invalid(
                "invalid_set_order",
                "Set numbers must be unique and contiguous, beginning with one",
            )
    for orders in section_orders.values():
        if sorted(orders) != list(range(1, len(orders) + 1)):
            raise _invalid(
                "invalid_exercise_order",
                "Exercise display order must be unique and contiguous within each section",
            )


def _present(value: object | None) -> bool:
    return value is not None


def validate_set_for_tracking_mode(
    item: WorkoutSetPrescriptionData, tracking_mode: ExerciseTrackingMode
) -> None:
    has_repetitions = _present(item.repetitions_min)
    has_duration = _present(item.target_duration_seconds)
    has_distance = _present(item.target_distance_value)
    has_load = _present(item.target_load_original_value)
    has_assistance = _present(item.target_assistance_original_value)
    has_rir = _present(item.target_rir)
    has_tempo = _present(item.tempo)

    if tracking_mode == ExerciseTrackingMode.REPETITIONS_AND_LOAD:
        valid = has_repetitions and not any(
            (has_duration, has_distance, has_assistance, has_rir)
        )
    elif tracking_mode == ExerciseTrackingMode.REPETITIONS_ONLY:
        valid = has_repetitions and not any(
            (has_duration, has_distance, has_load, has_assistance)
        )
    elif tracking_mode == ExerciseTrackingMode.DURATION:
        valid = has_duration and not any(
            (has_repetitions, has_distance, has_load, has_assistance, has_rir, has_tempo)
        )
    elif tracking_mode == ExerciseTrackingMode.DISTANCE_AND_DURATION:
        valid = has_distance and has_duration and not any(
            (has_repetitions, has_load, has_assistance, has_rir, has_tempo)
        )
    else:
        valid = has_repetitions and not any(
            (has_duration, has_distance, has_load)
        )
    if not valid:
        raise _invalid(
            "tracking_mode_mismatch",
            f"Set prescription fields do not match {tracking_mode.value}",
        )


def _validate_graph(
    repository: WorkoutTemplateRepository,
    coach: User,
    body: WorkoutTemplateDraftData,
) -> list[tuple[WorkoutTemplateExerciseData, ExerciseVersion]]:
    _validate_contiguous_orders(body.exercises)
    resolved: list[tuple[WorkoutTemplateExerciseData, ExerciseVersion]] = []
    for exercise_data in body.exercises:
        exercise_version = repository.get_selectable_exercise_version(
            coach.id, exercise_data.exercise_version_id
        )
        if exercise_version is None:
            raise _invalid(
                "exercise_version_not_selectable",
                "Exercise version must be published, active, and visible to the coach",
            )
        for set_data in exercise_data.sets:
            validate_set_for_tracking_mode(set_data, exercise_version.tracking_mode)
        resolved.append((exercise_data, exercise_version))
    return resolved


def _set_values(data: WorkoutSetPrescriptionData) -> dict:
    load_value = (
        quantize_measurement(data.target_load_original_value)
        if data.target_load_original_value is not None
        else None
    )
    assistance_value = (
        quantize_measurement(data.target_assistance_original_value)
        if data.target_assistance_original_value is not None
        else None
    )
    distance_value = (
        quantize_measurement(data.target_distance_value)
        if data.target_distance_value is not None
        else None
    )
    return {
        **data.model_dump(mode="python"),
        "target_distance_value": distance_value,
        "target_load_original_value": load_value,
        "target_load_canonical_kg": (
            canonical_kilograms(load_value, data.target_load_original_unit)
            if load_value is not None and data.target_load_original_unit is not None
            else None
        ),
        "target_assistance_original_value": assistance_value,
        "target_assistance_canonical_kg": (
            canonical_kilograms(assistance_value, data.target_assistance_original_unit)
            if assistance_value is not None
            and data.target_assistance_original_unit is not None
            else None
        ),
    }


def _replace_graph(
    db: Session,
    version: WorkoutTemplateVersion,
    body: WorkoutTemplateDraftData,
    resolved: list[tuple[WorkoutTemplateExerciseData, ExerciseVersion]],
    *,
    increment_revision: bool,
) -> None:
    for field in TEMPLATE_FIELDS:
        setattr(version, field, getattr(body, field))
    if version.exercises:
        version.exercises.clear()
        db.flush()
    for exercise_data, _exercise_version in resolved:
        template_exercise = WorkoutTemplateExercise(
            exercise_version_id=exercise_data.exercise_version_id,
            section=exercise_data.section,
            display_order=exercise_data.display_order,
            coach_notes=exercise_data.coach_notes,
            trainee_instructions=exercise_data.trainee_instructions,
        )
        template_exercise.sets = [
            WorkoutSetPrescription(**_set_values(set_data))
            for set_data in exercise_data.sets
        ]
        version.exercises.append(template_exercise)
    if increment_revision:
        version.draft_revision += 1
    version.updated_at = datetime.now(UTC)


def _decimal_string(value: Decimal | None) -> str | None:
    return format(value, "f") if value is not None else None


def workout_template_content_hash(version: WorkoutTemplateVersion) -> str:
    exercises = []
    ordered_exercises = sorted(
        version.exercises,
        key=lambda item: (SECTION_ORDER[item.section], item.display_order),
    )
    for exercise in ordered_exercises:
        sets = []
        for item in sorted(exercise.sets, key=lambda current: current.set_number):
            distance_meters = (
                canonical_meters(item.target_distance_value, item.target_distance_unit)
                if item.target_distance_value is not None
                and item.target_distance_unit is not None
                else None
            )
            sets.append(
                {
                    "set_number": item.set_number,
                    "set_type": item.set_type.value,
                    "repetitions_min": item.repetitions_min,
                    "repetitions_max": item.repetitions_max,
                    "target_duration_seconds": item.target_duration_seconds,
                    "target_distance_value": _decimal_string(item.target_distance_value),
                    "target_distance_unit": (
                        item.target_distance_unit.value if item.target_distance_unit else None
                    ),
                    "target_distance_canonical_meters": _decimal_string(distance_meters),
                    "target_load_original_value": _decimal_string(
                        item.target_load_original_value
                    ),
                    "target_load_original_unit": (
                        item.target_load_original_unit.value
                        if item.target_load_original_unit
                        else None
                    ),
                    "target_load_canonical_kg": _decimal_string(
                        item.target_load_canonical_kg
                    ),
                    "target_assistance_original_value": _decimal_string(
                        item.target_assistance_original_value
                    ),
                    "target_assistance_original_unit": (
                        item.target_assistance_original_unit.value
                        if item.target_assistance_original_unit
                        else None
                    ),
                    "target_assistance_canonical_kg": _decimal_string(
                        item.target_assistance_canonical_kg
                    ),
                    "target_rpe": _decimal_string(item.target_rpe),
                    "target_rir": _decimal_string(item.target_rir),
                    "rest_seconds": item.rest_seconds,
                    "tempo": item.tempo,
                    "instructions": item.instructions,
                }
            )
        exercises.append(
            {
                "exercise_version_id": str(exercise.exercise_version_id),
                "section": exercise.section.value,
                "display_order": exercise.display_order,
                "coach_notes": exercise.coach_notes,
                "trainee_instructions": exercise.trainee_instructions,
                "sets": sets,
            }
        )
    payload = {
        "name": version.name,
        "description": version.description,
        "goal_tags": sorted(version.goal_tags),
        "estimated_duration_minutes": version.estimated_duration_minutes,
        "target_session_rpe": (
            format(Decimal(str(version.target_session_rpe)), "f")
            if version.target_session_rpe is not None
            else None
        ),
        "coach_notes": version.coach_notes,
        "trainee_instructions": version.trainee_instructions,
        "exercises": exercises,
    }
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _set_out(item: WorkoutSetPrescription) -> dict:
    return {
        "id": item.id,
        "set_number": item.set_number,
        "set_type": item.set_type,
        "repetitions_min": item.repetitions_min,
        "repetitions_max": item.repetitions_max,
        "target_duration_seconds": item.target_duration_seconds,
        "target_distance_value": item.target_distance_value,
        "target_distance_unit": item.target_distance_unit,
        "target_load_original_value": item.target_load_original_value,
        "target_load_original_unit": item.target_load_original_unit,
        "target_load_canonical_kg": item.target_load_canonical_kg,
        "target_assistance_original_value": item.target_assistance_original_value,
        "target_assistance_original_unit": item.target_assistance_original_unit,
        "target_assistance_canonical_kg": item.target_assistance_canonical_kg,
        "target_rpe": item.target_rpe,
        "target_rir": item.target_rir,
        "rest_seconds": item.rest_seconds,
        "tempo": item.tempo,
        "instructions": item.instructions,
        "created_at": item.created_at,
    }


def _version_out(version: WorkoutTemplateVersion) -> dict:
    exercises = sorted(
        version.exercises,
        key=lambda item: (SECTION_ORDER[item.section], item.display_order),
    )
    return {
        "id": version.id,
        "workout_template_id": version.workout_template_id,
        "version_number": version.version_number,
        "version_status": version.version_status.value,
        "draft_revision": version.draft_revision,
        **{field: getattr(version, field) for field in TEMPLATE_FIELDS},
        "content_hash": version.content_hash,
        "created_by_user_id": version.created_by_user_id,
        "created_at": version.created_at,
        "updated_at": version.updated_at,
        "published_at": version.published_at,
        "exercises": [
            {
                "id": exercise.id,
                "exercise_version_id": exercise.exercise_version_id,
                "section": exercise.section,
                "display_order": exercise.display_order,
                "coach_notes": exercise.coach_notes,
                "trainee_instructions": exercise.trainee_instructions,
                "created_at": exercise.created_at,
                "sets": [
                    _set_out(item)
                    for item in sorted(exercise.sets, key=lambda current: current.set_number)
                ],
            }
            for exercise in exercises
        ],
    }


def template_detail_out(template: WorkoutTemplate) -> dict:
    draft = _draft(template)
    published = _published(template)
    versions = sorted(template.versions, key=lambda item: item.version_number, reverse=True)
    return {
        "id": template.id,
        "owner_coach_id": template.owner_coach_id,
        "status": template.status,
        "current_published_version_id": template.current_published_version_id,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "archived_at": template.archived_at,
        "draft_version": _version_out(draft) if draft else None,
        "published_version": _version_out(published) if published else None,
        "versions": [
            {
                "id": version.id,
                "version_number": version.version_number,
                "version_status": version.version_status.value,
                "draft_revision": version.draft_revision,
                "name": version.name,
                "content_hash": version.content_hash,
                "updated_at": version.updated_at,
                "published_at": version.published_at,
            }
            for version in versions
        ],
    }


def get_workout_template(
    db: Session, coach: User, template_id: uuid.UUID
) -> dict:
    template = WorkoutTemplateRepository(db).get_owned_for_update(coach.id, template_id)
    if template is None:
        raise template_not_found()
    return template_detail_out(template)


def list_workout_templates(
    db: Session,
    coach: User,
    *,
    page: int,
    per_page: int,
    status: WorkoutTemplateStatus | None,
    goal_tag: str | None,
    search: str | None,
) -> dict:
    templates = WorkoutTemplateRepository(db).list_owned(coach.id)
    items = []
    normalized_tag = goal_tag.strip().lower() if goal_tag else None
    normalized_search = search.strip().lower() if search else None
    for template in templates:
        if status is not None and template.status != status:
            continue
        draft = _draft(template)
        published = _published(template)
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
                "id": template.id,
                "status": template.status,
                "name": selected.name,
                "goal_tags": selected.goal_tags,
                "estimated_duration_minutes": selected.estimated_duration_minutes,
                "current_published_version_number": (
                    published.version_number if published else None
                ),
                "has_draft": draft is not None,
                "created_at": template.created_at,
                "updated_at": template.updated_at,
                "archived_at": template.archived_at,
            }
        )
    total = len(items)
    start = (page - 1) * per_page
    return {
        "items": items[start : start + per_page],
        "page": page,
        "per_page": per_page,
        "total": total,
    }


def create_workout_template(
    db: Session, coach: User, body: WorkoutTemplateCreateRequest
) -> dict:
    repository = WorkoutTemplateRepository(db)
    resolved = _validate_graph(repository, coach, body)
    template = WorkoutTemplate(
        owner_coach_id=coach.id,
        status=WorkoutTemplateStatus.ACTIVE,
    )
    version = WorkoutTemplateVersion(
        workout_template=template,
        version_number=1,
        version_status=WorkoutTemplateVersionStatus.DRAFT,
        draft_revision=1,
        created_by_user_id=coach.id,
    )
    _replace_graph(db, version, body, resolved, increment_revision=False)
    db.add(template)
    db.commit()
    return get_workout_template(db, coach, template.id)


def replace_workout_template_draft(
    db: Session,
    coach: User,
    template_id: uuid.UUID,
    body: WorkoutTemplateDraftReplaceRequest,
) -> dict:
    template = _owned_active_template(db, coach, template_id)
    draft = _draft(template)
    if draft is None:
        raise _conflict(
            "workout_template_draft_missing",
            "Create a revision before editing a published workout template",
        )
    if draft.draft_revision != body.expected_draft_revision:
        raise _conflict(
            "workout_template_draft_conflict",
            "The draft changed since it was loaded; reload before saving",
        )
    resolved = _validate_graph(WorkoutTemplateRepository(db), coach, body)
    _replace_graph(db, draft, body, resolved, increment_revision=True)
    template.updated_at = datetime.now(UTC)
    db.commit()
    return get_workout_template(db, coach, template.id)


def _stored_draft_data(version: WorkoutTemplateVersion) -> WorkoutTemplateDraftData:
    return WorkoutTemplateDraftData.model_validate(
        {
            **{field: getattr(version, field) for field in TEMPLATE_FIELDS},
            "exercises": [
                {
                    "exercise_version_id": exercise.exercise_version_id,
                    "section": exercise.section,
                    "display_order": exercise.display_order,
                    "coach_notes": exercise.coach_notes,
                    "trainee_instructions": exercise.trainee_instructions,
                    "sets": [
                        {
                            key: getattr(item, key)
                            for key in WorkoutSetPrescriptionData.model_fields
                        }
                        for item in exercise.sets
                    ],
                }
                for exercise in version.exercises
            ],
        }
    )


def publish_workout_template_draft(
    db: Session, coach: User, template_id: uuid.UUID
) -> dict:
    template = _owned_active_template(db, coach, template_id)
    draft = _draft(template)
    if draft is None:
        if _published(template) is not None:
            return template_detail_out(template)
        raise _conflict(
            "workout_template_draft_missing", "No draft is available to publish"
        )
    body = _stored_draft_data(draft)
    _validate_graph(WorkoutTemplateRepository(db), coach, body)
    now = datetime.now(UTC)
    draft.content_hash = workout_template_content_hash(draft)
    draft.version_status = WorkoutTemplateVersionStatus.PUBLISHED
    draft.published_at = now
    draft.updated_at = now
    template.current_published_version_id = draft.id
    template.updated_at = now
    db.commit()
    return get_workout_template(db, coach, template.id)


def _clone_version(source: WorkoutTemplateVersion, coach_id: uuid.UUID) -> WorkoutTemplateVersion:
    clone = WorkoutTemplateVersion(
        version_number=source.version_number + 1,
        version_status=WorkoutTemplateVersionStatus.DRAFT,
        draft_revision=1,
        created_by_user_id=coach_id,
        **{field: getattr(source, field) for field in TEMPLATE_FIELDS},
    )
    for exercise in source.exercises:
        exercise_clone = WorkoutTemplateExercise(
            exercise_version_id=exercise.exercise_version_id,
            section=exercise.section,
            display_order=exercise.display_order,
            coach_notes=exercise.coach_notes,
            trainee_instructions=exercise.trainee_instructions,
        )
        exercise_clone.sets = [
            WorkoutSetPrescription(
                **{
                    key: getattr(item, key)
                    for key in WorkoutSetPrescriptionData.model_fields
                },
                target_load_canonical_kg=item.target_load_canonical_kg,
                target_assistance_canonical_kg=item.target_assistance_canonical_kg,
            )
            for item in exercise.sets
        ]
        clone.exercises.append(exercise_clone)
    return clone


def create_workout_template_revision(
    db: Session, coach: User, template_id: uuid.UUID
) -> dict:
    template = _owned_active_template(db, coach, template_id)
    if _draft(template) is not None:
        raise _conflict(
            "workout_template_draft_exists", "This workout template already has a draft"
        )
    published = _published(template)
    if published is None:
        raise _conflict(
            "workout_template_unpublished", "Publish the initial draft first"
        )
    clone = _clone_version(published, coach.id)
    clone.version_number = WorkoutTemplateRepository(db).next_version_number(template.id)
    template.versions.append(clone)
    template.updated_at = datetime.now(UTC)
    db.commit()
    return get_workout_template(db, coach, template.id)


def archive_workout_template(
    db: Session, coach: User, template_id: uuid.UUID
) -> dict:
    template = WorkoutTemplateRepository(db).get_owned(coach.id, template_id)
    if template is None:
        raise template_not_found()
    if template.status == WorkoutTemplateStatus.ACTIVE:
        now = datetime.now(UTC)
        template.status = WorkoutTemplateStatus.ARCHIVED
        template.archived_at = now
        template.updated_at = now
        db.commit()
    return get_workout_template(db, coach, template.id)
