import enum
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
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


class ExerciseScope(str, enum.Enum):
    SYSTEM = "system"
    COACH_PRIVATE = "coach_private"


class ExerciseStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ExerciseVersionStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ExerciseTrackingMode(str, enum.Enum):
    REPETITIONS_AND_LOAD = "repetitions_and_load"
    REPETITIONS_ONLY = "repetitions_only"
    DURATION = "duration"
    DISTANCE_AND_DURATION = "distance_and_duration"
    BODYWEIGHT_OR_ASSISTED_REPETITIONS = "bodyweight_or_assisted_repetitions"


class WorkoutTemplateStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class WorkoutTemplateVersionStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class WorkoutTemplateSection(str, enum.Enum):
    WARM_UP = "warm_up"
    MAIN = "main"
    COOL_DOWN = "cool_down"


class WorkoutSetType(str, enum.Enum):
    WARM_UP = "warm_up"
    WORKING = "working"
    BACK_OFF = "back_off"
    DROP_SET = "drop_set"


class TrainingProgramStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class TrainingProgramVersionStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class ProgramWeekday(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class TrainingAssignmentStatus(str, enum.Enum):
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class ScheduledWorkoutStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class AssignmentHistoryEvent(str, enum.Enum):
    ASSIGNED = "assigned"
    SCHEDULED = "scheduled"
    ACTIVATED = "activated"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class WeightUnit(str, enum.Enum):
    KG = "kg"
    LB = "lb"


class DistanceUnit(str, enum.Enum):
    METERS = "meters"
    KILOMETERS = "kilometers"
    MILES = "miles"


def enum_values(enum_class: type[enum.Enum]) -> list[str]:
    return [str(item.value) for item in enum_class]


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), index=True)
    status: Mapped[str] = mapped_column(String(30), default="active")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
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


