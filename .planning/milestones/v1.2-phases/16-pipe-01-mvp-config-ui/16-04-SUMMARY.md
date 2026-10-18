---
phase: 16-pipe-01-mvp-config-ui
plan: 04
subsystem: web
tags: [react, vite, playwright, pytest, pipeline-config, ports-and-adapters, boundary-guard]

# Dependency graph
requires:
  - phase: 16-pipe-01-mvp-config-ui
    plan: 01
    provides: pipelineConfigApi.js transport boundary, AdminPipelineConfigPage tracer shell, admin/pipeline route, GET/PUT config routes
  - phase: 16-pipe-01-mvp-config-ui
    plan: 02
    provides: server 400 top-level {"errors":[...]} reject payload consumed by the page error panel
  - phase: 13-admin-material-email-preview-honesty
    provides: AdminDigestPage role-gate/load-state chrome + window.confirm disposition reused by the pipeline page
provides:
  - Complete AdminPipelineConfigPage surface (empty/dirty/reset/status/load-error + validation-error panel + save-failure retry)
  - pipelineConfigApi.js 400 -> INVALID_CONFIG mapping + sessionStorage-backed mock harness arms
  - Admin-gated «Пайплайн» NavLink in AppShell.jsx
  - window.__DIGEST_PIPELINE_CONFIG_HARNESS__ exposure in main.jsx
  - PIPE-03 static-source storage-boundary guard in tests/unit/test_http_pipeline_config.py
affects: [16 verification, PIPE-EXEC-* v1.3 execution UI]

# Actuals (#2632) — chars/4 over the realized diff, same scale as the plan estimate.
actuals:
  tokens: 4989
  tasks: 2
  commits: 4

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "sessionStorage-backed mock control arms (armFailNextLoad persists across reload; save arms consume once)"
    - "Static-source boundary guard asserting SPA storage coupling cannot leak into a component"
    - "beforeunload unsaved-changes guard using window.confirm for the exact UI-SPEC copy"

key-files:
  created: []
  modified:
    - web/src/pages/AdminPipelineConfigPage.jsx
    - web/src/services/pipelineConfigApi.js
    - web/src/components/AppShell.jsx
    - web/src/main.jsx
    - tests/admin.spec.js
    - tests/unit/test_http_pipeline_config.py

key-decisions:
  - "Mock harness arms live in sessionStorage (not module scope) so armFailNextLoad survives page.reload() — required to arm an initial-load failure before mount; save arms are consumed once so retry can succeed"
  - "The page performs no client-side YAML validation: only a server INVALID_CONFIG reject opens the error panel, and the document stays dirty (D-03/D-07)"
  - "aria-invalid is driven by the rejected flag (not error count) so a reject with no structured errors still marks the editor"
  - "Existing digest no-«пайплайн» assertions were scoped to the digest page content because the new global «Пайплайн» nav item legitimately adds that word to the shell"
  - "window.__DIGEST_PIPELINE_CONFIG_HARNESS__ was exposed in Task 1 (plan scheduled it for Task 2) so Task 1's Playwright verify could pass"

patterns-established:
  - "Page error contract: data-testid=pipeline-config-errors role=alert with one pipeline-config-error row per server error, prefix Строка {line}: / {path}: else none, server message verbatim"
  - "Honest reject: keep the document editable + dirty, clear stale errors on the next edit"

