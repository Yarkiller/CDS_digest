# Phase 11: Address tech debt: captions diagnostics and persist error classification - Research

**Researched:** 2026-10-02
**Domain:** Operator CLI diagnostics (captions/URL envelopes), PostgREST persist error classification, Supabase RPC idempotency amend
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Captions / stderr diagnostics
- **D-01:** Operator-facing `IngestError` JSON on stderr carries only locked `stage` / `reason` plus `video_id` (and existing allowlisted context keys already in the mapper). The `message` field is built from `reason` + `video_id` only — never raw SDK text, never proxy credentials, never a credentialed URL. — **Reversibility:** costly — stderr JSON is the operator contract (Phase 10 D-05 / Phase 7 CR-01).
- **D-02:** Do not expand captions or URL context allowlists. Keep the locked allowlists from Phase 7.
- **D-03:** SDK exception text is discarded at the adapter/mapper boundary. Phase 11 introduces no log file, no structlog, and no debug channel. Developer debugging of raw SDK text is out of scope until Phase 12+.

### SDK exceptions outside the captions catalog
- **D-04:** CookieInvalid and any other base SDK exception that escapes the typed `CaptionsError` catch chain must be caught and raised as a typed path that maps to the existing reason `unknown_captions_error`. Do not add new captions reasons. Do not expand the `IngestError` stage set (Phase 10 D-08). — **Reversibility:** costly — reason catalog and stage set are operator contracts.
- **D-05:** A traceback must never reach the operator terminal on a captions-stage failure. Pipeline failures remain `IngestError.to_dict()` JSON on stderr with a non-zero exit.

### Persist error classification
- **D-06:** Fix recognition only: treat SQLSTATE `23514` the same as the named `check_violation` path already expected by `_BATCH_CODES`; treat numeric HTTP status codes on non-JSON gateway errors as the existing `rpc_error` branch (read status when string `code` is absent). — **Reversibility:** reversible — classification is adapter-local.
- **D-07:** Do not add, rename, or remove entries in `PERSIST_REASONS` (Phase 9 D-04). Happy-path and idempotent re-run stdout contracts stay unchanged.

### Sent-batch re-run (already_saved)
- **D-08:** When a material already exists and its only shortlist row is on a sent batch (`sent_at IS NOT NULL`), the run must succeed with exit 0 and print `already_saved: true` with the stored `material_id` / `slug` / `batch_id` / `rank` from the existing row — consistent with Phase 10 D-09 / D-10. — **Reversibility:** costly — stdout contract.
- **D-09:** Implement D-08 in the `persist_draft_and_enqueue` RPC: on that edge, return the existing material/shortlist ids with `already_saved: true` instead of raising `P0001`. Do not insert a second `materials` row and do not refresh draft content. — **Reversibility:** one-way — undo needs a follow-up migration of the SECURITY DEFINER RPC (same class as migrations 007/008).

### Carried forward (do not re-open)
- Phase 10 D-05 / D-08: pipeline failures are `IngestError.to_dict()` JSON on stderr; stage set stays `url`, `captions`, `metadata`, `consistency`, `llm`, `llm_truncation`, `persist`.
- Phase 10 D-09 / D-10 / D-12: `already_saved` line on success; re-run exit 0; stored slug/ids on conflict.
- Phase 9 D-04 / D-09..D-11: persist mapper + locked reasons; idempotency in RPC; no Python video_id pre-check; no content refresh on re-run.
- Phase 7 CR-01 / D-13: context allowlists and credential redaction on diagnostic envelopes.

### Claude's Discretion
- Exact catch placement for base SDK exceptions (adapter vs thin wrapper) as long as D-04 / D-05 hold and TDD is followed.
- Exact RPC SELECT for “existing row on sent batch” (which shortlist row / ordering) as long as D-08 / D-09 hold and no second material is inserted.
- How unit tests simulate SQLSTATE `23514` and numeric HTTP statuses without a live network.

### Deferred Ideas (OUT OF SCOPE)
### Phase 12+ (explicitly deferred this discussion)
- Optional `--debug` flag that may emit SDK text on stderr for developers.
- Optional file-based structured logging for the CLI (do not pull backend structlog into `ingestion-service` in Phase 11).

