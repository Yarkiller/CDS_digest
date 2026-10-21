---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 06
subsystem: ui
tags: [tailwind-v4, design-tokens, contrast, playwright, static-gates, tdd]

# Dependency graph
requires:
  - phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
    provides: "25-05 declared --color-success-ink / --color-voting-ink-on-tint / --color-danger-ink / --color-field-border and exported blendOver for tint composites"
provides:
  - "Every status label under web/src paints an -ink role; no text-success / text-voting / text-danger survives as a label (G-18)"
  - "admin-toast moved onto the alias family (border-rule / bg-paper-2 / text-ink): 16.296 light, 14.516 dark"
  - "G-10 enforced with no carve-out; G-16 spec-contract gate on the existing status literals"
  - "Computed-colour e2e proof in both themes for status pills, auth errors, send banner and the toast"
affects: [25-07-admin-chrome-wr-03-wr-04, verify-work, ui-review]

actuals:
  tokens: 7370
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Status token = fill only; its label is always the -ink role (usage-level gate G-18)"
    - "Feedback chrome is drawn from the alias family (paper-2 / rule / ink), never from a 'solid' token pair"
    - "Tint contrast is measured on the composite via blendOver(token, surface, alpha), both statically and in the browser"

key-files:
  created:
    - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-06-SUMMARY.md
  modified:
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js
    - web/src/pages/AdminDigestPage.jsx
    - web/src/pages/AdminPipelineConfigPage.jsx
    - web/src/pages/LoginPage.jsx
    - web/src/pages/RegisterPage.jsx
    - web/src/pages/VotingPage.jsx
    - web/src/pages/KnowledgePage.jsx
    - web/src/components/ErrorPanel.jsx

key-decisions:
  - "Migrated all 18 label sites to the -ink roles rather than raising the base status tokens: the fills stay as the brand colours, only the label moves to the legible role"
  - "The toast became an alias-family surface (bg-paper-2 + border-rule + text-ink) instead of a one-off colour, so G-6/G-10 stay meaningful"
  - "G-18 scans exact class tokens (stringLiterals + tokenSet), so text-success-ink / text-voting-ink-on-tint are not false positives"
  - "G-16 only asserts literals that the harness can actually render; the send-failure banner ('Рассылка не отправлена') has no injector and is deliberately not invented"

patterns-established:
  - "G-18: a status token may fill, never label — the gate names file + exact token"
  - "G-16: one assertion per outcome, and admin-toast must be read by computed colour"
  - "e2e theme settlement: pages with a ThemeToggle wait for data-theme; the auth shell writes it explicitly"

requirements-completed: [PIPEUI-02, THEME-02]

coverage:
  - id: D1
    description: "18 status label sites paint text-success-ink / text-voting-ink-on-tint / text-danger-ink, and G-18 rejects the base tokens as labels"
    requirement: PIPEUI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-18: a status token is a fill, never a label"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-18 proof: the label scan rejects the base token and accepts the -ink roles"
        status: pass
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#status labels legible in both themes"
        status: pass
    human_judgment: false
  - id: D2
    description: "admin-toast is an alias-family surface (border-rule / bg-paper-2 / text-ink) above 4.5:1 in both themes, and the bg-text-primary carve-out is gone from G-10"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-10: no theme-dependent veil survives under web/src"
        status: pass
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#failure toast legible"
        status: pass
    human_judgment: false
  - id: D3
    description: "G-16 enforces one assertion per status outcome and requires admin-toast to be read by computed colour"
    requirement: PIPEUI-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-16: the status contract holds across the e2e specs"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-16 proof: one assertion per outcome, and the toast is read by colour"
        status: pass
    human_judgment: false
  - id: D4
    description: "Auth field errors and the send banner are legible in both themes (computed colour + contrast on the painted surface)"
    requirement: THEME-02
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#auth field errors legible"
        status: pass
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#send banner legible"
        status: pass
    human_judgment: false

duration: 21min
completed: 2026-10-21
status: complete
---

# Phase 25 Plan 06: Status Labels on `-ink` Roles and a Legible Admin Toast Summary

Every status label in `web/src` now paints an `-ink` role, the invisible admin toast became an alias-family surface, and two new static gates (G-18, G-16) keep both from regressing.

