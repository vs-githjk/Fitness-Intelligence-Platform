from sqlalchemy import select

from app.database import SessionLocal
from app.models import CoachProfile, CoachTraineeAssignment, Role, TraineeProfile, User, utcnow
from app.security import hash_password

COACH_EMAIL = "coach@fitness.example.com"
TRAINEE_EMAIL = "trainee@fitness.example.com"
DEMO_PASSWORD = "DemoPass123!"


def seed() -> None:
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
        db.commit()


if __name__ == "__main__":
    seed()
