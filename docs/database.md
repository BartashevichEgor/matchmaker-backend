# База данных

Сервис работает с PostgreSQL в контейнерном и production-режимах и с SQLite для локального запуска и тестов. Доступ выполняется SQLAlchemy, а схема версионируется Alembic (`core-api/migrations`).

Основные таблицы: `users` и `profiles` — учётная запись и публичная анкета; `skills`, `roles`, `profile_skills` — справочники и навыки; `projects`, `project_skills`, `project_roles` — проекты и требования; `swipes`, `matches`, `project_members` — подбор и вступление в команду; `notifications` — приватные события мэтчей и вступления в проект; `email_codes`, `refresh_sessions` — подтверждение e-mail и сессии.

Ключевые ограничения: e-mail и username уникальны; уровень навыка и вес находятся в диапазоне 1–5; для пары проект–кандидат допускается единственный мэтч; внешние ключи каскадно удаляют зависимые записи там, где это безопасно. SQLite включает `foreign_keys=ON`.

Миграции выполняются командой `python -m alembic upgrade head`; проверка — `python -m alembic check`. Для новой миграции используйте `alembic revision --autogenerate -m "краткое-описание"`, затем обязательно прочитайте сгенерированный файл и запустите тесты.

Исходник диаграммы: [uml/schema.puml](uml/schema.puml).
