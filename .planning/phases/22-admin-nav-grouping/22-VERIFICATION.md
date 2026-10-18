---
phase: 22-admin-nav-grouping
verified: 2026-10-18T07:35:00Z
status: passed
score: 18/18 must-haves verified
covered_files:
  - .planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md
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
covered_digest: "v2:sha256:d35ee6e3e88dc520b2a11d01f3efe625efd636e7f010cf38924c3cb7279cd3f6"
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: passed
  previous_score: 18/18
  reason: "Stale covered_digest refresh (#4682) — Phase 23 later modified covered files (tests/admin.spec.js, AdminPipelineConfigPage.jsx); must-haves re-checked against current codebase; plans not re-executed"
  gaps_closed: []
  gaps_remaining: []
  regressions: []
prohibitions:
  - statement: "MUST NOT add a dirty-nav carve-out that lets a genuine tab or select leave skip UnsavedChangesDialog (D-13; Phase 19 D-04)."
    tier: judgment
    verdict: held
    evidence: "AdminLayout.handleSectionTabClick calls preventDefault ONLY when section === target; tests/admin.spec.js:219-249 (WR-01) and :1597/:1636 (dirty→tab / select leave) pass on current tree; useUnsavedChangesGuard still wired in AdminPipelineConfigPage.jsx:114."
  - statement: "MUST NOT restore a VISIBLE page title or H1 on the admin pages (D-06) — the new heading must stay sr-only."
    tier: judgment
    verdict: held
    evidence: "AdminLayout.jsx:49 is the only h1 under AdminLayout and carries className=\"sr-only\"; rg '<h1' over AdminDigestPage/AdminPipelineConfigPage → 0; tests/admin.spec.js:252-288 pass."
  - statement: "MUST NOT mark the section switch with ARIA tablist/tab/tabpanel roles (D-12)."
    tier: judgment
    verdict: held
    evidence: "rg 'role=\"tab|tablist|tabpanel' over web/src/components → 0 matches; switch remains nav aria-label + NavLink / native select."
  - statement: "MUST NOT set aria-current=\"page\" on the shell «Админ» pill (WR-02)."
    tier: judgment
    verdict: held
    evidence: "AppShell.jsx:98 uses the literal 'true' when adminActive; tests/admin.spec.js:290-313 pass."
  - statement: "MUST NOT weaken the employee role gate or render admin data for an employee (ADMIN-01 / D-77)."
    tier: judgment
    verdict: held
    evidence: "tests/admin.spec.js:1769-1802 deep-links employee into /admin/digest — forbidden-page + «Недостаточно прав», zero admin data surfaces, zero shell «Админ»; passed this session."
  - statement: "MUST NOT reintroduce a second AppShell top-level item labelled «Пайплайн» (ADUX-12)."
    tier: judgment
    verdict: held
    evidence: "rg 'Пайплайн' over AppShell.jsx and App.jsx → 0; label exists only inside AdminLayout.jsx (tab, option, sr-only h1)."
  - statement: "MUST NOT introduce an /admin index route or redirect (D-04)."
    tier: judgment
    verdict: held
    evidence: "App.jsx:38-45 — pathless AdminLayout with children admin/digest and admin/pipeline only; no path 'admin' and no index child; catch-all still redirects unknown paths to /."
  - statement: "MUST NOT wrap admin/materials/:id under AdminLayout so the preview gains the tab-bar (D-03, D-11)."
    tier: judgment
    verdict: held
    evidence: "App.jsx:47 keeps admin/materials/:id as a sibling; tests/admin.spec.js:189-198 assert zero admin-section-nav/select on preview while shell pill stays bg-accent."
  - statement: "MUST NOT rewrite Phase 19 modal copy or action labels (D-15)."
    tier: judgment
    verdict: held
    evidence: "tests/admin.spec.js:241-243 and :1613 compare exact body «Есть несохранённые изменения. Уйти без сохранения?»; both green this session."
---

# Phase 22: Admin nav grouping Verification Report

