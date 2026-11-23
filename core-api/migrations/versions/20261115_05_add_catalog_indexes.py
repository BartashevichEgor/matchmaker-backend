"""Add indexes for catalog, favorites and matching query paths."""

from alembic import op

revision = "mm_20261115_05"
down_revision = "mm_20261115_04"
branch_labels = None
depends_on = None


def upgrade():
    indexes = (
        ("ix_profiles_visibility_role_work_format", "profiles", ["visibility", "role_id", "work_format"]),
        ("ix_projects_catalog", "projects", ["visibility", "status", "updated_at", "id"]),
        ("ix_profile_skills_skill_profile", "profile_skills", ["skill_id", "profile_id"]),
        ("ix_project_skills_skill_project", "project_skills", ["skill_id", "project_id"]),
        ("ix_project_roles_role_project", "project_roles", ["role_id", "project_id"]),
        ("ix_saved_profiles_user_created", "saved_profiles", ["user_id", "created_at"]),
        ("ix_saved_projects_user_created", "saved_projects", ["user_id", "created_at"]),
        (
            "ix_swipes_candidate_direction_project",
            "swipes",
            ["candidate_id", "direction", "project_id"],
        ),
        ("ix_project_members_user_project", "project_members", ["user_id", "project_id"]),
    )
    for name, table, columns in indexes:
        op.create_index(name, table, columns)


def downgrade():
    for name, table in (
        ("ix_project_members_user_project", "project_members"),
        ("ix_swipes_candidate_direction_project", "swipes"),
        ("ix_saved_projects_user_created", "saved_projects"),
        ("ix_saved_profiles_user_created", "saved_profiles"),
        ("ix_project_roles_role_project", "project_roles"),
        ("ix_project_skills_skill_project", "project_skills"),
        ("ix_profile_skills_skill_profile", "profile_skills"),
        ("ix_projects_catalog", "projects"),
        ("ix_profiles_visibility_role_work_format", "profiles"),
    ):
        op.drop_index(name, table_name=table)
