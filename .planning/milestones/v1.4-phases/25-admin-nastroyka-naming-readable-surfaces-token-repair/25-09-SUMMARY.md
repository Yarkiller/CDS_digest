---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 09
subsystem: testing
tags: [node:test, playwright, semantic-token-coverage, contrast, regex-scanner, tailwind]

# Dependency graph
requires:
  - phase: 25-08
    provides: primary label role migration (36 literals → text-primary-text) and the G-14/G-16 gates this plan rewrites
provides:
  - TINT_TOKEN / tintAlphaSites / tintLabelMeasurements (G-14 reads tint alpha from the class, not a constant)
  - REGEX_LITERAL (anchored to the opening slash) + regexLiterals + alternativesOf + literalsCoveredBy (whole-body compile)
  - statusContractOffences R1 (all regex literals) + R3 (±15-line toast colour window)
  - pillAlpha in tests/admin-chrome.spec.js (alpha read from the pill class; `tintAlpha` constant removed)
affects: [verify-work, G-14/G-16 future consumers, THEME-02 proof gates]

# Actuals (#2632) — pairs with the plan's `estimate` to calibrate future estimates.
actuals:
  tokens: 6114
  tasks: 2
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "anchored regex-literal scanner: REGEX_LITERAL = /\\/((?![*\\/])(?:\\\\\\/|[^/\\n\\\\]|\\\\.)+)\\/([a-z]*)/g"
    - "offset-preserving comment masking (block + whole-line // → spaces) so `file:line` stays accurate"
    - "tint alpha from the class token (no alpha constant anywhere in tests)"

key-files:
  created: []
  modified:
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js

key-decisions:
  - "regexLiterals masks comments (block + whole-line // become spaces) instead of removing them, so line numbers stay exact — mutation #5 pinned the phantom at tests/web-app.spec.js:388."
  - "The e2e helper is named `pillAlpha`, not `tintAlpha*`, so the `Select-String 'tintAlpha' → 0` acceptance holds literally."
  - "R1 offender keeps the `one regex matches N status literals` shape so the existing proof filter `/one (regex|assertion) matches/` and the `Выпуск опубликован | Рассылка не отправлена` assertion stay green."

requirements-completed: [THEME-02]

# Coverage metadata (#1602)
coverage:
  - id: D1
    description: "G-14 reads tint alpha from the class token (TINT_TOKEN / tintAlphaSites / tintLabelMeasurements); a /60 mutation reddens both themes"
    requirement: "THEME-02"
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-14 proof: the tint alpha is read from the class, so a /60 mutation fails"
        status: pass
    human_judgment: false
  - id: D2
    description: "G-16 R1/R3 enforce the status contract: anchored regex-literal scan (R1) + ±15-line toast colour window (R3)"
    requirement: "THEME-02"
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-16 proof: an alternation inside hasText, name or toHaveAccessibleName is an offender"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-16 proof: a text-only toast check fails even though the file reads colours elsewhere"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-16 proof: a single-alternative regex body is not an alternation"
        status: pass
    human_judgment: false

# Metrics
duration: 17min
completed: 2026-10-21
status: complete
---

# Phase 25 Plan 09: G-14 tint alpha from the class and G-16 R1/R3 status-contract rewrite

**Rewrote G-14 to parse tint alpha from the class token (`bg-success/15` → 0.15) and G-16 R1/R3 to scan every anchored regex literal and read toast colours inside a ±15-line window — test-only, no production files changed.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-21T22:27:09+03:00
- **Completed:** 2026-10-21T22:44:00+03:00
- **Tasks:** 2
- **Files modified:** 2 (`tests/unit/test_semantic_token_coverage.js`, `tests/admin-chrome.spec.js`)
- **Plan head:** `871839d` → `80b9c13`

## Accomplishments

- **GAP-25-6 closed by substance:** `G-14` now collects its tint sites from the tree via `TINT_TOKEN` + `tintAlphaSites` and measures via `tintLabelMeasurements`; the `/N` suffix is the alpha, never a constant. The hardcoded `STATUS_LABEL_TINTS` (with its `alpha: 0.15/0.2/0.1`) is gone, replaced by `TINT_LABEL_ROLES` (tint → ink, no alpha).
- **G-14 now measures 7 sites / 4 unique tokens**, including the `hover:bg-danger/15` site at `ErrorPanel.jsx:16` (4.875 on light `paper-2` — the tightest pair of the family) and lists the file provenance of every pair.
- **GAP-25-7 closed:** `G-16` R1 scans *all* regex literals (anchored `REGEX_LITERAL`) with a form check (`alternativesOf ≥ 2`) and a whole-body compile (`literalsCoveredBy`), catching `getByText` / `filter({hasText})` / `{name}` / `toHaveAccessibleName` **and** the grouped `(?:A|B)` / `^(A|B)$` spellings. R3 reads `admin-toast` colours inside ±15 lines, so the distant `styleTriple` helper no longer keeps it green (WR-09).
- **`tests/admin-chrome.spec.js` drops the second `tintAlpha` constant**; the status-label case derives the alpha from the pill's own class via `pillAlpha` and throws if the tint token is missing.
- **Four proof tests added** (3 RED-then-green, 1 anti-false-positive pin). `test:js` → 95 pass / 0 fail; Playwright `admin-chrome` 12 passed, `admin` 88 passed.

## Tint family measured (input to G-14)

