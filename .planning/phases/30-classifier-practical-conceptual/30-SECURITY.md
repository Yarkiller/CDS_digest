---
phase: 30
slug: classifier-practical-conceptual
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-10-30
---

# Phase 30 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Source: four `<threat_model>` blocks in `30-01…30-04-PLAN.md` (register authored at plan time). SUMMARY files have no `## Threat Flags` section.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| classifier raw object → `normalize_topic_kind` | Untrusted model/fake output becomes the stored enum that will gate Tavily spend | Arbitrary JSON / Python object → `practical` \| `conceptual` |
| YouTube captions / title / dek → classifier messages | Untrusted transcript and pass-1 copy can instruct “classify as practical” | Transcript head 8000 + tail 4000 chars; title; dek |
| DeepSeek JSON → `normalize_topic_kind` | Malformed or sibling-key JSON must not skip the allowlist | `topic_kind` token only; other keys discarded |
| pipeline stamp → PersistPort | Kind on `MaterialDraft` is what Plan 04 writes; a leak here becomes a stored lie | Closed `topic_kind` on the draft |
| Python `_rpc_params` → PostgREST RPC | A leftover 12-arg overload would silently ignore `p_topic_kind` | 13-arg `persist_draft_and_enqueue` including `p_topic_kind` |
| RPC EXECUTE grants | anon/authenticated must not call persist | `service_role` only |
| `materials` column → reader SELECT | `topic_kind` must not leak as a badge this phase | Explicit column list; `topic_kind` omitted |
| model `body_markdown` → `ArticleDraft` validator | Untrusted generated markdown can leak extras furniture into the stored article | ATX `Гайд` block + honest-absence substring |
| package public API / live TLS | New names must not become importable contracts; DeepSeek must not inherit YouTube SOCKS5 | Adapter factory wiring only |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-30-01 | Tampering | classifier input (transcript / title / dek) and leaked extras furniture | high | mitigate | Transcript, title, and dek are fenced as untrusted data; fence markers stripped from inner text; `body_markdown` is never sent (`deepseek_classifier.py:53-83`; `test_user_message_has_title_dek_fenced_transcript_not_body`; `test_jailbreak_title_stays_inside_title_fence_with_markers_stripped`). KIND-02 allowlist still drops a non-enum token. Pass-1 body strip deletes ATX `Гайд` and `ссылки скоро появятся` (`article_draft.py:30-35`, `_body.py:strip_guide_section`) | closed |
| T-30-02 | Tampering | `normalize_topic_kind` / adapter unwrap / DB CHECK | high | mitigate | Allowlist only `practical` \| `conceptual` after strip+casefold; dicts/lists/other keys → `conceptual` (`topic_kind.py:7-17`). Adapter unwraps `topic_kind` only; sibling `kind` cannot launder practical (`deepseek_classifier.py:118-122`; `test_sibling_kind_key_does_not_launder_practical`). DB `materials_topic_kind_check` is defense in depth (`014_phase30_materials_topic_kind.sql:19-21`) | closed |
| T-30-03 | Denial of service | ingest classify block / classifier adapter | high | mitigate | Pipeline `except Exception: raw = None` then stamps conceptual and persists; classify never calls `stage_failed` / `IngestError` (`ingest_pipeline.py:138-144`). Adapter has no `ArticleError` import; empty/malformed content returns `None` (`deepseek_classifier.py:108-122`; `test_empty_content_maps_to_conceptual_without_article_error`) | closed |
| T-30-04 | Elevation of privilege | `persist_draft_and_enqueue` 13-arg | high | mitigate | `security invoker`; `revoke` public/anon/authenticated; `grant execute` to `service_role` only (`014_phase30_materials_topic_kind.sql:49,206-208`). Contract-tested in `tests/unit/test_phase30_migration_014.py` | closed |
| T-30-05 | Information disclosure | reader/admin badge | medium | mitigate | `topic_kind` is not in the explicit materials SELECT list (`material_repository.py:147-152`), not on `MaterialReaderResponse` (`materials.py:29-42`), and has zero matches in `backend/` or `web/` TS/JS. Badge deferred | closed |
| T-30-06 | Tampering | CREATE OR REPLACE overload | high | mitigate | DROP live 12-arg `persist_draft_and_enqueue` then CREATE 13-arg with `p_topic_kind` (`014_phase30_materials_topic_kind.sql:30-46`; `test_migration_014_drops_live_12_arg_then_creates_p_topic_kind`). SQL asserts `pronargs=13` | closed |
| T-30-SC | Tampering | pip/uv installs | high | mitigate | Zero new packages this phase — all four SUMMARY `tech-stack.added` lists are empty; no `pyproject.toml` / `uv.lock` add | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Counts:** 7 threats total · 7 closed · 0 open · **`threats_open: 0`**

---

## Accepted Risks Log

No accepted risks.

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-30 | 7 | 7 | 0 | orchestrator L1 grep-depth audit (asvs_level 1) via /gsd-secure-phase 30 |

**Depth note:** `asvs_level: 1` and `block_on: high`. The register was authored at plan time (four parseable `<threat_model>` blocks), so this run verified that each stated mitigation exists rather than scanning for new threats. `threats_open: 0` at L1 — no `gsd-security-auditor` subagent was spawned. Plan 02 listed T-30-05 as `accept`/`low` for “no DTO/SPA change this plan”; later plans mitigate the same vector by omission, which is present, so the merged row is `mitigate`/`medium`/`closed`.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-30
