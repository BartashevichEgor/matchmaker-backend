from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import ROOT


def test_empty_database_upgrades_and_creates_catalog_indexes(tmp_path):
    database_path = tmp_path / "migration-test.db"
    engine = create_engine(f"sqlite:///{database_path}")
    config = Config(str(ROOT / "alembic.ini"))

    with engine.connect() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

        expected = {
            "profiles": {"ix_profiles_visibility_role_work_format"},
            "projects": {"ix_projects_catalog"},
            "profile_skills": {"ix_profile_skills_skill_profile"},
            "project_skills": {"ix_project_skills_skill_project"},
            "project_roles": {"ix_project_roles_role_project"},
            "saved_profiles": {"ix_saved_profiles_user_created"},
            "saved_projects": {"ix_saved_projects_user_created"},
            "swipes": {"ix_swipes_candidate_direction_project"},
            "project_members": {"ix_project_members_user_project"},
            "notifications": {
                "ix_notifications_recipient_created",
                "ix_notifications_recipient_read",
            },
        }
        inspector = inspect(connection)
        for table, expected_names in expected.items():
            actual_names = {index["name"] for index in inspector.get_indexes(table)}
            assert expected_names <= actual_names, (
                f"Missing indexes from {table}: {expected_names - actual_names}"
            )

        command.downgrade(config, "base")
        command.upgrade(config, "head")

    engine.dispose()