### Out of this phase title (accept or schedule separately)
- Phase 6 DTO barrel / language-strip / naive datetime debt.
- Phase 7 WR-03 caption snippet separator and WR-04 oEmbed 5xx/429 taxonomy (only if needed to satisfy D-01..D-05; otherwise leave unless planner proves they block diagnostics).
- Phase 8 wheel packaging of lecture/podcast templates.
- Phase 10 FakeDraftPersister.seed_item already_saved fidelity (test-fake only) unless required to prove D-08.
- Admin preview / email-HTML / draft→ready UI follow-ups from UAT.
- Nyquist `/gsd-validate-phase` for phases 6–8.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAP-02 | Missing/disabled/blocked captions exit non-zero with `stage=captions` and zero DB rows | Harden adapter catch + mapper so out-of-catalog SDK (e.g. `CookieInvalid`) → `unknown_captions_error` JSON stderr, never traceback; keep CAPTIONS_REASONS frozen |
| PERS-02 | Enqueue on current unsent batch; overflow creates new unsent batch | Do not change enqueue/overflow logic; only conflict/sent-batch return path and classification of check/gateway errors |
| CLI-02 | Re-run same `video_id` is conflict-safe (no duplicate materials/shortlist) | Amend RPC so sent-batch-only shortlist returns `already_saved: true` instead of `P0001`; keep ON CONFLICT DO NOTHING |
| CLI-04 | CLI prints staged progress checkmarks | No change to checkmark contract; ensure sent-batch re-run still prints checkmarks + `already_saved: true` with exit 0 |
</phase_requirements>

## Summary

Phase 11 is a **hardening / classification** phase, not a greenfield feature. Captions diagnostic redaction (Phase 7 CR-01) and the `YouTubeTranscriptApiException` catch-all (WR-01) are already present in HEAD and covered by unit tests — planner work there is mostly **regression locks** (adapter → mapper → CLI stderr) plus any residual escape hatch for non-SDK `Exception` types. The real gaps are persist-side: `_BATCH_CODES` recognizes the condition name `check_violation` but live PostgREST sends SQLSTATE `23514`; numeric HTTP `code` values from `generate_default_error_message` are dropped by `_sdk_code` (string-only); and migration `008` still **raises `P0001`** when the only shortlist row sits on a sent batch.

**Do not** follow Phase 10 REVIEW’s suggested remapping of integer HTTP ≥500 → `network_error`. Locked **D-06** keeps that path on the existing **`rpc_error`** branch — make the read of numeric status explicit and unit-test it.

**Primary recommendation:** TDD three waves — (1) captions/CLI regression for `CookieInvalid` → `unknown_captions_error` JSON stderr; (2) persist adapter classification for `"23514"` + int HTTP `code` → existing reasons without touching `PERSIST_REASONS`; (3) migration `009` CREATE OR REPLACE of `persist_draft_and_enqueue` plus invert `test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` / `BatchTrackingFakePersister` sent-batch conflict behavior.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Captions SDK exception → typed `CaptionsError` | API / Backend (`data-collection` adapter) | — | SDK types must not escape adapters; taxonomy lives at adapter boundary |
| `CaptionsError` → `IngestError` envelope | API / Backend (`ingestion-service` mapper) | — | Operator reason catalog + allowlisted context |
| CLI stderr JSON / exit code | Browser / Client (Typer CLI process) | API / Backend | `cli.py` catches `IngestError` only; unmapped exceptions become traceback |
| Persist PostgREST classification | API / Backend (`supabase_persist` adapter) | — | Map SQLSTATE/HTTP codes → `DraftPersist*` without leaking SDK text |
| `PERSIST_REASONS` / `map_persist_error` | API / Backend (mapper) | — | Locked frozenset; do not mutate in Phase 11 |
| Sent-batch `already_saved` return | Database / Storage (RPC) | API / Backend (adapter parse) | Idempotency edge is SQL; Python must not pre-check `video_id` |
| Offline migration contract tests | API / Backend (pytest unit) | — | String/SQL contract tests; live Studio apply is human gate |

