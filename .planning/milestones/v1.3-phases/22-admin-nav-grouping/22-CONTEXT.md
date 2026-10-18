# Phase 22: Admin nav grouping - Context

**Gathered:** 2026-10-17
**Status:** Ready for planning

<domain>
## Phase Boundary

The pipeline config surface is reached from the **admin area**, not a second top-level nav item. Exactly one AppShell entry «Админ» points to `/admin/digest`. An **in-page** tab-bar «Дайджест | Пайплайн» switches between the existing digest and pipeline pages. Route `/admin/pipeline` is unchanged; **no new route** is added. `16-UI-SPEC` A-2 is amended so it no longer mandates a second top-level «Пайплайн» item, and the "no second navigation bar" rule stays honoured because the tab-bar is in-page content, not shell chrome.

This is a **frontend-only** backlog close-out (backlog 999.5 / ADUX-12 / Phase 16 UAT option C). It regroups navigation; it does not change the pipeline validator, config API, digest send flow, or materials preview behaviour beyond shell active-state.

**In scope:**
- Remove top-level AppShell «Пайплайн»; keep a single «Админ» → `/admin/digest`.
- Shared `AdminLayout` (tabs + `<Outlet>`) nested under `AppShell` for `digest` + `pipeline` only.
- Underline in-page tabs that **replace** each page's H1; labels «Дайджест | Пайплайн».
- AppShell «Админ» active on any `/admin/*`; click always navigates to `/admin/digest`.
- Narrow viewport (`< sm`): native `<select>` backstop; phone admin is not a target use case.
- Dirty pipeline editor: Phase 19 `useBlocker` / `UnsavedChangesDialog` fires on tab (and select) navigation — no carve-out; new Playwright journey; copy unchanged.
- Amend `16-UI-SPEC` A-2; RED-first Playwright for the nav contract (tripwire: tests that assert top-level «Пайплайн»).

**Out of scope:**
- New routes (including `/admin` index redirect).
- Materials-preview chrome changes (no new «← К шортлисту» this phase).
- ADUX-10 / ingest-sources editor (Phase 23).
- Pipeline editor features, validator, config API, composition, schema.
- Polished mobile-admin UX beyond the select backstop.

</domain>

<decisions>
## Implementation Decisions

### Tab-bar host
- **D-01:** Shared **AdminLayout** with tab-bar + `<Outlet>`; digest and pipeline are child routes. — **Reversibility:** costly — undoing means re-flattening routes and re-duplicating tabs on every admin page that needs them.
- **D-02:** AdminLayout is **nested inside AppShell** (RequireAuth → AppShell → AdminLayout → page). Top-level shell chrome stays; only the «Пайплайн» shell link is removed. — **Reversibility:** costly — layout nesting touches `App.jsx` and every admin child path.
- **D-03:** Only **`digest` + `pipeline`** sit under AdminLayout; `/admin/materials/:id` remains a **sibling** without the tab-bar. — **Reversibility:** reversible.
- **D-04:** **No `/admin` index redirect** — no new `/admin` route; entry is the shell «Админ» link → `/admin/digest`. — **Reversibility:** reversible.

### Tab visual style
- **D-05:** **Underline tabs** (text + bottom border on active) — not AppShell pills — so the control reads as in-page section switch, honouring 16-UI-SPEC "no second navigation bar". — **Reversibility:** reversible.
- **D-06:** Tabs **replace** the page H1 (no duplicate display title above content). — **Reversibility:** reversible.
- **D-07:** Tab labels: **«Дайджест» | «Пайплайн»** (ROADMAP / ADUX-12 short forms). — **Reversibility:** reversible.
- **D-08:** Active tab is **display-size** (`text-3xl font-semibold`); inactive quieter. — **Reversibility:** reversible.

