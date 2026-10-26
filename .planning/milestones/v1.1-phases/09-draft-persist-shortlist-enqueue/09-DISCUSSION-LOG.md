# Phase 9: Draft Persist & Shortlist Enqueue - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-27
**Phase:** 9-Draft Persist & Shortlist Enqueue
**Areas discussed:** Persist port/adapter ownership, Atomic transaction boundary, Idempotency / duplicate handling, Material row completion, Batch selection & rank assignment

---

## Persist port/adapter ownership

| Option | Description | Selected |
|--------|-------------|----------|
| Port in `ingestion-service/application/ports/`, adapter in `supabase-integration` | Keeps DB adapters in one module; adds workspace dependency. | |
| Port and adapter both inside `ingestion-service` | No new workspace dependency; internal Supabase adapter. | ✓ |
| Port in `backend/application/ports/`, adapter in `supabase-integration` | Aligns with existing backend repository pattern; adds `backend` dependency. | |

**User's choice:** Port and adapter both inside `ingestion-service`.
**Notes:** User accepted the trade-off of duplicating DB adapter responsibility to avoid changing the workspace dependency graph.

---

### Follow-up: Supabase client source

| Option | Description | Selected |
|--------|-------------|----------|
| Add `supabase` PyPI package to `ingestion-service` | Build service-role client inside `ingestion-service/composition/`. | ✓ |
| Import `create_service_role_client` from `supabase-integration` | Reuse existing client factory without a declared dependency. | |

**User's choice:** Add `supabase` directly to `ingestion-service`.

---

### Follow-up: Port signature

| Option | Description | Selected |
|--------|-------------|----------|
| `DraftRepository.save(...) -> SavedDraft` | Matches backend repository naming. | |
| `PersistPort.persist(...) -> PersistResult` | Pipeline-stage semantics; returns `material_id`, `slug`, `batch_id`, `rank`. | ✓ |

**User's choice:** `PersistPort.persist(MaterialDraft) -> PersistResult`.
**Notes:** User noted `PersistPort.persist` is tautological and suggested `DraftPersister.persist` as an optional rename; recorded as non-blocking.

---

### Follow-up: Failure surface

| Option | Description | Selected |
|--------|-------------|----------|
| Raise `DraftPersistError` and map to `IngestError` | Mirrors captions/metadata/article mappers. | ✓ |
| Return result union (`PersistResult \| PersistFailure`) | Heavier refactor of existing exception-based flow. | |

**User's choice:** Raise `DraftPersistError` and map to `IngestError(stage="persist")`.

---

## Atomic transaction boundary

| Option | Description | Selected |
|--------|-------------|----------|
| One Postgres RPC for all three steps | INSERT material, find/create batch, INSERT item — single transaction, zero rows on failure. | ✓ |
| Python orchestrates three SDK calls with compensation | Simpler to read, but not atomic and risks orphan rows. | |
| RPC inserts material; Python handles batch/item | Material row may exist without shortlist item on failure. | |

**User's choice:** Single Postgres RPC.

---

### Follow-up: RPC location

| Option | Description | Selected |
|--------|-------------|----------|
| Tracked migration file (`007_phase9_persist_draft.sql`) | Versioned with `create or replace function`. | ✓ |
| Ad-hoc apply via Studio/MCP and runbook only | No tracked migration. | |

**User's choice:** Tracked migration file.

---

### Follow-up: What RPC generates vs. receives

| Option | Description | Selected |
|--------|-------------|----------|
| Python generates `slug` and `reading_minutes` | Keeps business rules testable in Python. | ✓ |
| RPC generates `slug` and `reading_minutes` internally | One less thing for Python to coordinate. | |

**User's choice:** Python generates and passes `slug`/`reading_minutes`.

---

### Follow-up: Multiple unsent batches

| Option | Description | Selected |
|--------|-------------|----------|
| Pick latest unsent batch; create new if full | Tolerates multiple unsent batches. | ✓ |
| Enforce single-unsent-batch invariant and raise error | Strict model, but requires cleanup if duplicates exist. | |

**User's choice:** Pick latest unsent batch; create new if full.

---

## Idempotency / duplicate handling

| Option | Description | Selected |
|--------|-------------|----------|
| Unique constraint on `materials.youtube_video_id` | Treats a video as a single material across all time. | ✓ |
| Unique constraint on `materials.slug` only | Allows duplicate video ids with different slugs. | |
| Both unique on `youtube_video_id` and `slug` | Most defensive; requires careful slug generation. | |

**User's choice:** Unique on `youtube_video_id`.

---

