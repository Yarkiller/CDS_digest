# Phase 4: Knowledge & Razbory - Pattern Map

**Mapped:** 2026-09-20
**Files analyzed:** 32
**Analogs found:** 31 / 32

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/.../domain/razbor.py` | model | transform | `backend/.../domain/material.py` (Enum + frozen dataclass) | exact |
| `backend/.../domain/knowledge.py` | model | transform | same file (`KnowledgeHit` — keep score server-side) | exact |
| `backend/.../domain/errors.py` | model | request-response | same file (`MaterialNotFoundError`, `MaterialValidationError`) | exact |
| `backend/.../ports/knowledge_chunk_repository.py` | service | CRUD | same file (+ `search(...)`); live vs list_all split | exact |
| `backend/.../ports/query_embedder.py` | service | transform | `data-collection/.../foundry.py` `EMBEDDING_DIM=1024` + Protocol style of ports | role-match |
| `backend/.../ports/razbor_repository.py` | service | CRUD | `backend/.../ports/issue_repository.py` | exact |
| `backend/.../ports/notebook_storage.py` | service | file-I/O | **no close analog** — Path containment helper | none |
| `backend/.../use_cases/search_knowledge.py` | service | request-response | same file (evolve: blank guard, pagination, dedupe) | exact |
| `backend/.../use_cases/list_razbors.py` | service | request-response | `backend/.../use_cases/list_archive_issues.py` | exact |
| `backend/.../use_cases/get_razbor.py` | service | request-response | `backend/.../use_cases/get_material_for_reader.py` | exact |
| `backend/.../use_cases/download_razbor_notebook.py` | service | file-I/O | `get_material_for_reader.py` (not-found raise) + RESEARCH FileResponse sketch | partial |
| `backend/.../routes/knowledge.py` | route | request-response | `backend/.../routes/issues.py` (list + auth) + `materials.py` (DTO omit internals) | exact |
| `backend/.../routes/razbory.py` | route | request-response | `materials.py` (detail 404) + `issues.py` (list empty 200) | exact |
| `backend/.../interface/http/app.py` | config | — | same file (`include_router`) | exact |
| `backend/.../composition/container.py` | config | — | same file (add ports + `search` kwargs) | exact |
| `backend/.../composition/live.py` | config | — | same file (replace InMemory chunks; wire RazborRepo) | exact |
| `backend/.../tests_support/in_memory.py` | utility | CRUD | `InMemoryKnowledgeChunkRepository` / `InMemoryIssueRepository` | exact |
| `supabase-integration/.../knowledge_chunk_repository.py` | service | CRUD | `supabase-integration/.../material_repository.py` | exact |
| `supabase-integration/.../razbor_repository.py` | service | CRUD | `material_repository.py` + `issue_repository.py` list | exact |
| `supabase-integration/.../__init__.py` | config | — | same file (export adapters) | exact |
| `web/src/services/knowledgeApi.js` | service | request-response | `web/src/services/contentApi.js` | exact |
| `web/src/services/razboryApi.js` | service | request-response | `contentApi.js` (list + NOT_FOUND detail) + blob download | role-match |
| `web/src/pages/KnowledgePage.jsx` | component | request-response | same file (evolve Submit/chips/API) | exact |
| `web/src/pages/RazboryListPage.jsx` | component | request-response | `ArchivePage.jsx` (list/empty/ServiceUnavailable) | exact |
| `web/src/pages/RazborPage.jsx` | component | request-response | `MaterialPage.jsx` (TOC/markdown/soft 404) | exact |
| `web/src/components/ChronologyItem.jsx` | component | transform | design-frontend `razbory.html` chronology-item + Archive list row | role-match |
| `web/src/components/MaterialListRow.jsx` | component | transform | same file (link by `slug`, optional cover null) | exact |
| `web/src/App.jsx` | config | — | same file (add `/razbory` routes) | exact |
| `web/src/components/AppShell.jsx` | component | — | same file (nav «Разборы») | exact |
| `web/src/data/mock.js` | config | — | existing materials/voting mock blocks | exact |
| `tests/unit/test_search_knowledge.py` | test | request-response | same file (extend role/empty/dedupe/offset) | exact |
| `tests/unit/test_http_knowledge_search.py` | test | request-response | `tests/unit/test_http_materials.py` | exact |
| `tests/unit/test_http_razbory.py` | test | request-response | `test_http_materials.py` + `test_http_issues.py` | exact |
| `tests/unit/test_razbor_use_cases.py` | test | transform | `test_get_material_for_reader.py` | exact |
| `tests/web-app.spec.js` (+ razbory specs) | test | request-response | same file knowledge blocks + Archive/Material e2e | exact |

## Pattern Assignments

### `backend/src/backend/domain/razbor.py` (model, transform)

**Analog:** `backend/src/backend/domain/material.py`

**Imports / Enum + frozen entity** (lines 1–32):
```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MaterialStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"


