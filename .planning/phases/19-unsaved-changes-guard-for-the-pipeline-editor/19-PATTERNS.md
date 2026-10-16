# Phase 19: Unsaved-changes guard for the pipeline editor - Pattern Map

**Mapped:** 2026-10-16
**Files analyzed:** 8 (5 new/modified production surfaces + 3 test surfaces)
**Analogs found:** 6 / 8 (2 have no direct codebase analog — see "No Analog Found")

> **Scope note:** Frontend-only phase. All analogs live under `web/src/` and `tests/`.
> Every analog path below was verified git-**tracked** via `git ls-files -- …`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web/src/App.jsx` | config / route | request-response (routing) | itself (declarative) → `createBrowserRouter` shape | self-refactor |
| `web/src/main.jsx` | config (mount) | request-response | itself (unchanged — verify only) | n/a (no change) |
| `web/src/utils/unsavedChangesGuard.js` | utility | event-driven | `web/src/utils/forbiddenChrome.js` | role-match |
| `web/src/hooks/useUnsavedChangesGuard.js` | hook | event-driven | *(none — no custom hooks exist)* | no analog |
| `web/src/components/UnsavedChangesDialog.jsx` | component (modal) | request-response | `web/src/pages/AdminDigestPage.jsx` (confirm modal) + `web/src/components/ActionButton.jsx` | exact (markup) / role-match (component) |
| `web/src/pages/AdminPipelineConfigPage.jsx` | page / component | request-response | itself (correct the handler; wire the guard) | self-refactor |
| `tests/admin.spec.js` | test (e2e) | request-response | itself — existing tripwire + journeys | self-amend |
| `tests/unit/test_unsaved_changes_guard.js` | test (unit) | event-driven | `tests/unit/test_admin_mark_ready.js` | exact |

## Pattern Assignments

### `web/src/App.jsx` (config / route, request-response)

**Analog:** itself — `web/src/App.jsx` (the declarative tree that becomes a route-object array).

**Current imports + tree** (lines 1-19):
```jsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell.jsx'
import RequireAuth from './components/RequireAuth.jsx'
// …page imports unchanged…
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
```

**Target shape (data router, module-scope router):**
```jsx
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
      // …every child route preserved verbatim…
      { path: 'admin/pipeline', element: <AdminPipelineConfigPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
])

export default function App() {
  return <RouterProvider router={router} />
}
```

**Hard rules the executor must not get wrong** (from RESEARCH §Pattern 1 / Pitfall 3):
- Router instance at **module scope**, never inside `App()` (`main.jsx:70` wraps in `<StrictMode>` — StrictMode double-invokes render; an in-body router duplicates history listeners).
- Keep **every** import on `react-router-dom` (`react-router-dom/dist/index.mjs:13-18` re-exports the flushSync-wired `RouterProvider`; importing from `react-router/dom` is needless divergence).
- Preserve the pathless layout route (`element={<RequireAuth><AppShell /></RequireAuth>}`) + relative child paths, `index`, `*`, and `Navigate`-as-`element` exactly.
- Add **no** `errorElement` (behaviour-preserving refactor only — RESEARCH Open Question 3).

**Migration is its own plan (D-09):** gate = full Playwright suite green (record baseline Wave 0, assert equal after). Never combine with the guard plan.

---

### `web/src/main.jsx` (config / mount)

**Analog:** itself — `web/src/main.jsx` (lines 70-73):
```jsx
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

**Action: none expected.** The router's home is `App.jsx` module scope. Do **not** create the router in `main.jsx` *and* `App.jsx`. Listed only because the context named it; treat as a verify-only surface (the `__DIGEST_PIPELINE_CONFIG_HARNESS__` block at `main.jsx:67-72` is consumed by the new tests and must stay untouched).

---

### `web/src/utils/unsavedChangesGuard.js` (utility, event-driven)

**Analog:** `web/src/utils/forbiddenChrome.js` (the established Vite-free pure-helper convention — same file the Playwright suite imports via `pathToFileURL`).

**Analog header/export convention** (`forbiddenChrome.js:1-13`):
```js
/**
 * Assert-only email chrome ban list (ADUX-04, D-17/D-18).
 * Keep in sync with backend.domain.email_chrome.FORBIDDEN_LOWER.
 * Do not call from renderers to mutate output — tests and scrub tooling only.
 */

/** @type {readonly string[]} */
export const FORBIDDEN_LOWER = ['test-header', 'test_header', 'testheader']

/**
 * @param {string | null | undefined} text
 * @returns {boolean}
 */
export function containsForbiddenChrome(text) { … }
```

