# PHASE-2-ADD-AUTH-SERVICE

## Goal

Реализовать локальную mock-авторизацию как отдельный контракт, который потом можно заменить FastAPI-версией без изменений UI и роутинга.

## Scope

- Определить публичные модели `User`, `CredentialsInput`, `RegisterFormInput`.
- Вынести общую Zod-валидацию email и пароля в переиспользуемую схему.
- Реализовать форму регистрации с `confirmPassword` и дополнительной проверкой совпадения паролей.
- Определить `AuthService` с методами `register`, `login`, `logout`, `getCurrentUser`.
- Реализовать `mockAuthService` как единственное место доступа к `localStorage`.
- Добавить версионированные ключи для пользователей и сессии.
- Нормализовать email через `trim().toLowerCase()` до проверок, сравнений и сохранения.
- Обрабатывать повреждённые данные storage и неизвестный `userId` как гостевую сессию.
- Добавить `AuthProvider` с состояниями `user` и `isInitialized`.
- Подключить логику возврата после логина на валидный внутренний URL.

## Detailed Requirements

### 1. Domain model and validation

- `User` должен быть публичной моделью без пароля.
- `CredentialsInput` должен содержать email и пароль как входной контракт, а нормализация должна выполняться внутри сервиса до проверок и сохранения.
- `RegisterFormInput` должен существовать только для UI-формы и включать `confirmPassword`.
- Базовая Zod-схема должна проверять email и пароль минимум 8 символов.

### 2. Service contract and error semantics

- `AuthService.register(input): Promise<User>` должен создавать пользователя и сессию.
- `AuthService.login(input): Promise<User>` должен проверять учётные данные.
- `AuthService.logout(): Promise<void>` должен удалять только session state.
- `AuthService.getCurrentUser(): Promise<User | null>` должен восстанавливать активную сессию или возвращать `null`.
- Ошибки должны быть типизированы и различать duplicate email, invalid credentials, storage unavailable.
- После успешного `register` пользователь должен получать активную сессию и редирект на `/feed`.

### 3. Storage implementation

- `mockAuthService` должен быть единственным местом доступа к `localStorage`.
- Нельзя использовать модульный кэш для users/session.
- Должны быть отдельные versioned keys для users и session.
- Session storage должен хранить только `userId`.
- При чтении storage повреждённый JSON должен очищаться и трактоваться как гостевая ситуация.
- Если session указывает на несуществующий `userId`, session должна очищаться.

### 4. Email normalization and duplication rules

- Email должен нормализоваться до всех сравнений и сохранения.
- Нормализация должна происходить в service layer, а не только в форме.
- Дубликаты email должны сравниваться после normalizing.
- Форма и сервис должны разделять общую схему и UI-расширение с confirmPassword.

### 5. Provider and redirect flow

- `AuthProvider` должен восстанавливать сессию асинхронно.
- Provider должен хранить `user`, `isInitialized` и auth actions.
- Provider не должен выполнять навигацию внутри себя.
- Если storage недоступен, provider должен завершить инициализацию и отдать UI ошибку через state.
- `ProtectedRoute` не должен редиректить до завершения инициализации.
- После инициализации гость должен отправляться на `/login`.
- В `router state` нужно сохранять `pathname`, `search` и `hash`.
- После входа возврат разрешён только на внутренний путь, начинающийся с `/`.
- Авторизованный пользователь на `/login` и `/register` должен уходить на `/feed`.

## Deliverables

- Рабочий mock-auth слой.
- Провайдер auth для приложения.
- Формы входа и регистрации с валидацией и ошибками.
- Чёткий контракт для будущей серверной замены.

## Exit Criteria

- Регистрация и логин работают локально.
- Сессия сохраняется и восстанавливается.
- Редиректы соответствуют контракту.
- Ошибки auth и storage различимы и пригодны для UI.