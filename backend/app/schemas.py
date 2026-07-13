import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import Role

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


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    invite_code: str = Field(min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    age: int | None = Field(default=None, ge=16, le=100)
    height_cm: float | None = Field(default=None, ge=100, le=250)
    weight_kg: float | None = Field(default=None, ge=30, le=350)
    selected_goal: Goal | None = None
    target_weight_kg: float | None = Field(default=None, ge=30, le=350)
    timezone: str = Field(default="UTC", max_length=80)


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
    assessment_status: str
    current_score: float | None
    band: str | None
    open_alerts: int


class CoachTraineeDetail(BaseModel):
    trainee: UserOut
    profile: ProfileOut | None
    assessment_status: str
    health_index: HealthIndexOut | None


class ErrorDetail(BaseModel):
    code: str
    message: str
    fields: dict[str, str] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
