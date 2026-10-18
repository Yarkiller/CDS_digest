---
phase: "22"
slug: "admin-nav-grouping"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-18"
---

# Phase 22 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| AppShell → AdminLayout | Single «Админ» link; in-page Дайджест\|Пайплайн | `appRole`, route paths |
| AdminLayout → admin pages | Nested digest/pipeline under pathless layout | Section tab navigation |
| AdminLayout → ForbiddenPage | Employee deep-link may see chrome above Forbidden | No new data surface |
| Browser → Phase 19 leave guard | Dirty pipeline → in-page tab leave | Dirty flag / blocker |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-22-01 | Information Disclosure | AdminLayout on employee deep-link | low | accept | Tabs above ForbiddenPage by design; pages Forbidden; no new data | closed |
| T-22-02 | Spoofing | admin-section-select navigate | medium | mitigate | Hard-coded `/admin/digest` \| `/admin/pipeline` only | closed |
| T-22-03 | Elevation of Privilege | AppShell admin pills | low | mitigate | `appRole === 'admin'` on single «Админ» link; API gates unchanged | closed |
| T-22-04 | Tampering | Dirty→tab navigation | medium | mitigate | Phase 19 dialog; Playwright stay/leave; no carve-out | closed |
| T-22-05 | Repudiation | 16-UI-SPEC A-2 drift | low | mitigate | Explicit SUPERSEDED marker + ADUX-12 pointer | closed |
| T-22-06 | Tampering | `handleSectionTabClick` | medium | mitigate | `preventDefault` only when `section === target` | closed |
| T-22-07 | Spoofing | Shell «Админ» `aria-current` | medium | mitigate | `aria-current="true"`, never `"page"` | closed |
| T-22-08 | Information Disclosure | Employee deep-link chrome | low | accept | Chrome only; IN-03 pins absence of data surfaces | closed |
| T-22-09 | Repudiation | Geometry tests | low | mitigate | Assert `main` + `documentElement` widths + 639px control | closed |
| T-22-SC | Tampering | npm/pip installs | high | mitigate | No new packages this phase | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-22-01 | T-22-01 | Employee deep-link may see AdminLayout section chrome above ForbiddenPage; pages stay Forbidden; no new data surface (UI-SPEC / RESEARCH Pitfall 6). Server `require_admin` remains source of truth. | plan 22-01 / secure-phase L1 | 2026-10-18 |
| AR-22-02 | T-22-08 | Same chrome disclosure; IN-03 pins absence of `admin-digest-page` / shortlist / rows. Intentional layout nesting, not a data leak. | plan 22-03 / secure-phase L1 | 2026-10-18 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-18 | 10 | 10 | 0 | /gsd-secure-phase → gsd-security-auditor L1 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-18
