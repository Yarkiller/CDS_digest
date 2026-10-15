# Phase 18: Reader-route honesty for draft materials - Pattern Map

**Mapped:** 2026-10-15
**Files analyzed:** 12 (7 production, 5 test) + 2 composition files verified as "no edit"
**Analogs found:** 12 / 12

> Ground rules for this phase (from `18-CONTEXT.md` D-11/D-12, which supersede parts of D-05/D-09):
> - `GET /materials/{slug}` and `get_material_for_reader` stay **byte-identical**. Never the subject of an edit.
> - The email `href` builder `email_render.py` **stays `{base}/materials/{slug}`** (D-11). Only the anchor's `target`/`rel` attributes change. `test_preview_email_html_matches_send_html` and `test_email_render.py` href assertions must NOT be amended.
> - `ready` → reader route is a **client-side** redirect (D-12); the endpoint 404s for non-draft.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/src/backend/application/use_cases/get_material_for_preview.py` (NEW) | use-case (service) | CRUD (read) | `backend/src/backend/application/use_cases/get_material_for_reader.py` | exact (inverted predicate) |
| `backend/src/backend/interface/http/routes/admin.py` (MODIFIED — new `GET /admin/materials/{slug}`) | controller / route | request-response | same file `post_material_ready` (`:302-331`) + `routes/materials.py:97-113` | exact |
| `backend/src/backend/composition/container.py` (VERIFY — likely no edit) | config / wiring | — | `:110-119` materials wiring | n/a — no new port/adapter (research §Don't Hand-Roll) |
| `backend/src/backend/composition/live.py` (VERIFY — likely no edit) | config / wiring | — | `:49` `materials=SupabaseMaterialRepository(admin_client)` | n/a |
| `backend/src/backend/application/use_cases/email_render.py` (MODIFIED — anchor `target`/`rel`) | utility / renderer | transform | same file `render_interstitial_html` (`:17-26`) | exact (self) |
| `web/src/App.jsx` (MODIFIED — new `admin/materials/:id`) | route config | request-response | `web/src/App.jsx:36` (`materials/:id`) | exact |
| `web/src/pages/MaterialPage.jsx` (MODIFIED — `preview` + injected loader) | component | request-response → render | itself (`:57-96`, `:194`, `:206`) | self |
| `web/src/services/adminApi.js` (MODIFIED — new `fetchMaterialPreview`) | service (API client) | request-response | `contentApi.js:317-357` (`fetchMaterial`) + `adminApi.js:234-301` (`fetchShortlist`) | exact |
| `web/src/pages/AdminDigestPage.jsx` (MODIFIED — shortlist link `:994-1000`, iframe `:869-875`) | component | request-response | itself | self |
| `tests/unit/test_get_material_for_preview.py` (NEW) | test (unit, use-case) | — | `tests/unit/test_get_material_for_reader.py` | exact |
| `tests/unit/test_http_admin.py` (MODIFIED — preview HTTP cases) | test (unit, HTTP) | — | itself (fixtures `_mint`/`_seed_profile`/`_client`) | self |
| `tests/unit/test_http_materials.py` (MODIFIED — admin-token reader case) | test (unit, HTTP) | — | itself (`:121-131` tripwire PRESERVE) | self |
| `tests/admin.spec.js` (MODIFIED — amend 4 asserts + new spec) | test (e2e) | — | itself (`:407,690,713,816-821`) | self |

## Pattern Assignments

### `backend/src/backend/application/use_cases/get_material_for_preview.py` (use-case, CRUD read)

**Analog:** `backend/src/backend/application/use_cases/get_material_for_reader.py` (13 lines, whole file). Copy the shape and **invert the status predicate** (`!= DRAFT` instead of `!= READY`).

**Core pattern** (`get_material_for_reader.py:1-13`):
```python
"""Load a ready material by slug for the reader — draft/missing → not found."""

from __future__ import annotations

from backend.application.ports.material_repository import MaterialRepository
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus


def get_material_for_reader(repo: MaterialRepository, slug: str) -> Material:
    material = repo.get_by_slug(slug)
    if material is None or material.status != MaterialStatus.READY:
        raise MaterialNotFoundError(slug)
    return material
