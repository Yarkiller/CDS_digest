---
status: rejected_pending_path
phase: 29-pass-1-richer-templates
plan: 03
started: 2026-10-26T18:47:47Z
updated: 2026-10-27T08:22:00Z
---

# Phase 29 — Live ingest UAT (plan 03)

Owner editorial sign-off is Task 3 (`checkpoint:human-verify`, `gate=blocking-human`). This file records the machine-observable evidence. **It is not owner approval.** Attempt 3 persisted a draft (`material_id=26`); ART criteria below are scored against that draft. On 2026-10-27 the owner **rejected** the live draft with a named defect (quoted in Owner sign-off). Task 3 remains open: path pending. ART-01 / ART-02 / ART-03 are **not** marked complete. Live row 26 was not patched.

**Attempt 1 failed** (2026-10-26) at `stage=metadata` `ProxyError`. **Attempt 2** (2026-10-27) ran after the operator confirmed SOCKS5/adguard-vpn is running; that confirmation unblocks the *intent* of the metadata path, not the dest connect. The httpx oEmbed probe still did not return HTTP 200, so **no ingest was spent**. **Attempt 3** (2026-10-27): operator authorized one live ingest with YouTube proxy disabled in-process (direct egress). That is **not** owner editorial approval of a draft. SOCKS hostname/IPv6 CONNECT refused on Attempts 1–2; this proof used direct YouTube because SOCKS dest-connect was refused.

## Pre-flight (recorded before the run)

Halt condition (named, not observed as a missing key): a missing `SUPABASE_URL` or `SUPABASE_SECRET_KEY` would halt before the LLM call is spent, because `build_supabase_service_client` raises `ConfigurationError` at persist time.

Credentials probe (`uv run --env-file ./ingestion-service/.env python -c "… Settings.from_env(); print(bool(s.deepseek_api_key), bool(s.supabase_url), bool(s.supabase_secret_key), bool(s.youtube_proxy_url))"`):

```
True True True True
```

No secret printed. All four required values are present in `.env`. Re-probed on Attempt 2: still `True True True True`.

**Attempt 3 override (operator, 2026-10-27):** SOCKS dest-connect still refused; ingest must load `.env` then clear `YOUTUBE_PROXY_URL` in-process before `Settings.from_env` / CLI. `.env` file was **not** edited. After that load+clear:

```
True True True False
```

(`bool(deepseek_api_key)`, `bool(supabase_url)`, `bool(supabase_secret_key)`, `bool(youtube_proxy_url)`). `bool(Settings.from_env().youtube_proxy_url)` printed `False`. `proxy_cleared True`.

| Check | Attempt 1 (2026-10-26) | Attempt 2 (2026-10-27, after operator restored VPN) | Attempt 3 (2026-10-27, direct egress) |
|-------|------------------------|------------------------------------------------------|----------------------------------------|
| `DEEPSEEK_API_KEY` | present | present | present |
| `SUPABASE_URL` | present | present | present |
| `SUPABASE_SECRET_KEY` | present | present | present |
| `YOUTUBE_PROXY_URL` | present (`socks5://adguard:***@192.168.1.68:1080`; password masked) | unchanged; not printed | present in `.env` (unchanged); **cleared in-process** so `Settings.youtube_proxy_url is None` |
| `api.deepseek.com` TLS | TLSv1.3 (direct; `trust_env=False` on the DeepSeek client) | TLSv1.3 (direct) | TLSv1.3 (direct) |
| SOCKS5 endpoint `192.168.1.68:1080` | TCP open (`Test-NetConnection TcpTestSucceeded=True`) | TCP open again (`TcpTestSucceeded=True`, ~35 s) | not used; orchestrator probe: `127.0.0.1:1080` not listening; SOCKS dest-connect previously refused |
| Local `adguard-vpn` container on this host | not visible (`docker` Desktop pipe missing; `wsl docker` missing) | still not visible | not used |
| Unit gate (post-29-01/29-02 tree) | 95 passed in 1.57s | 95 passed in 1.61s | 95 passed in 1.70s |
| Full suite before verdict | 1197 passed, 1 warning in 14.80s | not re-run (no draft to verdict) | 1197 passed, 1 warning in 14.37s |

