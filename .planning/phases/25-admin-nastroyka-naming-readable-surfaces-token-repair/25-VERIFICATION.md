---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
verified: 2026-10-21T15:45:00Z
status: gaps_found
score: 37/51 must-have entries verified (1 partial, 1 not proven, 12 backstop abstentions)
goal: "An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product."
goal_clauses:
  - id: GC-1
    clause: "sees it named «Настройка»"
    status: met
  - id: GC-2
    clause: "every field and label legible in both themes"
    status: not_met
    evidence: "WR-02 light-theme status labels 1.92:1 / 1.62:1 / 3.17:1 / 3.76:1; WR-05 admin toast 1.00:1 in both themes; 25-03 must_have #12 retry link text-accent 2.43:1 on light paper"
  - id: GC-3
    clause: "chrome that matches the rest of the product"
    status: met
requirements:
  PIPEUI-01: satisfied
  PIPEUI-02: satisfied
  PIPEUI-03: satisfied
  PIPEUI-04: satisfied
  THEME-01: satisfied
  THEME-02: satisfied
requirement_ids_in_plans: [PIPEUI-01, PIPEUI-02, PIPEUI-03, PIPEUI-04, THEME-01, THEME-02]
requirement_ids_in_requirements_md: [PIPEUI-01, PIPEUI-02, PIPEUI-03, PIPEUI-04, THEME-01, THEME-02]
orphaned_requirements: []
unmapped_requirement_ids: []
review_disposition:
  closed: [CR-01, WR-01, IN-02]
  closed_by: [c0e60cc, b4369b7, aa57dd7, 47741f5]
  open_deferred: [WR-02, WR-03, WR-04, WR-05, WR-06, IN-01, IN-03, IN-04, IN-05]
  goal_threatening_open: [WR-02, WR-05]
covered_files:
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-01-PLAN.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-02-PLAN.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-03-PLAN.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-04-PLAN.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-01-SUMMARY.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-02-SUMMARY.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-03-SUMMARY.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-04-SUMMARY.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-UI-SPEC.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-VALIDATION.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-REVIEW.md
  - .planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-REVIEW-DISPOSITION.md
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - playwright.config.js
  - tests/admin-chrome.spec.js
  - tests/admin.spec.js
  - tests/helpers/contrast.js
  - tests/unit/test_semantic_token_coverage.js
  - web/src/index.css
  - web/src/components/AdminLayout.jsx
  - web/src/components/IngestSourcesSection.jsx
  - web/src/components/AppShell.jsx
  - web/src/components/ActionButton.jsx
  - web/src/components/ServiceUnavailable.jsx
  - web/src/components/UnsavedChangesDialog.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/pages/KnowledgePage.jsx
  - web/src/pages/LoginPage.jsx
  - web/src/pages/RegisterPage.jsx
behavior_unverified: 12
overrides_applied: 0
gaps_found: 4
---

# Phase 25 — Verification Report

**Phase:** `25-admin-nastroyka-naming-readable-surfaces-token-repair`
**Goal (ROADMAP § Phase 25):** «An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product.»
**Verdict:** **`gaps_found`** — clause 1 (naming) and clause 3 (chrome) are met and proven; clause 2 (**every field and label legible in both themes**) is **not met**. All four plans are green and every plan-level must_have that has an automated proof is proven, but nine review findings remain open, and two of them are direct counter-examples to the legibility clause, independently re-measured in this pass.

## Verification Method

- Read all four PLANs, all four SUMMARYs, `25-UI-SPEC.md`, `25-VALIDATION.md`, `25-REVIEW.md`, `25-REVIEW-DISPOSITION.md`, `REQUIREMENTS.md` and `ROADMAP.md` § Phase 25.
- Cross-checked every `must_haves` entry against the working tree (not against SUMMARY prose).
- Re-ran the automated evidence from a clean port: `Get-NetTCPConnection -LocalPort 5174 -State Listen` returned **no listener** before every Playwright invocation (STATE.md § Blockers precondition satisfied).
- Re-measured the contested contrast pairs with the repository's own WCAG helper (`tests/helpers/contrast.js`), not with external tooling.

### Commands run in this pass

