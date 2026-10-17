---
phase: 18-reader-route-honesty-for-draft-materials
verified: 2026-10-17T20:18:48Z
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
covered_digest: "v2:sha256:6ac99f0fdbca14f7ce6caf37adeca2562d4244cbb1ce1689ac33bfe99ab16f99"
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
    enforced_by: "tests/unit/test_http_materials.py#test_materials_draft_slug_returns_404_not_403; #test_materials_draft_slug_returns_404_for_admin_token_too; preview/send pools both still filter ready; tests/admin.spec.js#черновик открывается на предпросмотре с баннером; 18-UAT.md test 1 result:pass"
    flagged: false
    human_signed_off: "18-UAT.md (2026-10-15, still accurate 2026-10-17T20:18Z) — result: pass"
  - statement: "MUST NOT expose an unpublished material's `related` or `tags` — a draft's neighbours and taxonomy can themselves be unpublished and internal, so the draft preview payload ships both as empty lists rather than a filtered projection."
    verification: judgment
    requirement_id: ADUX-08
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "tests/unit/test_http_admin.py#test_admin_material_preview_draft_returns_200_reader_dto; DTO builder _to_preview_response tags=[]/related=[]; Playwright count-0 assertions; 18-UAT.md test 2 result:pass"
    flagged: false
    human_signed_off: "18-UAT.md (2026-10-15, still accurate 2026-10-17T20:18Z) — result: pass"
  - statement: "MUST NOT turn the preview surface into a second copy of the reader contract — `MaterialReaderResponse` gains no `status`/`preview` field, `get_material_for_reader` is never widened, and 'draft ≡ missing' on the reader route stays true."
    verification: judgment
    requirement_id: ADUX-07
    judge_verdict: "NOT VIOLATED (non-authoritative LLM judge)"
    enforced_by: "MaterialReaderResponse (materials.py:29-43) status-free; git diff 3754f87 HEAD -- get_material_for_reader.py routes/materials.py empty; 18-UAT.md test 3 result:pass"
    flagged: false
    human_signed_off: "18-UAT.md (2026-10-15, still accurate 2026-10-17T20:18Z) — result: pass"
re_verification:
  previous_status: passed
  previous_score: 20/20
  previous_verified: 2026-10-17T08:50:00Z
  previous_covered_digest: "v2:sha256:b5b6f08476e763c17dc0854233dcc3ecb77c8dfd93fe57eb7919ff63a814e1de"
  reason: "stale covered_digest (#4682) — covered source changed after the prior verifier ran (Phase 22 AdminLayout/shell-nav wiring in App.jsx + AdminDigestPage.jsx + tests/admin.spec.js; Phase 23 ingest-sources edits touching AdminDigestPage.jsx / admin.py / adminApi.js)"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
advisory: []
---

# Phase 18: Reader-route honesty for draft materials Verification Report

