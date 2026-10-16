"""Run pytest in a newly created disposable database on the configured local PG server."""

import os
import subprocess
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

from app.core.config import get_settings


def main():
    url = make_url(get_settings().database_url)
    if url.get_backend_name() != "postgresql":
        raise SystemExit("Configure local PostgreSQL before running this command.")
    name = "matchmaker_test_" + uuid4().hex
    params = dict(host=url.host, port=url.port, user=url.username, password=url.password, dbname=url.database)
    with psycopg.connect(**params, autocommit=True) as connection:
        connection.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        try:
            env = dict(os.environ)
            env["MATCHMAKER_TEST_DATABASE_URL"] = url.set(database=name).render_as_string(hide_password=False)
            result = subprocess.run([sys.executable, "-m", "pytest", "-q"], env=env, check=False)
        finally:
            connection.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
