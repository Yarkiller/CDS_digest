---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "POST response is authoritative; preservePromotedReady reconciles a still-draft refetch (web/src/services/adminReadyReconcile.js)"
trigger: "Per-row «Сделать ready» click does nothing — state unchanged (ADUX-05, D-85 unblock broken). Discovered during UAT verification of Phase 14."
created: 2026-10-03T18:58:00Z
updated: 2026-10-03T19:10:00Z
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: investigating
---

## Current Focus

<!-- OVERWRITE on each update - reflects NOW -->

hypothesis: Per-row promote is a silent no-op in the LIVE path because the optimistic
  `material_status: ready` flip is unconditionally overwritten by the post-POST shortlist
  refetch (`applyBatch(dto)`). In live mode `markReady` couples promote success to a
  refetch of `/admin/shortlist`; if that refetch returns the material still `draft`, the
  badge silently reverts — no toast, no console error. The mock path cannot exhibit this
  because `applyMockMarkReady` mutates `mockBatch.items` before `cloneBatch()`, so its
  reconcile always returns `ready`.

test: Read `promoteReady` (AdminDigestPage.jsx), `markReady`/`applyMockMarkReady`
  (adminApi.js / adminReadyMock.js), `mark_material_ready` + Supabase repos.
expecting: Confirm optimistic→refetch overwrite is the silent-revert mechanism; confirm
  live join (`materials.status`) vs mock (in-memory mutate) divergence.
next_action: Record evidence + write Resolution.root_cause; return ROOT CAUSE FOUND.

## Symptoms

<!-- Written during gathering, then IMMUTABLE -->

expected: Clicking per-row «Сделать ready» next to a draft badge promotes draft→ready,
  flips the badge, and clears the D-85 send-gate draft hint (ADUX-05 / D-85 unblock).
actual: Per-row «Сделать ready» click does nothing. State unchanged. D-85 unblock broken.
errors: None reported in console text; user suspects a live-vs-mock mismatch.
reproduction: Open Admin Digest page, click per-row «Сделать ready» on a draft row.
started: Discovered during UAT verification of Phase 14.

## Eliminated

<!-- APPEND only - prevents re-investigating -->

- hypothesis: Button is disabled by `mutating` stuck true
  evidence: `mutating` is set false in `finally` of every mutating handler
    (`promoteReady`, `promoteApprovedDrafts`, `applyDecision`); starts `false`; button
    renders `disabled={mutating}` only while a request is in flight.
  timestamp: 2026-10-03T19:05:00Z

- hypothesis: Handler early-returns because `item.material_status !== 'draft'`
  evidence: Button only renders when `item.material_status === 'draft'`, so the guard
    `item.material_status !== 'draft'` is false at click time.
  timestamp: 2026-10-03T19:05:00Z

