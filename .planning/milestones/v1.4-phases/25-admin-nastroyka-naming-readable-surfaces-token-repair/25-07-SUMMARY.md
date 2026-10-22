---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: "07"
subsystem: frontend
tags: [a11y, contrast, design-tokens, static-gates, playwright]
dependency-graph:
  requires: ["25-05", "25-06"]
  provides:
    - "field-border painted on all 16 controls (3:1 non-text boundary)"
    - "G-17 control-boundary gate + decorative-rule guard"
    - "G-19 usage-level accent label gate"
    - "single-fill ActionButton state model"
    - "theme-race-free gotoAdmin harness"
  affects:
    - web/src/components
    - web/src/pages
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js
tech-stack:
  added: []
  patterns:
    - "measured dual-theme assertion (computed colour -> contrastRatio, no literals)"
    - "mutually exclusive fill selection for stateful buttons"
key-files:
  created: []
  modified:
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js
    - web/src/components/ActionButton.jsx
    - web/src/components/IngestSourcesSection.jsx
    - web/src/components/IngestionScheduleSection.jsx
    - web/src/components/AdminLayout.jsx
    - web/src/components/SearchPill.jsx
    - web/src/pages/LoginPage.jsx
    - web/src/pages/RegisterPage.jsx
    - web/src/pages/KnowledgePage.jsx
    - web/src/pages/AdminDigestPage.jsx
    - web/src/pages/AdminPipelineConfigPage.jsx
decisions:
  - "gotoAdmin waits for data-theme only when the page actually mounts the theme toggle — the auth shell mounts none, so an unconditional wait would hang /login."
  - "ActionButton keeps stateFill.loading empty and dims through an additive stateChrome map: a truthy loading fill would strip the variant fill mid-flight and regress must_have #13."
  - "G-17 pins the 16 controls plus four exact decorative class lists; field-border on a non-control literal fails, so the boundary and divider roles cannot drift back together."
metrics:
  duration: 19m
  tasks: 2
  files: 12
  completed: 2026-10-21
status: complete
actuals:
  tokens: 9257
  tasks: 2
  commits: 2
---

# Phase 25 Plan 07: Control boundary and accent label Summary

`field-border` now paints the edge of all 16 form controls at ≥ 3:1, link labels ride `accent-text` at ≥ 4.5:1, `ActionButton` paints exactly one fill per state, and `gotoAdmin` no longer asserts a theme it may not have reached.

## Performance

- **Duration:** 19 min
- **Started:** 2026-10-21T17:12Z
- **Completed:** 2026-10-21T17:31Z
- **Tasks:** 2 (one TDD cycle: RED + GREEN)
- **Files modified:** 12

## Accomplishments

- **GAP-25-3 closed.** The retry-upload link and the preview link carry `text-accent-text` (`#0E7490` light / `#06B6D4` dark) instead of `text-accent`. Measured on the painted ancestor: retry link 2.428 → **5.358** (light), **7.248** (dark); preview link **5.121** light on `bg-app`, **7.900** dark on `bg-base`.
- **GAP-25-4 closed.** All 16 controls (8 inputs/selects/textarea in the ingest and schedule sections, 2 on `AdminLayout`, 2 in `LoginPage`, 3 in `RegisterPage`, 1 in `SearchPill`, 1 in `AdminDigestPage`, 1 in `AdminPipelineConfigPage`, plus the `AdminDigestPage` checkbox) carry `border-field-border`. Both the schedule `select` and the digest `input` now match `rgb(100, 116, 139)` in both themes. Boundary went from **1.233** (light `rule` `#E2E8F0` on white) and **1.554** (dark `rule` `#2A3548` on `#0B0F17`) to **4.759** / **4.030**. Card edges, row dividers and the preview frame stay on `border-rule` and measure **1.233** / **1.554** — deliberately below the 3:1 floor the tests assert they do *not* meet.
- **G-17 added** (control boundary): pins the control count at 16, requires `border-field-border` on every one, and fails if `field-border` appears on any of the four decorative literals. **G-19 added** (accent label): forbids `text-accent` on a text-bearing element and requires `text-accent-text`; carries a proof case that a bare `text-accent` fails and that `text-accent-text` passes. Run: **89/89 unit tests green** (G-0…G-19, canon 51/13 unchanged).
- **WR-03 closed.** `ActionButton` resolves its fill once (`variantClass` when no state fill, `stateFill[state]` when there is one) instead of concatenating both. The vote button's class list is now `["bg-voting", …]` in idle, hover, focus, active, disabled and loading — the former `["bg-voting", "bg-danger-solid"]` yellow-over-red race (1.918:1) is gone.
- **WR-04 closed.** `gotoAdmin` now awaits `(document.documentElement.dataset.theme ?? 'dark') === theme` before returning, so every light-theme assertion in this plan reads a settled page. The wait is skipped on pages without the toggle (`/login`, `/register`), which mounts no theme switch — so the auth routes do not hang.
- **Verification:** `npm run test:js` 89/89; `npx playwright test tests/admin-chrome.spec.js --project=web` 11/11; `npx playwright test tests/admin.spec.js --project=web` 88/88; `npm run build` exit 0.

