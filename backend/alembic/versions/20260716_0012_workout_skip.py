"""Add explicit pre-start whole-workout skip metadata.

Revision ID: 20260716_0012
Revises: 20260716_0011
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0012"
down_revision = "20260716_0011"
branch_labels = None
depends_on = None

TABLE = "scheduled_workouts"
NEW_COLUMNS = ("skip_kind", "skip_reason", "skip_note", "skipped_at")


def _existing_columns() -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    existing = _existing_columns()
    if set(NEW_COLUMNS).issubset(existing):
        return
    with op.batch_alter_table(TABLE) as batch:
        if "skip_kind" not in existing:
            batch.add_column(sa.Column("skip_kind", sa.String(length=10), nullable=True))
        if "skip_reason" not in existing:
            batch.add_column(sa.Column("skip_reason", sa.String(length=40), nullable=True))
        if "skip_note" not in existing:
            batch.add_column(sa.Column("skip_note", sa.String(length=500), nullable=True))
        if "skipped_at" not in existing:
            batch.add_column(sa.Column("skipped_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    existing = _existing_columns()
    if not set(NEW_COLUMNS).intersection(existing):
        return
    with op.batch_alter_table(TABLE) as batch:
        for column in ("skipped_at", "skip_note", "skip_reason", "skip_kind"):
            if column in existing:
                batch.drop_column(column)
