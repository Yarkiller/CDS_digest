# Phase 9: Draft Persist & Shortlist Enqueue - Context

**Gathered:** 2026-09-27
**Status:** Ready for planning

<domain>
## Phase Boundary

A successful ingest run writes a `materials` row with `status=draft` and required provenance fields, then enqueues it on the current unsent `digest_shortlist_batches` row with `decision=pending` and `rank = max(rank)+1`. When the current unsent batch is full, the run atomically creates a new unsent batch and enqueues there. Re-running the same YouTube `video_id` returns the existing material/shortlist ids without creating duplicates or refreshing content. All failures at the persist stage produce zero DB rows and map to `IngestError(stage="persist")`.

Backend/SPA stay readers. The Typer CLI one-shot, idempotency printing, staged progress, and UAT belong to Phase 10.
</domain>

<decisions>
## Implementation Decisions

### Persist port and adapter ownership
- **D-01:** The persist port and its Supabase-backed adapter both live inside `ingestion-service`. `ingestion-service` does not take a new workspace dependency on `supabase-integration` for this phase. — **Reversibility:** costly — moving the adapter out later means extracting the port, adapter, and env wiring into another module and updating all tests/composition.
- **D-02:** `ingestion-service` adds the `supabase` PyPI package to `ingestion-service/pyproject.toml` and builds its own service-role client in `ingestion-service/composition/` from `SUPABASE_URL` + `SUPABASE_SECRET_KEY`. — **Reversibility:** reversible — dependency and env names are local.
- **D-03:** Port signature: `PersistPort.persist(material_draft: MaterialDraft) -> PersistResult`, where `PersistResult` is a dataclass with `material_id`, `slug`, `batch_id`, `rank`. (User noted `PersistPort.persist` is tautological and suggested `DraftPersister.persist` as an optional rename; non-blocking.) — **Reversibility:** costly — `PersistResult` fields are the CLI-01 operator output contract.
- **D-04:** The adapter raises a module-local `DraftPersistError` with stable reason codes; a mapper in `ingestion_service.mapping.persist` converts it to `IngestError(stage="persist")`, mirroring the captions/metadata/article mappers. — **Reversibility:** costly — reason codes become part of the operator JSON contract.

### Atomic transaction boundary
- **D-05:** Persist is one Postgres RPC (e.g., `persist_draft_and_enqueue(...)`) that INSERTs the `materials` row, finds or creates the current unsent `digest_shortlist_batches` row, and INSERTs the `digest_shortlist_items` row in a single transaction. Any failure rolls back to zero rows. — **Reversibility:** one-way — once the RPC is deployed, the operator pipeline depends on its signature and behavior; changing it requires a new migration.
- **D-06:** The RPC lives in a tracked migration: `supabase-integration/migrations/007_phase9_persist_draft.sql` (`create or replace function public.persist_draft_and_enqueue(...)`). — **Reversibility:** one-way — migration is the canonical schema record for the shared VM.
- **D-07:** Python generates `slug` and `reading_minutes` before calling the RPC; the RPC only inserts the row and enqueues. — **Reversibility:** reversible — rules live in Python and can be changed without a migration.
- **D-08:** If multiple unsent batches exist, the RPC picks the latest one (`week_start` desc, then `created_at` desc). If that batch is full, it creates a new batch. — **Reversibility:** reversible — behavior is contained in the RPC body.

### Idempotency / duplicate handling
- **D-09:** Add a unique constraint on `materials.youtube_video_id` in migration `007`. A re-run hits `ON CONFLICT (youtube_video_id) DO NOTHING`, the RPC looks up the existing material and its unsent shortlist row, and returns the existing ids. — **Reversibility:** one-way — adding and later removing a unique constraint is a schema change.
- **D-10:** Re-runs are no-ops: no new shortlist row is created and the existing material content is not refreshed. If the operator wants a refreshed draft, they must delete the old material first. — **Reversibility:** costly — changing this later changes CLI-02 semantics and the RPC lookup path.
- **D-11:** Idempotency lives in the RPC (single round-trip, no race window), not in a Python pre-check. — **Reversibility:** reversible.

