---
phase: 14-draft-ready-justification-honesty
reviewed: 2026-10-04T17:05:00Z
depth: standard
files_reviewed: 20
files_reviewed_list:
  - backend/src/backend/application/use_cases/mark_material_ready.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/domain/material.py
  - backend/src/backend/domain/shortlist.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - supabase-integration/src/supabase_integration/material_repository.py
  - web/src/index.css
  - web/src/main.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/services/adminApi.js
  - web/src/services/adminReadyMock.js
  - web/src/services/adminReadyReconcile.js
  - tests/admin.spec.js
  - tests/unit/test_admin_mark_ready.js
  - tests/unit/test_http_admin.py
  - tests/unit/test_mark_material_ready.py
  - tests/unit/test_score_factors.py
  - tests/unit/test_set_shortlist_decision.py
  - tests/unit/test_supabase_material_repository_embed.py
findings:
  critical: 0
  warning: 3
  info: 6
  total: 9
status: issues_found
---

# Phase 14: Code Review Report

**Reviewed:** 2026-10-04T17:05:00Z
**Depth:** standard
**Files Reviewed:** 20
**Status:** issues_found

## Summary

Re-run of the execute-phase `code_review_gate` during a stale-verification refresh, against the current on-disk source. Phase-16 edits to shared files (`admin.py`, `test_http_admin.py`, and the React/`index.css` surface) are present on disk and were reviewed as they currently stand; none of them structurally changed the Phase-14 promote/justify paths.

Independently reproduced this run:

- `uv run pytest tests/unit` is green (757 passed, 1 deprecation warning); the five Phase-14 backend suites are green (59 passed).
- `node --test tests/unit/test_admin_mark_ready.js` is green (10 passed).
- The central honesty helper still fabricates labels for non-string structured entries — reproduced directly against the on-disk module:
  `honest_factor_labels({'factors':[{'label':None},{'label':None}]}) -> ['None','None']`,
  `({'label':1},{'label':2}) -> ['1','2']`, booleans and containers stringify the same way.

Locked phase decisions hold on disk and are **not** flagged:

- Single `POST /admin/materials/{id}/ready` is body-less and returns `MarkReadyResponse(... extra="forbid")`; already-ready is a 200 no-op and `published_at` is untouched (`Material.with_ready_status`, `material.py:47-51`).
- Batch `POST /admin/materials/ready` is declared **before** the `{material_id}` route (`admin.py:272` vs `:303`), returns HTTP 200 `{"results": [...]}` partial success (never 207), and never aborts on a per-id `MaterialNotFoundError` / `PersistenceError` / unexpected `Exception`.
- Approve cannot flip triage status: `set_shortlist_decision` never touches `materials`, and the AST import guard in `test_set_shortlist_decision.py:119-143` still holds.
- The batch «Сделать ready все одобренные черновики» CTA is absent **by design** (operator override 14-07) — its absence is intended, not a regression, and is not flagged.

No BLOCKER was found. Three Warnings and six Info items remain open (all independently re-verified against current source). The strongest is WR-01: the phase's central honesty helper can fabricate labels from non-string factor entries — latent today because no Phase-14 writer produces such `score_factors`, which is why it is a WARNING rather than a BLOCKER, not because the contract is weak.

## Narrative Findings (AI reviewer)

## Warnings

### WR-01: `honest_factor_labels` fabricates labels for non-string structured entries

**File:** `backend/src/backend/domain/shortlist.py:22-27`
**Issue:** The structured branch coerces *any* present `label` value to a string, so non-readable values count as readable factors and can clear the ≥2 honesty gate:

```python
labels = [
    str(f.get("label", "")).strip()
    for f in factors
    if isinstance(f, dict)
]
```

A missing key hits the `""` default (safe), but an explicitly `null` / numeric / boolean / container value is stringified. Reproduced against the current source:

```text
honest_factor_labels({'factors':[{'label':None},{'label':None}]})    -> ['None', 'None']
honest_factor_labels({'factors':[{'label':1},{'label':2}]})          -> ['1', '2']
honest_factor_labels({'factors':[{'label':True},{'label':False}]})   -> ['True', 'False']
honest_factor_labels({'factors':[{'label':['a']},{'label':{'b':1}}]}) -> ["['a']", "{'b': 1}"]
honest_factor_labels({'factors':[{'label':'A'},{'label':None}]})     -> ['A', 'None']
```

Two `None` entries clear the `len(labels) < 2` check, so the admin shortlist renders fabricated «обоснование» text joined with ` · ` (`factorText`, `AdminDigestPage.jsx:79-83`). This defeats D-13/D-14 ("silent-fake ban everywhere", "never fabricated"). Reachability today is low — the only Phase-14 path into `score_factors` is the seed (string labels) and no `score_factors` writer ships this phase — so this is a latent WARNING, but it is exactly the phase's honesty mechanism.

**Fix:** Accept only string labels; skip everything else, then add non-string cases to the matrix.

```python
labels = [
    f["label"].strip()
    for f in factors
    if isinstance(f, dict) and isinstance(f.get("label"), str)
]
labels = [x for x in labels if x]
```

```python
assert honest_factor_labels({"factors": [{"label": None}, {"label": None}]}) == []
assert honest_factor_labels({"factors": [{"label": 1}, {"label": 2}]}) == []
```

### WR-02: Live `markReady` still rolls a persisted promote back on JSON parse failure

**File:** `web/src/services/adminApi.js:390-395` (consumer: `web/src/pages/AdminDigestPage.jsx:338-365`)
**Issue:** The live path treats a 2xx as successful only if the body parses:

```javascript
if (!response.ok) {
  throw mapHttpError(response, 'Не удалось сделать ready')
}
// Promote persisted; MarkReadyResponse is authoritative (G-14-2 — no refetch coupling).
return response.json()
```

If the promote persisted server-side but the 2xx body is empty/unparseable (proxy truncation, an intermediary `204`, a future route change), `markReady` rejects with a `SyntaxError`. `promoteReady`'s outer `catch` then runs `setItems(previous)`, rolling the row back to `draft` and re-arming the D-85 draft block — the exact silent-revert class G-14-2 removed, merely relocated from the refetch boundary to the response-parse boundary. `response_model=MarkReadyResponse` makes this unlikely, not impossible. Note `tests/unit/test_admin_mark_ready.js:118-121` asserts the literal `return response.json()` inside live `markReady`, so any fix must update that source-shape lock.

**Fix:** Treat reaching `response.ok` as authoritative; never let body parsing decide promote success.

```javascript
if (!response.ok) {
  throw mapHttpError(response, 'Не удалось сделать ready')
}
try {
  return await response.json()
} catch {
  // Persisted; body unreadable — synthesize the authoritative result.
  return { material_id: materialId, status: 'ready' }
}
```

### WR-03: The PGRST201 regression test does not lock the FK hint name

**File:** `tests/unit/test_supabase_material_repository_embed.py:243-245`
**Issue:** The fake raises `PGRST201` only for a bare `material_relations(` (line 129), and the assertions require a `!` hint plus `(to_material_id)` but never the exact constraint name:

```python
assert "material_relations!" in spec
assert re.search(r"material_relations![^(]+\(to_material_id\)", spec)
assert "material_relations(to_material_id)" not in spec
```

A typo'd hint such as `material_relations!material_relations_from_material_idfkey(to_material_id)` passes this test while production fails with `PGRST200` (unknown relationship), re-raising the 503 the 14-06 fix closed. The one literal the fix depends on is the one assertion the test omits — false-green on a just-fixed blocker. (The production literal is correct: `material_relations_from_material_id_fkey` is the Postgres default name for the inline `from_material_id` FK in `001_initial_schema.sql:117`.)

**Fix:** Assert the exact disambiguated literal.

```python
assert (
    "material_relations!material_relations_from_material_id_fkey(to_material_id)" in spec
)
```

## Info

### IN-01: Batch-promote client/harness surface is now dead code

