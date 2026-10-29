# PHASE-1-ADD-ROUTING

## Goal

Поднять основу приложения на Vite и собрать маршрутизацию, которая отделяет публичные страницы от защищённой зоны, не привязываясь пока к конкретной auth-реализации.

## Scope

- Создать Vite-проект в `matchmaker-frontend/web` с React + TypeScript.
- Подключить `@vitejs/plugin-react`.
- Настроить npm-скрипты для `dev`, `build`, `preview`, `test`, `test:watch`, `coverage`.
- Подключить React Router и подготовить базовую структуру `App`, `router`, `routes`.
- Подготовить публичные маршруты `/`, `/login`, `/register`, `*`.
- Подготовить защищённые маршруты `/feed`, `/projects`, `/profile`, `/matches`, `/chat/:matchId`.
- Зафиксировать, что стартовая страница, вход, регистрация и 404 не используют `AppLayout`.

## Detailed Requirements

### 1. Project bootstrap

- Сгенерировать Vite-проект в `matchmaker-frontend/web`.
- Выбрать React + TypeScript шаблон.
- Проверить, что базовая сборка и dev server запускаются через npm.
- Убедиться, что структура проекта готова к дальнейшему добавлению feature folders.

### 2. Tooling and test foundation

- Подключить `@vitejs/plugin-react`.
- Подготовить `Zod`, `vitest` и `jsdom` для дальнейших тестов.
- Заложить конфигурацию под React Testing Library и `user-event`.
- Добавить `jest-dom` в тестовую среду.
- Настроить scripts для сборки, запуска и тестов.

### 3. Route map and application shell

- Создать route map, в котором публичные страницы отделены от защищённых.
- Публичный shell должен содержать `/`, `/login`, `/register`, `*`.
- Protected shell должен содержать `/feed`, `/projects`, `/profile`, `/matches`, `/chat/:matchId`.
- Пока auth-слой не подключён, маршруты защищённой зоны должны существовать как каркас без навигационных side effects.

### 4. Page skeletons

- Создать отдельные page entry points для всех публичных маршрутов.
- Создать route entry points для всех protected маршрутов.
- Подготовить единый fallback 404 page.
- Зафиксировать, что публичные страницы не используют общий layout для защищённой зоны.

### 5. Folder structure

- Организовать папки так, чтобы отдельно жили `app`, `pages`, `routes`, `shared`, `features` и `test`.
- Не смешивать layout-слой и page-level компоненты на этом этапе.
- Оставить структуру готовой для подключения auth и protected UI в следующих фазах.

## Deliverables

- Рабочий Vite-проект.
- Базовая конфигурация React Router.
- Черновая структура маршрутов и страниц.
- Настроенные инструменты тестирования.

## Exit Criteria

- Приложение запускается локально.
- Публичные и защищённые маршруты определены.
- Публичные страницы не зависят от защищённого layout.
- Базовая инфраструктура готова к следующей фазе auth.