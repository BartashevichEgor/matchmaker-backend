# Matchmaker Web

Фронтенд MVP Matchmaker на React + TypeScript + Vite.

## Запуск

Требуется Node.js 20 или новее.

```bash
npm install
npm run dev
```

## Сборка и тесты

```bash
npm run build
npm run test
npm run test:watch
npm run coverage
```

## Что уже есть

- Vite-проект с React Router, Vitest и React Testing Library.
- Публичные страницы `/`, `/login`, `/register`.
- Двухпанельные страницы входа и регистрации: презентационная панель слева и форма справа в пропорции 50/50 на desktop; на mobile остаётся только форма.
- Защищённые маршруты-заглушки `/feed`, `/projects`, `/profile`, `/matches`, `/chat/:matchId`.
- Публичный `404`.
- Локальная mock-авторизация с восстановлением сессии, валидацией и обработкой повреждённого storage.
- Inline-валидация форм: красная обводка и небольшая подпись под ошибочным полем; неверные credentials показываются безопасным общим сообщением.
- Защищённый layout с collapsible sidebar на desktop, нижней мобильной навигацией и выходом на `/login`.

## Ограничения MVP

- Пароли хранятся в открытом виде в `localStorage`. Это допустимо только для локального mock-MVP и не должно использоваться в production.
- Реальные API, FastAPI/JWT, подтверждение email и доменная логика разделов будут добавлены позднее.

## Ручная проверка

- Проверены публичная страница, регистрация, вход, защищённая лента и выход с переходом на `/login`.
- Проверены desktop и узкие mobile viewport: sidebar раскрывается по hover, mobile bottom navigation открывает боковое меню, горизонтального overflow у страницы нет.
- Для форм и элементов навигации добавлены видимые `focus-visible` состояния.
