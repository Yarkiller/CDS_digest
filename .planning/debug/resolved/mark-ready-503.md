---
status: resolved
resolved:
  at: 2026-10-13
  evidence: "_fetch_one emits the FK-hinted material_relations embed, so live get()/get_by_slug() return a Material instead of raising PGRST201"
audit_acknowledged:
  milestone: v1.2
  at: 2026-10-05
  status: unknown
---

# DEBUG — live promote `503` / batch all-fail (G-14-1, G-14-4)

**Status:** root cause found
**Phase:** 14-draft-ready-justification-honesty
**Date:** 2026-10-03
**Symptoms:** Per-row «Сделать ready» → toast «Не удалось сделать ready», row stays «черновик». Batch → «Не удалось сделать ready: 9, 10, 11, 12» (all ids fail).
**Live evidence:** `POST /admin/materials/{id}/ready` → **503**; `POST /admin/materials/ready` → **200** with every `results[].ok=false`. Reproduced for ids 9, 10, 11, 12.

## Root cause

`SupabaseMaterialRepository._fetch_one` (`supabase-integration/src/supabase_integration/material_repository.py:128-146`)
embeds `material_relations(to_material_id)` without naming the foreign key:

```python
.select(
    "id,slug,...,material_tags(tag_slug,tag_label),"
    "material_relations(to_material_id)"
)
```

`materials` and `material_relations` are linked by **two** foreign keys:

- `material_relations_from_material_id_fkey` — `materials(id) → material_relations(from_material_id)`
- `material_relations_to_material_id_fkey` — `materials(id) → material_relations(to_material_id)`

PostgREST refuses the ambiguous embed (`PGRST201`: *"Could not embed because more than one
relationship was found for 'materials' and 'material_relations'"*), the driver raises, and
`_fetch_one` wraps it in `PersistenceError` — so **every** `get()` / `get_by_slug()` call fails.

Chain:

```
mark_material_ready → repo.get(material_id)          # SupabaseMaterialRepository
  → _fetch_one → ambiguous embed → APIError
  → PersistenceError("materials fetch by id failed: ...")
      single route  → HTTPException 503 materials_unavailable
      batch route   → per-id {ok: false, error: "materials_unavailable"} (HTTP 200)
```

## Reproduction (read-only, live DB)

```bash
uv run --env-file .env python - <<'PY'
import os
from supabase_integration import create_service_role_client, SupabaseMaterialRepository
repo = SupabaseMaterialRepository(
    create_service_role_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
)
print(repo.get(1))
PY
```

Observed: `postgrest.exceptions.APIError: {'code': 300, ... 'PGRST201' ...}`
wrapped as `PersistenceError: materials fetch by id failed`.

## Suggested fix direction (non-binding)

Disambiguate the embed by FK name in `_fetch_one`:

```python
"material_relations!material_relations_from_material_id_fkey(to_material_id)"
```

Also verify `material_tags(...)` resolves unambiguously (same PGRST201 class), then re-run the
probe to confirm `get()` returns a `Material`. Regression-lock with a fake-client/contract test
asserting the disambiguated select string (and/or simulating the PGRST201 ambiguity error).

## Blast radius

Any live code path using `SupabaseMaterialRepository.get` / `.get_by_slug` is broken, not just
promote — e.g. the public material reader (`get_by_slug`). Existing tests use
`InMemoryMaterialRepository` / fake Supabase clients and never hit the real PostgREST embed, so
the break was invisible to the suite.

## Files involved

- `supabase-integration/src/supabase_integration/material_repository.py` — ambiguous `material_relations` embed in `_fetch_one`
- `backend/src/backend/application/use_cases/mark_material_ready.py` — surfaces the `PersistenceError`
- `backend/src/backend/interface/http/routes/admin.py` — `PersistenceError → 503`
