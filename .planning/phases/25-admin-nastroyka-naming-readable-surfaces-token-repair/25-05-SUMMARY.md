---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 05
subsystem: ui
tags: [design-tokens, wcag-contrast, tailwind-v4, tdd, gap-closure]

# Dependency graph
requires:
  - phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
    provides: "the semantic family in @theme static / [data-theme=light], the shared contrast helper, G-0…G-13 and the -solid label migration"
provides:
  - "blendOver(colour, base, alpha) — the single tint-composite implementation in tests/helpers/contrast.js"
  - "G-14: status label roles measured on their tint composite and on bare surfaces, both themes, floor 4.5"
  - "G-15: the field boundary measured at WCAG 1.4.11's 3:1, with the decorative rule proven to fail the same floor"
  - "--color-success-ink, --color-voting-ink-on-tint, --color-accent-text (themed) and --color-field-border (flat)"
affects: ["25-06", "25-07"]

actuals:
  tokens: 4036
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "A tint composite is measured through one shared helper, never an ad-hoc expression inside a gate"
    - "A role that is identical in both themes is pinned flat by FLAT; a role whose *composite* flips is pinned themed by its own gate, not by THEMED"

key-files:
  created: []
  modified:
    - tests/helpers/contrast.js
    - tests/unit/test_semantic_token_coverage.js
    - web/src/index.css

key-decisions:
  - "blendOver ignores the alpha carried by `colour` — a browser serializes the tint as rgba(...), and the strength under measurement is the argument, never the serialization"
  - "--color-field-border is the flat #64748B, not the requested #4B5563/#64748B pair: #4B5563 measures 2.328 on dark paper and would fail the same 3:1 gate this plan switches on"
  - "success-ink / voting-ink-on-tint / accent-text are deliberately absent from THEMED — G-4's anti-vacuum check would demand consumers that do not exist until 25-06/25-07; their theme dependence is pinned inside G-14 instead"
  - "the accent label role is named accent-text, not *-accent-ink, because G-5 forbids that substring; the base --color-accent is untouched and the dark value of the new role is byte-identical to it"

patterns-established:
  - "Composite-first contrast: any ratio against a translucent surface is taken through blendOver, so a `bg-<status>/<alpha>` label cannot be measured against the flat fill by accident"
  - "Proof tests reproduce a recorded offender numerically (1.925 / 1.62 / 1.918, and rule at 1.425 / 1.485) so a detector cannot go green by measuring nothing"

requirements-completed: [THEME-02]

coverage:
  - id: D1
    description: "blendOver composites a translucent tint over an opaque base and always returns an opaque normalized rgb(); it throws on a translucent base and on alpha outside 0..1"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-14 proof: blendOver always returns an opaque normalized rgb()"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-14 proof: the detector reproduces the recorded 1.925:1 tint offender"
        status: pass
    human_judgment: false
  - id: D2
    description: "G-14 measures success-ink / voting-ink-on-tint / danger-ink on their tint composites over paper, paper-2 and bg-app in both themes, and the label roles on the bare surfaces, at a 4.5 floor"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-14: a status label clears 4.5:1 on its tint and on bare surfaces, both themes"
        status: pass
    human_judgment: false
  - id: D3
    description: "G-15 measures --color-field-border at 3:1 on the three surfaces in both themes and proves the same floor rejects the decorative rule"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-15: the field boundary clears the 3:1 non-text floor in both themes"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-15 proof: the same 3:1 floor rejects the decorative rule"
        status: pass
    human_judgment: false
  - id: D4
    description: "The four tokens exist in the single @theme static block with three light overrides and none for field-border, and Tailwind emits them into the built CSS"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-3: declares every theme-independent role once and never overrides it"
        status: pass
      - kind: other
        ref: "npm run build -> exit 0; --color-success-ink, --color-voting-ink-on-tint, --color-accent-text, --color-field-border present in web/dist/assets/*.css"
        status: pass
      - kind: e2e
        ref: "npx playwright test tests/admin-chrome.spec.js --project=web -> 4 passed"
        status: pass
    human_judgment: false

# Metrics
duration: 8 min
completed: 2026-10-21
status: complete
---

# Phase 25 Plan 05: Tint-composite label roles and a real field boundary

**Three themed status-label roles plus a flat `#64748B` field boundary, measured on the tint composite in both themes by G-14 and against WCAG 1.4.11's 3:1 by G-15 — no component touched**

## Performance

