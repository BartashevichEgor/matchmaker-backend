"""Add private saved cards."""

import sqlalchemy as sa
from alembic import op

revision = "mm_20261115_03"
down_revision = "mm_20261115_02"
branch_labels = None
depends_on = None


def upgrade():
    for table, target, foreign_table in (
        ("saved_profiles", "target_user_id", "users.id"),
        ("saved_projects", "project_id", "projects.id"),
    ):
        op.create_table(
            table,
            sa.Column(
                "user_id",
                sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column(
                target,
                sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
                sa.ForeignKey(foreign_table, ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade():
    op.drop_table("saved_projects")
    op.drop_table("saved_profiles")
