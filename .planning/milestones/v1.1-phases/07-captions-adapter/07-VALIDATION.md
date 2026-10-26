---
phase: 7
slug: captions-adapter
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-26
validated: 2026-10-02
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | root `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths = ["tests/unit"]` |
| **Quick run command** | `uv run pytest tests/unit/test_extract_video_id.py tests/unit/test_ingest_error.py tests/unit/test_youtube_transcript_adapter.py tests/unit/test_captions_error_mapping.py tests/unit/test_fake_transcript_provider_failures.py tests/unit/test_youtube_oembed_adapter.py tests/unit/test_metadata_error_mapping.py tests/unit/test_fake_video_metadata_provider.py tests/unit/test_ingestion_settings.py tests/unit/test_data_collection_public_api.py -x` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run targeted new unit file(s) with `-x`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-W0 | 01 | 1 | CAP-01/CAP-02 | — | N/A | infra | register `integration` marker; scaffold deps (07-01) | ✅ | ✅ green |
| 07-url | 01 | 1 | CAP-01 | T-07-SSRF | Allowlist YouTube URL forms; reject non-YouTube | unit | `uv run pytest tests/unit/test_extract_video_id.py -x` | ✅ | ✅ green |
| 07-err | 01 | 1 | CAP-01 | T-07-REASON | IngestError envelope + map_url_error stage=url | unit | `uv run pytest tests/unit/test_ingest_error.py -x` | ✅ | ✅ green |
| 07-cap | 01 | 1 | CAP-01/CAP-02 | T-07-FAILCLOSED | Mocked captions happy path + no_preferred/empty | unit | `uv run pytest tests/unit/test_youtube_transcript_adapter.py -x` | ✅ | ✅ green |
| 07-map | 02 | 2 | CAP-02 | T-07-REASON | Locked reason codes; fail-closed CaptionsError | unit | `uv run pytest tests/unit/test_captions_error_mapping.py tests/unit/test_youtube_transcript_adapter.py -x` | ✅ | ✅ green |
| 07-d15 | 02 | 2 | D-15 | — | FakeTranscriptProvider additive failures | unit | `uv run pytest tests/unit/test_fake_transcript_provider_failures.py tests/unit/test_transcript_provider_fake.py -x` | ✅ | ✅ green |
| 07-meta | 03 | 3 | CAP-01 | T-07-SSRF | Canonical watch URL only after id extract | unit | `uv run pytest tests/unit/test_youtube_oembed_adapter.py -x` | ✅ | ✅ green |
| 07-meta-map | 03 | 3 | CAP-02 | T-07-CTXLEAK | MetadataError → stage=metadata locked reasons | unit | `uv run pytest tests/unit/test_metadata_error_mapping.py -x` | ✅ | ✅ green |
| 07-fake-meta | 03 | 3 | D-26 | — | FakeVideoMetadataProvider failure catalog | unit | `uv run pytest tests/unit/test_fake_video_metadata_provider.py -x` | ✅ | ✅ green |
| 07-public | 03 | 3 | D-21 | — | Seven-name public `__all__` + negative guards | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ✅ | ✅ green |
| 07-settings | 03 | 3 | D-16/D-17 | T-07-PROXY | Settings/proxy injection; no proxy in error context | unit | `uv run pytest tests/unit/test_ingestion_settings.py -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] Register `integration` pytest marker; keep default unit-only collection
- [x] RED tests for `extract_video_id` accept/reject matrix (D-01…D-05)
- [x] RED tests for transcript adapter language preference + error mapping (mocked SDK)
- [x] RED tests for oEmbed adapter + MetadataError mapping (mocked httpx)
- [x] RED tests for `IngestError.to_dict()` envelope
- [x] RED tests for FakeTranscriptProvider failures (D-15, plan 07-02) and FakeVideoMetadataProvider (D-26, plan 07-03)
- [x] Scaffold `ingestion-service` workspace member + `data-collection` deps (`youtube-transcript-api`, `httpx[socks]`, `PySocks`)
- [x] Extend runbook with `YOUTUBE_PROXY_URL` + optional live tests
- [x] Assert no Supabase migrations / persist writers / Typer CLI / openai deps in this phase

*Existing infrastructure: pytest + `tests/unit/` covers Phase 6 ports/fakes — extend, do not replace.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live captions via AdGuard SOCKS | CAP-01 | Network + local proxy | Set `YOUTUBE_PROXY_URL=socks5://192.168.1.68:1080`; run path-explicitly (root `testpaths` stays `tests/unit`, so a bare `-m integration` collects nothing): `RUN_YOUTUBE_INTEGRATION=1 uv run pytest tests/integration -m integration` per runbook |
| Cloud.ru without proxy → `youtube_blocked` | CAP-02 | Ops confirmation | Document risk; do not “fix” with Whisper |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-02

---

## Validation Audit 2026-10-02

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Audit notes:
- State A: draft `07-VALIDATION.md` still marked pending after phase execution.
- Cross-check vs PLAN/SUMMARY/VERIFICATION + filesystem: all Per-Task automated commands resolve to existing unit files.
- Targeted Phase 7 unit files: **172 passed**; full suite: **611 passed**.
- Manual-only rows unchanged (live SOCKS + Cloud.ru ops confirmation).
- No auditor spawn — zero COVERED→MISSING/PARTIAL gaps.
