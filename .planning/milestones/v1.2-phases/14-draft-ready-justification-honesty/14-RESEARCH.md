# Phase 14: Draft→ready & justification honesty - Research

**Researched:** 2026-10-03
**Domain:** Admin digest triage — material status flip (draft→ready) + shortlist score_factors honesty UX
**Confidence:** HIGH (codebase seams); MEDIUM (FastAPI docs); LOW (ecosystem partial-success conventions)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Draft→ready control placement (ADUX-05 UX)
- **D-01:** Per-row «Сделать ready» control **next to the draft badge** on the shortlist row — visual separation: **state ≠ decision** (Approve/Reject cluster stays separate). — **Reversibility:** reversible.
- **D-02:** **Reject auto-ready on Approve** — approve ≠ ready. Operator must promote explicitly. — **Reversibility:** reversible.
- **D-03:** Optional **batch** control appears only when there are **approved drafts** (D-85 blockers). Pending/rejected drafts do not surface batch. — **Reversibility:** reversible.
- **D-04:** **Confirm only for batch**; per-row is **one-click**. Soft empty-body warn (D-10) is the only per-row interstitial. — **Reversibility:** reversible.
- **D-05:** After promote: **optimistic** badge `draft` → `ready` + **silent refetch** (same UX pattern as Approve/Reject). — **Reversibility:** reversible.

### Lightweight ready semantics (ADUX-05 API / domain)
- **D-06:** Promote is a **lightweight status flip only** — sets `materials.status` to `ready`. **Must not** call `publish_material`, set `published_at`, or trigger knowledge indexing. Purpose: unblock D-85 send gate. Full publish would triple Phase 14 scope. — **Reversibility:** costly — SPA/API clients will treat admin ready as status-only; later “true publish” must be a distinct path.
- **D-07:** API is **material-scoped**: `POST /admin/materials/{id}/ready`. Status lives on `materials`, not `shortlist_items`. Decision ≠ ready. Extensible beyond shortlist. FE already has `material_id` from shortlist enrich. — **Reversibility:** costly — route becomes the admin promote contract.
- **D-08:** Batch: **one** endpoint accepting `material_ids[]` with **partial success** (consistent with decision-batch failure handling). FE uses optimistic UI; does not FE-loop as the API strategy. Exact batch path is Claude’s discretion as long as it stays material-scoped under `/admin/materials/…`. — **Reversibility:** costly — batch response shape becomes FE/test contract.
- **D-09:** **Idempotent:** `draft` → `ready`; already-`ready` → **200 no-op**. **No ready→draft** in Phase 14 (reverse deferred). — **Reversibility:** reversible for adding reverse later; changing no-op→409 would be costly for clients.
- **D-10:** **No API quality gate** — empty/missing body is allowed. UI may soft-warn («продолжить?») when body empty; API always allows. Admin control + honesty (empty is a valid state). — **Reversibility:** reversible.

### Justification honesty bar (ADUX-06)
- **D-11:** **Honest-empty only** this phase. Do **not** implement `score_factors` writers, PIPE config UI, or ingest fill. Demo seed factors already exist; leave them. PIPE-01 / ingest stub → Phase 16 / v1.3+. — **Reversibility:** reversible (fillers can land later without undoing honesty).
- **D-12:** **Scope wall (explicit):** no `score_factors` writers / config UI / ingest fill in Phase 14. — **Reversibility:** reversible as a planning constraint.
- **D-13:** **Silent-fake ban everywhere:** FE never fabricates labels; BE maps only real stored factors via `honest_factor_labels` (D-79 ≥2 rule stays); no backend defaults like «релевантность». — **Reversibility:** costly — honesty is a product contract already shipped in Phase 5.
- **D-14:** ADUX-06 done bar: **regression lock** + **Playwright empty assert** + **unit matrix** for `honest_factor_labels` (0 / 1 / 2+ / whitespace). Populated factor UI stays Phase 5 design; light polish only if empty-copy change forces a shared component touch — **no redesign**. — **Reversibility:** reversible.