@dataclass(frozen=True)
class Material:
    id: int
    slug: str
    title: str
    # ...
    status: MaterialStatus
    body_markdown: str
```

**Copy for Razbor:** `RazborStatus(str, Enum)` with `ANNOUNCEMENT = "announcement"`, `PUBLISHED = "published"` matching schema enum; frozen `Razbor` with `id`, `title`, `body_markdown`, `meeting_at`, `status`, `notebook_path`, `created_at`. No FastAPI/Pydantic in domain. Optional view field `content_kind` may live on HTTP DTO / use-case result, not necessarily on entity.

---

### `backend/src/backend/domain/knowledge.py` (model, transform)

**Analog:** same file — keep `KnowledgeHit.score` for ranking; **omit from HTTP JSON** (D-59).

**Core pattern** (lines 20–26):
```python
@dataclass(frozen=True)
class KnowledgeHit:
    material_id: int
    material_slug: str
    chunk_index: int
    snippet: str
    score: float
```

**HTTP mapping:** route response uses material presentation fields + `snippet` only — never serialize `score`.

---

### `backend/src/backend/domain/errors.py` (model, request-response)

**Analog:** same file

**Not-found / validation** (lines 1–19):
```python
class DomainError(Exception):
    """Base domain error."""


class MaterialNotFoundError(DomainError):
    def __init__(self, material_id: int | str) -> None:
        super().__init__(f"material {material_id} not found")
        self.material_id = material_id


