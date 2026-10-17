---
phase: 22-admin-nav-grouping
verified: 2026-10-17T12:56:00Z
status: passed
score: 18/18 must-haves verified
covered_files:
  - .planning/phases/22-admin-nav-grouping/22-01-PLAN.md
  - .planning/phases/22-admin-nav-grouping/22-01-SUMMARY.md
  - .planning/phases/22-admin-nav-grouping/22-02-PLAN.md
  - .planning/phases/22-admin-nav-grouping/22-02-SUMMARY.md
  - .planning/phases/22-admin-nav-grouping/22-03-PLAN.md
  - .planning/phases/22-admin-nav-grouping/22-03-SUMMARY.md
  - tests/admin.spec.js
  - web/src/App.jsx
  - web/src/components/AdminLayout.jsx
  - web/src/components/AppShell.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
covered_digest: "v2:sha256:8e6dc8f16eebb4e2c7afcd31dfcbbce221776eeed26457e44ce907604ec5b60c"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: 11/14
  gaps_closed:
    - "At sm+ the two tab labels stay on one row without horizontal page scroll at 1280px and at the sm edge (~640px)"
    - "Below sm the select remains fully usable within the content column without horizontal overflow"
    - "Single «Админ» pill remains visible in the wrapping shell nav when the header wraps on narrow widths"
    - "WR-01: an already-active section tab click with a dirty editor opened a false leave dialog"
    - "WR-02 / IN-04: the shell «Админ» pill had no aria-current off /admin/digest and carried a dead /admin equality branch"
    - "IN-01: admin surfaces had no level-1 heading"
    - "IN-03: the employee nav assertion ran on a route where AdminLayout never mounts"
  gaps_remaining: []
  regressions: []
prohibitions:
  - statement: "MUST NOT add a dirty-nav carve-out that lets a genuine tab or select leave skip UnsavedChangesDialog (D-13; Phase 19 D-04)."
    tier: judgment
    verdict: held
    evidence: "AdminLayout.handleSectionTabClick calls preventDefault ONLY when section === target; tests/admin.spec.js:236-249 proves a genuine tab leave in the same state still opens the unchanged dialog and «Остаться» keeps URL + draft; useUnsavedChangesGuard.js and UnsavedChangesDialog.jsx are untouched in 4214910..HEAD."
  - statement: "MUST NOT restore a VISIBLE page title or H1 on the admin pages (D-06) — the new heading must stay sr-only."
    tier: judgment
    verdict: held
    evidence: "AdminLayout.jsx:49 is the only h1 under AdminLayout and carries className=\"sr-only\"; tests/admin.spec.js:262-283 asserts the class AND a <=1px box on both surfaces, so dropping sr-only turns the suite red; no h1 exists in AdminDigestPage.jsx / AdminPipelineConfigPage.jsx."
  - statement: "MUST NOT mark the section switch with ARIA tablist/tab/tabpanel roles (D-12)."
    tier: judgment
    verdict: held
    evidence: "rg 'role=\"tab|tablist|tabpanel' over web/src/components -> 0 matches; the switch remains nav aria-label + NavLink / native select."
  - statement: "MUST NOT set aria-current=\"page\" on the shell «Админ» pill (WR-02)."
    tier: judgment
    verdict: held
    evidence: "AppShell.jsx:98 uses the literal 'true' when adminActive; tests/admin.spec.js:290-313 pins 'true' on digest/pipeline/materials and absence on /."
  - statement: "MUST NOT weaken the employee role gate or render admin data for an employee (ADMIN-01 / D-77)."
    tier: judgment
    verdict: held
    evidence: "tests/admin.spec.js:1769-1802 deep-links an employee into /admin/digest and asserts forbidden-page + «Недостаточно прав», zero admin-digest-page/admin-shortlist/admin-shortlist-row, zero shell «Админ»; backend auth untouched."
  - statement: "MUST NOT reintroduce a second AppShell top-level item labelled «Пайплайн» (ADUX-12)."
    tier: judgment
    verdict: held
    evidence: "rg 'Пайплайн' over AppShell.jsx and App.jsx -> 0 matches; the label exists only inside AdminLayout.jsx (tab, option, sr-only h1)."
  - statement: "MUST NOT introduce an /admin index route or redirect (D-04)."
    tier: judgment
    verdict: held
    evidence: "App.jsx:38-45 — pathless AdminLayout with children admin/digest and admin/pipeline only; no path 'admin' and no index child; the catch-all still redirects unknown paths to /."
  - statement: "MUST NOT wrap admin/materials/:id under AdminLayout so the preview gains the tab-bar (D-03, D-11)."
    tier: judgment
    verdict: held
    evidence: "App.jsx:43 keeps admin/materials/:id as a sibling; tests/admin.spec.js:189-198 asserts zero admin-section-nav/select on the preview while the shell pill stays bg-accent."
  - statement: "MUST NOT rewrite Phase 19 modal copy or action labels (D-15)."
    tier: judgment
    verdict: held
    evidence: "tests/admin.spec.js:242-244 compares the exact body «Есть несохранённые изменения. Уйти без сохранения?» and reuses unsaved-changes-stay/-leave; neither UnsavedChangesDialog.jsx nor the copy changed in the phase diff."
