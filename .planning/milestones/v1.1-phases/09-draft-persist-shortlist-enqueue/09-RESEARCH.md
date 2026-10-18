# Phase 9: Draft Persist & Shortlist Enqueue — Research

**Researched:** 2026-09-27  
**Question:** *What do I need to know to PLAN this phase well?*  
**Confidence:** HIGH for repo/schema/contracts; MEDIUM for `supabase-py` sync RPC edge cases (verified via Context7 + live client pattern)

---

## Short Answer

Phase 9 is the **write-side bridge** between the LLM output (`MaterialDraft`) and the existing admin triage surface (`/admin/digest`). To plan it well you need to know:

1. **Ownership is locked:** the persist port *and* its Supabase adapter both live inside `ingestion-service` (D-01). Do not plan a new dependency on `supabase-integration`; plan a local port + adapter + mapper + fake.
2. **Atomicity is a Postgres RPC:** a single `persist_draft_and_enqueue(...)` function must INSERT `materials`, find/create the current unsent `digest_shortlist_batches`, and INSERT `digest_shortlist_items` in one transaction. Any failure → zero rows.
3. **Idempotency is schema-backed:** migration `007` adds a unique constraint on `materials.youtube_video_id`; the RPC uses `ON CONFLICT ... DO NOTHING` then returns existing ids. Re-runs are true no-ops.
4. **Material row completion happens in Python:** slug, `reading_minutes`, and `roles` are generated/copied before the RPC call; the RPC only persists and enqueues.
5. **Batch capacity is configurable:** `SHORTLIST_BATCH_SIZE` (default 5) is passed into the RPC; full batches trigger creation of a new unsent batch.
6. **Error surface is staged:** adapter-local `DraftPersistError` maps to `IngestError(stage="persist")`, mirroring captions/metadata/article mappers.
7. **Phase 9 amends Phase 8:** `ArticleDraft` must grow `roles: list[RoleKind]`, which means updating the DTO, both templates, the DeepSeek adapter validation, and Phase 8 tests.

---

## Scope Boundary (what Phase 9 owns)

| In scope | Out of scope |
|----------|--------------|
| Persist port + Supabase adapter inside `ingestion-service` | Backend/SPA changes; backend remains a reader |
| Migration `007` with unique constraint + RPC | Calling `claim_and_publish_digest` (admin send path) |
| `MaterialDraft` → `materials` (`status=draft`) + `digest_shortlist_items` (`decision=pending`) | Setting `status=ready` or auto-publish |
| Current-unsent-batch resolution + overflow batch creation | Scheduler / HTTP API / playlist ingest |
| Idempotent re-run on same `youtube_video_id` | Refreshing draft content on re-run |
| `SHORTLIST_BATCH_SIZE` env wiring | Whisper / transcription fallback |
| `DraftPersistError` → `IngestError(stage="persist")` mapping | New `IngestError` stages |
| Extending `ArticleDraft` with `roles` | Chunking / embeddings on ingest |

---

## Key Research Findings

### 1. Persist port/adapter ownership: keep it inside `ingestion-service`

**Decision:** D-01/D-02 place the port and adapter in `ingestion-service`; `ingestion-service` adds a direct `supabase` PyPI dependency rather than importing `supabase-integration`.

**Implications for planning:**
- Plan a new `ingestion_service.application.ports.persist` module (or similar) with a `Protocol`.
- Plan a new `ingestion_service.adapters.supabase_persist` module implementing that port.
- Plan a `build_supabase_service_client(...)` factory in `ingestion_service.composition.clients` using `SUPABASE_URL` + `SUPABASE_SECRET_KEY`.
- Do **not** plan changes to `supabase-integration/__init__.py` public API for this phase.

**Trade-off to acknowledge:** DB-write responsibility is duplicated between `ingestion-service` and `supabase-integration`. The user accepted this to avoid changing the workspace dependency graph.

