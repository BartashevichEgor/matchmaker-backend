# Matchmaker Core API

FastAPI-сервис для поиска проектных команд. Реализованы регистрация и подтверждение email, вход и восстановление пароля, JWT с ротацией refresh-токенов, профили и навыки, проекты, рекомендации, свайпы и matches. На `/` находится небольшая демонстрационная страница по макетам входа/регистрации; основной React-клиент и iOS разрабатываются отдельно.

## Быстрый запуск на Windows

Команды выполняются из корня репозитория, где находятся `core-api` и `chat-service`:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r core-api/requirements-dev.txt
.\start.ps1
```

Если окружение уже создано, первый пункт пропустите. `start.ps1` создаёт отсутствующий `core-api/.env` со случайным JWT-секретом, применяет миграции, добавляет справочники и запускает сервер. Существующий `.env` сохраняется. Без DATABASE_URL используется SQLite. Если уже инициализирован отдельный локальный PostgreSQL проекта, скрипт запускает его перед API.

Если политика PowerShell запрещает запуск скриптов, выполните эквивалентные команды без изменения политики:

```powershell
cd core-api
..\.venv\Scripts\python.exe -m app.cli bootstrap
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Главная страница: http://127.0.0.1:8000/ ; Swagger: http://127.0.0.1:8000/docs ; проверка: http://127.0.0.1:8000/health . Swagger использует локальные JS/CSS, поэтому не требует CDN. Закрытие терминала или Ctrl+C останавливает обычный dev-сервер. Для фонового запуска из корня предусмотрен `start-background.ps1`; он не включает autoreload. Логи фонового запуска — `core-api/.local/server.stderr.log`, PID — `core-api/.local/server.pid`. Автозапуск после перезагрузки Windows не устанавливается.

## PostgreSQL на этом компьютере

Обнаруженная установка PostgreSQL 16 используется отдельным экземпляром проекта на `127.0.0.1:55432`. Данные лежат в `core-api/.local/postgres`. Существующая Windows-служба PostgreSQL и её данные не меняются. Запуск из корня: `./start-local-db.ps1`. При первой инициализации создаётся случайный пароль, SCRAM-аутентификация и локальная строка подключения; секреты исключены из Git. Эта установка предназначена для локальной разработки, не для публикации в интернет.

При переносе на другой компьютер можно указать свой DATABASE_URL либо использовать Docker Compose. Не копируйте готовую `.venv` между компьютерами; создайте её заново. Локальная база SQLite, если была создана ранее, автоматически в PostgreSQL не переносится.

## Docker Compose

Нужен установленный и запущенный Docker. Из корня скопируйте `.env.example` в `.env` и заполните `POSTGRES_PASSWORD` случайной строкой из букв/цифр, а `JWT_SECRET` — случайной строкой не короче 32 символов. Для генерации можно выполнить `python -c "import secrets; print(secrets.token_hex(32))"` дважды.

```powershell
docker compose up --build -d
docker compose ps
docker compose logs api
```

Compose запускает PostgreSQL 16, Redis 7, API и Mailpit. БД и Redis не публикуются наружу. API: localhost:8000; тестовая почта: localhost:8025. Прежде остановите другой сервер на 8000. `docker compose down` останавливает контейнеры и сохраняет volumes. Удаление volumes приводит к потере данных.

Docker на текущем компьютере не установлен, поэтому сборка образа и запуск Compose здесь пока не проверены. Реальная БД для текущего локального запуска — отдельный PostgreSQL, а не контейнер.

## Email и вход

В локальном режиме `MAIL_MODE=outbox`: письма сохраняются как TXT в `core-api/.local/outbox`, а не отправляются адресату. На регистрации укажите уникальный `username` от 1 до 50 символов (краевые пробелы будут убраны), затем откройте последнее письмо, скопируйте код и подтвердите email. После этого войдите. Пароль должен содержать 8–128 символов. Код действует 10 минут; повторная отправка заменяет предыдущий. Тесты создают временные аккаунты только в отдельной тестовой базе; готовых пользователей и общих паролей в рабочую БД не добавляется.

В Compose используется SMTP Mailpit — письма доступны в его веб-интерфейсе. Для внешнего SMTP укажите реальный адрес, учётные данные и соответствующие STARTTLS/SSL-настройки. Реальная доставка зависит от этого провайдера и отдельно проверяется перед деплоем.

## Учебная демонстрация с другой машины

