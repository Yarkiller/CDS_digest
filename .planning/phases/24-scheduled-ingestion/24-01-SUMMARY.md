---
phase: 24-scheduled-ingestion
plan: 01
subsystem: ingestion
tags: [youtube-atom, ingest-collect, cursor, httpx, typer, tdd]

requires:
  - phase: 23-admin-managed-ingest-sources
    provides: pipeline_ingest_sources table + admin CRUD for enabled sources
provides:
  - VideoRef/FeedListing/VideoListProvider + YouTubeFeedAdapter (Atom, 1 MiB cap)
  - is_newer/advance_cursor domain helpers
  - CollectSourceReader + SupabaseCollectSourceReader
  - run_collect_batch + ingest-collect CLI entry point
  - INGEST_TEMPLATE / INGEST_MAX_VIDEOS_PER_SOURCE settings
affects:
  - 24-02 (window/limit/isolation)
  - 24-03 (due gate + migration 013 cursor columns)
  - 24-04 (systemd units + ING-07 guard)

actuals:
  tokens: 22866
  tasks: 2
  commits: 3

plan_head_before: 874ea23aea37372606d3039d4d4a608c798ba8e7
plan_head_after: af1939102df447836452366d1456f3a3acd57b01

tech-stack:
  added: []
  patterns:
    - injected httpx.AsyncClient + stream/aiter_bytes with 1 MiB cap
    - separate Typer app for ingest-collect (zero diff on cli.py)
    - domain advance_cursor before adapter write (monotonic)

key-files:
  created:
    - data-collection/src/data_collection/dto/video_ref.py
    - data-collection/src/data_collection/ports/video_list_provider.py
    - data-collection/src/data_collection/adapters/youtube_feed.py
    - data-collection/src/data_collection/errors/feed.py
    - ingestion-service/src/ingestion_service/domain/schedule.py
    - ingestion-service/src/ingestion_service/application/ports/collect_sources.py
    - ingestion-service/src/ingestion_service/adapters/supabase_collect_sources.py
    - ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
    - ingestion-service/src/ingestion_service/collect_cli.py
    - tests/unit/test_youtube_feed_adapter.py
    - tests/unit/test_schedule_due.py
    - tests/unit/test_collect_batch.py
    - tests/unit/test_collect_cli_contract.py
    - tests/unit/test_supabase_collect_sources_contract.py
  modified:
    - data-collection/src/data_collection/__init__.py
    - data-collection/src/data_collection/ports/__init__.py
    - ingestion-service/src/ingestion_service/composition/settings.py
    - ingestion-service/src/ingestion_service/composition/clients.py
    - ingestion-service/src/ingestion_service/tests_support/fakes.py
    - ingestion-service/pyproject.toml
    - ingestion-service/.env.example
    - tests/unit/test_data_collection_public_api.py
    - tests/unit/test_ingestion_settings.py
    - tests/unit/test_ingestion_env_example.py

key-decisions:
  - "Threat mitigations T-24-01/T-24-02 (DTD scan + 1 MiB cap) landed in tracer GREEN so failure-matrix tests could pin them without a second production commit"
  - "Blank INGEST_TEMPLATE defaults to lecture (same blank-env idiom as MAX_TRANSCRIPT_CHARS); invalid non-blank values raise ConfigurationError"

patterns-established:
  - "FakeFeed / FakeCollectSourceReader live in ingestion_service.tests_support.fakes with call spies"
  - "collect_cli.build_collect_deps is the CliRunner monkeypatch seam (mirrors build_ingest_deps)"

requirements-completed: [ING-02, ING-05, ING-07]

coverage:
  - id: D1
    description: "Enabled source Atom feed → VideoRef → run_ingest_pipeline(bare video_id, on_stage=None) → cursor advance + stdout summary"
    requirement: ING-02
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_run_collect_batch_ingests_one_new_video_and_advances_cursor"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_happy_path_summary_stdout"
        status: pass
    human_judgment: false
  - id: D2
    description: "Async VideoListProvider with injected httpx.AsyncClient; channel_id/playlist_id query params"
    requirement: ING-02
    verification:
      - kind: unit
        ref: "tests/unit/test_youtube_feed_adapter.py#test_list_recent_channel_sends_channel_id_query"
        status: pass
      - kind: unit
        ref: "tests/unit/test_youtube_feed_adapter.py#test_list_recent_playlist_sends_playlist_id_query"
        status: pass
    human_judgment: false
  - id: D3
    description: "Monotonic is_newer/advance_cursor and batch writes domain result not raw candidate"
    requirement: ING-05
    verification:
      - kind: unit
        ref: "tests/unit/test_schedule_due.py#test_is_newer_same_second_tie_break_by_video_id"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_batch.py#test_run_collect_batch_uses_domain_advance_cursor_not_raw_candidate"
        status: pass
    human_judgment: false
  - id: D4
    description: "FeedSkip diagnostics one stderr line each; videos_failed unchanged; separate ingest-collect entry point; cli.py untouched"
    requirement: ING-07
    verification:
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_collect_cli_feed_skip_goes_to_stderr"
        status: pass
      - kind: unit
        ref: "tests/unit/test_collect_cli_contract.py#test_pyproject_registers_ingest_collect_entry_point"
        status: pass
      - kind: unit
        ref: "tests/unit/test_cli_ingest_contract.py"
        status: pass
    human_judgment: false
  - id: D5
    description: "Deterministic FeedError reasons for status/network/doctype/oversize/invalid XML and per-entry skips"
    requirement: ING-02
    verification:
      - kind: unit
        ref: "tests/unit/test_youtube_feed_adapter.py"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-10-18
