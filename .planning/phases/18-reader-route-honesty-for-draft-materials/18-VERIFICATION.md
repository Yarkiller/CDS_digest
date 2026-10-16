---
phase: 18-reader-route-honesty-for-draft-materials
verified: 2026-10-16T10:59:33Z
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
covered_digest: "v2:sha256:03d0aafe335eb998ece09c5d11402d810d82de9fe22d5266fe870ff672fd98d9"
behavior_unverified: 0
overrides_applied: 0
decision_coverage:
  honored: 12
  total: 12
  not_honored: []
unverified_prohibitions: 0
prohibitions:
  - statement: "MUST NOT present unpublished material as published on any surface — a draft must never be served by the public reader route, must never enter the digest email or the send pool, and wherever draft content is shown it must carry a visible not-published marker."
    verification: judgment
    requirement_id: ADUX-07
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "tests/unit/test_http_materials.py#test_materials_draft_slug_returns_404_not_403; #test_materials_draft_slug_returns_404_for_admin_token_too; tests/admin.spec.js#черновик открывается на предпросмотре с баннером; 18-UAT.md test 1 result:pass"
    flagged: false
    human_signed_off: "18-UAT.md (2026-10-15) — result: pass"
  - statement: "MUST NOT expose an unpublished material's `related` or `tags` — a draft's neighbours and taxonomy can themselves be unpublished and internal, so the draft preview payload ships both as empty lists rather than a filtered projection."
    verification: judgment
    requirement_id: ADUX-08
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "tests/unit/test_http_admin.py#test_admin_material_preview_draft_returns_200_reader_dto; 18-UAT.md test 2 result:pass"
    flagged: false
    human_signed_off: "18-UAT.md (2026-10-15) — result: pass"
  - statement: "MUST NOT turn the preview surface into a second copy of the reader contract — `MaterialReaderResponse` gains no `status`/`preview` field, `get_material_for_reader` is never widened, and 'draft ≡ missing' on the reader route stays true."
    verification: judgment
    requirement_id: ADUX-07
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "MaterialReaderResponse status-free; git diff 3754f87..HEAD get_material_for_reader.py empty; test_admin_material_preview_slug_key_parity_with_reader; 18-UAT.md test 3 result:pass"
    flagged: false
    human_signed_off: "18-UAT.md (2026-10-15) — result: pass"
re_verification:
  previous_status: human_needed
  previous_score: 20/20
  previous_verified: 2026-10-15T12:55:00Z
  previous_covered_digest: "v2:sha256:beb41051c4117cf7a588a8f569966be1d4e54368f7ac29158305d40e13b46297"
  reason: "stale covered_digest (#4682) — covered source changed after prior verifier run (notably web/src/App.jsx via Phase 19 createBrowserRouter migration)"
  gaps_closed:
    - "Judgment-tier prohibitions 1–3 discharged by 18-UAT.md (status:complete, 3/3 pass) — no longer drive human_needed"
  gaps_remaining: []
  regressions: []
advisory: []
---

# Phase 18: Reader-route honesty for draft materials Verification Report

