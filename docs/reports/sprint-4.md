# Спринт 4 — безопасность и интеграция (12.10–25.10.2026)

## 4/S1. Бэклог Sprint 4

Приоритеты: pytest и журналирование backend, JWT, Swagger/OpenAPI, сетевое
взаимодействие клиентов с API. Definition of Done: код, тест, документация,
безопасная ошибка и доказательство запуска.

## 4/S2. Scrum meeting 07 — неделя 7

Егор реализовал FastAPI MVP: миграции, PostgreSQL-модель, регистрацию,
подтверждение e-mail, JWT, профили, навыки, проекты, рекомендации, swipes и
matches. Роман довёл web-экраны и auth flow. Алина добавила KMP-экраны и
сетевые модели. Вероника проверила Figma-соответствие и UI-состояния.

Блокер: контракт web/KMP и API уточнялся по `username`, e-mail verification
и полям JSON. Решение: контракт задокументирован в Swagger и `api.md`.

## 4/S3. Scrum meeting 08 — неделя 8

Сделаны реальная регистрация → outbox-код → подтверждение → login → JWT и
базовая интеграция клиентов. В backend добавлены request logging и тесты.
Следующий приоритет: внешний сетевой запуск и чат.

## 4/S4. Review & Retrospective

**Готово:** backend-ядро, JWT, Swagger, тесты, health, документация,
web/KMP auth contract. **Не готово:** полноценный внешний стенд и чат.

**Улучшение:** фиксировать тестовый сценарий как цепочку запросов и не
называть Docker-проверенным, пока Docker реально не запускался.

## 4/1. Тестирование и логирование backend

Используются pytest/FastAPI TestClient и изолированные тестовые БД. Логи
содержат метод, путь, статус, длительность и request ID; пароли/JWT/body
запроса не записываются. Подтверждение: `core-api/tests/`,
`core-api/app/main.py`, запуск `python -m pytest -q`.

## 4/2. JWT

Пароли хешируются Argon2. Access JWT передаётся как `Authorization: Bearer`;
refresh JWT ротируется, logout отзывает сессии. E-mail должен быть
подтверждён до получения рабочей сессии. Подробности — `core-api/docs/api.md`.

## 4/3. Swagger

Swagger доступен по `/docs`, OpenAPI JSON — `/openapi.json`, статическая
версия — [`api/openapi.yaml`](../../api/openapi.yaml). Для закрытых методов в
Swagger сначала выполняется login, затем access token вводится через Authorize.

## 4/4. Сетевое взаимодействие

Web-клиент обращается к FastAPI по HTTP/JSON; origin Vite разрешается в
`CORS_ORIGINS`. Для демонстрации на другой машине требуется внешний HTTPS URL
API и обновление `VITE_API_BASE_URL`. Локальная инструкция находится в
[`docs/deployment.md`](../deployment.md).
