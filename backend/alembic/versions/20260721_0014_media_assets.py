"""Add provider-independent media asset table.

Revision ID: 20260721_0014
Revises: 20260721_0013
"""

import sqlalchemy as sa

from alembic import op

revision = "20260721_0014"
down_revision = "20260721_0013"
branch_labels = None
depends_on = None

MEDIA = "media_assets"


def _tables() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _create_media() -> None:
    op.create_table(
        MEDIA,
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_user_id", sa.Uuid(), nullable=False),
        sa.Column("uploader_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "purpose",
            sa.Enum(
                "generic",
                "avatar",
                "exercise_image",
                "exercise_gif",
                "document",
                name="mediapurpose",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "visibility",
            sa.Enum(
                "private",
                "coach_trainee",
                "exercise",
                name="mediavisibility",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "lifecycle_status",
            sa.Enum(
                "active",
                "replaced",
                "soft_deleted",
                "purged",
                name="medialifecyclestatus",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "storage_provider",
            sa.Enum(
                "local",
                "s3",
                name="mediastorageproviderkind",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("replaced_by_media_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("purged_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("byte_size >= 0", name="ck_media_assets_byte_size"),
        sa.ForeignKeyConstraint(
            ["owner_user_id"], ["users.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["uploader_user_id"], ["users.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["replaced_by_media_id"], [f"{MEDIA}.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_media_assets_storage_key"),
    )
    op.create_index("ix_media_assets_owner_user_id", MEDIA, ["owner_user_id"])
    op.create_index("ix_media_assets_lifecycle_status", MEDIA, ["lifecycle_status"])
    op.create_index(
        "ix_media_assets_owner_lifecycle", MEDIA, ["owner_user_id", "lifecycle_status"]
    )
    op.create_index(
        "ix_media_assets_purpose_lifecycle", MEDIA, ["purpose", "lifecycle_status"]
    )


def upgrade() -> None:
    # The initial revision's live metadata creates this table on a fresh database,
    # so guard the create for real deployed databases where it does not yet exist.
    if MEDIA not in _tables():
        _create_media()


def downgrade() -> None:
    if MEDIA in _tables():
        op.drop_table(MEDIA)
