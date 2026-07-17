"""Add immutable workout load summary for Workout Intelligence analytics.

Revision ID: 20260716_0011
Revises: 20260716_0010
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0011"
down_revision = "20260716_0010"
branch_labels = None
depends_on = None

TABLE = "workout_load_summaries"


def upgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if TABLE in tables:
        return

    op.create_table(
        TABLE,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("workout_session_id", sa.Uuid(), nullable=False),
        sa.Column("calculation_version", sa.String(length=50), nullable=False),
        sa.Column("planned_session_load", sa.Float(), nullable=True),
        sa.Column("completed_session_load", sa.Float(), nullable=True),
        sa.Column("session_volume_kg", sa.Numeric(14, 3), nullable=True),
        sa.Column("completed_repetitions", sa.Integer(), nullable=False),
        sa.Column("completed_working_sets", sa.Integer(), nullable=False),
        sa.Column("completed_prescribed_sets", sa.Integer(), nullable=False),
        sa.Column("skipped_prescribed_sets", sa.Integer(), nullable=False),
        sa.Column("completed_added_sets", sa.Integer(), nullable=False),
        sa.Column("completed_exercises", sa.Integer(), nullable=False),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("total_distance_meters", sa.Numeric(14, 3), nullable=True),
        sa.Column("calculation_payload", sa.JSON(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "completed_repetitions >= 0 AND completed_working_sets >= 0 "
            "AND completed_prescribed_sets >= 0 AND skipped_prescribed_sets >= 0 "
            "AND completed_added_sets >= 0",
            name="ck_workout_load_summary_non_negative_counts",
        ),
        sa.ForeignKeyConstraint(
            ["workout_session_id"], ["workout_sessions.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "workout_session_id",
            "calculation_version",
            name="uq_workout_load_summary_session_version",
        ),
    )
    op.create_index(
        f"ix_{TABLE}_workout_session_id", TABLE, ["workout_session_id"]
    )
    op.create_index(
        "ix_workout_load_summaries_session_version",
        TABLE,
        ["workout_session_id", "calculation_version"],
    )


def downgrade() -> None:
    tables = set(sa.inspect(op.get_bind()).get_table_names())
    if TABLE not in tables:
        return
    op.drop_index("ix_workout_load_summaries_session_version", table_name=TABLE)
    op.drop_index(f"ix_{TABLE}_workout_session_id", table_name=TABLE)
    op.drop_table(TABLE)
