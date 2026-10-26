---
phase: 10-cli-composition-uat
reviewed: 2026-10-01T19:30:00Z
depth: deep
files_reviewed: 16
files_reviewed_list:
  - ingestion-service/src/ingestion_service/cli.py
  - ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
  - ingestion-service/src/ingestion_service/application/ports/persist.py
  - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
  - ingestion-service/src/ingestion_service/composition/clients.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - supabase-integration/migrations/008_phase10_persist_already_saved.sql
  - tests/unit/test_cli_ingest_contract.py
  - tests/unit/test_ingest_pipeline.py
  - tests/unit/test_persist_port.py
  - tests/unit/test_supabase_draft_persister_contract.py
  - tests/unit/test_phase10_migration_008.py
  - tests/unit/test_build_ingest_deps_wiring.py
  - tests/unit/test_persist_idempotency_overflow.py
  - tests/unit/test_persist_draft_use_case.py
  - tests/unit/test_captions_failure_zero_persist.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-10-01T19:30:00Z
**Depth:** deep
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the phase 10 ingest CLI, pipeline, persist port, Supabase adapter, composition wiring, migration 008, and the unit tests that lock those contracts.

The operator path matches the locked stdout contract: three checkmarks, four id lines, `already_saved`, human stderr for config and template load, and `IngestError` JSON for pipeline failures. Migration 008 returns the stored `materials.slug` on `youtube_video_id` conflict and sets `already_saved` on both returns. Grants stay `security invoker` and `service_role` only. Named RPC parameters are not concatenated into SQL.

No critical defects. Three warnings are wrong failure classification on the live PostgREST client, and an in-memory persister that does not treat seeded video ids as already saved.

## Warnings

### WR-01: Check-constraint failures are classified as RPC errors

**File:** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py:25`
**Issue:** `_BATCH_CODES` contains the PostgreSQL condition name `check_violation`. The installed PostgREST client puts the SQLSTATE on `APIError.code` (`postgrest.exceptions.APIError`, field `code`). A check failure such as `materials.reading_minutes >= 0` is SQLSTATE `23514`, not the string `check_violation`. `23505` is handled correctly; `23514` falls through `_is_sdk_error` and becomes `DraftPersistRpcError` / `reason=rpc_error` instead of `batch_creation_failed`. `tests/unit/test_supabase_draft_persister_contract.py:241` stubs `PostgrestAPIError("check_violation")`, so the suite stays green against a code the live client does not send.
**Fix:**

```python
_BATCH_CODES = frozenset({"P0001", "23514"})
```

```python
error=PostgrestAPIError("23514", RAW_POSTGRES)
```

### WR-02: Non-JSON HTTP errors skip the network mapping

**File:** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py:81`
**Issue:** `_sdk_code` keeps only non-empty strings. When PostgREST cannot parse an error body, `generate_default_error_message` sets `code` to the HTTP status as an `int` (`postgrest/exceptions.py`). That value is dropped. The exception is still `APIError`, so `_is_sdk_error` maps a 502/503 HTML gateway response to `rpc_error`. `httpx.NetworkError` and `TimeoutException` are mapped to `network_error` only when they propagate as those types. A completed HTTP error response does not.
**Fix:**

```python
def _sdk_code(exc: BaseException) -> str | None:
    code = getattr(exc, "code", None)
    if isinstance(code, str) and code:
        return code
    return None


def _is_gateway_http_error(exc: BaseException) -> bool:
    code = getattr(exc, "code", None)
    return isinstance(code, int) and code >= 500
```

Treat `_is_gateway_http_error(exc)` like `_is_network_error` inside `_map_exception`, and add a unit test whose `APIError.code` is the integer `503`.

### WR-03: Seeded video ids are not idempotent in the batch fake

**File:** `ingestion-service/src/ingestion_service/tests_support/fakes.py:78`
**Issue:** `BatchTrackingFakePersister.seed_item` stores `video_id` on the batch item and counts it toward capacity, but it does not insert into `self.stored`. `persist` only treats a video as already saved when that dict already has the id (`fakes.py:96`). Seeding `video_id="published-vid"` and then persisting the same id inserts a second logical material with `already_saved=False`. Migration 008's `ON CONFLICT (youtube_video_id) DO NOTHING` would return the existing row and `already_saved` true. Overflow tests only persist new ids, so they do not catch this. A later test that seeds an existing shortlist row and re-ingests it would go green while the SQL would not insert.
**Fix:**

```python
def seed_item(
    self,
    batch_id: int,
    *,
    decision: str = "pending",
    video_id: str | None = None,
) -> None:
    batch = self.batches[batch_id]
    rank = len(batch.items) + 1
    batch.items.append(
        {"video_id": video_id, "rank": rank, "decision": decision}
    )
    if video_id is None or video_id in self.stored:
        return
    material_id = self._next_material_id
    self._next_material_id += 1
    self.stored[video_id] = PersistResult(
        material_id=material_id,
        slug=video_id,
        batch_id=batch_id,
        rank=rank,
        already_saved=False,
    )
```

## Info

### IN-01: `already_saved` is coerced with `bool()`

**File:** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py:73`
**Issue:** `bool(payload["already_saved"])` accepts any truthy value. JSON `null` becomes `False` (printed as a first insert, exit 0). A non-empty string, including `"false"`, becomes `True`. Migration 008 sends a JSON boolean, and the live re-run showed `true`/`false`, so the operator path is fine. A malformed payload with the key present still passes `_RESULT_KEYS`.
**Fix:** Require `isinstance(payload["already_saved"], bool)` and raise `DraftPersistRpcError` otherwise. Apply the same strictness to `slug` so `str(None)` cannot become the stdout token `None`.

### IN-02: Migration test does not bind each flag to its branch

**File:** `tests/unit/test_phase10_migration_008.py:47`
**Issue:** `test_migration_008_both_returns_include_already_saved` only checks that both `'already_saved', true` and `'already_saved', false` appear somewhere in the executable SQL. Swapping them between the `v_inserted = 0` return and the insert return would still pass. The current function text is correct (`true` on conflict, `false` after insert).
**Fix:** Assert the conflict block (from `v_inserted = 0` through its `return`) contains `'already_saved', true` and does not contain `'already_saved', false`, and assert the opposite on the final insert `return`.

### IN-03: `PersistResult.already_saved` defaults to a first insert

**File:** `ingestion-service/src/ingestion_service/application/ports/persist.py:17`
**Issue:** `already_saved: bool = False` means any caller that omits the field reports a new row. The adapter and the fakes set it explicitly. A new port implementation that forgets the flag would make the CLI print `already_saved: false` and exit 0 on a re-run.
**Fix:** Drop the default so constructing `PersistResult` without `already_saved` is a type error.

---

_Reviewed: 2026-10-01T19:30:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
