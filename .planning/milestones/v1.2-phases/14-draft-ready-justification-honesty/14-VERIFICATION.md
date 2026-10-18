---
phase: 14-draft-ready-justification-honesty
verified: 2026-10-04T16:57:44Z
status: passed
score: 24/24 must-haves verified
covered_files:
  - .planning/phases/14-draft-ready-justification-honesty/14-01-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-01-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-02-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-02-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-03-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-03-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-04-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-04-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-05-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-05-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-06-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-06-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-07-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-07-SUMMARY.md
  - .planning/phases/14-draft-ready-justification-honesty/14-08-PLAN.md
  - .planning/phases/14-draft-ready-justification-honesty/14-08-SUMMARY.md
  - backend/src/backend/application/use_cases/mark_material_ready.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/domain/material.py
  - backend/src/backend/domain/shortlist.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/tests_support/in_memory.py
  - data-collection/src/data_collection/dto/_body.py
  - data-collection/src/data_collection/dto/article_draft.py
  - supabase-integration/src/supabase_integration/material_repository.py
  - tests/admin.spec.js
  - tests/unit/test_admin_mark_ready.js
  - tests/unit/test_article_draft_body_audience.py
  - tests/unit/test_http_admin.py
  - tests/unit/test_mark_material_ready.py
  - tests/unit/test_score_factors.py
  - tests/unit/test_set_shortlist_decision.py
  - tests/unit/test_supabase_material_repository_embed.py
  - web/src/index.css
  - web/src/main.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/services/adminApi.js
  - web/src/services/adminReadyMock.js
  - web/src/services/adminReadyReconcile.js
covered_digest: "v2:sha256:3eb508d111c70c7c7e576e9bf4cf3c697c4dffa734eba7d6309e7e1450278ddb"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 22/24
  reason: "GSD #4682 stale re-verification — a later commit (4239f0f, phase 16) modified the covered file tests/admin.spec.js after the previous verifier ran, so the recorded covered_digest no longer matched the working tree. All covered sources are committed and the tree is clean for phase 14 files."
  gaps_closed: []
  gaps_remaining: []
  regressions: []
  superseded:
    - "Prior truth: batch partial promote optimistic UI (14-03) — FE batch affordance removed by operator override (14-07); backend batch path retained and HTTP-covered"
    - "Prior truth: batch stale-refetch no-clobber reconcile (14-04 must_have #4) — no FE batch caller remains"
    - "Prior truth: quantified batch CTA «Сделать ready все одобренные черновики (N)» (14-05) — control removed by 14-07"
    - "Prior truth: sticky-footer batch-CTA geometry backstop (14-03) — batch CTA removed"
---

# Phase 14: Draft→ready & justification honesty Verification Report