| Command | Result |
|---|---|
| `npm run test:js` | **76 pass / 0 fail** (23 suites, 370 ms) — G-0…G-13 incl. G-9b, G-11 + proof, G-12 + proof, G-13; canon `51/13` untouched |
| `npx playwright test --list --project=web` | **152 tests in 6 files**; `admin-chrome.spec.js` named at `:77` (naming), `:119` (chrome), `:174` (select legible), `:218` (theme-independent labels) |
| `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` | **4 passed (16.1s)** |
| `npm test` | **158 passed (4.3m)** — no regressions, both projects |
| `npm run build` | exit 0, `✓ built in 385ms` (only pre-existing chunk-size / `INEFFECTIVE_DYNAMIC_IMPORT` warnings) |
| Node contrast re-measurement (`tests/helpers/contrast.js`) | see § Measured contrast evidence |
| `rg` / `Read` over `web/src` | see § Static checks |

### Static checks

| Check | Result |
|---|---|
| `@theme` blocks in `web/src/index.css` (after comment stripping) | **1** |
| `[data-theme="light"]` blocks | **1** |
| `accent-ink` occurrences under `web/src` | **0** |
| `bg-ink` occurrences (with or without alpha) | **0** |
| `bg-paper/…` or `bg-paper-2/…` opacity modifiers | **0** |
| `bg-text-primary` occurrences | **1** — `AdminDigestPage.jsx:808` (the toast, see GAP-25-2) |
| Arbitrary-value colour utilities under `web/src` | **0** (G-12 allow-list empty; CR-01 retired the last `oklch()` literals) |
| «ингеста» under `web/src` | **0** |
| «Пайплайн» / «пайплайн» in admin chrome | **0** — remaining hits are `AdminPipelineConfigPage` subtitle / `aria-label="YAML конфига пайплайна"` / `placeholder` (out of PIPEUI-01 scope by PLAN 25-01 § «НЕ трогать»: «Конфиг пайплайна» is the page heading, not the section label) and mock article text in `web/src/data/mock.js` |
| `toHaveClass(/bg-primary/)` in `tests/admin.spec.js` | **0 matches** (`rg` exit 1) |
| `bg-primary-solid` / `text-on-solid` / `bg-scrim` consumer sites | **19** class-string lines |
| `test.skip` / `it.skip` / `.todo(` in phase test files | **0**; `tests/admin-chrome.spec.js` declares exactly **4** `test(` |

## Goal-Backward Analysis

| Clause | Status | Proof | Counter-evidence |
|---|---|---|---|
| **GC-1** «sees it named «Настройка»» | **MET** | `naming:` test asserts the tab, the sr-only `h1` (single, `width ≤ 1px`) and the mobile `<option>`; `page.url()` still `/admin/pipeline`; `admin-tab-pipeline` count 1; both `aria-label="Разделы админки"` unchanged. `web/src/App.jsx:62` still mounts the page on `admin/pipeline`. | none |
| **GC-2** «every field and label legible in both themes» | **NOT MET** | The «Тип» select and both sibling fields are proven at 11.85:1 (dark) / 10.35:1 (light); the `-solid` label family and the pill/CTA/voting pairs are proven at 5.70 / 5.36 / 9.31. | Four light-theme label pairs measure **1.92 / 1.62 / 3.17 / 3.76**; the admin toast measures **1.00** in both themes; the load-error retry link measures **2.43** on light `paper`. See GAP-25-1…GAP-25-3. |
| **GC-3** «chrome that matches the rest of the product» | **MET** | `chrome:` test: «Админ» node count 1 and identical to the shell pill; tab `font-size === ingest-sources-heading font-size === 24px`; `column-gap 16px` (pre-fix 8); `margin-top 0px`; `nav.top − main.top < 48` (pre-fix 64); heading «Источники»; navigation contract intact. | none |

**Why this is not a pass.** The nine deferred findings are an **operator decision recorded in `25-REVIEW-DISPOSITION.md`**, not a proof of correctness. Per the goal-backward test, a deferral does not convert an unmet clause into a satisfied one: a label that measures 1.92:1 in the light theme is not «legible in both themes», irrespective of who accepted the debt. Equally, the six requirement IDs are **not** failed: each requirement's own must_haves are proven, and the unmet clause is scoped below to the specific pairs listed in GAP-25-1…GAP-25-3.

## Must-Have Scorecard

| Plan | must_have entries | ✓ verified | ◐ partial | ✗ not proven | ⊘ backstop → human |
|---|---|---|---|---|---|
| 25-01 (PIPEUI-01) | 6 | **6** | 0 | 0 | 0 |
| 25-02 (PIPEUI-03/04) | 11 | **9** | 0 | 0 | 2 |
| 25-03 (THEME-02/PIPEUI-02) | 23 | **13** | 1 | 1 | 8 |
| 25-04 (THEME-01) | 11 | **9** | 0 | 0 | 2 |
| **Total** | **51** | **37** | **1** | **1** | **12** |

