---
phase: "24"
slug: "scheduled-ingestion"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
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
| T1 | 01 | 1 | ING-02 | T-24-01 | Listing port exposes only `video_id` + tz-aware `published`; no publisher capability | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -q` | ✅ amended | ✅ green |
| T2 | 01 | 1 | ING-02 | T-24-01, T-24-02 | Non-200 / broken XML / oversize → `FeedError`; 1 MiB cap before parse; DTD rejected | unit (adapter) | `uv run pytest tests/unit/test_youtube_feed_adapter.py -q` | ✅ existing | ✅ green |
| T3 | 01 | 1 | ING-05 | T-24-08 | `is_newer` strict `>` + `video_id` tie-break; `advance_cursor` monotonic | unit (domain) | `uv run pytest tests/unit/test_schedule_due.py -q` | ✅ existing | ✅ green |
| T4 | 01 | 1 | ING-02 | T-24-04 | `INGEST_TEMPLATE` invalid → `ConfigurationError` at start; no secret printed | unit | `uv run pytest tests/unit/test_ingestion_settings.py tests/unit/test_ingestion_env_example.py -q` | ✅ amended | ✅ green |
| T5 | 01 | 1 | ING-02, ING-05 | T-24-07 | Sources read only from DB (`is_enabled`), never argv; SDK errors mapped at adapter boundary | unit (adapter contract) | `uv run pytest tests/unit/test_supabase_collect_sources_contract.py -q` | ✅ existing | ✅ green |
| T6 | 01 | 1 | ING-02, ING-05 | T-24-07 | Batch writes drafts + pending shortlist only; every `FeedSkip` gets exactly one stderr line via `emit_diagnostic` | unit (use-case) | `uv run pytest tests/unit/test_collect_batch.py -q` | ✅ existing | ✅ green |
| T7 | 01 | 1 | ING-06 | T-24-07 | Summary only on stdout, diagnostics on stderr, no `✓`; tracer exits 0 | unit (CLI) | `uv run pytest tests/unit/test_collect_cli_contract.py -q` | ✅ existing | ✅ green |
| T8 | 03 | 3 | ING-05 | T-24-10, T-24-11 | Cursor columns + singleton `ingestion_schedule`, RLS enabled, zero policies | text-contract | `uv run pytest tests/unit/test_phase24_migration_013.py -q` | ✅ existing | ✅ green |
| T9 | 05 | 5 | ING-06 | T-24-20, T-24-21 | `require_admin` on GET/PATCH; `extra="forbid"`; `time_of_day` pattern | unit (HTTP) | `uv run pytest tests/unit/test_http_ingestion_schedule.py -q` | ✅ existing | ✅ green |
| T10 | 05 | 5 | ING-06 | T-24-22 | `service_role` client only in composition; 503 when repo absent | unit (wiring) | `uv run pytest tests/unit/test_live_container_wiring.py tests/unit/test_http_ingestion_schedule.py -q` | ✅ existing | ✅ green |
| T11 | 06 | 6 | ING-06 | T-24-41 | UI reaches backend only through `web/src/services/` | Playwright (mock arm) | `npm run test:web -- tests/admin.spec.js -g "automatic collection|ingest source|Источники ингеста"` | ✅ existing | ✅ green |
| T12 | 06 | 6 | ING-06 | T-24-40, T-24-43 | Block order (sources → schedule → YAML); banned words absent; save-on-change; retry wired to page loader | Playwright + PRESERVE tripwire | `npm run test:web -- tests/admin.spec.js -g "automatic collection|pipeline config no execution controls"` | ✅ existing | ✅ green |
| T13 | 04 | 4 | ING-06 | T-24-32, T-24-33, T-24-35 | Unit text contract: `Type=oneshot`, `EnvironmentFile=`, `OnFailure=`, `TimeoutStartSec=`, `RuntimeDirectory=digest-ingest`, `flock -n` on `/run/digest-ingest/lock`, absolute `ingest-collect`, no secrets | text-contract | `uv run pytest tests/unit/test_phase24_systemd_units.py -q` | ✅ existing | ✅ green |
| T14 | 04 | 4 | ING-07 | T-24-31 | Import graph + runtime `sys.modules` never reach publish/send or `backend` | static (AST) + subprocess | `uv run pytest tests/unit/test_phase24_scheduler_guard.py -q` | ✅ existing | ✅ green |
| T15 | 04 | 4 | ING-06 | — | Runbook §4k env keys stay in sync with `.env.example` | text-contract | `uv run pytest tests/unit/test_phase24_systemd_units.py -q -k runbook_4k` | ✅ existing | ✅ green |
| T16 | 02 | 2 | ING-05 | T-24-08 | Window sorted oldest→newest, limit cuts the tail, re-run at feed head makes zero LLM calls | unit (domain + use-case) | `uv run pytest tests/unit/test_schedule_due.py tests/unit/test_collect_batch.py -q` | ✅ existing | ✅ green |
| T17 | 02 | 2 | ING-06 | T-24-07, T-24-09 | Per-video/per-source isolation, `list_enabled_sources()` failure → one line + exit 2, exit codes 0/1/2 | unit (use-case + CLI) | `uv run pytest tests/unit/test_collect_batch.py tests/unit/test_collect_cli_contract.py -q` | ✅ existing | ✅ green |
| T18 | 03 | 3 | ING-06 | T-24-12, T-24-13 | Due gate in `Europe/Moscow`, `last_run_at` always stamped, schedule/stamp failures → one line + exit 2/1 | unit (domain + use-case + CLI) | `uv run pytest tests/unit/test_schedule_due.py tests/unit/test_collect_batch.py tests/unit/test_collect_cli_contract.py tests/unit/test_supabase_collect_sources_contract.py -q` | ✅ existing | ✅ green |
| T19 | 05 | 5 | ING-06 | T-24-21 | `days_of_week` normalization and `time_of_day` validation before persistence | unit (domain/use-case) | `uv run pytest tests/unit/test_ingestion_schedule_domain.py -q` | ✅ existing | ✅ green |
| T20 | 05 | 5 | ING-06 | T-24-22 | Supabase schedule adapter: defaults on missing row, upsert singleton, SDK errors → `PersistenceError` | unit (adapter contract) | `uv run pytest tests/unit/test_supabase_ingestion_schedule_repository_contract.py -q` | ✅ existing | ✅ green |
| — | — | — | ING-07 | — | `ingest <url>` stdout byte-identical | PRESERVE | `uv run pytest tests/unit/test_cli_ingest_contract.py -q` | ✅ existing | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/test_youtube_feed_adapter.py` — ING-02 listing (valid feed, entry without `videoId`, broken `published`, no-namespace doc, HTML instead of XML, > 1 MiB response, chunked without `content-length`)
- [x] `tests/unit/test_schedule_due.py` — ING-05/06 cursor + due
- [x] `tests/unit/test_collect_batch.py` — ING-02/05/06 batch, one stderr line per `FeedSkip`, isolation, limit, zero LLM at feed head, DB-failure exit 2
- [x] `tests/unit/test_collect_cli_contract.py` — ING-06 summary/exit codes (own contract; never touch `test_cli_ingest_contract.py`)
- [x] `tests/unit/test_supabase_collect_sources_contract.py` — source/schedule read, monotonic cursor UPDATE, SDK error mapping
- [x] `tests/unit/test_phase24_migration_013.py` — migration text contract
- [x] `tests/unit/test_phase24_systemd_units.py` — unit-file text contract
- [x] `tests/unit/test_phase24_scheduler_guard.py` — ING-07 (AST + subprocess)
- [x] `tests/unit/test_http_ingestion_schedule.py` — GET/PATCH admin surface (JWT harness copied from `test_http_ingest_sources.py`)
- [x] `tests/unit/test_ingestion_schedule_domain.py` — `days_of_week` normalization, time validation, use-case merge (`24-05` task 1)
- [x] `tests/unit/test_supabase_ingestion_schedule_repository_contract.py` — defaults, singleton upsert, `PersistenceError` mapping (`24-05` task 3)
- [x] `tests/admin.spec.js` — new describe for the schedule block + `resetIngestionScheduleMock`
- [x] **AMEND** `tests/unit/test_data_collection_public_api.py` — `path.name.endswith("cli.py")` and extended `PUBLIC_NAMES`/`__all__`
- [x] **AMEND** `tests/unit/test_ingestion_settings.py` — defaults, `podcast`, `ConfigurationError` for `INGEST_TEMPLATE` / `INGEST_MAX_VIDEOS_PER_SOURCE` (`24-01` task 1)
- [x] **AMEND** `tests/unit/test_ingestion_env_example.py` `REQUIRED_INGESTION_KEYS` — `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE`
- [x] `ingestion-service/.env.example` — two new non-secret keys
- [x] Framework install: none required

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Atom feed shape (namespaces, ~15 entries) | ING-02 | Outbound `www.youtube.com` unreachable from the research environment (`WinError 10054`) | On the VM: `ingest-collect` with one real `UC…` source, confirm drafts appear and summary counts are sane |
| systemd timer actually fires and `flock` blocks overlap | ING-06 | No systemd locally | `systemctl start digest-ingest.timer`, wait one 15-min tick, `journalctl -u digest-ingest` shows a run; start a second run during the first and confirm exit 75 |
| Operator applies migration 013 on the shared VM | ING-05 | `psql` not available locally | Apply `013_*.sql`, then `ingest-collect` on a scheduled slot and verify cursor columns advance |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s for unit
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-18 (Nyquist audit at /gsd-verify-work)

---

## Validation Audit 2026-10-18

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 3 manual-only (live Atom feed, live systemd timer/flock, migration 013 on shared VM) |

**Evidence:** all 17 mapped test artifacts exist. Mapped unit set run together:
`uv run pytest` over the 16 mapped unit files → **227 passed** (7.14 s). Playwright slice:
`npx playwright test --project=web tests/admin.spec.js --grep "automatic collection|ingest source|pipeline config no execution controls"` → **17 passed** (1.1 m) against a fresh mock dev server.

**Harness note (not a code defect):** the first Playwright attempt failed all 17 checks on the
login screen because a stale Vite dev server was already listening on `127.0.0.1:5174` with
`VITE_USE_MOCKS=false` from `web/.env.local`, and `reuseExistingServer` adopted it. Killing that
listener and letting Playwright boot its own `VITE_USE_MOCKS=true` server made the slice green.
This repeats the `.planning/STATE.md` warning: kill the stale listener before a web run.

**Deferred:** `24-UAT.md` test 6 (live run against a real enabled source) is recorded as a
deferred follow-up; `pipeline_ingest_sources` is empty, so there is nothing to collect from.