### Empty «Обоснование» UX
- **D-15:** Exact empty copy (shortlist row only): **`Обоснование недоступно — скоринг не запускался`**. Preserves old phrase for searchability + adds reason. No 0-vs-&lt;2 sub-case distinction in copy. — **Reversibility:** reversible (copy), but Playwright/mocks lock the exact string this phase.
- **D-16:** Placement: **shortlist row only** (material preview modal does not show factors today). Same **muted** style as current empty copy (content state, not error). — **Reversibility:** reversible.
- **D-17:** Mocks + Playwright assert the **exact** string (Phase 13 honesty-assert pattern). — **Reversibility:** reversible.

### Carried forward (do not re-open)
- Phase 5 **D-85**: Approve allowed on drafts; Send blocked while any approved item is still draft.
- Phase 5 **D-79**: ≥2 readable factor labels or honesty empty via `honest_factor_labels`.
- Phase 12/13 shortlist enrich + `extra="forbid"` — additive fields only via explicit model updates.
- Phase 13 preview honesty complete; draft→ready + justification were deferred here.

### Claude's Discretion
- Exact batch route path under `/admin/materials/…` (e.g. collection POST vs nested) as long as D-07/D-08 hold.
- Soft-warn dialog microcopy for empty body («продолжить?»).
- Button label micro-variants («Сделать ready» / RU equivalent) as long as placement (D-01) holds.
- Whether batch confirm copy lists titles or counts.
- Partial-success response field names mirroring existing decision-batch patterns.

### Deferred Ideas (OUT OF SCOPE)
- Auto-ready on Approve — rejected for this product
- Full `publish_material` / `published_at` / knowledge indexing on promote
- ready→draft reverse control — Phase 15+
- PIPE-01 config UI / ingest `score_factors` writers — Phase 16 / v1.3+
- Factors display in material preview modal — not shown today; out of Phase 14
- CLI `--debug` — Phase 15
- Live SMTP — v1.3
- Phase 13 backlog reader `/materials/<slug>` errors and cursor-pointer polish — stay in Phase 999.* backlog, not this phase
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADUX-05 | Admin can set material status from `draft` → `ready` in UI so send is not blocked by D-85 without SQL | New domain status-only flip (not `as_ready`/`publish_material`); `POST /admin/materials/{id}/ready` + batch; FE per-row + approved-drafts batch; InMemory shortlist status sync for tests; send gate unchanged |
| ADUX-06 | Shortlist «Обоснование» honest — populated `score_factors` or explicit empty (no silent fake) | Keep `honest_factor_labels` D-79; change FE empty copy to exact D-15 string; Playwright + unit matrix; no writers/PIPE UI |
</phase_requirements>

## Summary

Phase 14 closes the UAT gap where operators SQL-updated `materials.status` to unblock D-85 send, and locks honesty copy for empty shortlist justifications. The critical architectural fork is already decided: **lightweight status flip ≠ full publish**. Existing `Material.as_ready` calls `assert_publishable()` and sets `published_at` — it must not be reused. A new domain transition + use-case writing only `status`/`updated_at` via `MaterialRepository.save` unblocks send while leaving `publish_material` / knowledge indexing out of path.

ADUX-06 is mostly a **regression + copy** phase: backend honesty helper already ships; FE today shows lowercase `обоснование недоступно` and Playwright asserts that string. Update to the exact D-15 sentence, extend the unit matrix for whitespace edge cases, and ban any FE/BE fake labels.

**Primary recommendation:** Implement `mark_material_ready` (status-only) behind `POST /admin/materials/{id}/ready` + collection batch `POST /admin/materials/ready`, mirror Approve/Reject optimistic UX for the per-row control, and treat ADUX-06 as exact-string honesty lock — no score_factors writers.

## Project Constraints (from CLAUDE.md / AGENTS.md)

No root `CLAUDE.md` or `.claude/CLAUDE.md` found this session. Actionable directives from `AGENTS.md` + workspace rules:

- **TDD mandatory:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST (Red→Green→Refactor).
- **Ports & Adapters:** domain/application have zero FastAPI/Supabase/httpx; adapters in `supabase-integration` / `data-collection`; wiring only in `composition/`.
- **Frontend:** API only via `web/src/services/`; UI must not invent business labels.
- **Git `origin`:** push/pull/fetch via WSL only (not relevant to Phase 14 implementation).
- **Project skills present:** `.agents/skills/{hallmark,supabase,supabase-postgres-best-practices}` — Hallmark applies only if redesigning UI; CONTEXT forbids redesign (D-14). No schema/migration required for status flip (column already exists).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Lightweight draft→ready status flip | API / Backend (domain + use-case) | Database / Storage | Status is `materials.status`; domain owns transition rules; repo persists |
| Admin promote HTTP contract | API / Backend | — | Thin FastAPI routes under `/admin`, `require_admin` |
| Shortlist reflection of status | Database / Storage (join) | API / Backend | Live shortlist reads `materials.status` via join; GET shortlist already exposes `material_status` |
| D-85 send gate | API / Backend | — | Unchanged: blocks approved∩draft; ready flip removes blocker |
| Per-row / batch promote UX | Browser / Client | — | Optimistic badge + silent refetch; soft empty-body warn |
| Honest «Обоснование» labels | API / Backend (`honest_factor_labels`) | Browser / Client (display only) | BE maps stored factors; FE never fabricates |
| Empty justification copy | Browser / Client | — | Exact RU string when `factor_labels.length < 2` |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | `0.141.1` [VERIFIED: backend/pyproject.toml:8] — runtime `fastapi 0.141.1` via `uv run python` | Admin HTTP routes | Already pinned; path+body patterns match existing admin router |
| Pydantic | `2.13.5` [VERIFIED: runtime `uv run python`] | `extra="forbid"` DTOs | Existing admin DTO pattern (`ConfigDict(extra="forbid")`) |
| pytest | `9.1.1` [VERIFIED: `uv run pytest --version`] | Unit tests | Project unit path `tests/unit` |
| Playwright | `1.62.1` [VERIFIED: `npx playwright --version` / package.json `^1.62.1`] | Admin E2E honesty asserts | Existing `tests/admin.spec.js` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `dataclasses.replace` (stdlib) | — | Immutable Material updates | Status-only flip without `as_ready` |
| In-memory fakes (`backend.tests_support.in_memory`) | in-repo | Unit/HTTP tests without Supabase | All ADUX-05 unit coverage |
| React admin page + `adminApi.js` | in-repo | UX + mock client | ADUX-05/06 FE |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Status-only flip | Reuse `publish_material` / `as_ready` | **Forbidden by D-06** — sets `published_at` + quality gate |
| Material-scoped ready API | Shortlist-scoped `…/shortlist/items/{id}/ready` | Rejected by D-07 — status lives on materials |
| Batch FE-loop like decisions | One batch endpoint | D-08 requires real batch API |
| PIPE/ingest score_factors fill | Honest-empty copy only | D-11/D-12 scope wall |

**Installation:**
```bash
# No new packages — use existing backend/web stack
# Verify:
uv run python -c "import fastapi,pydantic; print(fastapi.__version__, pydantic.__version__)"
uv run pytest --version
npx playwright --version
```

**Version verification:** FastAPI 0.141.1, Pydantic 2.13.5, pytest 9.1.1, Playwright 1.62.1 confirmed this session against the project environment.

## Package Legitimacy Audit

> Phase 14 installs **no new external packages**. Legitimacy gate run on already-pinned stack only.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| fastapi | PyPI | existing pin `==0.141.1` | seam: unknown | github.com/fastapi/fastapi | SUS (too-new / unknown-downloads) | **No install** — already in `backend/pyproject.toml`; do not re-resolve |
| pydantic | PyPI | runtime 2.13.5 | seam: unknown | github.com/pydantic/pydantic | SUS (unknown-downloads) | **No install** — transitive/runtime already present |
| pytest | PyPI | 9.1.1 | seam: unknown | github.com/pytest-dev/pytest | SUS (unknown-downloads) | **No install** — already in root test deps |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** fastapi / pydantic / pytest via seam download-metadata gaps — **not actionable for this phase** (no new installs). Planner must not add new packages without a fresh legitimacy check.

## Architecture Patterns

### System Architecture Diagram

