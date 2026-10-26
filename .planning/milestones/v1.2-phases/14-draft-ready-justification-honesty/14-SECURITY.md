---
phase: "14"
slug: "draft-ready-justification-honesty"
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-03"
---

# Phase 14 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|----------------|
| Admin JWT → POST /admin/materials/{id}/ready | Only admins may flip triage status | Material id → status-only ready write |
| Use-case → MaterialRepository | Status write must not stamp publish metadata | with_ready_status / published_at unchanged |
| Admin JWT → POST /admin/materials/ready | Batch status writes stay admin-only | material_ids[] → per-id outcomes |
| Batch JSON body → MarkReadyBatchRequest | Mass-assign blocked by extra=forbid | Declared fields only |
| Browser → adminApi ready endpoints | Token + admin-only; UI must not invent business labels | Bearer + AdminApiError |
| Shortlist DTO factor_labels → caption | Display-only honesty contract | factor_labels → factorText / D-15 empty copy |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-14-01 | Elevation of Privilege | POST /admin/materials/{id}/ready | high | mitigate | Depends(require_admin); employee 403 unit proof | closed |
| T-14-02 | Tampering | mark_material_ready / with_ready_status | high | mitigate | Status-only replace; published_at unchanged; never publish_material/as_ready/index (D-06) | closed |
| T-14-03 | Information Disclosure | 404 missing material | medium | mitigate | Stable detail material_not_found; no row leakage beyond accepted admin existence probe | closed |
| T-14-04 | Elevation of Privilege | POST /admin/materials/ready | high | mitigate | Depends(require_admin); employee 403 proof | closed |
| T-14-05 | Tampering | MarkReadyBatchRequest | medium | mitigate | ConfigDict(extra="forbid"); 422 on unknown fields | closed |
| T-14-06 | Information Disclosure | batch per-id errors | low | accept | Per-id material_not_found without leaking other materials' payloads — acceptable admin probe surface | closed |
| T-14-07 | Spoofing | factorText / factor_labels display | high | mitigate | Exact D-15 empty copy; never fabricate labels; honest_factor_labels matrix (D-13…D-17) | closed |
| T-14-08 | Tampering | Optimistic ready badge | medium | mitigate | Failure restores draft + toast; silent refetch reconciles; no fake ready on error (UI-SPEC E1) | closed |
| T-14-09 | Elevation of Privilege | markReady client calls | high | mitigate | Reuse Bearer + AdminApiError; backend require_admin remains source of truth | closed |
| T-14-SC | Tampering | npm/pip/cargo installs | high | mitigate | No package installs in phase plans; gate N/A retained | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

### L1 evidence (grep-depth)

| Threat ID | Evidence |
|-----------|----------|
| T-14-01 | `admin.py` single ready route uses `Depends(require_admin)`; `test_admin_mark_ready_employee_returns_403` |
| T-14-02 | `Material.with_ready_status` + `mark_material_ready`; tests assert `published_at` unchanged; no `publish_material`/`as_ready` call |
| T-14-03 | Single ready HTTP path returns `detail="material_not_found"` on missing material |
| T-14-04 | Batch ready route uses `Depends(require_admin)`; `test_admin_mark_ready_batch_employee_returns_403` |
| T-14-05 | `MarkReadyBatchRequest` has `ConfigDict(extra="forbid")` |
| T-14-06 | `mark_materials_ready` maps missing ids to per-id `error="material_not_found"` only (accepted) |
| T-14-07 | `factorText` returns exact D-15 sentence when `<2` labels; `honest_factor_labels` unit matrix green |
| T-14-08 | `AdminDigestPage` restores `previous` items + toast on markReady/markReadyBatch failure |
| T-14-09 | `adminApi.markReady` / `markReadyBatch` require accessToken / Authorization; map errors via `AdminApiError` |
| T-14-SC | Plan summaries `tech-stack.added: []`; no npm/pip/cargo installs in phase |

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-14-01 | T-14-06 | Batch per-id `material_not_found` reveals existence of requested ids to admins only — same probe surface as single-id 404; no cross-material payload leakage. Low severity; plan disposition accept. | plan disposition (14-02-PLAN) | 2026-10-03 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-03 | 10 | 10 | 0 | gsd-secure-phase (L1 short-circuit) |

## Security Audit 2026-10-03

| Metric | Count |
|--------|-------|
| Threats found | 10 |
| Closed | 10 |
| Open | 0 |

State B create from PLAN.md threat models (plans 01–03) + SUMMARY threat flags (none open). `register_authored_at_plan_time: true`, `asvs_level: 1`, `threats_open: 0` → L1 grep-depth sufficient; auditor not spawned.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-03
