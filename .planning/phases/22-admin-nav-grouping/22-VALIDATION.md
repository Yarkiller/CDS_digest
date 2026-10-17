---
phase: "22"
slug: "admin-nav-grouping"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-17"
---

# Phase 22 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | @playwright/test ^1.62.1 |
| **Config file** | `playwright.config.js` (web project → Vite `:5174`, `VITE_USE_MOCKS=true`) |
| **Quick run command** | `npx playwright test tests/admin.spec.js --project=web -g "pipeline config nav|Админ nav|dirty editor blocks|Дайджест"` |
| **Full suite command** | `npx playwright test --project=web` |
| **Estimated runtime** | ~60–180 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command above
- **After every plan wave:** Run `npx playwright test --project=web`
- **Before `/gsd-verify-work`:** Full web suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 22-01-01 | 01 | 1 | ADUX-12 | T-22-01 | Shell: one Админ, no Пайплайн | e2e | `npx playwright test tests/admin.spec.js --project=web -g "pipeline config nav\|Админ nav"` | ✅ AMEND | ⬜ pending |
| 22-01-02 | 01 | 1 | ADUX-12 | T-22-02 | In-page Дайджест\|Пайплайн + active tab | e2e | same file, section-nav cases | ❌ W0 | ⬜ pending |
| 22-02-01 | 02 | 2 | ADUX-12 | T-22-03 | Dirty→tab Дайджест opens Phase 19 dialog | e2e | dirty→Дайджест journey | ❌ W0 | ⬜ pending |
| 22-02-02 | 02 | 2 | ADUX-12 | — | 16-UI-SPEC A-2 amended | docs | file diff / plan verify | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Amend `tests/admin.spec.js` shell «Пайплайн» tripwires (admin presence / employee absence) — scope to landmarks
- [ ] Amend heading asserts for «Shortlist дайджеста» / «Конфиг пайплайна» (D-06 fallout)
- [ ] Add in-page section-nav presence + active-tab assertions (`admin-section-nav` / tab testids)
- [ ] Add dirty→tab «Дайджест» stay/leave journey (D-14)
- [ ] Update comments that claim shell has global «Пайплайн»
- [ ] Doc task: supersede `16-UI-SPEC` A-2 + Route/nav section

*Existing Playwright + Vite web project covers harness; Wave 0 is test/doc amendments, not framework install.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual tab-bar layout at `sm` breakpoint | ADUX-12 | Pixel/layout judgment | Resize to ~640px; confirm in-page tabs, no second top nav bar |

*All functional nav behaviors have automated Playwright verification planned.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