```text
Admin UI (/admin/digest)
  │
  ├─ per-row «Сделать ready» ──POST /admin/materials/{id}/ready──┐
  │     (optional empty-body soft confirm)                        │
  ├─ batch «ready» (only if approved∩draft)                       │
  │     ──POST /admin/materials/ready {material_ids[]}──┐         │
  │                                                     ▼         ▼
  │                                          mark_material_ready use-case
  │                                                     │
  │                              MaterialRepository.get → status flip → save
  │                              (NOT publish_material / as_ready / index)
  │                                                     │
  │                              materials.status = ready (published_at unchanged)
  │                                                     │
  ├─ silent refetch GET /admin/shortlist ◄── join materials.status ──┘
  │         material_status badge draft→ready
  │
  └─ Send ── send_digest ── if any approved∩draft → DraftInSendPoolError (D-85)
                            else proceed (unchanged)

Shortlist «Обоснование»:
  score_factors (stored) → honest_factor_labels (≥2) → factor_labels
  if empty → FE exact copy D-15 (never invent labels)
```

### Recommended Project Structure
```
backend/src/backend/
  domain/material.py              # NEW: status-only ready transition (not as_ready)
  application/use_cases/
    mark_material_ready.py        # NEW: single + batch helpers
  application/ports/
    material_repository.py        # unchanged Protocol (get/save)
  interface/http/routes/admin.py  # NEW routes + forbid DTOs
  tests_support/in_memory.py      # sync material_status for shortlist fake (test fidelity)

web/src/
  services/adminApi.js            # markReady / markReadyBatch + mocks
  pages/AdminDigestPage.jsx       # per-row control, batch, empty copy

tests/
  unit/test_mark_material_ready.py   # NEW Wave 0
  unit/test_http_admin.py            # extend
  unit/test_score_factors.py         # extend matrix
  admin.spec.js                      # ready control + exact empty copy
```

### Pattern 1: Status-only domain transition (contrast with publish)
**What:** Flip `MaterialStatus.DRAFT` → `READY` without quality gate or `published_at`.
**When to use:** Admin ADUX-05 promote only.
**Example:**
```python
# Contrast — DO NOT call for ADUX-05 [VERIFIED: backend/src/backend/domain/material.py:10-46]
# class MaterialStatus(str, Enum):
#     DRAFT = "draft"
#     READY = "ready"
# def as_ready(self, published_at: datetime) -> Material:
#     self.assert_publishable()
#     return replace(self, status=MaterialStatus.READY, published_at=published_at, updated_at=published_at)

from dataclasses import replace
from datetime import datetime, timezone
from backend.domain.material import Material, MaterialStatus

def with_ready_status(material: Material, *, now: datetime) -> Material:
    """Lightweight ready — no assert_publishable, published_at unchanged."""
    if material.status == MaterialStatus.READY:
        return material
    return replace(material, status=MaterialStatus.READY, updated_at=now)
```

### Pattern 2: Thin admin route + material repo (not shortlist decision)
**What:** Material-scoped POST under `/admin`, auth via `require_admin`, container.materials.
**When to use:** ADUX-05 single + batch.
**Example:**
```python
# Source: FastAPI body+path [CITED: https://fastapi.tiangolo.com/tutorial/body]
# Project DTO style [VERIFIED: backend/src/backend/interface/http/routes/admin.py:35-36]
#     model_config = ConfigDict(extra="forbid")

@router.post("/materials/{material_id}/ready", response_model=MarkReadyResponse)
def post_material_ready(material_id: int, request: Request, _admin=Depends(require_admin)):
    materials = request.app.state.container.materials
    material = mark_material_ready(materials, material_id)
    return MarkReadyResponse(material_id=material.id, status=material.status.value)
```

### Pattern 3: Batch partial success (discretion recommendation)
**What:** One collection POST; HTTP 200 with per-id results; do not FE-loop as API strategy (D-08).
**When to use:** Batch promote of approved-draft blockers.
**Recommended shape (discretion):**
```python
# [ASSUMED] response field names — lock in plan + tests
class MarkReadyBatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_ids: list[int]

class MarkReadyBatchItemResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material_id: int
    ok: bool
    status: str | None = None  # "ready" when ok
    error: str | None = None   # e.g. "material_not_found"

class MarkReadyBatchResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    results: list[MarkReadyBatchItemResult]
```
**Batch path (discretion):** `POST /admin/materials/ready` (collection) alongside D-07 single `POST /admin/materials/{id}/ready`. Register collection route so it is not shadowed awkwardly; `{id}: int` rejects the literal `"ready"` with 422, so both can coexist.

