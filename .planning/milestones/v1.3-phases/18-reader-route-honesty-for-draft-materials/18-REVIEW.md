---
phase: 18-reader-route-honesty-for-draft-materials
reviewed: 2026-10-15T12:03:37Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - backend/src/backend/application/use_cases/get_material_for_preview.py
  - backend/src/backend/application/use_cases/email_render.py
  - backend/src/backend/interface/http/routes/admin.py
  - web/src/services/adminApi.js
  - web/src/App.jsx
  - web/src/pages/MaterialPage.jsx
  - web/src/pages/AdminDigestPage.jsx
  - tests/unit/test_get_material_for_preview.py
  - tests/unit/test_http_admin.py
  - tests/unit/test_http_materials.py
  - tests/unit/test_email_render.py
  - tests/admin.spec.js
findings:
  critical: 1
  warning: 2
  info: 5
  total: 8
status: issues_found
---

# Phase 18: Code Review Report

**Reviewed:** 2026-10-15T12:03:37Z
**Depth:** standard (plus one empirical browser verification of the top finding)
**Files Reviewed:** 12
**Status:** issues_found

## Summary

Phase 18 adds an admin-gated draft preview surface across three plans: `GET /admin/materials/{slug}` (`get_material_for_preview` + `_to_preview_response`), the SPA route `admin/materials/:id` reusing `MaterialPage` with an additive `preview` prop, and link/CTA honesty (`target`/`rel` on the email CTA, the widened iframe sandbox, the shortlist repoint). The backend half is well built and the threat register is genuinely mitigated; the frontend half contains **one reachable, empirically reproduced regression that renders the reader route permanently blank after any preview→reader handoff**.

`files_reviewed` covers every production file plus the four test files the phase touched (`git diff --name-only 3754f87..HEAD`, planning artifacts excluded).

### Answers to the requested review focus

