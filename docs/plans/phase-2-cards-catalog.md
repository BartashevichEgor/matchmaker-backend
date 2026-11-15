# Backend Phase 2 — Profiles, projects, onboarding and cards implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose real profile/project cards, two-mode onboarding, one-project-per-account management, filters, pagination and private favorites.

**Architecture:** A User owns one personal Profile and zero or one Project. Registration mode from Backend Phase 1 controls the first setup route only. Profile/project publication is independent from the current discovery mode, and all public cards are filtered server-side.

**Tech Stack:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2, pytest.

**Spec:** `docs/superpowers/specs/2026-11-14-matchmaker-mvp.md`

## Global Constraints

- Registration modes are exactly `developer|project`; no `both` mode exists.
- A user may own at most one project; the UI hides the create action after creation and the API rejects direct/stale second creates with `409`.
- Profile and project card visibility uses `draft|published|hidden`.
- Public catalog returns only verified/active published profiles and published open projects.
- Catalog pagination is deterministic offset/limit with limit max 100.
- Favorites are private, idempotent and never create matches.
- Matching remains strictly developer↔project and is implemented in Backend Phase 3.

## Review Focus

- Existing duplicate project owners are detected before the unique constraint and never silently merged.
- `next_setup=none` is returned for a completed initial card so clients route to the main page.
- Draft/hidden cards and private profile fields never leak through catalog endpoints.
- A second project cannot be created through UI, direct API or concurrent requests.
- Web and iOS receive the same onboarding/card DTOs and error semantics.

---

### Task 1: Extend card models and enforce one project per user

**Files:**
- Modify: `backend/core-api/app/models.py`
- Modify: `backend/core-api/app/schemas.py`
- Create: `backend/core-api/migrations/versions/20261115_02_extend_card_fields.py`
- Create: `backend/core-api/migrations/versions/20261115_03_add_saved_cards.py`
- Test: `backend/core-api/tests/test_matching.py`

**Interfaces:**
- Consumes: Phase 1 `User.onboarding_mode`, existing Profile/Project relations.
- Produces: `Profile.work_format`, `Profile.visibility`, project metadata/visibility, unique `Project.owner_id`, `SavedProfile`, `SavedProject` and typed card DTOs.

- [ ] Step 1: Add failing tests for visibility defaults, allowed enums, duplicate project creation and unique saved-card rows.
- [ ] Step 2: Add `Profile.visibility` and project fields with defaults `visibility=draft`, `kind=project`, `work_format=remote`, `commitment=flexible`.
- [ ] Step 3: Add the unique owner constraint for `Project.owner_id`; migration must fail with an actionable duplicate-owner list rather than deleting/merging data.
- [ ] Step 4: Add `SavedProfile(user_id,target_user_id,created_at)` and `SavedProject(user_id,project_id,created_at)` with composite uniqueness.
- [ ] Step 5: Add Pydantic validation for `kind=project|company`, `work_format=remote|hybrid|onsite`, `commitment=full_time|part_time|flexible`, `visibility=draft|published|hidden`.
- [ ] Step 6: Set `revision=mm_20261115_02`, `down_revision=mm_20261115_01` and `revision=mm_20261115_03`, `down_revision=mm_20261115_02`.
- [ ] Step 7: Run empty/existing PostgreSQL migration tests and commit `feat: add card visibility and ownership limits`.

### Task 2: Implement public people and project catalogs

**Files:**
- Modify: `backend/core-api/app/api/profiles.py`
- Modify: `backend/core-api/app/api/projects.py`
- Modify: `backend/core-api/app/services/views.py`
- Modify: `backend/core-api/app/schemas.py`
- Test: `backend/core-api/tests/test_matching.py`

**Interfaces:**
- Consumes: Task 1 card fields and existing ownership dependencies.
- Produces: `GET /api/v1/profiles`, `GET /api/v1/projects`, `GET /api/v1/projects/mine`, `POST /api/v1/projects`, `PUT /api/v1/projects/{id}`, `PATCH /api/v1/projects/{id}/status`.