### 2. Atomic transaction: one Postgres RPC

**Decision:** D-05/D-06 require a single RPC `public.persist_draft_and_enqueue(...)` in migration `supabase-integration/migrations/007_phase9_persist_draft.sql`.

**What the RPC must do:**
1. Receive a complete material payload: `title`, `dek`, `body_markdown`, `slug`, `reading_minutes`, `format='статья'`, `status='draft'`, `provenance_label`, `source_url`, `youtube_video_id`, `source_author`, `source_published_at`, `roles`, plus `batch_size`.
2. `INSERT INTO materials ... ON CONFLICT (youtube_video_id) DO NOTHING`.
3. Look up the material id (new or existing).
4. Look up the latest unsent batch: `sent_at IS NULL`, order by `week_start DESC, created_at DESC`, limit 1.
5. If no unsent batch exists, or the chosen batch has `count(items) >= batch_size`, create a new batch with `week_start = date_trunc('week', current_date)::date`.
6. `INSERT INTO digest_shortlist_items (batch_id, material_id, rank, decision) VALUES (...)` with `rank = max(rank)+1` in the target batch.
7. Return `jsonb` with `material_id`, `slug`, `batch_id`, `rank`.

**Why an RPC:**
- Three separate SDK calls (material → batch → item) risk orphan rows if the process crashes or the network fails mid-way.
- The existing `claim_and_publish_digest` RPC (migrations 005/006) already establishes the pattern of doing multi-table writes atomically inside Postgres and revoking execute from `anon`/`authenticated`.
- The unique-constraint idempotency check and the batch-capacity check must be race-safe; a single transaction is the simplest correct model.

**RPC security model:**
- Create the RPC with `security invoker` and grant execute to `service_role` only, mirroring `claim_and_publish_digest`.
- The adapter will call it with a service-role client, so RLS policies do not block inserts.

### 3. Calling the RPC from Python

**Verified pattern:** `supabase-py` exposes `.rpc(name, params).execute()` on both sync and async clients (Context7 `/supabase/supabase-py`). The project already uses the **sync** client (`supabase.create_client`) in `supabase-integration/src/supabase_integration/client.py`.

**Expected adapter call shape:**

```python
from supabase import Client

class SupabaseDraftPersister:
    def __init__(self, client: Client) -> None:
        self._client = client

    def persist(self, material_draft: MaterialDraft) -> PersistResult:
        payload = {
            "p_title": material_draft.title,
            "p_slug": material_draft.slug,
            # ... all fields, plus p_batch_size
        }
        result = self._client.rpc("persist_draft_and_enqueue", payload).execute()
        data = result.data  # jsonb object from the RPC
        return PersistResult(...)
```

**Open detail for planner:** name the RPC parameters consistently (`p_` prefix is conventional in the existing `claim_and_publish_digest`).

### 4. Schema state and migration 007

**Current schema (migration 001):**
- `materials` already has `status material_status default 'draft'`, `slug unique`, `provenance_label not null`, `roles text[] default '{}'`, `reading_minutes int default 0`.
- `materials` does **not** yet have `source_url`, `youtube_video_id`, `source_author`, or `source_published_at`.
- `digest_shortlist_batches` has `week_start`, `created_at`, `sent_at` (nullable).
- `digest_shortlist_items` has `(batch_id, material_id)` PK, `rank > 0`, `decision default 'pending'`.

**Migration 007 must add:**
- `materials.source_url text not null`
- `materials.youtube_video_id text not null unique`
- `materials.source_author text not null`
- `materials.source_published_at timestamptz`
- The unique constraint above is also the idempotency key.
- `create or replace function public.persist_draft_and_enqueue(...)`.
- Grants/revokes for the RPC.

**Backward compatibility note:** `materials.provenance_label` already exists and is `not null`. Existing Phase 5 seed rows set it; new inserts must provide it.

### 5. Idempotency semantics

