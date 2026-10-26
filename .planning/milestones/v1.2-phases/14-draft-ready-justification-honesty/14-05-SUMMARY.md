---
phase: 14-draft-ready-justification-honesty
plan: 05
subsystem: ui
tags: [react, vite, playwright, admin, adux-05, gap-closure, tdd]

# Dependency graph
requires:
  - phase: 14-draft-ready-justification-honesty
    provides: "14-04 FE promote reconciliation (preservePromotedReady) + __DIGEST_ADMIN_STALE_READY__ stale-refetch lock"
provides:
  - "Localized material_status pill via materialStatusLabel («готов»/«черновик», raw fallback)"
  - "Qualified decisionCaption («одобрен (в шортлист)» / «отклонён (из шортлиста)») — two disambiguated status axes"
  - "Sticky send footer deduped — no re-listed approved-draft <ul>"
  - "Quantified batch CTA «Сделать ready все одобренные черновики (N)»"
affects: [14-draft-ready-justification-honesty, admin-shortlist]

actuals:
  tokens: 2040
  tasks: 2
  commits: 4
plan_head_before: 68a3ce0c7d2480f65c63e3875677eff481913108
plan_head_after: fb9845ae166e677c0eeef64d6d357d6ff192d110

tech-stack:
  added: []
  patterns:
    - "Two independent status axes rendered as distinct labelled dimensions (publish-readiness pill vs shortlist triage decision caption)"
    - "Count-only footer hint + quantified action label; no duplicate title list under the sticky footer"

key-files:
  created: []
  modified:
    - web/src/pages/AdminDigestPage.jsx
    - tests/admin.spec.js

key-decisions:
  - "Localize the pill in copy only (materialStatusLabel) rather than hiding/merging axes — material_status and decision stay independent (D-02: approve ≠ ready)"
  - "Qualify the triage caption with its scope («в шортлист»/«из шортлиста») so draft + approved reads as two dimensions, not a contradiction"
  - "Drop the footer <ul> entirely (approved-draft titles already rendered in the shortlist) and quantify the CTA from approvedDrafts.length"
  - "Left sendHint and the confirm dialog («Сделать ready N одобренных черновиков?») untouched — already unambiguous"

patterns-established:
  - "materialStatusLabel(status) maps ready→«готов», draft→«черновик», raw fallback otherwise; used for the row pill text"
  - "decisionCaption(decision) qualifies the shortlist decision axis independently of material readiness"
  - "Batch CTA label interpolates approvedDrafts.length so the action scope is explicit"

requirements-completed: [ADUX-05]

coverage:
  - id: D1
    description: "Approved draft row shows two disambiguated localised axes: «черновик» pill + «одобрен (в шортлист)» caption; ready rows show «готов» (G-14-2a)"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#Approve does not auto-ready draft (D-02)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#populated shortlist shows ≤5 rows with badges and score factors"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#per-row Сделать ready promotes draft and clears draft hint (ADUX-05)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sticky send footer no longer duplicates approved-draft titles; batch CTA is quantified «Сделать ready все одобренные черновики (N)» (G-14-2b)"
    requirement: "ADUX-05"
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#batch Сделать ready одобренные черновики issues one markReadyBatch (ADUX-05)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#approved draft blocks send with draft hint (ADMIN-03/07, D-85)"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-10-03
status: complete
---

# Phase 14 Plan 05: Disambiguate status axes + dedupe send footer (ADUX-05) Summary

**Approved drafts no longer read as a contradiction — the material_status pill is localised («черновик»/«готов») and the triage caption is qualified («одобрен (в шортлист)»), and the sticky footer drops its duplicate title list for a count-only hint plus a quantified batch CTA.**

## Performance

- **Duration:** 12min
- **Started:** 2026-10-03T16:45:09Z
- **Completed:** 2026-10-03T16:57:00Z
- **Tasks:** 2
- **Files modified:** 2 (0 created, 2 modified)

