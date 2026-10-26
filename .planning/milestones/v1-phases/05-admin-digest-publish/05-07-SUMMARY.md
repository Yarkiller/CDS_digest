---
phase: 05-admin-digest-publish
plan: 07
subsystem: ui
tags: [fastapi, react, playwright, preview, digest, composition, TDD]

requires:
  - phase: 05-admin-digest-publish
    provides: Admin shortlist triage + preview/send gate (05-06) and approved∩ready pool
provides:
  - Preview composition use-case (intro + ordered material/text blocks → preview.body)
  - HTTP DigestPreviewRequest on POST /admin/shortlist/preview
  - adminApi + AdminDigestPage wiring so «Вводный текст» reaches «Превью письма»
  - Playwright intro-in-preview gate (G-05-1)
affects: [05-08-block-reorder-ui, digest-send-composition]

actuals:
  tokens: 9200
  tasks: 3
  commits: 5

tech-stack:
  added: []
  patterns:
    - Pure FE composition helpers in adminPreviewComposition.js (node --test friendly)
    - SPA posts intro/blocks; modal renders preview.body alongside items

key-files:
  created:
    - web/src/services/adminPreviewComposition.js
    - tests/unit/test_admin_preview_composition.js
  modified:
    - backend/src/backend/application/use_cases/preview_digest_email.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/domain/errors.py
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx
    - tests/unit/test_preview_digest.py
    - tests/unit/test_http_admin.py
    - tests/admin.spec.js

key-decisions:
  - "Default blocks = approved∩ready by rank until 05-08 reorder UI"
  - "Extracted adminPreviewComposition.js so node --test avoids Vite import.meta"
  - "Email modal shows preview.body (intro visible) and keeps items list for existing D-86/D-90 tests"

patterns-established:
  - "Preview composition: intro + [{kind:material|text}] → body; items[] from material blocks only"
  - "UI calls only adminApi; page builds default material blocks via pure helper"

requirements-completed: [ADMIN-04, ADMIN-03]

coverage:
  - id: D1
    description: preview_digest_email composes intro + ordered blocks into body; invalid material → 400
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/unit/test_preview_digest.py"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py"
        status: pass
    human_judgment: false
  - id: D2
    description: SPA posts intro/blocks and renders composed preview.body in «Превью письма»
    requirement: ADMIN-04
    verification:
      - kind: unit
        ref: "tests/unit/test_admin_preview_composition.js"
        status: pass
      - kind: automated_ui
        ref: "tests/admin.spec.js#Вводный текст appears in Превью письма (G-05-1 / ADMIN-04)"
        status: pass
    human_judgment: false
  - id: D3
    description: Existing preview unlock / send / already-sent admin contracts remain green
    requirement: ADMIN-03
    verification:
      - kind: automated_ui
        ref: "tests/admin.spec.js"
        status: pass
    human_judgment: false

duration: 25min
completed: 2026-09-21
status: complete
---

# Phase 05 Plan 07: Preview Composition Spine Summary

**Intro and ordered blocks reach `preview.body` end-to-end — «Вводный текст» is visible in «Превью письма» (G-05-1).**

## Performance

- **Duration:** ~25min (Task 1 prior wave + Tasks 2–3 resume)
- **Started:** 2026-09-21T18:26:27Z (resume)
- **Completed:** 2026-09-21T18:31:00Z
- **Tasks:** 3/3
- **Files modified:** 10

## Accomplishments

- Backend `preview_digest_email` accepts `intro` + ordered `material`/`text` blocks; HTTP `DigestPreviewRequest` on preview; invalid composition → 400; `sent_at` untouched (D-86).
- SPA: `adminApi.previewEmail` serializes composition; mock builds body from intro/blocks; `AdminDigestPage` sends `contextText` + default rank-ordered material blocks and renders `preview.body`.
- Playwright proves a unique intro phrase appears in the letter preview dialog; 15/15 admin.spec.js green.

## Task Commits

Each task was committed atomically:

1. **Task 1: Preview composition use-case + HTTP body** — `dc14c06` (test) → `d7e9e0e` (feat)
2. **Task 2: adminApi + AdminDigestPage pass intro/blocks** — `a34d5bd` (test) → `cee255d` (feat)
3. **Task 3: Playwright — intro appears in letter preview** — `145ddf3` (test)

**Plan metadata:** `737920b` (docs: complete plan)

## Files Created/Modified

- `backend/src/backend/application/use_cases/preview_digest_email.py` — composition inputs + body order
- `backend/src/backend/interface/http/routes/admin.py` — DigestPreviewRequest
- `backend/src/backend/domain/errors.py` — InvalidPreviewCompositionError
- `web/src/services/adminPreviewComposition.js` — pure buildDefaultMaterialBlocks / composePreviewBody
- `web/src/services/adminApi.js` — previewEmail(composition) mock + live JSON
- `web/src/pages/AdminDigestPage.jsx` — openEmailPreview wires intro/blocks; modal body region
- `tests/unit/test_preview_digest.py` / `test_http_admin.py` — composition contracts
- `tests/unit/test_admin_preview_composition.js` — FE pure helpers
- `tests/admin.spec.js` — intro-in-preview Playwright gate

## Decisions Made

- Default material order remains approved∩ready by rank; reorder/insert UI deferred to 05-08.
- Pure FE composition module (not inlined in adminApi) so `node --test` works without Vite env.
- Modal keeps items `<ul>` for existing tests and adds `data-testid="email-preview-body"` for intro visibility.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] Pure composition module for node:test**
- **Found during:** Task 2 (RED)
- **Issue:** Importing `adminApi.js` under `node --test` pulls authApi → supabaseClient → `import.meta.env` crash (same class as knowledgeApi).
- **Fix:** Added `web/src/services/adminPreviewComposition.js` with pure helpers; adminApi re-exports and uses them.
- **Files modified:** `adminPreviewComposition.js`, `adminApi.js`, `test_admin_preview_composition.js`
- **Verification:** `node --test tests/unit/test_admin_preview_composition.js` — 3 passed
- **Committed in:** `a34d5bd` / `cee255d`

**Total deviations:** 1 auto-fixed (Rule 2)
**Impact on plan:** Necessary for TDD/verify under node; no scope creep into 05-08.

## Issues Encountered

None beyond the node:test import boundary (handled above). Tracer human-verify for Task 1 was approved before resume.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

G-05-1 composition spine closed for default-ordered path. Ready for 05-08 (reorder/insert block UI) and remaining gap-closure plans. Do not weaken ADMIN-04/D-86/D-90 assertions.

## Self-Check: PASSED

- FOUND: `web/src/services/adminPreviewComposition.js`
- FOUND: `tests/unit/test_admin_preview_composition.js`
- FOUND: `05-07-SUMMARY.md` (this file)
- FOUND commits: `dc14c06`, `d7e9e0e`, `a34d5bd`, `cee255d`, `145ddf3`

---
*Phase: 05-admin-digest-publish*
*Completed: 2026-09-21*
