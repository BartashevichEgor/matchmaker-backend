# Matchmaker Backend

Backend-only repository for the Matchmaker API: FastAPI, PostgreSQL/SQLite,
JWT authentication, profiles, projects, recommendations, swipes and matches.
The web and mobile clients live in the separate `matchmaker-frontend`
repository. The persisted chat service is planned for Backend Phase 4 and is
not part of this cleanup baseline.

## Requirements

- Python 3.13+
- Docker Desktop for the Compose workflow
- PowerShell on Windows for the examples below

## Local API

Run these commands from the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r core-api/requirements-dev.txt
Copy-Item core-api/.env.example core-api/.env
```

Set a random `JWT_SECRET` of at least 32 characters in `core-api/.env`, then
start the API from `core-api`:

```powershell
Set-Location core-api
..\.venv\Scripts\python.exe -m app.cli bootstrap
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Without `DATABASE_URL`, local development uses SQLite. For PostgreSQL, Redis
and SMTP/Mailpit settings, configure `core-api/.env` explicitly.

Useful endpoints:

- API metadata: `http://127.0.0.1:8000/`
- Swagger: `http://127.0.0.1:8000/docs`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`
- Liveness: `http://127.0.0.1:8000/ping`
- Readiness: `http://127.0.0.1:8000/health`

## Docker Compose

Copy `.env.example` to `.env` at the repository root and replace the example
database password and JWT secret with local-only random values:

```powershell
Copy-Item .env.example .env
docker compose --env-file .env -f deploy/docker-compose.yml up --build -d --wait
docker compose --env-file .env -f deploy/docker-compose.yml ps
docker compose --env-file .env -f deploy/docker-compose.yml logs backend
docker compose -f deploy/docker-compose.yml down
```

Compose starts PostgreSQL, Redis, Mailpit and FastAPI. Mailpit is available at
`http://127.0.0.1:8025`. `docker compose down -v` also deletes the database
and Mailpit volumes; use it only when that data is no longer needed.

## Database and migrations

From `core-api`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic check
```

Read [database documentation](docs/database.md) before changing the schema.
Every schema change requires an Alembic migration; do not reset a shared
database.

## Tests and lint

From `core-api`:

```powershell
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m ruff format --check .
```

The test suite uses isolated SQLite by default. PostgreSQL-specific checks are
available through `python -m scripts.test_postgres` when a test database is
configured.

## Documentation

- [API contract](core-api/docs/api.md)
- [Database](docs/database.md)
- [Deployment](docs/deployment.md)
- [Documentation index](docs/README.md)
- [Backend phase plans](docs/plans/)
- [Contributing](CONTRIBUTING.md)
