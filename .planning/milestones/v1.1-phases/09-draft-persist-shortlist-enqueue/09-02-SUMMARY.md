---
phase: 09-draft-persist-shortlist-enqueue
plan: 02
subsystem: ingestion
tags: [persist-port, ingest-error, slugify, fake, use-case]

requires:
  - phase: 09-draft-persist-shortlist-enqueue
    provides: MaterialDraft.roles closed set
  - phase: 08-deepseek-article-templates
    provides: MaterialDraft, IngestError, mapper pattern

provides:
  - PersistPort Protocol and frozen PersistResult
  - persist_draft use-case that writes slug and reading_minutes then calls the port
  - generate_slug and estimate_reading_minutes helpers
  - DraftPersistError taxonomy and map_persist_error
  - FakeDraftPersister with call spy, stored map, and scripted failures

affects:
  - 09-03 (SupabaseDraftPersister implements PersistPort)
  - 09-04 (composition wiring and CAP-02 persist spy)
  - 10 (CLI prints PersistResult fields)

actuals:
  tokens: 4100
  tasks: 3
  commits: 7

tech-stack:
  added:
    - python-slugify>=8.0,<9
  patterns:
    - PersistPort is a runtime_checkable Protocol; use-case depends only on the port
    - map_persist_error locks PERSIST_REASONS and a four-key context allowlist
    - FakeDraftPersister stores first PersistResult per video_id and returns it on repeat

key-files:
  created:
    - ingestion-service/src/ingestion_service/application/ports/persist.py
    - ingestion-service/src/ingestion_service/application/use_cases/persist_draft.py
    - ingestion-service/src/ingestion_service/domain/material_completion.py
    - ingestion-service/src/ingestion_service/adapters/persist_errors.py
    - ingestion-service/src/ingestion_service/mapping/persist.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - tests/unit/test_persist_port.py
    - tests/unit/test_persist_error_mapping.py
    - tests/unit/test_material_completion.py
    - tests/unit/test_persist_draft_use_case.py
  modified:
    - data-collection/src/data_collection/dto/material_draft.py
    - ingestion-service/src/ingestion_service/mapping/__init__.py
    - ingestion-service/pyproject.toml
    - uv.lock

key-decisions:
  - PersistResult is frozen with exactly material_id, slug, batch_id, rank (D-03).
  - persist_draft always calls port.persist; FakeDraftPersister owns idempotent stored lookup (D-11).
  - generate_slug is slugify(title)[:50] plus -{video_id}; reading_minutes is max(1, ceil(words/200)).
  - PERSIST_REASONS is the locked five-reason set; context keys are only video_id, slug, batch_id, reason.

patterns-established:
  - "Ingestion persist errors map at the mapper, not in the use-case."
  - "MaterialDraft.slug defaults to empty string so assemble_material_draft still constructs; persist_draft overwrites slug and reading_minutes."

requirements-completed:
  - PERS-01
  - PERS-02

coverage:
  - id: D1
    description: "PersistPort.persist returns PersistResult; FakeDraftPersister records calls, returns a scripted result, raises scripted failures, and stores one result per video_id."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_persist_port.py#test_concrete_persist_port_returns_persist_result"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_port.py#test_fake_records_call_and_returns_scripted_result"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_port.py#test_fake_raises_scripted_error_and_still_records_call"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_port.py#test_fake_repeat_video_id_returns_stored_result_without_second_entry"
        status: pass
    human_judgment: false
  - id: D2
    description: "DraftPersistError subtypes map to locked persist reasons with allowlisted context and no secret or raw Postgres leakage."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_persist_error_mapping.py#test_map_persist_error_subtype_to_locked_reason"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_error_mapping.py#test_persist_reasons_is_exact_locked_set"
        status: pass
    human_judgment: false
  - id: D3
    description: "persist_draft writes deterministic slug and reading_minutes, always calls the port, and two calls with the same video_id return one stored PersistResult."
    requirement: PERS-02
    verification:
      - kind: unit
        ref: "tests/unit/test_material_completion.py#test_generate_slug_transliterates_title_and_appends_video_id"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_draft_use_case.py#test_persist_draft_returns_port_result_and_enriches_draft"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_draft_use_case.py#test_persist_draft_twice_same_video_id_returns_same_result"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-09-27
status: complete
---

# Phase 9 Plan 02: Persist port + fake + mapper Summary

