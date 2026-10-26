---
phase: 26
slug: section-context-anchor-scrolling-and-header-active-state
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-10-22
---

# Phase 26 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Source: `26-RESEARCH.md` § Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Playwright `@playwright/test` 1.62.1 (Chromium) + `node --test` (Node 24.21.0) |
| **Config file** | `playwright.config.js` — `web` project: `testMatch: /(web-app\|auth\|knowledge\|razbory\|admin(-chrome)?)\.spec\.js/`, `baseURL: http://127.0.0.1:5174`, `webServer` with `VITE_USE_MOCKS=true`, `reuseExistingServer: !CI` |
| **Quick run command** | `npx playwright test tests/web-app.spec.js --project=web` |
| **Full suite command** | `npm run test:web` |
| **Static gates** | `npm run test:js` |
| **Build gate** | `npm run build` |
| **Estimated runtime** | quick ≈ 60–90 s; full web suite ≈ 5–8 min |

**Pre-run precondition:** port 5174 must be free (`Get-NetTCPConnection -LocalPort 5174 -State Listen`); a stale server started with `web/.env.local` (`VITE_USE_MOCKS=false`) makes every spec land on the login screen.

---

## Sampling Rate

- **After every task commit:** `npx playwright test tests/web-app.spec.js --project=web`
- **After every plan wave:** `npm run test:web` (+ `npm run test:js` when a gate changed)
- **Before `/gsd-verify-work`:** full suite green, `npm run test:js` green, `npm run build` green
- **Max feedback latency:** 120 seconds (quick run)

---

## Per-Task Verification Map

> Task IDs are indicative — the planner binds them to real plan/task numbers.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 26-??-01 | TBD | 1 | NAV-01 (C-01, C-02b) | — | N/A | E2E | `npx playwright test tests/web-app.spec.js --project=web -g "anchor"` | ❌ W0 | ⬜ pending |
| 26-??-02 | TBD | 1 | NAV-01 (C-02) | — | N/A | E2E | same file (`-g "anchor"`) | ❌ W0 (+ fixture) | ⬜ pending |
| 26-??-03 | TBD | 1 | NAV-01 (C-03) | — | N/A | E2E | same file | ❌ W0 (+ fixture) | ⬜ pending |
| 26-??-04 | TBD | 1 | NAV-01 (C-04, C-05) | — | N/A | E2E | same file, 390×844 and 639×844 | ❌ W0 | ⬜ pending |
| 26-??-05 | TBD | 1 | NAV-01 (C-06) | — | N/A | E2E | same file (+ razbor fixture) | ❌ W0 | ⬜ pending |
| 26-??-06 | TBD | 1 | NAV-01 (C-19) | Tampering (spoofed offset mechanism) | Exactly one offset mechanism in `web/src` | static | `npm run test:js` | ❌ W0 (new gate) | ⬜ pending |
| 26-??-07 | TBD | 2 | NAV-02 (C-08, C-14) | Spoofing (UI-context only) | Pill fill is presentational only | E2E | `npx playwright test tests/web-app.spec.js --project=web` | ❌ W0 | ⬜ pending |
| 26-??-08 | TBD | 2 | NAV-02 (C-09) | — | N/A | E2E | same file | ❌ W0 | ⬜ pending |
| 26-??-09 | TBD | 2 | NAV-02 (C-10) | — | N/A | E2E | same file | ❌ W0 | ⬜ pending |
| 26-??-10 | TBD | 2 | NAV-02 (C-11) | — | N/A | E2E | same file | ❌ W0 | ⬜ pending |
| 26-??-11 | TBD | 2 | NAV-02 (C-12) | — | N/A | E2E | same file (+ `related` fixture) | ❌ W0 | ⬜ pending |
| 26-??-12 | TBD | 3 | NAV-02 (C-13, C-15, C-18, C-20) | Information disclosure (persisted origin) | Direct visit claims nothing | E2E | same file (pins) | ❌ W0 | ⬜ pending |
| 26-??-13 | TBD | 3 | NAV-02 (C-16) | — | Admin surface unaffected | E2E | `npx playwright test tests/admin.spec.js --project=web -g "Админ pill"` | ✅ exists — extend | ⬜ pending |
| 26-??-14 | TBD | 3 | NAV-02 (C-17) | Tampering (DOM injection via marker) | `state.section` compared against 3 literals, never rendered; no storage API | static + artefact | `npm run test:js` + written audit in PLAN | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/web-app.spec.js` — extend the existing TOC `describe` with C-01…C-06 (NAV-01) and C-08…C-20 (NAV-02). Preferred over a new file — `testMatch` would silently skip `tests/section-context.spec.js`.
- [ ] `web/src/data/mock.js` — lengthen `rag-systems.body_markdown` (≥6 headings, ≥1.25 viewports of body below the target, first section still short); lengthen one razbor body (id 3); add one `related` to `sql-dashboards` (it has `body[]`, no `body_markdown`).
- [ ] `tests/unit/test_section_context_gates.js` — new static gate for C-19 / `@theme static` token placement / absence of `localStorage`–`sessionStorage` in the changed files.
- [ ] No framework install needed; no `playwright.config.js` change needed while criteria live in `web-app.spec.js`.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| C-17 static audit artefact | NAV-02 | The closed-list read point is a source review, not a behaviour a browser can observe without forging `history.state` in the router's internal format (UI-SPEC marks it a backstop) | Record in PLAN: where `state?.section` is read, which three literals, that no second read point exists, and that no `localStorage`/`sessionStorage` write was added |

*Everything else has automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 120s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
