---
phase: 01-platform-foundation-auth
plan: 05
subsystem: auth
tags: [spa-auth, supabase-js, require-auth, meapi, playwright, vite-mocks]

requires:
  - phase: 01-platform-foundation-auth
    provides: JWT GET /me + POST /me/ping API (Plans 01–03); D-09/D-11/D-12 context
provides:
  - Sole supabaseClient createClient + authApi (signIn/signOut/getSession)
  - Corporate emailDomain helper with node --test
  - LoginPage + RequireAuth returnUrl gate (VITE_USE_MOCKS default true)
  - meApi GET /me + POST /me/ping with mock/live paths
  - Playwright tests/auth.spec.js (6 contracts)
affects:
  - 01-06 docs/deploy notes if any FE env docs
  - Phase 2+ live issue/vote APIs behind same RequireAuth
  - Phase 5 AUTH-03 admin 403 remainder

actuals:
  tokens: 7378
  tasks: 3
  commits: 6

tech-stack:
  added: ["@supabase/supabase-js@2.116.0"]
  patterns:
    - FE talks only through web/src/services/ (authApi, meApi, emailDomain)
    - VITE_USE_MOCKS default true; __DIGEST_FORCE_AUTH_GATE__ for offline RequireAuth tests
    - Auth/me harness on window mirrors votingApi arm-fail

key-files:
  created:
    - web/src/services/emailDomain.js
    - web/src/services/emailDomain.test.js
    - web/src/services/supabaseClient.js
    - web/src/services/authApi.js
    - web/src/services/authEnv.js
    - web/src/services/meApi.js
    - web/src/pages/LoginPage.jsx
    - web/src/components/RequireAuth.jsx
    - web/src/components/PlatformProofBanner.jsx
    - tests/auth.spec.js
  modified:
    - web/src/App.jsx
    - web/src/main.jsx
    - web/src/pages/IssuePage.jsx
    - web/package.json
    - web/package-lock.json
    - playwright.config.js

key-decisions:
  - "Mock authApi/meApi when VITE_USE_MOCKS!==false; live supabase-js + fetch only when false"
  - "RequireAuth skips gate when mocks on (D-09); tests force gate via window.__DIGEST_FORCE_AUTH_GATE__"
  - "sanitizeReturnUrl allows same-origin relative paths only (T-01-12)"
  - "AUTH-03 admin API 403 deferred to Phase 5"

patterns-established:
  - "Pages never import @supabase/supabase-js — only supabaseClient.js"
  - "Playwright harness: window.__DIGEST_AUTH_HARNESS__ / __DIGEST_ME_HARNESS__"

requirements-completed: [PLAT-03, PLAT-07, AUTH-01, AUTH-02, AUTH-03]

coverage:
  - id: D1
    description: "Corporate email domain helper rejects non-ADR-0003 domains"
    requirement: AUTH-01
    verification:
      - kind: unit
        ref: "web/src/services/emailDomain.test.js"
        status: pass
    human_judgment: false
  - id: D2
    description: "Disallowed domain shows inline message; signIn not invoked"
    requirement: AUTH-01
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#rejects disallowed email domain without creating a session"
        status: pass
    human_judgment: false
  - id: D3
    description: "Successful login without returnUrl navigates to current issue /"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#navigates to current issue after successful login without returnUrl"
        status: pass
    human_judgment: false
  - id: D4
    description: "returnUrl=/voting returns to /voting after login"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#returns to returnUrl path after successful login"
        status: pass
    human_judgment: false
  - id: D5
    description: "Auth gate redirects unauthenticated users to /login?returnUrl=…"
    requirement: AUTH-03
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#redirects protected route to login with returnUrl when auth gate is on"
        status: pass
    human_judgment: false
  - id: D6
    description: "meApi mock identity + platform ping proof on IssuePage"
    requirement: PLAT-03
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#shows mock CurrentUser identity and accepts platform ping"
        status: pass
    human_judgment: false
  - id: D7
    description: "Login network failure shows ErrorPanel + Retry (PLAT-07)"
    requirement: PLAT-07
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#shows retryable network banner when sign-in fails"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-19
status: complete
---

# Phase 01 Plan 05: SPA Auth + meApi Summary

