# Backend Phase 4 — Separate chat service implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a separate Node.js chat service with persisted conversations, unread state and authenticated REST/WebSocket messaging for matched users.

**Architecture:** FastAPI remains the identity and authorization authority. Node owns chat persistence and sockets, but calls FastAPI `ChatAccessRead` before every read/write-sensitive operation. Node does not share `JWT_SECRET` and cannot authorize from client-supplied match data alone.

**Tech Stack:** Node.js LTS, TypeScript, Fastify, ws, PostgreSQL, pg, Zod, Vitest, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-11-14-matchmaker-mvp.md`

## Global Constraints

- Service code lives under `backend/chat-service`; it is not frontend code.
- WebSocket authentication is the first JSON message, never a query parameter.
- FastAPI authorization endpoint: `GET /api/v1/matches/{match_id}/chat-access`.
- Chat database is separate from FastAPI tables; migrations are restart-safe.
- Messages are bounded to 4000 characters and deduplicated by `(sender_user_id, client_message_id)`.
- Unread count excludes the current user’s own messages and uses a per-user conversation read cursor.

## Review Focus

- Nonparticipants cannot read, send or join even if they guess IDs.
- Access is rechecked on reconnect and every send.
- SQL migrations are applied exactly once across restarts.
- Duplicate client retries do not duplicate messages.
- Tokens never appear in URLs, logs or persisted chat data.

---

### Task 1: Scaffold service and Compose deployment

**Files:**
- Create: `backend/chat-service/package.json`
- Create: `backend/chat-service/tsconfig.json`
- Create: `backend/chat-service/Dockerfile`
- Create: `backend/chat-service/src/config.ts`
- Create: `backend/chat-service/src/server.ts`
- Create: `backend/chat-service/src/bootstrap.ts`
- Create: `backend/chat-service/src/backend-client.ts`
- Modify: `backend/docker-compose.yml`
- Modify: `backend/.env.example`
- Test: `backend/chat-service/tests/health.test.ts`

**Interfaces:**
- Consumes: FastAPI `ChatAccessRead` contract and `CHAT_DATABASE_URL`/`MATCHMAKER_API_URL`.
- Produces: Fastify `/health`, `backend-client.getChatAccess(matchId,userAccessToken)`, Docker `chat-db` and `chat` services.

- [ ] Step 1: Add a failing health test for service and dependency status.
- [ ] Step 2: Parse `CHAT_PORT`, `CHAT_DATABASE_URL`, `MATCHMAKER_API_URL` and `CHAT_INTERNAL_TIMEOUT_MS` strictly.
- [ ] Step 3: Implement Fastify startup/shutdown and `bootstrap.ts` migration-before-listen behavior.
- [ ] Step 4: Use `Dockerfile CMD ["node", "dist/bootstrap.js"]`.
- [ ] Step 5: Add `chat-db` PostgreSQL 16 with `chat_data` volume/healthcheck and `chat` with healthcheck `/health`, depending on `api` and `chat-db`.
- [ ] Step 6: Run npm test/typecheck and commit `feat: scaffold chat service`.

### Task 2: Add restart-safe persistence and unread state

**Files:**
- Create: `backend/chat-service/src/db.ts`
- Create: `backend/chat-service/src/migrator.ts`
- Create: `backend/chat-service/src/migrations/001_chat_schema.sql`
- Create: `backend/chat-service/src/conversations.ts`
- Create: `backend/chat-service/src/messages.ts`
- Create: `backend/chat-service/src/read-state.ts`
- Test: `backend/chat-service/tests/migrations.test.ts`
- Test: `backend/chat-service/tests/messages.test.ts`
- Test: `backend/chat-service/tests/read-state.test.ts`

**Interfaces:**
- Consumes: Task 1 config and database pool.
- Produces: `conversation`, `message`, `conversation_read_state` and `schema_migrations` tables; idempotent repositories.

- [ ] Step 1: Add failing tests for migration restart, conversation idempotency, sender ownership and duplicate client message IDs.
- [ ] Step 2: Create transactional `schema_migrations` application with a unique version key and startup lock.
- [ ] Step 3: Implement `getOrCreateConversation(matchId)`.
- [ ] Step 4: Implement `insertMessage` with body limit 4000 and duplicate acknowledgement.
- [ ] Step 5: Implement cursor pagination ordered by `(created_at,id)`.
- [ ] Step 6: Implement read state `(conversation_id,user_id,last_read_message_id,last_read_at)`.
- [ ] Step 7: Count unread messages where sender differs from current user and message cursor is after the user cursor; missing state means all other-user messages are unread.
- [ ] Step 8: Advance read cursor transactionally to the latest message visible at transaction start; later committed messages remain unread.
- [ ] Step 9: Run restart and concurrent send/read tests and commit `feat: persist chat and unread state`.

### Task 3: Implement REST authorization and messages

**Files:**
- Create: `backend/chat-service/src/routes/conversations.ts`
- Modify: `backend/chat-service/src/server.ts`
- Test: `backend/chat-service/tests/routes.test.ts`

**Interfaces:**
- Consumes: Tasks 1–2 and FastAPI `ChatAccessRead`.
- Produces: `GET /chat/conversations`, `GET /chat/conversations/{conversation_id}/messages`, `POST /chat/conversations/{conversation_id}/messages`, `POST /chat/conversations/{conversation_id}/read`.

- [ ] Step 1: Add failing tests for missing bearer, invalid access, pagination, message creation and mark-read.
- [ ] Step 2: Require `Authorization: Bearer <access>` on every route and never log the token.
- [ ] Step 3: Resolve conversation to match ID and call FastAPI before every read/write.
- [ ] Step 4: Return `401` invalid token, `403` valid outsider, `404` unknown conversation and `422` invalid message body.
- [ ] Step 5: Return cursor `next_cursor` and per-user `unread_count` in conversation summaries.
- [ ] Step 6: Make mark-read return the updated unread count.
- [ ] Step 7: Run route tests and commit `feat: expose authorized chat REST API`.

### Task 4: Implement authenticated WebSocket protocol

**Files:**
- Create: `backend/chat-service/src/ws.ts`
- Modify: `backend/chat-service/src/server.ts`
- Test: `backend/chat-service/tests/ws.test.ts`

**Interfaces:**
- Consumes: Tasks 1–3 and `ChatAccessRead`.
- Produces: `WS /chat/ws`.

Client authentication:

```json
{"type":"authenticate","access_token":"...","match_id":42}
```

Client send/read events:

```json
{"type":"send","client_message_id":"c-123","body":"Hello"}
{"type":"read","last_read_message_id":123}
```

Server events:

```json
{"type":"authenticated","conversation_id":"match:42"}
{"type":"message","message":{}}
{"type":"message_ack","client_message_id":"c-123","duplicate":false,"message":{}}
{"type":"error","code":"forbidden|unauthorized|invalid_message"}
```

- [ ] Step 1: Add tests for timeout without authentication, invalid match, successful join, reconnect and send-after-expiry.
- [ ] Step 2: Reject unauthenticated sockets after the bounded handshake timeout.
- [ ] Step 3: Call FastAPI on authentication, reconnect and every send.
- [ ] Step 4: Persist before broadcast and use `client_message_id` for retry idempotency.
- [ ] Step 5: Handle read events through the read-state repository and broadcast only within the conversation.
- [ ] Step 6: Close unauthorized sockets without exposing backend details.
- [ ] Step 7: Run WebSocket tests and commit `feat: add authorized chat websocket`.

### Task 5: Verify and hand off chat protocol

**Files:**
- Modify: `backend/core-api/docs/api.md`
- Modify: `backend/core-api/docs/deployment.md`
- Test: `backend/chat-service/tests/health.test.ts`
- Test: `backend/chat-service/tests/routes.test.ts`
- Test: `backend/chat-service/tests/ws.test.ts`

**Interfaces:**
- Consumes: Tasks 1–4 and Backend Phase 3 ChatAccessRead.
- Produces: stable REST/WebSocket contract for Web/iOS Phase 4.

- [ ] Step 1: Run Node tests/typecheck and backend authorization tests.
- [ ] Step 2: Run Compose health checks for API, chat-db and chat.
- [ ] Step 3: Verify a matched candidate and project owner can exchange messages; an outsider cannot.
- [ ] Step 4: Verify reconnect/send authorization and duplicate retry behavior.
- [ ] Step 5: Document environment variables, protocol payloads and service startup order.
- [ ] Step 6: Send the protocol and test output to Web/iOS owners and commit `docs: hand off chat protocol`.

## Exit Criteria

- Matched users can list conversations, load history, send and receive messages.
- Unread counts and mark-read are correct per user.
- Nonparticipants cannot use REST or WebSocket chat.
- Service restarts do not re-run successful migrations or lose schema state.

## Handoff

Web/iOS consume the exact REST paths and WebSocket payloads. Phase 5 consumes the Compose health checks and deployment variables.

## Rollback

Stop/remove only the chat service integration and isolated chat database if needed; do not modify FastAPI match rows or delete project/user data.