### Material row completion
- **D-12:** Slug is generated in Python: slugify title, truncate to ~50 chars, append `-{youtube_video_id}`. Example shape: `{slugify(title)[:50]}-{video_id}`. — **Reversibility:** costly — the slug is the admin-visible URL and idempotency assumes slug stability for a given video.
- **D-13:** `reading_minutes = max(1, ceil(word_count(body_markdown) / 200))`. — **Reversibility:** reversible.
- **D-14:** `materials.roles` is populated from the LLM output. Extend `ArticleDraft` (Phase 8 output contract) to include `roles: list[RoleKind]` where `RoleKind` is `employee | analyst | ds`. The LLM classifies audience; if the LLM returns an invalid or empty list, fall back to `["employee"]`. — **Reversibility:** costly — changes `ArticleDraft`, the prompt templates, the DeepSeek adapter validation, and Phase 8 tests. This is a cross-phase amendment to Phase 8 artifacts owned by Phase 9 planning.
- **D-14a / decision A (by design):** RoleKind is closed only in Python (`normalize_roles` on `ArticleDraft` / `MaterialDraft`). The RPC `persist_draft_and_enqueue` writes `coalesce(p_roles, '{}')` with no CHECK. A direct `service_role` call can persist unknown roles; that is accepted — the ingest CLI is the only v1 writer. — **Reversibility:** reversible — a CHECK can be added later once existing rows are clean.
- **D-15:** Other `materials` columns: `format = 'статья'`, `status = 'draft'`, `source_id = null`, no tags/relations. — **Reversibility:** reversible.

### Batch selection & rank assignment
- **D-16:** A new batch uses `week_start = date_trunc('week', current_date)::date` (Monday of current week). — **Reversibility:** reversible.
- **D-17:** New item rank = `max(rank) + 1` within the target batch. — **Reversibility:** reversible.
- **D-18:** Batch capacity counts all items in the batch, including rejected ones. Rejected items still occupy a slot until the batch is sent. — **Reversibility:** reversible.
- **D-19:** Batch capacity is configurable via env var `SHORTLIST_BATCH_SIZE` with default `5`; the value is passed into the RPC. — **Reversibility:** reversible.

### Claude's Discretion
- Exact Python helper for slugification (e.g., `python-slugify` dependency vs a small local function) as long as the slug format matches D-12.
- Exact word-count tokenization for `reading_minutes` as long as it follows D-13.
- Exact `DraftPersistError` subtype names and reason-code set, as long as the mapper emits locked `persist` reasons.
- Whether the RPC is called via `supabase` SDK `.rpc(...)` or raw PostgREST, as long as the call is inside the adapter and errors map to `DraftPersistError`.
- File/module layout inside `ingestion-service` for the persist port, adapter, mapper, and fake as long as the public surface stays clean.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 9 goal, success criteria, PERS-01/PERS-02
- `.planning/REQUIREMENTS.md` — PERS-01, PERS-02, CLI-02 (idempotency), CLI-01 (output fields)
- `.planning/PROJECT.md` — v1.1 ingestion milestone; material = prepared article; DeepSeek MVP bend of ADR-0002
- `.planning/phases/06-ports-dtos/06-CONTEXT.md` — `MaterialDraft` fields, assembler, `source_published_at` nullable
- `.planning/phases/07-captions-adapter/07-CONTEXT.md` — `IngestError` stages include `persist`; fail-closed envelope pattern
- `.planning/phases/08-deepseek-article-templates/08-CONTEXT.md` — `ArticleDraft` shape, always-Russian output, locked LLM reason codes

### Architecture & process rules
- `.cursor/rules/architecture.mdc` — Ports & Adapters; composition owns wiring
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — FoundryModels long-term; DeepSeek temporary bend
- `docs/adr/0004-self-hosted-supabase-on-vm.md` — self-hosted Supabase as primary store

### Schema & existing DB adapters
- `supabase-integration/migrations/001_initial_schema.sql` — base `materials`, `digest_shortlist_batches`, `digest_shortlist_items` schema
- `supabase-integration/migrations/005_phase5_admin_shortlist.sql` — admin shortlist columns + demo seed + `claim_and_publish_digest` RPC
- `supabase-integration/migrations/006_claim_publish_material_ids.sql` — updated RPC signature
- `supabase-integration/src/supabase_integration/material_repository.py` — existing read/upsert pattern against `materials`
- `supabase-integration/src/supabase_integration/shortlist_repository.py` — existing batch ordering and `sent_at` semantics