class MaterialValidationError(DomainError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
```

**Add:** `RazborNotFoundError`, `KnowledgeQueryValidationError` (blank/overlong `q`), optionally `NotebookNotAvailableError` / path escape → map in route to 404/400. Keep `PersistenceError` → HTTP 503.

---

### `backend/src/backend/application/ports/knowledge_chunk_repository.py` (service, CRUD)

**Analog:** same file — extend Protocol

**Current port** (lines 8–11):
```python
class KnowledgeChunkRepository(Protocol):
    def replace_for_material(self, material_id: int, chunks: list[KnowledgeChunk]) -> list[KnowledgeChunk]: ...

    def list_all(self) -> list[KnowledgeChunk]: ...
```

**Add `search(...)`** (from RESEARCH; keep `list_all` for index/tests / in-memory hybrid):
```python
def search(
    self,
    *,
    query_embedding: list[float],
    query_text: str,
    role_filter: str | None,
    limit: int,
    offset: int,
) -> list[KnowledgeHit]: ...
```

In-memory fake may implement `search` by reusing current Python cosine+FTS from `search_knowledge`; live Supabase adapter runs SQL `<=>` + FTS and returns hits (score still domain-only).

---

### `backend/src/backend/application/ports/query_embedder.py` (service, transform)

**Analog:** Protocol style from `material_repository.py` + dim contract from `data-collection/src/data_collection/dto/foundry.py`

**Port shape:**
```python
class QueryEmbedder(Protocol):
    def embed(self, text: str) -> list[float]: ...
```

**Dim constraint** (`foundry.py` lines 5–6, 52–53): length **1024**. Deterministic stub for Phase 4; unit-test vector length.

---

### `backend/src/backend/application/ports/razbor_repository.py` (service, CRUD)

**Analog:** `backend/src/backend/application/ports/issue_repository.py`

**List / get Protocol** (lines 10–21):
```python
class IssueRepository(Protocol):
    def get_latest_published(self) -> Issue | None: ...

    def get_by_number(self, number: int) -> Issue | None: ...

    def list_past_published(self) -> list[Issue]: ...
```

**Copy for RazborRepository:** `list_for_reader() -> list[Razbor]` (order `meeting_at DESC NULLS LAST`, then `created_at DESC`); `get(razbor_id: int) -> Razbor | None`. Notebook path resolution can be repo method or separate `NotebookStorage` port.

---

### `backend/src/backend/application/use_cases/search_knowledge.py` (service, request-response)

**Analog:** same file — evolve blank guard, material dedupe, offset/limit

**Imports + hybrid scoring** (lines 1–64):
```python
from backend.application.ports.knowledge_chunk_repository import KnowledgeChunkRepository
from backend.application.ports.material_repository import MaterialRepository
from backend.domain.knowledge import KnowledgeHit

def search_knowledge(
    *,
    materials: MaterialRepository,
    chunks: KnowledgeChunkRepository,
    query_embedding: list[float],
    query_text: str,
    role_filter: str | None,
    limit: int = 5,
) -> list[KnowledgeHit]:
    # ... list_all + cosine 0.7 / FTS 0.3 ...
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]
```

**Evolve:**
1. `q = query_text.strip()`; empty → raise `KnowledgeQueryValidationError` (KNOW-01).
2. Prefer `chunks.search(...)` when adapter supports SQL; in-memory path may keep list_all hybrid inside fake `search`.
3. Dedupe by `material_id` (best score wins) **before** offset/limit.
4. Add `offset`; return enough for `has_more` (fetch `limit+1` or return count flag from use-case wrapper).

---

### `backend/src/backend/application/use_cases/list_razbors.py` (service, request-response)

**Analog:** `backend/src/backend/application/use_cases/list_archive_issues.py`

**Core pattern** (lines 1–11):
```python
def list_archive_issues(issues: IssueRepository) -> list[Issue]:
    """Return published issues excluding the latest-published current issue."""
    return issues.list_past_published()
```

**Copy:** thin `list_razbors(repo) -> list[Razbor]` — ordering lives in repository; use-case does not import supabase.

---

### `backend/src/backend/application/use_cases/get_razbor.py` (service, request-response)

**Analog:** `backend/src/backend/application/use_cases/get_material_for_reader.py`

**Core pattern** (lines 1–14):
```python
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus


def get_material_for_reader(repo: MaterialRepository, slug: str) -> Material:
    material = repo.get_by_slug(slug)
    if material is None or material.status != MaterialStatus.READY:
        raise MaterialNotFoundError(slug)
    return material
```

**Copy for get_razbor:** missing id → `RazborNotFoundError`. Both `announcement` and `published` are valid list/detail statuses (announcement is not a soft-404). Compute `content_kind` / `notebook_available` here or in HTTP mapper from body + `notebook_path`.

---

### `backend/src/backend/application/use_cases/download_razbor_notebook.py` (service, file-I/O)

**Analog:** not-found raise from `get_material_for_reader.py`; FileResponse wiring from RESEARCH (no in-repo FileResponse yet).

**Use-case returns safe `Path` (or raises):** missing razbor → NotFound; missing/`None` notebook_path → dedicated error; path must resolve under `NOTEBOOK_ROOT` with containment check (reject `..`).

**Route layer** (RESEARCH sketch — planner implements):
```python
from fastapi.responses import FileResponse

