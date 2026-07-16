import secrets
from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import AppEnvironment, Settings, settings
from app.daily_services import calculate_and_store_daily_score, get_check_in, local_today
from app.database import SessionLocal
from app.exercise_services import exercise_content_hash
from app.models import (
    AssessmentStatus,
    CoachProfile,
    CoachTraineeAssignment,
    DailyCheckIn,
    Exercise,
    ExerciseScope,
    ExerciseStatus,
    ExerciseTrackingMode,
    ExerciseVersion,
    ExerciseVersionStatus,
    OnboardingAssessment,
    Role,
    TraineeProfile,
    TrainingProgram,
    TrainingProgramVersion,
    User,
    WorkoutTemplate,
    WorkoutTemplateVersion,
    utcnow,
)
from app.repositories.exercises import ExerciseRepository
from app.schemas import (
    AssessmentData,
    TrainingProgramCreateRequest,
    WorkoutTemplateCreateRequest,
)
from app.security import hash_password
from app.services import save_assessment, submit_assessment
from app.training_program_services import (
    create_training_program,
    publish_training_program_draft,
)
from app.workout_template_services import (
    create_workout_template,
    publish_workout_template_draft,
)

COACH_EMAIL = "coach@fitness.example.com"
TRAINEE_EMAIL = "trainee@fitness.example.com"
DEMO_PASSWORD = "DemoPass123!"
NO_CHECKIN_EMAIL = "no-checkins@fitness.example.com"

DEMO_SCENARIOS: tuple[dict[str, Any], ...] = (
    {
        "email_setting": "demo_trainee_email",
        "first_name": "Aarav",
        "last_name": "Improving",
        "pattern": "improving",
        "missing": {6, 13},
    },
    {
        "email": "demo.low-readiness@fitness.example.com",
        "first_name": "Mira",
        "last_name": "Low Readiness",
        "pattern": "low_readiness",
        "missing": {12},
    },
    {
        "email": "demo.activity@fitness.example.com",
        "first_name": "Kabir",
        "last_name": "Activity Gap",
        "pattern": "activity_gap",
        "missing": {7, 15},
    },
    {
        "email": "demo.hydration@fitness.example.com",
        "first_name": "Anika",
        "last_name": "Hydration Review",
        "pattern": "hydration",
        "missing": {10},
        "baseline": {"hydration_ml": 1400},
    },
    {
        "email": "demo.stress@fitness.example.com",
        "first_name": "Dev",
        "last_name": "Stress Review",
        "pattern": "stress_sleep",
        "missing": {8},
        "baseline": {"sleep_hours": 5.8, "sleep_quality": 2, "stress_level": 8},
    },
    {
        "email": "demo.missing@fitness.example.com",
        "first_name": "Isha",
        "last_name": "Missing Check-ins",
        "pattern": "missing",
        "missing": set(range(21)) - {0, 3, 9, 16},
    },
    {
        "email": "demo.stable@fitness.example.com",
        "first_name": "Rohan",
        "last_name": "Steady Performer",
        "pattern": "stable_high",
        "missing": set(),
    },
)

BASELINE = {
    "age": 31,
    "height_cm": 176,
    "weight_kg": 75,
    "selected_goal": "general_health",
    "target_weight_kg": 72,
    "hydration_ml": 2500,
    "sleep_hours": 7.5,
    "sleep_quality": 4,
    "wake_refreshed": True,
    "daily_steps": 8500,
    "activity_types": ["walking", "strength_training"],
    "activity_minutes_weekly": 180,
    "workout_frequency_weekly": 3,
    "average_rpe": 7,
    "workout_duration_minutes": 50,
    "perceived_recovery": 4,
    "stress_level": 4,
    "resting_heart_rate": 64,
    "palpitations": False,
    "shortness_of_breath": False,
    "chest_pain": False,
    "calorie_mode": "maintenance",
    "calorie_target": 2200,
    "calorie_intake": 2150,
    "protein_target_g": 110,
    "protein_intake_g": 105,
    "carbohydrate_intake_g": 250,
    "healthy_fat_intake_g": 70,
    "fruit_servings": 2,
    "vegetable_servings": 3,
    "fiber_g": 30,
    "meal_consistency": 4,
}

