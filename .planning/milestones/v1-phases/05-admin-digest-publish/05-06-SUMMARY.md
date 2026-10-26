---
phase: 05-admin-digest-publish
plan: 06
subsystem: testing
tags: [playwright, pytest, admin-digest, honesty-gate, returnUrl, tdd]

requires:
  - phase: 05-admin-digest-publish
    provides: AdminDigestPage SPA + live adapters + stub mailer + migration 005
provides:
  - Expanded tests/admin.spec.js honesty suite (403, empty, top-N, preview fail/success, draft block, send, already-sent)
  - ADMIN-08 returnUrl /issues/{n} + sanitize open-redirect in auth.spec.js
  - Post-send «К выпуску →» CTA from issue_url (D-90)
  - 05-VALIDATION.md Wave 0 complete + File Exists green map
affects:
  - gsd-verify-work Phase 5 UAT
  - milestone ship gate

actuals:
  tokens: 20963
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Playwright admin harness flags + exact:true for multi-strip RU copy"
    - "ADMIN-08 reuses sanitizeReturnUrl same-origin paths only (T-05-20)"
    - "Success banner keeps Отправка записана as exact text node beside issue Link"

key-files:
  created:
    - .planning/phases/05-admin-digest-publish/05-06-SUMMARY.md
  modified:
    - tests/admin.spec.js
    - tests/auth.spec.js
    - web/src/pages/AdminDigestPage.jsx
    - .planning/phases/05-admin-digest-publish/05-VALIDATION.md
    - docs/agents/local-platform-runbook.md
    - tests/unit/test_http_knowledge_search.py

key-decisions:
  - "D-90 SPA: surface sendDigest.issue_url as «К выпуску →» after Отправка записана"
  - "ADMIN-08 e2e via auth.spec returnUrl=/issues/13; open-redirect // rejected to /"
  - "nyquist_compliant left false for validate-phase; wave_0_complete true"

patterns-established:
  - "Pattern: phase honesty gate = pytest -q + admin.spec.js under mocks"
  - "Pattern: cite ADMIN + D-* IDs in Playwright describe headers"

requirements-completed: [ADMIN-01, ADMIN-04, ADMIN-06, ADMIN-07, ADMIN-08]

coverage:
  - id: D1
    description: "Employee deep-link /admin/digest shows 403 Недостаточно прав + На выпуск (D-77)"
    requirement: ADMIN-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#employee deep-link /admin/digest shows 403 Недостаточно прав"
        status: pass
    human_judgment: false
  - id: D2
    description: "Empty shortlist honesty + no пайплайн; loading never flashes empty success"
    requirement: ADMIN-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#empty shortlist shows Кандидатов пока нет without пайплайн"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#loading shortlist does not flash empty success"
        status: pass
    human_judgment: false
  - id: D3
    description: "Select-all / top-3 checkbox ops (ADMIN-06)"
    requirement: ADMIN-06
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#Выбрать все and Оставить топ-3 update checkboxes"
        status: pass
    human_judgment: false
  - id: D4
    description: "Preview fail keeps send locked; success unlocks; draft blocks; send success + already-sent"
    requirement: ADMIN-04
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#preview failure keeps send locked"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#approved draft blocks send with draft hint (ADMIN-03/07, D-85)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#превью unlocks send; confirm records Отправка записана + issue link (D-90)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#Уже отправлено when batch already sent"
        status: pass
    human_judgment: false
  - id: D5
    description: "ADMIN-08 returnUrl /issues/{n} after login; sanitize rejects // open redirects (D-90, T-05-20)"
    requirement: ADMIN-08
    verification:
      - kind: e2e
        ref: "tests/auth.spec.js#ADMIN-08 / D-90: returnUrl /issues/{n} lands on published issue after login"
        status: pass
      - kind: e2e
        ref: "tests/auth.spec.js#sanitizeReturnUrl rejects protocol-relative open redirects"
        status: pass
      - kind: unit
        ref: "tests/unit/test_stub_mailer.py"
        status: pass
    human_judgment: false
  - id: D6
    description: "05-VALIDATION.md Wave 0 complete; File Exists ✅ for phase test map"
    verification:
      - kind: other
        ref: ".planning/phases/05-admin-digest-publish/05-VALIDATION.md#wave_0_complete"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 06: Honesty E2E Gate + VALIDATION Summary

