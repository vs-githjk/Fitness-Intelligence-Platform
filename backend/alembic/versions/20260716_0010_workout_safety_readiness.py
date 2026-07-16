"""Add workout safety reporting and immutable readiness context.

Revision ID: 20260716_0010
Revises: 20260716_0009
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0010"
down_revision = "20260716_0009"
branch_labels = None
depends_on = None

NEW_TABLES = {
    "workout_readiness_contexts",
    "workout_safety_reports",
    "workout_safety_reviews",
}


def _enum(*values: str, name: str, length: int | None = None) -> sa.Enum:
    return sa.Enum(*values, name=name, native_enum=False, length=length)


def _constraint_names(table: str) -> set[str]:
    return {
        item["name"]
        for item in sa.inspect(op.get_bind()).get_check_constraints(table)
        if item["name"]
    }


def _upgrade_execution_states() -> None:
    dialect = op.get_bind().dialect.name
    lifecycle = (
        "(status = 'in_progress' AND completed_at IS NULL AND ended_at IS NULL) OR "
        "(status = 'completed' AND completed_at IS NOT NULL AND ended_at IS NULL) OR "
        "(status IN ('ended_incomplete', 'safety_ended') "
        "AND completed_at IS NULL AND ended_at IS NOT NULL)"
    )
    exercise_values = (
        "status IN ('not_started', 'in_progress', 'completed', 'skipped', "
        "'paused_for_safety', 'safety_stopped')"
    )
    event_values = (
        "event_type IN ('session_started', 'session_resumed', 'set_completed', "
        "'set_updated', 'set_skipped', 'set_added', 'exercise_skipped', "
        "'session_completed', 'session_ended_incomplete', 'safety_report_submitted', "
        "'exercise_paused_for_safety', 'session_safety_ended')"
    )
    if dialect == "sqlite":
        with op.batch_alter_table("workout_sessions", recreate="always") as batch:
            batch.drop_constraint("ck_workout_sessions_lifecycle", type_="check")
            batch.create_check_constraint("ck_workout_sessions_lifecycle", lifecycle)
        with op.batch_alter_table("workout_session_exercises", recreate="always") as batch:
            batch.alter_column(
                "status", existing_type=sa.String(length=11), type_=sa.String(length=20)
            )
            batch.create_check_constraint(
                "ck_workout_session_exercises_status_values", exercise_values
            )
        with op.batch_alter_table("workout_session_events", recreate="always") as batch:
            batch.alter_column(
                "event_type", existing_type=sa.String(length=24), type_=sa.String(length=32)
            )
            batch.create_check_constraint(
                "ck_workout_session_events_type_values", event_values
            )
        return
    op.drop_constraint(
        "ck_workout_sessions_lifecycle", "workout_sessions", type_="check"
    )
    op.create_check_constraint(
        "ck_workout_sessions_lifecycle", "workout_sessions", lifecycle
    )
    op.alter_column(
        "workout_session_exercises",
        "status",
        existing_type=sa.String(length=11),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_workout_session_exercises_status_values",
        "workout_session_exercises",
        exercise_values,
    )
    op.alter_column(
        "workout_session_events",
        "event_type",
        existing_type=sa.String(length=24),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
    op.create_check_constraint(
        "ck_workout_session_events_type_values", "workout_session_events", event_values
    )


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    present = NEW_TABLES.intersection(tables)
    if present == NEW_TABLES:
        return
    if present:
        raise RuntimeError("Phase 7A schema is only partially present")
    _upgrade_execution_states()

    op.create_table(
        "workout_readiness_contexts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scheduled_workout_id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_id", sa.Uuid(), nullable=False),
        sa.Column("trainee_id", sa.Uuid(), nullable=False),
        sa.Column("daily_score_snapshot_id", sa.Uuid(), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column("readiness_score", sa.Float(), nullable=True),
        sa.Column("readiness_state", sa.String(length=40), nullable=True),
        sa.Column("source_local_date", sa.Date(), nullable=True),
        sa.Column("calculation_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scoring_version", sa.String(length=50), nullable=True),
        sa.Column("age_days", sa.Integer(), nullable=True),
        sa.Column("is_stale", sa.Boolean(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
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
        sa.ForeignKeyConstraint(
            ["scheduled_workout_id"], ["scheduled_workouts.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["workout_session_id"], ["workout_sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["daily_score_snapshot_id"],
            ["daily_score_snapshots.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scheduled_workout_id", name="uq_workout_readiness_scheduled"),
        sa.UniqueConstraint("workout_session_id", name="uq_workout_readiness_session"),
    )
    for column in (
        "scheduled_workout_id",
        "workout_session_id",
        "trainee_id",
        "daily_score_snapshot_id",
    ):
        op.create_index(
            f"ix_workout_readiness_contexts_{column}",
            "workout_readiness_contexts",
            [column],
        )
    op.create_index(
        "ix_workout_readiness_trainee_source",
        "workout_readiness_contexts",
        ["trainee_id", "source_local_date"],
    )

    op.create_table(
        "workout_safety_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_exercise_id", sa.Uuid(), nullable=True),
        sa.Column("workout_set_log_id", sa.Uuid(), nullable=True),
        sa.Column("trainee_id", sa.Uuid(), nullable=False),
        sa.Column(
            "category",
            _enum(
                "pain",
                "unusual_discomfort",
                "chest_discomfort",
                "breathing_difficulty",
                "dizziness_or_faintness",
                "loss_of_balance",
                "equipment_or_environment",
                "other",
                name="safetycategory",
                length=30,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            _enum("mild", "moderate", "severe", name="safetyseverity", length=10),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("activity_stopped", sa.Boolean(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            _enum(
                "open",
                "acknowledged",
                "resolved",
                name="safetyreportstatus",
                length=20,
            ),
            nullable=False,
        ),
        sa.CheckConstraint(
            "note IS NULL OR length(note) <= 500", name="ck_workout_safety_report_note"
        ),
        sa.ForeignKeyConstraint(
            ["workout_session_id"], ["workout_sessions.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["workout_session_exercise_id"],
            ["workout_session_exercises.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["workout_set_log_id"], ["workout_set_logs.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in (
        "workout_session_id",
        "workout_session_exercise_id",
        "workout_set_log_id",
        "trainee_id",
    ):
        op.create_index(
            f"ix_workout_safety_reports_{column}", "workout_safety_reports", [column]
        )
    op.create_index(
        "ix_workout_safety_reports_trainee_created",
        "workout_safety_reports",
        ["trainee_id", "created_at"],
    )
    op.create_index(
        "ix_workout_safety_reports_status_created",
        "workout_safety_reports",
        ["status", "created_at"],
    )
    op.create_index(
        "ix_workout_safety_reports_session_created",
        "workout_safety_reports",
        ["workout_session_id", "created_at"],
    )

    op.create_table(
        "workout_safety_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_safety_report_id", sa.Uuid(), nullable=False),
        sa.Column("coach_id", sa.Uuid(), nullable=False),
        sa.Column(
            "action",
            _enum(
                "acknowledged",
                "resolved",
                name="safetyreviewaction",
                length=20,
            ),
            nullable=False,
        ),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "note IS NULL OR length(note) <= 500", name="ck_workout_safety_review_note"
        ),
        sa.ForeignKeyConstraint(
            ["workout_safety_report_id"],
            ["workout_safety_reports.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("workout_safety_report_id", "coach_id"):
        op.create_index(
            f"ix_workout_safety_reviews_{column}", "workout_safety_reviews", [column]
        )
    op.create_index(
        "ix_workout_safety_reviews_report_created",
        "workout_safety_reviews",
        ["workout_safety_report_id", "created_at"],
    )


def _downgrade_execution_states() -> None:
    op.execute(
        sa.text(
            "DELETE FROM workout_session_events WHERE event_type IN "
            "('safety_report_submitted', 'exercise_paused_for_safety', "
            "'session_safety_ended')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE workout_session_exercises SET status = 'skipped' "
            "WHERE status IN ('paused_for_safety', 'safety_stopped')"
        )
    )
    op.execute(
        sa.text(
            "UPDATE workout_sessions SET status = 'ended_incomplete' "
            "WHERE status = 'safety_ended'"
        )
    )
    lifecycle = (
        "(status = 'in_progress' AND completed_at IS NULL AND ended_at IS NULL) OR "
        "(status = 'completed' AND completed_at IS NOT NULL AND ended_at IS NULL) OR "
        "(status = 'ended_incomplete' AND completed_at IS NULL AND ended_at IS NOT NULL)"
    )
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        with op.batch_alter_table("workout_sessions", recreate="always") as batch:
            batch.drop_constraint("ck_workout_sessions_lifecycle", type_="check")
            batch.create_check_constraint("ck_workout_sessions_lifecycle", lifecycle)
        with op.batch_alter_table("workout_session_exercises", recreate="always") as batch:
            if (
                "ck_workout_session_exercises_status_values"
                in _constraint_names("workout_session_exercises")
            ):
                batch.drop_constraint(
                    "ck_workout_session_exercises_status_values", type_="check"
                )
            batch.alter_column(
                "status", existing_type=sa.String(length=20), type_=sa.String(length=11)
            )
        with op.batch_alter_table("workout_session_events", recreate="always") as batch:
            if (
                "ck_workout_session_events_type_values"
                in _constraint_names("workout_session_events")
            ):
                batch.drop_constraint(
                    "ck_workout_session_events_type_values", type_="check"
                )
            batch.alter_column(
                "event_type", existing_type=sa.String(length=32), type_=sa.String(length=24)
            )
        return
    op.drop_constraint(
        "ck_workout_sessions_lifecycle", "workout_sessions", type_="check"
    )
    op.create_check_constraint(
        "ck_workout_sessions_lifecycle", "workout_sessions", lifecycle
    )
    op.drop_constraint(
        "ck_workout_session_exercises_status_values",
        "workout_session_exercises",
        type_="check",
    )
    op.alter_column(
        "workout_session_exercises",
        "status",
        existing_type=sa.String(length=20),
        type_=sa.String(length=11),
        existing_nullable=False,
    )
    op.drop_constraint(
        "ck_workout_session_events_type_values",
        "workout_session_events",
        type_="check",
    )
    op.alter_column(
        "workout_session_events",
        "event_type",
        existing_type=sa.String(length=32),
        type_=sa.String(length=24),
        existing_nullable=False,
    )


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if not NEW_TABLES.intersection(tables):
        return
    if not NEW_TABLES.issubset(tables):
        raise RuntimeError("Phase 7A schema is only partially present")
    op.drop_table("workout_safety_reviews")
    op.drop_table("workout_safety_reports")
    op.drop_table("workout_readiness_contexts")
    _downgrade_execution_states()
