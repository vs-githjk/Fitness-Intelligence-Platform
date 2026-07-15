"""mark controlled public demo accounts

Revision ID: 20260716_0004
Revises: 20260715_0003
Create Date: 2026-07-16
"""

import sqlalchemy as sa

from alembic import op

revision = "20260716_0004"
down_revision = "20260715_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("users")}
    if "is_demo" in columns:
        return
    op.add_column(
        "users",
        sa.Column("is_demo", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    columns = {item["name"] for item in sa.inspect(op.get_bind()).get_columns("users")}
    if "is_demo" in columns:
        op.drop_column("users", "is_demo")
