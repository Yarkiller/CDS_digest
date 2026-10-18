---
phase: 2
slug: issue-materials-archive
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-09-19
updated: 2026-09-20
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright `^1.62.1` + pytest via `uv run pytest` |
| **Config file** | `playwright.config.js`; pytest via project `uv` |
| **Quick run command** | `npm run test:web` / `uv run pytest tests/unit/test_http_issues.py -x` |
| **Full suite command** | `npm test` && `npm run test:unit` |
| **Estimated runtime** | ~120 seconds (full gate in 02-06 only) |

---

## Sampling Rate

- **After every task commit:** Run targeted pytest file or single Playwright test
- **After every plan wave:** Run targeted verifies for that plan (not full suite until 02-06)
- **Before `/gsd-verify-work`:** Full suite must be green (`npm test` + `npm run test:unit`) via 02-06 final gate
- **Max feedback latency:** Prefer &lt;60s per task; full suite ~120s allowed once at phase gate (02-06-02)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | ISSUE-01 | T-02-01 | JWT on GET /issues/current | unit | `uv run pytest tests/unit/test_get_current_issue.py tests/unit/test_http_issues.py -x` | ✅ | ✅ green |
| 02-01-02 | 01 | 1 | ISSUE-01 | T-02-02 | empty CTA no blank page | e2e | `npx playwright test tests/web-app.spec.js -g "готовится\|issue\|выпуск"` | ✅ | ✅ green |
| 02-01-03 | 01 | 1 | — | — | Wave 0 importorskip scaffolds + file existence | unit | node exists-check + pytest scaffolds (skip OK, fail not OK) | ✅ | ✅ green |
| 02-02-01 | 02 | 2 | ISSUE-01, MAT-01 | T-02-04 | idempotent seed no TRUNCATE | script | node check on `002_phase2_issue_seed.sql` | ✅ | ✅ green |
| 02-02-02 | 02 | 2 | ISSUE-01, MAT-01 | T-02-03, T-02-05 | service_role adapters only | unit | `uv run pytest tests/unit/test_supabase_issue_repository_contract.py tests/unit/test_live_container_wiring.py -x` | ✅ | ✅ green |
| 02-02-03 | 02 | 2 | ISSUE-01 | T-02-04 | [BLOCKING] seed applied | human | SQL counts after push/MCP | ✅ | ✅ green |
| 02-03-01 | 03 | 3 | ISSUE-04 | T-02-01 | archive excludes current | unit | `uv run pytest tests/unit/test_list_archive_issues.py tests/unit/test_get_issue_by_number.py tests/unit/test_http_issues.py -x` | ✅ | ✅ green |
| 02-03-02 | 03 | 3 | ISSUE-04 | — | /archive nav + past issue | e2e | `npx playwright test tests/web-app.spec.js -g "archive\|Архив"` | ✅ | ✅ green |
| 02-04-01 | 04 | 4 | MAT-02 | T-02-01 | draft → 404 | unit | `uv run pytest tests/unit/test_get_material_for_reader.py tests/unit/test_http_materials.py -x` | ✅ | ✅ green |
| 02-04-02 | 04 | 4 | MAT-01 | T-02-06 | rehype-sanitize TOC | unit | `node --test tests/unit/test_markdown_toc.js` | ✅ | ✅ green |
| 02-04-03 | 04 | 4 | MAT-01, MAT-02, MAT-03, ISSUE-03 | T-02-06 | prose + soft 404 + dek hide | e2e | `npx playwright test tests/web-app.spec.js -g "material\|материал\|rag-systems"` | ✅ | ✅ green |
| 02-05-01 | 05 | 5 | ISSUE-02 | — | voting_cycle on current DTO | unit | `uv run pytest tests/unit/test_get_current_issue.py tests/unit/test_http_issues.py -x` | ✅ | ✅ green |
| 02-05-02 | 05 | 5 | ISSUE-02 | — | open/closed callout | e2e | `npx playwright test tests/web-app.spec.js -g "Голосование\|Выбрать тему\|callout"` | ✅ | ✅ green |
| 02-06-01 | 06 | 6 | D-21..23 / ISSUE-* | T-02-02 | splash no mock fallback | e2e | `npx playwright test tests/web-app.spec.js -g "ошибочка\|bad_gateway\|Повторить"` | ✅ | ✅ green |
| 02-06-02 | 06 | 6 | ISSUE-01..04, MAT-01..03 | T-02-02 | phase gate (full suite) | e2e+unit | `npm run test:web && npm run test:unit` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Requirement → assertion path (phase gate)