## Task Commits

Each task was committed atomically:

1. **Task 1: control-boundary and accent-label gates + computed-colour proofs (RED)** — `40191a0` (test)
2. **Task 2: field boundary on every control, accent label role, single-fill button, theme-race fix (GREEN)** — `716bdfe` (feat)

**Plan metadata:** committed with this SUMMARY (`docs(25-07)`).

## Files Created/Modified

- `tests/unit/test_semantic_token_coverage.js` — G-17/G-19 gates plus `controlTags()`, `readJsxOpeningTag()`, `controlBoundaryOffences()`, `decorativeBoundaryOffences()`, `accentLabelOffences()`, and four proof tests.
- `tests/admin-chrome.spec.js` — `gotoAdmin` theme wait (WR-04), `paintedPair` ancestor climb, and three computed-colour cases (links, control boundary vs decorative rule, single button fill).
- `web/src/components/ActionButton.jsx` — mutually exclusive `variantClass` / `stateFill` with additive `stateChrome` (WR-03).
- `web/src/components/IngestSourcesSection.jsx` — retry link `text-accent-text`; 3 controls on `field-border`.
- `web/src/components/IngestionScheduleSection.jsx` — link `text-accent-text`; schedule `select` on `field-border`.
- `web/src/components/AdminLayout.jsx` — 2 controls on `field-border`.
- `web/src/components/SearchPill.jsx` — search input on `field-border`.
- `web/src/pages/LoginPage.jsx` — 2 controls on `field-border`.
- `web/src/pages/RegisterPage.jsx` — 3 controls on `field-border`.
- `web/src/pages/KnowledgePage.jsx` — search input on `field-border`.
- `web/src/pages/AdminDigestPage.jsx` — preview URL input, seed textarea and checkbox on `field-border`; one `text-accent` link corrected.
- `web/src/pages/AdminPipelineConfigPage.jsx` — config input on `field-border`.

## Decisions Made

- **Theme wait is conditional.** `gotoAdmin` awaits the `data-theme` write only where the toggle is mounted; the auth shell has no toggle, so waiting there would time out on a signal that never arrives.
- **Loading keeps its fill.** `stateFill.loading` is empty and the `cursor-wait opacity-80` chrome lives in a separate additive map. The plan's literal `stateFill.loading = 'cursor-wait opacity-80'` would have made `hasStateFill` true and dropped `bg-voting` while the upload is in flight — a regression of 25-VERIFICATION #13 ("in-flight keeps its colour").
- **Roles are pinned by class, not by intent.** G-17 enumerates the four decorative literals it expects; adding `field-border` to any of them (or dropping a control) fails, so "the divider was promoted to a control boundary" cannot pass silently.
- **Thresholds are imported.** The new e2e cases read `TEXT_CONTRAST` / `NON_TEXT_CONTRAST` from the token gate, so lowering a floor in one place is caught by the other.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ActionButton lost its fill while loading**
- **Found during:** Task 2 (the RED case asserted one fill in *every* state, loading included)
- **Issue:** The plan's `stateFill.loading = 'cursor-wait opacity-80'` is truthy, so the planned `Boolean(stateFill[state])` guard would replace `bg-voting` with chrome classes only — the in-flight button would go transparent, contradicting 25-VERIFICATION #13.
- **Fix:** `stateFill.loading = ''` (variant fill preserved) and the dimming chrome moved to a separate additive `stateChrome` map. The guard expression is exactly the plan's.
- **Files modified:** `web/src/components/ActionButton.jsx`
- **Commit:** `716bdfe`

**2. [Rule 3 - Blocking] Dev server died between the RED and GREEN Playwright runs**
- **Found during:** Task 2 verification
- **Issue:** The first post-GREEN `admin-chrome` run failed with `net::ERR_CONNECTION_REFUSED` on `127.0.0.1:5174` — a stale dev-server lifecycle, not a product failure.
- **Fix:** Confirmed the port was free, then re-ran; Playwright started its own server and the suite passed 11/11. No code change.
- **Files modified:** none

## Issues Encountered

- JSX opening tags that contain arrow functions (`onChange={(e) => …}`) broke the naive tag scanner: the `>` in `=>` looked like the end of the tag. `readJsxOpeningTag()` now tracks brace depth and quote state, so a control is never silently skipped by the gate.

## User Setup Required

None — no external service configuration required.

## Known Stubs

None.

## Threat Flags

None. No new network surface, auth path, or schema change; the changes are class strings and test-only helpers.

## Next Phase Readiness

- Phase 25 is complete: the seven plans are done and all four must-have gaps (25-3, 25-4) plus WR-03/WR-04 are closed.
- `WINDOWS.md` gained no new entries for this plan.
- The gates G-17/G-19 are now part of `npm run test:js`, so any future control or label added without the right token fails the suite rather than the eye.

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- All 12 files listed under `key-files.modified` exist on disk.
- Both task commits resolve in `git log --oneline --all`: `40191a0` (RED) and `716bdfe` (GREEN).
- `npm run test:js` — 89/89; `tests/admin-chrome.spec.js` — 11/11; `tests/admin.spec.js` — 88/88; `npm run build` — exit 0.
