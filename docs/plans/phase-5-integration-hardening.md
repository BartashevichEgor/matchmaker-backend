# Backend Phase 5 — Production hardening and backend handoff implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make backend/chat deployment fail-closed, observable, rate-limited, indexed, recoverable and ready for Web/iOS full-stack acceptance.

**Architecture:** FastAPI, chat service, PostgreSQL, Redis and SMTP/Mailpit remain separately configured services. Production requires PostgreSQL, Redis, SMTP and valid JWT settings; local/test fallbacks remain explicit.

**Tech Stack:** FastAPI, PostgreSQL, Redis, SMTP, Docker Compose, Alembic, Node.js/TypeScript, pytest, Ruff.

**Spec:** `docs/superpowers/specs/2026-11-14-matchmaker-mvp.md`

## Global Constraints

- Do not modify Web/iOS source in the backend plan.
- Production must fail closed when PostgreSQL, Redis, SMTP or JWT settings are missing.
- Logs exclude credentials, tokens, codes, message bodies and passwords.
- Rate limits use Redis and return HTTP 429 with `Retry-After`.
- No destructive database reset, force-push or unreviewed production migration.
- Full moderation console, organization members, multi-project accounts and advanced search remain post-MVP.

## Review Focus

- Missing production dependencies fail startup with actionable errors.
- Readiness distinguishes app liveness from database/Redis/SMTP/chat dependency failure.
- Rate limits cannot be bypassed by changing casing or retrying across workers.
- Backups restore the exact deployed migration chain into an isolated database.
- Backend handoff artifacts match Web/iOS API clients and acceptance flow.

---

### Task 1: Harden production configuration and observability

**Files:**
- Modify: `backend/core-api/app/core/config.py`
- Modify: `backend/core-api/app/main.py`
- Modify: `backend/core-api/app/api/health.py`
- Modify: `backend/core-api/app/core/limits.py`
- Modify: `backend/docker-compose.yml`
- Modify: `backend/.env.example`
- Create: `backend/core-api/tests/test_production_config.py`

**Interfaces:**
- Consumes: Phase 1–4 service settings and health contracts.
- Produces: fail-closed settings, `/ping` liveness, `/health` readiness, safe request IDs/logs and Redis rate limits.

- [x] Step 1: Add failing tests for missing JWT secret, non-PostgreSQL production DB, absent Redis and non-SMTP production mail.
- [x] Step 2: Make production settings fail startup while local/test settings remain explicit.
- [x] Step 3: Separate `/ping` from `/health` and report dependency status without secrets.
- [x] Step 4: Add request IDs, duration/status logs and redaction assertions.
- [x] Step 5: Configure Redis limits: login 5/15m per IP+normalized email, verification send 3/15m per user+IP, verification check 5/10m per user, favorites 60/min per user, swipes 120/min per user, chat sends 60 per 60-second window per user.
- [x] Step 6: Return `429`, error code `rate_limited` and `Retry-After` seconds.
- [x] Step 7: Run backend tests and Ruff.
- [ ] Step 8: Commit `harden: validate production configuration` with the approved Phase 5 PR work.

### Task 2: Add indexes and recovery scripts

**Files:**
- Create: `backend/core-api/migrations/versions/20261115_05_add_catalog_indexes.py` (`mm_20261115_05` after actual current head `mm_20261115_04`)
- Create: `backend/scripts/backup-db.sh`
- Create: `backend/scripts/restore-check.sh`
- Modify: `backend/core-api/docs/database.md`
- Modify: `backend/core-api/docs/deployment.md`
- Create: `backend/core-api/tests/test_migrations.py`
- Modify: `backend/core-api/app/models.py`, `backend/core-api/migrations/env.py` (keep metadata and isolated migration tests aligned)

**Interfaces:**
- Consumes: the actual current migration chain through `mm_20261115_04`, all catalog/matching/notification tables and Compose settings.
- Produces: migration `mm_20261115_05`, indexed queries and isolated backup/restore procedures.

- [x] Step 1: Add migration tests for empty database upgrade and expected index names.
- [x] Step 2: Create `20261115_05_add_catalog_indexes.py` with `revision=mm_20261115_05`, `down_revision=mm_20261115_04`.
- [x] Step 3: Add indexes for profile filters, project visibility/status/owner, favorites, notifications, swipes and matches.
- [x] Step 4: Implement backup to an explicit target path without deleting source data.
- [x] Step 5: Implement restore-check against an isolated database/container, never active production.
- [x] Step 6: Document retention, migration order, restore steps and rollback boundaries.
- [x] Step 7: Run backend tests, Alembic migration checks, Ruff, Compose config validation and shell syntax checks.
- [x] Step 8: Run the container restore check with Docker Engine and a PostgreSQL dump.
- [ ] Step 9: Commit `ops: add database recovery checks` with the approved Phase 5 PR work.

### Task 3: Verify full backend acceptance

**Files:**
- Modify: `backend/core-api/docs/api.md`
- Modify: `backend/core-api/docs/deployment.md`
- Test: `backend/core-api/tests/test_auth.py`
- Test: `backend/core-api/tests/test_matching.py`
- Test: `backend/core-api/tests/test_concurrency.py`
- Test: `backend/core-api/tests/test_production_config.py`
- Test: `backend/core-api/tests/test_migrations.py`

**Interfaces:**
- Consumes: Backend Phases 0–4 and the Web/iOS handoff contracts.
- Produces: backend acceptance report inputs and release checklist.

- [x] Step 1: Run PostgreSQL, Redis, Mailpit, FastAPI and chat Compose services.
- [x] Step 2: Register a developer-mode account and a separate project-mode account; verify both by Mailpit.
- [x] Step 3: Complete profile/project setup, confirm completed login routes to main, and confirm one project ownership.
- [x] Step 4: Execute developer↔project like/match/notification/chat flow; reject developer↔developer and project↔project.
- [x] Step 5: Run refresh replay/concurrency, rate-limit, migration, backup/restore and service-health checks.
- [ ] Step 6: Document known skips and send backend release checklist to Web/iOS owners; commit `docs: complete backend acceptance handoff`.

## Exit Criteria

- Production configuration fails closed and readiness is meaningful.
- Migrations, indexes, backups and restore checks are tested.
- Backend contracts match all owner-specific client plans.
- Full developer↔project flow reaches authorized chat without invalid match types.

## Handoff

Send Web/iOS owners API docs, environment contract, health URLs, rate-limit behavior, exact DTO versions and acceptance results. Do not deploy or tag releases from this plan.

## Rollback

Keep hardening behind configuration gates. Revert only the relevant backend commit or disable chat independently; never reset production databases or delete backup artifacts.
