---
status: complete
phase: 28-live-proof-streamed-deepseek-ingest
source: [28-VERIFICATION.md]
started: 2026-10-22T19:50:00+03:00
updated: 2026-10-22T20:36:00+03:00
---

## Current Test

[testing complete]

## Tests

### 1. A long video runs through the streamed path
expected: exit 0; material id, slug and batch id printed; the LLM stage completes under streaming.
result: pass
source: automated
evidence: "`uv run --env-file ./ingestion-service/.env ingest https://www.youtube.com/watch?v=HR7hD8TO4Z8 --template lecture --debug` → EXIT=0, wall clock 21.91 s, `stage=llm elapsed_ms=16578 response_chars=10314`, `material_id: 25`, `batch_id: 7`. Video measured 24.14 min. Transcript: `evidence/ingest-run-1.log`."
screenshots: []

### 2. Draft material + pending shortlist row, tied by youtube_video_id
expected: `materials.status='draft'` for the video and a `pending` row in `digest_shortlist_items`.
result: pass
source: automated
evidence: "`materials`: id=25, status=draft, youtube_video_id=HR7hD8TO4Z8. `digest_shortlist_items`: batch_id=7, material_id=25, rank=2, decision=pending. The id was absent from `materials` before the run (`already_saved: false`)."
screenshots: []

### 3. No connection error; streamed elapsed recorded
expected: no `network_error` at `llm`, no `APIConnectionError`; elapsed value in the record.
result: pass
source: automated
evidence: "Log scan for APIConnectionError / network_error / Connection aborted / ReadTimeout / retrying / Traceback → NONE. `stage=llm elapsed_ms=16578`."
screenshots: []

### 4. Operator preconditions are reproducible
expected: env file, proxy requirement, required flags and video choice written down.
result: pass
source: automated
evidence: "`28-01-SUMMARY.md` § Runbook. Measured preconditions: direct TLS to YouTube times out (proxy mandatory for captions only), DeepSeek direct via `trust_env=False`, `uv` strips quotes in the env file, `--template` is mandatory (exit 2 otherwise), `youtube_video_id` unique so the id must be new."
screenshots: []

### 5. INVALID_ROLE filter toast (carried from Phase 27)
expected: kb-filter-toast «Фильтр недоступен» for ~4 s on a role-chip change; error stays on kb-search-error.
result: skipped
reason: "Deferred follow-up: needs the SPA on the live API with an authenticated browser session. This phase's proof ran through the service-key CLI and never opened a browser; the mock adapter cannot emit INVALID_ROLE."

## Summary

total: 5
passed: 4
issues: 0
pending: 0
skipped: 1
blocked: 0

## Gaps

<!-- Blocked tests are environment gates, not code issues — intentionally not listed here. -->

## Deferred Follow-Ups

```yaml
- test: 5
  idea: "Sign in on the live API, click a role chip that provokes INVALID_ROLE, and confirm kb-filter-toast «Фильтр недоступен» for ~4 s while the error stays on kb-search-error."
  deferred_at: 2026-10-22
  verify_in: "next phase touching /knowledge against the live API, or a dedicated gap-closure plan"
```