status: complete
---

# Phase 24 Plan 01: Ingest-collect Atom tracer Summary

**`ingest-collect` vertical slice: Atom feed → VideoRef → `run_ingest_pipeline` (bare id, `on_stage=None`) → monotonic cursor → two-line stdout summary, with deterministic FeedError/FeedSkip taxonomy.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-18T11:19:39Z
- **Completed:** 2026-10-18T11:29:58Z
- **Tasks:** 2/2
- **Files modified:** 24

## Accomplishments

- Production path from enabled `pipeline_ingest_sources` through YouTube Atom listing into the existing ingest pipeline without touching `cli.py` or `run_ingest_pipeline`.
- Cursor helpers `is_newer` / `advance_cursor` plus batch write-through of the domain result (no rollback on older candidates).
- Failure-matrix pins for feed_status/network/doctype/too_large/invalid_xml and per-entry FeedSkip reasons (D-25/D-26).

## Task Commits

1. **Task 1 RED:** `63ba265` — `test(24-01): add failing tests for ingest-collect tracer`
2. **Task 1 GREEN:** `26d7b4c` — `feat(24-01): implement ingest-collect Atom-feed tracer slice`
3. **Task 2:** `af19391` — `test(24-01): pin Atom feed failure-matrix reasons`

_Note: Task 2 needed no production commit — mitigations already in tracer GREEN._

## Files Created/Modified

- `data-collection/.../adapters/youtube_feed.py` — stream + 1 MiB cap + local-name parse
- `ingestion-service/.../collect_cli.py` — `ingest-collect` Typer entry
- `ingestion-service/.../collect_batch.py` — batch orchestration
- `ingestion-service/.../domain/schedule.py` — cursor pure functions
- Unit contracts under `tests/unit/test_*collect*`, `test_youtube_feed_adapter.py`, `test_schedule_due.py`

## Decisions Made

- Landed T-24-01/T-24-02 mitigations in the tracer GREEN commit so Task 2 could be a characterization pin without a second feat commit.
- Blank `INGEST_TEMPLATE` defaults to `lecture`; non-blank invalid values raise `ConfigurationError`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical] Full feed failure taxonomy in tracer GREEN**
- **Found during:** Task 1 GREEN (threat_model mitigations for `parse_feed` / `_read_capped`)
- **Issue:** Plan split DTD/cap/skip reasons into Task 2, but threat register marks them mitigate on Task 1 files.
- **Fix:** Implemented full `_read_capped` + `parse_feed` skips/reasons in tracer GREEN; Task 2 only added tests.
- **Files modified:** `data-collection/src/data_collection/adapters/youtube_feed.py`
- **Commit:** `26d7b4c`

**2. [Rule 1 - Bug] Contract assert expected `is_enabled` in SELECT columns**
- **Found during:** Task 1 GREEN
- **Issue:** Plan/adapter filters via `.eq("is_enabled", True)`; select list correctly omits the column.
- **Fix:** Assert select string + filter pair instead of substring in selected columns.
- **Files modified:** `tests/unit/test_supabase_collect_sources_contract.py`
- **Commit:** `26d7b4c`

**Total deviations:** 2 auto-fixed (1 Rule 2, 1 Rule 1). **Impact:** none on contracts; Task 2 became test-only.

## TDD Gate Compliance

- RED commit present: `test(24-01): …` (`63ba265`)
- GREEN commit present: `feat(24-01): …` (`26d7b4c`)
- RED phase failed on missing production symbols (ImportError) before GREEN — matches plan wording; `workflow.tdd_mode` is false so TAP RED-evidence gate was not enforced.

## Known Stubs

None.

## Threat Flags

None beyond plan `<threat_model>` (mitigations implemented).

## Issues Encountered

None.

## Next Phase Readiness

Ready for `24-02` (window selection, limit, error isolation / exit codes).

## Self-Check: PASSED

- Created files exist on disk (DTO/port/adapter/CLI/use-case/domain).
- Commits `63ba265`, `26d7b4c`, `af19391` present in `git log`.
- Verify commands: 104 unit tests green for tracer suite + public API + cli ingest contract; feed adapter 17 passed after failure matrix.
