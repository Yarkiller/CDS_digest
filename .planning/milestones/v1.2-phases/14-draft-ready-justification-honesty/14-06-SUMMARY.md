---
phase: 14-draft-ready-justification-honesty
plan: 06
subsystem: database
tags: [supabase, postgrest, postgresql, embed, fk-hint, gap-closure, adux-05, pgrst201]

# Dependency graph
requires:
  - phase: 14-draft-ready-justification-honesty
    provides: "14-01/14-02 promote routes (POST /admin/materials/{id}/ready, /admin/materials/ready) that call repo.get()"
provides:
  - "Disambiguated material_relations!material_relations_from_material_id_fkey(to_material_id) embed in SupabaseMaterialRepository._fetch_one"
  - "Offline PGRST201-rejecting regression locking get()/get_by_slug() + the embed shape"
  - "Live material reader + admin promote read path healed (503 -> 200; PGRST201 eliminated)"
affects: [14-draft-ready-justification-honesty, admin-shortlist, public-material-reader]

actuals:
  tokens: 1552
  tasks: 1
  commits: 1
plan_head_before: 842dff2f6f5489ba35b2fe060a78aad110c286d3
plan_head_after: 02e16bced19abccccf7c075cf5d9bffe8549064b

tech-stack:
  added: []
  patterns:
    - "PostgREST embeds that traverse a table with >1 FK into the parent MUST carry an FK hint (!<fk-constraint-or-column>); a single-FK embed stays unhinted"
    - "Offline fake client that raises the PGRST201-shaped error for a bare embed — regression-locks the real PostgREST embed without a network hop"

key-files:
  created:
    - tests/unit/test_supabase_material_repository_embed.py
  modified:
    - supabase-integration/src/supabase_integration/material_repository.py

key-decisions:
  - "Hint by FK constraint name material_relations!material_relations_from_material_id_fkey(to_material_id) — the Postgres default name for the from_material_id FK, keeping outgoing-relations semantics"
  - "Leave material_tags(tag_slug,tag_label) unhinted — it has a single FK into materials so it is unambiguous"
  - "Fix stays inside the adapter boundary (_fetch_one select literal only); no domain/use-case/route edits"

patterns-established:
  - "Simulated PGRST201 rejection in an offline fake: select() records the spec and raises when a bare material_relations( embed is requested"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: "Live SupabaseMaterialRepository.get()/get_by_slug() return a Material (no PGRST201/PersistenceError); admin promote path is unblocked (G-14-1 / G-14-4)"
    requirement: "ADUX-05"
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_material_repository_embed.py#test_get_returns_material_under_ambiguous_embed_rejection"
        status: pass
      - kind: unit
        ref: "tests/unit/test_supabase_material_repository_embed.py#test_get_by_slug_returns_material_under_ambiguous_embed_rejection"
        status: pass
      - kind: integration
        ref: "live read probe: repo.get(2) -> ready rag-systems; get_by_slug('rag-systems') -> Material"
        status: pass
    human_judgment: false
  - id: D2
    description: "The material_relations embed is FK-disambiguated; material_tags stays unhinted (regression-locked)"
    requirement: "ADUX-05"
    verification:
      - kind: unit
        ref: "tests/unit/test_supabase_material_repository_embed.py#test_fetch_one_disambiguates_relations_embed_and_keeps_tags_unhinted"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 06: Disambiguate the material_relations embed (G-14-1 / G-14-4) Summary

**The admin promote 503 is fixed at its shared root cause — `_fetch_one` now emits the FK-hinted `material_relations!material_relations_from_material_id_fkey(to_material_id)` embed, so live `get()`/`get_by_slug()` return a Material instead of raising PGRST201 → PersistenceError, with an offline PGRST201-rejecting fake locking the shape.**

## Performance

