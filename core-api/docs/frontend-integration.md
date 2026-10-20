# Контракт React ↔ FastAPI

Этот документ связывает актуальный React-проект из `matchmaker-frontend/web` с backend Matchmaker.

> React-проект пока использует `mockAuthService` и `localStorage`, поэтому эти запросы не выполняются автоматически. Backend уже подготовлен для замены mock-сервиса на HTTP-сервис без изменения дизайна форм.

## Адреса разработки

- React/Vite: `http://127.0.0.1:5173`
- FastAPI: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Базовый API-путь: `http://127.0.0.1:8000/api/v1`

CORS для `localhost:5173` и `127.0.0.1:5173` включён в backend.

## Сценарий входа

### 1. Регистрация

`POST /api/v1/auth/register`

```json
{
  "username": "Егор Попкорн",
  "email": "egor@example.com",
  "password": "password123"
}
```

React уже сравнивает пароль и `confirmPassword` в форме, а перед вызовом `AuthService` удаляет `confirmPassword`, поэтому backend принимает именно этот payload. Для других клиентов `password_confirm` или `confirmPassword` остаются необязательными полями дополнительной проверки. Успешный ответ `201` означает, что создан аккаунт и отправлен код; пользователь ещё не авторизован.

### 2. Подтверждение e-mail

`POST /api/v1/auth/verify-email`

```json
{
  "email": "egor@example.com",
  "code": "123456"
}
```

В локальном режиме письмо сохраняется в `core-api/.local/outbox`. Для React нужен отдельный экран ввода кода после регистрации.

### 3. Вход и JWT

`POST /api/v1/auth/login`

```json
{
  "email": "egor@example.com",
  "password": "password123"
}
```

Ответ содержит `access_token`, `refresh_token`, `token_type` и `expires_in`. `access_token` передаётся в каждом закрытом запросе:

```http
Authorization: Bearer <access_token>
```

### 4. Восстановление сессии для AuthProvider

`GET /api/v1/auth/session`

```json
{
  "id": "42",
  "username": "egor.dev",
  "email": "egor@example.com",
  "createdAt": "2026-10-20T10:00:00Z"
}
```

Поля специально соответствуют TypeScript-модели `User` во frontend: строковый `id` и camelCase `createdAt`.

### 5. Выход

`POST /api/v1/auth/logout` с access JWT. Сервер отзывает все refresh-сессии пользователя. Затем React удаляет токены из browser storage и очищает пользователя в `AuthProvider`.

## Единые правила валидации

| Поле | Правило |
|---|---|
| username | 1–50 символов после обрезки краевых пробелов; имя не может быть пустым |
| e-mail | корректный адрес; пробелы и регистр нормализуются |
| password | 8–128 символов |
| confirmPassword | проверяется в React-форме до отправки запроса |
| code | ровно 6 цифр |

## Что нужно заменить в React

1. Создать `api-auth-service.ts`, реализующий текущий интерфейс `AuthService` через `fetch`.
2. После регистрации открыть страницу подтверждения e-mail, а не создавать локальную сессию и не переходить сразу на `/feed`.
3. После `verify-email` выполнить login, сохранить JWT и получить пользователя через `/auth/session`.
4. На `401` выполнить refresh один раз; при неудаче удалить токены и перейти на `/login`.
5. Убрать `mock-auth-service.ts` из production-провайдера. Его можно оставить только для unit-тестов.

## Соответствие ошибок UI

| HTTP | Причина | Что показать в интерфейсе |
|---|---|---|
| 422 | поле не прошло серверную валидацию | ошибку под соответствующим полем |
| 409 | e-mail или username занят | ошибку у e-mail или username |
| 400 | неверный или просроченный код | ошибку на экране подтверждения |
| 401 | неверные учётные данные / токен | «Неверный e-mail или пароль» либо повторный login |
| 403 | e-mail ещё не подтверждён | перейти к экрану подтверждения e-mail |
| 429 | слишком много попыток | сообщение и задержку повторной попытки |
| 5xx / сеть | сервер недоступен | состояние Offline из Figma |
