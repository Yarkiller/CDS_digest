---
phase: 04-knowledge-razbory
plan: 02
subsystem: ui
tags: [knowledge, search, react, knowledgeApi, mocks, tdd, KNOW-01]

requires:
  - phase: 04-knowledge-razbory
    provides: GET /knowledge/search JWT DTO without score (04-01)
provides:
  - knowledgeApi.searchKnowledge behind isMocksEnabled
  - KnowledgePage Submit/Enter «Найти» + hint chips + inline guards
  - MaterialListRow slug links + null cover degradation
affects:
  - 04-03 role chips
  - 04-09 Playwright knowledge honesty

actuals:
  tokens: 7310
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "SPA search only on Submit/Enter; validateKnowledgeQuery before fetch"
    - "mockSearchKnowledge pure DTO (no score); authEnv/authApi dynamic import for node:test"
    - "Topic hint chips fill q only (D-60); «Показать ещё» when has_more (D-61)"

key-files:
  created:
    - web/src/services/knowledgeApi.js
    - tests/unit/test_knowledge_api.js
  modified:
    - web/src/pages/KnowledgePage.jsx
    - web/src/components/MaterialListRow.jsx
    - web/src/data/mock.js

key-decisions:
  - "Role chips omitted until 04-03; no role param sent from SPA yet"
  - "Client max q = 500 Unicode code points matching backend"
  - "anomaly-detection mock cover set null to exercise Q2 degradation"

patterns-established:
  - "Pattern: knowledgeApi isMocksEnabled cutover + ErrorPanel/Повторить for partial search failure"
  - "Pattern: MaterialListRow uses slug ?? id and cover_url ?? cover with placeholder when null"

requirements-completed: [KNOW-01]

coverage:
  - id: D1
    description: Submit/Enter «Найти» calls searchKnowledge; hits render via MaterialListRow by slug; no filterMaterials; no scores
    requirement: KNOW-01
    verification:
      - kind: unit
        ref: tests/unit/test_knowledge_api.js#returns API-shaped hits without score and maps null cover_url
        status: pass
      - kind: other
        ref: "node -e plan verify (searchKnowledge + Найти + !filterMaterials)"
        status: pass
    human_judgment: false
  - id: D2
    description: Pre-search topic hint chips fill query without executing search (D-60)
    requirement: KNOW-01
    verification: []
    human_judgment: true
    rationale: Hint-chip fill-only UX is source-present; Playwright honesty reserved for 04-09
  - id: D3
    description: Blank/whitespace and overlong (>500 code points) show inline copy and never call API
    requirement: KNOW-01
    verification:
      - kind: unit
        ref: tests/unit/test_knowledge_api.js#rejects blank and whitespace-only with Введите запрос
        status: pass
      - kind: unit
        ref: tests/unit/test_knowledge_api.js#rejects overlong queries with Сократите запрос
        status: pass
      - kind: other
        ref: "node -e KnowledgePage source includes Введите запрос / Сократите запрос / Показать ещё"
        status: pass
    human_judgment: false
  - id: D4
    description: «Показать ещё» advances offset when has_more (D-61)
    requirement: KNOW-01
    verification:
      - kind: unit
        ref: tests/unit/test_knowledge_api.js#paginates with has_more when more materials exist
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 02: Knowledge SPA Search Summary

**KnowledgePage Submit/Enter «Найти» wired to `knowledgeApi.searchKnowledge` under mocks, with blank/overlong inline guards and slug-linked hit rows (KNOW-01 / D-57…D-61).**

## Performance

- **Duration:** 5min
- **Started:** 2026-09-21T04:36:15Z
- **Completed:** 2026-09-21T04:41:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- `knowledgeApi.searchKnowledge` behind `isMocksEnabled()` with pure `mockSearchKnowledge` DTO (no score)
- KnowledgePage: visible «Найти», topic hint chips fill-only, ErrorPanel + «Повторить», «Показать ещё»
- Client `validateKnowledgeQuery` blocks blank/overlong before any API call
- `MaterialListRow` navigates by slug; null cover degrades without broken `<img>`

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end SPA knowledge search tests** - `73c0a93` (test)
2. **Task 1 (GREEN): Wire KnowledgePage → knowledgeApi** - `867aa83` (feat)
3. **Task 2 (RED): Blank/overlong guard tests** - `206c82d` (test)
4. **Task 2 (GREEN): Inline blank/overlong guards** - `78c9a4a` (feat)

**Plan metadata:** (pending docs commit)

_Note: TDD tasks used test → feat commit pairs_

## Files Created/Modified

- `web/src/services/knowledgeApi.js` — searchKnowledge + mockSearchKnowledge + validateKnowledgeQuery
- `web/src/pages/KnowledgePage.jsx` — Submit/Enter SPA; hint chips; inline guards; pagination
- `web/src/components/MaterialListRow.jsx` — slug link; null cover placeholder
- `web/src/data/mock.js` — anomaly-detection `cover: null` for Q2
- `tests/unit/test_knowledge_api.js` — node:test coverage for mock DTO + validation

## Decisions Made

- Role chips deferred to 04-03 (no role param from SPA yet)
- Max query length 500 Unicode code points on client to match 04-01 backend
- Playwright knowledge rewrite left for 04-09 (plan assumption)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Dynamic import authEnv/authApi for node:test**
- **Found during:** Task 1 (GREEN)
- **Issue:** Static import of authApi pulled supabaseClient → `import.meta.env` crash under `node --test`
- **Fix:** Dynamic `import('./authEnv.js')` / `import('./authApi.js')` inside `searchKnowledge` only
- **Files modified:** `web/src/services/knowledgeApi.js`
- **Verification:** `node --test tests/unit/test_knowledge_api.js` passed
- **Committed in:** `867aa83`

**Total deviations:** 1 auto-fixed (Rule 3)
**Impact on plan:** Testability only; no behavior change in browser

## Issues Encountered

Existing `tests/web-app.spec.js` knowledge cases still assert client `filterMaterials` / tag selects / «Загрузить ещё» — will fail until 04-09 rewrite. Recorded in `.planning/WINDOWS.md`. Left untouched per plan scope (Playwright deferred).

## TDD Gate Compliance

- RED `test(04-02)` commits: `73c0a93`, `206c82d`
- GREEN `feat(04-02)` commits: `867aa83`, `78c9a4a`

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| KnowledgePage role filter | No Analyst/DS/Все chips | Deferred to 04-03 |
| Playwright knowledge e2e | Still old facet assertions | Deferred to 04-09 |

## Threat Flags

None beyond plan threat model — score fields stripped in live mapper even if present (T-04-01).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave-2 SPA search path ready for 04-03 role chips (re-run on chip change when q non-empty)
- 04-09 must rewrite knowledge Playwright to Submit/Enter + guards + «Показать ещё»

## Self-Check: PASSED

- FOUND: `web/src/services/knowledgeApi.js`
- FOUND: `web/src/pages/KnowledgePage.jsx`
- FOUND: `tests/unit/test_knowledge_api.js`
- FOUND: commits `73c0a93`, `867aa83`, `206c82d`, `78c9a4a`

---
*Phase: 04-knowledge-razbory*
*Completed: 2026-09-21*
