---
phase: 10
slug: cli-composition-uat
status: verified
threats_open: 0
asvs_level: 1
created: 2026-10-01
---

# Phase 10 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

ASVS L1 grep verification. Plans `10-01` through `10-05` each contain a `<threat_model>`. Summaries report no threat flags beyond that register. `block_on` is `high`. No open threats at or above that threshold.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Operator argv → Typer | Untrusted URL string and template enum enter the CLI process. | YouTube URL, `TemplateKind` |
| CLI → pipeline ports | Composition injects adapters. Domain and use-cases do not read `os.environ`. Secrets are read only in `Settings.from_env`. | Settings, port calls |
| stdout / stderr | Operators may redirect streams. Secrets must not appear in checkmarks, id lines, or human/JSON errors. | stage names, ids, `IngestError` JSON |
| Pipeline exceptions → stderr | Mapped `IngestError` vs config human text. Raw SDK exceptions must not escape. | allowlisted context |
| Env example / UAT notes | Committed placeholders and operator evidence only. Live secrets stay in gitignored `ingestion-service/.env`. | key names, material ids, slugs |
| RPC params → Postgres | Typed named parameters only. No string-built SQL in Python. | `p_*` payload |
| RPC grants | `service_role`-only execute. `anon` / `authenticated` / `public` revoked. | privilege grants |
| Adapter ← RPC jsonb | Untrusted shape validated. Missing keys become `DraftPersistRpcError`. | `material_id`, `slug`, `batch_id`, `rank`, `already_saved` |
| Operator machine → DeepSeek / YouTube / Supabase | Live UAT uses local secrets. No new HTTP surface; drafts are read on the existing `/admin/digest` path. | outbound API calls |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-10-01 | Information disclosure | `cli.py` stderr/stdout | high | mitigate | `cli.py:27-31` static checkmarks; `79-83` id lines from `PersistResult` only; `71-77` config text or `IngestError.to_dict()`. `url.py:20-32` strips userinfo from diagnostics. `settings.py:55,59` secret fields `repr=False`. | closed |
| T-10-02 | Spoofing / misconfig | `Settings.from_env` | medium | mitigate | No `load_dotenv` under `ingestion-service/`. `settings.py:63-64` reads `os.environ` (or an injected mapping). Blank keys fail in `clients.py` before network. Operator must pass `uv run --env-file ingestion-service/.env` (D-02). | closed |
| T-10-03 | Tampering | `--template` / URL | medium | mitigate | `cli.py:52-55` Typer `TemplateKind` enum. `url.py:9-16,59-61` host allowlist; unknown hosts raise `InvalidYouTubeUrl`. | closed |
| T-10-SC | Tampering | package installs | high | mitigate | `10-01-SUMMARY.md` Auth Gates: typer package-legitimacy `blocking-human` cleared (`approved`) before install. Plans `10-03` and `10-05` install no packages. | closed |
| T-10-04 | Information disclosure | consistency `IngestError.context` | high | mitigate | `ingest_pipeline.py:63-66` context is only `transcript_video_id` and `metadata_video_id`. Message is a fixed mismatch string. | closed |
| T-10-05 | Information disclosure | D-08 human stderr | medium | mitigate | `clients.py:54,93` and `settings.py:22-40` `ConfigurationError` text names key names or constraint text, not values. CLI echoes `str(err)` only for that type. | closed |
| T-10-06 | Spoofing | wrong env file | medium | mitigate | `ingestion-service/.env.example` is empty placeholders. `docs/agents/local-platform-runbook.md` requires `ingestion-service/.env` and forbids the root backend `.env`. | closed |
| T-10-07 | Injection | `persist_draft_and_enqueue` params | high | mitigate | `008_phase10_persist_already_saved.sql` uses typed `p_*` parameters and `INSERT ... VALUES`. No `EXECUTE`/`format()` of `youtube_video_id` or slug. `supabase_persist.py:46-61` passes a named dict to `.rpc()`. | closed |
| T-10-08 | Elevation | RPC grants | high | mitigate | `008:24` `security invoker`; `168-176` `revoke all` from `public`, `anon`, `authenticated`; `grant execute` to `service_role` only. | closed |
| T-10-09 | Tampering / race | `ON CONFLICT DO NOTHING` | high | mitigate | `008:73` `on conflict (youtube_video_id) do nothing`; `75` `v_inserted = row_count`; `88-114` conflict returns stored slug and `already_saved: true`. No Python pre-check. | closed |
| T-10-10 | Information disclosure | adapter errors | high | mitigate | `supabase_persist.py:43` maps with `from None` (raw SDK text dropped). `77-78` context is `slug` + `reason` only. `mapping/persist.py:26-33` allowlist; message is `persist {reason}`. | closed |
| T-10-11 | Information disclosure | live UAT notes | high | mitigate | `10-UAT.md` warns against pasting `SUPABASE_SECRET_KEY` / `DEEPSEEK_API_KEY`. Rows record template, `material_id`, slug, rank, and video-id suffix. Full watch URLs were not stored. | closed |
| T-10-12 | Spoofing / misconfig | env file selection | medium | mitigate | `10-UAT.md` command block and the runbook both require `--env-file ingestion-service/.env` only (CLI-05). | closed |
| T-10-13 | Denial of service | live DeepSeek/YouTube | low | accept | Manual UAT is four videos. The operator can abort. There is no scheduler. See Accepted Risks Log. | closed |
| T-10-14 | Elevation | live RPC grants after push | high | mitigate | `10-05-SUMMARY.md` migrate evidence: one `persist_draft_and_enqueue`; execute is postgres (owner) + `service_role` only; no `anon` / `authenticated` / `public`. SQL grants in `008:168-176` match that check. | closed |

*Status: closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `workflow.security_block_on` count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-10-13 | T-10-13 | Live UAT calls DeepSeek and YouTube for four operator-chosen videos. Volume is bounded, the operator can abort, and no scheduler was added. | plan-time accept (10-04) | 2026-10-01 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-10-01 | 15 | 15 | 0 | orchestrator ASVS L1 (register authored at plan time; auditor skipped) |

Threat flags from `10-01`–`10-03` summaries: none beyond the plan register. `10-04` and `10-05` summaries have no Threat Flags section.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-10-01
