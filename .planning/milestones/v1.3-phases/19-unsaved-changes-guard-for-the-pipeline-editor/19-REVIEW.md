---
phase: 19-unsaved-changes-guard-for-the-pipeline-editor
reviewed: 2026-10-16T07:10:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - web/src/App.jsx
  - web/src/utils/unsavedChangesGuard.js
  - web/src/hooks/useUnsavedChangesGuard.js
  - web/src/components/UnsavedChangesDialog.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - tests/unit/test_unsaved_changes_guard.js
  - tests/admin.spec.js
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 19: Code Review Report

**Reviewed:** 2026-10-16T07:10:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Plans 19-01 and 19-02 largely match their SUMMARY claims: module-scope `createBrowserRouter` + `RouterProvider`, reusable util/hook/dialog trio, boolean `useBlocker(dirty)`, two-statement `armBeforeUnload` registered only while dirty, locked Russian copy, reset `window.confirm` path untouched, and amended tripwire plus SPA/save Playwright journeys. No security vulnerabilities or shipping-blocking logic errors were confirmed on the reachable happy paths. Two maintainability/robustness warnings remain: the leave dialog is only mounted on the ready render path, and Escape’s `onStay` identity is unstable across parent re-renders.

## Warnings

### WR-01: Leave dialog missing on early-return branches while blocker can still be armed

**File:** `web/src/pages/AdminPipelineConfigPage.jsx:164-216` (early returns) vs `:339-343` (dialog only on ready path)
**Issue:** `useUnsavedChangesGuard(dirty)` correctly runs above all five early returns, so `useBlocker(true)` and `beforeunload` stay active whenever `yaml !== savedYaml`. `UnsavedChangesDialog` is only rendered in the final ready return. If `dirty` is ever true while `roleState`/`loadState` takes an early-return branch (e.g. future `loadKey` bump that calls `setLoadState('loading')` without clearing yaml, or Phase 23 reuse of this wiring), SPA navigation blocks with no Stay/Leave UI — a deadlock until dirty clears. Current UI does not expose a control that sets `loadKey`/`roleKey` from the dirty ready editor, so this is not hit today, but the invariant “blocker armed ⇒ dialog mountable” is structurally violated.
**Fix:** Render the dialog on every return path (or once before branching), e.g.:

```jsx
const leaveDialog = (
  <UnsavedChangesDialog
    open={blocker.state === 'blocked'}
    onStay={() => blocker.reset()}
    onLeave={() => blocker.proceed()}
  />
)

if (roleState === 'loading') {
  return (
    <>
      {leaveDialog}
      <section aria-busy="true" data-testid="admin-role-loading">…</section>
    </>
  )
}
// …same for other early returns; keep leaveDialog in the ready return too
```

### WR-02: Unstable `onStay` identity rebinds Escape listener every parent render

**File:** `web/src/pages/AdminPipelineConfigPage.jsx:341-342` → `web/src/components/UnsavedChangesDialog.jsx:11-20`
**Issue:** `onStay={() => blocker.reset()}` and `onLeave={() => blocker.proceed()}` are new function identities every render. `UnsavedChangesDialog`’s Escape effect depends on `[open, onStay]`, so while the modal is open any parent re-render (status tick, save completion race, etc.) tears down and re-attaches the `keydown` listener. Escape can be missed in that gap, stranding the user on a blocked navigation until they click «Остаться».
**Fix:** Stabilize callbacks at the call site or inside the dialog via a ref:

```jsx
// In UnsavedChangesDialog.jsx
const onStayRef = useRef(onStay)
useEffect(() => { onStayRef.current = onStay }, [onStay])
useEffect(() => {
  if (!open) return undefined
  function onKeyDown(event) {
    if (event.key === 'Escape') onStayRef.current()
  }
  window.addEventListener('keydown', onKeyDown)
  return () => window.removeEventListener('keydown', onKeyDown)
}, [open]) // intentionally not onStay
```

## Info

### IN-01: Browser Back / History POP not covered by Playwright

**File:** `tests/admin.spec.js:1224-1278`
**Issue:** SPA leave journeys only click shell «Архив». `useBlocker` also intercepts History POP (Back). No automated proof that Back shows the same modal and Stay/Leave semantics.
**Fix:** Add a focused journey: dirty editor → `page.goBack()` (after a prior in-app nav into the page) → assert dialog + Stay keeps `/admin/pipeline`.

### IN-02: Generic save-failure path untested for guard arming

**File:** `tests/admin.spec.js:1281-1314`; `web/src/pages/AdminPipelineConfigPage.jsx:155-158`
**Issue:** ADUX-09 / D-12 require the guard to stay armed after save failure as well as `INVALID_CONFIG` reject. The Playwright pin covers reject-then-Stay and successful-save disarm only. The `else` branch (`setSaveError` / `status: 'failed'`) leaves `yaml`/`savedYaml` unchanged (correct) but has no SPA-nav assertion.
**Fix:** Arm `armFailNextSave` (or equivalent harness), save, assert dialog still appears on «Архив».

### IN-03: Redundant `Boolean(dirty)` wrapper

**File:** `web/src/hooks/useUnsavedChangesGuard.js:13`
**Issue:** `dirty` is already a boolean (`yaml !== savedYaml`). `Boolean(dirty)` is noise and slightly obscures the D-04 “boolean form” contract for readers.
**Fix:** `const blocker = useBlocker(dirty)`.

---

### Claims check (SUMMARY vs source)

| Claim | Verdict |
|---|---|
| 19-01: module-scope `createBrowserRouter` + `RouterProvider`, no `errorElement`, route set preserved | Confirmed (`web/src/App.jsx`) |
| 19-02: util/hook/dialog trio; copy single-homed in util | Confirmed |
| 19-02: `armBeforeUnload` = `preventDefault` + truthy `returnValue`; no confirm/alert | Confirmed |
| 19-02: hook above early returns; dirty = `yaml !== savedYaml` | Confirmed |
| 19-02: reset `window.confirm(RESET_CONFIRM)` untouched | Confirmed |
| 19-02: page-local confirm-in-unload removed | Confirmed |
| 19-02: tripwire amended + SPA/save journeys present | Confirmed |

---

_Reviewed: 2026-10-16T07:10:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
