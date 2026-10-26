---
phase: 09-draft-persist-shortlist-enqueue
verified: 2026-10-02T05:53:56Z
status: passed
score: 5/5 must-haves verified
covered_files:
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-01-PLAN.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-01-SUMMARY.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-02-PLAN.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-02-SUMMARY.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-03-PLAN.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-03-SUMMARY.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-04-PLAN.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-04-SUMMARY.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-CONTEXT.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-COVERAGE.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-DISCUSSION-LOG.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-PATTERNS.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-PLAN-CHECK.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-RESEARCH.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-REVIEW-DISPOSITION.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-REVIEW-FIX.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-REVIEW.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-UAT.md
  - .planning/phases/09-draft-persist-shortlist-enqueue/09-VALIDATION.md
  - data-collection/src/data_collection/__init__.py
  - data-collection/src/data_collection/adapters/deepseek_article.py
  - data-collection/src/data_collection/assemble.py
  - data-collection/src/data_collection/dto/article_draft.py
  - data-collection/src/data_collection/dto/material_draft.py
  - data-collection/src/data_collection/dto/role_kind.py
  - data-collection/src/data_collection/templates/lecture.md
  - data-collection/src/data_collection/templates/podcast.md
  - data-collection/src/data_collection/tests_support/fakes.py
  - ingestion-service/.env.example
  - ingestion-service/pyproject.toml
  - ingestion-service/src/ingestion_service/adapters/persist_errors.py
  - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
  - ingestion-service/src/ingestion_service/application/ports/persist.py
  - ingestion-service/src/ingestion_service/application/use_cases/ingest_until_persist.py
  - ingestion-service/src/ingestion_service/application/use_cases/persist_draft.py
  - ingestion-service/src/ingestion_service/composition/__init__.py
  - ingestion-service/src/ingestion_service/composition/clients.py
  - ingestion-service/src/ingestion_service/composition/settings.py
  - ingestion-service/src/ingestion_service/domain/material_completion.py
  - ingestion-service/src/ingestion_service/mapping/__init__.py
  - ingestion-service/src/ingestion_service/mapping/persist.py
  - ingestion-service/src/ingestion_service/tests_support/__init__.py
  - ingestion-service/src/ingestion_service/tests_support/fakes.py
  - supabase-integration/migrations/007_phase9_persist_draft.sql
  - tests/unit/test_article_draft_internal.py
  - tests/unit/test_article_draft_roles.py
  - tests/unit/test_assemble_material_draft.py
  - tests/unit/test_captions_failure_zero_persist.py
  - tests/unit/test_data_collection_public_api.py
  - tests/unit/test_deepseek_article_adapter.py
  - tests/unit/test_fake_article_generator.py
  - tests/unit/test_ingestion_clients.py
  - tests/unit/test_ingestion_settings.py
  - tests/unit/test_material_completion.py
  - tests/unit/test_material_draft_roles.py
  - tests/unit/test_persist_draft_use_case.py
  - tests/unit/test_persist_error_mapping.py
  - tests/unit/test_persist_idempotency_overflow.py
  - tests/unit/test_persist_port.py
  - tests/unit/test_phase9_migration_007.py
  - tests/unit/test_supabase_draft_persister_contract.py
covered_digest: "v2:sha256:22b032f0cc6625f38c3990b21c436631e590092ca825ddd2d919941034fad97f"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 20
  total: 20
  not_honored: []
  tool_substring:
    honored: 19
    total: 20
    missed: ["D-14a"]
    note: "gsd-tools check decision-coverage-verify is a substring heuristic. D-14a is honored in live SQL (coalesce p_roles, no CHECK) in 007 and in the Phase 10 replacement 008."
re_verification:
  previous_status: passed
  previous_score: 5/5
  previous_verified: 2026-09-27T18:36:11Z
  stale_reason: "Covered source changed after the last verifier run (#4682). Phase 10 edited covered files: PersistResult.already_saved (10-01), adapter already_saved parse (10-05), .env.example (10-02). Uncommitted data-collection tests_support/fakes.py adds await asyncio.sleep(0) on the three fakes. Phase 9 draft/enqueue behavior is unchanged."
  gaps_closed: []
  gaps_remaining: []
  regressions: []
