---
phase: "19"
slug: "unsaved-changes-guard-for-the-pipeline-editor"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-16"
---

# Phase 19 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser SPA → router | Every route reachability decision is made here; a widened route is an authorization surface | Route table / auth layout |
| Router layout → RequireAuth | Auth gate wraps AppShell; composition change could bypass authentication | Session / children |
| Browser window (document unload) → app | beforeunload fires; page code cannot drive prompt text | Dirty flag → preventDefault |
| Router navigation → app state | Navigation intent meets dirty draft | Blocker state |
| App render → DOM | Modal is a new DOM surface | Constant leave copy only |
| window.addEventListener registry | Leaked/duplicated beforeunload traps the user | Handler reference |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-19-01 | Elevation of Privilege | `web/src/App.jsx` route array | high | mitigate | Data-router migration preserves pathless `RequireAuth`+`AppShell` layout and `*`→`/` catch-all; route set unchanged | closed |
| T-19-02 | Tampering | router instance under StrictMode | medium | mitigate | `const router = createBrowserRouter([...])` at module scope; never inside `App()` | closed |
| T-19-03 | Denial of Service (user work) | `useBlocker` under non-data router | medium | mitigate | Migration (19-01) landed and verified before guard (19-02); plans never combined | closed |
| T-19-04 | Denial of Service (leaked handler) | `armBeforeUnload` + guard effect | high | mitigate | Effect keyed on `[dirty]`; removes exact imported handler; body is `preventDefault` + truthy `returnValue` only — no `confirm`/`alert` | closed |
| T-19-05 | Denial of Service (silent draft loss) | `useBlocker` + `UnsavedChangesDialog` | high | mitigate | `useBlocker(Boolean(dirty))` with no carve-out; Stay/Escape → `reset()`, Leave → `proceed()` | closed |
| T-19-06 | Tampering (XSS) | `UnsavedChangesDialog.jsx` | medium | mitigate | Renders constant `UNSAVED_LEAVE_CONFIRM` only; no `dangerouslySetInnerHTML`; props are booleans/callbacks | closed |
| T-19-07 | Denial of Service (session expiry) | `RequireAuth` 401 → login redirect | low | accept | Same blocker intercepts redirect; under mocks RequireAuth short-circuits — documented accepted gap | closed |
| T-19-SC | Tampering | npm / pip / cargo installs | high | accept | Phase installs zero packages — all APIs already present | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-19-01 | T-19-07 | RequireAuth 401 redirect under `VITE_USE_MOCKS` is not browser-reproducible; blocker still intercepts real location changes while dirty; no pathname carve-out added | plan 19-02 / verify-work L1 | 2026-10-16 |
| AR-19-02 | T-19-SC | Zero package installs this phase — package-legitimacy audit N/A | plans 19-01/19-02 | 2026-10-16 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-16 | 8 | 8 | 0 | verify-work → secure-phase L1 short-circuit |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-16
