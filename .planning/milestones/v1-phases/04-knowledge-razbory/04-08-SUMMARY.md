---
phase: 04-knowledge-razbory
plan: 08
subsystem: database
tags: [supabase, knowledge-chunks, razbor, hybrid-search, live-wiring, seed-migration, KNOW-01, KNOW-02, RAZB-01, RAZB-03]

requires:
  - phase: 04-knowledge-razbory
    provides: Knowledge/razbor ports + HTTP role allowlist (04-01/03/04) and notebook NOTEBOOK_ROOT (04-07)
provides:
  - Idempotent migration 004 seeding knowledge_chunks (1024-d) + razbors + hybrid RPC
  - SupabaseKnowledgeChunkRepository + SupabaseRazborRepository live adapters
  - build_live_container wires SQL adapters + StubQueryEmbedder (no InMemory chunks)
  - Runbook §4d Applied confirmed on shared VM
affects:
  - 04-09 Playwright live knowledge/razbor proofs
  - Live APP_CONTAINER=live hybrid search and razbor reads

actuals:
  tokens: 20136
  tasks: 3
  commits: 4

tech-stack:
  added: []
  patterns:
    - "Idempotent Phase 4 seed via ON CONFLICT / WHERE NOT EXISTS; no TRUNCATE"
    - "Hybrid search via SECURITY INVOKER RPC search_knowledge_chunks; service_role only"
    - "Live composition: SupabaseKnowledgeChunkRepository + SupabaseRazborRepository + StubQueryEmbedder"

key-files:
  created:
    - supabase-integration/migrations/004_phase4_knowledge_razbory.sql
    - supabase-integration/src/supabase_integration/knowledge_chunk_repository.py
    - supabase-integration/src/supabase_integration/razbor_repository.py
  modified:
    - supabase-integration/src/supabase_integration/__init__.py
    - backend/src/backend/composition/live.py
    - backend/src/backend/composition/container.py
    - backend/src/backend/composition/settings.py
    - docs/agents/local-platform-runbook.md
    - tests/unit/test_live_container_wiring.py
    - tests/unit/test_supabase_knowledge_chunk_repository_contract.py
    - tests/unit/test_supabase_razbor_repository_contract.py

key-decisions:
  - "Hybrid fusion via SECURITY INVOKER RPC search_knowledge_chunks — not list_all + Python cosine on live"
  - "StubQueryEmbedder algorithm aligned with seeded 1024-d vectors for demo semantic hits (A3 / Foundry opt-out)"
  - "Blocking human apply: operator confirmed SQL + notebook + NOTEBOOK_ROOT before close-out"

patterns-established:
  - "Pattern: Phase N seed migration + runbook § Applied line after blocking human checkpoint"
  - "Pattern: Supabase adapters implement ports; PersistenceError at SDK boundary; wiring only in composition/live.py"

requirements-completed: [KNOW-01, KNOW-02, RAZB-01, RAZB-03]

coverage:
  - id: D1
    description: Idempotent migration 004 seeds knowledge_chunks (1024-d embeddings) and razbors without TRUNCATE
    requirement: KNOW-01
    verification:
      - kind: other
        ref: node -e "004 SQL mentions knowledge_chunks/razbors and has no TRUNCATE"
        status: pass
    human_judgment: false
  - id: D2
    description: Live hybrid search uses SQL/RPC adapters — not InMemory list_all cosine
    requirement: KNOW-02
    verification:
      - kind: unit
        ref: tests/unit/test_live_container_wiring.py
        status: pass
      - kind: unit
        ref: tests/unit/test_supabase_knowledge_chunk_repository_contract.py
        status: pass
    human_judgment: false
  - id: D3
    description: SupabaseRazborRepository list/get wired in build_live_container (RAZB-01)
    requirement: RAZB-01
    verification:
      - kind: unit
        ref: tests/unit/test_supabase_razbor_repository_contract.py
        status: pass
    human_judgment: false
  - id: D4
    description: [BLOCKING] Migration 004 + notebook under NOTEBOOK_ROOT applied on shared VM / API host
    requirement: RAZB-03
    verification:
      - kind: manual_procedural
        ref: docs/agents/local-platform-runbook.md#4d — Applied 2026-09-21 operator confirmed
        status: pass
    human_judgment: true
    rationale: Shared-VM schema push and host filesystem NOTEBOOK_ROOT cannot be proven by unit tests alone

duration: continuation-closeout
completed: 2026-09-21
status: complete
---

# Phase 04 Plan 08: Live Knowledge/Razbor Adapters + Seed Summary

