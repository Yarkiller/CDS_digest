# Phase 19: Unsaved-changes guard for the pipeline editor - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-15
**Phase:** 19-unsaved-changes guard for the pipeline editor
**Areas discussed:** In-app prompt surface, Leave actions, Reload/close backstop, Guard packaging

---

## In-app prompt surface

| Option | Description | Selected |
|--------|-------------|----------|
| Custom in-app modal | The Russian copy lives in a DOM dialog («Уйти без сохранения» / «Остаться»); DOM-testable in Playwright; only surface that can host the copy | ✓ |
| Keep `window.confirm` | Minimal change, same mechanism as the reset confirm, zero new UI chrome; but binary dialog, asserted via `page.on('dialog')` | |
| Claude's discretion | Let Claude pick what fits the TDD cycle with least work | |

**User's choice:** Custom in-app modal
**Notes:** None beyond the selection.

| Option | Description | Selected |
|--------|-------------|----------|
| Match existing modal pattern + Esc | Overlay + `role="dialog"` + `aria-modal` + `aria-labelledby` + «Остаться»; add Esc = «Остаться» only; no focus trap | ✓ |
| Full a11y | Plus focus trap, auto-focus on «Остаться», focus restore, click-outside = «Остаться» | |
| Claude's discretion | | |

**User's choice:** Match existing modal pattern + Esc
**Notes:** Rationale — the project's existing modals (`AdminDigestPage`) have no focus trap or auto-focus; adding one now would be a new responsibility in a single component.

---

## Leave actions

| Option | Description | Selected |
|--------|-------------|----------|
| Two actions | «Уйти без сохранения» + «Остаться»; exactly `ADUX-09`; «Сохранить и выйти» → deferred | ✓ |
| Three actions | Add «Сохранить и выйти» (save-then-navigate); on save failure/reject stay with the error and the modal open — a new failure branch and a new test class | |
| Claude's discretion | | |

**User's choice:** Two actions
**Notes:** None beyond the selection.

| Option | Description | Selected |
|--------|-------------|----------|
| Block all | Includes the `RequireAuth` 401 → `/login?returnUrl=…` redirect; one blocker with no exceptions; `useBlocker`'s default | ✓ |
| Exempt `/login` | Block only user-initiated navigation; the auth redirect always passes; needs a pathname predicate + its own test | |
| Claude's discretion | | |

**User's choice:** Block all
**Notes:** Rationale — the typed draft is never lost silently; on session expiry the admin sees the modal first and reaches `/login` only after choosing «Уйти без сохранения».

---

## Reload/close backstop

| Option | Description | Selected |
|--------|-------------|----------|
| Correct `beforeunload` only | Exactly ROADMAP criterion 2; no new storage mechanism; the native prompt text is browser-owned and unconfigurable | ✓ |
| + `sessionStorage` recovery | Persist the YAML on edit and restore on mount so even a confirmed reload keeps the text — a new capability beyond `ADUX-09` | |
| Claude's discretion | | |

**User's choice:** Correct `beforeunload` only
**Notes:** None beyond the selection.

---

## Guard packaging

| Option | Description | Selected |
|--------|-------------|----------|
| Reusable hook + dialog | e.g. a `useUnsavedChangesGuard` hook + dialog component; Phase 23 (`ADUX-10`) reuses it without a rewrite; one source of copy and behaviour | |
| Page-local | Fewest new files now; Phase 23 either duplicates the logic or extracts it then — risk of copy/behaviour drift | |
| Claude's discretion | | ✓ |

**User's choice:** Claude's discretion
**Notes:** Claude's decision recorded in CONTEXT.md as D-07 — take the **reusable hook + dialog**, because `ADUX-10` (Phase 23) already obliges the same guard on the ingest-sources editor and a page-local copy would drift.

| Option | Description | Selected |
|--------|-------------|----------|
| Keep reset on `window.confirm` | The phase is about leaving, not resetting; 16-UI-SPEC D-12 copy and the two reset tests stay byte-identical | ✓ |
| Unify reset onto the same modal | One UX on the page, but a wider diff and a deliberate amendment of two existing reset tests | |
| Claude's discretion | | |

**User's choice:** Keep reset on `window.confirm`
**Notes:** Mixing one modal and one `window.confirm` on the same page is accepted (matches the rest of the project).

---

## Claude's Discretion

- **Guard packaging** — user deferred; resolved as **reusable hook + dialog component** (CONTEXT D-07), justified by the planned Phase 23 consumer (`ADUX-10`).
- *(Packaging sub-choices not asked: where the hook/component files live, the exact modal markup/classes, the blocker wiring details — all left to the planner/executor within D-01…D-08.)*

## Deferred Ideas

- **«Сохранить и выйти» (save-then-navigate)** as a third modal action — new failure path, not required by `ADUX-09`; candidate backlog item.
- **`sessionStorage` draft recovery** — persisting the in-progress YAML across reload/close; a new capability (draft storage), outside `ADUX-09`; candidate backlog item.
