# matchmaker-backend
Backend REST API &amp; Scoring Engine for Project Matchmaker (FastAPI + PostgreSQL)

Основной backend находится в [core-api](core-api/README.md): регистрация, JWT, профили, навыки, проекты, ранжирование и matches. Каталог `chat-service` предназначен для отдельного Node.js-сервиса Ромы.

Локальный запуск на Windows из корня: `./start.ps1`. Предварительно установите зависимости из `core-api/requirements-dev.txt` в `.venv`. Фоновый запуск: `./start-background.ps1`.

Приложение: http://127.0.0.1:8000/ ; Swagger: http://127.0.0.1:8000/docs . Контейнерное окружение описано в `docker-compose.yml` и README сервиса. Пользовательские пароли, письма и базы в Git не включаются.
