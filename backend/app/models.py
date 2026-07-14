import enum
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Role(str, enum.Enum):
    COACH = "coach"
    TRAINEE = "trainee"


class AssessmentStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class CoachProfile(Base):
    __tablename__ = "coach_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    display_name: Mapped[str] = mapped_column(String(200))
    credentials_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class TraineeProfile(Base):
    __tablename__ = "trainee_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[float | None] = mapped_column(Float)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    selected_goal: Mapped[str | None] = mapped_column(String(50))
    target_weight_kg: Mapped[float | None] = mapped_column(Float)
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class CoachTraineeAssignment(Base):
    __tablename__ = "coach_trainee_assignments"
    __table_args__ = (UniqueConstraint("coach_id", "trainee_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="active")
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class OnboardingAssessment(Base):
    __tablename__ = "onboarding_assessments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[AssessmentStatus] = mapped_column(
        Enum(AssessmentStatus, native_enum=False), default=AssessmentStatus.DRAFT
    )
    schema_version: Mapped[str] = mapped_column(String(50), default="onboarding-v1")
    responses: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    snapshots: Mapped[list["HealthIndexSnapshot"]] = relationship(back_populates="assessment")


class HealthIndexSnapshot(Base):
    __tablename__ = "health_index_snapshots"
    __table_args__ = (UniqueConstraint("assessment_id", "scoring_version"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("onboarding_assessments.id", ondelete="CASCADE"), index=True
    )
    overall_score: Mapped[float] = mapped_column(Float)
    interpretation_band: Mapped[str] = mapped_column(String(50))
    scoring_version: Mapped[str] = mapped_column(String(50))
    calculation_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    assessment: Mapped[OnboardingAssessment] = relationship(back_populates="snapshots")
    components: Mapped[list["ScoreComponentSnapshot"]] = relationship(cascade="all, delete-orphan")


class ScoreComponentSnapshot(Base):
    __tablename__ = "score_component_snapshots"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    health_index_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_index_snapshots.id", ondelete="CASCADE"), index=True
    )
    component_key: Mapped[str] = mapped_column(String(60))
    normalized_score: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    weighted_contribution: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)


class RiskAlert(Base):
    __tablename__ = "risk_alerts"
    __table_args__ = (Index("ix_risk_alert_trainee_status", "trainee_id", "status"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    health_index_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("health_index_snapshots.id", ondelete="CASCADE"), index=True, nullable=True
    )
    daily_score_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("daily_score_snapshots.id", ondelete="CASCADE"), index=True, nullable=True
    )
    rule_key: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30), default="open")
    title: Mapped[str] = mapped_column(String(200))
    explanation: Mapped[str] = mapped_column(Text)
    recommended_action: Mapped[str] = mapped_column(Text)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    rule_version: Mapped[str] = mapped_column(String(50))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DailyCheckIn(Base):
    __tablename__ = "daily_check_ins"
    __table_args__ = (
        UniqueConstraint("trainee_id", "local_date", name="uq_daily_check_in_trainee_date"),
        Index("ix_daily_check_in_trainee_date", "trainee_id", "local_date"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    local_date: Mapped[date] = mapped_column(Date)
    timezone: Mapped[str] = mapped_column(String(80))
    sleep_hours: Mapped[float] = mapped_column(Float)
    sleep_quality: Mapped[int] = mapped_column(Integer)
    wake_refreshed: Mapped[bool] = mapped_column(Boolean)
    soreness: Mapped[int] = mapped_column(Integer)
    fatigue: Mapped[int] = mapped_column(Integer)
    stress: Mapped[int] = mapped_column(Integer)
    steps: Mapped[int] = mapped_column(Integer)
    exercised: Mapped[bool] = mapped_column(Boolean)
    exercise_minutes: Mapped[int | None] = mapped_column(Integer)
    session_rpe: Mapped[float | None] = mapped_column(Float)
    activity_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    water_liters: Mapped[float] = mapped_column(Float)
    calories_consumed: Mapped[float | None] = mapped_column(Float)
    protein_grams: Mapped[float | None] = mapped_column(Float)
    nutrition_adherence: Mapped[int | None] = mapped_column(Integer)
    overall_feeling: Mapped[str] = mapped_column(String(30))
    note: Mapped[str | None] = mapped_column(String(500))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    score_snapshots: Mapped[list["DailyScoreSnapshot"]] = relationship(
        back_populates="check_in", cascade="all, delete-orphan"
    )


class DailyScoreSnapshot(Base):
    __tablename__ = "daily_score_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "daily_check_in_id", "scoring_version", name="uq_daily_score_check_in_version"
        ),
        Index("ix_daily_score_trainee_date", "trainee_id", "local_date"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    daily_check_in_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_check_ins.id", ondelete="CASCADE"), index=True
    )
    local_date: Mapped[date] = mapped_column(Date)
    recovery_score: Mapped[float] = mapped_column(Float)
    activity_score: Mapped[float] = mapped_column(Float)
    nutrition_score: Mapped[float | None] = mapped_column(Float)
    readiness_score: Mapped[float] = mapped_column(Float)
    readiness_state: Mapped[str] = mapped_column(String(40))
    scoring_version: Mapped[str] = mapped_column(String(50))
    calculation_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    check_in: Mapped[DailyCheckIn] = relationship(back_populates="score_snapshots")
    components: Mapped[list["DailyScoreComponent"]] = relationship(
        cascade="all, delete-orphan"
    )


class DailyScoreComponent(Base):
    __tablename__ = "daily_score_components"
    __table_args__ = (
        UniqueConstraint(
            "daily_score_snapshot_id", "component_key", name="uq_daily_score_component_key"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    daily_score_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("daily_score_snapshots.id", ondelete="CASCADE"), index=True
    )
    component_key: Mapped[str] = mapped_column(String(80))
    normalized_score: Mapped[float] = mapped_column(Float)
    weight: Mapped[float] = mapped_column(Float)
    contribution: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(40))
    explanation: Mapped[str] = mapped_column(Text)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
