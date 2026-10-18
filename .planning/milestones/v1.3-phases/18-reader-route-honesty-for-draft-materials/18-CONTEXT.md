# Phase 18: Reader-route honesty for draft materials - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning

<domain>
## Phase Boundary

An admin can read any **draft** material in the normal reader rendering at an admin-gated preview surface, while the public reader route stays ready-only and unchanged: `GET /materials/{slug}` and `get_material_for_reader` remain untouched, and an unknown **or draft** slug returns an opaque 404 (never 403) to any authenticated reader; no unpublished `related`/`tags` are exposed, the preview response is served `no-store`, and the admin shortlist + email-preview links reach the preview surface instead of the reader route that 404s for a draft.

The phase is a **backlog debt close-out** (backlog 999.1). It adds a new admin read surface; it does not change the reader contract, does not add publishing behaviour, and does not add any new capability beyond "an admin can read a draft".

</domain>

<decisions>
## Implementation Decisions

### Preview surface
- **D-01:** The preview is a **dedicated admin route** backed by a **new admin-gated endpoint** — not a preview flag on the reader route, and not a reuse of the existing in-page admin-digest preview. Rationale: the criterion requires the *normal reader rendering*, and the reader route + `get_material_for_reader` must stay byte-identical. — **Reversibility:** reversible — the new route/endpoint is additive; removing it touches only its own call sites.

### Response shape and rendering
- **D-02:** The preview endpoint returns **exactly the same DTO as `GET /materials/{slug}`**, and the frontend renders it with the **same page component** used by the reader — so "normal reader rendering" is structural, not an imitation. No separate preview DTO, no duplicated markup. — **Reversibility:** costly — a later switch to a distinct preview DTO would change the response contract and every consumer of that endpoint.

### Authorization
- **D-03:** The preview endpoint is gated by the **existing `require_admin` mechanism** (`profiles.role=admin` resolved through the DB), identical to every other `/admin/*` route. No JWT-app-role shortcut. — **Reversibility:** reversible — the gate is one dependency; changing it is a local edit.

### Status coverage
- **D-04:** The preview serves **`draft` only**. There is no preview-specific success path for any other status.
- **D-05:** For `ready` and `published` the preview **redirects to the public reader route** — both statuses are already readable there, so the reader route is the honest destination and no draft marker is shown. This keeps the ROADMAP goal's "any draft (or ready) material" satisfied (a `ready` material *is* readable, just at the reader route) while keeping the preview surface meaning "not yet readable by ordinary readers". — **Reversibility:** reversible — redirect behaviour lives in one place.

### Preview marker and caching
- **D-06:** A **persistent banner above the article** (e.g. «Черновик — предпросмотр, не опубликовано») marks the draft. Chosen over an inline title badge (easier to scroll past) and over a chrome-only marker (the marker must travel with the article body, which is the thing being pre-read). Follows the existing editorial banner pattern. — **Reversibility:** reversible — presentational.
- **D-07:** The preview response is served **`no-store`** (criterion 3). The reader response's caching behaviour is not changed. — **Reversibility:** reversible.

### Unpublished related/tags exposure
- **D-08:** When the material is not published, the **`related` and `tags` blocks are omitted entirely** from the preview rendering. Chosen over rendering them filtered to ready-only (more machinery for a surface whose entire purpose is reading one article) and over a mixed tags-shown/related-hidden split. Simplest honest surface with zero unpublished leakage (criterion 3). — **Reversibility:** reversible — a conditional in the render path.