**Phase Goal:** Admin can unblock send without SQL and see honest shortlist justification
**Verified:** 2026-10-04T16:57:44Z
**Status:** passed
**Re-verification:** Yes — stale re-verification (GSD #4682). Regenerated from the CURRENT codebase with a fresh `covered_digest`; the prior report's 22/24 (2 backstop abstentions) now closes to 24/24 because the completed `14-UAT.md` records directly-observed behavior for all three prior human items.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | SC1 / ADUX-05: Admin can set a material `draft` → `ready` in the admin UI without a direct SQL workaround (D-01, D-07) | ✓ VERIFIED | `AdminDigestPage` `admin-mark-ready` button → `adminApi.markReady` → `POST /admin/materials/{id}/ready`; Playwright `per-row Сделать ready promotes draft and clears draft hint (ADUX-05)` PASS (independent run); UAT #1 live pass (POST 200, DB status=ready) |
| 2 | SC2 / ADUX-05: after promotion the D-85 send gate no longer blocks that material solely for still being draft | ✓ VERIFIED | `test_admin_mark_ready_promotes_draft_and_clears_send_gate` green; `sendUnlocked` still requires `approvedDrafts.length === 0`; Playwright asserts the draft hint clears and send path transitions |
| 3 | SC3 / ADUX-06: shortlist «Обоснование» shows populated `score_factors` or an explicit empty state — never a silent fake | ✓ VERIFIED | `factorText` returns the exact D-15 empty string for <2 labels, joins server labels only; `tests/unit/test_score_factors.py` named 0/1/2+/whitespace matrix green; Playwright asserts (`populated shortlist shows ≤5 rows…`) |
| 4 | D-06: status-only promote leaves `published_at` unchanged and never routes through `publish_material` / `Material.as_ready` / `assert_publishable` / indexing | ✓ VERIFIED | `Material.with_ready_status` (`material.py:48-53`) uses `replace(status=READY, updated_at=now)` with no publish gate; `mark_material_ready.py` imports no publish/index path; `test_mark_material_ready_empty_body_draft_sets_ready_leaves_published_at` green |
| 5 | D-07 / D-09 / D-10: single `POST /admin/materials/{id}/ready` returns 200 ready for a draft; already-ready is a 200 no-op; empty body still promotes; missing material → 404 `material_not_found`; employee → 403 | ✓ VERIFIED | `admin.py:303-331` single route with `Depends(require_admin)` + `MarkReadyResponse(extra=forbid)`; `test_admin_mark_ready_already_ready_is_noop` / `_missing_material_returns_404` / `_employee_returns_403` green |
| 6 | D-08: batch `POST /admin/materials/ready` returns HTTP 200 order-preserving partial success; `extra=forbid`; empty ids → `results=[]`; never 207 / never abort | ✓ VERIFIED | `admin.py:271-300`; `mark_materials_ready` per-id try/except; `test_admin_mark_ready_batch_partial_success_preserves_order` / `_empty_ids_returns_empty_results` / `_unknown_field_returns_422` / `_employee_returns_403` green |
| 7 | D-02: Approve on a draft leaves `material_status` draft — approve ≠ ready | ✓ VERIFIED | `test_admin_decision_approve_returns_updated_shortlist_with_status` green; Playwright `Approve does not auto-ready draft (D-02)` PASS (`черновик` + `одобрен (в шортлист)` coexist, `admin-mark-ready` still visible) |
| 8 | G-14-1 / G-14-4 (read): `SupabaseMaterialRepository._fetch_one` uses an FK-disambiguated `material_relations!material_relations_from_material_id_fkey(to_material_id)` embed so live `get()` / `get_by_slug()` return a `Material` (no PGRST201 → 503); `material_tags` stays unhinted | ✓ VERIFIED | `material_repository.py:145-153` emits the hinted embed; `test_get_returns_material_under_ambiguous_embed_rejection` / `test_get_by_slug_...` / `test_fetch_one_disambiguates_relations_embed_and_keeps_tags_unhinted` green |
| 9 | G-14-1 (write): live promote persists — `save` UPDATEs domain-owned columns by id instead of a full-row upsert (428C9 / 23502 cannot recur) | ✓ VERIFIED | `material_repository.py:96-139` `.update(payload).eq("id", …)` with empty-`data` guard; `test_save_updates_owned_columns_by_id_instead_of_full_row_upsert` / `_preserves_unmodelled_provenance_columns_on_the_live_row` / `_signals_when_no_row_matches` green |
| 10 | Live per-row promote on real Supabase data (G-14-1 read+write re-check) | ✓ VERIFIED | `14-UAT.md` test 1 (result: pass, updated 2026-10-04T07:15Z, after the write-path commit) — POST 200, badge `готов`, DB `materials.id=12` status=ready, re-promote idempotent, `published_at` null |
| 11 | D-01: per-row «Сделать ready» sits next to the draft badge and hides once ready | ✓ VERIFIED | `admin-mark-ready` testid in the row meta flex (`AdminDigestPage.jsx:729-740`), gated on `material_status === 'draft'`; Playwright per-row + stale tests assert it disappears after promote |
| 12 | D-05: after promote optimistic ready + silent refetch; on failure a toast and the badge stays draft — no fake ready | ✓ VERIFIED | Optimistic `setItems` + rollback-on-failure in `promoteReady` (`AdminDigestPage.jsx:331-368`); Playwright per-row test PASS |
| 13 | G-14-2: a still-draft refetch never silently reverts a promoted row | ✓ VERIFIED (behavioral) | `preservePromotedReady` forces promoted ids back to ready; `promoteReady` wraps `refreshed.items` (`AdminDigestPage.jsx:348-359`); Playwright `stale still-draft refetch does not revert a promoted row (G-14-2)` PASS (independent run) + node suite `preservePromotedReady refetch reconciliation` green |
| 14 | G-14-2: live `markReady` POSTs `/admin/materials/{id}/ready` and treats `MarkReadyResponse` as source of truth — no `fetchShortlist` coupling | ✓ VERIFIED | `adminApi.js:359-396` body has no `fetchShortlist`; returns `response.json()` (live) / `{material_id,status:'ready'}` (mock); node source-shape test `markReady is decoupled from fetchShortlist and returns a MarkReadyResult` green |
| 15 | G-14-2: a harness flag simulates a backend that acknowledges the POST without persisting | ✓ VERIFIED | `adminApi.js:368` reads `stickyFlag('__DIGEST_ADMIN_STALE_READY__')` and skips `applyMockMarkReady`; cleared in `resetAdminHarness` (`adminApi.js:198`); Playwright stale test exercises it |
| 16 | 14-07: the footer offers no batch promote (control + handler + import gone) and the «Уберите черновики…» hint renders in no state; `sendHint` coherent | ✓ VERIFIED | No `admin-mark-ready-batch` / `promoteApprovedDrafts` / `markReadyBatch` in `AdminDigestPage.jsx`; `sendHint` branch order (`AdminDigestPage.jsx:252-260`) ends with neutral `Отправка недоступна.`; Playwright `no batch promote CTA is rendered (G-14-2)` PASS; node source-shape lock green |
| 17 | 14-07: D-85 gate still holds — `sendUnlocked` requires `approvedDrafts.length === 0`, so Send stays disabled while an approved draft exists | ✓ VERIFIED | `AdminDigestPage.jsx:246-250`; Playwright `approved draft blocks send with draft hint (D-85)` asserts the hint + disabled Send |
| 18 | 14-07: per-row control retained unchanged; retained backend batch route + `mark_materials_ready` and the unhooked FE `markReadyBatch` client/mock remain available and tested | ✓ VERIFIED | Per-row path untouched; backend batch HTTP tests green; `markReadyBatch` export + `applyMockMarkReadyBatch` node-tested (`applyMockMarkReadyBatch … (D-08)`); no UI caller remains (intentional) |
| 19 | G-14-2a (14-05): an approved draft row reads as two disambiguated axes — `materialStatusLabel` («черновик»/«готов») + `decisionCaption` («одобрен (в шортлист)»/«отклонён (из шортлиста)») | ✓ VERIFIED | `AdminDigestPage.jsx:69-79`; pill renders `materialStatusLabel(item.material_status)`; Playwright D-02 case asserts both coexist |
| 20 | G-14-2b (14-05): the sticky send footer no longer re-lists approved-draft titles | ✓ VERIFIED | Footer renders only `admin-send-hint` + buttons (no `<ul>`); Playwright asserts footer `ul` count 0 |
| 21 | D-13…D-17 / ADUX-06: exact D-15 empty copy + populated server-only join + named `honest_factor_labels` 0/1/2+/whitespace matrix | ✓ VERIFIED | `factorText` exact string `Обоснование недоступно — скоринг не запускался` (`AdminDigestPage.jsx:81-85`); `test_score_factors.py` named cases green; FE never fabricates labels |
| 22 | G-14-3 (14-08): interactive admin controls show `cursor: pointer`, disabled buttons excluded, locked by a computed-cursor assertion | ✓ VERIFIED | `index.css:35-41` `@layer base { button:not(:disabled) { cursor: pointer } }`; Playwright `interactive admin controls show a pointer cursor (G-14-3)` PASS (audited controls + disabled Send guard) |
| 23 | 14-03 backstop: long material titles still wrap with usable draft badge + «Сделать ready» | ✓ VERIFIED | UAT test 2 (result: pass) — at 390px, injected 3× title computed `overflow-wrap: break-word`, badge + «Сделать ready» usable, 0px horizontal overflow; layout classes (`break-words`, flex-wrap) unchanged since |
| 24 | 14-03 backstop: long factor captions and the empty justification sentence wrap with `break-words` inside `max-w-[12rem]` | ✓ VERIFIED | UAT test 3 (result: pass) — `max-width: 192px`, `overflow-wrap: break-word`, long caption wrapped with no overflow and intact row grid |

**Score:** 24/24 truths verified (0 present-behavior-unverified)

> Truths 23–24 carry `verification: backstop` and were the prior report's two abstentions. They are now resolved by directly-observed behavior recorded in the completed `14-UAT.md` (tests 2 and 3) against layout code that has not changed since that observation.

### Superseded Must-Haves (operator override, plan 14-07)

| Prior truth | Disposition |
| ----------- | ----------- |
| Batch partial promote: ok ids ready, failed ids toast + stay draft (D-08, FE) | FE batch affordance removed; backend batch path retained but unhooked and HTTP-covered |
| Batch promote path applies the same no-clobber reconcile to its ok ids | No FE batch caller remains |
| Quantified batch CTA «Сделать ready все одобренные черновики (N)» (14-05) | Batch control removed |
| Sticky-footer batch-CTA geometry backstop (many titles) | Batch CTA removed |

### Advisory (New Scope, Unevidenced)

None — no new-scope findings raised during this re-verification.

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `supabase-integration/src/supabase_integration/material_repository.py` | FK-disambiguated relations embed in `_fetch_one`; `save` updates owned columns by id | ✓ VERIFIED | Hinted embed at L150-153; `save` `.update(...).eq("id", …)` with empty-data guard |
| `tests/unit/test_supabase_material_repository_embed.py` | Offline PGRST201 read regression + write-path (428C9/23502) regression | ✓ VERIFIED | 6 named tests included in the 66-pass targeted run |
| `web/src/pages/AdminDigestPage.jsx` | Batch CTA/handler/import removed; coherent `sendHint`; per-row retained; reconciled refetch | ✓ VERIFIED | No batch testid/handler/import; D-85 gate intact; `preservePromotedReady` wired |
| `web/src/index.css` | Global `button:not(:disabled){cursor:pointer}` base rule | ✓ VERIFIED | Present at L35-41 |
| `tests/admin.spec.js` | Playwright per-row/stale/no-batch/pointer-cursor/D-02 locks | ✓ VERIFIED | Named phase-14 tests independently run: 7 passed |
| `tests/unit/test_admin_mark_ready.js` | node `--test` reconcile + batch-removal source-shape lock | ✓ VERIFIED | 10 pass / 0 fail |
| `web/src/services/adminApi.js` | `markReady` decoupled from refetch; stale harness flag; `markReadyBatch` retained | ✓ VERIFIED | No `fetchShortlist` in `markReady`; `return response.json()` |
| `web/src/services/adminReadyReconcile.js` | Pure `preservePromotedReady` | ✓ VERIFIED | Identity-preserving; node suite green |
| `web/src/services/adminReadyMock.js` | Pure mock helpers; material 104 empty `factor_labels` seed | ✓ VERIFIED | Node suite green |
| `backend/src/backend/domain/material.py` | `with_ready_status` status-only transition | ✓ VERIFIED | No publish gate; `published_at` untouched |
| `backend/src/backend/domain/shortlist.py` | `honest_factor_labels` | ✓ VERIFIED | ≥2 rule; 0/1/2+/whitespace matrix green (+ WR-02 flat-key fallback) |
| `backend/src/backend/application/use_cases/mark_material_ready.py` | single + batch helpers | ✓ VERIFIED | status-only; per-id errors; never aborts |
| `backend/src/backend/interface/http/routes/admin.py` | ready routes | ✓ VERIFIED | `require_admin`; batch before `{id}`; `extra=forbid` |
| `backend/src/backend/tests_support/in_memory.py` | shortlist status overlay | ✓ VERIFIED | `attach_materials` / `_overlay_batch` overlays `material_status` |
| `backend/src/backend/composition/container.py` | wire materials into shortlist fake | ✓ VERIFIED | `InMemoryShortlistRepository(materials=materials_repo)` |
| `data-collection/src/data_collection/dto/_body.py` + `article_draft.py` | Normalise leaked `## Аудитория` prompt scaffolding out of `body_markdown` | ✓ VERIFIED | `test_article_draft_body_audience.py` (7 cases: role-JSON / echoed-prompt / no-section / later-section / mid-text / idempotency / roles-wins) green |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `AdminDigestPage` «Сделать ready» | `POST /admin/materials/{id}/ready` | `markReady` (source of truth) → optimistic → reconciled refetch | ✓ WIRED | Playwright stale + per-row proof green |
| `SupabaseMaterialRepository.save` | PostgREST `materials` UPDATE | `.update(domain-owned payload).eq("id", material.id)` | ✓ WIRED | Offline 428C9/23502 regression green |
| `SupabaseMaterialRepository._fetch_one` | PostgREST `materials` embed | `material_relations!material_relations_from_material_id_fkey(to_material_id)` | ✓ WIRED | Offline PGRST201 regression green |
| native `<button>` (admin) | `index.css` `@layer base` | `button:not(:disabled){cursor:pointer}` | ✓ WIRED | Computed-cursor Playwright green |
| approved draft | `admin-send-footer` | `sendHint` neutral lock; no batch CTA; `sendUnlocked` D-85 | ✓ WIRED | Playwright D-85 + no-batch tests green |
| `factor_labels[]` | `factorText` caption | BE `honest_factor_labels` → shortlist DTO | ✓ WIRED | No fabricated defaults (see WR-01 edge) |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| Admin shortlist badge | `item.material_status` | GET shortlist / materials join (live) or mock overlay | Yes | ✓ FLOWING |
| Ready promote (write) | `materials.status` | `mark_material_ready` → `SupabaseMaterialRepository.save` UPDATE by id | Yes | ✓ FLOWING |
| Post-promote reconcile | `refreshed.items` → `preservePromotedReady` | `fetchShortlist()` refetch wrapped before `applyBatch` | Yes | ✓ FLOWING |
| Обоснование caption | `item.factor_labels` | BE `honest_factor_labels` → shortlist DTO | Yes when ≥2 string labels; else D-15 empty | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| Backend phase suites (ready/HTTP/score/decision/embed/audience) | `uv run pytest tests/unit/test_mark_material_ready.py tests/unit/test_http_admin.py tests/unit/test_score_factors.py tests/unit/test_set_shortlist_decision.py tests/unit/test_supabase_material_repository_embed.py tests/unit/test_article_draft_body_audience.py -q` | 66 passed in 3.05s | ✓ PASS |
| FE reconcile + batch-removal source lock | `node --test tests/unit/test_admin_mark_ready.js` | 10 pass / 0 fail | ✓ PASS |
| Named Phase 14 Playwright locks | `npx playwright test --project=web tests/admin.spec.js --grep "per-row Сделать ready\|stale still-draft\|no batch promote CTA\|pointer cursor\|Approve does not auto-ready\|approved draft blocks send\|populated shortlist shows"` | 7 passed (24.7s) | ✓ PASS |
| `honest_factor_labels` non-string edge | `uv run python -c "…h({'factors':[{'label':None},{'label':None}]})…"` | `['None', 'None']` — see WR-01 | ✗ (advisory) |
| Debt markers in covered sources | grep `TBD\|FIXME\|XXX\|HACK\|PLACEHOLDER` | none | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
| ----- | ------- | ------ | ------ |
| — | — | No phase-declared `scripts/*/tests/probe-*.sh` | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| ADUX-05 | 14-01…14-08 | Admin sets material `draft`→`ready` in UI so send is not blocked by D-85 without SQL | ✓ SATISFIED | API + FE + unit/HTTP/Playwright (incl. stale-refetch lock + read/write heal + live UAT) |
| ADUX-06 | 14-03 | Honest «Обоснование» — populated or explicit empty, no silent fake | ✓ SATISFIED | D-15 FE copy + `honest_factor_labels` matrix + Playwright exact assert (WR-01 non-string edge noted) |

**Orphaned requirements:** none. `REQUIREMENTS.md` maps only ADUX-05 and ADUX-06 to Phase 14 (both marked Complete); both are declared in plan frontmatter and accounted for above.

### Prohibitions

| Statement | Verdict | Evidence |
| --------- | ------- | -------- |
| MUST NOT call `publish_material` / `as_ready` / `assert_publishable` / indexing on admin promote | ✓ held | `with_ready_status` + `mark_material_ready.py` + `admin.py` ready routes grep clean |
| MUST NOT auto-ready on Approve / `set_shortlist_decision` | ✓ held | `test_admin_decision_approve_returns_updated_shortlist_with_status` + Playwright D-02 |
| MUST NOT implement batch via a FE-loop of single ready | ✓ held | `markReadyBatch` body never calls `markReady` (node test); FE no longer calls the batch path |
| MUST NOT return HTTP 207 / abort batch on missing id | ✓ held | HTTP 200 + per-id `material_not_found` |
| MUST NOT fabricate FE factor labels | ✓ held | `factorText` joins server labels only |
| MUST NOT add `score_factors` writers / PIPE UI this phase | ✓ held | No writers/UI added |
| MUST NOT redesign shortlist chrome beyond required copy/placement | ✓ held | Changes are localised copy + control placement only |
| MUST NOT couple Approve toolbar to `markReady` | ✓ held | `applyDecision` separate from `promoteReady` |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| `backend/src/backend/domain/shortlist.py` | 20-27 | `str(f.get("label", ""))` coerces a non-string label — `honest_factor_labels({'factors':[{'label':None},{'label':None}]})` → `['None','None']` (WR-01) | ⚠️ Warning | Latent honesty edge: a DB `score_factors` with `null`/numeric labels renders fabricated chips. Not reachable from current product paths (no `score_factors` writers this phase; seed uses strings). Declared 0/1/2+/whitespace matrix is green. Recommend Phase 16 fix (accept only `str` labels + matrix cases) |
| `web/src/services/adminApi.js` | 389-396 | Live `markReady` treats an unparseable 2xx body as failure, so `promoteReady` can roll back a persisted promote (WR-02) | ℹ️ Info | Edge (proxy truncation / unexpected 204); `response_model=MarkReadyResponse` makes it unlikely. `G-14-2` main class (refetch clobber) is fixed |
| `tests/unit/test_supabase_material_repository_embed.py` | 243-245 | Regression asserts any `material_relations!<hint>(...)` but not the exact FK constraint name (WR-03) | ℹ️ Info | A typo'd hint could pass the test and re-open the live 503; the shipped literal is live-verified. Recommend asserting the exact literal |
| `web/src/services/adminApi.js` / `main.jsx` | 406-436 / 29,60 | `markReadyBatch` + `getMockMarkReadyBatchCalls` now have no UI caller (IN-01) | ℹ️ Info | Intentional retention of the D-08 backend/client contract; dead bundle weight only |
| phase-modified sources | — | No `TBD` / `FIXME` / `XXX` debt markers (grep over all covered sources) | — | None — no blocker |

### Human Verification Required

None outstanding. The three human items raised by the previous report are satisfied by the completed `14-UAT.md` (status: complete, 3/3 pass, 0 issues), recorded after the last touch to the relevant code:

1. **Live per-row promote (G-14-1 read+write)** — `14-UAT.md` test 1: pass. Real Supabase (`VITE_USE_MOCKS=false`), `POST /admin/materials/12/ready` → 200, badge `готов`, DB status=ready, idempotent re-POST, `published_at` null.
2. **Long title + ready CTA layout (14-03 backstop)** — `14-UAT.md` test 2: pass (`overflow-wrap: break-word`, controls usable, 0px overflow at 390px).
3. **Long factor caption / empty justification wrap (14-03 backstop)** — `14-UAT.md` test 3: pass (wraps at 192px, row grid intact).

### Gaps Summary

No goal-blocking gaps. `status` is no longer `stale`: the report was regenerated from the current codebase and `covered_digest` recomputed with `verification.fingerprint`. All three roadmap success criteria (SC1/SC2/SC3) and every PLAN/SUMMARY must-have are VERIFIED, including the two 14-03 layout backstops that were previously abstained (now closed by the completed UAT). The operator's deliberate removal of the batch promote control (14-07) is recorded as superseded, not a gap. Remaining review warnings (WR-01 non-string-label honesty edge; WR-02 parse-failure rollback; WR-03 hint-name not locked; IN-01 unhooked batch plumbing) are quality concerns carried as `open`, not goal-blocking.

---

_Verified: 2026-10-04T16:57:44Z_
_Verifier: Claude (gsd-verifier)_
