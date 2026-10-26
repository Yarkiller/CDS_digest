# Phase 14: Draft→ready & justification honesty - Pattern Map

**Mapped:** 2026-10-03
**Files analyzed:** 13
**Analogs found:** 12 / 13

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/src/backend/domain/material.py` | model | transform | `backend/src/backend/domain/material.py` (`as_ready` contrast) | exact (extend; do not reuse publish gate) |
| `backend/src/backend/application/use_cases/mark_material_ready.py` | service | CRUD | `backend/src/backend/application/use_cases/publish_material.py` | role-match (status-only fork) |
| `backend/src/backend/interface/http/routes/admin.py` | route | request-response | `backend/src/backend/interface/http/routes/admin.py` + `materials.py` | exact (DTO/auth) / role-match (404) |
| `backend/src/backend/tests_support/in_memory.py` | utility | CRUD | `backend/src/backend/tests_support/in_memory.py` | exact (extend shortlist sync) |
| `backend/src/backend/application/ports/material_repository.py` | model | CRUD | same file (unchanged Protocol) | exact — reuse only |
| `web/src/services/adminApi.js` | service | request-response | `web/src/services/adminApi.js` (`setDecision`) | exact |
| `web/src/pages/AdminDigestPage.jsx` | component | request-response | `web/src/pages/AdminDigestPage.jsx` | exact |
| `tests/unit/test_mark_material_ready.py` | test | CRUD | `tests/unit/test_publish_and_index.py` | role-match |
| `tests/unit/test_http_admin.py` | test | request-response | `tests/unit/test_http_admin.py` | exact |
| `tests/unit/test_score_factors.py` | test | transform | `tests/unit/test_score_factors.py` | exact |
| `tests/unit/test_set_shortlist_decision.py` | test | CRUD | `tests/unit/test_set_shortlist_decision.py` | exact |
| `tests/unit/test_send_digest.py` | test | request-response | `tests/unit/test_send_digest.py` | exact |
| `tests/admin.spec.js` | test | request-response | `tests/admin.spec.js` | exact |

## Pattern Assignments

### `backend/src/backend/domain/material.py` (model, transform)

**Analog:** `backend/src/backend/domain/material.py` — **contrast only**; ADUX-05 must not call `as_ready` / `assert_publishable`.

**Imports / status enum** (lines 1–12):
```python
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum

from backend.domain.errors import MaterialValidationError


class MaterialStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
```

**Anti-pattern — full publish transition** (lines 34–46) — DO NOT reuse for Phase 14:
```python
    def assert_publishable(self) -> None:
        if not self.title.strip():
            raise MaterialValidationError("title is required")
        if not self.body_markdown.strip():
            raise MaterialValidationError("body is required")
        # ...

    def as_ready(self, published_at: datetime) -> Material:
        self.assert_publishable()
        return replace(self, status=MaterialStatus.READY, published_at=published_at, updated_at=published_at)
```

**Core pattern to add** (status-only; D-06/D-09 — from RESEARCH, aligned with `replace` usage above):
```python
def with_ready_status(self, *, now: datetime) -> Material:
    """Lightweight ready — no assert_publishable; published_at unchanged."""
    if self.status == MaterialStatus.READY:
        return self
    return replace(self, status=MaterialStatus.READY, updated_at=now)
```

---

### `backend/src/backend/application/use_cases/mark_material_ready.py` (service, CRUD)

**Analog:** `backend/src/backend/application/use_cases/publish_material.py`

**Imports + get/save skeleton** (lines 1–16) — copy structure; swap `as_ready` for status-only:
```python
from __future__ import annotations

from datetime import datetime, timezone

from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material