return FileResponse(
    path,
    filename=path.name,
    media_type="application/x-ipynb+json",
    content_disposition_type="attachment",
)
```

---

### `backend/src/backend/interface/http/routes/knowledge.py` (route, request-response)

**Analog:** `issues.py` (auth + list DTO) + `materials.py` (`extra="forbid"`, JWT gate)

**Auth + container require** (`materials.py` 7–14, 45–52, 86–114):
```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from backend.interface.http.deps import get_principal

router = APIRouter(prefix="/materials", tags=["materials"])

def _require_materials(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "materials", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_not_configured",
        )
    return container.materials

@router.get("/{slug}", response_model=MaterialReaderResponse)
def read_material_by_slug(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> MaterialReaderResponse:
    del claims  # auth gate only
    # NotFound → 404 detail=...; PersistenceError → 503
```

**Knowledge-specific:**
- `GET /knowledge/search?q=&role=&limit=&offset=`
- Blank `q` → **400** (`empty_query`); SPA shows «Введите запрос»
- Response model: `{ items: [...], has_more, limit, offset }` — **no `score`**
- Role allowlist: `analyst` | `ds` | omit; never UI labels
- Join ready materials only (adapter / use-case)

---

### `backend/src/backend/interface/http/routes/razbory.py` (route, request-response)

**Analog:** list empty 200 from `issues.py` archive; detail soft 404 from `materials.py`

**Archive list empty honesty** (`issues.py` 179–211):
```python
@archive_router.get("/archive", response_model=ArchiveListResponse)
def read_archive(...):
    archive = list_archive_issues(issues)
    return ArchiveListResponse(
        issues=[ArchiveIssueResponse(...) for issue in archive]
    )
```

**Detail 404** (`materials.py` 102–108):
```python
except MaterialNotFoundError as exc:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="material_not_found",
    ) from exc
```

**Razbory routes:**
- `GET /razbory` → list chronology DTOs (id, title, meeting_at, status label)
- `GET /razbory/{id}` → announcement stub vs published longread fields + `content_kind` + `notebook_available`
- `GET /razbory/{id}/notebook` → `FileResponse` + `get_principal`
- Constant byline: reuse `EDITOR_BYLINE = "Редакция Digest CDS"` from `materials.py` line 19 if schema has no author

---

### `backend/src/backend/composition/live.py` + `container.py` (config)

**Analog:** same files — Phase 3 voting wiring pattern

**live.py today still uses InMemory for chunks** (lines 40–48):
```python
return AppContainer(
    materials=SupabaseMaterialRepository(admin_client),
    chunks=InMemoryKnowledgeChunkRepository(),  # ← replace with SupabaseKnowledgeChunkRepository
    # ...
)
```

**Copy:** construct service_role client only here; add `razbors=SupabaseRazborRepository(admin_client)`; wire `QueryEmbedder` stub; never put secrets in Vite.

**container.py `search` method** (lines 54–69): extend with `offset` / embedder call at HTTP or container edge — embedder is application port, not React.

---

### `supabase-integration/.../knowledge_chunk_repository.py` (service, CRUD)

**Analog:** `supabase-integration/src/supabase_integration/material_repository.py`

**Adapter skeleton** (lines 72–131):
```python
class SupabaseMaterialRepository:
    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def _fetch_one(self, column: str, value: Any) -> Material | None:
        try:
            result = (
                self._client.table("materials")
                .select("...")
                .eq(column, value)
                .limit(1)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"materials fetch by {column} failed: {exc}") from exc
```

**Knowledge adapter:** parameterized hybrid SQL (vector `<=>` + `content_tsv` / `ts_rank_cd`); filter `$role = ANY (m.roles)`; `m.status = 'ready'`; map SDK errors → `PersistenceError`. Prefer raw SQL / RPC if PostgREST cannot express hybrid fusion cleanly — still only inside this adapter.

---

### `supabase-integration/.../razbor_repository.py` (service, CRUD)

**Analog:** same material/issue adapter pattern — `table("razbors").select(...).order(...)`.

**RLS note (RESEARCH pitfall 7):** no SELECT policy for authenticated browser — **service_role only** via composition (same as issues/materials).

---

### `backend/src/backend/tests_support/in_memory.py` (utility, CRUD)

**Analog:** `InMemoryKnowledgeChunkRepository` (lines 104–130)

```python
class InMemoryKnowledgeChunkRepository:
    def __init__(self) -> None:
        self._chunks: list[KnowledgeChunk] = []

    def list_all(self) -> list[KnowledgeChunk]:
        return list(self._chunks)