### Ingestion code contracts
- `data-collection/src/data_collection/dto/material_draft.py` — fields persisted by this phase
- `data-collection/src/data_collection/dto/article_draft.py` — to be extended with `roles`
- `data-collection/src/data_collection/templates/lecture.md` — prompt to update for roles
- `data-collection/src/data_collection/templates/podcast.md` — prompt to update for roles
- `data-collection/src/data_collection/assemble.py` — `MaterialDraft` assembler
- `ingestion-service/src/ingestion_service/domain/errors.py` — `IngestError` and `Stage` literal
- `ingestion-service/src/ingestion_service/composition/settings.py` — where `SHORTLIST_BATCH_SIZE` and Supabase env are loaded
- `ingestion-service/src/ingestion_service/composition/clients.py` — pattern for building injected clients

### Domain
- `backend/src/backend/domain/material.py` — domain `Material` shape and `MaterialStatus`
- `backend/src/backend/domain/errors.py` — `PersistenceError` pattern for adapters

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ingestion_service.domain.errors.IngestError` and existing `map_*_error` mappers — add `map_persist_error` following the same locked-reason + context-allowlist pattern.
- `ingestion_service.composition.Settings` — already loads `YOUTUBE_PROXY_URL`, `MAX_TRANSCRIPT_CHARS`, DeepSeek settings. Add `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, and `SHORTLIST_BATCH_SIZE` there.
- `ingestion_service.composition.clients` — already builds ready YouTube/httpx/DeepSeek clients. Add a `build_supabase_service_client(settings)` factory.
- `SupabaseMaterialRepository` / `SupabaseShortlistRepository` in `supabase-integration` — read patterns and table shapes to mirror in the new RPC.
- `data-collection.tests_support.fakes` — pattern for in-memory fakes with call spies.

### Established Patterns
- Ports are `typing.Protocol` in the consumer's application layer; adapters implement them; composition wires.
- Adapter errors are mapped at the boundary into module-local exceptions, then into `IngestError` in `ingestion_service.mapping`.
- Unit tests use in-memory fakes; integration tests are optional and skipped by default.
- Migrations are idempotent `create or replace` / `add column if not exists` and applied manually to the shared VM.

### Integration Points
- Phase 8 `DeepSeekArticleGenerator` returns `ArticleDraft`; Phase 9 extends `ArticleDraft` with `roles` and the assembler copies them into `MaterialDraft`.
- Phase 10 Typer CLI will call the persist use-case and print `material_id`, `slug`, `batch_id`, `rank`.
- Existing `/admin/digest` shortlist UI reads `digest_shortlist_items` + `materials`; no backend/SPA changes needed for drafts to appear.
- Migration `007` must be applied to the shared VM before Phase 10 UAT.

</code_context>

<specifics>
## Specific Ideas

- Slug example: `{slugify(title)[:50]}-{video_id}` (e.g., `kak-ispolzovat-pgvector-dQw4w9WgXcQ`).
- `reading_minutes` example: a 400-word draft → `2` minutes.
- New batch `week_start` example: if run on 2026-09-27 (Sunday), the batch week_start is 2026-09-22 (Monday of that ISO week) — clarify in tests if using ISO-week semantics.
- Role prompt addition (sketch): "Кто целевая аудитория материала? Верни список ролей из: employee, analyst, ds." Fallback to `["employee"]` if missing/invalid.
- Env vars to add to `ingestion-service/.env.example`: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SHORTLIST_BATCH_SIZE` (optional, default 5).
</specifics>

<deferred>
## Deferred Ideas

- HTTP API or scheduler for ingestion — Phase 10 is CLI-only; HTTP/scheduler is v2 (ING-01, ING-02).
- Transcription when captions are missing — v2 (ING-03).
- Transcript chunking for context budget — v2 (ING-04).
- Public leaderboard, quiz cards, YAML pipeline UI, live SMTP, signup mail — post-v1.1 per PROJECT.md.
- Refreshing draft content on re-run — explicitly rejected; delete-then-re-ingest if refresh needed.

</deferred>

---

*Phase: 9-Draft Persist & Shortlist Enqueue*
*Context gathered: 2026-09-27*