**Target content** (copy the doc-comment + named-export + JSDoc style; body from RESEARCH §Pattern 4):
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

**Constraints:** must be Vite-free / no `import.meta` / no React (so `node --test` can import it). Keep `armBeforeUnload` a **pure two-statement** function — the unit test's third assertion (`String(armBeforeUnload)` contains no `confirm`/`alert`) depends on it. `RESET_CONFIRM` may stay in the page (D-08 / Open Question 5); moving it is optional and its string must **not** change.

---

### `web/src/hooks/useUnsavedChangesGuard.js` (hook, event-driven)

**Analog:** *(none — no custom hooks exist in the repo; `Grep "export (default )?function use[A-Z]"` → 0 matches)*. Use RESEARCH §Pattern 2 verbatim; the new `web/src/hooks/` directory is created by this file.

**Composition style to borrow** from existing React files (e.g. `RequireAuth.jsx:12-24`, `AppShell.jsx:33-39`) — `useEffect` with a `let cancelled`/cleanup-return and explicit `return undefined` for the no-op branch:

**Target content:**
```jsx
import { useEffect } from 'react'
import { useBlocker } from 'react-router-dom'
import { armBeforeUnload } from '../utils/unsavedChangesGuard.js'

/**
 * @param {boolean} dirty  `yaml !== savedYaml` — the page's single source of truth (D-12)
 * @returns {import('react-router-dom').Blocker}
 */
export function useUnsavedChangesGuard(dirty) {
  const blocker = useBlocker(dirty) // boolean form → blocks EVERY SPA nav, no carve-out (D-04)

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

**Constraints:** module-scope imported handler reference (exact add/remove identity); effect keyed on `[dirty]` only (never `yaml`, never `[]`).

---

### `web/src/components/UnsavedChangesDialog.jsx` (component / modal, request-response)

**Analog (markup — D-02, exact):** `web/src/pages/AdminDigestPage.jsx` confirm modal (lines 889-925).

**Overlay + `role="dialog"` pattern** (`AdminDigestPage.jsx:889-899`):
```jsx
<div
  className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
  role="dialog"
  aria-modal="true"
  aria-labelledby="confirm-send-title"
>
  <div className="w-full max-w-md rounded-2xl bg-paper p-6">
    <h2 id="confirm-send-title" className="text-2xl font-semibold">
      Подтвердите отправку
    </h2>
```

**Button row pattern** (`AdminDigestPage.jsx:916-925`):
```jsx
<div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
  <button
    type="button"
    className="inline-flex min-h-11 items-center justify-center rounded-full border border-rule px-4 text-sm"
    disabled={sending}
    onClick={() => setConfirmOpen(false)}
  >
    Отмена
  </button>
  …
```

**Analog (component conventions — role-match):** `web/src/components/ActionButton.jsx` (default-exported function component, `type="button"`, Tailwind token classes, `min-h-11` hit target).

**Target content** (from RESEARCH §Pattern 3) — mirrors the overlay/`aria-modal`/`aria-labelledby` above, plus an `Escape → onStay` keydown effect (D-02 safe action):
```jsx
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
        <h2 id="unsaved-changes-title" className="text-2xl font-semibold">Несохранённые изменения</h2>
        <p data-testid="unsaved-changes-message" className="mt-4 text-sm leading-relaxed text-ink-2">
          {UNSAVED_LEAVE_CONFIRM}
        </p>
        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button type="button" data-testid="unsaved-changes-stay" … onClick={onStay}>Остаться</button>
          <button type="button" data-testid="unsaved-changes-leave" … onClick={onLeave}>Уйти без сохранения</button>
        </div>
      </div>
    </div>
  )
}
```

**Constraints (D-02):** **no** focus trap, **no** auto-focus, **no** focus restore — the two shipped modals have none and this phase does not introduce them. Renders a **constant string only** (never the YAML) — see Security Domain.

---

### `web/src/pages/AdminPipelineConfigPage.jsx` (page, request-response)

**Analog:** itself — correct the broken effect (lines 107-121) and wire the hook.

**The broken `beforeunload` effect to REPLACE** (lines 108-121) — the bug's alibi (Pitfall 3):
```jsx
useEffect(() => {
  if (!dirty) return undefined
  function onBeforeUnload(event) {
    if (typeof window.confirm === 'function' && !window.confirm(UNSAVED_LEAVE_CONFIRM)) {
      event.preventDefault()
      event.returnValue = ''
    }
  }
  window.addEventListener('beforeunload', onBeforeUnload)
  return () => {
    window.removeEventListener('beforeunload', onBeforeUnload)
  }
}, [dirty])
```

**The dirty signal to CONSUME, never re-derive** (line 107):
```jsx
const dirty = yaml !== savedYaml
```

**Target wiring** (RESEARCH §Pattern 5) — hook call **above every early return** (the five `roleState`/`loadState` returns begin at lines 178, 185, 190, 200, 214):
```jsx
const dirty = yaml !== savedYaml                       // (:107 — unchanged)

