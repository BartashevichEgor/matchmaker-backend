# Backend Phase 3 — Person/project matching and notifications implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an idempotent, concurrency-safe developer↔project matching flow with private in-app notifications.

**Architecture:** The existing directional Swipe model remains the source of decisions. A Match always contains one `project_id` and one `candidate_user_id`; the candidate must have a published developer profile, and the project must be open/published. Mutual likes create one immutable match and notifications atomically.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis, pytest.

**Spec:** `docs/superpowers/specs/2026-11-14-matchmaker-mvp.md`

## Global Constraints

- Valid match shape is only `developer ↔ project`.
- Developer↔developer and project↔project matches are rejected at API and database boundaries.
- Repeated like/pass requests are idempotent; no undo/unmatch in MVP.
- Blocked/closed/unpublished projects cannot receive new likes.
- Matches are private to the candidate and project owner.
- Notifications are in-app only; `project_joined` goes to the project owner.
- Match and notification writes commit atomically.

## Review Focus

- Concurrent opposite likes create one match and exactly one notification per participant.
- A project owner cannot act as a candidate on their own project.
- A candidate without a published profile cannot swipe or be matched.
- Outsiders cannot read match details or notifications.
- Read/mark-read operations affect only the notification recipient.

---

### Task 1: Harden swipe and match invariants

**Files:**
- Modify: `backend/core-api/app/models.py`
- Modify: `backend/core-api/app/api/swipes.py`
- Modify: `backend/core-api/app/services/views.py`
- Modify: `backend/core-api/app/schemas.py`
- Create: `backend/core-api/migrations/versions/20261115_04_matching_indexes.py` only if the index/constraint audit finds a missing required index or constraint.
- Test: `backend/core-api/tests/test_matching.py`
- Test: `backend/core-api/tests/test_concurrency.py`

**Interfaces:**
- Consumes: Phase 2 published Profile/Project and owner checks.
- Produces: `PUT /api/v1/projects/{project_id}/my-swipe`, `PUT /api/v1/projects/{project_id}/candidates/{candidate_id}/swipe` and complete `MatchRead`.

- [x] Step 1: Add tests for idempotent like/pass, pass-after-match, hidden/closed/blocked projects, duplicate matches, unpublished candidates and ownership violations.
- [x] Step 2: Audit existing uniqueness and indexes. Existing composite uniqueness and foreign-key indexes cover these queries, so no empty index migration was added.
- [x] Step 3: Preserve the project row lock and candidate published-profile check; reject owner swipes on hidden or unpublished projects.
- [x] Step 4: Keep owner swipes restricted to the project owner and reject self-swipes.
- [x] Step 5: Return `MatchRead` with backward-compatible IDs plus project/candidate summaries, `created_at` and `room_key`.
- [ ] Step 6: SQLite unit tests pass; PostgreSQL concurrency tests remain pending because the local Docker daemon is unavailable. Keep the draft PR unmerged until these tests pass.

### Task 2: Add match details and chat-access authorization

**Files:**
- Modify: `backend/core-api/app/api/swipes.py`
- Modify: `backend/core-api/app/services/views.py`
- Modify: `backend/core-api/app/schemas.py`
- Test: `backend/core-api/tests/test_matching.py`

**Interfaces:**
- Consumes: Task 1 MatchRead and participant checks.
- Produces: `GET /api/v1/matches`, `GET /api/v1/matches/{match_id}`, `GET /api/v1/matches/{match_id}/chat-access`, `POST /api/v1/matches/{match_id}/join`.

`MatchRead`:

```json
{"id":42,"project":{"id":9,"title":"API Platform","owner_id":3,"kind":"project"},"candidate":{"user_id":7,"display_name":"Ada Lovelace","headline":"Python developer","avatar_url":null},"created_at":"2026-11-15T12:00:00Z","room_key":"match:42"}
```

`ChatAccessRead`:

```json
{"allowed":true,"match_id":42,"room_key":"match:42","candidate_id":7,"project_owner_id":3,"expires_at":null}
```

