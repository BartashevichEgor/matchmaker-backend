"""add username to users

Revision ID: 6c8289de3b2a
Revises: 0e5a5b1319e6
"""

import sqlalchemy as sa
from alembic import op

revision = "6c8289de3b2a"
down_revision = "0e5a5b1319e6"
branch_labels = None
depends_on = None


def upgrade():
    # The temporary nullable column makes the upgrade safe for a locally used
    # database that already contains accounts.  Newly generated handles are
    # only a migration fallback: all new accounts must supply a username.
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(length=30), nullable=True))
    op.execute("UPDATE users SET username = 'user_' || id WHERE username IS NULL")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("username", existing_type=sa.String(length=30), nullable=False)
        batch_op.create_unique_constraint("uq_users_username", ["username"])


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_username", type_="unique")
        batch_op.drop_column("username")
