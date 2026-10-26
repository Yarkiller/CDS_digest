---
phase: 13-admin-material-email-preview-honesty
plan: 04
subsystem: ui
tags: [admin, email-preview, iframe, playwright, adux-02, adux-03, sandbox]

requires:
  - phase: 13-admin-material-email-preview-honesty
    provides: Preview API additive html (Plan 13-02) + AdminItemPreview modal shell patterns (Plan 13-03)
provides:
  - "AdminEmailPreview sandboxed iframe (email-preview-frame, sandbox='', srcDoc=backend/mock html)"
  - "Playwright migrated off email-preview-body as honesty target (frameLocator)"
  - "Connecting-text + intro hint «Пустая строка = новый абзац»"
  - "Retry copy «Повторить превью»; D-86 fingerprint gate unchanged"
affects:
  - 13-05 Ban scrub / FIX-01 notes
  - Phase verify-work UAT for email iframe long-text backstops

actuals:
  tokens: 2813
  tasks: 2
  commits: 4
plan_head_before: 236336346e8db8a4b3904f799d0d03e386f297e6
plan_head_after: 7750cc9700304b28d1224abf309062c1cc9d7874

tech-stack:
  added: []
  patterns:
    - "Email honesty surface is sandboxed iframe srcDoc only — never dangerouslySetInnerHTML / FE HTML assembly"
    - "Mock preview html mirrors backend render_email_html shape for Playwright; live path uses API html"
    - "Interstitial editors expose muted Label-size paragraph hint without markdown toolbar"

key-files:
  created: []
  modified:
    - tests/admin.spec.js
    - web/src/services/adminApi.js
    - web/src/pages/AdminDigestPage.jsx

key-decisions:
  - "Keep secondary items <ul> under iframe for existing rank/title list asserts; honesty surface is iframe only"
  - "Missing preview.html shows «Превью недоступно» rather than falling back to plain body"
  - "Hint under both intro and connecting-text textareas (UI-SPEC E3 / D-15)"

patterns-established:
  - "Admin email preview: subject (Subhead) → sandboxed iframe → optional items list"
  - "Playwright email honesty: frameLocator('[data-testid=email-preview-frame]') + material title / Читать →"

requirements-completed: [ADUX-02, ADUX-03]

coverage:
  - id: D1
    description: "Successful preview renders sandboxed email-preview-frame with material title and Читать → from html"
    requirement: ADUX-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#email-preview-frame shows sandboxed backend HTML with material title"
        status: pass
    human_judgment: false
  - id: D2
    description: "Intro/interstitial composition honesty asserted inside iframe; D-86 unlock still requires successful preview"
    requirement: ADUX-02
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#G-05-1: intro + interstitial in Превью письма; send records Отправка записана"
        status: pass
    human_judgment: false
  - id: D3
    description: "Muted hint «Пустая строка = новый абзац» under intro and connecting-text; no markdown toolbar"
    requirement: ADUX-03
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#Пустая строка = новый абзац hint under intro and connecting text"
        status: pass
    human_judgment: false
  - id: D4
    description: "Long email subject wraps; long HTML scrolls via modal/iframe without clipping close"
    verification: []
    human_judgment: true
    rationale: "Plan must_haves mark long-text as backstop visual verification"
  - id: D5
    description: "Long connecting text wraps/scrolls in textarea; hint remains visible below"
    verification: []
    human_judgment: true
    rationale: "Plan must_haves mark long-text as backstop visual verification"

duration: 7min
completed: 2026-10-03
status: complete
---

# Phase 13 Plan 04: Email iframe + interstitial hint UI Summary

**Admin email preview displays backend/mock HTML in a fully sandboxed iframe; Playwright honesty moved to frameLocator; intro/connecting-text show paragraph-break hint.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-03T06:51:43Z
- **Completed:** 2026-10-03T06:57:20Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Replaced plain `email-preview-body` with `<iframe data-testid="email-preview-frame" sandbox="" srcDoc={html} />` (D-08/D-10; ADUX-02).
- Mock `previewEmail` returns composition-shaped `html` (titles, dek, Читать →); live path keeps API JSON including `html`.
- Playwright asserts material title / intro / interstitial order inside the frame; retry CTA is «Повторить превью»; D-86 fingerprint gate untouched.
- Intro + connecting-text editors show muted «Пустая строка = новый абзац» (D-15; ADUX-03).

## Task Commits

1. **Task 1 (RED): Sandboxed email HTML iframe + Playwright migration** — `0feaa9c` (test)
2. **Task 1 (GREEN):** iframe + mock html + retry copy — `ba84ed6` (feat)
3. **Task 2 (RED): Connecting-text paragraph hint** — `52d8b9f` (test)
4. **Task 2 (GREEN):** hint under intro + connecting text — `7750cc9` (feat)

**Plan metadata:** `9387c1d` (docs: complete plan)

## Files Created/Modified

- `tests/admin.spec.js` — frameLocator honesty suite + interstitial hint e2e; migrated off `email-preview-body`
- `web/src/services/adminApi.js` — mock `html` via `composeMockPreviewHtml`; typedef includes `html`
- `web/src/pages/AdminDigestPage.jsx` — sandboxed iframe preview; «Повторить превью»; paragraph hints

## Decisions Made

- Secondary items list retained under the iframe so existing rank/title list asserts stay green; honesty surface is exclusively the iframe.
- No FE HTML assembly from titles/deks in the SPA; mock HTML lives in `adminApi` only for Playwright.
- Hint on both intro and connecting-text per UI-SPEC E3 (both feed interstitial HTML).

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

Plan frontmatter is `type: execute` with per-task `tdd="true"`.

| Task | RED | GREEN | Evidence |
|------|-----|-------|----------|
| 1 Email iframe | `0feaa9c` | `ba84ed6` | `RED_EVIDENCE_OK` (`13-04-task1-red-evidence.json`) |
| 2 Interstitial hint | `52d8b9f` | `7750cc9` | `RED_EVIDENCE_OK` (`13-04-task2-red-evidence.json`) |

## Issues Encountered

- `npm run test:web -- … -g "…"` dropped `-g` under PowerShell; used `npx playwright test … --grep` for filtered runs.
- Pre-existing flaky/unrelated `/me network failure` test failed when the whole file ran without grep — out of scope; not fixed (Rule scope boundary).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Email iframe honesty + interstitial hint ready for verify-work / Phase 13-05 ban scrub.
- Long-text backstops (D4/D5) remain human judgment.

## Self-Check: PASSED

- FOUND: `web/src/pages/AdminDigestPage.jsx` (iframe + hints)
- FOUND: `web/src/services/adminApi.js` (mock html)
- FOUND: `tests/admin.spec.js` (frameLocator + hint)
- FOUND: commits `0feaa9c`, `ba84ed6`, `52d8b9f`, `7750cc9`

---
*Phase: 13-admin-material-email-preview-honesty*
*Completed: 2026-10-03*