Candidate video (same id on all three attempts; unused until Attempt 3):

| Field | Value |
|-------|--------|
| URL | `https://www.youtube.com/watch?v=aircAruvnKk` |
| `youtube_video_id` | `aircAruvnKk` |
| Kind | lecture (single-speaker explainer; `--template lecture`) |
| Pre-run `materials` query | Attempt 1: 0 rows. Attempt 2 (Supabase MCP `select id, youtube_video_id, status where youtube_video_id = 'aircAruvnKk'`): **0 rows**. Attempt 3 (same MCP query before ingest): **0 rows**. Still absent; not an `already_saved` re-hit. |
| Captions probe | Attempt 1: `video_id=aircAruvnKk language=ru chars=16960` (adapter `get`; `ru` preferred over `en`). `evidence/transcript-1.txt` kept. Attempt 2 did not recapture because ingest was not spent. Attempt 3 recapture skipped (same id; pre-flight captions `aircAruvnKk ru 16960` with proxy unset). |
| `MAX_TRANSCRIPT_CHARS` | 80000; 16960 fits, so the run cannot die on the budget gate |
| Duration (public listing) | ~19 min (above the 15+ min bar) |

### Attempt 1 live-path risk (kept)

Known live-path risk (recorded before Attempt 1, not a production edit): `httpx.AsyncClient(proxy=YOUTUBE_PROXY_URL)` to `https://www.youtube.com/oembed` returned `ProxyError: Proxy Server could not connect: Connection refused` on three retries. The same URL through `requests` with the same SOCKS5 URL returned **200**. Captions (`YouTubeTranscriptApi` + `GenericProxyConfig`) succeed. The ingest metadata stage uses httpx.

### Attempt 2 httpx oEmbed probe (required HTTP 200 before ingest)

Probed with the same client ingest uses (`build_httpx_client(Settings.from_env())` → `httpx.AsyncClient(proxy=YOUTUBE_PROXY_URL)`), destination `https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=aircAruvnKk&format=json`. Secrets redacted in every exception string. **HTTP 200 was not observed. Ingest was not started.**

| Probe | Result |
|-------|--------|
| httpx first shot | `ProtocolError Malformed reply` |
| httpx retries 1–3 (same client) | `ProxyError Proxy Server could not connect: Connection refused.` (three times) |
| `requests` through the same SOCKS5 URL | `ConnectionError` / `SOCKSHTTPSConnectionPool` / `NewConnectionError` — **regression vs Attempt 1**, where `requests` returned 200 |
| httpx through proxy to `https://example.com/` | `ConnectError All connection attempts failed` |
| httpx oEmbed (later shot) | `ConnectError All connection attempts failed` |
| Direct `api.deepseek.com:443` | TLSv1.3 (unchanged; DeepSeek must stay off the YouTube proxy) |

Interpretation: TCP:1080 is open, so the operator’s “VPN is running” is true at the socket, but the SOCKS dest connect still does not tunnel HTTPS (YouTube oEmbed *and* example.com). That is the same class of egress issue as Attempt 1’s metadata `ProxyError`. Captions succeeding on Attempt 1 does not make metadata httpx succeed. **No production file was edited.**

### Attempt 3 pre-flight (direct egress; SOCKS precondition overridden)

Operator signal: `done` — proceed with ingest using direct YouTube egress (no SOCKS). **Not** “approved” of a draft.

Same ingest client with proxy unset (`build_httpx_client` after in-process clear):

| Probe | Result |
|-------|--------|
| credentials after env-file + clear | `True True True False` |
| `bool(youtube_proxy_url)` | `False` |
| httpx oEmbed (no proxy) | **HTTP 200** |
| captions adapter `get(aircAruvnKk)` (no proxy) | `aircAruvnKk ru 16960` |
| `api.deepseek.com` TLS | TLSv1.3 |
| `.env` | unchanged (git status clean under `ingestion-service/` and `data-collection/`) |

Orchestrator (2026-10-27) had already measured httpx oEmbed without proxy HTTP 200 and captions `ru` 16960 chars; SOCKS `127.0.0.1:1080` not listening. Plan precondition “`YOUTUBE_PROXY_URL` is set and the `adguard-vpn` container is connected” is **operator-overridden** for this attempt and recorded here; it is not silently dropped.