## Accomplishments
- Added `materialStatusLabel(status)` and rendered it in place of the raw `{item.material_status}` pill, so rows now read «черновик»/«готов» instead of raw English `draft`/`ready`.
- Qualified `decisionCaption` to «одобрен (в шортлист)» / «отклонён (из шортлиста)», making the shortlist triage decision a distinct labelled axis from publish-readiness; an approved draft now reads as two independent dimensions (G-14-2a).
- Removed the sticky footer `<ul>` that re-listed `approvedDrafts` titles already visible in the shortlist (G-14-2b).
- Renamed the batch CTA to the quantified action «Сделать ready все одобренные черновики (N)» with `N = approvedDrafts.length`; left `sendHint` and the confirm dialog unchanged (G-14-2b).

## Task Commits

Each task was committed atomically (TDD: RED then GREEN):

1. **Task 1: Disambiguate material_status pill and decision caption (G-14-2a)**
   - `4e6a24d` (test) — add failing localized status-axis asserts (G-14-2a)
   - `c5e28fc` (feat) — localize status pill + qualify decision caption (G-14-2a)
2. **Task 2: Dedupe sticky footer and quantify batch CTA (G-14-2b)**
   - `20f0549` (test) — add failing dedupe footer + quantified CTA asserts (G-14-2b)
   - `fb9845a` (feat) — dedupe send footer + quantify batch CTA (G-14-2b)

**Plan metadata:** pending (this SUMMARY commit)

_Note: TDD tasks commit RED and GREEN separately, so a single plan task spans two commits._

## Files Created/Modified
- `web/src/pages/AdminDigestPage.jsx` — added `materialStatusLabel`; qualified `decisionCaption`; pill renders `materialStatusLabel(item.material_status)`; removed the footer `<ul>`; batch CTA label interpolates `approvedDrafts.length`. Per-row «Сделать ready» button condition (`material_status === 'draft'`) and pill styling unchanged. No `adminApi`/services changes (display-copy only).
- `tests/admin.spec.js` — updated every English `draft`/`ready` pill assertion to the localised labels; D-02 asserts «черновик» + «одобрен (в шортлист)» coexist; batch test asserts the quantified CTA and that `admin-send-footer` has no `<ul>`; approved-draft-blocks-send asserts the row «черновик» pill instead of the removed `· draft` footer text.

## Decisions Made
- Kept the two axes as two labelled dimensions (copy change) rather than merging them — `material_status` and `decision` remain independent by design (D-02: approve ≠ ready).
- Removed the footer title list outright (it was a strict subset of the already-rendered shortlist) instead of collapsing it to a count line; the quantified CTA carries the scope.
- Left the confirm dialog and send hint untouched — already unambiguous and asserted by prior tests.

## Deviations from Plan

None - plan executed exactly as written. TDD RED was observed for both tasks before GREEN:
- Task 1 RED: 5 failed / 30 passed — failures were exactly the new localised-label/caption assertions (`getByText('готов'/'черновик'/'одобрен (в шортлист)')` element-not-found).
- Task 2 RED: 2 failed / 33 passed — failures were the quantified CTA `toHaveText` and the footer `<ul>` `toHaveCount(0)`.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- G-14-2a and G-14-2b are closed: the status axes are disambiguated/localised and the sticky footer is deduped with a quantified CTA, regression-locked by the full admin Playwright suite.
- Ready for phase-level verification of Phase 14 (`/gsd-verify-work 14`).

---
*Phase: 14-draft-ready-justification-honesty*
*Completed: 2026-10-03*

## Self-Check: PASSED

- FOUND: `.planning/phases/14-draft-ready-justification-honesty/14-05-SUMMARY.md`
- FOUND: `web/src/pages/AdminDigestPage.jsx`, `tests/admin.spec.js`
- FOUND: `4e6a24d`, `c5e28fc`, `20f0549`, `fb9845a` (TDD RED/GREEN task commits)
- `npm run test:web -- tests/admin.spec.js -g "одобрен|черновик|готов|badges|draft|Сделать ready"` — 35 passed / 0 failed
- `npm run test:web -- tests/admin.spec.js -g "Сделать ready|footer|draft hint|одобренных черновиков"` — 35 passed / 0 failed
- `npm run test:web -- tests/admin.spec.js` (full admin suite) — 35 passed / 0 failed
- `node --test tests/unit/test_admin_mark_ready.js` — 10 passed / 0 failed
