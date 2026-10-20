# Contribution Matrix

| Phase | Readiness | Concrete Features | Key Files | Dependencies | Review Gate |
| --- | --- | --- | --- | --- | --- |
| PHASE-1 | done | Vite bootstrap, npm scripts, React Router setup, public routes, protected route skeleton, 404 page, app folder structure | `web/package.json`, `web/vite.config.*`, `web/src/main.*`, `web/src/app/router.*`, `web/src/pages/*` | none | app starts, routes resolve, public pages render outside layout |
| PHASE-2 | done | auth types and schemas, mockAuthService, localStorage versioning, email normalization, session restore, AuthProvider, login/register forms, redirect state handling | `web/src/features/auth/*`, `web/src/shared/lib/auth/*`, `web/src/app/providers/*`, `web/src/pages/login/*`, `web/src/pages/register/*` | PHASE-1 | register/login/logout/session restore/deep-link redirect all pass |
| PHASE-3 | done | AppLayout, collapsible sidebar, icon navigation, active navigation, SectionPlaceholder component, protected section pages (feed, projects, profile, matches, chat with matchId), logout button flow | `web/src/layouts/AppLayout/*`, `web/src/shared/ui/SectionPlaceholder.tsx`, `web/src/app/router.tsx` | PHASE-1, PHASE-2 | protected routes render through layout, active nav works, sidebar does not overflow on mobile |
| PHASE-4 | done | route tests, auth tests, storage edge case tests, deep-link tests, README commands, MVP limitations documentation, manual desktop/mobile checks | `web/src/**/*.test.*`, `web/src/test/*`, `web/README.md` | PHASE-1, PHASE-2, PHASE-3 | route/auth/storage coverage is complete and documented |

## How to Use

- `Readiness` should move from `not started` to `in progress` and then `done`.
- `Concrete Features` should be updated whenever the feature scope changes.
- `Dependencies` should reflect prerequisite phases that must be stable before work starts.
- `Review Gate` should be the acceptance checklist for phase completion.

## Tracking Rules

- Update the matrix whenever a feature is added to, removed from, or reassigned between phases.
- Do not mark a phase done until its exit criteria are verified.
- Keep the matrix synchronized with the phase files and the main plan.