class CoachInvite(Base):
    __tablename__ = "coach_invites"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_coach_invites_token_hash"),
        UniqueConstraint("used_by_user_id", name="uq_coach_invites_used_by_user_id"),
        Index("ix_coach_invites_coach_id", "coach_id"),
        Index("ix_coach_invites_coach_created", "coach_id", "created_at"),
        Index("ix_coach_invites_expires_at", "expires_at"),
        Index("ix_coach_invites_intended_email", "intended_email"),
        Index("ix_coach_invites_token_hash", "token_hash"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    token_hash: Mapped[str] = mapped_column(String(64))
    intended_email: Mapped[str | None] = mapped_column(String(320))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    used_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "(scope = 'system' AND owner_coach_id IS NULL) OR "
            "(scope = 'coach_private' AND owner_coach_id IS NOT NULL)",
            name="ck_exercises_scope_owner",
        ),
        Index("ix_exercises_scope_status", "scope", "status"),
        Index("ix_exercises_owner_status", "owner_coach_id", "status"),
        Index(
            "uq_exercises_system_slug",
            "slug",
            unique=True,
            sqlite_where=text("scope = 'system'"),
            postgresql_where=text("scope = 'system'"),
        ),
        Index(
            "uq_exercises_owner_slug",
            "owner_coach_id",
            "slug",
            unique=True,
            sqlite_where=text("owner_coach_id IS NOT NULL"),
            postgresql_where=text("owner_coach_id IS NOT NULL"),
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    scope: Mapped[ExerciseScope] = mapped_column(
        Enum(ExerciseScope, native_enum=False, values_callable=enum_values)
    )
    owner_coach_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(120))
    status: Mapped[ExerciseStatus] = mapped_column(
        Enum(ExerciseStatus, native_enum=False, values_callable=enum_values),
        default=ExerciseStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    versions: Mapped[list["ExerciseVersion"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan"
    )


class ExerciseVersion(Base):
    __tablename__ = "exercise_versions"
    __table_args__ = (
        UniqueConstraint("exercise_id", "version_number", name="uq_exercise_version_number"),
        CheckConstraint("version_number > 0", name="ck_exercise_versions_positive_version"),
        CheckConstraint(
            "(status = 'draft' AND published_at IS NULL AND content_hash IS NULL) OR "
            "(status = 'published' AND published_at IS NOT NULL AND content_hash IS NOT NULL)",
            name="ck_exercise_versions_publication_state",
        ),
        Index("ix_exercise_versions_exercise_status", "exercise_id", "status"),
        Index(
            "uq_exercise_versions_one_draft",
            "exercise_id",
            unique=True,
            sqlite_where=text("status = 'draft'"),
            postgresql_where=text("status = 'draft'"),
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[ExerciseVersionStatus] = mapped_column(
        Enum(ExerciseVersionStatus, native_enum=False, values_callable=enum_values)
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str] = mapped_column(Text)
    tracking_mode: Mapped[ExerciseTrackingMode] = mapped_column(
        Enum(ExerciseTrackingMode, native_enum=False, values_callable=enum_values), index=True
    )
    category: Mapped[str] = mapped_column(String(80), index=True)
    movement_pattern: Mapped[str] = mapped_column(String(80), index=True)
    equipment: Mapped[list[str]] = mapped_column(JSON, default=list)
    primary_muscle_groups: Mapped[list[str]] = mapped_column(JSON, default=list)
    secondary_muscle_groups: Mapped[list[str]] = mapped_column(JSON, default=list)
    unilateral: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_cues: Mapped[list[str]] = mapped_column(JSON, default=list)
    image_url: Mapped[str | None] = mapped_column(String(2048))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048))
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    exercise: Mapped[Exercise] = relationship(back_populates="versions")


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"
    __table_args__ = (
        Index("ix_workout_templates_owner_status", "owner_coach_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[WorkoutTemplateStatus] = mapped_column(
        Enum(WorkoutTemplateStatus, native_enum=False, values_callable=enum_values),
        default=WorkoutTemplateStatus.ACTIVE,
    )
    current_published_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "workout_template_versions.id",
            name="fk_workout_templates_current_published_version",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    versions: Mapped[list["WorkoutTemplateVersion"]] = relationship(
        back_populates="workout_template",
        cascade="all, delete-orphan",
        foreign_keys="WorkoutTemplateVersion.workout_template_id",
    )


class WorkoutTemplateVersion(Base):
    __tablename__ = "workout_template_versions"
    __table_args__ = (
        UniqueConstraint(
            "workout_template_id",
            "version_number",
            name="uq_workout_template_version_number",
        ),
        CheckConstraint(
            "version_number > 0", name="ck_workout_template_versions_positive_version"
        ),
        CheckConstraint(
            "draft_revision > 0", name="ck_workout_template_versions_positive_draft_revision"
        ),
        CheckConstraint(
            "(version_status = 'draft' AND published_at IS NULL AND content_hash IS NULL) OR "
            "(version_status = 'published' AND published_at IS NOT NULL AND content_hash IS NOT NULL)",
            name="ck_workout_template_versions_publication_state",
        ),
        Index(
            "ix_workout_template_versions_template_status",
            "workout_template_id",
            "version_status",
        ),
        Index(
            "uq_workout_template_versions_one_draft",
            "workout_template_id",
            unique=True,
            sqlite_where=text("version_status = 'draft'"),
            postgresql_where=text("version_status = 'draft'"),
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_templates.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    version_status: Mapped[WorkoutTemplateVersionStatus] = mapped_column(
        Enum(
            WorkoutTemplateVersionStatus,
            native_enum=False,
            values_callable=enum_values,
        )
    )
    draft_revision: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    goal_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    target_session_rpe: Mapped[float | None] = mapped_column(Float)
    coach_notes: Mapped[str | None] = mapped_column(Text)
    trainee_instructions: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    workout_template: Mapped[WorkoutTemplate] = relationship(
        back_populates="versions",
        foreign_keys=[workout_template_id],
    )
    exercises: Mapped[list["WorkoutTemplateExercise"]] = relationship(
        back_populates="workout_template_version",
        cascade="all, delete-orphan",
        order_by="WorkoutTemplateExercise.display_order",
    )


class WorkoutTemplateExercise(Base):
    __tablename__ = "workout_template_exercises"
    __table_args__ = (
        UniqueConstraint(
            "workout_template_version_id",
            "section",
            "display_order",
            name="uq_workout_template_exercise_order",
        ),
        CheckConstraint(
            "display_order > 0", name="ck_workout_template_exercises_positive_order"
        ),
        Index(
            "ix_workout_template_exercises_version_section_order",
            "workout_template_version_id",
            "section",
            "display_order",
        ),
        Index(
            "ix_workout_template_exercises_exercise_version",
            "exercise_version_id",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_template_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_template_versions.id", ondelete="CASCADE"), index=True
    )
    exercise_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_versions.id", ondelete="RESTRICT"), index=True
    )
    section: Mapped[WorkoutTemplateSection] = mapped_column(
        Enum(WorkoutTemplateSection, native_enum=False, values_callable=enum_values)
    )
    display_order: Mapped[int] = mapped_column(Integer)
    coach_notes: Mapped[str | None] = mapped_column(Text)
    trainee_instructions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    workout_template_version: Mapped[WorkoutTemplateVersion] = relationship(
        back_populates="exercises"
    )
    exercise_version: Mapped[ExerciseVersion] = relationship()
    sets: Mapped[list["WorkoutSetPrescription"]] = relationship(
        back_populates="workout_template_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSetPrescription.set_number",
    )


class WorkoutSetPrescription(Base):
    __tablename__ = "workout_set_prescriptions"
    __table_args__ = (
        UniqueConstraint(
            "workout_template_exercise_id",
            "set_number",
            name="uq_workout_set_prescription_number",
        ),
        CheckConstraint("set_number > 0", name="ck_workout_set_prescriptions_positive_number"),
        CheckConstraint(
            "(repetitions_min IS NULL AND repetitions_max IS NULL) OR "
            "(repetitions_min > 0 AND repetitions_max >= repetitions_min)",
            name="ck_workout_set_prescriptions_repetitions",
        ),
        CheckConstraint(
            "target_duration_seconds IS NULL OR target_duration_seconds > 0",
            name="ck_workout_set_prescriptions_duration",
        ),
        CheckConstraint(
            "target_rpe IS NULL OR (target_rpe >= 0 AND target_rpe <= 10)",
            name="ck_workout_set_prescriptions_rpe",
        ),
        CheckConstraint(
            "target_rir IS NULL OR (target_rir >= 0 AND target_rir <= 10)",
            name="ck_workout_set_prescriptions_rir",
        ),
        CheckConstraint(
            "rest_seconds IS NULL OR rest_seconds >= 0",
            name="ck_workout_set_prescriptions_rest",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_template_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_template_exercises.id", ondelete="CASCADE"), index=True
    )
    set_number: Mapped[int] = mapped_column(Integer)
    set_type: Mapped[WorkoutSetType] = mapped_column(
        Enum(WorkoutSetType, native_enum=False, values_callable=enum_values)
    )
    repetitions_min: Mapped[int | None] = mapped_column(Integer)
    repetitions_max: Mapped[int | None] = mapped_column(Integer)
    target_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    target_distance_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    target_distance_unit: Mapped[DistanceUnit | None] = mapped_column(
        Enum(DistanceUnit, native_enum=False, values_callable=enum_values)
    )
    target_load_original_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    target_load_original_unit: Mapped[WeightUnit | None] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values)
    )
    target_load_canonical_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    target_assistance_original_value: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3)
    )
    target_assistance_original_unit: Mapped[WeightUnit | None] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values)
    )
    target_assistance_canonical_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 3)
    )
    target_rpe: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    target_rir: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    tempo: Mapped[str | None] = mapped_column(String(30))
    instructions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    workout_template_exercise: Mapped[WorkoutTemplateExercise] = relationship(
        back_populates="sets"
    )