```

**Add:** `search(...)` on chunks fake; new `InMemoryRazborRepository`; `StubQueryEmbedder` returning length-1024 lists. Follow `InMemoryIssueRepository` seed-list constructor style.

---

### `web/src/services/knowledgeApi.js` (service, request-response)

**Analog:** `web/src/services/contentApi.js`

**Mocks gate + auth + error codes** (lines 1–22, 108–133, 157–199):
```javascript
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'

export class ContentApiError extends Error {
  constructor(message, { code = 'CONTENT_FAILED', retryable = true } = {}) {
    super(message)
    this.name = 'ContentApiError'
    this.code = code
    this.retryable = retryable
  }
}

async function authHeaders(accessToken) {
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new ContentApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }
  return { Authorization: `Bearer ${token}` }
}

if (isMocksEnabled()) { /* return mock DTO */ }
// live: fetch(`${apiBase()}/...`, { headers })
// 401 → UNAUTHORIZED; network → NETWORK; never silent mock fallback
```

**Knowledge:** `searchKnowledge({ q, role, limit, offset })` → `GET /knowledge/search?...`. Map 400 empty_query for inline validation. Playwright harness flags for empty hits / fail-next (mirror `armEmptyArchive` / `armFailNextContentFetch`).

---

### `web/src/services/razboryApi.js` (service, request-response)

**Analog:** `contentApi.js` list + soft 404 detail

**NOT_FOUND mapping** (lines 238–278, 348–352):
```javascript
if (response.status === 404) {
  throw new ContentApiError('Материал не найден.', {
    code: 'NOT_FOUND',
    retryable: false,
  })
}
```

**Copy:** `fetchRazbory()`, `fetchRazbor(id)`, `downloadRazborNotebook(id)` (blob/`response.blob()` + object URL, or navigate with Bearer — prefer fetch blob so failures can toast «Не удалось скачать»). Same `isMocksEnabled()` cutover.

---

### `web/src/pages/KnowledgePage.jsx` (component, request-response)

**Analog:** same file — rewrite behavior; keep visual tokens

**Current client filter + load-more** (lines 9–41, 106–149):
```javascript
const PAGE_SIZE = 3
// filterMaterials(materials, filters) — REPLACE with knowledgeApi
function reset() {
  setFilters(initialFilters)  // D-65: reset must clear ONLY role, keep query
}
```

**Evolve to:**
- Submit / Enter + visible «Найти» (D-57) — **not** onChange search
- Role chips Analyst / DS / «Все» (D-62); drop tag/format/topic selects (D-63)
- Role chip change re-runs search if query non-empty (D-64)
- Pre-search: neutral empty + topic **hint** chips that fill query (D-60)
- Zero-hit: «Ничего не нашли» + «Сбросить фильтр» clears role only (D-65)
- `has_more` → «Показать ещё» via API offset (D-61)
- Page GET / search partial failure: ServiceUnavailable vs ErrorPanel+Retry (carry Phase 2–3)
- Hits → `MaterialListRow` with **slug** link + snippet; no scores

**ServiceUnavailable / load pattern** — copy from `ArchivePage.jsx` lines 7–33, 52.

---

### `web/src/pages/RazboryListPage.jsx` (component, request-response)

**Analog:** `web/src/pages/ArchivePage.jsx`

**List / empty / splash** (lines 7–64):
```jsx
const [status, setStatus] = useState('loading')
fetchArchive()
  .then((dto) => { setIssues(dto.issues ?? []); setStatus('ready') })
  .catch(() => setStatus('error'))