- hypothesis: CR-01 as originally described (refetch throw → FE draft rollback after
    successful POST) is still live
  evidence: `markReady` already wraps the refetch in `try/catch` returning `null`;
    `promoteReady` keeps optimistic ready when `dto` is null. Regression test
    `tests/unit/test_admin_mark_ready.js` ("live markReady / promoteReady CR-01
    refetch best-effort") locks this. CR-01/IN-01 already fixed.
  timestamp: 2026-10-03T19:06:00Z

- hypothesis: Backend `material_status` denormalized on `digest_shortlist_items`
  evidence: `001_initial_schema.sql` `digest_shortlist_items` has no `material_status`
    column; `SupabaseShortlistRepository._item_from_row` reads `materials.status` from the
    join (`material_status=str(material.get("status") or "draft")`).
  timestamp: 2026-10-03T19:07:00Z

- hypothesis: Admin auth divergence between GET /admin/shortlist and POST
    /admin/materials/{id}/ready
  evidence: Both routes use `Depends(require_admin)`; GET works (user sees shortlist), so
    the same JWT/profile passes for POST. `isMocksEnabled()` and `useLiveAuth()` agree for
    `VITE_USE_MOCKS=false` (`.env.local`).
  timestamp: 2026-10-03T19:08:00Z

## Evidence

<!-- APPEND only - facts discovered -->

- timestamp: 2026-10-03T19:01:00Z
  checked: web/src/pages/AdminDigestPage.jsx promoteReady (lines ~327-360)
  found: Optimistic `setItems(ready)` → `const dto = await markReady(id)` →
    `if (dto) applyBatch(dto, …)` else refetch; on catch `setItems(previous)` + toast.
    `applyBatch(dto)` REPLACES items from `dto.items`, overwriting the optimistic ready.
  implication: If refetched dto still reports `draft`, badge reverts silently (no throw).

- timestamp: 2026-10-03T19:02:00Z
  checked: web/src/services/adminApi.js markReady live path (lines ~355-392)
  found: Live path: POST `/admin/materials/{id}/ready` → if ok `return await
    fetchShortlist(token)`; refetch failure caught → `return null`. Mock path:
    `applyMockMarkReady(mockBatch.items, id)` then `return cloneBatch()`.
  implication: Mock reconcile always `ready`; live reconcile depends on backend persisting.

- timestamp: 2026-10-03T19:03:00Z
  checked: web/src/services/adminReadyMock.js applyMockMarkReady
  found: Mutates `item.material_status = 'ready'` in the shared `mockBatch.items` seed.
  implication: Mock `cloneBatch()` reflects ready — masks the silent-revert class in tests.

- timestamp: 2026-10-03T19:04:00Z
  checked: backend/src/backend/application/use_cases/mark_material_ready.py +
    supabase-integration material_repository.py save()
  found: `mark_material_ready` → `with_ready_status` → `repo.save` upserts `materials`
    with `status='ready'` via service_role (RLS bypass). Correct when deployed.
  implication: Live backend code is correct; silent no-op is a reconciliation/refetch
    overwrite, not a backend logic error — surfaces when the live promote doesn't persist
    (deployment gap / material-id mismatch / PersistenceError→503).

- timestamp: 2026-10-03T19:04:30Z
  checked: supabase-integration shortlist_repository.py _item_from_row + _batch_with_items
  found: `material_status=str(material.get("status") or "draft")` from `materials(status,…)`
    join using service_role.
  implication: Shortlist reflects live `materials.status`; no denormalized copy.

- timestamp: 2026-10-03T19:05:00Z
  checked: web/.env.local + .env + settings.py + composition/live.py
  found: `VITE_USE_MOCKS=false`, `VITE_API_BASE_URL=http://127.0.0.1:8000`;
    `APP_CONTAINER=live`; `build_live_container` wires SupabaseMaterialRepository +
    SupabaseShortlistRepository.
  implication: App is running live, not mock; mock tests therefore do not cover the live
    reconcile path that silently reverts.

- timestamp: 2026-10-03T19:06:00Z
  checked: tests/unit/test_admin_mark_ready.js + tests/admin.spec.js
  found: Playwright per-row test drives the mock path and auto-accepts the empty-body
    `window.confirm`; CR-01 unit test only asserts source-shape (try/catch + return null),
    not the live "POST 2xx but refetch returns draft" reconcile.
  implication: No test covers the live silent-revert reconcile — the gap that let it ship.

## Resolution

<!-- OVERWRITE as understanding evolves -->

root_cause: "Per-row «Сделать ready» is a silent no-op in the LIVE path because the
  optimistic `ready` flip is not authoritative: `promoteReady` unconditionally applies the
  post-POST shortlist refetch (`applyBatch(dto)`), which overwrites the optimistic `ready`
  back to `draft` whenever the refetched shortlist still reports `draft`. In live mode
  `markReady` couples promote success to `fetchShortlist`; the mock path is immune because
  `applyMockMarkReady` mutates the in-memory seed so `cloneBatch()` always returns `ready`.
  The live no-op triggers when the backend-side promote does not persist (backend not
  running Phase 14 `mark_material_ready`, material-id mismatch → `MaterialNotFoundError`,
  or `PersistenceError` → 503) — and the reconciliation silently reverts instead of
  surfacing it."
fix: ""
verification: ""
files_changed: []
