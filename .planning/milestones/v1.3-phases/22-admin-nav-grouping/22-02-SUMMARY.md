---
phase: 22-admin-nav-grouping
plan: 02
subsystem: testing
tags: [playwright, react-router-dom, unsaved-changes-guard, adux-12, ui-spec]

# Dependency graph
requires:
  - phase: 22-admin-nav-grouping
    provides: AdminLayout in-page section switch (admin-section-nav / admin-tab-digest / admin-tab-pipeline / admin-section-select) and the single shell «Админ» entry
  - phase: 19-unsaved-changes-guard-for-the-pipeline-editor
    provides: useUnsavedChangesGuard boolean useBlocker + UnsavedChangesDialog copy/testids reused unchanged
provides:
  - Playwright dirty→in-page tab stay/leave journey (D-14) plus a below-sm select leave journey (D-19), both asserting the byte-identical Phase 19 dialog
  - Characterization pin proving the tab/select leave paths need no guard carve-out on the post-22-01 tree
  - 16-UI-SPEC A-2 + Route/nav supersession by ADUX-12 / Phase 22 with a pointer to 22-UI-SPEC
affects: [22-verify-work, 23-ingest-sources]

# Actuals (#2632) — chars/4 over the realized diff (2 files, +79/−6)
actuals:
  tokens: 2718
  tasks: 2
  commits: 2
  plan_head_before: 2780e6cf6f7656d1de2da1cbb81c28dcc804219a
  plan_head_after: 202b72cb251caa601d4f40490cdd5d3235965dfe

tech-stack:
  added: []
  patterns:
    - "Landmark-scoped dirty-leave journey: the section nav is fetched by data-testid so the shell nav can never satisfy a «Дайджест» click"
    - "Two-journey guard proof: the sm+ NavLink path and the below-sm select path are separate tests so a select-only regression cannot hide behind a green tab case"
    - "Characterization pin recorded as a legitimate GREEN-first outcome — a new journey that passes on an unchanged tree is evidence D-14/D-19 already hold, not a reason to manufacture a production edit"
    - "Upstream UI-SPEC retirement: strike the obsolete clause, keep the surviving rule («no second navigation bar»), and point at the superseding phase spec"

key-files:
  created: []
  modified:
    - tests/admin.spec.js
    - .planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md

key-decisions:
  - "Both new journeys passed on the post-22-01 tree with zero production edits, so this plan is a characterization pin: D-13/D-14/D-15/D-19 already hold because AdminLayout uses NavLink for tabs and navigate() for the select (D-19)"
  - "The tab journey scopes «Дайджест» to admin-section-nav rather than a bare name match, so the shell can never produce a false green if a future change reintroduces an admin shell item"
  - "The narrow select journey was kept as a second test instead of an optional inline assert: it is the only automated proof that the below-sm control does not bypass the Phase 19 blocker"
  - "16-UI-SPEC A-2 is marked SUPERSEDED in three places (top banner, A-2 row, Route/nav heading) so a reader landing anywhere sees the retirement; the page-H1 copy row is struck with D-06 rather than silently contradicting the shipped pages"
  - "No editor/toolbar/validator/save text in 16-UI-SPEC was touched — the supersession diff is 9 lines added and 6 removed"

patterns-established:
  - "Dirty-leave proof pattern: same dialog testids (unsaved-changes-message / -stay / -leave) for every leave origin — shell link, in-page tab, narrow select"
  - "A superseded assumption keeps its historical text visible (strikethrough) next to the replacement contract, so the decision trail survives"

requirements-completed: [ADUX-12]