## Project Constraints (from AGENTS.md / architecture / TDD)

- **TDD mandatory:** no production code before a failing automated test (`NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`).
- **Ports & Adapters:** SDK/HTTP/SQL errors mapped at adapter boundary; domain/use-cases stay free of `supabase` / `httpx` / direct SQL.
- **Composition root only** for wiring clients; Phase 11 must not invent new composition shortcuts.
- **Module boundaries:** captions taxonomy in `data-collection`; `IngestError` / mappers / CLI in `ingestion-service`; RPC SQL in `supabase-integration/migrations/`.
- **No deep-imports** across module internals.
- Project skills present: `hallmark`, `supabase`, `supabase-postgres-best-practices` — use Supabase SECURITY INVOKER + `CREATE OR REPLACE` migration pattern already established by 007/008.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `youtube-transcript-api` | installed in workspace (CookieInvalid under `_errors`) | Captions SDK | Already wired; catch hierarchy rooted at `YouTubeTranscriptApiException` |
| `postgrest` | `2.31.0` [VERIFIED: uv run import] | PostgREST client / `APIError` | Live `APIError.code` carries SQLSTATE strings; non-JSON path sets int status |
| `supabase` (Python client) | workspace dep | RPC `persist_draft_and_enqueue` | Existing `SupabaseDraftPersister` |
| `httpx` | `0.28.1` [VERIFIED: uv run import] | Network error types in persist mapper | Already used by `_is_network_error` |
| `typer` | `0.27.2` [VERIFIED: uv run import] | Operator CLI | Already emits `IngestError.to_dict()` JSON on stderr |
| PostgreSQL / Supabase SQL | project migrations 007/008 | RPC amend | One-way `CREATE OR REPLACE FUNCTION` pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | `9.1.1` [VERIFIED: uv run pytest --version] | Unit tests | All Phase 11 RED→GREEN |
| `uv` | `0.10.9` [VERIFIED: uv --version] | Workspace tooling | No new deps expected |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RPC amend for sent-batch | Python video_id pre-check | Forbidden by Phase 9 D-11 / carried forward |
| Map int HTTP → `network_error` | Keep `rpc_error` (D-06) | Phase 10 REVIEW suggested network; **locked D-06 overrides** |
| Edit applied `008` in place | New `009_*.sql` CREATE OR REPLACE | Matches 007→008 one-way amend pattern |

**Installation:** none — Phase 11 must not add packages.

**Version verification:** `postgrest 2.31.0`, `httpx 0.28.1`, `typer 0.27.2`, `pytest 9.1.1` via `uv run` in this session.

## Package Legitimacy Audit

> Phase 11 installs **no new external packages**. Existing workspace deps were probed; PyPI download signals returned null → seam `SUS` (tooling gap), not a reason to add/remove deps.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| *(none new)* | — | — | — | — | — | No install |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none for Phase 11 install (no install tasks)

## Architecture Patterns

### System Architecture Diagram

```text
Operator CLI (typer)
  │  URL arg
  ▼
run_ingest_pipeline
  ├─ extract_video_id → map_url_error → IngestError(stage=url)
  ├─ captions.get ──► YouTubeTranscriptAdapter
  │                      SDK exc → CaptionsError(+exception_class)
  │                      └─ map_captions_error → IngestError(stage=captions)
  ├─ metadata / LLM / assemble (unchanged)
  └─ persist_draft → SupabaseDraftPersister.rpc(persist_draft_and_enqueue)
                       │
                       ├─ success / already_saved jsonb → PersistResult → stdout
                       └─ APIError.code
                            ├─ "23505" → DraftPersistConflictError
                            ├─ "P0001"|"check_violation"|"23514" → DraftPersistBatchError
                            ├─ str other / int HTTP status → DraftPersistRpcError  (D-06)
                            └─ network types → DraftPersistNetworkError
                       └─ map_persist_error → IngestError(stage=persist)

Postgres RPC conflict (v_inserted=0):
  try unsent shortlist row → return already_saved true
  else any shortlist row (sent ok) → return already_saved true   ◄── Phase 11
  else raise P0001 (truly no shortlist row)
```

