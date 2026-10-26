# Phase 16 — UI Review

**Audited:** 2026-10-04
**Baseline:** `16-UI-SPEC.md` (approved design contract; shadcn not initialized, custom token system)
**Screenshots:** captured — `.planning/ui-reviews/16-20261004-213616/` (`pipeline-empty-desktop.png`, `pipeline-populated-desktop.png`, `pipeline-populated-tablet.png`, `pipeline-populated-mobile.png`, `root-desktop.png`)
**Interaction captures:** off (`workflow.ui_interaction_capture` false in the `<config>` block)

> Screenshot note: the dev server on `:5173` is live-auth mode and redirects `/admin/pipeline` → `/login`. Captures were taken against a mock-mode Vite server (`VITE_USE_MOCKS=true`, `127.0.0.1:5174`, per `playwright.config.js`) with `window.__DIGEST_MOCK_ME_ROLE__ = 'admin'` set by an init script. The first capture pass (login page) was discarded after a hash collision revealed the route was not rendered.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | All locked copy ships verbatim; one undeclared status string («Есть несохранённые изменения»). |
| 2. Visuals | 3/4 | Clear editor focal point; save-failure panel hand-rolls `ErrorPanel` styling instead of reusing it. |
| 3. Color | 2/4 | Accent/danger honored, but the success role is never rendered — «Сохранено» is muted gray. |
| 4. Typography | 2/4 | 5 sizes ship vs the contract's "exactly 4" (`text-sm` is undeclared); `font-medium` expanded onto new controls. |
| 5. Spacing | 3/4 | All spacing maps to the locked scale; minor empty-state padding below the declared 2xl value. |
| 6. Experience Design | 2/4 | Rich state coverage, but the unsaved-changes guard misses in-app SPA navigation (silent edit loss). |

**Overall: 15/24**

---

## Top 3 Priority Fixes

1. **BLOCKER — unsaved edits are silently discarded on in-app navigation.** The dirty guard is `beforeunload`-only (`AdminPipelineConfigPage.jsx:109-121`); clicking any AppShell nav link (Выпуск, Архив, База, …, Админ) unmounts the page without a prompt, and `window.confirm` inside a real `beforeunload` handler is ignored by browsers (the generic prompt shows instead of the locked copy). Fix: add a React Router blocker (`useBlocker`/route blocker or a dirty-guard on shell links) so in-app navigation raises «Есть несохранённые изменения. Уйти без сохранения?», and keep `beforeunload` only for real unloads.
2. **WARNING — the reserved success color is never used.** UI-SPEC reserves the send-green success tint for inline «Сохранено», yet `AdminPipelineConfigPage.jsx:283` styles the status caption uniformly `text-sm text-muted`, so the confirmation (line 236) renders as muted gray (no `155`/green class anywhere). Fix: render the `saved` caption with the success tint (e.g. `text-[oklch(45%_0.13_155)]`) and keep the clean/`saving` captions muted.
3. **WARNING — typography exceeds the declared 4-size scale; ErrorPanel is duplicated.** `text-sm` is used on hints, subhead, status, error rows and buttons (lines 205, 219, 255, 265, 274, 283, 304, 314) — a fifth size the contract forbids; `font-medium` is also expanded onto new controls. Separately, the save-failure block (lines 320-336) re-implements `ErrorPanel.jsx`'s container classes instead of reusing the component. Fix: bind these to `text-base`/`text-xs` per the contract and reuse `ErrorPanel`.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

Verified against the Copywriting Contract — every locked string ships verbatim:
- Eyebrow «Админ» (`AdminPipelineConfigPage.jsx:245`), H1 «Конфиг пайплайна» (246), subhead «Просмотр и правка без запуска пайплайна» (247).
- Primary CTA «Сохранить конфиг» (269), secondary «Отменить изменения» (278).
- Empty state «Конфиг ещё не задан» / «Введите YAML и сохраните — конфиг будет доступен при следующих заходах.» (254-256), placeholder «# YAML конфига пайплайна» (349).
- Load error «Не удалось загрузить конфиг» + «Повторить загрузку» (219, 227).
- Validation heading «Проверьте конфиг перед сохранением» (297); row prefixes `Строка {line}: ` / `{path}: ` via `errorPrefix()` (13-17); fallback «Конфиг не прошёл проверку» (314); save failure «Конфиг не сохранён» + «Повторить сохранение» (325, 332).
- Both confirms are exact: `RESET_CONFIRM` (22) and `UNSAVED_LEAVE_CONFIRM` (25).
- No-execution honesty: grep for the banned controls (Запустить/Выполнить/Запуск/Планировщик/Расписание) returns only «без запуска пайплайна» in the subhead; the Playwright no-execution case is green.

**Finding (WARNING):** the status caption introduces «Есть несохранённые изменения» (`AdminPipelineConfigPage.jsx:237`), a string not in the Copywriting Contract (which defines only saving/saved/clean/failed captions). Harmless but undeclared; either adopt it into the contract or drop it.

### Pillar 2: Visuals (3/4)

- Focal point is unambiguous: the mono editor body (`min-h-[20rem]`, `font-mono`) is the dominant surface; the toolbar sits above it with a solid-accent primary and an outlined secondary — correct hierarchy.
- Empty state renders a bordered card + editor; validation panel renders directly above the editor per the contract.
- No icon-only buttons ship in this phase, so the aria-label/tooltip check is N/A.
- **Finding (WARNING):** the save-failure block (`AdminPipelineConfigPage.jsx:320-336`) duplicates `ErrorPanel.jsx`'s container classes (`rounded-* border-[oklch(70%_0.12_25)] bg-[oklch(96%_0.03_25)] p-4`) instead of reusing the component the UI-SPEC names ("reuse existing ErrorPanel"). It also swaps ErrorPanel's `font-display` heading for `font-sans`. Near-identical styling now, but two sources of the same pattern will drift.

