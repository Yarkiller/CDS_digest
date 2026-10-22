---
phase: 26-section-context-anchor-scrolling-and-header-active-state
verified: 2026-10-22T06:06:00Z
status: passed
score: 19/19 must-haves verified
behavior_unverified: 0
overrides_applied: 0
goal: "A reader who jumps inside an article and a reader who opens a material from a section both keep their bearings."
requirements:
  NAV-01: satisfied
  NAV-02: satisfied
requirement_ids_in_plans: [NAV-01, NAV-02]
requirement_ids_in_requirements_md: [NAV-01, NAV-02]
orphaned_requirements: []
unmapped_requirement_ids: []
gaps: []
accepted_residuals:
  - band: "1280×800"
    residual: "gap ≈7px (offset 80px vs measured header 73px)"
    verdict: "Not a violation — inside the declared [1, 32] band and above the live header height."
  - band: "640–999px"
    residual: "negative gap (−43…−19px): offset is 80px while the live header is 99–123px tall"
    verdict: "Accepted residual of locked decision D-02. It does not fail criteria 1–2 as proven (short/deep section at the tested 1280×800 proof viewport, mobile claims at 390/639), but a viewport-independent reading of NAV-01 ('no heading hidden under the header') is NOT met in this band. Recorded as a WARNING for the deferred chrome redesign (second breakpoint); no must-have declares this band, so it is not a blocking gap."
---

# Phase 26: Section context — anchor scrolling and header active state — Verification Report

**Phase Goal:** A reader who jumps inside an article and a reader who opens a material from a section both keep their bearings.
**Verified:** 2026-10-22T06:06:00Z
**Status:** passed
**Re-verification:** No — initial verification (no previous `26-VERIFICATION.md` existed)

## Goal Achievement

### Observable Truths

