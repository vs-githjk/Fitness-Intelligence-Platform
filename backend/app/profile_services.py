"""Shared identity services: role-agnostic user profile and preferences.

These records are the canonical identity layer. TraineeProfile.timezone is kept in
sync from preferences for backward compatibility with daily/workout local-date
logic; no existing behavior is changed.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    DistanceUnit,
    TraineeProfile,
    User,
    UserPreferences,
    UserProfile,
    WeightUnit,
    utcnow,
)
from app.schemas import UserPreferencesUpdate, UserProfileUpdate


def _transient_demo_defaults(instance: UserProfile | UserPreferences) -> None:
    """Populate in-memory defaults so a read-only demo record serializes.

    ORM Python-side defaults are only applied on flush, which demo accounts must
    not trigger. This fills the identity fields for the transient response only.
    """
    now = utcnow()
    instance.id = uuid.uuid4()
    instance.created_at = now
    instance.updated_at = now


def get_or_create_user_profile(db: Session, user: User) -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.user_id == user.id))
    if profile is not None:
        return profile
    profile = UserProfile(user_id=user.id)
    if user.is_demo:
        # Demo accounts are read-only; return a transient default without persisting.
        _transient_demo_defaults(profile)
        return profile
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_or_create_user_preferences(db: Session, user: User) -> UserPreferences:
    preferences = db.scalar(
        select(UserPreferences).where(UserPreferences.user_id == user.id)
    )
    if preferences is not None:
        return preferences
    trainee_profile = db.scalar(
        select(TraineeProfile).where(TraineeProfile.user_id == user.id)
    )
    timezone = trainee_profile.timezone if trainee_profile is not None else "UTC"
    preferences = UserPreferences(user_id=user.id, timezone=timezone)
    if user.is_demo:
        # Read-only transient default; mirror the model's Python-side defaults.
        _transient_demo_defaults(preferences)
        preferences.weight_unit = WeightUnit.KG
        preferences.distance_unit = DistanceUnit.KILOMETERS
        preferences.locale = "en"
        preferences.privacy_settings = {}
        preferences.accessibility_settings = {}
        return preferences
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences


def update_user_profile(
    db: Session, user: User, body: UserProfileUpdate
) -> UserProfile:
    profile = get_or_create_user_profile(db, user)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_user_preferences(
    db: Session, user: User, body: UserPreferencesUpdate
) -> UserPreferences:
    preferences = get_or_create_user_preferences(db, user)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(preferences, key, value)
    if "timezone" in data:
        # Preferences.timezone is canonical; keep the legacy trainee field in sync so
        # existing daily/workout local-date behavior stays consistent for trainees.
        trainee_profile = db.scalar(
            select(TraineeProfile).where(TraineeProfile.user_id == user.id)
        )
        if trainee_profile is not None:
            trainee_profile.timezone = data["timezone"]
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    return preferences