### Recommended Project Structure

```text
data-collection/src/data_collection/
  adapters/youtube_transcript.py   # catch chain (discretionary broaden)
  errors/captions.py               # fixed safe messages (already)

ingestion-service/src/ingestion_service/
  mapping/captions.py              # CAPTIONS_REASONS + message builder (lock tests)
  mapping/persist.py               # PERSIST_REASONS — DO NOT CHANGE
  adapters/supabase_persist.py     # _BATCH_CODES + _sdk_code / classification
  tests_support/fakes.py           # BatchTrackingFakePersister sent-batch edge
  cli.py                           # IngestError → JSON stderr (unchanged)

supabase-integration/migrations/
  008_phase10_persist_already_saved.sql   # starting point — do not edit in place
  009_phase11_persist_sent_batch_already_saved.sql  # NEW CREATE OR REPLACE

tests/unit/
  test_captions_error_mapping.py
  test_youtube_transcript_adapter.py
  test_cli_ingest_contract.py          # optional CookieInvalid→stderr JSON
  test_supabase_draft_persister_contract.py
  test_persist_idempotency_overflow.py # invert sent-batch re-run test
  test_phase10_migration_008.py        # keep green
  test_phase11_migration_009.py        # NEW offline SQL contract
```

### Pattern 1: Adapter catch → taxonomy → mapper envelope
**What:** SDK exceptions become module-local errors with safe `str`; mappers build `IngestError.message` from reason + video_id only.
**When to use:** Every captions/persist/URL failure path that reaches the CLI.
**Example:**
```python
# Source: ingestion-service/src/ingestion_service/mapping/captions.py (current HEAD)
def map_captions_error(error: CaptionsError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_captions_error")
    return IngestError(
        stage="captions",
        reason=reason,
        message=f"captions {reason} for {error.video_id}",
        context=_forward_context(error),
    )
```

### Pattern 2: One-way RPC amend via new migration file
**What:** `CREATE OR REPLACE FUNCTION public.persist_draft_and_enqueue(...)` in a new numbered SQL file; mirror grants/revokes from 008; offline string contract tests; human Studio apply.
**When to use:** Any change to applied SECURITY INVOKER RPC body (D-09).

### Pattern 3: Persist classification by code frozensets
**What:** Read `exc.code`; match frozensets; never put SDK message into `DraftPersistError` args/context beyond allowlisted keys.
**When to use:** All PostgREST failures from the draft persister.

### Anti-Patterns to Avoid
- **Expanding CAPTIONS_REASONS / PERSIST_REASONS / Stage literal:** operator contracts; forbidden by D-04/D-07/Phase 10 D-08.
- **Python video_id existence pre-check:** violates Phase 9 D-11.
- **Logging SDK text / `--debug`:** deferred to Phase 12+ (D-03).
- **Remapping int HTTP → `network_error`:** contradicts locked D-06 (`rpc_error`).
- **Editing applied `008` in place:** use `009` CREATE OR REPLACE.
- **Leaving `test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` green as-is:** that test currently **locks the bug** D-08 must remove.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SQLSTATE / condition name mapping | Custom Postgres error parser | Frozenset membership on `APIError.code` (`"23514"`, `"check_violation"`, `"P0001"`) | PostgREST already surfaces SQLSTATE |
| Idempotent re-run after send | Python shortlist lookup | RPC conflict branch return | Single transactional truth; Phase 9 D-05/D-11 |
| Secret-safe stderr | Ad-hoc string scrubbing of SDK text | Fixed adapter messages + mapper-built `message` | CR-01 class leaks come from `str(error)` / context dumps |
| Live DB for classification unit tests | Integration against Supabase | Fake `PostgrestAPIError(code=...)` / int `code` stubs | Discretion + existing contract style |

**Key insight:** Most captions “tech debt” from the milestone audit is already fixed in code; Phase 11 value is persist classification + RPC sent-batch return + regression tests that prevent reintroduction.

## Runtime State Inventory