const blocker = useUnsavedChangesGuard(dirty)          // NEW — MUST precede every early return

// …later, inside the rendered <section>:
<UnsavedChangesDialog
  open={blocker.state === 'blocked'}
  onStay={() => blocker.reset()}
  onLeave={() => blocker.proceed()}
/>
```

**Keep unchanged:** the reset-to-saved `window.confirm(RESET_CONFIRM)` path (lines 131-138, D-08) and the `INVALID_CONFIG` branch that leaves `savedYaml` untouched (lines 163-169, D-12). Do not add a second "touched" flag (Anti-Pattern A1).

⚠️ **Rules-of-Hooks trap (Pitfall 5):** calling `useUnsavedChangesGuard` after any of the early returns changes the hook count between renders → React throws. Call it beside `const dirty`.

---

### `tests/admin.spec.js` (e2e test)

**Analog:** itself — amend the tripwire (`:1143-1171`), add new journeys inside the existing describe block (title at `:1107`), preserve the two reset tests (`:1172`, `:1190`).

**Harness to reuse** (`tests/admin.spec.js:26-48`) — `gotoAsRole(page, role, path)` sets `__DIGEST_MOCK_ME_ROLE__`, resets admin mocks, reloads for `/admin` paths. Mock-arm handle: `window.__DIGEST_PIPELINE_CONFIG_HARNESS__` (`main.jsx:67-72`).

**Tripwire to AMEND, never delete** — currently asserts a synthetic-event dialog (`:1143-1171`):
```js
test("pipeline config dirty gating arms the unsaved-leave guard", async ({ page }) => {
  await gotoAsRole(page, "admin", "/admin/pipeline");
  const editor = page.getByTestId("pipeline-config-editor");

  const cleanPrevented = await page.evaluate(() => {
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    return event.defaultPrevented;
  });
  expect(cleanPrevented).toBe(false);
  …
  await expect.poll(() => message).toBe("Есть несохранённые изменения. Уйти без сохранения?");
});
```

**Target: the real browser contract** (RESEARCH §Code Examples — `page.close({ runBeforeUnload: true })` + `page.on('dialog')`, after a real interaction for sticky activation):
```js
test("pipeline config dirty gating arms the unsaved-leave guard", async ({ page }) => {
  await gotoAsRole(page, "admin", "/admin/pipeline");
  const editor = page.getByTestId("pipeline-config-editor");

  // clean: real interaction (sticky activation, MDN) then close — negative stays non-vacuous
  const cleanSeen = [];
  page.on("dialog", async (d) => { cleanSeen.push(d.type()); await d.dismiss(); });
  await editor.click();
  await page.close({ runBeforeUnload: true });
  expect(cleanSeen).toEqual([]);

  // dirty: real prompt, browser-owned text
  await gotoAsRole(page, "admin", "/admin/pipeline");
  await page.getByTestId("pipeline-config-editor").fill("template: lecture\n");
  const dirtySeen = [];
  page.on("dialog", async (d) => { dirtySeen.push(d.type()); await d.accept(); });
  await page.close({ runBeforeUnload: true });
  await expect.poll(() => dirtySeen).toEqual(["beforeunload"]);
});
```

**Assert only `dialog.type()`** (D-06 / Anti-Pattern A6) — never the prompt text. **Never** keep a synthetic-`beforeunload` dialog assertion (A7).

**New journeys** (RESEARCH §Code Examples) — all inside the `:1107` describe block:
- `dirty editor blocks in-app nav; Cancel keeps the draft` — click `nav[aria-label="Основная навигация"]` link «Архив» (`AppShell.jsx:69-77`), assert modal copy via `getByTestId("unsaved-changes-message")`, assert URL unchanged, click `unsaved-changes-stay`, assert draft intact.
- `confirming the modal navigates once and never double-prompts` — click `unsaved-changes-leave`, assert `/archive`, assert `nativeDialogs === []`.
- `save disarms the guard; a server reject keeps it armed` — `armRejectNextSave([...])` → save → error visible → nav still blocks; then successful save → `pipeline-config-status` = «Сохранено» → nav proceeds.

**Pitfall 7:** never leave the editor dirty in a test that then installs a `page.on('dialog')` listener for the reset path.

---

### `tests/unit/test_unsaved_changes_guard.js` (unit test)

**Analog:** `tests/unit/test_admin_mark_ready.js` (exact — the `node --test` + Vite-free-pure-helper convention).

**Analog conventions** (`test_admin_mark_ready.js:1-12`):
```js
/**
 * RED→GREEN: admin mark-ready mock helpers + adminApi wiring (ADUX-05 / D-07, D-08).
 * Pure module — no Vite/supabase imports (node --test friendly).
 * Run: node --test tests/unit/test_admin_mark_ready.js
 */
