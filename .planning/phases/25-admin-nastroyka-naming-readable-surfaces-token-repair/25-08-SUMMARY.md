---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: "08"
subsystem: frontend
tags: [a11y, contrast, design-tokens, static-gates, playwright]
requirements-completed: [THEME-02]
dependency-graph:
  requires: ["25-07"]
  provides:
    - "--color-primary-text label role (dark #A78BFA / light #6D28D9)"
    - "G-20 primary-label gate + G-20 proof test"
    - "36 text-primary literals migrated to text-primary-text"
    - "pipeline retry e2e (both themes, computed colour)"
  affects:
    - web/src/index.css
    - web/src/components
    - web/src/pages
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js
tech-stack:
  added: []
  patterns:
    - "label/fill role separation: --color-primary stays fill/border/ring/tint, --color-primary-text is the label"
    - "token-exact class comparison via classTokens — text-primary is a substring of text-primary-text"
    - "measured dual-theme assertion (computed colour -> contrastRatio, no literals)"
key-files:
  created: []
  modified:
    - web/src/index.css
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js
    - web/src/components/ActionButton.jsx
    - web/src/components/AppShell.jsx
    - web/src/components/ChronologyItem.jsx
    - web/src/components/EditorialCallout.jsx
    - web/src/components/IssueToc.jsx
    - web/src/components/MaterialListRow.jsx
    - web/src/pages/AdminDigestPage.jsx
    - web/src/pages/AdminPipelineConfigPage.jsx
    - web/src/pages/ArchivePage.jsx
    - web/src/pages/ForbiddenPage.jsx
    - web/src/pages/IssuePage.jsx
    - web/src/pages/KnowledgePage.jsx
    - web/src/pages/LoginPage.jsx
    - web/src/pages/MaterialPage.jsx
    - web/src/pages/ProfilePage.jsx
    - web/src/pages/RazborPage.jsx
    - web/src/pages/RazboryListPage.jsx
    - web/src/pages/RegisterPage.jsx
    - web/src/pages/VotingPage.jsx
decisions:
  - "The base --color-primary stays byte-identical (#8B5CF6) as fill/border/ring/tint (D-05); only the label role moves to the theme-dependent --color-primary-text (#A78BFA dark / #6D28D9 light)."
  - "G-20 scans className string literals token-exact, never substrings: text-primary-text, text-text-primary, bg-primary, border-primary and outline-primary are all non-offenders, so the gate cannot self-trigger on its own fix."
  - "The save-retry background is assembled from tokens via blendOver(--color-danger, --color-bg-app, 0.1) because getComputedStyle serializes bg-danger/10 to oklab(…/0.1), which parseColor refuses."
metrics:
  duration: 12m
  tasks: 3
  files: 22
  completed: 2026-10-21
status: complete
actuals:
  tokens: 8015
  tasks: 3
  commits: 4
  plan_head_before: 43397f038f88a70348fd5fe7dad6435ebdd67b22
  plan_head_after: bc9653a42029c184ab0f68f42714ff157bf0e00f
---

# Phase 25 Plan 08: primary label role and 36-literal migration Summary

The base `--color-primary` no longer paints any label: a separate theme-dependent role `--color-primary-text` (`#A78BFA` dark / `#6D28D9` light) now carries all 36 primary text literals across 19 files, and gate `G-20` forbids `text-primary` as a label role.

## Performance

- **Duration:** 12 min
- **Started:** 2026-10-21T22:06Z (RED commit)
- **Completed:** 2026-10-21T22:16Z (final migration commit)
- **Tasks:** 3 (one TDD cycle: RED → GREEN part 1 → GREEN part 2)
- **Files modified:** 22 (19 components/pages + `index.css` + 2 test files)
- **Commits:** 4 (RED, GREEN part 1, test-isolation fix, GREEN part 2)

## Accomplishments

- **GAP-25-5 / GC-2 / WR-07 closed.** `--color-primary-text` is declared once in `@theme static` (`#A78BFA`) and once under `[data-theme="light"]` (`#6D28D9`); the base `--color-primary: #8B5CF6` is untouched (D-05).
- **36 literals migrated** in 19 files (35 `className` sites + the `ActionButton.jsx:35` JSDoc mention) from `text-primary` / `hover:text-primary` to `text-primary-text` / `hover:text-primary-text`. Zero standalone `text-primary` remain in `web/src`; `text-text-primary` stays at 34 lines and `text-accent-text` stays at 3 sites.
- **G-20 added** (primary is not a label role): scans `web/src/**/*.{js,jsx}` string literals for `text-primary`, `hover:text-primary`, `text-primary/<n>`; asserts zero offenders. Its proof test pins both directions (`text-primary`, `hover:text-primary`, `text-primary/80` fail; `text-primary-text`, `text-text-primary`, `bg-primary`, `border-primary`, `outline-primary` pass). RED reproduced exactly 36 offenders (35 className + 1 JSDoc).
- **e2e case added** (`pipeline retry actions are legible in both themes`): asserts the *computed* colour of both retry buttons in both themes and the contrast on their painted/token-assembled surfaces.
- **Verification:** `npm run test:js` 91/91 (G-0…G-20 + proof + canon 51/13 unchanged); `npx playwright test tests/admin-chrome.spec.js --project=web` 12/12; `npx playwright test tests/admin.spec.js --project=web` 88/88; `npm run build` exit 0.

## Contrast — before / after

Base `#8B5CF6` (before) vs new role `#A78BFA` dark / `#6D28D9` light (after), flat pairs over the three surfaces:

