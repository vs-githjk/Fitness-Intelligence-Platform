"""Add password_reset_tokens for self-service password reset.

Revision ID: 20260814_0018
Revises: 20260724_0017

Additive and non-destructive. Creates a single table holding only the SHA-256 hash of an
opaque reset token (never the raw token), with an expiry and a single-use marker. No
existing table is altered.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260814_0018"
down_revision = "20260724_0017"
branch_labels = None
depends_on = None

TABLE = "password_reset_tokens"


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    if TABLE in _tables():
        return
    op.create_table(
        TABLE,
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash", name="uq_password_reset_tokens_token_hash"),
    )
    op.create_index(
        "ix_password_reset_tokens_user_id", TABLE, ["user_id"], unique=False
    )
    op.create_index(
        "ix_password_reset_tokens_expires_at", TABLE, ["expires_at"], unique=False
    )


def downgrade() -> None:
    if TABLE not in _tables():
        return
    op.drop_index("ix_password_reset_tokens_expires_at", table_name=TABLE)
    op.drop_index("ix_password_reset_tokens_user_id", table_name=TABLE)
    op.drop_table(TABLE)
