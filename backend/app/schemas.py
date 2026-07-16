import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models import (
    DistanceUnit,
    ExerciseScope,
    ExerciseStatus,
    ExerciseTrackingMode,
    Role,
    WeightUnit,
    WorkoutSetType,
    WorkoutTemplateSection,
    WorkoutTemplateStatus,
)

Goal = Literal[
    "fat_loss", "muscle_gain", "strength", "endurance", "general_health", "athletic_performance"
]


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    role: Role
    is_demo: bool


class RegistrationBase(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)


class TraineeRegisterRequest(RegistrationBase):
    invite_code: str = Field(min_length=1, max_length=100)


class CoachRegisterRequest(RegistrationBase):
    registration_code: str = Field(min_length=1, max_length=200)


# Backward-compatible request shape for the former trainee registration endpoint.
RegisterRequest = TraineeRegisterRequest


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class DemoSessionRequest(BaseModel):
    role: Role


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CoachInviteCreate(BaseModel):
    intended_email: EmailStr | None = None
    expires_in_days: Literal[1, 3, 7, 14, 30] = 7


class CoachInviteOut(BaseModel):
    id: uuid.UUID
    intended_email: EmailStr | None
    status: Literal["active", "used", "expired", "revoked"]
    expires_at: datetime
    used_at: datetime | None
    used_by_user_id: uuid.UUID | None
    revoked_at: datetime | None
    created_at: datetime


class CoachInviteCreatedOut(CoachInviteOut):
    token: str


class ProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=16, le=100)
    height_cm: float | None = Field(default=None, ge=100, le=250)
    weight_kg: float | None = Field(default=None, ge=30, le=350)
    selected_goal: Goal | None = None
    target_weight_kg: float | None = Field(default=None, ge=30, le=350)
    timezone: str = Field(default="UTC", max_length=80)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Use a valid IANA timezone, such as Asia/Kolkata") from exc
        return value


class ProfileOut(ProfileUpdate):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID


class AssessmentData(BaseModel):
    age: int | None = Field(default=None, ge=16, le=100)
    height_cm: float | None = Field(default=None, ge=100, le=250)
    weight_kg: float | None = Field(default=None, ge=30, le=350)
    selected_goal: Goal | None = None
    target_weight_kg: float | None = Field(default=None, ge=30, le=350)
    hydration_ml: float | None = Field(default=None, ge=0, le=10000)
    sleep_hours: float | None = Field(default=None, ge=0, le=16)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    wake_refreshed: bool | None = None
    daily_steps: int | None = Field(default=None, ge=0, le=100000)
    activity_types: list[str] = Field(default_factory=list, max_length=20)
    activity_minutes_weekly: int | None = Field(default=None, ge=0, le=5000)
    workout_frequency_weekly: int | None = Field(default=None, ge=0, le=14)
    average_rpe: float | None = Field(default=None, ge=0, le=10)
    workout_duration_minutes: int | None = Field(default=None, ge=0, le=600)
    perceived_recovery: int | None = Field(default=None, ge=1, le=5)
    stress_level: int | None = Field(default=None, ge=0, le=10)
    resting_heart_rate: int | None = Field(default=None, ge=30, le=220)
    palpitations: bool = False
    shortness_of_breath: bool = False
    chest_pain: bool = False
    calorie_mode: Literal["maintenance", "deficit", "surplus"] | None = None
    calorie_target: float | None = Field(default=None, ge=800, le=8000)
    calorie_intake: float | None = Field(default=None, ge=0, le=10000)
    protein_target_g: float | None = Field(default=None, ge=0, le=500)
    protein_intake_g: float | None = Field(default=None, ge=0, le=500)
    carbohydrate_intake_g: float | None = Field(default=None, ge=0, le=1500)
    healthy_fat_intake_g: float | None = Field(default=None, ge=0, le=500)
    fruit_servings: float | None = Field(default=None, ge=0, le=30)
    vegetable_servings: float | None = Field(default=None, ge=0, le=30)
    fiber_g: float | None = Field(default=None, ge=0, le=150)
    meal_consistency: int | None = Field(default=None, ge=1, le=5)

    @field_validator("activity_types")
    @classmethod
    def unique_activity_types(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip().lower() for item in value if item.strip()))


REQUIRED_ASSESSMENT_FIELDS = [
    "age",
    "height_cm",
    "weight_kg",
    "selected_goal",
    "hydration_ml",
    "sleep_hours",
    "sleep_quality",
    "wake_refreshed",
    "daily_steps",
    "activity_minutes_weekly",
    "workout_frequency_weekly",
    "average_rpe",
    "stress_level",
    "calorie_mode",
]


class AssessmentSaveRequest(BaseModel):
    responses: AssessmentData