### Nested admin routes
- **D-09:** AppShell «Админ» is **active on any `/admin/*`** (digest, pipeline, materials preview). — **Reversibility:** reversible — typically `NavLink` `className` / `isActive` matching, not `end`.
- **D-10:** Click «Админ» **always navigates to `/admin/digest`** (fixed entry; matches ROADMAP). — **Reversibility:** reversible.
- **D-11:** On `/admin/materials/:id` this phase does **nothing** beyond «Админ» highlight — no new back-link. — **Reversibility:** reversible.
- **D-12:** Tab-bar markup is **`nav aria-label="Разделы админки"` + `NavLink`**, not `role="tablist"` / tab / tabpanel — these are routes, not in-place tabs. — **Reversibility:** reversible.

### Dirty pipeline guard
- **D-13:** Dirty YAML → click tab «Дайджест» fires the **Phase 19** `UnsavedChangesDialog`; tab navigation is ordinary SPA nav with **no carve-out** (Phase 19 D-04 carried forward). — **Reversibility:** reversible — adding a carve-out would need its own test and would reopen silent draft loss.
- **D-14:** **New Playwright journey**: dirty editor → in-page tab «Дайджест» → modal → «Остаться» keeps draft/URL; «Уйти без сохранения» lands on digest. — **Reversibility:** reversible.
- **D-15:** Modal **copy and actions unchanged** from Phase 19 («Есть несохранённые изменения. Уйти без сохранения?» / «Остаться» / «Уйти без сохранения»). — **Reversibility:** reversible.

### Narrow viewport
- **D-16:** On narrow viewports the tab-bar **collapses** (not always-row, not horizontal scroll). — **Reversibility:** reversible.
- **D-17:** Collapse control is a native **`<select>`** with options Дайджест / Пайплайн. — **Reversibility:** reversible.
- **D-18:** Breakpoint **`sm` (640px)** — underline `NavLink`s from `sm` up; `<select>` below. Phone administration is **not a target use case**; the select is a backstop only. — **Reversibility:** reversible.
- **D-19:** `<select>` `onChange` uses router **`navigate()`** so the Phase 19 guard still fires. — **Reversibility:** reversible.

### Claude's Discretion
None — every gray area was decided explicitly; no "you decide" leftovers.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 22 — goal, ADUX-12, four success criteria, tripwire disposition (`tests/admin.spec.js` nav assertions → **AMEND**), UI hint.
- `.planning/ROADMAP.md` § Backlog 999.5 — originating UAT option C (tab-bar; «Админ» → `/admin/digest`; route unchanged; amend 16-UI-SPEC A-2; TDD first).
- `.planning/REQUIREMENTS.md` — `ADUX-12` (one «Админ» entry + in-page «Дайджест | Пайплайн»; `/admin/pipeline` unchanged; no new route).
- `.planning/PROJECT.md` — v1.3 framing; backlog 999.5 promotion into Phase 22.
- `.planning/STATE.md` — current focus; Vite `:5174` flakiness blocker before full Playwright runs.

### Upstream UI contract to amend
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` § A-2 — currently mandates a second top-level «Пайплайн» AppShell item and "Do not add a second navigation bar"; **must be updated** so A-2 matches ADUX-12 (in-page tabs honour the no-second-bar rule).
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UAT.md` — deferred test 0 (option C) that this phase closes.

### Guard contract (must stay green)
- `.planning/phases/19-unsaved-changes-guard-for-the-pipeline-editor/19-CONTEXT.md` — D-01…D-04, D-12 (modal, no carve-out, dirty = `yaml !== savedYaml`).
- `web/src/hooks/useUnsavedChangesGuard.js` — boolean `useBlocker`.
- `web/src/components/UnsavedChangesDialog.jsx` — Phase 19 leave UI.

