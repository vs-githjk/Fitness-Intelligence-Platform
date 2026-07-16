"""Add versioned multi-week training programs.

Revision ID: 20260716_0007
Revises: 20260716_0006
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0007"
down_revision = "20260716_0006"
branch_labels = None
depends_on = None

TABLES = {"training_programs", "training_program_versions", "program_weeks", "program_sessions"}
CURRENT_VERSION_FK = "fk_training_programs_current_published_version"


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    present = TABLES.intersection(tables)
    if present == TABLES:
        return
    if present:
        raise RuntimeError("Training program schema is only partially present")
    op.create_table(
        "training_programs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_coach_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.Enum("active", "archived", name="trainingprogramstatus", native_enum=False), nullable=False),
        sa.Column("current_published_version_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'archived')", name="ck_training_programs_status_values"),
        sa.ForeignKeyConstraint(["owner_coach_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_programs_owner_coach_id", "training_programs", ["owner_coach_id"])
    op.create_index("ix_training_programs_owner_status", "training_programs", ["owner_coach_id", "status"])
    op.create_index("ix_training_programs_current_published_version_id", "training_programs", ["current_published_version_id"])
    op.create_table(
        "training_program_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_program_id", sa.Uuid(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("version_status", sa.Enum("draft", "published", name="trainingprogramversionstatus", native_enum=False), nullable=False),
        sa.Column("draft_revision", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal_tags", sa.JSON(), nullable=False),
        sa.Column("duration_weeks", sa.Integer(), nullable=False),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("trainee_instructions", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("version_status IN ('draft', 'published')", name="ck_training_program_versions_status_values"),
        sa.CheckConstraint("version_number > 0", name="ck_training_program_versions_positive_version"),
        sa.CheckConstraint("draft_revision > 0", name="ck_training_program_versions_positive_draft_revision"),
        sa.CheckConstraint("duration_weeks >= 1 AND duration_weeks <= 12", name="ck_training_program_versions_duration"),
        sa.CheckConstraint("(version_status = 'draft' AND published_at IS NULL AND content_hash IS NULL) OR (version_status = 'published' AND published_at IS NOT NULL AND content_hash IS NOT NULL)", name="ck_training_program_versions_publication_state"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["training_program_id"], ["training_programs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("training_program_id", "version_number", name="uq_training_program_version_number"),
    )
    op.create_index("ix_training_program_versions_training_program_id", "training_program_versions", ["training_program_id"])
    op.create_index("ix_training_program_versions_program_status", "training_program_versions", ["training_program_id", "version_status"])
    op.create_index("uq_training_program_versions_one_draft", "training_program_versions", ["training_program_id"], unique=True, sqlite_where=sa.text("version_status = 'draft'"), postgresql_where=sa.text("version_status = 'draft'"))
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("training_programs") as batch_op:
            batch_op.create_foreign_key(CURRENT_VERSION_FK, "training_program_versions", ["current_published_version_id"], ["id"], ondelete="RESTRICT")
    else:
        op.create_foreign_key(CURRENT_VERSION_FK, "training_programs", "training_program_versions", ["current_published_version_id"], ["id"], ondelete="RESTRICT")
    op.create_table(
        "program_weeks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_program_version_id", sa.Uuid(), nullable=False),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(120), nullable=True),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("is_deload", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("week_number > 0 AND week_number <= 12", name="ck_program_weeks_number"),
        sa.ForeignKeyConstraint(["training_program_version_id"], ["training_program_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("training_program_version_id", "week_number", name="uq_program_week_number"),
    )
    op.create_index("ix_program_weeks_training_program_version_id", "program_weeks", ["training_program_version_id"])
    op.create_index("ix_program_weeks_version_number", "program_weeks", ["training_program_version_id", "week_number"])
    op.create_table(
        "program_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("program_week_id", sa.Uuid(), nullable=False),
        sa.Column("workout_template_version_id", sa.Uuid(), nullable=False),
        sa.Column("weekday", sa.Enum("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", name="programweekday", native_enum=False), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("planned_duration_override_minutes", sa.Integer(), nullable=True),
        sa.Column("target_session_rpe_override", sa.Float(), nullable=True),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("trainee_instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("weekday IN ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')", name="ck_program_sessions_weekday_values"),
        sa.CheckConstraint("display_order > 0 AND display_order <= 14", name="ck_program_sessions_order"),
        sa.CheckConstraint("planned_duration_override_minutes IS NULL OR (planned_duration_override_minutes >= 1 AND planned_duration_override_minutes <= 1440)", name="ck_program_sessions_duration_override"),
        sa.CheckConstraint("target_session_rpe_override IS NULL OR (target_session_rpe_override >= 0 AND target_session_rpe_override <= 10)", name="ck_program_sessions_rpe_override"),
        sa.ForeignKeyConstraint(["program_week_id"], ["program_weeks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["workout_template_version_id"], ["workout_template_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("program_week_id", "weekday", "display_order", name="uq_program_session_day_order"),
    )
    op.create_index("ix_program_sessions_program_week_id", "program_sessions", ["program_week_id"])
    op.create_index("ix_program_sessions_workout_template_version_id", "program_sessions", ["workout_template_version_id"])
    op.create_index("ix_program_sessions_template_version", "program_sessions", ["workout_template_version_id"])
    op.create_index("ix_program_sessions_week_day_order", "program_sessions", ["program_week_id", "weekday", "display_order"])


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if not TABLES.intersection(tables):
        return
    if not TABLES.issubset(tables):
        raise RuntimeError("Training program schema is only partially present")
    op.drop_table("program_sessions")
    op.drop_table("program_weeks")
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("training_programs") as batch_op:
            batch_op.drop_constraint(CURRENT_VERSION_FK, type_="foreignkey")
    else:
        op.drop_constraint(CURRENT_VERSION_FK, "training_programs", type_="foreignkey")
    op.drop_table("training_program_versions")
    op.drop_table("training_programs")
