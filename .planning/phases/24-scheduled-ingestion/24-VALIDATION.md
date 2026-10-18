---
phase: "24"
slug: "scheduled-ingestion"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-18"
---

# Phase 24 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from `24-RESEARCH.md` § Validation Architecture. Task IDs are provisional until
> `24-*-PLAN.md` exists; the mapping is by behavior, not by task number.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `pytest>=8.3.0` (unit) + `@playwright/test ^1.62.1` (web proof) |
| **Config file** | `pyproject.toml` (`testpaths = ["tests/unit"]`, `pythonpath = ["."]`); `playwright.config.js` (`testDir: "./tests"`, project `web` on `http://127.0.0.1:5174`) |
| **Quick run command** | `uv run pytest tests/unit/test_youtube_feed_adapter.py tests/unit/test_schedule_due.py -q` |
| **Full suite command** | `uv run pytest` then `npm run test:web` (kill stale listener on `127.0.0.1:5174` first — see `.planning/STATE.md`) |
| **Estimated runtime** | unit ~10–30 s; full Playwright `web` project ~2–4 min |

---

## Sampling Rate

- **After every task commit:** run the task's own new test file, then `uv run pytest tests/unit -q`
- **After every plan wave:** run `uv run pytest` and `npm run test:web` (full green before next wave)
- **Before `/gsd-verify-work`:** full unit + full Playwright `web` must be green
- **Max feedback latency:** 30 seconds (unit); live VM smoke (`systemctl start`, `journalctl -u`) is operator-only and not part of the automated gate

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| T1 | 01 | 1 | ING-02 | T-24-01 | Listing port exposes only `video_id` + tz-aware `published`; no publisher capability | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -q` | ❌ W0 (AMEND) | ⬜ pending |
| T2 | 01 | 1 | ING-02 | T-24-01, T-24-02 | Non-200 / broken XML / oversize → `FeedError`; 1 MiB cap before parse; DTD rejected | unit (adapter) | `uv run pytest tests/unit/test_youtube_feed_adapter.py -q` | ❌ W0 | ⬜ pending |
| T3 | 01 | 1 | ING-05 | T-24-08 | `is_newer` strict `>` + `video_id` tie-break; `advance_cursor` monotonic | unit (domain) | `uv run pytest tests/unit/test_schedule_due.py -q` | ❌ W0 | ⬜ pending |
| T4 | 01 | 1 | ING-02 | T-24-04 | `INGEST_TEMPLATE` invalid → `ConfigurationError` at start; no secret printed | unit | `uv run pytest tests/unit/test_ingestion_settings.py tests/unit/test_ingestion_env_example.py -q` | ❌ W0 (AMEND) | ⬜ pending |
| T5 | 01 | 1 | ING-02, ING-05 | T-24-07 | Sources read only from DB (`is_enabled`), never argv; SDK errors mapped at adapter boundary | unit (adapter contract) | `uv run pytest tests/unit/test_supabase_collect_sources_contract.py -q` | ❌ W0 | ⬜ pending |
| T6 | 01 | 1 | ING-02, ING-05 | T-24-07 | Batch writes drafts + pending shortlist only; every `FeedSkip` gets exactly one stderr line via `emit_diagnostic` | unit (use-case) | `uv run pytest tests/unit/test_collect_batch.py -q` | ❌ W0 | ⬜ pending |
| T7 | 01 | 1 | ING-06 | T-24-07 | Summary only on stdout, diagnostics on stderr, no `✓`; tracer exits 0 | unit (CLI) | `uv run pytest tests/unit/test_collect_cli_contract.py -q` | ❌ W0 | ⬜ pending |
| T8 | 03 | 3 | ING-05 | T-24-10, T-24-11 | Cursor columns + singleton `ingestion_schedule`, RLS enabled, zero policies | text-contract | `uv run pytest tests/unit/test_phase24_migration_013.py -q` | ❌ W0 | ⬜ pending |
| T9 | 05 | 5 | ING-06 | T-24-20, T-24-21 | `require_admin` on GET/PATCH; `extra="forbid"`; `time_of_day` pattern | unit (HTTP) | `uv run pytest tests/unit/test_http_ingestion_schedule.py -q` | ❌ W0 | ⬜ pending |
| T10 | 05 | 5 | ING-06 | T-24-22 | `service_role` client only in composition; 503 when repo absent | unit (wiring) | `uv run pytest tests/unit/test_live_container_wiring.py tests/unit/test_http_ingestion_schedule.py -q` | ❌ W0 | ⬜ pending |
| T11 | 06 | 6 | ING-06 | T-24-41 | UI reaches backend only through `web/src/services/` | Playwright (mock arm) | `npm run test:web -- tests/admin.spec.js -g "automatic collection|ingest source|Источники ингеста"` | ❌ W0 | ⬜ pending |
| T12 | 06 | 6 | ING-06 | T-24-40, T-24-43 | Block order (sources → schedule → YAML); banned words absent; save-on-change; retry wired to page loader | Playwright + PRESERVE tripwire | `npm run test:web -- tests/admin.spec.js -g "automatic collection|pipeline config no execution controls"` | ❌ W0 | ⬜ pending |
| T13 | 04 | 4 | ING-06 | T-24-32, T-24-33, T-24-35 | Unit text contract: `Type=oneshot`, `EnvironmentFile=`, `OnFailure=`, `TimeoutStartSec=`, `RuntimeDirectory=digest-ingest`, `flock -n` on `/run/digest-ingest/lock`, absolute `ingest-collect`, no secrets | text-contract | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | ❌ W0 | ⬜ pending |
| T14 | 04 | 4 | ING-07 | T-24-31 | Import graph + runtime `sys.modules` never reach publish/send or `backend` | static (AST) + subprocess | `uv run pytest tests/unit/test_phase24_scheduler_guard.py -q` | ❌ W0 | ⬜ pending |
| T15 | 04 | 4 | ING-06 | — | Runbook §4k env keys stay in sync with `.env.example` | text-contract | `uv run pytest tests/unit/test_phase24_systemd_units.py -q -k runbook_4k` | ❌ W0 | ⬜ pending |
| T16 | 02 | 2 | ING-05 | T-24-08 | Window sorted oldest→newest, limit cuts the tail, re-run at feed head makes zero LLM calls | unit (domain + use-case) | `uv run pytest tests/unit/test_schedule_due.py tests/unit/test_collect_batch.py -q` | ❌ W0 | ⬜ pending |
| T17 | 02 | 2 | ING-06 | T-24-07, T-24-09 | Per-video/per-source isolation, `list_enabled_sources()` failure → one line + exit 2, exit codes 0/1/2 | unit (use-case + CLI) | `uv run pytest tests/unit/test_collect_batch.py tests/unit/test_collect_cli_contract.py -q` | ❌ W0 | ⬜ pending |
| T18 | 03 | 3 | ING-06 | T-24-12, T-24-13 | Due gate in `Europe/Moscow`, `last_run_at` always stamped, schedule/stamp failures → one line + exit 2/1 | unit (domain + use-case + CLI) | `uv run pytest tests/unit/test_schedule_due.py tests/unit/test_collect_batch.py tests/unit/test_collect_cli_contract.py tests/unit/test_supabase_collect_sources_contract.py -q` | ❌ W0 | ⬜ pending |
| T19 | 05 | 5 | ING-06 | T-24-21 | `days_of_week` normalization and `time_of_day` validation before persistence | unit (domain/use-case) | `uv run pytest tests/unit/test_ingestion_schedule_domain.py -q` | ❌ W0 | ⬜ pending |
| T20 | 05 | 5 | ING-06 | T-24-22 | Supabase schedule adapter: defaults on missing row, upsert singleton, SDK errors → `PersistenceError` | unit (adapter contract) | `uv run pytest tests/unit/test_supabase_ingestion_schedule_repository_contract.py -q` | ❌ W0 | ⬜ pending |
| — | — | — | ING-07 | — | `ingest <url>` stdout byte-identical | PRESERVE | `uv run pytest tests/unit/test_cli_ingest_contract.py -q` | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_youtube_feed_adapter.py` — ING-02 listing (valid feed, entry without `videoId`, broken `published`, no-namespace doc, HTML instead of XML, > 1 MiB response, chunked without `content-length`)
- [ ] `tests/unit/test_schedule_due.py` — ING-05/06 cursor + due
- [ ] `tests/unit/test_collect_batch.py` — ING-02/05/06 batch, one stderr line per `FeedSkip`, isolation, limit, zero LLM at feed head, DB-failure exit 2
- [ ] `tests/unit/test_collect_cli_contract.py` — ING-06 summary/exit codes (own contract; never touch `test_cli_ingest_contract.py`)
- [ ] `tests/unit/test_supabase_collect_sources_contract.py` — source/schedule read, monotonic cursor UPDATE, SDK error mapping
- [ ] `tests/unit/test_phase24_migration_013.py` — migration text contract
- [ ] `tests/unit/test_phase24_systemd_units.py` — unit-file text contract
- [ ] `tests/unit/test_phase24_scheduler_guard.py` — ING-07 (AST + subprocess)
- [ ] `tests/unit/test_http_ingestion_schedule.py` — GET/PATCH admin surface (JWT harness copied from `test_http_ingest_sources.py`)
- [ ] `tests/unit/test_ingestion_schedule_domain.py` — `days_of_week` normalization, time validation, use-case merge (`24-05` task 1)
- [ ] `tests/unit/test_supabase_ingestion_schedule_repository_contract.py` — defaults, singleton upsert, `PersistenceError` mapping (`24-05` task 3)
- [ ] `tests/admin.spec.js` — new describe for the schedule block + `resetIngestionScheduleMock`
- [ ] **AMEND** `tests/unit/test_data_collection_public_api.py` — `path.name.endswith("cli.py")` and extended `PUBLIC_NAMES`/`__all__`
- [ ] **AMEND** `tests/unit/test_ingestion_settings.py` — defaults, `podcast`, `ConfigurationError` for `INGEST_TEMPLATE` / `INGEST_MAX_VIDEOS_PER_SOURCE` (`24-01` task 1)
- [ ] **AMEND** `tests/unit/test_ingestion_env_example.py` `REQUIRED_INGESTION_KEYS` — `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE`
- [ ] `ingestion-service/.env.example` — two new non-secret keys
- [ ] Framework install: none required

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Atom feed shape (namespaces, ~15 entries) | ING-02 | Outbound `www.youtube.com` unreachable from the research environment (`WinError 10054`) | On the VM: `ingest-collect` with one real `UC…` source, confirm drafts appear and summary counts are sane |
| systemd timer actually fires and `flock` blocks overlap | ING-06 | No systemd locally | `systemctl start digest-ingest.timer`, wait one 15-min tick, `journalctl -u digest-ingest` shows a run; start a second run during the first and confirm exit 75 |
| Operator applies migration 013 on the shared VM | ING-05 | `psql` not available locally | Apply `013_*.sql`, then `ingest-collect` on a scheduled slot and verify cursor columns advance |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for unit
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
