"""Add shared user profile and preferences identity records.

Revision ID: 20260721_0013
Revises: 20260716_0012
"""

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa

from alembic import op

revision = "20260721_0013"
down_revision = "20260716_0012"
branch_labels = None
depends_on = None

PROFILES = "user_profiles"
PREFERENCES = "user_preferences"


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _create_profiles() -> None:
    op.create_table(
        PROFILES,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("preferred_display_name", sa.String(length=120), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_profiles_user_id"),
    )


def _create_preferences() -> None:
    op.create_table(
        PREFERENCES,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("timezone", sa.String(length=80), nullable=False),
        sa.Column(
            "weight_unit",
            sa.Enum("kg", "lb", name="weightunit", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "distance_unit",
            sa.Enum(
                "meters", "kilometers", "miles", name="distanceunit", native_enum=False
            ),
            nullable=False,
        ),
        sa.Column("locale", sa.String(length=20), nullable=False),
        sa.Column("theme", sa.String(length=20), nullable=True),
        sa.Column("privacy_settings", sa.JSON(), nullable=False),
        sa.Column("accessibility_settings", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_user_preferences_user_id"),
    )


def _users_table() -> sa.Table:
    meta = sa.MetaData()
    return sa.Table("users", meta, sa.Column("id", sa.Uuid()))


def _trainee_profiles_table() -> sa.Table:
    meta = sa.MetaData()
    return sa.Table(
        "trainee_profiles",
        meta,
        sa.Column("user_id", sa.Uuid()),
        sa.Column("timezone", sa.String(length=80)),
    )


def _profiles_table() -> sa.Table:
    meta = sa.MetaData()
    return sa.Table(
        PROFILES,
        meta,
        sa.Column("id", sa.Uuid()),
        sa.Column("user_id", sa.Uuid()),
        sa.Column("preferred_display_name", sa.String(length=120)),
        sa.Column("bio", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def _preferences_table() -> sa.Table:
    meta = sa.MetaData()
    return sa.Table(
        PREFERENCES,
        meta,
        sa.Column("id", sa.Uuid()),
        sa.Column("user_id", sa.Uuid()),
        sa.Column("timezone", sa.String(length=80)),
        sa.Column("weight_unit", sa.String(length=10)),
        sa.Column("distance_unit", sa.String(length=12)),
        sa.Column("locale", sa.String(length=20)),
        sa.Column("theme", sa.String(length=20)),
        sa.Column("privacy_settings", sa.JSON()),
        sa.Column("accessibility_settings", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )


def _backfill() -> None:
    """Create one profile and one preference row for every user that lacks them.

    Idempotent: only inserts for users without an existing row, so it is safe to
    re-run and safe against the live test accounts. Trainee timezones are copied
    from the existing trainee_profiles so the canonical preference matches today's
    behavior; other users default to UTC.
    """
    bind = op.get_bind()
    now = datetime.now(UTC)

    users_t = _users_table()
    profiles_t = _profiles_table()
    preferences_t = _preferences_table()
    trainee_t = _trainee_profiles_table()

    user_ids = list(bind.execute(sa.select(users_t.c.id)).scalars())
    if not user_ids:
        return

    trainee_tz = {
        row.user_id: row.timezone
        for row in bind.execute(
            sa.select(trainee_t.c.user_id, trainee_t.c.timezone)
        )
    }

    existing_profiles = set(bind.execute(sa.select(profiles_t.c.user_id)).scalars())
    profile_rows = [
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "preferred_display_name": None,
            "bio": None,
            "created_at": now,
            "updated_at": now,
        }
        for user_id in user_ids
        if user_id not in existing_profiles
    ]
    if profile_rows:
        bind.execute(profiles_t.insert(), profile_rows)

    existing_prefs = set(bind.execute(sa.select(preferences_t.c.user_id)).scalars())
    preference_rows = [
        {
            "id": uuid.uuid4(),
            "user_id": user_id,
            "timezone": trainee_tz.get(user_id) or "UTC",
            "weight_unit": "kg",
            "distance_unit": "kilometers",
            "locale": "en",
            "theme": None,
            "privacy_settings": {},
            "accessibility_settings": {},
            "created_at": now,
            "updated_at": now,
        }
        for user_id in user_ids
        if user_id not in existing_prefs
    ]
    if preference_rows:
        bind.execute(preferences_t.insert(), preference_rows)


def upgrade() -> None:
    tables = _tables()
    if PROFILES not in tables:
        _create_profiles()
    if PREFERENCES not in tables:
        _create_preferences()
    _backfill()


def downgrade() -> None:
    tables = _tables()
    if PREFERENCES in tables:
        op.drop_table(PREFERENCES)
    if PROFILES in tables:
        op.drop_table(PROFILES)