DAILY_VALUES = [
    # Oldest to newest; offset four is intentionally missing.
    (7, 8.0, 3, 2, 9000, True, 45, 6, 2.6, "good"),
    (6, 8.3, 2, 2, 11000, True, 55, 7, 2.8, "excellent"),
    (5, 7.6, 4, 3, 8000, False, None, None, 2.4, "good"),
    (3, 7.8, 3, 3, 9500, True, 40, 6, 2.5, "good"),
    (2, 5.8, 8, 8, 4200, True, 75, 9, 1.2, "poor"),
    (1, 5.6, 8, 8, 3500, True, 80, 9, 1.1, "poor"),
    (0, 4.8, 9, 9, 2800, True, 90, 9, 1.0, "very_poor"),
]

SYSTEM_EXERCISES: tuple[dict[str, Any], ...] = (
    {
        "slug": "dumbbell-goblet-squat",
        "name": "Dumbbell goblet squat",
        "tracking_mode": ExerciseTrackingMode.REPETITIONS_AND_LOAD,
        "category": "strength",
        "movement_pattern": "squat",
        "equipment": ["dumbbell"],
        "primary_muscle_groups": ["quadriceps", "glutes"],
        "secondary_muscle_groups": ["core"],
        "unilateral": False,
        "instructions": "Hold one dumbbell at the chest and squat with controlled depth.",
        "safety_cues": ["Keep the knees tracking in line with the toes."],
    },
    {
        "slug": "dead-bug",
        "name": "Dead bug",
        "tracking_mode": ExerciseTrackingMode.REPETITIONS_ONLY,
        "category": "core",
        "movement_pattern": "anti-extension",
        "equipment": [],
        "primary_muscle_groups": ["core"],
        "secondary_muscle_groups": [],
        "unilateral": True,
        "instructions": "Alternate lowering opposite limbs while keeping the trunk controlled.",
        "safety_cues": ["Use a range that allows the lower back to remain controlled."],
    },
    {
        "slug": "front-plank",
        "name": "Front plank",
        "tracking_mode": ExerciseTrackingMode.DURATION,
        "category": "core",
        "movement_pattern": "isometric",
        "equipment": ["exercise mat"],
        "primary_muscle_groups": ["core"],
        "secondary_muscle_groups": ["shoulders"],
        "unilateral": False,
        "instructions": "Hold a straight, braced position supported by forearms and feet.",
        "safety_cues": ["End the hold if position cannot be maintained comfortably."],
    },
    {
        "slug": "treadmill-walk",
        "name": "Treadmill walk",
        "tracking_mode": ExerciseTrackingMode.DISTANCE_AND_DURATION,
        "category": "cardio",
        "movement_pattern": "walking",
        "equipment": ["treadmill"],
        "primary_muscle_groups": ["lower body"],
        "secondary_muscle_groups": [],
        "unilateral": False,
        "instructions": "Walk at a controlled pace for the planned distance and duration.",
        "safety_cues": ["Use the safety stop and step off if balance feels uncertain."],
    },
    {
        "slug": "assisted-pull-up",
        "name": "Assisted pull-up",
        "tracking_mode": ExerciseTrackingMode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "category": "strength",
        "movement_pattern": "vertical pull",
        "equipment": ["pull-up station"],
        "primary_muscle_groups": ["back"],
        "secondary_muscle_groups": ["biceps"],
        "unilateral": False,
        "instructions": "Complete controlled pull-up repetitions with optional assistance.",
        "safety_cues": ["Avoid dropping rapidly into the bottom position."],
    },
)