**Phase Goal:** An admin can open any draft (or ready) material at an admin-gated preview and read it in the normal reader rendering, while ordinary readers still get an opaque 404 and no unpublished content is exposed.
**Verified:** 2026-10-17T20:18:48Z
**Status:** passed
**Re-verification:** Yes — stale-digest refresh (#4682); re-derived `covered_digest`, re-ran all automated evidence in this session.

> **Headline:** all four ROADMAP success criteria and all 20 must-have truths are **✓ VERIFIED** against freshly re-run evidence, not SUMMARY claims. `behavior_unverified` is **0**, `overrides_applied` is **0**, no gaps and no human-verification items remain. The three judgment-tier prohibitions remain discharged by `18-UAT.md` (status `complete`, 3/3 pass) and its claims were re-checked against the current tree. `covered_digest` refreshed: `b5b6f084…` → **`6ac99f0f…`**. Digest is now current (not stale).

## Evidence base (independently re-run this session)

| Check | Command | Result |
|---|---|---|
| Phase-18 unit files | `.venv\Scripts\python.exe -m pytest -q tests/unit/test_get_material_for_preview.py tests/unit/test_http_admin.py tests/unit/test_http_materials.py tests/unit/test_email_render.py` | **77 passed**, 1 warning, 2.82 s |
| Named tripwires + DTO/`no-store` | 6 named pytest cases (draft 404, admin-token 404, reader no-`no-store`, draft 200 DTO, draft `no-store`, employee 403) | **6 passed**, 1.31 s |
| Email anchor cases | `pytest -k "read_link_opens_in_new_context or blank_slug_emits_no_anchor_attributes or is_idempotent"` | **9 passed**, 997 deselected |
| Full backend unit suite (run once) | `.venv\Scripts\python.exe -m pytest -q` | **1006 passed**, 1 warning, 11.15 s |
| Phase-18 Playwright — draft preview block | `npx playwright test --project=web tests/admin.spec.js -g "предпросмотр черновика" --workers=1` | **5 passed** (16.3 s) |
| Phase-18 Playwright — email + shortlist honesty | `npx playwright test … -g "email preview honesty\|превью письма…\|Открыть материал…\|ban-list\|material preview honesty" --workers=1` | **9 passed** (26.1 s) |
| Reader route / use case immutability | `git diff 3754f87 HEAD -- routes/materials.py get_material_for_reader.py preview_digest_email.py tests/web-app.spec.js` | **empty** (0 lines) |
| Preserved tripwire | `git diff -U0 3754f87 HEAD -- tests/unit/test_http_materials.py` | additions only — `test_materials_draft_slug_returns_404_not_403` body untouched |
| `gsd-tools` artifacts (18-01/02/03) | `query verify.artifacts` ×3 | **all_passed** (5 + 4 + 5) |
| `gsd-tools` key-links (18-01/02/03) | `query verify.key-links` ×3 | **all_verified** (5 + 4 + 3) |
| Debt-marker gate | `Select-String 'TBD\|FIXME\|XXX'` over 12 covered impl/test files | **0 matches** |
| Acceptance greps | `email_render.py` `/admin/`; `AdminDigestPage.jsx` `allow-scripts\|allow-same-origin`; `MaterialPage.jsx` `material.status\|dto.status\|material_status`, bare `fetch(`, `fetchMe\|meApi` | **0 / 0 / 0 / 0 (only `clearFailNextContentFetch()`) / 0** |
| `no-store` scope | `Select-String 'no-store' admin.py` | **1** (preview route header only) |
| Decision-coverage gate | `gsd-tools query check.decision-coverage-verify` | **12/12 honored**, `not_honored: []` |
| Fingerprint | `gsd-tools query verification.fingerprint` (18 files) | `v2:sha256:6ac99f0f…` (refreshed) |
| Test-quality audit | skip patterns on requirement-linked tests | **0 skips**, **0 circular** |

**Post-prior-pass source drift (accounted for, not a gap).** Covered files were touched by Phase 22 (AdminLayout / shell «Админ» entry — `App.jsx` now nests digest+pipeline under `AdminLayout` while `admin/materials/:id` remains a sibling with `<MaterialPage preview />`) and Phase 23 (ingest-sources edits on shared admin surfaces). Phase-18 invariants were re-proven green under the current tree.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| **SC1** | | | |
| 1 | Admin `GET /admin/materials/{slug}` for a draft → 200 with reader DTO key set, `tags==[]`, `related==[]`, no `status` | ✓ VERIFIED | `test_admin_material_preview_draft_returns_200_reader_dto` green; `_to_preview_response` `admin.py:347-365`; route `:430-461`; `MaterialReaderResponse` `materials.py:29-43` has no `status` |
| 2 | Preview renders draft in **normal reader rendering** + banner «Черновик — предпросмотр, не опубликовано» | ✓ VERIFIED | Playwright `черновик открывается на предпросмотре с баннером` green; `App.jsx:47` reuses `MaterialPage`; banner `MaterialPage.jsx:182-189` |
| 3 | Shortlist «Открыть материал →» on a **draft** opens admin preview with banner | ✓ VERIFIED | Playwright `черновик: «Открыть материал →» ведёт на админ-предпросмотр…` green; link `AdminDigestPage.jsx:990` |
| 4 | Preview gated by `require_admin`; employee → 403, anonymous → 401 | ✓ VERIFIED | `test_admin_material_preview_employee_returns_403` (named run) + anonymous 401 case in 77-pass run; `Depends(require_admin)` at `admin.py:445` |
| **SC2** | | | |
| 5 | `GET /materials/{slug}` and `get_material_for_reader` byte-identical to pre-phase | ✓ VERIFIED | `git diff 3754f87 HEAD` empty for both; `get_material_for_reader` still `status != READY → MaterialNotFoundError` |
| 6 | Draft slug on reader → opaque 404 `material_not_found` (never 403) | ✓ VERIFIED | `test_materials_draft_slug_returns_404_not_403` green (named run) |
| 7 | Reader route has **no role branch** — admin token still 404 | ✓ VERIFIED | `test_materials_draft_slug_returns_404_for_admin_token_too` green (named run) |
| 8 | 403 only from role gate; unknown/`ready` → 404 for admin (no slug oracle) | ✓ VERIFIED | unknown/ready/outcomes cases green in 77-pass run |
| 9 | Malformed slug refused at validation (never 200/403) | ✓ VERIFIED | `test_admin_material_preview_malformed_slug_never_succeeds` green; `_SLUG_PATTERN` on Path |
| **SC3** | | | |
| 10 | Only draft-preview 200 carries `Cache-Control: no-store` | ✓ VERIFIED | draft `no-store` + reader no-`no-store` named tests green; one `no-store` in `admin.py:460` |
| 11 | Preview exposes no unpublished `related`/`tags` | ✓ VERIFIED | DTO test asserts both `[]`; Playwright asserts tags/related/«Связанные материалы» count 0 |
| 12 | Repeat preview reads identical; no write path | ✓ VERIFIED | `test_admin_material_preview_repeat_is_identical_and_writes_nothing` green; use case is pure read |
| **SC4** | | | |
| 13 | Email «Читать →» has `target="_blank" rel="noopener noreferrer"` (backend + mock) | ✓ VERIFIED | `email_render.py:54`; `adminApi.js:572`; email_render suite green |
| 14 | Iframe `sandbox="allow-popups allow-popups-to-escape-sandbox"`; CTA opens top-level context | ✓ VERIFIED | Playwright popup-escape case green; `AdminDigestPage.jsx:867`; withheld-token greps → 0 |
| 15 | Shared email href stays `{base}/materials/{slug}`; no `/admin/` in renderer | ✓ VERIFIED | `email_render.py` href builder; grep `/admin/` → 0; `preview_digest_email.py` diff empty |
| 16 | Blank slug emits no anchor; renderers idempotent | ✓ VERIFIED | blank-slug + idempotent named cases green |
| **Cross-cutting** | | | |
| 17 | Ready/unknown preview slug → client `<Navigate replace>` to reader (CR-01 reset) | ✓ VERIFIED | Playwright ready-redirect + click-path cases green; resets at `MaterialPage.jsx:87-88`; redirect `:128-130` |
| 18 | Ordinary reader on preview URL → `ForbiddenPage` for existing and nonexistent slug | ✓ VERIFIED | Two Playwright employee cases green; `MaterialPage.jsx:124-126` |
| 19 | Reader route `/materials/:id` behaviourally unchanged | ✓ VERIFIED | `App.jsx:33` `<MaterialPage />` no props; `tests/web-app.spec.js` diff vs 3754f87 empty |
| 20 | SPA reaches preview only via `adminApi.fetchMaterialPreview` | ✓ VERIFIED | `MaterialPage.jsx:70`; `adminApi.js:327+`; key-link verify WIRED |

**Score:** 20/20 truths verified (**0** present-but-behavior-unverified, **0** overridden)

**Behavior-dependent truths:** truth 17 (NOT_FOUND → reader handoff + effect reset) and truth 14 (sandbox popup escape) are ✓ VERIFIED by passing Playwright cases that assert the rendered reader surface and the `popup` event respectively — not by symbol presence alone.

**Coincidental-reliance:** none flagged.

### Advisory (New Scope, Unevidenced)

None — the re-verification Step 7 scan found no new-scope unevidenced findings. Files changed since the prior pass (`App.jsx`, `AdminDigestPage.jsx`, `admin.py`, `adminApi.js`, `tests/admin.spec.js`) were re-checked; drift is Phase 22/23 wiring, and every phase-18 invariant they touch still holds under re-run evidence.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `get_material_for_preview.py` | draft-only read | ✓ VERIFIED | 15 lines; `DRAFT` only; no SDK imports; `verify.artifacts` passed |
| `admin.py` preview route + `_to_preview_response` | `require_admin` + `no-store` + empty tags/related | ✓ VERIFIED | `:347-365`, `:430-461`, header at `:460` |
| `test_get_material_for_preview.py` | use-case RED gate | ✓ VERIFIED | green in 77-pass |
| `test_http_admin.py` | preview HTTP cases | ✓ VERIFIED | green in 77-pass |
| `test_http_materials.py` | admin-token 404 + no-`no-store`; tripwire preserved | ✓ VERIFIED | 3 matching cases green; tripwire untouched |
| `test_email_render.py` | target/rel + blank-slug + idempotency | ✓ VERIFIED | named cases green |
| `adminApi.js` | `fetchMaterialPreview` + mock anchor attrs | ✓ VERIFIED | `:327+`, `:572` |
| `App.jsx` | `admin/materials/:id` → preview | ✓ VERIFIED | `:47` (post–Phase-22 `AdminLayout`; still wired as sibling) |
| `MaterialPage.jsx` | banner, redirect, forbidden, CR-01 reset | ✓ VERIFIED | `:59-130`, banner `:182-189` |
| `AdminDigestPage.jsx` | sandbox + shortlist repoint | ✓ VERIFIED | `:867`, `:990` |
| `email_render.py` | anchor attrs; href unchanged | ✓ VERIFIED | `:54`; no `/admin/` |
| `tests/admin.spec.js` | Phase-18 specs | ✓ VERIFIED | 5 + 9 matching specs green; no skips |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `App.jsx` | `MaterialPage.jsx` | `<MaterialPage preview />` on `admin/materials/:id` | ✓ WIRED | `App.jsx:47`; gsd-tools verified |
| `MaterialPage.jsx` | `adminApi.js` | `fetchMaterialPreview` when `preview` | ✓ WIRED | `:70` |
| `adminApi.js` | `admin.py` | `GET …/admin/materials/{slug}` | ✓ WIRED | `:362` |
| `admin.py` | `get_material_for_preview` | call + `MaterialNotFoundError`→404 | ✓ WIRED | `:449-454` |
| `get_material_for_preview` | `MaterialRepository.get_by_slug` | existing port | ✓ WIRED | `:12` |
| `MaterialPage.jsx` | `ForbiddenPage` | FORBIDDEN → component | ✓ WIRED | `:124-126` |
| `MaterialPage.jsx` | reader route | NOT_FOUND → `<Navigate replace>` | ✓ WIRED | `:128-130` |
| `AdminDigestPage.jsx` | preview route | shortlist `Link to` | ✓ WIRED | `:990` |
| `email_render.py` | `adminApi.js` mock | shared `rel="noopener noreferrer"` | ✓ WIRED | `email_render.py:54` / `adminApi.js:572` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `MaterialPage` preview | `material` fields | `fetchMaterialPreview` → live admin GET or mock shortlist draft | Yes | ✓ FLOWING |
| Banner | `preview` prop | route | n/a (route-derived by design) | ✓ FLOWING |
| `tags`/`related` | D-08 constants `[]` | `_to_preview_response` | intentional empty | ✓ FLOWING (D-08) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Phase-18 unit files | `pytest -q` (4 files) | 77 passed | ✓ PASS |
| Named tripwires + DTO/`no-store` | 6 named tests | 6 passed | ✓ PASS |
| Email anchor attributes / blank slug / purity | `pytest -k "…"` | 9 passed | ✓ PASS |
| Full backend suite | `pytest -q` | 1006 passed | ✓ PASS |
| Draft preview SPA block | `playwright … -g "предпросмотр черновика" --workers=1` | 5 passed | ✓ PASS |
| Email CTA + shortlist honesty | `playwright …` (9 cases) | 9 passed | ✓ PASS |
| Reader immutability | `git diff 3754f87 HEAD` (reader route/use case/preview pool) | empty | ✓ PASS |
| Debt markers | `Select-String 'TBD\|FIXME\|XXX'` (12 files) | 0 | ✓ PASS |

### Probe Execution

N/A — no phase-declared or conventional `scripts/*/tests/probe-*.sh`.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| **ADUX-07** | 18-01, 18-02, 18-03 | Admin-gated preview in normal reader rendering; public route ready-only opaque 404 | ✓ SATISFIED | Truths 1–9, 17–20; REQUIREMENTS.md `[x]` / Complete |
| **ADUX-08** | 18-01, 18-03 | Shortlist/email links → preview; `no-store`; banner; empty related/tags; CTA escapes sandbox | ✓ SATISFIED | Truths 3, 10–16; REQUIREMENTS.md `[x]` / Complete |

**Orphaned requirements:** none — both IDs mapped to Phase 18 in REQUIREMENTS.md are declared in plan frontmatter and satisfied.

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --------- | ---------- | ------ | ------- | -------- | --------------- | ------- |
| `test_get_material_for_preview.py` | ADUX-07 | 3 | 0 | No | Behavioral | ✓ PASS |
| `test_http_admin.py` | ADUX-07/08 | preview-related | 0 | No | Value/Status | ✓ PASS |
| `test_http_materials.py` | ADUX-07 | tripwire + admin-token + no-`no-store` | 0 | No | Value | ✓ PASS |
| `test_email_render.py` | ADUX-08 | target/rel + blank + idempotent | 0 | No | Value | ✓ PASS |
| `tests/admin.spec.js` | ADUX-07/08 | 14 matching specs re-run | 0 | No | Behavioral | ✓ PASS |

**Disabled tests on requirements:** 0. **Circular patterns:** 0. **Insufficient assertions:** 0.

### Decision Coverage (non-blocking gate)

12/12 trackable `18-CONTEXT.md` decisions honored; `not_honored: []`. Message: All trackable CONTEXT.md decisions are honored by shipped artifacts.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | No `TBD`/`FIXME`/`XXX` in covered files | — | Clean |
| — | — | No stub/hollow preview path; D-08 empties are intentional and test-pinned | — | Not a stub |
| — | — | No skipped requirement-linked tests | — | Not a blocker |

### Human Verification Required

N/A — judgment-tier prohibitions were signed off in `18-UAT.md` (`status: complete`, 3/3 pass). Each UAT expectation was re-checked against the current tree this session (reader-route 404 for every token, empty `tags`/`related`, status-free `MaterialReaderResponse`, unchanged `get_material_for_reader`, preview banner present) and all three remain accurate. `human_verification` empty → status may be `passed`.

### Gaps Summary

**None.** Stale-digest re-verification (#4682) confirms the phase goal still holds after covered-source drift (Phase 22 AdminLayout / Phase 23 shared admin surfaces). Automated evidence was re-run in this process and is green; the pre-existing UAT remains accurate; `covered_digest` refreshed from `b5b6f084…` to `6ac99f0f…`. Digest is **current** (no longer stale).

---

_Verified: 2026-10-17T20:18:48Z_
_Verifier: Claude (gsd-verifier)_
