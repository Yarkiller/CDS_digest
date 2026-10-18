---
phase: 4
slug: knowledge-razbory
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-20
updated: 2026-09-21
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Updated by plan **04-09** (Playwright honesty gate + unit suite green).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (`uv run pytest`) + Playwright `@playwright/test` ^1.62.1 |
| **Config file** | `playwright.config.js` (`testMatch`: web-app\|auth\|knowledge\|razbory); pytest via uv project |
| **Quick run command** | `uv run pytest tests/unit/test_search_knowledge.py -x` |
| **Full suite command** | `npm run test:unit && npm run test:web` |
| **Honesty e2e** | `npx playwright test tests/knowledge.spec.js tests/razbory.spec.js --project=web` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run targeted pytest file(s) for touched use-case/route
- **After every plan wave:** `npm run test:unit` + affected Playwright project
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** Prefer &lt;60s per task; full suite ~120s allowed at phase gate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-W0-01 | 00 | 0 | KNOW-01 | T-04-score | Omit score from HTTP; blank q → 400 | unit | `uv run pytest tests/unit/test_http_knowledge_search.py -x` | ✅ | ✅ green |
| 04-W0-02 | 00 | 0 | KNOW-02…04 | T-04-draft | Role allowlist; no ML substitute on empty | unit | `uv run pytest tests/unit/test_search_knowledge.py -x` | ✅ | ✅ green |
| 04-W0-03 | 00 | 0 | RAZB-01…04 | T-04-path | JWT; path containment for notebooks | unit | `uv run pytest tests/unit/test_http_razbory.py -x` | ✅ | ✅ green |
| 04-W0-04 | 00 | 0 | KNOW/RAZB | — | Submit/Enter, chips, TOC, notebook UX | e2e | `npx playwright test tests/knowledge.spec.js tests/razbory.spec.js --project=web` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → assertion path (phase gate)

| Requirement | Automated path | Gate evidence (04-09) |
|-------------|----------------|------------------------|
| KNOW-01 | unit search/HTTP blank-400 + honest empty; e2e Submit/Enter; whitespace → «Введите запрос»; no score badges | `tests/knowledge.spec.js` + `test_http_knowledge_search.py` |
| KNOW-02 | unit role_filter analyst; e2e Analyst chip | `tests/knowledge.spec.js` + `test_search_knowledge.py` |
| KNOW-03 | e2e DS search → open material | `tests/knowledge.spec.js` |
| KNOW-04 | unit empty honesty; e2e «Сбросить фильтр» clears role only | `tests/knowledge.spec.js` |
| RAZB-01 | unit HTTP list; e2e chronology + empty CTA → `/voting` | `tests/razbory.spec.js` + `test_http_razbory.py` |
| RAZB-02 | e2e sticky TOC section jump | `tests/razbory.spec.js` |
| RAZB-03 | unit FileResponse; e2e enabled/disabled + «Notebook скоро будет» dual strip | `tests/razbory.spec.js` |
| RAZB-04 | unit DTO content_kind; e2e «Качество» vs «Обзор» + soft 404 | `tests/razbory.spec.js` |

### Unclassified probe dispositions (COVERAGE.md)

| Requirement | Disposition | Covered by |
|-------------|-------------|------------|
| KNOW-01 / KNOW-03 / KNOW-04 / RAZB-02 / RAZB-04 unclassified | **N/A** — covered by this e2e gate | 04-09 Playwright + prior unit plans |

---

## Wave 0 Requirements

- [x] `tests/unit/test_http_knowledge_search.py` — KNOW-01…04 HTTP contract (blank 400, role filter, no score field, pagination)
- [x] Extend `tests/unit/test_search_knowledge.py` — role filter empty honesty; material dedupe; offset
- [x] `tests/unit/test_http_razbory.py` — list/detail/announcement/404/notebook
- [x] `tests/unit/test_razbor_use_cases.py` — content_kind metrics vs overview
- [x] Rewrite knowledge Playwright cases (no tag facet; Submit/Enter, chips, reset-filter-only) → `tests/knowledge.spec.js`
- [x] Playwright razbory specs (list empty CTA, sticky TOC, notebook disabled/enabled, Обзор vs Качество) → `tests/razbory.spec.js`
- [x] In-memory `RazborRepository` + `QueryEmbedder` fakes in `tests_support`
- [x] Seed fixtures: chunks+embeddings, published multi-section razbor ± notebook, announcement, overview-without-metrics (migration 004 + mocks)

---

## Manual-Only Verifications / UI-SPEC Backstops

> Never silent pass — each row is `verification: backstop` or `human_needed` until held-out visual check at `/gsd-verify-work`.

| Behavior | Requirement | Why Manual | Verification | Test Instructions |
|----------|-------------|------------|--------------|-------------------|
| Snippet row + no numeric scores | KNOW-01 / D-59 | Visual ranking honesty | backstop | Search at 1280; confirm snippet rows, no score badges (e2e asserts absence of score copy; visual still held-out) |
| Chronology list vs material cards | RAZB-01 / D-67 | Layout judgment | backstop | Open `/razbory`; confirm date/status overline pattern (not cover cards) |
| Dual notebook strip placement | RAZB-03 / D-71 | Layout | backstop | Published razbor with notebook — strip at top and near end |
| Hit list + «Показать ещё» pagination | KNOW overflow E2 | Mock catalog &lt; page size 10 — no live many-hits arm | human_needed | insufficient_spec under mocks; prove with live seed or fixture that forces `has_more` |
| Chronology many-items reflow | RAZB overflow E3 | Needs large catalog fixture | human_needed | insufficient_spec — visual at many chronology items |
| Long razbor sticky TOC / no H-overflow | RAZB overflow E4 | Layout judgment beyond TOC jump | backstop | Long published razbor at 1280 + mobile details TOC |
| Long query wraps in search field | KNOW long-text E1 | Visual form layout | backstop | Paste long query; field wraps without breaking Submit |
| Long razbor / announcement title wrap | RAZB long-text E4/E5 | Visual hero wrap | backstop | Long title on published + announcement stub |

**Mocks remain CI default** (`VITE_USE_MOCKS=true` in Playwright webServer). Optional live FE↔BE after 04-08 seed: see runbook §5b.

---

## Phase gate commands (04-09)

```bash
npm run test:unit
# 170 passed (2026-09-21)

npx playwright test tests/knowledge.spec.js tests/razbory.spec.js --project=web
# 7 passed (2026-09-21)
```

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s (task) / ~120s (phase gate)
- [x] `nyquist_compliant: true` set in frontmatter
- [x] UI-SPEC backstops listed explicitly (never silent pass)

**Approval:** wave_0_complete — ready for `/gsd-verify-work` (manual backstops remain held-out)
