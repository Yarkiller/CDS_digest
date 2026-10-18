# Phase 22: Admin nav grouping - Pattern Map

**Mapped:** 2026-10-17
**Files analyzed:** 7
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web/src/components/AdminLayout.jsx` | component (layout) | request-response | `web/src/components/AppShell.jsx` (+ eyebrow from admin pages) | role-match |
| `web/src/App.jsx` | config (route tree) | request-response | `web/src/App.jsx` (existing nested RequireAuth→AppShell) | exact |
| `web/src/components/AppShell.jsx` | component | request-response | `web/src/components/AppShell.jsx` (in-place) | exact |
| `web/src/pages/AdminDigestPage.jsx` | component (page) | request-response | `web/src/pages/AdminDigestPage.jsx` (eyebrow/H1 chrome) | exact |
| `web/src/pages/AdminPipelineConfigPage.jsx` | component (page) | request-response | `web/src/pages/AdminPipelineConfigPage.jsx` (eyebrow/H1 + guard) | exact |
| `tests/admin.spec.js` | test | request-response | `tests/admin.spec.js` (nav tripwires + dirty Archive journey) | exact |
| `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` | config (docs) | — | same file § A-2 + Route/nav | exact |

**Reuse unchanged (do not rewrite):** `web/src/hooks/useUnsavedChangesGuard.js`, `web/src/components/UnsavedChangesDialog.jsx`.

## Pattern Assignments

### `web/src/components/AdminLayout.jsx` (component/layout, request-response) — NEW

**Analog:** `web/src/components/AppShell.jsx` (Outlet + labelled `nav` + `NavLink`); eyebrow/chrome from admin pages; `navigate()` from `SearchPill.jsx`.

**Imports pattern** (AppShell lines 1–2; extend with navigate/location):
```jsx
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
```

**Outlet layout pattern** (AppShell lines 110–112 — child content under chrome):
```jsx
<main className="mx-auto max-w-6xl px-4 py-10">
  <Outlet />
</main>
```
AdminLayout sits *inside* that `<main>` Outlet; its own chrome wraps a nested `<Outlet />` only (no second `main`/`max-w-6xl`).

**Labelled section nav pattern** (AppShell lines 67–70 — parallel landmark, different label):
```jsx
<nav
  className="order-last flex w-full flex-wrap gap-1 sm:order-none sm:w-auto"
  aria-label="Основная навигация"
>
```
Copy the landmark idea; use `aria-label="Разделы админки"` + `data-testid="admin-section-nav"`. Do **not** reuse pill `linkClass`.

**Eyebrow pattern** (AdminDigestPage / AdminPipelineConfigPage — move into layout once):
```jsx
<p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
```

**H1 weight for active tab** (AdminPipelineConfigPage line 232 — tabs replace H1):
```jsx
<h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Конфиг пайплайна</h1>
```
Active tab: `text-3xl font-semibold text-ink border-b-2 border-accent`; inactive: `text-3xl font-normal text-muted` + `border-b-2 border-transparent`; each link `inline-flex min-h-11 items-end`.

**NavLink className callback** (AppShell lines 10–14 — adapt to underline, not pills):
```jsx
const linkClass = ({ isActive }) =>
  [
    'inline-flex min-h-11 items-center rounded-full px-3 text-sm',
    isActive ? 'bg-accent text-accent-ink' : 'text-ink-2 hover:bg-paper-2',
  ].join(' ')