{status === 'error' ? <ServiceUnavailable onRetry={reload} /> : null}
{status === 'ready' && issues.length === 0 ? (
  <div data-testid="archive-empty">
    <h2>...</h2>
    <Link to="/">К текущему выпуску →</Link>
  </div>
) : null}
```

**Razbory empty (D-69):** copy «Разборов пока нет» + **only** CTA `Link to="/voting"` («К голосованию»). List rows = chronology (date/status overline, title, byline, «Читать») — not MaterialListRow covers. Announcement shows «Анонс».

---

### `web/src/pages/RazborPage.jsx` (component, request-response)

**Analog:** `web/src/pages/MaterialPage.jsx`

**Soft 404 + TOC + markdown** (lines 57–93, 113–131, 135–190):
```jsx
fetchMaterial(slug)
  .catch((err) => {
    if (err instanceof ContentApiError && err.code === 'NOT_FOUND') {
      setNotFound(true)
      setStatus('ready')
      return
    }
    setStatus('error')
  })

// Soft 404 CTA → «К списку разборов» (/razbory) instead of issue/archive

const headings = extractMarkdownHeadings(material.body_markdown ?? '')
<nav className="sticky top-24 hidden max-h-[70vh] w-56 shrink-0 overflow-auto lg:block" ...>
<Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug, rehypeSanitize]}>
```

**Announcement (D-68):** stub only (title/date/status) — **no** empty prose/TOC.
**Published:** sticky TOC (`lg:`) + notebook strip top **and** bottom (design-frontend `razbor.html`); missing notebook → disabled + «Notebook скоро будет»; download fail → toast.
**Metrics (D-73):** if `content_kind === 'quality'` render «Качество» block/TOC entry; if `overview` show hero badge «Обзор» and **omit** empty metrics section (same honesty as dek/related conditionals on MaterialPage 159–220).

**Toast pattern:** `VotingPage.jsx` `setToast` + fade (~lines 90, 145–150, 373–379).

---

### `web/src/components/ChronologyItem.jsx` (component, transform)

**Analog:** design-frontend `pages/razbory.html` (lines 74–77) + Archive list link styling

```html
<article class="chronology-item">
  <span class="text-overline chronology-item__date">14 апреля 2026 · предстоящий</span>
  <h2 class="chronology-item__title">RAG в корпоративной среде</h2>
  <p class="text-body-sm text-secondary chronology-item__byline">...</p>