PRIVATE_EXERCISES: tuple[dict[str, Any], ...] = (
    {
        "slug": "coach-tempo-split-squat",
        "name": "Coach tempo split squat",
        "tracking_mode": ExerciseTrackingMode.REPETITIONS_ONLY,
        "category": "strength",
        "movement_pattern": "lunge",
        "equipment": [],
        "primary_muscle_groups": ["quadriceps", "glutes"],
        "secondary_muscle_groups": ["core"],
        "unilateral": True,
        "instructions": "Use the coach-defined controlled tempo for each split-squat repetition.",
        "safety_cues": ["Use stable support if balance is uncertain."],
    },
    {
        "slug": "coach-marching-carry",
        "name": "Coach marching carry",
        "tracking_mode": ExerciseTrackingMode.DURATION,
        "category": "conditioning",
        "movement_pattern": "carry",
        "equipment": ["dumbbell"],
        "primary_muscle_groups": ["core"],
        "secondary_muscle_groups": ["shoulders", "hips"],
        "unilateral": True,
        "instructions": "March in place while maintaining the coach-defined carry position.",
        "safety_cues": ["Set the load down under control if grip or posture changes."],
    },
)


def _seed_exercise(
    db,
    *,
    specification: dict[str, Any],
    scope: ExerciseScope,
    coach: User | None = None,
) -> Exercise:
    repository = ExerciseRepository(db)
    exercise = (
        repository.get_system_by_slug(specification["slug"])
        if scope == ExerciseScope.SYSTEM
        else repository.get_private_by_slug(coach.id, specification["slug"])
    )
    if exercise is None:
        exercise = Exercise(
            scope=scope,
            owner_coach_id=coach.id if coach else None,
            slug=specification["slug"],
            status=ExerciseStatus.ACTIVE,
        )
        db.add(exercise)
        db.flush()
    published = next(
        (
            item
            for item in exercise.versions
            if item.status == ExerciseVersionStatus.PUBLISHED
        ),
        None,
    )
    if published is None:
        version = ExerciseVersion(
            exercise_id=exercise.id,
            version_number=1,
            status=ExerciseVersionStatus.PUBLISHED,
            description=None,
            image_url=None,
            thumbnail_url=None,
            created_by_user_id=coach.id if coach else None,
            published_at=utcnow(),
            **{key: value for key, value in specification.items() if key != "slug"},
        )
        version.content_hash = exercise_content_hash(version)
        exercise.versions.append(version)
    return exercise


def seed_exercise_library(db, coach: User | None = None) -> None:
    """Idempotently add immutable system content and owner-private coach examples."""
    for specification in SYSTEM_EXERCISES:
        _seed_exercise(
            db, specification=specification, scope=ExerciseScope.SYSTEM
        )
    if coach is not None:
        for specification in PRIVATE_EXERCISES:
            _seed_exercise(
                db,
                specification=specification,
                scope=ExerciseScope.COACH_PRIVATE,
                coach=coach,
            )
    db.commit()


def _published_exercise_version(db, coach: User, slug: str) -> ExerciseVersion:
    version = db.scalar(
        select(ExerciseVersion)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(
            Exercise.slug == slug,
            ExerciseVersion.status == ExerciseVersionStatus.PUBLISHED,
            (Exercise.owner_coach_id.is_(None) | (Exercise.owner_coach_id == coach.id)),
        )
        .order_by(ExerciseVersion.version_number.desc())
    )
    if version is None:
        raise RuntimeError(f"Seed exercise version is missing: {slug}")
    return version