- **Duration:** 6min
- **Started:** 2026-10-03T18:10:00Z
- **Completed:** 2026-10-03T18:16:00Z
- **Tasks:** 1
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments
- Replaced the bare `material_relations(to_material_id)` embed in `SupabaseMaterialRepository._fetch_one` with `material_relations!material_relations_from_material_id_fkey(to_material_id)`, disambiguating the two-FK relationship (`from_material_id` vs `to_material_id`) that PostgREST rejected with PGRST201.
- Added `tests/unit/test_supabase_material_repository_embed.py` — a self-contained fake client whose `select()` records the column spec and raises a PGRST201-shaped error for a bare `material_relations(` embed. It locks `repo.get()`, `repo.get_by_slug()`, and the disambiguated-vs-unhinted embed contract.
- Left `material_tags(tag_slug,tag_label)` unhinted (single FK → unambiguous) and kept the fix entirely inside the adapter (`_fetch_one`).
- Live read probe confirms the heal on real PostgREST: `repo.get(2)` → `ready rag-systems`, `repo.get_by_slug('rag-systems')` → Material (no PersistenceError). This removes the HTTP 503 (`materials_unavailable`) path on `POST /admin/materials/{id}/ready` and makes a genuine batch partial result reachable (G-14-4).

## Task Commits

Each task was committed atomically (TDD: RED then GREEN in one commit):

1. **Task 1: Disambiguate material_relations embed + offline PGRST201 regression** - `02e16bc` (fix)

**Plan metadata:** pending (this SUMMARY + tracking commit)

_Note: RED (`uv run pytest tests/unit/test_supabase_material_repository_embed.py -x`) failed with `PersistenceError: materials fetch by id failed: Could not embed because more than one relationship was found…` before the GREEN edit._

## Files Created/Modified
- `supabase-integration/src/supabase_integration/material_repository.py` — `_fetch_one` select now carries the FK hint; no other adapter behavior changed.
- `tests/unit/test_supabase_material_repository_embed.py` — new offline PGRST201-class regression (3 tests) + the recorded embed spec.

## Decisions Made
- FK-constraint-name hint (`material_relations_from_material_id_fkey`) rather than the FK-column hint, preserving outgoing-relations semantics (`from_material_id = <row>` → `to_material_id`).
- Only the `_fetch_one` select literal changed — no `_related_ids`/`_filter_ready_relations`/`save`/domain/route edits, honoring the adapter-boundary constraint.

## Deviations from Plan

None - plan executed exactly as written. The plan's fallback (FK-column hint `material_relations!from_material_id(...)`) was not needed — the constraint-name hint was accepted by the live read probe on the first attempt.

## Issues Encountered
None. (`get(1)` returned `None` in the live probe simply because material id 1 does not exist in the live DB; probing an existing id returned a Material.)

## User Setup Required
None - `.env` already exposes `SUPABASE_URL` / `SUPABASE_SECRET_KEY`; no new configuration.

## Next Phase Readiness
- G-14-1 closed: live promote reads no longer 503. G-14-4 (batch genuine partial result) is unblocked at the read layer — the FE batch control itself is removed by plan 14-07 per the operator decision.
- Ready for phase-level verification of Phase 14.

---
*Phase: 14-draft-ready-justification-honesty*
*Completed: 2026-10-03*

## Self-Check: PASSED

- FOUND: `.planning/phases/14-draft-ready-justification-honesty/14-06-SUMMARY.md`
- FOUND: `supabase-integration/src/supabase_integration/material_repository.py`, `tests/unit/test_supabase_material_repository_embed.py`
- FOUND: `02e16bc` (task commit)
- `uv run pytest tests/unit/test_supabase_material_repository_embed.py tests/unit/test_supabase_issue_repository_contract.py -x` — 12 passed
- `uv run pytest tests/unit/test_http_admin.py -k "ready" -q` — 10 passed, 21 deselected
- live read probe — `get(2)= ready rag-systems`; `get_by_slug ok= True`