### 25-01 — naming tracer (PIPEUI-01)

| # | must_have | Status | Evidence |
|---|---|---|---|
| 1 | tab `admin-tab-pipeline` reads «Настройка», sibling «Дайджест» | ✓ | `admin-chrome.spec.js:84`, `:109`; `AdminLayout.jsx:68`, `:60` |
| 2 | sr-only `h1` «Настройка», single, `width ≤ 1px` | ✓ | `admin-chrome.spec.js:90-96` |
| 3 | mobile `<option>` «Настройка», options `['Дайджест','Настройка']`, value `/admin/pipeline` | ✓ | `admin-chrome.spec.js:98-104`; `AdminLayout.jsx:80-81` |
| 4 | `page.url()` ends `/admin/pipeline`, testid count 1, `aria-label` intact | ✓ | `admin-chrome.spec.js:106-116` |
| 5 | `admin-chrome.spec.js` collected by the `web` project | ✓ | `--list --project=web` names all four cases; 152 tests / 6 files |
| 6 | PIPEUI-01 flagged assumption (static literal, no input domain) | ✓ | covered by the three text assertions + unchanged-URL assertion, as the plan's own formulation requires |

### 25-02 — admin chrome + «Источники» (PIPEUI-03, PIPEUI-04)

| # | must_have | Status | Evidence |
|---|---|---|---|
| 1 | «Админ» count 1 and that node is the shell pill; eyebrow gone | ✓ | `admin-chrome.spec.js:129-137` (identity check via element handle) |
| 2 | tab `font-size` === content `h2` === `24px` | ✓ | `admin-chrome.spec.js:142-144`; `AdminLayout.jsx:13` (`text-2xl`) |
| 3 | `column-gap` === `16px` and `> 8` | ✓ | `admin-chrome.spec.js:151-152`; `AdminLayout.jsx:50` (`gap-4`) |
| 4 | `margin-top` === `0px`, `nav.top − main.top < 48` | ✓ | `admin-chrome.spec.js:155-160`; `AdminLayout.jsx:50` (`mt-0`) |
| 5 | `ingest-sources-heading` exactly «Источники» | ✓ | `admin-chrome.spec.js:163`; `IngestSourcesSection.jsx:169-174`; `tests/admin.spec.js` (`toHaveText`) |
| 6 | `aria-label`s, four `data-testid`s and `mt-6` unchanged | ✓ | `admin-chrome.spec.js:166-171`; `AdminLayout.jsx:48-49`, `:72-74`, `:84` |
| 7 | **320px: both tab labels on one line in the 44px target** | ⊘ backstop | never measured by an automated run → § Human verification #1 |
| 8 | **320px: mobile select keeps 44px with `paper` fill / `ink` text** | ⊘ backstop | never measured by an automated run → § Human verification #2 |
| 9-11 | PIPEUI-03 / PIPEUI-04 flagged assumptions (`unclassified`, `boundary`, `precision`) | ✓ | resolved by exact-string equality and relative measured comparisons, as the plan states |

### 25-03 — token family + readable «Тип» (THEME-02, PIPEUI-02)