Для задания о сетевом взаимодействии backend можно временно открыть через SSH-туннель `localhost.run`. На компьютере с работающим API выполните из корня репозитория:

```powershell
ssh -T -R 80:127.0.0.1:8000 nokey@localhost.run
```

Сервис выведет временный HTTPS-адрес вида `https://<случайное-имя>.lhr.life`. На компьютере с React-клиентом запишите в `web/.env`:

```env
VITE_API_BASE_URL=https://<случайное-имя>.lhr.life/api/v1
```

После перезапуска Vite формы работают с этим API. На API уже разрешены origins локального Vite (`http://localhost:5173` и `http://127.0.0.1:5173`). URL действует, пока открыт SSH-процесс; это канал для учебной демонстрации, а не production-развёртывание. Не публикуйте реальные пароли или персональные данные через временный адрес.

В Swagger сначала вызовите login, скопируйте `access_token`, нажмите Authorize и вставьте токен без префикса Bearer. На демонстрационной странице токены живут только в памяти вкладки: после обновления нужен новый вход.

## Переменные окружения

| Имя | Назначение | Локальное значение по умолчанию |
|---|---|---|
| ENVIRONMENT | local/test/production | local |
| DATABASE_URL | SQLAlchemy URL | SQLite в core-api/local.db при отсутствии настройки |
| JWT_SECRET | Секрет подписи и HMAC кодов | Обязателен; bootstrap генерирует |
| JWT_ISSUER | Издатель токенов | matchmaker |
| ACCESS_MINUTES | Срок access JWT | 15 |
| REFRESH_DAYS | Срок refresh JWT | 7 |
| REDIS_URL | Redis для общих лимитов | Нет; один процесс с локальными лимитами |
| CORS_ORIGINS | JSON-массив origin клиентов | localhost:5173 и 127.0.0.1:5173 |
| MAIL_MODE | outbox/smtp | outbox |
| OUTBOX_DIR | Путь локальных писем | core-api/.local/outbox |
| MAIL_SERVER / MAIL_PORT | SMTP-сервер | localhost / 1025 |
| MAIL_FROM | Отправитель | noreply@matchmaker.local |
| MAIL_USERNAME / MAIL_PASSWORD | SMTP-аутентификация | Пустые |
| MAIL_STARTTLS / MAIL_SSL_TLS | Шифрование SMTP | false / false |
| MAIL_USE_CREDENTIALS | Использовать SMTP-логин | false |

В production настройки требуют PostgreSQL, Redis и SMTP. Root `.env` предназначен для Compose; `core-api/.env` — для Python-процесса. Переменные процесса имеют приоритет. Сессии хранятся в реляционной БД для надёжного отзыва; Redis используется для лимитов. Кэширование сессий в Redis пока не реализовано.

## Миграции и проверка

Из `core-api`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic check
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m scripts.test_postgres
..\.venv\Scripts\python.exe -m ruff check .
..\.venv\Scripts\python.exe -m ruff format --check .
```

Обычный pytest использует временную SQLite. `scripts.test_postgres` создаёт новую БД с уникальным именем на настроенном PostgreSQL, выполняет тесты и удаляет только эту тестовую БД. Команды требуют прав CREATE DATABASE. Схема проверяется применением, откатом и повторным применением миграции в тестовой базе. GitHub Actions содержит отдельные проверки SQLite и PostgreSQL; фактический запуск CI требует отправки изменений в GitHub.

Требования верхнего уровня закреплены по версиям; полный транзитивный lock пока не используется. Ruff отвечает за стиль и ошибки Python. Проверка SonarLint/SonarQube for IDE остаётся локальной настройкой редактора команды.

## Назначение администратора

Зарегистрируйте пользователя, подтвердите email, затем из `core-api` выполните:

```powershell
..\.venv\Scripts\python.exe -m app.cli make-admin --email your-email@example.com
```

Обычная регистрация и PATCH анкеты не позволяют выдать себе права администратора.

## Структура

`app/api` — маршруты; `app/core` — конфигурация, безопасность, лимиты; `app/models.py` — таблицы; `app/schemas.py` — HTTP-модели; `app/services` — представления, почта и scoring; `migrations` — версия схемы; `tests` — сценарии; `app/static` — демонстрационная страница.

Подробнее: [схема БД](docs/database.md), [контракт API и чата](docs/api.md), [интеграция React с FastAPI](docs/frontend-integration.md), [материалы сдачи](docs/delivery.md), [деплой](docs/deployment.md).