Every truth below was checked against the working tree and re-proven by running the named test in this verification session; no SUMMARY claim was taken as evidence.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | **Criterion 1 (short section):** after a «Содержание» click the heading sits in `gap = heading.top − header.bottom ∈ [1, 32]` and fully inside the viewport, with the header height measured live (never 64) and the first section proven shorter than one viewport | ✓ VERIFIED | `tests/web-app.spec.js` C-01 (`pad ∈ [header+1, header+32]`, measured header 73, pad 80) and C-02 (reachability gate, second-heading distance < innerHeight, gap ≤ 32, `bottom ≤ innerHeight`). Ran: 18/18 NAV specs passed. |
| 2 | **Criterion 2 (long section):** a deep TOC target is below the fold before the click and lands in the same `[1, 32]` band afterwards, in an article with ≥ 6 headings | ✓ VERIFIED | C-03 asserts `heading.top > innerHeight` pre-click, `links.count() ≥ 6`, `assertReachable`, then gap ≥ 1 / ≤ 32 and `bottom ≤ innerHeight`. Passed. |
| 3 | **Criterion 3 (archive origin):** `/archive → /issues/13` keeps «Архив» lit, and opening a material from there keeps it lit on `/materials/sql-dashboards` | ✓ VERIFIED | C-08 (`aria-current="true"` + `bg-primary-solid` on `/issues/13`, other two dark) and C-09 (same after the material hop, `isLit === true`). Passed. |
| 4 | **Criterion 4 (search origin):** `/knowledge → /materials/rag-systems` lights «База» and not «Архив» | ✓ VERIFIED | C-11 asserts «База» `true` + fill, «Выпуск»/«Архив» `null` + no fill. Passed. |
| 5 | **Criterion 5a (honest degradation):** a direct fresh-context visit to `/materials/:slug` lights nothing | ✓ VERIFIED | C-13: first action is `page.goto`, no `history.replaceState`, no hand-made context; all five shell entries proven `toBeVisible()` before `aria-current === null` and no active fill. Passed. |
| 6 | **Criterion 5b:** `/issues/:number` typed directly lights «Архив» | ✓ VERIFIED | C-14, fresh `goto('/issues/13')`: «Архив» `true` + fill, others null. Passed. |
| 7 | **Criterion 5c:** `/` lights only «Выпуск» | ✓ VERIFIED | C-15 (`page` on «Выпуск» at `/`) plus C-20 (`litCount === 1`, exactly one `aria-current` on `/`). Passed. |
| 8 | Own routes keep `aria-current="page"` on exactly their pill (`/`, `/archive`, `/knowledge`, `/voting`, `/razbory`) | ✓ VERIFIED | C-15 loops all five routes; passed (no regression from the `NavLink → Link` conversion). |
| 9 | Current-issue origin lights «Выпуск» (symmetry with the archive branch) | ✓ VERIFIED | C-10: `/ → /materials/rag-systems` → «Выпуск» `true` + fill, «Архив»/«База» dark. Passed. |
| 10 | The marker survives the second hop through «Связанные материалы» | ✓ VERIFIED | C-12: archive → issue → `sql-dashboards` → related `rag-systems` keeps «Архив» `true`; barrier is the target `h1`, so the stale-DOM false green is closed. Passed. |
| 11 | **One offset mechanism, applied once:** exactly one `scroll-padding-top` in `web/src`, token-derived, in `@layer base`, no `scroll-mt` / `scroll-margin` / `scroll-behavior`, `index.css:117` untouched | ✓ VERIFIED | Static gates 1–5; `node --test tests/unit/test_section_context_gates.js` → 11/11 pass. `rg` over `web/src` finds only `index.css:152`. |
| 12 | Mobile token is a measured `200px` only below 640px; at 640 it is `64px`; the offset clears the live mobile header and the target stays below it and in the viewport at 390 and 639 | ✓ VERIFIED | C-04 / C-05 (three independent claims each, band deliberately not asserted) plus the media-block gate. Passed. |
| 13 | Razbor anchors are covered by the same global rule with **zero** edits to `RazborPage.jsx` (D-05) | ✓ VERIFIED | C-06 band assertion on `/razbory/3`; `git diff --name-only` for the phase contains no `RazborPage.jsx`. Passed. |
| 14 | An unreachable short page is not force-scrolled: `reachable === false`, gap stays > 32px before and after, band not applied | ✓ VERIFIED | C-02b asserts `maxScroll < headingDocTop`, `pre.gap > 32`, `after.gap > 32`, `bottom ≤ innerHeight`. Passed. |
| 15 | The «Админ» prefix pattern still works and the admin route is untouched | ✓ VERIFIED | `AppShell.jsx` `adminActive = pathname.startsWith('/admin/')` unchanged with `aria-current={adminActive ? 'true' : undefined}`; C-16 (both admin paths: «Админ» lit, three sections visible/dark) and the pre-existing WR-02 pin both passed. |
| 16 | The origin marker is a closed list read at exactly one point, blind-forwarded by `MaterialPage`, never persisted | ✓ VERIFIED | Six static gates (one `state?.section`, all three literals actually reach `===` in `AppShell` only, no comparison in `MaterialPage`, no `localStorage`/`sessionStorage`/`document.cookie` in the seven marker files) → 11/11; behaviourally re-proven by C-13. |
| 17 | A heading-less material renders no «Содержание» while the global offset stays live | ✓ VERIFIED | Zero-heading pin: `material-toc` count 0, `details` count 0, zero `[id^="user-content-"]`, `pad > 0` and `pad ≥ measured header + 1`. Passed. |
| 18 | The active pill changes paint only, token-exact, in both themes | ✓ VERIFIED | C-18: identical `min-h-11 rounded-full px-2.5 text-sm`; active `bg-primary-solid text-on-solid` = `rgb(124,58,237)` / `rgb(255,255,255)`; idle `text-text-secondary hover:bg-bg-surface`; no `bg-primary` substring in either state; light theme re-read. Passed. |
| 19 | **Locked scope facts honoured:** no breadcrumb / «вы здесь», no route-hierarchy change, no new navigation surface, one scroll mechanism, `adminActive` intact | ✓ VERIFIED | `rg -i "breadcrumb|хлебные крошки|вы здесь|you are here" web/src` → no matches. Phase diff (`a40ace2~1..a6ce121`) touches only the nine expected source/test files — `App.jsx`, `RazborPage.jsx` and every other route/component absent. `AppShell` still renders the same five entries plus «Админ» (no new link). |

**Score:** 19/19 truths verified (0 present, behavior-unverified)

### Accepted Residuals — explicit verdict (required by the orchestrator)

| Band | Residual | Verdict |
|---|---|---|
| 1280×800 | ≈7px gap below the heading (offset `80px`, live header `73px`) | **No violation.** It is a positive gap inside the declared `[1, 32]` band and above the measured header height — exactly what criteria 1–2 ask for. |
| 640–999px | **negative** gap (−43…−19px: offset `80px`, live header 99–123px) | **WARNING, accepted, non-blocking.** Criteria 1–2 are proven at the tested proof viewport (1280×800, short and deep sections) and the mobile claims are scoped to 390/639 without the band, so no must-have or roadmap proof step fails. However, read viewport-independently, NAV-01's promise ("no heading hidden under the header") is **not** met for a reader at 640–999px: the heading would sit partly under the sticky header. This is an explicit consequence of locked decision D-02 (the `64px` `sm+` token; a second breakpoint is deferred to the chrome redesign), recorded by 26-01 before execution. It must be revisited there — it is not silently ignored. |
| 390 / 639 | ≈19px / ≈93px gaps | **No violation** — outside the band by design (C-04/C-05 declare three claims without an upper bound). |