def _template_seed_payloads(db, coach: User) -> tuple[tuple[dict[str, Any], bool], ...]:
    exercise_ids = {
        slug: str(_published_exercise_version(db, coach, slug).id)
        for slug in (
            "dumbbell-goblet-squat",
            "dead-bug",
            "front-plank",
            "treadmill-walk",
            "assisted-pull-up",
            "coach-tempo-split-squat",
        )
    }
    full_body = {
        "name": "Full Body Strength",
        "description": "Synthetic strength template demonstrating immutable prescriptions.",
        "goal_tags": ["strength", "general_health"],
        "estimated_duration_minutes": 50,
        "target_session_rpe": 7,
        "coach_notes": "Seeded coach-only notes.",
        "trainee_instructions": "Move with control and stop for unusual discomfort.",
        "exercises": [
            {
                "exercise_version_id": exercise_ids["dead-bug"],
                "section": "warm_up",
                "display_order": 1,
                "sets": [
                    {
                        "set_number": 1,
                        "set_type": "warm_up",
                        "repetitions_min": 8,
                        "repetitions_max": 10,
                        "target_rir": 3,
                        "rest_seconds": 30,
                        "tempo": "2-1-2",
                    }
                ],
            },
            {
                "exercise_version_id": exercise_ids["dumbbell-goblet-squat"],
                "section": "main",
                "display_order": 1,
                "sets": [
                    {
                        "set_number": number,
                        "set_type": "working",
                        "repetitions_min": 8,
                        "repetitions_max": 10,
                        "target_load_original_value": 35,
                        "target_load_original_unit": "lb",
                        "target_rpe": 7,
                        "rest_seconds": 90,
                        "tempo": "3-1-1",
                    }
                    for number in range(1, 4)
                ],
            },
            {
                "exercise_version_id": exercise_ids["coach-tempo-split-squat"],
                "section": "main",
                "display_order": 2,
                "coach_notes": "Private coach exercise retained by exact version.",
                "sets": [
                    {
                        "set_number": number,
                        "set_type": "working",
                        "repetitions_min": 6,
                        "repetitions_max": 8,
                        "target_rpe": 7,
                        "target_rir": 2,
                        "rest_seconds": 75,
                        "tempo": "3-1-2",
                    }
                    for number in range(1, 3)
                ],
            },
        ],
    }
    recovery = {
        "name": "Recovery and Mobility",
        "description": "Synthetic low-complexity recovery and conditioning template.",
        "goal_tags": ["recovery", "endurance"],
        "estimated_duration_minutes": 35,
        "target_session_rpe": 5,
        "coach_notes": None,
        "trainee_instructions": "Keep every effort conversational and controlled.",
        "exercises": [
            {
                "exercise_version_id": exercise_ids["front-plank"],
                "section": "warm_up",
                "display_order": 1,
                "sets": [
                    {
                        "set_number": 1,
                        "set_type": "warm_up",
                        "target_duration_seconds": 30,
                        "target_rpe": 4,
                        "rest_seconds": 30,
                    }
                ],
            },
            {
                "exercise_version_id": exercise_ids["treadmill-walk"],
                "section": "main",
                "display_order": 1,
                "sets": [
                    {
                        "set_number": 1,
                        "set_type": "working",
                        "target_duration_seconds": 1200,
                        "target_distance_value": 1.5,
                        "target_distance_unit": "miles",
                        "target_rpe": 5,
                    }
                ],
            },
            {
                "exercise_version_id": exercise_ids["assisted-pull-up"],
                "section": "cool_down",
                "display_order": 1,
                "sets": [
                    {
                        "set_number": 1,
                        "set_type": "back_off",
                        "repetitions_min": 5,
                        "repetitions_max": 6,
                        "target_assistance_original_value": 20,
                        "target_assistance_original_unit": "kg",
                        "target_rir": 3,
                        "rest_seconds": 60,
                        "tempo": "2-1-2",
                    }
                ],
            },
        ],
    }
    beginner_draft = {
        "name": "Beginner Conditioning",
        "description": "Synthetic unpublished template draft.",
        "goal_tags": ["general_health"],
        "estimated_duration_minutes": 25,
        "target_session_rpe": 5,
        "coach_notes": "Draft seed; not yet selectable for future assignment.",
        "trainee_instructions": None,
        "exercises": [
            {
                "exercise_version_id": exercise_ids["dumbbell-goblet-squat"],
                "section": "main",
                "display_order": 1,
                "sets": [
                    {
                        "set_number": 1,
                        "set_type": "working",
                        "repetitions_min": 8,
                        "repetitions_max": 12,
                        "target_load_original_value": 10,
                        "target_load_original_unit": "kg",
                        "target_rpe": 5,
                        "rest_seconds": 60,
                    }
                ],
            }
        ],
    }
    return ((full_body, True), (recovery, True), (beginner_draft, False))


