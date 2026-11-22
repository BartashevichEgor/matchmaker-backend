"""Add private in-app notifications."""

import sqlalchemy as sa
from alembic import op

revision = "mm_20261115_04"
down_revision = "mm_20261115_03"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), primary_key=True),
        sa.Column(
            "recipient_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(length=30), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("event_key", sa.String(length=160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("type IN ('match_created', 'project_joined')", name="ck_notification_type"),
        sa.UniqueConstraint("event_key", name="uq_notification_event_key"),
    )
    op.create_index("ix_notifications_recipient_created", "notifications", ["recipient_id", "created_at"])
    op.create_index("ix_notifications_recipient_read", "notifications", ["recipient_id", "read_at"])


def downgrade():
    op.drop_index("ix_notifications_recipient_read", table_name="notifications")
    op.drop_index("ix_notifications_recipient_created", table_name="notifications")
    op.drop_table("notifications")