---

# Phase 22: Admin nav grouping Verification Report

**Phase Goal:** The pipeline config surface is reached from the admin area rather than a second top-level nav item — one «Админ» entry → `/admin/digest`, plus an in-page tab-bar «Дайджест | Пайплайн»; `/admin/pipeline` unchanged, no new route (ADUX-12).
**Verified:** 2026-10-17T12:56:00Z
**Status:** passed
**Re-verification:** Yes — after gap-closure plan 22-03 (previous report: `human_needed`, 11/14)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Exactly one AppShell «Админ» entry, always → `/admin/digest`; primary nav landmark has zero «Пайплайн» links (ROADMAP SC1) | ✓ VERIFIED | `AppShell.jsx:92-104` is the sole admin-gated link; `rg "Пайплайн"` over `AppShell.jsx`/`App.jsx` → 0; tests `:67`, `:1751-1768` pass |
| 2 | In-page «Разделы админки» switch with ordered «Дайджест» → «Пайплайн» on both admin routes (underline nav at sm+, native select below), URLs unchanged, no `/admin` index (ROADMAP SC2) | ✓ VERIFIED | `AdminLayout.jsx:52-85`; `App.jsx:38-45` pathless parent, no index; tests `:139-169`, `:201-217` pass |
| 3 | 16-UI-SPEC A-2 no longer mandates a second shell «Пайплайн» and «no second navigation bar» still holds (ROADMAP SC3) | ✓ VERIFIED | `16-UI-SPEC.md:19` supersession banner, `:30` A-2 struck + ADUX-12, `:190-193` Route/nav rewritten with in-page rationale |
| 4 | A failing Playwright test existed before the nav change (ROADMAP SC4, TDD) | ✓ VERIFIED | Commit order: `4b62669 test(22-01)` before `fed7b0b feat(22-01)`; for 22-03 `e4646bc test` before `df3fb17 feat` and `1be70f3 test` before `e4046a7 feat`; both RED runs recorded in SUMMARY with assertion-level failures, no connection errors |
| 5 | Shell «Админ» is visually active on digest, pipeline and materials preview | ✓ VERIFIED | `AppShell.jsx:37,98-99`; tests `:170-198`, `:290-313` assert `bg-accent` on all three paths |
| 6 | Page-level H1s «Shortlist дайджеста» / «Конфиг пайплайна» and duplicate eyebrow remain removed | ✓ VERIFIED | `rg "<h1"` over `web/src/pages` → no admin-page heading; tests `:286-288`, `:206`, `:1097` pass |
| 7 | Adjacency: shell landmark and section landmark never merge; «Пайплайн» lives only in the section switch | ✓ VERIFIED | `AppShell.jsx` has no «Пайплайн»; test `:164-167` scopes the query to `nav[aria-label="Основная навигация"]` and expects 0 |
| 8 | Cardinality: the switch always has exactly two destinations | ✓ VERIFIED | Two literal `NavLink`s (`AdminLayout.jsx:57-77`) and two literal `<option>`s (`:82-83`); test `:147-150` expects 2 and exact labels |
| 9 | Ordering: «Дайджест» precedes «Пайплайн» in both nav and option list | ✓ VERIFIED | Declaration order in `AdminLayout.jsx`; test `:150-151` checks nth(0)/nth(1); select path exercised by `:201-217` |
| 10 | Dirty YAML → in-page «Дайджест» opens the unchanged Phase 19 dialog; «Остаться» keeps URL + draft, «Уйти» lands on digest | ✓ VERIFIED | `AdminPipelineConfigPage.jsx:107` guard untouched; test `:1597-1634` passes with exact copy and testids |
| 11 | Below-sm select leave uses SPA `navigate()`, guard still fires, no `document.location` | ✓ VERIFIED | `AdminLayout.jsx:81`; test `:1636-1665` passes (dialog, stay keeps draft, leave reaches digest) |
| 12 | **Former backstop 1** — at 1280px and exactly the 640px `sm` edge, on both routes, both tabs are on one row with no horizontal page/content-column scroll | ✓ VERIFIED (explicit automated evidence) | `tests/admin.spec.js:316-347`: `Math.abs(digestBox.y - pipelineBox.y) <= 1`, `digestBox.x + width <= pipelineBox.x`, `documentElement.scrollWidth <= clientWidth` AND `main.scrollWidth <= clientWidth`; 639px negative control (`:341-346`) returns a hidden nav + visible select, proving the probe is breakpoint-sensitive. Case executed in this session (10/10 selected `Admin nav grouping` tests passed) |
| 13 | **Former backstop 2** — below sm the select stays inside the content column with no horizontal overflow | ✓ VERIFIED (explicit automated evidence) | `tests/admin.spec.js:349-372`: at 480px and 400px the select box starts inside `main` (+16px padding, 1px tolerance), ends before `main` right edge and inside the viewport, width ≤ column width, and `documentElement` does not overflow; option→URL switching is independently pinned by `:201-217`. |
| 14 | **Former backstop 3** — single «Админ» pill stays visible when the shell nav wraps at narrow width | ✓ VERIFIED (explicit automated evidence) | `tests/admin.spec.js:374-401`: at 480px it first proves the wrap by measuring `navBox.height > one pill's height`, then asserts the single shell «Админ» link is visible with `x >= 0` and `x + width <= 480`, and that the section switch is the select only (nav hidden). |
| 15 | WR-01 — clicking the already-active section tab with a dirty editor opens no dialog, keeps URL + draft, while a genuine tab leave still prompts | ✓ VERIFIED | `AdminLayout.jsx:35-37,60,69`; test `:219-250` observed RED before the fix (dialog count 1) and is green now; the same test re-asserts the D-13 no-carve-out path |
| 16 | WR-02 / IN-04 — shell «Админ» exposes `aria-current="true"` on every `/admin/*`, none on `/`, keeps href and active class; no dead `/admin` equality branch | ✓ VERIFIED | `AppShell.jsx:37` prefix-only; `:92-104` `Link` + manual `aria-current`; test `:290-313` asserts `"true"` on digest/pipeline/preview, null on `/`, href and `bg-accent` everywhere |
| 17 | IN-01 — exactly one visually hidden `h1` per admin surface («Дайджест» / «Пайплайн»), no visible title restored | ✓ VERIFIED | `AdminLayout.jsx:49`; `.sr-only` utility at `index.css:21-31`; test `:252-288` asserts count 1, `sr-only` class, and ≤1px width/height on both surfaces |
| 18 | IN-03a — employee deep-linking `/admin/digest` gets layout chrome + ForbiddenPage, no admin data surface, no shell «Админ», exactly two level-1 headings | ✓ VERIFIED | Test `:1769-1802` (replaces the vacuous `/`-route assertion) asserts `forbidden-page` + «Недостаточно прав», zero `admin-digest-page`/`admin-shortlist`/`admin-shortlist-row`, zero shell «Админ», and two level-1 headings (sr-only section name + visible state name) |