> Migration / RPC amend phase — runtime state matters for the applied function body.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `materials` / `digest_shortlist_*` rows unchanged in schema; conflict edge currently raises instead of returning ids | No row migration; behavior change only after RPC replace |
| Live service config | Applied `persist_draft_and_enqueue` body from migration 008 on shared Supabase | Human Studio apply of migration `009` (same gate class as 008 / plan 10-05) |
| OS-registered state | None — verified by phase scope (CLI + SQL file only) | none |
| Secrets/env vars | No new env keys; existing ingestion `.env` / service_role unchanged | none |
| Build artifacts | None for SQL amend; Python packages unchanged | none |

## Common Pitfalls

### Pitfall 1: Unit test locks the sent-batch failure
**What goes wrong:** `tests/unit/test_persist_idempotency_overflow.py::test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` expects `DraftPersistBatchError` when the only shortlist row is on a sent batch.
**Why it happens:** Fake mirrored pre-D-08 RPC raise (`BatchTrackingFakePersister.persist` raises when `batch.sent_at is not None`).
**How to avoid:** RED→GREEN by inverting that test to expect `already_saved=True` + exit-path ids; update fake conflict branch to return stored ids instead of raising.
**Warning signs:** New RPC SQL green offline but overflow suite still expects raise.

### Pitfall 2: `check_violation` name vs SQLSTATE `23514`
**What goes wrong:** Tests stub `PostgrestAPIError("check_violation")` and stay green while live check failures send `"23514"` → misclassified as `rpc_error`.
**Why it happens:** PostgreSQL condition name `check_violation` maps to SQLSTATE `23514` [CITED: https://www.postgresql.org/docs/16/errcodes-appendix.html — table row `` `23514` `` / `` `check_violation` ``].
**How to avoid:** Keep `"check_violation"` **and** add `"23514"` to `_BATCH_CODES`; add a dedicated unit case for `"23514"`.
**Warning signs:** Only the name string is tested.

### Pitfall 3: Confusing D-06 with Phase 10 REVIEW WR-02 fix text
**What goes wrong:** Implementer maps int HTTP ≥500 to `network_error` per 10-REVIEW.
**Why it happens:** Phase 10 advisory suggested network; Phase 11 **D-06 locks `rpc_error`**.
**How to avoid:** Explicit branch: if `code` is `int` (status), classify as `DraftPersistRpcError` / `rpc_error`; unit-test `code=503`.
**Warning signs:** New test asserts `DraftPersistNetworkError` for int 503.

### Pitfall 4: Assuming captions CR-01/WR-01 still need production edits
**What goes wrong:** Large rewrite of mappers/adapters when HEAD already uses safe messages + `YouTubeTranscriptApiException` catch + CookieInvalid unit coverage.
**Why it happens:** Milestone audit still lists Phase 7 debt; `07-REVIEW-FIX.md` marks those findings already_fixed.
**How to avoid:** Start with failing **end-to-end CLI/pipeline** regression if any gap remains; only touch catch chain if a concrete escape is proven (discretionary bare `Exception` wrap).
**Warning signs:** Changing CAPTIONS_REASONS or allowlists (violates D-02/D-04).

### Pitfall 5: Uncaught exception → Typer traceback
**What goes wrong:** Any exception that is not `IngestError` / config errors escapes `cli.py` and prints a traceback (violates D-05).
**Why it happens:** CLI only catches `IngestError` (and config/template errors as human text).
**How to avoid:** Adapter must convert SDK failures to `CaptionsError`; pipeline maps to `IngestError` before CLI.
**Warning signs:** CliRunner stderr contains `Traceback` for CookieInvalid.

### Pitfall 6: Editing migration 008 after apply
**What goes wrong:** Local file and remote function diverge; contract tests pass against unapplied text.
**How to avoid:** Author `009_*.sql` CREATE OR REPLACE; keep 008 immutable; checkpoint for human Studio apply.
**Warning signs:** Diff only inside `008_phase10_persist_already_saved.sql`.

## Code Examples

### Current `_BATCH_CODES` / `_sdk_code` (gap)
```python
# Source: ingestion-service/src/ingestion_service/adapters/supabase_persist.py:24-25,81-83
_BATCH_CODES = frozenset({"P0001", "check_violation"})

def _sdk_code(exc: BaseException) -> str | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, str) and code else None
```

**Prescribed fix shape (adapter-local, D-06/D-07):**
```python
_BATCH_CODES = frozenset({"P0001", "check_violation", "23514"})

def _sdk_code(exc: BaseException) -> str | None:
    code = getattr(exc, "code", None)
    if isinstance(code, str) and code:
        return code
    return None

def _http_status_code(exc: BaseException) -> int | None:
    code = getattr(exc, "code", None)
    return code if isinstance(code, int) else None

# In _map_exception, after batch/conflict string matches:
# if _http_status_code(exc) is not None and _is_sdk_error(exc):
#     return DraftPersistRpcError("rpc_error", ...)
```

### postgrest non-JSON default error (int status)
```python
# Source: .venv/Lib/site-packages/postgrest/exceptions.py:62-68 [VERIFIED]
def generate_default_error_message(r):
    return {
        "message": "JSON could not be generated",
        "code": r.status_code,
        "hint": "Refer to full message for details",
        "details": str(r.content),
    }
```

### Migration 008 conflict raise to amend (verbatim)
```sql
-- Source: supabase-integration/migrations/008_phase10_persist_already_saved.sql:88-101 [VERIFIED]
    if v_inserted = 0 then
    select si.batch_id, si.rank
    into v_batch_id, v_rank
    from public.digest_shortlist_items si
    join public.digest_shortlist_batches b on b.id = si.batch_id
    where si.material_id = v_material_id
      and b.sent_at is null
    order by b.week_start desc, b.created_at desc
    limit 1;

    if v_batch_id is null then
      raise exception 'persist_draft_and_enqueue: existing material % has no shortlist row', v_material_id
        using errcode = 'P0001';
    end if;
```

**Prescribed amend (discretionary SELECT; must satisfy D-08/D-09):** when unsent lookup yields null, SELECT any shortlist row for `v_material_id` (order by `week_start desc, created_at desc`, `limit 1`) including `sent_at IS NOT NULL`, then return the same `jsonb_build_object(..., 'already_saved', true)` path; raise `P0001` only if **no** shortlist row exists at all. Do not insert materials/shortlist on this edge.

### Locked PERSIST_REASONS (must not change)
```python
# Source: ingestion-service/src/ingestion_service/mapping/persist.py:16-24 [VERIFIED]
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

### Captions unknown fallback (already correct)
```python
# Source: ingestion-service/src/ingestion_service/mapping/captions.py:65-72 [VERIFIED]
def map_captions_error(error: CaptionsError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_captions_error")
    return IngestError(
        stage="captions",
        reason=reason,
        message=f"captions {reason} for {error.video_id}",
        context=_forward_context(error),
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `message=str(error)` with context dump | Mapper builds `message` from reason + video_id | Phase 7 post-review fix | CR-01 closed in HEAD |
| Catch only `CouldNotRetrieveTranscript` | Also `YouTubeTranscriptApiException` + AttributeError/TypeError | Phase 7 post-review fix | CookieInvalid → CaptionsError |
| Conflict raise when no unsent shortlist | Return `already_saved` true including sent-batch row | Phase 11 (planned) | CLI-02 edge closed |
| `_BATCH_CODES` name-only `check_violation` | Also SQLSTATE `23514` | Phase 11 (planned) | Honest `batch_creation_failed` |

**Deprecated/outdated:**
- Treating Phase 10 REVIEW “int HTTP → network_error” as authoritative for Phase 11 — overridden by D-06.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Shared Supabase still has migration 008 applied and needs a new 009 file (not an in-place 008 edit) | Runtime State / Patterns | Wrong file strategy vs applied DB |
| A2 | Truly-no-shortlist-row conflict should still raise `P0001` after sent-batch fallback | Code Examples | Over-broad already_saved if product wanted different handling |
| A3 | Residual captions production edits may be unnecessary if CLI regression already passes | Pitfalls | Wasted churn vs missed bare-Exception escape |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Open Questions (RESOLVED)

1. **Human Studio apply timing for migration 009**
   - What we know: Phase 10 used offline contract tests + human apply gate for 008.
   - What's unclear: Whether planner should put apply in the same plan as SQL authoring or a follow-up checkpoint.
   - Recommendation: Mirror Phase 10 — author + offline tests first; explicit `checkpoint:human-verify` for Studio apply before calling live CLI UAT done.
   - **RESOLVED:** Split — `11-03` authors migration 009 + offline SQL/fake invert after one-way decision gate; `11-04` owns `[BLOCKING]` Studio/psql apply (`checkpoint:human-verify`) before live CLI-02 claim.

2. **Bare `Exception` wrap in captions adapter**
   - What we know: CookieInvalid already maps via `YouTubeTranscriptApiException`; CLI traceback risk remains for non-SDK exceptions.
   - What's unclear: Whether D-04’s “any other base SDK exception” requires a final `except Exception → CaptionsError`.
   - Recommendation: Discretion — add only if a RED test shows an escape; prefer narrow SDK base catch over swallowing `KeyboardInterrupt` (exclude `BaseException`).
   - **RESOLVED:** RED-only — `11-01` adds production catch only if CliRunner/adapter RED proves an escape; no blanket `except Exception`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | unit tests / adapters | ✓ | 3.14.0 | — |
| `uv` | workspace runs | ✓ | 0.10.9 | — |
| `pytest` | Nyquist / TDD | ✓ | 9.1.1 | — |
| `postgrest` (installed) | persist classification | ✓ | 2.31.0 | — |
| Supabase Studio / remote apply | migration 009 | ✓ (process) / human | — | Offline SQL contract tests; block live verification until apply |
| Live YouTube / network | not required for Phase 11 unit scope | n/a | — | Mocked SDK / fake client |

**Missing dependencies with no fallback:**
- None for offline unit work; live RPC verification blocked until human applies `009`.

**Missing dependencies with fallback:**
- Live Supabase apply → offline `test_phase11_migration_009.py` string contracts + mocked persister tests.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`) |
| Quick run command | `uv run pytest tests/unit/test_captions_error_mapping.py tests/unit/test_youtube_transcript_adapter.py tests/unit/test_supabase_draft_persister_contract.py tests/unit/test_persist_idempotency_overflow.py tests/unit/test_phase11_migration_009.py -q` |
| Full suite command | `uv run pytest tests/unit -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAP-02 / D-04 | CookieInvalid → CaptionsError → `unknown_captions_error` | unit | `uv run pytest tests/unit/test_youtube_transcript_adapter.py::test_adapter_maps_sdk_exception_to_captions_subtype tests/unit/test_captions_error_mapping.py -q` | ✅ adapter+mapper; ❌ Wave 0 CLI stderr JSON regression |
| CAP-02 / D-01 | `message` / `to_dict()["message"]` free of SDK/proxy secrets | unit | `uv run pytest tests/unit/test_captions_error_mapping.py::test_map_captions_error_redacts_credentialed_proxy_context -q` | ✅ |
| CAP-02 / D-05 | Captions failure → JSON stderr, no Traceback | unit | CliRunner + raising captions fake/SDK | ❌ Wave 0 extend `test_cli_ingest_contract.py` |
| PERS-02 / D-06 | `"23514"` → `DraftPersistBatchError` / `batch_creation_failed` | unit | extend `test_supabase_draft_persister_contract.py` | ❌ Wave 0 (only `check_violation` today) |
| PERS-02 / D-06 | int HTTP `code` (e.g. 503) → `DraftPersistRpcError` | unit | extend persister contract | ❌ Wave 0 |
| PERS-02 / D-07 | `PERSIST_REASONS` frozenset unchanged | unit | assert frozenset equality in mapping test | ✅ pattern exists; keep locked |
| CLI-02 / D-08–D-09 | Sent-batch-only conflict returns already_saved true (SQL) | unit (SQL contract) | `test_phase11_migration_009.py` | ❌ Wave 0 |
| CLI-02 / D-08 | Fake/overflow path returns already_saved true (not raise) | unit | invert `test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` | ✅ file exists, **behavior must flip** |
| CLI-04 | Checkmarks still printed on success re-run | unit | existing CliRunner re-run | ✅ |

### Sampling Rate
- **Per task commit:** quick run command above (subset for the touched area)
- **Per wave merge:** `uv run pytest tests/unit -q`
- **Phase gate:** Full unit suite green before `/gsd-verify-work`; human confirms Studio applied `009` before claiming live CLI-02 sent-batch edge

### Wave 0 Gaps
- [ ] `tests/unit/test_supabase_draft_persister_contract.py` — cases for `code="23514"` → batch error; `code=503` (int) → rpc_error; keep `check_violation` case
- [ ] `tests/unit/test_phase11_migration_009.py` — offline SQL: conflict fallback without `sent_at is null` exclusive raise; `'already_saved', true`; no second insert; grants unchanged pattern
- [ ] Invert `tests/unit/test_persist_idempotency_overflow.py::test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` (+ fake persist conflict branch)
- [ ] Optional but recommended: CliRunner captions failure with CookieInvalid/CaptionsError → stderr JSON `unknown_captions_error`, stdout without Traceback
- [ ] Framework install: none — pytest already in dependency-groups.dev

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | CLI uses service_role via existing settings; no new auth |
| V3 Session Management | no | — |
| V4 Access Control | yes | RPC remains `security invoker`; revoke public/anon/authenticated; grant `service_role` only (mirror 008) |
| V5 Input Validation | yes | Locked reason catalogs; allowlisted diagnostic context; no raw SDK text on stderr |
| V6 Cryptography | no | — |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Proxy/credential leak on stderr | Information Disclosure | Mapper-built messages; context allowlists; discard SDK text (D-01..D-03) |
| SQL/RPC privilege escalation via grants | Elevation of Privilege | Keep revoke/grant block from 008 on REPLACE |
| Misclassified errors → operator retries unsafe actions | Spoofing / Tampering (ops) | Correct `23514` / HTTP status classification (D-06) |
| Duplicate material insert on re-run | Tampering | `ON CONFLICT DO NOTHING` + already_saved return (D-08/D-09) |

## Sources

### Primary (HIGH confidence)
- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` — `_BATCH_CODES`, `_sdk_code`, `_map_exception` (Read this session)
- `supabase-integration/migrations/008_phase10_persist_already_saved.sql:88-101` — sent-batch raise path (Read this session)
- `.venv/Lib/site-packages/postgrest/exceptions.py:62-68` — int `status_code` on non-JSON errors (Read this session)
- `tests/unit/test_persist_idempotency_overflow.py:98-119` — test locking sent-batch raise (Read this session)
- `data-collection/.../youtube_transcript.py` + `tests/unit/test_youtube_transcript_adapter.py` — CookieInvalid catch coverage (Read this session)
- https://www.postgresql.org/docs/16/errcodes-appendix.html — `` `23514` `` = `` `check_violation` `` [CITED]

### Secondary (MEDIUM confidence)
- Context7 `/websites/postgresql_16` — RAISE ERRCODE name vs SQLSTATE
- Context7 `/websites/supabase` — `CREATE OR REPLACE` + `security invoker` function template
- `.planning/phases/07-captions-adapter/07-REVIEW-FIX.md` — CR-01/WR-01 already_fixed in tree
- `.planning/phases/10-cli-composition-uat/10-REVIEW.md` — WR-01/WR-02 classification debt (note D-06 override on HTTP→rpc_error)
- `.planning/v1.1-MILESTONE-AUDIT.md` — tech_debt inventory for phases 7/10

### Tertiary (LOW confidence)
- WebSearch synthesis on postgrest-py docs typing `code` as str — superseded by installed `generate_default_error_message` source read

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions and installed postgrest behavior verified in-session
- Architecture: HIGH — code paths and migration conflict branch read in full
- Pitfalls: HIGH — contradictory locked test + D-06 vs 10-REVIEW explicitly identified

**Research date:** 2026-10-02
**Valid until:** 2026-11-01 (stable adapters; re-check if postgrest major bumps)
