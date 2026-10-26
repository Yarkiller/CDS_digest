---
phase: "13"
slug: "admin-material-email-preview-honesty"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-02"
validated: "2026-10-03"
---

# Phase 13 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (unit) + Playwright (e2e) |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]`; `playwright.config.js` |
| **Quick run command** | `uv run pytest tests/unit/test_email_render.py tests/unit/test_http_admin.py tests/unit/test_preview_digest.py tests/unit/test_send_digest.py -x` |
| **Full suite command** | `npm run test:unit && npm run test:web` |
| **Estimated runtime** | ~60–180 seconds |

---

## Sampling Rate

- **After every task commit:** Run focused pytest / Playwright file(s) for the task
- **After every plan wave:** Run `npm run test:unit`
- **Before `/gsd-verify-work`:** `npm run test:unit && npm run test:web` must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 13-01-01 | 01 | 1 | ADUX-01 | T-13-01 | Admin-only shortlist enrichment; full item keys | unit | `uv run pytest tests/unit/test_http_admin.py::test_admin_shortlist_returns_full_items -x` | ✅ | ✅ green |
| 13-02-01 | 02 | 1 | ADUX-02/03/04 | T-13-02 | Interstitial HTML + ban asserts; no runtime strip | unit | `uv run pytest tests/unit/test_email_render.py -x` | ✅ | ✅ green |
| 13-02-02 | 02 | 1 | ADUX-02/03 | T-13-02 | Preview returns escaped `html`; plain `\n\n` honesty | unit | `uv run pytest tests/unit/test_preview_digest.py -k "html or interstitial" -x` | ✅ | ✅ green |
| 13-02-03 | 02 | 1 | ADUX-04 | T-13-03 | Ban-list asserts; no runtime strip in email_render | unit | `uv run pytest tests/unit/test_email_render.py -k "forbidden or chrome" -x` | ✅ | ✅ green |
| 13-03-01 | 03 | 2 | ADUX-01 | T-13-01 | Material modal body/provenance/counts/reader link | e2e | `npm run test:web -- tests/admin.spec.js -g "material preview"` | ✅ | ✅ green |
| 13-03-02 | 03 | 2 | ADUX-01 | T-13-01 | Empty body copy without toast | e2e | `npm run test:web -- tests/admin.spec.js -g "Текст материала недоступен"` | ✅ | ✅ green |
| 13-04-01 | 04 | 2 | ADUX-02 | T-13-02 | Sandboxed iframe shows backend HTML | e2e | `npm run test:web -- tests/admin.spec.js -g "email-preview-frame"` | ✅ | ✅ green |
| 13-04-02 | 04 | 2 | ADUX-03 | T-13-02 | Connecting-text paragraph hint | e2e | `npm run test:web -- tests/admin.spec.js -g "Пустая строка"` | ✅ | ✅ green |
| 13-05-01 | 05 | 3 | ADUX-04 | T-13-03 | Migration 010 + runbook + TS ban mirror | unit+repo | `uv run pytest tests/unit/test_email_render.py -k "forbidden or chrome" -x` | ✅ | ✅ green |
| 13-05-02 | 05 | 3 | ADUX-04 | T-13-03 | Playwright ban surfaces (modal + iframe) | e2e | `npm run test:web -- tests/admin.spec.js -g "ban-list\|forbidden chrome"` | ✅ | ✅ green |
| 13-06-01 | 06 | 3 | ADUX-02 | T-13-02 | Send path records body_html from shared renderer | unit | `uv run pytest tests/unit/test_send_digest.py -k "html or body_html or interstitial" -x` | ✅ | ✅ green |
| 13-06-02 | 06 | 3 | ADUX-02 | T-13-02 | preview html == send html | unit | `uv run pytest -k test_preview_email_html_matches_send_html -x` | ✅ | ✅ green |
| 13-07-01 | 07 | 4 | ADUX-01 | T-13-01 | Material close stays visible while body scrolls | e2e | `npm run test:web -- tests/admin.spec.js -g "material preview close stays visible"` | ✅ | ✅ green |
| 13-07-02 | 07 | 4 | ADUX-02 | T-13-02 | Email close stays visible while preview scrolls | e2e | `npm run test:web -- tests/admin.spec.js -g "email preview close stays visible"` | ✅ | ✅ green |
| 13-08-01 | 08 | 4 | ADUX-02 | T-13-02 | Email preview without duplicate ranked list | e2e | `npm run test:web -- tests/admin.spec.js -g "email-preview-frame\|email preview close"` | ✅ | ✅ green |
| 13-08-02 | 08 | 4 | ADUX-02 | T-13-02 | Regression: email suite green without item list | e2e | `npm run test:web -- tests/admin.spec.js -g "Превью письма\|email-preview-frame"` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_email_render.py` — interstitial matrix + `render_email_html` + ban asserts (ADUX-02/03/04)
- [x] `tests/unit/test_http_admin.py::test_admin_shortlist_returns_full_items` — ADUX-01
- [x] `tests/unit/test_preview_digest.py` / send tests — html field + parity
- [x] Update `tests/admin.spec.js` email preview selectors for iframe
- [x] Extend FE mocks in `web/src/services/adminApi.js` with full item fields + `html`
- [x] Update `12-FIX-01-LOCK.md` item schema section (D-03)
- [x] Migration `010_phase13_scrub_test_header.sql` + runbook §4f/§4g
- [x] In-memory shortlist seeds carry new `ShortlistItem` fields

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual paragraph spacing in email iframe | ADUX-03 | Pixel spacing subjective | Open «Превью письма»; confirm `\n\n` interstitial shows as separate paragraphs |

*Automated unit matrix covers `\n\n` → `<p>`; manual is polish-only. Does not block `nyquist_compliant`.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 180s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-03

---

## Validation Audit 2026-10-03

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

**State:** A (existing VALIDATION.md audited). Seeded Wave-0 map was stale (`status: draft`, all ⬜ pending); rebuilt from plans 13-01…13-08 + live tests. Focused unit sample: 21 passed (`test_email_render`, `test_admin_shortlist_returns_full_items`, preview html/parity). Cross-check: `13-VERIFICATION.md` requirements ADUX-01…04 SATISFIED. No auditor spawn (zero gaps).