```
In-page tabs must **not** use `rounded-full` / `bg-accent` fills (D-05).

**Guard-safe navigate** (SearchPill lines 4–7, 21–24):
```jsx
const navigate = useNavigate()
// …
navigate(q ? `/knowledge?q=${encodeURIComponent(q)}` : '/knowledge')
```
Narrow `<select onChange={(e) => navigate(e.target.value)}>` with hard-coded `/admin/digest` | `/admin/pipeline` only (D-19). Prefer `useLocation().pathname` for `value`.

**No analog for native `<select>` section switch** — first in codebase; follow 22-UI-SPEC classes: `min-h-11 w-full max-w-sm rounded-xl border border-rule bg-paper px-3 text-base text-ink`, `sm:hidden` vs `hidden sm:flex` on the nav row.

---

### `web/src/App.jsx` (config/route tree, request-response)

**Analog:** `web/src/App.jsx` — existing pathless parent wrapping children (RequireAuth → AppShell).

**Nested layout parent** (lines 20–40):
```jsx
{
  element: (
    <RequireAuth>
      <AppShell />
    </RequireAuth>
  ),
  children: [
    { index: true, element: <IssuePage isCurrent /> },
    // …
    { path: 'admin/digest', element: <AdminDigestPage /> },
    { path: 'admin/materials/:id', element: <MaterialPage preview /> },
    { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },
    { path: '*', element: <Navigate to="/" replace /> },
  ],
},
```

**Target nesting** (pathless AdminLayout; materials stays sibling — RESEARCH Pattern 1):
```jsx
import AdminLayout from './components/AdminLayout.jsx'
// inside RequireAuth → AppShell children:
{
  element: <AdminLayout />,
  children: [
    { path: 'admin/digest', element: <AdminDigestPage /> },
    { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },
  ],
},
{ path: 'admin/materials/:id', element: <MaterialPage preview /> },
```
Do **not** add `path: 'admin'` or an `/admin` index (D-04).

---

### `web/src/components/AppShell.jsx` (component, request-response)

**Analog:** same file — remove second pill; custom active for `/admin/*`.

**Admin-gated dual pills to change** (lines 86–95):
```jsx
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

**Keep:** `to="/admin/digest"`, `appRole === 'admin'` gate, pill `linkClass`, `aria-label="Основная навигация"`.

**Custom isActive** (RESEARCH Pattern 2 — add `useLocation`):
```jsx
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
const { pathname } = useLocation()
const adminActive = pathname === '/admin' || pathname.startsWith('/admin/')
<NavLink
  to="/admin/digest"
  className={() => linkClass({ isActive: adminActive })}
>
  Админ
</NavLink>
```
Default NavLink prefix match on `/admin/digest` does **not** light on `/admin/pipeline` or materials preview (Pitfall 1).

**Prefix-match reference** (same file line 71 — `end` for home only):
```jsx
<NavLink to="/" end className={linkClass}>
  Выпуск
</NavLink>
```
«Админ» must **not** use `end`; use explicit pathname check instead.

---

### `web/src/pages/AdminDigestPage.jsx` (page, request-response)

**Analog:** same file — strip duplicated eyebrow + H1 on every branch (D-06).

**Chrome to remove** (repeated on error/loading/ready — e.g. lines 485–486, 520–521):
```jsx
<p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
<h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Shortlist дайджеста</h1>
```

**Keep:** `data-testid="admin-digest-page"`, Forbidden/ServiceUnavailable branches, content `h2`s (e.g. «Кандидатов пока нет», «дайджест успешно выпущен»), triage/send UI.

**Empty-copy scoping note for tests** (admin.spec.js lines 137–140): page-scoped `/пайплайн/i` will fail once in-page tab «Пайплайн» exists — AMEND to exclude section nav / assert empty-state copy only.

---

### `web/src/pages/AdminPipelineConfigPage.jsx` (page, request-response)

**Analog:** same file — drop eyebrow/H1; keep hint + Phase 19 guard.

**Chrome to remove** (all ready/loading/error branches — e.g. lines 179–180, 231–232):
```jsx
<p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
<h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Конфиг пайплайна</h1>
```

**Keep hint** (line 233):
```jsx
<p className="mt-2 text-sm text-muted">Просмотр и правка без запуска пайплайна</p>
```

**Guard wiring unchanged** (lines 106–107, 339–343):
```jsx
const dirty = yaml !== savedYaml
const blocker = useUnsavedChangesGuard(dirty)
// …
<UnsavedChangesDialog
  open={blocker.state === 'blocked'}
  onStay={() => blocker.reset()}
  onLeave={() => blocker.proceed()}
/>
```
Tab/select leave needs **no** guard code changes (D-13).

---

### `tests/admin.spec.js` (test, request-response)

**Analog:** same file — shell nav scoping + dirty Archive journey.

**Preserve Админ shell contract** (lines 67–71):
```js
test("admin sees Админ nav linking to /admin/digest", async ({ page }) => {
  await gotoAsRole(page, "admin", "/");
  const adminLink = page.getByRole("link", { name: /^Админ$/ });
  await expect(adminLink).toBeVisible();
  await expect(adminLink).toHaveAttribute("href", "/admin/digest");
});
```

**Tripwire to AMEND** (lines 1371–1380):
```js
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
**Amend direction:** On `/`, shell `navigation` «Основная навигация» has **zero** «Пайплайн»; on `/admin/digest` as admin, section nav (`getByRole("navigation", { name: /разделы админки/i })` or `getByTestId("admin-section-nav")`) exposes «Пайплайн»; employee on `/` still zero. Prefer landmark/testid scoping (Pitfall 3).

**H1 asserts to AMEND** (lines 114–115, 997–998):
```js
page.getByRole("heading", { name: "Shortlist дайджеста", exact: true })
page.getByRole("heading", { name: "Конфиг пайплайна", exact: true })
```
Replace with active-tab / `admin-tab-*` / hint text asserts in the same RED wave.

**Dirty→tab journey template** (lines 1230–1284 — swap Архив for in-page «Дайджест»):
```js
const archive = page
  .getByRole("navigation", { name: /основная навигация/i })
  .getByRole("link", { name: /^Архив$/ });
await archive.click();
// dialog → stay / Escape / leave — same testids:
// unsaved-changes-message, unsaved-changes-stay, unsaved-changes-leave
```
New D-14 case: dirty editor → section nav «Дайджест» → modal → «Остаться» keeps `/admin/pipeline` + draft; «Уйти без сохранения» → digest. Copy byte-identical to Phase 19.

**Comments to update** (lines 137, 158): «AppShell now has a global «Пайплайн»» — stale after shell removal.

---

### `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` (docs)

**Analog:** same file — textual supersession only.

**A-2 to supersede** (line 28):
```text
| A-2 | **Route + nav placement:** … | **New admin route `/admin/pipeline`** …; a new `Админ`-gated nav item **«Пайплайн»** in `AppShell.jsx`. …
```

**Route/nav contract to supersede** (lines 188–191):
```text
- `AppShell.jsx` gains one `Админ`-gated nav item **«Пайплайн»** …
- … muted eyebrow «Админ», H1 «Конфиг пайплайна» …
```

Mark A-2 **superseded by ADUX-12 / Phase 22**; keep «Do not add a second navigation bar» true via in-page tabs. Point to `22-UI-SPEC.md`. Do not rewrite editor/toolbar contracts.

## Shared Patterns

### Nested layout + Outlet
**Source:** `web/src/App.jsx` + `web/src/components/AppShell.jsx`
**Apply to:** AdminLayout nesting under AppShell; digest/pipeline children only
```jsx
// Pathless parent (no path key) → children keep full relative paths
{ element: <AdminLayout />, children: [ /* admin/digest, admin/pipeline */ ] }
```

### Landmark-scoped navigation queries
**Source:** `tests/admin.spec.js` lines 1237–1239; AppShell `aria-label="Основная навигация"`
**Apply to:** All shell vs section-nav Playwright asserts
```js
page.getByRole("navigation", { name: /основная навигация/i })
page.getByRole("navigation", { name: /разделы админки/i }) // or getByTestId("admin-section-nav")
```

### Unsaved-leave guard (reuse only)
**Source:** `web/src/hooks/useUnsavedChangesGuard.js` + `UnsavedChangesDialog.jsx` + pipeline page wiring
**Apply to:** Tab NavLink + select `navigate()` — no carve-out
```jsx
const blocker = useUnsavedChangesGuard(dirty) // dirty = yaml !== savedYaml
<UnsavedChangesDialog
  open={blocker.state === 'blocked'}
  onStay={() => blocker.reset()}
  onLeave={() => blocker.proceed()}
