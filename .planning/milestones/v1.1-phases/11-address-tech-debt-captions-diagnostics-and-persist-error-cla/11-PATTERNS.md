# Phase 11: Address tech debt: captions diagnostics and persist error classification - Pattern Map

**Mapped:** 2026-10-02
**Files analyzed:** 12
**Analogs found:** 12 / 12

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` | adapter | request-response | same file (extend `_BATCH_CODES` / `_map_exception`) | exact |
| `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql` | migration | CRUD | `supabase-integration/migrations/008_phase10_persist_already_saved.sql` | exact |
| `ingestion-service/src/ingestion_service/tests_support/fakes.py` | test-utility | CRUD | same file (`BatchTrackingFakePersister.persist` conflict branch) | exact |
| `tests/unit/test_supabase_draft_persister_contract.py` | test | request-response | same file (`test_check_violation_maps_to_batch_error`) | exact |
| `tests/unit/test_phase11_migration_009.py` | test | file-I/O | `tests/unit/test_phase10_migration_008.py` | exact |
| `tests/unit/test_persist_idempotency_overflow.py` | test | CRUD | same file (`test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed`) | exact |
| `tests/unit/test_cli_ingest_contract.py` | test | request-response | same file (`test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr`) | exact |
| `data-collection/src/data_collection/adapters/youtube_transcript.py` | adapter | request-response | same file (`_fetch` catch chain) | exact |
| `tests/unit/test_youtube_transcript_adapter.py` | test | request-response | same file (`test_adapter_maps_sdk_exception_to_captions_subtype`) | exact |
| `tests/unit/test_captions_error_mapping.py` | test | transform | same file (redaction + `unknown_captions_error`) | exact |
| `ingestion-service/src/ingestion_service/mapping/captions.py` | utility | transform | same file — **lock only, do not expand allowlists/reasons** | exact |
| `ingestion-service/src/ingestion_service/mapping/persist.py` | utility | transform | same file — **`PERSIST_REASONS` must not change (D-07)** | exact |

## Pattern Assignments

### `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` (adapter, request-response)

**Analog:** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py`

**Imports pattern** (lines 1–20):
```python
from __future__ import annotations

from typing import Any

import httpx
from postgrest.exceptions import APIError as PostgrestAPIError
from supabase import Client

from data_collection.dto.material_draft import MaterialDraft
from ingestion_service.adapters.persist_errors import (
    DraftPersistBatchError,
    DraftPersistConflictError,
    DraftPersistError,
    DraftPersistNetworkError,
    DraftPersistRpcError,
    DraftPersistUnknownError,
)
from ingestion_service.application.ports.persist import PersistResult
```

**Core classification pattern** (lines 24–25, 81–129) — extend, do not rewrite:
```python
_CONFLICT_CODES = frozenset({"23505"})
_BATCH_CODES = frozenset({"P0001", "check_violation"})  # Phase 11: add "23514"

def _sdk_code(exc: BaseException) -> str | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, str) and code else None  # int code stays None today

def _map_exception(exc: BaseException, draft: MaterialDraft) -> DraftPersistError:
    video_id = draft.youtube_video_id
    code = _sdk_code(exc)
    if _is_network_error(exc):
        return DraftPersistNetworkError("network_error", video_id=video_id, ...)
    if code in _CONFLICT_CODES:
        return DraftPersistConflictError("persist_conflict", ...)
    if code in _BATCH_CODES:
        return DraftPersistBatchError("batch_creation_failed", ...)
    if _is_sdk_error(exc):
        return DraftPersistRpcError("rpc_error", ...)  # D-06: int HTTP must reach here
    return DraftPersistUnknownError("unknown_persist_error", ...)
```

**Prescribed Phase 11 delta (from RESEARCH, keep frozenset + safe context):**
```python
_BATCH_CODES = frozenset({"P0001", "check_violation", "23514"})

def _http_status_code(exc: BaseException) -> int | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, int) else None

# After string batch/conflict matches, before/inside SDK branch:
# if _http_status_code(exc) is not None and _is_sdk_error(exc):
#     return DraftPersistRpcError("rpc_error", video_id=..., context=_safe_context(...))
```