| Surface | dark before | dark after | light before | light after |
|---|---|---|---|---|
| `bg-app` (`#0B0F17` / `#F8FAFC`) | 4.529 ✓ | **7.048** | 4.047 ✗ | **6.791** |
| `paper` (`#131925` / `#FFFFFF`) | 4.156 ✗ | **6.466** | 4.234 ✗ | **7.105** |
| `paper-2` (`#1A2233` / `#F1F5F9`) | 3.756 ✗ | **5.844** | 3.865 ✗ | **6.485** |

Worst of the six flat pairs is `#A78BFA` on `paper-2` = **5.844** (margin 1.344); best is `#6D28D9` on `paper` = **7.105**. On the `bg-primary/15` tint the worst base is again `paper-2`: **4.934** dark / **5.430** light (margin 0.434) — both above the 4.5 floor.

The two buttons that drove the gap, measured in-browser:

| Button | surface | before | after |
|---|---|---|---|
| `pipeline-config-retry` | `bg-app` | 4.047 light / 4.529 dark | **6.791** light / **7.048** dark |
| `pipeline-config-save-retry` | `bg-danger/10` | 3.566 light / 4.186 dark | **5.984** light / **6.513** dark |

## Coverage (migration map, 36 literals in 19 files)

| File | literals | File | literals |
|---|---|---|---|
| `ActionButton.jsx` | 2 (1 className + 1 JSDoc) | `IssuePage.jsx` | 2 |
| `AppShell.jsx` | 2 | `KnowledgePage.jsx` | 1 |
| `ChronologyItem.jsx` | 1 | `LoginPage.jsx` | 1 |
| `EditorialCallout.jsx` | 1 | `MaterialPage.jsx` | 7 |
| `IssueToc.jsx` | 1 | `ProfilePage.jsx` | 1 |
| `MaterialListRow.jsx` | 1 | `RazborPage.jsx` | 3 |
| `AdminDigestPage.jsx` | 5 | `RazboryListPage.jsx` | 1 |
| `AdminPipelineConfigPage.jsx` | 2 | `RegisterPage.jsx` | 1 |
| `ArchivePage.jsx` | 2 | `VotingPage.jsx` | 1 |
| `ForbiddenPage.jsx` | 1 | | |

## Mutation check (G-20)

Reverting `AdminPipelineConfigPage.jsx:242` (`pipeline-config-retry`) to `text-primary` makes `npm run test:js` fail on `G-20: primary is not a label role — use text-primary-text: web/src/pages/AdminPipelineConfigPage.jsx: text-primary`. Reverting restores 91/91 green. The gate is proven non-vacuous.

## Task Commits

Each task committed atomically:

1. **Task 1: G-20 gate + pipeline retry e2e (RED)** — `c770512` (test): `THEMED`/`UTILITY_PATTERN` gain `primary-text`; `PRIMARY_LABEL`, `PRIMARY_LABEL_OFFENDERS`, `primaryLabelOffences()`; `G-20` + proof; e2e case. Fails on 36 offenders / missing token.
2. **Task 2: declare `--color-primary-text` (GREEN part 1)** — `76f92cb` (feat): two declarations in `index.css`; G-1/G-2 green, G-4 red as "declared but unused".
3. **Task 3: migrate 36 literals (GREEN part 2)** — `bc9653a` (feat): token-exact replacement across 19 files.

**Plan metadata:** committed with this SUMMARY (`docs(25-08)`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Pipeline retry e2e failed on test isolation, not on the token**
- **Found during:** Task 3 verification (first `admin-chrome` run: 11/12, new case failed)
- **Issue:** `armFailNextLoad()` is sessionStorage-backed and never cleared by `fetchPipelineConfig` (unlike `armFailNextSave`, which deletes itself after one consume). Branch A armed the load failure and left it sticky, so Branch B's `gotoAdmin` re-landed on the load-error shell and the config editor / `ingest-sources-section` never mounted.
- **Fix:** Reset `window.__DIGEST_PIPELINE_CONFIG_HARNESS__.resetPipelineConfigHarness()` before Branch B's `gotoAdmin`.
- **Files modified:** `tests/admin-chrome.spec.js`
- **Commit:** `b925d82`

## Issues Encountered

- The `text-primary` → `text-primary-text` replacement had to be token-exact: a plain substring replace would produce `text-text-primary-text` and `bg-primary-text`. The migration was driven by a negative-lookaround regex `(?<![\w-])text-primary(?![\w-])` and verified with the same pattern (0 results after, 36 before).

## User Setup Required

None — no external service configuration required.

## Known Stubs

None.

## Threat Flags

None. No new network surface, auth path, or schema change; the changes are CSS tokens, class strings, static-analysis gates, and test helpers. Threat model T-25-24…T-25-28 mitigations (className-scoped scanning, token-exact grep verification, computed-colour assertions) all landed.

## Next Phase Readiness

- The four previously closed gates stay green: labels on fills 5.201…11.007 (G-9), toast 16.296/14.516 (G-15), accent links 5.358/7.248 (G-17), field boundary 4.759/3.698 vs 3.0 floor (G-18).
- Canon `51 / 13` unchanged; `G-4` anti-vacuum sees `primary-text` in use.
- `WINDOWS.md` gained no new entries for this plan.

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- All 22 files listed under `key-files.modified` exist on disk.
- All four commits resolve in `git log`: `c770512` (RED), `76f92cb` (GREEN part 1), `b925d82` (test fix), `bc9653a` (GREEN part 2).
- `npm run test:js` — 91/91; `tests/admin-chrome.spec.js` — 12/12; `tests/admin.spec.js` — 88/88; `npm run build` — exit 0.
- Mutation check confirmed G-20 fails on `text-primary` and recovers on revert.
