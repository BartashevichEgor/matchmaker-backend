# Backend Phase 1 — Auth, JWT, sessions and email implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the backend auth contract for registration mode, email verification, JWT refresh, session rotation, logout and SMTP/Mailpit delivery.

**Architecture:** FastAPI remains the identity authority. Web uses access JWT plus HttpOnly refresh cookie; mobile uses access/refresh JSON tokens. Refresh sessions are database-backed and rotated atomically. Local Compose sends through Mailpit; production uses configured SMTP.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Redis, PyJWT, pwdlib/Argon2, fastapi-mail, pytest.

**Spec:** `docs/superpowers/specs/2026-11-14-matchmaker-mvp.md`

## Global Constraints

- Preserve `/api/v1` and deprecated auth aliases during the migration window.
- Registration requires `mode=developer|project`; `mode=both` returns `422`.
- A normal login with completed initial setup does not force setup redirect; the onboarding state is consumed by Phase 2.
- Access JWT lifetime is 15 minutes; refresh sessions default to 7 days.
- Verification codes are six digits, valid for 10 minutes and limited to five failed attempts.
- Link tokens are opaque, single-use, stored only as digests and valid for 24 hours.
- Production requires PostgreSQL, Redis and SMTP; local Compose uses Mailpit at `mailpit:1025` with inbox `http://localhost:8025`.
- Never log passwords, codes, tokens, refresh cookies or SMTP credentials.

## Review Focus

- Concurrent refresh requests produce at most one valid replacement.
- Replayed or revoked refresh tokens fail without creating a new session.
- `mode=both`, missing mode and invalid mode are rejected consistently.
- SMTP failure leaves the user unverified and returns a retryable `503`.
- Resend/reset responses do not reveal whether an email is registered.

---

### Task 1: Add registration-mode and session schema contract

**Files:**
- Modify: `backend/core-api/app/models.py`
- Modify: `backend/core-api/app/schemas.py`
- Modify: `backend/core-api/app/core/security.py`
- Modify: `backend/core-api/app/core/config.py`
- Create: `backend/core-api/migrations/versions/20261115_01_extend_refresh_sessions.py`
- Test: `backend/core-api/tests/test_auth.py`

**Interfaces:**
- Consumes: existing `User`, `EmailCode`, `RefreshSession`, `token()` and `decode_token()`.
- Produces: `Register.mode`, `User.onboarding_mode`, `WebTokens`, mobile token pair, `SessionRead`, `VerifyLinkInput` and access JWT `sid`.

- [ ] Step 1: Add failing tests for `mode=developer`, `mode=project`, rejected `mode=both`, missing mode and persisted mode.
- [ ] Step 2: Add `User.onboarding_mode` with allowed values `developer|project`.
- [ ] Step 3: Add `created_at`, `last_used_at`, `revoked_at`, `revocation_reason`, `user_agent`, client metadata and compatibility checks for `RefreshSession`.
- [ ] Step 4: Create `20261115_01_extend_refresh_sessions.py` with `revision=mm_20261115_01`, `down_revision=a13c8f92d4be`; backfill existing users as `developer`, existing session `created_at=now()`, nullable last-used/revocation/client fields and preserve `revoked`.
- [ ] Step 5: Add `sid` to access JWTs and keep refresh `jti` bound to the session primary key.
- [ ] Step 6: Define exact response shapes: web body `{access_token,token_type,expires_in}` with refresh cookie only; mobile body `{access_token,refresh_token,token_type,expires_in,refresh_expires_in,session_id}`.
- [ ] Step 7: Run `backend/.venv/Scripts/pytest.exe backend/core-api/tests/test_auth.py -q` and commit `auth: define mode and session contract`.

### Task 2: Implement registration and atomic session lifecycle

**Files:**
- Modify: `backend/core-api/app/api/auth.py`
- Modify: `backend/core-api/app/api/deps.py`
- Modify: `backend/core-api/app/core/security.py`
- Test: `backend/core-api/tests/test_auth.py`
- Test: `backend/core-api/tests/test_concurrency.py`

**Interfaces:**
- Consumes: Task 1 schemas and session model.
- Produces: registration with mode; `/auth/web/*`; `/auth/mobile/*`; `/auth/sessions`; per-session revoke; deprecated `/auth/login`, `/auth/refresh`, `/auth/logout` aliases.

