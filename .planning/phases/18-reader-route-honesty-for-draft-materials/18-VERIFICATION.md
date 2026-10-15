---
phase: 18-reader-route-honesty-for-draft-materials
verified: 2026-10-15T12:55:00Z
status: passed
score: 20/20 must-haves verified
covered_files:
  - .planning/phases/18-reader-route-honesty-for-draft-materials/18-01-PLAN.md
  - .planning/phases/18-reader-route-honesty-for-draft-materials/18-01-SUMMARY.md
  - .planning/phases/18-reader-route-honesty-for-draft-materials/18-02-PLAN.md
  - .planning/phases/18-reader-route-honesty-for-draft-materials/18-02-SUMMARY.md
  - .planning/phases/18-reader-route-honesty-for-draft-materials/18-03-PLAN.md
  - .planning/phases/18-reader-route-honesty-for-draft-materials/18-03-SUMMARY.md
  - backend/src/backend/application/use_cases/email_render.py
  - backend/src/backend/application/use_cases/get_material_for_preview.py
  - backend/src/backend/interface/http/routes/admin.py
  - tests/admin.spec.js
  - tests/unit/test_email_render.py
  - tests/unit/test_get_material_for_preview.py
  - tests/unit/test_http_admin.py
  - tests/unit/test_http_materials.py
  - web/src/App.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/MaterialPage.jsx
  - web/src/services/adminApi.js

covered_digest: "v2:sha256:beb41051c4117cf7a588a8f569966be1d4e54368f7ac29158305d40e13b46297"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 12
  total: 12
  not_honored: []
unverified_prohibitions: 3
prohibitions:
  - statement: "MUST NOT present unpublished material as published on any surface — a draft must never be served by the public reader route, must never enter the digest email or the send pool, and wherever draft content is shown it must carry a visible not-published marker."
    verification: judgment
    requirement_id: ADUX-07
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "tests/unit/test_http_materials.py#test_materials_draft_slug_returns_404_not_403; #test_materials_draft_slug_returns_404_for_admin_token_too; tests/admin.spec.js#черновик открывается на предпросмотре с баннером (material-preview-banner)"
    flagged: "unverified-prohibition — human review recommended"
  - statement: "MUST NOT expose an unpublished material's `related` or `tags` — a draft's neighbours and taxonomy can themselves be unpublished and internal, so the draft preview payload ships both as empty lists rather than a filtered projection."
    verification: judgment
    requirement_id: ADUX-08
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "tests/unit/test_http_admin.py#test_admin_material_preview_draft_returns_200_reader_dto (tags == [] and related == [] on a draft carrying two tags and one ready related id)"
    flagged: "unverified-prohibition — human review recommended"
  - statement: "MUST NOT turn the preview surface into a second copy of the reader contract — `MaterialReaderResponse` gains no `status`/`preview` field, `get_material_for_reader` is never widened, and 'draft ≡ missing' on the reader route stays true."
    verification: judgment
    requirement_id: ADUX-07
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "backend/src/backend/interface/http/routes/materials.py:29-43 (no status field); git diff 3754f87..HEAD -- get_material_for_reader.py is empty; tests/unit/test_http_admin.py#test_admin_material_preview_slug_key_parity_with_reader"
    flagged: "unverified-prohibition — human review recommended"
