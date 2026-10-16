import os
import re
import tempfile
from pathlib import Path

import pytest

_test_dir = tempfile.TemporaryDirectory(prefix="matchmaker-tests-")
os.environ["ENVIRONMENT"] = "test"
os.environ["JWT_SECRET"] = "test-only-secret-not-for-any-real-deployment-12345"
os.environ["DATABASE_URL"] = os.environ.get(
    "MATCHMAKER_TEST_DATABASE_URL", "sqlite:///" + (Path(_test_dir.name) / "test.db").as_posix()
)
os.environ["MAIL_MODE"] = "outbox"
os.environ["OUTBOX_DIR"] = str(Path(_test_dir.name) / "outbox")
os.environ.pop("REDIS_URL", None)

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.cli import seed  # noqa: E402
from app.core.config import ROOT, get_settings  # noqa: E402
from app.core.limits import _local  # noqa: E402
from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def migrated_database():
    if engine.dialect.name == "postgresql":
        assert engine.url.database.startswith("matchmaker_test"), (
            "Refusing to test against a non-test database"
        )
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    command.check(Config(str(ROOT / "alembic.ini")))
    command.downgrade(Config(str(ROOT / "alembic.ini")), "base")
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    yield
    engine.dispose()
    _test_dir.cleanup()


@pytest.fixture(autouse=True)
def clean_database(migrated_database):
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            tables = ", ".join('"' + table.name + '"' for table in Base.metadata.sorted_tables)
            connection.execute(text("TRUNCATE " + tables + " RESTART IDENTITY CASCADE"))
        else:
            for table in reversed(Base.metadata.sorted_tables):
                connection.execute(table.delete())
    _local.clear()
    seed()
    yield


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def read_code(email, purpose="verify"):
    files = sorted(get_settings().outbox_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    for file in files:
        body = file.read_text(encoding="utf-8")
        if f"To: {email}\n" in body and f"Purpose: {purpose}\n" in body:
            return re.search(r"Code: (\d{6})", body)[1]
    raise AssertionError("No email was written")


@pytest.fixture
def account(client):
    def create(email="student@example.com"):
        password = "ValidPassword123!"
        username = re.sub(r"[^a-z0-9._-]", "-", email.split("@", 1)[0].lower())
        result = client.post(
            "/api/v1/auth/register",
            json={
                "username": username,
                "email": email,
                "password": password,
                "password_confirm": password,
            },
        )
        assert result.status_code == 201, result.text
        result = client.post("/api/v1/auth/verify-email", json={"email": email, "code": read_code(email)})
        assert result.status_code == 200, result.text
        result = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert result.status_code == 200, result.text
        tokens = result.json()
        headers = {"Authorization": "Bearer " + tokens["access_token"]}
        user = client.get("/api/v1/users/me", headers=headers).json()
        return user, headers, tokens

    return create
