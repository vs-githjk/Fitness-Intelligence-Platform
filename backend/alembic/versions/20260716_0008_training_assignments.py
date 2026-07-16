"""Add program assignment and date-only workout scheduling.

Revision ID: 20260716_0008
Revises: 20260716_0007
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0008"
down_revision = "20260716_0007"
branch_labels = None
depends_on = None

TABLES = {"training_assignments", "scheduled_workouts", "assignment_history"}


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    present = TABLES.intersection(tables)
    if present == TABLES:
        return
    if present:
        raise RuntimeError("Training assignment schema is only partially present")

    op.create_table(
        "training_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("coach_id", sa.Uuid(), nullable=False),
        sa.Column("trainee_id", sa.Uuid(), nullable=False),
        sa.Column("training_program_version_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "active",
                "scheduled",
                "superseded",
                "cancelled",
                name="trainingassignmentstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("is_primary", sa.Boolean(), nullable=False),
        sa.Column("effective_start_date", sa.Date(), nullable=False),
        sa.Column("effective_end_date", sa.Date(), nullable=True),
        sa.Column("timezone", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('active', 'scheduled', 'superseded', 'cancelled')",
            name="ck_training_assignments_status_values",
        ),
        sa.CheckConstraint(
            "effective_end_date IS NULL OR effective_end_date >= effective_start_date",
            name="ck_training_assignments_date_range",
        ),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["training_program_version_id"],
            ["training_program_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_training_assignments_coach_id", "training_assignments", ["coach_id"])
    op.create_index("ix_training_assignments_trainee_id", "training_assignments", ["trainee_id"])
    op.create_index(
        "ix_training_assignments_training_program_version_id",
        "training_assignments",
        ["training_program_version_id"],
    )
    op.create_index(
        "ix_training_assignments_coach_trainee",
        "training_assignments",
        ["coach_id", "trainee_id"],
    )
    op.create_index(
        "ix_training_assignments_trainee_dates",
        "training_assignments",
        ["trainee_id", "effective_start_date"],
    )
    op.create_index(
        "uq_training_assignments_active_primary",
        "training_assignments",
        ["trainee_id"],
        unique=True,
        sqlite_where=sa.text("is_primary = 1 AND status = 'active'"),
        postgresql_where=sa.text("is_primary = true AND status = 'active'"),
    )
    op.create_index(
        "uq_training_assignments_scheduled_primary",
        "training_assignments",
        ["trainee_id"],
        unique=True,
        sqlite_where=sa.text("is_primary = 1 AND status = 'scheduled'"),
        postgresql_where=sa.text("is_primary = true AND status = 'scheduled'"),
    )

    op.create_table(
        "scheduled_workouts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("trainee_id", sa.Uuid(), nullable=False),
        sa.Column("program_session_id", sa.Uuid(), nullable=False),
        sa.Column("workout_template_version_id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("program_week_number", sa.Integer(), nullable=False),
        sa.Column("program_week_label", sa.String(120), nullable=True),
        sa.Column("is_deload", sa.Boolean(), nullable=False),
        sa.Column(
            "weekday",
            sa.Enum(
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
                name="programweekday",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
        sa.Column("planned_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("target_session_rpe", sa.Float(), nullable=True),
        sa.Column("coach_notes", sa.Text(), nullable=True),
        sa.Column("trainee_instructions", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "scheduled",
                "cancelled",
                "superseded",
                name="scheduledworkoutstatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('scheduled', 'cancelled', 'superseded')",
            name="ck_scheduled_workouts_status_values",
        ),
        sa.CheckConstraint(
            "program_week_number > 0 AND program_week_number <= 12",
            name="ck_scheduled_workouts_week",
        ),
        sa.CheckConstraint(
            "display_order > 0 AND display_order <= 14",
            name="ck_scheduled_workouts_order",
        ),
        sa.ForeignKeyConstraint(
            ["training_assignment_id"], ["training_assignments.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["program_session_id"], ["program_sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["workout_template_version_id"],
            ["workout_template_versions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "training_assignment_id",
            "program_week_number",
            "weekday",
            "display_order",
            name="uq_scheduled_workout_assignment_slot",
        ),
    )
    op.create_index(
        "ix_scheduled_workouts_training_assignment_id",
        "scheduled_workouts",
        ["training_assignment_id"],
    )
    op.create_index("ix_scheduled_workouts_trainee_id", "scheduled_workouts", ["trainee_id"])
    op.create_index(
        "ix_scheduled_workouts_program_session_id",
        "scheduled_workouts",
        ["program_session_id"],
    )
    op.create_index(
        "ix_scheduled_workouts_workout_template_version_id",
        "scheduled_workouts",
        ["workout_template_version_id"],
    )
    op.create_index(
        "ix_scheduled_workouts_trainee_date",
        "scheduled_workouts",
        ["trainee_id", "scheduled_date"],
    )
    op.create_index(
        "ix_scheduled_workouts_assignment_status",
        "scheduled_workouts",
        ["training_assignment_id", "status"],
    )

    op.create_table(
        "assignment_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("training_assignment_id", sa.Uuid(), nullable=False),
        sa.Column("coach_id", sa.Uuid(), nullable=False),
        sa.Column("trainee_id", sa.Uuid(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "assigned",
                "scheduled",
                "activated",
                "superseded",
                "cancelled",
                name="assignmenthistoryevent",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('assigned', 'scheduled', 'activated', 'superseded', 'cancelled')",
            name="ck_assignment_history_event_values",
        ),
        sa.ForeignKeyConstraint(
            ["training_assignment_id"], ["training_assignments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assignment_history_training_assignment_id",
        "assignment_history",
        ["training_assignment_id"],
    )
    op.create_index("ix_assignment_history_coach_id", "assignment_history", ["coach_id"])
    op.create_index("ix_assignment_history_trainee_id", "assignment_history", ["trainee_id"])
    op.create_index(
        "ix_assignment_history_trainee_created",
        "assignment_history",
        ["trainee_id", "created_at"],
    )
    op.create_index(
        "ix_assignment_history_assignment_created",
        "assignment_history",
        ["training_assignment_id", "created_at"],
    )


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if not TABLES.intersection(tables):
        return
    if not TABLES.issubset(tables):
        raise RuntimeError("Training assignment schema is only partially present")
    op.drop_table("assignment_history")
    op.drop_table("scheduled_workouts")
    op.drop_table("training_assignments")