def seed_workout_templates(db, coach: User) -> None:
    """Idempotently seed synthetic template graphs after their exercises exist."""
    for payload, should_publish in _template_seed_payloads(db, coach):
        exists = db.scalar(
            select(WorkoutTemplate.id)
            .join(
                WorkoutTemplateVersion,
                WorkoutTemplateVersion.workout_template_id == WorkoutTemplate.id,
            )
            .where(
                WorkoutTemplate.owner_coach_id == coach.id,
                WorkoutTemplateVersion.name == payload["name"],
            )
        )
        if exists is not None:
            continue
        created = create_workout_template(
            db, coach, WorkoutTemplateCreateRequest.model_validate(payload)
        )
        if should_publish:
            publish_workout_template_draft(db, coach, created["id"])


def _published_template_version(db, coach: User, name: str) -> WorkoutTemplateVersion:
    version = db.scalar(
        select(WorkoutTemplateVersion)
        .join(
            WorkoutTemplate,
            WorkoutTemplate.id == WorkoutTemplateVersion.workout_template_id,
        )
        .where(
            WorkoutTemplate.owner_coach_id == coach.id,
            WorkoutTemplateVersion.name == name,
            WorkoutTemplateVersion.version_status == "published",
        )
    )
    if version is None:
        raise RuntimeError(f"Seed workout template version is missing: {name}")
    return version


def _program_payloads(db, coach: User) -> tuple[tuple[dict[str, Any], bool], ...]:
    strength = _published_template_version(db, coach, "Full Body Strength")
    recovery = _published_template_version(db, coach, "Recovery and Mobility")
    weeks = []
    for week_number in range(1, 5):
        sessions = [
            {
                "workout_template_version_id": str(strength.id),
                "weekday": "monday",
                "display_order": 1,
                "required": True,
                "planned_duration_override_minutes": None,
                "target_session_rpe_override": 6 if week_number == 4 else 7,
                "coach_notes": "Coach-authored lower-intensity context." if week_number == 4 else None,
                "trainee_instructions": "Prioritize controlled technique.",
            },
            {
                "workout_template_version_id": str(recovery.id),
                "weekday": "thursday",
                "display_order": 1,
                "required": True,
                "planned_duration_override_minutes": None,
                "target_session_rpe_override": None,
                "coach_notes": None,
                "trainee_instructions": "Keep the effort conversational.",
            },
        ]
        if week_number == 2:
            sessions.append(
                {
                    "workout_template_version_id": str(recovery.id),
                    "weekday": "thursday",
                    "display_order": 2,
                    "required": False,
                    "planned_duration_override_minutes": 20,
                    "target_session_rpe_override": 4,
                    "coach_notes": None,
                    "trainee_instructions": "Optional mobility extension.",
                }
            )
        weeks.append(
            {
                "week_number": week_number,
                "label": "Coach-authored deload" if week_number == 4 else f"Build week {week_number}",
                "coach_notes": "No automatic reductions are applied." if week_number == 4 else None,
                "is_deload": week_number == 4,
                "sessions": sessions,
            }
        )
    published = {
        "name": "Four Week Strength Foundation",
        "description": "Synthetic four-week reusable program with exact template versions.",
        "goal_tags": ["strength", "general_health"],
        "duration_weeks": 4,
        "coach_notes": "Synthetic coach-only program context.",
        "trainee_instructions": "Complete required workouts before optional sessions.",
        "weeks": weeks,
    }
    draft = {
        "name": "Endurance Foundation Draft",
        "description": "Synthetic unpublished multi-week program draft.",
        "goal_tags": ["endurance"],
        "duration_weeks": 2,
        "coach_notes": "Draft content only.",
        "trainee_instructions": None,
        "weeks": [
            {
                "week_number": number,
                "label": f"Foundation week {number}",
                "coach_notes": None,
                "is_deload": False,
                "sessions": [
                    {
                        "workout_template_version_id": str(recovery.id),
                        "weekday": "tuesday",
                        "display_order": 1,
                        "required": True,
                    }
                ],
            }
            for number in range(1, 3)
        ],
    }
    return ((published, True), (draft, False))