def publish_material(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    published_at = now or datetime.now(timezone.utc)
    ready = material.as_ready(published_at)
    return repo.save(ready)
```

**Target core pattern** (planner: implement this shape, not `publish_material`):
```python
def mark_material_ready(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    clock = now or datetime.now(timezone.utc)
    updated = material.with_ready_status(now=clock)  # or inline replace; published_at untouched
    if updated is material:  # already ready — D-09 no-op
        return material
    return repo.save(updated)
```

**Batch helper** (no backend batch analog — compose from single + FE partial-success toast pattern):
```python
def mark_materials_ready(repo: MaterialRepository, material_ids: list[int], *, now: datetime | None = None) -> list[...]:
    # per-id try: ok/status or error="material_not_found"; never abort whole batch
    ...
```

**Port reuse** — `backend/src/backend/application/ports/material_repository.py` (lines 8–13):
```python
class MaterialRepository(Protocol):
    def get(self, material_id: int) -> Material | None: ...
    def get_by_slug(self, slug: str) -> Material | None: ...
    def save(self, material: Material) -> Material: ...
```

---

### `backend/src/backend/interface/http/routes/admin.py` (route, request-response)

**Analog (auth + forbid DTOs + thin handler):** same file — `post_shortlist_decision`  
**Analog (MaterialNotFoundError → 404):** `backend/src/backend/interface/http/routes/materials.py`

**Imports / auth** (admin.py lines 7–32):
```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
# ...
from backend.interface.http.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])
```

**DTO pattern** (lines 35–72):
```python
class SetShortlistDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(
        ...,
        min_length=1,
        description="shortlist_decision: pending|approved|rejected (D-82; allowlist in use-case)",
    )
```

**Auth + domain→HTTP map** (lines 231–260):
```python
def post_shortlist_decision(
    material_id: int,
    body: SetShortlistDecisionRequest,
    request: Request,
    admin: CurrentUser = Depends(require_admin),
) -> AdminShortlistResponse:
    shortlist = _require_shortlist(request)
    try:
        dto = set_shortlist_decision(...)
    except InvalidShortlistDecisionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_decision") from exc
    except ShortlistNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="shortlist_item_not_found") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="shortlist_unavailable") from exc
    return _to_response(dto)
```

**Materials 404 detail string** (materials.py lines 45–52, 102–108) — use for single ready:
```python
def _require_materials(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "materials", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_not_configured",
        )
    return container.materials

# ...
    except MaterialNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="material_not_found",
        ) from exc
```

**Container access** (admin.py lines 143–150, 335) — ready routes use `container.materials`, not shortlist:
```python
def _require_container(request: Request):
    container = request.app.state.container
    if container is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="container_not_configured",
        )
    return container
```

**Batch request body shape analog** — `SendDigestRequest.material_ids` (admin.py lines 114–119):
```python
class SendDigestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_ids: list[int] | None = None
```

**Recommended new DTOs** (discretion A1 from RESEARCH — no in-repo partial-success response yet):
```python
class MarkReadyBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_ids: list[int]

class MarkReadyBatchItemResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_id: int
    ok: bool
    status: str | None = None
    error: str | None = None
```

---

### `backend/src/backend/tests_support/in_memory.py` (utility, CRUD)

**Analog:** same file — `InMemoryMaterialRepository` + denormalized `ShortlistItem.material_status`.

**Material repo** (lines 306–320) — already sufficient for status flip:
```python
class InMemoryMaterialRepository:
    def __init__(self, materials: list[Material] | None = None) -> None:
        self._by_id: dict[int, Material] = {m.id: m for m in (materials or [])}
        self._by_slug: dict[str, Material] = {m.slug: m for m in (materials or [])}

    def get(self, material_id: int) -> Material | None:
        return self._by_id.get(material_id)

    def save(self, material: Material) -> Material:
        self._by_id[material.id] = material
        self._by_slug[material.slug] = material
        return material
```

**Shortlist denormalization pitfall** (lines 215–220) — `set_decision` copies `material_status` unchanged; live joins `materials.status`. Phase 14 must add overlay/sync so GET shortlist reflects ready after mark-ready:
```python
                updated.append(
                    ShortlistItem(
                        material_id=item.material_id,
                        rank=item.rank,
                        title=item.title,
                        material_status=item.material_status,  # denormalized — sync needed
                        decision=decision,
                        # ...
                    )
                )
