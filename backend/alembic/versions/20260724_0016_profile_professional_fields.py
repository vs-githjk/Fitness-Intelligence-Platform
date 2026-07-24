"""Add professional profile fields and avatar reference to user_profiles.

Revision ID: 20260724_0016
Revises: 20260723_0015

Additive and non-destructive. Extends the shared, role-agnostic user_profiles
record so both roles can maintain a polished profile on top of the existing
identity and media infrastructure:
- headline, coaching_specialties, years_of_experience, certifications_text are
  surfaced for coaches; training_goals is surfaced for trainees. All are optional
  and self-declared; none are verified.
- avatar_media_id points at the current ACTIVE avatar MediaAsset and is SET NULL if
  that asset row is ever removed.

Existing profile rows are untouched; every new column is nullable.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260724_0016"
down_revision = "20260723_0015"
branch_labels = None
depends_on = None

_NEW_COLUMNS = (
    ("headline", sa.String(length=160)),
    ("coaching_specialties", sa.JSON()),
    ("years_of_experience", sa.Integer()),
    ("certifications_text", sa.Text()),
    ("training_goals", sa.Text()),
)


def _columns(table: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    existing = _columns("user_profiles")
    with op.batch_alter_table("user_profiles") as batch:
        for name, column_type in _NEW_COLUMNS:
            if name not in existing:
                batch.add_column(sa.Column(name, column_type, nullable=True))
        if "avatar_media_id" not in existing:
            batch.add_column(
                sa.Column(
                    "avatar_media_id",
                    sa.Uuid(),
                    sa.ForeignKey(
                        "media_assets.id",
                        name="fk_user_profiles_avatar_media",
                        ondelete="SET NULL",
                    ),
                    nullable=True,
                )
            )


def downgrade() -> None:
    existing = _columns("user_profiles")
    with op.batch_alter_table("user_profiles") as batch:
        if "avatar_media_id" in existing:
            batch.drop_column("avatar_media_id")
        for name, _column_type in reversed(_NEW_COLUMNS):
            if name in existing:
                batch.drop_column(name)
