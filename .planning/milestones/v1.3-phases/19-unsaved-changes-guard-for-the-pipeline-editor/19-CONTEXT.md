# Phase 19: Unsaved-changes guard for the pipeline editor - Context

**Gathered:** 2026-10-15
**Status:** Ready for planning

<domain>
## Phase Boundary

The admin pipeline editor (`/admin/pipeline`, `AdminPipelineConfigPage.jsx`) **warns before losing unsaved edits** on both paths: **in-app SPA navigation** and **reload/close**. A clean editor prompts on neither path. The dirty flag clears after a successful save and stays armed after a server reject. The Russian copy «Есть несохранённые изменения. Уйти без сохранения?» is reused verbatim.

This is a **frontend-only backlog debt close-out** (backlog 999.6 / tech-debt `WR-04`+`WR-05`). It fixes the *mechanism* of the guard; it does not add editing features, does not change the validator or the config API, and does not add any execution surface.

**In scope:**
- A correct `beforeunload` handler in the pipeline editor (`preventDefault()` + truthy `returnValue`, no `window.confirm` inside it).
- An in-app navigation guard for the editor, backed by the React Router data-router `useBlocker`.
- `web/src/App.jsx` migrated from declarative `<BrowserRouter>` to a data router (`createBrowserRouter` + `RouterProvider`) — **as its own behaviour-preserving plan** (see D-09).
- Amending the existing dirty-gating Playwright test (tripwire, see D-10).
- RED/GREEN Playwright coverage of the real user journey (edit → click a shell nav link → modal → Cancel keeps the draft / confirm navigates once).

**Out of scope:**
- ADUX-10 — the guard on the ingest-sources editor ships in **Phase 23**, not here (D-11).
- `sessionStorage` (or any) draft persistence — the phase warns, it does not store the draft (D-05).
- A «Сохранить и выйти» third action (deferred, see Deferred Ideas).
- Changing the reset-to-saved confirm, the validator, the config API, composition, or the schema.
- Any redesign of the editor UI, editor hints, or the config DTO.

</domain>

<decisions>
## Implementation Decisions

### In-app prompt surface
- **D-01:** The in-app (SPA) leave confirmation is a **custom in-app modal**, not `window.confirm`. The copy «Есть несохранённые изменения. Уйти без сохранения?» lives in the modal body — the in-app guard is the only surface where the Russian copy can be shown at all (the reload/close prompt text is browser-owned, see D-06). — **Reversibility:** reversible — presentational; the blocker logic is unchanged if the surface is later swapped.
- **D-02:** The modal **repeats the project's existing modal pattern** (`AdminDigestPage`): full-screen overlay (`fixed inset-0` + `bg-ink/40`) with `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and explicit buttons. It additionally handles **Esc = «Остаться»** (the safe action). No focus trap, no auto-focus, and no focus restore — those do not exist in any current project modal and are deliberately not introduced here. — **Reversibility:** reversible.

### Leave actions
- **D-03:** The modal offers **two actions only**: «Уйти без сохранения» (calls `blocker.proceed()`) and «Остаться» (calls `blocker.reset()`, keeping the draft). No «Сохранить и выйти». — **Reversibility:** reversible.
- **D-04:** While dirty, the guard blocks **every** navigation — including the `RequireAuth` 401 → `/login?returnUrl=…` redirect — with **no exceptions**: one blocker predicate, no pathname-based carve-out. Rationale: the typed draft is never lost silently; on session expiry the admin first sees the modal and only leaves for `/login` after explicitly choosing «Уйти без сохранения». This is `useBlocker`'s default behaviour and needs no extra code. — **Reversibility:** reversible — one predicate in the blocker (adding an exemption later is a local edit), though it would then need its own test.

### Reload/close backstop
- **D-05:** Reload/close is covered by a **correct `beforeunload` handler only** — it does exactly `event.preventDefault()` and a **truthy** `event.returnValue`, is attached **only while dirty**, and is removed on unmount and after a successful save. It contains **no** `window.confirm`/`alert`. No `sessionStorage` draft recovery is added. — **Reversibility:** reversible.
- **D-06:** The native reload/close prompt text is **browser-owned and cannot be customized**; the shipped handler shows no app copy there. This is the honest end state, not a defect (custom copy is impossible inside `beforeunload`). — **Reversibility:** reversible.