| Requirement | Automated path |
|-------------|----------------|
| ISSUE-01 | unit `test_get_current_issue` / `test_http_issues` + e2e current hero/TOC or empty |
| ISSUE-02 | unit voting_cycle + e2e open/closed/absent callout |
| ISSUE-03 | e2e material TOC + prose from slug `/materials/rag-systems` |
| ISSUE-04 | unit archive + e2e Архив nav / past issue / empty archive |
| MAT-01 | unit markdown TOC + e2e Статья badge + prose |
| MAT-02 | unit draft 404 + e2e soft «Материал не найден» (no bad_gateway) |
| MAT-03 | e2e dek hide + related/prose reader surface |

---

## Wave 0 Requirements

- [x] `tests/unit/test_get_current_issue.py` — D-24 selection + empty current (02-01)
- [x] `tests/unit/test_list_archive_issues.py` — importorskip scaffold (02-01); green when 02-03 modules land
- [x] `tests/unit/test_get_material_for_reader.py` — importorskip scaffold (02-01); green when 02-04 modules land
- [x] `tests/unit/test_http_issues.py` / `test_http_materials.py` — JWT + 401/404 shapes
- [x] Extend `tests/web-app.spec.js` — archive, callout, markdown TOC, splash (02-03…02-06)
- [x] In-memory fakes for `IssueRepository` / cycle reader in `tests_support/in_memory.py`
- [x] Optional: unit test for `markdownToc` heading extraction (02-04)

---

## Flagged assumptions (SPECLESS / EDGE_ABSENT)

All ISSUE-*/MAT-* probe items were unclassified; plans author explicit must_haves from CONTEXT/RESEARCH/UI-SPEC:

| Assumption | Source | Plan handling |
|------------|--------|---------------|
| A1 Editor byline constant string | RESEARCH | 02-04 DTO constant — no schema column |
| A2 Open-first else latest closed cycle | RESEARCH | 02-05 use-case selection |
| A3 rehype-sanitize required | RESEARCH security | 02-04 deps + threat T-02-06 |
| A4 Archive cards typography/count only | RESEARCH / UI-SPEC | 02-03 — no thumbs required |
| Unpublished issue number → soft empty | RESEARCH Q1 RESOLVED | 02-03 404/empty + CTA to current |
| Related DTO `{slug,title}[]` | RESEARCH Q2 RESOLVED | 02-04 |
| UI-SPEC 10 backstops | 02-UI-SPEC ## UI Considerations | must_haves.truths — verify visually at phase verify |

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Typography-only hero atmosphere | ISSUE-01 / UI-SPEC / D-26 | Visual density/contrast judgment | Open `/` at 1280 and 390; confirm no cover image, typography-only hero |
| UI-SPEC backstops (overflow/plural/long-text/nav) | UI Considerations | Held-out visual | Spot-check IssueTOC, archive grid, material TOC, hero, nav at 390/1280 — see `describe.skip` in `tests/web-app.spec.js` |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (importorskip scaffolds keep suite green)
- [x] No watch-mode flags
- [x] Feedback latency &lt;60s for non-gate tasks; full suite only at 02-06-02
- [ ] `nyquist_compliant: true` set in frontmatter *(left false until `/gsd-validate-phase`)*

**Approval:** pending validate-phase