### Follow-up: Shortlist re-run behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Material-level idempotent: no shortlist changes on re-run | First successful run did the enqueue; re-runs are no-ops. | ✓ |
| Enqueue if material exists but is not in any current unsent batch | Allows re-running a video after its previous batch was sent. | |
| Fail if material exists but is not in an unsent batch | Re-runs after send are out of scope. | |

**User's choice:** Material-level idempotent no-op.

---

### Follow-up: Where idempotency check lives

| Option | Description | Selected |
|--------|-------------|----------|
| RPC handles idempotency in one round-trip | `ON CONFLICT ... DO NOTHING` then lookup; no race window. | ✓ |
| Python use-case checks before RPC | Extra round-trip and race window. | |

**User's choice:** RPC handles it.

---

### Follow-up: Content refresh on re-run

| Option | Description | Selected |
|--------|-------------|----------|
| No refresh on re-run | True no-op; delete old draft to refresh. | ✓ |
| Refresh title/dek/body on conflict (upsert semantics) | Keeps same ids but updates content. | |

**User's choice:** No refresh on re-run.

---

## Material row completion

| Option | Description | Selected |
|--------|-------------|----------|
| `{slugify(title)[:50]}-{video_id}` | Human-readable, deterministic, unique. | ✓ |
| Use YouTube `video_id` directly as the slug | Simple but not human-readable. | |
| Slugify title + short hash of video id | Readable but less deterministic. | |

**User's choice:** `{slugify(title)[:50]}-{video_id}`.

---

### Follow-up: `reading_minutes`

| Option | Description | Selected |
|--------|-------------|----------|
| Word count / 200 | Standard editorial estimate. | ✓ |
| Default 0 | Minimal adapter; fill later. | |
| Character count / 1000 | Cheap but less accurate for Russian. | |

**User's choice:** `max(1, ceil(word_count / 200))`.

---

### Follow-up: `materials.roles`

| Option | Description | Selected |
|--------|-------------|----------|
| Empty array; admin assigns later | No LLM change. | |
| Default `{'employee'}` | Every draft visible to base persona. | |
| LLM returns roles; extend `ArticleDraft` | Closed set employee/analyst/ds; Phase 9 persists. | ✓ |

**User's choice:** Extend `ArticleDraft` with `roles: list[RoleKind]`.
**Notes:** This amends the Phase 8 output contract; Phase 9 planning must include updating `ArticleDraft`, templates, DeepSeek adapter validation, and Phase 8 tests.

---

### Follow-up: Role set and fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Closed enum with fallback to `["employee"]` | `employee | analyst | ds`; at least one required; fallback on invalid/empty. | ✓ |
| Closed enum, strict fail on invalid/empty | Invalid/empty LLM output fails ingest. | |
| Open string list | Persist LLM labels as-is. | |

**User's choice:** Closed enum with fallback to `["employee"]`.

---

## Batch selection & rank assignment

| Option | Description | Selected |
|--------|-------------|----------|
| `current_date` (today) | Simple, matches ingest day. | |
| Monday of current week | Matches weekly digest cycle. | ✓ |
| `latest_batch.week_start + 7 days` | Preserves weekly cadence explicitly. | |

**User's choice:** Monday of current week.

---

### Follow-up: Rank assignment

| Option | Description | Selected |
|--------|-------------|----------|
| `max(rank) + 1` | Stable ordering, no collisions. | ✓ |
| `count(items) + 1` | Intuitive position, but duplicates possible with gaps. | |
| Fill lowest unused rank | Compact, but reorders and complex. | |

**User's choice:** `max(rank) + 1`.

---

### Follow-up: What counts toward batch capacity

| Option | Description | Selected |
|--------|-------------|----------|
| All items count | Rejected items still occupy a slot. | ✓ |
| Only pending and approved items count | Rejected items free a slot. | |

**User's choice:** All items count.

---

### Follow-up: Capacity configurability

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded to 5 | Matches PERS-02; minimal surface. | |
| Configurable via env var with default 5 | More flexible for UAT. | ✓ |

**User's choice:** Configurable `SHORTLIST_BATCH_SIZE` default 5.

---

## Claude's Discretion

- Exact slugification implementation.
- Exact word-count tokenization for `reading_minutes`.
- Exact `DraftPersistError` subtype/reason-code naming.
- RPC transport details inside the adapter.
- Internal file/module layout inside `ingestion-service`.

## Deferred Ideas

- HTTP API / scheduler for ingestion — v2.
- Transcription when captions missing — v2.
- Transcript chunking for context budget — v2.
- Public leaderboard, quiz cards, YAML pipeline UI, live SMTP, signup mail — post-v1.1.
- Refreshing draft content on re-run — rejected; delete-then-re-ingest instead.
