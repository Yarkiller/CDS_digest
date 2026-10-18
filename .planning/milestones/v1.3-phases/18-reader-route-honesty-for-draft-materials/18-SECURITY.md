---
phase: 18
slug: reader-route-honesty-for-draft-materials
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-10-15
---

# Phase 18 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser SPA → FastAPI | An authenticated user's Bearer JWT and a caller-chosen `slug` path parameter cross here | JWT (bearer credential), caller-controlled path segment |
| FastAPI deps → `require_admin` | Untrusted role claims meet the DB-backed `profiles.role` lookup — the only authorization authority | Role claims, DB-read `profiles.role` |
| Route → application use case | Domain-typed input only; the use case never sees HTTP concepts | Domain-typed slug, domain `Material` |
| Use case → `MaterialRepository` | The persistence boundary; the preview must be read-only across it | `Material` entity (may be `draft`) |
| HTTP response → any shared/browser cache | An unpublished body crosses here, so it must be non-cacheable | Draft body markdown (unpublished) |
| SPA route → preview service | A caller-chosen URL path segment becomes the `slug` sent to the admin endpoint | Caller-controlled path segment |
| Preview payload → reader renderer | Draft markdown reaches `react-markdown`; the sanitisation boundary must be the existing one | Draft body markdown → HTML |
| Mock harness → component | `window.__DIGEST_MOCK_*` flags are test-only seams that must never become a live code path | Test-only role/token flags |
| Backend renderer → email HTML | The shared `render_email_html` output is consumed both by the sandboxed admin preview and by the real digest mail sent to ordinary readers | Email HTML (recipient-facing) |
| Email HTML → sandboxed iframe | Backend-rendered markup runs inside `srcDoc` under a sandbox attribute chosen on the client | Backend-rendered markup |
| Sandboxed frame → top-level app | A `target="_blank"` navigation crosses out of the frame; the sandbox tokens decide whether it is silent, sandboxed, or a real top-level context | Navigation intent |
| Admin shortlist link → SPA route | A route the link resolves against must be admin-gated, or the repoint would move the 404 rather than fix it | Route target |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-18-01 | Information Disclosure | `read_material_preview` / `get_material_for_preview` | high | mitigate | The preview route is a NEW `/admin/*` route; `get_material_for_reader` and `routes/materials.py` are byte-identical after this phase (`git diff 3754f87 HEAD -- …` → 0 lines), and the added admin-token reader-route case proves the reader route has no role branch — a draft can never be served there. Test: `tests/unit/test_http_materials.py#test_materials_draft_slug_returns_404_for_admin_token_too` | closed |
| T-18-02 | Information Disclosure | slug-existence oracle via a 403/404 differential | high | mitigate | `Depends(require_admin)` (`admin.py:373`) resolves before `_require_materials` (`admin.py:375`) and before any slug lookup; every non-`draft` slug answers `404 material_not_found` (`admin.py:381`). 403 is raised only by `require_admin`. Tests pin both directions. | closed |
| T-18-03 | Information Disclosure | unpublished relations / taxonomy leaking through the preview payload | high | mitigate | `_to_preview_response` ships `tags=[]` and `related=[]` (`admin.py:289-290`) and never calls the reader's `_related_ready` projection. Test: `tests/unit/test_http_admin.py#test_admin_material_preview_draft_returns_200_reader_dto` (asserted on a draft carrying two tags and one ready related id) | closed |
| T-18-04 | Information Disclosure | shared-proxy or browser caching of an unpublished body | high | mitigate | `response.headers["Cache-Control"] = "no-store"` (`admin.py:388`) — the ONLY `Cache-Control` write anywhere in `backend/src/backend` (grep: 1 match, no middleware), so it cannot widen onto the reader route. Test asserts the reader response carries no `no-store`. | closed |
| T-18-05 | Elevation of Privilege | the email-preview iframe gaining popup or script powers | high | mitigate | `sandbox="allow-popups allow-popups-to-escape-sandbox"` (`AdminDigestPage.jsx:875`); `allow-scripts` and `allow-same-origin` are deliberately withheld (grep → 0 matches). The popup cannot inherit the frame's origin or run its scripts, and the frame's HTML is backend-rendered with stdlib `html.escape` only. | closed |
| T-18-06 | Information Disclosure | an admin-only URL reaching the real digest mail ordinary readers receive | high | mitigate | The shared href builder keeps `{base}/materials/{slug}`; `email_render.py` contains no `/admin/` (grep → 0 matches) and `preview_digest_email.py` + `tests/unit/test_preview_digest.py` are byte-identical (`git diff 3754f87 HEAD` → 0 lines), so preview≡send parity is provably intact (D-11). | closed |
| T-18-07 | Tampering | `MaterialPage` markdown rendering of a draft body (XSS) | high | mitigate | The preview reuses the reader's `react-markdown` pipeline with `rehypeSlug` + `rehypeSanitize` unchanged (`MaterialPage.jsx:233`; D-02 structural reuse); no `dangerouslySetInnerHTML` (grep → 0 matches), no new plugin, no sanitisation bypass. | closed |
| T-18-08 | Information Disclosure | a client-side decision leaking slug existence to a non-admin | high | mitigate | The page maps the server's 403 to `ForbiddenPage` and performs no `/me` pre-check and no local slug lookup; the mock branch's seat-role gate runs before the slug lookup (`adminApi.js:333-339`), so an employee's screen is identical for an existing and a nonexistent slug (asserted by two cases). | closed |
| T-18-09 | Elevation of Privilege | client-side role trust | high | mitigate | `fetchMaterialPreview` sends the admin Bearer token but asserts nothing about the role; the backend `require_admin` DB-role gate remains the only authorization authority (D-03). No JWT claim is inspected in the SPA (grep for `decodeJwt`/`jwtDecode`/`parseJwt`/`.role` in `adminApi.js` → 0 matches). | closed |
| T-18-10 | Information Disclosure | stale draft content surviving on the client | medium | mitigate | The preview loader is invoked per route mount with `preview` in the effect's dependency list, and the draft marker is rendered from the route prop (`MaterialPage.jsx:182`), not from any cached payload field, so a navigation to the reader route cannot leave the banner on screen. Reinforced by the CR-01 fix, which resets `redirectToReader`/`forbidden` on every load. | closed |
| T-18-11 | Information Disclosure | the repointed shortlist link pointing at an ungated route | high | mitigate | The link (`AdminDigestPage.jsx:998`) resolves to the `admin/materials/:id` route shipped in 18-02, which loads through the `require_admin`-gated endpoint; the route's own Playwright cases prove an employee sees `ForbiddenPage` rather than the draft. | closed |
| T-18-SC | Tampering | package-manager installs | high | accept | This phase installs zero packages (`18-RESEARCH.md` § Package Legitimacy Audit: not applicable). `git diff 3754f87 HEAD --stat -- package.json package-lock.json web/package.json web/package-lock.json pyproject.toml uv.lock` → 0 lines: no `uv add`, no `npm install`, no lockfile change. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-18-01 | T-18-05 | Granted `allow-popups-to-escape-sandbox` lets the popup leave the sandboxed origin, but `allow-scripts` is withheld at the frame, so the frame body cannot open a popup without a user click; the frame's markup is backend-rendered with `html.escape` only. Granting plain `allow-popups` instead would leave the reader SPA inert in the new tab and defeat the fix. Residual risk accepted as bounded by the withheld script token. | Phase 18 code review (findings focus #3, verified clean) | 2026-10-15 |
| AR-18-02 | T-18-SC | No package installs this phase, so no package-legitimacy gate applies. | 18-01-PLAN.md `must_haves` | 2026-10-15 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-15 | 12 | 12 | 0 | gsd-secure-phase (orchestrator, ASVS L1, grep-depth) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-15
