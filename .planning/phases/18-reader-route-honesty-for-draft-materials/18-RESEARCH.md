# Phase 18: Reader-route honesty for draft materials - Research

**Researched:** 2026-10-15
**Domain:** FastAPI HTTP contract + React SPA route/authz surface (brownfield debt close-out, no new packages)
**Confidence:** HIGH (codebase contracts, all read this session) / MEDIUM (web-platform + framework behaviour from primary docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The preview is a **dedicated admin route** backed by a **new admin-gated endpoint** — not a preview flag on the reader route, and not a reuse of the existing in-page admin-digest preview. Rationale: the criterion requires the *normal reader rendering*, and the reader route + `get_material_for_reader` must stay byte-identical. — **Reversibility:** reversible — the new route/endpoint is additive; removing it touches only its own call sites.
- **D-02:** The preview endpoint returns **exactly the same DTO as `GET /materials/{slug}`**, and the frontend renders it with the **same page component** used by the reader — so "normal reader rendering" is structural, not an imitation. No separate preview DTO, no duplicated markup. — **Reversibility:** costly — a later switch to a distinct preview DTO would change the response contract and every consumer of that endpoint.
- **D-03:** The preview endpoint is gated by the **existing `require_admin` mechanism** (`profiles.role=admin` resolved through the DB), identical to every other `/admin/*` route. No JWT-app-role shortcut. — **Reversibility:** reversible — the gate is one dependency; changing it is a local edit.
- **D-04:** The preview serves **`draft` only**. There is no preview-specific success path for any other status.
- **D-05:** For `ready` and `published` the preview **redirects to the public reader route** — both statuses are already readable there, so the reader route is the honest destination and no draft marker is shown. This keeps the ROADMAP goal's "any draft (or ready) material" satisfied (a `ready` material *is* readable, just at the reader route) while keeping the preview surface meaning "not yet readable by ordinary readers". — **Reversibility:** reversible — redirect behaviour lives in one place.
- **D-06:** A **persistent banner above the article** (e.g. «Черновик — предпросмотр, не опубликовано») marks the draft. Chosen over an inline title badge (easier to scroll past) and over a chrome-only marker (the marker must travel with the article body, which is the thing being pre-read). Follows the existing editorial banner pattern. — **Reversibility:** reversible — presentational.
- **D-07:** The preview response is served **`no-store`** (criterion 3). The reader response's caching behaviour is not changed. — **Reversibility:** reversible.
- **D-08:** When the material is not published, the **`related` and `tags` blocks are omitted entirely** from the preview rendering. Chosen over rendering them filtered to ready-only (more machinery for a surface whose entire purpose is reading one article) and over a mixed tags-shown/related-hidden split. Simplest honest surface with zero unpublished leakage (criterion 3). — **Reversibility:** reversible — a conditional in the render path.
- **D-09:** The «Открыть материал →» links built in `preview_digest_email.py` and `email_render.py` (today `{base}/materials/{slug}`) are **repointed at the admin preview URL**, and the email-preview CTA opens it with `target="_blank" rel="noopener noreferrer"` so it escapes the `sandbox=""` iframe (criterion 4). Chosen over a `postMessage` bridge from the sandboxed frame into the parent SPA (more moving parts to maintain) over a backend admin-only redirect on the reader route (which would put preview behaviour onto the route the phase exists to keep pure).
- **D-10:** The **admin shortlist** link is repointed at the same admin preview surface, so shortlist and email preview agree on one destination (criterion 4).

### Claude's Discretion

- Exact route path and HTTP verb/path shape for the new admin endpoint (`/admin/materials/{slug}` vs another `/admin/...` spelling), and which router file it lands in (`routes/admin.py` vs `routes/materials.py`) — subject to the `/admin/*` + `require_admin` convention.
- The exact banner copy and its placement within the existing reader layout, provided it is persistent and above the article body.
- Whether the `no-store` header is set at the endpoint or via the route dependency, provided the preview response carries it.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADUX-07 | Admin can open any material (draft or ready) at an admin-gated preview and read it in the normal reader rendering; the public `GET /materials/{slug}` stays ready-only and an unknown **or draft** slug returns an opaque 404 (never 403) | New admin-gated read use case + `GET /admin/materials/{slug}` (§Architecture Patterns); `require_admin` gate (§Don't Hand-Roll); reader-route tripwire preserved (§Validation Architecture); `MaterialReaderResponse` reused verbatim (§Code Examples) |
| ADUX-08 | The admin shortlist and email-preview links target the admin preview surface; a draft preview is served non-cacheable (`no-store`) and carries a visible preview marker, exposing no `related`/`tags` of unpublished material | `no-store` via FastAPI `Response` param (§Code Examples); `tags=[]`/`related=[]` on the draft payload (§Pitfalls 3); banner in the reused `MaterialPage` (§Pattern 3); link repointing sites + **the D-09 conflict that must be resolved before planning** (§Open Questions 1) |

</phase_requirements>

## Summary

This phase closes backlog 999.1. The defect is narrow and well-localised: `get_material_for_reader` is deliberately ready-only, so the admin shortlist's «Открыть материал →» link (`AdminDigestPage.jsx:996`, `to={/materials/${slug}}`) 404s the moment the row it belongs to is still a `draft` — the exact rows the admin is triaging. The fix is additive: one admin-gated endpoint that serves a draft with the *same* reader DTO, one SPA route that renders the *same* `MaterialPage` with a banner, and repointed links. Nothing on `/materials/{slug}` or in `get_material_for_reader` changes.

The research found three things that the plan must settle and one that it must not get wrong. First, **the reader DTO carries no `status` field** (`MaterialReaderResponse` fields are `slug,title,dek,body_markdown,format,provenance,tags,related,reading_minutes,published_at,editor`), so D-02's "exactly the same DTO" and D-05's "ready redirects to the reader route" cannot both be expressed in the payload — the plan must choose a redirect *layer* (recommendation in Open Questions 2). Second, **D-08 needs no frontend conditional at all** if the preview *payload* carries `tags=[]` and `related=[]`: `MaterialPage` already renders both blocks only when `length > 0`, so "omitted entirely" and "empty array" coincide. Third, and most consequentially, **D-09 as literally written conflicts with two shipped contracts**: `render_email_html` is shared by the email preview *and* the real digest send, its `href` today is `{base}/materials/{slug}`, the pool is `approved ∩ ready` (never a draft), and `test_preview_email_html_matches_send_html` asserts `send_html == preview.html`. Repointing that shared builder at an admin-only URL would put admin links into the real digest mail that ordinary readers receive (MAIL-01 inherits this) while leaving the parity test green. This is flagged as Open Question 1 with a recommendation; it needs a decision before the plan is written, not during execution.

**Primary recommendation:** Add `get_material_for_preview` (application use case) + `GET /admin/materials/{slug}` behind `require_admin`, returning the reader DTO with `tags=[]`/`related=[]` and `Cache-Control: no-store`, `status == READY` → 404 so the SPA lands on the reader route (D-04 literal + D-05 outcome); add `/admin/materials/:slug` in `App.jsx` rendering the existing `MaterialPage` with an injected loader + `preview` flag; repoint the shortlist link; and resolve the D-09 email-link conflict before touching `email_render.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| "Who may preview a draft" (authorization) | API / Backend | — | D-03: `require_admin` resolves `profiles.role` through the DB; server-side only, never a client check |
| "What is visible for a draft" (`tags`/`related` omission) | API / Backend | — | The payload decides; the SPA renders what it is handed (D-08) |
| Draft read by slug (`get_material_for_preview`) | Application (backend use case) | — | Thin router + use case + existing `MaterialRepository` port; no new port, no new adapter |
| `no-store` caching contract | API / Backend | — | HTTP response header on the preview response only; reader response untouched (D-07) |
| Reader-route contract (ready-only, opaque 404) | API / Backend | — | Unchanged; tripwire PRESERVE |
| `ready` → reader-route destination (D-05) | API / Backend **or** Browser/Client | — | Layer is unnamed in D-05; see Open Questions 2 for the recommended split |
| Preview banner marker | Browser / Client | — | Presentational; belongs to the preview SPA route, not to the DTO (the DTO has no status field) |
| Admin shortlist link repointing (D-10) | Browser / Client | — | SPA `<Link to>` in `AdminDigestPage.jsx` |
| Email-preview CTA escaping the sandbox | Browser / Client | API / Backend (href builder) | The `target`/sandbox tokens are client; the `href` is produced by the backend renderer → cross-tier, hence Open Question 1 |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | already installed (`backend/pyproject.toml`) | New `GET /admin/materials/{slug}` route; `Response` header injection; `RedirectResponse` if the 307 variant is chosen | Project-standard HTTP edge; `require_admin` is a FastAPI dependency |
| Pydantic | already installed | Reuse `MaterialReaderResponse` verbatim (D-02) | Zero new DTO code |
| react-router-dom | ^7.18.3 (`web/package.json`) | New `/admin/materials/:slug` route | Already the SPA router |
| react-markdown + rehype-sanitize + rehype-slug | ^10.1.0 / ^6.0.0 / ^6.0.0 | Reused unchanged by `MaterialPage` | "Normal reader rendering" is structural (D-02) |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | >=8.3.0 (`[dependency-groups].dev`) | RED-first HTTP + use-case tests (the ROADMAP-mandated test type) | Always for this phase |
| `node --test` (built-in, node 24.21.0) | — | Any *pure* JS helper added (e.g. a Vite-free link/route helper) | Only if a pure helper is extracted; see Validation Architecture |
| @playwright/test | ^1.62.1 | Integration proof of the SPA route + banner + link targets | After pytest is green |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reusing `MaterialReaderResponse` | A distinct preview DTO with `preview: true` | **Forbidden by D-02.** Also would force a second render path, defeating "structural reader rendering" |
| `require_admin` (DB role) | JWT app-role claim | **Forbidden by D-03** and by AUTH-03/D-74 |
| Backend HTTP 307 for `ready` (D-05) | Client-side redirect | Both satisfy D-05's *outcome*; the layer is unnamed in D-05 → Open Questions 2 |

**Installation:**
```bash
# none — this phase installs no new packages (see Package Legitimacy Audit)
```

**Version verification:** No new package is proposed, so no registry lookup is required. The only versions this phase depends on are already pinned in `backend/pyproject.toml` / `web/package.json`, both read this session `[VERIFIED: web/package.json:12-21]`.

## Package Legitimacy Audit

> **Not applicable — this phase installs zero external packages.**

The phase is additive code inside `backend/` and `web/`, both of which already have every dependency it needs (FastAPI, Pydantic, pytest; react-router-dom, react-markdown). No `npm install`, `pip install`, or `uv add` step appears anywhere in this research.

**Packages removed due to [SLOP] verdict:** none (none proposed)
**Packages flagged as suspicious [SUS]:** none (none proposed)

## Architecture Patterns

### System Architecture Diagram

```
                    ADMIN BROWSER (SPA, Vite/React)
  ┌──────────────────────────────────────────────────────────────┐
  │ /admin/digest  (AdminDigestPage)                             │
  │   shortlist row ──► «Открыть материал →»  ──(D-10 repoint)──┐│
  │   email preview modal                                      ││
  │     <iframe sandbox="…" srcDoc=backend-html>               ││
  │        «Читать →»                                          ││
  │        └─(Open Q1: target + sandbox tokens)────────────────┤│
  └────────────────────────────────────────────────────────────┼┘
                                                               ▼
                                    /admin/materials/:slug   (NEW SPA route)
                                               │  renders the SAME MaterialPage
                                               │  + draft banner (D-06)
                                               ▼
                     web/src/services/adminApi.js  ──►  fetchMaterialPreview(slug)
                                               │           Authorization: Bearer <jwt>
                                               ▼
  ─────────────────────────────── HTTP boundary ───────────────────────────────
                                               │
                     GET /admin/materials/{slug}     (NEW route, routes/admin.py)
                                               │
                        deps: get_principal ──► require_admin (profiles.role)
                                               │
                        application: get_material_for_preview(repo, slug)
                                               │
                             repo.get_by_slug(slug)   ── MaterialRepository port
                                               │
                    ┌──────────────────────────┴───────────────────────────┐
                    │ status == DRAFT                status == READY        │
                    │  → 200 MaterialReaderResponse  │  → 404 (never 403)   │
                    │    tags=[], related=[]         │    (+ SPA lands on    │
                    │    Cache-Control: no-store     │     /materials/{slug})│
                    └──────────────────────────────────────────────────────┘
                                               │
  ─────────────────── UNCHANGED, MUST STAY SO ──┴──────────────────────────────
     GET /materials/{slug}  →  get_material_for_reader  →  ready-only, draft ≡ missing
                                                            404 material_not_found
```

### Recommended Project Structure

```
backend/src/backend/
├── application/use_cases/
│   └── get_material_for_preview.py     # NEW — draft-only read by slug
├── interface/http/routes/
│   └── admin.py                        # NEW route in the existing /admin router
└── (composition/ untouched — no new port, no new adapter)

web/src/
├── App.jsx                             # NEW <Route path="admin/materials/:slug">
├── pages/MaterialPage.jsx              # additive props: loader + preview banner
├── services/adminApi.js                # NEW fetchMaterialPreview(slug)
└── services/contentApi.js              # touched only if D-09 needs the preview href
```

### Pattern 1: Application use case, not a router branch

**What:** The draft/ready decision lives in a use case that takes only the `MaterialRepository` port; the router maps domain errors to HTTP.
**When to use:** Always for this phase — `.cursor/rules/architecture.mdc` forbids status logic in routers.
**Example:**
```python
# NEW: backend/src/backend/application/use_cases/get_material_for_preview.py
def get_material_for_preview(repo: MaterialRepository, slug: str) -> Material:
    """Draft-only admin read (D-04); ready/unknown are NOT previewable (D-05)."""
    material = repo.get_by_slug(slug)
    if material is None or material.status != MaterialStatus.DRAFT:
        raise MaterialNotFoundError(slug)
    return material
```

### Pattern 2: Router maps domain errors to HTTP, exactly like the reader route

**What:** Mirror `read_material_by_slug`'s error mapping so the surface is predictable.
**When to use:** The new endpoint.
**Example:**
```python
# Source: backend/src/backend/interface/http/routes/admin.py (existing convention) —
# backend/src/backend/interface/http/routes/materials.py:98-113
@router.get("/materials/{slug}", response_model=MaterialReaderResponse)
def read_material_preview(
    request: Request,
    response: Response,
    slug: str = Path(..., pattern=_SLUG_PATTERN),
    _admin: CurrentUser = Depends(require_admin),
) -> MaterialReaderResponse:
    materials = _require_materials(request)
    try:
        material = get_material_for_preview(materials, slug)
    except MaterialNotFoundError as exc:
        raise HTTPException(status_code=404, detail="material_not_found") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=503, detail="materials_unavailable") from exc
    response.headers["Cache-Control"] = "no-store"  # D-07
    return _to_preview_response(materials, material)
```

### Pattern 3: Reuse `MaterialPage` with additive props

**What:** `MaterialPage` currently takes **no props** and calls `fetchMaterial(slug)` directly (`MaterialPage.jsx:57,73`). D-02's "same page component" is satisfied by an additive prop pair — an injected loader and a preview flag — not by a copy.
**When to use:** The new route only; the existing `materials/:id` route passes nothing and behaves identically.
**Example:**
```jsx
// NEW route in App.jsx (inside the same RequireAuth/AppShell block)
<Route path="admin/materials/:slug" element={<MaterialPage preview />} />

// MaterialPage.jsx — additive, reader call site unchanged
export default function MaterialPage({ preview = false, loadMaterial = fetchMaterialPreviewShim }) {
  // preview=true  → fetch via the admin endpoint, render the banner (D-06),
  //                  and on NOT_FOUND navigate to /materials/{slug} (D-05 outcome)
  // preview=false → current behaviour, byte-identical
}
```
Do **not** branch the component's markup on anything other than the `preview` flag and the data; `tags`/`related` blocks need **no new conditional** because the draft payload already sends empty arrays (D-08).

### Pattern 4: `no-store` via the `Response` parameter

**What:** FastAPI extracts headers from a declared `Response` parameter into the final response while still applying `response_model`.
**When to use:** D-07. This keeps the Pydantic DTO as the return value (D-02) instead of hand-building a `JSONResponse`.
**Example:**
```python
# Source: Context7 /websites/fastapi_tiangolo (advanced/response-headers)
@app.get("/headers-and-object/")
def get_headers(response: Response):
    response.headers["X-Cat-Dog"] = "alone in the world"
    return {"message": "Hello World"}
```

### Anti-Patterns to Avoid

- **Loosening the reader route:** adding `?preview=1`, an admin branch, or a role check inside `get_material_for_reader`. This is the #1 catalogued pitfall and the tripwire's subject.
- **A preview-specific DTO or a `preview: true` field:** violates D-02 and forks the render path.
- **Status logic in the router:** `if material.status == ...` inside `admin.py` instead of in the use case.
- **A new port or adapter:** `MaterialRepository.get_by_slug` already returns the material at any status — nothing new to wire.
- **Returning 403 for a draft/ready slug on the new endpoint:** 403 would be an existence oracle and break the "never 403" discipline the phase exists to enforce (keep 403 for *non-admins*, 404 for *anything not a previewable draft*).
- **Adding `status` to `MaterialReaderResponse`:** the reader contract must stay byte-identical for the tripwire and for `web-app.spec.js`.
- **Rendering the banner based on DTO data:** the DTO cannot express "draft" — the banner belongs to the preview route, not the payload.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Admin authorization | A role read in the SPA, a JWT claim check, or a per-route copy of the DB lookup | `require_admin` (`deps.py:52`) | D-03 + AUTH-03/D-74; a single gate mechanism; already covered by tests that seed `profiles._by_id` |
| Slug validation | A hand-rolled regex in the new route | `_SLUG_PATTERN` from `routes/materials.py:18` | One canonical pattern; consistent 422 behaviour |
| Reader DTO shape | A new preview model | `MaterialReaderResponse` (`materials.py:29`) | D-02; zero drift between preview and reader payloads |
| Ready-only filtering of `related` | A second filter for the preview | The preview sends `related=[]` (D-08) — the existing `_related_ready` stays the reader's alone | D-08 chose omission precisely to avoid new filtering machinery |
| Cache-control plumbing | A middleware or a new dependency class | `response.headers["Cache-Control"] = "no-store"` on the one route | D-07 is a per-response contract; a middleware would leak onto the reader route |
| `no-store` semantics | Re-deriving HTTP caching rules | FastAPI/Pydantic + `Response` header per Context7 | Framework-supported, no invention |

**Key insight:** every piece of this phase already exists as a shipped mechanism; the phase is *composition and targeting*, not construction. The only genuinely new decisions are the redirect layer (Open Question 2) and the email-link scope (Open Question 1).

## Common Pitfalls

### Pitfall 1: Repointing the shared email renderer (`email_render.py`) breaks the real digest mail

**What goes wrong:** `render_email_html` → `render_material_email_block` emits `href="…/materials/{slug}"` (`email_render.py:46-47`) and is called by **both** `preview_digest_email` and `send_digest` (`send_digest.py:171`). Changing that base to an admin-only URL changes the **real digest email** that ordinary readers receive: their «Читать →» would land on an admin-only surface and 403.
**Why it happens:** D-09 names `email_render.py` as a link builder to repoint, reading it as a preview-only surface; it is in fact shared with send.
**How to avoid:** Decide Open Question 1 explicitly before touching `email_render.py`. If the preview must differ from send, thread a link-base parameter and consciously amend `test_preview_email_html_matches_send_html` (`test_preview_digest.py:413`, asserts `send_html == preview.html`) and the `test_email_render.py` `/materials/` href assertions (`:57, :76, :141, :152`).
**Warning signs:** the diff touches `render_material_email_block`'s URL with no change to `test_email_render.py`; the parity test passes but the send pool's href is now admin-only.

### Pitfall 2: `target="_blank"` inside `sandbox=""` silently fails

**What goes wrong:** D-09's chosen mechanism (`target="_blank"`) requires the `allow-popups` sandbox token. MDN: "`allow-popups`: Allows popups (created, for example, by `Window.open()` or `target='_blank'`). **If this keyword is not used, such functionality will silently fail.**" The email-preview iframe is `sandbox=""` (`AdminDigestPage.jsx:873`), i.e. all restrictions applied — so the CTA stays broken with no error.
**Why it happens:** the sandbox attribute is read as "it just can't top-navigate", when in fact opening a new tab is blocked too.
**How to avoid:** amend the iframe to `sandbox="allow-popups allow-popups-to-escape-sandbox"`. MDN on the second token: without it "a redirected page, popup window, or new tab will be subject to the same sandbox restrictions as the originating iframe" — which would sandbox the SPA route you open. Three existing Playwright assertions pin `sandbox=""` and must be **AMEND**ed, not deleted: `tests/admin.spec.js:407`, `:690`, `:713`.
**Warning signs:** the Playwright assertion `toHaveAttribute("sandbox", "")` still present after the change; a click test that only asserts the link is *visible* rather than that a new page opened.

### Pitfall 3: Trying to "omit" `tags`/`related` with a second payload shape

**What goes wrong:** D-08 says the blocks are "omitted entirely", which reads like the DTO must lack the fields. D-02 forbids a different DTO. The two requirements are only reconcilable if the draft payload keeps the **same fields with empty values**.
**Why it happens:** "omitted from the rendering" is read as "omitted from the payload".
**How to avoid:** send `tags=[]` and `related=[]` for drafts. `MaterialPage` already gates both blocks on `length > 0` (`MaterialPage.jsx:194`, `:206`), so the rendering omission is automatic and needs no new conditional.
**Warning signs:** a `preview`-conditioned `tags`/`related` block added to `MaterialPage`; a DTO class with `exclude` set; a test asserting the *keys* are absent from the JSON.

### Pitfall 4: 403 leaking draft existence

**What goes wrong:** gating "may I see this draft" and "is this a draft" with the same status code. A non-admin must get 403 for any slug; an admin must get 404 for a non-draft slug and 200 for a draft. Crossing these produces an existence oracle.
**Why it happens:** `require_admin` raises 403 (`deps.py:64-69`) and it is tempting to reuse 403 for "not previewable".
**How to avoid:** 403 only from `require_admin` (role); 404 for every non-draft outcome on the new endpoint.
**Warning signs:** a test asserting 403 for a *ready* slug with an admin token.

### Pitfall 5: The SPA cannot tell draft from ready from the payload

**What goes wrong:** the banner logic is written as `if (material.status === 'draft')`. `MaterialReaderResponse` has **no** `status` field (verified `materials.py:29-43`), so `material.status` is `undefined` and the banner either never renders or always renders.
**Why it happens:** the admin shortlist DTO *does* carry `material_status`, so the field feels available.
**How to avoid:** the banner is a property of the **preview route** (`preview` prop), never of the DTO. Ready materials never reach the preview route (D-04/D-05).
**Warning signs:** `material.status`, `dto.status`, or `dto.material_status` referenced in `MaterialPage.jsx`.

### Pitfall 6: `TestClient`/`fetch` silently following the redirect

**What goes wrong:** if the 307 variant is chosen for D-05, `TestClient` follows redirects by default and asserts 200 (the reader DTO) instead of the redirect; in the browser, `fetch` follows it too and the SPA renders the reader DTO at the preview URL *with the draft banner*. Conversely `redirect: 'manual'` yields an **opaque-redirect** response in cross-origin cases, so a naive `response.status === 307` check misses it.
**Why it happens:** redirect handling differs per client and per origin relation.
**How to avoid:** pytest must pass `follow_redirects=False` and assert the `Location` header; the service must handle both the real 3xx status and the opaque shape, and there must be a browser-level proof of the end state. This fragility is the main argument for the SPA-side redirect in Open Question 2.
**Warning signs:** a green test that never inspects `Location`; a Playwright test that asserts the preview URL instead of the reader URL after opening a ready material.

### Pitfall 7: Assuming the browser suite can prove the draft-404 contract

**What goes wrong:** writing the RED test as a Playwright spec. Under `VITE_USE_MOCKS=true` (forced by `playwright.config.js:51-54`) `web/src/data/mock.js` materials have **no `status`** field, so draft-404 is structurally unreproducible there.
**Why it happens:** the browser suite is the usual integration gate.
**How to avoid:** the RED test is a **pytest HTTP test** (`tests/unit/test_http_materials.py` style) — exactly what the ROADMAP tripwire note mandates — with Playwright as integration proof of the SPA surface only. Note the useful asymmetry: the admin shortlist seed slugs (`building-production-rag-systems`, …) do **not** exist in `web/src/data/mock.js` (which has `rag-systems`, `prompt-engineering`, `sql-dashboards`, …), so a mock `fetchMaterial(longSlug)` 404s and the preview path *is* Playwright-reproducible, while the reader-route 404 semantics remain pytest-only.
**Warning signs:** a new `*.spec.js` asserting 404 for a draft; a mocked material gaining a `status` field.

### Pitfall 8: Amending the wrong tests

**What goes wrong:** repointing links and changing the sandbox breaks existing assertions that encode the *current* destinations; deleting them instead of amending them destroys the honesty proof.
**Why it happens:** the change is "just a link".
**How to avoid:** treat this list as the AMEND set — `tests/admin.spec.js:816-821` (shortlist `Открыть материал →` href `/materials/building-production-rag-systems`), `tests/admin.spec.js:407,690,713` (`sandbox=""`), and — only if Open Question 1 resolves to "preview links differ" — `tests/unit/test_email_render.py:57,76,141,152`. The PRESERVE set is `tests/unit/test_http_materials.py:121` (`test_materials_draft_slug_returns_404_not_403`) and the parity proof `tests/unit/test_preview_digest.py:413`.
**Warning signs:** a test file deleted or a `pytest.mark.skip` added.

## Code Examples

Verified patterns from the codebase (all read this session) and primary docs.

### The contract that must not change

```python
# backend/src/backend/application/use_cases/get_material_for_reader.py:11-13
def get_material_for_reader(repo: MaterialRepository, slug: str) -> Material:
    material = repo.get_by_slug(slug)
    if material is None or material.status != MaterialStatus.READY:
        raise MaterialNotFoundError(slug)
    return material
```

```python
# backend/src/backend/domain/material.py:10-12 — the entire status vocabulary (no PUBLISHED)
class MaterialStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
```
`published_at` is a nullable timestamp on `Material` (`material.py:30`), not a status: D-05's "`ready` and `published`" collapses to the single `MaterialStatus.READY` branch.

### The DTO the preview must reuse verbatim (note the absence of `status`)

```python
# backend/src/backend/interface/http/routes/materials.py:29-43
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

### The gate the new endpoint must use

```python
# backend/src/backend/interface/http/deps.py:64-69
    user = get_current_user(container.profiles, claims)
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="forbidden",
        )
```

### The tripwire, exactly as it stands

```python
# tests/unit/test_http_materials.py:121-131
def test_materials_draft_slug_returns_404_not_403() -> None:
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    draft = _material(slug="secret-draft", status=MaterialStatus.DRAFT)
    client = _client(jwk, materials=[draft])
    token = _mint(private_key, email="alice@sberbank.ru")
    response = client.get(
        "/materials/secret-draft",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "material_not_found"
```

### `no-store` on one route (framework-verified)

```python
# Source: Context7 /websites/fastapi_tiangolo — advanced/response-headers
@app.get("/headers-and-object/")
def get_headers(response: Response):
    response.headers["X-Cat-Dog"] = "alone in the world"
    return {"message": "Hello World"}
```

### The two client-side touch points

```jsx
// web/src/pages/AdminDigestPage.jsx:994-1000 — D-10 repoint site
          {slug ? (
            <Link
              to={`/materials/${slug}`}
              className="mt-6 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
            >
              Открыть материал →
```

```jsx
// web/src/pages/AdminDigestPage.jsx:869-875 — the sandbox (Open Question 1 / Pitfall 2)
                    <iframe
                      data-testid="email-preview-frame"
                      title="Превью письма HTML"
                      sandbox=""
                      srcDoc={emailModal.preview.html}
```

### The shared href builder and why Open Question 1 exists

```python
# backend/src/backend/application/use_cases/email_render.py:45-48
    clean_slug = slug.strip()
    if clean_slug:
        href = html.escape(f"{base}/materials/{clean_slug}", quote=True)
        parts.append(f'<p><a href="{href}">Читать →</a></p>')
```

```python
# backend/src/backend/application/use_cases/preview_digest_email.py:47-54 — the pool is READY-only
def _approved_ready(items: tuple[ShortlistItem, ...]) -> list[ShortlistItem]:
    return sorted(
        [
            item
            for item in items
            if item.decision == "approved" and item.material_status == "ready"
        ],
        key=lambda item: item.rank,
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Preview a draft in the admin in-page modal (shortlist DTO only) | Read a draft in the real reader rendering at an admin-gated route | this phase | "Normal reader rendering" becomes structural (D-02) |
| Draft link → reader route → «Материал не найден» | Draft link → admin preview route | this phase | Closes backlog 999.1 (W-1) |
| `sandbox=""` (all restrictions) on the email preview iframe | `allow-popups` (or an out-of-frame CTA) | this phase | The preview CTA can actually reach the app (criterion 4) |

**Deprecated/outdated:**
- Nothing is deprecated by this phase. The reader route's caching behaviour, `get_material_for_reader`, and the `_related_ready` filter stay exactly as they are — changing any of them is an explicit anti-goal.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `fetch(..., { redirect: 'manual' })` surfaces a cross-origin redirect as an opaque-redirect response (`type: 'opaqueredirect'`, `status: 0`) and a same-origin one as the real 3xx — so a status check must accept both shapes | Pitfall 6, Open Questions 2 | The ready→reader redirect silently fails for ready materials; only reachable if the backend-307 variant is chosen |
| A2 | Adding `allow-popups allow-popups-to-escape-sandbox` to the email-preview iframe is acceptable security-wise for backend-rendered, `html.escape`d markup | Pitfall 2, Security Domain | A widened sandbox on an escaped-HTML document; MDN warns sandboxing is void if content can be opened outside the frame, hence the explicit `_blank`-plus-tokens design |
| A3 | `README`/docs need no update for this phase (no runbook/ops surface is touched) | — | Docs drift; low impact |

## Open Questions

1. **What exactly does D-09 repoint, given the email renderer is shared with the real digest send?**
   - **What we know:** the email-preview pool is `approved ∩ ready` (`preview_digest_email.py:47-54`), so **no draft can ever appear in the email preview**; today its links already resolve on the reader route. The email HTML builder `render_email_html` is shared by preview *and* send (`send_digest.py:171`), its href is `{base}/materials/{slug}` (`email_render.py:46-47`), and `test_preview_email_html_matches_send_html` (`test_preview_digest.py:413`) asserts `send_html == preview.html`. The draft-404 that motivates the phase lives in the **shortlist modal** link (`AdminDigestPage.jsx:996`), not in the email.
   - **What is unclear:** whether ADUX-08's "email-preview links target the admin preview surface" requires the *href* to change (which would put admin URLs into the real mail that ordinary readers receive, and/or break the D-12 preview≡send parity) or whether the intent is criterion 4's other half — "the email-preview CTA navigates the top-level app rather than being trapped inside the `sandbox=""` iframe".
   - **Recommendation:** satisfy criterion 4's *behavioural* requirement without regressing the real mail: (a) repoint the **shortlist** link to the admin preview route (D-10, unambiguous, fixes the drafts-404 defect); (b) for the email HTML keep `{base}/materials/{slug}` for both paths, add `target="_blank" rel="noopener noreferrer"` to the anchor, and amend the iframe to `sandbox="allow-popups allow-popups-to-escape-sandbox"`. If the user insists on admin URLs inside the email preview, then the link base must become a parameter threaded from `preview_digest_email` only, and `test_preview_email_html_matches_send_html` + the `test_email_render.py` href assertions must be consciously amended — a shipped-invariant change that should be confirmed before planning, not during execution.

2. **Which layer owns D-05's `ready` → reader-route redirect?**
   - **What we know:** the reader DTO has no `status` field (`materials.py:29-43`), so the payload cannot express "this is ready, go elsewhere". D-04 says the endpoint has "no preview-specific success path for any other status"; D-05 says the preview redirects. The layer is not named; D-05's reversibility note only requires that "redirect behaviour lives in one place".
   - **What is unclear:** backend HTTP 307 vs. client-side navigation, and — for `ready` — whether the new endpoint 404s (D-04 literal) or 307s.
   - **Recommendation (prescriptive):** implement it **client-side**, with the endpoint serving drafts only (`DRAFT` → 200; anything else → 404 `material_not_found`). The SPA preview page treats `NOT_FOUND` as "not a previewable draft" and issues `<Navigate to={/materials/${slug}} replace />`, which arrives at the reader route (D-05's stated outcome) and shows no draft marker. Rationale: one request, no HTTP-redirect opacity (Pitfall 6 / A1), D-04 honoured literally, deterministic in pytest (endpoint 404 + reader 200/404) and reproducible under mocks in Playwright. The alternative — a backend `RedirectResponse(url=f"{site_url}/materials/{slug}", status_code=307)` — is the literal reading of "redirects", but it requires `follow_redirects=False` in pytest, `redirect: 'manual'` plus opaque-redirect handling in the service, and a mock-level 3xx emulation for the browser suite.

3. **Does the new preview route need its own role pre-check in the SPA?**
   - **What we know:** `AdminDigestPage` pre-checks via `fetchMe` and renders `ForbiddenPage` on `UNAUTHORIZED`/`FORBIDDEN`; the backend gate is the real control (D-03).
   - **What is unclear:** whether the preview page should duplicate that pre-check or simply map the endpoint's 403 through the existing `AdminApiError` `FORBIDDEN` mapping (`adminApi.js:217-218`) to `ForbiddenPage`.
   - **Recommendation:** map the endpoint's 403 → `ForbiddenPage`; skip the extra `fetchMe` round trip. The backend remains the single authorization authority (D-03), which is also the honest reading of "an ordinary reader gets an opaque 404" — a non-admin hitting the preview route must not be told whether the slug exists.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Playwright + `node --test` | ✓ | 24.21.0 | — |
| Python | backend + pytest | ✓ | 3.14.0 (project requires >=3.12) | — |
| uv | `uv run pytest` workspace deps | ✓ | 0.10.9 | `python -m pytest` if the venv exists |
| pytest | RED/GREEN backend tests | ✓ | >=8.3.0 declared | — |
| Playwright browsers | SPA integration proof | ✓ | ^1.62.1 + `scripts/ensure-playwright-browsers.cjs` on postinstall | pytest-only verification (browser proof becomes manual) |
| FastAPI / Pydantic | new endpoint | ✓ | already pinned in `backend/pyproject.toml` | — |
| react-router-dom / react-markdown | new SPA route | ✓ | ^7.18.3 / ^10.1.0 | — |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >=8.3.0 (testpaths `tests/unit`, `pythonpath = ["."]`); Playwright ^1.62.1 for SPA integration; built-in `node --test` for pure Vite-free JS helpers |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js`; (`web/package.json` has no test script — `node --test <path>` is run per file) |
| Quick run command | `uv run pytest tests/unit/test_http_admin.py tests/unit/test_http_materials.py -q` |
| Full suite command | `uv run pytest` |
| Browser integration | `npm run test:web -- tests/admin.spec.js` then `npm run test:web` (full web project) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| ADUX-07 | Admin GETs a draft slug on the new endpoint → 200 with the reader DTO shape | unit (HTTP) | `uv run pytest tests/unit/test_http_admin.py -k preview -x` | ❌ Wave 0 |
| ADUX-07 | Employee GETs the same endpoint → 403 `forbidden` (no slug oracle) | unit (HTTP) | same file | ❌ Wave 0 |
| ADUX-07 | Unauthenticated → 401 | unit (HTTP) | same file | ❌ Wave 0 |
| ADUX-07 | Unknown slug, admin token → 404 `material_not_found` | unit (HTTP) | same file | ❌ Wave 0 |
| ADUX-07 | **Tripwire PRESERVE** — reader route, draft slug, any authenticated reader → 404 `material_not_found`; add an *admin* token case so the reader route provably has no role branch | unit (HTTP) | `uv run pytest tests/unit/test_http_materials.py -x` | ✅ exists (`:121`) + ❌ Wave 0 admin-token case |
| ADUX-07 | Reader route still 200 for a ready material (no regression) | unit (HTTP) | `uv run pytest tests/unit/test_http_materials.py -x` | ✅ exists |
| ADUX-07 | `get_material_for_preview` draft-only semantics against an in-memory fake; `MaterialNotFoundError` on `READY`/missing | unit (use case) | `uv run pytest tests/unit/test_get_material_for_preview.py -x` | ❌ Wave 0 |
| ADUX-08 | Draft preview response carries `Cache-Control: no-store`; the reader response does **not** | unit (HTTP) | same admin file | ❌ Wave 0 |
| ADUX-08 | Draft preview payload has `tags == []` and `related == []`, with the same keys as the reader DTO | unit (HTTP) | same admin file | ❌ Wave 0 |
| ADUX-08 | Ready slug on the preview endpoint → 404 (recommended variant) **or** 307 + `Location` (alternative) | unit (HTTP) | same admin file, `follow_redirects=False` if 307 | ❌ Wave 0 |
| ADUX-08 | SPA: shortlist «Открыть материал →» targets `/admin/materials/{slug}` | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "Открыть материал"` | ✅ exists — **AMEND** `:816-821` |
| ADUX-08 | SPA: preview route shows the draft banner + `material-prose`, and `material-tags`/`material-related` have count 0 | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "предпросмотр"` | ❌ Wave 0 |
| ADUX-08 | Email-preview CTA escapes the iframe (new tab) | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "email-preview"` | ❌ Wave 0 after the sandbox amend; three `sandbox=""` asserts **AMEND** `:407,:690,:713` |
| ADUX-08 | Email render/preview≡send invariants | unit | `uv run pytest tests/unit/test_email_render.py tests/unit/test_preview_digest.py -q` | ✅ exists — amend only if Open Question 1 resolves to "preview links differ" |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/unit/test_http_admin.py tests/unit/test_http_materials.py tests/unit/test_email_render.py -q`
- **Per wave merge:** `uv run pytest` then `npm run test:web` (full web project)
- **Phase gate:** full pytest green + full web Playwright project green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `backend/tests_support/in_memory.py` — no change needed (`InMemoryMaterialRepository.get_by_slug` already returns materials at any status; `backend/src/backend/tests_support/in_memory.py:339-340`), but the admin HTTP fixtures (`_admin_client_with_batch`, `_seed_profile`, `_mint`) live in `tests/unit/test_http_admin.py` and should be reused rather than reinvented.
- [ ] `tests/unit/test_get_material_for_preview.py` — draft-only use-case semantics (ADUX-07).
- [ ] `tests/unit/test_http_admin.py` — new preview route cases: 200 draft + `no-store` + empty `tags`/`related`; 403 employee; 401 anonymous; 404 unknown; 404/307 ready.
- [ ] `tests/unit/test_http_materials.py` — add the admin-token reader-route 404 case (proves no role branch on the reader route) **without touching** `test_materials_draft_slug_returns_404_not_403`.
- [ ] `tests/admin.spec.js` — new preview-route spec; **amend** the shortlist href assert and the three `sandbox=""` asserts.
- [ ] Mock layer: the preview fetch must be mockable (`adminApi.js` mock branch) so the SPA banner is Playwright-reproducible; note that `web/src/data/mock.js` materials have no `status`, so the mock branch must not attempt a status decision.
- [ ] Framework install: none.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (inherited) | `get_principal` — Bearer JWT verified against JWKS + corporate email gate (`deps.py:21-49`) |
| V3 Session Management | no | No session surface added; JWT is forwarded by the existing SPA service layer |
| V4 Access Control | **yes** | `require_admin` DB-role gate (`deps.py:52-70`); 403 for non-admins, 404 for non-draft slugs — never mixed |
| V5 Input Validation | yes | `_SLUG_PATTERN = r"^[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*$"` on the path param (`materials.py:18`), reused verbatim; `extra="forbid"` on every DTO |
| V6 Cryptography | no | Nothing cryptographic is added; no hand-rolled crypto, no new tokens |
| V14 Data Protection | yes | `Cache-Control: no-store` on the draft response (D-07); `tags`/`related` empty (D-08); no canonical/SEO metadata emitted |

### Known Threat Patterns for FastAPI + React SPA

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Draft exposure through a loosened reader route | Information Disclosure | Reader route + `get_material_for_reader` untouched; tripwire PRESERVE; new tests assert the *admin* token also gets 404 there |
| Slug enumeration via status-code differential | Information Disclosure | 404 (never 403) for every non-draft slug to an admin; 403 only from the role gate, before any slug lookup |
| Unpublished relations leaking through the preview | Information Disclosure | `tags=[]`/`related=[]` on the draft payload (D-08) — no filtering logic to get wrong |
| Shared-proxy / browser caching of an unpublished body | Information Disclosure | `Cache-Control: no-store` only on the preview response; reader caching unchanged (D-07) |
| Sandbox escape via the email-preview iframe | Elevation of Privilege | The HTML is backend-rendered with stdlib `html.escape` only (`email_render.py`), no scripts, no `allow-scripts`/`allow-same-origin`. Adding `allow-popups` widens the sandbox deliberately (A2); keep `allow-scripts` and `allow-same-origin` off so a popup cannot inherit script/same-origin powers |
| Admin CTA leaking an admin URL to ordinary readers | Information Disclosure / broken UX | Open Question 1 — the real digest must keep reader-route hrefs |
| Unsanitised markdown in the preview | Tampering / XSS | `MaterialPage` already renders through `rehypeSanitize` (`MaterialPage.jsx:185-190`) and the preview reuses it |

## Project Constraints (from project instructions)

`./CLAUDE.md` **does not exist** in the working directory (verified this session). The operative instructions are `AGENTS.md` and `.cursor/rules/*.mdc`; the planner must honour these:

- **Mandatory Red–Green–Refactor** (`.cursor/rules/tdd.mdc`, `AGENTS.md`): no production code before a failing test. Write the pytest HTTP/use-case test first, watch it fail for the expected reason, then implement minimally, then run the new test plus the full suite.
- **Tests assert behaviour, not mocks**: in-memory fakes of ports are used only where a real dependency is unavailable (the project already ships `InMemoryMaterialRepository`, `InMemoryShortlistRepository`, `InMemoryProfileRepository`).
- **Ports & Adapters** (`.cursor/rules/architecture.mdc`): dependencies point inward; domain/application must not import `fastapi`/`supabase`/`httpx`; routers stay thin and delegate to use cases; wiring only in `composition/`.
- **No new port or adapter** is needed here — `MaterialRepository` already exposes `get_by_slug` at any status.
- **FE accesses the API only through `web/src/services/`** — no `fetch` in a page component.
- **Config/generated/one-off files** are the only TDD exemption; nothing in this phase qualifies.
- **`AGENTS.md`**: issues live under `.scratch/`; `origin` git operations only via WSL (not PowerShell).

## Sources

### Primary (HIGH confidence — read from this checkout this session)

- `backend/src/backend/application/use_cases/get_material_for_reader.py:11-13` — the ready-only contract
- `backend/src/backend/interface/http/routes/materials.py:18,29-43,55-81,98-113` — `_SLUG_PATTERN`, `MaterialReaderResponse`, `_related_ready`, the reader route + error mapping
- `backend/src/backend/interface/http/routes/admin.py:219-226,271-333` — `_require_materials`, the existing `/admin/materials/*` routes, `require_admin` convention
- `backend/src/backend/interface/http/deps.py:21-70` — Bearer verify → corporate email gate → `require_admin`
- `backend/src/backend/domain/material.py:10-12,30` — `MaterialStatus` (only DRAFT/READY) and nullable `published_at`
- `backend/src/backend/application/ports/material_repository.py:7-13` — the port (no change needed)
- `backend/src/backend/composition/container.py:104-133`, `composition/live.py:49` — materials wiring in both containers
- `backend/src/backend/application/use_cases/email_render.py:45-48`, `preview_digest_email.py:47-54`, `send_digest.py:168-190` — the shared href builder, the ready-only preview pool, the send path
- `backend/src/backend/tests_support/in_memory.py:331-345` — `InMemoryMaterialRepository`
- `tests/unit/test_http_materials.py:121-131`, `tests/unit/test_http_admin.py` (fixtures + patterns), `tests/unit/test_email_render.py:50-152`, `tests/unit/test_preview_digest.py:413-447`
- `tests/admin.spec.js:407,690,713,816-821` — the assertions this phase must amend
- `web/src/pages/MaterialPage.jsx:57,73,185-220`, `web/src/pages/AdminDigestPage.jsx:869-875,994-1000`, `web/src/services/adminApi.js:217-218`, `web/src/services/contentApi.js:318-356`, `web/src/data/mock.js` (ids), `web/src/services/adminReadyMock.js`
- `web/src/App.jsx:36` — route table; `playwright.config.js:44-54` — forced `VITE_USE_MOCKS=true`
- `.planning/ROADMAP.md:97-109`, `.planning/REQUIREMENTS.md:14-17`, `.planning/research/PITFALLS.md:747-800`, `.planning/config.json` (no `nyquist_validation` key → section included)

### Secondary (MEDIUM confidence)

- `[CITED: developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe]` — sandbox `allow-popups` / `allow-popups-to-escape-sandbox` / top-navigation semantics
- `[CITED: fastapi.tiangolo.com/advanced/response-headers]` (via Context7 `/websites/fastapi_tiangolo`) — `Response` parameter header injection
- `[CITED: fastapi.tiangolo.com/reference/responses, /advanced/custom-response]` (via Context7) — `RedirectResponse` defaults to 307 and sets `Location`

### Tertiary (LOW confidence, marked for validation)

- A1 (opaque-redirect `fetch` behaviour) — training knowledge, not probed in a browser this session; only load-bearing if the backend-307 variant is chosen.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; every dependency already pinned and verified in-repo; the framework behaviours used are cited from primary docs.
- Architecture: HIGH — every integration point (router, use case, port, service, route table, link sites, test files) was opened and read this session with line-level quotes.
- Pitfalls: HIGH for the in-repo pitfalls (each tied to a read file and line) / MEDIUM for the web-platform pitfall (MDN-cited). The headline D-09 conflict is HIGH — it follows directly from two files read in full (`email_render.py`, `send_digest.py`) plus a live parity assertion.

**Research date:** 2026-10-15
**Valid until:** ~2026-11-14 (stable domain; re-check only if `MaterialReaderResponse`, `require_admin`, `render_email_html`, or the iframe sandbox change before the plan is executed).