class TrainingProgram(Base):
    __tablename__ = "training_programs"
    __table_args__ = (Index("ix_training_programs_owner_status", "owner_coach_id", "status"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[TrainingProgramStatus] = mapped_column(
        Enum(TrainingProgramStatus, native_enum=False, values_callable=enum_values),
        default=TrainingProgramStatus.ACTIVE,
    )
    current_published_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "training_program_versions.id",
            name="fk_training_programs_current_published_version",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    versions: Mapped[list["TrainingProgramVersion"]] = relationship(
        back_populates="training_program",
        cascade="all, delete-orphan",
        foreign_keys="TrainingProgramVersion.training_program_id",
    )


class TrainingProgramVersion(Base):
    __tablename__ = "training_program_versions"
    __table_args__ = (
        UniqueConstraint(
            "training_program_id", "version_number", name="uq_training_program_version_number"
        ),
        CheckConstraint("version_number > 0", name="ck_training_program_versions_positive_version"),
        CheckConstraint("draft_revision > 0", name="ck_training_program_versions_positive_draft_revision"),
        CheckConstraint("duration_weeks >= 1 AND duration_weeks <= 12", name="ck_training_program_versions_duration"),
        CheckConstraint(
            "(version_status = 'draft' AND published_at IS NULL AND content_hash IS NULL) OR "
            "(version_status = 'published' AND published_at IS NOT NULL AND content_hash IS NOT NULL)",
            name="ck_training_program_versions_publication_state",
        ),
        Index("ix_training_program_versions_program_status", "training_program_id", "version_status"),
        Index(
            "uq_training_program_versions_one_draft",
            "training_program_id",
            unique=True,
            sqlite_where=text("version_status = 'draft'"),
            postgresql_where=text("version_status = 'draft'"),
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_program_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_programs.id", ondelete="CASCADE"), index=True
    )
    version_number: Mapped[int] = mapped_column(Integer)
    version_status: Mapped[TrainingProgramVersionStatus] = mapped_column(
        Enum(TrainingProgramVersionStatus, native_enum=False, values_callable=enum_values)
    )
    draft_revision: Mapped[int] = mapped_column(Integer, default=1)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    goal_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    duration_weeks: Mapped[int] = mapped_column(Integer)
    coach_notes: Mapped[str | None] = mapped_column(Text)
    trainee_instructions: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    training_program: Mapped[TrainingProgram] = relationship(
        back_populates="versions", foreign_keys=[training_program_id]
    )
    weeks: Mapped[list["ProgramWeek"]] = relationship(
        back_populates="training_program_version",
        cascade="all, delete-orphan",
        order_by="ProgramWeek.week_number",
    )


class ProgramWeek(Base):
    __tablename__ = "program_weeks"
    __table_args__ = (
        UniqueConstraint(
            "training_program_version_id", "week_number", name="uq_program_week_number"
        ),
        CheckConstraint("week_number > 0 AND week_number <= 12", name="ck_program_weeks_number"),
        Index("ix_program_weeks_version_number", "training_program_version_id", "week_number"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_program_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_program_versions.id", ondelete="CASCADE"), index=True
    )
    week_number: Mapped[int] = mapped_column(Integer)
    label: Mapped[str | None] = mapped_column(String(120))
    coach_notes: Mapped[str | None] = mapped_column(Text)
    is_deload: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    training_program_version: Mapped[TrainingProgramVersion] = relationship(
        back_populates="weeks"
    )
    sessions: Mapped[list["ProgramSession"]] = relationship(
        back_populates="program_week",
        cascade="all, delete-orphan",
        order_by="ProgramSession.display_order",
    )


class ProgramSession(Base):
    __tablename__ = "program_sessions"
    __table_args__ = (
        UniqueConstraint(
            "program_week_id", "weekday", "display_order", name="uq_program_session_day_order"
        ),
        CheckConstraint("display_order > 0 AND display_order <= 14", name="ck_program_sessions_order"),
        CheckConstraint(
            "planned_duration_override_minutes IS NULL OR "
            "(planned_duration_override_minutes >= 1 AND planned_duration_override_minutes <= 1440)",
            name="ck_program_sessions_duration_override",
        ),
        CheckConstraint(
            "target_session_rpe_override IS NULL OR "
            "(target_session_rpe_override >= 0 AND target_session_rpe_override <= 10)",
            name="ck_program_sessions_rpe_override",
        ),
        Index("ix_program_sessions_week_day_order", "program_week_id", "weekday", "display_order"),
        Index("ix_program_sessions_template_version", "workout_template_version_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    program_week_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_weeks.id", ondelete="CASCADE"), index=True
    )
    workout_template_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_template_versions.id", ondelete="RESTRICT"), index=True
    )
    weekday: Mapped[ProgramWeekday] = mapped_column(
        Enum(ProgramWeekday, native_enum=False, values_callable=enum_values)
    )
    display_order: Mapped[int] = mapped_column(Integer)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    planned_duration_override_minutes: Mapped[int | None] = mapped_column(Integer)
    target_session_rpe_override: Mapped[float | None] = mapped_column(Float)
    coach_notes: Mapped[str | None] = mapped_column(Text)
    trainee_instructions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    program_week: Mapped[ProgramWeek] = relationship(back_populates="sessions")
    workout_template_version: Mapped[WorkoutTemplateVersion] = relationship()


class TrainingAssignment(Base):
    __tablename__ = "training_assignments"
    __table_args__ = (
        CheckConstraint(
            "effective_end_date IS NULL OR effective_end_date >= effective_start_date",
            name="ck_training_assignments_date_range",
        ),
        Index(
            "uq_training_assignments_active_primary",
            "trainee_id",
            unique=True,
            sqlite_where=text("is_primary = 1 AND status = 'active'"),
            postgresql_where=text("is_primary = true AND status = 'active'"),
        ),
        Index(
            "uq_training_assignments_scheduled_primary",
            "trainee_id",
            unique=True,
            sqlite_where=text("is_primary = 1 AND status = 'scheduled'"),
            postgresql_where=text("is_primary = true AND status = 'scheduled'"),
        ),
        Index("ix_training_assignments_coach_trainee", "coach_id", "trainee_id"),
        Index("ix_training_assignments_trainee_dates", "trainee_id", "effective_start_date"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    training_program_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_program_versions.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[TrainingAssignmentStatus] = mapped_column(
        Enum(TrainingAssignmentStatus, native_enum=False, values_callable=enum_values)
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_start_date: Mapped[date] = mapped_column(Date)
    effective_end_date: Mapped[date | None] = mapped_column(Date)
    timezone: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    program_version: Mapped[TrainingProgramVersion] = relationship()
    scheduled_workouts: Mapped[list["ScheduledWorkout"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan", order_by="ScheduledWorkout.scheduled_date"
    )
    history: Mapped[list["AssignmentHistory"]] = relationship(
        back_populates="assignment", cascade="all, delete-orphan", order_by="AssignmentHistory.created_at"
    )


class ScheduledWorkout(Base):
    __tablename__ = "scheduled_workouts"
    __table_args__ = (
        UniqueConstraint(
            "training_assignment_id",
            "program_week_number",
            "weekday",
            "display_order",
            name="uq_scheduled_workout_assignment_slot",
        ),
        CheckConstraint("program_week_number > 0 AND program_week_number <= 12", name="ck_scheduled_workouts_week"),
        CheckConstraint("display_order > 0 AND display_order <= 14", name="ck_scheduled_workouts_order"),
        Index("ix_scheduled_workouts_trainee_date", "trainee_id", "scheduled_date"),
        Index("ix_scheduled_workouts_assignment_status", "training_assignment_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_assignments.id", ondelete="CASCADE"), index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    program_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("program_sessions.id", ondelete="RESTRICT"), index=True
    )
    workout_template_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_template_versions.id", ondelete="RESTRICT"), index=True
    )
    scheduled_date: Mapped[date] = mapped_column(Date)
    program_week_number: Mapped[int] = mapped_column(Integer)
    program_week_label: Mapped[str | None] = mapped_column(String(120))
    is_deload: Mapped[bool] = mapped_column(Boolean, default=False)
    weekday: Mapped[ProgramWeekday] = mapped_column(
        Enum(ProgramWeekday, native_enum=False, values_callable=enum_values)
    )
    display_order: Mapped[int] = mapped_column(Integer)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    planned_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    target_session_rpe: Mapped[float | None] = mapped_column(Float)
    coach_notes: Mapped[str | None] = mapped_column(Text)
    trainee_instructions: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ScheduledWorkoutStatus] = mapped_column(
        Enum(ScheduledWorkoutStatus, native_enum=False, values_callable=enum_values),
        default=ScheduledWorkoutStatus.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assignment: Mapped[TrainingAssignment] = relationship(back_populates="scheduled_workouts")
    program_session: Mapped[ProgramSession] = relationship()
    workout_template_version: Mapped[WorkoutTemplateVersion] = relationship()


class AssignmentHistory(Base):
    __tablename__ = "assignment_history"
    __table_args__ = (
        Index("ix_assignment_history_trainee_created", "trainee_id", "created_at"),
        Index("ix_assignment_history_assignment_created", "training_assignment_id", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    training_assignment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("training_assignments.id", ondelete="RESTRICT"), index=True
    )
    coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    event_type: Mapped[AssignmentHistoryEvent] = mapped_column(
        Enum(AssignmentHistoryEvent, native_enum=False, values_callable=enum_values)
    )
    effective_date: Mapped[date] = mapped_column(Date)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    assignment: Mapped[TrainingAssignment] = relationship(back_populates="history")


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
