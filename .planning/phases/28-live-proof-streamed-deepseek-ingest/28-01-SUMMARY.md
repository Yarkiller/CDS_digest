# Summary 28-01: Live streamed ingest proven, FU-27-01 closed

**Status:** complete
**Requirement:** ING-09 → satisfied
**Date:** 2026-10-22

## Outcome

One live run on a 24.1-minute video traversed the streamed DeepSeek path and landed a draft plus a
pending shortlist row, with no connection error. `exit 0` in **21.91 s** wall clock, of which the LLM
stage was **16 578 ms**.

```
uv run --env-file ./ingestion-service/.env ingest "https://www.youtube.com/watch?v=HR7hD8TO4Z8" --template lecture --debug
```

```text
✓ transcript
[20:20:25] debug stage=captions elapsed_ms=2156 video_id=HR7hD8TO4Z8 transcript_chars=20923 transcript_words=3428 language=ru
[20:20:26] debug stage=metadata elapsed_ms=1014 video_id=HR7hD8TO4Z8
✓ LLM
[20:20:43] debug stage=llm elapsed_ms=16578 template=lecture response_chars=10314
✓ saved
[20:20:43] debug stage=persist elapsed_ms=389 material_id=25 slug=kak-ustroeny-iazykovye-modeli-ot-chisel-v-failakh--HR7hD8TO4Z8 batch_id=7 rank=2 already_saved=False
material_id: 25
slug: kak-ustroeny-iazykovye-modeli-ot-chisel-v-failakh--HR7hD8TO4Z8
batch_id: 7
rank: 2
already_saved: false
EXIT=0
ELAPSED_S=21.91
```

Full transcript: `evidence/ingest-run-1.log`.

## Database read-back

`materials` by `youtube_video_id=HR7hD8TO4Z8`:

| id | slug | status | youtube_video_id | created_at |
|----|------|--------|------------------|-----------|
| 25 | `kak-ustroeny-iazykovye-modeli-ot-chisel-v-failakh--HR7hD8TO4Z8` | **draft** | `HR7hD8TO4Z8` | 2026-10-22T17:20:43Z |

`digest_shortlist_items` by `material_id=25`:

| batch_id | material_id | rank | decision |
|----------|-------------|------|----------|
| 7 | 25 | 2 | **pending** |

`rank=2` is correct, not a defect: batch 7 is still unsent and already holds `material_id=24` at rank 1.

## Criteria

| # | Criterion | Verdict |
|---|-----------|---------|
| 1 | exit 0 + material id / slug / batch id printed, video >10 min | ✓ 24.14 min, exit 0, `material_id: 25`, slug, `batch_id: 7` |
| 2 | `status=draft` material **plus** a pending shortlist row, tied by `youtube_video_id` | ✓ material 25 → `youtube_video_id=HR7hD8TO4Z8`; shortlist `material_id=25`, `decision=pending` |
| 3 | No `network_error` at `llm`, no `APIConnectionError`; streamed elapsed recorded | ✓ log scan for `APIConnectionError\|network_error\|Connection aborted\|ReadTimeout\|retrying\|Traceback` → **NONE**; `stage=llm elapsed_ms=16578` |
| 4 | Operator preconditions written down, reproducible | ✓ see Runbook below |

## Runbook (reproducible by another operator)

1. **Proxy is mandatory for the captions stage.** Direct TLS to YouTube is blocked from this host
   (measured: TCP:443 opens, but `ssl.wrap_socket` times out for `www.youtube.com` and
   `www.youtube-nocookie.com`, while `api.deepseek.com` negotiates TLSv1.3). The run used
   `YOUTUBE_PROXY_URL=socks5://adguard:***@192.168.1.68:1080` from `ingestion-service/.env`, with the
   `adguard-vpn` container connected (location `HANOI`). DeepSeek is reached **directly**, not through
   the proxy — `build_async_deepseek_client` uses `trust_env=False`.
2. **Env file:** `ingestion-service/.env` via `uv run --env-file`. Quotes around values are fine —
   measured: `uv` strips them.
3. **`--template` is required.** The ROADMAP's literal command omits it and exits **2**
   (`Missing option '--template'`) before any network call. The command that works is
   `... ingest <url> --template lecture`.
4. **Pick an id absent from `materials`.** `youtube_video_id` is unique; a repeat run reports
   `already_saved: true` and creates no new draft/pending pair, which would make the proof vacuous.

## Findings

- The ROADMAP command line is incomplete (`--template` missing). Recorded as a documentation
  inaccuracy; no code change warranted.
- Forbidden network egress asymmetry: YouTube needs the proxy, DeepSeek must not use it. This is
  already how composition is wired, so it is a precondition rather than a bug.

## Rider: FU-27-01 closed (TDD)

`SearchPill.jsx` empty branch pushed a history entry, so from a settled `?q=RAG` an empty header Enter
stacked a landing and Back re-entered the executed query (`T-27-16` / `AR-27-03`).

- **RED:** `an empty header submit replaces the history entry` failed on `history.length` 2 → 3.
- **GREEN:** `navigate('/knowledge', { replace: true })`; the case now pins the unchanged length and that
  Back leaves `/knowledge`.
- Commit `d77412f`. `27-SECURITY.md` now records T-27-16 as **closed** (19/19, 0 open) and FU-27-01 as
  resolved.

## Gates

| Gate | Result |
|------|--------|
| `npx playwright test --project=web tests/knowledge.spec.js` | 37 passed |
| `npx playwright test --project=web tests/web-app.spec.js` | 55 passed |
| `npm run test:js` | 112 passed, 0 failed |

Two intermediate full-suite runs produced mass failures with no stale `5174` listener present and went
green on an immediate re-run — the known dev-server flakiness in STATE § Blockers, not a diff signal.

## Still open

**`INVALID_ROLE` toast** (`27-UAT.md` test 3) is **not** closed. It needs the SPA running with
`VITE_USE_MOCKS=false` plus an authenticated session; the ingest run works on a service key and never
opens a browser. Recorded as deferred again rather than claimed.

## Files touched

- `web/src/components/SearchPill.jsx` — `{ replace: true }` on the empty submit.
- `tests/knowledge.spec.js` — new case.
- `.planning/phases/27-header-search-runs-on-submit/27-SECURITY.md` — T-27-16 closed, FU-27-01 resolved.
- `.planning/phases/28-live-proof-streamed-deepseek-ingest/` — CONTEXT, this plan, this summary, evidence log.