**Decision:** D-09/D-10/D-11.

- A re-run of the same `youtube_video_id` returns the existing `material_id`, `slug`, `batch_id`, and `rank`.
- No new shortlist item is created.
- Existing material content is **not** refreshed (D-10). If the operator wants a fresh draft, they must delete the old material first.
- The idempotency check lives in the RPC, not in Python, to avoid a race window.

**Planning implication:** the use-case layer does not need a pre-check; it passes the draft to the port and receives a `PersistResult`. Tests must verify that a second call with the same `video_id` returns identical ids and that the fake/port records only one persist call.

### 6. Material row completion (Python-side)

**Slug (D-12):**
- Format: `{slugify(title)[:50]}-{youtube_video_id}`.
- Example: `kak-ispolzovat-pgvector-dQw4w9WgXcQ`.
- Deterministic and unique because `youtube_video_id` is unique.
- Slug generation should live in the use-case or a small domain helper, not the adapter.

**Library choice:** `python-slugify` is the standard choice. Alternatively, a small local slugifier is acceptable under "Claude's Discretion". If using `python-slugify`, add it to `ingestion-service/pyproject.toml`.

**Reading minutes (D-13):**
- `reading_minutes = max(1, ceil(word_count(body_markdown) / 200))`.
- Word-count tokenization can be simple whitespace split for Russian/English mixed markdown; exact tokenizer is discretionary.

**Roles (D-14):**
- Extend `ArticleDraft` with `roles: list[RoleKind]` where `RoleKind` is a closed set: `employee | analyst | ds`.
- The LLM classifies audience; the DeepSeek adapter validates the output and falls back to `["employee"]` if the list is empty or contains invalid values.
- The assembler copies `roles` from `ArticleDraft` into `MaterialDraft`.
- This is technically a **Phase 8 contract amendment** owned by Phase 9 planning.

**Other columns (D-15):**
- `format = 'статья'`
- `status = 'draft'`
- `source_id = null` (the `ingestion_sources` table is not used for v1.1 provenance)
- No tags/relations.

### 7. Batch selection and rank assignment

**Batch creation (D-16):**
- New batch `week_start = date_trunc('week', current_date)::date` (Monday of current ISO week).
- Example: run on 2026-09-27 (Sunday) → `week_start = 2026-09-22` (Monday of that ISO week).

**Batch selection (D-08):**
- Pick the latest unsent batch (`sent_at IS NULL`), ordering by `week_start DESC, created_at DESC`.
- Tolerate multiple unsent batches; do not enforce a single-unsent-batch invariant.

**Capacity (D-17/D-18/D-19):**
- `rank = max(rank) + 1` within the target batch.
- Capacity counts **all** items in the batch, including rejected ones.
- Capacity is configurable via `SHORTLIST_BATCH_SIZE` (default 5); passed into the RPC.
- If the current batch is full, create a new unsent batch and enqueue there.

**Planning implication:** tests must cover:
- First ingest when no unsent batch exists → creates batch.
- Ingest when current batch has 1–4 items → appends.
- Ingest when current batch has 5 items → creates new batch.
- Rejected items still count toward capacity.

### 8. Error surface: `DraftPersistError` → `IngestError(stage="persist")`

**Pattern to mirror:** existing mappers in `ingestion_service/mapping/captions.py`, `metadata.py`, and `article.py`.

**Planned reason codes (locked contract):**
- `persist_conflict` — unexpected unique violation / data conflict.
- `batch_creation_failed` — RPC could not create a new batch.
- `rpc_error` — RPC raised an exception (PostgREST/Postgres error).
- `network_error` — could not reach Supabase.
- `unknown_persist_error` — fallback.

**Context allowlist:** do not forward raw Postgres messages, stack traces, or secret material. Safe context keys: `video_id`, `slug`, `batch_id`, `reason`.

