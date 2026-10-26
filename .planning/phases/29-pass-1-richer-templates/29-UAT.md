---
status: deferred
phase: 29-pass-1-richer-templates
plan: 03
started: 2026-10-26T18:47:47Z
updated: 2026-10-26T18:55:00Z
---

# Phase 29 — Live ingest UAT (plan 03)

Owner editorial sign-off is Task 3 (`checkpoint:human-verify`, `gate=blocking-human`). This file records the machine-observable evidence. **It is not owner approval.** The live proof did not persist a draft, so every ART criterion below is **deferred**, not pass and not fail.

## Pre-flight (recorded before the run)

Halt condition (named, not observed as a missing key): a missing `SUPABASE_URL` or `SUPABASE_SECRET_KEY` would halt before the LLM call is spent, because `build_supabase_service_client` raises `ConfigurationError` at persist time.

Credentials probe (`uv run --env-file ./ingestion-service/.env python -c "… Settings.from_env(); print(bool(s.deepseek_api_key), bool(s.supabase_url), bool(s.supabase_secret_key), bool(s.youtube_proxy_url))"`):

```
True True True True
```

No secret printed. All four required values are present.

| Check | Result |
|-------|--------|
| `DEEPSEEK_API_KEY` | present |
| `SUPABASE_URL` | present |
| `SUPABASE_SECRET_KEY` | present |
| `YOUTUBE_PROXY_URL` | present (`socks5://adguard:***@192.168.1.68:1080`; password masked) |
| `api.deepseek.com` TLS | TLSv1.3 (direct; `trust_env=False` on the DeepSeek client) |
| SOCKS5 endpoint `192.168.1.68:1080` | TCP open (`Test-NetConnection TcpTestSucceeded=True`) |
| Local `adguard-vpn` container on this host | not visible (`docker` Desktop pipe missing; `wsl docker` missing). Proxy is a LAN endpoint, not a local container. Captions adapter succeeded, so the SOCKS5 path used by ingest captions is connected. |
| Unit gate (post-29-01/29-02 tree) | `uv run pytest tests/unit/test_article_templates.py tests/unit/test_deepseek_article_adapter.py tests/unit/test_article_draft_body_audience.py -x` → **95 passed in 1.57s** |
| Full suite before verdict | `uv run pytest` → **1197 passed, 1 warning in 14.80s** |

Candidate video:

| Field | Value |
|-------|--------|
| URL | `https://www.youtube.com/watch?v=aircAruvnKk` |
| `youtube_video_id` | `aircAruvnKk` |
| Kind | lecture (single-speaker explainer; `--template lecture`) |
| Pre-run `materials` query | `select id, youtube_video_id where youtube_video_id = 'aircAruvnKk'` → **0 rows** (absent; not an `already_saved` re-hit) |
| Captions probe | `video_id=aircAruvnKk language=ru chars=16960` (adapter `get`; `ru` preferred over `en`) |
| `MAX_TRANSCRIPT_CHARS` | 80000; 16960 fits, so the run cannot die on the budget gate |
| Duration (public listing) | ~19 min (above the 15+ min bar) |

Known live-path risk (recorded before the run, not a production edit): `httpx.AsyncClient(proxy=YOUTUBE_PROXY_URL)` to `https://www.youtube.com/oembed` returned `ProxyError: Proxy Server could not connect: Connection refused` on three retries. The same URL through `requests` with the same SOCKS5 URL returned **200**. Captions (`YouTubeTranscriptApi` + `GenericProxyConfig`) succeed. The ingest metadata stage uses httpx.

## Run

One command only. Template actually run: **lecture**. No second run.

```
uv run --env-file ./ingestion-service/.env ingest "https://www.youtube.com/watch?v=aircAruvnKk" --template lecture --debug
```

Quoted from `evidence/ingest-run-1.log`:

```
command: uv run --env-file ./ingestion-service/.env ingest "https://www.youtube.com/watch?v=aircAruvnKk" --template lecture --debug
wall_clock_before_utc: 2026-10-26T18:54:44Z
wall_clock_after_utc: 2026-10-26T18:54:53Z
elapsed_s: 8.71
exit_code: 1

--- stderr ---
[21:54:48] debug stage=captions elapsed_ms=2032 video_id=aircAruvnKk transcript_chars=16960 transcript_words=2506 language=ru
[21:54:53] debug stage=metadata elapsed_ms=5015 reason=network_error exit_code=1
{"ok": false, "stage": "metadata", "reason": "network_error", "message": "metadata network_error for aircAruvnKk", "exit_code": 1, "context": {"video_id": "aircAruvnKk", "exception_class": "ProxyError"}}

--- stdout ---
✓ transcript
```

Printed ids: **none**. There is no `material_id`, `slug`, `batch_id`, `rank`, or `already_saved`. There is no `stage=llm` line, so `template=` and `response_chars=` were not emitted. No `APIConnectionError` in the log. The failure is `stage=metadata reason=network_error exception_class=ProxyError`.