## Performance

- **Duration:** 21 min
- **Started:** 2026-10-21T19:45:00+03:00
- **Completed:** 2026-10-21T20:06:00+03:00
- **Tasks:** 3
- **Files modified:** 9

## Accomplishments

- Migrated all 18 status label sites (`text-success` / `text-voting` / `text-danger`) to `text-success-ink` / `text-voting-ink-on-tint` / `text-danger-ink` across 7 components; the fills (`bg-success/15`, `bg-voting/20`, `bg-danger/10`) are untouched.
- Fixed the 1.00:1 admin toast: `bg-text-primary` + `text-text-primary` → `border border-rule bg-paper-2 text-ink`, measured **16.296:1** light / **14.516:1** dark.
- Removed the `if (token === 'bg-text-primary') continue` carve-out from G-10, so the veil scan now covers all of `web/src` with no exception path.
- Added G-18 (usage-level label-role scan) and its proof, plus G-16 (status-assert contract across `*.spec.js`) and its proof.
- Added four computed-colour Playwright cases covering status pills, auth errors, the send banner and the toast in both themes.

## Measured contrast (before → after)

| Surface | Theme | Before | After |
|---|---|---|---|
| success pill on its 15% tint | light | 2.001 (`#22C55E`) | **6.262** (`#166534`) |
| success pill on its 15% tint | dark | 5.966 | **7.801** (`#4ADE80`) |
| voting pill on its 20% tint | light | 1.686 (`#EAB308`) | **7.621** (`#713F12`) |
| voting pill on its 20% tint | dark | 6.116 | **9.419** (`#FDE68A`) |
| auth field error on the card | light | 3.763 (`#EF4444`) | **6.470** (`#B91C1C`) |
| auth field error on the card | dark | 4.676 | **6.361** (`#F87171`) |
| send banner on the page shell | light | 2.279 | **7.130** (`#166534`) |
| admin toast (bg vs text) | light | 1.000 | **16.296** |
| admin toast (bg vs text) | dark | 1.000 | **14.516** |

Thresholds unchanged: 4.5 for text, 3.0 for non-text. Ratios are computed with `contrastRatio` / `blendOver` from `tests/helpers/contrast.js`, never hard-coded in the gates.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED — G-18, G-16 and the G-10 carve-out removal** - `2f699c3` (test)
2. **Task 2: RED — four computed-colour e2e cases** - `e3fe0e2` (test)
3. **Task 3: GREEN — 18 label sites + the toast** - `6d2c353` (feat)

**Plan metadata:** (docs: complete 25-06 plan)

## RED evidence

`npm run test:js` before any component edit (commit `2f699c3`):

- `G-10: no theme-dependent veil survives under web/src` — `web/src/pages/AdminDigestPage.jsx: bg-text-primary`
- `G-18: a status token is a fill, never a label` — 18 offenders, e.g. `web/src/pages/LoginPage.jsx: text-danger`
- `G-16: the status contract holds across the e2e specs` — `tests/*.spec.js: no spec checks admin-toast, so the 1.00:1 toast stays unproven`

`npx playwright test tests/admin-chrome.spec.js --project=web` before the component edit (commit `e3fe0e2`):

- `status labels legible in both themes` — expected `rgb(74, 222, 128)`, received `rgb(34, 197, 94)` (dark)
- `auth field errors legible` — expected `rgb(248, 113, 113)`, received `rgb(239, 68, 68)` (dark)
- `send banner legible` — expected `rgb(74, 222, 128)`, received `rgb(34, 197, 94)` (dark)
- `failure toast legible` — background `rgb(241, 245, 249)` equals the text colour instead of `rgb(26, 34, 51)` (dark)

## Files Created/Modified

