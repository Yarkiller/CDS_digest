---
phase: 01-platform-foundation-auth
plan: 07
subsystem: auth
tags: [spa-auth, signup, register, playwright, g-01-3, plat-07]

requires:
  - phase: 01-platform-foundation-auth
    provides: LoginPage + authApi signIn/meApi display-name (Plan 01-05); UAT G-01-3 diagnosis
provides:
  - authApi.signUp (mock + live supabase.auth.signUp via publishable client)
  - Public /register RegisterPage with Логин nickname
  - Slim /login (email+password only); Регистрация → /register
  - Playwright G-01-3 + register domain/empty/returnUrl/network contracts
affects:
  - Phase 1 UAT G-01-3 closure
  - COVERAGE signUp INTEGRATE (amend D-08)
  - Live Supabase Auth (email confirm may leave user without session)

actuals:
  tokens: 7344
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - Self-service signUp only through web/src/services/authApi (publishable client)
    - Display nickname (Логин) collected on /register; persisted via meApi + updateAuthDisplayName
    - Register harness mirrors login: getSignUpInvocationCount + armFailNextSignUp

key-files:
  created:
    - web/src/pages/RegisterPage.jsx
  modified:
    - web/src/services/authApi.js
    - web/src/pages/LoginPage.jsx
    - web/src/App.jsx
    - web/src/main.jsx
    - tests/auth.spec.js
    - .planning/phases/01-platform-foundation-auth/COVERAGE.md

key-decisions:
  - "Логин is display nickname on /register only; login is email+password (operator G-01-3 / amend D-08)"
  - "signUp via publishable supabase-js; never service_role in web/"
  - "If live signUp returns user without session (email confirm), ErrorPanel stays on /register — no admin confirm APIs"

patterns-established:
  - "Public auth routes: /login and /register siblings outside RequireAuth"
  - "auth-sign-up-calls data-testid mirrors auth-sign-in-calls for domain-gate proofs"

requirements-completed: [AUTH-01, AUTH-02, PLAT-07]

coverage:
  - id: D1
    description: "Регистрация on /login navigates to /register"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#Регистрация on login navigates to /register"
        status: pass
    human_judgment: false
  - id: D2
    description: "Login form is email + password only (no Имя/Логин)"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#login form is email and password only"
        status: pass
    human_judgment: false
  - id: D3
    description: "Register Логин becomes shell identity after signUp"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#shows Логин as shell identity after register"
        status: pass
    human_judgment: false
  - id: D4
    description: "Register corporate domain gate rejects without signUp"
    requirement: AUTH-01
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#rejects disallowed email domain on register without signUp"
        status: pass
    human_judgment: false
  - id: D5
    description: "Empty Логин blocks register without signUp"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#blocks empty Логин on register without signUp"
        status: pass
    human_judgment: false
  - id: D6
    description: "Register honors returnUrl after success"
    requirement: AUTH-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#returns to returnUrl path after successful register"
        status: pass
    human_judgment: false
  - id: D7
    description: "Register surfaces retryable network ErrorPanel + Повторить"
    requirement: PLAT-07
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#shows retryable network banner when signUp fails"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-19
status: complete
---

# Phase 01 Plan 07: Registration UX (G-01-3) Summary

**Self-service `/register` with Логин nickname, slim email+password login, and Playwright contracts closing UAT gap G-01-3.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-19T19:21:46Z
- **Completed:** 2026-09-19T19:28:30Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Working «Регистрация» CTA → `/register` with email, password, and «Логин»
- Login no longer collects display name; nickname persists on register via `meApi` + Auth metadata
- Corporate domain gate + empty Логин + returnUrl + PLAT-07 network Retry on register; `tests/auth.spec.js` 13/13 green

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end self-service register** — `1f521bb` (test) → `0a2a648` (feat)
2. **Task 2: Register domain gate + returnUrl + empty Логин** — `a3dc9f6` (test) → `ad454a8` (feat)
3. **Task 3: Register network failure ErrorPanel + Retry** — `9f79235` (test; feat already in Task 1)

**Plan metadata:** `b87fc16` (docs: complete plan)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified

- `web/src/pages/RegisterPage.jsx` — registration UX (Логин, domain gate, ErrorPanel)
- `web/src/services/authApi.js` — `signUp`, harness counters / `armFailNextSignUp`
- `web/src/pages/LoginPage.jsx` — email+password only; Link to `/register`
- `web/src/App.jsx` — public `/register` route
- `web/src/main.jsx` — expose `armFailNextSignUp` on harness
- `tests/auth.spec.js` — G-01-3 + register edge contracts
- `.planning/phases/01-platform-foundation-auth/COVERAGE.md` — signUp → INTEGRATE

## Decisions Made

- Nickname field labeled «Логин» with helper that it is a voting display nickname (not ФИО)
- Live signUp without session → Russian confirm-email message; stay on `/register`
- Threat mitigations T-01-07-01/02 applied: domain gate before signUp; publishable client only

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Domain gate, empty Логин, returnUrl, and network ErrorPanel shipped in Task 1 RegisterPage**
- **Found during:** Task 1 (threat model T-01-07-01 / PLAT-07 parity)
- **Issue:** Thin happy-path RegisterPage would omit AUTH-01 UI gate and PLAT-07 Retry if deferred blindly
- **Fix:** Implemented gates + ErrorPanel in Task 1; Task 2/3 locked with Playwright (Task 3 RED passed immediately — contract lock only)
- **Files modified:** `web/src/pages/RegisterPage.jsx`, `web/src/services/authApi.js`, `web/src/main.jsx`
- **Commit:** `0a2a648` (impl); `9f79235` (Task 3 lock test)

## TDD Gate Compliance

- Task 1: RED `1f521bb` → GREEN `0a2a648` ✓
- Task 2: RED `a3dc9f6` → GREEN `ad454a8` ✓
- Task 3: locking test only (`9f79235`); no separate feat — behavior already green from Task 1 (documented deviation)

## Issues Encountered

None blocking. Interactive tracer human-verify skipped because plan `autonomous: true` and orchestrator required full PLAN COMPLETE; tracer `<verify>` re-run green before expansion.

## User Setup Required

None.

## Next Phase Readiness

- G-01-3 code truths hold under mocks; optional live UAT re-check with `VITE_USE_MOCKS=false` if email confirm is enabled on VM
- STATE/ROADMAP updates owned by orchestrator (not this executor)

## Known Stubs

None.

## Self-Check: PASSED

- FOUND: `web/src/pages/RegisterPage.jsx`
- FOUND: `web/src/services/authApi.js` (`signUp`)
- FOUND: commits `1f521bb`, `0a2a648`, `a3dc9f6`, `ad454a8`, `9f79235`
- FOUND: `npx playwright test tests/auth.spec.js` → 13 passed
