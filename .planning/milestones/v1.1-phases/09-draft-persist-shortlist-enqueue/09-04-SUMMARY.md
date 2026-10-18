---
phase: 09-draft-persist-shortlist-enqueue
plan: 04
subsystem: ingestion
tags: [composition, settings, supabase-client, persist, shortlist, cap-02]

requires:
  - phase: 09-draft-persist-shortlist-enqueue
    provides: PersistPort, persist_draft, FakeDraftPersister, SupabaseDraftPersister
  - phase: 07-captions-adapter
    provides: CaptionsError, FakeTranscriptProvider, CAP-02 deferred persist spy

provides:
  - Settings.supabase_url, Settings.supabase_secret_key, Settings.shortlist_batch_size
  - build_supabase_service_client and build_supabase_draft_persister factories
  - ingestion-service/.env.example with empty secret placeholders
  - In-memory idempotency, overflow, and batch_sent proofs
  - CAP-02 deferred proof: captions/article failure → persist.calls == []

affects:
  - 10 (CLI composition imports Settings and factories)

actuals:
  tokens: 6027
  tasks: 4
  commits: 8
plan_head_before: 6208e0a95c5d5f4f5e3c9435adf73253d448c134

tech-stack:
  added: []
  patterns:
    - Composition owns service-role wiring; adapters do not read os.environ
    - Blank SUPABASE_URL or SUPABASE_SECRET_KEY raises ConfigurationError before create_client
    - Persist idempotency and overflow are proven at the port boundary with an in-memory fake

key-files:
  created:
    - ingestion-service/.env.example
    - tests/unit/test_ingestion_clients.py
    - tests/unit/test_persist_idempotency_overflow.py
    - tests/unit/test_captions_failure_zero_persist.py
  modified:
    - ingestion-service/src/ingestion_service/composition/settings.py
    - ingestion-service/src/ingestion_service/composition/clients.py
    - ingestion-service/src/ingestion_service/composition/__init__.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - tests/unit/test_ingestion_settings.py

key-decisions:
  - Settings.from_env({}) still succeeds; supabase fields stay None; shortlist_batch_size defaults to 5.
  - build_supabase_service_client never calls create_client when url or key is blank.
  - D-11 stands: persist_draft has no Python video_id pre-check; the fake returns the stored PersistResult.
  - CAP-02 deferred proof is a direct boundary test, not a CLI orchestrator.

patterns-established:
  - "SHORTLIST_BATCH_SIZE is a positive integer validated like MAX_TRANSCRIPT_CHARS."
  - "A latest batch with sent_at set is skipped; overflow opens a new unsent batch at rank 1."
  - "CaptionsError or ArticleError must leave FakeDraftPersister.calls empty."

requirements-completed:
  - PERS-01
  - PERS-02

coverage:
  - id: D1
    description: "Settings loads optional Supabase credentials and validates SHORTLIST_BATCH_SIZE as a positive integer with default 5."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py#test_settings_from_env_unset_supabase_fields_and_default_batch_size"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingestion_settings.py#test_invalid_shortlist_batch_size_raises_configuration_error"
        status: pass
    human_judgment: false
  - id: D2
    description: "Composition exports service-role and persister factories; .env.example documents placeholders with no live key."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_ingestion_clients.py#test_build_supabase_service_client_rejects_blank_and_does_not_create_client"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingestion_clients.py#test_build_supabase_draft_persister_uses_settings_batch_size"
        status: pass
      - kind: unit
        ref: "tests/unit/test_ingestion_clients.py#test_ingestion_env_example_documents_supabase_placeholders"
        status: pass
    human_judgment: false
  - id: D3
    description: "persist_draft is idempotent on youtube_video_id, overflows a full unsent batch, counts rejected items, and skips sent batches."
    requirement: PERS-02
    verification:
      - kind: unit
        ref: "tests/unit/test_persist_idempotency_overflow.py#test_persist_draft_twice_same_video_id_is_idempotent"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_idempotency_overflow.py#test_overflow_creates_new_unsent_batch_at_capacity"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_idempotency_overflow.py#test_rejected_item_counts_toward_batch_capacity"
        status: pass
      - kind: unit
        ref: "tests/unit/test_persist_idempotency_overflow.py#test_batch_sent_skips_latest_sent_batch"
        status: pass
    human_judgment: false
  - id: D4
    description: "A captions or article failure leaves FakeDraftPersister.calls empty (Phase 7 CAP-02 deferred proof)."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_captions_failure_zero_persist.py#test_captions_failure_leaves_persist_calls_empty"
        status: pass
      - kind: unit
        ref: "tests/unit/test_captions_failure_zero_persist.py#test_article_failure_leaves_persist_calls_empty"
        status: pass
    human_judgment: false

duration: 7min
completed: 2026-09-27
status: complete
---

# Phase 9 Plan 04: Composition wiring + CAP-02 deferred proof Summary