**Mapping module:** plan `ingestion_service.mapping.persist` with `map_persist_error` and locked `PERSIST_REASONS` set.

### 9. Composition and env wiring

**Settings (`ingestion_service/composition/settings.py`):**
- Add `supabase_url: str`
- Add `supabase_secret_key: str`
- Add `shortlist_batch_size: int = 5` (validate positive integer, fail at startup like `MAX_TRANSCRIPT_CHARS`)

**Clients (`ingestion_service/composition/clients.py`):**
- Add `build_supabase_service_client(settings: Settings) -> Client` using `supabase.create_client(settings.supabase_url, settings.supabase_secret_key)`.
- Add a factory that builds the `SupabaseDraftPersister` from the client.

**Env example (`ingestion-service/.env.example`):**
```dotenv
SUPABASE_URL=https://...
SUPABASE_SECRET_KEY=...
SHORTLIST_BATCH_SIZE=5
```

### 10. TDD and fake strategy

**Requirement from rules:** no production code without a failing test first.

**Plan tests in this order:**
1. **Port contract test:** define `PersistPort` Protocol and `PersistResult` dataclass; write a test that a fake implementation can satisfy it.
2. **Mapper test:** `DraftPersistError` subtypes → `IngestError(stage="persist")` with locked reasons and redacted context.
3. **Use-case test (happy path):** given a `MaterialDraft`, call `persist` on a fake port; assert returned `PersistResult` fields.
4. **Use-case test (idempotency):** call persist twice with same `video_id`; assert fake records one call and same result.
5. **Adapter contract test (with mocked Supabase client):** mock `client.rpc(...).execute()` returning expected JSON; assert adapter emits correct `PersistResult`.
6. **Adapter error mapping test:** mock RPC raising exceptions; assert `DraftPersistError` with correct reason.
7. **Migration test:** verify `007` SQL adds columns, unique constraint, and function; optional integration test skipped by default.
8. **Phase 7 CAP-02 deferred live proof:** fake failing `TranscriptProvider` + spy `PersistPort` → `persist.calls == []`.

**Fake pattern:** mirror `FakeTranscriptProvider` / `FakeVideoMetadataProvider` in `data-collection/tests_support/fakes.py`. The fake should record calls and support scripted failures by `video_id` or slug.

### 11. Phase 8 amendments needed

Because `ArticleDraft` must gain `roles`, Phase 9 planning must include tasks that touch Phase 8 artifacts:

- `data-collection/src/data_collection/dto/article_draft.py` — add `roles: list[RoleKind]`.
- `data-collection/src/data_collection/templates/lecture.md` and `podcast.md` — add audience-role instruction.
- `data-collection/src/data_collection/adapters/deepseek_article.py` — validate `roles`, fallback to `["employee"]`.
- `data-collection/src/data_collection/assemble.py` — copy `roles` into `MaterialDraft`.
- `data-collection/src/data_collection/dto/material_draft.py` — add `roles` field (if not already present; currently `roles` is only on the DB domain model).
- Tests: update `test_article_draft_internal.py`, `test_deepseek_article_adapter.py`, `test_fake_article_generator.py`, `test_assemble_material_draft.py`, etc.

**Decision note:** D-14 marks this as "costly" because it changes the prompt templates, DeepSeek adapter validation, and Phase 8 tests. The planner should allocate a dedicated plan wave (e.g., `09-01`) to these amendments before building the persist adapter.

### 12. What the backend/SPA needs

**Nothing.** The existing `/admin/digest` path already reads `digest_shortlist_items` joined with `materials` and surfaces `status=draft` (proven by Phase 5 seed `phase5-admin-draft`). Phase 9 must not add backend or frontend code.

---

## Validation Architecture

> This section seeds the per-phase Nyquist validation strategy (`09-VALIDATION.md`). It describes what Phase 9 must prove, how success is scored, which reference cases are required, what guardrails prevent regressions, and what production signals should be watched after ship.

