"""Extend cards and enforce one project per owner."""

import sqlalchemy as sa
from alembic import op

revision = "mm_20261115_02"
down_revision = "mm_20261115_01"
branch_labels = None
depends_on = None


def upgrade():
    duplicates = (
        op.get_bind()
        .execute(
            sa.text("SELECT owner_id FROM projects GROUP BY owner_id HAVING COUNT(*) > 1 ORDER BY owner_id")
        )
        .scalars()
        .all()
    )
    if duplicates:
        raise RuntimeError(f"Resolve duplicate project owners before migrating: {duplicates}")
    with op.batch_alter_table("profiles") as batch:
        batch.add_column(sa.Column("visibility", sa.String(20), nullable=False, server_default="draft"))
        batch.add_column(sa.Column("work_format", sa.String(20), nullable=False, server_default="remote"))
        batch.create_check_constraint(
            "ck_profile_visibility", "visibility IN ('draft', 'published', 'hidden')"
        )
        batch.create_check_constraint(
            "ck_profile_work_format", "work_format IN ('remote', 'hybrid', 'onsite')"
        )
    with op.batch_alter_table("projects") as batch:
        batch.add_column(sa.Column("visibility", sa.String(20), nullable=False, server_default="draft"))
        batch.add_column(sa.Column("kind", sa.String(20), nullable=False, server_default="project"))
        batch.add_column(sa.Column("work_format", sa.String(20), nullable=False, server_default="remote"))
        batch.add_column(sa.Column("commitment", sa.String(20), nullable=False, server_default="flexible"))
        batch.add_column(sa.Column("website_url", sa.String(300), nullable=True))
        batch.add_column(sa.Column("logo_url", sa.String(300), nullable=True))
        batch.add_column(
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        )
        batch.create_unique_constraint("uq_project_owner", ["owner_id"])
        batch.drop_index("ix_projects_owner_id")
        batch.create_check_constraint(
            "ck_project_visibility", "visibility IN ('draft', 'published', 'hidden')"
        )
        batch.create_check_constraint("ck_project_kind", "kind IN ('project', 'company')")
        batch.create_check_constraint(
            "ck_project_work_format", "work_format IN ('remote', 'hybrid', 'onsite')"
        )
        batch.create_check_constraint(
            "ck_project_commitment", "commitment IN ('full_time', 'part_time', 'flexible')"
        )


def downgrade():
    with op.batch_alter_table("projects") as batch:
        for name in (
            "ck_project_commitment",
            "ck_project_work_format",
            "ck_project_kind",
            "ck_project_visibility",
        ):
            batch.drop_constraint(name, type_="check")
        batch.drop_constraint("uq_project_owner", type_="unique")
        batch.create_index("ix_projects_owner_id", ["owner_id"], unique=False)
        for name in (
            "updated_at",
            "logo_url",
            "website_url",
            "commitment",
            "work_format",
            "kind",
            "visibility",
        ):
            batch.drop_column(name)
    with op.batch_alter_table("profiles") as batch:
        batch.drop_constraint("ck_profile_work_format", type_="check")
        batch.drop_constraint("ck_profile_visibility", type_="check")
        batch.drop_column("work_format")
        batch.drop_column("visibility")