**PersistPort, PersistResult, DraftPersistError mapping, slug/reading-minutes helpers, FakeDraftPersister, and persist_draft locked before any Supabase adapter**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-27T15:20:56Z
- **Completed:** 2026-09-27T15:26:00Z
- **Tasks:** 3
- **Files modified:** 15

## Accomplishments
- Locked `PersistPort.persist(MaterialDraft) -> PersistResult` with a frozen four-field result
- Mapped `DraftPersistError` subtypes to `IngestError(stage=persist)` with `PERSIST_REASONS` and a context allowlist
- `persist_draft` overwrites `slug` and `reading_minutes`, always calls the port, and does not pre-check `video_id`

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: PersistPort + fake tests** - `aeec34b` (test)
2. **Task 1 GREEN: PersistPort, PersistResult, FakeDraftPersister** - `c40966b` (feat)
3. **Task 2 RED: persist error mapping tests** - `c4f9fb5` (test)
4. **Task 2 GREEN: DraftPersistError taxonomy + map_persist_error** - `ba8c6ba` (feat)
5. **Task 3 RED: slug completion + persist_draft tests** - `d3969db` (test)
6. **Task 3 GREEN: MaterialDraft fields, helpers, persist_draft** - `6fe3bdc` (feat)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified
- `ingestion-service/src/ingestion_service/application/ports/persist.py` - PersistPort Protocol and PersistResult
- `ingestion-service/src/ingestion_service/application/use_cases/persist_draft.py` - persist_draft use-case
- `ingestion-service/src/ingestion_service/domain/material_completion.py` - generate_slug and estimate_reading_minutes
- `ingestion-service/src/ingestion_service/adapters/persist_errors.py` - DraftPersistError subtypes
- `ingestion-service/src/ingestion_service/mapping/persist.py` - map_persist_error and PERSIST_REASONS
- `ingestion-service/src/ingestion_service/tests_support/fakes.py` - FakeDraftPersister
- `data-collection/src/data_collection/dto/material_draft.py` - slug="" and reading_minutes=1 defaults
- `ingestion-service/pyproject.toml` / `uv.lock` - python-slugify>=8.0,<9
- `tests/unit/test_persist_port.py` - port and fake contract
- `tests/unit/test_persist_error_mapping.py` - locked reasons and redaction
- `tests/unit/test_material_completion.py` - slug and reading minutes
- `tests/unit/test_persist_draft_use_case.py` - enrichment and D-11 no pre-check

## Decisions Made
- Application persist contract lives in `ingestion-service`; no Supabase imports in domain, use-case, or fake.
- Idempotent re-run behavior is the fake/port stand-in returning the first stored `PersistResult`; `persist()` may be invoked twice.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] DraftPersistError base class shipped with Task 1 GREEN**
- **Found during:** Task 1 GREEN (FakeDraftPersister type hint)
- **Issue:** The fake's `failures` map is `dict[str, DraftPersistError]`; Task 2 owns the taxonomy file.
- **Fix:** Added the base `DraftPersistError` in Task 1 GREEN so the fake and its tests type-check; Task 2 added subtypes and the mapper.
- **Files modified:** `ingestion-service/src/ingestion_service/adapters/persist_errors.py`
- **Verification:** `uv run pytest tests/unit/test_persist_port.py` exits 0
- **Committed in:** `c40966b` (Task 1 GREEN)

---

**Total deviations:** 1 auto-fixed (1 blocking).
**Impact on plan:** Required for the Task 1 fake contract. No scope creep.

## Issues Encountered
- Full `uv run pytest` is 538 passed / 1 failed: pre-existing `test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (noted in 09-01). Unrelated to persist; not fixed.
- Context7 has no `python-slugify` library ID; dependency added via `uv add --package ingestion-service` as specified, and slug output was checked locally.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
Ready for 09-03 (migration 007 + SupabaseDraftPersister). PersistPort, error mapping, and persist_draft are locked.

## Self-Check: PASSED
- key-files.created exist on disk
- `git log --oneline --all --grep="09-02"` returns 6 commits before this SUMMARY
- Task acceptance criteria and plan focused suite: 25 passed
- Plan verification focused command: 25 passed; full unit suite 538 passed / 1 pre-existing fail

---
*Phase: 09-draft-persist-shortlist-enqueue*
*Completed: 2026-09-27*
