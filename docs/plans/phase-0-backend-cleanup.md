# Backend Phase 0 — Repository cleanup implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `backend/` a backend-only repository by removing the imported client, launcher scripts, personal reports and static demo while preserving API, migrations, tests, Compose and technical documentation.

**Architecture:** `backend/` remains the FastAPI repository; `frontend/` remains the standalone client repository and is read-only during this phase. Cleanup is performed on a branch based on the latest backend remote commit, with no history rewrite.

**Tech Stack:** Git, PowerShell, FastAPI, SQLAlchemy, Alembic, pytest, Ruff, Docker Compose.

**Spec:** `docs/superpowers/specs/2026-11-14-matchmaker-mvp.md`

## Global Constraints

- Do not modify `frontend/`.
- Do not delete backend API code, migrations, tests, Compose services, CI or technical API/database/deployment docs.
- Keep `core-api/scripts/render_erd.ps1`.
- Keep the `/auth/session` response adapter `frontend_user`.
- Do not reset, force-push, rewrite history or delete secrets.

## Review Focus

- Cleanup starts from the latest `backend/origin/main`.
- `frontend/` has identical clean status before and after cleanup.
- `/`, `/docs`, `/openapi.json`, `/health`, `/ping`, migrations and tests still work.
- Retained files contain no references to deleted launchers or embedded frontend code.
- The backend README remains sufficient for direct and Compose-based setup.

---

### Task 1: Prepare the cleanup branch

**Files:**
- No source files changed.

**Interfaces:**
- Consumes: `backend` and `frontend` Git statuses.
- Produces: branch `chore/backend-only-cleanup` based on fetched `backend/origin/main`.

- [ ] Step 1: Run `git -C backend status --short --branch` and `git -C frontend status --short --branch`; stop if either working tree has uncommitted changes.
- [ ] Step 2: Run `git -C backend fetch origin main` without changing the working tree.
- [ ] Step 3: Create `git -C backend switch -c chore/backend-only-cleanup origin/main`; do not overwrite an existing branch.
- [ ] Step 4: Record `git -C backend rev-parse HEAD`, the top-level tree and the clean frontend status.
- [ ] Step 5: Commit nothing in this task.

### Task 2: Delete imported client and launcher artifacts

**Files:**
- Delete: `backend/frontend/`
- Delete: `backend/start.ps1`
- Delete: `backend/start-demo.ps1`
- Delete: `backend/start-background.ps1`
- Delete: `backend/start-local-db.ps1`
- Delete: `backend/chat-service/README.md`

**Interfaces:**
- Consumes: backend Compose and direct core-api commands.
- Produces: no embedded client source, no developer launcher scripts and no placeholder chat README.

- [ ] Step 1: Delete only the six listed backend targets; never use a workspace-wide recursive delete.
- [ ] Step 2: Verify `Test-Path backend/frontend`, `Test-Path frontend/web` and `Test-Path frontend/ios` return `False`, `True`, `True` respectively.
- [ ] Step 3: Verify `git -C backend status --short` lists only the intended deletions.
- [ ] Step 4: Commit `chore: remove embedded frontend and launcher scripts`.

### Task 3: Rewrite backend-only documentation

**Files:**
- Delete: `backend/core-api/docs/egor-backend-guide.md`
- Delete: `backend/core-api/docs/egor-weekly-status.md`
- Delete: `backend/core-api/docs/report-drafts.md`
- Delete: `backend/core-api/docs/sprint-2-review-retrospective.md`
- Delete: `backend/core-api/docs/frontend-integration.md`
- Delete: `backend/core-api/docs/figma-auth-contract.md`
- Delete: `backend/core-api/docs/delivery.md`
- Modify: `backend/README.md`
- Modify: `backend/core-api/README.md`

**Interfaces:**
- Consumes: `backend/docker-compose.yml`, requirements files, `alembic.ini`, API/database/deployment docs.
- Produces: backend-only setup instructions covering Compose, direct Uvicorn, migrations, tests, Ruff, SMTP/Mailpit and API docs.

- [ ] Step 1: Delete only personal/reporting/integration documents listed above.
- [ ] Step 2: Rewrite `backend/README.md` with exact setup commands from the backend root and links to retained technical docs.
- [ ] Step 3: Rewrite `backend/core-api/README.md` without references to deleted launchers, static demo or embedded frontend.
- [ ] Step 4: Run `rg -n "frontend/|start-demo|start-background|start-local-db|start\.ps1|egor-|report-drafts|sprint-2|figma-auth|frontend-integration|delivery\.md" backend` and remove stale retained references.
- [ ] Step 5: Commit `docs: simplify backend-only documentation`.

### Task 4: Remove the backend static demo page

**Files:**
- Delete: `backend/core-api/app/static/index.html`
- Delete: `backend/core-api/app/static/style.css`
- Delete: `backend/core-api/app/static/app.js`
- Delete: `backend/core-api/app/static/favicon.svg`
- Modify: `backend/core-api/app/main.py`
- Test: `backend/core-api/tests/test_matching.py`

**Interfaces:**
- Consumes: FastAPI app and existing health/OpenAPI tests.
- Produces: `GET /` JSON `{ "service": "matchmaker-api", "docs": "/docs", "health": "/health" }`; `/docs`, `/openapi.json`, `/health` and `/ping` remain unchanged.

- [ ] Step 1: Add a failing root endpoint test asserting the exact JSON response and HTTP 200.
- [ ] Step 2: Remove the demo FileResponse/static mount while preserving Swagger assets.
- [ ] Step 3: Run `backend/.venv/Scripts/pytest.exe backend/core-api/tests/test_matching.py -q` and require root, health and OpenAPI tests to pass.
- [ ] Step 4: Commit `refactor: remove backend demo page`.

### Task 5: Verify and hand off the clean backend

**Files:**
- No planned source changes; fix only stale references or documentation errors found by verification.

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: reviewable backend-only cleanup branch for Backend Phase 1.

- [ ] Step 1: Run `backend/.venv/Scripts/pytest.exe backend/core-api -q`.
- [ ] Step 2: Run `backend/.venv/Scripts/ruff.exe check backend/core-api`.
- [ ] Step 3: Validate Compose with process-local `POSTGRES_PASSWORD` and `JWT_SECRET`; do not create or commit secrets.
- [ ] Step 4: Confirm `frontend/` status is unchanged and the backend diff contains only approved cleanup.
- [ ] Step 5: Record test results, intentional skips and the resulting backend commit SHA.

## Exit Criteria

- Backend repository contains no imported frontend or developer launcher artifacts.
- Standalone frontend remains unchanged.
- API, migrations, tests, Compose and technical docs remain usable.

## Handoff

Backend Phase 1 starts from the cleanup branch/commit. Share the final commit SHA and verification output with Web and iOS owners; they must not depend on deleted backend client files.

## Rollback

Revert only the cleanup commits on the cleanup branch. Do not restore files by resetting shared branches and do not modify the standalone frontend repository.
