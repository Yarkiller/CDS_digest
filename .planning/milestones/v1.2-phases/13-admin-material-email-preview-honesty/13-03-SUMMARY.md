---
phase: 13-admin-material-email-preview-honesty
plan: 03
subsystem: ui
tags: [admin, material-preview, markdown, playwright, adux-01, react-markdown]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Enriched shortlist DTO fields (body_markdown, provenance_label, slug, counts) from Plan 13-01 backend
provides:
  - "AdminItemPreview title → provenance → counts → sanitized markdown → reader link"
  - "adminApi DEFAULT_ITEMS + __DIGEST_ADMIN_MATERIAL_EMPTY_BODY__ sticky mock"
  - "Playwright material preview honesty suite (populated + empty body)"
affects:
  - 13-04 Email preview iframe (FE)
  - 13-05 Ban scrub notes
  - Phase 14 draft→ready / score_factors (deferred; not introduced here)

actuals:
  tokens: 3086
  tasks: 2
  commits: 2
plan_head_before: dcc236ea0997f2eafb3331ece1f8b45ed06df6f9
plan_head_after: 3672bdd76c2bfe359802aa280a58620d9d8ce5f7

tech-stack:
  added: []
  patterns:
    - "Material modal reuses MaterialPage markdown stack (react-markdown + remark-gfm + rehype-sanitize + rehype-slug)"
    - "No fetch-on-open — modal reads enriched shortlist item only (D-01)"
    - "Honest empty body muted copy; provenance omitted when blank"

key-files:
  created: []
  modified:
    - tests/admin.spec.js
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx

key-decisions:
  - "Extract AdminItemPreview helper instead of growing inline modal JSX — same Phase 5 chrome, D-05 order only"
  - "Counts always rendered (including honest zeros); provenance row omitted when empty"
  - "Reader link rendered only when slug is non-empty"

patterns-established:
  - "Admin material preview: title → optional provenance → counts → Markdown|empty copy → «Открыть материал →»"
  - "Empty-body harness: sticky __DIGEST_ADMIN_MATERIAL_EMPTY_BODY__ zeros item[0] body/provenance/counts"

requirements-completed: [ADUX-01]

coverage:
  - id: D1
    description: "Populated material preview shows provenance, counts, markdown body text, and reader link without materials-by-id fetch"
    requirement: ADUX-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#material preview shows body_markdown provenance counts and reader link"
        status: pass
    human_judgment: false
  - id: D2
    description: "Empty body_markdown shows «Текст материала недоступен», honest zero counts, omits provenance, no toast; close remains visible"
    requirement: ADUX-01
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#material preview empty body shows Текст материала недоступен without toast"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-10-03
status: complete
---

# Phase 13 Plan 03: Material modal honesty UI Summary

**AdminItemPreview renders enriched shortlist markdown with provenance, counts, honest empty body, and reader link — Playwright green for ADUX-01 / D-04…D-06.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-10-03T06:37:12Z
- **Completed:** 2026-10-03T06:42:30Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Playwright material-preview honesty suite locks populated path (body/provenance/counts/link, no fetch-on-open) and empty-body path (muted copy, zero counts, provenance omitted, no toast).
- `adminApi` mocks expose all six additive shortlist fields plus `__DIGEST_ADMIN_MATERIAL_EMPTY_BODY__` sticky harness.
- `AdminItemPreview` matches MaterialPage markdown stack and UI-SPEC E1 order without redesigning digest chrome.

## Task Commits

1. **Task 1 (RED): FE mocks + AdminItemPreview markdown honesty** — `cf7de16` (test)
2. **Task 1 (GREEN) + Task 2 edges:** AdminItemPreview implementation covers empty provenance / zero counts / close visibility — `3672bdd` (feat)

**Plan metadata:** `43a3e98` (docs: complete plan)

_Note: Task 2 Playwright edge asserts landed in the RED commit; GREEN implementation satisfied both tasks without a separate task-2 production commit._

## Files Created/Modified

- `tests/admin.spec.js` — material preview honesty describe (populated + empty)
- `web/src/services/adminApi.js` — AdminShortlistItem typedef/mocks + empty-body sticky
- `web/src/pages/AdminDigestPage.jsx` — AdminItemPreview enriched layout + markdown

## Decisions Made

- Keep Phase 5 modal chrome (`aria-label="Закрыть"`, scrollable `max-h-[90vh]` panel); only replace stub title/dek body with D-05 stack.
- Discard incidental pre-resume refactor hunks in `AdminDigestPage.jsx` / `adminApi.js` — stage only plan-scoped honesty changes on a dirty tree.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Restored wiped uncommitted adminApi enrichment after accidental checkout**
- **Found during:** Task 1 (resume)
- **Issue:** Partial-state adminApi enrichment existed only in the working tree; `git checkout HEAD -- web/src/services/adminApi.js` to drop incidental refactor also removed the plan’s mock enrichment.
- **Fix:** Re-applied typedef, DEFAULT_ITEMS additive fields, reset harness clear, and sticky empty-body clone path from the captured partial diff.
- **Files modified:** `web/src/services/adminApi.js`
- **Commit:** `cf7de16`

**2. [Rule 2 - Missing critical] Discarded incidental AdminDigestPage refactor**
- **Found during:** Task 1 (resume)
- **Issue:** Dirty tree included a large component-extract refactor unrelated to material honesty.
- **Fix:** Restored `AdminDigestPage.jsx` from HEAD, then applied only AdminItemPreview + markdown imports.
- **Files modified:** `web/src/pages/AdminDigestPage.jsx`
- **Commit:** `3672bdd`

## TDD Gate Compliance

Plan frontmatter is `type: execute` with per-task `tdd="true"` (not `type: tdd`). RED verified intentionally:

| Gate | Evidence |
|------|----------|
| RED | Both material-preview tests failed on missing provenance / empty-body copy against stub UI; mocks present so failure is UI honesty, not fixture absence |
| GREEN | `npx playwright test --project=web tests/admin.spec.js -g "material preview"` → 2 passed |
| REFACTOR | None required |

## Known Stubs

None introduced by this plan. Empty-body copy «Текст материала недоступен» is intentional honesty UI (D-06), not a stub.

## Threat Flags

None beyond plan threat model. Markdown render uses rehype-sanitize (T-13-05 mitigated); no new npm packages (T-13-SC).

## Self-Check: PASSED

- FOUND: `tests/admin.spec.js`
- FOUND: `web/src/services/adminApi.js`
- FOUND: `web/src/pages/AdminDigestPage.jsx`
- FOUND: commit `cf7de16`
- FOUND: commit `3672bdd`
)