def seed_training_programs(db, coach: User) -> None:
    """Idempotently seed synthetic program graphs after published templates exist."""
    for payload, should_publish in _program_payloads(db, coach):
        exists = db.scalar(
            select(TrainingProgram.id)
            .join(
                TrainingProgramVersion,
                TrainingProgramVersion.training_program_id == TrainingProgram.id,
            )
            .where(
                TrainingProgram.owner_coach_id == coach.id,
                TrainingProgramVersion.name == payload["name"],
            )
        )
        if exists is not None:
            continue
        created = create_training_program(
            db, coach, TrainingProgramCreateRequest.model_validate(payload)
        )
        if should_publish:
            publish_training_program_draft(db, coach, created["id"])


def ensure_seed_allowed(config: Settings = settings) -> None:
    if not config.seed_demo_data:
        raise RuntimeError("Demo seeding is disabled; set SEED_DEMO_DATA=true explicitly")
    if config.app_env is AppEnvironment.PRODUCTION:
        raise RuntimeError("Demo seeding is not allowed in production")


def _demo_check_in(pattern: str, offset: int) -> dict[str, Any]:
    progress = 20 - offset
    exercised = offset % 2 == 0
    values: dict[str, Any] = {
        "sleep_hours": 7.2,
        "sleep_quality": 4,
        "wake_refreshed": True,
        "soreness": 3,
        "fatigue": 3,
        "stress": 4,
        "steps": 8200,
        "exercised": exercised,
        "exercise_minutes": 45 if exercised else None,
        "session_rpe": 6 if exercised else None,
        "activity_types": ["strength_training"] if exercised else [],
        "water_liters": 2.4,
        "calories_consumed": 2150,
        "protein_grams": 105,
        "nutrition_adherence": 86,
        "overall_feeling": "good",
        "note": None,
    }
    if pattern == "improving":
        values.update(
            sleep_hours=min(8.2, 6.2 + progress * 0.09),
            sleep_quality=3 if progress < 7 else 4,
            wake_refreshed=progress >= 7,
            soreness=max(2, 6 - progress // 5),
            fatigue=max(2, 6 - progress // 5),
            stress=max(2, 6 - progress // 6),
            steps=6000 + progress * 280,
            water_liters=min(2.8, 1.8 + progress * 0.05),
            protein_grams=80 if offset <= 2 else 105,
            nutrition_adherence=72 if offset <= 2 else 86,
            overall_feeling="excellent" if progress >= 16 else "good",
        )
    elif pattern == "low_readiness" and offset <= 3:
        values.update(
            sleep_hours=4.6,
            sleep_quality=1,
            wake_refreshed=False,
            soreness=8,
            fatigue=9,
            stress=9,
            steps=2600,
            exercised=True,
            exercise_minutes=85,
            session_rpe=9,
            water_liters=1.1,
            protein_grams=65,
            nutrition_adherence=48,
            overall_feeling="very_poor",
        )
    elif pattern == "activity_gap":
        values.update(
            steps=2200 + (offset % 3) * 400,
            exercised=offset % 6 == 0,
            exercise_minutes=20 if offset % 6 == 0 else None,
            session_rpe=4 if offset % 6 == 0 else None,
            activity_types=["walking"] if offset % 6 == 0 else [],
            overall_feeling="okay",
        )
    elif pattern == "hydration":
        values.update(water_liters=0.9, nutrition_adherence=58, overall_feeling="okay")
    elif pattern == "stress_sleep":
        values.update(
            sleep_hours=5.2,
            sleep_quality=2,
            wake_refreshed=False,
            fatigue=7,
            stress=9,
            steps=5200,
            overall_feeling="poor",
        )
    elif pattern == "stable_high":
        values.update(
            sleep_hours=8.1,
            sleep_quality=5,
            soreness=2,
            fatigue=2,
            stress=2,
            steps=11800,
            water_liters=2.9,
            protein_grams=120,
            nutrition_adherence=94,
            overall_feeling="excellent",
        )
    return values


def _ensure_demo_user(
    db,
    *,
    email: str,
    first_name: str,
    last_name: str,
    role: Role,
) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is not None and not user.is_demo:
        raise RuntimeError(f"Refusing to replace non-demo account at {email}")
    if user is None:
        user = User(
            email=email,
            password_hash=hash_password(secrets.token_urlsafe(48)),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_demo=True,
        )
        db.add(user)
        db.flush()
    else:
        user.first_name = first_name
        user.last_name = last_name
        user.role = role
        user.status = "active"
        user.is_demo = True
    return user


def seed_public_demo_workspace(
    db, config: Settings = settings, current_time: datetime | None = None
) -> None:
    now = current_time or datetime.now(UTC)
    coach = _ensure_demo_user(
        db,
        email=config.demo_coach_email,
        first_name="Maya",
        last_name="Demo Coach",
        role=Role.COACH,
    )
    coach_profile = db.scalar(select(CoachProfile).where(CoachProfile.user_id == coach.id))
    if coach_profile is None:
        db.add(
            CoachProfile(
                user_id=coach.id,
                display_name="Maya Demo Coach",
                credentials_text="Synthetic public demo profile; credentials are not verified.",
            )
        )
    seed_exercise_library(db, coach)
    seed_workout_templates(db, coach)
    seed_training_programs(db, coach)

    for scenario in DEMO_SCENARIOS:
        email = (
            getattr(config, scenario["email_setting"])
            if scenario.get("email_setting")
            else scenario["email"]
        )
        trainee = _ensure_demo_user(
            db,
            email=email,
            first_name=scenario["first_name"],
            last_name=scenario["last_name"],
            role=Role.TRAINEE,
        )
        profile = db.scalar(
            select(TraineeProfile).where(TraineeProfile.user_id == trainee.id)
        )
        if profile is None:
            profile = TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata")
            db.add(profile)
        else:
            profile.timezone = "Asia/Kolkata"
        assignment = db.scalar(
            select(CoachTraineeAssignment).where(
                CoachTraineeAssignment.coach_id == coach.id,
                CoachTraineeAssignment.trainee_id == trainee.id,
            )
        )
        if assignment is None:
            db.add(
                CoachTraineeAssignment(
                    coach_id=coach.id,
                    trainee_id=trainee.id,
                    accepted_at=now,
                )
            )
        else:
            assignment.status = "active"
            assignment.accepted_at = assignment.accepted_at or now
        db.commit()

        submitted = db.scalar(
            select(OnboardingAssessment).where(
                OnboardingAssessment.trainee_id == trainee.id,
                OnboardingAssessment.status == AssessmentStatus.SUBMITTED,
            )
        )
        if submitted is None:
            baseline = {**BASELINE, **scenario.get("baseline", {})}
            save_assessment(db, trainee, AssessmentData.model_validate(baseline))
            submit_assessment(db, trainee)

        today = now.astimezone(ZoneInfo("Asia/Kolkata")).date()
        for offset in range(20, -1, -1):
            if offset in scenario["missing"]:
                continue
            local_date = today - timedelta(days=offset)
            timestamp = datetime.combine(
                local_date, time(12), ZoneInfo("Asia/Kolkata")
            ).astimezone(UTC)
            item = get_check_in(db, trainee.id, local_date)
            if item is None:
                item = DailyCheckIn(
                    trainee_id=trainee.id,
                    local_date=local_date,
                    timezone="Asia/Kolkata",
                    submitted_at=timestamp,
                    created_at=timestamp,
                )
                db.add(item)
            for key, value in _demo_check_in(scenario["pattern"], offset).items():
                setattr(item, key, value)
            item.updated_at = timestamp
            db.flush()
            calculate_and_store_daily_score(db, trainee.id, item, timestamp)
            db.commit()


def seed() -> None:
    ensure_seed_allowed()
    with SessionLocal() as db:
        coach = db.scalar(select(User).where(User.email == COACH_EMAIL))
        if coach is None:
            coach = User(
                email=COACH_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                first_name="Maya",
                last_name="Coach",
                role=Role.COACH,
            )
            db.add(coach)
            db.flush()
            db.add(
                CoachProfile(
                    user_id=coach.id,
                    display_name="Maya Coach",
                    credentials_text="Demo coach profile; credentials are not verified.",
                )
            )
        trainee = db.scalar(select(User).where(User.email == TRAINEE_EMAIL))
        if trainee is None:
            trainee = User(
                email=TRAINEE_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                first_name="Arjun",
                last_name="Trainee",
                role=Role.TRAINEE,
            )
            db.add(trainee)
            db.flush()
            db.add(TraineeProfile(user_id=trainee.id, timezone="Asia/Kolkata"))
        no_checkin = db.scalar(select(User).where(User.email == NO_CHECKIN_EMAIL))
        if no_checkin is None:
            no_checkin = User(
                email=NO_CHECKIN_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                first_name="Nila",
                last_name="No Check-ins",
                role=Role.TRAINEE,
            )
            db.add(no_checkin)
            db.flush()
            db.add(TraineeProfile(user_id=no_checkin.id, timezone="Asia/Kolkata"))
        db.flush()
        existing = db.scalar(
            select(CoachTraineeAssignment).where(
                CoachTraineeAssignment.coach_id == coach.id,
                CoachTraineeAssignment.trainee_id == trainee.id,
            )
        )
        if existing is None:
            db.add(
                CoachTraineeAssignment(
                    coach_id=coach.id, trainee_id=trainee.id, accepted_at=utcnow()
                )
            )
        no_checkin_assignment = db.scalar(
            select(CoachTraineeAssignment).where(
                CoachTraineeAssignment.coach_id == coach.id,
                CoachTraineeAssignment.trainee_id == no_checkin.id,
            )
        )
        if no_checkin_assignment is None:
            db.add(
                CoachTraineeAssignment(
                    coach_id=coach.id, trainee_id=no_checkin.id, accepted_at=utcnow()
                )
            )
        db.commit()

        seed_exercise_library(db, coach)
        seed_workout_templates(db, coach)
        seed_training_programs(db, coach)

        submitted = db.scalar(
            select(OnboardingAssessment).where(
                OnboardingAssessment.trainee_id == trainee.id,
                OnboardingAssessment.status == AssessmentStatus.SUBMITTED,
            )
        )
        if submitted is None:
            save_assessment(db, trainee, AssessmentData.model_validate(BASELINE))
            submit_assessment(db, trainee)

        today, timezone_name = local_today(db, trainee.id)
        timezone = ZoneInfo(timezone_name)
        for offset, sleep, stress, fatigue, steps, exercised, minutes, rpe, water, feeling in DAILY_VALUES:
            local_date = today - timedelta(days=offset)
            if get_check_in(db, trainee.id, local_date):
                continue
            timestamp = datetime.combine(local_date, time(12), timezone).astimezone(UTC)
            item = DailyCheckIn(
                trainee_id=trainee.id,
                local_date=local_date,
                timezone=timezone_name,
                sleep_hours=sleep,
                sleep_quality=5 if sleep >= 7.5 else 2,
                wake_refreshed=sleep >= 7.5,
                soreness=2 if sleep >= 7.5 else 8,
                fatigue=fatigue,
                stress=stress,
                steps=steps,
                exercised=exercised,
                exercise_minutes=minutes,
                session_rpe=rpe,
                activity_types=["strength_training"] if exercised else [],
                water_liters=water,
                calories_consumed=2150 if sleep >= 7.5 else 1700,
                protein_grams=105 if sleep >= 7.5 else 70,
                nutrition_adherence=90 if sleep >= 7.5 else 55,
                overall_feeling=feeling,
                note=None,
                submitted_at=timestamp,
                created_at=timestamp,
                updated_at=timestamp,
            )
            db.add(item)
            db.flush()
            calculate_and_store_daily_score(db, trainee.id, item, timestamp)
            db.commit()

        seed_public_demo_workspace(db)


if __name__ == "__main__":
    seed()