This is a captions-vs-metadata split on the same SOCKS5 URL: captions completed (`transcript_chars=16960`, matching `evidence/transcript-1.txt`), then oEmbed via httpx was refused by the proxy destination. A captions failure would be a proxy problem, not a template problem; this metadata `ProxyError` is the same class of egress issue. **No production file was edited to rescue the proof.** The LLM was never called, so the rewritten templates were not observed.

## Draft read-back route

**None.** No `material_id` was printed, so neither `/admin/materials/{id}` nor the read-only `materials` fallback ran. `evidence/draft-1.json` was **not** written (the fallback is only for when a draft exists and the admin preview is unavailable).

Pre-run absence of `aircAruvnKk` was re-checked; the failed run did not insert a row.

## Transcribed heading list

Not observed. No `body_markdown` was persisted.

Legacy scaffold walk (cannot be scored against a live draft):

| Literal | In produced `##` list |
|---------|------------------------|
| `## Тезис` | not observed |
| `## Ход рассуждения` | not observed |
| `## Вывод` | not observed |
| `## О чём разговор` | not observed |
| `## Позиции` | not observed |
| `## Что запомнить` | not observed |

Section count: not observed (cannot confirm “not a fixed three”).

## dek

Not observed. No draft row.

## `## Конкретика` per-bullet audit

Section presence: **not observed** (no article body). This is not D-08 honest omission of an empty facts block — the model never ran.

| # | Subject | Asserted number/name/tool/version | Transcript fragment |
|---|---------|-----------------------------------|---------------------|
| — | — | — | no bullets to audit; ingest stopped before `stage=llm` |

## Criterion verdicts

### ART-01 criterion 1 — headings follow the talk

**Verdict: deferred**

Observed: ingest exited 1 at `stage=metadata` with `exception_class=ProxyError`. No `body_markdown`, no heading list. The six legacy scaffold literals cannot be walked against a produced article. Missing: a completed `stage=llm` persist of a new `status=draft` material for `youtube_video_id=aircAruvnKk`.

### ART-02 criterion 2 — facts block transcript-traceable

**Verdict: deferred**

Observed: no `## Конкретика` text exists to audit. `evidence/transcript-1.txt` is captured (`aircAruvnKk` / `ru` / 16960 chars, matching `stage=captions transcript_chars=16960`) but has nothing to compare against. Missing: the produced facts block (or an honest omit of that heading on a completed draft).

### ART-03 criterion 3 — `## Зачем это СВА` and `dek` hook (CONTEXT override: one optional section)

**Verdict: deferred**

Owner-override reading (D-10/D-11/D-17): exactly one СВА section, `## Зачем это СВА`, written when an analog exists and omitted honestly when none does; a second caveats heading is a failure of this criterion, not a bonus; `dek` stays a 1–2 sentence hook. Observed: neither the section nor `dek` exists because no draft was persisted. Missing: the produced body and `dek` of a completed ingest.

### Truncation guard — `response_chars` vs 16000

**Verdict: deferred** (not a phase failure; not an escalation)

The log has no `stage=llm` line, so `response_chars` was never measured. Crossing ≥16000 is a one-way owner `max_tokens` escalation; that band was not reached because the LLM was not called. Quoted figure: **absent**. Missing: `stage=llm … response_chars=…` on a completed run.

## Owner sign-off

Not recorded. Task 3 is `blocking-human` and was not auto-approved. There is no live draft at `/admin/materials/{id}` for the owner to read.

## Runbook

1. **Env file:** `ingestion-service/.env` via `uv run --env-file ./ingestion-service/.env`.
2. **Command ( `--template` is mandatory):** `uv run --env-file ./ingestion-service/.env ingest "<url>" --template lecture --debug`. This run used `--template lecture` because the video is a single-speaker explainer. Omitting `--template` exits 2 before any network call.
3. **Captions proxy:** `YOUTUBE_PROXY_URL=socks5://adguard:***@192.168.1.68:1080`. Direct TLS to YouTube from this host times out; captions require the SOCKS5 path. The `adguard-vpn` container is the operator-side VPN that must be connected so destination connects succeed. On this dispatch, captions through that URL succeeded; httpx oEmbed to `www.youtube.com` returned SOCKS dest `Connection refused`.
4. **DeepSeek egress:** direct (`trust_env=False`). Do not route DeepSeek through the YouTube SOCKS5 proxy. `api.deepseek.com` negotiated TLSv1.3 on this host.
5. **Fresh video id:** `youtube_video_id` is unique. Pre-flight must show the id absent from `materials`. `already_saved: true` is not evidence. This run’s id `aircAruvnKk` was absent; the run never persisted, so the id remains unused.
6. **Existing materials keep old headings by design.** No backfill, no re-ingest of saved rows.
7. **Do not set `max_tokens` and do not re-run to improve a result.** A `response_chars >= 16000` figure is recorded once as an owner escalation.
8. **A code fix to rescue the proof invalidates the proof.** This halt was not patched.

## Summary counts

| Criterion | Verdict |
|-----------|---------|
| ART-01 headings | deferred |
| ART-02 facts audit | deferred |
| ART-03 СВА + dek | deferred |
| `response_chars` band | deferred (unmeasured) |
| Owner read | not recorded |