**Score:** 18/18 truths verified (0 present, behavior-unverified).
The specless-probe truths from 22-01 (adjacency / cardinality / ordering) are not re-derived; they remain covered by rows 7–9 and by tests `:139-169`, as plan 22-03 required.

### Deferred Items

None. IN-02 (`waitForTimeout` at `tests/admin.spec.js:639`) is a review **Info** finding, not a must-have truth; it is explicitly deferred with a follow-up recipe in `22-03-PLAN.md` and is listed under Anti-Patterns below.

### Advisory (New Scope, Unevidenced)

None. This re-verification produced no new-scope Step 7 blocker.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/components/AdminLayout.jsx` | same-section click suppression + one `sr-only` h1 + section nav/select/Outlet | ✓ VERIFIED | `verify.artifacts` 3/3 passed; `handleSectionTabClick` closes over per-render `section`; h1 at `:49`; select still `navigate()` |
| `web/src/components/AppShell.jsx` | admin pill = `Link` + manual `aria-current`; prefix-only active matching | ✓ VERIFIED | `:37` has no `pathname === '/admin'`; `aria-current={adminActive ? 'true' : undefined}`; one «Админ» link |
| `tests/admin.spec.js` | six net-new cases + one in-place rewrite + `layoutMetrics` helper | ✓ VERIFIED | 72 tests; helper `:122-135`; new cases `:219`, `:252`, `:290`, `:316`, `:349`, `:374`; rewritten employee case `:1769`; 0 skipped |
| `web/src/App.jsx` | pathless `AdminLayout` for digest+pipeline; materials sibling; no admin index | ✓ VERIFIED | `:38-45`; unchanged by 22-03 |
| `web/src/pages/AdminDigestPage.jsx` | no page H1 / duplicate eyebrow | ✓ VERIFIED | No `<h1>`; unchanged by 22-03 |
| `web/src/pages/AdminPipelineConfigPage.jsx` | no H1/eyebrow; hint + guard untouched | ✓ VERIFIED | No `<h1>`; `useUnsavedChangesGuard` wiring present; not in the 22-03 diff |
| `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` | A-2 + Route/nav superseded with 22-UI-SPEC pointer | ✓ VERIFIED | `:19`, `:30`, `:140`, `:190-193` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/admin.spec.js` | `web/src/components/AdminLayout.jsx` | active-tab click asserts zero dialogs — green only when `preventDefault` fires first | WIRED | `verify.key-links` 4/4 verified |
| `tests/admin.spec.js` | `web/src/components/AppShell.jsx` | `aria-current` read from the shell landmark link | WIRED | landmark-scoped `shellAdminLink` |
| `tests/admin.spec.js` | `web/src/index.css` | `.sr-only` keeps the heading in the a11y tree while hidden | WIRED | `index.css:21-31` |
| `web/src/components/AdminLayout.jsx` | `web/src/App.jsx` | pathless parent + `<Outlet />` covers every child branch | WIRED | `App.jsx:40-43`, `AdminLayout.jsx:88-90` |
| `web/src/App.jsx` | `web/src/components/AdminLayout.jsx` | `element: <AdminLayout />` with digest+pipeline children | WIRED | import `:3`, element `:40` |
| `web/src/components/AppShell.jsx` | `/admin/digest` | sole admin-gated `Link to="/admin/digest"` | WIRED | `:93`; tests `:67`, `:1545`-area tripwire |
| `web/src/pages/AdminPipelineConfigPage.jsx` | `useUnsavedChangesGuard` | `useUnsavedChangesGuard(dirty)` + dialog | WIRED | `:107`, `:331`; behavior pinned by `:1597`, `:1636` |
| `16-UI-SPEC.md` | `22-UI-SPEC.md` | superseded-by pointer | WIRED | `16-UI-SPEC.md:19`, `:30`, `:190` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `AdminLayout.jsx` | `section` | `useLocation().pathname` (real router state) | Yes — drives select `value`, active tab, sr-only heading | ✓ FLOWING |
| `AppShell.jsx` | `adminActive` | `useLocation().pathname` | Yes — drives `aria-current` and `bg-accent` | ✓ FLOWING |
| `AppShell.jsx` | `appRole` | `getAccessToken()` → `fetchMe()` (existing session flow) | Yes — gates the single admin entry | ✓ FLOWING |
| `AdminLayout.jsx` | destinations (2 URLs) | literal route whitelist per contract (D-10/D-17) | N/A — static by requirement, not a stub | ✓ VERIFIED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Admin nav-grouping contract, including all three former backstops | `npx playwright test --project=web tests/admin.spec.js -g "Admin nav grouping"` | `10 passed (29.7s)` — exactly 10 cases selected and executed | ✓ PASS |
| Full admin file | `npx playwright test --project=web tests/admin.spec.js` | `72 passed (3.1m)`, 0 failed, 0 skipped | ✓ PASS |
| First full-file attempt (transparency) | same command, earlier in the session | `37 passed / 35 failed`, failures begin mid-file, no listener on 5174 afterwards — the documented Vite mid-run death (`STATE.md`), not a code regression; the clean targeted + full re-runs above supersede it | ⚠️ INFRA (documented) |