class AssessmentOut(BaseModel):
    id: uuid.UUID
    status: str
    schema_version: str
    responses: AssessmentData
    missing_required_fields: list[str]
    submitted_at: datetime | None
    updated_at: datetime


class ComponentOut(BaseModel):
    key: str
    raw_inputs: dict[str, Any]
    normalized_score: float
    weight: float
    weighted_contribution: float
    status: str
    explanation: str


class RiskFlagOut(BaseModel):
    rule_key: str
    severity: str
    status: str = "open"
    title: str
    explanation: str
    recommended_action: str
    triggering_inputs: dict[str, Any]
    rule_version: str
    triggered_at: datetime


class RecommendationOut(BaseModel):
    key: str
    category: str
    priority: str
    trigger: str
    recommended_action: str
    supporting_calculation: dict[str, Any]
    safety_text: str | None = None


class HealthIndexOut(BaseModel):
    id: uuid.UUID
    trainee_id: uuid.UUID
    assessment_id: uuid.UUID
    overall_score: float
    band: str
    scoring_version: str
    calculated_at: datetime
    components: list[ComponentOut]
    missing_fields: list[str]
    risk_flags: list[RiskFlagOut]
    recommendations: list[RecommendationOut]


class CoachTraineeSummary(BaseModel):
    trainee_id: uuid.UUID
    name: str
    email: str
    selected_goal: Goal | None
    assessment_status: str
    assessment_updated_at: datetime | None
    current_score: float | None
    band: str | None
    baseline_calculated_at: datetime | None
    open_alerts: int
    latest_check_in_date: date | None = None
    latest_check_in_at: datetime | None = None
    latest_readiness_score: float | None = None
    latest_readiness_state: str | None = None
    checked_in_today: bool = False
    open_daily_alerts: int = 0


class CoachTraineeDetail(BaseModel):
    trainee: UserOut
    profile: ProfileOut | None
    assessment_status: str
    assessment: AssessmentOut | None
    health_index: HealthIndexOut | None


class TraineeCoachOut(BaseModel):
    assignment_status: str
    coach_id: uuid.UUID | None = None
    coach_name: str | None = None
    coach_email: EmailStr | None = None


OverallFeeling = Literal["very_poor", "poor", "okay", "good", "excellent"]


class DailyCheckInData(BaseModel):
    sleep_hours: float = Field(ge=0, le=16)
    sleep_quality: int = Field(ge=1, le=5)
    wake_refreshed: bool
    soreness: int = Field(ge=0, le=10)
    fatigue: int = Field(ge=0, le=10)
    stress: int = Field(ge=0, le=10)
    steps: int = Field(ge=0, le=100000)
    exercised: bool
    exercise_minutes: int | None = Field(default=None, ge=1, le=600)
    session_rpe: float | None = Field(default=None, ge=0, le=10)
    activity_types: list[str] = Field(default_factory=list, max_length=12)
    water_liters: float = Field(ge=0, le=12)
    calories_consumed: float | None = Field(default=None, ge=0, le=10000)
    protein_grams: float | None = Field(default=None, ge=0, le=500)
    nutrition_adherence: int | None = Field(default=None, ge=0, le=100)
    overall_feeling: OverallFeeling
    note: str | None = Field(default=None, max_length=500)

    @field_validator("activity_types")
    @classmethod
    def clean_activity_types(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip().lower() for item in value if item.strip()]
        if any(len(item) > 50 for item in cleaned):
            raise ValueError("Activity labels must be 50 characters or fewer")
        return list(dict.fromkeys(cleaned))

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        return cleaned or None

    @model_validator(mode="after")
    def exercise_fields_match(self) -> "DailyCheckInData":
        if self.exercised and (self.exercise_minutes is None or self.session_rpe is None):
            raise ValueError("Exercise duration and session RPE are required when exercise is reported")
        if not self.exercised:
            self.exercise_minutes = None
            self.session_rpe = None
            self.activity_types = []
        return self


class DailyCheckInOut(DailyCheckInData):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    trainee_id: uuid.UUID
    local_date: date
    timezone: str
    submitted_at: datetime
    created_at: datetime
    updated_at: datetime


class DailyScoreComponentOut(BaseModel):
    key: str
    group: str
    raw_inputs: dict[str, Any]
    normalized_score: float
    weight: float
    contribution: float
    status: str
    explanation: str
    missing: bool = False


class DailyScoreSummaryOut(BaseModel):
    id: uuid.UUID
    trainee_id: uuid.UUID
    daily_check_in_id: uuid.UUID
    local_date: date
    recovery_score: float
    activity_score: float
    nutrition_score: float | None
    readiness_score: float
    readiness_state: str
    scoring_version: str
    calculated_at: datetime


