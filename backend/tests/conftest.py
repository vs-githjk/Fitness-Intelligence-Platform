from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.invitations import hash_invite_token
from app.main import app
from app.models import CoachInvite, CoachProfile, Role, User
from app.security import hash_password


@pytest.fixture
def db() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        coach = User(
            email="coach@example.com",
            password_hash=hash_password("CoachPass123!"),
            first_name="Test",
            last_name="Coach",
            role=Role.COACH,
        )
        other_coach = User(
            email="other@example.com",
            password_hash=hash_password("OtherPass123!"),
            first_name="Other",
            last_name="Coach",
            role=Role.COACH,
        )
        session.add_all([coach, other_coach])
        session.flush()
        session.add_all(
            [
                CoachProfile(user_id=coach.id, display_name="Test Coach"),
                CoachProfile(user_id=other_coach.id, display_name="Other Coach"),
            ]
        )
        session.add(
            CoachInvite(
                coach_id=coach.id,
                token_hash=hash_invite_token("FIT-DEMO-2026"),
                expires_at=datetime.now(UTC) + timedelta(days=30),
            )
        )
        session.commit()
        yield session


@pytest.fixture
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def complete_assessment() -> dict:
    return {
        "age": 30,
        "height_cm": 175,
        "weight_kg": 75,
        "selected_goal": "general_health",
        "target_weight_kg": 72,
        "hydration_ml": 2400,
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
        "resting_heart_rate": 65,
        "palpitations": False,
        "shortness_of_breath": False,
        "chest_pain": False,
        "calorie_mode": "maintenance",
        "calorie_target": 2200,
        "calorie_intake": 2100,
        "protein_target_g": 110,
        "protein_intake_g": 100,
        "carbohydrate_intake_g": 250,
        "healthy_fat_intake_g": 70,
        "fruit_servings": 2,
        "vegetable_servings": 3,
        "fiber_g": 30,
        "meal_consistency": 4,
    }