```

**Preview variant (D-04 + D-12):** same signature `(repo: MaterialRepository, slug: str) -> Material`, same `MaterialNotFoundError`; predicate becomes `material is None or material.status != MaterialStatus.DRAFT`. Port untouched — `MaterialRepository.get_by_slug` (`application/ports/material_repository.py`) already returns the material at any status; `InMemoryMaterialRepository.get_by_slug` (`tests_support/in_memory.py:339-340`) backs it in tests.

**Domain error to raise** (`backend/src/backend/domain/errors.py:8-11`):
```python
class MaterialNotFoundError(DomainError):
    def __init__(self, material_id: int | str) -> None:
        super().__init__(f"material {material_id} not found")
        self.material_id = material_id
```

**Do NOT** import `fastapi`/`httpx`/`supabase` here (`.cursor/rules/architecture.mdc`).

---

### `backend/src/backend/interface/http/routes/admin.py` (controller, request-response)

**Analogs:** same file `post_material_ready` (`:302-331`) for router style + `require_admin`; `routes/materials.py:97-113` for the domain-error → HTTP mapping and the DTO builder.

**Imports pattern** (`admin.py:1-42` — already present; add only the use-case + DTO symbols you need):
```python
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from backend.domain.current_user import CurrentUser
from backend.domain.errors import MaterialNotFoundError, PersistenceError
from backend.interface.http.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])
```

**`require_admin` gate + `_require_materials`** (`admin.py:219-226`, `:302-314`):
```python
def _require_materials(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "materials", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="materials_not_configured",
        )
    return container.materials


@router.post("/materials/{material_id}/ready", response_model=MarkReadyResponse, ...)
def post_material_ready(
    material_id: int,
    request: Request,
    _admin: CurrentUser = Depends(require_admin),   # D-03: DB-role gate, never a JWT claim
) -> MarkReadyResponse:
    materials = _require_materials(request)
    try:
        material = mark_material_ready(materials, material_id)
    except MaterialNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="material_not_found") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="materials_unavailable") from exc
```

**Core route to mirror** — the reader route (`routes/materials.py:97-113`), which is the exact error-mapping + response-builder shape the preview must copy (but with `require_admin` in place of `get_principal`, plus the `no-store` header):
```python
@router.get("/{slug}", response_model=MaterialReaderResponse, summary="Ready material by slug", ...)
def read_material_by_slug(
    request: Request,
    slug: str = Path(..., pattern=_SLUG_PATTERN),
    claims: AccessTokenClaims = Depends(get_principal),
) -> MaterialReaderResponse:
    del claims
    materials = _require_materials(request)
    try:
        material = get_material_for_reader(materials, slug)
    except MaterialNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="material_not_found") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="materials_unavailable") from exc
    return _to_response(materials, material)
```

**New route shape (compose of the two analogs):**
```python
@router.get("/materials/{slug}", response_model=MaterialReaderResponse)
def read_material_preview(
    request: Request,
    response: Response,                       # D-07: header injection (Pattern 4 in RESEARCH)
    slug: str = Path(..., pattern=_SLUG_PATTERN),
    _admin: CurrentUser = Depends(require_admin),
) -> MaterialReaderResponse:
    materials = _require_materials(request)
    try:
        material = get_material_for_preview(materials, slug)
    except MaterialNotFoundError as exc:
        raise HTTPException(status_code=404, detail="material_not_found") from exc   # 404 for every non-draft (D-12)
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="materials_unavailable") from exc
    response.headers["Cache-Control"] = "no-store"
    return _to_preview_response(material)
```
- `_SLUG_PATTERN = r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$"` is defined once at `routes/materials.py:18` — import it, do not re-roll.
- `MaterialReaderResponse` (`routes/materials.py:29-43`) is reused verbatim (D-02). No `status` field.
- For drafts, build the DTO with `tags=[]`, `related=[]` (D-08); the reader's `_related_ready` filter stays the reader's alone.
- **403 only comes from `require_admin`; every non-draft slug is 404** (Pitfall 4).

---

### `backend/src/backend/composition/container.py` / `composition/live.py` (config — EXPECT NO EDIT)

Research §Don't Hand-Roll is explicit: no new port, no new adapter. `MaterialRepository.get_by_slug` already serves any status. Verify both files still wire `materials` unchanged; only touch them if a genuinely new collaborator appears (it should not).

**Existing wiring to leave as-is** (`container.py:110-119`):
```python
materials_repo = InMemoryMaterialRepository(materials)
...
container = AppContainer(
    materials=materials_repo,
    ...
```
(`live.py:49`: `materials=SupabaseMaterialRepository(admin_client),`)

