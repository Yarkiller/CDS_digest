---
phase: 04-knowledge-razbory
plan: 09
subsystem: testing
tags: [playwright, e2e, knowledge, razbory, nyquist, validation]

requires:
  - phase: 04-knowledge-razbory
    provides: Knowledge SPA + razbory list/detail/notebook under mocks and live adapters (04-01…04-08)
provides:
  - Consolidated Playwright honesty suites for KNOW-01…04 and RAZB-01…04
  - Updated 04-VALIDATION.md with wave_0_complete / nyquist_compliant
  - Optional live FE↔BE proof checklist in local-platform-runbook §5b
affects: [verify-work, phase-5]

actuals:
  tokens: 17630
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Playwright web testMatch includes knowledge|razbory; webServer forces VITE_USE_MOCKS=true"
    - "TOC heading ids = user-content- + unicode slug (rehype-slug + sanitize clobber)"

key-files:
  created:
    - tests/knowledge.spec.js
    - tests/razbory.spec.js
  modified:
    - tests/web-app.spec.js
    - playwright.config.js
    - web/src/utils/markdownToc.js
    - tests/unit/test_markdown_toc.js
    - .planning/phases/04-knowledge-razbory/04-VALIDATION.md
    - docs/agents/local-platform-runbook.md
    - .planning/WINDOWS.md

key-decisions:
  - "Mocks remain CI default; live KNOW/RAZB proof is optional runbook §5b"
  - "UI-SPEC overflow/long-text backstops recorded as human_needed/backstop — never silent pass"
  - "TOC ids prefixed with user-content- to match rehype-sanitize clobber"

patterns-established:
  - "Phase honesty e2e lives in dedicated knowledge.spec.js / razbory.spec.js, not web-app.spec.js"

requirements-completed: [KNOW-01, KNOW-02, KNOW-03, KNOW-04, RAZB-01, RAZB-02, RAZB-03, RAZB-04]

coverage:
  - id: D1
    description: Knowledge honesty e2e — Submit/Enter, whitespace guard, role chips, DS→material, reset-filter, no scores
    requirement: KNOW-01
    verification:
      - kind: e2e
        ref: "tests/knowledge.spec.js#knowledge honesty (KNOW-01…04)"
        status: pass
    human_judgment: false
  - id: D2
    description: Razbory honesty e2e — chronology/empty CTA, sticky TOC jump, notebook dual strip, Качество/Обзор, soft 404
    requirement: RAZB-01
    verification:
      - kind: e2e
        ref: "tests/razbory.spec.js#razbory honesty (RAZB-01…04)"
        status: pass
    human_judgment: false
  - id: D3
    description: Full pytest unit gate green (170 tests)
    verification:
      - kind: unit
        ref: "npm run test:unit"
        status: pass
    human_judgment: false
  - id: D4
    description: UI-SPEC overflow/long-text visual backstops (pagination has_more, many chronology, wrap)
    verification: []
    human_judgment: true
    rationale: "insufficient_spec under mock catalog size; held-out for /gsd-verify-work per 04-VALIDATION.md"

duration: 9min
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 09: Playwright Honesty Gate Summary

**Playwright knowledge + razbory honesty suites green under mocks; VALIDATION.md marked wave_0_complete / nyquist_compliant with explicit UI-SPEC backstops.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-09-21T09:16:33Z
- **Completed:** 2026-09-21T09:25:32Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Consolidated KNOW-01…04 and RAZB-01…04 Playwright coverage in dedicated specs (7/7 green)
- Fixed Cyrillic TOC jump bug (unicode slug + `user-content-` sanitize clobber alignment)
- Refreshed `04-VALIDATION.md` Wave 0 map; documented optional live FE↔BE in runbook §5b
- Closed WINDOWS #12/#13 (deferred Playwright razbory/notebook proofs)

## Task Commits

1. **Task 1 (RED): Consolidate Playwright honesty suites** — `a14e175` (test)
2. **Task 1 (GREEN): Register suites + TOC fix** — `00fb077` (feat)
3. **Task 2: Unit gate + VALIDATION Nyquist refresh** — `fde14e4` (docs)

**Plan metadata:** `7688392` (docs: complete plan)

## Files Created/Modified

- `tests/knowledge.spec.js` — KNOW honesty e2e
- `tests/razbory.spec.js` — RAZB honesty e2e
- `tests/web-app.spec.js` — removed duplicate knowledge cases (no tag facets)
- `playwright.config.js` — testMatch + forced mocks
- `web/src/utils/markdownToc.js` — unicode + sanitize-aligned heading ids
- `tests/unit/test_markdown_toc.js` — Cyrillic / prefix contract
- `.planning/phases/04-knowledge-razbory/04-VALIDATION.md` — Nyquist refresh
- `docs/agents/local-platform-runbook.md` — §5b optional live proof
- `.planning/WINDOWS.md` — fixed #12/#13; logged UI-SPEC backstops as #14

## Decisions Made

- Keep Playwright CI on mocks; live KNOW/RAZB is optional human proof after 04-08 seed
- Pagination `has_more` under mocks remains `human_needed` (catalog &lt; page size 10)
- Unclassified COVERAGE probes recorded as N/A covered by this gate

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Cyrillic TOC links missed heading ids**
- **Found during:** Task 1 (sticky TOC e2e)
- **Issue:** `slugify` stripped Cyrillic (`\w`); TOC hrefs also omitted `user-content-` clobber from `rehype-sanitize`
- **Fix:** Unicode `\p{L}\p{N}` slugify + `HEADING_ID_PREFIX = 'user-content-'`
- **Files modified:** `web/src/utils/markdownToc.js`, `tests/unit/test_markdown_toc.js`, `tests/razbory.spec.js`
- **Verification:** sticky TOC Playwright case green; unit Cyrillic ids match
- **Committed in:** `00fb077`

**2. [Rule 3 - Blocking] Playwright did not discover new specs**
- **Found during:** Task 1 RED verify
- **Issue:** `testMatch` only `(web-app|auth)`
- **Fix:** Expand to `(web-app|auth|knowledge|razbory)`
- **Files modified:** `playwright.config.js`
- **Committed in:** `00fb077`

**Total deviations:** 2 auto-fixed (Rule 1 ×1, Rule 3 ×1)
**Impact on plan:** Necessary for RAZB-02 honesty; no scope creep.

## Issues Encountered

None beyond the TOC id mismatch discovered by the honesty e2e itself.

## Known Stubs

None introduced by this plan. Pre-existing Phase 4 stubs (StubQueryEmbedder Foundry OPT-OUT, etc.) remain in WINDOWS ledger and are out of scope for 04-09.

## Auth Gates

None.

## Threat Flags

None — no new network/auth surface; mocks only in fixtures.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 4 automated honesty gate is green. Ready for `/gsd-verify-work` including held-out UI-SPEC visual backstops. Phase 5 can proceed after verify.

## Self-Check: PASSED

- FOUND: `.planning/phases/04-knowledge-razbory/04-09-SUMMARY.md`
- FOUND: `tests/knowledge.spec.js`, `tests/razbory.spec.js`, `04-VALIDATION.md`
- FOUND: commits `a14e175`, `00fb077`, `fde14e4`

---
*Phase: 04-knowledge-razbory*
*Completed: 2026-09-21*
