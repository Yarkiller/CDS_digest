---
phase: 22-admin-nav-grouping
plan: 03
subsystem: testing
tags: [playwright, react-router-dom, aria-current, sr-only, geometry-backstop, adux-12]

# Dependency graph
requires:
  - phase: 22-admin-nav-grouping
    provides: AdminLayout pathless chrome (admin-section-nav / admin-tab-digest / admin-tab-pipeline / admin-section-select) and the single shell «Админ» entry from 22-01, plus the dirty→tab/select guard proof from 22-02
  - phase: 19-unsaved-changes-guard-for-the-pipeline-editor
    provides: useUnsavedChangesGuard + UnsavedChangesDialog leave contract that must stay byte-identical (D-13/D-15)
provides:
  - Same-section tab click suppression in AdminLayout (WR-01) with a Playwright case proving a genuine tab leave still prompts
  - One sr-only level-1 heading per admin surface above the section switch (IN-01, D-06 preserved)
  - Shell «Админ» pill with manual aria-current="true" on every /admin/* path and no dead /admin equality branch (WR-02, IN-04)
  - Deterministic Playwright geometry pins for the three former human-only backstops at 1280/640/639 and 480/400 (GAP-BACKSTOP-1/2/3), plus a real employee deep-link case (IN-03)
affects: [22-verify-work, 23-ingest-sources]

# Actuals (#2632) — chars/4 over the realized diff (3 files, +278/−12)
actuals:
  tokens: 4204
  tasks: 3
  commits: 5
  plan_head_before: 42149103ae6e587b6ef74bcf272657578a63ec48
  plan_head_after: 79c6a1b2f534a5e0677733213b44d3b12d6d85a7

tech-stack:
  added: []
  patterns:
    - "TDD for a nav defect: the test states the non-leave (URL + draft + zero dialogs) before asserting the guard still fires for a real leave, so a broadened suppression cannot pass"
    - "Hidden-outline pattern: the accessible name lives in a sr-only h1 in the shared layout, and the case pins BOTH the class and a <=1px bounding box because Playwright treats a 1x1 box as visible"
    - "Manual aria-current on a fixed-href entry: compute state from the pathname prefix, pass \"true\" (not \"page\") because the href is one destination inside a current section"
    - "Geometry backstop pattern: one local layoutMetrics(page) probe (documentElement + main + viewport) with document.fonts.ready before every measurement, and a breakpoint negative control instead of a manufactured failure"
    - "Vacuity audit: replace an assertion that runs on a route where the component never mounts with one on the route that actually mounts it"

key-files:
  created: []
  modified:
    - web/src/components/AdminLayout.jsx
    - web/src/components/AppShell.jsx
    - tests/admin.spec.js

key-decisions:
  - "The same-section suppression lives in AdminLayout.handleSectionTabClick (declared inside the component so it closes over the per-render section) and fires preventDefault ONLY when section === target — the Phase 19 hook, the dialog and its copy are untouched (D-13, D-15)"
  - "The IN-01 heading is an h1 with className=\"sr-only\" placed above the section nav, so ready/loading/error/forbidden branches all inherit it and D-06's no-visible-title rule still holds"
  - "The shell pill switched from NavLink to Link so aria-current is set from the already-computed prefix; the value is the literal \"true\", never \"page\", because the href targets digest while the whole admin section is current (WR-02)"
  - "The dead `pathname === '/admin'` disjunct was deleted rather than commented out — there is no /admin route (D-04) and the catch-all redirects it to /, so the prefix is now the single source of truth (IN-04)"
  - "The three backstops were written as characterization pins (expected GREEN) with a 639px negative control as the red-proof substitute; no tolerance was widened and every measured baseline matched the plan's recorded numbers"
  - "The overflow assertion covers BOTH documentElement and main: documentElement is the page scroll, main is the content column that owns the switch and excludes the wrapping shell header, so it is the tighter signal"
  - "IN-02 (waitForTimeout in the G-14-2 case) stays deferred exactly as the plan documented — fixing it needs a new shortlist-fetch counter in production/mock harness code outside this plan's file set"

requirements-completed: [ADUX-12]

coverage:
  - id: D1
    description: "Clicking the ALREADY-ACTIVE section tab with a dirty editor opens no dialog, keeps the URL and preserves the draft, while clicking the other tab still raises the unchanged Phase 19 dialog and «Остаться» keeps URL + draft"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#dirty editor ignores a click on the already-active section tab (WR-01, D-13)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every admin surface exposes exactly one level-1 heading named after its section, carrying the sr-only class and a <=1px box, with no visible page title restored"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#admin surfaces expose exactly one visually hidden h1 (IN-01, D-06)"
        status: pass
    human_judgment: false
  - id: D3
    description: "The shell «Админ» link reports aria-current=\"true\" on /admin/digest, /admin/pipeline and the materials preview, no aria-current on /, keeps href=/admin/digest and keeps bg-accent"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#shell Админ pill exposes aria-current on every admin path (WR-02, IN-04)"
        status: pass
    human_judgment: false
  - id: D4
    description: "Section tabs sit on one row with no document-level or content-column horizontal overflow at 1280px and at exactly the 640px sm edge, and the same probe returns a hidden nav + visible select at 639px"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#section tabs share one row with no overflow at 1280 and the 640px sm edge (GAP-BACKSTOP-1)"
        status: pass
    human_judgment: false
  - id: D5
    description: "At 480px and 400px the section select is visible, starts and ends inside the content column and the viewport, does not exceed the column width, and the document does not scroll horizontally"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#narrow section select stays inside the content column without overflow (GAP-BACKSTOP-2)"
        status: pass
    human_judgment: false
  - id: D6
    description: "At 480px, where the shell nav measurably wraps past one pill row, the single «Админ» pill stays fully inside the viewport and the section switch is the select only"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#single shell Админ pill stays visible when the shell nav wraps (GAP-BACKSTOP-3)"
        status: pass
    human_judgment: false
  - id: D7
    description: "An employee deep-linking /admin/digest gets layout chrome + ForbiddenPage «Недостаточно прав», no admin data surface, no shell «Админ», and exactly two level-1 headings (sr-only section name + visible state name)"
    requirement: ADUX-12
    verification:
      - kind: e2e
        ref: "tests/admin.spec.js#employee deep-link renders Forbidden and no admin data at /admin/digest (IN-03)"
        status: pass
    human_judgment: false

metrics:
  duration: 25min
  completed: 2026-10-17
status: complete
---

# Phase 22 Plan 03: Gap-closure backstops + shell a11y state Summary

**A dirty admin editor no longer prompts on the tab it is already on, the shell «Админ» pill now announces the admin section to assistive tech on every `/admin/*` path, each admin page regains one visually hidden `h1`, and the three former human-only layout backstops are proven by deterministic Playwright geometry at 1280/640/639 and 480/400**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-10-17T12:11:00Z (15:11 local)
- **Completed:** 2026-10-17T12:35:10Z (15:35 local)
- **Tasks:** 3
- **Files modified:** 3 (0 created)

## RED → GREEN evidence (TDD, mandatory)

Tasks 1 and 2 are `tdd="true"`. No production file was touched before each RED run was observed.

**Task 1 RED** — command: `npm run test:web -- tests/admin.spec.js -g "WR-01|IN-01|dirty editor blocks"`

```text
  1) [web] › tests\admin.spec.js:197:3 › Admin nav grouping — in-page section switch … › dirty editor ignores a click on the already-active section tab (WR-01, D-13)

    Error: expect(locator).toHaveCount(expected) failed

    Locator:  getByRole('dialog')
    Expected: 0
    Received: 1

    > 214 |     await expect(page.getByRole("dialog")).toHaveCount(0);

  2) [web] › tests\admin.spec.js:230:3 › Admin nav grouping — in-page section switch … › admin surfaces expose exactly one visually hidden h1 (IN-01, D-06)

    Error: expect(locator).toHaveCount(expected) failed

    Locator:  getByRole('heading', { name: 'Дайджест', exact: true, level: 1 })
    Expected: 1
    Received: 0

    > 240 |     await expect(digestHeading).toHaveCount(1);

  2 failed
  66 passed (3.4m)
```

Both failures are the intended ones: a dialog opened on the already-active tab (WR-01) and no level-1 heading existed at all, so the `sr-only` class/geometry assertions never resolved (IN-01). No `ERR_CONNECTION_REFUSED`, no "0 passed", no unrelated failure; 66 is the pre-existing baseline from 22-02.

**Task 2 RED** — command: `npm run test:web -- tests/admin.spec.js -g "WR-02|admin-section pipeline tab|materials preview"`

```text
  1) [web] › tests\admin.spec.js:268:3 › Admin nav grouping — in-page section switch … › shell Админ pill exposes aria-current on every admin path (WR-02, IN-04)

    Error: expect(locator).toHaveAttribute(expected) failed

    Locator:  getByRole('navigation', { name: /основная навигация/i }).getByRole('link', { name: /^Админ$/ })
    Expected: "true"
    Received: "page"

    Call log:
      - locator resolved to <a aria-current="page" href="/admin/digest" … class="… bg-accent text-accent-ink">Админ</a>

    > 289 |       await expect(adminLink).toHaveAttribute("aria-current", "true");

  1 failed
  68 passed (3.2m)
```

The `/` step passed (no attribute) and the first `/admin/*` path failed with NavLink's own `"page"` — exactly the shipped-tree value the plan predicted. The remaining two admin paths assert the identical expectation after the same assertion block.

**GREEN** — Task 1: `npm run test:web -- tests/admin.spec.js` → **68 passed (3.2m)**. Task 2: → **69 passed (3.1m)**. Task 3 + final full file: **72 passed (3.1m)**, no `ERR_CONNECTION_REFUSED`, port `5174` verified free (no listener) before the final run.

**Task 3 is a characterization pin** — the four layout/coverage cases are GREEN on the shipped tree by design, as the plan states; their red-proof substitute is the 639px negative control inside GAP-BACKSTOP-1 (same probe, nav hidden + select visible).

**TDD gate commits:** `test(22-03)` → `feat(22-03)` → `test(22-03)` → `feat(22-03)` → `test(22-03)`. Both required RED commits precede their `feat` counterparts.

## Accomplishments

- **WR-01 / D-13:** `AdminLayout.handleSectionTabClick(event, target)` is declared inside the component (closing over the per-render `section`) and calls `preventDefault()` only when the clicked tab is already the active section. A dirty editor keeps URL, draft and no dialog on the active tab; a genuine leave to the other tab still raises the byte-identical Phase 19 dialog and «Остаться» keeps URL + draft.
- **IN-01 / D-06:** one `<h1 className="sr-only">` naming the current section sits above the section nav, so ready/loading/error/forbidden branches all inherit an outline anchor while no visible title returns.
- **WR-02 / IN-04:** the shell «Админ» pill is a `Link` with `aria-current={adminActive ? 'true' : undefined}`; `bg-accent`, `href="/admin/digest"` and the role gate are unchanged, and the unreachable `pathname === '/admin'` equality is gone.
- **GAP-BACKSTOP-1/2/3 now deterministic:** tabs share one row (tops equal within 1px, digest ends before pipeline starts) with no `documentElement` or `main` overflow at 1280 and exactly 640 on both admin routes; the select stays inside the content column at 480 and 400; at 480 the wrapped shell keeps the single «Админ» pill fully in the viewport while the section switch is the select only.
- **IN-03:** the vacuous employee test (which browsed `/`, a route where `AdminLayout` never renders) is replaced in place by a deep-link case proving layout chrome + `ForbiddenPage`, zero admin data surfaces, no shell «Админ», and exactly two level-1 headings on that branch.
- `tests/admin.spec.js` grows 66 → 72 cases: seven written, one rewritten in place.

## Task Commits

Each task was committed atomically (TDD: test → feat):

1. **Task 1 (RED): pin same-tab click suppression and the admin h1 outline** - `e4646bc` (test)
2. **Task 1 (GREEN): suppress same-section tab clicks + add a visually hidden section h1** - `df3fb17` (feat)
3. **Task 2 (RED): require aria-current=true on the shell admin pill for every admin path** - `1be70f3` (test)
4. **Task 2 (GREEN): truthful aria-current + drop the dead /admin branch** - `e4046a7` (feat)
5. **Task 3: automate the layout backstops and replace the vacuous employee case** - `79c6a1b` (test)

**Plan metadata:** docs commit (this SUMMARY only — STATE.md/ROADMAP.md are owned by the orchestrator for this dispatch)

## Files Created/Modified

- `web/src/components/AdminLayout.jsx` — `handleSectionTabClick` wired to both `NavLink`s; one `sr-only` `h1` above the nav. Guard hook, dialog, copy and select branch untouched.
- `web/src/components/AppShell.jsx` — admin `NavLink` → `Link` with manual `aria-current`; `adminActive` reduced to the `/admin/` prefix; D-09 comment updated to say the prefix is the single source of truth.
- `tests/admin.spec.js` — `layoutMetrics(page)` helper beside `shellNav`/`shellAdminLink`; two guard/a11y cases (WR-01, IN-01); one aria-current case (WR-02/IN-04); three geometry cases (GAP-BACKSTOP-1/2/3); the employee case rewritten in place (IN-03).

## Decisions Made

- Suppressed only the exact same-section click rather than adding a same-location carve-out to `useUnsavedChangesGuard`: the local fix cannot weaken the Phase 19 contract globally (D-13), and the very next assertion in the same test proves a genuine leave still prompts.
- Used `aria-current="true"` instead of `"page"` for the shell pill: the link points at digest while the whole admin section is the current context, and it also keeps the section-tab `"page"` assertions (which pin react-router's own value) meaningful.
- Kept the IN-01 heading in the layout, not in the pages: one heading covers every child branch including the employee forbidden branch without editing either page.
- Asserted overflow on both `documentElement` and `main`. `documentElement` catches page-level scroll; `main` is the content column that owns the switch and excludes the wrapping header, so it is the tighter, more meaningful signal. Measured baseline matched the plan exactly (1280 → document 1280/1280, main 1152/1152; 640 → both 640/640; 480/400 select x=16 with width 384/368).
- Measured the shell wrap instead of hardcoding it: `GAP-BACKSTOP-3` compares the nav box height to an actual pill box rather than to a 44px constant.
- Left the pre-existing `waitForTimeout(500)` (now `tests/admin.spec.js:639`) alone — that is the explicitly deferred IN-02 with its reason and follow-up recipe recorded in the plan; no new timeout was introduced (diff scan: 0 added `waitForTimeout`).

## Deviations from Plan

None — plan executed exactly as written. No auto-fixes (Rules 1–3) were needed, no architectural change (Rule 4) arose, and no geometry tolerance was widened.

## Issues Encountered

- A first attempt to commit the Task 2 RED test failed on PowerShell quoting of the em-dash/backslash-bearing commit body (`error: pathspec … did not match`); the message was rewritten with single-quoted `-m` arguments and the commit succeeded. No content changed, no `--amend` was needed because nothing had been committed.
- Playwright's `-g` filter did not narrow the runs (same operational note as 22-01/22-02): each targeted command executed the whole file. Evidence is unaffected — the failure lists contain only the target cases, and the pass counts (66 → 68 → 69 → 72) track the added cases.
- Port `5174` was free before every run (`Get-NetTCPConnection` → no listener), so the STATE.md Vite flakiness blocker did not recur.

## Known Stubs

None — no placeholder copy, empty-value plumbing, or unwired control was introduced (tests plus two local component deltas only).

## Threat Flags

None — no new network surface, auth path, or file-access pattern. T-22-06 is mitigated by `handleSectionTabClick` firing only on `section === target` plus the same-test genuine-leave assertion; T-22-07 by pinning the literal `"true"` on digest/pipeline/preview and absence on `/`; T-22-08 is unchanged (chrome still renders for an employee, but IN-03 now pins that no data surface does); T-22-09 by asserting both `main` and `documentElement` widths plus the 639px negative control; T-22-SC held (no package installs).

## Deferred (explicit, not silently dropped)

**IN-02** — `tests/admin.spec.js:639` still uses `waitForTimeout(500)` in the G-14-2 case. Deferred per the plan: under `VITE_USE_MOCKS=true` the refetch is a mocked promise with no network request, and no observable busy attribute exists during `mutating`; the deterministic fix needs a shortlist-fetch counter in `web/src/services/adminApi.js` + `web/src/main.jsx`, outside this plan's file set. Follow-up recipe is recorded in the plan and in `22-REVIEW-DISPOSITION.md`.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `22-VERIFICATION.md` rows #12–14 (the three `behavior_unverified_items`) are now CI-verifiable, so the `human_needed` verdict can be re-derived without a manual backstop pass.
- WR-01, WR-02, IN-01, IN-03, IN-04 are retired; IN-02 remains the only carry-over finding from `22-REVIEW.md`.
- `tests/admin.spec.js` is green at 72 passed; the three Phase 19 dirty-leave journeys (`:1597`, `:1636`, and the new WR-01 case) all pass together, proving the guard contract did not move.
- Phase 23 (ingest sources) can grow under the «Пайплайн» tab; nothing in the chrome, guard, or shell contract changed shape.

---
*Phase: 22-admin-nav-grouping*
*Completed: 2026-10-17*

## Self-Check: PASSED

- Files present: `web/src/components/AdminLayout.jsx`, `web/src/components/AppShell.jsx`, `tests/admin.spec.js` (3/3 FOUND)
- Commits present: `e4646bc`, `df3fb17`, `1be70f3`, `e4046a7`, `79c6a1b` (5/5 FOUND)
- Old vacuous title `pipeline config nav item hidden for employee` → 0 occurrences; `pathname === '/admin'` in `AppShell.jsx` → 0 occurrences
- Full suite: 72 passed (3.1m), 0 failed, no `ERR_CONNECTION_REFUSED`