## Run

### Attempt 1 (2026-10-26) — ingest spent, metadata failed

One command only. Template actually run: **lecture**. No second run of this video.

```
uv run --env-file ./ingestion-service/.env ingest "https://www.youtube.com/watch?v=aircAruvnKk" --template lecture --debug
```

Quoted from the Attempt 1 capture of `evidence/ingest-run-1.log` (later overwritten by Attempt 3, which is the canonical live-proof log):

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

### Attempt 2 (2026-10-27) — ingest not spent

Operator signal: `SOCKS5/adguard-vpn запущен и работает`. That is **not** “approved” of a draft; it only unblocked the retry of the metadata probe.

Required HTTP 200 on httpx oEmbed was not observed (see Attempt 2 probe table). Per resume instructions: do not invent a run. `aircAruvnKk` remained absent from `materials`.

### Attempt 3 (2026-10-27) — ingest spent, persist succeeded (direct egress)

One command only. Template actually run: **lecture**. Same video id; first persist, so not `already_saved`. `.env` not edited. Proxy cleared in-process after `--env-file` load.

```
uv run --env-file ./ingestion-service/.env python $env:TEMP\gsd-29-03-ingest.py
argv: ingest https://www.youtube.com/watch?v=aircAruvnKk --template lecture --debug
```

Quoted from `evidence/ingest-run-1.log` (canonical evidence file; overwritten by this successful run):

```
command: uv run --env-file ./ingestion-service/.env python $env:TEMP\gsd-29-03-ingest.py
argv: ingest https://www.youtube.com/watch?v=aircAruvnKk --template lecture --debug
override: YOUTUBE_PROXY_URL cleared in-process after --env-file load; .env file unchanged; direct YouTube egress (no SOCKS)
wall_clock_before_utc: 2026-10-27T05:54:02Z
wall_clock_after_utc: 2026-10-27T05:54:22Z
elapsed_s: 20.06
exit_code: 0

--- stderr ---
[08:54:04] debug stage=captions elapsed_ms=1063 video_id=aircAruvnKk transcript_chars=16960 transcript_words=2506 language=ru
[08:54:05] debug stage=metadata elapsed_ms=577 video_id=aircAruvnKk
[08:54:22] debug stage=llm elapsed_ms=16766 template=lecture response_chars=9847
[08:54:22] debug stage=persist elapsed_ms=311 material_id=26 slug=neiroset-kak-matematicheskaia-model-struktura-vesa-aircAruvnKk batch_id=7 rank=3 already_saved=False

--- stdout ---
✓ transcript
✓ LLM
✓ saved
material_id: 26
slug: neiroset-kak-matematicheskaia-model-struktura-vesa-aircAruvnKk
batch_id: 7
rank: 3
already_saved: false
```

Printed ids: `material_id: 26`, `slug: neiroset-kak-matematicheskaia-model-struktura-vesa-aircAruvnKk`, `batch_id: 7`, `rank: 3`, `already_saved: false`. `stage=llm` carries `template=lecture` and `response_chars=9847`. No `network_error` and no `APIConnectionError` anywhere in the log. `transcript_chars=16960` matches `evidence/transcript-1.txt`. Shortlist read-back (read-only): `digest_shortlist_items` row `material_id=26` / `batch_id=7` / `rank=3` / `decision=pending`. **No production file was edited.**

## Draft read-back route

**Read-only fallback** (admin preview not opened: Vite `5174` / `VITE_USE_MOCKS=false` login risk from STATE.md). Route: `build_supabase_service_client(Settings.from_env()).table('materials').select('title,dek,body_markdown').eq('id', '26').single()` after the same env-file load + in-process proxy clear. Writes `evidence/draft-1.json` with exactly those three keys. Never updates the row. Equivalent MCP `select title, dek, body_markdown from materials where id = '26'` returned the same row. `len(body_markdown)=9847` matches `response_chars=9847`.

Preview path for the owner (Task 3): `/admin/materials/26`.

## Transcribed heading list

