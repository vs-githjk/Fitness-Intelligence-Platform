"""Add resumable trainee workout execution.

Revision ID: 20260716_0009
Revises: 20260716_0008
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0009"
down_revision = "20260716_0008"
branch_labels = None
depends_on = None

TABLES = {
    "workout_sessions",
    "workout_session_exercises",
    "workout_set_logs",
    "workout_session_events",
}


def _enum(*values: str, name: str, length: int | None = None) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, length=length)


def _upgrade_scheduled_status() -> None:
    constraint_names = {
        item["name"]
        for item in sa.inspect(op.get_bind()).get_check_constraints("scheduled_workouts")
    }
    with op.batch_alter_table("scheduled_workouts", recreate="always") as batch:
        if "ck_scheduled_workouts_status_values" in constraint_names:
            batch.drop_constraint("ck_scheduled_workouts_status_values", type_="check")
        batch.alter_column(
            "status",
            existing_type=sa.String(length=10),
            type_=_enum(
                "scheduled",
                "in_progress",
                "completed",
                "partial",
                "cancelled",
                "superseded",
                name="scheduledworkoutstatus",
                length=20,
            ),
            existing_nullable=False,
        )
        batch.create_check_constraint(
            "ck_scheduled_workouts_status_values",
            "status IN ('scheduled', 'in_progress', 'completed', 'partial', 'cancelled', 'superseded')",
        )


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    present = TABLES.intersection(tables)
    if present == TABLES:
        status_column = next(
            item
            for item in inspector.get_columns("scheduled_workouts")
            if item["name"] == "status"
        )
        if (getattr(status_column["type"], "length", 0) or 0) < 20:
            _upgrade_scheduled_status()
        return
    if present:
        raise RuntimeError("Workout execution schema is only partially present")

    _upgrade_scheduled_status()

    op.create_table(
        "workout_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_workout_id", sa.Uuid(), nullable=False),
        sa.Column("trainee_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            _enum("in_progress", "completed", "ended_incomplete", name="workoutsessionstatus"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("session_rpe", sa.Numeric(4, 1), nullable=True),
        sa.Column("trainee_note", sa.Text(), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("revision > 0", name="ck_workout_sessions_positive_revision"),
        sa.CheckConstraint(
            "actual_duration_minutes IS NULL OR actual_duration_minutes > 0",
            name="ck_workout_sessions_actual_duration",
        ),
        sa.CheckConstraint(
            "session_rpe IS NULL OR (session_rpe >= 0 AND session_rpe <= 10)",
            name="ck_workout_sessions_rpe",
        ),
        sa.CheckConstraint(
            "(status = 'in_progress' AND completed_at IS NULL AND ended_at IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL AND ended_at IS NULL) OR "
            "(status = 'ended_incomplete' AND completed_at IS NULL AND ended_at IS NOT NULL)",
            name="ck_workout_sessions_lifecycle",
        ),
        sa.ForeignKeyConstraint(["scheduled_workout_id"], ["scheduled_workouts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_sessions_scheduled_workout_id", "workout_sessions", ["scheduled_workout_id"], unique=True)
    op.create_index("ix_workout_sessions_trainee_id", "workout_sessions", ["trainee_id"])
    op.create_index("ix_workout_sessions_trainee_status", "workout_sessions", ["trainee_id", "status"])
    op.create_index("ix_workout_sessions_trainee_activity", "workout_sessions", ["trainee_id", "last_activity_at"])

    op.create_table(
        "workout_session_exercises",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_id", sa.Uuid(), nullable=False),
        sa.Column("source_workout_template_exercise_id", sa.Uuid(), nullable=False),
        sa.Column("exercise_version_id", sa.Uuid(), nullable=False),
        sa.Column("section", _enum("warm_up", "main", "cool_down", name="workouttemplatesection"), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("trainee_instructions", sa.Text(), nullable=True),
        sa.Column("prescription_snapshot", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            _enum("not_started", "in_progress", "completed", "skipped", name="workoutsessionexercisestatus"),
            nullable=False,
        ),
        sa.Column("skip_reason", sa.String(50), nullable=True),
        sa.Column("skip_note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("display_order > 0", name="ck_workout_session_exercises_order"),
        sa.ForeignKeyConstraint(["workout_session_id"], ["workout_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_workout_template_exercise_id"], ["workout_template_exercises.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["exercise_version_id"], ["exercise_versions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_session_id", "section", "display_order", name="uq_workout_session_exercise_order"),
    )
    op.create_index("ix_workout_session_exercises_workout_session_id", "workout_session_exercises", ["workout_session_id"])
    op.create_index("ix_ws_exercises_source_template_exercise", "workout_session_exercises", ["source_workout_template_exercise_id"])
    op.create_index("ix_workout_session_exercises_exercise_version_id", "workout_session_exercises", ["exercise_version_id"])
    op.create_index("ix_workout_session_exercises_session_status", "workout_session_exercises", ["workout_session_id", "status"])

    op.create_table(
        "workout_set_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_exercise_id", sa.Uuid(), nullable=False),
        sa.Column("source_prescription_id", sa.Uuid(), nullable=True),
        sa.Column("source", _enum("prescribed", "trainee_added", name="workoutsetlogsource"), nullable=False),
        sa.Column("idempotency_key", sa.String(100), nullable=True),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("set_type", _enum("warm_up", "working", "back_off", "drop_set", name="workoutsettype"), nullable=False),
        sa.Column("tracking_mode", _enum("repetitions_and_load", "repetitions_only", "duration", "distance_and_duration", "bodyweight_or_assisted_repetitions", name="exercisetrackingmode"), nullable=False),
        sa.Column("planned_repetitions_min", sa.Integer(), nullable=True),
        sa.Column("planned_repetitions_max", sa.Integer(), nullable=True),
        sa.Column("planned_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("planned_distance_value", sa.Numeric(12, 3), nullable=True),
        sa.Column("planned_distance_unit", _enum("meters", "kilometers", "miles", name="distanceunit"), nullable=True),
        sa.Column("planned_load_original_value", sa.Numeric(12, 3), nullable=True),
        sa.Column("planned_load_original_unit", _enum("kg", "lb", name="weightunit"), nullable=True),
        sa.Column("planned_assistance_original_value", sa.Numeric(12, 3), nullable=True),
        sa.Column("planned_assistance_original_unit", _enum("kg", "lb", name="weightunit"), nullable=True),
        sa.Column("planned_rpe", sa.Numeric(4, 1), nullable=True),
        sa.Column("planned_rir", sa.Numeric(4, 1), nullable=True),
        sa.Column("planned_rest_seconds", sa.Integer(), nullable=True),
        sa.Column("planned_tempo", sa.String(30), nullable=True),
        sa.Column("planned_instructions", sa.Text(), nullable=True),
        sa.Column("actual_repetitions", sa.Integer(), nullable=True),
        sa.Column("actual_load_original_value", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_load_original_unit", _enum("kg", "lb", name="weightunit"), nullable=True),
        sa.Column("actual_load_canonical_kg", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_assistance_original_value", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_assistance_original_unit", _enum("kg", "lb", name="weightunit"), nullable=True),
        sa.Column("actual_assistance_canonical_kg", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("actual_distance_value", sa.Numeric(12, 3), nullable=True),
        sa.Column("actual_distance_unit", _enum("meters", "kilometers", "miles", name="distanceunit"), nullable=True),
        sa.Column("actual_rpe", sa.Numeric(4, 1), nullable=True),
        sa.Column("actual_rir", sa.Numeric(4, 1), nullable=True),
        sa.Column("status", _enum("planned", "completed", "skipped", name="workoutsetlogstatus"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("set_number > 0", name="ck_workout_set_logs_set_number"),
        sa.CheckConstraint("revision > 0", name="ck_workout_set_logs_revision"),
        sa.CheckConstraint("actual_repetitions IS NULL OR actual_repetitions > 0", name="ck_workout_set_logs_repetitions"),
        sa.CheckConstraint("actual_duration_seconds IS NULL OR actual_duration_seconds > 0", name="ck_workout_set_logs_duration"),
        sa.CheckConstraint("actual_rpe IS NULL OR (actual_rpe >= 0 AND actual_rpe <= 10)", name="ck_workout_set_logs_rpe"),
        sa.CheckConstraint("actual_rir IS NULL OR (actual_rir >= 0 AND actual_rir <= 10)", name="ck_workout_set_logs_rir"),
        sa.ForeignKeyConstraint(["workout_session_exercise_id"], ["workout_session_exercises.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_prescription_id"], ["workout_set_prescriptions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_session_exercise_id", "set_number", name="uq_workout_set_log_number"),
        sa.UniqueConstraint("workout_session_exercise_id", "idempotency_key", name="uq_workout_set_log_idempotency"),
    )
    for column in ("workout_session_exercise_id", "source_prescription_id"):
        op.create_index(f"ix_workout_set_logs_{column}", "workout_set_logs", [column])
    op.create_index("ix_workout_set_logs_exercise_status", "workout_set_logs", ["workout_session_exercise_id", "status"])

    op.create_table(
        "workout_session_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", _enum("session_started", "session_resumed", "set_completed", "set_updated", "set_skipped", "set_added", "exercise_skipped", "session_completed", "session_ended_incomplete", name="workoutsessioneventtype"), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workout_session_id"], ["workout_sessions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workout_session_events_workout_session_id", "workout_session_events", ["workout_session_id"])
    op.create_index("ix_workout_session_events_actor_user_id", "workout_session_events", ["actor_user_id"])
    op.create_index("ix_workout_session_events_session_created", "workout_session_events", ["workout_session_id", "created_at"])
    op.create_index("ix_workout_session_events_actor_created", "workout_session_events", ["actor_user_id", "created_at"])


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if not TABLES.intersection(tables):
        return
    if not TABLES.issubset(tables):
        raise RuntimeError("Workout execution schema is only partially present")
    op.drop_table("workout_session_events")
    op.drop_table("workout_set_logs")
    op.drop_table("workout_session_exercises")
    op.drop_table("workout_sessions")
    # The earlier schedule model cannot represent execution outcomes. Downgrade already removes
    # their session graphs, so restore those rows to its only non-terminal actionable state.
    op.execute(
        sa.text(
            "UPDATE scheduled_workouts SET status = 'scheduled' "
            "WHERE status IN ('in_progress', 'completed', 'partial')"
        )
    )
    constraint_names = {
        item["name"]
        for item in sa.inspect(op.get_bind()).get_check_constraints("scheduled_workouts")
    }
    with op.batch_alter_table("scheduled_workouts", recreate="always") as batch:
        if "ck_scheduled_workouts_status_values" in constraint_names:
            batch.drop_constraint("ck_scheduled_workouts_status_values", type_="check")
        batch.alter_column(
            "status",
            existing_type=sa.String(length=20),
            type_=_enum(
                "scheduled",
                "cancelled",
                "superseded",
                name="scheduledworkoutstatus",
                length=10,
            ),
            existing_nullable=False,
        )
        batch.create_check_constraint(
            "ck_scheduled_workouts_status_values",
            "status IN ('scheduled', 'cancelled', 'superseded')",
        )