**Idempotent migration 004 seeds 1024-d knowledge chunks and razbors with hybrid RPC; live composition wires Supabase adapters + StubQueryEmbedder; operator confirmed apply on knowledge-db.ru with NOTEBOOK_ROOT ready.**

## Performance

- **Duration:** continuation close-out after blocking human checkpoint (tasks 1–2 prior wave)
- **Started:** prior wave (seed + adapters)
- **Completed:** 2026-09-21T09:13:00Z
- **Tasks:** 3
- **Files modified:** 9 (+ SUMMARY/runbook Applied close-out)

## Accomplishments

- Checked-in `004_phase4_knowledge_razbory.sql`: hybrid `search_knowledge_chunks` RPC (SECURITY INVOKER), seeded chunks spanning ds/analyst ready materials, published multi-section razbor with notebook_path, announcement stub, overview without metrics — all idempotent, no TRUNCATE.
- `SupabaseKnowledgeChunkRepository` / `SupabaseRazborRepository` implement ports; `build_live_container` replaces InMemory chunks with SQL adapters + StubQueryEmbedder; service_role stays in composition only.
- Blocking human gate cleared: operator confirmed SQL applied, notebook present under NOTEBOOK_ROOT, `.env` NOTEBOOK_ROOT set; runbook §4d **Applied** recorded.

## Task Commits

Each task was committed atomically:

1. **Task 1: Idempotent Phase 4 seed SQL + runbook** - `d7b7593` (feat)
2. **Task 2 (RED): failing live adapter/wiring tests** - `b4f870d` (test)
3. **Task 2 (GREEN): wire Supabase knowledge and razbor live adapters** - `f78d144` (feat)
4. **Task 3: record human apply + SUMMARY** - `31f4f1e` (docs)

**Plan metadata:** `31f4f1e` (docs: complete plan) — STATE/ROADMAP follow in final docs commit if needed

## Files Created/Modified

- `supabase-integration/migrations/004_phase4_knowledge_razbory.sql` — seed + hybrid RPC
- `supabase-integration/src/supabase_integration/knowledge_chunk_repository.py` — SQL hybrid search adapter
- `supabase-integration/src/supabase_integration/razbor_repository.py` — list/get adapter
- `supabase-integration/src/supabase_integration/__init__.py` — exports
- `backend/src/backend/composition/live.py` — live wiring (no InMemory chunks)
- `docs/agents/local-platform-runbook.md` — §4d apply-once + Applied line
- Contract/wiring unit tests under `tests/unit/`

## Decisions Made

- Hybrid fusion via SECURITY INVOKER RPC called only through service_role adapter — not Python `list_all` cosine on live.
- StubQueryEmbedder kept (Foundry opt-out) and aligned with seeded vectors for demo hits.
- Exact SQL row counts omitted from Applied note when resume signal did not inventory them; operator confirmed verify queries.

## Deviations from Plan

None - plan executed exactly as written (blocking human apply cleared by operator confirmation).

## Issues Encountered

- Task 3 was a `checkpoint:human-action` (blocking-human). Operator applied migration offline; executor resumed to record Applied + SUMMARY only. Unrelated WIP left unstaged on dirty tree.

## User Setup Required

**Shared VM / local API already configured by operator for this plan.** See [local-platform-runbook.md §4d](../../../docs/agents/local-platform-runbook.md):

- `NOTEBOOK_ROOT` pointing at host dir with `hybrid-retrieval.ipynb`
- Existing `SUPABASE_URL` / `SUPABASE_SECRET_KEY` (server only; never `VITE_`)
- Migration 004 applied once on knowledge-db.ru

## Next Phase Readiness

- Live knowledge search and razbor reads can hit Supabase under `APP_CONTAINER=live`.
- Ready for 04-09 Playwright / live verification plans that depend on seeded chunks and notebook download.

## Auth Gates

- Task 3 blocking-human: operator applied schema/seed + notebook + NOTEBOOK_ROOT; resumed with `done (applied)`.

## Self-Check: PASSED

- FOUND: `supabase-integration/migrations/004_phase4_knowledge_razbory.sql`
- FOUND: `supabase-integration/src/supabase_integration/knowledge_chunk_repository.py`
- FOUND: `supabase-integration/src/supabase_integration/razbor_repository.py`
- FOUND: commits `d7b7593`, `b4f870d`, `f78d144`
- FOUND: runbook **Applied:** 2026-09-21 operator confirmed
- FOUND: this SUMMARY at `.planning/phases/04-knowledge-razbory/04-08-SUMMARY.md`

---
*Phase: 04-knowledge-razbory*
*Completed: 2026-09-21*