**Phase Goal:** An admin can open any draft (or ready) material at an admin-gated preview and read it in the normal reader rendering, while ordinary readers still get an opaque 404 and no unpublished content is exposed.
**Verified:** 2026-10-16T10:59:33Z
**Status:** passed
**Re-verification:** Yes — stale digest refresh (#4682); prior pass was `human_needed` only for judgment prohibitions (now UAT-signed); covered source changed (`App.jsx` data-router migration)

> **Headline:** all four ROADMAP success criteria and all 20 derived must-have truths remain **✓ VERIFIED** with freshly re-run automated evidence. `behavior_unverified` is **0**. Judgment prohibitions are **human-signed-off** via `18-UAT.md` (`status: complete`, 3/3 pass). `covered_digest` refreshed (`beb41051…` → `03d0aafe…`). Phase goal achieved.

## Evidence base (independently re-run this session, not taken from SUMMARYs)

| Check | Command | Result |
|---|---|---|
| Phase-18 unit files | `.venv\Scripts\python.exe -m pytest -q tests/unit/test_get_material_for_preview.py tests/unit/test_http_admin.py tests/unit/test_http_materials.py tests/unit/test_email_render.py` | **75 passed**, 1 warning, 3.41 s |
| Named tripwires + preview DTO/`no-store` | 5 named pytest cases (draft 404×2, reader no-`no-store`, draft 200 DTO, draft `no-store`) | **5 passed** |
| Phase-18 Playwright subset | `npx playwright test --project=web -g "предпросмотр\|черновик\|Читать\|Открыть материал\|Forbidden\|готовая строка\|sandbox\|баннер"` | **11 passed** (33.4 s); port 5174 was free |
| Reader route / use case immutability | `git diff 3754f87 HEAD -- …/routes/materials.py …/get_material_for_reader.py …/preview_digest_email.py` | **empty** (0 lines) |
| Preserved test files | `git diff 3754f87 HEAD -- tests/web-app.spec.js tests/unit/test_preview_digest.py` | **empty** |
| `gsd-tools` artifacts (18-01/02/03) | `query verify.artifacts` ×3 | **all_passed** (5+4+5) |
| `gsd-tools` key-links (18-01/02/03) | `query verify.key-links` ×3 | **all_verified** (5+4+3) |
| Debt-marker gate | `Select-String 'TBD\|FIXME\|XXX'` over 12 covered impl/test files | **0 matches** |
| Acceptance greps | `email_render.py` `/admin/`; `AdminDigestPage.jsx` `allow-scripts\|allow-same-origin` | 0 / 0 |
| Decision-coverage gate | `gsd-tools query check.decision-coverage-verify` | **12/12 honored** |
| Fingerprint | `gsd-tools query verification.fingerprint` | `v2:sha256:03d0aafe…` (refreshed) |
| Post-prior source change | `git log --since=2026-10-15T12:55:00Z -- web/src/App.jsx` | Phase 19 migrate to `createBrowserRouter`; `admin/materials/:id` → `<MaterialPage preview />` **still present** (line 37) |

**Orchestrator regression gate (accepted, not re-run):** 159 pytest files from phases 17/18/20 unit suites passed; `node --test tests/unit/test_unsaved_changes_guard.js` passed 3.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| **SC1** | | | |
| 1 | Admin `GET /admin/materials/{slug}` for a draft → 200 with reader DTO key set, `tags==[]`, `related==[]`, no `status` | ✓ VERIFIED | `test_admin_material_preview_draft_returns_200_reader_dto` (re-run green); `admin.py:275-293` `_to_preview_response`; route `admin.py:358-389` |
| 2 | Preview renders draft in **normal reader rendering** + banner «Черновик — предпросмотр, не опубликовано» | ✓ VERIFIED | Playwright `черновик открывается на предпросмотре с баннером` (in 11-pass run); `App.jsx:37` reuses `MaterialPage`; banner `MaterialPage.jsx:182-188` |
| 3 | Shortlist «Открыть материал →» on a **draft** opens admin preview with banner | ✓ VERIFIED | Playwright `черновик: «Открыть материал →» ведёт на админ-предпросмотр…`; link `AdminDigestPage.jsx:998` |
| 4 | Preview gated by `require_admin`; employee → 403, anonymous → 401 | ✓ VERIFIED | `test_admin_material_preview_employee_returns_403`, `…anonymous_returns_401`; `Depends(require_admin)` at `admin.py:373` |
| **SC2** | | | |
| 5 | `GET /materials/{slug}` and `get_material_for_reader` byte-identical to pre-phase | ✓ VERIFIED | `git diff 3754f87 HEAD` empty for both |
| 6 | Draft slug on reader → opaque 404 `material_not_found` (never 403) | ✓ VERIFIED | `test_materials_draft_slug_returns_404_not_403` (named re-run green) |
| 7 | Reader route has **no role branch** — admin token still 404 | ✓ VERIFIED | `test_materials_draft_slug_returns_404_for_admin_token_too` (named re-run green) |
| 8 | 403 only from role gate; unknown/`ready` → 404 for admin (no slug oracle) | ✓ VERIFIED | preview suite cases `…unknown_slug…`, `…ready_slug…`, `…outcomes_are_status_driven` collected + suite green |
| 9 | Malformed slug refused at validation (never 200/403) | ✓ VERIFIED | `test_admin_material_preview_malformed_slug_never_succeeds`; `_SLUG_PATTERN` imported from `materials.py` |
| **SC3** | | | |
| 10 | Only draft-preview 200 carries `Cache-Control: no-store` | ✓ VERIFIED | `test_admin_material_preview_draft_has_no_store` + `test_materials_ready_response_is_not_no_store` (named re-run); `admin.py:388` |
| 11 | Preview exposes no unpublished `related`/`tags` | ✓ VERIFIED | DTO test asserts both `[]`; Playwright banner suite asserts tags/related blocks absent |
| 12 | Repeat preview reads identical; no write path | ✓ VERIFIED | `test_admin_material_preview_repeat_is_identical_and_writes_nothing`; use case is pure read |
| **SC4** | | | |
| 13 | Email «Читать →» has `target="_blank" rel="noopener noreferrer"` (backend + mock) | ✓ VERIFIED | `email_render.py:54`; `adminApi.js:572`; email_render unit suite in 75-pass |
| 14 | Iframe `sandbox="allow-popups allow-popups-to-escape-sandbox"`; CTA opens top-level context | ✓ VERIFIED | Playwright D-11 popup case green; `AdminDigestPage.jsx:875`; greps for withheld tokens → 0 |
| 15 | Shared email href stays `{base}/materials/{slug}`; no `/admin/` in renderer | ✓ VERIFIED | `email_render.py:52`; grep `/admin/` → 0; `preview_digest_email.py` diff empty |
| 16 | Blank slug emits no anchor; renderers idempotent | ✓ VERIFIED | blank-slug / idempotent cases in `test_email_render.py` (suite green) |
| **Cross-cutting** | | | |
| 17 | Ready/unknown preview slug → client `<Navigate replace>` to reader (CR-01 reset) | ✓ VERIFIED | Playwright ready-redirect + CR-01 click-path cases green; `MaterialPage.jsx:87-88,128-130` |
| 18 | Ordinary reader on preview URL → `ForbiddenPage` for existing and nonexistent slug | ✓ VERIFIED | Playwright employee Forbidden cases (both) green; `MaterialPage.jsx:112-125` |
| 19 | Reader route `/materials/:id` behaviourally unchanged | ✓ VERIFIED | `App.jsx:32` `<MaterialPage />` no props; `web-app.spec.js` diff empty vs baseline |
| 20 | SPA reaches preview only via `adminApi.fetchMaterialPreview` | ✓ VERIFIED | `MaterialPage.jsx:70`; `adminApi.js:327-376`; key-link verify WIRED |

**Score:** 20/20 truths verified (**0** present-but-behavior-unverified)

**Behavior-dependent truths:** truth 17 (NOT_FOUND → reader handoff + effect reset) remains ✓ VERIFIED via Playwright CR-01 case `клик по «Открыть материал →» на готовой строке…` (green in this session's 11-pass run).

**Coincidental-reliance:** none flagged.

### Advisory (New Scope, Unevidenced)

None — re-verification Step 7 scan found no new-scope unevidenced blockers. Phase 19's `App.jsx` data-router migration preserved the `admin/materials/:id` preview route; Playwright subset still green.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `get_material_for_preview.py` | draft-only read | ✓ VERIFIED | 15 lines; DRAFT only; no SDK imports; `verify.artifacts` passed |
| `admin.py` preview route + `_to_preview_response` | `require_admin` + `no-store` + empty tags/related | ✓ VERIFIED | `:275-293`, `:358-389` |
| `test_get_material_for_preview.py` | use-case RED gate | ✓ VERIFIED | in 75-pass |
| `test_http_admin.py` | preview HTTP cases | ✓ VERIFIED | 12 material-preview cases collected; suite green |
| `test_http_materials.py` | admin-token 404 + no-`no-store`; tripwire | ✓ VERIFIED | named tripwires green |
| `test_email_render.py` | target/rel + blank-slug | ✓ VERIFIED | in 75-pass |
| `adminApi.js` | `fetchMaterialPreview` + mock anchors | ✓ VERIFIED | `:327-376`, `:572` |
| `App.jsx` | `admin/materials/:id` → preview | ✓ VERIFIED | `:37` (post–Phase-19 router; still wired) |
| `MaterialPage.jsx` | banner, redirect, forbidden, CR-01 reset | ✓ VERIFIED | `:59-188` |
| `AdminDigestPage.jsx` | sandbox + shortlist repoint | ✓ VERIFIED | `:875`, `:998` |
| `email_render.py` | anchor attrs; href unchanged | ✓ VERIFIED | `:52-54` |
| `tests/admin.spec.js` | Phase-18 specs | ✓ VERIFIED | 11 matching specs green; no skips |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `App.jsx` | `MaterialPage.jsx` | `<MaterialPage preview />` on `admin/materials/:id` | ✓ WIRED | `App.jsx:37`; gsd-tools verified |
| `MaterialPage.jsx` | `adminApi.js` | `fetchMaterialPreview` when `preview` | ✓ WIRED | `:70` |
| `adminApi.js` | `admin.py` | `GET …/admin/materials/{slug}` | ✓ WIRED | `:362` |
| `admin.py` | `get_material_for_preview` | call + `MaterialNotFoundError`→404 | ✓ WIRED | `:377-382` |
| `get_material_for_preview` | `MaterialRepository.get_by_slug` | existing port | ✓ WIRED | `:12` |
| `MaterialPage.jsx` | `ForbiddenPage` | FORBIDDEN → component | ✓ WIRED | `:124-125` |
| `MaterialPage.jsx` | reader route | NOT_FOUND → `<Navigate>` | ✓ WIRED | `:128-130` |
| `AdminDigestPage.jsx` | preview route | shortlist Link | ✓ WIRED | `:998` |
| `email_render.py` | `adminApi.js` mock | shared `rel="noopener noreferrer"` | ✓ WIRED | gsd-tools 18-03 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `MaterialPage` preview | `material` fields | `fetchMaterialPreview` → live admin GET or mock shortlist draft | Yes | ✓ FLOWING |
| Banner | `preview` prop | route | n/a (route-derived by design) | ✓ FLOWING |
| `tags`/`related` | D-08 constants `[]` | `_to_preview_response` | intentional empty | ✓ FLOWING (D-08) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase-18 unit files | pytest 4 files | 75 passed | ✓ PASS |
| Named tripwires + DTO/`no-store` | 5 named tests | 5 passed | ✓ PASS |
| Phase-18 Playwright subset | 11 matching specs | 11 passed | ✓ PASS |
| Reader immutability | git diff vs 3754f87 | empty | ✓ PASS |
| Debt markers | Select-String | 0 | ✓ PASS |

### Probe Execution

N/A — no phase-declared or conventional `scripts/*/tests/probe-*.sh`.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| **ADUX-07** | 18-01, 18-02, 18-03 | Admin-gated preview in normal reader rendering; public route ready-only opaque 404 | ✓ SATISFIED | Truths 1–9, 17–20; REQUIREMENTS.md `[x]` / Complete |
| **ADUX-08** | 18-01, 18-03 | Shortlist/email links → preview; `no-store`; banner; empty related/tags; CTA escapes sandbox | ✓ SATISFIED | Truths 3, 10–16; REQUIREMENTS.md `[x]` / Complete |

**Orphaned requirements:** none.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `test_get_material_for_preview.py` | ADUX-07 | 3 | 0 | No | Behavioral | ✓ PASS |
| `test_http_admin.py` | ADUX-07/08 | 12 preview-related | 0 | No | Value/Status | ✓ PASS |
| `test_http_materials.py` | ADUX-07 | 2+ tripwire | 0 | No | Value | ✓ PASS |
| `test_email_render.py` | ADUX-08 | target/rel + blank | 0 | No | Value | ✓ PASS |
| `tests/admin.spec.js` | ADUX-07/08 | Phase-18 specs | 0 | No | Behavioral | ✓ PASS |

**Disabled tests on requirements:** 0. **Circular patterns:** 0. **Insufficient assertions:** 0.

### Decision Coverage (non-blocking gate)

12/12 trackable `18-CONTEXT.md` decisions honored; `not_honored: []`.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No `TBD`/`FIXME`/`XXX` in covered files | — | Clean |
| — | — | No stub/hollow preview path; D-08 empties are intentional | — | Not a stub |
| — | — | No skipped requirement-linked tests | — | Not a blocker |

### Human Verification Required

N/A — judgment-tier prohibitions were signed off in `18-UAT.md` (`status: complete`, started 2026-10-15T12:58:00Z, updated 2026-10-15T13:25:00Z, 3/3 pass). No outstanding human items; `human_verification` empty → status may be `passed`.

### Gaps Summary

**None.** Stale-digest re-verification (#4682) confirms the phase goal still holds after covered-source drift (`App.jsx` Phase 19 migration). Automated evidence re-run green; UAT discharged the prior `human_needed` driver.

---

_Verified: 2026-10-16T10:59:33Z_
_Verifier: Claude (gsd-verifier)_
