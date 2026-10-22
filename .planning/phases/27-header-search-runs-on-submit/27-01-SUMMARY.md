---
phase: 27-header-search-runs-on-submit
plan: 01
subsystem: testing
tags: [node:test, static-gate, sha256, react, knowledge-search, single-call-site]

# Dependency graph
requires:
  - phase: 26-section-context
    provides: the house style for web/src static gates (tests/unit/test_section_context_gates.js walker + counter)
provides:
  - sha256 pin over web/src/services/knowledgeApi.js (measured pre-edit, LF-normalised)
  - static proof that only web/src/pages/KnowledgePage.jsx imports and calls searchKnowledge
  - static proof that the X-1 counter and any second search limiter stay out of the frozen adapter
affects: [27-02, 27-03, 27-04, 27-05]

actuals:
  tokens: 2110
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Digest pin over LF-normalised source text (checkout-independent) instead of raw bytes"
    - "Comment-stripping source scanner that pins its own exclusion (declaration) so the filter cannot pass vacuously"
    - "Limiter matched by declaration regex, never by bare token, when the name is also imported"

key-files:
  created:
    - tests/unit/test_knowledge_api_snapshot.js
    - tests/unit/test_knowledge_search_single_call_site.js
  modified: []

key-decisions:
  - "The adapter digest is taken over readFileSync(..., 'utf8').replace(/\\r\\n/g, '\\n') so a CRLF checkout cannot redden C-24 for the wrong reason"
  - "The call-site scanner excludes the adapter's own `function searchKnowledge(` declaration by SHAPE (not by whitelisting a file) and pins that exclusion with its own assertion, so an empty scan cannot pass"
  - "The limiter gate matches /(?:export )?const DEFAULT_SEARCH_LIMIT =/ per file and asserts set equality, because KnowledgePage.jsx imports the bare name"
  - "The plan's import regex was unfixable as written (required a quote immediately after `knowledgeApi`); widened to `knowledgeApi[^'\"]*['\"]`"

patterns-established:
  - "Non-vacuity by real mutation: mutate, observe the stated failure, revert, re-run green, confirm the revert is byte-identical"
  - "A gate that filters text must pin what it filters out (here: the one declaration) or it can silently count zero"

requirements-completed: [KNOW-05]

