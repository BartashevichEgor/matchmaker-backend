"""expand username for web client

Revision ID: a13c8f92d4be
Revises: 6c8289de3b2a
"""

import sqlalchemy as sa
from alembic import op

revision = "a13c8f92d4be"
down_revision = "6c8289de3b2a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=30),
            type_=sa.String(length=50),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=50),
            type_=sa.String(length=30),
            existing_nullable=False,
        )