human_verification:
  - test: "Sign off prohibition 1 — no unpublished material presented as published. Check the reader route, the digest email renderer and the admin preview: confirm a draft is never served as published anywhere and always carries the «Черновик — предпросмотр, не опубликовано» marker."
    expected: "A draft is reachable only behind `require_admin`, is 404 on `/materials/{slug}` for every token, never enters the email/send pool, and the preview carries the marker."
    why_human: "Declared `verification: judgment` in 18-01-PLAN.md `must_haves.prohibitions` — a must-NOT truth with no wired test-tier enforcement; the framework routes judgment prohibitions to the end-of-phase human checkpoint. The playwright/unit evidence below is strong but does not discharge a judgment item."
  - test: "Sign off prohibition 2 — no unpublished `related`/`tags` exposure. Confirm shipping both collections as `[]` (rather than a ready-filtered projection) is the intended, complete answer for the preview surface."
    expected: "The preview payload's `tags`/`related` are empty by design, and no other draft-facing surface projects unpublished taxonomy/neighbours."
    why_human: "Judgment-tier must-NOT (privacy). Test evidence: `test_admin_material_preview_draft_returns_200_reader_dto` asserts both arrays empty on a draft that actually carries two tags and a ready related id."
  - test: "Sign off prohibition 3 — the preview surface is not a second copy of the reader contract. Confirm `MaterialReaderResponse` staying status-free and `get_material_for_reader` staying ready-only are intent, not just current shape."
    expected: "`MaterialReaderResponse` has no `status`/`preview` field; `get_material_for_reader` is unchanged; 'draft ≡ missing' on the reader route remains the contract."
    why_human: "Judgment-tier must-NOT (transparency). Structural evidence: the DTO field list is status-free and `git diff` shows the use case and reader route are byte-identical, but the intent claim needs a human."
---

# Phase 18: Reader-route honesty for draft materials Verification Report

**Phase Goal:** An admin can open any draft (or ready) material at an admin-gated preview and read it in the normal reader rendering, while ordinary readers still get an opaque 404 and no unpublished content is exposed.
**Verified:** 2026-10-15T12:55:00Z
**Status:** human_needed
**Re-verification:** No — initial verification (covers the CR-01 fix already on HEAD `0791173`)

> **Headline:** all four ROADMAP success criteria and all 20 derived must-have truths are **✓ VERIFIED** with automated evidence, `behavior_unverified` is **0**, and there are **no gaps**. The `human_needed` status is driven **solely** by the three `must_haves.prohibitions` in `18-01-PLAN.md`, which are `verification: judgment` and therefore route to the end-of-phase human checkpoint (LLM-judge verdicts recorded below, non-authoritative). **No `/gsd-plan-phase --gaps` cycle is warranted.**

## Evidence base (independently re-run this session, not taken from SUMMARYs)

| Check | Command | Result |
|---|---|---|
| Backend unit + HTTP suite | `.venv\Scripts\python.exe -m pytest -q` | **836 passed**, 1 warning, 7.58 s |
| Full SPA Playwright project | `npx playwright test --project=web` | **110 passed** (2.5 m), incl. all 5 Phase-18 specs and the CR-01 click-path test |
| Reader route / use case immutability | `git diff 3754f87 HEAD -- backend/.../routes/materials.py backend/.../get_material_for_reader.py backend/.../preview_digest_email.py` | **empty** (byte-identical) |
| Preserved test files | `git diff 3754f87 HEAD -- tests/web-app.spec.js tests/unit/test_preview_digest.py` | **empty** |
| Tripwire byte-identity | `git diff 3754f87 HEAD -- tests/unit/test_http_materials.py \| grep '^-'` | only the `--- a/` header — **pure addition**, `test_materials_draft_slug_returns_404_not_403` untouched |
| Debt-marker gate | `Select-String 'TBD\|FIXME\|XXX'` over all 12 changed impl/test files | **0 matches** |
| Acceptance greps | `email_render.py` for `/admin/`; `AdminDigestPage.jsx` for `allow-scripts\|allow-same-origin`; `admin.py` for `no-store` | 0 / 0 / exactly 1 |
| Decision-coverage gate | `gsd-tools query check.decision-coverage-verify` | **12/12 honored**, `not_honored: []` |

