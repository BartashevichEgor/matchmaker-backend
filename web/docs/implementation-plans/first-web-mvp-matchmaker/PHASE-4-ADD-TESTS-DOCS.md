# PHASE-4-ADD-TESTS-DOCS

## Goal

Закрыть MVP тестами, проверить крайние случаи auth/storage и оформить запуск проекта в README.

## Scope

- Написать тесты для всех публичных, защищённых и неизвестных маршрутов.
- Проверить отсутствие `AppLayout` на `/`, `/login`, `/register` и 404.
- Проверить deep-link гостя `/chat/abc?tab=info#messages` и возврат после входа.
- Проверить клиентскую и сервисную валидацию.
- Проверить автоматический вход после регистрации.
- Проверить дубликаты email в разном регистре.
- Проверить успешный и ошибочный логин.
- Проверить выход, удаление сессии, переход на `/login` и повторную защиту маршрутов.
- Проверить восстановление сессии новым монтированием `AuthProvider`.
- Проверить повреждённые данные storage, неизвестный `userId` и ошибку недоступного storage.
- Обновить README с командами запуска, тестирования и ограничением про открытое хранение паролей в mock-MVP.
- Задокументировать технические долги в TECHNICAL-DEBT.md (vi.mock coupling, интерфейс AuthService, dependency injection для тестов).

## Detailed Requirements

### 1. Tooling and test foundation

- Использовать Vitest как основной test runner.
- Использовать jsdom как DOM environment.
- Использовать React Testing Library для render/assert flow.
- Использовать `user-event` для пользовательских сценариев.
- Использовать `jest-dom` для декларативных DOM assertions.
- Перед каждым тестом очищать `localStorage`.

### 2. Route coverage

- Покрыть публичные маршруты.
- Покрыть защищённые маршруты.
- Покрыть неизвестный маршрут и публичный 404.
- Проверить, что публичные маршруты не рендерят `AppLayout`.

### 3. Auth flow coverage

- Проверить регистрацию как вход в систему без дополнительного логина.
- Проверить успешный и неуспешный login.
- Проверить duplicate email с разным регистром.
- Проверить logout и удаление session state.
- Проверить возврат после login на сохранённый внутренний URL.

### 4. Storage and session edge cases

- Проверить повреждённый JSON в storage.
- Проверить session с неизвестным `userId`.
- Проверить storage unavailable error path.
- Проверить асинхронное восстановление сессии через fresh mount.

### 5. Documentation and manual checks

- Обновить README с командами запуска и тестирования.
- Обозначить ограничение открытого хранения паролей для mock-MVP.
- Зафиксировать ручную проверку desktop/mobile, focus states и отсутствие горизонтального overflow.

## Implementation Steps

1. Создать route tests для public/private/404 paths.
2. Создать form tests для register/login validation and submission states.
3. Создать service tests для auth service and storage behavior.
4. Создать provider tests для session restore and redirect state.
5. Создать logout and deep-link redirect tests.
6. Проверить edge cases corrupted storage and unknown userId.
7. Обновить README and manual QA notes.

## Deliverables

- Набор unit/integration тестов.
- Покрытие маршрутов и auth-flow.
- Обновлённая документация в README.

## Exit Criteria

- Основные сценарии MVP покрыты тестами.
- Edge cases storage/auth проверены.
- README даёт понятную инструкцию по запуску и ограничениям mock-MVP.
