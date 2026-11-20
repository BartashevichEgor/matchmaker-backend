# Matchmaker Core API

FastAPI service for registration and email verification, authentication,
profiles, skills, projects, recommendations, swipes and matches. The API is
the backend source of truth; client applications are maintained separately.

## Local setup

Run setup from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r core-api/requirements-dev.txt
Copy-Item core-api/.env.example core-api/.env
```

Set a random `JWT_SECRET` of at least 32 characters in `core-api/.env`, then
run these commands from `core-api`:

```powershell
..\.venv\Scripts\python.exe -m app.cli bootstrap
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Without `DATABASE_URL`, the local API uses SQLite. Configure PostgreSQL,
Redis and SMTP/Mailpit explicitly in `core-api/.env` when needed.

Endpoints:

- API metadata: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Liveness: `http://127.0.0.1:8000/ping`
- Readiness: `http://127.0.0.1:8000/health`

## Docker Compose

From the repository root, copy `.env.example` to `.env`, replace the example
database password and JWT secret, then run:

```powershell
docker compose -f deploy/docker-compose.yml up --build -d
docker compose -f deploy/docker-compose.yml ps
docker compose -f deploy/docker-compose.yml logs backend
```

Compose starts PostgreSQL and FastAPI. Stop it with
`docker compose -f deploy/docker-compose.yml down`. The `-v` option also
deletes the database volume.

## Migrations

Run from `core-api`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic check
```

Use Alembic for every schema change. Do not reset a shared database.

## Tests and lint

Run from `core-api`:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m ruff format --check .
```

The default test suite uses isolated SQLite. PostgreSQL-specific checks are
available through `python -m scripts.test_postgres` when a test database is
configured.

## Structure

- `app/api` — HTTP routes.
- `app/core` — configuration, security and rate limits.
- `app/models.py` — database models.
- `app/schemas.py` — HTTP schemas.
- `app/services` — mail, scoring and view services.
- `migrations` — Alembic migrations.
- `tests` — API and domain tests.

See [API contract](docs/api.md), [database documentation](docs/database.md),
[deployment documentation](../docs/deployment.md) and the [backend phase
plans](../docs/plans/).