coverage:
  - id: D1
    description: "web/src/services/knowledgeApi.js is pinned by sha256 measured on the clean pre-edit file; any edit fails npm run test:js (C-24)"
    requirement: KNOW-05
    verification:
      - kind: unit
        ref: "tests/unit/test_knowledge_api_snapshot.js#knowledgeApi.js stays byte-identical to the frozen snapshot (C-24)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Exactly one module in web/src imports searchKnowledge, and the failure names the offending file"
    requirement: KNOW-05
    verification:
      - kind: unit
        ref: "tests/unit/test_knowledge_search_single_call_site.js#imports searchKnowledge in exactly one module"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exactly one non-comment call site of searchKnowledge( exists in web/src, in KnowledgePage.jsx only"
    requirement: KNOW-05
    verification:
      - kind: unit
        ref: "tests/unit/test_knowledge_search_single_call_site.js#calls searchKnowledge from exactly one non-comment site"
        status: pass
    human_judgment: false
  - id: D4
    description: "The X-1 counter key is absent from the frozen adapter and DEFAULT_SEARCH_LIMIT is defined only there"
    requirement: KNOW-05
    verification:
      - kind: unit
        ref: "tests/unit/test_knowledge_search_single_call_site.js#keeps the request counter out of the frozen adapter"
        status: pass
    human_judgment: false
  - id: D5
    description: "Both gates are non-vacuous: the digest gate reddens on a one-space adapter edit, the call-site gate reddens on a second searchKnowledge({}) call, and both return to green after a byte-identical revert"
    verification:
      - kind: other
        ref: "manual mutation: append one space to web/src/services/knowledgeApi.js -> npm run test:js red (sha256 6eeb37c5…); git checkout + LF restore -> green; append `void searchKnowledge({})` to KnowledgePage.jsx -> red (2 calls); git checkout -> green (13670 bytes / 404 CRLF)"
        status: pass
    human_judgment: true
    rationale: "A mutation is performed and reverted by hand; the recorded evidence is a one-time observation rather than a repeatable suite run, so a human must accept it."

# Metrics
duration: 10min
completed: 2026-10-22
status: complete
---

# Phase 27 Plan 01: Frozen adapter digest and single call-site gate Summary

**Two non-vacuous static gates for KNOW-05: a sha256 pin over the untouched `knowledgeApi.js` adapter and a scanner proving only `KnowledgePage.jsx` imports and calls `searchKnowledge`, both auto-discovered by `npm run test:js` with zero config change.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-22T10:07:00Z
- **Completed:** 2026-10-22T10:16:00Z
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments

- `tests/unit/test_knowledge_api_snapshot.js` pins the adapter to the digest **measured this session on the `git status`-clean file**: `bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f` over LF-normalised text (6283 bytes, 0 CRLF pairs), with the failure message naming `C-24` and `27-CONTEXT.md § Out of scope`.
- `tests/unit/test_knowledge_search_single_call_site.js` proves the structural half of UI-SPEC C-05: one importing module, one non-comment call site, no `__DIGEST_KNOWLEDGE_SEARCH_COUNT__` in the adapter and exactly one `DEFAULT_SEARCH_LIMIT` **definition**.
- Both gates were shown failing for their own stated reason and restored: a one-space adapter edit reddened the digest gate, a second `searchKnowledge({})` call reddened the call-site gate, and both returned to green with the tree byte-identical.
- Full suite green: `npm run test:js` → **112 tests / 27 suites / 112 pass / 0 fail** (109 before this plan's files existed).

## Task Commits

Each task was committed atomically, as a RED/GREEN pair (the 25-01 precedent):

1. **Task 1: Freeze the adapter — sha256 pin (S0 / C-24)**
   - `6a85d86` — `test(27-01)`: failing gate with the `TODO` literal
   - `c213a57` — `feat(27-01)`: measured digest pasted (GREEN)
2. **Task 2: Single call site gate — one import, one non-comment call (S3)**
   - `272c291` — `test(27-01)`: failing naive bare-token scanner (RED)
   - `e741d1a` — `feat(27-01)`: comment stripping, declaration exclusion, declaration-matched limiter (GREEN)

**Plan metadata:** committed after this file (docs commit).

## Files Created/Modified

- `tests/unit/test_knowledge_api_snapshot.js` — sha256 pin over the frozen adapter (one `it`).
- `tests/unit/test_knowledge_search_single_call_site.js` — three `it`s: one importer, one non-comment call site, counter/limiter absent from the adapter.

No production file was touched. `web/src/services/knowledgeApi.js` and `web/src/pages/KnowledgePage.jsx` are byte-identical to their pre-plan content (`git hash-object` matches the index blob; `git status` clean).

## Decisions Made

- **LF-normalised digest, not raw bytes.** `readFileSync(..., 'utf8').replace(/\r\n/g, '\n')` keeps the pin checkout-independent while still failing on any content edit. No byte-count assertion was added — the plan explicitly allows it to differ between checkouts, and the digest already covers content.
- **Declarations are excluded by shape, not by whitelisting the adapter.** The first GREEN attempt proved why this matters: `knowledgeApi.js` contains `export async function searchKnowledge(`, so the naive call-shape needle still read `2` after comment stripping. The filter skips only matches preceded by `function `, and a separate assertion demands `function searchKnowledge(` still be found once — without it, a scanner that found nothing would pass vacuously.
- **The limiter is matched as a declaration.** `DEFAULT_SEARCH_LIMIT` appears 3 times in the adapter (definition + two default params) and twice in the page (import + limit argument), so the gate resolves `/^\s*(?:export\s+)?const\s+DEFAULT_SEARCH_LIMIT\s*=/m` per file and asserts the definer set is exactly `['web/src/services/knowledgeApi.js']`.
- **Comment stripping is line-leading only.** A blanket `//` strip would eat `https://` inside string literals; block comments are blanked by replacing their non-newline characters with spaces.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] The plan's import regex could never match the real module specifier**
- **Found during:** Task 2 GREEN (first run after writing the final scanner)
- **Issue:** `/import\s*\{[^}]*\bsearchKnowledge\b[^}]*\}\s*from\s*['"][^'"]*knowledgeApi['"]/` demands a quote immediately after `knowledgeApi`, but the specifier is `'../services/knowledgeApi.js'`. The gate failed with `found none` on the clean tree — it would have been unpassable without weakening it.
- **Fix:** widened the tail to `knowledgeApi[^'"]*['"]` (still anchored to an import from a `knowledgeApi*` module).
- **Files modified:** `tests/unit/test_knowledge_search_single_call_site.js`
- **Verification:** gate green on the clean tree; import assertion still names the offending file.
- **Committed in:** `e741d1a` (Task 2 GREEN)

**2. [Rule 1 - Bug] The plan's predicted RED numbers were low; the gate's requirement was kept, not loosened**
- **Found during:** Task 2 RED
- **Issue:** the plan predicted the naive bare-token scan would read `3` (import + call + prose comment) and the bare limiter token `2`. Measured: `searchKnowledge` reads **5** (`KnowledgePage.jsx` ×3 — import, call, comment — plus `knowledgeApi.js` ×2 — JSDoc line 43 and the declaration) and `DEFAULT_SEARCH_LIMIT` spans **2 files** with 5 occurrences. The plan's research undercounted the adapter's own textual hits.
- **Fix:** none to the requirement. The RED was committed with the measured numbers; GREEN reaches exactly `1` by stripping comments and excluding declarations, and the limiter assertion is per-file set equality (as the plan itself specified), not a scalar count.
- **Files modified:** `tests/unit/test_knowledge_search_single_call_site.js`
- **Verification:** `# pass 3` on the clean tree; both mutations red.
- **Committed in:** `272c291` (RED) / `e741d1a` (GREEN)

### Nothing else deviated

No production code, no config change, no edit to `scripts/run-unit-js.cjs`, and the adapter was never edited (its bytes were restored, see Issues Encountered).

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs in the plan's own literals, neither weakened a gate)
**Impact on plan:** none on scope. Both fixes were required for the gates to exist at all; the assertions are stricter than the plan's prose (declaration exclusion is self-pinned, limiter matched by declaration).

## Issues Encountered

- **`git checkout --` rewrites line endings on this checkout.** `core.autocrlf=true` with `.gitattributes: * text=auto` means checkout writes CRLF, so reverting the one-space mutation turned the adapter from its original 6283-byte LF form into 6485 bytes / 202 CRLF pairs. That is exactly the false-RED case the digest normalisation exists for, but the must-have also states "6283 bytes, 0 CRLF pairs on this checkout". The original LF bytes were restored from the unchanged content, then verified: 6283 bytes, 0 CRLF, `git hash-object` equals the index blob (`6c032d9…`) and `git status --porcelain -- web/src/services/knowledgeApi.js` is empty. `KnowledgePage.jsx` reverted to its own original form directly (13670 bytes / 404 CRLF).
- No other problems. No checkpoint, no auth gate, no package install.

## Threat Flags

None — the plan ships two test files that only read the working tree. No new endpoint, auth path, file access pattern or schema change crosses a trust boundary.

## Known Stubs

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- The adapter is frozen and provably untouched, so 27-02 may edit `KnowledgePage.jsx` — and *only* that page — to add X-1 and the submit effect. Any adapter edit now fails `npm run test:js` at the digest gate.
- The call-site gate is the guard that 27-02/27-03 must keep green: a second `searchKnowledge(` call site (including one hidden in a new helper) reddens it, and the failure names the file.
- Both files are auto-discovered by the existing flat `tests/unit/*.js` glob; no runner config change was made and none is needed for later plans.

---
*Phase: 27-header-search-runs-on-submit*
*Completed: 2026-10-22*

## Self-Check: PASSED

- Created files exist: `tests/unit/test_knowledge_api_snapshot.js`, `tests/unit/test_knowledge_search_single_call_site.js`, `.planning/phases/27-header-search-runs-on-submit/27-01-SUMMARY.md`.
- Commits exist: `6a85d86`, `c213a57`, `272c291`, `e741d1a`.
- `npm run test:js`: 112 pass / 0 fail.
- `web/src` is clean: no adapter or page modification survived the mutation checks.