### Guard packaging
- **D-07:** *(Claude's Discretion — user deferred to Claude)* The guard is packaged as a **reusable hook + dialog component** rather than page-local logic (e.g. a `useUnsavedChangesGuard`-style hook plus an `UnsavedChangesDialog` component under `web/src/`), so the guard is armed identically on the editor today and on the ingest-sources editor in Phase 23. Rationale: `ADUX-10` already obliges Phase 23 to reuse this guard; a page-local copy would silently drift from it (copy string, blocker semantics, handler contract). — **Reversibility:** costly — re-inlining later means re-splitting the copy/behaviour across two editors and re-pinning both test surfaces.
- **D-08:** The **reset-to-saved confirm stays `window.confirm`** with its existing copy «Отменить изменения и вернуть последнюю сохраненную версию?» (16-UI-SPEC D-12); the two existing reset Playwright tests are **not** amended. Mixing one modal and one `window.confirm` on the same page is accepted — that matches the rest of the project. — **Reversibility:** reversible.

### Carried forward — locked by ROADMAP / Phase 16, not re-decided here
- **D-09:** `web/src/App.jsx` is migrated from declarative `<BrowserRouter>` to a data router (`createBrowserRouter` + `RouterProvider`) **as its own behaviour-preserving plan**, gated by the **full Playwright suite green before the guard is wired**. The migration and the guard are **never combined in one plan** — a `useBlocker` throw would otherwise be misattributed to the migration. Every route is an at-risk regression surface, in particular the auth-gated parent route (`RequireAuth` + `AppShell`), the `admin/materials/:id` preview route (Phase 18), and the `*` → `/` catch-all. (ROADMAP criterion 4; PITFALLS Pitfall 4.) — **Reversibility:** costly — the router object replaces the JSX route tree and changes how `RequireAuth`/`AppShell` wrap children; reverting touches `App.jsx` and the shell/layout wiring.
- **D-10:** Tripwire `tests/admin.spec.js` → `"pipeline config dirty gating arms the unsaved-leave guard"` → **AMEND** (never delete). The amended test asserts the **handler contract** (registered only when dirty, sets the flag, removed on unmount and after a successful save) instead of asserting a `dialog`/`defaultPrevented` after a **synthetic** `beforeunload`. No test may keep asserting that a dialog appears during `beforeunload` — that assertion is the bug's alibi.
- **D-11:** **`ADUX-10` is NOT owned here.** The guard covering the ingest-sources editor ships in **Phase 23**; the ROADMAP records this gap as deliberate. Phase 19 only has to make the guard *extractable* for that reuse (D-07).
- **D-12:** The dirty contract is **locked**: `dirty === yaml !== savedYaml`; it clears on a successful save, stays armed after a server reject (`INVALID_CONFIG`) or a save failure, prompts on neither path when clean, and the two mechanisms must never **double-prompt** (the modal owns the message; the beforeunload handler shows no app copy).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` § Phase 19 — goal, requirement `ADUX-09`, the four success criteria (incl. criterion 4's data-router migration), dependency on Phase 17, and the tripwire disposition.
- `.planning/ROADMAP.md` § Backlog 999.6 — the originating debt (`WR-04`, `WR-05`), both recorded as an accepted known limitation, plus the `ADUX-10` ownership note.
- `.planning/REQUIREMENTS.md` — `ADUX-09` (guard on SPA nav **and** reload/close; existing copy; clean = no warning; clears on save, armed after reject) and `ADUX-10` (**Phase 23**, not Phase 19).
- `.planning/PROJECT.md` — v1.3 milestone framing; the Key Decisions rows for Backlog 999.6 and the v1.2 → v1.3 deferral.
- `.planning/STATE.md` — current focus and the **Vite dev-server flakiness** operational blocker (check for a stale listener on `127.0.0.1:5174` and kill it before any full-suite run; mass `ERR_CONNECTION_REFUSED` is indistinguishable from a real regression unless the error text is read).

### Research evidence for THIS phase
- `.planning/research/PITFALLS.md` § **Pitfall 3** — *"`window.confirm` inside `beforeunload` — shipped, and asserted by a passing test"*: the exact bug, why the green test proves nothing, and the required handler (`preventDefault()` + **truthy** `returnValue`, nothing else) — **this is D-05/D-10's source**.
- `.planning/research/PITFALLS.md` § **Pitfall 4** — *"`useBlocker` requires a data router — and this app is on `<BrowserRouter>`"*: migrate `App.jsx` as its own behaviour-preserving plan, never combined with the guard — **this is D-09's source**.
- `.planning/research/PITFALLS.md` § **Pitfall 5** — *"A guard that fires on a successful save, or double-prompts"*: the four failure modes around `dirty`, async save, and two guard mechanisms — **this is D-12's source**.
- `.planning/research/PITFALLS.md` § Tripwire/test table (row: `tests/admin.spec.js` "pipeline config dirty gating arms the unsaved-leave guard") and § Technical Debt Patterns (row: "Add the guard mechanism and the router migration in one plan" = **Never**) and § Verification checklist (the five `999.6` bullets: handler contract, SPA navigation, save/reject, router, no double-prompt).
- `.planning/research/SUMMARY.md` § "Phase 18: Backlog 999.6 — unsaved-changes guard" — the router-migration-as-its-own-plan recommendation and the "phase decision required" note.

> **Numbering warning:** `PITFALLS.md` carries a *provisional* phase mapping that predates the shipped roadmap — it labels 999.6 as "Phase 18" and 999.7 as "Phase 19". The roadmap assigns 999.6 to **Phase 19**. Address pitfalls by name, not by the numbers in that table.

### Copy and UI contract
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` § copy table — the locked rows «Есть несохранённые изменения. Уйти без сохранения?» (leave) and «Отменить изменения и вернуть последнюю сохранённую версию?» (reset), and § "Unsaved-changes guard" (the MVP `window.confirm` disposition this phase supersedes for the leave path only).
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-REVIEW-DISPOSITION.md` — the `WR-04` / `WR-05` rows (`deferred`, reason: accepted known limitation → backlog 999.6).

### Code to change / reuse
- `web/src/pages/AdminPipelineConfigPage.jsx` — the ONLY page whose guard changes; holds `UNSAVED_LEAVE_CONFIRM`, `RESET_CONFIRM`, the `dirty` derivation, `onSave`, and the **broken** `beforeunload` effect (lines ~108–121) that must be corrected.
- `web/src/App.jsx` — the declarative `<BrowserRouter>` route tree that becomes `createBrowserRouter(...)` + `<RouterProvider>` **in the separate migration plan** (D-09).
- `web/src/main.jsx` — where `<App />` is mounted under `StrictMode`; the router object's home is decided by the migration plan (StrictMode double-invocation matters for the blocker/handler lifecycle, Pitfall 5d).
- `web/src/components/RequireAuth.jsx` — the 401 → `/login?returnUrl=…` `<Navigate>` that D-04 deliberately blocks.
- `web/src/components/AppShell.jsx` — the shell `NavLink` set (Выпуск/Архив/База/Голосование/Разборы/Админ/Пайплайн) is the in-app navigation intent the guard intercepts, and the natural click target for the RED test.
- `web/src/pages/AdminDigestPage.jsx` — the existing `role="dialog"` + `aria-modal="true"` modal pattern D-02 mirrors (lines ~825–900).
- `tests/admin.spec.js` — the tripwire test `"pipeline config dirty gating arms the unsaved-leave guard"` (~line 1143, to be **AMENDED**) plus the two reset-confirm tests (~lines 1174, 1191, must stay green unchanged) and the empty/dirty/reset/nav describe block (~line 1107).

### Rules that constrain the change
- `.cursor/rules/tdd.mdc` — RED-first is mandatory: a failing Playwright test must exist before the production change.
- `.cursor/rules/architecture.mdc` — frontend reaches the backend only through `web/src/services/`; UI must not own business rules (this phase has no backend surface at all).
- `AGENTS.md` — TDD cycle and `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`.

**No ADR governs this phase.** `docs/adr/0001`–`0004` (leaderboard, Cloud.ru/FoundryModels, email domains, self-hosted Supabase) are unrelated to the unsaved-changes guard.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Existing modal pattern** (`AdminDigestPage.jsx`): overlay + `role="dialog"` + `aria-modal="true"` + `aria-labelledby` — the shape D-02 repeats; no new abstraction over it is needed.
- `useBlocker` (already available in the installed `react-router-dom` `^7.18.3`) — the in-app guard primitive; usable **only** under a data router (D-09).
- `UNSAVED_LEAVE_CONFIRM` / `RESET_CONFIRM` constants — the locked copy already lives in the page; the leave copy moves into the modal, the reset copy stays where it is (D-08).
- The `dirty` derivation and `onSave` success/failure branches already implement D-12's contract; the guard consumes that signal rather than re-deriving dirtiness.

### Established Patterns
- **Dirty-gating is already authoritative in the page**: `dirty = yaml !== savedYaml`, the Save/Reset buttons are disabled when clean, and `status` carries `clean`/`dirty`/`saving`/`saved`/`failed`. The guard must key off exactly this signal — not a second, independent "touched" flag (Pitfall 5a/5b).
- **The Playwright suite green-lights the broken handler** by dispatching a synthetic `beforeunload` and asserting a dialog. The amended test must assert the *contract* (dirty-scoped attach, flag set, removal on unmount/save) — verified by DOM behaviour, not by native dialogs.
- **Modals in this project are DOM, not `window.confirm`** — which is what makes the in-app guard fully DOM-testable (click «Остаться»/«Уйти без сохранения»).
- **`window.confirm` remains legitimate outside `beforeunload`** (the reset path) — the prohibition in D-05 is specific to the unload handler.

### Integration Points
- `web/src/pages/AdminPipelineConfigPage.jsx` → the guard hook (D-07) → modal component, all inside the editor subtree; **no** service, router, or backend call is added.
- `web/src/App.jsx` → data-router migration (D-09) is the **separate** plan that must land green *before* the guard is wired.
- `tests/admin.spec.js` → the amended tripwire test + new SPA-navigation/save/reject tests; the `web` Playwright project runs with `VITE_USE_MOCKS=true`, so all guard behaviour here is reproducible in the browser suite (no backend needed).
- `ADUX-10` (Phase 23) → consumes the extracted hook (D-07); the guard must stay green there.

</code_context>

<specifics>
## Specific Ideas

- **Required `beforeunload` contract** (verbatim from the research): the handler does exactly two things — `event.preventDefault()` and `event.returnValue = true` (truthy; `returnValue` as a *user-visible message* is deprecated and ignored by modern browsers). Nothing else. It is attached only when dirty and removed on unmount and after a successful save.
- **The Russian copy travels with the article of state that owns it**: the leave copy «Есть несохранённые изменения. Уйти без сохранения?» moves into the in-app modal; the reset copy «Отменить изменения и вернуть последнюю сохраненную версию?» stays with `window.confirm`.
- **Division of labour, recorded explicitly:** `beforeunload` covers reload/close/tab; the router blocker covers in-app navigation and explicitly does *not* cover hard reloads or cross-origin navigation. Both are required; neither alone is sufficient.
- **Warning signs to grep for in review:** `window.confirm` still inside a `beforeunload` listener; any test asserting a `dialog` or `defaultPrevented` after a *synthesised* `beforeunload`; `BrowserRouter` still imported while `useBlocker` is used; `useBlocker must be used within a data router` in the console.
- **Full-suite runs must first clear a stale Vite server** on `127.0.0.1:5174` (STATE blocker): mass `ERR_CONNECTION_REFUSED` is the recurring false-regression signature; a clean re-run has produced 110 passed every time.

</specifics>

<deferred>
## Deferred Ideas

- **«Сохранить и выйти» (save-then-navigate) as a third modal action** — deliberately not shipped in Phase 19. It adds a new failure path (an async save that fails or is rejected must prevent the navigation) and is not required by `ADUX-09`. Candidate backlog item for `/gsd-review-backlog`.
- **`sessionStorage` draft recovery** — persisting the in-progress YAML so even a *confirmed* reload/close does not lose the typed text. This is a new capability (draft storage), not a guard, and is outside `ADUX-09`. Candidate backlog item.

</deferred>

---

*Phase: 19-unsaved-changes-guard-for-the-pipeline-editor*
*Context gathered: 2026-10-15*