**Anti-vacuity checks on the former backstops**
- The `-g` filter was not vacuous: the targeted run reported `[9/10]` and `[10/10]` for GAP-BACKSTOP-2 and GAP-BACKSTOP-3, i.e. each case ran exactly once.
- The row probe is not self-satisfying: it asserts viewport-relative top equality, left-to-right order, and BOTH page-level and content-column `scrollWidth <= clientWidth`; any wrap or overflow breaks it, and the 639px negative control shows the same probe distinguishes breakpoints.
- The select probe measures the real box against the `main` content column and the viewport (not a child of the select), plus document overflow; the existing option→URL navigation at 480px covers "usable" functionally.
- The shell-pill probe first measures that the nav actually wrapped (`navBox.height > pillHeight`) instead of assuming it, then bounds the single admin link to the viewport.

### Probe Execution

Not applicable: no PLAN/SUMMARY in the phase declares probe scripts, and no `scripts/*/tests/probe-*.sh` participates in this phase (SPA chrome + Playwright + docs).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADUX-12 | 22-01, 22-02, 22-03 | One «Админ» entry (→ `/admin/digest`) + in-page tab-bar «Дайджест \| Пайплайн»; `/admin/pipeline` unchanged; no new route | ✓ SATISFIED | Truths #1–#2, #5–#17; `REQUIREMENTS.md:44` description matches; `:109` marks Phase 22 Complete |

