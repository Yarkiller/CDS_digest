# Phase 22: Admin nav grouping - Research

**Researched:** 2026-10-17
**Domain:** React SPA navigation / nested layout routes (frontend-only)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
#### Tab-bar host
- **D-01:** Shared **AdminLayout** with tab-bar + `<Outlet>`; digest and pipeline are child routes. — **Reversibility:** costly — undoing means re-flattening routes and re-duplicating tabs on every admin page that needs them.
- **D-02:** AdminLayout is **nested inside AppShell** (RequireAuth → AppShell → AdminLayout → page). Top-level shell chrome stays; only the «Пайплайн» shell link is removed. — **Reversibility:** costly — layout nesting touches `App.jsx` and every admin child path.
- **D-03:** Only **`digest` + `pipeline`** sit under AdminLayout; `/admin/materials/:id` remains a **sibling** without the tab-bar. — **Reversibility:** reversible.
- **D-04:** **No `/admin` index redirect** — no new `/admin` route; entry is the shell «Админ» link → `/admin/digest`. — **Reversibility:** reversible.

#### Tab visual style
- **D-05:** **Underline tabs** (text + bottom border on active) — not AppShell pills — so the control reads as in-page section switch, honouring 16-UI-SPEC "no second navigation bar". — **Reversibility:** reversible.
- **D-06:** Tabs **replace** the page H1 (no duplicate display title above content). — **Reversibility:** reversible.
- **D-07:** Tab labels: **«Дайджест» | «Пайплайн»** (ROADMAP / ADUX-12 short forms). — **Reversibility:** reversible.
- **D-08:** Active tab is **display-size** (`text-3xl font-semibold`); inactive quieter. — **Reversibility:** reversible.

#### Nested admin routes
- **D-09:** AppShell «Админ» is **active on any `/admin/*`** (digest, pipeline, materials preview). — **Reversibility:** reversible — typically `NavLink` `className` / `isActive` matching, not `end`.
- **D-10:** Click «Админ» **always navigates to `/admin/digest`** (fixed entry; matches ROADMAP). — **Reversibility:** reversible.
- **D-11:** On `/admin/materials/:id` this phase does **nothing** beyond «Админ» highlight — no new back-link. — **Reversibility:** reversible.
- **D-12:** Tab-bar markup is **`nav aria-label="Разделы админки"` + `NavLink`**, not `role="tablist"` / tab / tabpanel — these are routes, not in-place tabs. — **Reversibility:** reversible.

#### Dirty pipeline guard
- **D-13:** Dirty YAML → click tab «Дайджест» fires the **Phase 19** `UnsavedChangesDialog`; tab navigation is ordinary SPA nav with **no carve-out** (Phase 19 D-04 carried forward). — **Reversibility:** reversible — adding a carve-out would need its own test and would reopen silent draft loss.
- **D-14:** **New Playwright journey**: dirty editor → in-page tab «Дайджест» → modal → «Остаться» keeps draft/URL; «Уйти без сохранения» lands on digest. — **Reversibility:** reversible.
- **D-15:** Modal **copy and actions unchanged** from Phase 19 («Есть несохранённые изменения. Уйти без сохранения?» / «Остаться» / «Уйти без сохранения»). — **Reversibility:** reversible.

#### Narrow viewport
- **D-16:** On narrow viewports the tab-bar **collapses** (not always-row, not horizontal scroll). — **Reversibility:** reversible.
- **D-17:** Collapse control is a native **`<select>`** with options Дайджест / Пайплайн. — **Reversibility:** reversible.
- **D-18:** Breakpoint **`sm` (640px)** — underline `NavLink`s from `sm` up; `<select>` below. Phone administration is **not a target use case**; the select is a backstop only. — **Reversibility:** reversible.
- **D-19:** `<select>` `onChange` uses router **`navigate()`** so the Phase 19 guard still fires. — **Reversibility:** reversible.

### Claude's Discretion
None — every gray area was decided explicitly; no "you decide" leftovers.

