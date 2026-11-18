# Chat Service

WebSocket-сервис группового чата для Matchmaker. Клиент сначала отправляет
`authenticate` с access JWT и `match_id`; сервис проверяет членство через
`core-api` endpoint `/api/v1/matches/{id}/chat-access`. Только после ответа
`200` сокет добавляется в комнату матча.

## Локальный запуск

```powershell
cd chat-service
Copy-Item .env.example .env
npm install
npm start
```

Проверка: `http://127.0.0.1:8010/health`.

Подключение: `ws://127.0.0.1:8010/ws`. Первое сообщение:

```json
{"type":"authenticate","access_token":"<JWT>","match_id":1}
```

После события `{"type":"authenticated"...}` разрешено отправлять
`{"type":"message","text":"Привет"}`. Сообщение рассылается всем
активным сокетам комнаты. История сообщений намеренно не хранится в этом
учебном этапе; это задача следующей части чата.