| Token | Files (provenance) | Ink role | Tightest pair (light) | Tightest pair (dark) |
|---|---|---|---|---|
| `bg-danger/10` | ErrorPanel.jsx, IngestSourcesSection.jsx, AdminPipelineConfigPage.jsx ×2 | danger-ink | 5.201 (paper-2) | 5.283 (paper-2) |
| `bg-danger/15` | ErrorPanel.jsx (`hover:`) | danger-ink | **4.875** (paper-2) | 4.984 (paper-2) |
| `bg-success/15` | AdminDigestPage.jsx | success-ink | 5.795 (paper-2) | 7.044 (paper-2) |
| `bg-voting/20` | AdminDigestPage.jsx | voting-ink-on-tint | 7.057 (paper-2) | 8.473 (paper-2) |

Upper bound: 10.532 (dark `voting/20` on `bg-app`).

## Task Commits

1. **Task 1 (RED): four proof tests, three fail** — `9d1acf2` (test)
2. **Task 2 (GREEN): G-14 + G-16 rewrite + e2e alpha-from-class** — `80b9c13` (feat)

**Plan metadata:** docs commit (below).

## RED failure output (recorded before GREEN)

- `G-14 proof: the tint alpha is read from the class, so a /60 mutation fails` — `ReferenceError: tintAlphaSites is not defined`.
- `G-16 proof: an alternation inside hasText, name or toHaveAccessibleName is an offender` — `AssertionError: form must be exactly one R1 offender … actual: 0`.
- `G-16 proof: a text-only toast check fails even though the file reads colours elsewhere` — `AssertionError: exactly one offender, got: — actual: 0`.
- `G-16 proof: a single-alternative regex body is not an alternation` — green (anti-false-positive pin; no RED reason).

The `/15 → /60` mutation on the **unchanged** gate stayed green (GAP-25-6 evidence) before Task 2 landed.

## Mutation protocols (each reddened its gate, then was reverted)

1. **G-14 /60** — `bg-success/15 → /60` in `AdminDigestPage.jsx:718` → G-14 reddens: light 4.181 (bg-app) / 4.094 (paper-2) / 4.264 (paper); dark 3.011 / 2.699 / 2.850 — all < 4.5.
2. **G-16 R3 toast** — remove the three colour expects at `admin-toast` → G-16 reddens `tests/admin-chrome.spec.js:544: reads admin-toast but never its computed backgroundColor within ±15 lines` (the `borderTopColor` inside the `expected` object at line 530 is inside the window; `backgroundColor` at 528 is 16 lines away and correctly excluded).
3. **G-16 R1 non-grouped** — `page.getByRole("status", { name: /Выпуск опубликован|Уже отправлено/ })` → R1 reddens `tests/admin.spec.js:860: one regex matches 2 status literals (Выпуск опубликован | Уже отправлено)`.
4. **G-16 R1 grouped (W1)** — `{ name: /(?:Выпуск опубликован|Уже отправлено)/ }` → R1 reddens with the same two literals (the old per-alternative compile silently returned 0 here).
5. **REGEX_LITERAL anchor** — remove the leading `\/` → G-16 reddens `tests/web-app.spec.js:388: one regex matches 5 status literals (…) — /|traceback|Error:/` and the proof pin reddens too; `tests/web-app.spec.js` itself is untouched.
6. **voting-ink-on-tint flat (W2)** — `--color-voting-ink-on-tint: #713F12 → #FDE68A` in the light block → G-14 reddens `--color-voting-ink-on-tint has no real light override (#FDE68A in both themes)`.

## Files Created/Modified

- `tests/unit/test_semantic_token_coverage.js` — `TINT_TOKEN`, `TINT_LABEL_ROLES`, `tintAlphaSites`, `tintLabelMeasurements`, rewritten `G-14`; `REGEX_LITERAL`, `regexLiterals`, `alternativesOf`, `literalsCoveredBy`, rewritten R1/R3 in `statusContractOffences`; four proof tests.
- `tests/admin-chrome.spec.js` — `pillAlpha` helper; status-label case reads alpha from the pill class; `tintAlpha` constant removed.

## Decisions Made

- `regexLiterals` masks comments (block + whole-line `//` → spaces) rather than removing them, so offsets/newlines — and therefore `file:line` — stay exact. The plan's `replace(…,'')` for block comments would shift every line after a multi-line block comment; masking is the same "no comment regexes" guarantee with correct line numbers (mutation #5 pinned `:388`).
- The e2e helper is `pillAlpha` so the acceptance `Select-String 'tintAlpha' → 0` holds literally (0 matches confirmed).
- R1 offender text keeps the `one regex matches N status literals` shape so the pre-existing proof assertions (`/one (regex|assertion) matches/`, `Выпуск опубликован | Рассылка не отправлена`) stay green unchanged.

## Deviations from Plan

None that changed scope or behaviour — the plan executed as written. Two implementation refinements are recorded above under Decisions: (1) offset-preserving comment masking instead of `replace(…,'')` for line-number accuracy; (2) `pillAlpha` naming to satisfy the literal `tintAlpha` grep criterion. Neither touches a production file, the 4.5 threshold, or any allowlist.

## Issues Encountered

None — the only flakiness noted is the known Vite/port-5174 issue, which was avoided by confirming port 5174 was free before the Playwright runs (0 listeners).

## Next Phase Readiness

- `G-14` and `G-16` now fail on their own mutations (GAP-25-6, GAP-25-7 closed); the 4.5 floor, `G-9`, `G-15`, `G-17`, `G-18`, `G-19` are untouched.
- `npm run build` produces no new warnings (only the pre-existing chunk-size note).

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- `25-09-SUMMARY.md` exists.
- Commit `9d1acf2` (Task 1 RED) and `80b9c13` (Task 2 GREEN) both present in history.