### Deferred Ideas (OUT OF SCOPE)
- **Materials-preview back-link** («← К шортлисту» → `/admin/digest`) — consciously skipped this phase (D-11); candidate for a later UX pass if preview navigation feels stranded.
- **Polished mobile-admin tab UX** (custom menu, larger hit targets, etc.) — out of scope while phone admin is non-target (D-18).
- **`/admin` index redirect** — rejected (D-04); revisit only if bookmarks to bare `/admin` become a real need.
- **ADUX-10 / ingest-sources on the Пайплайн tab** — Phase 23; AdminLayout must leave room for that content without redesigning the tab-bar.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADUX-12 | Pipeline config reached from admin area: one «Админ» → `/admin/digest` + in-page «Дайджест \| Пайплайн»; `/admin/pipeline` unchanged; no new route | Pathless nested layout + AppShell single entry + underline in-page `NavLink`s; tripwire AMEND for shell «Пайплайн» and H1 heading asserts; 16-UI-SPEC A-2 textual supersession |
</phase_requirements>

## Project Constraints (from AGENTS.md / architecture)

- **TDD mandatory:** NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST (Playwright RED for nav contract before AppShell/AdminLayout changes).
- **Ports & Adapters:** frontend-only phase; no backend/API/schema changes; SPA talks to APIs only via `web/src/services/` (unchanged this phase).
- **No new component kit / shadcn:** hand-rolled React + existing Tailwind token system (`22-UI-SPEC.md` locked).
- **Design system locked:** extend in place; do not invent tokens, icons, or motion.

## Summary

Phase 22 closes backlog 999.5 / ADUX-12 by regrouping admin navigation in the Vite React SPA. Today `App.jsx` mounts flat siblings `admin/digest`, `admin/pipeline`, and `admin/materials/:id` under `RequireAuth` → `AppShell`, and `AppShell` exposes two admin-gated pills («Админ» + «Пайплайн»). The locked shape is: remove the shell «Пайплайн» pill; keep a single «Админ» link that always goes to `/admin/digest` and lights active on any `/admin/*`; introduce a shared `AdminLayout` (eyebrow + underline section switch + `<Outlet>`) wrapping only digest and pipeline; leave materials preview as a sibling without tabs; amend Phase 16 UI-SPEC A-2 so it no longer mandates the second top-level item.

No new npm packages are required. Stack is already `react-router-dom@7.18.3` with a data router (`createBrowserRouter` + `RouterProvider`) from Phase 19 — nested layout routes need only a pathless parent route. Phase 19 `useUnsavedChangesGuard` / `UnsavedChangesDialog` already block ordinary SPA navigations; tab `NavLink` clicks and narrow-select `navigate()` reuse that contract without code changes to the guard itself.

**Primary recommendation:** RED-first amend `tests/admin.spec.js` (shell «Пайплайн» tripwires + H1 heading asserts + new tab/dirty→tab journeys), then add pathless `AdminLayout` children for digest/pipeline, custom AppShell `isActive` for `/admin/*`, drop duplicate page H1/eyebrow, and textually supersede `16-UI-SPEC` A-2 in the same phase.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Top-level «Админ» / remove «Пайплайн» | Browser / Client (`AppShell`) | — | Shell chrome only; role gate already in shell |
| In-page «Дайджест \| Пайплайн» section switch | Browser / Client (`AdminLayout`) | — | In-page content, not shell bar (honours no-second-nav-bar) |
| Route nesting / URL stability | Browser / Client (`App.jsx` router) | — | Pathless layout preserves `/admin/digest` and `/admin/pipeline` |
| Dirty leave on tab/select | Browser / Client (Phase 19 guard on pipeline page) | — | Existing `useBlocker`; no backend |
| Role gating of admin pages | Browser / Client (page-level Forbidden) | API / Backend (unchanged) | Server remains source of truth; phase does not touch API |
| 16-UI-SPEC A-2 amend | CDN / Static (planning docs) | — | Documentation contract update, not runtime |
| Playwright nav contract | Browser / Client (E2E) | — | RED-first behavioural proof |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-router-dom | 7.18.3 (installed; registry latest 7.18.4) | Data router, nested layouts, `NavLink`, `Outlet`, `useBlocker`, `navigate` | Already wired in `App.jsx`; Phase 19 guard depends on it `[VERIFIED: web/package.json + npm ls]` |
| react / react-dom | ^19.2.8 | UI | Existing SPA `[VERIFIED: web/package.json]` |
| Tailwind CSS | ^4.3.3 | Utility styling for underline tabs / select | Existing `@theme` tokens; `sm:` = 640px default `[VERIFIED: web/package.json]` |
| @playwright/test | ^1.62.1 (local CLI 1.62.1) | E2E nav + dirty→tab journeys | Existing `tests/admin.spec.js` `[VERIFIED: package.json + npx playwright --version]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Vite | ^8.2.2 | Dev server for Playwright web project on `:5174` | Existing; watch for flakiness blocker in STATE.md |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pathless layout wrapping digest+pipeline | `path: 'admin'` parent with nested children | Path prefix parent also works, but pathless matches locked D-01…D-04 with zero URL change and keeps materials as true sibling more obviously |
| Custom `isActive` on «Админ» | Point shell link at `/admin` with prefix match | Rejected — D-04 forbids `/admin` index; `to` must stay `/admin/digest` |
| ARIA `tablist` | Route `NavLink`s | Locked D-12 — URL is source of truth |

**Installation:** none — reuse installed packages. Do **not** `npm install` for this phase.

**Version verification:** `npm view react-router-dom version` → `7.18.4`; installed `7.18.3`. `@playwright/test` range `^1.62.1`; local CLI `1.62.1`.

## Package Legitimacy Audit

> This phase installs **no new external packages**. Audit of already-in-tree deps for planner awareness:

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| react-router-dom | npm | mature | ~45M/wk | github.com/remix-run/react-router | OK | Already installed — Approved |
| @playwright/test | npm | mature (registry “too-new” signal on latest publish) | ~76M/wk | github.com/microsoft/playwright | SUS (too-new) | Already installed — **do not reinstall**; no checkpoint needed for reuse |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** `@playwright/test` latest publish flagged too-new by seam — **not installing this phase**; keep pinned workspace version.

## Architecture Patterns

### System Architecture Diagram

```text
[Browser URL]
     │
     ▼