**Login via supabase-js services, RequireAuth gated by VITE_USE_MOCKS, and meApi proof banner close AUTH-01/02/03 SPA contracts offline-green.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-09-19T15:22:34Z
- **Completed:** 2026-09-19T15:30:30Z
- **Tasks:** 3/3
- **Files modified:** 16

## Accomplishments

- Pure `emailDomain` helper (ADR-0003) with `node --test` (4 passed)
- LoginPage + authApi mock harness; RequireAuth + sanitized returnUrl
- meApi mock/live shapes; PlatformProofBanner on IssuePage for D-10 proof
- Playwright `tests/auth.spec.js` 6/6; web-app regression 14/14 under default mocks

## Task Commits

1. **Task 1 RED:** `a907a99` — `test(01-05): add failing test for corporate email domain helper`
2. **Task 1 GREEN:** `e7c54ff` — `feat(01-05): implement corporate email domain helper`
3. **Task 2 RED:** `13fa241` — `test(01-05): add failing Playwright auth contracts`
4. **Task 2 GREEN:** `e933e98` — `feat(01-05): implement SPA login, authApi, and RequireAuth`
5. **Task 3 RED:** `1b6c951` — `test(01-05): add failing tests for meApi, returnUrl, and login network UX`
6. **Task 3 GREEN:** `191b849` — `feat(01-05): add meApi client and platform proof banner`

**Plan metadata:** `bb39a5a` — `docs(01-05): complete SPA auth and meApi plan`

## Files Created/Modified

- `web/src/services/emailDomain.js` — corporate domain allowlist
- `web/src/services/supabaseClient.js` — sole createClient
- `web/src/services/authApi.js` / `authEnv.js` — sign-in session + mocks/returnUrl helpers
- `web/src/services/meApi.js` — Bearer GET /me + POST /me/ping
- `web/src/pages/LoginPage.jsx` — editorial login UX
- `web/src/components/RequireAuth.jsx` — auth gate
- `web/src/components/PlatformProofBanner.jsx` — FE↔API proof UI
- `tests/auth.spec.js` — Playwright auth contracts
- `playwright.config.js` — include auth.spec.js in web project

## Decisions Made

- Default mocks keep RequireAuth open; force-gate window flag for AUTH-03 SPA test without a second Vite project
- Mock meApi derives email from mock session after login
- Package `@supabase/supabase-js@2.116.0` installed per pre-approved legitimacy

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Expand Playwright web testMatch for auth.spec.js**
- **Found during:** Task 2
- **Issue:** `playwright.config.js` only matched `web-app.spec.js`, so `tests/auth.spec.js` would not run
- **Fix:** `testMatch: /(web-app|auth)\.spec\.js/`
- **Files modified:** `playwright.config.js`
- **Verification:** `npx playwright test --project=web tests/auth.spec.js`
- **Committed in:** `13fa241`

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** Necessary for verify; no scope creep.

## Issues Encountered

None beyond the testMatch gap above.

## User Setup Required

None for offline mock path. Live proof still needs `VITE_USE_MOCKS=false`, `VITE_SUPABASE_*`, `VITE_API_BASE_URL` (root `.env.example` from Plan 01).

## Next Phase Readiness

SPA auth + meApi ready. AUTH-03 admin-route 403 remains Phase 5. Wave sibling 01-04 live adapters can pair with `VITE_USE_MOCKS=false` for end-to-end platform proof.

## TDD Gate Compliance

- RED: `a907a99`, `13fa241`, `1b6c951`
- GREEN: `e7c54ff`, `e933e98`, `191b849`
- Gates satisfied for all three tasks.

## Test counts

- `node --test web/src/services/emailDomain.test.js` — **4 passed**
- `npx playwright test --project=web tests/auth.spec.js` — **6 passed**
- `npx playwright test --project=web tests/web-app.spec.js` — **14 passed** (regression)

## Self-Check: PASSED

- FOUND: web/src/services/supabaseClient.js
- FOUND: web/src/services/emailDomain.js
- FOUND: web/src/pages/LoginPage.jsx
- FOUND: web/src/components/RequireAuth.jsx
- FOUND: web/src/services/meApi.js
- FOUND: tests/auth.spec.js
- FOUND: a907a99, e7c54ff, 13fa241, e933e98, 1b6c951, 191b849
