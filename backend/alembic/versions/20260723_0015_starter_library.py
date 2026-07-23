"""Add starter-library ownership marker and clone attribution.

Revision ID: 20260723_0015
Revises: 20260721_0014

Additive and non-destructive:
- users.is_system marks the single non-login account that owns the read-only
  curated starter library.
- workout_templates.cloned_from_template_id and training_programs.
  cloned_from_program_id record independent-snapshot attribution when coach content
  is cloned from starter content (self-referential; no cross-table cycle).

Existing coach and trainee rows, programs, and assignments are untouched.
"""

import sqlalchemy as sa

from alembic import op

revision = "20260723_0015"
down_revision = "20260721_0014"
branch_labels = None
depends_on = None


def _columns(table: str) -> set[str]:
    return {col["name"] for col in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    users = _columns("users")
    if "is_system" not in users:
        with op.batch_alter_table("users") as batch:
            batch.add_column(
                sa.Column(
                    "is_system",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )

    if "cloned_from_template_id" not in _columns("workout_templates"):
        with op.batch_alter_table("workout_templates") as batch:
            batch.add_column(
                sa.Column(
                    "cloned_from_template_id",
                    sa.Uuid(),
                    sa.ForeignKey(
                        "workout_templates.id",
                        name="fk_workout_templates_cloned_from",
                        ondelete="SET NULL",
                    ),
                    nullable=True,
                )
            )

    if "cloned_from_program_id" not in _columns("training_programs"):
        with op.batch_alter_table("training_programs") as batch:
            batch.add_column(
                sa.Column(
                    "cloned_from_program_id",
                    sa.Uuid(),
                    sa.ForeignKey(
                        "training_programs.id",
                        name="fk_training_programs_cloned_from",
                        ondelete="SET NULL",
                    ),
                    nullable=True,
                )
            )


def downgrade() -> None:
    if "cloned_from_program_id" in _columns("training_programs"):
        with op.batch_alter_table("training_programs") as batch:
            batch.drop_column("cloned_from_program_id")

    if "cloned_from_template_id" in _columns("workout_templates"):
        with op.batch_alter_table("workout_templates") as batch:
            batch.drop_column("cloned_from_template_id")

    if "is_system" in _columns("users"):
        with op.batch_alter_table("users") as batch:
            batch.drop_column("is_system")
