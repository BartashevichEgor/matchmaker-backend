# Контракт REST API Matchmaker

Префикс бизнес-методов — `/api/v1`. Полная исполняемая спецификация с полями, обязательностью, ограничениями и типами ответов: `/openapi.json`; интерактивная документация `/docs`.

API принимает JSON. Для защищённых методов передаётся `Authorization: Bearer <access_token>`. Идентификатор действующего пользователя берётся из токена. Ошибки: `{"detail":"описание"}`; ошибка валидации 422 — массив объектов loc/msg/type. Секретные входные значения не включаются в ошибки или журналы.

| Метод | Путь относительно /api/v1 | Доступ | Результат |
|---|---|---|---|
| POST | /auth/register | Гость | 201, сообщение; `mode` обязателен: `developer` или `project` |
| GET | /auth/session | Access JWT | Пользователь в полях React AuthService (`id`, `username`, `email`, `createdAt`) |
| POST | /auth/verify-email | Гость | 200; 400 при неверном/истёкшем коде |
| POST | /auth/resend-verification | Гость | Обобщённое сообщение без раскрытия существования аккаунта |
| POST | /auth/login, /auth/mobile/login | Гость | access и refresh tokens для мобильного/legacy транспорта |
| POST | /auth/web/login | Гость + Origin | access token + CSRF token; refresh token — HttpOnly cookie |
| POST | /auth/refresh, /auth/mobile/refresh | Refresh JWT | Новая пара токенов; старый refresh одноразовый |
| POST | /auth/web/refresh | Refresh cookie + Origin + `X-CSRF-Token` | Новый access token, CSRF token и rotated HttpOnly cookie |
| POST | /auth/logout, /auth/web/logout-all | Access JWT | Отзыв всех сессий текущего пользователя |
| POST | /auth/mobile/logout | Refresh JWT | Отзыв мобильной сессии |
| POST | /auth/web/logout | Refresh cookie + Origin + `X-CSRF-Token` | Отзыв web-сессии и очистка cookie |
| GET | /auth/sessions | Access JWT | Список сессий без refresh-токенов |
| DELETE | /auth/sessions/{session_id} | Access JWT | Отзыв одной своей сессии |
| POST | /auth/forgot-password | Гость | Запрос кода восстановления |
| POST | /auth/reset-password | Гость с кодом | Новый пароль и отзыв всех сессий |
| GET | /users/me | Access JWT | Приватные данные аккаунта без хеша |
| GET, PATCH | /profiles/me | Свой профиль | PATCH меняет только переданные поля |
| PUT | /profiles/me/skills | Подтверждённый пользователь | Полная замена списка навыков |
| GET | /profiles/{user_id} | Подтверждённый пользователь | Публичная анкета без email и даты рождения |
| GET | /skills, /roles | Все | Справочники; offset/limit |
| POST, PATCH | /admin/skills, /admin/skills/{id} | Администратор | Создание/редактирование навыков |
| POST, PATCH | /admin/roles, /admin/roles/{id} | Администратор | Создание/редактирование специализаций |
| GET, POST | /projects | Подтверждённый пользователь | Каталог либо создание, 201 |
| GET, PUT | /projects/{id} | Просмотр — пользователь; изменение — владелец | PUT полностью заменяет описание и требования |
| PATCH | /projects/{id}/status | Владелец | open/closed; заблокированный проект не открыть |
| PATCH | /admin/projects/{id}/status | Администратор | blocked/open |
| GET | /recommendations/projects | Подтверждённый пользователь | Ранжированный список проектов |
| GET | /projects/{id}/recommendations/candidates | Владелец | Ранжированные анкеты кандидатов |
| PUT | /projects/{id}/my-swipe | Соискатель | like/pass и match при наличии |
| PUT | /projects/{id}/candidates/{user_id}/swipe | Владелец | like/pass от имени проекта |
| GET | /matches | Участник совпадения | Доступные совпадения |
| GET | /matches/{id}/chat-access | Участник совпадения | Проверка доступа к room_key |
| POST | /matches/{id}/join | Кандидат | Вступление в команду после match |