**Error handling pattern** (lines 35–43, 77–78):
```python
def persist(self, material_draft: MaterialDraft) -> PersistResult:
    try:
        result = self._client.rpc(_RPC_NAME, params).execute()
        return _persist_result(result.data)
    except DraftPersistError:
        raise
    except Exception as exc:
        raise _map_exception(exc, material_draft) from None

def _safe_context(draft: MaterialDraft, reason: str) -> dict[str, Any]:
    return {"slug": draft.slug, "reason": reason}  # never SDK message text
```

**Do not change:** `PERSIST_REASONS` mapping lives in `mapping/persist.py`; adapter only raises typed `DraftPersist*` with locked reason strings.

---

### `supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql` (migration, CRUD)

**Analog:** `supabase-integration/migrations/008_phase10_persist_already_saved.sql`

**Header / amend pattern** (lines 1–6):
```sql
-- Phase 10: amend persist_draft_and_enqueue for D-09 / D-12 (CLI-02).
-- CREATE OR REPLACE only — do not edit applied 007 in place.
-- Conflict: return stored materials.slug + already_saved true.
-- Idempotent grants/revokes mirror 007; security invoker; service_role only.
```

**Function signature + security** (lines 8–26) — copy verbatim into 009:
```sql
create or replace function public.persist_draft_and_enqueue(
  p_title text,
  ...
  p_batch_size int
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
```

**Conflict branch to amend** (lines 87–115) — current bug + already_saved return shape:
```sql
  if v_inserted = 0 then
    select si.batch_id, si.rank
    into v_batch_id, v_rank
    from public.digest_shortlist_items si
    join public.digest_shortlist_batches b on b.id = si.batch_id
    where si.material_id = v_material_id
      and b.sent_at is null   -- Phase 11: fall back when this yields null
    order by b.week_start desc, b.created_at desc
    limit 1;

    if v_batch_id is null then
      raise exception 'persist_draft_and_enqueue: existing material % has no shortlist row', v_material_id
        using errcode = 'P0001';  -- Phase 11: only if NO shortlist row at all
    end if;

    return jsonb_build_object(
      'material_id', v_material_id,
      'slug', v_slug,
      'batch_id', v_batch_id,
      'rank', v_rank,
      'already_saved', true
    );
  end if;
```

**Prescribed amend (D-08/D-09):** when unsent lookup is null, SELECT any shortlist row for `v_material_id` (same order, `limit 1`) including `sent_at IS NOT NULL`, then reuse the same `jsonb_build_object(..., 'already_saved', true)` path; raise `P0001` only if no shortlist row exists. Do not insert materials/shortlist on conflict.

**Grants pattern** (lines 168–176) — mirror exactly in 009:
```sql
revoke all on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) from public;
revoke all on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) from anon, authenticated;
grant execute on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) to service_role;
```

**Anti-pattern:** do not edit applied `008_phase10_persist_already_saved.sql` in place.

---

### `ingestion-service/src/ingestion_service/tests_support/fakes.py` (test-utility, CRUD)

**Analog:** same file — `BatchTrackingFakePersister`

**Core conflict branch to invert** (lines 94–110):
```python
def persist(self, material_draft: MaterialDraft) -> PersistResult:
    self.calls.append(material_draft)
    existing = self.stored.get(material_draft.youtube_video_id)
    if existing is not None:
        batch = self.batches.get(existing.batch_id)
        if batch is not None and batch.sent_at is not None:
            raise DraftPersistBatchError(  # Phase 11: return already_saved=True instead
                "batch_creation_failed",
                video_id=material_draft.youtube_video_id,
            )
        return PersistResult(
            material_id=existing.material_id,
            slug=existing.slug,
            batch_id=existing.batch_id,
            rank=existing.rank,
            already_saved=True,
        )
```

**Prescribed Phase 11 delta:** on sent-batch conflict, return stored ids with `already_saved=True` (mirror RPC). Raise `DraftPersistBatchError` only for truly missing shortlist (if fake models that edge).

**Seed helpers to keep** (lines 70–92): `seed_batch(..., sent_at=...)` + `seed_item(...)` remain the test setup API.

---

### `tests/unit/test_supabase_draft_persister_contract.py` (test, request-response)

**Analog:** same file

**Fake PostgREST error stub** (lines 22–27) — extend for int `code` (D-06):
```python
class PostgrestAPIError(Exception):
    """Mock PostgREST/Postgres error with a SQLSTATE `.code`."""

    def __init__(self, code: str, message: str = RAW_POSTGRES) -> None:
        self.code = code
        super().__init__(message)
```

