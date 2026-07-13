import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
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
    health_index_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("health_index_snapshots.id", ondelete="CASCADE"), index=True
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
