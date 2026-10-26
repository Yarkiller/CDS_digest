# Phase 2: Issue, Materials & Archive - Pattern Map

**Mapped:** 2026-09-19
**Files analyzed:** 28
**Analogs found:** 26 / 28

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/.../ports/issue_repository.py` | port (Protocol) | CRUD (read) | `backend/.../ports/profile_repository.py` | exact |
| `backend/.../ports/voting_cycle_reader.py` | port (Protocol) | CRUD (read) | `backend/.../ports/ping_recorder.py` | role-match |
| `backend/.../ports/material_repository.py` | port (extend) | CRUD | `backend/.../ports/material_repository.py` | exact (extend) |
| `backend/.../use_cases/get_current_issue.py` | service (use-case) | request-response | `backend/.../use_cases/get_current_user.py` | exact |
| `backend/.../use_cases/get_issue_by_number.py` | service (use-case) | request-response | `backend/.../use_cases/publish_material.py` | role-match |
| `backend/.../use_cases/list_archive_issues.py` | service (use-case) | CRUD (list) | `backend/.../use_cases/search_knowledge.py` | role-match |
| `backend/.../use_cases/get_material_for_reader.py` | service (use-case) | request-response | `backend/.../use_cases/publish_material.py` | exact |
| `backend/.../routes/issues.py` | route / controller | request-response | `backend/.../routes/me.py` | exact |
| `backend/.../routes/materials.py` | route / controller | request-response | `backend/.../routes/me.py` | exact |
| `backend/.../interface/http/app.py` | config | request-response | `backend/.../interface/http/app.py` | exact (extend) |
| `backend/.../composition/container.py` | config / DI | request-response | `backend/.../composition/container.py` | exact (extend) |
| `backend/.../composition/live.py` | config / DI | request-response | `backend/.../composition/live.py` | exact (extend) |
| `backend/.../tests_support/in_memory.py` | test utility | CRUD | `backend/.../tests_support/in_memory.py` | exact (extend) |
| `supabase-integration/.../issue_repository.py` | adapter / service | CRUD (read) | `supabase-integration/.../profile_repository.py` | exact |
| `supabase-integration/.../material_repository.py` | adapter / service | CRUD (read) | `supabase-integration/.../profile_repository.py` | exact |
| `supabase-integration/.../__init__.py` | config | — | `supabase-integration/.../__init__.py` | exact (extend) |
| `supabase-integration/migrations/002_phase2_issue_seed.sql` | migration / seed | file-I/O | `supabase-integration/migrations/001_initial_schema.sql` | partial |
| `web/src/services/contentApi.js` | service | request-response | `web/src/services/meApi.js` | exact |
| `web/src/pages/ArchivePage.jsx` | component / page | request-response | `web/src/pages/KnowledgePage.jsx` | role-match |
| `web/src/pages/IssuePage.jsx` | component / page | request-response | `web/src/pages/IssuePage.jsx` + `PlatformProofBanner.jsx` | exact (wire) |
| `web/src/pages/MaterialPage.jsx` | component / page | request-response | `web/src/pages/MaterialPage.jsx` | exact (extend) |
| `web/src/components/ServiceUnavailable.jsx` | component | request-response | `web/src/components/ErrorPanel.jsx` + `PlatformProofBanner.jsx` | role-match |
| `web/src/utils/markdownToc.js` | utility | transform | `web/src/utils/filters.js` | role-match |
| `web/src/App.jsx` | config / route | request-response | `web/src/App.jsx` | exact (extend) |
| `web/src/components/AppShell.jsx` | component | request-response | `web/src/components/AppShell.jsx` | exact (extend) |
| `web/public/bad_gateway.png` | config / asset | file-I/O | `web/public/covers/*` (static Vite assets) | role-match |
| `docs/agents/local-platform-runbook.md` | config / docs | — | `docs/agents/local-platform-runbook.md` §4 seed | exact (extend) |
| `tests/unit/test_http_issues.py` (+ materials / use-cases) | test | request-response | `tests/unit/test_http_me.py` | exact |
| `tests/web-app.spec.js` | test | request-response | `tests/web-app.spec.js` | exact (extend) |
| `web/package.json` (markdown deps) | config | — | `web/package.json` | exact |

## Pattern Assignments

### `backend/src/backend/application/ports/issue_repository.py` (port, CRUD-read)

**Analog:** `backend/src/backend/application/ports/profile_repository.py`

**Imports + Protocol shape** (lines 1–13):
```python
from __future__ import annotations

from typing import Protocol

from backend.domain.current_user import CurrentUser


class ProfileRepository(Protocol):
    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser: ...

    def set_display_name(self, user_id: str, display_name: str) -> CurrentUser: ...
```

**Copy for planner:** Same `Protocol` + `from __future__ import annotations` + domain DTO return types. For issues, define methods such as `get_latest_published()`, `get_by_number(number: int)`, `list_published_excluding(current_id: int)` returning an `Issue` / read-model DTO (new domain dataclass or application DTO — mirror `CurrentUser` frozen dataclass style in `domain/current_user.py`).

**Secondary analog:** `material_repository.py` for multi-method read/write Protocol style (lines 8–11).

---

### `backend/src/backend/application/ports/voting_cycle_reader.py` (port, CRUD-read)

**Analog:** `backend/src/backend/application/ports/ping_recorder.py`

**Protocol pattern** (lines 1–15):
```python
from __future__ import annotations

from typing import Protocol


class PingRecorder(Protocol):
    def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        payload: dict,
    ) -> str: ...
```

**Copy for planner:** Narrow read-only Protocol (e.g. `get_active_cycle() -> VotingCycleStub | None`). Keyword-only args if useful; no SDK imports. Alternatively fold into `IssueRepository.get_current_with_cycle()` — if so, still keep cycle selection logic in use-case, not adapter.

---

### `backend/src/backend/application/ports/material_repository.py` (port extend, CRUD)

**Analog:** itself — extend in place

**Current surface** (lines 8–11):
```python
class MaterialRepository(Protocol):
    def get(self, material_id: int) -> Material | None: ...

    def save(self, material: Material) -> Material: ...
```

**Copy for planner:** Add `get_by_slug(slug: str) -> Material | None` (and optionally `list_related_ready(material_id: int) -> list[...]`). Keep `get`/`save` for publish/index. Domain entity already has `slug`, `body_markdown`, `dek`, `tags`, `related_material_ids` — see `domain/material.py` lines 16–32.

---

### `backend/src/backend/application/use_cases/get_current_issue.py` (use-case, request-response)

**Analog:** `backend/src/backend/application/use_cases/get_current_user.py`

**Thin orchestration** (lines 1–11):
```python
from backend.application.ports.profile_repository import ProfileRepository
from backend.domain.auth_claims import AccessTokenClaims
from backend.domain.current_user import CurrentUser


def get_current_user(profiles: ProfileRepository, claims: AccessTokenClaims) -> CurrentUser:
    return profiles.get_or_upsert(claims.sub, claims.email)
```

**Copy for planner:** Pure function; ports injected as args; no FastAPI/Supabase. For current issue: call `issues.get_latest_published()`; optionally attach cycle via `VotingCycleReader`; return `None` or empty DTO when no published row (D-24 empty → SPA «выпуск готовится»).

---

### `backend/.../use_cases/get_issue_by_number.py` / `get_material_for_reader.py` (use-case, request-response)

**Analog:** `backend/src/backend/application/use_cases/publish_material.py`

**Not-found + domain error** (lines 10–16):
```python
def publish_material(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    published_at = now or datetime.now(timezone.utc)
    ready = material.as_ready(published_at)
    return repo.save(ready)
```

**Domain errors** (`domain/errors.py` lines 5–8):
```python
class MaterialNotFoundError(DomainError):
    def __init__(self, material_id: int) -> None:
        super().__init__(f"material {material_id} not found")
        self.material_id = material_id
```

**Copy for planner:**
- `get_material_for_reader(repo, slug)`: `get_by_slug` → if missing **or** `status != READY` → raise `MaterialNotFoundError` (or slug-aware variant) so HTTP always 404 (D-39 / no draft leak).
- `get_issue_by_number`: missing/unpublished → domain not-found (soft 404 at HTTP).
- Reuse `_draft()` factory pattern from `tests/unit/test_publish_and_index.py` lines 14–34 for unit fixtures (`body_markdown` with `##` headings).

---

### `backend/.../use_cases/list_archive_issues.py` (use-case, list)

**Analog:** `backend/src/backend/application/use_cases/search_knowledge.py`

**Port-only filtering in use-case** (lines 22–36, 60–61):
```python
def search_knowledge(
    *,
    materials: MaterialRepository,
    chunks: KnowledgeChunkRepository,
    query_embedding: list[float],
    query_text: str,
    role_filter: str | None,
    limit: int = 5,
) -> list[KnowledgeHit]:
    # ... filter/score in use-case, not in UI ...
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]
```

**Copy for planner:** Resolve current via latest published, then list others with `published_at IS NOT NULL` excluding current (D-31). Business rule lives here, not in React.

---

### `backend/src/backend/interface/http/routes/issues.py` & `materials.py` (route, request-response)

**Analog:** `backend/src/backend/interface/http/routes/me.py`

**Imports + Pydantic response + Depends(get_principal)** (lines 7–16, 52–72):
```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from backend.domain.auth_claims import AccessTokenClaims
from backend.interface.http.deps import get_principal

router = APIRouter(tags=["me"])


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    email: str
    role: str
    display_name: str | None = None


@router.get("/me", response_model=CurrentUserResponse, ...)
def read_me(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUserResponse:
    container = request.app.state.container
    if container is None or getattr(container, "profiles", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="profiles_not_configured",
        )
    user = get_current_user(container.profiles, claims)
    return _to_response(user)
```

**Auth dependency** (`deps.py` lines 19–22):
```python
def get_principal(
    request: Request,
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> AccessTokenClaims:
```

**404 mapping** (from RESEARCH / FastAPI — apply at route edge):
```python
from fastapi import HTTPException
# if material is None / MaterialNotFoundError:
raise HTTPException(status_code=404, detail="material_not_found")
```

**Copy for planner:**
| Route | Handler pattern |
|-------|-----------------|
| `GET /issues/current` | `Depends(get_principal)` → use-case → response model; empty current → `200` + empty DTO **or** documented empty shape (prefer 200 + `items: []` / null issue for SPA empty CTA) |
| `GET /issues/{number}` | path int; 404 if missing |
| `GET /archive` | list past only |
| `GET /materials/{slug}` | 404 soft for draft/unknown |

Register routers in `app.py` like `me` (lines 48–49):
```python
app.include_router(health.router)
app.include_router(me.router)
# → app.include_router(issues.router); app.include_router(materials.router)
```

---

### `backend/src/backend/composition/container.py` & `live.py` (DI, request-response)

**Analog:** same files (extend)

**AppContainer fields** (`container.py` lines 24–29):
```python
@dataclass
class AppContainer:
    materials: MaterialRepository
    chunks: KnowledgeChunkRepository
    profiles: ProfileRepository
    pings: PingRecorder
```

**Live wiring** (`live.py` lines 19–44) — **critical gap**:
```python
def build_live_container(settings: Settings) -> AppContainer:
    admin_client = create_service_role_client(
        settings.supabase_url,
        settings.supabase_secret_key,
    )
    return AppContainer(
        materials=InMemoryMaterialRepository(),  # ← REPLACE with SupabaseMaterialRepository
        chunks=InMemoryKnowledgeChunkRepository(),
        profiles=SupabaseProfileRepository(admin_client),
        pings=SupabasePingRecorder(admin_client),
    )
```

**Copy for planner:** Add `issues: IssueRepository` (and optional `voting_cycles: VotingCycleReader`) to `AppContainer` + `build_in_memory_container` + `build_live_container`. Construct Supabase adapters **only** in `live.py` with `service_role` client (same as profiles/pings). Update `test_live_container_wiring.py` assertions for new adapter types.

---

### `backend/src/backend/tests_support/in_memory.py` (test utility, CRUD)

**Analog:** itself — `InMemoryMaterialRepository` / `InMemoryProfileRepository`

**In-memory fake pattern** (lines 50–91):
```python
class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, CurrentUser] = {}

    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser:
        ...

class InMemoryMaterialRepository:
    def __init__(self, materials: list[Material] | None = None) -> None:
        self._by_id: dict[int, Material] = {m.id: m for m in (materials or [])}

    def get(self, material_id: int) -> Material | None:
        return self._by_id.get(material_id)
```

**Copy for planner:** Add `InMemoryIssueRepository` with seedable published issues + items; extend material fake with `_by_slug` / `get_by_slug`. Keep dict-backed, no I/O.

---

### `supabase-integration/.../issue_repository.py` & `material_repository.py` (adapter, CRUD-read)

**Analog:** `supabase-integration/src/supabase_integration/profile_repository.py`

**Imports + client Protocol + PersistenceError boundary** (lines 1–60):
```python
from backend.domain.current_user import CurrentUser
from backend.domain.errors import PersistenceError

class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...

class SupabaseProfileRepository:
    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser:
        try:
            existing = (
                self._client.table("profiles")
                .select("id,email,role,display_name")
                .eq("id", user_id)
                .execute()
            )
            rows = getattr(existing, "data", None) or []
            ...
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise PersistenceError(f"profiles get_or_upsert failed: {exc}") from exc
```

**Secondary analog:** `ping_recorder.py` for insert/select + missing-row → `PersistenceError`.

**Copy for planner:**
- Tables: `digest_issues`, `digest_issue_items`, `materials`, `material_tags`, `material_relations`, `voting_cycles`.
- Current issue query: `.not_.is_("published_at", "null").order("published_at", desc=True).limit(1)`.
- Map SDK exceptions → `PersistenceError` only at adapter boundary.
- Export from `__init__.py` like `SupabaseProfileRepository` (lines 14–19).

**Schema columns to map** (`001_initial_schema.sql` 124–130, 184–189):
- `digest_issues`: `number`, `period_label`, `title`, `published_at`
- `voting_cycles`: `opens_at`, `closes_at`, `status` (`open`|`closed`)

---

### `supabase-integration/migrations/002_phase2_issue_seed.sql` (seed, file-I/O)

**Analog:** schema facts in `001_initial_schema.sql` + narrative in `web/src/data/mock.js`

**No existing seed file** — closest patterns:
1. Table/constraint definitions in migration (do not alter schema for `cover_url` / `is_current` — D-24/D-26).
2. Content source: `mock.js` `currentIssue` (№14) + `materials` with `id` as **slug** (e.g. `rag-systems`).
3. Runbook tone: `docs/agents/local-platform-runbook.md` §4 — shared VM, no reckless resets, document apply-once.

**Copy for planner:** Idempotent `INSERT … ON CONFLICT (number) DO UPDATE` / `ON CONFLICT (slug) DO UPDATE`; seed **two** published issues + one `voting_cycles` row; fixed slugs matching Playwright (`rag-systems`). No `TRUNCATE`/`DELETE`. Document in runbook (select/insert only via MCP).

---

### `web/src/services/contentApi.js` (service, request-response)

**Analog:** `web/src/services/meApi.js` (primary); harness pattern also in `votingApi.js`

**Typed error + mocks gate + Bearer fetch** (lines 3–86):
```javascript
export class MeApiError extends Error {
  constructor(message, { code = 'ME_FAILED', retryable = true } = {}) {
    super(message)
    this.name = 'MeApiError'
    this.code = code
    this.retryable = retryable
  }
}

function useMocks() {
  return import.meta.env.VITE_USE_MOCKS !== 'false'
}

function apiBase() {
  return (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
}

export async function fetchMe(accessToken) {
  if (failNextFetch) { /* armFailNext harness */ }
  if (useMocks()) { /* return mock DTO — never as fallback after live failure */ }
  const token = accessToken ?? (await getAccessToken())
  let response
  try {
    response = await fetch(`${apiBase()}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new MeApiError('…', { code: 'NETWORK', retryable: true })
  }
  if (response.status === 401) {
    throw new MeApiError('…', { code: 'UNAUTHORIZED', retryable: false })
  }
  if (!response.ok) {
    throw new MeApiError('…', { code: 'NETWORK', retryable: true })
  }
  return response.json()
}
```

**Prefer shared gate:** `isMocksEnabled()` from `authEnv.js` lines 6–12 (handles empty/`undefined` as true — D-09/D-20).

**Copy for planner:**
- `ContentApiError` with `code: 'NETWORK' | 'NOT_FOUND' | 'UNAUTHORIZED'`, `retryable`.
- Functions: `fetchCurrentIssue`, `fetchIssueByNumber`, `fetchArchive`, `fetchMaterial(slug)`.
- Live 404 material → `NOT_FOUND` / `retryable: false` (soft editorial UI).
- Network/5xx → `NETWORK` / `retryable: true` (splash + Retry) — **never** catch and return `mock.js`.
- `armFailNextContentFetch()` for Playwright PLAT-07 (mirror `armFailNextMeFetch`).

Mock DTOs should stay shape-compatible with API (map `mock.js` `body[]` → `body_markdown` string for offline path).

---

### `web/src/pages/IssuePage.jsx` (page, request-response)

**Analog:** itself (layout) + load/error from `PlatformProofBanner.jsx`

**Current layout** (IssuePage lines 6–32): typography hero + `EditorialCallout` + `IssueToc`.

**Load + ErrorPanel + Retry** (`PlatformProofBanner.jsx` lines 15–84):
```javascript
async function loadMe() {
  setError(null)
  try {
    const token = await getAccessToken()
    const user = await fetchMe(token)
    setMe(user)
  } catch (err) {
    setError({
      message: err instanceof MeApiError ? err.message : '…',
      retryable: err instanceof MeApiError ? err.retryable : true,
    })
  }
}
// render ErrorPanel + conditional «Повторить» calling loadMe again
```

**EditorialCallout** (`EditorialCallout.jsx` lines 3–14): omit `actionTo`/`actionLabel` when closed (D-35).

**Copy for planner:**
- Replace `mock.js` imports with `contentApi` (unless mocks inside service).
- Prop/route flag `isCurrent`: callout **only** on `/` (D-34); past `/issues/:number` shares layout without callout.
- Empty materials → «выпуск готовится» + CTA → `/archive` (D-30).
- Voting fields from DTO (`voting_cycle.status`, end date) — no SPA business rules for open/closed.

---

### `web/src/pages/MaterialPage.jsx` (page, request-response)

**Analog:** itself (soft 404 already present lines 8–17)

**Soft 404** (lines 8–17):
```jsx
if (!material) {
  return (
    <section>
      <h1 className="font-display text-3xl font-semibold">Материал не найден</h1>
      <p className="mt-3 text-ink-2">Проверьте ссылку или вернитесь к выпуску.</p>
      <Link to="/" className="mt-6 inline-flex text-accent">← К выпуску</Link>
    </section>
  )
}
```

**Copy for planner:**
- Fetch by slug (`useParams().id` stays; value = slug).
- Replace `body.map` paragraphs with `react-markdown` + `remark-gfm` + `rehype-slug` + `rehype-sanitize` (RESEARCH stack).
- Hide dek when empty (D-36); tags/related only if API returns data (D-37).
- Soft 404: **no** `bad_gateway.png` (D-39). Load failure: splash component, not this branch.
- TOC: headings via `markdownToc.js` + anchor links matching `rehype-slug` ids.
- Keep Playwright selectors: heading «материал не найден», link «к выпуску», URL `/materials/rag-systems`.

---

### `web/src/pages/ArchivePage.jsx` (page, request-response)

**Analog:** `KnowledgePage.jsx` (list + empty recovery) + IssuePage typography

**Empty recovery pattern** (`tests/web-app.spec.js` / Knowledge empty heading «ничего не нашли»).

**Copy for planner:** New page under RequireAuth shell; list past issues (cards/links to `/issues/:number`); empty → CTA «К текущему выпуску» → `/` (D-30); always show link «К текущему выпуску» on archive (D-28). Do **not** copy design-frontend «текущий» badge inside archive (D-31 pitfall).

---

### `web/src/components/ServiceUnavailable.jsx` (component, request-response)

**Analog:** `ErrorPanel.jsx` + Retry button from `PlatformProofBanner.jsx`

**ErrorPanel** (lines 1–25): `role="alert"`, title/message, optional dismiss — **no status codes**.

**Copy for planner:** Wrapper showing `/bad_gateway.png` (after move to `web/public/`) + fixed friendly copy («Не удалось загрузить…») + Retry callback. Never render HTTP codes/stacktraces (D-22/D-23). Can compose `ErrorPanel` or be standalone — CONTEXT discretion.

---

### `web/src/utils/markdownToc.js` (utility, transform)

**Analog:** `web/src/utils/filters.js` — pure functions, no React

```javascript
export function filterMaterials(items, { query = '', ... } = {}) { ... }
export function padIssueNumber(position) {
  return String(position).padStart(2, '0')
}
```

**Copy for planner:** Export pure `extractMarkdownHeadings(markdown) -> { id, text, level }[]` aligned with `rehype-slug` algorithm (or document shared slug helper). Unit-testable without DOM.

---

### `web/src/App.jsx` & `AppShell.jsx` (routing / nav)

**Analog:** themselves

**Routes** (`App.jsx` lines 14–26):
```jsx
<Route element={<RequireAuth><AppShell /></RequireAuth>}>
  <Route index element={<IssuePage />} />
  <Route path="voting" element={<VotingPage />} />
  <Route path="knowledge" element={<KnowledgePage />} />
  <Route path="materials/:id" element={<MaterialPage />} />
  {/* ADD: archive, issues/:number */}
</Route>
```

**Nav** (`AppShell.jsx` lines 60–68): add `NavLink to="/archive"` «Архив» beside Выпуск / База / Голосование.

**IssueToc links** already use `/materials/${item.id}` (`IssueToc.jsx` line 10) — keep slug as id.

---

### Tests

**HTTP unit analog:** `tests/unit/test_http_me.py`

**JWT harness** (lines 31–90): mint ES256 token → `TestClient` + `create_app` + `signing_key_resolver` → assert 401 without auth, 200 with corporate JWT.

**Copy for planner:** Same `_mint` / `_app_bundle` helpers for `GET /issues/current`, `/archive`, `/materials/{slug}` — 401 without Bearer; 404 for draft/unknown slug; archive excludes current.

**Use-case unit analog:** `tests/unit/test_publish_and_index.py` — in-memory repo + domain fixtures.

**E2E analog:** `tests/web-app.spec.js` lines 4–12, 99–105 — extend for archive nav, empty states, markdown TOC, splash Retry (`armFailNext` like meApi harness).

**Live wiring:** extend `test_live_container_wiring.py` when Supabase material/issue adapters replace in-memory.

---

## Shared Patterns

### Authentication (JWT on all content GETs)
**Source:** `backend/src/backend/interface/http/deps.py` + `routes/me.py`  
**Apply to:** `issues.py`, `materials.py`

```python
claims: AccessTokenClaims = Depends(get_principal)
```

SPA: `Authorization: Bearer ${token}` via `getAccessToken()` from `authApi.js` (as in `meApi.js`).

### Mock / live cutover (D-20)
**Source:** `web/src/services/authEnv.js` + `meApi.js`  
**Apply to:** `contentApi.js`, all content pages

```javascript
export function isMocksEnabled() {
  const value = import.meta.env.VITE_USE_MOCKS
  return value === undefined || value === '' || value === 'true'
}
```

Never silent mock fallback after live failure (D-21).

### Error handling
| Layer | Pattern | Source |
|-------|---------|--------|
| Adapter | `except Exception → PersistenceError` | `profile_repository.py` |
| Use-case | `MaterialNotFoundError` / domain errors | `publish_material.py` |
| HTTP | `HTTPException` 401/403/404/503 | `me.py` / `deps.py` |
| SPA | Typed `*ApiError` + `retryable` + ErrorPanel/Retry | `meApi.js` / `PlatformProofBanner.jsx` |
| Soft 404 | Editorial empty, no splash art | `MaterialPage.jsx` |
| Hard load fail | Splash `bad_gateway.png` + Retry | new ServiceUnavailable; D-22 |

### Ports & Adapters / composition
**Source:** `architecture.mdc` + `composition/live.py`  
**Apply to:** all backend + supabase-integration files

- Ports = `Protocol` in `application/ports/`
- Adapters in `supabase-integration/`
- Clients only in `composition/live.py` (`service_role`)
- FE only via `web/src/services/`

### TDD
**Source:** `.cursor/rules/tdd.mdc`  
Failing pytest/Playwright first; Wave 0 tests listed in RESEARCH Validation Architecture.

### Editorial UI honesty
**Source:** CONTEXT D-36–D-39 + existing Material soft-404  
Omit empty dek/tags/related; never fabricate; draft → soft 404.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `supabase-integration/migrations/002_phase2_issue_seed.sql` | seed | file-I/O | No checked-in seed SQL yet; only schema migration + mock.js narrative + runbook seed prose |
| `web/src/utils/markdownToc.js` (+ react-markdown stack) | utility | transform | No markdown rendering or heading TOC util in repo; use RESEARCH npm stack + filters.js purity style |

## Metadata

**Analog search scope:** `backend/src/backend/`, `supabase-integration/src/`, `web/src/`, `tests/`, `docs/agents/`, `supabase-integration/migrations/`  
**Files scanned:** ~80 (backend 42 py + web 38 jsx/js + supabase 5 + tests 23 + migration/docs)  
**Strong analogs used (top):** `me.py`, `meApi.js`, `profile_repository.py` (port+adapter), `publish_material.py`, `in_memory.py`, `IssuePage.jsx`/`MaterialPage.jsx`, `PlatformProofBanner.jsx`, `test_http_me.py`  
**Pattern extraction date:** 2026-09-19