Phase 11: allow `code: str | int` so `PostgrestAPIError(503, ...)` simulates `generate_default_error_message`.

**Classification case to clone** (lines 241–255):
```python
def test_check_violation_maps_to_batch_error() -> None:
    from ingestion_service.adapters.persist_errors import DraftPersistBatchError
    from ingestion_service.adapters.supabase_persist import SupabaseDraftPersister

    client = _FakeClient(
        _happy_data(),
        error=PostgrestAPIError("check_violation", RAW_POSTGRES),
    )
    try:
        SupabaseDraftPersister(client, batch_size=5).persist(_draft())
    except DraftPersistBatchError as exc:
        _assert_safe_error(exc)
        return
    raise AssertionError("expected DraftPersistBatchError")
```

**Add parallel cases:**
- `PostgrestAPIError("23514", ...)` → `DraftPersistBatchError` / `batch_creation_failed`
- `PostgrestAPIError` with `code=503` (int) → `DraftPersistRpcError` / `rpc_error` (**not** `DraftPersistNetworkError` — D-06)

**Safety assertion pattern:** reuse `_assert_safe_error(exc)` so planted Postgres text never appears in error args/context.

---

### `tests/unit/test_phase11_migration_009.py` (test, file-I/O)

**Analog:** `tests/unit/test_phase10_migration_008.py`

**Imports / path / helpers** (lines 1–25):
```python
"""RED→GREEN: migration 008 SQL contract for stored slug + already_saved (D-09, D-12; CLI-02)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase-integration/migrations/008_phase10_persist_already_saved.sql"

def _sql() -> str:
    assert MIGRATION.is_file(), "008_phase10_persist_already_saved.sql must exist"
    return MIGRATION.read_text(encoding="utf-8")

def _sql_without_line_comments() -> str:
    kept: list[str] = []
    for raw in _sql().splitlines():
        kept.append(raw.split("--", 1)[0])
    return "\n".join(kept)

def _normalized_executable_sql() -> str:
    return " ".join(_sql_without_line_comments().lower().split())
```

**Assertions to mirror for 009** (adapt from lines 28–70):
```python
assert "create or replace function public.persist_draft_and_enqueue" in executable
assert "security invoker" in executable
assert "'already_saved', true" in executable
assert "grant execute" in lower and "to service_role" in lower
assert "revoke all" in lower and "from anon, authenticated" in lower
assert "truncate " not in _normalized_executable_sql()
```

**Phase 11-specific contracts:**
- Conflict fallback must not raise solely because `sent_at is null` filter misses (assert presence of a second shortlist SELECT without exclusive `sent_at is null`, or assert raise text only for “no shortlist row”)
- Keep `on conflict (youtube_video_id) do nothing`
- No second insert on conflict path (string-level: conflict branch returns before insert into `digest_shortlist_items`)

---

### `tests/unit/test_persist_idempotency_overflow.py` (test, CRUD)

**Analog:** same file — invert the locking test

**Current bug-locking test** (lines 98–119):
```python
def test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed() -> None:
    """WR-02: post-publish re-run must not return the sent batch."""
    fake = _batch_fake(batch_size=5)
    sent_at = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)
    fake.seed_batch(batch_id=3, sent_at=sent_at)
    fake.seed_item(3, decision="pending", video_id="published-vid")
    fake.stored["published-vid"] = PersistResult(
        material_id=9, slug="published-vid", batch_id=3, rank=1, already_saved=False,
    )

    with pytest.raises(DraftPersistBatchError) as exc:
        persist_draft(_draft("published-vid"), fake)
    assert exc.value.reason == "batch_creation_failed"
```

**Prescribed invert (D-08):**
```python
def test_rerun_when_only_sent_batch_exists_returns_already_saved() -> None:
    result = persist_draft(_draft("published-vid"), fake)
    assert result.already_saved is True
    assert result.material_id == 9
    assert result.batch_id == 3
    assert result.rank == 1
    assert result.slug == "published-vid"
```

Keep neighboring overflow / skip-sent-batch enqueue tests green (new material still must not enqueue onto a sent batch).

---

### `tests/unit/test_cli_ingest_contract.py` (test, request-response)