RequireAuth
     │
     ▼
AppShell ── nav «Основная навигация»
     │         └─ «Админ» → /admin/digest  (active if pathname starts with /admin)
     │         └─ (removed) «Пайплайн»
     │
     ▼
<main><Outlet/></main>
     │
     ├── pathless AdminLayout ── eyebrow «Админ»
     │         │                 nav/select «Разделы админки»
     │         │                   ├─ NavLink «Дайджест» → /admin/digest
     │         │                   └─ NavLink «Пайплайн» → /admin/pipeline
     │         └── <Outlet/>
     │               ├─ AdminDigestPage
     │               └─ AdminPipelineConfigPage
     │                     └─ useUnsavedChangesGuard(dirty)
     │                           └─ UnsavedChangesDialog (on tab/select leave)
     │
     └── sibling admin/materials/:id → MaterialPage(preview)
           (no AdminLayout; shell «Админ» still active)
```

### Recommended Project Structure

```text
web/src/
├── App.jsx                          # nest digest+pipeline under AdminLayout
├── components/
│   ├── AppShell.jsx                 # remove Пайплайн; custom isActive for /admin/*
│   ├── AdminLayout.jsx              # NEW — eyebrow + tabs/select + Outlet
│   └── UnsavedChangesDialog.jsx     # reuse unchanged
├── hooks/useUnsavedChangesGuard.js  # reuse unchanged
└── pages/
    ├── AdminDigestPage.jsx          # drop H1 + duplicate eyebrow
    └── AdminPipelineConfigPage.jsx  # drop H1 + duplicate eyebrow; keep hint + guard
tests/
└── admin.spec.js                    # AMEND tripwires; add tab + dirty→tab journeys
.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/
└── 16-UI-SPEC.md                    # supersede A-2 + Route/nav contract text
```

### Pattern 1: Pathless layout route (digest + pipeline only)
**What:** Parent route with `element: <AdminLayout />` and **no `path`**, children keep full relative paths `admin/digest` and `admin/pipeline`.
**When to use:** Need shared chrome without adding a URL segment and without creating `/admin` index (D-04).
**Example:**
```jsx
// Source: Context7 /remix-run/react-router — pathless layout routes
// Current flat siblings [VERIFIED: web/src/App.jsx:36-38]:
//   { path: 'admin/digest', element: <AdminDigestPage /> },
//   { path: 'admin/materials/:id', element: <MaterialPage preview /> },
//   { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },

{
  element: <AdminLayout />,
  children: [
    { path: 'admin/digest', element: <AdminDigestPage /> },
    { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },
  ],
},
{ path: 'admin/materials/:id', element: <MaterialPage preview /> },
```

### Pattern 2: Custom shell active match for `/admin/*`
**What:** `NavLink to="/admin/digest"` does **not** auto-activate on `/admin/pipeline` (prefix match requires descendant under `/admin/digest/…`).
**When to use:** D-09 — light «Админ» on digest, pipeline, and materials preview.
**Example:**
```jsx
// Source: Context7 NavLink isActive determination (pathname prefix under `to`)
// Default linkClass today [VERIFIED: web/src/components/AppShell.jsx:10-14]
const adminLinkClass = ({ isActive }) =>
  linkClass({
    isActive:
      isActive ||
      (typeof window !== 'undefined' &&
        false) /* prefer useLocation in component */,
  })

// Prefer inside AppShell:
import { NavLink, useLocation } from 'react-router-dom'
const { pathname } = useLocation()
const adminActive = pathname === '/admin' || pathname.startsWith('/admin/')
<NavLink
  to="/admin/digest"
  className={() => linkClass({ isActive: adminActive })}
>
  Админ
</NavLink>
```

### Pattern 3: Narrow select uses `navigate()` (guard-safe)
**What:** `<select onChange={(e) => navigate(e.target.value)}>` with values `/admin/digest` | `/admin/pipeline`.
**When to use:** D-17…D-19 below `sm`.
**Why:** Same SPA history transition as `NavLink` → `useBlocker` fires.

### Anti-Patterns to Avoid
- **Second AppShell pill for «Пайплайн»:** directly violates ADUX-12 / success criterion 1.
- **`role="tablist"` on section switch:** locked out by D-12; use `nav` + links.
- **Adding `/admin` index or redirect:** locked out by D-04.
- **Pill / `bg-accent` fills on in-page tabs:** reads as second nav bar; use underline only (D-05).
- **Keeping page H1 «Shortlist дайджеста» / «Конфиг пайплайна» under layout:** duplicates hierarchy (D-06); also breaks existing Playwright heading asserts until amended.
- **Carve-out for dirty→tab navigation:** silent draft loss; Phase 19 D-04 / D-13 forbid it.
- **Backend or `pipelineConfigApi` changes:** out of scope.
- **Wrapping materials preview in AdminLayout:** D-03 forbids tab-bar there.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Nested admin chrome | Duplicate tabs on each page | Pathless `AdminLayout` + `<Outlet>` | Single source; Phase 23 can grow under Пайплайн |
| SPA leave guard | Custom `beforeunload` / history hacks for tabs | Existing `useUnsavedChangesGuard` + dialog | Already proven against shell «Архив» nav |
| Active shell match | Manual CSS class toggles via effects | `useLocation` + `NavLink` className callback | Router owns location truth |
| Responsive section switch | Custom drawer / horizontal scroll | Native `<select>` below `sm` | Phone admin non-target; D-17 |
| Component kit for tabs | shadcn Tabs / Headless UI | Hand-rolled underline `NavLink`s | UI-SPEC Tool: none |

**Key insight:** This phase is a **route-tree + chrome** change. The expensive mistakes are wrong nesting (URL drift, materials under tabs) and forgetting that default `NavLink` matching will leave «Админ» inactive on `/admin/pipeline`.

## Runtime State Inventory

> Structural route regrouping — light inventory.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no DB keys or collections named for shell nav labels | none |
| Live service config | None — nav is client-only | none |
| OS-registered state | None | none |
| Secrets/env vars | None — no env keys for nav labels | none |
| Build artifacts | Vite/Playwright caches may hold old bundle until refresh | Kill stale `:5174` before full suite (STATE blocker); no rename of packages |

**Nothing found in category:** Stored data / live service / OS / secrets — verified by phase scope (frontend nav only) and codebase review of change surface.

## Common Pitfalls

### Pitfall 1: Assuming `to="/admin/digest"` lights active on `/admin/pipeline`
**What goes wrong:** Shell «Админ» looks inactive on pipeline and materials preview.
**Why it happens:** RR `NavLink` prefix match only activates descendants under the `to` pathname, not siblings under `/admin`.
**How to avoid:** Custom `isActive` via `useLocation().pathname.startsWith('/admin')` (D-09).
**Warning signs:** Visual regression on `/admin/pipeline` and `/admin/materials/:id`.

### Pitfall 2: H1 removal breaks existing Playwright heading asserts
**What goes wrong:** Suite red for reasons unrelated to shell «Пайплайн» tripwire.
**Why it happens:** Tests assert `getByRole("heading", { name: "Shortlist дайджеста" })` and `"Конфиг пайплайна"` `[VERIFIED: tests/admin.spec.js:114-115]` / `[VERIFIED: tests/admin.spec.js:997-998]`.
**How to avoid:** AMEND those asserts in the same RED wave — assert active tab / `data-testid` / remaining hint text instead.
**Warning signs:** Failures mentioning missing headings after D-06.

### Pitfall 3: `getByRole("link", { name: "Пайплайн", exact: true })` becomes ambiguous
**What goes wrong:** After move, in-page tab is still a link named «Пайплайн»; tests that only checked count/visibility can pass for the wrong landmark.
**Why it happens:** Name-only queries ignore shell vs section nav.
**How to avoid:** Scope queries: shell via `navigation` name «Основная навигация»; section via `admin-section-nav` / «Разделы админки».
**Warning signs:** False greens after shell removal.

### Pitfall 4: Select uses `window.location` or `<a>` assignment
**What goes wrong:** Full document navigation bypasses `useBlocker` or double-prompts with `beforeunload`.
**Why it happens:** Native select habit.
**How to avoid:** `navigate(path)` only (D-19).
**Warning signs:** Dirty→select leave does not open `UnsavedChangesDialog`.

### Pitfall 5: Pathful `/admin` parent accidentally creates index behaviour
**What goes wrong:** Visiting `/admin` 404s or falls through to `*` → `/`, confusing bookmarks.
**Why it happens:** Adding `path: 'admin'` without index child.
**How to avoid:** Prefer pathless layout (Pattern 1); never add `/admin` index (D-04).

### Pitfall 6: Employee deep-link shows AdminLayout tabs
**What goes wrong:** Authenticated employee on `/admin/digest` sees section tabs above ForbiddenPage.
**Why it happens:** Role gate is page-level; layout wraps outlet (accepted by 22-UI-SPEC).
**How to avoid:** Do not invent hide-tabs carve-out this phase; ensure employee tests still pass (they assert shortlist absence, not absence of all chrome).
**Warning signs:** New a11y complaints — defer unless tests fail.

### Pitfall 7: Vite `:5174` flakiness masquerades as nav regressions
**What goes wrong:** Mass `ERR_CONNECTION_REFUSED` on Playwright web project.
**Why it happens:** Stale Vite reuse fight (STATE.md blocker).
**How to avoid:** Check/kill listener on 5174 before full suite; re-run clean.
**Warning signs:** Connection refused, not assertion mismatch.

## Code Examples

### Current AppShell admin pills (to change)
```jsx
// [VERIFIED: web/src/components/AppShell.jsx:86-94]
{appRole === 'admin' ? (
  <>
    <NavLink to="/admin/digest" className={linkClass}>
      Админ
    </NavLink>
    <NavLink to="/admin/pipeline" className={linkClass}>
      Пайплайн
    </NavLink>
  </>
) : null}
```

### AdminLayout skeleton (target)
```jsx
// Source: 22-UI-SPEC AdminLayout contract + Context7 Outlet
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

