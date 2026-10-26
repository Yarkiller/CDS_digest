---
status: complete
phase: 09-draft-persist-shortlist-enqueue
source:
  - 09-01-SUMMARY.md
  - 09-02-SUMMARY.md
  - 09-03-SUMMARY.md
  - 09-04-SUMMARY.md
started: 2026-09-27T18:20:00Z
updated: 2026-09-27T18:31:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server/service. Clear ephemeral state (temp DBs, caches, lock files). Start the application from scratch. Server boots without errors, any seed/migration completes, and a primary query (health check, homepage load, or basic API call) returns live data.
result: pass

### 2. Migration 007 applied on the shared VM
expected: persist_draft_and_enqueue exists (count=1), four provenance columns present, unique index live on youtube_video_id, execute granted to service_role and not to anon/authenticated/public. After the WR-05 re-apply: function prosrc contains FOR UPDATE, and unique index digest_shortlist_items_batch_id_rank_key is present.
result: pass
coverage_id: D3
requirement: PERS-02
reason: human_judgment

### 3. ArticleDraft.roles keeps valid values, filters unknown, and falls back to employee when missing or empty.
expected: |
  ArticleDraft.roles keeps valid values, filters unknown, and falls back to employee when missing or empty.
result: pass
source: automated
coverage_id: D1
requirement: PERS-01

### 4. MaterialDraft.roles uses the same normalization rules.
expected: |
  MaterialDraft.roles uses the same normalization rules.
result: pass
source: automated
coverage_id: D2
requirement: PERS-01

### 5. lecture.md and podcast.md ask the LLM for a JSON array of employee, analyst, ds.
expected: |
  lecture.md and podcast.md ask the LLM for a JSON array of employee, analyst, ds.
result: pass
source: automated
coverage_id: D3
requirement: PERS-01

### 6. DeepSeek adapter stub JSON with roles round-trips; empty roles become [employee].
expected: |
  DeepSeek adapter stub JSON with roles round-trips; empty roles become [employee].
result: pass
source: automated
coverage_id: D4
requirement: PERS-01

### 7. assemble_material_draft copies article.roles onto MaterialDraft.
expected: |
  assemble_material_draft copies article.roles onto MaterialDraft.
result: pass
source: automated
coverage_id: D5
requirement: PERS-01

### 8. RoleKind, ArticleDraft, and normalize_roles stay off the public package root.
expected: |
  RoleKind, ArticleDraft, and normalize_roles stay off the public package root.
result: pass
source: automated
coverage_id: D6
requirement: PERS-01

### 9. FakeArticleGenerator returns a scripted ArticleDraft including roles and records the call.
expected: |
  FakeArticleGenerator returns a scripted ArticleDraft including roles and records the call.
result: pass
source: automated
coverage_id: D7
requirement: PERS-01

### 10. PersistPort.persist returns PersistResult; FakeDraftPersister records calls, returns a scripted result, raises scripted failures, and stores one result per video_id.
expected: |
  PersistPort.persist returns PersistResult; FakeDraftPersister records calls, returns a scripted result, raises scripted failures, and stores one result per video_id.
result: pass
source: automated
coverage_id: D1
requirement: PERS-01

### 11. DraftPersistError subtypes map to locked persist reasons with allowlisted context and no secret or raw Postgres leakage.
expected: |
  DraftPersistError subtypes map to locked persist reasons with allowlisted context and no secret or raw Postgres leakage.
result: pass
source: automated
coverage_id: D2
requirement: PERS-01

### 12. persist_draft writes deterministic slug and reading_minutes, always calls the port, and two calls with the same video_id return one stored PersistResult.
expected: |
  persist_draft writes deterministic slug and reading_minutes, always calls the port, and two calls with the same video_id return one stored PersistResult.
result: pass
source: automated
coverage_id: D3
requirement: PERS-02

### 13. Migration 007 SQL contract: provenance columns, unique youtube_video_id, persist_draft_and_enqueue, sent_at IS NULL batch predicate, idempotent conflict path, service_role grant, no destructive wipes.
expected: |
  Migration 007 SQL contract: provenance columns, unique youtube_video_id, persist_draft_and_enqueue, sent_at IS NULL batch predicate, idempotent conflict path, service_role grant, no destructive wipes.
result: pass
source: automated
coverage_id: D1
requirement: PERS-01

### 14. SupabaseDraftPersister maps a mocked RPC payload to PersistResult and maps SDK/Postgres failures to DraftPersistError subtypes without leaking secrets or raw error text.
expected: |
  SupabaseDraftPersister maps a mocked RPC payload to PersistResult and maps SDK/Postgres failures to DraftPersistError subtypes without leaking secrets or raw error text.
result: pass
source: automated
coverage_id: D2
requirement: PERS-01

### 15. Settings loads optional Supabase credentials and validates SHORTLIST_BATCH_SIZE as a positive integer with default 5.
expected: |
  Settings loads optional Supabase credentials and validates SHORTLIST_BATCH_SIZE as a positive integer with default 5.
result: pass
source: automated
coverage_id: D1
requirement: PERS-01

### 16. Composition exports service-role and persister factories; .env.example documents placeholders with no live key.
expected: |
  Composition exports service-role and persister factories; .env.example documents placeholders with no live key.
result: pass
source: automated
coverage_id: D2
requirement: PERS-01

### 17. persist_draft is idempotent on youtube_video_id, overflows a full unsent batch, counts rejected items, and skips sent batches.
expected: |
  persist_draft is idempotent on youtube_video_id, overflows a full unsent batch, counts rejected items, and skips sent batches.
result: pass
source: automated
coverage_id: D3
requirement: PERS-02

### 18. A captions or article failure leaves FakeDraftPersister.calls empty (Phase 7 CAP-02 deferred proof).
expected: |
  A captions or article failure leaves FakeDraftPersister.calls empty (Phase 7 CAP-02 deferred proof).
result: pass
source: automated
coverage_id: D4
requirement: PERS-01

## Summary

total: 18
passed: 18
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