- **Duration:** 8 min
- **Started:** 2026-10-21T19:39:47+03:00
- **Completed:** 2026-10-21T19:50:00+03:00
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `blendOver(colour, base, alpha)` landed in the shared contrast helper as the single tint-composite implementation. It returns an opaque normalized `rgb(r, g, b)`, ignores the alpha carried by `colour` (so a browser's `rgba(34, 197, 94, 0.15)` is usable as-is), throws on a translucent base and on alpha outside `0..1`.
- G-14 measures the three status label roles on their own tint composite over `paper` / `paper-2` / `bg-app` in both themes, and the label roles again on the bare surfaces, at a 4.5 floor. Measured green values: `success-ink` 7.801 / 7.044 / 8.778 dark and 6.262 / 5.795 / 6.024 light; `voting-ink-on-tint` 9.419 / 8.473 / 10.532 and 7.621 / 7.057 / 7.326; `danger-ink` on `danger/10` 5.837 / 5.283 / 6.407 and 5.665 / 5.201 / 5.449.
- G-15 measures `--color-field-border` at 3.698 / 3.342 / 4.030 (dark) and 4.759 / 4.344 / 4.548 (light), and its proof shows the same floor rejecting the decorative `rule` at 1.425 / 1.485 — so the gate distinguishes a boundary from a divider.
- Four tokens declared: `--color-success-ink` `#4ADE80`/`#166534`, `--color-voting-ink-on-tint` `#FDE68A`/`#713F12`, `--color-accent-text` `#06B6D4`/`#0E7490` (all with real light overrides), and `--color-field-border: #64748B` declared flat with no override. Zero existing lines changed (`git diff --numstat` = 28 insertions, 0 deletions).
- Canon untouched: `canonDark.size === 51` / `canonLight.size === 13`, and no component under `web/src` was edited.

## Task Commits

Each task was committed atomically:

1. **Task 1: blendOver + G-14/G-15 + proofs (RED)** - `b65e530` (test)
2. **Task 2: declare the four tokens (GREEN)** - `77a8315` (feat)

**Plan metadata:** committed immediately after this file (docs: complete plan)

## Files Created/Modified

- `tests/helpers/contrast.js` — added `blendOver` and exported it next to `contrastRatio`; `parseColor` / `relativeLuminance` / `contrastRatio` unchanged.
- `tests/unit/test_semantic_token_coverage.js` — added `TINT_BASES`, `STATUS_LABEL_TINTS`, `LABELS_ON_SURFACE`; G-14 + two proofs, G-15 + proof; `field-border` joined `FLAT`; `UTILITY_PATTERN` learned the new family names, longest first.
- `web/src/index.css` — 28 inserted lines: three themed label roles plus their three light overrides, and the flat `--color-field-border` in the theme-independent group.

## TDD Evidence (RED)

- **Command:** `npm run test:js` — **exit code 1**
- **Target 1:** `G-14: a status label clears 4.5:1 on its tint and on bare surfaces, both themes`
  - **Expected:** fail because the label roles are not declared yet.
  - **Actual:** `AssertionError: a status label must survive its own tint in both themes: --color-success-ink is not declared in the dark block; --color-voting-ink-on-tint is not declared in the dark block; --color-success-ink is not declared in the light block; --color-voting-ink-on-tint is not declared in the light block; --color-accent-text is not declared in the dark block; --color-accent-text is not declared in the light block`
- **Target 2:** `G-15: the field boundary clears the 3:1 non-text floor in both themes`
  - **Expected:** fail because the boundary role is not declared yet.
  - **Actual:** `AssertionError: a form boundary must clear WCAG 1.4.11's 3:1 (a decorative divider must not be reused as one): --color-field-border is not declared in @theme (WCAG 1.4.11 needs a boundary role of its own)`
- **Also red, same root cause:** `G-3: declares every theme-independent role once and never overrides it` — `[--color-field-border is not declared in @theme]` (see Deviations #1).
- **Proofs green before any declaration** (they measure literals, not `index.css`): `G-14 proof: the detector reproduces the recorded 1.925:1 tint offender`, `G-14 proof: blendOver always returns an opaque normalized rgb()`, `G-15 proof: the same 3:1 floor rejects the decorative rule`.
- **RED record:** tests 81, pass 78, fail 3; the three failures are the two new gates plus the FLAT extension of an existing gate. **Semantic assessment:** the red is the planned assertion on the planned missing declarations (not a syntax, import, discovery or fixture failure), and every other check in the same run stayed green.

## Decisions Made

- **`blendOver` ignores the tint's own alpha.** `getComputedStyle` serializes `bg-success/15` as `rgba(34, 197, 94, 0.15)`; transferring that alpha into the result would hand `contrastRatio` a translucent surface, which throws by design. The strength is the argument. Pinned by a proof (`rgba(...)` input + `alpha` 0.15 → `rgb(216, 242, 228)`).
- **`field-border` is flat `#64748B`.** The `#4B5563`/`#64748B` pair from the statement would fail its own 3:1 gate in the dark theme (2.328 on `paper`). `#64748B` clears 3:1 on all three surfaces in both themes, so the role is theme-independent and G-3 pins the absence of an override. Deviation is measured, not aesthetic.
- **The three label roles stay out of `THEMED`.** G-4's anti-vacuum half demands a consumer for every `THEMED` name; the consumers arrive in 25-06 and 25-07. G-14 pins their theme dependence instead (present in the block, and a light value that differs from the dark one).
- **The accent label is `accent-text`.** `accent-ink` is forbidden by G-5 (D-10), so the name avoids the substring entirely; `--color-accent` and `outline-accent` are untouched, and the dark value `#06B6D4` is byte-identical to `--color-accent`, so the dark theme does not move visually.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] G-3 turns red in the same RED run as G-14/G-15**

- **Found during:** Task 1 (RED)
- **Issue:** The plan's `<action>` requires `field-border` to join `FLAT` in Task 1, while its `<acceptance_criteria>` expects only the two *new* gates to fail ("остальные существующие проверки остаются зелёными"). Adding the name to `FLAT` makes the existing G-3 fail too, because the token is still undeclared.
- **Fix:** Followed the normative `<action>` (a flat role must be pinned in `FLAT` at the moment the gate is introduced, otherwise the GREEN commit's "no light override" property would be unproven). Both failures name the same missing declaration, so the RED cause is unchanged; GREEN clears all three.
- **Files modified:** `tests/unit/test_semantic_token_coverage.js`
- **Verification:** RED = 3 failures (G-3/G-14/G-15), GREEN = 81/81 pass.
- **Committed in:** `b65e530` (RED), cleared by `77a8315` (GREEN)

**2. [Rule 1 - Bug] STATE.md plan counter**

- **Found during:** state bookkeeping
- **Issue:** `state.advance-plan` incremented the working-tree position (`Plan: 1 of 7`, written for the gap-closure subset) to `Plan: 2 of 7`, but four plans of seven are already executed and this plan is 25-05.
- **Fix:** Corrected the position to `Plan: 5 of 7` and `progress.completed_plans: 5` by hand; the frontmatter `state_head` written by the tool was kept.
- **Files modified:** `.planning/STATE.md`
- **Verification:** matches `4 (existing summaries) + 1 = 5` of `7` plans on disk.
- **Committed in:** the plan metadata commit

---

**Total deviations:** 2 auto-fixed (2 bug/bookkeeping)
**Impact on plan:** No scope creep. #1 is a plan-internal contradiction resolved in favour of the normative action and documented so the verifier does not read it as an unexpected failure; #2 is bookkeeping arithmetic, no product effect.

## Issues Encountered

- Documentation drift left deliberately untouched: the `[data-theme="light"]` comment still says "The seven theme-independent roles are deliberately absent" while `FLAT` now holds eight (`field-border` joined). Task 2's acceptance requires `git diff --numstat -- web/src/index.css` to show zero deleted lines and the action forbids editing existing lines, so the comment was not rewritten. Worth a one-line follow-up in 25-06/25-07 which already open that file's neighbourhood.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- 25-06 can migrate the 18 status labels onto `text-success-ink` / `text-voting-ink-on-tint` / `text-danger-ink`: the roles are declared, emitted into the built CSS, and G-14 is green on the pairs 25-06 will produce.
- 25-07 can paint `border-field-border` on the 16 controls and move the three accent labels onto `text-accent-text`: G-15 already holds the 3:1 floor and pins the absence of a light override.
- Both plans can introduce their usage-level scans (G-18 / G-19) on the existing `tokenSet`, and `UTILITY_PATTERN` already recognises `success-ink`, `voting-ink-on-tint` and `accent-text`, longest-first, so `text-success` cannot be mistaken for `text-success-ink`.
- Nothing under `web/src` uses the four new names yet — that is intended, and G-4 stays green because the anti-vacuum half only covers `THEMED`.

## Self-Check: PASSED

- `tests/helpers/contrast.js` — FOUND
- `tests/unit/test_semantic_token_coverage.js` — FOUND
- `web/src/index.css` — FOUND
- commit `b65e530` — FOUND
- commit `77a8315` — FOUND
- `tests/unit/test_concept2_canon.js` untouched — FOUND (`git diff --name-only` lists only the three files above)

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*
