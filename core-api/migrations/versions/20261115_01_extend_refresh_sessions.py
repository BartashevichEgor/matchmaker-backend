"""extend auth sessions and onboarding mode

Revision ID: mm_20261115_01
Revises: a13c8f92d4be
"""

import sqlalchemy as sa
from alembic import op

revision = "mm_20261115_01"
down_revision = "a13c8f92d4be"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("onboarding_mode", sa.String(length=20), nullable=False, server_default="developer")
        )
        batch_op.create_check_constraint(
            "ck_user_onboarding_mode", "onboarding_mode IN ('developer', 'project')"
        )

    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.add_column(
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        )
        batch_op.add_column(sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("revocation_reason", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("user_agent", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("client_ip_hash", sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table("refresh_sessions") as batch_op:
        batch_op.drop_column("client_ip_hash")
        batch_op.drop_column("user_agent")
        batch_op.drop_column("revocation_reason")
        batch_op.drop_column("revoked_at")
        batch_op.drop_column("last_used_at")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("ck_user_onboarding_mode", type_="check")
        batch_op.drop_column("onboarding_mode")