requirements-completed: [PIPE-01, PIPE-02, PIPE-03]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "Empty state (no saved config) renders the locked copy + placeholder with Save disabled; typing sets dirty and enables Save + «Отменить изменения»; status caption «Изменений нет»/«Сохранение…»/«Сохранено»"
    requirement: PIPE-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config empty state shows the locked copy and a disabled Save"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config dirty gating enables Save and reset on edit"
        status: pass
    human_judgment: false
  - id: D2
    description: "Reset («Отменить изменения») confirms with the exact copy «Отменить изменения и вернуть последнюю сохранённую версию?» and reverts to the last saved value; Cancel keeps the edit; unsaved-leave guard uses the exact copy «Есть несохранённые изменения. Уйти без сохранения?»"
    requirement: PIPE-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config reset confirm reverts to the last saved version"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config reset confirm cancel keeps the edit"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config dirty gating arms the unsaved-leave guard"
        status: pass
    human_judgment: false
  - id: D3
    description: "Load failure renders «Не удалось загрузить конфиг» with retry testid pipeline-config-retry; retry after reset recovers"
    requirement: PIPE-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config load error shows retry and recovers after reset"
        status: pass
    human_judgment: false
  - id: D4
    description: "Reject renders every structured server error (Строка {line}/ {path}) verbatim in role=alert, falls back to «Конфиг не прошёл проверку», keeps the document dirty, sets aria-invalid, and clears stale errors on edit"
    requirement: PIPE-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config validation renders every server error row and keeps the document dirty"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config validation falls back to a single generic string when the reject has no structured errors"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config validation clears stale errors on edit"
        status: pass
    human_judgment: false
  - id: D5
    description: "Save failure (network/5xx) renders «Конфиг не сохранён» with a pipeline-config-save-retry control; retry can succeed and show «Сохранено»"
    requirement: PIPE-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config save failure shows a retry control and can succeed"
        status: pass
    human_judgment: false
  - id: D6
    description: "The «Пайплайн» nav item to /admin/pipeline renders only for admin, and no banned execution control string renders on the page"
    requirement: PIPE-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config nav item renders only for admin"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config nav item hidden for employee"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config no execution controls render"
        status: pass
    human_judgment: false
  - id: D7
    description: "PIPE-03 boundary: AdminPipelineConfigPage imports the service, neither page nor service imports a supabase module, and only the service composes /admin/pipeline/config"
    requirement: PIPE-03
    verification:
      - kind: unit
        ref: "tests/unit/test_http_pipeline_config.py#test_pipeline_page_reaches_storage_only_through_service_no_supabase"
        status: pass
    human_judgment: false
  - id: D8
    description: "Overflow/long-text backstops: long YAML scrolls inside the editor, the Save toolbar stays reachable, error rows wrap with break-words"
    verification: []
    human_judgment: true
    rationale: "Backstop visual truths (overflow/long-text) are not asserted by an automated test; the editor uses min-h-[20rem]/max-h-[60vh] overflow-auto and error rows use break-words, but a verifier must confirm at real widths"

# Metrics
duration: 20min
completed: 2026-10-04
status: complete
commits: 4
plan_head_before: c576465a71633861ee2accb547f664d7ade2bd6c
plan_head_after: 4239f0f22b791ec91b0cb051c43191de29d79f3d
---

# Phase 16 Plan 04: Complete SPA pipeline-config surface with honest reject/save-failure states and a storage-boundary guard

**The admin pipeline page now renders its locked empty/dirty/reset/status states and every server validation error verbatim while keeping the rejected document dirty, shows honest save failures with retry, gates the «Пайплайн» nav on admin, and proves via a static guard that the SPA reaches storage only through `pipelineConfigApi.js`.**

## Performance

- **Duration:** 20 min
- **Started:** 2026-10-04T11:08:00Z
- **Completed:** 2026-10-04T11:28:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- `AdminPipelineConfigPage` completed per the approved UI-SPEC: `pipeline-config-empty` block with the locked copy + placeholder, clean/dirty gating, `pipeline-config-reload` reset with the exact confirm copy, `beforeunload` unsaved-changes guard, `pipeline-config-status` caption, and the load-error retry
- The 400 reject path renders one `pipeline-config-error` row per structured server error (`Строка {line}: `/`{path}: ` prefix, message verbatim) inside a `role="alert"` panel with the «Проверьте конфиг перед сохранением» heading, falls back to «Конфиг не прошёл проверку», sets `aria-invalid`, and clears stale errors on edit — the document is never auto-reverted (D-07)
- Save failure shows «Конфиг не сохранён» with `pipeline-config-save-retry`; the retry can succeed and show «Сохранено»
- `pipelineConfigApi.js` maps 400 → `INVALID_CONFIG` (retryable false, `errors` array) and exposes the sessionStorage-backed harness arms; `main.jsx` exposes `window.__DIGEST_PIPELINE_CONFIG_HARNESS__`
- `AppShell.jsx` gains the admin-gated «Пайплайн» NavLink; the page ships no run/trigger/scheduler control
- PIPE-03 boundary guard added and green: page imports the service, neither page nor service imports Supabase, only the service composes `/admin/pipeline/config`

## Task Commits

Each task ran the RED→GREEN cycle and was committed atomically:

1. **Task 1: SPA validation-error panel, reject mapping, save-failure UX, PIPE-03 guard** — `032eddf` (test RED), `26446db` (feat GREEN)
2. **Task 2: Page completeness — empty/dirty/reset/nav/no-execution** — `4cbb360` (test RED), `4239f0f` (feat GREEN)

_Note: no REFACTOR commit was needed — the GREEN implementations were already minimal._

## Files Created/Modified
- `web/src/pages/AdminPipelineConfigPage.jsx` — empty block, dirty gating, reset + confirm, beforeunload guard, validation-error panel, save-failure retry, aria-invalid
- `web/src/services/pipelineConfigApi.js` — 400 `INVALID_CONFIG` mapping (already present) plus `armRejectNextSave`/`armFailNextSave`/`armFailNextLoad`/`resetPipelineConfigHarness` sessionStorage arms
- `web/src/components/AppShell.jsx` — admin-gated «Пайплайн» NavLink
- `web/src/main.jsx` — `window.__DIGEST_PIPELINE_CONFIG_HARNESS__` exposure
- `tests/admin.spec.js` — 13 Playwright cases (validation/save-failure + empty/dirty/reset/nav/no-execution); two digest no-«пайплайн» assertions scoped to the digest page
- `tests/unit/test_http_pipeline_config.py` — `test_pipeline_page_reaches_storage_only_through_service_no_supabase` boundary guard

