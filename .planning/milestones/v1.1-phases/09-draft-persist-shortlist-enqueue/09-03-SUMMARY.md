---
phase: 09-draft-persist-shortlist-enqueue
plan: 03
subsystem: database
tags: [supabase, postgres, migration, persist-rpc, draft, shortlist, youtube_video_id]

requires:
  - phase: 09-draft-persist-shortlist-enqueue
    provides: PersistPort, PersistResult, DraftPersistError, persist_draft, FakeDraftPersister
  - phase: 05-admin-digest
    provides: materials, digest_shortlist_batches, digest_shortlist_items, Phase 5 demo row

provides:
  - Migration 007 provenance columns on materials (source_url, youtube_video_id, source_author, source_published_at)
  - Unique constraint materials.youtube_video_id
  - Atomic persist_draft_and_enqueue RPC (draft-only insert + unsent-batch enqueue)
  - SupabaseDraftPersister implementing PersistPort via a single RPC
  - supabase>=2.0,<3 on ingestion-service

affects:
  - 09-04 (composition wiring, CAP-02 persist spy, overflow/batch_sent tests)
  - 10 (CLI persist path against the live RPC)

actuals:
  tokens: 5456
  tasks: 4
  commits: 7

tech-stack:
  added:
    - supabase>=2.0,<3
  patterns:
    - Single security-invoker RPC owns persist+enqueue; adapter is a thin typed caller
    - SDK/Postgres exceptions map to DraftPersistError subtypes with allowlisted context
    - Unique youtube_video_id plus ON CONFLICT DO NOTHING for idempotent re-runs

key-files:
  created:
    - supabase-integration/migrations/007_phase9_persist_draft.sql
    - ingestion-service/src/ingestion_service/adapters/supabase_persist.py
    - tests/unit/test_phase9_migration_007.py
    - tests/unit/test_supabase_draft_persister_contract.py
  modified:
    - ingestion-service/pyproject.toml
    - uv.lock

key-decisions:
  - "D-05/D-06/D-09 proceed: single persist+enqueue RPC, migration 007 is the canonical record, unique youtube_video_id."
  - "User pushed via Studio SQL (not supabase db push); persist_draft_and_enqueue is live on the shared VM."
  - "RPC execute is granted to service_role; postgres owner retains execute (expected)."
  - "Unique constraint on materials.youtube_video_id is live as materials_youtube_video_id_key."

patterns-established:
  - "Phase 9 writes go through one PL/pgSQL RPC; Python never splits insert and enqueue."
  - "Human migrate checkpoints record Studio apply + pg_proc/column/grant verification instead of CLI push."

requirements-completed:
  - PERS-01
  - PERS-02

coverage:
  - id: D1
    description: "Migration 007 SQL contract: provenance columns, unique youtube_video_id, persist_draft_and_enqueue, sent_at IS NULL batch predicate, idempotent conflict path, service_role grant, no destructive wipes."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_phase9_migration_007.py#test_migration_007_exists_and_adds_provenance_columns"
        status: pass
      - kind: unit
        ref: "tests/unit/test_phase9_migration_007.py#test_migration_007_creates_persist_draft_and_enqueue_rpc"
        status: pass
      - kind: unit
        ref: "tests/unit/test_phase9_migration_007.py#test_migration_007_skips_sent_batches_and_is_idempotent_on_video_id"
        status: pass
      - kind: unit
        ref: "tests/unit/test_phase9_migration_007.py#test_migration_007_grants_execute_only_to_service_role"
        status: pass
    human_judgment: false
  - id: D2
    description: "SupabaseDraftPersister maps a mocked RPC payload to PersistResult and maps SDK/Postgres failures to DraftPersistError subtypes without leaking secrets or raw error text."
    requirement: PERS-01
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_draft_persister_contract.py#test_persist_returns_result_from_mocked_rpc"
        status: pass
      - kind: unit
        ref: "tests/unit/test_supabase_draft_persister_contract.py#test_api_connection_error_maps_to_network_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_supabase_draft_persister_contract.py#test_unique_violation_23505_maps_to_conflict_error"
        status: pass
      - kind: unit
        ref: "tests/unit/test_supabase_draft_persister_contract.py#test_rpc_p0001_maps_to_batch_error"
        status: pass
    human_judgment: false
  - id: D3
    description: "Migration 007 applied on the shared VM: persist_draft_and_enqueue exists, four provenance columns present, unique index live, execute granted to service_role and not to anon/authenticated/public."
    requirement: PERS-02
    verification:
      - kind: manual_procedural
        ref: "Studio SQL apply of 007_phase9_persist_draft.sql; pg_proc persist_draft_and_enqueue count=1; information_schema columns count=4; index materials_youtube_video_id_key UNIQUE; execute grants postgres owner + service_role"
        status: pass
    human_judgment: true
    rationale: "Shared-VM schema apply is an operator action. The executor must not run supabase db push; human verified RPC, columns, unique index, and grants after Studio SQL."

