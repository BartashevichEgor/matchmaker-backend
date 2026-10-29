# PHASE-3-ADD-PROTECTED-PAGES

## Goal

Собрать защищённую пользовательскую часть приложения: общий layout, навигацию, заглушки страниц и поведение выхода.

## Scope

- Реализовать `AppLayout` только для защищённых страниц.
- Добавить сворачиваемый sidebar, активную навигацию и кнопку выхода.
- В свернутом состоянии показывать иконки, а при наведении мыши на desktop раскрывать названия разделов.
- На mobile показывать нижнюю навигацию с Menu, Feed, Profile, Matches и Projects; по Menu открывать полный sidebar.
- Создать единый компонент-заглушку для `/feed`, `/projects`, `/profile`, `/matches`.
- На странице `/chat/:matchId` отображать `matchId` вместе с общим шаблоном заглушки.
- Подключить выход через `await logout()` и редирект на `/login` с `replace`.

## Detailed Requirements

### 1. Layout shell

- `AppLayout` должен оборачивать только authenticated routes.
- Layout должен отсутствовать на `/`, `/login`, `/register` и `*`.
- Sidebar должен содержать бренд приложения, навигацию и кнопку выхода.
- Layout не должен быть привязан к данным домена, кроме auth state и nav state.

### 2. Navigation shell

- Sidebar должен плавно расширяться на desktop при наведении или фокусе.
- На узких экранах использовать нижнюю навигацию, а sidebar открывать поверх страницы через Menu; горизонтального overflow быть не должно.
- Active state должен подсвечивать текущий route.
- Поведение активного состояния должно работать и на `/chat/:matchId`.

### 3. Protected section placeholder

- Должен существовать один переиспользуемый компонент-заглушка.
- Он должен принимать title, description и статусный бейдж.
- На всех защищённых разделах нужно использовать один и тот же шаблон.
- Для `chat` шаблон должен дополнительно показывать `matchId`.

### 4. Logout flow

- Кнопка выхода должна вызывать `await logout()`.
- После успешного logout защищённый маршрут должен отправлять пользователя на `/login` с `replace`.
- Навигация после logout должна происходить только после завершения async операции.

## Implementation Steps

1. Создать `AppLayout` с sidebar, nav, outlet area и logout action.
2. Сверстать responsive sidebar с collapsed/expanded состояниями и mobile bottom navigation.
3. Реализовать `SectionPlaceholder` как единый шаблон для protected pages.
4. Подключить `/feed`, `/projects`, `/profile`, `/matches` к одному placeholder component.
5. Подключить `/chat/:matchId` к тому же шаблону с отображением matchId.
6. Добавить logout action, который завершает auth session и редиректит на `/login`.

## Deliverables

- Защищённый layout.
- Навигация по разделам.
- Все protected pages в виде заглушек.
- Выход из аккаунта с корректным редиректом.

## Exit Criteria

- Все protected routes рендерятся через общий layout.
- Активная навигация работает.
- Logout очищает сессию и возвращает на `/login`.
- Sidebar не ломает ширину страницы на мобильных устройствах.
