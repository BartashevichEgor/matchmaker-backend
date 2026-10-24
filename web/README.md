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
- Регистрация, подтверждение e-mail, JWT-вход и восстановление сессии через FastAPI.
- Inline-валидация форм: красная обводка и небольшая подпись под ошибочным полем; неверные credentials показываются безопасным общим сообщением.
- Защищённый layout с collapsible sidebar на desktop, нижней мобильной навигацией и выходом на `/login`.

## Подключение к backend

1. Запустите API из репозитория backend на `http://127.0.0.1:8000`.
2. Скопируйте `.env.example` в `.env`. При необходимости укажите в `VITE_API_BASE_URL` адрес доступного API с суффиксом `/api/v1`.
3. Запустите `npm run dev`. Vite работает на `http://127.0.0.1:5173`, этот адрес уже разрешён CORS-настройкой backend.

После регистрации backend сохраняет письмо с шестизначным кодом в `core-api/.local/outbox/` при локальном режиме `MAIL_MODE=outbox`. Подтвердите код на странице `/verify-email`, затем выполните вход. В браузере сохраняются только JWT-токены; пароль в `localStorage` не записывается.

## Ручная проверка

- Проверены публичная страница, регистрация, вход, защищённая лента и выход с переходом на `/login`.
- Проверены desktop и узкие mobile viewport: sidebar раскрывается по hover, mobile bottom navigation открывает боковое меню, горизонтального overflow у страницы нет.
- Для форм и элементов навигации добавлены видимые `focus-visible` состояния.
