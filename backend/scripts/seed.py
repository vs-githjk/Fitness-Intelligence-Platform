from datetime import UTC, datetime, time, timedelta
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


if __name__ == "__main__":
    seed()