```

---

### `web/src/services/adminApi.js` (service, request-response)

**Analog:** `setDecision` (lines 371–416) — mock/live cutover, `AdminApiError`, Bearer header.

```javascript
export async function setDecision(materialId, decision, accessToken) {
  if (useMocks()) {
    await delay(60)
    // ... mutate mockBatch.items, return cloneBatch()
  }

  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/shortlist/items/${materialId}/decision`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ decision }),
    })
  } catch {
    throw new AdminApiError('Не сохранено', { code: 'NETWORK', retryable: true })
  }

  if (!response.ok) {
    throw mapHttpError(response, 'Не сохранено')
  }

  const body = await response.json()
  return mapShortlistBody(body)
}
```

**Mock seed with empty factors + draft** (lines 83–98) — keep for ADUX-06 honesty; ensure empty-copy Playwright row exists:
```javascript
  {
    material_id: 104,
    rank: 4,
    title: 'SQL Dashboards for Audit Reporting',
    material_status: 'draft',
    decision: 'pending',
    score: 0.74,
    factor_labels: [],
    body_markdown: '',
    // ...
  },
```

**Target:** `markReady(materialId)` → `POST /admin/materials/{id}/ready`; `markReadyBatch(materialIds)` → `POST /admin/materials/ready` once (D-08 — no FE loop as API strategy). Mock updates `item.material_status = 'ready'`.

---

### `web/src/pages/AdminDigestPage.jsx` (component, request-response)

**Analog:** same file — `factorText`, `approvedDrafts`, `applyDecision`, draft badge cluster.

**Honesty empty** (lines 73–77) — change string only (D-15):
```javascript
function factorText(item) {
  const labels = Array.isArray(item.factor_labels) ? item.factor_labels.filter(Boolean) : []
  if (labels.length < 2) return 'обоснование недоступно'
  return labels.join(' · ')
}
// Target: 'Обоснование недоступно — скоринг не запускался'
```

**Approved-draft gate** (lines 214–221, 244–248) — batch ready control visibility (D-03):
```javascript
  const approvedDrafts = useMemo(
    () => items.filter((item) => item.decision === 'approved' && item.material_status === 'draft'),
    [items],
  )
  // sendHint when approvedDrafts.length > 0: 'Уберите черновики...'
```

**Partial-success / silent refetch** (lines 285–318) — mirror for ready; batch must call API once:
```javascript
  async function applyDecision(decision) {
    // ...
      for (const id of ids) {
        try {
          latest = await setDecision(id, decision)
        } catch {
          failed.push(id)
        }
      }
      if (failed.length > 0) {
        try {
          const dto = await fetchShortlist()
          applyBatch(dto, setItems, setBatchMeta, setDigestRest, setDaysUntilNextBatch)
        } catch { /* ... */ }
        setToast(
          failed.length === ids.length
            ? 'Не сохранено'
            : `Не сохранено: ${failed.join(', ')}`,
        )
```

**Draft badge placement** (lines 673–684) — D-01: put «Сделать ready» next to this badge, not in Approve/Reject cluster:
```javascript
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <span
                        className={[
                          'rounded-md px-2 py-0.5 text-xs font-medium',
                          item.material_status === 'ready'
                            ? 'bg-[oklch(92%_0.04_155)] text-[oklch(35%_0.1_155)]'
                            : 'bg-[oklch(93%_0.05_50)] text-[oklch(45%_0.12_38)]',
                        ].join(' ')}
                      >
                        {item.material_status}
                      </span>
```

**Muted factor caption** (lines 691–693):
```javascript
                    <p className="mt-1 max-w-[12rem] break-words text-xs text-muted">
                      {factorText(item)}
                    </p>
```

---

### `tests/unit/test_mark_material_ready.py` (test, CRUD)

**Analog:** `tests/unit/test_publish_and_index.py`

**Fixture + assertions** (lines 14–49) — reuse `_draft()` helper; invert publish expectations:
```python
def _draft(**overrides: object) -> Material:
    base = {
        "id": 1,
        "slug": "rag-systems",
        "title": "Building Production RAG Systems",
        # ...
        "status": MaterialStatus.DRAFT,
        "published_at": None,
        # ...
    }
    base.update(overrides)
    return Material(**base)

def test_publish_material_sets_ready_when_quality_gate_passes() -> None:
    repo = InMemoryMaterialRepository([_draft()])
    published = publish_material(repo, material_id=1)
    assert published.status == MaterialStatus.READY
    assert published.published_at is not None

def test_publish_material_rejects_empty_body() -> None:
    repo = InMemoryMaterialRepository([_draft(body_markdown="")])
    with pytest.raises(MaterialValidationError):
        publish_material(repo, material_id=1)
```

**Phase 14 cases to assert instead:**
- empty body **allowed**; `published_at is None` (unchanged)
- already-ready → same object / no-op (D-09)
- missing id → `MaterialNotFoundError`
- never imports / calls `publish_material` / `index_material_chunks`

---

### `tests/unit/test_http_admin.py` (test, request-response)

**Analog:** same file — decision auth + D-85 draft stays draft + send draft pool.

**Client harness** (lines 59–74, 589–602):
```python
def _client(signing_jwk: dict[str, Any], container: AppContainer) -> TestClient:
    # Settings + create_app(..., container=container, signing_key_resolver=...)
    return TestClient(app)

def _admin_client_with_batch(batch: ShortlistBatch | None):
    container.shortlist = InMemoryShortlistRepository(batch=batch)
    # seed admin profile, mint token
    return client, headers, container
```

**Approve ≠ ready lock** (lines 446–473) — keep / extend as D-02 regression:
```python
    assert draft["decision"] == "approved"
    assert draft["material_status"] == "draft"
```

**Send blocked by approved draft** (lines 823–857) — bridge after ready: POST ready then send succeeds:
```python
def test_admin_send_draft_in_pool_returns_400() -> None:
    """ADMIN-03 / D-85: approved draft blocks send with 400."""
    # ...
    assert detail == "draft_in_send_pool" or (
        isinstance(detail, dict) and detail.get("code") == "draft_in_send_pool"
    )
```

**New cases:** employee 403 on `/admin/materials/{id}/ready`; 200 draft→ready; 200 already-ready no-op; batch partial success; forbid unknown JSON fields; GET shortlist `material_status=="ready"` after promote (needs in-memory sync).

---

### `tests/unit/test_score_factors.py` (test, transform)

**Analog:** same file + `backend/src/backend/domain/shortlist.py` `honest_factor_labels`.

**Existing matrix** (test_score_factors.py lines 25–29, 44–54):
```python
def test_honest_factor_labels_empty_when_fewer_than_two_readable() -> None:
    assert honest_factor_labels({}) == []
    assert honest_factor_labels({"factors": [{"label": "Только один"}]}) == []
    assert honest_factor_labels({"Единственный": 1.0}) == []
    assert honest_factor_labels({"factors": [{"label": ""}, {"label": "  "}]}) == []
```

**Domain rule** (shortlist.py lines 10–37) — do not invent labels; ≥2 or `[]`:
```python
def honest_factor_labels(score_factors: Mapping[str, Any] | None) -> list[str]:
    # ...
    if len(labels) < 2:
        return []
    return labels
```

**Extend for D-14:** named cases 0 / 1 / 2+ / whitespace-only flat keys (if gaps remain). No production change required unless tests reveal a bug.

---

### `tests/unit/test_set_shortlist_decision.py` (test, CRUD)

**Analog:** same file — D-02 / D-85 approve-on-draft:

```python
def test_approve_allowed_on_draft_material() -> None:
    """ADMIN-03 / D-85: Approve succeeds on draft — no DraftInSendPoolError here."""
    # ...
    draft = next(i for i in snapshot.items if i.material_id == 102)
    assert draft.decision == "approved"
    assert draft.material_status == "draft"
```

Keep as regression lock: approve must never flip `material_status`.

---

### `tests/unit/test_send_digest.py` (test, request-response)

**Analog:** same file — D-85 gate (lines 143–170):

```python
def test_send_blocks_approved_draft_in_pool() -> None:
    """ADMIN-03 / D-85: any approved draft → DraftInSendPoolError; not sent."""
    # material_status="draft", decision="approved"
    with pytest.raises(DraftInSendPoolError) as exc_info:
        ...
    assert 102 in exc_info.value.draft_material_ids
```

**Bridge test pattern:** seed approved∩draft → `mark_material_ready` on materials repo + sync shortlist status → `send_digest` no longer raises for that id. Prefer HTTP bridge in `test_http_admin.py` if shortlist fake gains materials overlay.

---

### `tests/admin.spec.js` (test, request-response)

**Analog:** same file — honesty string + D-85 draft hint.

**Old empty assert** (lines 120–121) — replace with exact D-15:
```javascript
    await expect(page.getByText("обоснование недоступно").first()).toBeVisible();
// → await expect(page.getByText("Обоснование недоступно — скоринг не запускался").first()).toBeVisible();
```

**Approved-draft send block** (lines 252–268) — extend with promote control smoke:
```javascript
  test("approved draft blocks send with draft hint (ADMIN-03/07, D-85)", async ({ page }) => {
    // approve draft row → hint visible → send disabled
    // NEW: click «Сделать ready» → badge ready → hint clears / send path unblocked after preview
  });
```

## Shared Patterns

### Authentication (admin-only)
**Source:** `backend/src/backend/interface/http/routes/admin.py` + `backend/src/backend/interface/http/deps.py` (`require_admin`)  
**Apply to:** All new `/admin/materials/.../ready` routes  
```python
_admin: CurrentUser = Depends(require_admin)
# Employee → 403 detail="forbidden" (see test_admin_decision_employee_returns_403)
```

### Error Handling
**Source:** `admin.py` decision map + `materials.py` `material_not_found`  
**Apply to:** Single ready route  
| Domain error | HTTP | detail |
|--------------|------|--------|
| `MaterialNotFoundError` | 404 | `material_not_found` |
| materials missing on container | 503 | `materials_not_configured` |
| batch item missing | 200 + per-id `ok: false`, `error: "material_not_found"` | |

### Validation
**Source:** admin DTOs `ConfigDict(extra="forbid")`  
**Apply to:** `MarkReadyBatchRequest` and any ready response models — additive fields only via explicit models (Phase 12 lock).

### FE API boundary
**Source:** `web/src/services/adminApi.js`  
**Apply to:** All ready client calls — UI never talks to FastAPI paths directly; mocks via `isMocksEnabled()`; no silent live→mock fallback.

### Honesty / silent-fake ban
**Source:** `backend/src/backend/domain/shortlist.py` `honest_factor_labels` + FE `factorText`  
**Apply to:** ADUX-06 — BE returns only real labels; FE shows D-15 string when `<2`; never invent «релевантность».

### Optimistic UX + silent refetch
**Source:** `AdminDigestPage.jsx` `applyDecision` / `fetchShortlist`  
**Apply to:** Per-row ready (D-05): optimistic `material_status='ready'`, then silent refetch; batch uses one API call + toast from failed ids in `results[]`.

### Composition wiring
**Source:** `backend/src/backend/composition/container.py` — `AppContainer.materials` already wired via `build_in_memory_container`  
**Apply to:** Ready routes read `request.app.state.container.materials`; do **not** wire through `container.publish` / `as_ready`.

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| Backend batch partial-success response DTO | route/DTO | request-response | No admin multi-id result envelope exists; decisions FE-loop today. Use RESEARCH A1 shape (`results[]` / `ok` / `error`) + lock in HTTP tests. Closest partial-success UX is FE `applyDecision` failed-id toast only. |

## Metadata

**Analog search scope:** `backend/src/backend/{domain,application,interface/http,tests_support,composition}`, `web/src/{pages,services}`, `tests/unit`, `tests/admin.spec.js`  
**Files scanned:** ~25 tracked candidates; 8 primary analogs deep-read  
**Tracked-source gate:** all named analog paths verified via `git ls-files`  
**Pattern extraction date:** 2026-10-03