### Purpose

Phase 9 introduces the first database write path in the ingestion pipeline and crosses the boundary from pure compute (captions + LLM) to durable state. Validation must therefore prove **correctness of persisted data**, **atomicity of the write**, **idempotent re-runs**, **secure error handling**, and **compatibility with the existing admin shortlist surface**. No live DeepSeek calls or Supabase network access are required for the gate; unit tests with fakes and mocked SDKs are sufficient.

### Evaluation Dimensions

| ID | Dimension | Requirement(s) | Scoring Rubric | Critical |
|----|-----------|---------------|----------------|----------|
| D1 | Material row completeness | PERS-01 | **PASS**: successful run inserts `materials` with `status='draft'` and all provenance fields (`source_url`, `youtube_video_id`, `source_author`, `source_published_at`, `provenance_label`). **PARTIAL**: row inserted but one non-null provenance field missing/null. **FAIL**: status not `draft` or provenance field absent. | Yes |
| D2 | Slug + reading minutes + roles | PERS-01, D-12…D-15 | **PASS**: slug follows `{slugify(title)[:50]}-{video_id}`; `reading_minutes >= 1` and reflects word count; `roles` is a non-empty subset of `{employee, analyst, ds}`. **PARTIAL**: one of the three incorrect. **FAIL**: multiple wrong or missing. | Yes |
| D3 | Shortlist enqueue | PERS-02 | **PASS**: item inserted on current unsent batch with `decision='pending'` and `rank = max(rank)+1`. **PARTIAL**: enqueued but rank/ decision wrong. **FAIL**: no item or wrong batch. | Yes |
| D4 | Batch overflow | PERS-02, D-16…D-19 | **PASS**: when current unsent batch count >= `SHORTLIST_BATCH_SIZE`, a new unsent batch is created with `week_start = date_trunc('week', current_date)::date` and the item lands there. **PARTIAL**: new batch created but `week_start` wrong. **FAIL**: duplicate insert into full batch or hard failure. | Yes |
| D5 | Idempotency | CLI-02, D-09…D-11 | **PASS**: re-running same `youtube_video_id` returns identical `material_id`, `slug`, `batch_id`, `rank`; no new material or shortlist row. **PARTIAL**: returns same ids but issues a second shortlist row. **FAIL**: duplicate material/shortlist rows. | Yes |
| D6 | Atomic fail-closed | PERS-01/PERS-02, D-05 | **PASS**: any exception inside persist maps to `IngestError(stage='persist')` and leaves zero DB rows. **PARTIAL**: error mapped but partial rows possible in some failure modes. **FAIL**: unmapped exception leaks or orphan rows created. | Yes |
| D7 | Persist error taxonomy | CLI-04, D-04 | **PASS**: `DraftPersistError` reasons are a locked set; mapper forwards only allowlisted context keys (`video_id`, `slug`, `batch_id`, `reason`); no secret or stack trace in `IngestError.to_dict()`. **PARTIAL**: reason set locked but context leaks raw Postgres message. **FAIL**: arbitrary reasons or secret leakage. | Yes |
| D8 | Phase 8 contract amendment | D-14 | **PASS**: `ArticleDraft` carries `roles`; both templates instruct the LLM; DeepSeek adapter validates/falls back to `["employee"]`; assembler copies into `MaterialDraft`; Phase 8 tests updated and green. **PARTIAL**: roles flow works but tests not updated. **FAIL**: roles missing from any layer. | Yes |
| D9 | Migration correctness | D-06, D-09 | **PASS**: migration `007` adds required columns, unique constraint, and RPC; is idempotent; grants/revokes mirror `claim_and_publish_digest`; no destructive statements. **PARTIAL**: migration works but lacks grants. **FAIL**: missing columns/constraint or non-idempotent. | Yes |
| D10 | Ports & Adapters hygiene | architecture.mdc | **PASS**: port is a `Protocol` in application layer; adapter implements it; no `supabase` imports outside adapter/composition; no env access outside `Settings`; dependencies point inward. **PARTIAL**: one minor leak. **FAIL**: deep imports or business logic in adapter/CLI. | Yes |
| D11 | Composition wiring | D-02, D-19 | **PASS**: `Settings` loads/validates `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SHORTLIST_BATCH_SIZE`; `clients` builds service-role client and persister; `.env.example` updated. **PARTIAL**: settings load but no validation. **FAIL**: missing wiring or secrets logged. | No |
| D12 | Backward compatibility | ADMIN-01 | **PASS**: existing `/admin/digest` shortlist still loads after migration; Phase 5 demo seed intact; no backend/SPA code changes required. **PARTIAL**: requires minor backend tweak. **FAIL**: breaks existing admin view. | No |