Ordered `##` from `body_markdown` in `evidence/draft-1.json` (verbatim, no paraphrase):

1. `## Нейрон — это просто число`
2. `## Зачем нужны скрытые слои`
3. `## Как устроен переход между слоями`
4. `## Матрицы и векторы: компактная запись`
5. `## Вся сеть — это функция`
6. `## Сигмоида устарела? Разговор с Лишей Ли`
7. `## Конкретика`
8. `## Зачем это СВА`

Section count: **8** (not a fixed three). No heading named «Содержание доклада». No `## Аудитория` in the body.

Legacy scaffold walk against the produced `##` list:

| Literal | In produced `##` list |
|---------|------------------------|
| `## Тезис` | absent |
| `## Ход рассуждения` | absent |
| `## Вывод` | absent |
| `## О чём разговор` | absent |
| `## Позиции` | absent |
| `## Что запомнить` | absent |

## dek

Observed (verbatim from `evidence/draft-1.json`):

> Как из 784 пикселей получается цифра? Разбираем устройство простейшей нейросети — без магии, но с матрицами и 13 000 параметров.

Two sentences. Topic hook about the talk (pixels → digit, structure, 13 000 parameters). Not an audit summary and not a substitute for `## Зачем это СВА`.

## `## Конкретика` per-bullet audit

Section presence: **present**. Talk is a 3Blue1Brown intro to neural nets (handwritten digits, 28×28, weighted sums, sigmoid, ReLU cameo) — concrete numbers/tools exist, so D-08 omit-when-empty does not apply.

| # | Subject | Asserted number/name/tool/version | Transcript fragment |
|---|---------|-----------------------------------|---------------------|
| 1 | Input layer size | **784** neurons for **28x28** pixels | `каждому из 28x28 пикселей входного изображения, а это всего 784 нейрона` |
| 2 | Output layer size | **10** neurons, one per digit | `мы видим 10 нейронов, каждый из которых соответствует определённой цифре` |
| 3 | Hidden layers | **two** hidden layers of **16** neurons; arbitrary, for explanation | `два скрытых слоя по 16 нейронов в каждом, и, признаться, это довольно произвольный выбор` / `я выбрал два слоя, потому что так будет проще объяснить` |
| 4 | Parameter count | almost **13 000** weights and biases | `эта сеть содержит почти 13 000 весов и смещений` |
| 5 | Sigmoid | compresses weighted sum to **0..1**; rarely used in modern nets | `сигмоидную функцию, также называемую логистической кривой` / `в современных сетях сигмоид используется довольно редко` |
| 6 | ReLU | **ReLU (Rectified Linear Unit)** = max(0, a); easier to train; works in deep nets | `ReLU просто гораздо проще для обучения` / `Rectified Linear Unit` / `берёт максимум из нуля и a` / `отлично работает для очень глубоких нейросетей` |

Zero `NOT FOUND` rows. Canonical spelling: ReLU expanded in the bullet as in the transcript (`Rectified Linear Unit`); «сигмоида» for the speaker’s «сигмоидная функция» (same referent; D-09).

## Criterion verdicts

### ART-01 criterion 1 — headings follow the talk

**Verdict: pass** (machine-observable; editorial “would an editor accept these as implicit chapters” remains Task 3)

Observed: eight `##` sections named after the talk’s own topics (neuron-as-number, why hidden layers, layer transition, matrix form, network-as-function, Lisa Li on sigmoid vs ReLU) plus the two optional shared headings. Six legacy scaffold literals are all **absent**. Section count is 8, not a fixed three. No «Содержание доклада». `## Аудитория` does not appear in the body.

### ART-02 criterion 2 — facts block transcript-traceable

**Verdict: pass**

Observed: `## Конкретика` is present with six bullets. Every asserted number/name/tool has a matching fragment in `evidence/transcript-1.txt` (table above). No invented version numbers. No `NOT FOUND`.

### ART-03 criterion 3 — `## Зачем это СВА` and `dek` hook (CONTEXT override: one optional section)

**Verdict: pass** (machine-observable honesty bar; editorial voice quality remains Task 3)

