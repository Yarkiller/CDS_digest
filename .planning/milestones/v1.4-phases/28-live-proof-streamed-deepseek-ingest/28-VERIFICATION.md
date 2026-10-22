---
phase: 28-live-proof-streamed-deepseek-ingest
verified: 2026-10-22T20:35:00Z
status: passed
score: 4/4 success criteria verified
behavior_unverified: 1
deferred_items: 1
overrides_applied: 0
goal: "Prove the committed streaming fix (0dddc75) on a real long video end to end."
requirements:
  ING-09: satisfied
requirement_ids_in_plans: [ING-09]
requirement_ids_in_requirements_md: [ING-09]
orphaned_requirements: []
unmapped_requirement_ids: []
decision_coverage:
  honored: 9
  total: 9
  not_honored: []
gaps: []
behavior_unverified_items:
  - truth: "E3 · error — a role-chip change that receives INVALID_ROLE shows kb-filter-toast «Фильтр недоступен» for ~4 s while the search error stays on kb-search-error"
    test: "Run the SPA against the live API, sign in, then click a role chip that provokes INVALID_ROLE."
    expected: "Toast «Фильтр недоступен» for ~4 s; the header never carries the error."
    why_unverified: "Requires an authenticated live browser session. This phase's proof ran through the service-key CLI and never opened a browser; the mock adapter cannot emit INVALID_ROLE."
    disposition: "Still deferred (carried from 27-UAT test 3, re-confirmed here rather than claimed closed)."
human_verification: []
---

# Phase 28: Live proof — streamed DeepSeek ingest — Verification Report

**Phase Goal:** Prove the committed streaming fix (`0dddc75`) on a real long video end to end.
**Verified:** 2026-10-22T20:35:00Z
**Status:** passed
**Re-verification:** No — initial verification (the proof ran in this phase).

The goal is observably true in the live system, not merely in the tree: a 24.14-minute video was
ingested through `stream=True` in 21.91 s wall clock (LLM stage 16 578 ms), producing material 25 as
`draft` plus a `pending` shortlist row at `batch 7 / rank 2`, with zero connection errors in the log.

## Goal Achievement

### Success criteria (ROADMAP § Phase 28)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `uv run --env-file ./ingestion-service/.env ingest <url>` on a video longer than 10 minutes exits 0 and prints material id, slug and batch id | ✓ VERIFIED | Video `HR7hD8TO4Z8`, measured **24.14 min** (558 snippets, last end 1448.6 s). `EXIT=0`, `material_id: 25`, `slug: kak-ustroeny-iazykovye-modeli-ot-chisel-v-failakh--HR7hD8TO4Z8`, `batch_id: 7`. Transcript: `evidence/ingest-run-1.log`. **Deviation:** the literal command requires `--template lecture`; without it Typer exits 2 (`Missing option '--template'`) before any network call — measured, and the working command is the one that ran. |
| 2 | A `status=draft` material **plus** a pending shortlist row exist in Supabase for that video, tied by `youtube_video_id` | ✓ VERIFIED | `materials`: `id=25`, `status=draft`, `youtube_video_id=HR7hD8TO4Z8`, `created_at=2026-10-22T17:20:43Z`. `digest_shortlist_items`: `batch_id=7`, `material_id=25`, `rank=2`, `decision=pending`. The id was **absent** from `materials` before the run, so this is a real insert, not an `already_saved` re-hit (`already_saved: false`). |
| 3 | No `network_error` at stage `llm` and no `APIConnectionError` anywhere; the streamed elapsed time is recorded | ✓ VERIFIED | Log scan for `APIConnectionError\|network_error\|Connection aborted\|ReadTimeout\|retrying\|Traceback` → **NONE**. `stage=llm elapsed_ms=16578`, `response_chars=10314`. Wall clock 21.91 s; `persist` 389 ms. |
| 4 | The operator preconditions that made it pass are written into the phase summary, reproducible | ✓ VERIFIED | `28-01-SUMMARY.md` § Runbook: proxy mandatory for captions only (`socks5://adguard:***@192.168.1.68:1080`, `adguard-vpn` connected, location `HANOI`), DeepSeek direct (`trust_env=False`), `--env-file ./ingestion-service/.env` (uv strips quotes — measured), `--template lecture` mandatory, and "pick an id absent from `materials`" because `youtube_video_id` is unique. |

**Score:** 4/4 success criteria verified · 0 unverified · 0 backstop abstentions.

### Scope discipline

The phase was proof-only and stayed so: `data-collection/` and `ingestion-service/` received **zero
edits**. The only production file touched is `web/src/components/SearchPill.jsx`, and only for the
rider item the project owner folded into this session (FU-27-01).

### Measured preconditions that shaped the proof

| Observation | Measurement | Consequence |
|-------------|-------------|-------------|
| Direct TLS to YouTube blocked from this host | `ssl.wrap_socket` → `TimeoutError` for `www.youtube.com` and `www.youtube-nocookie.com`; TCP:443 connects | Captions must use the proxy; without it the run dies at `captions`, which would be misread as a streaming failure |
| DeepSeek reachable directly | TLSv1.3 to `api.deepseek.com` | LLM stage legitimately bypasses the proxy (`trust_env=False`) |
| `--template` required | `ingest <url>` → exit 2, `Missing option '--template'` | ROADMAP command line is incomplete; the evidence records the command that ran |
| Id uniqueness | `materials.youtube_video_id` is UNIQUE; 12 rows already present | A repeat run on the same video proves nothing (`already_saved: true`) |

### Rider item

**FU-27-01 closed under TDD.** `SearchPill.jsx` empty branch now navigates with `{ replace: true }`.
RED measured `history.length` 2 → 3; GREEN pins the unchanged length and that Back leaves `/knowledge`.
Commit `d77412f`; `27-SECURITY.md` records T-27-16 **closed** (19/19 threats, 0 open) and FU-27-01
**resolved**.

### Gates

| Gate | Result |
|------|--------|
| `tests/knowledge.spec.js` | 37 passed |
| `tests/web-app.spec.js` | 55 passed |
| `npm run test:js` | 112 passed, 0 failed |

Note: two intermediate full-suite runs produced mass failures with **no** stale `5174` listener present
and passed on an immediate re-run. This is the recorded dev-server flakiness (STATE § Blockers), not a
signal about the diff; the final runs are the evidence.

## Gaps Summary

No gaps. `ING-09` is satisfied by measurement, not assertion.

## Not closed here

`INVALID_ROLE` toast (`27-UAT.md` test 3) remains deferred: it needs the SPA on the live API with an
authenticated session, which this phase never opened. It is **not** counted as passed.
