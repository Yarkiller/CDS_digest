---
phase: 13-admin-material-email-preview-honesty
plan: 01
subsystem: api
tags: [fastapi, shortlist, admin-dto, pydantic, supabase, tdd, adux-01]

requires:
  - phase: 12-admin-shortlist-empty-batch-contract
    provides: Empty-batch AdminShortlistResponse shapes + FIX-01 lock + extra=forbid posture
provides:
  - "Enriched GET /admin/shortlist item DTO (body_markdown, provenance_label, slug, reading_minutes, char_count, word_count)"
  - "Named proof test_admin_shortlist_returns_full_items"
  - "Widened ShortlistRepository materials join + in-memory set_decision copy-through"
  - "Updated 12-FIX-01-LOCK.md full-item schema (D-03)"
affects:
  - 13-03 Admin material modal (FE consumes full shortlist DTO)
  - 13-02 email HTML preview (shares admin shortlist material fields)

actuals:
  tokens: 3932
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "material_counts(body) → (char_count, word_count) via len + str.split()"
    - "Additive AdminShortlistItemResponse fields under ConfigDict(extra=forbid)"
    - "Enrich via ShortlistRepository.get_current_batch join only (no materials-by-id)"

key-files:
  created: []
  modified:
    - tests/unit/test_http_admin.py
    - backend/src/backend/domain/shortlist.py
    - backend/src/backend/application/use_cases/get_admin_shortlist.py
    - backend/src/backend/interface/http/routes/admin.py
    - backend/src/backend/tests_support/in_memory.py
    - supabase-integration/src/supabase_integration/shortlist_repository.py
    - .planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md

key-decisions:
  - "Counts computed in get_admin_shortlist from body_markdown; reading_minutes passed through from stored join column"
  - "ShortlistItem seed fields landed in RED commit so the HTTP key assert fails intentionally (not TypeError)"

patterns-established:
  - "Full-item shortlist proofs use required-key asserts (FIX-01 D-08), never full-body JSON equality"
  - "Phase 13 item enrichment stays on existing admin shortlist + require_admin"

requirements-completed: [ADUX-01]

coverage:
  - id: D1
    description: "GET /admin/shortlist non-empty items include body_markdown, provenance_label, slug, reading_minutes, char_count, word_count"
    requirement: ADUX-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_returns_full_items"
        status: pass
    human_judgment: false
  - id: D2
    description: "Phase 12 empty-batch shapes remain green after item schema growth"
    requirement: ADUX-01
    verification:
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_no_batches_returns_null_batch_id"
        status: pass
      - kind: unit
        ref: "tests/unit/test_http_admin.py#test_admin_shortlist_empty_unsent_batch_returns_batch_id"
        status: pass
    human_judgment: false
  - id: D3
    description: "FIX-01 lock documents full AdminShortlistItem additive fields under extra=forbid"
    requirement: ADUX-01
    verification:
      - kind: other
        ref: "rg body_markdown|provenance_label|char_count|word_count|reading_minutes on 12-FIX-01-LOCK.md"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-10-02
status: complete
plan_head_before: 2dff4dd1646372965eb08d5cb4c6ae7aebfa7950
plan_head_after: fd1e6cc6eeddf3a3385e4786dafd1c3fe4237284
---

# Phase 13 Plan 01: Enriched shortlist item DTO Summary

**GET /admin/shortlist items now carry full material preview fields (body, provenance, slug, reading minutes, char/word counts) proven by `test_admin_shortlist_returns_full_items`.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-10-02T19:16:20Z
- **Completed:** 2026-10-02T19:23:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- End-to-end enriched shortlist item DTO: repository join → domain → use-case counts → HTTP response
- Named ADUX-01 proof green; Phase 12 empty-batch proofs still green
- FIX-01 lock grown with Shape 3 full-item schema without collapsing empty shapes

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): End-to-end enriched GET /admin/shortlist full-item contract** - `e5d005f` (test)
2. **Task 1 (GREEN): End-to-end enriched GET /admin/shortlist full-item contract** - `0e1d807` (feat)
3. **Task 2: Grow FIX-01 lock item schema for full DTOs** - `fd1e6cc` (docs)

## TDD Gate Compliance

| Gate | Commit | Evidence |
|------|--------|----------|
| RED | `e5d005f` | `test_admin_shortlist_returns_full_items` failed with `AssertionError: missing required key: body_markdown`; `check tdd-red-evidence` → `RED_EVIDENCE_OK` |
| GREEN | `0e1d807` | Same three node ids pass (`full_items` + Phase 12 empty pair) |
| REFACTOR | n/a | Not needed |

## Files Created/Modified

- `tests/unit/test_http_admin.py` — named proof `test_admin_shortlist_returns_full_items`
- `backend/src/backend/domain/shortlist.py` — additive ShortlistItem / AdminShortlistItem fields + `material_counts`
- `backend/src/backend/application/use_cases/get_admin_shortlist.py` — map preview fields + counts
- `backend/src/backend/interface/http/routes/admin.py` — AdminShortlistItemResponse additive fields; `_to_response`
- `backend/src/backend/tests_support/in_memory.py` — set_decision copies new material fields
- `supabase-integration/src/supabase_integration/shortlist_repository.py` — widened materials select + `_item_from_row`
- `.planning/phases/12-admin-shortlist-empty-batch-contract/12-FIX-01-LOCK.md` — Shape 3 full-item DTO docs (D-03)

## Decisions Made

- Compute `char_count`/`word_count` in the use-case from `body_markdown`; pass stored `reading_minutes` from the join (D-02 / RESEARCH A1)
- Keep enrichment on existing `GET /admin/shortlist` + `Depends(require_admin)`; no materials-by-id route (D-01 / T-13-01)
- RED commit included additive `ShortlistItem` defaults so the seed constructs and the HTTP assertion fails intentionally

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Pytest JUnit XML trips the Surefire name parser (`classname` contains `name=`); RED evidence persisted in TAP shape for `check tdd-red-evidence` while the live pytest AssertionError remained the intentional failure.
- Unrelated WIP in `in_memory.py` was temporarily isolated so the GREEN commit only staged set_decision field copy-through; WIP restored after commit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Wave-1 tracer locked the full shortlist item payload. Plans 13-02 (email HTML) and 13-03 (material modal) can consume the enriched DTO without a second fetch.

## Self-Check: PASSED

- FOUND: `tests/unit/test_http_admin.py` (`test_admin_shortlist_returns_full_items`)
- FOUND: `e5d005f`, `0e1d807`, `fd1e6cc`
- FOUND: Phase 12 empty proofs still collectable/green after model growth

---
*Phase: 13-admin-material-email-preview-honesty*
*Completed: 2026-10-02*