**Phase Goal:** The pipeline config surface is reached from the admin area rather than a second top-level nav item — one «Админ» entry → `/admin/digest`, plus an in-page tab-bar «Дайджест | Пайплайн»; `/admin/pipeline` unchanged, no new route (ADUX-12).
**Verified:** 2026-10-18T07:35:00Z
**Status:** passed
**Re-verification:** Yes — stale `covered_digest` refresh after Phase 23 modified covered files (previous report: `passed`, 18/18, digest `8e6dc8f1…`)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Exactly one AppShell «Админ» entry, always → `/admin/digest`; primary nav landmark has zero «Пайплайн» links (ROADMAP SC1) | ✓ VERIFIED | `AppShell.jsx:91-103` sole admin-gated link; `rg "Пайплайн"` over `AppShell.jsx`/`App.jsx` → 0; Playwright `:139-168` passed this session |
| 2 | In-page «Разделы админки» switch with ordered «Дайджест» → «Пайплайн» on both admin routes (underline nav at sm+, native select below), URLs unchanged, no `/admin` index (ROADMAP SC2) | ✓ VERIFIED | `AdminLayout.jsx:51-84`; `App.jsx:38-45` pathless parent, no index; tests `:139-217` passed |
| 3 | 16-UI-SPEC A-2 no longer mandates a second shell «Пайплайн» and «no second navigation bar» still holds (ROADMAP SC3) | ✓ VERIFIED | `16-UI-SPEC.md:19` supersession banner, `:30` A-2 struck + ADUX-12, `:190-193` Route/nav rewritten with in-page rationale |
| 4 | A failing Playwright test existed before the nav change (ROADMAP SC4, TDD) | ✓ VERIFIED | Commit order preserved in history: `4b62669 test(22-01)` before `fed7b0b feat(22-01)`; for 22-03 `e4646bc`/`1be70f3` test before feat; RED runs recorded in SUMMARYs |
| 5 | Shell «Админ» is visually active on digest, pipeline and materials preview | ✓ VERIFIED | `AppShell.jsx:38,98-99`; tests `:170-198`, `:290-313` passed this session |
| 6 | Page-level H1s «Shortlist дайджеста» / «Конфиг пайплайна» and duplicate eyebrow remain removed | ✓ VERIFIED | `rg "<h1"` over admin pages → no page heading; tests `:252-288` passed |
| 7 | Adjacency: shell landmark and section landmark never merge; «Пайплайн» lives only in the section switch | ✓ VERIFIED | `AppShell.jsx` has no «Пайплайн»; test `:164-167` scopes to `nav[aria-label="Основная навигация"]` and expects 0 — green |
| 8 | Cardinality: the switch always has exactly two destinations | ✓ VERIFIED | Two literal `NavLink`s + two `<option>`s in `AdminLayout.jsx`; test `:147-150` expects 2 — green |
| 9 | Ordering: «Дайджест» precedes «Пайплайн» in both nav and option list | ✓ VERIFIED | Declaration order in `AdminLayout.jsx`; test `:150-151` + select path `:201-217` — green |
| 10 | Dirty YAML → in-page «Дайджест» opens the unchanged Phase 19 dialog; «Остаться» keeps URL + draft, «Уйти» lands on digest | ✓ VERIFIED | `AdminPipelineConfigPage.jsx:114` guard present (Phase 23 still wires it); test `:1597` passed this session |
| 11 | Below-sm select leave uses SPA `navigate()`, guard still fires, no `document.location` | ✓ VERIFIED | `AdminLayout.jsx:80`; test `:1636` passed this session |
| 12 | At 1280px and exactly the 640px `sm` edge, both tabs on one row, no horizontal page/content-column scroll | ✓ VERIFIED | `tests/admin.spec.js:316-347` geometry + 639px negative control — passed this session (`Admin nav grouping` 10/10) |
| 13 | Below sm the select stays inside the content column with no horizontal overflow | ✓ VERIFIED | `tests/admin.spec.js:349-372` at 480px and 400px — passed this session |
| 14 | Single «Админ» pill stays visible when the shell nav wraps at narrow width | ✓ VERIFIED | `tests/admin.spec.js:374-401` — passed this session |
| 15 | WR-01 — already-active section tab with dirty editor opens no dialog; genuine tab leave still prompts | ✓ VERIFIED | `AdminLayout.jsx:36-38`; test `:219-250` passed this session |
| 16 | WR-02 / IN-04 — shell «Админ» exposes `aria-current="true"` on every `/admin/*`, none on `/` | ✓ VERIFIED | `AppShell.jsx:38,92-102`; test `:290-313` passed |
| 17 | IN-01 — exactly one visually hidden `h1` per admin surface («Дайджест» / «Пайплайн») | ✓ VERIFIED | `AdminLayout.jsx:49`; `.sr-only` at `index.css:21-31`; test `:252-288` passed |
| 18 | IN-03a — employee deep-linking `/admin/digest` gets layout chrome + ForbiddenPage, no admin data, no shell «Админ» | ✓ VERIFIED | Test `:1769-1802` passed this session |