Owner-override reading (D-10/D-11/D-17): exactly one СВА section, `## Зачем это СВА`, written when an analog exists and omitted honestly when none does; a second caveats heading is a failure of this criterion, not a bonus; `dek` stays a 1–2 sentence hook.

Observed: analog exists (a model as a function with tunable weights/biases — control/model/process-quality analog even though the speaker never said «аудит»). Section is **present**, one heading only (`## Риски и ограничения` / `## Что учесть СВА` absent). Closing sentence states «Никаких новых обязанностей или стандартов из этого не следует» — no invented duty, internal standard, or number. Register is analog + «стоит смотреть» / questions to model owners, not «уже требуется по политике N». `dek` is the two-sentence hook quoted above, not an audit dump.

### Truncation guard — `response_chars` vs 16000

**Verdict: recorded; below band** (not a phase failure; not an escalation)

Quoted from the log: `stage=llm elapsed_ms=16766 template=lecture response_chars=9847`. Compared with the 16000 band: **9847 < 16000**. No `max_tokens` change. No re-run. Phase 28 baseline on the old template was `response_chars=10314` / `elapsed_ms=16578`; this run is in the same wall-clock neighbourhood (`elapsed_ms=16766`) and did not cross the escalation threshold.

## Owner sign-off

**Rejected by owner on 2026-10-27. Not approved.**

Task 3 is `blocking-human` and was not auto-approved. Operator authorization of Attempt 3 (direct YouTube egress) is **not** editorial approval. Draft remains `/admin/materials/26`. Live material `id=26` is **left as-is**: neither a shape defect nor a content defect is patched by editing the live row. Templates, CSS, renderer, and production code were not edited in this record.

Owner's words (verbatim, no paraphrase of the complaint):

> Разделы и Зачем это СВА нужно выделить из общего массива, возможно рамочкой но не очень яркой или фоном. В Конкретику должно попасть интересные факты, а не просто набор статичных данных - 784 нейрона — входной слой для изображения 28x28 пикселей. Это ещё нормально а вот 10 нейронов — выходной слой, по одному на каждую цифру. - это уже не понятно для чего. Сними ограничение на использование только данных из статьи - пусть LLM добавит определения сложных терминов или сноски с текста, которые не понятны, а также справочные данные.

### Classification of named items

| # | Owner item (quoted) | Class | Home | This commit |
|---|---------------------|-------|------|-------------|
| 1 | «Разделы и Зачем это СВА нужно выделить из общего массива, возможно рамочкой но не очень яркой или фоном.» | Visual frame / background for topic sections and `## Зачем это СВА`. Renderer/UI (`MaterialPage`). | **Not** a 29-01/02 template reopen. Phase 29 Pitfall 4 (`29-RESEARCH.md`) and plan 29-02 prohibition: flat-looking blockquotes/tables on `MaterialPage` are accepted for v1.5; plan 29-03 also forbids a UAT criterion that depends on visual emphasis. Candidate later UI work (Phase 33-adjacent). | Recorded only. Not patched. |
| 2 | «В Конкретику должно попасть интересные факты, а не просто набор статичных данных - 784 нейрона — входной слой для изображения 28x28 пикселей. Это ещё нормально а вот 10 нейронов — выходной слой, по одному на каждую цифру. - это уже не понятно для чего.» | Prompt-shape defect of ART-02 **editorial quality**. `## Конкретика` must prefer interesting/explanatory facts over a static inventory. Owner's own bar: 784 neurons / 28×28 is OK; «10 нейронов — выходной слой, по одному на каждую цифру» fails because the purpose is unclear. | Would reopen 29-01/02 template instructions **if the owner chooses to fix in this phase**. Machine ART-02 (every asserted number/name/tool traced to the transcript; table above, zero `NOT FOUND`) still holds; the owner's editorial bar does not. | Recorded only. Live row not patched. Templates not reopened here. |
| 3 | «Сними ограничение на использование только данных из статьи - пусть LLM добавит определения сложных терминов или сноски с текста, которые не понятны, а также справочные данные.» | Content-expansion request: lift transcript-only so the LLM may add definitions of hard terms, footnotes, and reference data not in the transcript. | **Contradicts** locked D-18 / D-19 (`29-CONTEXT.md` / `29-RESEARCH.md`: pass-1 user message stays transcript-only; expanding a thin talk from other sources is Phase 32 pass-2, not this rewrite) and REQUIREMENTS ART-02 («filled from the transcript only»). Designed home is Phase 32 pass-2 enricher (**ENR-01**). **This commit does not silently override the lock.** | Conflict recorded. Lock not overridden. |

