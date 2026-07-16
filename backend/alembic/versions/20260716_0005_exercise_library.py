"""Add owned, versioned exercise library.

Revision ID: 20260716_0005
Revises: 20260716_0004
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0005"
down_revision = "20260716_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    present = {"exercises", "exercise_versions"}.intersection(tables)
    if present == {"exercises", "exercise_versions"}:
        return
    if present:
        raise RuntimeError("Exercise library schema is only partially present")
    op.create_table(
        "exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "scope",
            sa.Enum("system", "coach_private", name="exercisescope", native_enum=False),
            nullable=False,
        ),
        sa.Column("owner_coach_id", sa.Uuid(), nullable=True),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="exercisestatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "scope IN ('system', 'coach_private')",
            name="ck_exercises_scope_values",
        ),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_exercises_status_values",
        ),
        sa.CheckConstraint(
            "(scope = 'system' AND owner_coach_id IS NULL) OR "
            "(scope = 'coach_private' AND owner_coach_id IS NOT NULL)",
            name="ck_exercises_scope_owner",
        ),
        sa.ForeignKeyConstraint(["owner_coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exercises_owner_coach_id", "exercises", ["owner_coach_id"])
    op.create_index(
        "ix_exercises_owner_status", "exercises", ["owner_coach_id", "status"]
    )
    op.create_index("ix_exercises_scope_status", "exercises", ["scope", "status"])
    op.create_index(
        "uq_exercises_system_slug",
        "exercises",
        ["slug"],
        unique=True,
        sqlite_where=sa.text("scope = 'system'"),
        postgresql_where=sa.text("scope = 'system'"),
    )
    op.create_index(
        "uq_exercises_owner_slug",
        "exercises",
        ["owner_coach_id", "slug"],
        unique=True,
        sqlite_where=sa.text("owner_coach_id IS NOT NULL"),
        postgresql_where=sa.text("owner_coach_id IS NOT NULL"),
    )

    op.create_table(
        "exercise_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exercise_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "published",
                name="exerciseversionstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column(
            "tracking_mode",
            sa.Enum(
                "repetitions_and_load",
                "repetitions_only",
                "duration",
                "distance_and_duration",
                "bodyweight_or_assisted_repetitions",
                name="exercisetrackingmode",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("movement_pattern", sa.String(length=80), nullable=False),
        sa.Column("equipment", sa.JSON(), nullable=False),
        sa.Column("primary_muscle_groups", sa.JSON(), nullable=False),
        sa.Column("secondary_muscle_groups", sa.JSON(), nullable=False),
        sa.Column("unilateral", sa.Boolean(), nullable=False),
        sa.Column("safety_cues", sa.JSON(), nullable=False),
        sa.Column("image_url", sa.String(length=2048), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=2048), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "version_number > 0", name="ck_exercise_versions_positive_version"
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'published')",
            name="ck_exercise_versions_status_values",
        ),
        sa.CheckConstraint(
            "tracking_mode IN ('repetitions_and_load', 'repetitions_only', "
            "'duration', 'distance_and_duration', "
            "'bodyweight_or_assisted_repetitions')",
            name="ck_exercise_versions_tracking_mode_values",
        ),
        sa.CheckConstraint(
            "(status = 'draft' AND published_at IS NULL AND content_hash IS NULL) OR "
            "(status = 'published' AND published_at IS NOT NULL AND content_hash IS NOT NULL)",
            name="ck_exercise_versions_publication_state",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "exercise_id", "version_number", name="uq_exercise_version_number"
        ),
    )
    op.create_index("ix_exercise_versions_category", "exercise_versions", ["category"])
    op.create_index("ix_exercise_versions_exercise_id", "exercise_versions", ["exercise_id"])
    op.create_index(
        "ix_exercise_versions_exercise_status",
        "exercise_versions",
        ["exercise_id", "status"],
    )
    op.create_index(
        "ix_exercise_versions_movement_pattern",
        "exercise_versions",
        ["movement_pattern"],
    )
    op.create_index(
        "ix_exercise_versions_tracking_mode",
        "exercise_versions",
        ["tracking_mode"],
    )
    op.create_index(
        "uq_exercise_versions_one_draft",
        "exercise_versions",
        ["exercise_id"],
        unique=True,
        sqlite_where=sa.text("status = 'draft'"),
        postgresql_where=sa.text("status = 'draft'"),
    )


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "exercise_versions" in tables:
        op.drop_table("exercise_versions")
    if "exercises" in tables:
        op.drop_table("exercises")
