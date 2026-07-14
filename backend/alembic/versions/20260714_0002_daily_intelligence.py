"""Add daily check-ins and deterministic daily score snapshots."""

import sqlalchemy as sa

from alembic import op

revision = "20260714_0002"
down_revision = "20260713_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "daily_check_ins" not in tables:
        op.create_table(
            "daily_check_ins",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("trainee_id", sa.Uuid(), nullable=False),
            sa.Column("local_date", sa.Date(), nullable=False),
            sa.Column("timezone", sa.String(length=80), nullable=False),
            sa.Column("sleep_hours", sa.Float(), nullable=False),
            sa.Column("sleep_quality", sa.Integer(), nullable=False),
            sa.Column("wake_refreshed", sa.Boolean(), nullable=False),
            sa.Column("soreness", sa.Integer(), nullable=False),
            sa.Column("fatigue", sa.Integer(), nullable=False),
            sa.Column("stress", sa.Integer(), nullable=False),
            sa.Column("steps", sa.Integer(), nullable=False),
            sa.Column("exercised", sa.Boolean(), nullable=False),
            sa.Column("exercise_minutes", sa.Integer(), nullable=True),
            sa.Column("session_rpe", sa.Float(), nullable=True),
            sa.Column("activity_types", sa.JSON(), nullable=False),
            sa.Column("water_liters", sa.Float(), nullable=False),
            sa.Column("calories_consumed", sa.Float(), nullable=True),
            sa.Column("protein_grams", sa.Float(), nullable=True),
            sa.Column("nutrition_adherence", sa.Integer(), nullable=True),
            sa.Column("overall_feeling", sa.String(length=30), nullable=False),
            sa.Column("note", sa.String(length=500), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "trainee_id", "local_date", name="uq_daily_check_in_trainee_date"
            ),
        )
        op.create_index("ix_daily_check_ins_trainee_id", "daily_check_ins", ["trainee_id"])
        op.create_index(
            "ix_daily_check_in_trainee_date", "daily_check_ins", ["trainee_id", "local_date"]
        )

    if "daily_score_snapshots" not in tables:
        op.create_table(
            "daily_score_snapshots",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("trainee_id", sa.Uuid(), nullable=False),
            sa.Column("daily_check_in_id", sa.Uuid(), nullable=False),
            sa.Column("local_date", sa.Date(), nullable=False),
            sa.Column("recovery_score", sa.Float(), nullable=False),
            sa.Column("activity_score", sa.Float(), nullable=False),
            sa.Column("nutrition_score", sa.Float(), nullable=True),
            sa.Column("readiness_score", sa.Float(), nullable=False),
            sa.Column("readiness_state", sa.String(length=40), nullable=False),
            sa.Column("scoring_version", sa.String(length=50), nullable=False),
            sa.Column("calculation_payload", sa.JSON(), nullable=False),
            sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["daily_check_in_id"], ["daily_check_ins.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["trainee_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "daily_check_in_id", "scoring_version", name="uq_daily_score_check_in_version"
            ),
        )
        op.create_index(
            "ix_daily_score_snapshots_daily_check_in_id",
            "daily_score_snapshots",
            ["daily_check_in_id"],
        )
        op.create_index(
            "ix_daily_score_snapshots_trainee_id", "daily_score_snapshots", ["trainee_id"]
        )
        op.create_index(
            "ix_daily_score_snapshots_calculated_at", "daily_score_snapshots", ["calculated_at"]
        )
        op.create_index(
            "ix_daily_score_trainee_date", "daily_score_snapshots", ["trainee_id", "local_date"]
        )

    if "daily_score_components" not in tables:
        op.create_table(
            "daily_score_components",
            sa.Column("id", sa.Uuid(), nullable=False),
            sa.Column("daily_score_snapshot_id", sa.Uuid(), nullable=False),
            sa.Column("component_key", sa.String(length=80), nullable=False),
            sa.Column("normalized_score", sa.Float(), nullable=False),
            sa.Column("weight", sa.Float(), nullable=False),
            sa.Column("contribution", sa.Float(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("explanation", sa.Text(), nullable=False),
            sa.Column("input_snapshot", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(
                ["daily_score_snapshot_id"], ["daily_score_snapshots.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "daily_score_snapshot_id", "component_key", name="uq_daily_score_component_key"
            ),
        )
        op.create_index(
            "ix_daily_score_components_daily_score_snapshot_id",
            "daily_score_components",
            ["daily_score_snapshot_id"],
        )

    risk_columns = {column["name"] for column in sa.inspect(bind).get_columns("risk_alerts")}
    with op.batch_alter_table("risk_alerts") as batch:
        if "daily_score_snapshot_id" not in risk_columns:
            batch.add_column(sa.Column("daily_score_snapshot_id", sa.Uuid(), nullable=True))
            batch.create_foreign_key(
                "fk_risk_alert_daily_score_snapshot",
                "daily_score_snapshots",
                ["daily_score_snapshot_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch.create_index(
                "ix_risk_alerts_daily_score_snapshot_id", ["daily_score_snapshot_id"]
            )
        health_column = next(
            column for column in sa.inspect(bind).get_columns("risk_alerts")
            if column["name"] == "health_index_snapshot_id"
        )
        if not health_column["nullable"]:
            batch.alter_column(
                "health_index_snapshot_id", existing_type=sa.Uuid(), nullable=True
            )


def downgrade() -> None:
    bind = op.get_bind()
    tables = set(sa.inspect(bind).get_table_names())
    if "risk_alerts" in tables:
        columns = {column["name"] for column in sa.inspect(bind).get_columns("risk_alerts")}
        op.execute(sa.text("DELETE FROM risk_alerts WHERE health_index_snapshot_id IS NULL"))
        with op.batch_alter_table("risk_alerts") as batch:
            if "daily_score_snapshot_id" in columns:
                indexes = {
                    item["name"] for item in sa.inspect(bind).get_indexes("risk_alerts")
                }
                if "ix_risk_alerts_daily_score_snapshot_id" in indexes:
                    batch.drop_index("ix_risk_alerts_daily_score_snapshot_id")
                batch.drop_column("daily_score_snapshot_id")
            batch.alter_column(
                "health_index_snapshot_id", existing_type=sa.Uuid(), nullable=False
            )
    for table in ("daily_score_components", "daily_score_snapshots", "daily_check_ins"):
        if table in set(sa.inspect(bind).get_table_names()):
            op.drop_table(table)
