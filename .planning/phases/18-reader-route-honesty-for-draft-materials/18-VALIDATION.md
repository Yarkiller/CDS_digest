---
phase: 18
slug: reader-route-honesty-for-draft-materials
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-15
---

# Phase 18 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from `18-RESEARCH.md` §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.3.0 (`testpaths = tests/unit`, `pythonpath = ["."]`); Playwright ^1.62.1 for SPA integration; built-in `node --test` for pure Vite-free JS helpers |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| **Quick run command** | `uv run pytest tests/unit/test_http_admin.py tests/unit/test_http_materials.py -q` |
| **Full suite command** | `uv run pytest` |
| **Browser integration** | `npm run test:web -- tests/admin.spec.js` then `npm run test:web` |
| **Estimated runtime** | ~30–60 seconds (unit) / ~2–4 minutes (full web project) |

---

## Sampling Rate

- **After every task commit:** `uv run pytest tests/unit/test_http_admin.py tests/unit/test_http_materials.py tests/unit/test_email_render.py -q`
- **After every plan wave:** `uv run pytest` then `npm run test:web`
- **Before `/gsd-verify-work`:** Full pytest green **and** full web Playwright project green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 18-01-01 | 01 | 1 | ADUX-07 | T-18-01 / — | Admin GETs a draft slug on the new endpoint → 200 with the reader DTO shape | unit (HTTP) | `uv run pytest tests/unit/test_http_admin.py -k preview -x` | ❌ W0 | ⬜ pending |
| 18-01-02 | 01 | 1 | ADUX-07 | T-18-02 | Employee GETs the same endpoint → 403 `forbidden` (no slug oracle) | unit (HTTP) | same file | ❌ W0 | ⬜ pending |
| 18-01-03 | 01 | 1 | ADUX-07 | T-18-02 | Unauthenticated → 401 | unit (HTTP) | same file | ❌ W0 | ⬜ pending |
| 18-01-04 | 01 | 1 | ADUX-07 | T-18-02 | Unknown slug, admin token → 404 `material_not_found` | unit (HTTP) | same file | ❌ W0 | ⬜ pending |
| 18-01-05 | 01 | 1 | ADUX-07 | T-18-01 | **Tripwire PRESERVE** — reader route, draft slug, any authenticated reader → 404 `material_not_found`; plus an *admin* token case proving no role branch | unit (HTTP) | `uv run pytest tests/unit/test_http_materials.py -x` | ✅ `:121` / ❌ W0 admin case | ⬜ pending |
| 18-01-06 | 01 | 1 | ADUX-07 | — | Reader route still 200 for a ready material (no regression) | unit (HTTP) | `uv run pytest tests/unit/test_http_materials.py -x` | ✅ exists | ⬜ pending |
| 18-01-07 | 01 | 1 | ADUX-07 | — | `get_material_for_preview` draft-only semantics against an in-memory fake; `MaterialNotFoundError` on `READY`/missing | unit (use case) | `uv run pytest tests/unit/test_get_material_for_preview.py -x` | ❌ W0 | ⬜ pending |
| 18-01-08 | 01 | 1 | ADUX-08 | T-18-04 | Draft preview carries `Cache-Control: no-store`; the reader response does **not** | unit (HTTP) | `uv run pytest tests/unit/test_http_admin.py -x` | ❌ W0 | ⬜ pending |
| 18-01-09 | 01 | 1 | ADUX-08 | T-18-03 | Draft preview payload has `tags == []` and `related == []`, same keys as the reader DTO | unit (HTTP) | same file | ❌ W0 | ⬜ pending |
| 18-01-10 | 01 | 1 | ADUX-08 | T-18-02 | Ready slug on the preview endpoint → 404 `material_not_found` (D-12: no 307 variant) | unit (HTTP) | same file | ❌ W0 | ⬜ pending |
| 18-02-01 | 02 | 2 | ADUX-08 | T-18-07 | SPA: preview route shows the draft banner + `material-prose`; `material-tags`/`material-related` count 0 (implemented by 18-02 T1/T2) | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "предпросмотр"` | ❌ W0 | ⬜ pending |
| 18-02-02 | 02 | 2 | ADUX-07 | T-18-10 | SPA: `NOT_FOUND` on the preview route → `<Navigate to={/materials/${slug}} replace />`; no draft marker survives (18-02 T2) | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js tests/web-app.spec.js` | ❌ W0 | ⬜ pending |
| 18-02-03 | 02 | 2 | ADUX-07 | T-18-08 | SPA: employee `FORBIDDEN` → `ForbiddenPage` with no slug-existence signal and no `/me` pre-check (18-02 T3) | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "предпросмотр"` | ❌ W0 | ⬜ pending |
| 18-03-01 | 03 | 3 | ADUX-08 | — | SPA: shortlist «Открыть материал →» targets the admin preview surface | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "Открыть материал"` | ✅ exists — **AMEND** `:816-821` | ⬜ pending |
| 18-03-03 | 03 | 3 | ADUX-08 | T-18-05 | Email-preview CTA escapes the iframe (new tab) | e2e (Playwright) | `npm run test:web -- tests/admin.spec.js -g "email-preview"` | ❌ W0 after sandbox amend; **AMEND** `:407,:690,:713` | ⬜ pending |
| 18-03-04 | 03 | 3 | ADUX-08 | T-18-06 | Email render/preview≡send invariants | unit | `uv run pytest tests/unit/test_email_render.py tests/unit/test_preview_digest.py -q` | ✅ exists — **PRESERVE** (Open Question 1 resolved by D-11: the email href does **not** differ) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_get_material_for_preview.py` — draft-only use-case semantics (ADUX-07)
- [ ] `tests/unit/test_http_admin.py` — new preview route cases: 200 draft + `no-store` + empty `tags`/`related`; 403 employee; 401 anonymous; 404 unknown; 404 ready
- [ ] `tests/unit/test_http_materials.py` — add the **admin-token** reader-route 404 case (proves no role branch) **without touching** `test_materials_draft_slug_returns_404_not_403`
- [ ] `tests/admin.spec.js` — new preview-route spec; **amend** the shortlist href assert and the three `sandbox=""` asserts
- [ ] Mock layer: preview fetch must be mockable (`adminApi.js` mock branch) so the SPA banner is Playwright-reproducible; `web/src/data/mock.js` materials have no `status`, so the mock branch must not attempt a status decision
- [ ] `backend/src/backend/tests_support/in_memory.py` — no change needed; reuse the admin HTTP fixtures (`_admin_client_with_batch`, `_seed_profile`, `_mint`) from `tests/unit/test_http_admin.py`
- [ ] Framework install: **none**

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| — | — | — | All phase behaviors have automated verification. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