### Pattern 4: FE honesty empty (exact string)
**What:** When `<2` labels, show D-15 copy; never invent.
**When to use:** Shortlist row factor caption only.
```javascript
// Current [VERIFIED: web/src/pages/AdminDigestPage.jsx:73-76]
// function factorText(item) {
//   const labels = Array.isArray(item.factor_labels) ? item.factor_labels.filter(Boolean) : []
//   if (labels.length < 2) return 'обоснование недоступно'
//   return labels.join(' · ')
// }
// Target empty (D-15): 'Обоснование недоступно — скоринг не запускался'
```

### Anti-Patterns to Avoid
- **Calling `publish_material` / `Material.as_ready` / `container.publish` / `index_material_chunks`:** Violates D-06; sets `published_at` and may gate on body/title/provenance.
- **Auto-ready on Approve:** Forbidden by D-02.
- **FE fabricating factor labels** (e.g. default «релевантность»): Violates D-13.
- **score_factors writers / PIPE UI in this phase:** Violates D-11/D-12.
- **Putting ready on shortlist_items table/API:** Violates D-07.
- **Redesigning shortlist chrome for honesty:** D-14 — copy + assert only.
- **Business logic in FastAPI routers or React beyond presentation:** Architecture rule — use-case owns flip.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Material persistence | Ad-hoc SQL in route | `MaterialRepository.save` | Ports & adapters; live upsert already maps `status` |
| Factor honesty rules | New FE heuristics | `honest_factor_labels` | D-79 already encodes ≥2 / whitespace / flat-key fallback |
| Admin auth | Custom checks | `require_admin` | Existing D-74 gate |
| Optimistic multi-id UX | New state machine | Mirror `applyDecision` failed-id toast pattern | FE already handles partial failure for decisions |
| Email/send pool rules | Duplicate D-85 | Existing `send_digest` / `DraftInSendPoolError` | Gate already correct once status is ready |

**Key insight:** The product already has publish, send-gate, and honesty helpers — Phase 14 is a **thin admin control + honesty copy lock**, not a new pipeline.

## Common Pitfalls

### Pitfall 1: Reusing `as_ready` / `publish_material`
**What goes wrong:** Empty-body drafts fail `assert_publishable`, or `published_at` is stamped — full-publish semantics leak into triage.
**Why it happens:** Name similarity (`ready`) and existing `AppContainer.publish`.
**How to avoid:** New domain helper + use-case; unit test asserts `published_at is None` (or unchanged) after promote; never import `publish_material` from the new route.
**Warning signs:** Tests calling `container.publish`; response includes `published_at` set to "now".

### Pitfall 2: In-memory shortlist status desync
**What goes wrong:** HTTP unit tests flip `MaterialRepository` status but `GET /admin/shortlist` still shows `draft` because `InMemoryShortlistRepository` stores denormalized `material_status` on `ShortlistItem`.
**Why it happens:** Live `SupabaseShortlistRepository` joins `materials.status` [VERIFIED: supabase-integration/.../shortlist_repository.py:50] — `material_status=str(material.get("status") or "draft")` — in-memory does not.
**How to avoid:** Wave 0 — overlay/sync status from `InMemoryMaterialRepository` in the shortlist fake (or `set_material_status` helper used by mark-ready tests). Prove with HTTP test: seed draft material + shortlist item → POST ready → GET shortlist `material_status=="ready"` → send no longer raises `DraftInSendPoolError` for that id.
**Warning signs:** Green use-case tests, red HTTP shortlist/send integration.

### Pitfall 3: Reader visibility side effect
**What goes wrong:** After status-only ready, `get_material_for_reader` serves the material (gate is `status != READY` only) [VERIFIED: backend/.../get_material_for_reader.py:10-13].
**Why it happens:** MAT-01 equates ready with readable; D-06 accepts status-only ready without `published_at`.
**How to avoid:** Document as accepted consequence of locked D-06; do not "fix" by calling full publish. Do not expand Phase 14 into reader ACL redesign (deferred).
**Warning signs:** Planner tasks that try to hide ready-without-published_at — out of scope unless user re-opens D-06.

