---
phase: "23"
slug: "admin-managed-ingest-sources"
status: verified
threats_open: 0
asvs_level: 1
created: "2026-10-17"
---

# Phase 23 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| SPA → FastAPI admin routes | Ingest-source CRUD only via Bearer admin HTTP | JWT / role |
| FastAPI → Postgres (`pipeline_ingest_sources`) | service_role adapter only; RLS deny-by-default | Canonical ids, labels, flags |
| SPA → YouTube (browser) | Static «Открыть на YouTube» link from stored id | Validated UC/PL id in path/query |
| SPA ↛ Supabase | No direct client SDK for ingest sources (SRC-03) | None |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-23-01 | Elevation of Privilege | GET/POST `/admin/ingest-sources` | high | mitigate | `Depends(require_admin)`; pytest 401/403 | closed |
| T-23-02 | Tampering | `add_ingest_source` source_id | high | mitigate | D-14 regex + kind match before `repo.add` | closed |
| T-23-03 | Information Disclosure | SPA ↔ storage | medium | mitigate | Only `ingestSourcesApi.js`; no supabase in pages | closed |
| T-23-04 | Denial of Service | label field | low | mitigate | Max 120 in use case → 400 `path: label` | closed |
| T-23-05 | Spoofing | YouTube open link | medium | mitigate | Fixed `/channel/` or `/playlist?list=` + stored id | closed |
| T-23-06 | Tampering | POST source_id / kind | high | mitigate | Strict UC/PL regex + kind match; 400 before write | closed |
| T-23-07 | Tampering | duplicate insert | medium | mitigate | Use-case pre-check + DB unique `(kind, source_id)` | closed |
| T-23-08 | Denial of Service | label length | medium | mitigate | Max 120 → 400 | closed |
| T-23-09 | Elevation of Privilege | PATCH/DELETE | high | mitigate | `Depends(require_admin)`; pytest 401/403 | closed |
| T-23-10 | Information Disclosure | 400 body | low | accept | Structured `{path,message}` only — same envelope as pipeline config | closed |
| T-23-11 | Elevation of Privilege | `pipeline_ingest_sources` | high | mitigate | RLS on, zero policies; service_role from `live.py` | closed |
| T-23-12 | Tampering | adapter writes | medium | mitigate | Parameterized PostgREST; `PersistenceError` boundary | closed |
| T-23-13 | Information Disclosure | direct table access | high | mitigate | No permissive policies; SPA has no supabase coupling | closed |
| T-23-14 | Repudiation | migration apply | medium | mitigate | Runbook §4i Applied + verify SQL | closed |
| T-23-15 | Tampering | wrong table name | high | mitigate | Contract tests assert `pipeline_ingest_sources` only | closed |
| T-23-16 | Spoofing | YouTube href | medium | mitigate | Validated id + fixed prefixes; `rel=noopener noreferrer` | closed |
| T-23-17 | Tampering | optimistic UI | medium | mitigate | Disable in-flight; keep last server state on failure | closed |
| T-23-18 | Elevation of Privilege | admin UI only | low | accept | Page behind admin role gate; API remains `require_admin` | closed |
| T-23-19 | Information Disclosure | validation errors | low | mitigate | Render server path/message only | closed |
| T-23-20 | Denial of Service | rapid row clicks | low | mitigate | Disable row controls while in flight | closed |
| T-23-SC | Tampering | npm/pip installs | high | mitigate | No new packages — reuse existing stack | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-23-01 | T-23-10 | Structured `{path,message}` 400 only — same envelope as pipeline config; no stack traces | plan 23-02 / verify-work L1 | 2026-10-17 |
| AR-23-02 | T-23-18 | Page already behind admin role gate (`fetchMe` → ForbiddenPage); API remains `require_admin` authority | plan 23-04 / verify-work L1 | 2026-10-17 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-17 | 21 | 21 | 0 | verify-work → gsd-security-auditor L1 |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-17