---

### `backend/src/backend/application/use_cases/email_render.py` (utility/renderer, transform) — D-11 scoped

**Analog:** same file, `render_interstitial_html` (`:17-26`) for the pure-stdlib, no-FastAPI helper style.

**The ONLY change (D-11): anchor gains `target`/`rel`. The `href` stays `{base}/materials/{slug}`** (`email_render.py:45-48`):
```python
    clean_slug = slug.strip()
    if clean_slug:
        href = html.escape(f"{base}/materials/{clean_slug}", quote=True)
        parts.append(f'<p><a href="{href}">Читать →</a></p>')
```
Change to `<a href=... target="_blank" rel="noopener noreferrer">Читать →</a>`. Keep the builder shared by preview **and** send — that is what keeps `test_preview_email_html_matches_send_html` green and keeps admin URLs out of the real digest mail.

**Warning (Pitfall 1):** `render_material_email_block` is called by both `preview_digest_email` and `send_digest.py:171`. Do NOT change the URL base; do NOT touch `test_email_render.py:57,76,141,152`.

**Mirror in the mock path** — `web/src/services/adminApi.js:492-494` (`composeMockPreviewHtml`) builds the same anchor; add the same `target`/`rel` tokens there so the Playwright honesty test matches the backend shape:
```js
parts.push(
  `<p><a href="http://127.0.0.1:5173/materials/${escapeHtml(slug)}">Читать →</a></p>`,
)
```

---

### `web/src/App.jsx` (route config, request-response)

**Analog:** the reader route at `App.jsx:36`.

**Route table** (`App.jsx:36-41`):
```jsx
<Route path="materials/:id" element={<MaterialPage />} />
<Route path="razbory" element={<RazboryListPage />} />
<Route path="razbory/:id" element={<RazborPage />} />
<Route path="profile" element={<ProfilePage />} />
<Route path="admin/digest" element={<AdminDigestPage />} />
<Route path="admin/pipeline" element={<AdminPipelineConfigPage />} />
```
Add `admin/materials/:id` inside the **same** `RequireAuth`/`AppShell` block, next to the other `admin/*` routes. The parameter MUST be spelled `:id`, not `:slug` — `MaterialPage` destructures `const { id: slug } = useParams()` (`MaterialPage.jsx:57`), so `:slug` would leave that binding `undefined` and break both the fetch and the asserted `/admin/materials/{slug}` URL shape. D-12: the page itself decides the ready→reader redirect client-side, so App.jsx adds only the route entry.

---

### `web/src/pages/MaterialPage.jsx` (component, request-response → render)

**Analog:** itself. The additive-prop refactor must keep the current no-prop call site (`materials/:id`) byte-identical.

**Current signature + data load** (`MaterialPage.jsx:57-96`) — a component that takes **no props** and calls `fetchMaterial(slug)` directly:
```jsx
export default function MaterialPage() {
  const { id: slug } = useParams()
  const [material, setMaterial] = useState(null)
  const [status, setStatus] = useState('loading')
  const [notFound, setNotFound] = useState(false)
  ...
  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    setNotFound(false)
    fetchMaterial(slug)
      .then((dto) => { if (cancelled) return; setMaterial(dto); setStatus('ready') })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof ContentApiError && err.code === 'NOT_FOUND') {
          setNotFound(true); setStatus('ready'); return
        }
        setStatus('error')
      })
    return () => { cancelled = true }
  }, [slug, loadKey])
```