**Score:** 18/18 truths verified (0 present, behavior-unverified).

### Deferred Items

None actionable for phase goal. IN-02 (`waitForTimeout` at `tests/admin.spec.js:639`) remains an explicitly deferred Info finding from `22-03-PLAN.md` (not a must-have truth).

### Advisory (New Scope, Unevidenced)

None. Stale re-verification found no new-scope Step 7 blockers. Phase 23 commits touched `tests/admin.spec.js` and `AdminPipelineConfigPage.jsx` but did not regress Phase 22 must-haves (spot-checks green).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/src/components/AdminLayout.jsx` | same-section click suppression + sr-only h1 + section nav/select/Outlet | ✓ VERIFIED | `verify.artifacts` 22-01+22-03 passed; `handleSectionTabClick` closes over `section`; select uses `navigate()` |
| `web/src/components/AppShell.jsx` | admin pill = `Link` + manual `aria-current`; prefix-only active matching | ✓ VERIFIED | `:38` prefix-only; `aria-current={adminActive ? 'true' : undefined}`; one «Админ» link |
| `tests/admin.spec.js` | Admin nav grouping cases + dirty→tab + employee deep-link | ✓ VERIFIED | 80 tests (Phase 23 grew file); 0 skipped; nav-grouping describe + dirty/employee cases green this session |
| `web/src/App.jsx` | pathless `AdminLayout` for digest+pipeline; materials sibling; no admin index | ✓ VERIFIED | `:38-47` unchanged contract |
| `web/src/pages/AdminDigestPage.jsx` | no page H1 / duplicate eyebrow | ✓ VERIFIED | No `<h1>` |
| `web/src/pages/AdminPipelineConfigPage.jsx` | no H1/eyebrow; hint + guard intact after Phase 23 sources UI | ✓ VERIFIED | No `<h1>`; `useUnsavedChangesGuard(dirty)` at `:114` |
| `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` | A-2 + Route/nav superseded with 22-UI-SPEC pointer | ✓ VERIFIED | `:19`, `:30`, `:140`, `:190-193` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/admin.spec.js` | `web/src/components/AdminLayout.jsx` | active-tab click asserts zero dialogs | WIRED | `verify.key-links` 22-03 4/4 |
| `tests/admin.spec.js` | `web/src/components/AppShell.jsx` | `aria-current` from shell landmark | WIRED | landmark-scoped `shellAdminLink` |
| `tests/admin.spec.js` | `web/src/index.css` | `.sr-only` keeps heading in a11y tree | WIRED | `index.css:21-31` |
| `web/src/components/AdminLayout.jsx` | `web/src/App.jsx` | pathless parent + `<Outlet />` | WIRED | `App.jsx:40-43`, `AdminLayout.jsx:86-88` |
| `web/src/App.jsx` | `web/src/components/AdminLayout.jsx` | `element: <AdminLayout />` | WIRED | import + element |
| `web/src/components/AppShell.jsx` | `/admin/digest` | sole admin-gated `Link to="/admin/digest"` | WIRED | `:93` |
| `web/src/pages/AdminPipelineConfigPage.jsx` | `useUnsavedChangesGuard` | `useUnsavedChangesGuard(dirty)` + dialog | WIRED | `:114`; behavior pinned by `:1597`, `:1636` |
| `16-UI-SPEC.md` | `22-UI-SPEC.md` | superseded-by pointer | WIRED | `16-UI-SPEC.md:19`, `:30`, `:190` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `AdminLayout.jsx` | `section` | `useLocation().pathname` | Yes — drives select `value`, active tab, sr-only heading | ✓ FLOWING |
| `AppShell.jsx` | `adminActive` | `useLocation().pathname` | Yes — drives `aria-current` and `bg-accent` | ✓ FLOWING |
| `AppShell.jsx` | `appRole` | `getAccessToken()` → session fetch | Yes — gates the single admin entry | ✓ FLOWING |
| `AdminLayout.jsx` | destinations (2 URLs) | literal route whitelist (D-10/D-17) | N/A — static by requirement | ✓ VERIFIED |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Admin nav-grouping contract (10 cases incl. GAP-BACKSTOP-1/2/3) | `npx playwright test --project=web tests/admin.spec.js -g "Admin nav grouping"` | `10 passed (29.8s)` | ✓ PASS |
| Dirty→tab + narrow select leave | `npx playwright test … -g "blocks in-page section nav\|blocks the narrow section select"` | `2 passed (6.7s)` | ✓ PASS |
| Employee deep-link IN-03 | `npx playwright test … -g "employee deep-link renders Forbidden"` | `1 passed (4.2s)` | ✓ PASS |