export default function AdminLayout() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
      <nav
        className="mt-2 hidden gap-2 border-b border-rule sm:flex"
        aria-label="Разделы админки"
        data-testid="admin-section-nav"
      >
        <NavLink to="/admin/digest" data-testid="admin-tab-digest" className={tabClass}>
          Дайджест
        </NavLink>
        <NavLink to="/admin/pipeline" data-testid="admin-tab-pipeline" className={tabClass}>
          Пайплайн
        </NavLink>
      </nav>
      <select
        className="mt-2 min-h-11 w-full max-w-sm sm:hidden …"
        aria-label="Разделы админки"
        data-testid="admin-section-select"
        value={pathname.startsWith('/admin/pipeline') ? '/admin/pipeline' : '/admin/digest'}
        onChange={(e) => navigate(e.target.value)}
      >
        <option value="/admin/digest">Дайджест</option>
        <option value="/admin/pipeline">Пайплайн</option>
      </select>
      <div className="mt-6">
        <Outlet />
      </div>
    </div>
  )
}
```

### Tripwire tests to AMEND (RED first)
```js
// [VERIFIED: tests/admin.spec.js:1371-1380]
test("pipeline config nav item renders only for admin", async ({ page }) => {
  await gotoAsRole(page, "admin", "/");
  const link = page.getByRole("link", { name: "Пайплайн", exact: true });
  await expect(link).toBeVisible();
  await expect(link).toHaveAttribute("href", "/admin/pipeline");
});

