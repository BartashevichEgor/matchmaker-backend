# Auth Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the security, session-retention, expiry, and test-coverage gaps found in the Phase 1 backend diff.

**Architecture:** Keep FastAPI as the auth authority. Add a stateless double-submit CSRF token for web cookie actions, enforce encrypted authenticated SMTP in production, prune rotated session history, and make access-token authorization honor refresh-session expiry.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic Settings, Alembic, pytest, Ruff, Docker Compose.

**Spec:** `docs/plans/phase-1-auth-email.md` and the Phase 1 auth contract in `core-api/docs/api.md`.

## Global Constraints

- Keep backend and frontend as separate repositories; do not modify frontend code.
- Preserve deprecated mobile/legacy auth aliases.
- Do not log or return refresh tokens, verification credentials, passwords, or SMTP secrets.
- Keep SQLite tests isolated and PostgreSQL migrations compatible.
- Use the smallest focused change and preserve unrelated user changes.

## Review Focus

- Cross-site requests to cookie-authenticated refresh/logout must fail without a matching CSRF header and cookie.
- Production SMTP credentials must never be accepted without TLS.
- Repeated refresh rotation must not grow session history without bound.
- Expired refresh sessions must not authorize a still-valid access token.
- Verification limits, link expiry, resend invalidation, SMTP failure, and CSRF behavior must have regression tests.
- Public HTTP request bodies must be bounded before JSON parsing, including chunked requests.

### Task 1: Add web CSRF protection

**Files:**
- Modify: `core-api/app/api/auth.py`
- Modify: `core-api/app/schemas.py`
- Modify: `core-api/tests/test_auth.py`
- Modify: `core-api/docs/api.md`

**Interfaces:**
- Web login and refresh responses expose a random `csrf_token`; the same value is set in a non-HttpOnly cookie.
- Web refresh and logout require `X-CSRF-Token` to match the CSRF cookie, in addition to the existing exact Origin check.

- [x] Add helpers to set, clear, and validate the CSRF cookie/header pair without logging the token.
- [x] Include `csrf_token` in `WebTokens`, rotate it on web refresh, and clear it on web logout/logout-all.
- [x] Add tests for missing, mismatched, and valid CSRF tokens.
- [x] Document the client contract.

### Task 2: Enforce safe production SMTP configuration

**Files:**
- Modify: `core-api/app/core/config.py`
- Test: `core-api/tests/test_config.py`

**Interfaces:**
- Production settings reject authenticated SMTP without either STARTTLS or implicit TLS.
- Settings reject enabling both TLS modes at once.

- [x] Add validation with clear errors while leaving local Mailpit defaults unchanged.
- [x] Test unsafe production combinations and a valid TLS configuration.

### Task 3: Bound refresh-session history and authorization expiry

**Files:**
- Modify: `core-api/app/api/auth.py`
- Modify: `core-api/app/api/deps.py`
- Modify: `core-api/tests/test_auth.py`

**Interfaces:**
- Rotation deletes the just-consumed revoked session after the replacement session is created, preserving active session metadata without unbounded rotation rows.
- `current_user` requires the linked refresh session to have `expires_at > now`.

- [x] Delete revoked/expired session history when issuing a new session and expose active sessions only.
- [x] Add the expiry predicate to access-token session lookup.
- [x] Test rotation retention and access rejection after session expiry.

### Task 4: Cover the risky verification and delivery paths

**Files:**
- Modify: `core-api/tests/test_auth.py`

- [x] Test the fifth failed code attempt and rejection of the sixth.
- [x] Test verification-link expiry.
- [x] Test resend invalidates the previous code and link.
- [x] Test SMTP failure returns 503 while retaining the account for resend.

### Task 5: Verify the complete backend change

**Files:**
- No additional source files.

- [x] Run targeted tests, then the full pytest suite.
- [x] Run Ruff, format check, diff check, Alembic check, and Compose config validation.
- [x] Re-run `ponytail-review` and `security-best-practices` against the final diff.
- [x] Report any PostgreSQL-only checks that cannot run in the local environment.

### Task 6: Bound HTTP request bodies

**Files:**
- Create: `core-api/app/core/request_limits.py`
- Modify: `core-api/app/core/config.py`
- Modify: `core-api/app/main.py`
- Modify: `core-api/.env.example`
- Modify: `docs/deployment.md`
- Test: `core-api/tests/test_auth.py`
- Test: `core-api/tests/test_request_limits.py`

- [x] Reject bodies above the configured 2 MB default using both `Content-Length` and chunked-body accounting.
- [x] Keep the limit middleware outermost and return HTTP 413 without invoking routes.
- [x] Test fixed-length and chunked oversized requests.
- [x] Re-run the full backend and Docker verification suite.

## Recovery

All changes are additive or narrowly scoped. If a client cannot send the new CSRF header, the web auth contract must be updated before deployment; database schema and existing mobile/legacy token formats are unchanged.