- [x] Step 1: Add tests for list/detail summaries, candidate join, project-owner access and outsider denial.
- [x] Step 2: Add public-only summaries to the existing match response and the participant-checked match detail route.
- [x] Step 3: Return backward-compatible chat-access fields plus the access contract; outsiders get `403`, unknown matches `404`.
- [x] Step 4: Keep join candidate-only and idempotent; preserve project-to-project rejection.
- [x] Step 5: Matching endpoint tests pass on SQLite.

### Task 3: Add notification persistence and API

**Files:**
- Modify: `backend/core-api/app/models.py`
- Modify: `backend/core-api/app/schemas.py`
- Create: `backend/core-api/migrations/versions/20261115_04_add_notifications.py` if Task 1 needs no migration, otherwise `backend/core-api/migrations/versions/20261115_05_add_notifications.py`.
- Create: `backend/core-api/app/api/notifications.py`
- Modify: `backend/core-api/app/main.py`
- Test: `backend/core-api/tests/test_matching.py`

**Interfaces:**
- Consumes: Task 1 match transaction and current-user dependency.
- Produces: `GET /api/v1/notifications`, `GET /api/v1/notifications/unread-count`, `PATCH /api/v1/notifications/{notification_id}/read`, `POST /api/v1/notifications/read-all`.

- [x] Step 1: Add tests for recipient filtering, pagination, unread count, mark-read and read-all.
- [x] Step 2: Add the notification model and migration with a unique event key and recipient/read/created indexes.
- [x] Step 3: Allow only `match_created` and `project_joined`; deliver `project_joined` only to the project owner.
- [x] Step 4: Make notification reads ownership-checked and idempotent.
- [x] Step 5: Create `20261115_04_add_notifications.py` with `revision=mm_20261115_04`, `down_revision=mm_20261115_03`; no matching-index migration was needed.
- [x] Step 6: Notification API tests and migration checks pass on isolated SQLite.

### Task 4: Emit notifications atomically

**Files:**
- Modify: `backend/core-api/app/api/swipes.py`
- Modify: `backend/core-api/app/api/notifications.py`
- Test: `backend/core-api/tests/test_matching.py`
- Test: `backend/core-api/tests/test_concurrency.py`

**Interfaces:**
- Consumes: Task 3 Notification model and Task 2 match authorization.
- Produces: two `match_created` notifications per new mutual match and one owner-targeted `project_joined` notification per new membership.

- [x] Step 1: Add tests for two match recipients, one-sided likes, repeated likes, owner-only join notification and idempotent join.
- [x] Step 2: Insert match notifications in the same transaction using `match:{match_id}:user:{user_id}` event keys.
- [x] Step 3: Insert `project_joined` only when membership is first created, targeting the project owner.
- [ ] Step 4: SQLite checks pass; PostgreSQL concurrent likes/join tests remain pending because Docker is unavailable; keep the draft PR unmerged until they pass.

### Task 5: Verify and hand off matching contracts

**Files:**
- Modify: `backend/core-api/docs/api.md`
- Test: `backend/core-api/tests/test_matching.py`
- Test: `backend/core-api/tests/test_concurrency.py`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: stable matching/notification/chat-access contracts for Web/iOS Phase 3 and Backend Phase 4.

- [x] Step 1: Run the full backend suite and matching/notification tests on SQLite.
- [x] Step 2: Verify developer↔project match flow, self-swipe rejection and candidate profile eligibility.
- [x] Step 3: Verify participant and notification-recipient privacy on SQLite.
- [x] Step 4: Document JSON fields and status codes for the client owners.
- [ ] Step 5: Send the contract and test output to Web/iOS/Chat owners and commit `docs: hand off matching contracts`.

## Exit Criteria

- Only developer↔project matches can be created.
- Mutual likes create exactly one Match and exactly two private match notifications.
- Project membership creates one owner-targeted notification.
- Chat access is authorized for only the two match participants.

## Handoff

Web/iOS consume swipe, MatchRead and notification contracts. Backend Phase 4 consumes ChatAccessRead and must re-check it on REST reads, WebSocket authentication and sends.

## Rollback

Keep existing swipe endpoints backward-compatible. If notifications fail, roll back notification router/migration/client consumption while preserving the validated match transaction.
