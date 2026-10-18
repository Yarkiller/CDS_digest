---
phase: "12"
slug: "admin-shortlist-empty-batch-contract"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-04"
---

# Phase 12 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Admin JWT → `GET /admin/shortlist` | Only admins may read the shortlist; the empty edges must not weaken auth | Admin identity (JWT), shortlist (materials metadata) |
| Use-case DTO → `AdminShortlistResponse` | Undeclared fields must not serialize (`extra="forbid"`) | Shortlist DTO (non-secret) |
| Lock doc → executors / verifiers | Docs must not mis-state HTTP shapes (contract drift) | Contract documentation |
| Playwright sticky window flags → mock DTO | Flag leak can falsify empty vs rest UI | Test-harness state (non-secret) |
| Mock DTO → `AdminDigestPage` | Wrong `digest_rest`/empty mix misleads admin triage | Mock DTO (non-secret, Vite harness only) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-12-01 | Information Disclosure | `AdminShortlistResponse` construction | high | mitigate | `ConfigDict(extra="forbid")` retained (`admin.py:66`, item model `:47`); required-key tests assert declared empty fields only (`test_http_admin.py:261-297`, `:300-343`); `_to_response` passes only declared fields (`admin.py:244-269`) | closed |
| T-12-02 | Elevation of Privilege | `read_admin_shortlist` | high | mitigate | `Depends(require_admin)` retained (`admin.py:344-347`); guard enforces `profiles.role` not the JWT claim (`deps.py:53-70`); tests mint admin JWT, never bypass auth, and assert 401/403 negatives | closed |
| T-12-03 | Denial of Service | Empty-unsent schema path | medium | mitigate | Both empty shapes assert HTTP 200 + `items == []` (`test_http_admin.py:281,295,327,338`); use-case present-unsent branch returns a valid DTO (`get_admin_shortlist.py:61-67`), so schema validation cannot raise 500 | closed |
| T-12-04 | Tampering | `12-FIX-01-LOCK.md` vs live tests | medium | mitigate | Lock tables mirror D-04/D-08 (Shapes 1–2, assert rules, `extra="forbid"` posture); both proof names present and match the live node ids (`test_http_admin.py:261`, `:300`) | closed |
| T-12-05 | Repudiation | REQUIREMENTS/ROADMAP proof strings | low | accept | Docs-only; historical archives left intact by design — see Accepted Risks Log | closed |
| T-12-06 | Tampering | `resetAdminHarness` / sticky flags | medium | mitigate | `resetAdminHarness` clears `window.__DIGEST_ADMIN_EMPTY_UNSENT__ = false` (`adminApi.js:191`); `gotoAsRole` re-applies `extraInit` after reset (`tests/admin.spec.js:39-47`) | closed |
| T-12-07 | Spoofing | empty-unsent vs digest_rest mock | medium | mitigate | Flag precedence DIGEST_REST → EMPTY_UNSENT → EMPTY (`adminApi.js:246,249,252`); Playwright asserts `admin-digest-rest` count 0 on empty-unsent (`tests/admin.spec.js:164`) | closed |
| T-12-08 | Information Disclosure | Mock DTO fields | low | accept | Mocks are Vite test harness only; no production secret surface — see Accepted Risks Log | closed |
| T-12-SC | Tampering | npm/pip/cargo installs | high | mitigate | No package installs in this plan; no dependency manifests touched. Gate N/A — retained per phase SC reservation | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-12-01 | T-12-05 | Documentation-only surface (REQUIREMENTS/ROADMAP proof strings); historical archives intentionally left intact — no production impact | gsd-security-auditor (PLAN threat register) | 2026-10-04 |
| AR-12-02 | T-12-08 | Mock DTO fields live only in the Vite test harness; no production secret surface is reachable through them | gsd-security-auditor (PLAN threat register) | 2026-10-04 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-04 | 9 | 9 | 0 | gsd-security-auditor (ASVS L1, block_on=high) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-04