### Pitfall 4: Playwright / mock string drift
**What goes wrong:** Spec still asserts old `обоснование недоступно` while UI shows D-15; or case/punctuation mismatch.
**Why it happens:** Exact-string honesty contract (D-15/D-17); current assert [VERIFIED: tests/admin.spec.js:121] uses old lowercase phrase.
**How to avoid:** Update `factorText`, mocks if needed, and Playwright together in one wave; assert exact D-15.
**Warning signs:** Spec finds old string via substring while product shows new sentence (or vice versa).

### Pitfall 5: Batch FE-loop as API strategy
**What goes wrong:** Planner copies decision UX (`for (id of ids) setDecision`) for ready batch, violating D-08.
**Why it happens:** Decisions have no backend batch today — FE loops [VERIFIED: web/.../AdminDigestPage.jsx:285-298].
**How to avoid:** Implement real batch endpoint; FE calls once; partial-success results drive toast/selection.
**Warning signs:** `adminApi.markReady` called in a loop for batch control.

### Pitfall 6: Approve auto-ready regression
**What goes wrong:** Someone "helps" operators by setting ready inside `set_shortlist_decision`.
**Why it happens:** UAT pain (SQL workaround) tempts coupling.
**How to avoid:** Explicit unit: approve draft → still `material_status=draft`; D-02 lock in plan acceptance.
**Warning signs:** Decision use-case importing MaterialRepository.

## Code Examples

### Use-case skeleton (single)
```python
# Pattern aligned with publish_material contrast
# [VERIFIED: backend/src/backend/application/use_cases/publish_material.py:10-16]
# def publish_material(...):
#     material = repo.get(material_id)
#     ...
#     ready = material.as_ready(published_at)
#     return repo.save(ready)

def mark_material_ready(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    clock = now or datetime.now(timezone.utc)
    if material.status == MaterialStatus.READY:
        return material  # D-09 no-op
    updated = replace(material, status=MaterialStatus.READY, updated_at=clock)
    # published_at intentionally untouched (D-06)
    return repo.save(updated)
```

### FE empty-body soft warn (discretion microcopy)
```javascript
// Per-row: only interstitial when body empty (D-04/D-10)
const bodyEmpty = !(item.body_markdown || '').trim()
if (bodyEmpty && !window.confirm('Текст пуст. Сделать ready и продолжить?')) return
await markReady(item.material_id)
// optimistic material_status = 'ready'; then silent fetchShortlist()
```

