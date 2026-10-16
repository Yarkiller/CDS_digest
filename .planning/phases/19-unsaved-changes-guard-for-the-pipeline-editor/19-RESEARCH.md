# Phase 19: Unsaved-changes guard for the pipeline editor - Research

**Researched:** 2026-10-16
**Domain:** Frontend-only React 19 / react-router-dom 7 data-router behaviour (brownfield debt close-out, **zero new packages**)
**Confidence:** HIGH (framework contracts + the in-repo surfaces, all read this session) / MEDIUM (browser-owned `beforeunload` behaviour, verified against MDN + Playwright docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**In-app prompt surface**
- **D-01:** The in-app (SPA) leave confirmation is a **custom in-app modal**, not `window.confirm`. The copy «Есть несохранённые изменения. Уйти без сохранения?» lives in the modal body — the in-app guard is the only surface where the Russian copy can be shown at all (the reload/close prompt text is browser-owned, see D-06). — **Reversibility:** reversible — presentational; the blocker logic is unchanged if the surface is later swapped.
- **D-02:** The modal **repeats the project's existing modal pattern** (`AdminDigestPage`): full-screen overlay (`fixed inset-0` + `bg-ink/40`) with `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and explicit buttons. It additionally handles **Esc = «Остаться»** (the safe action). No focus trap, no auto-focus, and no focus restore — those do not exist in any current project modal and are deliberately not introduced here. — **Reversibility:** reversible.

**Leave actions**
- **D-03:** The modal offers **two actions only**: «Уйти без сохранения» (calls `blocker.proceed()`) and «Остаться» (calls `blocker.reset()`, keeping the draft). No «Сохранить и выйти». — **Reversibility:** reversible.
- **D-04:** While dirty, the guard blocks **every** navigation — including the `RequireAuth` 401 → `/login?returnUrl=…` redirect — with **no exceptions**: one blocker predicate, no pathname-based carve-out. Rationale: the typed draft is never lost silently; on session expiry the admin first sees the modal and only leaves for `/login` after explicitly choosing «Уйти без сохранения». This is `useBlocker`'s default behaviour and needs no extra code. — **Reversibility:** reversible — one predicate in the blocker (adding an exemption later is a local edit), though it would then need its own test.

**Reload/close backstop**
- **D-05:** Reload/close is covered by a **correct `beforeunload` handler only** — it does exactly `event.preventDefault()` and a **truthy** `event.returnValue`, is attached **only while dirty**, and is removed on unmount and after a successful save. It contains **no** `window.confirm`/`alert`. No `sessionStorage` draft recovery is added. — **Reversibility:** reversible.
- **D-06:** The native reload/close prompt text is **browser-owned and cannot be customized**; the shipped handler shows no app copy there. This is the honest end state, not a defect (custom copy is impossible inside `beforeunload`). — **Reversibility:** reversible.

**Guard packaging**
- **D-07:** *(Claude's Discretion — user deferred to Claude)* The guard is packaged as a **reusable hook + dialog component** rather than page-local logic (e.g. a `useUnsavedChangesGuard`-style hook plus an `UnsavedChangesDialog` component under `web/src/`), so the guard is armed identically on the editor today and on the ingest-sources editor in Phase 23. Rationale: `ADUX-10` already obliges Phase 23 to reuse this guard; a page-local copy would silently drift from it (copy string, blocker semantics, handler contract). — **Reversibility:** costly — re-inlining later means re-splitting the copy/behaviour across two editors and re-pinning both test surfaces.
- **D-08:** The **reset-to-saved confirm stays `window.confirm`** with its existing copy «Отменить изменения и вернуть последнюю сохраненную версию?» (16-UI-SPEC D-12); the two existing reset Playwright tests are **not** amended. Mixing one modal and one `window.confirm` on the same page is accepted — that matches the rest of the project. — **Reversibility:** reversible.

**Carried forward — locked by ROADMAP / Phase 16, not re-decided here**
- **D-09:** `web/src/App.jsx` is migrated from declarative `<BrowserRouter>` to a data router (`createBrowserRouter` + `RouterProvider`) **as its own behaviour-preserving plan**, gated by the **full Playwright suite green before the guard is wired**. The migration and the guard are **never combined in one plan** — a `useBlocker` throw would otherwise be misattributed to the migration. Every route is an at-risk regression surface, in particular the auth-gated parent route (`RequireAuth` + `AppShell`), the `admin/materials/:id` preview route (Phase 18), and the `*` → `/` catch-all. (ROADMAP criterion 4; PITFALLS Pitfall 4.) — **Reversibility:** costly — the router object replaces the JSX route tree and changes how `RequireAuth`/`AppShell` wrap children; reverting touches `App.jsx` and the shell/layout wiring.
- **D-10:** Tripwire `tests/admin.spec.js` → `"pipeline config dirty gating arms the unsaved-leave guard"` → **AMEND** (never delete). The amended test asserts the **handler contract** (registered only when dirty, sets the flag, removed on unmount and after a successful save) instead of asserting a `dialog`/`defaultPrevented` after a **synthetic** `beforeunload`. No test may keep asserting that a dialog appears during `beforeunload` — that assertion is the bug's alibi.
- **D-11:** **`ADUX-10` is NOT owned here.** The guard covering the ingest-sources editor ships in **Phase 23**; the ROADMAP records this gap as deliberate. Phase 19 only has to make the guard *extractable* for that reuse (D-07).
- **D-12:** The dirty contract is **locked**: `dirty === yaml !== savedYaml`; it clears on a successful save, stays armed after a server reject (`INVALID_CONFIG`) or a save failure, prompts on neither path when clean, and the two mechanisms must never **double-prompt** (the modal owns the message; the beforeunload handler shows no app copy).

### Claude's Discretion

- **Guard packaging** — user deferred; resolved as **reusable hook + dialog component** (CONTEXT D-07), justified by the planned Phase 23 consumer (`ADUX-10`).
- *(Packaging sub-choices not asked: where the hook/component files live, the exact modal markup/classes, the blocker wiring details — all left to the planner/executor within D-01…D-08.)*

### Deferred Ideas (OUT OF SCOPE)

- **«Сохранить и выйти» (save-then-navigate) as a third modal action** — deliberately not shipped in Phase 19. It adds a new failure path (an async save that fails or is rejected must prevent the navigation) and is not required by `ADUX-09`. Candidate backlog item for `/gsd-review-backlog`.
- **`sessionStorage` draft recovery** — persisting the in-progress YAML so even a *confirmed* reload/close does not lose the typed text. This is a new capability (draft storage), not a guard, and is outside `ADUX-09`. Candidate backlog item.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADUX-09 | The admin pipeline editor warns before losing unsaved changes on in-app SPA navigation **and** on reload/close, using the existing Russian copy; no warning when clean; the dirty flag clears after a successful save and stays armed after a server reject | In-app path: `useBlocker` under the migrated data router (§Pattern 1/2, §Code Examples) + `UnsavedChangesDialog` (§Pattern 3). Reload/close path: the two-statement `armBeforeUnload` contract (§Pattern 4). Dirty signal already exists and is correct (`AdminPipelineConfigPage.jsx:107`) — the guard consumes it, never re-derives it (§Anti-Patterns A1). Gate: amended tripwire + 4 new Playwright journeys (§Validation Architecture) |
</phase_requirements>

## Project Constraints (from CLAUDE.md / AGENTS.md / .cursor/rules)

`./CLAUDE.md` and `./.claude/CLAUDE.md` **do not exist** in this repo (`Test-Path` → `False`, both paths, checked this session). The binding directives therefore come from `AGENTS.md` (loaded at workspace level) and `.cursor/rules/`:

| Directive | Source | Effect on this phase |
|---|---|---|
| `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST` | `AGENTS.md`, `.cursor/rules/tdd.mdc` | A failing automated test must exist before the handler fix, the hook, the dialog, and the page wiring. The **router migration is the one carve-out**: it is a behaviour-preserving refactor, so its gate is the *existing* Playwright suite (green → refactor → green), not a new RED test. Never write a fake RED for it. |
| Tests assert behaviour, not mocks | `AGENTS.md` | The amended tripwire must assert the handler **contract** via a real browser prompt, not a synthetic-event dialog assertion. |
| Frontend reaches the backend only through `web/src/services/`; UI owns no business rules | `.cursor/rules/architecture.mdc` | This phase adds **no** service call, no port, no backend surface. The guard is pure presentation/navigation state. |
| Ports & Adapters, inward dependencies | `.cursor/rules/architecture.mdc` | Not engaged — no domain/application/infrastructure layer is touched. |
| Use Context7 for library/API docs | `.cursor/rules/context7.mdc` | Satisfied — every react-router-dom claim below came from Context7 (`/remix-run/react-router`) plus a read of the installed package bits. |
| Exceptions to TDD (configs, generated files, throwaway prototypes) need explicit agreement | `.cursor/rules/tdd.mdc` | Do **not** self-authorise the migration carve-out; record it in the plan as the stated exception. |

## Summary

This phase closes backlog 999.6 (`WR-04` + `WR-05`) entirely inside `web/`. Two mechanisms are required because neither alone is sufficient: `useBlocker` covers **in-app** navigation and explicitly does **not** cover hard reloads or cross-origin navigation; `beforeunload` covers reload/close/tab and cannot show app copy. `ADUX-09` needs both, so both ship.

Five findings drive how the plan must be shaped.

**1. The dirty signal is already correct — the guard must consume it, not rebuild it.** `const dirty = yaml !== savedYaml` `[VERIFIED: web/src/pages/AdminPipelineConfigPage.jsx:107]` is the single source of truth; `onSave`'s success branch sets `setSavedYaml(saved)`, and the `INVALID_CONFIG` reject branch deliberately leaves `savedYaml` untouched so the document stays dirty. Both halves of D-12 are therefore already implemented and only need to be *observed* by the guard. A second "touched" flag would be a new bug source (PITFALLS Pitfall 5a/5b).

**2. The shipped `beforeunload` effect is broken in a way a green test cannot see.** It gates `preventDefault()` behind `!window.confirm(UNSAVED_LEAVE_CONFIRM)` `[VERIFIED: web/src/pages/AdminPipelineConfigPage.jsx:109-121]`, and `tests/admin.spec.js:1143-1171` dispatches a **synthetic** `beforeunload`, asserts `defaultPrevented === true`, and asserts a `dialog` carrying the Russian copy. It passes only because Playwright auto-dismisses the dialog → `window.confirm` returns `false` → the branch runs. In a real browser the prompt text is browser-owned and required prior user interaction, so the assertion proves nothing. The corrected handler is exactly two statements and nothing else.

**3. `useBlocker` is unusable on today's router, and the migration is genuinely separable.** Context7 confirms at source level that `useBlocker` calls `useDataRouterContext("useBlocker")` and throws when `DataRouterContext` is absent, and that declarative `<BrowserRouter>` provides only Navigation/Location context. Today's `App.jsx` is declarative `[VERIFIED: web/src/App.jsx:17-19,45]`. The migration is a pure refactor with an existing, broad Playwright contract, so it belongs in its own plan gated by the whole suite (D-09).

**4. The data router is the *correct* import surface already installed — no dependency change, and one doc-driven trap to avoid.** `react-router-dom` 7.18.3 re-exports the **flushSync-wired** `RouterProvider` from `react-router/dom` `[VERIFIED: web/node_modules/react-router-dom/dist/index.mjs:13-18]`, so the migration can keep every import on `react-router-dom` (consistent with the rest of `web/src`). The v7 upgrade guide's advice to "import `RouterProvider` from `react-router/dom`" is aimed at callers importing from `react-router`; following it here would be a needless divergence, not a fix.

**5. The reload/close half *is* testable for real, and that is what replaces the alibi.** Playwright exposes a genuine `beforeunload` prompt via `page.close({ runBeforeUnload: true })` plus a `page.on('dialog')` handler, and MDN requires **sticky activation** before the browser will show it — so the test must perform a real interaction first or the negative ("clean editor") case is vacuous. This converts the tripwire from a synthetic-event assertion into a browser-level contract proof.

**Primary recommendation:** Ship **two plans**. Plan 1: migrate `App.jsx` to `createBrowserRouter` + `RouterProvider` with a module-scope router, behaviour-preserving, gated by the full Playwright suite green (baseline recorded before, count asserted after). Plan 2: add a node-testable two-statement `armBeforeUnload` helper, a `useUnsavedChangesGuard(dirty)` hook (boolean-form `useBlocker(dirty)` + dirty-scoped `beforeunload` effect), and an `UnsavedChangesDialog` that reuses the `AdminDigestPage` modal markup; wire them into `AdminPipelineConfigPage` **above its early returns**; amend the tripwire to the real-browser contract; and add four Playwright journeys (block→stay, block→leave-once, save→no-prompt, reject→still-prompt).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| In-app navigation interception | Browser / Client (router) | — | `useBlocker` lives in the SPA; there is no server involvement and no route to protect server-side |
| Reload / close / tab-close backstop | Browser / Client (`window`) | — | `beforeunload` is a window-level event; the prompt text is browser-owned (D-06) |
| Leave-decision UI + the Russian copy | Browser / Client (modal) | — | D-01/D-02: a DOM modal is the only surface that can host the copy |
| Dirty-flag ownership | Browser / Client (page state) | — | `yaml !== savedYaml` already lives in the page; no store, no context, no second flag (D-12) |
| Router shape (`App.jsx`) | Browser / Client | — | Client-only SPA; no SSR/framework mode, no loaders, no `basename` |
| `RequireAuth` 401 → `/login` redirect interception | Browser / Client (router) | — | The redirect is `<Navigate>`, i.e. a router navigation, so it traverses the same blocker path (D-04) — see Open Question 2 for the reachability analysis |
| Guard extractability for Phase 23 (`ADUX-10`) | Browser / Client (shared module) | — | D-07: one hook + one dialog + one copy constant, consumed by two editors |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react-router-dom | `^7.18.3` — installed **7.18.3** | `createBrowserRouter`, `RouterProvider`, `useBlocker`, `Navigate`, `NavLink` | Already the app's router; `useBlocker` ships in it, so **no dependency change** is needed `[VERIFIED: web/package.json:17]` |
| react / react-dom | `^19.2.8` | Component lifecycle for the hook, the effect, and `StrictMode` double-invocation | Already installed |
| @playwright/test | `^1.62.1` | The only honest proof of the SPA-guard journeys and of the real `beforeunload` prompt | Project-standard E2E harness; the `web` project runs with `VITE_USE_MOCKS=true` |
| `node --test` (built-in, Node 24.21.0) | — | Fast (<1 s) unit gate for the extracted pure `armBeforeUnload` helper | Established in this repo (`tests/unit/test_admin_mark_ready.js`, `tests/unit/test_markdown_toc.js` — both carry a `Run: node --test …` header) |
| Tailwind (project tokens `ink/40`, `paper`, `rule`, `accent`) | `^4.3.3` | Styling the overlay exactly as the existing modals do | Already installed; no new tokens |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tests/admin.spec.js` `gotoAsRole` helper | in-repo | Role harness + mock reset + reload | Every new journey in this phase |
| `window.__DIGEST_PIPELINE_CONFIG_HARNESS__` | in-repo (`web/src/main.jsx:67-72`) | `armFailNextSave` / `armRejectNextSave` arms | The save→no-prompt and reject→still-prompt journeys |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `useBlocker` (data router) | **Avoid the migration** and guard the page by other means | PITFALLS Pitfall 4 explicitly lists this as a legitimate fork, but it requires inventing an interception mechanism the router already provides, and it leaves the app on a router shape that cannot host the guard Phase 23 must reuse. D-09 already decided migration-as-its-own-plan. |
| `useBlocker` | `unstable_usePrompt({ when, message })` | Exists in 7.18.3 `[VERIFIED: web/node_modules/react-router/dist/development/index.d.ts — 'a8 as unstable_usePrompt']`, but it renders a **native `window.confirm`**, so it cannot satisfy D-01 (custom modal) and would put the copy in a browser dialog the phase explicitly rejects. Also still `unstable_`. |
| plain `useEffect` + `window.addEventListener` | `useBeforeUnload(callback, { capture })` | Exported in 7.18.3, but it is a thin `window.addEventListener` wrapper in a `useEffect` with **no conditional attachment** — a hook cannot be called conditionally, so it cannot satisfy D-05's "attached **only while dirty**" without attaching a no-op when clean. The plain effect with a `dirty` guard is the literal contract and is directly spy-testable. |
| A new guard state store / context | Reuse `dirty` from the page | A second source of dirtiness is exactly Pitfall 5a/5b. D-12 locks `dirty === yaml !== savedYaml`. |

**Installation:**

```bash
# none — this phase installs zero packages (see Package Legitimacy Audit)
```

**Version verification:** `web/package.json` declares `"react-router-dom": "^7.18.3"` `[VERIFIED: web/package.json:17]`, and the installed tree resolves to **7.18.3** for both `web/node_modules/react-router-dom/package.json` and `web/node_modules/react-router/package.json` (`"version": "7.18.3"`, read this session). React is `^19.2.8`, `@playwright/test` `^1.62.1`, Node `v24.21.0`, npm `11.18.0`. No registry lookup is required because nothing is being added.

## Package Legitimacy Audit

> **Not applicable — this phase installs zero external packages.**

The phase is a refactor plus new files inside `web/`. Every capability it needs (`createBrowserRouter`, `RouterProvider`, `useBlocker`, `Navigate`, Playwright's `runBeforeUnload`/`dialog` API, `node --test`) is already installed. No `npm install`, `pip install`, or `uv add` step appears anywhere in this research.

**Packages removed due to [SLOP] verdict:** none (none proposed)
**Packages flagged as suspicious [SUS]:** none (none proposed)

## Architecture Patterns

### System Architecture Diagram

```
                       ADMIN BROWSER (SPA, React 19 + data router)
  ┌───────────────────────────────────────────────────────────────────────────┐
  │ main.jsx: <StrictMode><App /></StrictMode>                                │
  │ App.jsx:  module-scope `router = createBrowserRouter([...])`              │
  │           <RouterProvider router={router} />                              │
  └───────────────────────────────────────────────────────────────────────────┘
                                    │
                     ┌──────────────┴───────────────┐
                     │ layout route (pathless)      │
                     │  element = <RequireAuth>     │
                     │              <AppShell />    │
                     │            </RequireAuth>    │
                     └──────────────┬───────────────┘
                                    │ <Outlet/>
                     ┌──────────────┴───────────────┐
                     │ AdminPipelineConfigPage      │
                     │  yaml / savedYaml            │
                     │  dirty = yaml !== savedYaml  │◄── single source of truth (D-12)
                     └──────────────┬───────────────┘
                                    │ dirty
                ┌───────────────────┴────────────────────┐
                │                                        │
   ┌────────────▼─────────────┐            ┌─────────────▼──────────────────┐
   │ useUnsavedChangesGuard   │            │ (same hook)                    │
   │  useBlocker(dirty)       │            │  useEffect: if (dirty)         │
   │  ─────────────────────── │            │    addEventListener(           │
   │  blocker.state           │            │      "beforeunload",           │
   └────────────┬─────────────┘            │      armBeforeUnload)          │
                │ "blocked"                │  cleanup: removeEventListener  │
   ┌────────────▼─────────────┐            └─────────────┬──────────────────┘
   │ UnsavedChangesDialog     │                          │
   │  role=dialog aria-modal  │                          │
   │  «Есть несохранённые …»  │                          │
   │  [Остаться] [Уйти …]     │                          │
   └────────────┬─────────────┘                          │
                │                                        │
      ┌─────────┴─────────┐                              │
      │                   │                              │
 blocker.reset()    blocker.proceed()                    │
 (stay, draft kept) (navigate ONCE)                      │
      │                   │                              │
      └─────► stays on      └─────► target route renders  │
              /admin/pipeline      (no doc unload →      │
                                    no double prompt)    │
                                                         │
                     ┌───────────────────────────────────┘
                     │ (only on an actual document unload)
                     ▼
        ┌──────────────────────────────────┐
        │ Browser-generated prompt         │
        │  text = BROWSER-OWNED (D-06)     │
        │  requires sticky activation      │
        └──────────────────────────────────┘
```

**Reading the diagram:** the primary use case — *type YAML → click a shell nav link → modal → Cancel keeps the draft* — travels the left branch only. The right branch is a distinct, non-overlapping backstop armed by the same `dirty` bit; because SPA navigation never unloads the document, `blocker.proceed()` can never also trigger the browser prompt, which is the structural reason no double prompt is possible.

### Recommended Project Structure

```
web/src/
├── utils/
│   └── unsavedChangesGuard.js     # armBeforeUnload(event) — two statements, no React, no Vite
├── hooks/
│   └── useUnsavedChangesGuard.js  # useBlocker(dirty) + dirty-scoped beforeunload effect
├── components/
│   └── UnsavedChangesDialog.jsx   # overlay + role=dialog + aria-modal + Esc=stay
├── pages/
│   └── AdminPipelineConfigPage.jsx  # consumes the hook; early returns untouched
└── App.jsx                          # createBrowserRouter + RouterProvider

tests/
├── unit/
│   └── test_unsaved_changes_guard.js  # node --test: the handler-body contract
└── admin.spec.js                      # amended tripwire + 4 new journeys
```

`utils/` is already the home of Vite-free pure helpers in this repo (`web/src/utils/forbiddenChrome.js` is imported by `tests/admin.spec.js` via `pathToFileURL` precisely because it has no Vite/`import.meta` dependency) — so `utils/unsavedChangesGuard.js` is node-`--test`-safe by the established convention. Keep the copy constant in the guard module (not in the page) so Phase 23 imports one source for both the string and the behaviour.

### Pattern 1: Data-router migration (`App.jsx`, Plan 1)

**What:** Replace the declarative JSX route tree with a route-object array and a module-scope router instance.
**When to use:** Plan 1 only — never in the same plan as the guard (D-09).

```jsx
// Source: Context7 /remix-run/react-router — createBrowserRouter + RouterProvider docs
// (api.reactrouter.com/v7/functions/react-router.createBrowserRouter.html)
import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
// …page imports unchanged…

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <IssuePage isCurrent /> },
      { path: 'archive', element: <ArchivePage /> },
      { path: 'issues/:number', element: <IssuePage isCurrent={false} /> },
      { path: 'voting', element: <VotingPage /> },
      { path: 'knowledge', element: <KnowledgePage /> },
      { path: 'materials/:id', element: <MaterialPage /> },
      { path: 'razbory', element: <RazboryListPage /> },
      { path: 'razbory/:id', element: <RazborPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: 'admin/digest', element: <AdminDigestPage /> },
      { path: 'admin/materials/:id', element: <MaterialPage preview /> },
      { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
```

**Hard notes the executor must not get wrong:**

- The router instance is created at **module scope**, not inside `App()`. Context7/the v7 API reference: "The `router` prop should be a single router instance created outside of the React tree. Avoid creating new routers during React renders/re-renders." `main.jsx` wraps `<App />` in `<StrictMode>`, and StrictMode intentionally double-invokes render — a router created in the component body would be instantiated twice, duplicating history listeners and navigation side-effects. This is a documented failure mode, not a hypothetical.
- Keep every import in `react-router-dom`. `[VERIFIED: web/node_modules/react-router-dom/dist/index.mjs:13-18]`:

  ```js
  import { HydratedRouter, RouterProvider } from "react-router/dom";
  export * from "react-router";
  export {
    HydratedRouter,
    RouterProvider
  };
  ```

  The explicit `react-router/dom` re-export wins over `export * from "react-router"`, so `import { RouterProvider } from 'react-router-dom'` already yields the `ReactDOM.flushSync`-wired provider. Following the v7 upgrade guide's "import from `react-router/dom`" here would be churn with no behavioural gain.
- Pathless layout route + relative child paths behave identically to the current nested `<Route>` tree (no `path` on the parent, so children are relative to `/`). `index`, `*`, and `Navigate`-as-`element` are all supported.
- **The one real behavioural delta** is error handling: a data router installs a default error boundary, so a render-time throw inside a route renders "Unexpected Application Error!" instead of unmounting to a blank page. See Open Question 3 — that difference is a *feature* for the guard plan (it can mask a `useBlocker` throw into an app-rendered error page rather than a crash), and it is exactly why the migration must be verified by the full suite before the guard lands.

### Pattern 2: The guard hook (`web/src/hooks/useUnsavedChangesGuard.js`)

**What:** One hook that arms both mechanisms off a single `dirty` bit and returns the blocker.

```jsx
// Source: Context7 /remix-run/react-router — docs/api/hooks/useBlocker.md
// Blocker = { state: "unblocked" | "blocked" | "proceeding", location, proceed(), reset() }
import { useEffect } from 'react'
import { useBlocker } from 'react-router-dom'
import { armBeforeUnload } from '../utils/unsavedChangesGuard.js'

/**
 * @param {boolean} dirty  `yaml !== savedYaml` — the page's single source of truth (D-12)
 * @returns {import('react-router-dom').Blocker}
 */
export function useUnsavedChangesGuard(dirty) {
  // Boolean form: blocks EVERY in-app navigation while dirty, with no
  // pathname carve-out (D-04) — this is the documented default surface.
  const blocker = useBlocker(dirty)

  useEffect(() => {
    if (!dirty) return undefined
    window.addEventListener('beforeunload', armBeforeUnload)
    return () => {
      window.removeEventListener('beforeunload', armBeforeUnload)
    }
  }, [dirty])

  return blocker
}
```

**Why the boolean form:** D-04 locks "one blocker predicate, no pathname-based carve-out". The `BlockerFunction` variant (`({ currentLocation, nextLocation }) => …`) exists and is the right shape *if* an exemption is ever added — it is explicitly not used here, and Context7 documents that the boolean form blocks all SPA navigations.

**Why a module-scope handler reference:** `armBeforeUnload` is a stable imported identity, so the `addEventListener`/`removeEventListener` pair is exact. An inline arrow re-created each render would still work (the effect re-runs on `dirty` only) but would defeat a listener-identity spy test and is a needless footgun.

### Pattern 3: The dialog (`web/src/components/UnsavedChangesDialog.jsx`)

**What:** The D-02 surface — a repeat of `AdminDigestPage`'s modal markup (`fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4` + `role="dialog"` + `aria-modal="true"` + `aria-labelledby`), plus Esc.

```jsx
// Mirrors web/src/pages/AdminDigestPage.jsx:824-836 (email modal) and :889-901 (confirm modal)
import { useEffect } from 'react'
import { UNSAVED_LEAVE_CONFIRM } from '../utils/unsavedChangesGuard.js'

export default function UnsavedChangesDialog({ open, onStay, onLeave }) {
  useEffect(() => {
    if (!open) return undefined
    function onKeyDown(event) {
      if (event.key === 'Escape') onStay()          // Esc = the SAFE action (D-02)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onStay])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="unsaved-changes-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-paper p-6">
        <h2 id="unsaved-changes-title" className="text-2xl font-semibold">
          Несохранённые изменения
        </h2>
        <p data-testid="unsaved-changes-message" className="mt-4 text-sm leading-relaxed text-ink-2">
          {UNSAVED_LEAVE_CONFIRM}
        </p>
        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            data-testid="unsaved-changes-stay"
            className="inline-flex min-h-11 items-center justify-center rounded-full border border-rule px-4 text-sm"
            onClick={onStay}
          >
            Остаться
          </button>
          <button
            type="button"
            data-testid="unsaved-changes-leave"
            className="inline-flex min-h-11 items-center justify-center rounded-full bg-[oklch(45%_0.13_155)] px-4 text-sm font-medium text-paper"
            onClick={onLeave}
          >
            Уйти без сохранения
          </button>
        </div>
      </div>
    </div>
  )
}
```

No focus trap, no auto-focus, no focus restore (D-02 — the project's modals have none and this phase does not introduce them).

### Pattern 4: The `beforeunload` helper (`web/src/utils/unsavedChangesGuard.js`)

```js
/** Reset-to-saved confirm copy (UI-SPEC; D-12) — stays with window.confirm (D-08). */
export const RESET_CONFIRM = 'Отменить изменения и вернуть последнюю сохранённую версию?'

/** Unsaved-changes leave copy (UI-SPEC; D-12) — the modal body only (D-01/D-06). */
export const UNSAVED_LEAVE_CONFIRM = 'Есть несохранённые изменения. Уйти без сохранения?'

/**
 * The exact `beforeunload` contract: two statements, nothing else.
 * No window.confirm, no app copy (the prompt text is browser-owned, D-06).
 * @param {BeforeUnloadEvent} event
 */
export function armBeforeUnload(event) {
  event.preventDefault()
  event.returnValue = true // truthy — the legacy activation path; the string form is deprecated
}
```

`RESET_CONFIRM` may stay in the page if the executor prefers; moving it is optional and would require touching the two reset tests' expectations only if the string changed (it must not).

### Pattern 5: Page wiring (the Rules-of-Hooks trap)

The hook **must be called before `AdminPipelineConfigPage`'s early returns**. The page has four (`roleState === 'loading'` / `'forbidden'` / `'error'`, then `loadState === 'loading'` / `'error'`), and they begin well after the `dirty` derivation. Place the guard right beside it:

```jsx
const dirty = yaml !== savedYaml                      // (:107 — unchanged)

const blocker = useUnsavedChangesGuard(dirty)         // NEW — must precede every early return

useEffect(() => { /* the corrected, two-statement handler */ }, [dirty])  // replaced

// …later, inside the rendered <section>:
<UnsavedChangesDialog
  open={blocker.state === 'blocked'}
  onStay={() => blocker.reset()}
  onLeave={() => blocker.proceed()}
/>
```

Placing the call after any `return` is a hard React error, not a lint nit.

### Anti-Patterns to Avoid

- **A1 — A second "touched" flag.** The guard keys off `dirty` only. A separate flag can drift (clear on save but not on reset, arm on load, …) and is Pitfall 5a/5b.
- **A2 — Optimistically clearing `dirty` in the save failure path.** The `INVALID_CONFIG` branch must keep `savedYaml` untouched so the guard stays armed (D-12 / ROADMAP criterion 3).
- **A3 — `blocker.proceed()` followed by a manual `navigate()`.** `proceed()` already completes the blocked navigation; calling `navigate()` too double-navigates. The "navigates exactly once" assertion exists to catch this.
- **A4 — Guarding with a pathname predicate "to avoid blocking the auth redirect".** D-04 forbids it, and Open Question 2 shows the redirect only becomes reachable *through* a navigation the blocker already intercepted.
- **A5 — Leaving the `beforeunload` effect keyed on anything other than `dirty`.** Keying on `yaml` re-registers on every keystroke; keying on `[]` never removes it and a clean editor prompts.
- **A6 — Asserting anything about the browser prompt's text.** It is browser-owned and, per MDN, generic. Assert `dialog.type() === 'beforeunload'` and nothing more.
- **A7 — Keeping any assertion of the form "a dialog appears after a synthetic `beforeunload`".** That assertion is the bug's alibi (D-10) and must not survive the amendment.
- **A8 — Creating the router inside the component.** Duplicate history listeners under StrictMode (see Pattern 1).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Intercepting an in-app navigation | A `popstate`/history patch, a `NavLink` `onClick` interceptor, a "pending navigation" store | `useBlocker` | It is the documented primitive, already installed, and it covers every navigation source (links, `navigate()`, `<Navigate>`, redirects) with one predicate. A manual interceptor covers only the sources you remembered. |
| Arming the reload/close prompt | A `window.confirm` inside the listener, an `alert`, a custom overlay | `event.preventDefault()` + truthy `returnValue` | The prompt is browser-owned; page code cannot render inside it (D-06). The current implementation is exactly the wrong turn (PITFALLS Pitfall 3). |
| Modal chrome/a11y | A new dialog abstraction, a focus trap, a portal library | The `AdminDigestPage` overlay + `role="dialog"` + `aria-modal` + `aria-labelledby` markup | D-02 locks this; a new abstraction would diverge from the two shipped modals and add responsibilities no other modal has. |
| Firing the browser prompt in tests | A synthetic `new Event('beforeunload')` | `page.close({ runBeforeUnload: true })` + `page.on('dialog')`, after a real interaction | A synthetic event proves the listener ran in the harness; the real path proves the browser actually prompts. |
| Fast unit coverage of the handler body | A jsdom/React-testing setup (not installed in this repo) | `node --test` on the pure `armBeforeUnload` helper | The repo already uses `node --test` for Vite-free pure helpers; a two-statement function is the ideal unit-test surface and costs <1 s. |

**Key insight:** every piece of this phase has an existing, documented primitive. The phase is *discipline*, not construction — the failure mode is picking the plausible-looking shortcut (`window.confirm` in the listener, synthetic event in the test, `useBlocker` on a declarative router).

## Runtime State Inventory

This phase contains a **refactor** (`App.jsx` router shape) and a **behaviour change** (the guard), so runtime state must be enumerated, not assumed.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| **Stored data** | Mock layer only, and it is deliberately durable across reloads: `MOCK_STORAGE_KEY = 'digest:pipeline-config-mock'` and `ARM_STORAGE_KEY = 'digest:pipeline-config-mock-arm'`, both in `sessionStorage` `[VERIFIED: web/src/services/pipelineConfigApi.js:26-33]` — the arm key's own docstring says "Stored in sessionStorage so it survives a reload (an initial-load failure must be armed before the page mounts) and clears on reset". No database, no `localStorage`, no cookies are touched by this phase. | **None** — but flag two consequences: (a) `sessionStorage` survives the `page.reload()` the amended tripwire performs, so a saved-then-reloaded editor comes back **clean**, which is what makes the "removed after a successful save" assertion meaningful; (b) any test that arms a mock rejection and then reloads keeps the arm armed. |
| **Live service config** | None. No Supabase, no backend, no environment variable, no service-side configuration is read or written. `VITE_USE_MOCKS` is set by `playwright.config.js:53` for the `web` project and is not modified. | **None** |
| **OS-registered state** | None registered by this phase. The only OS-adjacent artifact is the Playwright browser cache at `.playwright-browsers`, which exists (verified this session) and is managed by `scripts/ensure-playwright-browsers.cjs`. | **None** |
| **Secrets / env vars** | None. This phase reads no secret and adds no env var name. | **None** |
| **Build artifacts / installed packages** | None regenerate from this change. The only stale-state hazard is the **long-lived Vite dev server on `127.0.0.1:5174`**: `playwright.config.js:46` sets `reuseExistingServer: !process.env.CI`, so a stale listener is silently reused. Checked this session — **no listener is currently on 5174**, so the workspace is clean. STATE.md records that this is the recurring false-regression signature (mass `ERR_CONNECTION_REFUSED`). | **Operational** — run `Get-NetTCPConnection -LocalPort 5174 -State Listen` and kill any stale server before a full-suite run. A clean re-run has produced **110 passed** every time (STATE.md); use that as the migration gate baseline. |

**Canonical question — after every file is updated, what runtime systems still hold the old string/state?** Answer: **nothing that this phase renames.** No identifier, key, or path is renamed. The two mechanisms are additive, and the only "old state" that survives is the *broken handler behaviour* — which is deliberately removed from `AdminPipelineConfigPage.jsx` and must not survive anywhere else. Grep the final diff for `window.confirm` inside a `beforeunload` listener, and for `BrowserRouter` still imported while `useBlocker` is used.

## Common Pitfalls

### Pitfall 1: A green `beforeunload` test that green-lights a broken handler
**What goes wrong:** The shipped test dispatches a synthetic `beforeunload`, asserts `defaultPrevented === true`, and asserts a `dialog` carrying the Russian copy `[VERIFIED: tests/admin.spec.js:1143-1171]`. It passes because the buggy handler calls `window.confirm` and Playwright's dialog is auto-dismissed (returns `false`), so the `preventDefault()` branch runs. Real browsers will not let page code drive the unload prompt.
**Why it happens:** Headless Chromium *does* let the harness dispatch the event and open the dialog, so the test observes the harness, not the browser.
**How to avoid:** Assert the handler **body contract** (`preventDefault()` + truthy `returnValue`, no `confirm` call) in a fast `node --test`, and assert the **browser contract** (`dialog.type() === 'beforeunload'`) through `page.close({ runBeforeUnload: true })` after a real interaction. Never keep a synthetic-event dialog assertion.
**Warning signs:** `expect.poll(() => message).toBe("Есть несохранённые изменения…")` anywhere near a `beforeunload`; `new Event("beforeunload")` in a test; `window.confirm` inside the listener.

### Pitfall 2: `useBlocker` on a declarative router
**What goes wrong:** `useBlocker` calls `useDataRouterContext("useBlocker")` and throws when `DataRouterContext` is absent — `<BrowserRouter>` provides only Navigation/Location context.
**Why it happens:** The data-router prerequisite is easy to skim past, and today's `App.jsx` is declarative `[VERIFIED: web/src/App.jsx:19]`.
**How to avoid:** Land the migration in its own plan first (D-09). Under the migrated router the same throw would instead be caught by the data router's default error boundary and rendered as "Unexpected Application Error!" — i.e. it would look like a page bug, not a router bug, which is precisely why the migration must be proven green *before* the guard is wired.
**Warning signs:** `useBlocker must be used within a data router` in the console; `BrowserRouter` still imported while `useBlocker` is used; a migration "verified" by "the page loads".

### Pitfall 3: The router is recreated on every render (StrictMode)
**What goes wrong:** `<StrictMode>` double-invokes render; a router created in the component body is instantiated twice, duplicating history listeners and navigation side-effects. `main.jsx:70-73` wraps `<App />` in `<StrictMode>`.
**Why it happens:** The most natural refactor is to keep the router inside the component.
**How to avoid:** Create it once at module scope; the data-router API reference states the router prop "should be a single router instance created outside of the React tree".
**Warning signs:** `createBrowserRouter(` appearing inside a function body; duplicated navigations; doubled list fetches.

### Pitfall 4: A guard that fires on a successful save, or leaks across unmount
**What goes wrong:** Four failure modes at once (PITFALLS Pitfall 5): (a) navigating right after a save still prompts because `dirty` is still true in that tick; (b) a server reject disarms the guard; (c) both mechanisms arm and the user confirms twice; (d) the listener leaks across remounts so a clean editor prompts.
**Why it happens:** Three lifecycles (page state, router, window) with no shared signal.
**How to avoid:** Consume the existing `dirty` only; keep the `beforeunload` effect keyed on `[dirty]` so both the arm *and* the removal are automatic; **never let the SPA modal and the unload handler both display copy**; and prove "removed after a successful save" with a listener spy or a real reload.
**Warning signs:** A prompt after «Сохранено»; two dialogs for one navigation; the guard still armed after a reject; the handler re-registered on each keystroke.

### Pitfall 5: Hooks after early returns
**What goes wrong:** `AdminPipelineConfigPage` has early returns for `roleState === 'loading' | 'forbidden' | 'error'` and `loadState === 'loading' | 'error'`. Calling `useUnsavedChangesGuard` below any of them changes the hook count between renders → React throws "Rendered more hooks than during the previous render".
**Why it happens:** The modal JSX naturally belongs near the rendered section, and the hook gets dragged down with it.
**How to avoid:** Call the hook beside `const dirty` (line ~107), above every `return`.
**Warning signs:** An intermittent hook-count error as `roleState`/`loadState` transition.

### Pitfall 6: The negative `beforeunload` test is vacuous
**What goes wrong:** MDN states browsers "Require sticky activation for the dialog to be displayed. In other words, the browser will only show the dialog box if the frame or any embedded frame receives a user gesture or user interaction." A clean-editor test with no prior interaction would pass whether or not the handler is armed.
**Why it happens:** The negative case looks like "just close the page and assert nothing happened".
**How to avoid:** Perform a genuine interaction (e.g. the editor `fill()` already counts; add an explicit `click` in the clean case) before attempting the close/reload in **every** `beforeunload` case. Playwright's own suite does exactly this (`await newPage.click('body')`).
**Warning signs:** A `beforeunload` test whose only prior action is `page.goto`; a clean case that never interacts.

### Pitfall 7: A dirty editor breaking unrelated tests
**What goes wrong:** Once the handler is armed, any test that reloads/`goto`s/closes while dirty triggers a real prompt. Playwright auto-dismisses it when no `page.on('dialog')` listener is registered, so navigation proceeds — but a test that *does* register `page.on/once('dialog')` (the two reset-confirm tests do) could have the unload dialog consumed by its handler instead of the `window.confirm` it is waiting for.
**Why it happens:** Two dialog sources on one page.
**How to avoid:** In the new journeys, always reach a clean or explicitly-left state before a hard navigation; never leave the editor dirty in a test that then installs a dialog listener for the reset path. Keep the two reset tests untouched (D-08) — they do not navigate, so no unload dialog fires.
**Warning signs:** A reset test whose captured `message` is empty; a flaky "dialog never arrived" timeout.

### Pitfall 8: Treating the browser prompt's text as app copy
**What goes wrong:** Attempting to assert or customise the reload/close message.
**Why it happens:** The in-app copy is Russian and testable, so the reload path looks like it should match.
**How to avoid:** D-06 is the honest end state. Assert `dialog.type()` only.
**Warning signs:** `dialog.message()` asserted to a Russian string for a `beforeunload` dialog.

## Code Examples

Verified patterns from primary sources.

### Reading the blocker (the two-button contract)

```jsx
// Source: Context7 /remix-run/react-router — docs/api/hooks/useBlocker.md
// blocker.state: "unblocked" | "blocked" | "proceeding"
// blocker.proceed(): completes the blocked navigation
// blocker.reset():   returns to "unblocked" and stays at the current location
{blocker.state === 'blocked' && (
  <UnsavedChangesDialog
    open
    onStay={() => blocker.reset()}
    onLeave={() => blocker.proceed()}
  />
)}
```

### The blocked-navigation journey (new Playwright test)

```js
// tests/admin.spec.js — new describe/test inside the existing
// "Admin pipeline config — empty/dirty/reset/nav/no-execution" block
test("dirty editor blocks in-app nav; Cancel keeps the draft", async ({ page }) => {
  await gotoAsRole(page, "admin", "/admin/pipeline");
  const editor = page.getByTestId("pipeline-config-editor");
  await editor.fill("template: lecture\n");

  const nav = page.getByRole("navigation", { name: /основная навигация/i });
  await nav.getByRole("link", { name: /^Архив$/ }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(page.getByTestId("unsaved-changes-message")).toHaveText(
    "Есть несохранённые изменения. Уйти без сохранения?",
  );
  await expect(page).toHaveURL(/\/admin\/pipeline$/);   // blocked: still here

  await page.getByTestId("unsaved-changes-stay").click(); // blocker.reset()
  await expect(dialog).toHaveCount(0);
  await expect(page).toHaveURL(/\/admin\/pipeline$/);
  await expect(editor).toHaveValue("template: lecture\n"); // draft intact
});
```

### Confirm → navigate exactly once, with no second prompt

```js
test("confirming the modal navigates once and never double-prompts", async ({ page }) => {
  const nativeDialogs = [];
  page.on("dialog", (d) => { nativeDialogs.push(d.type()); return d.dismiss(); });

  await gotoAsRole(page, "admin", "/admin/pipeline");
  await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");
  await page.getByRole("navigation", { name: /основная навигация/i })
    .getByRole("link", { name: /^Архив$/ }).click();

  await page.getByTestId("unsaved-changes-leave").click(); // blocker.proceed()
  await expect(page).toHaveURL(/\/archive$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
  expect(nativeDialogs).toEqual([]); // the SPA path never touches beforeunload
});
```

### Save clears the guard; a reject keeps it armed (D-12 / criterion 3)

```js
test("save disarms the guard; a server reject keeps it armed", async ({ page }) => {
  await gotoAsRole(page, "admin", "/admin/pipeline");
  const editor = page.getByTestId("pipeline-config-editor");

  // reject → still dirty → navigating still blocks
  await editor.fill("template: lecture\n");
  await page.evaluate(() => window.__DIGEST_PIPELINE_CONFIG_HARNESS__.armRejectNextSave([
    { path: "template", message: "недопустимое значение" },
  ]));
  await page.getByTestId("pipeline-config-save").click();
  await expect(page.getByTestId("pipeline-config-errors")).toBeVisible();

  await page.getByRole("navigation", { name: /основная навигация/i })
    .getByRole("link", { name: /^Архив$/ }).click();
  await expect(page.getByRole("dialog")).toBeVisible();  // still armed
  await page.getByTestId("unsaved-changes-stay").click();

  // successful save → clean → navigation no longer blocks
  await page.getByTestId("pipeline-config-save").click();
  await expect(page.getByTestId("pipeline-config-status")).toHaveText("Сохранено");
  await page.getByRole("navigation", { name: /основная навигация/i })
    .getByRole("link", { name: /^Архив$/ }).click();
  await expect(page).toHaveURL(/\/archive$/);
  await expect(page.getByRole("dialog")).toHaveCount(0);
});
```

### Fast unit gate for the handler body (`node --test`)

```js
// tests/unit/test_unsaved_changes_guard.js — run: node --test tests/unit/test_unsaved_changes_guard.js
import test from 'node:test'
import assert from 'node:assert/strict'
import { armBeforeUnload } from '../../web/src/utils/unsavedChangesGuard.js'

test('armBeforeUnload preventDefaults and sets a truthy returnValue', () => {
  let prevented = false
  const event = { returnValue: undefined, preventDefault() { prevented = true } }
  armBeforeUnload(event)
  assert.equal(prevented, true)
  assert.ok(event.returnValue) // truthy — legacy activation path
})

test('armBeforeUnload sets returnValue before/independently of preventDefault', () => {
  // The two statements must both run, in either order, with no branching:
  // a falsy returnValue or a missing preventDefault makes the browser stay silent.
  const event = { returnValue: undefined, preventDefault() {} }
  armBeforeUnload(event)
  assert.equal(event.returnValue, true)
})

test('the handler body contains no window.confirm and no alert', () => {
  const body = String(armBeforeUnload)
  assert.equal(body.includes('confirm'), false)
  assert.equal(body.includes('alert'), false)
})
```

`armBeforeUnload` must stay a pure, two-statement function so these three assertions remain meaningful — the moment it grows a branch or a dialog call, the fast gate stops describing the contract.

### Replacing the tripwire's synthetic dispatch with the real browser contract

```js
// The pattern Playwright documents for beforeunload (docs/src/dialogs.md)
test("pipeline config dirty gating arms the unsaved-leave guard", async ({ page }) => {
  await gotoAsRole(page, "admin", "/admin/pipeline");
  const editor = page.getByTestId("pipeline-config-editor");

  // --- clean: a real interaction (sticky activation, MDN) then close ---
  const cleanSeen = [];
  page.on("dialog", async (d) => { cleanSeen.push(d.type()); await d.dismiss(); });
  await editor.click();                       // sticky activation — keeps the negative non-vacuous
  await page.close({ runBeforeUnload: true });
  await expect.poll(() => page.isClosed()).toBe(true);   // closed with no prompt
  expect(cleanSeen).toEqual([]);

  // --- dirty: real prompt, browser-owned text ---
  await gotoAsRole(page, "admin", "/admin/pipeline");
  await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");
  const dirtySeen = [];
  page.on("dialog", async (d) => { dirtySeen.push(d.type()); await d.accept(); });
  await page.close({ runBeforeUnload: true });
  await expect.poll(() => dirtySeen).toEqual(["beforeunload"]);
});
```

Two caveats the executor must respect: (1) a `page.on('dialog')` listener **must** handle the dialog or the action stalls — hence the explicit `dismiss()`/`accept()`; (2) after `page.close({ runBeforeUnload: true })` the page may stay open, so assert via `dialog` events, not via `isClosed()` alone, in the dirty case. If a `page.reload()` variant is preferred over `close`, it triggers the same dialog but a dismissed dialog cancels the navigation, so wrap the call and assert on the dialog event rather than on the reload promise.

### Migrating `main.jsx` (no change beyond the router's home)

`main.jsx:70-73` currently renders `<StrictMode><App /></StrictMode>`. Keep it exactly as-is; the router's home is `App.jsx`'s module scope. Do **not** create the router in `main.jsx` and also in `App.jsx`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `<BrowserRouter>` + `<Routes>` JSX | `createBrowserRouter` + `RouterProvider` (data router) | React Router 6.4 introduced data routers; the declarative API remains but has no data-router context | The data router is the only shape that exposes `useBlocker`; the JSX tree is otherwise equivalent |
| `window.confirm` inside `beforeunload` | `preventDefault()` + truthy `returnValue` in `beforeunload`, and a DOM modal for the SPA path | MDN: modern implementations require sticky activation and show only a generic browser-specified string | The Russian copy can only ever appear in the in-app modal (D-06) |
| `returnValue = "message"` | `returnValue = true` | Deprecated — the string form is ignored by modern browsers | Set a truthy value purely for the legacy activation path; never expect it to be displayed |
| `react-router-dom` as a distinct DOM package | In v7 `react-router-dom` re-exports `react-router` plus the DOM-specific `RouterProvider` | React Router v7 | No dependency change is needed; the flushSync-wired provider is already what `react-router-dom` hands you |

**Deprecated / outdated:**
- `unstable_usePrompt` — still exported but still `unstable_` and renders a native `window.confirm`; unsuitable under D-01.
- `useBeforeUnload` — available, but always attaches (no conditional attach); unsuitable under D-05.
- Custom text in the `beforeunload` prompt — impossible.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The **data-router default error boundary** catches a route render throw and renders "Unexpected Application Error!" instead of unmounting to a blank page, and this is the true behavioural delta of the migration | Pattern 1, Pitfall 2, Open Question 3 | LOW-MEDIUM — if wrong, an error path behaves as before. Either way the mitigation is unchanged (prove the migration green before wiring the guard). Not reproduced this session. |
| A2 | Accepting (not dismissing) the `beforeunload` dialog during the dirty test lets the close proceed, and `page.close({ runBeforeUnload: true })` reliably emits exactly one `beforeunload` dialog in the bundled Chromium | Code Examples, Validation Architecture | MEDIUM — if the event does not fire, the amended tripwire cannot prove the browser contract and the fallback (listener-registry spy + synthetic dispatch with a `window.confirm` spy) must carry it. Verified only against Playwright's own documented pattern, not executed here. |
| A3 | The remaining Playwright suite will not trip on an armed `beforeunload` handler because Playwright auto-dismisses dialogs when no `page.on('dialog')` listener exists | Pitfall 7 | MEDIUM — if a test registers a dialog listener while the editor is dirty, the unload dialog could be consumed instead of the expected `window.confirm`. Mitigated by never leaving the editor dirty in a test that then installs a listener. |
| A4 | The pre-migration baseline is **110 passed** for the `web` project | Runtime State Inventory, Validation Architecture | LOW — it comes from STATE.md's recorded clean re-run, not from a run this session. Record the actual number before migrating; do not assume it. |
| A5 | `web/src/utils/` is the correct home for the pure helper, matching the existing `forbiddenChrome.js` convention that `tests/admin.spec.js` already imports through `pathToFileURL` | Recommended Project Structure | LOW — cosmetic; the planner may relocate the file without consequence to the contract. |

## Open Questions

1. **Exact file split for the guard (D-07 leaves it to the planner).**
   - What we know: D-07 mandates a reusable hook + dialog; Phase 23 (`ADUX-10`) must import them without a rewrite; the copy constant must have one home.
   - What's unclear: whether the copy constant lives in the dialog, a small `copy.js`, or the `utils` helper.
   - Recommendation: put `armBeforeUnload` + `UNSAVED_LEAVE_CONFIRM` in `web/src/utils/unsavedChangesGuard.js` (Vite-free → `node --test`-able), the hook in `web/src/hooks/useUnsavedChangesGuard.js`, and the dialog in `web/src/components/UnsavedChangesDialog.jsx`. The page imports the hook and the dialog; the dialog imports only the copy constant.

2. **Does D-04's "the guard blocks the `RequireAuth` `/login` redirect too" actually hold?**
   - What we know: `RequireAuth` re-checks only inside an effect keyed on `[location.pathname, location.search]` `[VERIFIED: web/src/components/RequireAuth.jsx:45]`, and its `!authed` branch returns `<Navigate to={/login?returnUrl=…} replace />` `[VERIFIED: web/src/components/RequireAuth.jsx:59-63]`. `useBlocker`'s cleanup deletes the blocker when its host unmounts (`router.deleteBlocker(key)` — Context7 source excerpt), and `<Navigate>` would unmount the pipeline page.
   - What's unclear: whether a `<Navigate>`-driven redirect can ever begin **while the dirty editor is still mounted**.
   - Recommendation: it cannot, for the reachable reasons — the only trigger that flips `authed` to false is a location change, and a location change while dirty is exactly the navigation the blocker intercepts first. If the user chooses «Уйти без сохранения», the editor has already unmounted by the time `RequireAuth` re-checks and redirects, so no blocker is needed. **Do not add a pathname carve-out** (D-04). The plan should record this reachability argument rather than writing an unprovable test: with `VITE_USE_MOCKS=true` the Playwright `web` project short-circuits `RequireAuth` (`mocksOn` → `return children`), so the redirect path is not browser-reproducible here. A `window.__DIGEST_FORCE_AUTH_GATE__ = true` harness exists for exactly this gate, but it cannot express "dirty, then session expiry" because the gate is read once when `RequireAuth` mounts. **Flag this as an accepted, documented gap in the phase — it is not a blocker for `ADUX-09`, which speaks of in-app navigation, not session expiry.**

3. **Should the migration add an explicit `errorElement`?**
   - What we know: a data router installs a default error boundary (A1), which is a behaviour change for every route.
   - What's unclear: whether any existing test depends on a render throw propagating, and whether `containsForbiddenChrome` (`tests/admin.spec.js:19-24` imports `web/src/utils/forbiddenChrome.js`) would flag the default English error UI.
   - Recommendation: add **no** `errorElement` in the migration plan — adding one is a new behaviour, not a behaviour-preserving refactor. Record the delta in the plan and let the full-suite gate decide. If the suite stays green (expected, since no route throws in tests), ship as-is.

4. **What is the exact pre-migration baseline?**
   - What we know: STATE.md records "a clean re-run has produced 110 passed every time".
   - What's unclear: whether that number holds on the current tree (`experiment/gsd-framework` branch).
   - Recommendation: Wave 0 of Plan 1 runs `npm run test:web` once on the untouched tree, records the number, then re-runs after the migration and asserts equality. Do not hard-code 110.

5. **Do the copy constants need to move at all?**
   - What we know: `RESET_CONFIRM` at `:24` and `UNSAVED_LEAVE_CONFIRM` at `:27` `[VERIFIED: web/src/pages/AdminPipelineConfigPage.jsx:24,27]`.
   - What's unclear: whether the planner wants one module for both strings.
   - Recommendation: move `UNSAVED_LEAVE_CONFIRM` into the guard module (Phase 23 needs it; the dialog owns it). Leave `RESET_CONFIRM` where it is (D-08) to keep the two reset tests' surface untouched — its string must not change either way.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Node.js | Vite dev server, `node --test`, Playwright | ✓ | v24.21.0 | — |
| npm | Installing/running the `web` package | ✓ | 11.18.0 | — |
| react-router-dom (installed) | `useBlocker`, `createBrowserRouter`, `RouterProvider` | ✓ | 7.18.3 | — |
| react / react-dom | The hook and the dialog | ✓ | `^19.2.8` | — |
| @playwright/test | Both mechanisms' real proofs | ✓ | `^1.62.1` | — |
| Playwright browser cache | Running the `web` project | ✓ | `.playwright-browsers` present | — |
| `runBeforeUnload` support | The amended tripwire's browser contract | ✓ (documented API of the installed Playwright) | — | Listener-registry spy + `window.confirm` spy on a synthetic dispatch |
| Port `127.0.0.1:5174` free | A clean full-suite run | ✓ (no listener at research time) | — | Kill the stale listener; do not let `reuseExistingServer` reuse it |
| Backend / Supabase / pytest | — | ✗ (not needed) | — | N/A — this phase has **no** backend surface |

**Missing dependencies with no fallback:** none — every dependency this phase needs is installed and verified.

**Missing dependencies with fallback:** none.

**Operational precondition:** before any full-suite run, `Get-NetTCPConnection -LocalPort 5174 -State Listen` must return nothing. A stale long-lived Vite server makes every `web` test fail with `ERR_CONNECTION_REFUSED`, which STATE.md flags as indistinguishable from a real regression unless the error text is read.

## Validation Architecture

`workflow.nyquist_validation` is **absent** from `.planning/config.json` (which contains only `workflow._auto_chain_active` and `workflow.use_worktrees`), so per the research contract this section is **included**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `@playwright/test` `^1.62.1` (browser journeys) + built-in `node --test` on Node 24.21.0 (pure helper contract) |
| Config file | `playwright.config.js` (project `web`, `testMatch: /(web-app\|auth\|knowledge\|razbory\|admin)\.spec\.js/`, `webServer.env.VITE_USE_MOCKS: "true"`, `reuseExistingServer: !process.env.CI`) |
| Quick run command | `node --test tests/unit/test_unsaved_changes_guard.js` (<1 s, no browser) |
| Focused browser command | `npx playwright test --project=web tests/admin.spec.js -g "unsaved\|dirty gating"` |
| Full suite command | `npx playwright test --project=web` (baseline recorded before the migration; STATE.md's recorded clean value is 110 passed) |
| Estimated runtime | Unit <1 s; focused browser ~20–40 s; full `web` project ~2–4 min |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADUX-09 (handler body) | `armBeforeUnload` calls `preventDefault()` and sets a truthy `returnValue`; no `window.confirm` | unit | `node --test tests/unit/test_unsaved_changes_guard.js` | ❌ Wave 0 |
| ADUX-09 (criterion 2, dirty) | A dirty editor arms the browser's `beforeunload` prompt | e2e | `npx playwright test --project=web tests/admin.spec.js -g "unsaved-leave guard"` | ✅ `tests/admin.spec.js:1143` — **AMEND** |
| ADUX-09 (criterion 2, clean) | A clean editor prompts on neither path | e2e | same test (clean phase) + the save→navigate journey | ✅ **AMEND** |
| ADUX-09 (criterion 1) | In-app SPA nav with unsaved edits prompts with «Есть несохранённые изменения. Уйти без сохранения?»; Cancel keeps the draft | e2e | `npx playwright test --project=web tests/admin.spec.js -g "blocks in-app nav"` | ❌ Wave 0 |
| ADUX-09 (criterion 1) | Confirming navigates exactly once; no double prompt (no native dialog on the SPA path) | e2e | `npx playwright test --project=web tests/admin.spec.js -g "navigates once"` | ❌ Wave 0 |
| ADUX-09 (criterion 3) | Dirty clears after a successful save (no prompt); stays armed after an `INVALID_CONFIG` reject (prompts) | e2e | `npx playwright test --project=web tests/admin.spec.js -g "save disarms"` | ❌ Wave 0 |
| ADUX-09 (criterion 4) | `App.jsx` on a data router; no `useBlocker must be used within a data router`; every existing route still renders | e2e (regression gate) | `npx playwright test --project=web` (count equal to the Wave-0 baseline) | ✅ existing suite |
| D-08 (PRESERVE) | The two reset-confirm tests stay byte-identical and green | e2e | `npx playwright test --project=web tests/admin.spec.js -g "reset confirm"` | ✅ existing — **PRESERVE** |
| D-11 (OUT OF SCOPE) | `ADUX-10` — the ingest-sources editor guard | — | — | ❌ **deliberately not here** — Phase 23 |

### Sampling Rate

- **Per task commit:** `node --test tests/unit/test_unsaved_changes_guard.js` (Plan 2 task 1) and `npx playwright test --project=web tests/admin.spec.js -g "pipeline config"` thereafter.
- **Per wave merge:** `npx playwright test --project=web`.
- **Phase gate:** full `web` project green (count equal to the recorded baseline) before `/gsd-verify-work`.
- **Max feedback latency:** <1 s (unit) / <60 s (focused browser).

### Wave 0 Gaps

- [ ] `tests/unit/test_unsaved_changes_guard.js` — the `armBeforeUnload` body contract (covers criteria 2's handler contract).
- [ ] `web/src/utils/unsavedChangesGuard.js` — production module the unit test imports (RED first: create the test, run it, watch the import fail).
- [ ] `tests/admin.spec.js` — amend the tripwire (`:1143-1171`) AND add the three new journeys; do **not** delete the existing title.
- [ ] `tests/admin.spec.js` — a listener-registry spy (`page.addInitScript` wrapping `window.addEventListener`/`removeEventListener` for `'beforeunload'`) **only if** the real-prompt path proves unreproducible (Assumption A2 fallback). Prefer the real prompt.
- [ ] **Migration baseline:** run `npx playwright test --project=web` on the untouched tree in Plan 1's Wave 0 and record the number.
- [ ] Framework install: **none.**

## Security Domain

`security_enforcement` is absent from `.planning/config.json`, so this section is **included**. The phase's security surface is deliberately near-empty: it writes nothing, sends nothing, and adds no endpoint.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | `RequireAuth` is untouched. The migration must preserve its exact behaviour (it is one of the named at-risk regression surfaces, D-09). |
| V3 Session Management | no | Unchanged. The `getSession()` check and its `[location.pathname, location.search]` dependency are not modified (see Open Question 2). |
| V4 Access Control | no | `/admin/pipeline` server-side authorization is unchanged; the page's own `fetchMe` role gate is unchanged. The guard is presentational and confers no authority. |
| V5 Input Validation | no (unchanged) | The textarea's content is validated server-side by the pipeline-config validator. This phase adds no client-side validation and must not — a client-side rule would be a business rule in the UI, forbidden by `.cursor/rules/architecture.mdc`. |
| V6 Cryptography | no | Nothing is encrypted, hashed, or signed here. Never hand-roll. |

### Known Threat Patterns for {React 19 SPA + react-router-dom 7}

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Draft loss during an auth redirect becoming a data-availability defect | Denial of Service (of the user's own work) | D-04's single blocker predicate; the reachability analysis in Open Question 2 documents why it holds without a carve-out |
| The guard's modal becoming an XSS sink | Tampering | The modal renders a **constant string**, never the YAML or any server response. No `dangerouslySetInnerHTML`, no `href` built from input. |
| A behaviour-preserving refactor silently widening a route | Elevation of Privilege | The migration must not add/remove/loosen a route; the `*` → `/` catch-all and the `RequireAuth`-wrapped layout route are the named tripwires (D-09), and the full suite is the gate |
| A leaked `beforeunload` listener trapping the user | Denial of Service | The effect is keyed on `[dirty]`, so the handler is removed on a successful save and on unmount; the amended tripwire asserts removal |

**Security posture:** no new attack surface. The only security-relevant change is the requirement that the router migration does not alter route reachability or the auth gate — which is why the migration's verification is the *whole* suite, not a page-load smoke test.

## Sources

### Primary (HIGH confidence)

- **Context7 `/remix-run/react-router`** — fetched this session:
  - `docs/api/hooks/useBlocker.md` — the `Blocker` shape (`state`/`location`/`proceed()`/`reset()`), the boolean vs `BlockerFunction` forms, and "does not handle hard-reloads or cross-origin navigations".
  - `packages/react-router/lib/hooks.tsx` — the source-level proof that `useBlocker` calls `useDataRouterContext("useBlocker")`, that `<BrowserRouter>` supplies no `DataRouterContext`, and that `useBlocker`'s effect cleanup calls `router.deleteBlocker(key)`.
  - `docs/api/hooks/useBeforeUnload.md` — the `capture` option and the thin-wrapper signature.
  - `docs/upgrading/v7.md` — the "import `RouterProvider` from `react-router/dom`" guidance.
  - `docs/api/data-routers/RouterProvider.md` — "The `router` prop should be a single router instance created outside of the React tree. Avoid creating new routers during React renders/re-renders."
  - `docs/start/data/installation.md` — the canonical `createBrowserRouter` + `RouterProvider` example.
  - `docs/api/hooks/usePrompt.md` — `unstable_usePrompt` renders a native confirm.
- **The live repo, read this session** — `web/src/App.jsx` (`:1`, `:17-19`, `:45`), `web/src/main.jsx` (`:70-73`), `web/src/pages/AdminPipelineConfigPage.jsx` (`:24`, `:27`, `:107-121`), `web/src/components/RequireAuth.jsx` (`:45`, `:59-63`), `web/src/components/AppShell.jsx` (`:69-92`, the admin `NavLink` set), `web/src/pages/AdminDigestPage.jsx` (`:824-836`, `:889-901` — the modal pattern D-02 mirrors), `web/src/services/pipelineConfigApi.js` (`:26-33`, `:198-227`), `web/src/services/authEnv.js` (the `__DIGEST_FORCE_AUTH_GATE__` harness), `tests/admin.spec.js` (`:1-50` harness, `:1143-1171` tripwire, `:1174`/`:1191` reset tests by name), `playwright.config.js` (`:43-54`), `web/package.json` (`:17`).
- **The installed package tree, read this session** — `web/node_modules/react-router-dom/dist/index.mjs:13-18` (the `RouterProvider` re-export), `web/node_modules/react-router/dist/development/index.mjs` and `index.d.ts` (the export list: `useBlocker`, `useBeforeUnload`, `unstable_usePrompt`, `createBrowserRouter`, `RouterProvider`), and both `package.json` `"version": "7.18.3"` resolutions.
- **Playwright official docs** — [Dialogs](https://playwright.dev/docs/dialogs) (auto-dismiss with no listener; the `runBeforeUnload` section) and [Page](https://playwright.dev/docs/api/class-page) (`page.close({ runBeforeUnload: true })`); Playwright's own `tests/library/beforeunload.spec.ts` pattern of clicking the page first.
- **MDN** — [Window: beforeunload event](https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event): `preventDefault()` triggers the warning, **sticky activation** is required, only a generic browser-specified string is shown, and the `returnValue = true` variant exists for legacy activation.
- **Project planning artifacts** — `19-CONTEXT.md`, `19-DISCUSSION-LOG.md`, `.planning/ROADMAP.md` § Phase 19 + § Backlog 999.6, `.planning/REQUIREMENTS.md` (ADUX-09/ADUX-10 + traceability), `.planning/STATE.md` (the Vite/5174 blocker and the 110-passed baseline), `.planning/research/PITFALLS.md` (Pitfalls 3, 4, 5, 28; the Tripwire table; the Technical Debt Patterns row "Add the guard mechanism and the router migration in one plan = **Never**"; the five `999.6` verification-checklist bullets), `.planning/research/SUMMARY.md` (§ "Backlog 999.6 — unsaved-changes guard"), `.planning/research/STACK.md` (`:17`, `:404`).
- **Workspace rules** — `AGENTS.md`, `.cursor/rules/tdd.mdc`, `.cursor/rules/architecture.mdc`, `.cursor/rules/context7.mdc`.

### Secondary (MEDIUM confidence)

- React Router GitHub discussions on StrictMode double-render and router creation (`remix-run/react-router` discussion #10605, issues #9967 and #12970) — used only to corroborate the "create the router outside the tree" rule that the official API reference already states.

### Tertiary (LOW confidence)

- None. Every claim above is either source-read in this repo, or from official docs / Context7.

## Metadata

**Confidence breakdown:**

- **Standard stack: HIGH** — the exact installed versions were read from disk; the router capability set was read from the installed type definitions and Context7's source excerpts. No new package is proposed, so no registry risk exists.
- **Architecture: HIGH** — the migration shape, the guard packaging, and every code surface were read from the live files with line numbers.
- **Pitfalls: HIGH for framework mechanics, MEDIUM for the browser-prompt test mechanics** — the `useBlocker` throw, the `RouterProvider` re-export, and the broken handler are all source-verified; the `page.close({ runBeforeUnload: true })` behaviour is documented but was not executed this session (Assumption A2).
- **Reachability of the `RequireAuth` redirect (D-04): MEDIUM** — reasoned from `RequireAuth`'s effect dependencies and `useBlocker`'s cleanup semantics; not reproduced in a browser, and not browser-reproducible under `VITE_USE_MOCKS=true` (Open Question 2).

**Research date:** 2026-10-16
**Valid until:** 2026-11-15 (30 days) — the react-router-dom and Playwright surfaces are stable, and no dependency moves in this phase. Re-check only if `web/package.json`'s `react-router-dom` range changes.