## Decisions Made
- Harness arms persist in `sessionStorage`: `armFailNextLoad` must survive `page.reload()` (arming an initial-load failure before mount), and it persists until reset; `armRejectNextSave`/`armFailNextSave` are consumed once so the retry path can succeed. Module-scope arms would be wiped by the reload.
- No client-side YAML validation: only a server `INVALID_CONFIG` reject opens the panel; a reject keeps the document dirty (D-03/D-07, T-16-16).
- `aria-invalid` is driven by a `rejected` flag so a reject carrying no structured errors still marks the editor.
- The new global «Пайплайн» nav item required scoping two pre-existing digest no-«пайплайн» assertions to `admin-digest-page` (their intent — the digest page content never mentions pipeline — is preserved).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Exposed the pipeline-config harness in Task 1**
- **Found during:** Task 1 (GREEN)
- **Issue:** Task 1's Playwright tests call `window.__DIGEST_PIPELINE_CONFIG_HARNESS__`, but the plan scheduled the `main.jsx` exposure in Task 2. Without it Task 1's `<verify>` could not pass.
- **Fix:** Added the import + `window.__DIGEST_PIPELINE_CONFIG_HARNESS__` assignment in `web/src/main.jsx` as part of Task 1's GREEN.
- **Files modified:** `web/src/main.jsx`
- **Verification:** `npm run test:web -- tests/admin.spec.js` → 50 passed
- **Committed in:** `26446db` (Task 1 GREEN)

**2. [Rule 1 - Bug] Scoped two digest no-«пайплайн» assertions to the digest page**
- **Found during:** Task 2 (GREEN verification)
- **Issue:** The new global «Пайплайн» nav item made `page.getByText(/пайплайн/i)` on `/admin/digest` match the shell nav, breaking the two empty-shortlist tests that assert the digest page never mentions pipeline (D-80).
- **Fix:** Scoped both assertions to `page.getByTestId("admin-digest-page").getByText(/пайплайн/i)` — the digest page content still must not mention pipeline.
- **Files modified:** `tests/admin.spec.js`
- **Verification:** `npm run test:web -- tests/admin.spec.js` → 50 passed
- **Committed in:** `4239f0f` (Task 2 GREEN)

---

**Total deviations:** 2 auto-fixed (1 blocking ordering fix, 1 bug from the new nav item)
**Impact on plan:** Both fixes are required for the plan's own verification to pass; neither adds product scope beyond PIPE-01/PIPE-02/PIPE-03.

## Issues Encountered
- `npm run test:web -- tests/admin.spec.js -g "pipeline config"` did not honor the `-g` title filter through npm on Windows PowerShell (the full file ran). Resolved by running the full `tests/admin.spec.js` (50 passed), which is a superset of the filtered selection.
- The pre-existing `react(set-state-in-effect)` oxlint warning remains on the load effect (same pattern as `AdminDigestPage`); oxlint exits 0.

## Threat Flags

None — no new trust boundary. The nav item links an existing `require_admin`-gated route, and the mock harness arms are test-only (reachable only under `isMocksEnabled()`). T-16-15 (no secret rendered), T-16-16 (no client accept), and T-16-17 (admin nav gate) are implemented and asserted.

## Known Stubs

None. The mock harness arms are test-only controls, not production stubs.

## User Setup Required

None - no external service configuration required (live migration `011` is 16-03's `user_setup`).

## Next Phase Readiness
- The SPA pipeline-config surface is complete per `16-UI-SPEC.md`; 16-04 depends on 16-03's live adapter only for live-mode behaviour, which mock-mode Playwright does not exercise.
- PIPE-03 remains unmarked in REQUIREMENTS.md until 16-03's SUMMARY exists (shared-ID gate), even though this plan's PIPE-03 boundary guard is green.
- Full backend suite: **757 passed**. Full `tests/admin.spec.js`: **50 passed**.

### Verification results
- `uv run pytest tests/unit/test_http_pipeline_config.py -q` → **11 passed**
- `uv run pytest -q` → **757 passed**
- `npm run test:web -- tests/admin.spec.js` → **50 passed** (includes all 13 pipeline-config cases)

---
*Phase: 16-pipe-01-mvp-config-ui*
*Completed: 2026-10-04*

## Self-Check: PASSED
