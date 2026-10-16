---
phase: "19"
slug: "unsaved-changes-guard-for-the-pipeline-editor"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-16"
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `@playwright/test` `^1.62.1` (browser journeys) + built-in `node --test` on Node 24.21.0 (pure helper contract) |
| **Config file** | `playwright.config.js` (project `web`, `testMatch: /(web-app\|auth\|knowledge\|razbory\|admin)\.spec\.js/`, `webServer.env.VITE_USE_MOCKS: "true"`, `reuseExistingServer: !process.env.CI`) |
| **Quick run command** | `node --test tests/unit/test_unsaved_changes_guard.js` |
| **Full suite command** | `npx playwright test --project=web` |
| **Estimated runtime** | ~Unit <1 s; focused browser ~20–40 s; full `web` project ~2–4 min |

**Operational precondition (STATE.md blocker):** before any full-suite run, `Get-NetTCPConnection -LocalPort 5174 -State Listen` must return nothing. A stale long-lived Vite server makes every `web` test fail with `ERR_CONNECTION_REFUSED`, indistinguishable from a real regression unless the error text is read.

---

## Sampling Rate

- **After every task commit:** Run `node --test tests/unit/test_unsaved_changes_guard.js`; once the guard is wired, `npx playwright test --project=web tests/admin.spec.js -g "pipeline config"`
- **After every plan wave:** Run `npx playwright test --project=web`
- **Before `/gsd-verify-work`:** Full `web` project must be green, with the passed count equal to the Wave-0 baseline
- **Max feedback latency:** <1 s (unit) / <60 s (focused browser)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 (router migration) | 1 | ADUX-09 (criterion 4) | T-19-03 | Behaviour-preserving refactor; no route added/removed/loosened | e2e (regression gate) | `npx playwright test --project=web` (count equal to Wave-0 baseline) | ✅ existing suite | ⬜ pending |
| 19-01-02 | 01 (router migration) | 1 | ADUX-09 (criterion 4) | T-19-03 | `App.jsx` renders via `createBrowserRouter` + `RouterProvider`; `RequireAuth`/`AppShell` wrapping preserved | e2e (regression gate) | `npx playwright test --project=web` | ✅ existing suite | ⬜ pending |
| 19-02-01 | 02 (guard) | 2 | ADUX-09 (criterion 2, handler body) | T-19-04 | `armBeforeUnload` calls `preventDefault()` and sets truthy `returnValue`; contains no `window.confirm` | unit | `node --test tests/unit/test_unsaved_changes_guard.js` | ❌ W0 | ⬜ pending |
| 19-02-02 | 02 (guard) | 2 | ADUX-09 (criterion 2, dirty) | T-19-04 | A dirty editor arms the browser's `beforeunload` prompt | e2e | `npx playwright test --project=web tests/admin.spec.js -g "unsaved-leave guard"` | ✅ `tests/admin.spec.js:1143` — **AMEND** | ⬜ pending |
| 19-02-03 | 02 (guard) | 2 | ADUX-09 (criterion 2, clean) | — | A clean editor prompts on neither path | e2e | `npx playwright test --project=web tests/admin.spec.js -g "unsaved-leave guard"` | ✅ **AMEND** | ⬜ pending |
| 19-02-04 | 02 (guard) | 2 | ADUX-09 (criterion 1) | T-19-05 | In-app SPA nav while dirty prompts with «Есть несохранённые изменения. Уйти без сохранения?»; Cancel keeps the draft | e2e | `npx playwright test --project=web tests/admin.spec.js -g "blocks in-app nav"` | ❌ W0 | ⬜ pending |
| 19-02-05 | 02 (guard) | 2 | ADUX-09 (criterion 1) | T-19-05 | Confirming navigates exactly once; no double prompt on the SPA path | e2e | `npx playwright test --project=web tests/admin.spec.js -g "navigates once"` | ❌ W0 | ⬜ pending |
| 19-02-06 | 02 (guard) | 2 | ADUX-09 (criterion 3) | T-19-04 | Dirty clears after a successful save (no prompt); stays armed after an `INVALID_CONFIG` reject (prompts) | e2e | `npx playwright test --project=web tests/admin.spec.js -g "save disarms"` | ❌ W0 | ⬜ pending |
| 19-02-07 | 02 (guard) | 2 | D-08 (PRESERVE) | — | The two reset-confirm tests stay byte-identical and green | e2e | `npx playwright test --project=web tests/admin.spec.js -g "reset confirm"` | ✅ existing — **PRESERVE** | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Out of scope (deliberately not validated here):** `ADUX-10` — the ingest-sources editor guard ships in Phase 23; the ROADMAP records the gap as intentional.

---

## Wave 0 Requirements

- [ ] `tests/unit/test_unsaved_changes_guard.js` — the `armBeforeUnload` body contract (covers criterion 2's handler contract).
- [ ] `web/src/utils/unsavedChangesGuard.js` — production module the unit test imports (RED first: create the test, run it, watch the import fail).
- [ ] `tests/admin.spec.js` — amend the tripwire (`:1143-1171`) AND add the three new journeys; do **not** delete the existing title.
- [ ] `tests/admin.spec.js` — a listener-registry spy (`page.addInitScript` wrapping `window.addEventListener`/`removeEventListener` for `'beforeunload'`) **only if** the real-prompt path proves unreproducible (research Assumption A2 fallback). Prefer the real prompt (`page.close({ runBeforeUnload: true })`).
- [ ] **Migration baseline:** run `npx playwright test --project=web` on the untouched tree in Plan 1's Wave 0 and record the number (do not assume STATE.md's 110).
- [ ] Framework install: **none.** Everything is installed (`@playwright/test` `^1.62.1`, Node 24.21.0 `node --test`).

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The `RequireAuth` 401 → `/login?returnUrl=…` redirect is also blocked while dirty (D-04, no pathname carve-out) | ADUX-09 (criterion 1) | Not browser-reproducible under `VITE_USE_MOCKS=true` — the mocks short-circuit `RequireAuth`, so the redirect path is unreachable in the `web` project. The claim holds by reachability reasoning (`useBlocker`'s default predicate, its cleanup), recorded as a deliberate, accepted gap in the research (Open Question 2). | Not manually verifiable in-suite. If it ever becomes reachable under mocks, add a focused Playwright journey asserting the modal appears before any `/login` navigation. Do **not** add a pathname carve-out. |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