</article>
```

**React:** optional extract; else inline in `RazboryListPage`. Link to `/razbory/:id`. Byline: constant «Редакция Digest CDS» until author join exists.

---

### `web/src/components/MaterialListRow.jsx` (component, transform)

**Analog:** same file — fix slug pitfall

**Current** (lines 3–6):
```jsx
<Link to={`/materials/${material.id}`} ...>
```

**Must use** `material.slug` (or map API hit so `id` is slug only in mocks). Support `cover` null degradation. Keep `snippet` + tags.

---

### `web/src/App.jsx` + `AppShell.jsx` (config / component)

**Analog:** same files

**Routes** (`App.jsx` 19–33):
```jsx
<Route path="knowledge" element={<KnowledgePage />} />
<Route path="materials/:id" element={<MaterialPage />} />
// ADD:
// <Route path="razbory" element={<RazboryListPage />} />
// <Route path="razbory/:id" element={<RazborPage />} />
```

**Nav** (`AppShell.jsx` 60–71): add `NavLink to="/razbory"` label **«Разборы»** (D-66). Keep plural collection convention.

---

### Tests

| New test file | Analog | Copy |
|---------------|--------|------|
| `tests/unit/test_http_knowledge_search.py` | `test_http_materials.py` | JWT mint (`_mint`, `_client`, ES256 JWK), `build_in_memory_container`, assert no `score` in JSON, 400 blank, role filter |
| `tests/unit/test_http_razbory.py` | `test_http_materials.py` + `test_http_issues.py` | list empty 200; detail 404; notebook FileResponse headers; announcement stub fields |
| `tests/unit/test_razbor_use_cases.py` | `test_get_material_for_reader.py` | content_kind quality vs overview; missing → NotFound |
| Extend `test_search_knowledge.py` | same | role empty honesty (no cross-role tops); material dedupe; offset |
| Playwright knowledge | `tests/web-app.spec.js` lines 228–265 | rewrite tag facet → Submit/Enter + chips + reset-role-only |
| Playwright razbory | Archive/Material e2e patterns in same suite | empty CTA `/voting`; TOC; notebook disabled; Обзор vs Качество |

**HTTP test client pattern** (`test_http_materials.py` 80–98):
```python
settings = Settings(...)
app = create_app(
    settings,
    container=build_in_memory_container(materials=materials),
    signing_key_resolver=lambda _token: signing_jwk,
)
return TestClient(app)
```

## Shared Patterns

### Authentication (JWT gate)
**Source:** `backend/src/backend/interface/http/deps.py` via `get_principal` — used in `materials.py` / `issues.py`
**Apply to:** `knowledge.py`, `razbory.py` (all GETs including notebook)
```python
claims: AccessTokenClaims = Depends(get_principal)
del claims  # auth gate only; content is reader-shared
```

### Error → HTTP mapping
**Source:** `materials.py` 102–113; `errors.py`
**Apply to:** all new routes
| Domain | HTTP |
|--------|------|
| `*NotFoundError` | 404 + stable `detail` string |
| `KnowledgeQueryValidationError` | 400 |
| `PersistenceError` | 503 |
| Missing container port | 503 `*_not_configured` |

### Frontend mock cutover
**Source:** `contentApi.js` `isMocksEnabled()`
**Apply to:** `knowledgeApi.js`, `razboryApi.js`
- Never silent fallback to mocks after live failure (D-20/D-56 carry-forward)
- Page GET fail → `ServiceUnavailable`; search/mutation partial → banner/ErrorPanel + Retry

### Soft 404 UX
**Source:** `MaterialPage.jsx` + `contentApi.js` `NOT_FOUND`
**Apply to:** unknown razbor id → «К списку разборов» (`/razbory`)

### Honesty rendering
**Source:** `MaterialPage.jsx` conditional dek/related; Phase 2 CONTEXT
**Apply to:** announcement stub (no fake longread); metrics only when `content_kind=quality`; no score UI; no ML tops on zero-hit filter

### Composition-only secrets
**Source:** `live.py` docstring + lines 20–32
**Apply to:** Supabase knowledge/razbor adapters — service_role never in Vite

### Embedding dimension
**Source:** `data-collection/.../foundry.py` `EMBEDDING_DIM = 1024`; schema `vector(1024)`
**Apply to:** seed chunks + `QueryEmbedder` stub + unit length asserts

### Sticky TOC
**Source:** `MaterialPage.jsx` lines 45–48 + `utils/markdownToc.js`
**Apply to:** published razbor only; same `lg:` breakpoint

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/.../ports/notebook_storage.py` (optional) | service | file-I/O | No Path/FileResponse helper in repo yet — use RESEARCH FileResponse + Path.resolve containment; may inline in use-case if port not extracted |

*(Hybrid SQL itself has domain scoring analog in `search_knowledge.py` + schema indexes; only the notebook binary download path is greenfield.)*

## Metadata

**Analog search scope:** `backend/src/backend/{domain,application,interface,composition,tests_support}`, `supabase-integration/src`, `web/src/{pages,services,components,utils}`, `tests/unit`, `design-frontend/pages`, `data-collection/src`
**Files scanned:** ~55 primary + design-frontend references
**Pattern extraction date:** 2026-09-20
**Strongest cross-cutting analogs:** `materials.py` + `MaterialPage.jsx` (reader detail), `issues.py` + `ArchivePage.jsx` (list/empty), `contentApi.js` (mock/JWT), `search_knowledge.py` (hybrid scoring), `live.py` (service_role wiring)