/>
```

### Admin role gate in shell
**Source:** `web/src/components/AppShell.jsx` lines 86–95
**Apply to:** Single «Админ» pill only after change
```jsx
{appRole === 'admin' ? ( /* one NavLink */ ) : null}
```

### TDD / RED-first
**Source:** `.cursor/rules/tdd.mdc`, RESEARCH Validation Architecture
**Apply to:** Amend `tests/admin.spec.js` before AppShell/AdminLayout production edits

### Tailwind `sm:` breakpoint
**Source:** AppShell nav wrap (`sm:order-none sm:w-auto`); 22-UI-SPEC D-18
**Apply to:** `hidden sm:flex` tabs / `sm:hidden` select

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| Native `<select>` section switch in AdminLayout | interactive control | request-response | No existing SPA `<select>`+`navigate` chrome; invent from 22-UI-SPEC + `SearchPill` navigate pattern |
| Underline tab visual (`border-b-2 border-accent`) | style | — | AppShell uses pills only; copy weight from admin H1, underline treatment from UI-SPEC |

## Metadata

**Analog search scope:** `web/src/App.jsx`, `web/src/components/`, `web/src/pages/Admin*.jsx`, `web/src/hooks/useUnsavedChangesGuard.js`, `tests/admin.spec.js`, Phase 16 UI-SPEC
**Files scanned:** ~20 tracked frontend/test/doc files (git `ls-files` verified for all named analogs)
**Tracked-source gate:** all analog paths confirmed via `git ls-files` (non-empty)
**Pattern extraction date:** 2026-10-17
