# Matchmaker

Монорепозиторий учебного проекта Matchmaker: сервис поиска людей и проектов для команд.

| Каталог | Назначение |
| --- | --- |
| `core-api/` | FastAPI, PostgreSQL/SQLite, JWT, профили, навыки, проекты, мэтчи и Swagger. |
| `frontend/` | React + TypeScript + Vite веб-клиент: регистрация, подтверждение e-mail, вход и защищённые экраны. |
| `chat-service/` | Отдельный Node.js-сервис чата. |

## Быстрый локальный запуск

1. Создайте Python-окружение `.venv` в корне и установите `core-api/requirements-dev.txt`.
2. Из корня выполните:

```powershell
.\start-demo.ps1
```

Скрипт запускает API в фоне и открывает Vite-клиент на `http://127.0.0.1:5173`.
Если локальная PostgreSQL занята или недоступна, используйте:

```powershell
.\start-demo.ps1 -UseSqlite
```

Этот режим создаёт отдельную локальную SQLite-базу и не затрагивает PostgreSQL-данные. Код подтверждения при `MAIL_MODE=outbox` сохраняется в `core-api/.local/outbox/`.

API: `http://127.0.0.1:8000/` · Swagger: `http://127.0.0.1:8000/docs`.
Пользовательские пароли, письма и базы в Git не включаются.