**Additive props (D-02 — reuse, do not fork):**
```jsx
export default function MaterialPage({ preview = false, loadMaterial }) {
  const loader = loadMaterial ?? (preview ? fetchMaterialPreview : fetchMaterial)
  // preview=false → today's behaviour byte-identical (no `loadMaterial` prop → fetchMaterial).
  // preview=true  → load via the admin preview fetch; show the D-06 banner;
  //                 on NOT_FOUND, <Navigate to={`/materials/${slug}`} replace /> (D-12).
}
```
- Comment/element structure: extract the body into an inner component or keep the branch minimal; the existing `materials/:id` element in `App.jsx` passes no props.
- Import `Navigate` from `react-router-dom` (already imports `Link, useParams` at `:3`).
- D-08 needs **no new conditional**: the block gates already exist. `tags.length > 0` at `:194` and `related.length > 0` at `:206` hide both blocks automatically when the draft payload sends `tags=[]`/`related=[]`:
```jsx
{tags.length > 0 ? (<div className="mt-8 flex flex-wrap gap-2" data-testid="material-tags"> ... </div>) : null}
{related.length > 0 ? (<section className="mt-10" data-testid="material-related"> ... </section>) : null}
```
- Banner (D-06) is a property of the **route**, not the DTO — never read `material.status` (Pitfall 5; the reader DTO at `routes/materials.py:29-43` has no `status`). Place a persistent banner above the `<article>`/title.
- Markdown rendering stays exactly as-is (`:184-191`, `react-markdown` + `rehypeSlug` + `rehypeSanitize`) — that is the "normal reader rendering".
- **Reconciliation note (2026-10-15, revision 2):** the `App.jsx` route parameter and the `MaterialPage` prop signature above were reconciled with `18-02-PLAN.md` Task 1. Two earlier recommendations in this map were stale and are superseded: `admin/materials/:slug` → **`admin/materials/:id`** (the component destructures `id`), and `loadMaterial = fetchMaterial` → **`loadMaterial` with no default**, because a default of `fetchMaterial` would bind the loader on every render and silently defeat the preview loader. The plans are the source of truth; do not re-flag this divergence.

---

### `web/src/services/adminApi.js` (service, request-response) — new `fetchMaterialPreview`

**Analogs:** `web/src/services/contentApi.js:317-357` (`fetchMaterial` — the reader fetch with `NOT_FOUND` mapping) and `web/src/services/adminApi.js:234-391` (`fetchShortlist`/`markReady` — admin auth header + `mapHttpError`).

**Reader-fetch pattern to copy** (`contentApi.js:317-357`):
```js
export async function fetchMaterial(slug, accessToken) {
  if (consumeFailNext()) throwNetwork('Не удалось загрузить материал. Проверьте сеть.')
  if (isMocksEnabled()) {
    const material = getMaterialById(slug)
    if (!material) throw new ContentApiError('Материал не найден.', { code: 'NOT_FOUND', retryable: false })
    return mapMockMaterial(material)
  }
  const headers = await authHeaders(accessToken)
  let response
  try {
    response = await fetch(`${apiBase()}/materials/${encodeURIComponent(slug)}`, { headers })
  } catch { throwNetwork('Не удалось загрузить материал. Проверьте сеть.') }
  if (response.status === 401) throw new ContentApiError('Сессия истекла. Войдите снова.', { code: 'UNAUTHORIZED', retryable: false })
  if (response.status === 404) throw new ContentApiError('Материал не найден.', { code: 'NOT_FOUND', retryable: false })
  if (!response.ok) throwNetwork('Не удалось загрузить материал. Проверьте сеть.')
  return response.json()
}
```

**Admin auth + error mapping to copy** (`adminApi.js:278-301`, `:213-232`):
```js
const token = accessToken ?? (await getAccessToken())
if (!token) throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
let response
try {
  response = await fetch(`${apiBase()}/admin/shortlist`, { headers: { Authorization: `Bearer ${token}` } })
} catch { throw new AdminApiError('Не удалось загрузить shortlist. Проверьте сеть.', { code: 'NETWORK', retryable: true }) }
if (!response.ok) throw mapHttpError(response, 'Не удалось загрузить shortlist. Проверьте сеть.')
return mapShortlistBody(await response.json())
```
```js
function mapHttpError(response, fallbackMessage) {
  if (response.status === 403) return new AdminApiError('Недостаточно прав.', { code: 'FORBIDDEN', retryable: false })
  ...
  if (response.status === 404) return new AdminApiError(fallbackMessage, { code: 'NOT_FOUND', retryable: false })
  return new AdminApiError(fallbackMessage, { code: 'NETWORK', retryable: true })
}
```
**New `fetchMaterialPreview(slug, accessToken)`** = admin `Authorization: Bearer` + `GET ${apiBase()}/admin/materials/${encodeURIComponent(slug)}` → `mapHttpError` (403→`FORBIDDEN` → `ForbiddenPage`; 404→`NOT_FOUND` → the D-12 `<Navigate>`).
- **Mock branch is mandatory** (research §Wave 0 Gaps): the SPA banner must be Playwright-reproducible. The mock must NOT attempt a status decision (`web/src/data/mock.js` materials have no `status`); `getMaterialById(slug)` returns `null` for the admin shortlist seed slugs (`building-production-rag-systems`, …, `adminReadyMock.js:21,37,53,69,85`), so a mock `NOT_FOUND` exercises the redirect path.
- **No `fetch` in the page component** (`.cursor/rules/architecture.mdc`) — the page receives this loader as a prop.

