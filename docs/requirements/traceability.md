# Матрица трассируемости

| Требование | Jira/категория | Реализация | Проверка |
| --- | --- | --- | --- |
| US-01 Регистрация и вход | BE-004, FE-018 | `app/api/auth.py`, `web/src/features/auth` | `tests/test_auth.py`, `auth-pages.test.tsx` |
| US-02 Подтверждение e-mail | BE-005, FE-019 | `app/services/mail.py`, `VerifyEmailPage.tsx` | `test_auth.py`, `auth-pages.test.tsx` |
| US-03 Редактирование профиля | BE-010, FE-032 | `app/api/profiles.py`, `ProfilePage.tsx` | `test_matching.py`, `ProfilePage.test.tsx` |
| US-04 Каталог проектов | BE-006, FE-030 | `app/api/projects.py`, `CatalogPage.tsx` | `test_matching.py`, `profile-and-catalog-pages.test.tsx` |
| US-05 Свайп и мэтч | BE-007 | `app/api/swipes.py` | `test_matching.py` |
| US-06 Групповой чат | BE-009, FE-031 | Phase 4 plan; implementation not started after cleanup | Phase 4 backend/web tests |
| NFR-01 Безопасность JWT | BE-004 | `app/core/security.py` | `test_auth.py` |
| NFR-02 Проверяемость | TE-005 | CI, pytest, Vitest | workflow и команды README |
| NFR-03 Воспроизводимый запуск | EN-003 | `deploy/docker-compose.yml` | `/health`, compose config |

Строка считается закрытой только после подтверждённой ссылки на задачу, изменения кода и запуска соответствующей проверки.