duration: 12min
completed: 2026-09-27
status: complete
---

# Phase 9 Plan 03: Migration 007 + Supabase adapter Summary

**Atomic persist_draft_and_enqueue RPC with unique youtube_video_id, live on the shared VM after Studio apply, plus SupabaseDraftPersister mapping a single RPC to PersistResult**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-27T15:38:04Z
- **Completed:** 2026-09-27T15:50:00Z
- **Tasks:** 4
- **Files modified:** 6

## Accomplishments
- Accepted one-way schema decisions D-05, D-06, and D-09 before authoring migration 007
- Authored idempotent migration 007: provenance columns, unique `youtube_video_id`, and `persist_draft_and_enqueue` (`status='draft'`, unsent-batch only)
- Implemented `SupabaseDraftPersister` as the only ingestion-service adapter that calls Supabase, with safe `DraftPersistError` mapping
- Operator applied 007 via Studio SQL and confirmed the RPC, four columns, unique index, and execute grants on the shared VM

## Task Commits

Each task was committed atomically:

1. **Task 1: Schema gate proceed (D-05, D-06, D-09)** - `84ca0c7` (docs)
2. **Task 2 RED: SQL contract for migration 007** - `ecc97cc` (test)
3. **Task 2 GREEN: persist_draft_and_enqueue migration 007** - `7980b3e` (feat)
4. **Task 3 RED: SupabaseDraftPersister contract** - `929c2b9` (test)
5. **Task 3 GREEN: SupabaseDraftPersister + supabase dep** - `e173ea3` (feat)

**Plan metadata:** (this commit)

_Note: TDD tasks may have multiple commits (test → feat → refactor)_

## Files Created/Modified
- `supabase-integration/migrations/007_phase9_persist_draft.sql` - provenance columns, unique `youtube_video_id`, atomic persist+enqueue RPC
- `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` - `SupabaseDraftPersister` implementing `PersistPort`
- `tests/unit/test_phase9_migration_007.py` - offline SQL contract
- `tests/unit/test_supabase_draft_persister_contract.py` - mocked-client adapter contract
- `ingestion-service/pyproject.toml` / `uv.lock` - `supabase>=2.0,<3`

## Decisions Made
- D-05 / D-06 / D-09 proceed as one-way: single RPC, migration 007 is canonical, unique `youtube_video_id`.
- User pushed via Studio SQL after the migrate checkpoint; RPC is live (`pg_proc` count = 1).
- Unique index `materials_youtube_video_id_key` is live on the shared VM.
- postgres owner retains EXECUTE in addition to `service_role` (expected owner privilege); `anon` / `authenticated` / `public` have no execute.

## Deviations from Plan

### Designed halt before VM push

**1. Halt commit `ffa2b97` — executor must not run `supabase db push`**
- **Found during:** Task 4 (`checkpoint:migrate`)
- **Issue:** Shared-VM apply is a human gate. Running CLI push from the executor is forbidden.
- **Fix:** Plan halted with `docs(09-03): halt at migrate checkpoint before VM push` (`ffa2b97`). User applied Studio SQL and replied **pushed**.
- **Files modified:** `.planning/STATE.md` only (halt note)
- **Verification:** Human: `persist_draft_and_enqueue` = 1; materials columns = 4; unique index `materials_youtube_video_id_key`; execute = postgres owner + `service_role`. Success. No rows returned.
- **Committed in:** `ffa2b97` (halt, not a task GREEN)

### Expected grant residual

**2. postgres owner retains EXECUTE in addition to `service_role`**
- **Found during:** Task 4 human verification
- **Issue:** Plan wording says grant execute only to `service_role`. Function owner `postgres` also has EXECUTE.
- **Fix:** None. Owner execute is expected and does not grant `anon` / `authenticated` / `public`.
- **Verification:** Human grant check after Studio apply
- **Committed in:** n/a (schema state on the shared VM; no extra SQL)

---

**Total deviations:** 1 designed halt (`ffa2b97`) + 1 expected grant residual (postgres owner EXECUTE).
**Impact on plan:** No scope creep. RPC is live. Preferred CLI push was replaced by the documented Studio fallback.

## Issues Encountered
- `supabase db push` was not run. Operator applied `007_phase9_persist_draft.sql` via Studio SQL and confirmed success with no result rows.

## User Setup Required
None remaining. Migration 007 is already live on the shared VM (Studio SQL, user replied **pushed**). No USER-SETUP.md.

## Next Phase Readiness
Ready for 09-04 (Settings / Supabase client factories, overflow and `batch_sent` tests, CAP-02 persist spy). The live RPC and unique `youtube_video_id` are in place.

## Self-Check: PASSED
- key-files.created exist on disk
- Task commits `84ca0c7` … `e173ea3` are on the branch; halt `ffa2b97` recorded as a deviation
- Human migrate verification treated as done: RPC 1, columns 4, unique index present, grants as expected

---
*Phase: 09-draft-persist-shortlist-enqueue*
*Completed: 2026-09-27*