**Environment pitfall check:** before the Playwright run I confirmed **no listener on 127.0.0.1:5174** (`netstat`/`Get-NetTCPConnection` returned nothing), so Playwright started its own fresh Vite dev server. No `ERR_CONNECTION_REFUSED` signature appeared; the run was clean. The stale-server illusion recorded by the 18-02/18-03 executors did not affect this verification.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| **SC1** | | | |
| 1 | Admin `GET /admin/materials/{slug}` for a draft → 200 with the reader DTO's exact key set `{slug,title,dek,body_markdown,format,provenance,tags,related,reading_minutes,published_at,editor}`, `tags==[]`, `related==[]`, no `status` key | ✓ VERIFIED | `test_admin_material_preview_draft_returns_200_reader_dto` (exact key-set + `"status" not in body` + `body["body_markdown"] == "## Draft\n\nDraft body."`); route `admin.py:358-389` |
| 2 | The preview renders the draft in the **normal reader rendering** — same `MaterialPage`, same `react-markdown`+`rehypeSlug`+`rehypeSanitize` pipeline, same `material-prose` container — plus the persistent banner «Черновик — предпросмотр, не опубликовано» | ✓ VERIFIED | `tests/admin.spec.js#черновик открывается на предпросмотре с баннером` (banner visible + exact copy, H1 title, `material-prose` count 1); `App.jsx:40` reuses `MaterialPage`; `MaterialPage.jsx:223-235` renders through the same pipeline |
| 3 | The admin shortlist's «Открыть материал →» on a **draft** row opens the admin preview with the banner (backlog 999.1's symptom closed) | ✓ VERIFIED | `tests/admin.spec.js#черновик: «Открыть материал →» ведёт на админ-предпросмотр…` (URL `/admin/materials/sql-dashboards-…` + banner visible); link repointed at `AdminDigestPage.jsx:998` |
| 4 | The preview endpoint is gated by `require_admin` (DB `profiles.role`); a corporate employee → 403, anonymous → 401 | ✓ VERIFIED | `test_admin_material_preview_employee_returns_403` (`detail == "forbidden"`), `test_admin_material_preview_anonymous_returns_401`; `admin.py:374` `Depends(require_admin)` |
| **SC2** | | | |
| 5 | `GET /materials/{slug}` and `get_material_for_reader` are byte-identical to their pre-phase source | ✓ VERIFIED | `git diff 3754f87 HEAD` for `routes/materials.py` + `get_material_for_reader.py` is **empty** |
| 6 | A draft slug on the reader route → opaque 404 `material_not_found` (never 403) for an ordinary reader | ✓ VERIFIED | `test_materials_draft_slug_returns_404_not_403` (PRESERVE tripwire, byte-identical, green) |
| 7 | The reader route has **no role branch**: an admin token gets the same opaque 404 | ✓ VERIFIED | `test_materials_draft_slug_returns_404_for_admin_token_too` (seeds `role="admin"`, still 404 `material_not_found`), landed as a test-only characterisation pin with zero production edits |
| 8 | 403 comes only from the role gate, 404 only from the slug lookup — unknown/`ready` slugs answer 404 for an admin, so no slug-existence oracle | ✓ VERIFIED | `…employee_returns_403`, `…unknown_slug_returns_404`, `…ready_slug_returns_404`, `…outcomes_are_status_driven`; no case asserts 403 for a non-draft admin request |
| 9 | Edge — a slug violating `_SLUG_PATTERN` (empty / non-ASCII / consecutive or trailing hyphen) is refused at validation (404 or 422) — never 200, never 403 | ✓ VERIFIED | `test_admin_material_preview_malformed_slug_never_succeeds` (`--bad--`, bare `/admin/materials/`, `Привет-мир`); pattern imported verbatim from `materials.py:18` |
| **SC3** | | | |
| 10 | Only the draft-preview response carries `Cache-Control: no-store`; the reader response does not | ✓ VERIFIED | `test_admin_material_preview_draft_has_no_store` (`cache-control == "no-store"`); `test_materials_ready_response_is_not_no_store`; single header line `admin.py:388` — **on the body-bearing 200** |
| 11 | The preview exposes no unpublished `related`/`tags`: both ship as `[]` and the page renders neither block nor a «Связанные материалы» heading | ✓ VERIFIED | `test_admin_material_preview_draft_returns_200_reader_dto` (`tags==[]`, `related==[]` despite two tags + one ready related id); Playwright asserts `material-tags`, `material-related` and the heading at count 0 |
| 12 | Edge — repeated preview reads are byte-identical and write nothing; the use case and route hold no module-level mutable state or write path | ✓ VERIFIED | `test_admin_material_preview_repeat_is_identical_and_writes_nothing` (`first.json()==second.json()`, before/after `status`/`body_markdown`/`updated_at` equal); source scan: no `global`, no `.save`/`.update`/`.mark_` in the use case or route |
| **SC4** | | | |
| 13 | The email-preview «Читать →» anchor carries `target="_blank" rel="noopener noreferrer"` in both the backend renderer and the SPA mock mirror | ✓ VERIFIED | `email_render.py:53`; `tests/unit/test_email_render.py#test_render_material_email_block_read_link_opens_in_new_context` + `#…render_email_html_material_link…`; `adminApi.js:572` mock mirror |
| 14 | The email-preview iframe is `sandbox="allow-popups allow-popups-to-escape-sandbox"` with `allow-scripts`/`allow-same-origin` **absent**, and clicking the CTA opens a new top-level context | ✓ VERIFIED | `AdminDigestPage.jsx:875`; `tests/admin.spec.js#превью письма: «Читать →» открывает новую вкладку из песочницы` (Playwright `popup` event fires + attribute equality + two `not.toContain` asserts); grep for the withheld tokens → 0 |
| 15 | The shared email href stays `{base}/materials/{slug}` for preview and the real send; the parity test and every `/materials/` href assertion are unmodified | ✓ VERIFIED | `email_render.py:51` single `/materials/{clean_slug}`; `git diff` shows **only additions** to `test_email_render.py`; `tests/unit/test_preview_digest.py` unchanged & green; grep `/admin/` in `email_render.py` → 0 |
| 16 | Edge — a blank/whitespace slug emits no anchor (so `target`/`rel` can never sit on a dead link); both renderers are idempotent | ✓ VERIFIED | `#test_render_material_email_block_blank_slug_emits_no_anchor_attributes` (`""` and `"   "`), `#test_render_material_email_block_is_idempotent` |
| **Cross-cutting (reader-path regression + wiring)** | | | |
| 17 | A `ready`/unknown slug on the preview route lands on the reader route via a client-side `<Navigate replace>` — no 307, no opaque-redirect handling — with no draft marker | ✓ VERIFIED | `MaterialPage.jsx:104-107,128-130`; `tests/admin.spec.js#ready-материал уходит на читательский маршрут без баннера` (host-anchored URL + banner count 0); grep `redirect\|opaqueredirect` in `adminApi.js` → 0 |
| 18 | An ordinary reader who guesses the preview URL sees `ForbiddenPage` for **both** an existing and a nonexistent slug — no slug-existence signal, no `/me` round trip | ✓ VERIFIED | `tests/admin.spec.js#сотрудник на предпросмотре черновика…` + `#…неизвестного slug видит тот же Forbidden` (identical screen, `service-unavailable` count 0); `MaterialPage.jsx:120-122`; no `fetchMe`/`meApi` in page or service |
| 19 | The reader route `/materials/:id` is behaviourally unchanged: unknown id renders «Материал не найден» with recovery links; `tests/web-app.spec.js` unmodified and green; the reader branch passes no props | ✓ VERIFIED | `App.jsx:35` `<MaterialPage />` no props; `git diff` for `tests/web-app.spec.js` empty (its not-found case green in the 110-pass run); `MaterialPage.jsx:150-169` |
| 20 | The SPA reaches the preview endpoint only through `web/src/services/adminApi.js` (`fetchMaterialPreview`); no bare `fetch` in the page/`App.jsx`; the mock branch resolves against the shortlist batch (never `data/mock.js`) | ✓ VERIFIED | `adminApi.js:327-376` (live Bearer branch + `mockSeatRole()` gate before slug lookup, `mockBatch.items.find`, requires `material_status === 'draft'`); grep `/admin/materials/` in `web/src` → only `adminApi.js` |

