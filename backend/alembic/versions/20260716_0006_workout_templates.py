"""Add immutable workout template authoring.

Revision ID: 20260716_0006
Revises: 20260716_0005
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0006"
down_revision = "20260716_0005"
branch_labels = None
depends_on = None

TABLES = {
    "workout_templates",
    "workout_template_versions",
    "workout_template_exercises",
    "workout_set_prescriptions",
}
CURRENT_VERSION_FK = "fk_workout_templates_current_published_version"


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    present = TABLES.intersection(tables)
    if present == TABLES:
        return
    if present:
        raise RuntimeError("Workout template schema is only partially present")

    op.create_table(
        "workout_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_coach_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "archived", name="workouttemplatestatus", native_enum=False),
            nullable=False,
        ),
        sa.Column("current_published_version_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'archived')",
            name="ck_workout_templates_status_values",
        ),
        sa.ForeignKeyConstraint(["owner_coach_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_workout_templates_current_published_version_id",
        "workout_templates",
        ["current_published_version_id"],
    )
    op.create_index(
        "ix_workout_templates_owner_coach_id", "workout_templates", ["owner_coach_id"]
    )
    op.create_index(
        "ix_workout_templates_owner_status",
        "workout_templates",
        ["owner_coach_id", "status"],
    )

    op.create_table(
        "workout_template_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_template_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "version_status",
            sa.Enum(
                "draft",
                "published",
                name="workouttemplateversionstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("draft_revision", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal_tags", sa.JSON(), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("target_session_rpe", sa.Float(), nullable=True),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("trainee_instructions", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "version_status IN ('draft', 'published')",
            name="ck_workout_template_versions_status_values",
        ),
        sa.CheckConstraint(
            "version_number > 0", name="ck_workout_template_versions_positive_version"
        ),
        sa.CheckConstraint(
            "draft_revision > 0",
            name="ck_workout_template_versions_positive_draft_revision",
        ),
        sa.CheckConstraint(
            "(version_status = 'draft' AND published_at IS NULL AND content_hash IS NULL) OR "
            "(version_status = 'published' AND published_at IS NOT NULL AND content_hash IS NOT NULL)",
            name="ck_workout_template_versions_publication_state",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["workout_template_id"], ["workout_templates.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workout_template_id",
            "version_number",
            name="uq_workout_template_version_number",
        ),
    )
    op.create_index(
        "ix_workout_template_versions_workout_template_id",
        "workout_template_versions",
        ["workout_template_id"],
    )
    op.create_index(
        "ix_workout_template_versions_template_status",
        "workout_template_versions",
        ["workout_template_id", "version_status"],
    )
    op.create_index(
        "uq_workout_template_versions_one_draft",
        "workout_template_versions",
        ["workout_template_id"],
        unique=True,
        sqlite_where=sa.text("version_status = 'draft'"),
        postgresql_where=sa.text("version_status = 'draft'"),
    )

    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("workout_templates") as batch_op:
            batch_op.create_foreign_key(
                CURRENT_VERSION_FK,
                "workout_template_versions",
                ["current_published_version_id"],
                ["id"],
                ondelete="RESTRICT",
            )
    else:
        op.create_foreign_key(
            CURRENT_VERSION_FK,
            "workout_templates",
            "workout_template_versions",
            ["current_published_version_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    op.create_table(
        "workout_template_exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_template_version_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_version_id", sa.Uuid(), nullable=False),
        sa.Column(
            "section",
            sa.Enum(
                "warm_up",
                "main",
                "cool_down",
                name="workouttemplatesection",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("trainee_instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "section IN ('warm_up', 'main', 'cool_down')",
            name="ck_workout_template_exercises_section_values",
        ),
        sa.CheckConstraint(
            "display_order > 0", name="ck_workout_template_exercises_positive_order"
        ),
        sa.ForeignKeyConstraint(
            ["exercise_version_id"], ["exercise_versions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["workout_template_version_id"],
            ["workout_template_versions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workout_template_version_id",
            "section",
            "display_order",
            name="uq_workout_template_exercise_order",
        ),
    )
    op.create_index(
        "ix_workout_template_exercises_exercise_version",
        "workout_template_exercises",
        ["exercise_version_id"],
    )
    op.create_index(
        "ix_workout_template_exercises_exercise_version_id",
        "workout_template_exercises",
        ["exercise_version_id"],
    )
    op.create_index(
        "ix_workout_template_exercises_workout_template_version_id",
        "workout_template_exercises",
        ["workout_template_version_id"],
    )
    op.create_index(
        "ix_workout_template_exercises_version_section_order",
        "workout_template_exercises",
        ["workout_template_version_id", "section", "display_order"],
    )

    op.create_table(
        "workout_set_prescriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_template_exercise_id", sa.Uuid(), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column(
            "set_type",
            sa.Enum(
                "warm_up",
                "working",
                "back_off",
                "drop_set",
                name="workoutsettype",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("repetitions_min", sa.Integer(), nullable=True),
        sa.Column("repetitions_max", sa.Integer(), nullable=True),
        sa.Column("target_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("target_distance_value", sa.Numeric(12, 3), nullable=True),
        sa.Column(
            "target_distance_unit",
            sa.Enum(
                "meters",
                "kilometers",
                "miles",
                name="distanceunit",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("target_load_original_value", sa.Numeric(12, 3), nullable=True),
        sa.Column(
            "target_load_original_unit",
            sa.Enum("kg", "lb", name="weightunit", native_enum=False),
            nullable=True,
        ),
        sa.Column("target_load_canonical_kg", sa.Numeric(12, 3), nullable=True),
        sa.Column("target_assistance_original_value", sa.Numeric(12, 3), nullable=True),
        sa.Column(
            "target_assistance_original_unit",
            sa.Enum("kg", "lb", name="weightunit", native_enum=False),
            nullable=True,
        ),
        sa.Column("target_assistance_canonical_kg", sa.Numeric(12, 3), nullable=True),
        sa.Column("target_rpe", sa.Numeric(4, 1), nullable=True),
        sa.Column("target_rir", sa.Numeric(4, 1), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("tempo", sa.String(length=30), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "set_type IN ('warm_up', 'working', 'back_off', 'drop_set')",
            name="ck_workout_set_prescriptions_type_values",
        ),
        sa.CheckConstraint(
            "target_distance_unit IS NULL OR target_distance_unit IN ('meters', 'kilometers', 'miles')",
            name="ck_workout_set_prescriptions_distance_unit_values",
        ),
        sa.CheckConstraint(
            "target_load_original_unit IS NULL OR target_load_original_unit IN ('kg', 'lb')",
            name="ck_workout_set_prescriptions_load_unit_values",
        ),
        sa.CheckConstraint(
            "target_assistance_original_unit IS NULL OR target_assistance_original_unit IN ('kg', 'lb')",
            name="ck_workout_set_prescriptions_assistance_unit_values",
        ),
        sa.CheckConstraint(
            "set_number > 0", name="ck_workout_set_prescriptions_positive_number"
        ),
        sa.CheckConstraint(
            "(repetitions_min IS NULL AND repetitions_max IS NULL) OR "
            "(repetitions_min > 0 AND repetitions_max >= repetitions_min)",
            name="ck_workout_set_prescriptions_repetitions",
        ),
        sa.CheckConstraint(
            "target_duration_seconds IS NULL OR target_duration_seconds > 0",
            name="ck_workout_set_prescriptions_duration",
        ),
        sa.CheckConstraint(
            "(target_distance_value IS NULL AND target_distance_unit IS NULL) OR "
            "(target_distance_value > 0 AND target_distance_unit IS NOT NULL)",
            name="ck_workout_set_prescriptions_distance",
        ),
        sa.CheckConstraint(
            "(target_load_original_value IS NULL AND target_load_original_unit IS NULL "
            "AND target_load_canonical_kg IS NULL) OR "
            "(target_load_original_value >= 0 AND target_load_original_unit IS NOT NULL "
            "AND target_load_canonical_kg >= 0)",
            name="ck_workout_set_prescriptions_load",
        ),
        sa.CheckConstraint(
            "(target_assistance_original_value IS NULL AND target_assistance_original_unit IS NULL "
            "AND target_assistance_canonical_kg IS NULL) OR "
            "(target_assistance_original_value >= 0 AND target_assistance_original_unit IS NOT NULL "
            "AND target_assistance_canonical_kg >= 0)",
            name="ck_workout_set_prescriptions_assistance",
        ),
        sa.CheckConstraint(
            "target_rpe IS NULL OR (target_rpe >= 0 AND target_rpe <= 10)",
            name="ck_workout_set_prescriptions_rpe",
        ),
        sa.CheckConstraint(
            "target_rir IS NULL OR (target_rir >= 0 AND target_rir <= 10)",
            name="ck_workout_set_prescriptions_rir",
        ),
        sa.CheckConstraint(
            "rest_seconds IS NULL OR rest_seconds >= 0",
            name="ck_workout_set_prescriptions_rest",
        ),
        sa.ForeignKeyConstraint(
            ["workout_template_exercise_id"],
            ["workout_template_exercises.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workout_template_exercise_id",
            "set_number",
            name="uq_workout_set_prescription_number",
        ),
    )
    op.create_index(
        "ix_workout_set_prescriptions_workout_template_exercise_id",
        "workout_set_prescriptions",
        ["workout_template_exercise_id"],
    )


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "workout_templates" in tables and "workout_template_versions" in tables:
        if op.get_bind().dialect.name == "sqlite":
            with op.batch_alter_table("workout_templates") as batch_op:
                batch_op.drop_constraint(CURRENT_VERSION_FK, type_="foreignkey")
        else:
            op.drop_constraint(
                CURRENT_VERSION_FK, "workout_templates", type_="foreignkey"
            )
    for table in (
        "workout_set_prescriptions",
        "workout_template_exercises",
        "workout_template_versions",
        "workout_templates",
    ):
        if table in tables:
            op.drop_table(table)