**Analog:** same file — JSON stderr mid-pipeline failure

**CLI stderr JSON pattern** (lines 132–158):
```python
def test_cli_mid_pipeline_llm_error_keeps_transcript_checkmark_json_stderr(monkeypatch) -> None:
    import json
    from typer.testing import CliRunner
    from ingestion_service import cli as cli_mod

    deps = _fake_deps()
    deps.article = FakeArticleGenerator(
        result=_article(),
        failures={VIDEO_ID: ArticleNetworkError(VIDEO_ID)},
    )
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    payload = json.loads(result.stderr.strip())
    assert payload["ok"] is False
    assert payload["stage"] == "llm"
```

**Phase 11 captions regression (recommended Wave 0):** same CliRunner + `_fake_deps()` shape, but captions provider raises `CaptionsError` / CookieInvalid-mapped path → `stage == "captions"`, `reason == "unknown_captions_error"`, stderr JSON parseable, `"Traceback" not in result.stderr + result.stdout`.

**Production CLI catch** (`ingestion-service/src/ingestion_service/cli.py` lines 71–77) — do not change:
```python
except (ConfigurationError, TemplateLoadError) as err:
    typer.echo(str(err), err=True)
    raise typer.Exit(code=1) from err
except IngestError as err:
    typer.echo(json.dumps(err.to_dict()), err=True)
    raise typer.Exit(code=err.exit_code) from err
```

---

### `data-collection/src/data_collection/adapters/youtube_transcript.py` (adapter, request-response)

**Analog:** same file — catch chain already maps CookieInvalid via base SDK

**Catch-chain pattern** (lines 57–101):
```python
def _fetch(self, video_id: str) -> Transcript:
    try:
        return self._fetch_inner(video_id)
    except CaptionsError:
        raise
    # ... typed SDK subtypes ...
    except CouldNotRetrieveTranscript as exc:
        raise CaptionsError(video_id, exception_class=_exception_class(exc)) from exc
    except YouTubeTranscriptApiException as exc:
        raise CaptionsError(video_id, exception_class=_exception_class(exc)) from exc
    except (AttributeError, TypeError) as exc:
        raise CaptionsError(video_id, exception_class=_exception_class(exc)) from exc
```

**Safe message pattern** — taxonomy in `data-collection/.../errors/captions.py` lines 8–16:
```python
class CaptionsError(Exception):
    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        super().__init__(f"captions error for {video_id}")  # never str(sdk_exc)
```

**Discretion (D-04):** add bare `except Exception → CaptionsError` only if a RED test proves escape; never catch `BaseException` / `KeyboardInterrupt`. Prefer keeping HEAD if CLI regression already green.

---

### `tests/unit/test_youtube_transcript_adapter.py` (test, request-response)

**Analog:** same file

**CookieInvalid → CaptionsError case** (lines 219–245):
```python
(
    CookieInvalid("bad-cookie-path"),
    "CaptionsError",
    "CookieInvalid",
),
# ...
def test_adapter_maps_sdk_exception_to_captions_subtype(...):
    expected_cls = getattr(captions_errors, expected_type)
    adapter = YouTubeTranscriptAdapter(_RaisingApi(sdk_exc))
    with pytest.raises(expected_cls) as exc_info:
        asyncio.run(adapter.get(VIDEO_ID))
    assert err.context.get("exception_class") == sdk_name
```

Keep green; extend only if new catch branch (e.g. bare Exception) is introduced.

---

### `tests/unit/test_captions_error_mapping.py` (test, transform)

**Analog:** same file

**Unknown fallback + redaction** (lines 78–134):
```python
(CaptionsError(VIDEO_ID), "unknown_captions_error"),
# ...
mapped = map_captions_error(error)
assert mapped.stage == "captions"
assert mapped.reason == reason
payload = mapped.to_dict()
assert payload["ok"] is False

# Redaction (D-01):
assert "secret" not in mapped.message
assert "socks5://" not in payload["message"]
assert "proxy_url" not in mapped.context
```

**Mapper production pattern** (`mapping/captions.py` lines 65–72) — lock, do not expand `CAPTIONS_REASONS` / `_CONTEXT_ALLOWLIST`:
```python
def map_captions_error(error: CaptionsError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_captions_error")
    return IngestError(
        stage="captions",
        reason=reason,
        message=f"captions {reason} for {error.video_id}",
        context=_forward_context(error),
    )
```