- [ ] Step 1: Add failing tests for web cookie login, mobile bearer login, refresh rotation, current-session logout, logout-all and per-session revoke.
- [ ] Step 2: Require and persist `Register.mode` during `/api/v1/auth/register`.
- [ ] Step 3: Implement one shared token-issue function and transport-specific web/mobile adapters.
- [ ] Step 4: Implement web HttpOnly refresh cookie with exact origin, SameSite, Secure, CORS and CSRF behavior.
- [ ] Step 5: Implement mobile refresh token in JSON without browser-cookie dependency.
- [ ] Step 6: Atomically revoke consumed refresh sessions; refresh rejects either `revoked=true` or `revoked_at != null`.
- [ ] Step 7: Implement session listing/revoke, logout-all token-version increment and password-reset session invalidation.
- [ ] Step 8: Run SQLite tests and PostgreSQL concurrency tests; require PostgreSQL evidence for the rotation guarantee.
- [ ] Step 9: Commit `feat: implement auth session lifecycle`.

### Task 3: Implement verification and password-reset email delivery

**Files:**
- Modify: `backend/core-api/app/api/auth.py`
- Modify: `backend/core-api/app/services/mail.py`
- Create: `backend/core-api/app/services/mail_templates.py`
- Create: `backend/core-api/app/templates/email/verification.html`
- Create: `backend/core-api/app/templates/email/password_reset.html`
- Modify: `backend/core-api/app/core/config.py`
- Modify: `backend/core-api/.env.example`
- Modify: `backend/core-api/tests/test_auth.py`

**Interfaces:**
- Consumes: `EmailCode`, `Register.mode` and SMTP/Mailpit settings.
- Produces: `/verify-email`, `/verify-email-link`, `/resend-verification`, `/forgot-password`, `/reset-password`.

- [ ] Step 1: Add tests for HTML/plaintext delivery, code expiry, five-attempt limit, link expiry, link single-use, resend replacement and SMTP failure.
- [ ] Step 2: Reuse `EmailCode` with `purpose=verify_link` for the 24-hour link digest; keep numeric `verify` code at 10 minutes.
- [ ] Step 3: Render verification email with both link and six-digit code, and password-reset email with its reset credential; never render secrets into logs.
- [ ] Step 4: Make resend/reset enumeration-safe and preserve rate limits.
- [ ] Step 5: Ensure delivery failure leaves the account unverified and returns `503`.
- [ ] Step 6: Keep local `outbox` support for direct development and configure Compose Mailpit through `MAIL_MODE=smtp`, `MAIL_SERVER=mailpit`, `MAIL_PORT=1025`, `MAIL_FROM=noreply@matchmaker.local`.
- [ ] Step 7: Run focused auth tests and commit `feat: send verification and reset emails`.

### Task 4: Document and verify Mailpit handoff

**Files:**
- Modify: `backend/core-api/docs/deployment.md`
- Modify: `backend/core-api/docs/api.md`
- Create: `backend/docs/mailpit/README.md`
- Test: `backend/core-api/tests/test_auth.py`

**Interfaces:**
- Consumes: Tasks 1–3 and existing `backend/docker-compose.yml` Mailpit service.
- Produces: reproducible local inbox verification instructions for Web and iOS owners.

- [ ] Step 1: Document `docker compose up -d db redis mailpit api` from `backend/` and the `http://localhost:8025` inbox.
- [ ] Step 2: Document test registration with `mode=developer|project`, sender `noreply@matchmaker.local`, recipient filtering, code/link verification and resend/reset checks.
- [ ] Step 3: Document that likes, matches, project joins and chat notifications are in-app only in MVP.
- [ ] Step 4: Run the Mailpit flow against PostgreSQL and record the message subject, sender, recipient and successful verification.
- [ ] Step 5: Commit `docs: document Mailpit verification workflow` and send the README plus auth DTOs to Web/iOS owners.

## Exit Criteria

- Registration persists exactly one onboarding mode.
- Verified accounts can use web or mobile login and rotate refresh sessions safely.
- Verification works through Mailpit locally and generic SMTP in production.
- Normal login does not decide setup UI; it exposes stable auth/onboarding data for Phase 2.

## Handoff

Send Web and iOS owners the exact auth JSON shapes, cookie rules, registration `mode` field, verification endpoints and Mailpit README. Phase 2 backend consumes `User.onboarding_mode` and adds `GET /api/v1/onboarding`.

## Rollback

Keep deprecated auth aliases during rollout. If SMTP/template changes fail, disable link delivery while retaining numeric code verification and Mailpit/outbox; never delete users, email-code records or session history.