### Deferred Items

None beyond the 640–999px residual above (there is no later phase in this milestone that claims the second header breakpoint; the chrome redesign is listed as Deferred).

### Required Artifacts

| Artifact | Expected | Status | Details |
|---|---|---|---|
| `web/src/index.css` | `scroll-padding-top: calc(var(--header-height) + 1rem)` in `@layer base :root` + one `@media (max-width: 639.98px)` token override | ✓ VERIFIED | Lines 152 and 159-163; `--header-height: 64px;` at line 117 unchanged; gate counts exactly one of each |
| `web/src/components/AppShell.jsx` | derivation block + three `aria-current`-computing `<Link>`s | ✓ VERIFIED | `section = state?.section`, `home/archive/baseLit`, `current(ownRoute)`; `linkClass` and `adminActive` byte-identical in behaviour |
| `web/src/components/IssueToc.jsx` | required `section` prop, `state={{ section }}` | ✓ VERIFIED | Destructured, JSDoc union `'archive' \| 'issue'`, no default; used by both issue branches |
| `web/src/components/MaterialListRow.jsx` | required `section` prop, `state={{ section }}` | ✓ VERIFIED | Union `'archive' \| 'base' \| 'issue'`, no default |
| `web/src/pages/ArchivePage.jsx` | `state={{ section: 'archive' }}` on the issue card | ✓ VERIFIED | Line 73, exactly one occurrence (gate 6) |
| `web/src/pages/IssuePage.jsx` | `section={isCurrent ? 'issue' : 'archive'}` | ✓ VERIFIED | Line 188 |
| `web/src/pages/KnowledgePage.jsx` | `section="base"` at the only `MaterialListRow` call site | ✓ VERIFIED | Line 387, exactly one occurrence |
| `web/src/pages/MaterialPage.jsx` | `useLocation` + `originSection` + conditional `state` on related links | ✓ VERIFIED | Lines 65-66, 182, 270; zero literal comparisons (gate 4) |
| `web/src/data/mock.js` | lengthened `rag-systems` / razbor 3; `related` on `sql-dashboards` | ✓ VERIFIED | C-03 sees ≥ 6 headings and a below-fold target; C-06 reachable; C-12 related section visible |
| `tests/web-app.spec.js` | four anchor helpers + 18 NAV criteria | ✓ VERIFIED | `anchorIdOf`, `anchorGate`, `gapAfterScroll`, `assertReachable`; 7 anchor + 11 pill/state tests |
| `tests/admin.spec.js` | C-16 inside the existing describe | ✓ VERIFIED | Line 419, before the closing brace at 453; reuses `shellNav`/`shellAdminLink` |
| `tests/unit/test_section_context_gates.js` | 5 NAV-01 gates + 6 C-17 gates | ✓ VERIFIED | 11/11 green on raw file text (never `parseRules`) |

### Key Link Verification

| From | To | Via | Status | Details |
|---|---|---|---|---|
| `ArchivePage.jsx` | `AppShell.jsx` | `state={{ section: 'archive' }}` → `useLocation().state` → `archiveLit` | ✓ WIRED | C-08/C-09/C-12 passed |
| `IssuePage.jsx` | `IssueToc.jsx` | required `section` prop chosen by `isCurrent` | ✓ WIRED | C-09 / C-10 passed |
| `IssueToc` / `MaterialListRow` | `AppShell.jsx` | `<Link state={{ section }}>` → `history.state.usr.section` | ✓ WIRED | grep + gate 6 + C-09/C-10/C-11 |
| `KnowledgePage.jsx` | `MaterialListRow.jsx` | `section="base"` literal at the producer | ✓ WIRED | C-11 passed |
| `MaterialPage.jsx` | `AppShell.jsx` | `originState?.section` blind-forwarded to related links | ✓ WIRED | C-12 passed; gate 4 forbids a comparison here |
| `tests/web-app.spec.js` | `web/src/index.css` | `getComputedStyle(document.documentElement).scrollPaddingTop` | ✓ WIRED | C-01 / zero-heading read live 80px; C-04/C-05 read 216 |
| `tests/unit/test_section_context_gates.js` | source files | raw `readFileSync` + regex | ✓ WIRED | 11/11, including mutation-hardened anti-vacuum gate 2 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|---|---|---|---|---|
| `AppShell.jsx` | `section` → `homeLit` / `archiveLit` / `baseLit` | `history.state.usr.section` written by four real producers | Yes — literal written at each hop, verified by C-08…C-12 | ✓ FLOWING |
| `AppShell.jsx` | `archiveLit` also from `pathname.startsWith('/issues/')` | live router pathname | Yes — C-14 fresh `goto` | ✓ FLOWING |
| `IssueToc` / `MaterialListRow` | `section` prop | page-level literal (`ArchivePage`, `KnowledgePage`) or `isCurrent` | Yes — no default, no hardcode inside the reusable row | ✓ FLOWING |
| heading geometry | `heading.getBoundingClientRect()` | real DOM ids from `rehype-slug` (`user-content-…`) | Yes — rects measured after `document.fonts.ready`, never literals | ✓ FLOWING |

