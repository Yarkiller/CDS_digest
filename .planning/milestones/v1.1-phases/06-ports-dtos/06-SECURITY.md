---
phase: 06
slug: ports-dtos
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-26
---

# Phase 06 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Test → data-collection DTOs | Untrusted string inputs validated by Pydantic | Free-form strings (text, ids, language, URLs) |
| Port fake → unit test | Scripted doubles only; no live network | Scripted Transcript / ArticleDraft |
| Assembler → MaterialDraft | Pure transform; caller supplies provenance_label | Article fields + metadata + label |
| Downstream packages → `data_collection.__all__` | Only six public contracts; no fake/production mix | Public type/port names |
| data-collection vs backend `EMBEDDING_DIM` | Backend owns embedding constant | Constant 1024 / vector schema |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-06-01 | Tampering | Transcript / MaterialDraft / ArticleDraft validators | medium | mitigate | Shared `strip_non_blank` + language 2–10 after strip; blank/whitespace → ValidationError (ASVS V5) | closed |
| T-06-02 | Tampering | `require_material_draft` | high | mitigate | `isinstance(MaterialDraft)`; TypeError on Transcript — `test_material_draft_type_boundary.py` (D-CONTENT-01) | closed |
| T-06-03 | Spoofing | FakeArticleGenerator / FakeTranscriptProvider | high | mitigate | Fakes under `tests_support` only; package `__all__` six names; negative import tests (D-04) | closed |
| T-06-04 | Repudiation | `assemble_material_draft` provenance_label | medium | mitigate | Caller-supplied label only; assembler never invents (D-07/D-08) | closed |
| T-06-05 | Tampering | `published_at` / `source_published_at` None | medium | mitigate | Omit → None OK; copy-through assembler; fail-on-None forbidden (D-13/D-14); naive datetime rejected (WR-03) | closed |
| T-06-06 | Information Disclosure | Transcript.language enum too narrow | low | mitigate | Open string length 2–10 after strip; CAP-01 ru/en preference deferred to Phase 7 | closed |
| T-06-07 | Tampering | Dual public DTO contracts | high | mitigate | Deleted `dto/{youtube,foundry,text_import}.py` + tests; no coexistence (D-01…D-03) | closed |
| T-06-08 | Tampering | Accidental `EMBEDDING_DIM` removal from backend | high | mitigate | `query_embedder.EMBEDDING_DIM = 1024` unchanged; no Phase 6 edits (D-02) | closed |
| T-06-09 | Tampering | Accidental schema migration | medium | mitigate | No Phase 6 commits under `supabase-integration/migrations/` (D-14 deferred to Phase 9) | closed |
| T-06-SC | Tampering | Supply chain | low | accept | No new PyPI packages in Phase 6 plans | closed |

*Status: open · closed · open — below high threshold (non-blocking)*  
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` (high) count toward `threats_open`*  
*Disposition: mitigate · accept · transfer*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-SC | T-06-SC | Phase 6 adds no new third-party packages; existing workspace deps unchanged | plan threat_model (`disposition: accept`) | 2026-09-26 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-26 | 10 | 10 | 0 | gsd-secure-phase (State B → L1 short-circuit) |

**Evidence checked (L1):**
- DTO validators + unit edge tests (T-06-01, T-06-05, T-06-06)
- `require_material_draft` + type-boundary test (T-06-02)
- Public `__all__` whitelist + absent brownfield modules (T-06-03, T-06-07)
- Assembler provenance_label parameter passthrough (T-06-04)
- `backend/.../query_embedder.py` EMBEDDING_DIM=1024 (T-06-08)
- No `06-*` commits touching `supabase-integration/migrations/` (T-06-09)

`register_authored_at_plan_time: true` · `asvs_level: 1` · `threats_open: 0` → auditor deep-pass skipped per secure-phase short-circuit.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-26
