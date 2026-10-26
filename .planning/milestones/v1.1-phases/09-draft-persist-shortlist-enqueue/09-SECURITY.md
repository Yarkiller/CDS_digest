---
phase: 09
slug: draft-persist-shortlist-enqueue
status: verified
threats_open: 0
asvs_level: 1
created: 2026-09-27
---

# Phase 09 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| LLM JSON → `ArticleDraft.roles` | Untrusted model output is filtered against a closed RoleKind set and falls back to `employee`. | role strings |
| `data_collection.__all__` → importers | New RoleKind internals stay off the public root. | package API |
| `DraftPersistError` → `IngestError.to_dict()` | Operator JSON. Only allowlisted context keys are forwarded. | video_id, slug, batch_id, reason |
| Use-case → PersistPort | Business logic depends on a Protocol, not a concrete adapter. | MaterialDraft / PersistResult |
| `MaterialDraft` → RPC params | Untrusted ids/slug/title are named parameters on a typed Postgres RPC. No string interpolation. | p_* RPC payload |
| supabase SDK → adapter | SDK exceptions may contain raw Postgres text; only reason + allowlisted context are forwarded. | exception metadata |
| RPC grants | Execute restricted to `service_role`; `anon`/`authenticated`/`public` cannot call the write RPC. | privilege grants |
| Env vars → `Settings` | Secrets read once at startup; secret fields use `repr=False`. | SUPABASE_SECRET_KEY, DEEPSEEK_API_KEY |
| `Settings` → client factories | Blank url/key raises `ConfigurationError` before `create_client`. | credentials |
| Fakes → tests | In-memory proofs validate fail-closed behavior without a live database. | PersistPort calls |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-09-01 | Information disclosure | n/a this plan | low | accept | No new secrets in 09-01. `SUPABASE_SECRET_KEY` is not read or logged. | closed |
| T-09-02 | Injection | n/a this plan | low | accept | No RPC/SQL in 09-01. Role values filtered against `{employee, analyst, ds}`. | closed |
| T-09-03 | Elevation / RLS bypass | n/a this plan | low | accept | No schema or privilege change in 09-01. | closed |
| T-09-04 | Tampering / race | n/a this plan | low | accept | No multi-step write in 09-01. | closed |
| T-09-05 | Information disclosure | `map_persist_error` context | medium | mitigate | `mapping/persist.py:26-53` `_CONTEXT_ALLOWLIST` + `_forward_context`; `test_persist_error_mapping.py` plants `s3cr3t-k3y-09` and raw Postgres text | closed |
| T-09-06 | Injection | n/a this plan | low | accept | No RPC/SQL in 09-02. Slug from trusted title + video_id via `python-slugify`. | closed |
| T-09-07 | Elevation / RLS bypass | n/a this plan | low | accept | No schema or privilege change in 09-02. | closed |
| T-09-08 | Tampering / race | `FakeDraftPersister` | low | accept | In-memory fake; real atomicity is the 09-03 RPC. | closed |
| T-09-09 | Information disclosure | Adapter error context | high | mitigate | `supabase_persist.py:76-128` `_safe_context` / `_map_exception` (no `str(exc)`, no env read); message is `persist {reason}` | closed |
| T-09-10 | Injection | `persist_draft_and_enqueue` parameters | high | mitigate | Named `p_*` RPC params; `007_phase9_persist_draft.sql:87-118` `INSERT ... VALUES` with typed parameters (no `EXECUTE`/`format()` of video_id or slug) | closed |
| T-09-11 | Elevation / RLS bypass | RPC grants | high | mitigate | `007_phase9_persist_draft.sql:72` `security invoker`; `214-222` revoke `public`/`anon`/`authenticated`, grant `service_role` | closed |
| T-09-12 | Tampering / race | Persist + enqueue | high | mitigate | Single PL/pgSQL body; `ON CONFLICT (youtube_video_id) DO NOTHING` then lookup/batch/shortlist in the same function | closed |
| T-09-13 | Information disclosure | `Settings` / `.env.example` | high | mitigate | `settings.py:55,59` `field(repr=False)` on `deepseek_api_key` and `supabase_secret_key`; `.env.example` empty placeholders; `test_settings_repr_and_str_omit_secret_fields` | closed |
| T-09-14 | Injection | n/a this plan | low | accept | No new SQL/RPC in 09-04; parameterization lives in 09-03. | closed |
| T-09-15 | Elevation / RLS bypass | Client factories | medium | mitigate | `clients.py:77-81` blank url/key → `ConfigurationError` before `create_client` | closed |
| T-09-16 | Tampering / race | Idempotency/overflow proofs | medium | mitigate | Fake stores by `youtube_video_id`; RPC `ON CONFLICT` in one transaction | closed |

*Status: closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-09-01 | T-09-01 | 09-01 introduces no secrets or logging. | plan-time accept | 2026-09-27 |
| AR-09-02 | T-09-02 | 09-01 has no RPC/SQL; RoleKind is a closed set. | plan-time accept | 2026-09-27 |
| AR-09-03 | T-09-03 | 09-01 has no schema or privilege change. | plan-time accept | 2026-09-27 |
| AR-09-04 | T-09-04 | 09-01 has no multi-step write. | plan-time accept | 2026-09-27 |
| AR-09-06 | T-09-06 | 09-02 has no RPC/SQL; slug is generated from trusted title + video_id. | plan-time accept | 2026-09-27 |
| AR-09-07 | T-09-07 | 09-02 has no schema or privilege change. | plan-time accept | 2026-09-27 |
| AR-09-08 | T-09-08 | Fake atomicity is test-only; live race safety is T-09-12. | plan-time accept | 2026-09-27 |
| AR-09-14 | T-09-14 | 09-04 adds no SQL/RPC; parameterization is T-09-10. | plan-time accept | 2026-09-27 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-09-27 | 16 | 7 | 9 | gsd-security-auditor (first pass: T-09-13 blocking; 8 planned accepts unlogged) |
| 2026-09-27 | 16 | 16 | 0 | orchestrator after T-09-13 `repr=False` fix + accepted-risk log |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-09-27