coverage:
  - id: D1
    description: "Dirty pipeline → in-page «Дайджест» tab opens the Phase 19 dialog with unchanged copy; «Остаться» keeps URL + draft; «Уйти без сохранения» lands on /admin/digest"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config dirty editor blocks in-page section nav and Дайджест leave keeps the draft"
        status: pass
    human_judgment: false
  - id: D2
    description: "Below sm the section select leave while dirty opens the same dialog, keeps the draft on «Остаться», and reaches digest on «Уйти без сохранения» (no document.location bypass)"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#pipeline config dirty editor blocks the narrow section select leave"
        status: pass
    human_judgment: false
  - id: D3
    description: "16-UI-SPEC A-2 and its Route/nav bullets are superseded by ADUX-12 / Phase 22 with a 22-UI-SPEC pointer; no second-shell «Пайплайн» mandate remains active"
    requirement: ADUX-12
    verification:
      - kind: other
        ref: "plan <verify> node script → '16-UI-SPEC A-2 supersession OK' (ADUX-12 cite, superseded marker, AdminLayout/in-page, A-2 window check)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Visual backstops: tabs stay on one row at 1280px and ~640px without horizontal page scroll; the below-sm select is usable without overflow; the single «Админ» pill survives shell header wrap"
    requirement: ADUX-12
    verification: []
    human_judgment: true
    rationale: "UI-SPEC rows are `backstop` probes — automated asserts can only see the breakpoint swap (22-01 D4), not layout elegance; queued for end-of-phase UAT."

metrics:
  duration: 10min
  completed: 2026-10-17
status: complete
---

# Phase 22 Plan 02: Dirty→tab guard proof + 16-UI-SPEC A-2 supersession Summary

**Dirty pipeline → in-page «Дайджест» (and the below-sm select) proven to raise the unchanged Phase 19 leave dialog with zero production edits, while 16-UI-SPEC A-2's second-shell «Пайплайн» mandate is retired**

## Performance

- **Duration:** 10 min
- **Started:** 2026-10-17T10:36:00Z (13:36 local)
- **Completed:** 2026-10-17T10:45:00Z (13:45 local)
- **Tasks:** 2
- **Files modified:** 2 (0 created)

## TDD evidence (Task 1 — RED-first, GREEN-first outcome)

No production file was touched before or after the test run. The plan explicitly allows this
outcome: if the new journey passes immediately on the post-22-01 tree it is a characterization
pin proving D-14 already holds.

**RED attempt** — command:
`npm run test:web -- tests/admin.spec.js -g "dirty editor blocks|Дайджест|unsaved"`

```text
ok 54 [web] › tests\admin.spec.js:1430:3 › … › pipeline config dirty editor blocks the narrow section select leave
      [web] › … › pipeline config dirty editor blocks in-page section nav and Дайджест leave keeps the draft
66 passed (2.9m)
```

No failure, no `ERR_CONNECTION_REFUSED`, no `0 passed`. Count moved 64 → 66, so both new journeys
ran. **Interpretation:** the guard already fires on tab and select leave because `AdminLayout`
uses `NavLink` for tabs and `navigate()` for the select (D-13, D-19). Therefore GREEN needed **zero
production edits** — no change to `useUnsavedChangesGuard.js`, `UnsavedChangesDialog.jsx`, the
Phase 19 copy, `AdminLayout.jsx`, or either admin page. The test was committed first (before any
other work) as the plan requires.

**Task 2 verification** — plan `<verify>` node script over `16-UI-SPEC.md`:

```text
16-UI-SPEC A-2 supersession OK
```

(checks: `ADUX-12` cite · superseded marker · `AdminLayout|in-page` · A-2 window no longer mandates
a shell «Пайплайн» without supersession)

## Accomplishments

- `tests/admin.spec.js` gains a dirty→in-page «Дайджест» journey: dialog copy asserted byte-identical
  («Есть несохранённые изменения. Уйти без сохранения?»), «Остаться» keeps `/admin/pipeline` + the
  dirty draft + the active pipeline tab, «Уйти без сохранения» lands on `/admin/digest` with the
  dialog closed and the digest tab active (D-13, D-14, D-15).
- Second journey covers the below-sm `admin-section-select` leave: the same dialog appears, «Остаться»
  keeps the draft and re-syncs the select to `/admin/pipeline`, «Уйти без сохранения» reaches digest —
  automated proof that `navigate()` is the only select leave path (D-19).
- Both `«Дайджест»` lookups are scoped to `admin-section-nav` / `admin-section-select`, so the shell
  landmark can never satisfy them; no carve-out, no dialog or copy edit.
- `16-UI-SPEC.md` A-2 is explicitly superseded by ADUX-12 / Phase 22 with a pointer to
  `22-UI-SPEC.md`, and the Route/nav bullets now state the shipped contract: route retained, single
  shell «Админ» → `/admin/digest`, in-page underline tabs inside `AdminLayout`, ``no second navigation
  bar`` still true because the tab row is in-page content (D-05).
