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
| T3 | 01 | 1 | ING-05, ING-06 | — | `is_newer` strict `>` + `video_id` tie-break; `is_due` takes injected `tzinfo` | unit (domain) | `uv run pytest tests/unit/test_schedule_due.py -q` | ❌ W0 | ⬜ pending |
| T4 | 01 | 1 | ING-02 | T-24-04 | `INGEST_TEMPLATE` invalid → `ConfigurationError` at start; no secret printed | unit | `uv run pytest tests/unit/test_ingestion_settings.py tests/unit/test_ingestion_env_example.py -q` | ❌ W0 (AMEND) | ⬜ pending |
| T5 | 01 | 1 | ING-02, ING-05 | T-24-07 | Sources read only from DB (`is_enabled`), never argv; SDK errors mapped at adapter boundary | unit (adapter contract) | `uv run pytest tests/unit/test_supabase_collect_sources_contract.py -q` | ❌ W0 | ⬜ pending |
| T6 | 01 | 1 | ING-02, ING-05, ING-06 | T-24-03 | Batch writes drafts + pending shortlist only; per-video and per-source isolation | unit (use-case) | `uv run pytest tests/unit/test_collect_batch.py -q` | ❌ W0 | ⬜ pending |
| T7 | 01 | 1 | ING-06 | — | Readable summary on stdout, diagnostics on stderr, exit codes 0/1/2 | unit (CLI) | `uv run pytest tests/unit/test_collect_cli_contract.py -q` | ❌ W0 | ⬜ pending |
| T8 | 02 | 2 | ING-05 | T-24-06 | Cursor columns + singleton `ingestion_schedule`, RLS enabled, zero policies | text-contract | `uv run pytest tests/unit/test_phase24_migration_013.py -q` | ❌ W0 | ⬜ pending |
| T9 | 04 | 4 | ING-06 | T-24-06 | `require_admin` on GET/PATCH; `extra="forbid"`; `time_of_day` pattern | unit (HTTP) | `uv run pytest tests/unit/test_http_ingestion_schedule.py -q` | ❌ W0 | ⬜ pending |
| T10 | 04 | 4 | ING-06 | T-24-06 | `service_role` client only in composition; 503 when repo absent | unit (wiring) | `uv run pytest tests/unit/test_live_container_wiring.py tests/unit/test_http_ingestion_schedule.py -q` | ❌ W0 | ⬜ pending |
| T11 | 04 | 4 | ING-06 | — | UI reaches backend only through `web/src/services/` | Playwright (mock arm) | `npm run test:web -- tests/admin.spec.js -g "Автоматический сбор"` | ❌ W0 | ⬜ pending |
| T12 | 04 | 4 | ING-06 | — | Block order (sources → schedule → YAML); banned words absent; save-on-change | Playwright + PRESERVE tripwire | `npm run test:web -- tests/admin.spec.js -g "Автоматический сбор|pipeline config no execution controls render"` | ❌ W0 | ⬜ pending |
| T13 | 03 | 3 | ING-06 | T-24-08 | Unit text contract: `Type=oneshot`, `EnvironmentFile=`, `OnFailure=`, `RuntimeMaxSec=`, `flock -n`, absolute `ingest-collect`, no secrets | text-contract | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | ❌ W0 | ⬜ pending |
| T14 | 03 | 3 | ING-07 | T-24-03 | Import graph + runtime `sys.modules` never reach publish/send or `backend` | static (AST) + subprocess | `uv run pytest tests/unit/test_phase24_scheduler_guard.py -q` | ❌ W0 | ⬜ pending |
| T15 | 03 | 3 | ING-06 | — | Runbook documents smoke, diagnosis, manual retry | text-contract | `uv run pytest tests/unit/test_docs_runbook.py -q` (or the runbook test added by this phase) | ❌ W0 | ⬜ pending |
| — | — | — | ING-07 | — | `ingest <url>` stdout byte-identical | PRESERVE | `uv run pytest tests/unit/test_cli_ingest_contract.py -q` | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_youtube_feed_adapter.py` — ING-02 listing (valid feed, entry without `videoId`, broken `published`, no-namespace doc, HTML instead of XML, > 1 MiB response, chunked without `content-length`)
- [ ] `tests/unit/test_schedule_due.py` — ING-05/06 cursor + due
- [ ] `tests/unit/test_collect_batch.py` — ING-02/05/06 batch, isolation, limit, zero LLM on re-run
- [ ] `tests/unit/test_collect_cli_contract.py` — ING-06 summary/exit codes (own contract; never touch `test_cli_ingest_contract.py`)
- [ ] `tests/unit/test_supabase_collect_sources_contract.py` — source/schedule read, monotonic cursor UPDATE, SDK error mapping
- [ ] `tests/unit/test_phase24_migration_013.py` — migration text contract
- [ ] `tests/unit/test_phase24_systemd_units.py` — unit-file text contract
- [ ] `tests/unit/test_phase24_scheduler_guard.py` — ING-07 (AST + subprocess)
- [ ] `tests/unit/test_http_ingestion_schedule.py` — GET/PATCH admin surface (JWT harness copied from `test_http_ingest_sources.py`)
- [ ] `tests/unit/test_ingestion_schedule_use_cases.py` — `days_of_week` normalization, time validation
- [ ] `tests/admin.spec.js` — new describe for the schedule block + `resetIngestionScheduleMock`
- [ ] **AMEND** `tests/unit/test_data_collection_public_api.py` — `path.name.endswith("cli.py")` and extended `PUBLIC_NAMES`/`__all__`
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
