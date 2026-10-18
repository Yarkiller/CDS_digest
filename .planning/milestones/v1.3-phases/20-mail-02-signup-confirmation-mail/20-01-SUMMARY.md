---
phase: 20-mail-02-signup-confirmation-mail
plan: 01
subsystem: auth
tags: [playwright, supabase-auth, register, autoconfirm, honest-copy, mail-02]

requires:
  - phase: 19-unsaved-changes-guard
    provides: stable SPA shell / auth routes for register coverage
provides:
  - "D-07 honest (B) CONFIRM_MESSAGE on null-session register"
  - "armSignUpWithoutSession one-shot mock harness + __DIGEST_AUTH_HARNESS__ export"
  - "D-09/D-10 Playwright post-register letter-claim forbid + honest-copy assert"
affects:
  - 20-mail-02-signup-confirmation-mail
  - 21-mail-01-live-smtp-digest

actuals:
  tokens: 867
  tasks: 2
  commits: 2

plan_head_before: 947e6692356622f4bba9f21b63deac64d67227e5
plan_head_after: 8c027f185acb6b19ab156bedcd56bea8e6931a7d

tech-stack:
  added: []
  patterns:
    - "One-shot Playwright auth harness arms (armFailNext* / armSignUpWithoutSession)"
    - "Null-session register → non-retryable ErrorPanel with CONFIRM_MESSAGE"

key-files:
  created: []
  modified:
    - tests/auth.spec.js
    - web/src/services/authApi.js
    - web/src/main.jsx
    - web/src/pages/RegisterPage.jsx

key-decisions:
  - "D-02: Ship path (B) honest autoconfirm copy this session; relay-proof deferred to Phase 21 via Plan 20-02"
  - "D-07/D-08: CONFIRM_MESSAGE lives only in RegisterPage; authApi error-mapping strings untouched"
  - "D-10: DOM harness armSignUpWithoutSession forces null session under VITE_USE_MOCKS"

patterns-established:
  - "armSignUpWithoutSession one-shot flag cleared in resetAuthHarness and on first mock signUp"
  - "Post-register honest-copy Playwright test arms harness then asserts role=alert + forbids /письм/i"

requirements-completed: [MAIL-02]

coverage:
  - id: D1
    description: "Null-session register shows D-07 honest (B) copy and stays on /register"
    requirement: MAIL-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#post-register copy never claims a confirmation letter"
        status: pass
    human_judgment: false
  - id: D2
    description: "Post-register alert never claims a confirmation letter was sent"
    requirement: MAIL-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#post-register copy never claims a confirmation letter (not.toContainText /письм/i)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Autoconfirm happy-path register still shows Логин as shell identity"
    requirement: MAIL-02
    verification:
      - kind: automated_ui
        ref: "tests/auth.spec.js#shows Логин as shell identity after register"
        status: pass
    human_judgment: false
  - id: D4
    description: "ADR-0003 corporate email domain tripwire preserved (zero edits)"
    requirement: MAIL-02
    verification:
      - kind: unit
        ref: "uv run pytest tests/unit/test_auth_email_domain.py -x"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-10-16
status: complete
---

# Phase 20 Plan 01: Honest (B) post-register copy Summary

**Null-session register path shows locked honest copy «Регистрация завершена. Аккаунт активен — войдите.» via `armSignUpWithoutSession` harness; letter-claim language forbidden by Playwright regression.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-10-16T08:35:16Z
- **Completed:** 2026-10-16T08:39:14Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Replaced dishonest confirmation-letter `CONFIRM_MESSAGE` with D-07 honest autoconfirm (B) copy in `RegisterPage.jsx` only.
- Added `armSignUpWithoutSession()` one-shot mock null session (authApi + `__DIGEST_AUTH_HARNESS__`) so Playwright can exercise the `!session` branch under `VITE_USE_MOCKS`.
- Amended `tests/auth.spec.js` with letter-claim forbid + honest-copy assert; preserved «shows Логин as shell identity after register».
- Domain unit tripwire `tests/unit/test_auth_email_domain.py` green with zero edits (D-11).

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end honest (B) copy** - `63da648` (test)
2. **Task 1 (GREEN): harness + CONFIRM_MESSAGE** - `8c027f1` (feat)
3. **Task 2: Prove happy path + domain tripwire** - verification-only (no code commit); Playwright 2/2 + pytest 5/5 passed

**Plan metadata:** `29a4e7b` (docs: complete plan)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## TDD Gate Compliance

- **RED:** `63da648` — target test failed with `armSignUpWithoutSession is not a function` before any production edit; evidence `20-01-tdd-red-evidence.json` verified `RED_EVIDENCE_OK` / `target_test_failed`.
- **GREEN:** `8c027f1` — harness + D-07 copy; filtered Playwright green.
- **REFACTOR:** none.

## Files Created/Modified

- `tests/auth.spec.js` — new `post-register copy never claims a confirmation letter` test (D-09/D-10)
- `web/src/services/authApi.js` — `armSignUpWithoutSession` + reset; error-mapping strings unchanged (D-08)
- `web/src/main.jsx` — expose arm on `__DIGEST_AUTH_HARNESS__`
- `web/src/pages/RegisterPage.jsx` — `CONFIRM_MESSAGE` → D-07 string; `!session` flow unchanged

## Decisions Made

- D-02: Path (B) honest autoconfirm copy ships this session; criterion-4 relay smoke proof remains Plan 20-02 / Phase 21.
- D-07/D-08: Copy constant only in RegisterPage; authApi AuthApiError / NETWORK strings byte-identical.
- D-10: DOM harness path chosen for null-session coverage under mocks.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — Vite 5174 flake precondition did not block Task 2 smoke.

## Verification Outcomes (Task 2)

```text
npx playwright test tests/auth.spec.js --project=web -g "shell identity after register|post-register copy|Регистрация завершена|confirmation letter"
→ 2 passed (shell identity + post-register copy)

uv run pytest tests/unit/test_auth_email_domain.py -x
→ 5 passed; git status shows no modification to that file
```

## User Setup Required

None - no external service configuration required for path (B) SPA copy. Relay SMTP ops remain Plan 20-02 / Phase 21.

## Next Phase Readiness

- Ready for Plan 20-02 (close g-01-3b diagnosis + runbook relay shape; criterion-4 gap → Phase 21).
- Full `tests/auth.spec.js --project=web` remains VALIDATION.md wave/phase gate (not required by this plan's Task 2 filter).

## Self-Check: PASSED

- FOUND: `tests/auth.spec.js`, `web/src/services/authApi.js`, `web/src/main.jsx`, `web/src/pages/RegisterPage.jsx`
- FOUND: commits `63da648`, `8c027f1`
- FOUND: `CONFIRM_MESSAGE` equals `Регистрация завершена. Аккаунт активен — войдите.`
- FOUND: `shows Логин as shell identity after register` still present
- FOUND: no edits to `tests/unit/test_auth_email_domain.py`

---
*Phase: 20-mail-02-signup-confirmation-mail*
*Completed: 2026-10-16*