**File:** `web/src/services/adminApi.js:16,21,202-205,406-436`, `web/src/main.jsx:30,61`, `web/src/services/adminReadyMock.js:119-142`, `tests/unit/test_admin_mark_ready.js:46-62`
**Issue:** After 14-07 removed the CTA, nothing in the application calls `markReadyBatch` / `applyMockMarkReadyBatch`. `getMockMarkReadyBatchCalls` is imported into `window.__DIGEST_ADMIN_HARNESS__` and `mockMarkReadyBatchCalls` is reset/incremented, but no Playwright spec references the accessor (only a unit test asserting the export literal exists). This is dead production surface and bundle weight.
**Fix:** Remove the unused exports/harness wiring (and the dead unit assertions), or add a comment documenting the batch client as intentionally retained for a future batch tool.

### IN-02: `_filter_ready_relations` couples per-related lookup failures to the whole read

**File:** `supabase-integration/src/supabase_integration/material_repository.py:169-192`
**Issue:** With the embed working, every `get()` / `get_by_slug()` issues 1 + N queries. Any failure in a single related-material status query is wrapped as `PersistenceError` and fails the primary read, which the admin route maps to 503. A transient hiccup on a secondary relation re-widens the exact 503 blast radius this phase set out to close.
**Fix:** Degrade gracefully (drop the relation on lookup failure) or resolve all target statuses in one `.in_("id", ids)` query.

### IN-03: `MarkReadyBatchRequest.material_ids` is unbounded

**File:** `backend/src/backend/interface/http/routes/admin.py:151-154`
**Issue:** The request accepts an arbitrarily long `material_ids` list, driving N sequential `get` / `save` round-trips in one admin call. Admin-only, so not an authz hole, but there is no product-aligned cap.
**Fix:** Add `Field(max_length=…)` (e.g. a small multiple of `MAX_SHORTLIST_ITEMS`) so overflow yields 422.

### IN-04: Broad `except Exception` in batch promote masks defects without logging

**File:** `backend/src/backend/application/use_cases/mark_material_ready.py:70-79`
**Issue:** The catch-all maps any exception — including programming errors such as `TypeError` or an adapter bug — to `error="unexpected_error"` and continues, with no log. Reasonable resilience for D-08, but it can silently hide real defects behind a per-id result that reads as expected partial success.
**Fix:** Call `logger.exception(...)` before appending, or narrow the catch and keep a logged generic fallback.

### IN-05: Mock `sendDigest` order validation is weaker than the backend

**File:** `web/src/services/adminApi.js:626-633`
**Issue:** The mock only checks `materialIds.length !== poolIds.size || materialIds.some(id => !poolIds.has(id))`, which accepts duplicates (`[101, 101]` against pool `{101, 102}`) and silently drops the omitted id. The backend `_ordered_pool` rejects the same input via set equality. Not reachable from the UI today (issue blocks are deduped by `syncIssueBlocks`), but mock/backend contract drift can mask a future regression.
**Fix:** Mirror the backend.

```javascript
const uniqueIds = new Set(materialIds)
if (uniqueIds.size !== poolIds.size || materialIds.some((id) => !poolIds.has(id))) {
  throw new AdminApiError('Некорректный порядок материалов.', { code: 'BAD_REQUEST', retryable: false })
}
```

### IN-06: Stale-refetch regression test relies on a fixed sleep (timing-dependent false-pass window)

**File:** `tests/admin.spec.js:332-334`
**Issue:** The G-14-2 stale-ready test lets the optimistic update and the still-draft refetch settle with `await page.waitForTimeout(500)` before asserting the row stayed `ready`. Because the expected post-reconcile state is identical to the optimistic state, the assertions pass even if the refetch has not completed yet — so under unusually slow timers the test can go green before the revert it is meant to catch would have run. Mock delays are fixed (60ms POST + 80ms GET), so the practical risk is low, but the test is not conditioned on the reconciliation actually happening.
**Fix:** Wait on a deterministic signal (poll a harness counter/flag set when the post-promote `fetchShortlist` resolves) or assert the refetch completed before checking the badge, instead of a wall-clock timeout.

---

_Reviewed: 2026-10-04T17:05:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