`/ping` проверяет HTTP, `/health` — доступность БД, таблицы миграций и Redis при его настройке. 503 означает неготовность зависимости. Реальный WebSocket-чат относится к отдельному Phase 4-сервису и в текущий API не входит.

## Примеры

Регистрация:
```json
{"username":"Student Developer","email":"student@example.com","password":"ExamplePassword123!","mode":"developer"}
```
Логин:
```json
{"email":"student@example.com","password":"ExamplePassword123!"}
```
Подтверждение email:
```json
{"email":"student@example.com","code":"123456"}
```
Код выше — пример формата, не рабочий код. Действительный код приходит через настроенный транспорт.

Создание проекта:
```json
{"title":"Команда на хакатон","description":"Создаём сервис поиска студенческих команд.","skills":[{"skill_id":1,"weight":5}],"role_ids":[1]}
```
Список моих навыков:
```json
{"skills":[{"skill_id":1,"level":4},{"skill_id":3,"level":2}]}
```
Свайп:
```json
{"decision":"like"}
```

Списки проектов/рекомендаций/matches поддерживают offset=0, limit=20 (максимум 100). Каталоги — limit=50 (максимум 100). Фильтры проектов: skill_id, role_id, mine. Рекомендации: role_id. Сортировка рекомендаций по убыванию score, при равенстве — по ID. Уже оценённые объекты, собственные проекты и текущие членства исключаются.

## Авторизация и почта

`username` — обязательное публичное имя для каталога профилей: 1–50 символов после обрезки краевых пробелов, не может быть пустым и гарантированно уникально. `mode` — обязательный `developer` или `project`. Пароль: 8–128 символов. React проверяет повтор пароля до отправки регистрации; остальные клиенты могут передать необязательное поле `password_confirm` или `confirmPassword`, и сервер сверит его с паролем. Email нормализуется. Access JWT действует 15 минут, refresh — 7 дней; параметры конфигурируются. Данные JWT подписаны HS256, проверяются issuer/audience/type/exp/token_version/session. Web refresh хранится только в HttpOnly cookie и требует разрешённый Origin и совпадающий `X-CSRF-Token` с cookie `matchmaker_csrf`; web login и refresh возвращают этот токен в JSON. Мобильный transport получает refresh token в JSON. Logout и reset отзывают сессии. Код: 6 цифр, срок 10 минут, не более 5 неверных попыток. Verification link — opaque token, single-use, срок 24 часа; в письме он передаётся во fragment URL. Повторная отправка заменяет предыдущие verification credentials. SMTP-сбой даёт 503; уже созданный аккаунт можно подтвердить после повторного запроса.

Для действий авторизации установлены отдельные лимиты по email и IP. Redis обеспечивает общий лимит для нескольких процессов. Локальный режим без Redis предназначен для одного процесса. За reverse proxy доверяйте только IP своего proxy, иначе клиент может подделать адрес для лимитов.

## Интеграция чата

Backend Phase 3 предоставляет `GET /api/v1/matches/{id}/chat-access` для
проверки участника мэтча и выдачи `room_key`. Полный отдельный сервис чата,
хранение сообщений, REST/WebSocket-протокол и повторная авторизация относятся
к Backend Phase 4 и в текущем backend baseline не реализованы.

## Алгоритм подбора

Ось вектора — ID из общего справочника навыков. У пользователя значение равно level, у проекта — weight; отсутствие навыка равно 0. Score = dot(user, project) / (norm(user) * norm(project)). При пустом векторе score=0. Ответ содержит score в диапазоне 0..1 и matched_skill_ids. Это сходство направлений векторов, а не процент гарантированного соответствия квалификации. Версия MVP считает кандидатов в Python после выборки из реляционной БД; для больших каталогов потребуется пакетная загрузка/SQL-агрегация и нагрузочное тестирование.
