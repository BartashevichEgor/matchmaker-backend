# Отчёт 5/5 — структура репозитория и документация проекта

Дата среза: 26.11.2026. Проект: **Matchmaker** — платформа поиска команд для
проектов и хакатонов.

## Документация как код

| Требование | Артефакт | Проверка |
| --- | --- | --- |
| Общая навигация | [`docs/README.md`](../README.md) | относительные ссылки открываются в GitHub |
| Участие в разработке | [`CONTRIBUTING.md`](../../CONTRIBUTING.md) | есть ветки, PR, DoD и review |
| Контракт API | [`api/openapi.yaml`](../../api/openapi.yaml) | сравнивается с `/openapi.json` FastAPI |
| Архитектурные решения | [`docs/adr/`](../adr/) | ADR-0001, ADR-0002 |
| C4 | [`docs/c4/`](../c4/) | исходники PlantUML и SVG-представления |
| Данные | [`docs/database.md`](../database.md), [`docs/uml/schema.puml`](../uml/schema.puml) | PostgreSQL-схема и ERD |
| Развёртывание | [`docs/deployment.md`](../deployment.md), [`deploy/`](../../deploy/) | Docker Compose, `.env.example`, health-check |
| Релизы | [`docs/release-plan.md`](../release-plan.md), [`CHANGELOG.md`](../../CHANGELOG.md) | этапы и факт изменений |

## Состав и ответственность команды

| Участник | Роль | Подтверждённый вклад |
| --- | --- | --- |
| Егор Барташевич | Lead Backend / DevOps | FastAPI, PostgreSQL/миграции, JWT, OpenAPI, deploy, health, тесты и документация. Commits `0db7533`, `e89bbda`, `fd478dd`, `0d8ffb7` и др. |
| Роман Онисимов (`onissya`) | Web Frontend | React layout/auth/profile/catalog, responsive UI, планы реализации. Commits `d6cf2c7`, `0d8b9aa`, `c667288`, `30a286d`, `32c20f5`, `7a02a78`, `3bc1db6`, `98e4454`. |
| Алина Цыбулькина | iOS/KMP / QA | KMP экраны, auth-модели и тесты; позднее — frontend API/profile/catalog. Commit `8ce515f`, merge `62ea…`; в отдельном frontend-репозитории — `93fddd9` и последующие. |
| Вероника Соболь | UI/UX / Technical Writer | Макеты и UI-требования в Figma/Drive. Прямой Git-коммит под этим именем не найден, поэтому код ей не приписывается. |

В истории есть merge PR от Романа (`c50735c`) и merge изменений Алины
(`62ea…`). Для каждого следующего PR применяется правило из CONTRIBUTING:
автор описывает ручную проверку, минимум один reviewer проверяет контракт и
Definition of Done до merge.

## Структура репозитория

```
matchmaker-backend-new/
├── core-api/        FastAPI, SQLAlchemy, Alembic, pytest, OpenAPI runtime
├── frontend/web/    React + TypeScript web-клиент и тесты
├── chat-service/    Node.js WebSocket group-chat MVP и протокольные тесты
├── api/             статическая OpenAPI-спецификация
├── deploy/          Compose и пример окружения
├── docs/            архитектура, БД, C4, ADR, планы, отчёты
└── start-demo.ps1   локальный запуск демонстрации
```

## Как воспроизвести проверку

```powershell
cd core-api; python -m pytest -q
cd ../frontend/web; npm test; npm run build
cd ../../chat-service; npm test
```

Запуск и сетевые переменные описаны в [`docs/deployment.md`](../deployment.md).
Документ не утверждает, что функции без endpoint/теста готовы: file-avatar,
личные сообщения и постоянная история чата остаются в Product Backlog.

## Текст для Moodle

> Групповой отчёт 5/5: документация проекта хранится в репозитории в формате
> Docs as Code. Она включает README, CONTRIBUTING, OpenAPI, ADR, C4, схему БД,
> развёртывание, план релизов и CHANGELOG. Ссылки приведены в данном документе.
> Вклад участников подтверждён историей Git; пункты, не реализованные в коде,
> не отмечены как выполненные.