test("pipeline config nav item hidden for employee", async ({ page }) => {
  await gotoAsRole(page, "employee", "/");
  await expect(page.getByRole("link", { name: "Пайплайн", exact: true })).toHaveCount(0);
});
```

**Amend direction (planner):** On `/`, shell must have **zero** «Пайплайн» links; on `/admin/digest` as admin, section nav exposes «Пайплайн»; employee on `/` still zero. Add dirty→tab journey mirroring existing Archive leave tests at `[VERIFIED: tests/admin.spec.js:1230-1284]` but click in-page «Дайджест» instead of «Архив».

### 16-UI-SPEC A-2 supersession target
```text
Was [VERIFIED: .planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md:28]:
  New admin route /admin/pipeline + AppShell item «Пайплайн»

Becomes (Phase 22):
  Route /admin/pipeline retained; AppShell only «Админ» → /admin/digest;
  in-page underline tabs inside AdminLayout; mark A-2 superseded by ADUX-12 / Phase 22.
  «Do not add a second navigation bar» remains true — tabs are in-page content.
```

Also update Route/nav contract at `[VERIFIED: 16-UI-SPEC.md:188-191]` which still mandates the shell «Пайплайн» pill.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat admin routes + two shell pills | Pathless AdminLayout + one shell entry + in-page section nav | Phase 22 (ADUX-12) | Matches UAT option C; closes 999.5 |
| Declarative `<Routes>` tree | `createBrowserRouter` data router | Phase 19 | Nested layouts + `useBlocker` already available |

**Deprecated/outdated:**
- Phase 16 assumption A-2 “second top-level «Пайплайн»” — superseded by ADUX-12 (amend in-phase).
- Page-level H1 as sole admin section title on digest/pipeline — replaced by active tab weight (D-06/D-08).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Tailwind default `sm` breakpoint remains 640px in this project's `@theme` (no custom override found in `web/src/index.css`) | Narrow viewport / D-18 | Select/tabs swap at wrong width — confirm visually once |
| A2 | Employee seeing AdminLayout tabs on Forbidden deep-link is acceptable without further product review | Pitfall 6 | Extra a11y/copy task if rejected later |

**If this table is empty:** N/A — two low-risk assumptions logged.

## Open Questions (RESOLVED)

1. **Should H1-asserting Playwright tests be amended in the same plan wave as shell tripwires?**
   - What we know: D-06 removes headings that tests currently require.
   - What's unclear: plan wave split vs single RED commit.
   - Recommendation: same wave — otherwise intermediate commits cannot be green.
   - **RESOLVED:** Same plan wave — `22-01` amends H1 asserts and shell tripwires together (RED first in Tasks 1–2). Split waves would leave intermediate commits red.

2. **Optional narrow-select dirty journey?**
   - What we know: D-14 requires tab journey; UI-SPEC says optionally mirror select.
   - What's unclear: whether select path is must-have for phase gate.
   - Recommendation: implement select `navigate()`; add select dirty assertion only if cheap after tab journey is green.
   - **RESOLVED:** Select `navigate()` is in scope (`22-01` AdminLayout). Select dirty Playwright assertion is optional after the tab journey; `22-02` covers the dirty→tab stay/leave journey as the phase gate — select dirty is not required for phase gate.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite / Playwright | ✓ | v24.21.0 | — |
| npm | web scripts | ✓ | (workspace) | — |
| react-router-dom | nested layouts / blocker | ✓ | 7.18.3 installed | — |
| Playwright | E2E RED/GREEN | ✓ | 1.62.1 CLI | — |
| Vite `:5174` | Playwright web project | ⚠ flaky | Vite 8.x | Kill stale listeners before suite |

**Missing dependencies with no fallback:** none

**Missing dependencies with fallback:** Vite port fights — operational procedure in STATE.md, not a package install.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | @playwright/test ^1.62.1 |
| Config file | `playwright.config.js` (web project → Vite `:5174`, `VITE_USE_MOCKS=true`) |
| Quick run command | `npx playwright test tests/admin.spec.js --project=web -g "pipeline config nav\|Админ nav\|dirty editor blocks\|Дайджест"` |
| Full suite command | `npx playwright test --project=web` (after confirming no stale `:5174`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADUX-12 | Exactly one shell «Админ»; no shell «Пайплайн» | e2e | `npx playwright test tests/admin.spec.js --project=web -g "pipeline config nav\|Админ nav"` | ✅ tripwire exists — **AMEND** |
| ADUX-12 | In-page «Дайджест \| Пайплайн» on admin digest/pipeline | e2e | same file, new cases | ❌ Wave 0 |
| ADUX-12 | `/admin/pipeline` still resolves; no new route | e2e | existing pipeline happy path + new tab click | ✅ path coverage / ❌ tab click |
| ADUX-12 | Dirty→tab «Дайджест» opens Phase 19 dialog | e2e | new journey (D-14) | ❌ Wave 0 |
| ADUX-12 | 16-UI-SPEC A-2 amended | docs check | manual/plan verify file diff | ❌ Wave 0 (doc task) |
| ADUX-09 carry | Guard still blocks shell «Архив» leave | e2e | existing dirty Archive tests | ✅ keep green |

### Sampling Rate
- **Per task commit:** targeted `admin.spec.js` grep above
- **Per wave merge:** `npx playwright test --project=web`
- **Phase gate:** Full web suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Amend `tests/admin.spec.js` shell «Пайплайн» tripwires (admin presence / employee absence) — scope to landmarks
- [ ] Amend heading asserts for «Shortlist дайджеста» / «Конфиг пайплайна» (D-06 fallout)
- [ ] Add in-page section-nav presence + active-tab assertions (`admin-section-nav` / tab testids)
- [ ] Add dirty→tab «Дайджест» stay/leave journey (D-14)
- [ ] Update comments at lines ~137 / ~158 that claim shell has global «Пайплайн»
- [ ] Doc task: supersede `16-UI-SPEC` A-2 + Route/nav section (may be non-test Wave 0 sibling)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (indirect) | Existing `RequireAuth` — unchanged |
| V3 Session Management | no | — |
| V4 Access Control | yes | Shell links still `appRole === 'admin'`; page-level Forbidden for deep-links; API admin gates unchanged |
| V5 Input Validation | yes (light) | Narrow `<select>` values whitelist only `/admin/digest` and `/admin/pipeline` — no free-form path |
| V6 Cryptography | no | — |

### Known Threat Patterns for SPA nav regrouping

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Employee discovers admin section labels via deep-link layout | Information disclosure | Accepted this phase (UI-SPEC); pages still Forbidden; no new data |
| Open redirect via select navigate | Spoofing | Hard-coded option values only |
| Privilege escalation via client nav | Elevation | Impossible via chrome alone — server `require_admin` unchanged |
| Lost dirty draft via silent nav | Tampering / integrity | Phase 19 `useBlocker` — no carve-out (D-13) |

## Sources

### Primary (HIGH confidence)
- Repo source: `web/src/App.jsx`, `web/src/components/AppShell.jsx`, `web/src/hooks/useUnsavedChangesGuard.js`, `web/src/pages/AdminDigestPage.jsx`, `web/src/pages/AdminPipelineConfigPage.jsx`, `tests/admin.spec.js`, `16-UI-SPEC.md` A-2
- `22-CONTEXT.md`, `22-UI-SPEC.md` (approved), `REQUIREMENTS.md` ADUX-12
- Context7 `/remix-run/react-router` — nested/pathless layouts, Outlet, NavLink isActive, useBlocker

### Secondary (MEDIUM confidence)
- `npm view` / `npm ls` version checks for react-router-dom and Playwright
- gsd `package-legitimacy check` on existing deps
- STATE.md Vite `:5174` operational blocker

### Tertiary (LOW confidence)
- Assumption A1 (Tailwind `sm` = 640px with no project override)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; versions verified in workspace
- Architecture: HIGH — locked CONTEXT + existing data router; Context7 confirms pathless layout + NavLink matching pitfall
- Pitfalls: HIGH — tripwires and H1 asserts read from live tests this session

**Research date:** 2026-10-17
**Valid until:** 2026-11-16 (30 days — stable SPA nav patterns)