**Settings and composition factories wire the Supabase service-role client and SupabaseDraftPersister; in-memory proofs lock idempotency, overflow, batch_sent skip, and CAP-02 zero persist rows**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-27T15:55:26Z
- **Completed:** 2026-09-27T16:02:25Z
- **Tasks:** 4
- **Files modified:** 9

## Accomplishments
- `Settings.from_env({})` still succeeds; `supabase_url` / `supabase_secret_key` stay `None`; `shortlist_batch_size` defaults to 5 and rejects `0`, `-1`, `abc`, `5.5`
- `build_supabase_service_client` raises `ConfigurationError` before `create_client` when url or key is blank; `build_supabase_draft_persister` uses `settings.shortlist_batch_size`
- `ingestion-service/.env.example` documents `SUPABASE_URL=`, `SUPABASE_SECRET_KEY=`, and `SHORTLIST_BATCH_SIZE=5` with no live key
- Idempotent re-run returns one stored `PersistResult` while `persist()` may run twice; a full or sent batch opens a new unsent batch at rank 1
- CAP-02: `CaptionsUnavailable` or article failure leaves `FakeDraftPersister.calls == []`

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: supabase settings tests** - `45c3d75` (test)
2. **Task 1 GREEN: Settings supabase + batch size** - `f564a24` (feat)
3. **Task 2 RED: client factory tests** - `6f1759d` (test)
4. **Task 2 GREEN: factories + .env.example** - `c800e0e` (feat)
5. **Task 3 RED: idempotency/overflow tests** - `d024b08` (test)
6. **Task 3 GREEN: BatchTrackingFakePersister** - `a8334a0` (feat)
7. **Task 4 RED: CAP-02 zero-persist proof** - `45c72a8` (test)
8. **Task 4 GREEN: captions/article boundary helpers** - `0134f3d` (feat)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified
- `ingestion-service/src/ingestion_service/composition/settings.py` - supabase fields + `_shortlist_batch_size`
- `ingestion-service/src/ingestion_service/composition/clients.py` - `build_supabase_service_client` and `build_supabase_draft_persister`
- `ingestion-service/src/ingestion_service/composition/__init__.py` - export the new factories
- `ingestion-service/.env.example` - empty secret placeholders and batch-size default
- `ingestion-service/src/ingestion_service/tests_support/fakes.py` - `BatchTrackingFakePersister`
- `tests/unit/test_ingestion_settings.py` - supabase and batch-size validation
- `tests/unit/test_ingestion_clients.py` - factory and env-example contract
- `tests/unit/test_persist_idempotency_overflow.py` - idempotency, overflow, rejected capacity, batch_sent
- `tests/unit/test_captions_failure_zero_persist.py` - CAP-02 deferred persist spy

## Decisions Made
- Composition owns all wiring; adapters still do not read `os.environ`.
- D-11 stands: no Python pre-check in `persist_draft`; the fake stores one result per `video_id`.
- CAP-02 is proven at the captions/article → persist-port boundary, not via a Typer orchestrator.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] BatchTrackingFakePersister lives in tests_support/fakes.py**
- **Found during:** Task 3
- **Issue:** Top-level `files_modified` omitted `fakes.py`, but the task `<files>` list includes it as the reusable helper location.
- **Fix:** Implemented the helper in `ingestion_service.tests_support.fakes` so overflow/batch_sent proofs share the existing fake package.
- **Files modified:** `ingestion-service/src/ingestion_service/tests_support/fakes.py`
- **Verification:** `uv run pytest tests/unit/test_persist_idempotency_overflow.py` exits 0
- **Committed in:** `a8334a0` (Task 3 GREEN)

---

**Total deviations:** 1 auto-fixed (1 missing critical).
**Impact on plan:** Required for the reusable overflow fake. No scope creep. Migration 007 was not re-applied.

## Issues Encountered
- Full `uv run pytest` is 576 passed / 1 failed: pre-existing `test_http_admin.py::test_admin_shortlist_empty_batch_returns_200_empty_items` (noted in 09-01…09-03). Unrelated to composition/persist; not fixed.
- Plan-focused verification: 59 passed.

## User Setup Required
None - no external service configuration required. Migration 007 is already live from 09-03.

## Next Phase Readiness
Phase 9 plans are complete. Ready for Phase 10 (CLI composition & UAT). Settings, factories, and `.env.example` are the composition contract the Typer CLI will import.

## TDD Gate Compliance
All four tasks have RED `test(09-04)` then GREEN `feat(09-04)` commits. RED evidence records in `.planning/tmp/09-04-task{1-4}-red-evidence.json` verified `RED_EVIDENCE_OK`.

## Self-Check: PASSED
- key-files.created exist on disk
- `git log --oneline --all --grep="09-04"` returns 8 commits before this SUMMARY
- Task acceptance criteria and plan focused suite: 59 passed
- Plan verification focused command: 59 passed; full unit suite 576 passed / 1 pre-existing fail

---
*Phase: 09-draft-persist-shortlist-enqueue*
*Completed: 2026-09-27*
