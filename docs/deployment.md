# Развёртывание Matchmaker

## 1. Требования

Для локальной разработки нужны Python 3.13, Node.js 20+ и PowerShell. Для контейнерного запуска нужен Docker Desktop. PostgreSQL и Docker не обязательны для SQLite-демонстрации.

## 2. Структура

`core-api/` содержит FastAPI и миграции; `frontend/web/` — React/Vite; `chat-service/` — WebSocket; `deploy/` — production-подобный Compose. Конфигурацию не коммитим: используются `.env` и `.env.example`.

## 3. Переменные окружения

| Переменная | Назначение | Пример |
| --- | --- | --- |
| `DATABASE_URL` | URL SQLAlchemy | `postgresql+psycopg://user:password@db:5432/matchmaker` |
| `JWT_SECRET` | Секрет JWT, не менее 32 символов | случайная строка |
| `ENVIRONMENT` | `local`, `test`, `production` | `local` |
| `MAIL_MODE` | Локальная почта или SMTP | `outbox` |
| `VITE_API_BASE_URL` | Базовый API web-клиента | `/api/v1` или `http://127.0.0.1:8000/api/v1` |

## 4. Запуск, проверка и остановка

Локально: `./start-demo.ps1 -UseSqlite`; затем открыть `http://127.0.0.1:5173/register`. Проверка: `Invoke-WebRequest http://127.0.0.1:8000/health`. Остановить процессы можно через закрытие терминалов или по PID, записанному `start-background.ps1`.

Контейнерно: `cd deploy`, скопировать `.env.example` в `.env`, заменить секреты, затем выполнить `docker compose up --build -d`, `docker compose ps`, `docker compose logs backend`. Остановка: `docker compose down`; команда с `-v` удалит данные БД и применяется только намеренно.

## 5. Сервисы и порты

| Сервис | Порт хоста | Назначение |
| --- | --- | --- |
| frontend/nginx | 8080 | React и обратный прокси `/api/` |
| backend/FastAPI | внутренний 8000 | API и `/health` |
| db/PostgreSQL 17 | внутренний 5432 | постоянные данные |
| chat-service | 8010 локально | WebSocket-групповой чат |

## 6. Версионный запуск

Для воспроизводимой демонстрации: `git fetch --tags`, `git checkout v0.N.0`, затем выполнить запуск из пункта 4. Вернуться к разработке: `git switch main`.

## 7. Частые ошибки

`401/403` после входа — подтвердите e-mail и повторно войдите. `503` на `/health` — проверьте `DATABASE_URL`, миграции и состояние PostgreSQL. Ошибка CORS при локальной Vite-разработке — укажите origin в `CORS_ORIGINS`; в Docker используйте тот же origin через nginx. Пустой каталог — выполните `python -m app.cli seed` после миграций.