---

### `web/src/pages/AdminDigestPage.jsx` (component) — two targeted edits

**Analog:** itself.

**(a) Shortlist link repoint (D-10) — REPLACE `/materials/` with `/admin/materials/`** (`:994-1000`):
```jsx
{slug ? (
  <Link
    to={`/materials/${slug}`}
    className="mt-6 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
  >
    Открыть материал →
  </Link>
) : null}
```
This is the site of the actual defect (shortlist rows can be `draft`). `Link` comes from `react-router-dom` — the SPA route renders it in-app.

**(b) Email-preview iframe sandbox (D-11 / Pitfall 2)** (`:869-875`):
```jsx
<iframe
  data-testid="email-preview-frame"
  title="Превью письма HTML"
  sandbox=""
  srcDoc={emailModal.preview.html}
  className="mt-3 min-h-64 w-full rounded-xl border border-rule bg-white"
/>
```
Change `sandbox=""` → `sandbox="allow-popups allow-popups-to-escape-sandbox"`. **Keep `allow-scripts` and `allow-same-origin` OFF** (Security Domain). `allow-popups` is required for `target="_blank"`; `allow-popups-to-escape-sandbox` stops the opened SPA route inheriting the sandbox.

---

### `tests/unit/test_get_material_for_preview.py` (test, use-case) — NEW

**Analog:** `tests/unit/test_get_material_for_reader.py` (whole file, 60 lines) — copy its `_material(...)` factory and `InMemoryMaterialRepository([...])` usage, invert the status expectations.

**Test pattern** (`test_get_material_for_reader.py:1-60`):
```python
"""get_material_for_reader — ready-only by slug; draft treated as not found (D-39)."""

from backend.application.use_cases.get_material_for_reader import get_material_for_reader
from backend.domain.errors import MaterialNotFoundError
from backend.domain.material import Material, MaterialStatus
from backend.tests_support.in_memory import InMemoryMaterialRepository


def _material(*, slug: str, status: MaterialStatus, material_id: int = 1, related: tuple[str, ...] = ()) -> Material:
    now = datetime(2026, 3, 20, tzinfo=timezone.utc)
    return Material(id=material_id, slug=slug, title="Ready article", dek="", body_markdown="## Intro\n\nBody.",
        format="статья", status=status, reading_minutes=5, provenance_label="внутренний разбор", source_id=None,
        roles=("ds",), tags=(("RAG", "rag"),), related_material_ids=related,
        published_at=now if status == MaterialStatus.READY else None, created_at=now, updated_at=now)


def test_get_material_for_reader_draft_raises_not_found() -> None:
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    repo = InMemoryMaterialRepository([draft])
    with pytest.raises(MaterialNotFoundError):
        get_material_for_reader(repo, "secret-draft")
```
New file asserts the inverse: `DRAFT` → returns the material; `READY` → `MaterialNotFoundError`; missing → `MaterialNotFoundError` (D-04/D-12).

---

### `tests/unit/test_http_admin.py` (test, HTTP) — new preview cases

**Analog:** itself. Reuse the module fixtures verbatim — do not reinvent.

**Fixture patterns** (`test_http_admin.py:31-80`):
```python
def _mint(private_key, *, email: str, sub: str = "user-uuid-1", role: str = "authenticated") -> str: ...
def _client(signing_jwk: dict[str, Any], container: AppContainer) -> TestClient: ...
def _seed_profile(container: AppContainer, *, user_id: str, email: str, role: str) -> None:
    container.profiles._by_id[user_id] = CurrentUser(id=user_id, email=email, role=role, display_name=None)
```
New HTTP cases (research §Phase Requirements → Test Map): draft → 200 + reader DTO keys + `Cache-Control: no-store` + `tags==[]`/`related==[]`; employee → 403 `forbidden`; anonymous → 401; unknown slug (admin) → 404 `material_not_found`; `ready` (admin) → 404 (D-12). Build the container with `build_in_memory_container(materials=[...])` and seed a `role="admin"` profile.

---

### `tests/unit/test_http_materials.py` (test, HTTP) — PRESERVE + one added case

**Analog:** itself. **Do not modify** the tripwire.

