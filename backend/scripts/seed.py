import secrets
from datetime import UTC, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import AppEnvironment, Settings, settings
from app.daily_services import calculate_and_store_daily_score, get_check_in, local_today
from app.database import SessionLocal
from app.models import (
    AssessmentStatus,
    CoachProfile,
    CoachTraineeAssignment,
    DailyCheckIn,
    OnboardingAssessment,
    Role,
    TraineeProfile,
    User,
    utcnow,
)
from app.schemas import AssessmentData
from app.security import hash_password
from app.services import save_assessment, submit_assessment

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