### Pillar 3: Color (2/4)

- **Accent reserved-list honored**: solid accent on «Сохранить конфиг» (`:265`), `text-accent` on both retry links (`:223`, `:330`), `focus-visible:outline-accent` on the editor (`:347`); nav active state unchanged.
- **Danger honored**: error rows use the contract's explicit `text-[oklch(45%_0.14_25)]` (`:304`, `:314`); panels mirror `ErrorPanel`'s tint (`:293`, `:322`).
- **Finding (WARNING → pillar driver):** the success role is entirely absent. UI-SPEC: "Success reserved for: inline saved confirmation «Сохранено» (send-green tint)". The caption at `:283` is unconditionally `text-sm text-muted`; the string «Сохранено» (`:236`) therefore renders muted gray. Grep for the success hue (`155`) in the page returns nothing. A whole declared color role is unimplemented.
- 60/30/10 split reads correctly (paper surface dominant, rule/paper-2 secondary, accent button/links limited).

### Pillar 4: Typography (2/4)

- **Finding (WARNING → pillar driver):** the contract states Phase 16 markup declares "exactly 4 sizes" (`text-xs`, `text-base`, `text-2xl`, `text-3xl`) and "No fifth size". The implementation uses five: `text-xs`, **`text-sm`**, `text-base`, `text-2xl`, `text-3xl`. `text-sm` appears on the subhead, status caption, hints, error rows and button labels (`:181`, `:205`, `:206`, `:219`, `:255`, `:265`, `:274`, `:283`, `:304`, `:314`). This is the exact dimension the UI-SPEC checker signed off as **FLAG**.
- **Finding (minor):** weights are 400/600 plus `font-medium` (500) expanded onto new controls (`:265`, `:274`, `:223`, `:330`). The contract permits 500 only as reuse on existing shared admin controls, "do not expand".
- The mono family is correctly applied as a font choice (not a fifth size) on the editor (`:347`) and error prefixes (`:307`).

### Pillar 5: Spacing (3/4)

- Every spacing utility maps to the locked scale: `mt-2`/`space-y-2` (sm/8), `mt-4` (md/16), `mt-6` (lg/24), `p-3`/`gap-3` (continuity 3/12), `p-4` (md/16), `p-6` (lg/24), `px-5` (continuity 5/20), `min-h-11` (44px a11y lock).
- Arbitrary values are limited to the two contract-declared editor exceptions: `min-h-[20rem]` and `max-h-[60vh]` (`:347`). No other `[px]`/`[rem]` values in the new markup.
- **Finding (minor):** the empty-state block uses `p-6` (24px) while the contract maps empty-state breathing room to `2xl` (48px); the section uses `pb-16` (3xl/64px) which the contract marks "not required on Phase 16 deltas". Both are within the token set, so no off-scale values — just under-using the declared empty-state rhythm.
- Toolbar uses `flex flex-wrap` (`:261`), so the overflow/long-text backstops (Save never pushed off-screen) appear structurally sound.

### Pillar 6: Experience Design (2/4)

- **Strong coverage:** page loading («Загрузка…», `aria-busy`, `:200-211`), load error + retry (`:214-231`), empty state with disabled Save, dirty gating, saving state (`aria-busy` on toolbar, `:261`), inline saved confirmation, save-failure + retry, and the full validation-reject panel with one `pipeline-config-error` row per server error (`role="alert"`, `aria-invalid` on the editor, `:289-317`). Reset and leave both use `window.confirm` with exact copy. No execution control ships. Rejected documents stay editable and dirty (`:162-176`) — no auto-revert.
- **Finding (BLOCKER → pillar driver):** the unsaved-changes guard only registers `beforeunload` (`AdminPipelineConfigPage.jsx:109-121`). React Router has no blocker, so **in-app navigation** between shell routes (the nav pills in `AppShell.jsx`) discards a dirty document with no prompt and no copy — the contract requires confirming "Navigating away … while dirty". The Playwright case (`admin.spec.js:1060-1088`) dispatches a synthetic cancelable `Event("beforeunload")` and stubs the dialog, so it passes while real in-app navigation is unguarded.
- **Finding (WARNING):** calling `window.confirm` inside a `beforeunload` handler is ignored by real browsers (they show a generic prompt), so even on a full unload the locked copy «Есть несохранённые изменения. Уйти без сохранения?» will not actually render in production. The test does not exercise the browser's real beforeunload path.
- **Finding (minor):** `status === 'failed'` maps to an empty caption (`:239-240`), which is intentional (the panel carries the message) but leaves the reserved `.text-sm` slot rendering nothing.

---

## Files Audited

- `web/src/pages/AdminPipelineConfigPage.jsx`
- `web/src/services/pipelineConfigApi.js`
- `web/src/components/AppShell.jsx`
- `web/src/App.jsx`
- `web/src/main.jsx`
- `web/src/components/ErrorPanel.jsx` (reuse baseline)
- `web/src/components/ServiceUnavailable.jsx` (reuse baseline)
- `web/src/index.css` (locked tokens)
- `tests/admin.spec.js` (pipeline-config cases)
- Cross-check: `16-UI-SPEC.md`, `16-CONTEXT.md`, plans/summaries 16-01…16-04

**Registry Safety:** skipped — no `components.json` (shadcn not initialized; UI-SPEC declares no third-party registries).
