# Развёртывание Matchmaker Backend

## 1. Требования

Для локальной разработки нужен Python 3.13. Для контейнерного запуска нужен
Docker Desktop. PostgreSQL и Docker не обязательны для SQLite-тестов.

Клиенты Matchmaker поддерживаются в отдельном репозитории; этот репозиторий
содержит только API и backend-инфраструктуру.

## 2. Переменные окружения

| Переменная | Назначение | Пример |
| --- | --- | --- |
| `DATABASE_URL` | URL SQLAlchemy | `postgresql+psycopg://user:password@db:5432/matchmaker` |
| `JWT_SECRET` | Секрет JWT, не менее 32 символов | случайная строка |
| `ENVIRONMENT` | `local`, `test`, `production` | `local` |
| `REDIS_URL` | Redis для общих rate limits | `redis://redis:6379/0` |
| `MAIL_MODE` | Локальная почта или SMTP | `outbox` |
| `MAIL_SERVER` | SMTP/Mailpit host | `127.0.0.1` |
| `MAIL_PORT` | SMTP/Mailpit port | `1025` |

Локальная конфигурация находится в `core-api/.env` и не коммитится.
Конфигурация Compose находится в корневом `.env`, который создаётся из
`.env.example`.

## 3. Прямой запуск API

Из корня репозитория:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r core-api/requirements-dev.txt
Copy-Item core-api/.env.example core-api/.env
Set-Location core-api
..\.venv\Scripts\python.exe -m app.cli bootstrap
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Проверка:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
```

## 4. Docker Compose

Из корня репозитория:

```powershell
Copy-Item .env.example .env
docker compose -f deploy/docker-compose.yml up --build -d
docker compose -f deploy/docker-compose.yml ps
docker compose -f deploy/docker-compose.yml logs backend
```

Этот Compose запускает PostgreSQL и FastAPI. Остановка:

```powershell
docker compose -f deploy/docker-compose.yml down
```

Команда `docker compose -f deploy/docker-compose.yml down -v` удаляет volume БД и применяется
только намеренно.

## 5. Сервисы и порты

| Сервис | Порт хоста | Назначение |
| --- | --- | --- |
| API | `127.0.0.1:8000` | FastAPI, Swagger и health endpoints |
| PostgreSQL | внутренний Compose-порт | постоянные данные |

## 6. Частые ошибки

`503` на `/health` означает недоступность БД, Redis или другой обязательной
зависимости. Ошибка CORS означает, что клиентский origin не добавлен в
`CORS_ORIGINS`. Пустые справочники требуют запуска `python -m app.cli seed`
после миграций.