**Scoring summary:** D1–D10 are **critical** (any FAIL blocks ship). D11–D12 are **required** but may be deferred to a fast-follow if explicitly approved. A Nyquist-compliant phase scores **PASS on all critical dimensions and no FAIL elsewhere**.

### Reference Dataset & Fixtures

The validation dataset must cover the state space the RPC sees. Use the fixtures below in unit and integration tests.

| Fixture ID | Description | Used in |
|------------|-------------|---------|
| `material_draft_ru` | Valid `MaterialDraft` with `source_published_at` aware, Russian title, 400-word body, no roles | D1, D3 happy path |
| `material_draft_en` | Same with English source provenance label containing translation suffix | D1, CLI-03 prep |
| `material_draft_no_published_at` | `source_published_at = None` | D1 nullable provenance |
| `material_draft_long_body` | Body with >200 words to prove `reading_minutes > 1` | D2 |
| `material_draft_empty_roles` | LLM returned `[]`; assembler/adapter should normalize to `["employee"]` | D2, D8 |
| `material_draft_invalid_roles` | LLM returned `["manager", "employee"]`; filter unknown, keep `employee` | D8 |
| `video_id_duplicate` | Same `youtube_video_id` as `material_draft_ru` | D5 |
| `batch_empty` | No unsent batch in the (mock) DB | D3, D4 |
| `batch_with_n(n=1..5)` | Unsent batch already containing `n` pending/rejected items | D3, D4 overflow |
| `batch_sent` | Latest batch has `sent_at` set | D3 current-batch selection |
| `rpc_response_happy` | `{"material_id": 101, "slug": "...", "batch_id": 7, "rank": 3}` | Adapter unit tests |
| `rpc_response_conflict` | Postgres unique-violation code `23505` | D6, D7 |
| `rpc_response_batch_failed` | RPC raises `check_violation` or `P0001` | D6, D7 |
| `sdk_network_error` | `supabase-py` raises `APIConnectionError` | D6, D7 |
| `settings_valid` | `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SHORTLIST_BATCH_SIZE=5` | D10, D11 |
| `settings_invalid_batch_size` | `SHORTLIST_BATCH_SIZE=0` or non-integer | D11 validation |

**Integration dataset (shared VM, optional and skipped by default):**
- Apply migration `007` to the shared VM.
- Run one real YouTube video through the full pipeline end-to-end and verify row appears in `/admin/digest`.
- Re-run the same video and confirm idempotency.

### Guardrails

Guardrails are runtime or design-time checks that prevent the phase from entering an unsafe state.