**Score:** 20/20 truths verified (**0** present-but-behavior-unverified)

**Behavior-dependent truths (Step 3):** truth 17 is the phase's load-bearing state transition (the `NOT_FOUND → /materials/{slug}` handoff plus the effect's reset invariant). It is **✓ VERIFIED**, not `PRESENT_BEHAVIOR_UNVERIFIED`, because a behavioral test exercises it end-to-end: `tests/admin.spec.js:1289` «клик по «Открыть материал →» на готовой строке рендерит читательский маршрут, а не пустоту» asserts `material-not-found` is *visible* after the handoff. That test was landed RED in `99d8dd9` (failed `expect(locator).toBeVisible() — element(s) not found`) and turned GREEN by `14ea4de`, which added `setRedirectToReader(false)` / `setForbidden(false)` to the effect (`MaterialPage.jsx:88-89`). The pre-existing D-12 test could not observe this because `gotoAsRole` ends in `page.reload()` after the redirect has already moved the document (documented as WR-02 in the test file).

**Coincidental-reliance check (advisory, #1955):** none. Every passing truth's evidence names a precondition the code itself establishes (the `require_admin` dependency, the route's `preview` prop, the DTO defaults) or ordering the code enforces (the mock seat-role gate runs before the slug lookup; the `no-store` header is set before the return). No `coincidental_reliance_items`.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `backend/src/backend/application/use_cases/get_material_for_preview.py` (NEW) | draft-only read by slug | ✓ VERIFIED | 15 lines, substantive; `DRAFT` → material, `None`/`READY` → `MaterialNotFoundError`; no `fastapi`/`httpx`/`supabase` import; wired by the route |
| `backend/src/backend/interface/http/routes/admin.py` (MODIFIED) | `GET /admin/materials/{slug}` + `_to_preview_response` | ✓ VERIFIED | route at `:358-389` with `Depends(require_admin)` and `Path(..., pattern=_SLUG_PATTERN)`; `_to_preview_response` at `:275-293` ships `tags=[]`/`related=[]` and omits `editor` so the DTO default applies; exactly one `no-store` line |
| `tests/unit/test_get_material_for_preview.py` (NEW) | use-case RED gate | ✓ VERIFIED | 3 cases against `InMemoryMaterialRepository`; green |
| `tests/unit/test_http_admin.py` (MODIFIED) | preview-route cases | ✓ VERIFIED | 9 preview cases (`_preview_env` helper) incl. DTO shape, `no-store`, key parity, edge slugs, read-only; green |
| `tests/unit/test_http_materials.py` (MODIFIED) | admin-token 404 pin + reader no-`no-store`; tripwire PRESERVED | ✓ VERIFIED | pure-addition diff; tripwire byte-identical |
| `tests/unit/test_email_render.py` (MODIFIED) | `target`/`rel` + blank-slug + idempotency assertions | ✓ VERIFIED | pure-addition diff; pre-existing href asserts intact |
| `web/src/services/adminApi.js` (MODIFIED) | `fetchMaterialPreview` + mock anchor attributes | ✓ VERIFIED | `:327-376` service + `:572` mock mirror; `mapHttpError` reused (403→FORBIDDEN, 404→NOT_FOUND) |
| `web/src/App.jsx` (MODIFIED) | `admin/materials/:id` route | ✓ VERIFIED | `:40` `<Route path="admin/materials/:id" element={<MaterialPage preview />} />`; reader route `:35` unchanged |
| `web/src/pages/MaterialPage.jsx` (MODIFIED) | additive props, banner, redirect, forbidden | ✓ VERIFIED | 281 lines; banner `:182-188`; CR-01 reset `:82-89`; no `material.status` reference |
| `web/src/pages/AdminDigestPage.jsx` (MODIFIED) | iframe sandbox + shortlist repoint | ✓ VERIFIED | `:875` sandbox; `:998` `/admin/materials/${slug}` |
| `backend/src/backend/application/use_cases/email_render.py` (MODIFIED) | anchor `target`/`rel`; href unchanged | ✓ VERIFIED | `:53`; `DEFAULT_SITE_URL`, interstitial renderer, blank-slug guard, `render_email_html` byte-identical |
| `tests/admin.spec.js` (MODIFIED) | new specs + amended assertions | ✓ VERIFIED | 5 new Phase-18 specs; 4 amended assertions (`:408`, `:694`, `:736`, `:869`); no `test.skip`, no remaining `sandbox=""` |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `web/src/App.jsx` | `web/src/pages/MaterialPage.jsx` | `<MaterialPage preview />` on `admin/materials/:id` | ✓ WIRED | `App.jsx:40`; `:id` keeps `useParams()` unchanged |
| `web/src/pages/MaterialPage.jsx` | `web/src/services/adminApi.js` | `loader = loadMaterial ?? (preview ? fetchMaterialPreview : fetchMaterial)` | ✓ WIRED | `:70`; no bare `fetch(` call in the component |
| `web/src/services/adminApi.js` | `backend/.../routes/admin.py` | `GET ${apiBase()}/admin/materials/${slug}` | ✓ WIRED | `:362-364` live branch |
| `backend/.../routes/admin.py` | `get_material_for_preview.py` | `get_material_for_preview(materials, slug)` → `MaterialNotFoundError` → 404 | ✓ WIRED | `:376-384` |
| `get_material_for_preview.py` | `MaterialRepository.get_by_slug` | existing port, no new adapter/port | ✓ WIRED | `:13` |
| `MaterialPage.jsx` | `ForbiddenPage.jsx` | `preview && code === "FORBIDDEN"` → `<ForbiddenPage />` | ✓ WIRED | `:104-107`, `:120-122` |
| `MaterialPage.jsx` | reader route | `NOT_FOUND` + `preview` → `<Navigate to={/materials/${slug}} replace />` | ✓ WIRED | `:104-106`, `:128-130` |
| `AdminDigestPage.jsx` | `admin/materials/:id` route | shortlist `<Link to={/admin/materials/${slug}}>` | ✓ WIRED | `:998`; resolves against `App.jsx:40` |
| `email_render.py` | `adminApi.js` mock mirror | shared `rel="noopener noreferrer"` attribute set | ✓ WIRED | `email_render.py:53` ↔ `adminApi.js:572` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `MaterialPage.jsx` (preview route) | `material` (title, `body_markdown`, `provenance`, `reading_minutes`, `published_at`, `editor`) | `fetchMaterialPreview` → live `GET /admin/materials/{slug}` (Bearer) or the mock shortlist-batch branch resolving a `draft` item | Yes (live branch hits the real endpoint; the backend `test_…draft_returns_200_reader_dto` asserts a non-empty `body_markdown` from a real `Material`) | ✓ FLOWING |
| `MaterialPage.jsx` | `material-preview-banner` | the route's `preview` prop | n/a — route-derived by design (the DTO has no `status`; a payload check would be dead code, Pitfall 5) | ✓ FLOWING (intentional) |
| `MaterialPage.jsx` | `tags` / `related` | payload `tags: []`, `related: []` | n/a — constant by **requirement** (D-08), not a hollow prop; the page's pre-existing `length > 0` gates then hide both blocks | ✓ FLOWING (D-08 constant) |

*No `STATIC`/`DISCONNECTED`/`HOLLOW_PROP` findings.* The only "empty looking" values are the D-08-mandated empty collections, pinned as such by `test_admin_material_preview_draft_returns_200_reader_dto`.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Full backend suite | `.venv\Scripts\python.exe -m pytest -q` | `836 passed, 1 warning in 7.58s` | ✓ PASS |
| Full SPA Playwright project (incl. all 5 Phase-18 specs) | `npx playwright test --project=web` | `110 passed (2.5m)` | ✓ PASS |
| Phase-18 preview suite enumerates 9 named tests | `pytest tests/unit/test_http_admin.py --collect-only -q -k preview` (case names at `:1180-1341`) | 9 preview cases present | ✓ PASS |
| CR-01 rendered-surface pin passes on HEAD | Playwright case at `tests/admin.spec.js:1289` in the 110-pass run | green (was RED pre-`14ea4de`) | ✓ PASS |
| Reader route immutability | `git diff 3754f87 HEAD -- …/materials.py …/get_material_for_reader.py` | empty | ✓ PASS |
| Debt markers | `Select-String 'TBD\|FIXME\|XXX'` over 12 changed files | 0 | ✓ PASS |

### Probe Execution

N/A — this phase declares no probe scripts, and no `scripts/*/tests/probe-*.sh` exists in this repository. Skipped per Step 7c's discovery contract.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| **ADUX-07** | 18-01, 18-02, 18-03 | Admin can open any material (draft or ready) at an admin-gated preview and read it in the normal reader rendering; public `GET /materials/{slug}` stays ready-only and an unknown **or draft** slug returns an opaque 404 (never 403) | ✓ **SATISFIED** | Truths 1-9, 17-20. `require_admin` gate (`admin.py:374`); reader route + use case byte-identical; draft/unknown → 404 `material_not_found` for reader *and* admin tokens; preview reuses `MaterialPage`. `REQUIREMENTS.md:16` `[x]`, `:105` Traceability **Complete** |
| **ADUX-08** | 18-01, 18-03 | The admin shortlist and email-preview links target the admin preview surface; a draft preview is served non-cacheable (`no-store`) and carries a visible preview marker, exposing no `related`/`tags` of unpublished material | ✓ **SATISFIED** | Truths 3, 10-16. Shortlist link repointed (`AdminDigestPage.jsx:998`); CTA escapes the sandbox behaviourally (D-11); `no-store` on the body-bearing 200; marker visible; `tags`/`related` empty. `REQUIREMENTS.md:17` `[x]`, `:106` **Complete** |

**Orphaned requirements:** none. `grep "Phase 18" .planning/REQUIREMENTS.md` returns only ADUX-07/ADUX-08, and both are declared in the `requirements:` frontmatter of all three plans.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `tests/unit/test_get_material_for_preview.py` | ADUX-07 | 3 | 0 | No | Behavioral (`pytest.raises` on typed error) | ✓ PASS |
| `tests/unit/test_http_admin.py` | ADUX-07, ADUX-08 | 9 preview (+ suite) | 0 | No | Value/Status (exact key set, exact header, exact codes) | ✓ PASS |
| `tests/unit/test_http_materials.py` | ADUX-07 | 2 new | 0 | No | Value (`detail == "material_not_found"`, header absence) | ✓ PASS |
| `tests/unit/test_email_render.py` | ADUX-08 | 4 new | 0 | No | Value (substring on exact attributes) | ✓ PASS |
| `tests/admin.spec.js` | ADUX-07, ADUX-08 | 5 new | 0 | No | Behavioral (banner, click-path handoff, popup event, sandbox equality) | ✓ PASS |

**Disabled tests on requirements:** 0 → no BLOCKER (grep for `test.skip`/`describe.skip`/`pytest.mark.skip`/`it.todo` over the phase files → 0).
**Circular patterns detected:** 0 → no BLOCKER (no fixture-generating script imports the system under test).
**Insufficient assertions:** 0. Note the strong assertion upgrade the review gate forced: the D-12 redirect is pinned not merely by a URL match (which held while the page rendered `null`) but by `material-not-found` visibility, plus `material-prose` attachment and sandbox `not.toContain` guards.

### Decision Coverage (non-blocking gate)

12/12 trackable `18-CONTEXT.md` decisions are honored by shipped artifacts; `not_honored: []`. Notably: D-01/D-02 (dedicated admin route + reader-DTO reuse), D-03 (`require_admin` DB gate, no client role logic), D-05 *as amended by* D-12 (client-side `NOT_FOUND → /materials/{slug}` redirect), D-06 (route-scoped banner), D-07 (`no-store` on the preview only), D-08 (empty `tags`/`related`), D-10 (shortlist repoint), D-11 (behavioural CTA escape; shared href unchanged; the shortlist link is the only repointed link).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No `TBD`/`FIXME`/`XXX` in any of the 12 changed files | — | Debt-marker gate clean |
| — | — | No stub/hollow/`return null`-only implementations in the preview path; the only "empty" values are the D-08-mandated `tags`/`related` constants | — | Not a stub |
| — | — | No disabled/skipped tests on either requirement | — | Not a blocker |

**Review findings disposition (18-REVIEW.md → 18-REVIEW-DISPOSITION.md):** CR-01 (critical) **FIXED** on HEAD and pinned by a behavioural test; WR-01 and WR-02 **FIXED**. Verified independently: `MaterialPage.jsx:82-89` resets `redirectToReader` and `forbidden`; `tests/admin.spec.js:1273-1282` carries the WR-02 NOTE and `:1289` is the rendered-surface proof. IN-01…IN-05 (info) are recorded `deferred` with reasons — I concur they are acknowledged rather than phase gaps, **with one caveat on IN-02** (see below).

### Notes / Documented Residual Limitations (non-blocking)

1. **IN-02 — `no-store` is set only on the success path.** `admin.py:388` sets the header only after a successful lookup, so the 404 (`material_not_found`) and 503 (`materials_unavailable`) responses of this route carry no cache directive. This does **not** affect success criterion 3, which is about "a draft preview **response**" — the 200 is the only body-bearing response and it *is* `no-store`. Agreed as `deferred`, not a gap; worth a follow-up if an intermediary caching a 404 is ever a concern.
2. **Browser-suite observability.** The only draft seed (`adminReadyMock.js` material 104) has `char_count: 0` and no `body_markdown`, so the Playwright spec asserts `material-prose` **attached (count 1)**, never visible; the non-empty draft body is proven at the unit level instead (`body["body_markdown"] == "## Draft\n\nDraft body."`). The `adminReadyMock.js` seed and the unused `prose-column` class are both outside this phase's `files_modified` — acknowledged, not a gap.
3. **Email-preview popup landing page is deliberately unasserted.** The mock href host is `127.0.0.1:5173` while the Playwright `web` project serves on `5174`, so only the `popup` event is asserted. Correct scoping — criterion 4 asks that the CTA is not trapped in the sandbox, which the popup event proves.
4. **IN-01/IN-03/IN-04/IN-05** — acknowledged `deferred` info items (inert `loadMaterial` prop; cross-module `_SLUG_PATTERN` import + duplicated `_require_materials`; duplicated `mockSeatRole`; 401 mapped to NETWORK). None affects a success criterion; I agree with the dispositions.

### Human Verification Required

The phase's three `must_haves.prohibitions` (`18-01-PLAN.md`) are `verification: judgment`; they are flagged `unverified-prohibition — human review recommended` and require sign-off at the end-of-phase checkpoint.

### 1. Prohibition 1 — no unpublished material presented as published

**Test:** Inspect the reader route, the digest email renderer and the admin preview together. Confirm a draft is never served as published on any surface, never enters the email/send pool, and always carries the not-published marker where shown.
**Expected:** Draft reachable only behind `require_admin`; 404 on `/materials/{slug}` for every token; never in the email pool; preview carries «Черновик — предпросмотр, не опубликовано».
**Why human:** Judgment-tier must-NOT with no wired test-tier enforcement (LLM judge: NOT VIOLATED; test evidence: `test_materials_draft_slug_returns_404_not_403`, `…for_admin_token_too`, the banner spec).

### 2. Prohibition 2 — no unpublished `related`/`tags` exposure

**Test:** Confirm shipping both collections as `[]` (rather than a ready-filtered projection) is the intended and complete answer for the preview surface.
**Expected:** Preview payload `tags`/`related` empty by design; no other draft-facing surface projects unpublished taxonomy/neighbours.
**Why human:** Judgment-tier privacy must-NOT (LLM judge: NOT VIOLATED; test evidence: both arrays empty on a draft carrying two tags and a ready related id).

### 3. Prohibition 3 — the preview surface is not a second copy of the reader contract

**Test:** Confirm that `MaterialReaderResponse` staying status-free and `get_material_for_reader` staying ready-only are intent, not merely current shape.
**Expected:** DTO has no `status`/`preview` field; the use case is unchanged; "draft ≡ missing" on the reader route remains the contract.
**Why human:** Judgment-tier transparency must-NOT (LLM judge: NOT VIOLATED; structural evidence: status-free DTO field list, empty `git diff`, key-parity test).

### Gaps Summary

**None.** Every ROADMAP success criterion and every derived must-have truth is `✓ VERIFIED` with independently reproduced automated evidence (836 backend tests, 110 Playwright tests, immutable reader route/use case, byte-identical tripwire, zero debt markers). The `human_needed` status is produced **only** by the three flagged judgment-tier prohibitions above — it is not a gap, and it does not warrant a `/gsd-plan-phase --gaps` cycle. The one critical regression found in review (CR-01) is fixed on HEAD (`14ea4de`) and pinned by a behavioural test (`99d8dd9` → green).

No deferred items: nothing in the phase's must-haves is addressed by a later milestone phase (Phase 19+ are the unsaved-changes guard, mail, nav grouping, ingest sources and scheduling — unrelated).

---

_Verified: 2026-10-15T12:55:00Z_
_Verifier: Claude (gsd-verifier)_