const assert = require('node:assert/strict')
const { describe, it } = require('node:test')
```

The analog imports production modules 2 directories up: `await import('../../web/src/services/adminReadyMock.js')`.

**Target content** (RESEARCH §Code Examples):
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
  assert.ok(event.returnValue)
})

test('armBeforeUnload sets returnValue independently of preventDefault', () => {
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

**RED-first note (tdd.mdc):** Wave 0 creates this test **before** `web/src/utils/unsavedChangesGuard.js` exists — run it, watch the import fail, then implement the module.

---

## Shared Patterns

### Tailwind design tokens
**Source:** every `web/src/**/*.jsx` file (e.g. `AdminPipelineConfigPage.jsx:261-281`, `AppShell.jsx:10-13`).
**Apply to:** `UnsavedChangesDialog.jsx`.
Token classes only — `bg-paper`, `bg-ink/40`, `text-ink`/`text-ink-2`/`text-muted`, `border-rule`, `bg-accent`/`text-accent-ink`, `rounded-2xl`/`rounded-full`, `min-h-11` hit targets, `z-[400]` overlay. No new tokens, no hardcoded hex (oklch literals only where the page already uses them).

### Test-id naming
**Source:** `AdminPipelineConfigPage.jsx` (`pipeline-config-editor`, `pipeline-config-save`, `pipeline-config-status`, `pipeline-config-errors`).
**Apply to:** `UnsavedChangesDialog.jsx` → `unsaved-changes-message` / `unsaved-changes-stay` / `unsaved-changes-leave` (kebab-case, feature-prefixed). Reset tests rely on the existing `pipeline-config-*` ids — do not rename them.

### Vite-free pure helper (`node --test`-able)
**Source:** `web/src/utils/forbiddenChrome.js` (imported by `tests/admin.spec.js` via `pathToFileURL`) and `web/src/utils/filters.js`.
**Apply to:** `web/src/utils/unsavedChangesGuard.js` — no `import.meta`, no Vite globals, named ESM exports.

### React effect with cleanup
**Source:** `web/src/components/RequireAuth.jsx:13-42`, `web/src/components/AppShell.jsx:33-56`, `AdminPipelineConfigPage.jsx:48-73`.
**Apply to:** `useUnsavedChangesGuard.js` and `UnsavedChangesDialog.jsx` — `if (!cond) return undefined` no-op branch + returned cleanup that removes the exact listener reference.

### Copy constants (locked Russian strings)
**Source:** `AdminPipelineConfigPage.jsx:24,27` (`RESET_CONFIRM`, `UNSAVED_LEAVE_CONFIRM`).
**Apply to:** guard module (owns `UNSAVED_LEAVE_CONFIRM`) and the page (keeps `RESET_CONFIRM`). Both strings are locked by 16-UI-SPEC — do not paraphrase.

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `web/src/hooks/useUnsavedChangesGuard.js` | hook | event-driven | No custom hooks exist in `web/src` (0 matches for `export function use[A-Z]`); `web/src/hooks/` is a new directory. Use RESEARCH §Pattern 2; borrow the effect/cleanup style from `RequireAuth.jsx`. |
| `web/src/utils/unsavedChangesGuard.js` | utility | event-driven | Role-analog exists (`forbiddenChrome.js`) but the **behaviour** (`beforeunload` contract) has no prior art — the shipped handler is the bug being fixed. Body comes from RESEARCH §Pattern 4 / PITFALLS Pitfall 3. |

## Metadata

**Analog search scope:** `web/src/{pages,components,utils,hooks,services}`, `tests/`, `tests/unit/`, plus `web/src/App.jsx` and `web/src/main.jsx`.
**Files scanned:** ~12 read in full/targeted; all 10 named analog paths confirmed git-tracked via `git ls-files --`.
**Pattern extraction date:** 2026-10-16.
**Cross-check:** every excerpt above matches the live files read this session; the data-router shape and `useBlocker` behaviour are corroborated by `19-RESEARCH.md` (§Patterns 1-5, §Pitfalls 1-8).
