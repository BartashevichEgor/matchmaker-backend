# Technical Debt & Known Limitations

Этот файл документирует известные технические ограничения, долги и будущие refactoring'и в проекте.

## Тесты

### vi.mock для мокания auth service

**Статус:** Known limitation

**Проблема:**
В тестах `AppLayout.test.tsx` используется `vi.mock('../../shared/lib/auth/mock-auth-service', ...)` для мокания auth service. Это работает для MVP, когда mockAuthService является реальным сервисом, но создаёт coupling между тестами и реализацией.

**Почему это проблема:**
- `vi.mock` заменяет модуль на уровне загрузчика, что делает тесты зависимыми от структуры импортов
- Когда будет подключен реальный API (backend + database), mockAuthService будет заменён на реальный сервис, и тесты перестанут работать без модификаций
- Отсутствует dependency injection, который позволил бы подставлять мок-реализацию без модификации модулей

**План рефакторинга:**
1. Создать интерфейс `AuthService` с методами: `getCurrentUser()`, `login()`, `register()`, `logout()`
2. Реализовать `MockAuthService` для тестов и `RealAuthService` для production
3. В `AuthProvider` инжектировать сервис через пропсы или контекст (ability to override in tests)
4. В тестах использовать мок-реализацию через dependency injection вместо `vi.mock`
5. Убрать `vi.mock` из тестовых файлов

**Когда делать:**
Перед подключением реального API/бэкенда.

---

## Auth

### Пароли в открытом виде

**Статус:** MVP limitation (документировано в README)

**Проблема:**
В mock-MVP пароли хранятся в открытом виде в localStorage.

**План:**
Когда подключим реальный бэкенд, пароли будут хешироваться на сервере. В MVP это ограничение задокументировано.

---

## Navigation

### Chat link removed from navigation

**Статус:** Intentional (не технический долг)

**Причина:**
В навигации отсутствует ссылка на чат, так как для неё требуется реальный `matchId`. Когда будет реализован чат, ссылку нужно будет добавить обратно.

---

## Storage

### localStorage keys hardcoding

**Статус:** MVP acceptable

**Проблема:**
Используется хардкод ключей вроде `'matchmaker:v1:users'` и `'matchmaker:v1:session'`.

**Почему это не критично:**
Это intentional versioning strategy. При изменении структуры данных version можно будет инкрементировать.

**План рефакторинга (опционально):**
Вынести ключи в константы в отдельном модуле для централизованного управления.

---

## Layout

### AppLayout sidebar hardcodes brand link to /feed

**Статус:** Minor inconsistency

**Проблема:**
Бренд в sidebar ведёт на `/feed`, но это не конфигурируется.

**План:**
Можно сделать конфигурируемым через пропсы или константы, если понадобится изменить.

---

## Redirect

### Hardcoded origin in redirect validation (FIXED)

**Статус:** Fixed in refactor commit

**Что было:**
В `resolve-redirect-target.ts` использовался хардкод origin `'https://matchmaker.local'`.

**Что исправлено:**
Теперь используется `window.location.origin` для текущего origin.

**Урок:**
Избегать хардкода URL и origin в коде. Использовать runtime-значения или environment variables.