| # | must_have | Status | Evidence |
|---|---|---|---|
| 1 | coverage gate green (every used utility resolves, themed have overrides, flat do not) | ✓ | `npm run test:js` 76/0; G-0…G-13 |
| 2 | exactly one `@theme` and one `[data-theme="light"]` | ✓ | G-0; independently re-counted: 1 / 1 |
| 3 | `#ingest-sources-kind` pair `rgb(203,213,225)`/`rgb(19,25,37)` dark, `rgb(51,65,85)`/`rgb(255,255,255)` light, opaque, ≥ 4.5 | ✓ | `select legible in both themes`; ratios 11.85 / 10.35 |
| 4 | sibling `-id` / `-label` yield the identical pair | ✓ | same test, loop over three locators |
| 5 | options exactly `Канал` / `Плейлист` | ✓ | same test |
| 6 | `--color-paper` resolves at runtime | ✓ | same test + built CSS |
| 7 | zero `accent-ink`, zero `bg-ink`, no alpha on `bg-paper*` | ✓ | G-5 / G-6 + grep (0 / 0 / 0) |
| 8 | family contrast incl. `on-solid`/`danger-solid` floor ≥ 4.829 | ✓ | G-7; G-13 for `danger-ink` |
| 9 | aliases `paper`/`paper-2`/`ink` both themes, `rule`/`muted` dark only | ✓ | G-8 |
| 10 | Empty fields: opaque `paper` fill, `ink-2` value, **`rule` edge** | ◐ **partial** | fill + value proven by the spec; **`border-color` is never asserted at runtime** — the edge is proven only statically through G-4. Recorded rather than rounded up. See GAP-25-4. |
| 11 | Zero sources: heading + «Пока нет источников» on `paper`, `ink`/`muted` | ✓ | `IngestSourcesSection.jsx:169-200`; texts pinned by `tests/admin.spec.js` (158 passed) |
| 12 | Load error: «Не удалось загрузить источники» **and** «Повторить загрузку», **both ≥ 4.5:1 on `paper` in both themes** | ✗ **not proven** | The message is `text-ink-2` (11.85 / 10.35 ✓), but the action is `text-accent` = **2.43:1** on light `paper` (`#06B6D4` on `#FFFFFF`). The plan itself forbids touching `text-accent` (§ Known adjacent defects 3) — an internal contradiction, flagged by 25-03-SUMMARY. See GAP-25-3. |
| 13-20 | 8 backstops (partial form, 200-char id, initial load, id-only row, 20 rows @320, 0/1/20 rhythm, long id, 320px dialog) | ⊘ backstop | never measured → § Human verification #3…#10 |
| 21-23 | PIPEUI-02 (`empty`, `encoding`) and THEME-02 (`unclassified`) flagged assumptions | ✓ | `background != rgba(0,0,0,0)` before arithmetic + exact `rgb(...)` string equality; CSS-contract gate G-0…G-13 |

### 25-04 — theme-independent labels (THEME-01)

| # | must_have | Status | Evidence |
|---|---|---|---|
| 1 | pill `rgb(255,255,255)` on `rgb(124,58,237)`, ≥ 4.5 both themes | ✓ | `theme-independent labels in both themes`; 5.70 |
| 2 | `ingest-sources-add` white on `rgb(14,116,144)`, ≥ 4.5 | ✓ | same test; 5.36 |
| 3 | `voting` `rgb(15,23,42)` on `rgb(234,179,8)`, ≥ 4.5 — positive assertion | ✓ | same test (both themes) + G-7; 9.31 |
| 4 | no fill carries a theme-dependent label (G-9) | ✓ | G-9 empty offender list; G-9b reaches the `-solid` family |
| 5 | no full-screen veil uses a theme-dependent token (G-10); four overlays on `bg-scrim` | ✓ | G-10 empty; `UnsavedChangesDialog.jsx:26`, `AdminDigestPage.jsx` ×3 |
| 6 | no pill assertion rides on a substring | ✓ | five token-exact sites; `rg` for `toHaveClass(/bg-primary/)` empty |
| 7 | in-flight label keeps its colour, only opacity changes | ✓ (static) | `ActionButton.jsx` `stateClass.loading = 'cursor-wait opacity-80'` — no colour token; no e2e colour measurement exists, so this is a reading, as the SUMMARY states |
| 8-9 | **320px: longest CTA label wraps inside 44px**, **pill label renders fully inside the pill** | ⊘ backstop | never measured → § Human verification #11…#12 |
| 10-11 | THEME-01 flagged assumptions (`empty`, `encoding`) | ✓ | `background != rgba(0,0,0,0)` + exact `rgb(...)` equality; no length semantics in the domain |

## Requirement Coverage

Frontmatter cross-reference: PLAN frontmatter declares `PIPEUI-01` (25-01), `PIPEUI-03` + `PIPEUI-04` (25-02), `THEME-02` + `PIPEUI-02` (25-03), `THEME-01` (25-04). Union = **six** IDs, byte-identical to `REQUIREMENTS.md` § «Admin section naming and readable surfaces» / «Theme contrast» and to `ROADMAP.md` § Phase 25 **Requirements**. No orphaned requirement, no ID declared in a PLAN but absent from `REQUIREMENTS.md`, and none in `REQUIREMENTS.md` unmapped to a plan.