### Path pending (`gate=blocking-human`)

Plan 29-03 Task 3 stays halted until the owner names a path. Options implied by the classification (not auto-selected):

1. **Item 2 in this phase** — reopen Plans 01/02 and change `## Конкретика` prompt instructions so facts prefer explanatory interest over a static inventory.
2. **Item 1 later** — visual framing of sections / `## Зачем это СВА` as MaterialPage UI (Phase 33-adjacent); not a template reopen.
3. **Item 3 later, lock kept** — definitions, footnotes, and reference data wait for Phase 32 ENR-01.
4. **Item 3 now** — would be an explicit unlock of D-18/D-19 and ART-02 transcript-only. That is an architectural decision; it is **not** assumed here.

ART-01 / ART-02 / ART-03 remain unchecked. No `29-03-SUMMARY.md` is written from this rejection.

## Runbook

1. **Env file:** `ingestion-service/.env` via `uv run --env-file ./ingestion-service/.env`. **Do not edit this file for the proof.**
2. **Command (`--template` is mandatory):** Attempt 3 actually ran `uv run --env-file ./ingestion-service/.env python $env:TEMP\gsd-29-03-ingest.py` with `argv: ingest https://www.youtube.com/watch?v=aircAruvnKk --template lecture --debug` after `os.environ["YOUTUBE_PROXY_URL"] = ""`. Omitting `--template` exits 2 before any network call. Attempts 1–2 used the SOCKS-backed CLI form `uv run --env-file ./ingestion-service/.env ingest "<url>" --template lecture --debug`.
3. **YouTube egress for this proof:** **direct** (proxy cleared in-process). SOCKS hostname/IPv6 CONNECT was refused on Attempts 1–2 (`ProxyError` / dest `Connection refused` even with TCP:1080 open), so this proof does **not** demonstrate the captions-proxy path. Plan precondition that captions require `YOUTUBE_PROXY_URL` is operator-overridden for Attempt 3 and recorded here. Password never printed (`adguard:***` if the SOCKS URL is named).
4. **DeepSeek egress:** direct (`trust_env=False`). Do not route DeepSeek through the YouTube SOCKS5 proxy. `api.deepseek.com` negotiated TLSv1.3 on all three attempts.
5. **Fresh video id:** `youtube_video_id` is unique. Pre-flight must show the id absent from `materials`. `already_saved: true` is not evidence. `aircAruvnKk` was absent before Attempts 1–3; Attempt 3 printed `already_saved: false` and created `material_id=26`.
6. **Existing materials keep old headings by design.** No backfill, no re-ingest of saved rows.
7. **Do not set `max_tokens` and do not re-run to improve a result.** A `response_chars >= 16000` figure is recorded once as an owner escalation. Attempt 3 measured **9847** (below band).
8. **A code fix to rescue the proof invalidates the proof.** No production file was edited on any attempt.
9. **Before spending ingest:** httpx oEmbed through the *effective* YouTube path must return HTTP 200. TCP:1080 open is not sufficient for SOCKS. Attempt 3 required HTTP 200 with proxy unset.

## Summary counts

| Criterion | Verdict |
|-----------|---------|
| ART-01 headings | **pass** (Task 3 still owns editorial chapter-feel) |
| ART-02 facts audit | **pass** (machine traceability; owner editorial quality rejected — see sign-off) |
| ART-03 СВА + dek | **pass** (Task 3 still owns editorial voice) |
| `response_chars` band | **9847** (below 16000; not an escalation) |
| Owner read | **rejected** 2026-10-27 (named defect quoted above; not approved; path pending) |
| Attempt 1 ingest | failed (`stage=metadata` `ProxyError`) |
| Attempt 2 ingest | not started (oEmbed probe ≠ HTTP 200) |
| Attempt 3 ingest | **exit 0**, `already_saved=false`, `material_id=26`, `template=lecture` |
