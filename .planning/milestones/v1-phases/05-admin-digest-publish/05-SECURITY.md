---
phase: 05
slug: admin-digest-publish
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-09-22
---

# Phase 05 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

ASVS level 1. Plan-time threat models exist in 05-01…05-09. L1 classification found every `mitigate` control in code or migration, so the auditor spawn was skipped.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| SPA → FastAPI `/admin/*` | Bearer JWT; `profiles.role` is server-side only | Shortlist, decisions, preview, send |
| FastAPI → ProfileRepository | Admin authorization from `profiles.role` | Role check |
| composition/live.py → Supabase | `service_role` bypasses RLS — server-only | Batches, decisions, issues |
| Claim RPC → digest_batches | `sent_at IS NULL` claim; execute granted to `service_role` only | Publish + sent_at |
| Email link → login `returnUrl` | Path must stay on `/issues/{n}` | Issue deep link |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-05-01 | Elevation of Privilege | GET /admin/shortlist | high | mitigate | `require_admin` on admin routes; 403 otherwise | closed |
| T-05-02 | Spoofing | Client-forged /me.role | high | mitigate | Profile reloaded server-side; SPA nav is not the gate | closed |
| T-05-03 | Information Disclosure | Shortlist for employees | medium | mitigate | 403 without shortlist payload | closed |
| T-05-04 | Tampering | score_factors honesty | low | mitigate | `honest_factor_labels` computed in the use-case | closed |
| T-05-05 | Elevation of Privilege | decision route | high | mitigate | `require_admin` on the decision mutation | closed |
| T-05-06 | Tampering | decision body | medium | mitigate | Allowlist pending\|approved\|rejected; Pydantic `extra=forbid` | closed |
| T-05-07 | Spoofing | decided_by | medium | mitigate | Actor is authenticated `CurrentUser`, not a client field | closed |
| T-05-08 | Elevation of Privilege | preview/send routes | high | mitigate | `require_admin` on preview and send | closed |
| T-05-09 | Tampering | double-send race | high | mitigate | Atomic claim `sent_at IS NULL`; repeat send is 409 | closed |
| T-05-10 | Tampering | draft publish | high | mitigate | `DraftInSendPoolError` rejects approved∩draft | closed |
| T-05-11 | Spoofing | email open redirect | medium | mitigate | Issue path `/issues/{n}`; `sanitizeReturnUrl` rejects `//` | closed |
| T-05-12 | Repudiation | delivery honesty | medium | mitigate | Stub delivery status; SMTP fail-fast; UI copy «Отправка записана» | closed |
| T-05-13 | Elevation of Privilege | AdminDigestPage | high | mitigate | Client gate is UX only; mutations stay behind `require_admin` | closed |
| T-05-14 | Information Disclosure | shortlist via mocks | low | accept | Mocks are offline; live path uses JWT + admin | closed |
| T-05-15 | Spoofing | emailPreviewed flag | medium | mitigate | Server re-validates the pool; a failed preview cannot unlock send | closed |
| T-05-16 | Information Disclosure | service_role key | high | mitigate | Client created in composition only; web code never references the key | closed |
| T-05-17 | Elevation of Privilege | claim RPC grants | high | mitigate | Migration 005 revokes PUBLIC/anon/authenticated; grants `service_role` | closed |
| T-05-18 | Tampering | double publish | high | mitigate | Claim `WHERE sent_at IS NULL` / RPC | closed |
| T-05-19 | Tampering | shared VM wipe | medium | mitigate | Idempotent seed; migration 005 has no TRUNCATE | closed |
| T-05-20 | Spoofing | returnUrl in email link | medium | mitigate | `sanitizeReturnUrl` rejects protocol-relative redirects | closed |
| T-05-21 | Elevation of Privilege | admin e2e | high | mitigate | Employee deep-link 403 covered by `tests/admin.spec.js` | closed |
| T-05-G1-01 | Tampering | preview blocks | medium | mitigate | Preview rejects ids outside approved∩ready; route uses `require_admin` | closed |
| T-05-G1-02 | Information Disclosure | preview body | low | accept | Preview returns titles already on the shortlist; intro is admin-authored | closed |
| T-05-G1-03 | Tampering | send material_ids | medium | mitigate | Send requires exact approved∩ready set; extras/missing are 400 | closed |
| T-05-G1-04 | Elevation of Privilege | reorder ranks | medium | mitigate | Rank writes go through the service_role adapter, not client Supabase | closed |
| T-05-G2-01 | Information Disclosure | days_until_next_batch | low | accept | Weekly cadence constant only; no pipeline internals | closed |
| T-05-G2-02 | Spoofing | digest_rest | low | mitigate | Flag derived from `sent_at` behind `require_admin` | closed |
| T-05-SC | Tampering | npm/pypi installs | high | accept | Plans 05-01…05-09 add no packages (07–09 rate this high) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-05-01 | T-05-SC | No new npm/pypi packages in this phase. Later plans rate the same supply-chain accept as high. | plan threat_model | 2026-09-22 |
| AR-05-02 | T-05-14 | Mock shortlist is an offline test path. Live admin reads require JWT and `profiles.role=admin`. | plan threat_model | 2026-09-22 |
| AR-05-03 | T-05-G1-02 | Preview body repeats shortlist titles the admin already sees. Intro text is authored by that admin. | plan threat_model | 2026-09-22 |
| AR-05-04 | T-05-G2-01 | `days_until_next_batch` is the weekly cadence (7), not pipeline or voter data. | plan threat_model | 2026-09-22 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-22 | 28 | 28 | 0 | verify-work L1 (ASVS 1 short-circuit) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-22