| Requirement | Source plan(s) | Status | Evidence |
|---|---|---|---|
| **PIPEUI-01** — pipeline section named «Настройка» on tab, sr-only heading and mobile select, URL unchanged | 25-01 | ✓ **SATISFIED** | `naming:` test (8 assertions) — tab/h1/option texts, single h1 at `≤ 1px`, options array, value `/admin/pipeline`, `page.url()`, `aria-label` ×2; `App.jsx:62` route intact; `playwright.config.js` `testMatch` collects `admin(-chrome)?.spec.js` |
| **PIPEUI-02** — «Тип» select + «Канал»/«Плейлист» legible in both themes with explicit surface/text | 25-03 | ✓ **SATISFIED** | `select legible in both themes`: dark `rgb(203,213,225)` on `rgb(19,25,37)` (11.85), light `rgb(51,65,85)` on `rgb(255,255,255)` (10.35), opaque, sibling fields identical, options exact |
| **PIPEUI-03** — ingest block heading reads «Источники» | 25-02 | ✓ **SATISFIED** | `IngestSourcesSection.jsx:173`; `chrome:` test + `tests/admin.spec.js` `toHaveText('Источники')`; `rg 'ингеста' web/src` → 0 |
| **PIPEUI-04** — eyebrow gone, tab type = content `h2`, wider gap, less empty space | 25-02 | ✓ **SATISFIED** | `chrome:` test: count 1 (`Админ`), `24px === 24px`, `column-gap 16px > 8`, `margin-top 0px`, `nav.top − main.top < 48`; `tests/admin.spec.js` `text-2xl` ×2 |
| **THEME-01** — white labels on `primary`/`accent` fills and the active pill; `voting` keeps its dark label; ≥ 4.5 | 25-04 | ✓ **SATISFIED** | `theme-independent labels in both themes` (3 pairs × 2 themes): 5.70 / 5.36 / 9.31; G-9 / G-10 empty; five token-exact pill assertions |
| **THEME-02** — semantic admin token family declared in `@theme` with light overrides + a test that fails on an undeclared used token | 25-03 (gates extended in 25-04) | ✓ **SATISFIED** (one recorded deviation) | `index.css:39-44` + light overrides `:150-155`; seven theme-independent roles `:55-61` with no override (G-3); gate G-0…G-13. **Deviation:** the requirement text lists `accent-ink` among the family; the phase deliberately **retired** it (D-10) after migrating all three consumers to `bg-accent-solid`/`text-on-solid`, and G-5 now forbids it. Every token actually *used* under `web/src` resolves, and the gate fails on any new undeclared one — the requirement's operative clause («a test fails when a token used by those components is undeclared») holds. |

**Orphaned requirements:** none.
**Unmapped requirement IDs:** none.

**Status semantics.** `REQUIREMENTS.md` already marks all six IDs `Complete`, and this report does not overturn that: each requirement's own must_haves are proven. The `gaps_found` verdict is about the **phase goal**, which is broader than the sum of the six requirement statements — its middle clause quantifies over *every* field and label, including the status pills, error panels, auth field errors, toast and the load-error action that no requirement ID owns. Requirement-level `Complete` and goal-level `not met` are therefore both true at once, and the gap is recorded rather than resolved by either document.

## Measured contrast evidence

Recomputed in this pass with `tests/helpers/contrast.js` (`parseColor` → `relativeLuminance` → `contrastRatio`), compositing tints with the standard source-over formula.

### Pairs the phase fixed (≥ 4.5:1 required)

| Pair | Theme | Ratio | Verdict |
|---|---|---|---|
| `ink-2` on `paper` (select value / field surface) | dark `#CBD5E1` on `#131925` | **11.85** | ✓ |
| `ink-2` on `paper` | light `#334155` on `#FFFFFF` | **10.35** | ✓ |
| `on-solid` on `primary-solid` (pill, primary CTA) | both `#FFFFFF` on `#7C3AED` | **5.70** | ✓ |
| `on-solid` on `accent-solid` | both `#FFFFFF` on `#0E7490` | **5.36** | ✓ |
| `on-solid` on `success-solid` | both `#FFFFFF` on `#15803D` | **5.02** | ✓ |
| `on-solid` on `danger-solid` (floor) | both `#FFFFFF` on `#DC2626` | **4.829** | ✓ |
| `voting-ink` on `voting` | both `#0F172A` on `#EAB308` | **9.31** | ✓ |
| `danger-ink` on `paper` / `paper-2` | dark `#F87171` | **6.36 / 5.75** | ✓ (CR-01 fix) |
| `danger-ink` on `paper` / `paper-2` | light `#B91C1C` | **6.47 / 5.90** | ✓ (CR-01 fix) |

### Pairs that still fail (open findings — light theme unless stated)