| Guardrail | Mechanism | Prevents |
|-----------|-----------|----------|
| Unique constraint on `materials.youtube_video_id` | Schema (migration 007) | Duplicate material rows on concurrent ingests (D5) |
| Single RPC transaction | `persist_draft_and_enqueue` PL/pgSQL | Orphan material without shortlist item, or vice versa (D6) |
| `ON CONFLICT ... DO NOTHING` + lookup | Inside RPC | Race between two simultaneous ingests of the same video (D5) |
| `security invoker` + `service_role` execute only | RPC grants/revokes | Anonymous/authenticated users cannot write drafts or batches (D7, D10) |
| Context allowlist in `map_persist_error` | Python mapper | Secret leakage (`SUPABASE_SECRET_KEY`, raw SQL) in operator-facing output (D7) |
| `MaterialDraft` Pydantic validation | `data-collection` DTO | Blank/invalid fields reaching the RPC (D1) |
| `SHORTLIST_BATCH_SIZE` positive-integer validation | `Settings.from_env` | Zero or negative capacity causing infinite batches (D4, D11) |
| `status='draft'` hard-coded in RPC insert | Migration SQL | Operator accidentally inserting `ready` material and bypassing admin triage (D1) |
| No Supabase client creation outside composition | `architecture.mdc` | Adapter/use-case coupling to infrastructure (D10) |
| Fail-closed envelope | `IngestError(stage='persist')` for any adapter failure | Partial success being reported as success (D6) |
| Re-run no-op semantics | RPC returns existing ids without UPDATE | Silent content refresh that violates CLI-02 contract (D5) |

### Production Monitoring Signals

After Phase 9 ships, monitor these signals in the production Supabase/observability stack. They indicate whether the write path stays healthy and whether idempotency/capacity assumptions hold.

| Signal | Query / Source | Healthy Threshold | Alert Condition |
|--------|---------------|-------------------|-----------------|
| Persist success rate | `activity_events kind='ingest_persist_succeeded'` / CLI exit code logs | > 98% over 1h | < 95% for 10 minutes |
| Persist failure reasons | `IngestError.to_dict()` reason distribution | `unknown_persist_error` < 5% of failures | Spike in `rpc_error` or `network_error` |
| Idempotency hit rate | `materials.youtube_video_id` duplicate attempts vs new inserts | Re-runs < 30% of total runs | Sudden jump may indicate operator confusion or loop |
| Batch creation rate | New `digest_shortlist_batches` rows per hour | Stable, aligned with ingest schedule | > 2 new unsent batches per hour (possible capacity misconfiguration) |
| Average unsent batch size | `count(*) filter (where sent_at is null)` per batch | < `SHORTLIST_BATCH_SIZE` | Batch at capacity for >24h without send (editorial bottleneck) |
| RPC latency p50/p99 | Supabase Postgres logs / PostgREST metrics | p50 < 100ms, p99 < 500ms | p99 > 2s |
| Zero-row failure count | Logs where `IngestError(stage='persist')` and no material/shortlist rows exist | 0 after any failure | Any orphan row after reported failure |
| Migration drift | Schema hash / migration filename check | Migration `007` applied on all environments | Missing migration on shared VM |
| Rejected item capacity pressure | `%` of batch items with `decision='rejected'` | < 50% | Batch full of rejected items blocks new drafts (D4) |

**Recommended dashboards:**
- Ingest pipeline stage funnel: `url → captions → metadata → llm → persist` with counts and error reasons per stage.
- Admin shortlist load: number of unsent drafts, oldest unsent batch age, average time from `draft` to first decision.

### Traceability to Requirements and Threats

| Requirement | Critical Dimensions | Threat / Risk Addressed |
|-------------|---------------------|------------------------|
| PERS-01 | D1, D2 | T-09-PARTIAL: partial material row leaves admin without provenance |
| PERS-02 | D3, D4 | T-09-OVERFLOW: full batch silently drops drafts or overfills |
| CLI-02 | D5 | T-09-DUPE: duplicate charges/entries from operator re-runs |
| CLI-04 | D7 | T-09-LEAK: operator output exposes secrets or internals |
| architecture.mdc | D10 | T-09-COUPLING: Supabase specifics leak into use-cases/domain |
| D-05/D-06 | D6, D9 | T-09-ORPHAN: crash mid-persist leaves orphan rows |
| D-14 | D8 | T-09-ROLES: audience targeting missing from LLM output |