1. **`require_admin` gate / slug-existence oracle — clean.** `read_material_preview` resolves `Depends(require_admin)` (which itself depends on `get_principal`, i.e. JWT verify + corporate-domain gate) before `_require_materials` and `get_material_for_preview` ever run in the body, so an employee gets `403 forbidden` and an anonymous caller `401` for *any* slug — existing or not. Draft/ready/unknown all collapse into the opaque `404 material_not_found` for an admin. No draft can leak to a non-admin on this route, and the reader route keeps its role-free 404 (pinned by `test_materials_draft_slug_returns_404_for_admin_token_too`). No oracle found.
2. **`no-store` correctness — correct where it matters, incomplete on error paths.** The header is set on the preview route only, via the declared `Response` parameter; grep over `backend/src/backend` shows no middleware and no other route touching `Cache-Control`, so it cannot leak onto the reader route (also pinned by `test_materials_ready_response_is_not_no_store`). See IN-02 for the error-path gap (no leak, but a heuristically cacheable 404).
3. **Iframe sandbox token set — verified safe and justified.** `AdminDigestPage.jsx:876` is exactly `allow-popups allow-popups-to-escape-sandbox`; `allow-scripts` and `allow-same-origin` appear nowhere in the file (grep: 0 matches — the summary's own comment reword is what keeps that grep meaningful). `allow-popups-to-escape-sandbox` is *required* here: with plain `allow-popups` the popup would inherit the sandbox and the reader SPA would be inert in the new tab, defeating the fix. Because `allow-scripts` is withheld, the frame cannot open a popup without a user click, and the frame body is backend-rendered with `html.escape` only, so the escape token grants no auto-popup or script-assist primitive. No finding.
4. **Shared email href builder — cannot emit an admin URL.** `render_material_email_block` still builds `f"{base}/materials/{clean_slug}"` (`email_render.py:51`), `render_email_html` stays shared by `preview_digest_email` and `send_digest`, `preview_digest_email.py` got zero edits, and `test_preview_email_html_matches_send_html` is byte-identical and green. The new `target="_blank" rel="noopener noreferrer"` is an attribute-only change on the same anchor, and `rel="noreferrer"` also strips the Referer. No admin URL can reach recipient mail. No finding.
5. **The documented latent `redirectToReader`/`forbidden` reset — the assessment in `18-02-SUMMARY.md` is incomplete.** The preview→*preview* transition they analysed is indeed unreachable, but the missing reset is reachable through a path they did not consider: the D-12 `NOT_FOUND → <Navigate to=/materials/{slug}>` handoff from `/admin/materials/:id` to `/materials/:id`. React reconciles both routes' elements as the same `MaterialPage` component at the same position, so the instance (and its `redirectToReader` state) survives the route change. Rated **CR-01** and reproduced live in the browser (evidence below). The `forbidden` half stays latent — **WR-01**.

## Critical Issues

### CR-01: A stale `redirectToReader` survives the D-12 redirect — the reader route (and every later material navigation) renders nothing

**File:** `web/src/pages/MaterialPage.jsx:64` (state), `:77-114` (effect), `:79-80` (the two resets that exist), `:120-122` (unguarded early return)
**Verified also in:** `tests/admin.spec.js:1273-1282` (the test that cannot see it)

**Issue:** The effect resets `status` and `notFound` on every load but never resets `redirectToReader` (nor `forbidden`). `redirectToReader` is consumed by an early return that is **not** guarded by `preview`:

```jsx
if (redirectToReader) {
  return <Navigate to={`/materials/${slug}`} replace />
}
```

The reachable sequence is the phase's own D-12 design:

1. `/admin/materials/{ready-slug}` mounts `MaterialPage` with `preview` true (`App.jsx:40`).
2. `fetchMaterialPreview` rejects `NOT_FOUND` → `setRedirectToReader(true)` (`:96`).
3. The early return renders `<Navigate to="/materials/{slug}" replace />` → the router switches to route `materials/:id`, whose element is `<MaterialPage />` (no props), i.e. the **same component type at the same tree position** as `<MaterialPage preview />`. React reuses the instance and only updates props — the classic "component does not remount between routes rendering the same component" behaviour (independently evidenced by this file needing `setNotFound(false)` for the `/materials/a → /materials/b` case, which only makes sense if the instance is reused).
4. The effect re-runs on the `preview` deps change, resets `status`/`notFound`, loads the reader material — but `redirectToReader` is still `true`, so the render returns `<Navigate to={current url} replace />` again, i.e. `null`. The reader route's `material-not-found` / `material-prose` branch is never reached.

Because the `MaterialPage` instance stays mounted, **every subsequent in-app material navigation stays blank too** until a hard reload.

**Reproduced empirically** (Vite dev server on `127.0.0.1:5174` with `VITE_USE_MOCKS=true`, `window.__DIGEST_MOCK_ME_ROLE__='admin'`, Chromium):

| probe | URL after | `material-not-found` | `material-prose` | `h1` | `<main>` text |
|---|---|---|---|---|---|
| draft preview `/admin/materials/sql-dashboards-for-audit-reporting` | `/admin/materials/sql-dashboards-…` | 0 | 1 | `SQL Dashboards for Audit Reporting` | «Черновик — предпросмотр…» (correct) |
| **ready preview** `/admin/materials/building-production-rag-systems` | `/materials/building-production-rag-systems` | **0** | 0 | **none** | **empty** (defect) |
| control: same reader URL loaded fresh | `/materials/building-production-rag-systems` | **1** | 0 | `Материал не найден` | «Материал не найден…» (correct) |
| in-app navigation to a valid material after the redirect (`/materials/pgvector`) | `/materials/pgvector` | 0 | **0** | **none** | **empty** (defect spreads) |

Row 3 proves the reader route itself is fine and pins the cause to the stale flag, not to the loader or the mock data.

**User-facing reachability:** the only repointed link, `AdminDigestPage.jsx:997` «Открыть материал →» (`/admin/materials/{slug}`), appears on **ready** rows as well as the draft row — the phase's own amended assertion (`tests/admin.spec.js:895-900`) covers the ready row. Clicking it on a ready material now lands on a blank `/materials/{slug}` where the pre-phase code (link straight to `/materials/{slug}`) rendered the article. I drove that exact click path in the browser and reproduced the blank screen. In live mode it is worse than in mocks because the material genuinely exists.

**Fix** (the two lines `18-02-SUMMARY.md` itself proposed, now demonstrably required):

```jsx
useEffect(() => {
  let cancelled = false
  setStatus('loading')
  setNotFound(false)
  setRedirectToReader(false) // ← add
  setForbidden(false)        // ← add
  ...
}, [slug, loadKey, preview])
```

Equivalently (and defensively) guard the early return with the route identity: `if (preview && redirectToReader) { … }`. Ship it with the failing test from WR-02 — with the fix the reader surface renders; without it the assertion times out.

## Warnings

### WR-01: `forbidden` is never reset either — latent today, the same defect class as CR-01

**File:** `web/src/pages/MaterialPage.jsx:65`, `:104-107`, `:116-118`

**Issue:** The effect has the same gap for `forbidden` (`if (preview && forbidden) return <ForbiddenPage />`). Assessed reachability: it is **not reachable through the UI today** — a stale `forbidden` requires two different `/admin/materials/{slug}` values rendered by one mounted instance, and the only links into that route come from `/admin/digest` (different component → fresh mount); the only link out of `ForbiddenPage` leaves the route. Unlike CR-01, the `preview &&` guard also means it can never contaminate the reader route. So the summary's "latent, not reachable" call is correct *for this flag* — but the correct fix is the same single line as CR-01, and the moment a preview→preview link exists this becomes user-visible (a stale `ForbiddenPage` permanently replacing a now-permitted draft). Judge it a WARNING rather than an accepted risk.

**Fix:** `setForbidden(false)` in the effect body alongside `setRedirectToReader(false)` (CR-01). No test seam is needed beyond the one in WR-02.

### WR-02: The D-12 redirect test asserts only the URL, so it cannot detect CR-01

**File:** `tests/admin.spec.js:1273-1282`

**Issue:** `"ready-материал уходит на читательский маршрут без баннера"` asserts `toHaveURL(/^https?:\/\/[^/]+\/materials\/building-production-rag-systems$/)` and `material-preview-banner` count 0. Both hold *while the page renders nothing at all* (`<Navigate>` returns `null`), which is exactly what CR-01 does. The test therefore passes on the broken build — this is why a BLOCKER reached "all suites green". (The suite's own comments call the URL shape the "behavioural proof"; the URL is necessary but not sufficient.)

**Fix:** after the URL assertion, pin the rendered reader surface, e.g.

```js
await expect(page).toHaveURL(/^https?:\/\/[^/]+\/materials\/building-production-rag-systems$/)
// the reader route must actually render for this slug (absent from the reader mock → its 404 surface)
await expect(page.getByTestId("material-not-found")).toBeVisible()
```

(or `material-prose` for a slug present in `web/src/data/mock.js`). This is the RED that CR-01's fix needs.

## Info

### IN-01: `loadMaterial` is an unused prop — dead injection surface

**File:** `web/src/pages/MaterialPage.jsx:59`, `:70`
**Issue:** `loadMaterial` is read only to select the loader (`loadMaterial ?? (preview ? … : fetchMaterial)`); no caller ever passes it — `App.jsx:35` and `App.jsx:40` pass nothing, and no test in `tests/` passes it. It adds a public prop with no behaviour and no coverage.
**Fix:** drop it (and keep `preview` as the only seam), or add the test that uses it. Either way, do not leave an untested public prop.

### IN-02: `no-store` is set only on the success path

**File:** `backend/src/backend/interface/http/routes/admin.py:388`
**Issue:** `response.headers["Cache-Control"] = "no-store"` runs only after a successful lookup, so the 404 (`material_not_found`) and 503 (`materials_unavailable`) responses of this route carry no cache directive. 404 is heuristically cacheable per RFC 9111, so an intermediary could pin a "not previewable" verdict for a slug that is later reverted to `draft`. No draft content can leak (the 200 is the only body-bearing response and it is `no-store`), hence Info, not Warning.
**Fix:** set the header for the whole route — e.g. assign it before the `try`, or `.headers.setdefault(...)` in a small dependency shared with any future draft surface.

### IN-03: `_SLUG_PATTERN` is imported across route modules while its sibling helper is duplicated

**File:** `backend/src/backend/interface/http/routes/admin.py:44`, `:223-230` (and `routes/materials.py:18`, `:44-51`)
**Issue:** `admin.py` imports the underscore-private `_SLUG_PATTERN` from `routes/materials.py` and then declares its own `_require_materials`, which is a verbatim copy of the one in `materials.py`. The architecture rule asks for communication through a public surface; a private constant crossing modules plus a duplicated container guard is exactly the kind of drift that makes the two routes diverge later.
**Fix:** move `_SLUG_PATTERN` (and one shared `require_materials(request)` dependency) into `backend/interface/http/deps.py` or a small `routes/_common.py`, and import the public name from both routes.

### IN-04: `mockSeatRole()` re-implements `meApi`'s role resolution

**File:** `web/src/services/adminApi.js:307-315` (vs `web/src/services/meApi.js:44-49`)
**Issue:** `adminApi`'s local `mockSeatRole()` duplicates `meApi`'s `resolveMockRole()` logic against the same `window.__DIGEST_MOCK_ME_ROLE__` convention (with a different fallback: `'employee'` vs meApi's module-local `mockRole`). The summary's claim that this is "the same convention the /me mock uses" is true, but it is a copy, not a shared source.
**Fix:** export a single `resolveMockRole()` from `meApi.js` (or a tiny `authEnv` helper) and import it here so the two can never disagree.

### IN-05: An expired session on the preview endpoint is reported as a network failure

**File:** `web/src/services/adminApi.js:215-231` (used by `fetchMaterialPreview` at `:370-372`)
**Issue:** `mapHttpError` has no 401 branch, so it falls through to `code: 'NETWORK', retryable: true`. On the new preview surface an expired token therefore renders `<ServiceUnavailable>` («Не удалось загрузить материал. Проверьте сеть.») instead of a re-auth path — the mock branch, by contrast, throws an explicit `UNAUTHORIZED`. Inherited helper behaviour, newly exposed by this route, hence Info.
**Fix:** add `if (response.status === 401) return new AdminApiError('Сессия истекла. Войдите снова.', { code: 'UNAUTHORIZED', retryable: false })` — mirroring `contentApi.js:347-352`.

---

_Reviewed: 2026-10-15T12:03:37Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