- [ ] Step 1: Add failing tests for search, role/skill/work-format filters, deterministic pagination and public-card exclusion rules.
- [ ] Step 2: Implement public profiles ordered by `user_id ASC`, excluding self, unverified/inactive users and draft/hidden profiles.
- [ ] Step 3: Implement public projects ordered by `updated_at DESC, id DESC`, limited to published/open projects.
- [ ] Step 4: Implement `GET /projects/mine` for the owner’s draft/published/closed card without exposing private owner data.
- [ ] Step 5: Make `POST /projects` transactionally reject a second owner project with `409`, including concurrent create attempts.
- [ ] Step 6: Preserve owner-only edits and status changes; reject edits to another owner’s project.
- [ ] Step 7: Run catalog/ownership tests and commit `feat: expose profile and project catalogs`.

### Task 3: Implement onboarding state endpoint

**Files:**
- Create: `backend/core-api/app/api/onboarding.py`
- Modify: `backend/core-api/app/main.py`
- Modify: `backend/core-api/app/schemas.py`
- Test: `backend/core-api/tests/test_onboarding.py`

**Interfaces:**
- Consumes: Phase 1 `User.onboarding_mode`, Profile visibility/completeness and the single Project contract.
- Produces: `GET /api/v1/onboarding`:

```json
{
  "mode": "developer",
  "profile": {"exists": true, "complete": true, "visibility": "published"},
  "project": {"exists": false, "complete": false, "visibility": null, "status": null},
  "next_setup": "none",
  "can_create_project": true
}
```

- [ ] Step 1: Add failing tests for developer/project mode, incomplete/complete cards, optional second-card setup and unauthenticated access.
- [ ] Step 2: Return mode and completion summaries without private card fields.
- [ ] Step 3: Return `next_setup=profile` or `project` only for incomplete initial setup; return `next_setup=none` for completed accounts.
- [ ] Step 4: Return `can_create_project=false` whenever a project exists.
- [ ] Step 5: Register the read-only router under `/api/v1/onboarding` and commit `feat: add onboarding state endpoint`.

### Task 4: Implement favorites

**Files:**
- Create: `backend/core-api/app/api/favorites.py`
- Modify: `backend/core-api/app/main.py`
- Modify: `backend/core-api/app/schemas.py`
- Test: `backend/core-api/tests/test_matching.py`

**Interfaces:**
- Consumes: Task 1 SavedProfile/SavedProject and Task 2 card views.
- Produces: `GET /api/v1/favorites?kind=profile|project`, `PUT /api/v1/favorites/{kind}/{target_id}`, `DELETE /api/v1/favorites/{kind}/{target_id}`.

- [ ] Step 1: Add tests for save/list/remove, duplicate save, missing target, self-save and own-project save.
- [ ] Step 2: Validate target kind and resolve profile/project targets.
- [ ] Step 3: Make PUT idempotent and DELETE safe when absent.
- [ ] Step 4: Return only the current user’s favorites with public card summaries.
- [ ] Step 5: Register the router, verify OpenAPI and commit `feat: add private card favorites`.

### Task 5: Verify backend Phase 2 and hand off

**Files:**
- Modify: `backend/core-api/docs/api.md`
- Modify: `backend/core-api/docs/deployment.md`
- Test: `backend/core-api/tests/test_matching.py`
- Test: `backend/core-api/tests/test_onboarding.py`

**Interfaces:**
- Consumes: Tasks 1–4.
- Produces: stable DTOs and endpoint behavior for Web/iOS Phase 2 and Backend Phase 3.

- [ ] Step 1: Run backend tests for migrations, onboarding, catalog filters, one-project ownership and favorites.
- [ ] Step 2: Verify the flow: register developer mode, complete profile, login to main page, create one project later, confirm create action becomes manage state.
- [ ] Step 3: Verify project mode first setup and later optional developer-profile setup.
- [ ] Step 4: Verify direct second-project POST returns `409` while normal clients never render the create action.
- [ ] Step 5: Document DTOs, error codes and the `next_setup`/`can_create_project` contract.
- [ ] Step 6: Send the API contract and test output to Web/iOS owners and commit `docs: hand off Phase 2 card contracts`.

## Exit Criteria

- One user owns one personal profile and zero or one project.
- Catalogs expose only safe published cards.
- Completed login flow routes to the main page; incomplete initial setup routes to the correct setup form.
- Web/iOS can create the optional second card but cannot create a second project.

## Handoff

Web and iOS consume the exact onboarding JSON, catalog DTOs, `409` behavior and visibility rules. Backend Phase 3 consumes published developer profiles, published open projects and the ownership checks.

## Rollback

Apply migrations backward-compatibly. If the unique owner migration finds duplicates, stop before constraint creation and resolve data explicitly; never delete or merge projects automatically.
