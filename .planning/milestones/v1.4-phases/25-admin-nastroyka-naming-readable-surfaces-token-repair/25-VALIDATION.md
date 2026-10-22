---
phase: 25
slug: admin-nastroyka-naming-readable-surfaces-token-repair
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-21
---

# Phase 25 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `node:test` (Node 24.21.0) for CSS/token contracts + `@playwright/test` 1.62.1 for DOM / computed style |
| **Config file** | `scripts/run-unit-js.cjs` (auto-discovers `tests/unit/*.js`); `playwright.config.js` (requires `testMatch` amendment — `admin-chrome` is currently not matched and silently never runs) |
| **Quick run command** | `npm run test:js` (≈0.3 s) and `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` |
| **Full suite command** | `npm run test:js` then `npm run test:web` (`--project=web`; 148 tests before this phase) |
| **Estimated runtime** | ~0.3 s unit / ~2–4 min full web suite |

---

## Sampling Rate

- **After every task commit:** `npm run test:js` + the targeted `-g` run of `tests/admin-chrome.spec.js`
- **After every plan wave:** `npm run test:js` and `npm run test:web` (148 + new tests)
- **Before `/gsd-verify-work`:** both suites green, plus `npm run build` to prove the CSS still compiles
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | — | 0 | THEME-02 | T-25-04 / T-25-05 | `admin-chrome.spec.js` is actually collected by Playwright (`--list` names the file) | config | `npx playwright test --list --project=web` | ❌ W0 | ⬜ pending |
| TBD | — | 0 | THEME-02 | T-25-02 | G-1…G-8: every used semantic utility resolves to a declared `--color-*`, theme-dependent tokens have a `[data-theme="light"]` override, no `accent-ink` / `bg-ink` / alpha on `bg-paper*` | unit | `npm run test:js` | ❌ W0 | ⬜ pending |
| TBD | — | 0 | PIPEUI-02 | — | `tests/helpers/contrast.js` parses sRGB/hex and throws on `transparent` or alpha < 1 | unit | `npm run test:js` | ❌ W0 | ⬜ pending |
| TBD | — | 1 | PIPEUI-01 | T-25-01 | Tab, sr-only `h1` and mobile `<option>` read «Настройка»; `page.url()` still `/admin/pipeline`; `data-testid="admin-tab-pipeline"` unchanged; sibling tab still «Дайджест» | e2e | `npx playwright test tests/admin-chrome.spec.js -g "naming" --project=web` | ❌ W0 | ⬜ pending |
| TBD | — | 1 | PIPEUI-02 / THEME-02 | — | «Тип» select computed `background-color` equals the declared `paper` value (`rgb(19, 25, 37)` dark / `rgb(255, 255, 255)` light), `color` equals `ink-2`, contrast ≥ 4.5, «Канал» / «Плейлист» options present — asserted in both themes | e2e | `npx playwright test tests/admin-chrome.spec.js -g "select legible" --project=web` | ❌ W0 | ⬜ pending |
| TBD | — | 1 | PIPEUI-03 | — | `#ingest-sources-heading` === «Источники»; stale `"Источники ингеста"` pin at `tests/admin.spec.js:1834` amended | e2e | `npx playwright test tests/admin-chrome.spec.js -g "chrome" --project=web` | ❌ W0 | ⬜ pending |
| TBD | — | 1 | PIPEUI-04 | — | `getByText('Админ',{exact:true})` count 1; tab `font-size` equals heading `24px`; `column-gap` 16px > 8px; `margin-top` 0; `nav.top − main.top < 48` | e2e | `npx playwright test tests/admin-chrome.spec.js -g "chrome" --project=web` | ❌ W0 | ⬜ pending |
| TBD | — | 1 | THEME-01 | T-25-03 | Pill label `#FFFFFF` on `rgb(124, 58, 237)`, accent CTA `#FFFFFF` on `rgb(14, 116, 144)`, `voting` `rgb(15, 23, 42)` on `rgb(234, 179, 8)` — both themes, each ≥ 4.5 (voting pinned as a positive assertion) | e2e | `npx playwright test tests/admin-chrome.spec.js -g "theme-independent labels" --project=web` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

> Task IDs are refreshed from the final PLAN.md frontmatter after planning; the requirement-level mapping and RED evidence are fixed by `25-RESEARCH.md` § Validation Architecture.

---

## RED Evidence (why each check fails on the pre-fix tree)

| Check | Pre-fix measurement | Failing reason |
|---|---|---|
| `admin-tab-pipeline` text | `"Пайплайн"` | three literals in `AdminLayout.jsx` not renamed |
| `h1` text / `admin-section-select` options | `"Пайплайн"` / `["Дайджест", "Пайплайн"]` | same |
| select `background-color` | `rgba(0, 0, 0, 0)` | `bg-paper` never generated → transparent preflight background |
| select `color` | `rgb(241, 245, 249)` | `text-ink-2` never generated → inherits `text-primary` |
| contrast helper on select | throws `transparent surface has no contrast` | transparent surface |
| G-1…G-8 | first `assert.ok(dark.has('--color-paper'))` fails | all six tokens absent (`getPropertyValue` = `""`) |
| pill `color` | dark `rgb(241, 245, 249)` / light `rgb(15, 23, 42)` | `text-text-primary` is theme-dependent |
| pill ratio | dark 3.87 / light 4.22 | both themes fail |
| accent CTA ratio | dark 2.22 | `text-accent-ink` inert → inherits `text-primary` |
| `voting` label | dark `rgb(11, 15, 23)` (10.00 ✓) / light `rgb(248, 250, 252)` (**1.83 ✗**) | `text-bg-app` flips — the exception fails *positively* in light theme |
| `getByText('Админ',{exact:true})` count | **2** | eyebrow `<p>` + shell `<a>` |
| tab vs heading `font-size` | `30px` vs `24px` | `text-3xl` |
| `column-gap` | `8px` | `gap-2` |
| `nav.top − main.top` | `64` | eyebrow 16px + `mt-2` 8px |
| `#ingest-sources-heading` | `"Источники ингеста"` | text |

---

## Wave 0 Requirements

- [ ] `playwright.config.js` — `testMatch` must include `admin-chrome`, otherwise the new spec is silently skipped
- [ ] `tests/helpers/contrast.js` — `parseColor` / `relativeLuminance` / `contrastRatio` (throws on alpha < 1)
- [ ] `tests/unit/test_semantic_token_coverage.js` — G-1…G-8, own `parseBlock`, scans `web/src/**/*.{js,jsx}`
- [ ] `tests/admin-chrome.spec.js` — criteria 1, 2, 4, 5 (both themes)
- [ ] `tests/admin.spec.js` — amendments at `:139/:151`, `:165`, `:274`, `:416`, `:1307`, `:1834`, `:1754-1764`, `:186/:198/:216/:299/:312`

*Existing infrastructure covers the rest: `node:test`, Playwright + browsers, Vite dev server on `:5174`, `scripts/run-unit-js.cjs`. Nothing to install.*

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
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