| Pair | Measured composite | Ratio | Threshold | Finding |
|---|---|---|---|---|
| `text-success` `#22C55E` on `bg-success/15` over `bg-app` (digest status pill) | `#D8F2E4` | **1.92** ✗ | 4.5 | **WR-02** (`AdminDigestPage.jsx:717`) |
| `text-voting` `#EAB308` on `bg-voting/20` over `bg-app` (digest status pill) | `#F5ECCB` | **1.62** ✗ | 4.5 | **WR-02** (`AdminDigestPage.jsx:718`) |
| `text-danger` `#EF4444` on `bg-danger/10` over `bg-app` (config error panel) | `#F7E8EA` | **3.17** ✗ | 4.5 | **WR-02** (`AdminPipelineConfigPage.jsx:333-364`) |
| `text-danger` `#EF4444` on `bg-bg-surface` `#FFFFFF` (Login/Register field errors) | `#FFFFFF` | **3.76** ✗ | 4.5 | **WR-02** (`LoginPage.jsx:160/165/190`, `RegisterPage.jsx:141/172/177/202`) |
| `text-text-primary` on `bg-text-primary` (admin toast) | same token both sides | **1.00** ✗ (both themes) | 4.5 | **WR-05** (`AdminDigestPage.jsx:808`; G-10 exemption at `test_semantic_token_coverage.js:566`) |
| `text-accent` `#06B6D4` on light `paper` (load-error «Повторить загрузку») | `#FFFFFF` | **2.43** ✗ | 4.5 | 25-03 **must_have #12** (`IngestSourcesSection.jsx:186`; dark side is 7.25 ✓) |

The same status pairs pass in the dark theme (6.71 / 6.84 / 4.71 / 5.10 respectively), which is exactly why the phase's own gates are green: G-7 iterates `paper`/`paper-2` × `ink`/`ink-2`/`muted`, and G-9/G-10 are structural token scanners. Neither family of checks covers a *status token used as text on a tint*.

## Gaps Found

### GAP-25-1 — WR-02: status tokens as text on tints fail 4.5:1 in the light theme (goal clause GC-2)

**Severity:** goal-blocking (contrast of user-facing labels in the light theme)
**Where:** `web/src/pages/AdminDigestPage.jsx:717-718`; `web/src/pages/AdminPipelineConfigPage.jsx:333-335`, `:344`, `:354`, `:362-364`; `web/src/pages/LoginPage.jsx:160`, `:165`, `:190`; `web/src/pages/RegisterPage.jsx:141`, `:172`, `:177`, `:202`
**Measured:** 1.92:1, 1.62:1, 3.17:1, 3.76:1 (table above) — all below the 4.5:1 the phase itself adopts as its threshold.
**Why it blocks the goal:** these are visible labels («ready»/«draft» pills, the config validation panel, auth field errors) in the light theme. The goal says *every field and label* is legible *in both themes*; four of them are not.
**Deferred because (operator, `25-REVIEW-DISPOSITION.md`):** it needs its own `-ink` variant family plus an extension of G-7 to tint composites — a separate behavioural layer, «первый кандидат следующей фазы».
**Fix direction (from `25-REVIEW.md`):** add themed `-ink` variants (`success-ink`, `voting-ink-on-tint`, reuse `danger-ink`) and make G-7 iterate the `-ink` on `/10`–`/20` composite over `paper` pairs.

### GAP-25-2 — WR-05: the admin toast is 1.00:1 in both themes (goal clause GC-2)

**Severity:** goal-blocking
**Where:** `web/src/pages/AdminDigestPage.jsx:808` — `rounded-full bg-text-primary … text-sm text-text-primary`
**Measured:** `#F1F5F9` on `#F1F5F9` (dark) and `#0F172A` on `#0F172A` (light) = **1.00:1** in both themes. The digest-send confirmation is invisible.
**Gate status:** deliberately exempted — `test_semantic_token_coverage.js:566` `if (token === 'bg-text-primary') continue`, so the suite stays green whether or not it is ever fixed.
**Deferred because (operator):** «отдельный компонент», not a label-on-fill from THEME-01 and not a scrim; the exemption was kept to avoid widening the review-closure scope.

### GAP-25-3 — 25-03 must_have #12 is unproven and provably failing (load-error action)

