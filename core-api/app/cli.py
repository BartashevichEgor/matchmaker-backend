"""Local setup, demo catalogue seeding, and explicit administrative commands."""

import argparse
import os
import secrets

from app.core.config import ROOT


def init_config():
    path = ROOT / ".env"
    if not path.exists() and not os.environ.get("JWT_SECRET"):
        # Exclusive creation preserves an existing configuration and secret.
        with path.open("x", encoding="utf-8") as stream:
            stream.write(f"ENVIRONMENT=local\nJWT_SECRET={secrets.token_urlsafe(48)}\nMAIL_MODE=outbox\n")
        print("Created core-api/.env with a random local secret.")


def seed():
    from sqlalchemy import select

    from app.core.config import get_settings
    from app.db import SessionLocal
    from app.models import Project, Role, Skill, User

    with SessionLocal() as db:
        for model, names in (
            (
                Skill,
                [
                    "Python",
                    "FastAPI",
                    "PostgreSQL",
                    "SQL",
                    "React",
                    "TypeScript",
                    "Kotlin",
                    "Docker",
                    "Figma",
                    "Node.js",
                ],
            ),
            (Role, ["Backend", "Frontend", "iOS", "UI/UX", "Analyst", "DevOps"]),
        ):
            for name in names:
                if not db.scalar(select(model.id).where(model.name == name)):
                    db.add(model(name=name))
        db.commit()
        # A local demo catalogue makes the first launch useful. Test databases
        # intentionally stay deterministic and contain only fixture data.
        if get_settings().environment != "test":
            demo_projects = (
                (
                    "matchmaker-demo",
                    "demo@matchmaker.local",
                    "Команда для учебного хакатона",
                    "Ищем frontend-разработчика и дизайнера для MVP сервиса подбора команд.",
                ),
                (
                    "matchmaker-catalog",
                    "catalog@matchmaker.local",
                    "Пет-проект Matchmaker",
                    "Развиваем сервис поиска участников: FastAPI, React, PostgreSQL и UX-исследование.",
                ),
            )
            for username, email, title, description in demo_projects:
                owner = db.scalar(select(User).where(User.email == email))
                if not owner:
                    owner = User(
                        username=username,
                        email=email,
                        hashed_password="disabled-demo-account",
                        is_active=True,
                        is_verified=True,
                    )
                    db.add(owner)
                    db.flush()
                if not db.scalar(select(Project.id).where(Project.owner_id == owner.id)):
                    db.add(Project(owner_id=owner.id, title=title, description=description))
            db.commit()
    print("Skills and roles are ready.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init-config", "seed", "bootstrap", "make-admin"])
    parser.add_argument("--email")
    args = parser.parse_args()
    if args.command in ("init-config", "bootstrap"):
        init_config()
    if args.command == "bootstrap":
        from alembic import command
        from alembic.config import Config

        command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    if args.command in ("seed", "bootstrap"):
        seed()
    if args.command == "make-admin":
        from sqlalchemy import select

        from app.db import SessionLocal
        from app.models import User

        if not args.email:
            parser.error("--email is required")
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == args.email.lower()))
            if not user or not user.is_verified:
                parser.error("Register and verify this user first")
            user.is_admin = True
            db.commit()
        print("Administrator role granted.")


if __name__ == "__main__":
    main()