---

## Risks and Open Questions for the Planner

| Risk | Mitigation in plan |
|------|-------------------|
| Migration 007 not applied to shared VM before Phase 10 UAT | Add explicit runbook/MCP apply step and a `migrate-007` checkpoint before UAT. |
| `supabase-py` sync `.rpc(...).execute()` returns `APIResponse` with `.data` as a dict or list-of-dicts depending on RPC return type | Adapter tests should assert shape; use `jsonb_build_object` in the RPC so `.data` is a single dict. |
| `python-slugify` vs local slugifier | Decide in first planning wave; either adds a dependency or a small helper with tests. |
| Word-count tokenization for Russian markdown | Keep it simple (whitespace split); document the discretionary choice. |
| `source_published_at` nullable but `MaterialDraft` requires timezone-aware datetime | Assembler already copies nullable `published_at`; adapter must pass `None` or ISO string to RPC. |
| Roles fallback behavior in DeepSeek adapter | Define strict validation: unknown role strings are filtered; if list empty → `["employee"]`. |
| Re-runs after material approved/rejected on shortlist | Out of scope per D-10; document that re-runs are no-ops regardless of shortlist decision. |

---

## Suggested Plan Wave Breakdown

Based on dependencies and TDD order:

1. **09-01 — Amend Phase 8 contract with `roles`**
   - Add `RoleKind` enum, extend `ArticleDraft`, update templates, DeepSeek adapter validation, assembler, and tests.
2. **09-02 — Persist port + fake + mapper**
   - Define `PersistPort`, `PersistResult`, `DraftPersistError`, `map_persist_error`, and in-memory fake.
3. **09-03 — Migration 007 + Supabase adapter**
   - Write migration; implement `SupabaseDraftPersister` with mocked-client tests.
4. **09-04 — Composition wiring + settings + CAP-02 deferred proof**
   - Add env/settings/clients; wire fake persist port into use-case; prove captions failure writes zero rows.

---

## Sources

- **Canonical decisions:** `.planning/phases/09-draft-persist-shortlist-enqueue/09-CONTEXT.md`
- **Requirements:** `.planning/REQUIREMENTS.md` — PERS-01, PERS-02, CLI-01, CLI-02
- **Project state:** `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/ROADMAP.md`
- **Architecture rules:** `.cursor/rules/architecture.mdc`, `.cursor/rules/tdd.mdc`, `AGENTS.md`
- **Schema:** `supabase-integration/migrations/001_initial_schema.sql`, `005_phase5_admin_shortlist.sql`, `006_claim_publish_material_ids.sql`
- **Existing adapters:** `supabase-integration/src/supabase_integration/material_repository.py`, `shortlist_repository.py`, `client.py`, `__init__.py`
- **Ingestion contracts:** `data-collection/src/data_collection/dto/material_draft.py`, `article_draft.py`, `assemble.py`, `tests_support/fakes.py`, `__init__.py`
- **Ingestion error/mapping patterns:** `ingestion-service/src/ingestion_service/domain/errors.py`, `mapping/captions.py`, `mapping/metadata.py`, `mapping/article.py`
- **Composition patterns:** `ingestion-service/src/ingestion_service/composition/settings.py`, `clients.py`
- **Supabase-py RPC:** Context7 `/supabase/supabase-py` (sync `client.rpc(...).execute()` pattern)
- **Domain model:** `backend/src/backend/domain/material.py`, `backend/src/backend/domain/errors.py`
- **Prompt templates:** `data-collection/src/data_collection/templates/lecture.md`, `podcast.md`
- **Validation file patterns:** `.planning/phases/06-ports-dtos/06-VALIDATION.md`, `07-captions-adapter/07-VALIDATION.md`, `08-deepseek-article-templates/08-VALIDATION.md`

---

## RESEARCH COMPLETE