---

### `ingestion-service/src/ingestion_service/mapping/persist.py` (utility, transform)

**Analog:** same file — **do not mutate** `PERSIST_REASONS` (D-07)

**Locked frozenset** (lines 16–24):
```python
PERSIST_REASONS: frozenset[str] = frozenset(
    {
        "persist_conflict",
        "batch_creation_failed",
        "rpc_error",
        "network_error",
        "unknown_persist_error",
    }
)
```

**Map pattern** (lines 56–63):
```python
def map_persist_error(error: DraftPersistError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_persist_error")
    return IngestError(
        stage="persist",
        reason=reason,
        message=f"persist {reason}",
        context=_forward_context(error),
    )
```

Phase 11 work belongs in adapter classification + RPC, not this file.

---

## Shared Patterns

### Adapter → taxonomy → mapper → CLI stderr
**Source:** `youtube_transcript.py` + `mapping/captions.py` + `cli.py` + `domain/errors.py`
**Apply to:** Captions failure paths (D-01, D-04, D-05)

```python
# Adapter: raise CaptionsError(..., exception_class=type(exc).__name__) with safe str
# Mapper: message=f"captions {reason} for {error.video_id}" + allowlisted context only
# Domain: IngestError.to_dict() → ok/stage/reason/message/exit_code[/context]
# CLI: except IngestError → json.dumps(err.to_dict()) on stderr + non-zero exit
```

Unmapped exceptions become Typer tracebacks — adapter must convert before pipeline returns to CLI.

### Persist classification by code frozensets
**Source:** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py`
**Apply to:** All PostgREST failures from `SupabaseDraftPersister`

```python
_CONFLICT_CODES = frozenset({"23505"})
_BATCH_CODES = frozenset({"P0001", "check_violation", "23514"})  # after Phase 11
# string code → conflict/batch; int HTTP status on SDK error → rpc_error (D-06)
# never put RAW_POSTGRES / SDK message into DraftPersistError args beyond allowlisted context
```

### One-way RPC amend via new migration
**Source:** `supabase-integration/migrations/008_phase10_persist_already_saved.sql`
**Apply to:** `009_phase11_persist_sent_batch_already_saved.sql`

```sql
-- CREATE OR REPLACE FUNCTION public.persist_draft_and_enqueue(...)
-- security invoker; set search_path = public
-- mirror revoke public/anon/authenticated + grant service_role
-- offline string contract tests; human Studio apply checkpoint
```

### Offline SQL contract tests
**Source:** `tests/unit/test_phase10_migration_008.py`
**Apply to:** `tests/unit/test_phase11_migration_009.py`

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase-integration/migrations/009_...."
# strip -- comments, normalize whitespace, assert executable SQL tokens
```

### TDD / mocked PostgREST client
**Source:** `tests/unit/test_supabase_draft_persister_contract.py`
**Apply to:** `23514` + int HTTP classification tests

```python
class PostgrestAPIError(Exception):
    def __init__(self, code: str | int, message: str = RAW_POSTGRES) -> None:
        self.code = code
        super().__init__(message)

client = _FakeClient(_happy_data(), error=PostgrestAPIError(...))
SupabaseDraftPersister(client, batch_size=5).persist(_draft())
```

### In-memory PersistPort fake for idempotency
**Source:** `ingestion-service/.../tests_support/fakes.py` (`BatchTrackingFakePersister`)
**Apply to:** sent-batch re-run unit tests

```python
fake.seed_batch(batch_id=3, sent_at=sent_at)
fake.seed_item(3, video_id="published-vid")
fake.stored["published-vid"] = PersistResult(...)
# Phase 11: persist → already_saved True, not DraftPersistBatchError
```

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| *(none)* | — | — | All Phase 11 surfaces extend existing adapters, migration 008 amend pattern, or existing unit suites |

## Metadata

**Analog search scope:** `data-collection/src/data_collection/`, `ingestion-service/src/ingestion_service/`, `supabase-integration/migrations/`, `tests/unit/`
**Files scanned:** ~20 tracked sources (git `ls-files` verified for all named analogs)
**Pattern extraction date:** 2026-10-02
**Tracked-source gate:** all analog paths confirmed via `git ls-files` (non-empty)
