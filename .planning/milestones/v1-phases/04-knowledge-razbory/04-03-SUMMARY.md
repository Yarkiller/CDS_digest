---
phase: 04-knowledge-razbory
plan: 03
subsystem: ui
tags: [knowledge, search, role-chips, fastapi, react, tdd, KNOW-02, KNOW-03, KNOW-04]

requires:
  - phase: 04-knowledge-razbory
    provides: GET /knowledge/search and Knowledge SPA Submit/Enter from 04-01 and 04-02
provides:
  - Role chips Analyst / DS / Все with server allowlist analyst|ds
  - Zero-hit «Сбросить фильтр» clears role only and keeps the query
  - Unit proof that an analyst miss does not backfill ds materials
affects:
  - 04-09 Playwright knowledge honesty gate

actuals:
  tokens: 7334
  tasks: 2
  commits: 4

tech-stack:
  added: []
  patterns:
    - "normalize_role_filter allowlist analyst|ds; blank role is unrestricted (KNOW-02)"
    - "Chip change re-runs search only when the trimmed query is non-empty (D-64)"
    - "«Сбросить фильтр» sets role to Все and keeps query text (D-65)"

key-files:
  created: []
  modified:
    - backend/src/backend/application/use_cases/search_knowledge.py
    - backend/src/backend/interface/http/routes/knowledge.py
    - web/src/pages/KnowledgePage.jsx
    - web/src/services/knowledgeApi.js
    - web/src/utils/filters.js
    - web/src/data/mock.js
    - tests/unit/test_search_knowledge.py
    - tests/unit/test_http_knowledge_search.py
    - tests/web-app.spec.js

key-decisions:
  - "Invalid role is 400 invalid_role, not an empty 200; SPA toasts «Фильтр недоступен» and resets to Все"
  - "Null, empty, and whitespace role query params mean unrestricted («Все»)"
  - "Client filterMaterials no longer applies tag, format, or topic (D-63)"

patterns-established:
  - "Pattern: role chips send analyst|ds or omit; UI labels are never query values"
  - "Pattern: zero-hit CTA clears role only and re-runs the same query (D-65)"

requirements-completed: [KNOW-02, KNOW-03, KNOW-04]

coverage:
  - id: D1
    description: Role chips Analyst / DS / Все replace selects; server accepts only analyst|ds and treats a blank role as unrestricted
    requirement: KNOW-02
    verification:
      - kind: unit
        ref: tests/unit/test_search_knowledge.py#test_search_knowledge_role_analyst_excludes_ds_only_materials
        status: pass
      - kind: unit
        ref: tests/unit/test_http_knowledge_search.py#test_knowledge_search_invalid_role_returns_400
        status: pass
      - kind: unit
        ref: tests/unit/test_search_knowledge.py#test_search_knowledge_empty_role_filter_is_unrestricted
        status: pass
    human_judgment: false
  - id: D2
    description: Changing the DS chip re-runs search without «Найти» and the hit opens /materials/{slug}
    requirement: KNOW-03
    verification:
      - kind: e2e
        ref: tests/web-app.spec.js#filters knowledge by the Analyst chip and opens a DS hit
        status: pass
    human_judgment: false
  - id: D3
    description: Analyst zero-hit shows «Ничего не нашли» and «Сбросить фильтр» clears role only, keeps the query, and does not substitute ds materials
    requirement: KNOW-04
    verification:
      - kind: unit
        ref: tests/unit/test_search_knowledge.py#test_search_knowledge_analyst_empty_does_not_backfill_ds_materials
        status: pass
      - kind: e2e
        ref: tests/web-app.spec.js#keeps the query when resetting a role filter that found nothing
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-09-21
status: complete
---

# Phase 4 Plan 3: Role Chips and Honest Empty Search Summary

**Analyst/DS/Все chips filter knowledge search on the server, and an empty analyst result resets only the role without substituting other materials**

## Performance