No orphaned requirements: `REQUIREMENTS.md` maps only ADUX-12 to Phase 22, and it is declared in all three PLAN frontmatters.

### Decision Coverage

All 19 trackable `22-CONTEXT.md` decisions are honored by shipped artifacts (`check.decision-coverage-verify` → `{total: 19, honored: 19, not_honored: []}`).

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/admin.spec.js` | ADUX-12 | 72 | 0 | 0 | Behavioral (geometry, value, multi-step flow) | PASS |

Disabled tests on requirements: 0. Circular fixture generation: 0. The backstop cases assert measured geometry, not merely element presence.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/admin.spec.js` | 639 | `waitForTimeout(500)` (IN-02) | ℹ️ Info | Pre-existing, explicitly deferred in `22-03-PLAN.md` with a follow-up recipe; no new timeout was added (0 added in the 22-03 diff). Does not affect the phase goal |
| `22-REVIEW-DISPOSITION.md` | all rows | Six findings still recorded `open` | ℹ️ Info | Bookkeeping lag only: WR-01, WR-02, IN-01, IN-03, IN-04 are demonstrably landed in code/tests; only IN-02 remains intentionally deferred. Ledger should be updated to `fixed`/`deferred` by the orchestrator |
| `22-UAT.md` | tests 1–3 | Three items still `pending` | ℹ️ Info | These were the three human backstops now covered by deterministic Playwright geometry; the UAT items can be retired rather than retested |

No `TBD`/`FIXME`/`XXX` markers exist in any phase-modified file. No `TODO`/`HACK`/`PLACEHOLDER`/placeholder copy, no empty render stubs, no hardcoded-empty props in the phase's chrome.

### Human Verification Required

None. All three former `verification: backstop` truths now have explicit automated evidence that exercises their invariants and can fail when they break (rows #12–#14). Remaining aesthetic judgment (underline weight/colour) is already a signed-off UI-SPEC contract and is not a must-have truth.

### Gaps Summary

No gaps. The phase goal is achieved in code: a single shell «Админ» entry always targets `/admin/digest`, the in-page «Дайджест | Пайплайн» switch reaches the unchanged `/admin/pipeline` route, `admin/materials/:id` stays a sibling, and no `/admin` index exists. ADUX-12 is satisfied; all four ROADMAP success criteria are evidenced; all nine prohibitions held. Plan 22-03 converted the three former human-only backstops into falsifiable Playwright geometry assertions (including the 640px `sm` edge and a 639px negative control), retired WR-01/WR-02/IN-01/IN-03/IN-04, and left the Phase 19 guard contract provably intact. IN-02 remains the only carry-over review finding and is explicitly deferred with a concrete fix recipe.

---

_Verified: 2026-10-17T12:56:00Z_
_Verifier: Claude (gsd-verifier)_
