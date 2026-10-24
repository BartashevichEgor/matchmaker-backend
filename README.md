# Matchmaker Frontend

React-клиент учебного проекта **Matchmaker** — сервиса поиска людей для команды, идеи, проекта или хакатона.

## Стек

React 18, TypeScript, Vite, React Router, Zod, Vitest и React Testing Library. Адаптивная верстка реализована средствами CSS/Flexbox.

## Готовые пользовательские экраны

- вход;
- регистрация;
- подтверждение e-mail;
- ошибки e-mail, пароля, имени пользователя и сети;
- защищённые заготовки ленты, проектов, профиля, совпадений и чата.

Прототип: [Figma — Project Matchmaker](https://www.figma.com/design/PQ2HmEr99bpWbDCxgcnMbe/Project-Matchmaker?node-id=0-1).

## Подключение API

Контракт backend: [api.md](https://github.com/BartashevichEgor/matchmaker-backend/blob/main/core-api/docs/api.md). Интерактивная документация доступна у запущенного backend на `http://127.0.0.1:8000/docs`.

```bash
cd web
copy .env.example .env
npm install
npm run dev
```

По умолчанию `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`. Для доступа к серверу на другом компьютере укажите в `.env` опубликованный HTTPS-адрес API с суффиксом `/api/v1`, затем перезапустите Vite.

Подробности запуска и проверки находятся в [web/README.md](web/README.md).
