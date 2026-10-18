---
phase: 03
slug: voting-cycle
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-09-20
---

# Phase 03 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| SPA → FastAPI `/voting/*` | Bearer JWT; untrusted topic_id / expected_updated_at | Vote cast payload, ballot snapshot |
| FastAPI → cast_vote / get_ballot | Authn enforced; user_id must be claims.sub | Authenticated identity |
| composition/live.py → Supabase | service_role bypasses RLS — server-only | Votes, cycles, topics |
| Trigger → votes writes | Last-line defense when use-case skipped | INSERT/UPDATE on votes |
| BallotSnapshot → SPA | UI must not recompute leaders/tallies | Public tallies + leaders[] |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-03-01 | Elevation of Privilege | POST /voting/votes | high | mitigate | user_id = claims.sub only; PK (cycle_id, user_id) | closed |
| T-03-02 | Tampering | CastVoteRequest | medium | mitigate | Pydantic extra=forbid; topic ∈ active cycle | closed |
| T-03-03 | Spoofing | votingApi mock/live | high | mitigate | isMocksEnabled(); no silent mock fallback after live fail | closed |
| T-03-04 | Elevation of Privilege | service_role client | high | mitigate | Client only in composition/live.py; never Vite-prefixed | closed |
| T-03-05 | Tampering | closed-cycle votes | high | mitigate | VotingCycleClosedError + DB trigger + 409 CYCLE_CLOSED | closed |
| T-03-06 | Tampering | topic_id other cycle | high | mitigate | Use-case + trigger EXISTS topic.cycle_id match | closed |
| T-03-07 | Tampering | 003 seed SQL | medium | mitigate | WHERE NOT EXISTS / ON CONFLICT DO NOTHING; no TRUNCATE | closed |
| T-03-08 | Information Disclosure | Leader strip tallies | low | accept | Public topic tallies intentional (not ADR-0001 board) | closed |
| T-03-09 | Tampering | Client-side leader badge | medium | mitigate | leaders[] server-only; no topic.leading | closed |
| T-03-10 | Tampering | multi-device CAS | medium | mitigate | expected_updated_at CAS; 409 VOTE_CONFLICT | closed |
| T-03-11 | Denial of Service | idle poll | low | mitigate | No tally polling (D-55) | closed |
| T-03-12 | Denial of Service | PersistenceError | medium | mitigate | 503 voting_unavailable; no stack in detail | closed |
| T-03-SC | Tampering | npm/pypi | low | accept | No new packages in phase plans | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-03-01 | T-03-08 | Public topic tallies on the ballot are intentional product behavior (not ADR-0001 board secrecy) | plan threat_model + UAT post-verify | 2026-09-20 |
| AR-03-02 | T-03-SC | Phase plans introduce no new npm/pypi packages; supply-chain risk accepted at low severity | plan threat_model + UAT post-verify | 2026-09-20 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-20 | 13 | 13 | 0 | gsd-security-auditor (verify-work post) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-20