- `tests/unit/test_semantic_token_coverage.js` — G-10 carve-out removed; `FORBIDDEN_STATUS_LABELS` + `statusLabelOffences` + G-18 and proof; `STATUS_LITERALS` + `REGEX_ASSERTION` + `literalsCoveredBy` + `literalIsAsserted` + `statusContractOffences` + G-16 and proof.
- `tests/admin-chrome.spec.js` — `waitForTheme`, `forceTheme`, `styleTriple`, `cssToken` helpers; four new cases (`status labels legible in both themes`, `auth field errors legible`, `send banner legible`, `failure toast legible`).
- `web/src/pages/AdminDigestPage.jsx` — status pills `:717-718`, banner `:770`, toast `:808`.
- `web/src/pages/AdminPipelineConfigPage.jsx` — two error panels: `border-danger` → `border-danger-ink/60`, all five labels → `text-danger-ink`.
- `web/src/pages/LoginPage.jsx` (3), `web/src/pages/RegisterPage.jsx` (4), `web/src/pages/VotingPage.jsx` (2), `web/src/pages/KnowledgePage.jsx` (1), `web/src/components/ErrorPanel.jsx` (1) — label roles.

## Decisions Made

- Fill tokens stay as-is (`--color-success` / `--color-voting` / `--color-danger`); only the label moved to the `-ink` role. Raising the fills would have changed the pills' brand appearance beyond the gap.
- The toast takes the alias family (`bg-paper-2` + `border-rule` + `text-ink`) rather than a new dedicated toast token, matching the 25-UI-SPEC surface ladder and keeping G-6 (`bg-ink`/`bg-paper` banning) intact.
- G-18 matches complete class tokens via `stringLiterals`/`tokenSet`, so `text-success-ink` and `text-voting-ink-on-tint` never trip it, while `text-danger/70` does.
- G-16 asserts only literals the harness can actually render: `'Выпуск опубликован'` and `'Уже отправлено'` for the send banner, `'Не сохранено'` for the toast; `'Рассылка не отправлена'` has no failure injector in the admin harness, so it is registered but not demanded.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The auth case could not reach its light-theme branch**
- **Found during:** Task 3 (GREEN verification of `tests/admin-chrome.spec.js`).
- **Issue:** `web/src/pages/LoginPage.jsx` mounts no `ThemeToggle`, so nothing writes `data-theme` on `/login` and the shared `waitForTheme(page, theme)` helper timed out after 30s on the light iteration. The RED run had stopped earlier, on the dark colour assertion, which is why the gap only surfaced once the dark theme turned green.
- **Fix:** Added a `forceTheme(page, theme)` helper that writes/removes `document.documentElement["data-theme"]` exactly as `ThemeToggle.jsx:12-15` does and then waits for it; the auth case uses it instead of `waitForTheme`. `gotoAdmin` itself and WR-04 stay untouched (WR-04 belongs to 25-07).
- **Files modified:** `tests/admin-chrome.spec.js`
- **Verification:** `npx playwright test tests/admin-chrome.spec.js --project=web` → 8 passed; light-theme colour now asserted as `rgb(185, 28, 28)` = 6.470.
- **Committed in:** `6d2c353` (part of the GREEN commit).

---

**Total deviations:** 1 auto-fixed (1 Rule 1).
**Impact on plan:** Test-harness correctness only; no production behaviour beyond the plan's scope and no threshold weakened.

## Issues Encountered

The `admin.spec.js` run takes ~3.7 min (88 tests) and `npm run build` reports a pre-existing 849 kB chunk-size warning and two `INEFFECTIVE_DYNAMIC_IMPORT` notices — both pre-date this plan and are untouched.

## Verification

- `npm run test:js` → 85/85 pass, G-0…G-18 incl. both new gates and their proofs; canon `canonDark` 51 / `canonLight` 13 unchanged.
- `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` → 8 passed.
- `npx playwright test tests/admin.spec.js --project=web --reporter=line` → 88 passed.
- `npm run build` → exit 0.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 25-07 (WR-03 `ActionButton` duplicate fill, WR-04 `gotoAdmin` theme race, retry-link readability, 3:1 control border) can build on G-18/G-16 and the now-trusted `status labels` case.
- No blockers. `tests/unit/test_concept2_canon.js` untouched.

## Self-Check: PASSED

- `tests/unit/test_semantic_token_coverage.js` — modified, present.
- `tests/admin-chrome.spec.js` — modified, present.
- Commits `2f699c3`, `e3fe0e2`, `6d2c353` present in `git log`.
- `npm run test:js`, both Playwright specs and `npm run build` green after the GREEN commit.

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*