- **Duration:** 15 min
- **Started:** 2026-09-21T04:46:00Z
- **Completed:** 2026-09-21T05:01:12Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Role chips Analyst / DS / Все send `analyst`, `ds`, or no role; tag, format, and topic selects stay off the knowledge page (D-62, D-63, KNOW-02).
- A chip change re-runs search immediately when the trimmed query is non-empty, and does nothing but update the chip when the query is blank (D-64).
- Roles outside `analyst|ds` return 400 `invalid_role`. The page toasts «Фильтр недоступен» and falls back to «Все» without clearing the query (T-04-05).
- An analyst filter with no matches returns an empty list — it does not backfill ds materials (KNOW-04). «Сбросить фильтр» clears the role only and re-runs the same query (D-65).
- A DS hit still opens `/materials/{slug}` (KNOW-03). Blank and overlong query guards from 04-02 are unchanged.

## Task Commits

Each task was committed atomically:

1. **Task 1: Role chip filter — server allowlist + chip re-run** — `d58800a` (test), `4cb2843` (feat)
2. **Task 2: Zero-hit honesty + reset filter only + DS material link** — `133b030` (test), `26c2f79` (feat)

## Files Created/Modified

- `backend/src/backend/application/use_cases/search_knowledge.py` — allowlist `analyst|ds`; blank role is unrestricted
- `backend/src/backend/interface/http/routes/knowledge.py` — search contract documents 400 `invalid_role`
- `web/src/pages/KnowledgePage.jsx` — role chips, invalid-role toast, «Сбросить фильтр»
- `web/src/services/knowledgeApi.js` — maps `invalid_role` to «Фильтр недоступен»
- `web/src/utils/filters.js` — role-only helper; tag/format/topic no longer applied
- `web/src/data/mock.js` — analyst-only material for role membership
- `tests/unit/test_search_knowledge.py` — role allowlist and no cross-role backfill
- `tests/unit/test_http_knowledge_search.py` — HTTP role filter and 400 `invalid_role`
- `tests/web-app.spec.js` — retired tag-facet cases; chip, reset, and DS link specs

## Decisions Made

- Invalid role is `400 invalid_role`, not a silent empty 200. The SPA toasts «Фильтр недоступен» and resets the chip to «Все».
- Null, empty, and whitespace `role` mean unrestricted («Все»).
- `filterMaterials` ignores tag, format, and topic so a leftover client helper cannot widen Phase 4 search (D-63).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Retired «Загрузить ещё» Playwright case**
- **Found during:** Task 2 (zero-hit honesty)
- **Issue:** The old spec expected «Загрузить ещё» on landing. 04-02 renamed pagination to «Показать ещё», and the mock catalog (8 materials) is smaller than the page size (10), so that button never renders.
- **Fix:** The spec now searches for RAG, asserts the retired label is absent, and leaves full «Показать ещё» coverage to 04-09.
- **Files modified:** `tests/web-app.spec.js`
- **Verification:** Playwright knowledge cases passed (3/3)
- **Committed in:** `133b030`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Suite stays green. Pagination behavior is still covered by unit `has_more` tests; the visual «Показать ещё» path remains a 04-09 concern.

## Issues Encountered

- The no-backfill behavior was already enforced by membership filtering in `InMemoryKnowledgeChunkRepository` (04-01). The new unit test passed on first run and locks KNOW-04 rather than adding a second filter.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- KNOW-02…04 role chips and empty-state honesty are in the SPA and the use-case.
- 04-09 still owns the fuller Playwright honesty gate (blank/overlong, overflow «Показать ещё»).
- Blank and overlong guards were not changed.

## Self-Check: PASSED

- FOUND: backend/src/backend/application/use_cases/search_knowledge.py
- FOUND: web/src/pages/KnowledgePage.jsx
- FOUND: tests/unit/test_search_knowledge.py
- FOUND: d58800a, 4cb2843, 133b030, 26c2f79

---
*Phase: 04-knowledge-razbory*
*Completed: 2026-09-21*