class DailyScoreOut(DailyScoreSummaryOut):
    components: list[DailyScoreComponentOut]
    missing_fields: list[str]
    recent_training_load: dict[str, Any]
    risk_flags: list[RiskFlagOut]
    recommendations: list[RecommendationOut]


class TrendPoint(BaseModel):
    date: date
    value: float | None
    missing: bool
    rolling_average: float | None = None
    difference_from_previous: float | None = None


class TrendSeries(BaseModel):
    key: str
    label: str
    unit: str
    points: list[TrendPoint]


class DailyTrendsOut(BaseModel):
    start_date: date
    end_date: date
    timezone: str
    series: list[TrendSeries]


class ExerciseDraftData(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    instructions: str = Field(min_length=1, max_length=5000)
    tracking_mode: ExerciseTrackingMode
    category: str = Field(min_length=1, max_length=80)
    movement_pattern: str = Field(min_length=1, max_length=80)
    equipment: list[str] = Field(default_factory=list, max_length=20)
    primary_muscle_groups: list[str] = Field(min_length=1, max_length=20)
    secondary_muscle_groups: list[str] = Field(default_factory=list, max_length=20)
    unilateral: bool = False
    safety_cues: list[str] = Field(default_factory=list, max_length=20)
    image_url: str | None = Field(default=None, max_length=2048)
    thumbnail_url: str | None = Field(default=None, max_length=2048)

    @field_validator("name", "description", "instructions", "category", "movement_pattern")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        if value is not None and not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned

    @field_validator("equipment", "primary_muscle_groups", "secondary_muscle_groups")
    @classmethod
    def clean_labels(cls, value: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(item.strip().lower() for item in value if item.strip()))
        if any(len(item) > 80 for item in cleaned):
            raise ValueError("Metadata labels must be 80 characters or fewer")
        return cleaned

    @field_validator("safety_cues")
    @classmethod
    def clean_safety_cues(cls, value: list[str]) -> list[str]:
        cleaned = list(dict.fromkeys(item.strip() for item in value if item.strip()))
        if any(len(item) > 500 for item in cleaned):
            raise ValueError("Safety cues must be 500 characters or fewer")
        return cleaned

    @field_validator("image_url", "thumbnail_url")
    @classmethod
    def validate_image_url(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        parsed = urlsplit(cleaned)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Image URLs must be public HTTPS URLs without credentials")
        return cleaned

    @model_validator(mode="after")
    def require_primary_muscle_group(self) -> "ExerciseDraftData":
        if not self.primary_muscle_groups:
            raise ValueError("At least one primary muscle group is required")
        return self


class ExerciseCreateRequest(ExerciseDraftData):
    slug: str = Field(
        min_length=2,
        max_length=120,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )


class ExerciseVersionOut(ExerciseDraftData):
    id: uuid.UUID
    exercise_id: uuid.UUID
    version_number: int
    status: Literal["draft", "published"]
    content_hash: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None


class ExerciseSummaryOut(BaseModel):
    id: uuid.UUID
    scope: ExerciseScope
    owner_coach_id: uuid.UUID | None
    slug: str
    status: ExerciseStatus
    created_at: datetime
    archived_at: datetime | None
    published_version: ExerciseVersionOut | None
    draft_version: ExerciseVersionOut | None


class ExerciseDetailOut(ExerciseSummaryOut):
    versions: list[ExerciseVersionOut]


class WorkoutSetPrescriptionData(BaseModel):
    set_number: int = Field(ge=1, le=100)
    set_type: WorkoutSetType = WorkoutSetType.WORKING
    repetitions_min: int | None = Field(default=None, ge=1, le=1000)
    repetitions_max: int | None = Field(default=None, ge=1, le=1000)
    target_duration_seconds: int | None = Field(default=None, ge=1, le=86400)
    target_distance_value: Decimal | None = Field(default=None, gt=0, max_digits=12)
    target_distance_unit: DistanceUnit | None = None
    target_load_original_value: Decimal | None = Field(default=None, ge=0, max_digits=12)
    target_load_original_unit: WeightUnit | None = None
    target_assistance_original_value: Decimal | None = Field(default=None, ge=0, max_digits=12)
    target_assistance_original_unit: WeightUnit | None = None
    target_rpe: Decimal | None = Field(default=None, ge=0, le=10, decimal_places=1)
    target_rir: Decimal | None = Field(default=None, ge=0, le=10, decimal_places=1)
    rest_seconds: int | None = Field(default=None, ge=0, le=86400)
    tempo: str | None = Field(default=None, max_length=30)
    instructions: str | None = Field(default=None, max_length=2000)

    @field_validator("tempo", "instructions")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        return cleaned or None

    @model_validator(mode="after")
    def validate_measurement_pairs(self) -> "WorkoutSetPrescriptionData":
        pairs = (
            (self.repetitions_min, self.repetitions_max, "repetition range"),
            (self.target_distance_value, self.target_distance_unit, "distance"),
            (
                self.target_load_original_value,
                self.target_load_original_unit,
                "external load",
            ),
            (
                self.target_assistance_original_value,
                self.target_assistance_original_unit,
                "assistance",
            ),
        )
        for value, unit_or_maximum, label in pairs:
            if (value is None) != (unit_or_maximum is None):
                raise ValueError(f"Both {label} fields must be supplied together")
        if (
            self.repetitions_min is not None
            and self.repetitions_max is not None
            and self.repetitions_max < self.repetitions_min
        ):
            raise ValueError("repetitions_max must be at least repetitions_min")
        return self


class WorkoutTemplateExerciseData(BaseModel):
    exercise_version_id: uuid.UUID
    section: WorkoutTemplateSection
    display_order: int = Field(ge=1, le=500)
    coach_notes: str | None = Field(default=None, max_length=5000)
    trainee_instructions: str | None = Field(default=None, max_length=5000)
    sets: list[WorkoutSetPrescriptionData] = Field(min_length=1, max_length=100)

    @field_validator("coach_notes", "trainee_instructions")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        return cleaned or None


class WorkoutTemplateDraftData(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    goal_tags: list[str] = Field(default_factory=list, max_length=20)
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    target_session_rpe: float | None = Field(default=None, ge=0, le=10)
    coach_notes: str | None = Field(default=None, max_length=5000)
    trainee_instructions: str | None = Field(default=None, max_length=5000)
    exercises: list[WorkoutTemplateExerciseData] = Field(min_length=1, max_length=200)

    @field_validator("name", "description", "coach_notes", "trainee_instructions")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        cleaned = value.strip() if value else None
        if value is not None and not cleaned:
            raise ValueError("Value must not be blank")
        return cleaned

    @field_validator("goal_tags")
    @classmethod
    def clean_goal_tags(cls, value: list[str]) -> list[str]:
        cleaned = sorted({item.strip().lower() for item in value if item.strip()})
        if any(len(item) > 50 for item in cleaned):
            raise ValueError("Goal tags must be 50 characters or fewer")
        return cleaned


class WorkoutTemplateCreateRequest(WorkoutTemplateDraftData):
    pass


class WorkoutTemplateDraftReplaceRequest(WorkoutTemplateDraftData):
    expected_draft_revision: int = Field(ge=1)


class WorkoutSetPrescriptionOut(WorkoutSetPrescriptionData):
    id: uuid.UUID
    target_load_canonical_kg: Decimal | None
    target_assistance_canonical_kg: Decimal | None
    created_at: datetime


class WorkoutTemplateExerciseOut(BaseModel):
    id: uuid.UUID
    exercise_version_id: uuid.UUID
    section: WorkoutTemplateSection
    display_order: int
    coach_notes: str | None
    trainee_instructions: str | None
    created_at: datetime
    sets: list[WorkoutSetPrescriptionOut]


class WorkoutTemplateVersionOut(BaseModel):
    id: uuid.UUID
    workout_template_id: uuid.UUID
    version_number: int
    version_status: Literal["draft", "published"]
    draft_revision: int
    name: str
    description: str | None
    goal_tags: list[str]
    estimated_duration_minutes: int | None
    target_session_rpe: float | None
    coach_notes: str | None
    trainee_instructions: str | None
    content_hash: str | None
    created_by_user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    exercises: list[WorkoutTemplateExerciseOut]


class WorkoutTemplateVersionSummaryOut(BaseModel):
    id: uuid.UUID
    version_number: int
    version_status: Literal["draft", "published"]
    draft_revision: int
    name: str
    content_hash: str | None
    updated_at: datetime
    published_at: datetime | None


class WorkoutTemplateSummaryOut(BaseModel):
    id: uuid.UUID
    status: WorkoutTemplateStatus
    name: str
    goal_tags: list[str]
    estimated_duration_minutes: int | None
    current_published_version_number: int | None
    has_draft: bool
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None


class WorkoutTemplateListOut(BaseModel):
    items: list[WorkoutTemplateSummaryOut]
    page: int
    per_page: int
    total: int


class WorkoutTemplateDetailOut(BaseModel):
    id: uuid.UUID
    owner_coach_id: uuid.UUID
    status: WorkoutTemplateStatus
    current_published_version_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None
    draft_version: WorkoutTemplateVersionOut | None
    published_version: WorkoutTemplateVersionOut | None
    versions: list[WorkoutTemplateVersionSummaryOut]


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
