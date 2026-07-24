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


class ExerciseDifficulty(str, enum.Enum):
    """Instructional difficulty of an exercise. Self-declared, never a medical rating."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


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
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"
    SKIPPED = "skipped"


class WorkoutSkipKind(str, enum.Enum):
    ORDINARY = "ordinary"
    SAFETY = "safety"


class WorkoutSessionStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ENDED_INCOMPLETE = "ended_incomplete"
    SAFETY_ENDED = "safety_ended"


class WorkoutSessionExerciseStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    PAUSED_FOR_SAFETY = "paused_for_safety"
    SAFETY_STOPPED = "safety_stopped"


class WorkoutSetLogSource(str, enum.Enum):
    PRESCRIBED = "prescribed"
    TRAINEE_ADDED = "trainee_added"


class WorkoutSetLogStatus(str, enum.Enum):
    PLANNED = "planned"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class WorkoutSessionEventType(str, enum.Enum):
    SESSION_STARTED = "session_started"
    SESSION_RESUMED = "session_resumed"
    SET_COMPLETED = "set_completed"
    SET_UPDATED = "set_updated"
    SET_SKIPPED = "set_skipped"
    SET_ADDED = "set_added"
    EXERCISE_SKIPPED = "exercise_skipped"
    SESSION_COMPLETED = "session_completed"
    SESSION_ENDED_INCOMPLETE = "session_ended_incomplete"
    SAFETY_REPORT_SUBMITTED = "safety_report_submitted"
    EXERCISE_PAUSED_FOR_SAFETY = "exercise_paused_for_safety"
    SESSION_SAFETY_ENDED = "session_safety_ended"


class SafetyCategory(str, enum.Enum):
    PAIN = "pain"
    UNUSUAL_DISCOMFORT = "unusual_discomfort"
    CHEST_DISCOMFORT = "chest_discomfort"
    BREATHING_DIFFICULTY = "breathing_difficulty"
    DIZZINESS_OR_FAINTNESS = "dizziness_or_faintness"
    LOSS_OF_BALANCE = "loss_of_balance"
    EQUIPMENT_OR_ENVIRONMENT = "equipment_or_environment"
    OTHER = "other"


class SafetySeverity(str, enum.Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class SafetyReportStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class SafetyReviewAction(str, enum.Enum):
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


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


class MediaPurpose(str, enum.Enum):
    """What a stored media asset is for. Feature integrations arrive in later phases."""

    GENERIC = "generic"
    AVATAR = "avatar"
    EXERCISE_IMAGE = "exercise_image"
    EXERCISE_GIF = "exercise_gif"
    EXERCISE_VIDEO = "exercise_video"
    DOCUMENT = "document"


class MediaVisibility(str, enum.Enum):
    """Who may read an asset. Enforced centrally by the media service, never the client."""

    PRIVATE = "private"
    COACH_TRAINEE = "coach_trainee"
    EXERCISE = "exercise"


class MediaLifecycleStatus(str, enum.Enum):
    """Lifecycle of a stored asset. Transitions are guarded by the media service."""

    ACTIVE = "active"
    REPLACED = "replaced"
    SOFT_DELETED = "soft_deleted"
    PURGED = "purged"


class MediaStorageProviderKind(str, enum.Enum):
    """Storage backend that holds an asset's bytes.

    ``local`` is the only runtime-selectable provider in this phase; ``s3`` is a
    reserved forward-compatible value for an S3-compatible provider (S3/R2) that is
    not yet implemented and is rejected by the provider factory until it exists.
    """

    LOCAL = "local"
    S3 = "s3"


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
    # The single non-login account that owns the read-only curated starter library.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
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


class UserProfile(Base):
    """Role-agnostic identity record, one-to-one with a user.

    Shared foundation for both roles. Existing CoachProfile/TraineeProfile records
    are untouched; this holds cross-role display identity only.
    """

    __tablename__ = "user_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    preferred_display_name: Mapped[str | None] = mapped_column(String(120))
    bio: Mapped[str | None] = mapped_column(Text)
    # Professional identity fields. Self-declared, never verified; surfaced by role in
    # the UI (headline/specialties/experience/certifications for coaches, training
    # goals for trainees) but stored on the shared, role-agnostic profile record.
    headline: Mapped[str | None] = mapped_column(String(160))
    coaching_specialties: Mapped[list[str] | None] = mapped_column(JSON)
    years_of_experience: Mapped[int | None] = mapped_column(Integer)
    certifications_text: Mapped[str | None] = mapped_column(Text)
    training_goals: Mapped[str | None] = mapped_column(Text)
    # Current profile photo. Points at an ACTIVE avatar MediaAsset; SET NULL if the
    # asset row is ever removed. Delivery authorization lives in the identity layer.
    avatar_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            name="fk_user_profiles_avatar_media",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class UserPreferences(Base):
    """Role-agnostic preference record, one-to-one with a user.

    Timezone here is the canonical forward-looking preference. TraineeProfile.timezone
    is retained for backward compatibility and kept in sync for trainees.
    """

    __tablename__ = "user_preferences"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    timezone: Mapped[str] = mapped_column(String(80), default="UTC")
    weight_unit: Mapped[WeightUnit] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values),
        default=WeightUnit.KG,
    )
    distance_unit: Mapped[DistanceUnit] = mapped_column(
        Enum(DistanceUnit, native_enum=False, values_callable=enum_values),
        default=DistanceUnit.KILOMETERS,
    )
    locale: Mapped[str] = mapped_column(String(20), default="en")
    theme: Mapped[str | None] = mapped_column(String(20))
    privacy_settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    accessibility_settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MediaAsset(Base):
    """Provider-independent record of one stored binary asset.

    Bytes live in object storage behind a ``StorageProvider``; only metadata is kept
    here. The opaque ``storage_key`` is generated server-side and is never exposed
    through the API. Deletes are soft; bytes are removed only on an explicit purge.
    """

    __tablename__ = "media_assets"
    __table_args__ = (
        UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
        CheckConstraint("byte_size >= 0", name="ck_media_assets_byte_size"),
        Index("ix_media_assets_owner_lifecycle", "owner_user_id", "lifecycle_status"),
        Index("ix_media_assets_purpose_lifecycle", "purpose", "lifecycle_status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    uploader_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    purpose: Mapped[MediaPurpose] = mapped_column(
        Enum(MediaPurpose, native_enum=False, values_callable=enum_values),
        default=MediaPurpose.GENERIC,
    )
    visibility: Mapped[MediaVisibility] = mapped_column(
        Enum(MediaVisibility, native_enum=False, values_callable=enum_values),
        default=MediaVisibility.PRIVATE,
    )
    lifecycle_status: Mapped[MediaLifecycleStatus] = mapped_column(
        Enum(MediaLifecycleStatus, native_enum=False, values_callable=enum_values),
        default=MediaLifecycleStatus.ACTIVE,
        index=True,
    )
    storage_provider: Mapped[MediaStorageProviderKind] = mapped_column(
        Enum(MediaStorageProviderKind, native_enum=False, values_callable=enum_values),
        default=MediaStorageProviderKind.LOCAL,
    )
    storage_key: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(120))
    byte_size: Mapped[int] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    original_filename: Mapped[str | None] = mapped_column(String(255))
    replaced_by_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    purged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


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
    # Richer instructional knowledge. Optional and additive; never medical advice.
    difficulty: Mapped[ExerciseDifficulty | None] = mapped_column(
        Enum(ExerciseDifficulty, native_enum=False, values_callable=enum_values)
    )
    coaching_cues: Mapped[list[str] | None] = mapped_column(JSON)
    common_mistakes: Mapped[list[str] | None] = mapped_column(JSON)
    # Legacy external-URL image fields (pre-media-subsystem). Retained for
    # compatibility; new authored media uses the MediaAsset references below.
    image_url: Mapped[str | None] = mapped_column(String(2048))
    thumbnail_url: Mapped[str | None] = mapped_column(String(2048))
    # Authored media, part of this immutable version's content. Each points at an
    # ACTIVE MediaAsset (SET NULL if the asset row is ever removed). A single primary
    # image, one optional secondary image, and one optional demonstration video.
    primary_image_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            name="fk_exercise_versions_primary_image",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    secondary_image_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            name="fk_exercise_versions_secondary_image",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
    demonstration_video_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "media_assets.id",
            name="fk_exercise_versions_demonstration_video",
            ondelete="SET NULL",
        ),
        nullable=True,
    )
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
    # Read-only accessors for the authored media assets (explicit FKs disambiguate).
    primary_image: Mapped["MediaAsset | None"] = relationship(
        "MediaAsset", foreign_keys=[primary_image_media_id], viewonly=True
    )
    secondary_image: Mapped["MediaAsset | None"] = relationship(
        "MediaAsset", foreign_keys=[secondary_image_media_id], viewonly=True
    )
    demonstration_video: Mapped["MediaAsset | None"] = relationship(
        "MediaAsset", foreign_keys=[demonstration_video_media_id], viewonly=True
    )


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
    # Independent snapshot attribution when this template was duplicated from a
    # starter-library (system) template. Never implies ongoing synchronization.
    cloned_from_template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "workout_templates.id",
            name="fk_workout_templates_cloned_from",
            ondelete="SET NULL",
        ),
        nullable=True,
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
    # Independent snapshot attribution when this program was cloned from a
    # starter-library (system) program. Coach copies never re-sync with the source.
    cloned_from_program_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "training_programs.id",
            name="fk_training_programs_cloned_from",
            ondelete="SET NULL",
        ),
        nullable=True,
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
        Enum(
            ScheduledWorkoutStatus,
            native_enum=False,
            values_callable=enum_values,
            length=20,
        ),
        default=ScheduledWorkoutStatus.SCHEDULED,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    superseded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    skip_kind: Mapped[WorkoutSkipKind | None] = mapped_column(
        Enum(WorkoutSkipKind, native_enum=False, values_callable=enum_values, length=10)
    )
    skip_reason: Mapped[str | None] = mapped_column(String(40))
    skip_note: Mapped[str | None] = mapped_column(String(500))
    skipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    assignment: Mapped[TrainingAssignment] = relationship(back_populates="scheduled_workouts")
    program_session: Mapped[ProgramSession] = relationship()
    workout_template_version: Mapped[WorkoutTemplateVersion] = relationship()
    workout_session: Mapped["WorkoutSession | None"] = relationship(
        back_populates="scheduled_workout", uselist=False
    )
    readiness_context: Mapped["WorkoutReadinessContext | None"] = relationship(
        back_populates="scheduled_workout", uselist=False
    )


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    __table_args__ = (
        CheckConstraint("revision > 0", name="ck_workout_sessions_positive_revision"),
        CheckConstraint(
            "actual_duration_minutes IS NULL OR actual_duration_minutes > 0",
            name="ck_workout_sessions_actual_duration",
        ),
        CheckConstraint(
            "session_rpe IS NULL OR (session_rpe >= 0 AND session_rpe <= 10)",
            name="ck_workout_sessions_rpe",
        ),
        CheckConstraint(
            "(status = 'in_progress' AND completed_at IS NULL AND ended_at IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL AND ended_at IS NULL) OR "
            "(status IN ('ended_incomplete', 'safety_ended') "
            "AND completed_at IS NULL AND ended_at IS NOT NULL)",
            name="ck_workout_sessions_lifecycle",
        ),
        Index("ix_workout_sessions_trainee_status", "trainee_id", "status"),
        Index("ix_workout_sessions_trainee_activity", "trainee_id", "last_activity_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    scheduled_workout_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scheduled_workouts.id", ondelete="RESTRICT"), unique=True, index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[WorkoutSessionStatus] = mapped_column(
        Enum(WorkoutSessionStatus, native_enum=False, values_callable=enum_values)
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    actual_duration_minutes: Mapped[int | None] = mapped_column(Integer)
    session_rpe: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    trainee_note: Mapped[str | None] = mapped_column(Text)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    scheduled_workout: Mapped[ScheduledWorkout] = relationship(back_populates="workout_session")
    exercises: Mapped[list["WorkoutSessionExercise"]] = relationship(
        back_populates="workout_session",
        cascade="all, delete-orphan",
        order_by="WorkoutSessionExercise.display_order",
    )
    events: Mapped[list["WorkoutSessionEvent"]] = relationship(
        back_populates="workout_session",
        cascade="all, delete-orphan",
        order_by="WorkoutSessionEvent.created_at",
    )
    readiness_context: Mapped["WorkoutReadinessContext | None"] = relationship(
        back_populates="workout_session", uselist=False
    )
    safety_reports: Mapped[list["WorkoutSafetyReport"]] = relationship(
        back_populates="workout_session", order_by="WorkoutSafetyReport.created_at"
    )
    load_summaries: Mapped[list["WorkoutLoadSummary"]] = relationship(
        back_populates="workout_session", cascade="all, delete-orphan"
    )


class WorkoutSessionExercise(Base):
    __tablename__ = "workout_session_exercises"
    __table_args__ = (
        UniqueConstraint(
            "workout_session_id", "section", "display_order",
            name="uq_workout_session_exercise_order",
        ),
        CheckConstraint("display_order > 0", name="ck_workout_session_exercises_order"),
        Index(
            "ix_workout_session_exercises_session_status",
            "workout_session_id", "status",
        ),
        Index(
            "ix_ws_exercises_source_template_exercise",
            "source_workout_template_exercise_id",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True
    )
    source_workout_template_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_template_exercises.id", ondelete="RESTRICT")
    )
    exercise_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercise_versions.id", ondelete="RESTRICT"), index=True
    )
    section: Mapped[WorkoutTemplateSection] = mapped_column(
        Enum(WorkoutTemplateSection, native_enum=False, values_callable=enum_values)
    )
    display_order: Mapped[int] = mapped_column(Integer)
    trainee_instructions: Mapped[str | None] = mapped_column(Text)
    prescription_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[WorkoutSessionExerciseStatus] = mapped_column(
        Enum(
            WorkoutSessionExerciseStatus,
            native_enum=False,
            values_callable=enum_values,
            length=20,
        )
    )
    skip_reason: Mapped[str | None] = mapped_column(String(50))
    skip_note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    workout_session: Mapped[WorkoutSession] = relationship(back_populates="exercises")
    exercise_version: Mapped[ExerciseVersion] = relationship()
    sets: Mapped[list["WorkoutSetLog"]] = relationship(
        back_populates="session_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSetLog.set_number",
    )
    safety_reports: Mapped[list["WorkoutSafetyReport"]] = relationship(
        back_populates="workout_session_exercise"
    )


class WorkoutSetLog(Base):
    __tablename__ = "workout_set_logs"
    __table_args__ = (
        UniqueConstraint(
            "workout_session_exercise_id", "set_number",
            name="uq_workout_set_log_number",
        ),
        UniqueConstraint(
            "workout_session_exercise_id", "idempotency_key",
            name="uq_workout_set_log_idempotency",
        ),
        CheckConstraint("set_number > 0", name="ck_workout_set_logs_set_number"),
        CheckConstraint("revision > 0", name="ck_workout_set_logs_revision"),
        CheckConstraint(
            "actual_repetitions IS NULL OR actual_repetitions > 0",
            name="ck_workout_set_logs_repetitions",
        ),
        CheckConstraint(
            "actual_duration_seconds IS NULL OR actual_duration_seconds > 0",
            name="ck_workout_set_logs_duration",
        ),
        CheckConstraint(
            "actual_rpe IS NULL OR (actual_rpe >= 0 AND actual_rpe <= 10)",
            name="ck_workout_set_logs_rpe",
        ),
        CheckConstraint(
            "actual_rir IS NULL OR (actual_rir >= 0 AND actual_rir <= 10)",
            name="ck_workout_set_logs_rir",
        ),
        Index("ix_workout_set_logs_exercise_status", "workout_session_exercise_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_session_exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_session_exercises.id", ondelete="CASCADE"), index=True
    )
    source_prescription_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workout_set_prescriptions.id", ondelete="RESTRICT"), index=True
    )
    source: Mapped[WorkoutSetLogSource] = mapped_column(
        Enum(WorkoutSetLogSource, native_enum=False, values_callable=enum_values)
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(100))
    set_number: Mapped[int] = mapped_column(Integer)
    set_type: Mapped[WorkoutSetType] = mapped_column(
        Enum(WorkoutSetType, native_enum=False, values_callable=enum_values)
    )
    tracking_mode: Mapped[ExerciseTrackingMode] = mapped_column(
        Enum(ExerciseTrackingMode, native_enum=False, values_callable=enum_values)
    )
    planned_repetitions_min: Mapped[int | None] = mapped_column(Integer)
    planned_repetitions_max: Mapped[int | None] = mapped_column(Integer)
    planned_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    planned_distance_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    planned_distance_unit: Mapped[DistanceUnit | None] = mapped_column(
        Enum(DistanceUnit, native_enum=False, values_callable=enum_values)
    )
    planned_load_original_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    planned_load_original_unit: Mapped[WeightUnit | None] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values)
    )
    planned_assistance_original_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    planned_assistance_original_unit: Mapped[WeightUnit | None] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values)
    )
    planned_rpe: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    planned_rir: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    planned_rest_seconds: Mapped[int | None] = mapped_column(Integer)
    planned_tempo: Mapped[str | None] = mapped_column(String(30))
    planned_instructions: Mapped[str | None] = mapped_column(Text)
    actual_repetitions: Mapped[int | None] = mapped_column(Integer)
    actual_load_original_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    actual_load_original_unit: Mapped[WeightUnit | None] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values)
    )
    actual_load_canonical_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    actual_assistance_original_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    actual_assistance_original_unit: Mapped[WeightUnit | None] = mapped_column(
        Enum(WeightUnit, native_enum=False, values_callable=enum_values)
    )
    actual_assistance_canonical_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    actual_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    actual_distance_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    actual_distance_unit: Mapped[DistanceUnit | None] = mapped_column(
        Enum(DistanceUnit, native_enum=False, values_callable=enum_values)
    )
    actual_rpe: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    actual_rir: Mapped[Decimal | None] = mapped_column(Numeric(4, 1))
    status: Mapped[WorkoutSetLogStatus] = mapped_column(
        Enum(WorkoutSetLogStatus, native_enum=False, values_callable=enum_values)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    session_exercise: Mapped[WorkoutSessionExercise] = relationship(back_populates="sets")
    safety_reports: Mapped[list["WorkoutSafetyReport"]] = relationship(
        back_populates="workout_set_log"
    )


class WorkoutSessionEvent(Base):
    __tablename__ = "workout_session_events"
    __table_args__ = (
        Index("ix_workout_session_events_session_created", "workout_session_id", "created_at"),
        Index("ix_workout_session_events_actor_created", "actor_user_id", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="RESTRICT"), index=True
    )
    event_type: Mapped[WorkoutSessionEventType] = mapped_column(
        Enum(
            WorkoutSessionEventType,
            native_enum=False,
            values_callable=enum_values,
            length=32,
        )
    )
    actor_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    workout_session: Mapped[WorkoutSession] = relationship(back_populates="events")


class WorkoutReadinessContext(Base):
    __tablename__ = "workout_readiness_contexts"
    __table_args__ = (
        CheckConstraint(
            "(is_available AND daily_score_snapshot_id IS NOT NULL "
            "AND readiness_score IS NOT NULL AND readiness_state IS NOT NULL "
            "AND source_local_date IS NOT NULL AND calculation_timestamp IS NOT NULL "
            "AND scoring_version IS NOT NULL AND age_days IS NOT NULL "
            "AND age_days >= 0 AND is_stale IS NOT NULL) OR "
            "(NOT is_available AND daily_score_snapshot_id IS NULL "
            "AND readiness_score IS NULL AND readiness_state IS NULL "
            "AND source_local_date IS NULL AND calculation_timestamp IS NULL "
            "AND scoring_version IS NULL AND age_days IS NULL AND is_stale IS NULL)",
            name="ck_workout_readiness_availability",
        ),
        UniqueConstraint("scheduled_workout_id", name="uq_workout_readiness_scheduled"),
        UniqueConstraint("workout_session_id", name="uq_workout_readiness_session"),
        Index("ix_workout_readiness_trainee_source", "trainee_id", "source_local_date"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    scheduled_workout_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scheduled_workouts.id", ondelete="RESTRICT"), index=True
    )
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="RESTRICT"), index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    daily_score_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("daily_score_snapshots.id", ondelete="RESTRICT"), index=True
    )
    is_available: Mapped[bool] = mapped_column(Boolean)
    readiness_score: Mapped[float | None] = mapped_column(Float)
    readiness_state: Mapped[str | None] = mapped_column(String(40))
    source_local_date: Mapped[date | None] = mapped_column(Date)
    calculation_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scoring_version: Mapped[str | None] = mapped_column(String(50))
    age_days: Mapped[int | None] = mapped_column(Integer)
    is_stale: Mapped[bool | None] = mapped_column(Boolean)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    scheduled_workout: Mapped[ScheduledWorkout] = relationship(
        back_populates="readiness_context"
    )
    workout_session: Mapped[WorkoutSession] = relationship(
        back_populates="readiness_context"
    )


class WorkoutSafetyReport(Base):
    __tablename__ = "workout_safety_reports"
    __table_args__ = (
        CheckConstraint(
            "note IS NULL OR length(note) <= 500", name="ck_workout_safety_report_note"
        ),
        Index("ix_workout_safety_reports_trainee_created", "trainee_id", "created_at"),
        Index("ix_workout_safety_reports_status_created", "status", "created_at"),
        Index("ix_workout_safety_reports_session_created", "workout_session_id", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="RESTRICT"), index=True
    )
    workout_session_exercise_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workout_session_exercises.id", ondelete="RESTRICT"), index=True
    )
    workout_set_log_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workout_set_logs.id", ondelete="RESTRICT"), index=True
    )
    trainee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    category: Mapped[SafetyCategory] = mapped_column(
        Enum(SafetyCategory, native_enum=False, values_callable=enum_values, length=30)
    )
    severity: Mapped[SafetySeverity] = mapped_column(
        Enum(SafetySeverity, native_enum=False, values_callable=enum_values, length=10)
    )
    note: Mapped[str | None] = mapped_column(String(500))
    activity_stopped: Mapped[bool] = mapped_column(Boolean, default=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[SafetyReportStatus] = mapped_column(
        Enum(SafetyReportStatus, native_enum=False, values_callable=enum_values, length=20),
        default=SafetyReportStatus.OPEN,
    )
    workout_session: Mapped[WorkoutSession] = relationship(back_populates="safety_reports")
    workout_session_exercise: Mapped[WorkoutSessionExercise | None] = relationship(
        back_populates="safety_reports"
    )
    workout_set_log: Mapped[WorkoutSetLog | None] = relationship(
        back_populates="safety_reports"
    )
    reviews: Mapped[list["WorkoutSafetyReview"]] = relationship(
        back_populates="report", order_by="WorkoutSafetyReview.created_at"
    )


class WorkoutSafetyReview(Base):
    __tablename__ = "workout_safety_reviews"
    __table_args__ = (
        CheckConstraint(
            "note IS NULL OR length(note) <= 500", name="ck_workout_safety_review_note"
        ),
        Index("ix_workout_safety_reviews_report_created", "workout_safety_report_id", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_safety_report_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_safety_reports.id", ondelete="RESTRICT"), index=True
    )
    coach_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    action: Mapped[SafetyReviewAction] = mapped_column(
        Enum(SafetyReviewAction, native_enum=False, values_callable=enum_values, length=20)
    )
    note: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    report: Mapped[WorkoutSafetyReport] = relationship(back_populates="reviews")


class WorkoutLoadSummary(Base):
    """Immutable per-session load summary produced by the ``workout-load-v1`` engine.

    One row per terminal session per calculation version. Content is never
    mutated after creation; recalculation for an unchanged terminal session is
    idempotent (the existing row is returned as-is).
    """

    __tablename__ = "workout_load_summaries"
    __table_args__ = (
        UniqueConstraint(
            "workout_session_id",
            "calculation_version",
            name="uq_workout_load_summary_session_version",
        ),
        CheckConstraint(
            "completed_repetitions >= 0 AND completed_working_sets >= 0 "
            "AND completed_prescribed_sets >= 0 AND skipped_prescribed_sets >= 0 "
            "AND completed_added_sets >= 0",
            name="ck_workout_load_summary_non_negative_counts",
        ),
        Index(
            "ix_workout_load_summaries_session_version",
            "workout_session_id",
            "calculation_version",
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workout_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"), index=True
    )
    calculation_version: Mapped[str] = mapped_column(String(50))
    planned_session_load: Mapped[float | None] = mapped_column(Float)
    completed_session_load: Mapped[float | None] = mapped_column(Float)
    session_volume_kg: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    completed_repetitions: Mapped[int] = mapped_column(Integer, default=0)
    completed_working_sets: Mapped[int] = mapped_column(Integer, default=0)
    completed_prescribed_sets: Mapped[int] = mapped_column(Integer, default=0)
    skipped_prescribed_sets: Mapped[int] = mapped_column(Integer, default=0)
    completed_added_sets: Mapped[int] = mapped_column(Integer, default=0)
    completed_exercises: Mapped[int] = mapped_column(Integer, default=0)
    total_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    total_distance_meters: Mapped[Decimal | None] = mapped_column(Numeric(14, 3))
    calculation_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    workout_session: Mapped[WorkoutSession] = relationship(back_populates="load_summaries")


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