**PRESERVE (byte-identical)** (`test_http_materials.py:121-131`):
```python
def test_materials_draft_slug_returns_404_not_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client = _client(jwk, materials=[draft])
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get("/materials/secret-draft", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"
```
**ADD** one sibling case proving the reader route has **no role branch**: an admin-token request to the reader route for a draft slug still returns 404 (uses the `_client`/`_material` helpers at `:50-97`).

---

### `tests/admin.spec.js` (test, e2e) — AMEND 4 asserts + new spec

**Analog:** itself. Treat these as the **AMEND set** (Pitfall 8 — amend, never delete):

- Shortlist link target (`:816-821`):
```js
const readerLink = dialog.getByRole("link", { name: "Открыть материал →" });
await expect(readerLink).toBeVisible();
await expect(readerLink).toHaveAttribute("href", "/materials/building-production-rag-systems");
```
→ expect `/admin/materials/building-production-rag-systems`.
- Three `sandbox=""` assertions → `sandbox="allow-popups allow-popups-to-escape-sandbox"` at `:407`, `:690`, `:713`:
```js
await expect(iframe).toHaveAttribute("sandbox", "");
```
New spec: preview route shows the banner + `material-prose`, and `material-tags`/`material-related` have count 0 (mock `NOT_FOUND` → reader route).

## Shared Patterns

### Domain error → HTTP mapping (the shape every new HTTP handler copies)
**Source:** `backend/src/backend/interface/http/routes/materials.py:100-113` and `routes/admin.py:319-331`.
**Apply to:** the new `GET /admin/materials/{slug}` handler.
```python
try:
    material = <use_case>(materials, slug)
except MaterialNotFoundError as exc:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="material_not_found") from exc
except PersistenceError as exc:
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="materials_unavailable") from exc
```

### Admin gate (`require_admin`) — the ONLY authorization mechanism
**Source:** `backend/src/backend/interface/http/deps.py:52-70`.
**Apply to:** the new admin endpoint dependency list. 403 comes from here **only**; non-draft slugs are 404.
```python
def require_admin(request: Request, claims: AccessTokenClaims = Depends(get_principal)) -> CurrentUser:
    """Authorize admin from profiles.role only — never JWT role claim (D-74 / AUTH-03)."""
    ...
    user = get_current_user(container.profiles, claims)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user
```

### Slug validation — one canonical pattern
**Source:** `backend/src/backend/interface/http/routes/materials.py:18`.
**Apply to:** the new route's path param (`Path(..., pattern=_SLUG_PATTERN)`) — import it, never re-roll.
```python
_SLUG_PATTERN = r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$"
```

### Response DTO reuse — `MaterialReaderResponse` verbatim
**Source:** `backend/src/backend/interface/http/routes/materials.py:29-43`.
**Apply to:** the preview endpoint's `response_model` and the SPA renderer. Note the **absence of `status`** (drives D-06/D-08/D-12 design).
```python
class MaterialReaderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slug: str
    title: str
    dek: str
    body_markdown: str
    format: str
    provenance: str
    tags: list[str]
    related: list[RelatedMaterialResponse]
    reading_minutes: int
    published_at: datetime | None
    editor: str = EDITOR_BYLINE
```

### Thin-router → use-case → port split (Ports & Adapters)
**Source:** `routes/admin.py:302-331` + `get_admin_shortlist.py:16-59`.
**Apply to:** all backend work this phase. Router does HTTP only; use-case holds status logic; adapter (`MaterialRepository`) untouched; no `fastapi`/`supabase` import in application/domain.

### Frontend: all API access via `web/src/services/`
**Source:** `web/src/services/contentApi.js` / `adminApi.js`.
**Apply to:** the preview fetch (`fetchMaterialPreview` in `adminApi.js`) and the `MaterialPage` prop injection. No `fetch` in the page component.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| — | — | — | None — every file maps to a concrete existing analog. |

## Metadata

**Analog search scope:** `backend/src/backend/{application,interface,composition,domain,tests_support}`, `web/src/{pages,services,components,data}`, `tests/` and `tests/unit/`.
**Files scanned:** ~20 (13 read in full or by targeted range, 7 verified by grep/tracking).
**Tracked-source gate:** all named analog paths verified git-tracked via `git ls-files` (exit 0, non-empty) — no `.gsd/capabilities/**` mirror paths emitted.
**Pattern extraction date:** 2026-10-15
