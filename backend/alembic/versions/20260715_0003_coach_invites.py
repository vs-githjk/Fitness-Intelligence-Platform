"""Add secure single-use coach invitations."""

import sqlalchemy as sa

from alembic import op

revision = "20260715_0003"
down_revision = "20260714_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "coach_invites" in set(sa.inspect(bind).get_table_names()):
        return
    op.create_table(
        "coach_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("coach_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("intended_email", sa.String(length=320), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("used_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["coach_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash", name="uq_coach_invites_token_hash"),
        sa.UniqueConstraint("used_by_user_id", name="uq_coach_invites_used_by_user_id"),
    )
    op.create_index("ix_coach_invites_coach_id", "coach_invites", ["coach_id"])
    op.create_index(
        "ix_coach_invites_coach_created", "coach_invites", ["coach_id", "created_at"]
    )
    op.create_index("ix_coach_invites_expires_at", "coach_invites", ["expires_at"])
    op.create_index("ix_coach_invites_intended_email", "coach_invites", ["intended_email"])
    op.create_index("ix_coach_invites_token_hash", "coach_invites", ["token_hash"])


def downgrade() -> None:
    if "coach_invites" in set(sa.inspect(op.get_bind()).get_table_names()):
        op.drop_table("coach_invites")