**Severity:** must-have not proven; contributes to GC-2
**Where:** `web/src/components/IngestSourcesSection.jsx:186` — `font-medium text-accent hover:underline`
**Measured:** `#06B6D4` on light `paper` `#FFFFFF` = **2.43:1** (dark `paper` = 7.25 ✓). The must_have demands *both* the message and the action reach 4.5:1 on `paper` in both themes.
**Root cause:** the must_have contradicts the same plan's prohibition («не трогать `text-accent` … known adjacent defect 3»). 25-03-SUMMARY recorded it as `NOT PROVEN — противоречие внутри плана/UI-SPEC` and asked the planner to resolve it; that resolution has not landed.
**Note:** this finding is *not* attributable to a plan task failure — the executor could not satisfy both clauses at once without a new decision (`--color-accent-ink`-class token). It is recorded so the unproven must_have is not silently scored as proven.

### GAP-25-4 — 25-03 must_have #10 is only partially proven (field `rule` edge)

**Severity:** partial (no requirement failure, but the must_have is not fully measured)
**Where:** `tests/admin-chrome.spec.js` never reads `border-color`; the `rule` edge is proven only statically by G-4 (`border-rule` resolving to a declared `--color-rule`).
**Related open finding WR-06:** the declared light `rule` `#CBD5E1` is **1.48:1** against `paper` — below WCAG 1.4.11's 3:1 for UI component boundaries. This is a **non-text** criterion, so it does not by itself break the goal's «label legible» clause, but the deviation is recorded in `25-REVIEW.md` and is intentionally not claimed as conformant.

### Open findings that are not goal-blocking (recorded, not scored)

| ID | Finding | Why it does not change the verdict |
|---|---|---|
| WR-03 | `ActionButton` appends both `variantClass` and `stateClass`, so two fills coexist; today the state fill is dead, and a stylesheet-order flip would produce white-on-yellow 1.92:1 | Latent: the current cascade order makes the state unreachable; no shipped surface renders the failing pair. Verified `ActionButton.jsx:1-34` unchanged in this respect. |
| WR-04 | `gotoAdmin` never awaits `data-theme`, so light-theme assertions race the `useEffect` | Test reliability only; 158 runs green, no flake observed in this pass. |
| WR-06 | Light field edge 1.48:1 vs WCAG 1.4.11 3:1 | Non-text criterion, recorded deviation (see GAP-25-4). |
| IN-01 | `THEME_DEPENDENT_LABELS` is half dead (`text-accent-ink`, `text-bg-app` have no consumers) | Cosmetic gate hygiene. |
| IN-03 | G-7's `worst >= 4.829` floor is a change-detector, not an independent contrast gate | 4.5:1 is enforced by the main loop. |
| IN-04 | `issue_url` rendered as a `Link` without scheme/origin validation | Backend-controlled data, outside THEME/PIPEUI scope. |
| IN-05 | `.sr-only` re-declared although Tailwind v4 ships it | Harmless duplication; `naming:` still measures `width ≤ 1`. |

### Closed findings (verified in this pass, not merely asserted)

| ID | Closure commit | Verified state |
|---|---|---|
| CR-01 | `aa57dd7` (RED `c0e60cc`) | `rg 'oklch|\[#' web/src --glob '*.jsx'` → **0**; `danger-ink` on 7 lines (237, 253, 336, 338, 346, 356, 362); `--color-danger-ink` declared `index.css:50` + light `:156`; measured 6.36 / 5.75 / 6.47 / 5.90; G-11/G-12/G-13 green |
| WR-01 | `b4369b7` | G-9b (fill list reaches `-solid`), G-11 (+ proof reproducing the 1.98:1 offender), G-12 (+ prefix proof), G-13; 76/0 |
| IN-02 | `c0e60cc` | `parseColor` accepts `oklch()` (CSS Color 4 → oklab → linear sRGB) — this is what made CR-01 measurable |

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|---|---|---|---|
| — | `TBD` / `FIXME` / `XXX` in phase implementation files | none | `rg` clean |
| — | Skipped or `.todo` tests in phase test files | none | 0; 4 specs + 76 unit assertions all execute |
| — | Second `@theme` / second `[data-theme="light"]` block | none | 1 / 1 (G-0 green) |
| — | Arbitrary-value colour utilities under `web/src` | none | 0 after CR-01 (G-12 green) |
| `web/src/pages/AdminDigestPage.jsx:808` | Theme-dependent token used as both fill and label | **goal-blocking** | GAP-25-2 (WR-05) |
| status-tint call sites | Theme-flat status token used as text on a themed tint | **goal-blocking** | GAP-25-1 (WR-02) |

## Human Verification Required

The twelve `verification: backstop` must_haves were never measured by an automated run. Per the UI-SPEC (§ Planner lift) a backstop the verifier cannot confirm abstains → `human_needed`, never a silent pass. The two 320px assertions from 25-02 and 25-04 are #1-#2 and #11-#12 below.

