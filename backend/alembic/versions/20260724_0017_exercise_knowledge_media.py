"""Add exercise knowledge fields and authored media references.

Revision ID: 20260724_0017
Revises: 20260724_0016

Additive and non-destructive. Extends exercise_versions so an exercise becomes a
rich knowledge object:
- difficulty, coaching_cues, and common_mistakes carry instructional metadata
  (never medical advice).
- primary_image_media_id, secondary_image_media_id, and demonstration_video_media_id
  reference ACTIVE MediaAssets (SET NULL if an asset row is removed): one primary
  image, one optional secondary image, one optional demonstration video.

Existing exercise versions are untouched; every new column is nullable, so already
published (immutable) versions keep their exact content.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260724_0017"
down_revision = "20260724_0016"
branch_labels = None
depends_on = None

TABLE = "exercise_versions"

_SCALAR_COLUMNS = (
    (
        "difficulty",
        sa.Enum(
            "beginner",
            "intermediate",
            "advanced",
            name="exercisedifficulty",
            native_enum=False,
        ),
    ),
    ("coaching_cues", sa.JSON()),
    ("common_mistakes", sa.JSON()),
)
_MEDIA_COLUMNS = (
    ("primary_image_media_id", "fk_exercise_versions_primary_image"),
    ("secondary_image_media_id", "fk_exercise_versions_secondary_image"),
    ("demonstration_video_media_id", "fk_exercise_versions_demonstration_video"),
)


def _columns() -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(TABLE)}


def upgrade() -> None:
    existing = _columns()
    with op.batch_alter_table(TABLE) as batch:
        for name, column_type in _SCALAR_COLUMNS:
            if name not in existing:
                batch.add_column(sa.Column(name, column_type, nullable=True))
        for name, fk_name in _MEDIA_COLUMNS:
            if name not in existing:
                batch.add_column(
                    sa.Column(
                        name,
                        sa.Uuid(),
                        sa.ForeignKey(
                            "media_assets.id", name=fk_name, ondelete="SET NULL"
                        ),
                        nullable=True,
                    )
                )


def downgrade() -> None:
    existing = _columns()
    with op.batch_alter_table(TABLE) as batch:
        for name, _fk_name in reversed(_MEDIA_COLUMNS):
            if name in existing:
                batch.drop_column(name)
        for name, _column_type in reversed(_SCALAR_COLUMNS):
            if name in existing:
                batch.drop_column(name)