### Admin / email link target
- **D-09:** The «Открыть материал →» links built in `preview_digest_email.py` and `email_render.py` (today `{base}/materials/{slug}`) are **repointed at the admin preview URL**, and the email-preview CTA opens it with `target="_blank" rel="noopener noreferrer"` so it escapes the `sandbox=""` iframe (criterion 4). Chosen over a `postMessage` bridge from the sandboxed frame into the parent SPA (more moving parts to maintain) over a backend admin-only redirect on the reader route (which would put preview behaviour onto the route the phase exists to keep pure).
- **D-10:** The **admin shortlist** link is repointed at the same admin preview surface, so shortlist and email preview agree on one destination (criterion 4). *Amended by D-11: the shortlist link is now the **only** link repointed; "so shortlist and email preview agree" no longer holds.*
- **D-11:** *(plan-time checkpoint, 2026-10-15 — **amends D-09**)* Criterion 4 is satisfied **behaviourally, not by changing the email href**. The `email_render.py` href stays `{base}/materials/{slug}` for both the preview and the real send — preserving the `test_preview_email_html_matches_send_html` parity invariant and keeping admin URLs out of the mail ordinary readers receive; the anchor gains `target="_blank" rel="noopener noreferrer"` and the preview iframe is widened to `sandbox="allow-popups allow-popups-to-escape-sandbox"` with `allow-scripts` and `allow-same-origin` deliberately left off. Context: the email-preview pool is `approved ∩ ready` (`preview_digest_email.py:47-54`), so no draft can appear in the email preview at all; the draft-404 defect lives in the admin shortlist link and is closed by D-10. **D-11 supersedes D-09's "repoint `preview_digest_email.py` / `email_render.py`"** — `test_preview_email_html_matches_send_html` and the `test_email_render.py` href assertions must NOT be amended. — **Reversibility:** reversible — a presentation/attribute change plus one iframe attribute.
- **D-12:** *(plan-time checkpoint, 2026-10-15 — **resolves D-05's unnamed layer**)* The `ready` redirect is **client-side**. The preview endpoint serves drafts only — `DRAFT` → 200, any other status → 404 `material_not_found` (D-04 honoured literally; no preview-specific success path for any other status). The SPA preview page maps the endpoint's `NOT_FOUND` → `<Navigate to={/materials/${slug}} replace />`, which arrives at the reader route (D-05's stated outcome) and shows no draft marker. No backend 307 — no `follow_redirects=False` in pytest and no opaque-redirect handling in the service layer. — **Reversibility:** reversible — one conditional in the preview page.

### Claude's Discretion
- Exact route path and HTTP verb/path shape for the new admin endpoint (`/admin/materials/{slug}` vs another `/admin/...` spelling), and which router file it lands in (`routes/admin.py` vs `routes/materials.py`) — subject to the `/admin/*` + `require_admin` convention.
- The exact banner copy and its placement within the existing reader layout, provided it is persistent and above the article body.
- Whether the `no-store` header is set at the endpoint or via the route dependency, provided the preview response carries it.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` §Phase 18 — the goal, the four success criteria, requirements `ADUX-07`/`ADUX-08`, and the tripwire note.
- `.planning/ROADMAP.md` §Backlog 999.1 — the originating debt (`W-1`), its two follow-ups, and the "merged 999.2" note (identical root cause).
- `.planning/REQUIREMENTS.md` — `ADUX-07`, `ADUX-08` traceability.
- `.planning/PROJECT.md` — v1.3 milestone framing and the "reader-route honesty" bullet.

### Reader contract that must not change
- `backend/src/backend/application/use_cases/get_material_for_reader.py` — the ready-only use-case; the tripwire's subject.
- `backend/src/backend/interface/http/routes/materials.py` — `GET /materials/{slug}`; the route whose caching/status behaviour stays pure.
- `backend/src/backend/domain/material.py` — `Material`, `MaterialStatus`, `assert_publishable` / `as_ready`; the status vocabulary D-04/D-05 depend on.

### Admin surface and gating
- `backend/src/backend/interface/http/routes/admin.py` — existing `/admin/*` routes, including `/admin/shortlist` and the material ready endpoints; the `require_admin` convention.
- `backend/src/backend/interface/http/deps.py` — Bearer verify → corporate email gate → `require_admin` (DB role).
- `backend/src/backend/application/use_cases/get_admin_shortlist.py` — how the admin reads materials today.

### Link construction and the sandboxed email preview
- `backend/src/backend/application/use_cases/preview_digest_email.py` — builds the reader URL (`W-2`: blank slug emits no link).
- `backend/src/backend/application/use_cases/email_render.py` — the HTML href builder.
- `backend/src/backend/infrastructure/stub_mailer.py` — the mailer boundary.
- `.planning/ROADMAP.md` §Phase 13 — the `sandbox=""` iframe decision that makes D-09 necessary.

### Architecture and process constraints
- `.cursor/rules/architecture.mdc` — Ports & Adapters; thin routers; wiring only in `composition/`.
- `.cursor/rules/tdd.mdc` — mandatory Red–Green–Refactor.
- `CLAUDE.md` — project instructions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MaterialPage` (`web/src/pages/MaterialPage.jsx`): the reader page component. D-02 requires reusing this rather than writing a preview variant.
- `GET /materials/{slug}` response DTO: reusable verbatim as the preview payload (D-02).
- `require_admin` dependency (`backend/src/backend/interface/http/deps.py`): the existing DB-role admin gate (D-03).
- `preview_digest_email.py` / `email_render.py`: the two existing link builders D-09 repoints.
- `MaterialRepository` port: the persistence contract a new admin read use-case will consume; no new port should be needed.

### Established Patterns
- Thin routers call use-cases through `app.state.container`; the use-case holds the logic. A new preview read must follow this split, not put status logic in the router.
- Admin authorization is a DB-role check, not a JWT claim — D-03 must match.
- Editorial banner pattern: existing banner/copy conventions in the reader layout inform D-06.
- Frontend reaches the backend only through `web/src/services/`; the preview fetch belongs in a service module, not in the page component.
- `VITE_USE_MOCKS=true` makes draft-404 structurally unreproducible in the browser suite — ROADMAP notes the RED test must be a **pytest HTTP test**, with Playwright as integration proof only.

### Integration Points
- New admin endpoint → `routes/admin.py` (or `routes/materials.py`) → new admin read use-case → `MaterialRepository`.
- New SPA route → `web/src/App.jsx` → `MaterialPage` + preview marker + `related`/`tags` suppression.
- Admin shortlist row link + email-preview CTA → the admin preview URL (D-09/D-10).
- Tripwire to PRESERVE: `test_materials_draft_slug_returns_404_not_403`.

</code_context>

<specifics>
## Specific Ideas

- Banner copy proposed during discussion: «Черновик — предпросмотр, не опубликовано» (Russian copy per the CONTEXT language convention).
- The email-preview CTA must use `target="_blank" rel="noopener noreferrer"` — the sandboxed iframe cannot navigate the top-level app itself, which is why the link is repointed rather than re-navigated.
- D-05's redirect is what keeps the ROADMAP goal's "any draft (or ready) material" true without giving `ready` a preview-specific path.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 18-Reader-route honesty for draft materials*
*Context gathered: 2026-10-14*