Set the viewport explicitly (`320 × 568`) on `/admin/pipeline` with mocks (`VITE_USE_MOCKS=true`), dark **and** light theme.

| # | Plan | Test | Expected | Why human |
|---|---|---|---|---|
| 1 | 25-02 | **320px: tab row** — inspect «Дайджест» and «Настройка» | Both labels on **one line**, inside the 44px (`min-h-11`) target, no clipping, no wrapping, no horizontal scroll; `sm:flex` hides the row below 640px, so verify the layout at the `sm` boundary too if the row is visible | `overflow` backstop; no automated 320px case exists |
| 2 | 25-02 | **320px: mobile section select** | 44px height, painted `paper` fill, `ink` text, selected option text not clipped | `overflow` backstop; only computed colours are asserted, not geometry at 320px |
| 3 | 25-03 | Partially filled form (kind chosen, id + label empty) | All three controls still paint opaque `paper`, `ink-2` value text, both themes | `partial` backstop |
| 4 | 25-03 | 200-character id typed into `ingest-sources-id` | Scrolls inside the field; does not widen the `paper` block; does not clip «Добавить источник» | `long-text` backstop |
| 5 | 25-03 | Initial load in flight | No rows, no skeleton; heading «Источники» and `paper` surface stay painted, both themes | `loading` backstop |
| 6 | 25-03 | Row with id only (no label) | Enable/disable toggle and all row actions visible and legible | `partial` backstop |
| 7 | 25-03 | 20 rows at 320px | Page extends vertically, no row clipped, no horizontal scrollbar | `overflow` backstop |
| 8 | 25-03 | 0 / 1 / 20 rows | Same per-row `paper-2` surface and 8px rhythm; no singular/plural copy | `zero-one-many` backstop |
| 9 | 25-03 | Long channel/playlist id in a row | Wraps or truncates inside the row; row actions stay in the viewport; text stays ≥ 4.5:1 | `long-text` backstop |
| 10 | 25-03 | 320px: unsaved-changes dialog | Body wraps, both actions «Остаться» / «Уйти без сохранения» fully visible, no horizontal overflow | `overflow` backstop |
| 11 | 25-04 | **320px: longest CTA label** («Уйти без сохранения») | Wraps inside the 44px min-height target without clipping | `overflow` backstop |
| 12 | 25-04 | **320px: active nav pill label** | Renders fully inside the pill, `#FFFFFF` on `primary-solid`, no clipping | `overflow` backstop |

Additionally, two behaviours are proven by **reading** rather than by measurement (both flagged `human_judgment: true` in their SUMMARYs):

| # | Plan | Behaviour | Why human |
|---|---|---|---|
| 13 | 25-04 | In-flight button label keeps its colour (only opacity changes) | `stateClass.loading = 'cursor-wait opacity-80'` contains no colour token; no e2e measures colour mid-flight |
| 14 | 25-03 | Empty-control `rule` edge is actually painted | only static through G-4; `border-color` never read at runtime (GAP-25-4) |

## Assessment

- **All four plans delivered what they promised.** Every must_have with an automated proof is verified; the tracing slice, chrome geometry, token family, readable «Тип» and the `-solid`/scrim migrations are real in the tree and reproducible from a clean port. `npm test` = 158 passed, `npm run test:js` = 76 passed, `--list` = 152 tests in 6 files, build green.
- **The phase goal is nevertheless not fully achieved.** Its middle clause — «every field and label legible in both themes» — has measurable counter-examples in the light theme (1.92, 1.62, 3.17, 3.76), an invisible admin toast (1.00 in both themes), and one plan must_have (#12, 2.43) that cannot be proven without resolving an internal plan contradiction. `status: gaps_found`.
- **What is *not* at fault:** the naming clause, the chrome clause, all six requirement IDs, and the token-coverage root-cause repair. Scoring those as failed would be as dishonest as scoring the legibility clause as passed.
- **Recommended next action:** open the follow-up phase that WR-02/WR-05/25-03-#12 already point at — a themed status-ink family (`success-ink`, `voting-ink-on-tint`, reuse `danger-ink`) plus a G-7 extension to tint composites and removal of the `bg-text-primary` carve-out in G-10. That single change closes GAP-25-1, GAP-25-2 and GAP-25-3 together, because all three are the same defect: a theme-flat token used as a label on a theme-dependent surface.