### Probe Execution

Not applicable: no PLAN/SUMMARY declares probe scripts; SPA chrome + Playwright + docs only.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ADUX-12 | 22-01, 22-02, 22-03 | One «Админ» entry (→ `/admin/digest`) + in-page tab-bar «Дайджест \| Пайплайн»; `/admin/pipeline` unchanged; no new route | ✓ SATISFIED | Truths #1–#2, #5–#18; `REQUIREMENTS.md` ADUX-12 checked Complete → Phase 22 |

No orphaned requirements: `REQUIREMENTS.md` maps only ADUX-12 to Phase 22; all three PLAN frontmatters declare it.

### Decision Coverage

All 19 trackable `22-CONTEXT.md` decisions are honored by shipped artifacts (`check.decision-coverage-verify` → `{total: 19, honored: 19, not_honored: []}`).

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
|-----------|-----------|--------|---------|----------|-----------------|---------|
| `tests/admin.spec.js` | ADUX-12 | 80 | 0 | 0 | Behavioral (geometry, value, multi-step flow) | PASS |

Disabled tests on requirements: 0. Circular fixture generation: 0. File grew from 72→80 under Phase 23; Phase 22 nav-grouping cases remain active and green.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/admin.spec.js` | 639 | `waitForTimeout(500)` (IN-02) | ℹ️ Info | Pre-existing, explicitly deferred in `22-03-PLAN.md`; not a Phase 22 must-have |

No `TBD`/`FIXME`/`XXX` markers in phase-covered production files. No placeholder copy or empty render stubs in AdminLayout / AppShell chrome.

### Human Verification Required

None. Former backstop truths retain automated geometry evidence; re-run this session confirmed they still fail when broken (breakpoint-sensitive probes).

### Gaps Summary

No gaps. Stale digest refresh confirms the phase goal still holds after Phase 23 edits: single shell «Админ» → `/admin/digest`, in-page «Дайджест | Пайплайн» reaches unchanged `/admin/pipeline`, materials preview stays a sibling, no `/admin` index. ADUX-12 satisfied; all four ROADMAP success criteria evidenced; all nine prohibitions held. Fresh `covered_digest` is `v2:sha256:d35ee6e3e88dc520b2a11d01f3efe625efd636e7f010cf38924c3cb7279cd3f6`.

---

_Verified: 2026-10-18T07:35:00Z_
_Verifier: Claude (gsd-verifier)_