### Behavioral Spot-Checks

Port 5174 was confirmed free before every run (`Get-NetTCPConnection -LocalPort 5174 -State Listen` → no records).

| Behavior | Command | Result | Status |
|---|---|---|---|
| NAV-01 + NAV-02 behaviour (18 criteria) | `npx playwright test tests/web-app.spec.js --project=web -g "anchor offset\|section pills\|section state"` | **18 passed** (40.4s) | ✓ PASS |
| Static gates C-19 + C-17 (11 gates) | `node --test tests/unit/test_section_context_gates.js` | **11 pass / 0 fail** | ✓ PASS |
| Admin untouched | `npx playwright test tests/admin.spec.js --project=web -g "C-16"` | **1 passed** | ✓ PASS |
| «Админ» prefix regression | `npx playwright test tests/admin.spec.js --project=web -g "WR-02"` | **1 passed** | ✓ PASS |
| Razbor pins (`chronology-item` count 4 etc.) | `npx playwright test tests/razbory.spec.js --project=web` | **4 passed** | ✓ PASS |

Full-suite evidence from the orchestrator's post-merge gate on this same tree (`npm run build` OK, `npm run test:js` 108/108, `npm run test:web` 180/180) is consistent with the targeted runs above; the targeted runs are the authoritative evidence recorded here.

### Probe Execution

No probes are declared or implied by this phase (`rg "probe-"` over the three PLAN/SUMMARY files → none). Step 7c: **N/A**.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|---|---|---|---|---|
| NAV-01 | 26-01, 26-03 | Follow a «Содержание» link → target fully visible below the sticky header with breathing room, no hidden heading, no over-scroll | ✓ SATISFIED | C-01/C-02/C-03/C-02b/C-04/C-05/C-06 + one-mechanism gate; 18/18 + 11/11 passed. Residual: 640–999px band (see Accepted Residuals). |
| NAV-02 | 26-02, 26-03 | «Архив» stays lit on an archived issue and on a material opened from the archive; «База» for search-opened material; direct URL lights no false section | ✓ SATISFIED | C-08…C-15, C-18, C-20, C-13, C-16, C-17 gates; all passed. |

Every requirement ID declared in PLAN frontmatter (`NAV-01` in 26-01/26-03, `NAV-02` in 26-02/26-03) exists in `REQUIREMENTS.md` under Phase 26 and is marked `Complete`; there are **no orphaned and no unmapped** requirement IDs.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| — | — | No `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` / placeholder text in any phase-modified file | — | Debt-marker gate clean |
| — | — | No `toHaveClass(/bg-primary/)`, no `waitForURL` as the sole barrier, no `waitForTimeout` in phase-added specs (token-exact class splits and render barriers instead) | — | Test-integrity gate clean |
| `tests/admin.spec.js` | 692 | Pre-existing `waitForTimeout(500)` | ℹ️ Info | Outside the phase diff (`5fbb254..a6ce121` only adds lines 419-453); not introduced or weakened by Phase 26 |

### Locked Scope Confirmation

- **No breadcrumb component, no route-hierarchy change, no new navigation surface** — grep for breadcrumb/«вы здесь»/«you are here» returns nothing; `web/src/App.jsx` is absent from the phase diff; the shell still renders the same five entries plus «Админ».
- **Origin rides navigation state only** — `state={{ section }}` at every producer; `AppShell` is the single read point; zero `localStorage` / `sessionStorage` / `document.cookie` in the seven marker files; `MaterialPage` blind-forwards (gate 4).
- **One scroll-offset mechanism** — exactly one `scroll-padding-top` in `web/src`, expressed from the token, in `@layer base`; zero `scroll-mt` / `scroll-margin` / `scroll-behavior`.
- **«Админ» prefix pattern intact** — `adminActive = pathname.startsWith('/admin/')` unchanged; C-16 and WR-02 green.

## Gaps Summary

No blocking gaps. Both NAV-01 and NAV-02 are implemented, wired and behaviourally proven on the current working tree. The only open item is the documented 640–999px header-token residual, accepted by locked decision D-02 and recorded above as a WARNING for the deferred chrome redesign — it does not fail the criteria as proven, and it is not a silent omission.

---

_Verified: 2026-10-22T06:06:00Z_
_Verifier: Claude (gsd-verifier)_