- The page-H1 copy row is struck with the D-06 citation instead of silently contradicting the pages
  that no longer render an H1.

## Task Commits

Each task was committed atomically:

1. **Task 1: Playwright dirty editor → in-page «Дайджест» stay/leave journey** - `3092246` (test)
2. **Task 2: Supersede 16-UI-SPEC A-2 and Route/nav shell «Пайплайн» mandate** - `202b72c` (docs)

**Plan metadata:** docs commit (this SUMMARY + STATE.md + ROADMAP.md)

_No feat commit: the RED attempt was green, so this is a characterization pin (see TDD evidence)._

## Files Created/Modified

- `tests/admin.spec.js` — two new journeys in the existing `Admin pipeline config — empty/dirty/reset/nav/no-execution` describe; +70 lines, no edits to existing cases.
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` — top-of-file supersession banner, superseded A-2 row with the replacement contract, struck page-H1 copy row, rewritten Route/nav bullets; +9/−6 lines, every editor/toolbar/validation paragraph untouched.

## Decisions Made

- Treated the immediate green as the plan's sanctioned characterization-pin outcome rather than manufacturing a production change to force red.
- Kept the select journey as its own test (the plan marked it optional) because it is the only automated proof of D-19 — the tab case cannot see a `document.location` regression in the select.
- Scoped every section control by testid instead of a bare link-name match, so a future shell entry labelled «Дайджест» could not create a false green.
- Recorded the supersession in three locations in `16-UI-SPEC.md` and preserved the historical assumption text (strikethrough) for the decision trail.
- Left `REQUIREMENTS.md` untouched: ADUX-12 was already marked complete by Plan 22-01 and remains accurate (this plan completes its remaining proof, not a new requirement).

## Deviations from Plan

None — plan executed exactly as written (including the explicitly allowed green-first characterization pin).

## Issues Encountered

- Playwright's `-g` filter again did not narrow the run: the invocation executed all 66 `admin.spec.js` tests (~2.9 min). Evidence is unaffected — the summary line is a full-file pass and the test count confirms both new journeys ran. Same operational note as Plan 22-01.
- Port 5174 was free before the run (`Get-NetTCPConnection` → no listener), so the STATE.md Vite flakiness blocker did not recur.

## Human Visual Backstops (queue for end-of-phase UAT)

| # | Check | Why manual |
|---|-------|------------|
| 1 | At ~1280px and at the `sm` edge (~640px) the two tab labels stay on one row with no horizontal page scroll | Layout judgment; automation only proves the breakpoint swap |
| 2 | Below `sm` the native section select is fully usable inside the content column with no horizontal overflow | Same |
| 3 | When the shell header wraps at a narrow width, the single «Админ» pill stays visible and the section switch still reads as in-page underline chrome (not a second pill bar) | Visual hierarchy / product-shape judgment |

## Known Stubs

None — no placeholder copy, empty-value plumbing, or unwired control was introduced (test + docs only).

## Threat Flags

None — no new network surface, auth path, or file-access pattern. T-22-04 (dirty→tab tampering) is now covered by the two journeys; T-22-05 (A-2 drift) by the explicit superseded marker plus the plan verify script; T-22-SC held (no package installs).

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Phase 22 is code-complete: Plan 22-01 shipped the chrome, Plan 22-02 pinned the dirty-leave behaviour and retired the conflicting upstream contract.
- `/gsd-verify-work` should harvest the three visual backstops above as UAT items; `tests/admin.spec.js` is green at 66 passed.
- Phase 23 (ingest sources) can grow under the «Пайплайн» tab; the guard contract it inherits is unchanged and now pinned from three leave origins.

---
*Phase: 22-admin-nav-grouping*
*Completed: 2026-10-17*

## Self-Check: PASSED

- `tests/admin.spec.js` contains both new journeys (lines 1391 and 1430)
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` supersession verify → `16-UI-SPEC A-2 supersession OK`
- Commits `3092246` and `202b72c` present on `experiment/gsd-framework`
- Target run: 66 passed (2.9m), no `ERR_CONNECTION_REFUSED`, no `0 passed`