### honest_factor_labels matrix (extend existing)
```python
# Existing empties [VERIFIED: tests/unit/test_score_factors.py:25-29]
# assert honest_factor_labels({}) == []
# assert honest_factor_labels({"factors": [{"label": "Только один"}]}) == []
# assert honest_factor_labels({"Единственный": 1.0}) == []
# assert honest_factor_labels({"factors": [{"label": ""}, {"label": "  "}]}) == []
# Add explicit named cases for D-14: 0 / 1 / 2+ / whitespace-only keys if not already clear
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SQL `UPDATE materials SET status='ready'` (UAT #5) | Admin UI + material-scoped API | Phase 14 | No SQL for D-85 unblock |
| Full `as_ready`/`publish_material` for "ready" | Split: triage ready vs publish-on-send / true publish | Phase 14 lock D-06 | Avoids quality gate + published_at on triage |
| Empty copy `обоснование недоступно` | `Обоснование недоступно — скоринг не запускался` | Phase 14 D-15 | Honest reason; Playwright lock |
| Expect PIPE to fill factors for ADUX-06 | Honest-empty until Phase 16 | CONTEXT D-11 | Scope control |

**Deprecated/outdated:**
- Treating admin "ready" as synonym of `publish_material` — superseded by D-06 for this milestone.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Batch response fields `results[]` / `ok` / `error` are acceptable names | Pattern 3 | FE/tests rename cost if user prefers different shape — confirm via discretion in plan |
| A2 | Soft-warn confirm via `window.confirm` is acceptable until a shared dialog exists | Code Examples | May need in-app modal for a11y — discretionary |
| A3 | No new DB migration needed (`materials.status` already supports `ready`) | Standard Stack | If live enum/check constraint differs, live promote fails — verify only if executor hits DB error |
| A4 | Partial-success HTTP 200 (not 207 Multi-Status) matches product preference | Pattern 3 | Clients expecting 4xx on any failure would break — lock in HTTP tests |

## Open Questions (RESOLVED)

1. **Batch response field names** — RESOLVED
   - What we know: D-08 wants partial success; decision FE uses failed-id toast, no backend batch today.
   - What's unclear: Exact JSON keys.
   - Recommendation: Use `results: [{material_id, ok, status, error}]` (A1); lock with HTTP unit test.
   - **Locked plan answer:** Plan 02 DTOs `MarkReadyBatchRequest` / `MarkReadyBatchItemResult` / `MarkReadyBatchResponse` with fields `material_ids`, `results[]` `{material_id, ok, status, error}`; HTTP 200 partial success (A4). Locked by unit/HTTP tests in 14-02.

2. **In-memory shortlist sync mechanism** — RESOLVED
   - What we know: Live joins; in-memory denormalizes.
   - What's unclear: Overlay vs explicit `set_material_status` helper.
   - Recommendation: Prefer overlay from materials repo in test support (mirrors live); keep domain use-case materials-only.
   - **Locked plan answer:** Plan 01 wires `InMemoryShortlistRepository` to overlay `material_status` from an attached `InMemoryMaterialRepository` on get_current_batch / get_latest_batch (live-join fidelity); use-case stays materials-only.

3. **Reader visibility after triage ready** — RESOLVED
   - What we know: `get_material_for_reader` keys off `status == READY` only.
   - What's unclear: Whether product owners consider that a problem for empty-body ready materials.
   - Recommendation: Accept per D-06; do not expand scope. Note in plan acceptance notes.
   - **Locked plan answer:** Accepted consequence of D-06 (14-01 `must_haves.assumptions`); out of Phase 14 scope — no reader ACL redesign.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python / uv | Unit tests, backend | ✓ | Python 3.14.0 / uv 0.10.9 | — |
| pytest | ADUX-05/06 unit | ✓ | 9.1.1 | — |
| FastAPI (pinned) | Admin routes | ✓ | 0.141.1 | — |
| Playwright | Admin E2E | ✓ | 1.62.1 | — |
| Live Supabase | Optional live smoke | not required for phase unit/E2E mocks | — | In-memory + FE mocks |

**Missing dependencies with no fallback:** none

**Missing dependencies with fallback:** none

Step 2.6: external tools available for code/config phase; no blocking gaps.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + Playwright 1.62.1 |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests/unit"]`); Playwright via `package.json` scripts |
| Quick run command | `uv run pytest tests/unit/test_mark_material_ready.py tests/unit/test_score_factors.py tests/unit/test_http_admin.py -q` |
| Full suite command | `uv run pytest && npm run test:web` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADUX-05 | draft→ready status-only; `published_at` unchanged; no publish path | unit | `uv run pytest tests/unit/test_mark_material_ready.py -x` | ❌ Wave 0 |
| ADUX-05 | HTTP single ready 200 + idempotent already-ready | unit/HTTP | `uv run pytest tests/unit/test_http_admin.py -k ready -x` | ❌ Wave 0 (extend file) |
| ADUX-05 | HTTP batch partial success (found + missing) | unit/HTTP | same | ❌ Wave 0 |
| ADUX-05 | After ready, approved draft no longer trips `DraftInSendPoolError` | unit | `uv run pytest tests/unit/test_send_digest.py -k draft -x` (+ new bridge test) | ⚠️ partial — send gate exists; bridge after flip needed |
| ADUX-05 | Approve does not auto-ready | unit | decision test assertion | ⚠️ extend `test_set_shortlist_decision.py` |
| ADUX-05 | markReady/markReadyBatch mock helpers; batch single-call; empty factor_labels seed | unit (node) | `node --test tests/unit/test_admin_mark_ready.js` | ❌ Wave 0 |
| ADUX-05 | Per-row control + batch for approved drafts; optimistic UX | e2e | `npx playwright test tests/admin.spec.js -g "ready"` | ❌ Wave 0 |
| ADUX-06 | `honest_factor_labels` 0/1/2+/whitespace | unit | `uv run pytest tests/unit/test_score_factors.py -x` | ✅ extend |
| ADUX-06 | Exact empty copy on shortlist row | e2e | `npx playwright test tests/admin.spec.js -g "обоснование\|Обоснование"` | ⚠️ exists with old string — update |
| ADUX-06 | FE never fabricates labels when `factor_labels=[]` | e2e/unit | Playwright exact string + mock row with `[]` | ⚠️ update |