### Code to change / reuse
- `web/src/App.jsx` — flat `admin/digest`, `admin/pipeline`, `admin/materials/:id` under AppShell today; nest digest+pipeline under AdminLayout.
- `web/src/components/AppShell.jsx` — remove «Пайплайн» `NavLink`; «Админ» active on `/admin/*`, always `to="/admin/digest"`.
- `web/src/pages/AdminDigestPage.jsx` / `AdminPipelineConfigPage.jsx` — drop page H1 in favour of layout tabs (D-06); pages render as Outlet children.
- `tests/admin.spec.js` — tripwire `"pipeline config nav item renders only for admin"` / employee hidden assert top-level «Пайплайн» → **AMEND**; add tab-bar + dirty→tab journey (D-14).

### Rules
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — RED-first; no production code without a failing test first.
- `.cursor/rules/architecture.mdc` — frontend via `web/src/services/`; this phase is nav/layout only.

**No ADR governs this phase.**

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Data router already in place** (`createBrowserRouter` + `RouterProvider` in `App.jsx`) — nested AdminLayout routes need no second router migration.
- **Phase 19 guard trio** (`useUnsavedChangesGuard` + `UnsavedChangesDialog` + `armBeforeUnload`) — already wired on `AdminPipelineConfigPage`; tab/`navigate` leave paths reuse it unchanged (D-13, D-15, D-19).
- **AppShell `linkClass` / `NavLink` pattern** — shell stays pill-styled; in-page tabs deliberately use a different underline treatment (D-05).
- **AppShell `aria-label="Основная навигация"`** — parallel for admin section nav: `aria-label="Разделы админки"` (D-12).

### Established Patterns
- Admin routes today are **flat siblings** under RequireAuth+AppShell; nesting digest+pipeline is the structural change, materials preview stays sibling (D-03).
- Playwright already asserts **top-level «Пайплайн»** for admin and absence for employee — those tests become the RED tripwire when the shell link is removed.
- Comments in `tests/admin.spec.js` note digest-page scoping because shell has a global «Пайплайн» — amend those comments when the shell item is gone.
- Tailwind **`sm:` (640px)** is the project's established narrow breakpoint (AppShell nav wrap, digests, dialogs) — reuse for D-18.

### Integration Points
- `App.jsx` route tree → new `AdminLayout` element wrapping `admin/digest` + `admin/pipeline` children.
- `AppShell.jsx` → single «Админ» entry; active matching for `/admin/*`.
- New layout component (suggested under `web/src/components/`) owns underline tabs + narrow `<select>` + `<Outlet>`.
- `tests/admin.spec.js` → amend nav tripwires; add in-page tab presence; add dirty→tab modal journey (D-14).
- `16-UI-SPEC.md` A-2 → textual amend in the same phase (success criterion 3).

</code_context>

<specifics>
## Specific Ideas

- Variant **C** from Phase 16 UAT is the locked product shape: remove top-level «Пайплайн»; tab-bar on admin pages; «Админ» → `/admin/digest`; `/admin/pipeline` unchanged; no new route.
- Phone admin is **explicitly non-target** — do not invest in polished mobile chrome beyond the `sm` select backstop.
- Active tab visual weight should feel like the **former H1** (`text-3xl font-semibold`) so hierarchy is not lost when H1 is removed.
- Prefer **route semantics** (`nav` + `NavLink`) over ARIA tabs — switching sections changes the URL.

</specifics>

<deferred>
## Deferred Ideas

- **Materials-preview back-link** («← К шортлисту» → `/admin/digest`) — consciously skipped this phase (D-11); candidate for a later UX pass if preview navigation feels stranded.
- **Polished mobile-admin tab UX** (custom menu, larger hit targets, etc.) — out of scope while phone admin is non-target (D-18).
- **`/admin` index redirect** — rejected (D-04); revisit only if bookmarks to bare `/admin` become a real need.
- **ADUX-10 / ingest-sources on the Пайплайн tab** — Phase 23; AdminLayout must leave room for that content without redesigning the tab-bar.

</deferred>

---

*Phase: 22-admin-nav-grouping*
*Context gathered: 2026-10-17*