deferred:
  - truth: "PersistResult is a frozen dataclass with exactly the fields material_id, slug, batch_id, and rank"
    addressed_in: "Phase 10"
    evidence: "Phase 10 plan 10-01 adds PersistResult.already_saved (CLI-01, CLI-04). The four Phase 9 fields remain; already_saved defaults to False."
  - truth: "Live CLI persist of real captioned videos appears as drafts in /admin/digest"
    addressed_in: "Phase 10"
    evidence: "Phase 10 success criteria: UAT 3–5 real captioned videos; CLI-01/CLI-02/CLI-03"
  - truth: "Typer one-shot prints material_id, slug, batch_id, and rank"
    addressed_in: "Phase 10"
    evidence: "Phase 10 goal / CLI-01"
  - truth: "Idempotent CLI re-run does not create duplicate materials/shortlist rows (operator UX)"
    addressed_in: "Phase 10"
    evidence: "CLI-02 (RPC ON CONFLICT semantics already locked here; 008 returns stored slug and already_saved)"
human_verification: []
next_action: "Verification passed — continue."
next_command: ""
---

# Phase 9: Draft Persist & Shortlist Enqueue Verification Report

**Phase Goal:** A successful draft write lands as `status=draft` with required provenance and appears on an unsent shortlist batch (creating a new batch when the current one is full)
**Verified:** 2026-10-02T05:53:56Z
**Status:** passed
**Re-verification:** Yes — stale fingerprint refresh (#4682). Prior report `passed` 5/5 at 2026-09-27T18:36:11Z had no `gaps:` to close. Covered source changed afterward; this pass re-checked the goal against the current tree. ROADMAP/STATE were not edited.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ------- | ---------- | -------------- |
| 1 | Successful persist inserts `materials` with `status=draft` only (never `ready`) and required provenance fields `source_url`, `youtube_video_id`, `source_author`, `source_published_at`, `provenance_label` (PERS-01 / ROADMAP SC1) | ✓ VERIFIED | `007` INSERT hard-codes `'draft'` / `'статья'` and writes the five provenance columns. Phase 10 `008` `CREATE OR REPLACE` keeps the same INSERT. Adapter `_rpc_params` forwards `p_source_*` / `p_provenance_label` and omits `status`/`ready`. `test_persist_never_forwards_status_or_ready_to_rpc` passed in this run |
| 2 | The run enqueues `digest_shortlist_items` on the current unsent batch with `decision=pending` (PERS-02 / ROADMAP SC2) | ✓ VERIFIED | Both `007` and `008` insert `decision='pending'` and `rank = max(rank)+1` on the latest `sent_at IS NULL` batch (`FOR UPDATE`). `test_persist_idempotency_overflow.py` passed |
| 3 | When the current unsent batch already has 5 items, the run creates a new unsent batch and enqueues there (ROADMAP SC3) | ✓ VERIFIED | RPC: `v_item_count >= p_batch_size` inserts a new `digest_shortlist_batches` row. Settings default `shortlist_batch_size=5`. Named test `test_overflow_creates_new_unsent_batch_at_capacity` passed |
| 4 | Persist/enqueue never attaches to a batch with `sent_at` set (ROADMAP SC4) | ✓ VERIFIED | New-write select is `where b.sent_at is null` + `FOR UPDATE` in `007` and `008`. Conflict path requires `b.sent_at is null` and raises `P0001` if none. `test_migration_007_conflict_path_does_not_fall_back_to_sent_batch` and `test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` passed |
| 5 | CAP-02 deferred proof: captions (or article) failure leaves `persist.calls == []` (Phase 7 D-14 / 09-04) | ✓ VERIFIED | `run_ingest_until_persist` is captions → article → assemble → `persist_draft`. Named tests `test_captions_failure_leaves_persist_calls_empty` and `test_article_failure_leaves_persist_calls_empty` passed |

**Score:** 5/5 roadmap + CAP-02 must-haves verified (0 present, behavior-unverified)

### Supporting PLAN Truths

| Area | Truth | Status | Evidence |
| ---- | ----- | ------ | -------- |
| 09-01 roles | `ArticleDraft` / `MaterialDraft` `roles: list[RoleKind]`; unknown filtered; empty/`{}` → `["employee"]`; assembler copies `article.roles` | ✓ VERIFIED | `role_kind.normalize_roles`; `assemble.py` `roles=article.roles`; role tests in the 76-test run |
| 09-01 templates | `lecture.md` and `podcast.md` name `employee`, `analyst`, `ds` and ask for a JSON array | ✓ VERIFIED | `## Аудитория` line in both templates |
| 09-01 adapter | DeepSeek `process()` validates then `normalize_roles` | ✓ VERIFIED | `deepseek_article.py` assigns `draft.roles = normalize_roles(...)` |
| 09-01 public API | `data_collection.__all__` is exactly the seven existing names; `RoleKind` / `ArticleDraft` off root | ✓ VERIFIED | `__init__.py` lists those seven names only |
| 09-02 port | `PersistPort.persist(MaterialDraft) -> PersistResult` | ✓ VERIFIED | `application/ports/persist.py`. The four Phase 9 fields remain. `already_saved: bool = False` was added by Phase 10 (see Deferred) |
| 09-02 completion | `generate_slug` = `{slugify(title)[:50]}-{video_id}`; `reading_minutes = max(1, ceil(words/200))`; `persist_draft` overwrites both and always calls the port | ✓ VERIFIED | `material_completion.py`; `persist_draft.py` has no video_id pre-check |
| 09-02 fake | `FakeDraftPersister` records `calls` and stores one result per `youtube_video_id` | ✓ VERIFIED | `ingestion_service/tests_support/fakes.py` |
| 09-02 mapper | `PERSIST_REASONS` exact five; `stage=persist`, `exit_code=1`; context allowlist | ✓ VERIFIED | `mapping/persist.py` |
| 09-03 migration | 007 is idempotent; provenance columns; unique `youtube_video_id`; atomic RPC; `security invoker`; revoke public/anon/authenticated; grant `service_role`; unique `(batch_id, rank)` | ✓ VERIFIED | Migration file + `test_phase9_migration_007.py` passed |
| 09-03 adapter | `SupabaseDraftPersister` is the only non-composition `supabase` import; single `client.rpc(...).execute()` | ✓ VERIFIED | `supabase_persist.py`. Result keys now include `already_saved`, supplied by migration `008` (Phase 10). `007` still returns the four Phase 9 keys; `008` replaces the function |
| 09-04 settings | `shortlist_batch_size` defaults to 5; secret fields omitted from `repr` | ✓ VERIFIED | `settings.py` `repr=False` on `supabase_secret_key` and `deepseek_api_key`; settings tests passed |
| 09-04 factories | Blank url/key raises before `create_client`; factories exported; `.env.example` has empty `SUPABASE_URL` / `SUPABASE_SECRET_KEY` and `SHORTLIST_BATCH_SIZE=5` | ✓ VERIFIED | `composition/__init__.py` exports both factories. `.env.example` has no `s3cr3t` and no JWT-looking value |
| 09-04 idempotency | Re-run does not insert a second material or shortlist row (`ON CONFLICT DO NOTHING`) | ✓ VERIFIED | Conflict branch in `007` and `008` returns the existing unsent row. Overflow suite passed |

### Deferred Items

Items outside this phase's goal, or a Phase 9 wording that Phase 10 intentionally extended. Not actionable gaps.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | `PersistResult` "exactly four fields" | Phase 10 | 10-01 adds `already_saved` (default `False`). Four Phase 9 fields remain |
| 2 | Live CLI persist of real videos | Phase 10 | ROADMAP Phase 10 SC / CLI-01…CLI-03 |
| 3 | Typer prints `material_id`, `slug`, `batch_id`, `rank` | Phase 10 | CLI-01 |
| 4 | Idempotent CLI re-run operator UX | Phase 10 | CLI-02; `008` returns stored slug + `already_saved` |

### Advisory (New Scope, Unevidenced)

None. Prior advisory WR-01 (conflict path returned caller `p_slug`) is closed by migration `008`, which returns `materials.slug` and `already_saved`. WR-02, WR-04, and WR-05 stay closed in `007`/`008` and in the tests that passed this run.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | ----------- | ------- | ------- |
| `data-collection/.../dto/role_kind.py` | `RoleKind` + `VALID_ROLES` + `normalize_roles` | ✓ VERIFIED | Closed set `{employee, analyst, ds}` |
| `data-collection/.../dto/article_draft.py` | `roles` + before-validator | ✓ VERIFIED | Default `["employee"]` |
| `data-collection/.../dto/material_draft.py` | `roles` + slug/reading defaults + provenance | ✓ VERIFIED | Assembler still constructs without slug |
| `data-collection/.../assemble.py` | copies `article.roles` | ✓ VERIFIED | Direct field copy |
| `data-collection/.../templates/lecture.md` | audience-role instruction | ✓ VERIFIED | JSON array of three roles |
| `data-collection/.../templates/podcast.md` | audience-role instruction | ✓ VERIFIED | Same section |
| `data-collection/.../adapters/deepseek_article.py` | post-validate role normalize | ✓ VERIFIED | `normalize_roles` after validate |
| `ingestion-service/.../application/ports/persist.py` | `PersistPort` + `PersistResult` | ✓ VERIFIED | Four Phase 9 fields plus Phase 10 `already_saved` |
| `ingestion-service/.../application/use_cases/persist_draft.py` | enrich + `port.persist` | ✓ VERIFIED | No supabase / no pre-check |
| `ingestion-service/.../application/use_cases/ingest_until_persist.py` | CAP-02 composer | ✓ VERIFIED | Captions → article → assemble → persist_draft |
| `ingestion-service/.../domain/material_completion.py` | slug + reading minutes | ✓ VERIFIED | `python-slugify` |
| `ingestion-service/.../adapters/persist_errors.py` | `DraftPersistError` subtypes | ✓ VERIFIED | Five concrete types used by the mapper |
| `ingestion-service/.../mapping/persist.py` | `map_persist_error` + `PERSIST_REASONS` | ✓ VERIFIED | Allowlisted context |
| `ingestion-service/.../tests_support/fakes.py` | `FakeDraftPersister` + `BatchTrackingFakePersister` | ✓ VERIFIED | Overflow + sent-batch skip |
| `supabase-integration/migrations/007_phase9_persist_draft.sql` | columns + unique + RPC + lock/rank | ✓ VERIFIED | Exists and substantive. Effective function body after apply is `008`, which preserves these clauses |
| `ingestion-service/.../adapters/supabase_persist.py` | `SupabaseDraftPersister` | ✓ VERIFIED | Single named RPC; requires `already_saved` in the payload |
| `ingestion-service/.../composition/settings.py` | supabase + batch size + secret-safe repr | ✓ VERIFIED | Positive-int validation; `repr=False` |
| `ingestion-service/.../composition/clients.py` | service client + persister factories | ✓ VERIFIED | Blank credentials fail closed |
| `ingestion-service/.env.example` | empty URL/key + batch size 5 | ✓ VERIFIED | No `s3cr3t` / JWT-looking value |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | ---- | ------ | -------- |
| `ArticleDraft.roles` | `MaterialDraft.roles` | `assemble_material_draft` | ✓ WIRED | Direct copy; no extra role logic |
| LLM JSON `roles` | `ArticleDraft.roles` | `model_validate` then `normalize_roles` | ✓ WIRED | Unknown filtered; empty → `employee` |
| `persist_draft` | `PersistPort` | `port.persist(enriched)` | ✓ WIRED | Use-case imports domain + port only |
| `DraftPersistError` | `IngestError(stage=persist)` | `map_persist_error` | ✓ WIRED | Locked five reasons |
| `SupabaseDraftPersister` | `public.persist_draft_and_enqueue` | `client.rpc(name, params).execute()` | ✓ WIRED | Single call. Parser requires `already_saved`, which `008` returns |
| Postgres/SDK exception | `IngestError(stage=persist)` | subtype then mapper | ✓ WIRED | Contract tests passed |
| `Settings.from_env` | `SupabaseDraftPersister` | `build_supabase_service_client` → `build_supabase_draft_persister` | ✓ WIRED | Composition owns wiring |
| `CaptionsError` | `PersistPort` | `run_ingest_until_persist` | ✓ WIRED | Composer stops before `persist_draft` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `assemble_material_draft` | provenance fields | `ArticleDraft` + `VideoMetadata` + label | Yes | ✓ FLOWING |
| `persist_draft` | `slug` / `reading_minutes` | `generate_slug` / `estimate_reading_minutes` | Yes | ✓ FLOWING |
| `run_ingest_until_persist` | persist argument | captions → article → assemble | Yes (short-circuits on captions/article error) | ✓ FLOWING |
| `SupabaseDraftPersister` | RPC params | `MaterialDraft` fields + `batch_size` | Yes (typed `p_*` dict) | ✓ FLOWING |
| `persist_draft_and_enqueue` | `materials.status` | SQL literal `'draft'` | Yes (hard-coded in `007` and `008`) | ✓ FLOWING |
| `persist_draft_and_enqueue` | shortlist `decision` / `rank` | SQL `'pending'` + `max(rank)+1` under `FOR UPDATE` | Yes | ✓ FLOWING |
| Conflict return | `slug` / `already_saved` | `008` reads stored `materials.slug` | Yes (Phase 10). `007` still returns caller `p_slug` and is replaced on apply | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase 9 behavioral files (8) | `uv run pytest` on role, settings, persist use-case, migration 007, adapter contract, idempotency/overflow, captions-failure | **76 passed** in 2.25s | ✓ PASS |
| Named overflow | `test_overflow_creates_new_unsent_batch_at_capacity` | included in the 76 | ✓ PASS |
| Named sent-batch skip | `test_batch_sent_skips_latest_sent_batch` | included in the 76 | ✓ PASS |
| Named conflict-without-unsent | `test_rerun_when_only_sent_batch_exists_raises_batch_creation_failed` | included in the 76 | ✓ PASS |
| Named CAP-02 composer | `test_captions_failure_leaves_persist_calls_empty` | included in the 76 | ✓ PASS |
| Named no-status forward | `test_persist_never_forwards_status_or_ready_to_rpc` | included in the 76 | ✓ PASS |
| Workspace regression (orchestrator) | full unit suite | **196 passed**, including `test_admin_shortlist_empty_batch_returns_200_empty_items` | ✓ PASS (reported; not re-run here) |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No `scripts/*/tests/probe-*.sh` and no PLAN-declared probes | ? SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| PERS-01 | 09-01, 09-02, 09-03, 09-04 | Successful run inserts `materials` with `status=draft` only and provenance fields | ✓ SATISFIED | RPC hard-codes draft in `007` and `008`; DTO + adapter; no-status-forward test passed |
| PERS-02 | 09-01, 09-02, 09-03, 09-04 | Enqueue on current unsent batch (`decision=pending`); overflow creates a new unsent batch | ✓ SATISFIED | RPC + overflow/sent/conflict tests passed |

**Orphaned requirements:** None. REQUIREMENTS.md maps only PERS-01 and PERS-02 to Phase 9. Both IDs appear in every plan's `requirements:` field (09-01 through 09-04). CLI-01…CLI-05 map to Phase 10. CAP-02 maps to Phase 7 and is satisfied here by the composer spy.

### Decision Coverage (09-CONTEXT.md)

`gsd-tools check decision-coverage-verify`: tool substring **19/20** (missed D-14a). Independent code check: **20/20 honored.** Gate is non-blocking.

| Decision | Status | Evidence |
| -------- | ------ | -------- |
| D-01 Port + adapter live in `ingestion-service` | ✓ Honored | Persist port and adapter are inside ingestion-service |
| D-02 Own `supabase` package + composition client | ✓ Honored | Factories in `composition/clients.py` |
| D-03 `PersistResult` four fields | ✓ Honored | Four fields present; Phase 10 added `already_saved` |
| D-04 Local `DraftPersistError` → `stage=persist` | ✓ Honored | Mapper + locked reasons |
| D-05 Single persist+enqueue RPC | ✓ Honored | `persist_draft_and_enqueue` |
| D-06 Migration 007 is canonical | ✓ Honored | Tracked SQL file; `008` amends the function without editing 007 in place |
| D-07 Slug/minutes in Python | ✓ Honored | `persist_draft` enriches before the port |
| D-08 Latest unsent batch; full → new | ✓ Honored | `week_start desc, created_at desc` + overflow in `007` and `008` |
| D-09 Unique `youtube_video_id` | ✓ Honored | `materials_youtube_video_id_key` |
| D-10 Re-run no-op (no refresh, no second shortlist row) | ✓ Honored | `ON CONFLICT DO NOTHING` + existing-item lookup |
| D-11 No Python video_id pre-check | ✓ Honored | `persist_draft.py` always calls the port |
| D-12 Slug `{slugify(title)[:50]}-{video_id}` | ✓ Honored | `generate_slug` |
| D-13 `reading_minutes` ceil(words/200) min 1 | ✓ Honored | `estimate_reading_minutes` |
| D-14 `roles` on ArticleDraft/MaterialDraft | ✓ Honored | RoleKind + templates + adapter |
| D-14a RoleKind closed only in Python; RPC has no CHECK | ✓ Honored | `coalesce(p_roles, '{}')` and the no-CHECK comment in `007` and `008`. Tool substring miss |
| D-15 `format='статья'`, `status='draft'`, `source_id=null` | ✓ Honored | RPC INSERT literals |
| D-16 New batch `week_start = date_trunc('week', current_date)` | ✓ Honored | RPC insert |
| D-17 Rank = `max(rank)+1` | ✓ Honored | RPC + fake tests |
| D-18 Rejected items count toward capacity | ✓ Honored | `test_rejected_item_counts_toward_batch_capacity` passed |
| D-19 `SHORTLIST_BATCH_SIZE` default 5 | ✓ Honored | Settings + env example |

### Prohibitions

PLAN `verification` is `null` on every prohibition. Each one has a wired test that passed this run, so they are held.

| Prohibition | Tier | Status | Evidence |
| ----------- | ---- | ------ | -------- |
| MUST NOT export `RoleKind` / `ArticleDraft` from package root | test | ✓ Held | `__all__` is the seven public names |
| MUST NOT allow invalid/empty roles to reach persist without `["employee"]` fallback | test | ✓ Held | Validators + role tests |
| MUST NOT persist `status=ready` or any status other than `draft` | test | ✓ Held | RPC literal `'draft'`; adapter never forwards `status` |
| MUST NOT enqueue on a batch with `sent_at` set | test | ✓ Held | `sent_at IS NULL` on new-write and conflict path |
| MUST NOT expose `SUPABASE_SECRET_KEY`, raw Postgres, or stack traces in `IngestError` context | test | ✓ Held | Mapper allowlist; Settings `repr=False` |
| MUST NOT refresh/overwrite existing material content on re-run | test | ✓ Held | `ON CONFLICT DO NOTHING` |

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `test_article_draft_roles.py` / `test_material_draft_roles.py` | PERS-01 | yes | 0 | no | value | PASS |
| `test_phase9_migration_007.py` | PERS-01 / PERS-02 | yes | 0 | no | value (DDL + lock/rank + no sent fallback) | PASS |
| `test_supabase_draft_persister_contract.py` | PERS-01 | yes | 0 | no | value (provenance + no status + already_saved) | PASS |
| `test_persist_idempotency_overflow.py` | PERS-02 | yes | 0 | no | behavioral | PASS |
| `test_captions_failure_zero_persist.py` | CAP-02 | yes | 0 | no | behavioral (composer) | PASS |
| `test_ingestion_settings.py` | PERS-01 | yes | 0 | no | value | PASS |

**Disabled tests on requirements:** 0
**Circular patterns detected:** 0
**Insufficient assertions:** 0

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | — | — | No `TBD` / `FIXME` / `XXX` in phase production files scanned |

`data-collection/.../tests_support/fakes.py` has an uncommitted `await asyncio.sleep(0)` on the three fakes. That yields once; it still returns the scripted result and still records the call. It does not change role propagation or the persist contract.

### Human Verification Required

N/A — Infrastructure/foundation phase with no user-facing elements.
All acceptance criteria are verifiable programmatically. Live CLI persist of real videos is Phase 10.

Human UAT for this phase is already complete: **18/18 passed** (`09-UAT.md`, `status: complete`).

### Gaps Summary

No gaps found against the phase goal, PERS-01, PERS-02, or the four ROADMAP success criteria.

Stale-refresh deltas vs 2026-09-27T18:36:11Z:

- `covered_digest` regenerated: `v2:sha256:22b032f0cc6625f38c3990b21c436631e590092ca825ddd2d919941034fad97f` (was `v2:sha256:c2a7e5b3ece988764182baefc77e8353d64a64dbab06d63c5a18d6ae717afdb2`).
- Phase 10 added `PersistResult.already_saved` and taught the adapter to require it. Migration `008` returns it and returns the stored slug on conflict. Draft insert, provenance, unsent enqueue, overflow, and sent-batch skip are unchanged in both SQL bodies.
- This run: 76 phase-9 behavioral tests passed. Orchestrator regression: 196 unit tests passed.
- Prior advisory WR-01 is closed by `008`.

---

## Verification Metadata

**Verification approach:** Goal-backward (ROADMAP SCs + PLAN must-haves from 09-01…09-04 + CAP-02). SUMMARY.md claims were not treated as evidence.
**Must-haves source:** `.planning/ROADMAP.md` Phase 9 Success Criteria + four PLAN frontmatters
**Automated checks:** 76 phase-9 behavioral tests passed this run; decision-coverage-verify 19/20 substring, 20/20 in code
**Human checks required:** 0 (infrastructure phase; UAT already 18/18)
**ROADMAP/STATE:** not modified

---
_Verified: 2026-10-02T05:53:56Z_
_Verifier: Claude (gsd-verifier)_