### Sampling Rate
- **Per task commit:** targeted pytest file(s) for the task
- **Per wave merge:** `uv run pytest tests/unit/test_mark_material_ready.py tests/unit/test_score_factors.py tests/unit/test_http_admin.py tests/unit/test_send_digest.py tests/unit/test_set_shortlist_decision.py -q`
- **Phase gate:** Full `uv run pytest` + admin Playwright green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_mark_material_ready.py` — covers ADUX-05 domain/use-case (status-only, idempotent, not-found, published_at unchanged)
- [ ] HTTP cases in `tests/unit/test_http_admin.py` — single + batch ready routes
- [ ] In-memory shortlist↔materials status sync for HTTP/send bridge tests
- [ ] `tests/unit/test_admin_mark_ready.js` + `web/src/services/adminReadyMock.js` — fast FE service gate
- [ ] Playwright: per-row + batch promote; D-85 unblock smoke; exact D-15 empty copy (replace old assert)
- [ ] Extend `tests/unit/test_score_factors.py` named matrix cases for D-14 if gaps remain after review

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Existing JWT principal + admin profile (`require_admin`) |
| V3 Session Management | no (unchanged) | — |
| V4 Access Control | yes | Admin-only routes; employees 403 (existing pattern) |
| V5 Input Validation | yes | Pydantic `extra="forbid"`; `material_id: int`; bounded `material_ids` list |
| V6 Cryptography | no | — |

### Known Threat Patterns for admin material ready

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Non-admin promote | Elevation of Privilege | `require_admin` (same as shortlist decision) |
| Mass-assign / extra JSON fields | Tampering | `ConfigDict(extra="forbid")` on request DTOs |
| Promote unknown ids to probe | Information Disclosure | 404 `material_not_found` (single); per-id error in batch without leaking other rows |
| Silent fake justifications | Spoofing (trust) | D-13 / `honest_factor_labels` — no invented labels |
| Accidental full publish / indexing | Tampering / Integrity | D-06 scope wall — no `publish_material` / index calls |

## Sources

### Primary (HIGH confidence)
- In-repo: `backend/src/backend/domain/material.py` — `MaterialStatus`, `as_ready` / `assert_publishable`
- In-repo: `backend/src/backend/application/use_cases/publish_material.py` — contrast path
- In-repo: `backend/src/backend/domain/shortlist.py` — `honest_factor_labels`
- In-repo: `backend/src/backend/application/use_cases/send_digest.py` — `DraftInSendPoolError` / D-85
- In-repo: `web/src/pages/AdminDigestPage.jsx` — `factorText`, `approvedDrafts`, decision optimistic UX
- In-repo: `supabase-integration/.../shortlist_repository.py` — live `material_status` join
- Phase CONTEXT / REQUIREMENTS / 10-UAT.md #5–#6

### Secondary (MEDIUM confidence)
- Context7 `/websites/fastapi_tiangolo` — path params + body; `extra: "forbid"` model_config [CITED: fastapi.tiangolo.com/tutorial/body, header-param-models]

### Tertiary (LOW confidence)
- Ecosystem partial-success conventions — websearch provider unavailable to this subagent; recommendation based on in-repo decision FE pattern + CONTEXT D-08 [ASSUMED for field names]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pinned versions verified in environment; no new packages
- Architecture: HIGH — seams and anti-patterns verified in source this session
- Pitfalls: HIGH for as_ready/desync/string drift; MEDIUM for reader side-effect product acceptance

**Research date:** 2026-10-03
**Valid until:** 2026-11-02 (stable in-repo domain; re-check if MaterialStatus or shortlist DTO contracts change)