**Phase 5 honesty gate: Playwright covers 403/empty/top-N/preview/send/draft + ADMIN-08 returnUrl; VALIDATION Wave 0 marked complete; stub send surfaces «К выпуску →».**

## Performance

- **Duration:** 12min
- **Started:** 2026-09-21T15:38:59Z
- **Completed:** 2026-09-21T15:55:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Expanded `tests/admin.spec.js` to prove D-77 403, D-80 empty, ADMIN-06 top-N, preview fail gate, draft-in-pool block, zero-one-many preview counts, send success/already-sent, in-flight Approve disable
- ADMIN-08 / D-90: `auth.spec.js` returnUrl `/issues/13` + open-redirect rejection; SPA success CTA to `/issues/15`
- Refreshed `05-VALIDATION.md` (`wave_0_complete: true`, File Exists ✅); runbook §4e links admin Playwright gate

## Task Commits

Each task was committed atomically (TDD RED → GREEN for Task 1):

1. **Task 1 RED:** `3509b40` — test(05-06): expand admin honesty suite failing checks
2. **Task 1 GREEN:** `a090e52` — feat(05-06): surface issue link after stub send
3. **Task 2:** `21f778b` — chore(05-06): refresh VALIDATION map and phase gate

**Plan metadata:** `44d2d6b` (docs: complete honesty e2e gate plan)

## Files Created/Modified
- `tests/admin.spec.js` — full Phase 5 honesty e2e suite under mocks
- `tests/auth.spec.js` — ADMIN-08 returnUrl + sanitizeReturnUrl open-redirect
- `web/src/pages/AdminDigestPage.jsx` — post-send «К выпуску →» from `issue_url`
- `.planning/phases/05-admin-digest-publish/05-VALIDATION.md` — Nyquist map refresh
- `docs/agents/local-platform-runbook.md` — §4e Playwright honesty gate cross-link
- `tests/unit/test_http_knowledge_search.py` — StubMailer on AppContainer helper

## Decisions Made
- Wire D-90 issue CTA on success banner (UI-SPEC) rather than returnUrl-only proof
- Leave `nyquist_compliant: false` for `/gsd-validate-phase`; set `wave_0_complete: true`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Post-send issue link CTA**
- **Found during:** Task 1 (honesty suite RED)
- **Issue:** UI-SPEC / D-90 require success CTA to published `/issues/{n}`; SPA only showed banner text
- **Fix:** Store `sendDigest.issue_url` and render «К выпуску →» Link beside «Отправка записана»
- **Files modified:** `web/src/pages/AdminDigestPage.jsx`
- **Verification:** admin.spec.js send success test green
- **Committed in:** `a090e52`

**2. [Rule 3 - Blocking] Knowledge HTTP tests missing mailer**
- **Found during:** Task 2 (`uv run pytest -q` phase gate)
- **Issue:** `_seeded_container` omitted required `mailer=` after Phase 5 AppContainer change → 4 failures
- **Fix:** Pass `StubMailer()` into AppContainer
- **Files modified:** `tests/unit/test_http_knowledge_search.py`
- **Verification:** 225 passed
- **Committed in:** `21f778b`

---

**Total deviations:** 2 auto-fixed (1× Rule 2, 1× Rule 3)
**Impact on plan:** Required for D-90 honesty and phase verify gate; no scope creep.

## Issues Encountered
None beyond deviations above.

## User Setup Required
None - no external service configuration required. Live admin promote remains optional per runbook §4e.

## Next Phase Readiness
Phase 05 plans 01–06 complete. Ready for `/gsd-verify-work` on Admin Digest Publish. Optional live FE↔BE under `VITE_USE_MOCKS=false` remains human ops.

## TDD Gate Compliance
- RED `test(05-06)` commit `3509b40` present (failed on missing issue link)
- GREEN `feat(05-06)` commit `a090e52` present after RED
- No separate refactor commit (minimal span change only)

## Self-Check: PASSED
- FOUND: `tests/admin.spec.js`, `tests/auth.spec.js`, `05-VALIDATION.md`, AdminDigestPage issue CTA
- FOUND commits: `3509b40`, `a090e52`, `21f778b`

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
