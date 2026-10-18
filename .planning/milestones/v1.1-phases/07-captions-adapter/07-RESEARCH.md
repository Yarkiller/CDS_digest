# Phase 7: Captions Adapter - Research

**Researched:** 2026-09-26
**Domain:** YouTube captions + oEmbed adapters behind Phase 6 ports; URL→`video_id` parser; staged fail-closed errors; shared optional SOCKS/HTTP proxy — no LLM, no persist, no Typer one-shot
**Confidence:** HIGH (CONTEXT D-01…D-26 + CAP-01/CAP-02 + Phase 6 contracts verified in tree + youtube-transcript-api 1.2.x / httpx proxy docs via Context7); MEDIUM (exact `ingestion-service` package skeleton file names; subtype↔`reason` table is Claude's Discretion within locked reason codes); LOW (none blocking — live CAP-02 zero-DB spy deferred Phase 9/10 by D-14)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### URL → video_id
- **D-01:** Accept `youtube.com/watch?v=…`, `youtu.be/…`, `/shorts/…`, `/embed/…` (with or without `www`). Normalize `m.youtube.com` → `youtube.com`. Strip noise query params (`t`, `list`, `si`, `feature`, `ab_channel`, etc.). Reject playlist-without-`v=`, channel URLs, non-YouTube, watch without `v=`, and ids not exactly 11 chars.
- **D-02:** Out of scope for v1.1: `/live/`, `/v/`, `/e/` — add later when operators hit them, with a test.
- **D-03:** Also accept a bare 11-char video id (`[A-Za-z0-9_-]{11}`) as input.
- **D-04:** Parser is `extract_video_id(url)` (~25 lines) in `ingestion-service/`, **not** on `TranscriptProvider` / metadata ports. — **Reversibility:** costly.
- **D-05:** Parse failures use `stage=url` (before network). Caption unavailability uses `stage=captions` (after network). Both `exit_code=1`; distinguish via `stage` + `reason` in JSON. CAP-02 covers captions only; URL parse is not CAP-02.

#### Language preference
- **D-06:** Allow auto-generated captions when language matches preference (no manual-only filter).
- **D-07:** Dialect tags via prefix normalization: `base = lang.split("-")[0].lower()`; accept only if `base in ("ru", "en")`. Store `Transcript.language` as normalized base `"ru"` or `"en"`. Tests: `ru`, `ru-RU`, `en`, `en-US` match; `rue` / `enm` do not.
- **D-08:** Prefer order: if any `ru` track (manual or auto) → take it; else any `en`; else fail. No manual/auto ranking within a language.
- **D-09:** If neither preferred language exists → fail closed `stage=captions`, `reason=no_preferred_language`, include available languages in error `context`. Any-language fallback deferred to v1.2+.

#### Fail-closed error surface
- **D-10:** Mapped stable `reason` codes under `stage=captions`: `no_captions`, `no_preferred_language`, `captions_disabled`, `video_unavailable`, `youtube_blocked`, `bot_challenge`, `network_error`, `empty_captions`, `unknown_captions_error`. Do not pass through SDK exception class names as `reason`.
- **D-11:** `IngestError` lives in `ingestion-service/.../domain/errors.py` (not `data-collection`). Stages: `Literal["url", "captions", "metadata", "consistency", "llm", "llm_truncation", "persist"]`. CLI JSON via `to_dict()`. `data-collection` does not know pipeline stages. — **Reversibility:** costly.
- **D-12:** Adapter exceptions in `data-collection/errors/captions.py`: base `CaptionsError(video_id, **context)` plus subtypes `CaptionsUnavailable`, `CaptionsDisabled`, `CaptionsBlocked`, `CaptionsVideoUnavailable`, `CaptionsNoPreferredLanguage`, `CaptionsNetworkError`, `CaptionsEmpty` (and map bot challenges appropriately toward `bot_challenge`). Adapter maps SDK → these types; ingestion use-case maps → `IngestError(stage="captions", reason=...)`.
- **D-13:** Diagnostic JSON envelope: `{ok, stage, reason, message, context?, exit_code}`. `context` holds typed values (e.g. `video_id`, `available_languages`, exception class string) — not a free-form dump.
- **D-14:** Phase 7 proves CAP-02 at adapter/unit level: failures raise `CaptionsError` / never return a `Transcript`. Live “zero DB rows” with persist spy deferred to Phase 9/10 when persist exists. — Must add roadmap/test requirement later: fake failing `TranscriptProvider` + spy `PersistPort` → `persist.calls == []`.
- **D-15:** Extend `FakeTranscriptProvider` with additive `failures: dict[str, CaptionsError]` — `get` raises if `video_id` in map; existing success+spy tests unchanged.

#### Captions network / proxy
- **D-16:** Shared optional env `YOUTUBE_PROXY_URL` (`socks5://…` or `http://…`) for captions (`GenericProxyConfig`) and oEmbed (`httpx`). Unset → direct. Document Cloud.ru risk: without proxy, expect `IpBlocked` / `youtube_blocked`.
- **D-17:** Composition/`Settings` in `ingestion-service` reads env and injects ready clients into adapters. Adapters never read `os.environ`. Matches backend composition pattern.
- **D-18:** SOCKS support required for verified AdGuard path: `uv add` `httpx[socks]` and `PySocks` / `requests[socks]`.
- **D-19:** `PoTokenRequired` (and similar bot challenges) → `reason=bot_challenge`, distinct from `youtube_blocked`. Both fail-closed; no cookie/poToken bypass in v1.1.
- **D-20:** Tests: unit with mocked SDK always in CI; optional `@pytest.mark.integration` skipped by default; run with proxy via runbook (document in `docs/agents/local-platform-runbook.md`).

#### VideoMetadata / oEmbed (in Phase 7)
- **D-21:** Phase 7 ships captions **and** oEmbed: ports `TranscriptProvider` + `VideoMetadataProvider`; adapters `YouTubeTranscriptAdapter` + `YouTubeOEmbedAdapter`; `CaptionsError` + `MetadataError`; fakes for both; shared proxy; URL parser.
- **D-22:** `VideoMetadataProvider.get(video_id: str) -> VideoMetadata` — mirrors transcript port. Adapter builds canonical `https://www.youtube.com/watch?v={video_id}` for oEmbed; `VideoMetadata.source_url` is that canonical URL. URL parsing stays in `ingestion-service`.
- **D-23:** Metadata failure is fail-closed — no fabricated `"unknown"` author. `stage=metadata` with reasons such as `metadata_unavailable` / `network_error` (mapped from `MetadataError`). Zero DB rows when persist exists.
- **D-24:** Composition intent (Phase 10): fetch **captions first, then metadata**. Adapters remain independent; order is pipeline policy.
- **D-25:** Small `MetadataError` set in `data-collection`: base `MetadataError(video_id, **context)`; `MetadataUnavailable` (404/403/blocked); `MetadataNetworkError` (timeout/conn refused); `MetadataInvalidResponse` (bad JSON / missing `author_name`). Use-case maps to `IngestError(stage="metadata", …)`.
- **D-26:** Add `FakeVideoMetadataProvider` (success + spy + failure catalog pattern parallel to transcript fake).

### Claude's Discretion
- Exact file layout under `data-collection` for adapters/errors as long as public ports/DTOs and taxonomies match decisions above.
- Exact subtype ↔ `reason` mapping table (as long as the locked reason codes exist and SDK names stay out of `reason`).
- Whether `bot_challenge` gets its own `CaptionsError` subtype vs mapping from a blocked/unavailable subtype with context — prefer a clear, tested mapping.
- How optional integration tests are gated (`pytest.ini` markers / env skip) within the skipped-by-default rule.

### Deferred Ideas (OUT OF SCOPE)
- URL forms `/live/`, `/v/`, `/e/`
- Any-language caption fallback + translation marker (v1.2+)
- Manual-over-auto preference within a language (v1.2+)
- PoToken / cookie bypass for `bot_challenge`
- Fabricated author fallback on metadata failure
- **Phase 9/10:** live CAP-02 spy (`persist.calls == []`)
- DeepSeek, templates, persist, shortlist, Typer one-shot — Phases 8–10
- CONSISTENCY-01 (`transcript.video_id == metadata.video_id`) — Phase 10
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CAP-01 | Operator can pass a YouTube URL; the CLI resolves `video_id` and fetches captions with `ru`/`en` preference | `extract_video_id` in `ingestion-service` + `YouTubeTranscriptAdapter` implementing `TranscriptProvider.get(video_id)` with dialect-normalized ru→en preference (D-01…D-09) |
| CAP-02 | Missing, disabled, or blocked captions exit non-zero with `stage=captions` and write zero database rows | Adapter raises `CaptionsError` subtypes (never empty `Transcript`); ingestion maps → `IngestError(stage="captions", reason=…)`. **This phase:** unit proof only (D-14). Live zero-row spy = Phase 9/10 |
| *(CONTEXT beyond REQ IDs)* | oEmbed `VideoMetadataProvider` + `MetadataError` + shared proxy + `IngestError` envelope | D-16…D-26 — **in Phase 7 planning scope** even though CAP-* IDs name captions only |
| *(Roadmap SC-3)* | Captions failure writes zero database rows | Deferred live spy; Phase 7 documents contract + adapter-level “no Transcript returned” |
</phase_requirements>

## Summary

Phase 7 is the **first I/O wave** of v1.1 ingestion: stand up a thin `ingestion-service` package (URL parse + `IngestError` + Settings/composition that injects clients — **not** the Typer one-shot), implement real YouTube adapters in `data-collection` behind Phase 6 ports, and lock fail-closed staged diagnostics. CAP-01 is URL→`video_id` + captions with `ru` then `en` (dialect base normalization). CAP-02 is proven **at adapter/unit level** this phase; live “zero DB rows” waits until persist exists (D-14).

**Critical planner overrides vs early milestone research:**
1. Early `ARCHITECTURE.md` sketched `TranscriptProvider.fetch(url)` — **SUPERSEDED** by Phase 6 D-15 (`get(video_id)`) + Phase 7 D-04 (parse stays in `ingestion-service`).
2. Early research treated oEmbed as optional “later” — **SUPERSEDED** by CONTEXT **D-21…D-26**: captions **and** oEmbed ship together in Phase 7.
3. CAP-02 roadmap wording “writes zero database rows” is **partially deferred**: Phase 7 = no `Transcript` / raise `CaptionsError`; Phase 9/10 = spy persist port.

**Primary recommendation:** Scaffold minimal `ingestion-service` workspace member; add `youtube-transcript-api>=1.2,<2`, `httpx[socks]`, and SOCKS extras for `requests` to `data-collection`; implement adapters that accept injected `YouTubeTranscriptApi` / `httpx.AsyncClient` (never `os.environ`); add `VideoMetadataProvider` + public export; extend fakes with failure catalogs; map SDK exceptions → `CaptionsError`/`MetadataError` then → `IngestError.to_dict()`; unit-mock SDK in CI; gate optional live integration tests + document `YOUTUBE_PROXY_URL` in the runbook.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| `extract_video_id` | `ingestion-service` | — | D-04 — not on ports |
| `IngestError` + `to_dict()` | `ingestion-service/domain` | Phase 10 CLI | D-11 — pipeline stages are CLI contract |
| Settings / proxy env → client injection | `ingestion-service` composition | — | D-17; mirror backend `Settings.from_env` |
| `TranscriptProvider` Protocol | `data-collection` (exists) | — | Phase 6 D-15 |
| `VideoMetadataProvider` Protocol | `data-collection` (**new**) | — | D-21/D-22 |
| `YouTubeTranscriptAdapter` | `data-collection` adapters | — | External API ownership (`architecture.mdc`) |
| `YouTubeOEmbedAdapter` | `data-collection` adapters | — | D-21/D-22 |
| `CaptionsError` / `MetadataError` taxonomies | `data-collection` errors | ingestion mapper | D-12/D-25 — adapters never emit stage names |
| Fake failure catalogs | `data-collection/tests_support` | Unit tests | D-15/D-26; not public `__all__` |
| Map CaptionsError → IngestError | `ingestion-service` (thin mapper/use-case) | — | Boundary: data-collection ≠ pipeline stages |
| DeepSeek / persist / Typer one-shot | Out of scope | Phases 8–10 | CONTEXT deferred |
| Live CAP-02 DB spy | Out of scope | Phases 9–10 | D-14 |

## Project Constraints (from .cursor/rules/ + AGENTS.md)

| Directive | Implication for Phase 7 |
|-----------|-------------------------|
| Ports & Adapters (`architecture.mdc`) | YouTube/httpx SDK only in `data-collection` adapters; composition wires in `ingestion-service`; no SDK in domain/use-case beyond injected ports |
| No deep-imports across modules | Public `data_collection` exports grow by `VideoMetadataProvider` (+ optionally error types if planners choose public); fakes stay in `tests_support` |
| TDD Red–Green–Refactor | Failing unit tests first for parser, adapters (mocked SDK), error mapping, fake failure catalogs; then minimal code |
| No `Any` on ports/boundaries | Explicit `video_id: str` → `Transcript` / `VideoMetadata`; typed error context |
| Unit tests without network/DB | Mock/stub SDK clients; `@pytest.mark.integration` skipped by default (D-20) |
| D-CONTENT-01 | Captions stay `Transcript`; never write materials this phase |
| ADR-0002 / captions-only | No Whisper/Foundry ASR; IP block ≠ transcription opportunity (`PITFALLS.md` Pitfall 5) |
| Project skills (`.agents/skills`) | `hallmark` / Supabase skills do **not** apply to this phase (no UI; no schema writes) |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `youtube-transcript-api` | **1.2.4** latest on PyPI; pin `>=1.2.0,<2` `[VERIFIED: PyPI 2026-09-26; STACK.md]` | Captions fetch by `video_id` | Locked MVP; instance `.fetch` / `.list`; `GenericProxyConfig` |
| `httpx` | **0.28.1** (workspace) + extra `[socks]` `[VERIFIED: uv run import]` | oEmbed GET; SOCKS via `socksio` | Phase 6 verified oEmbed path; D-18 |
| `PySocks` / `requests[socks]` | add for captions SOCKS | `requests` (transitive via transcript API) needs SOCKS for `socks5://` | D-18; AdGuard `192.168.1.68:1080` |
| Pydantic v2 | `2.13.5` | Existing DTOs unchanged | Phase 6 |
| pytest | `9.1.1` | Unit + optional integration | Existing `tests/unit/` |
| Python `asyncio` | stdlib | Async ports wrapping sync SDK (`asyncio.to_thread` recommended) | Phase 6 async Protocols; no `pytest-asyncio` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `urllib.parse` | stdlib | URL parse / query strip in `extract_video_id` | D-01 |
| `unittest.mock` / tiny fakes | stdlib | Mock `YouTubeTranscriptApi` / httpx responses in unit tests | D-20 CI |
| Backend `Settings` pattern | existing | `ingestion_service` `Settings.from_env` + injectable environ | `[VERIFIED: backend/.../composition/settings.py]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `youtube-transcript-api` 1.2.x instance API | Old `YouTubeTranscriptApi.get_transcript` 0.6.x | **Forbidden** — API changed; STACK.md |
| `GenericProxyConfig` | `WebshareProxyConfig` | Webshare is vendor-specific; AdGuard is generic SOCKS — use Generic |
| Sync adapter methods | Keep async Protocols from Phase 6 | Locked — wrap sync SDK with `asyncio.to_thread` |
| URL parse on the port | `get(url)` | Violates D-04 / Phase 6 D-15 |
| Fabricated author `"unknown"` | Fail-closed `MetadataError` | Violates D-23 |
| Whisper on `no_captions` | Fail-closed | Milestone OUT / ADR-0002 |
| Live CAP-02 DB assert now | Adapter-level only (D-14) | Persist does not exist yet |
| Put `IngestError` in data-collection | Keep in ingestion-service | Violates D-11 |

**Installation (from repo root, after scaffolding):**

```bash
uv add --package data-collection "youtube-transcript-api>=1.2.0,<2" "httpx[socks]==0.28.1" "PySocks"
# optional equivalent: requests[socks] — ensure requests can use socks5:// via PySocks

# new workspace member ingestion-service (depends on data-collection only this phase)
# append to [tool.uv.workspace].members + [tool.uv.sources], then:
uv sync
```

**Version verification:** `httpx==0.28.1`, `pydantic==2.13.5`, `pytest==9.1.1` confirmed this session; `youtube-transcript-api` **not yet installed** (expected — Phase 7 adds it). PyPI latest = `1.2.4`.

## Package Legitimacy Audit

| Package | Registry | Age / reputation | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|------------------|-----------|-------------|---------|-------------|
| `youtube-transcript-api` | PyPI | Established (years); Context7 High | High volume | github.com/jdepoix/youtube-transcript-api | **PASS** | Pin `>=1.2.0,<2` |
| `httpx` | PyPI | Encode org; already locked | High | github.com/encode/httpx | **PASS** | Reuse `0.28.1` + `[socks]` |
| `socksio` | transitive via `httpx[socks]` | Encode ecosystem | — | — | **PASS** | Via extra only |
| `PySocks` | PyPI | Long-standing SOCKS for requests | High | — | **PASS** | Required for captions SOCKS (D-18) |
| `requests` / `defusedxml` | transitive via transcript API | — | — | — | **PASS** | Do not add directly |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none for this phase install list

## Architecture Patterns

### System Architecture Diagram

```text
Operator input (URL or bare video_id)
        |
        v
[ingestion-service]
  extract_video_id(url)  --fail--> IngestError(stage="url", ...)
        |
        | video_id
        v
  composition Settings.from_env
    YOUTUBE_PROXY_URL? --> GenericProxyConfig + httpx.AsyncClient(proxy=...)
        |
        | inject clients (adapters NEVER read os.environ)
        v
[data-collection adapters]
  YouTubeTranscriptAdapter.get(video_id) --> Transcript | raise CaptionsError
  YouTubeOEmbedAdapter.get(video_id)     --> VideoMetadata | raise MetadataError
        |
        v
[ingestion-service mapper]
  CaptionsError  --> IngestError(stage="captions", reason=locked_code, ...)
  MetadataError  --> IngestError(stage="metadata", reason=..., ...)
  IngestError.to_dict() --> {ok, stage, reason, message, context?, exit_code}

Phase 10 (NOT this phase): captions FIRST, then metadata, then LLM, then persist
Phase 9/10: failing TranscriptProvider + spy PersistPort => persist.calls == []
```

### Recommended Project Structure (discretion)

```text
data-collection/
  src/data_collection/
    __init__.py                      # ADD VideoMetadataProvider to __all__
    ports/
      transcript_provider.py         # EXISTS
      video_metadata_provider.py     # NEW Protocol
    adapters/
      youtube_transcript.py          # NEW YouTubeTranscriptAdapter
      youtube_oembed.py              # NEW YouTubeOEmbedAdapter
    errors/
      captions.py                    # NEW CaptionsError hierarchy
      metadata.py                    # NEW MetadataError hierarchy
    tests_support/fakes.py           # EXTEND FakeTranscriptProvider; ADD FakeVideoMetadataProvider
  pyproject.toml                     # ADD youtube-transcript-api, httpx[socks], PySocks

ingestion-service/                   # NEW uv workspace member (minimal)
  pyproject.toml                     # depends: data-collection
  src/ingestion_service/
    __init__.py
    url.py                           # extract_video_id
    domain/errors.py                 # IngestError + to_dict + stage Literal
    composition/settings.py          # YOUTUBE_PROXY_URL (+ injectable environ)
    composition/clients.py           # build proxy configs / httpx client / YTT api
    mapping/captions.py              # CaptionsError -> IngestError (thin)
    mapping/metadata.py              # MetadataError -> IngestError

tests/unit/
  test_extract_video_id.py
  test_ingest_error.py
  test_youtube_transcript_adapter.py   # mocked SDK
  test_youtube_oembed_adapter.py       # mocked httpx
  test_captions_error_mapping.py
  test_metadata_error_mapping.py
  test_fake_transcript_provider_failures.py  # additive D-15
  test_fake_video_metadata_provider.py
  test_data_collection_public_api.py   # extend __all__

tests/integration/                   # optional; skipped by default
  test_youtube_captions_live.py
  test_youtube_oembed_live.py

docs/agents/local-platform-runbook.md  # ADD YOUTUBE_PROXY_URL + how to run integration marks
```

**Why this layout:** Keeps external SDKs in `data-collection`; keeps pipeline stage vocabulary out of adapters (D-11); creates `ingestion-service` early enough for URL/`IngestError`/Settings without pulling Phase 10 Typer scope.

### Pattern 1: Injected clients (no env in adapters)

**What:** Adapter constructors take ready `YouTubeTranscriptApi` and/or `httpx.AsyncClient` (or a narrow callable). Composition builds proxy from `Settings.youtube_proxy_url`.  
**When to use:** Always (D-17).  
**Analog:** `[VERIFIED: backend/.../composition/settings.py]` — `Settings.from_env(environ=...)` injectable for tests.  
**Docs:** `GenericProxyConfig(http_url=..., https_url=...)` `[CITED: Context7 /jdepoix/youtube-transcript-api]`; httpx `Client(proxy=url)` + `httpx[socks]` for `socks5://` `[CITED: Context7 /encode/httpx]`.

```python
# Recommended construction when YOUTUBE_PROXY_URL is set:
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import GenericProxyConfig

proxy = settings.youtube_proxy_url  # e.g. "socks5://192.168.1.68:1080"
ytt = YouTubeTranscriptApi(
    proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy) if proxy else None
)
http = httpx.AsyncClient(proxy=proxy, timeout=30.0) if proxy else httpx.AsyncClient(timeout=30.0)
adapter = YouTubeTranscriptAdapter(api=ytt)
meta = YouTubeOEmbedAdapter(client=http)
```

### Pattern 2: Language preference with dialect base + list-then-pick

**What:** Do **not** rely solely on `fetch(languages=["ru","en"])` for dialect normalization (D-07 requires `ru-RU`→`ru` and rejects `rue`). Prefer:

1. `api.list(video_id)` → iterate tracks  
2. Partition by `base = language_code.split("-")[0].lower()`  
3. Prefer any track with `base == "ru"`, else any `base == "en"` (manual or auto — D-06/D-08)  
4. `track.fetch()` → join snippet texts → `Transcript(text=..., language=base, video_id=...)`  
5. If list empty / all disabled → `CaptionsUnavailable` / `CaptionsDisabled` as mapped  
6. If tracks exist but none ru/en → `CaptionsNoPreferredLanguage` with `available_languages` in context (D-09)  
7. If joined text blank after strip → `CaptionsEmpty` (Phase 6 D-09 forbids empty `Transcript`)

**Library note:** `fetch(video_id, languages=["ru","en"])` is still useful as a fast path in docs/examples `[CITED: Context7]`, but dialect + `no_preferred_language` context **requires** `list()` for available languages. Recommendation: implement list-then-pick as the canonical path (one code path, easier to test with fakes).

### Pattern 3: SDK → CaptionsError → IngestError (two-hop mapping)

**What:** Adapter catches `youtube_transcript_api` exceptions and raises module-local subtypes. Ingestion mapper translates subtypes → locked `reason` strings. SDK class names may appear only inside `context["exception_class"]`, never as `reason` (D-10/D-13).

**Recommended mapping table (discretion — locked reasons must remain):**

| SDK / condition | CaptionsError subtype (discretion) | `IngestError.reason` |
|-----------------|------------------------------------|----------------------|
| `NoTranscriptFound` after empty preferred set / no tracks | `CaptionsUnavailable` | `no_captions` |
| Preferred langs missing but others present | `CaptionsNoPreferredLanguage` | `no_preferred_language` |
| `TranscriptsDisabled` | `CaptionsDisabled` | `captions_disabled` |
| `VideoUnavailable` / `InvalidVideoId` / `AgeRestricted` (discretion group) | `CaptionsVideoUnavailable` | `video_unavailable` |
| `IpBlocked` / `RequestBlocked` | `CaptionsBlocked` | `youtube_blocked` |
| `PoTokenRequired` | Prefer dedicated subtype **or** `CaptionsBlocked` + context flag — **recommend own subtype** `CaptionsBotChallenge` (discretion) | `bot_challenge` |
| Timeout / connection errors from transport | `CaptionsNetworkError` | `network_error` |
| Fetched text blank | `CaptionsEmpty` | `empty_captions` |
| Other `CouldNotRetrieveTranscript` | base `CaptionsError` or catch-all | `unknown_captions_error` |

**Metadata mapping (D-25):**

| Condition | MetadataError | Suggested `reason` |
|-----------|---------------|--------------------|
| HTTP 404/403 / blocked body | `MetadataUnavailable` | `metadata_unavailable` |
| Timeout / connect error | `MetadataNetworkError` | `network_error` |
| Bad JSON / missing `author_name` | `MetadataInvalidResponse` | `metadata_invalid_response` (or fold into `metadata_unavailable` — prefer distinct for ops) |

### Pattern 4: Additive fake failure catalogs (D-15 / D-26)

**What:** Extend existing fakes without breaking Phase 6 success+spy tests:

```python
class FakeTranscriptProvider:
    def __init__(
        self,
        result: Transcript,
        failures: dict[str, CaptionsError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[str] = []

    async def get(self, video_id: str) -> Transcript:
        self.calls.append(video_id)
        if video_id in self._failures:
            raise self._failures[video_id]
        return self._result
```

Mirror for `FakeVideoMetadataProvider` with `VideoMetadata` + `MetadataError`.

### Pattern 5: Async port + sync SDK

**What:** `async def get` implementations call sync library via `await asyncio.to_thread(self._fetch_sync, video_id)` so the event loop is not blocked and unit tests keep using `asyncio.run`.  
**When to use:** Transcript adapter (sync `youtube-transcript-api`). oEmbed can be fully async with `httpx.AsyncClient`.  
**Do not** add `pytest-asyncio` unless necessary (Phase 6 locked `asyncio.run`).

### Pattern 6: Minimal ingestion-service scaffold (not Typer CLI)

**What:** Phase 7 creates the package + URL/`IngestError`/Settings/mapper tests. Phase 10 owns Typer entry, progress printers, and full pipeline orchestration (D-24 order).  
**Avoid:** Implementing `ingest` CLI command or DeepSeek wiring “while we’re here.”

### Anti-Patterns to Avoid

- **Adapters call `os.environ`:** Violates D-17.
- **Returning empty `Transcript` on failure:** Violates Phase 6 D-09 + CAP-02.
- **`reason=TranscriptsDisabled` or other SDK class names:** Violates D-10.
- **Putting `stage=` inside `data-collection`:** Violates D-11.
- **Whisper / Foundry ASR on IP block:** Pitfall 5; milestone OUT.
- **Fabricating `author="unknown"`:** Violates D-23.
- **Parsing URL inside ports:** Violates D-04.
- **Exporting fakes from `data_collection.__all__`:** Violates Phase 6 D-04.
- **Treating Phase 7 CAP-02 as requiring live Supabase:** Deferred by D-14 — do not block phase on DB.
- **Accepting `/live/`, `/v/`, `/e/` without decision reopen:** Out of scope (D-02).
- **Silent any-language fallback:** Violates D-09.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Captions HTTP/XML | Custom timedtext scraper | `youtube-transcript-api` 1.2.x | Maintained exception catalog + proxy helpers |
| oEmbed client | `urllib` ad-hoc | Injected `httpx.AsyncClient` | Timeouts, SOCKS, testability |
| SOCKS for AdGuard | Custom socket tunnel | `GenericProxyConfig` + `httpx[socks]` + `PySocks` | D-18; verified Phase 6 proxy host |
| URL regex sprawl | Multiple competing parsers | One `extract_video_id` with table-driven tests | D-01…D-05 |
| Pipeline stage enums in adapters | Duplicate stage strings | `IngestError` only in ingestion-service | D-11 |
| Async test plugin | New pytest-asyncio | `asyncio.run` | Phase 6 precedent |
| Live network in default CI | Unmarked live tests | `@pytest.mark.integration` + skip | D-20 |

**Key insight:** Phase 7 success is a **stable operator error contract** (`stage`/`reason`) plus **injected, testable adapters** — not a live UAT of 3–5 videos (that is Phase 10).

## Runtime State Inventory

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | No DB writes in Phase 7 | None — assert no migrations / supabase writers |
| Live service config | None for captions today | Document optional `YOUTUBE_PROXY_URL` in runbook only |
| OS-registered state | None | None |
| Secrets/env vars | New optional `YOUTUBE_PROXY_URL` (not a secret by itself; may embed credentials later) | Read only in `ingestion-service` Settings; never commit real proxy URLs with creds; never `VITE_*` |
| Build artifacts | New workspace member + lockfile after `uv add` | Commit lockfile as part of phase execution |
| Existing Phase 6 contracts | `Transcript`, `VideoMetadata`, `TranscriptProvider`, `FakeTranscriptProvider` | Extend; do not reopen field shapes |

**Nothing found** that blocks scaffolding. `ingestion-service/` directory **does not exist** yet `[VERIFIED: glob 0 files]`. Workspace members today: `backend`, `data-collection`, `supabase-integration` only `[VERIFIED: root pyproject.toml]`.

## Common Pitfalls

### Pitfall 1: Treating Cloud.ru `IpBlocked` as “no captions” / Whisper opportunity
**What goes wrong:** Wrong `reason`, operators chase content instead of proxy; Whisper creep.  
**Why it happens:** Library names are confusing; `PITFALLS.md` Pitfall 5.  
**How to avoid:** Map `IpBlocked`/`RequestBlocked` → `youtube_blocked`; `PoTokenRequired` → `bot_challenge` (D-19); document proxy in runbook.  
**Warning signs:** Works on laptop, fails on VM with `captions_disabled`.

### Pitfall 2: `fetch(languages=["ru","en"])` without `list()` for `no_preferred_language`
**What goes wrong:** Cannot populate `available_languages`; dialect `ru-RU` may be missed or `rue` falsely accepted.  
**How to avoid:** Canonical list-then-pick + base normalization tests (D-07/D-09).  
**Warning signs:** Only `NoTranscriptFound` mapped to `no_captions` for German-only videos.

### Pitfall 3: Putting URL parsing on the port “to save a package”
**What goes wrong:** Breaks Phase 6 fakes/tests; costly reversibility (D-04).  
**How to avoid:** `extract_video_id` only in `ingestion-service`.  
**Warning signs:** `TranscriptProvider.get` accepting full URLs.

### Pitfall 4: Adapters reading `os.environ`
**What goes wrong:** Untestable CI; dual config sources; violates D-17.  
**How to avoid:** Constructor injection; Settings in composition only.  
**Warning signs:** `os.getenv("YOUTUBE_PROXY_URL")` inside `adapters/`.

### Pitfall 5: Claiming CAP-02 complete via live DB without persist
**What goes wrong:** Phase blocked or false green.  
**How to avoid:** D-14 — adapter/unit proof now; roadmap note for Phase 9/10 spy.  
**Warning signs:** Phase 7 plan depends on `DraftMaterialWriter`.

### Pitfall 6: Empty transcript text coerced into `Transcript`
**What goes wrong:** Pydantic may reject or LLM later invents content.  
**How to avoid:** `CaptionsEmpty` before constructing DTO (Phase 6 D-09).  
**Warning signs:** Adapter returns `text=" "` after strip failure.

### Pitfall 7: Shipping Typer one-shot / DeepSeek in Phase 7
**What goes wrong:** Scope bleed into Phases 8–10; weaker TDD focus on captions.  
**How to avoid:** Minimal package scaffold only.  
**Warning signs:** `typer` / `openai` appear in Phase 7 lockfile diff.

### Pitfall 8: Integration tests unmarked → flaky CI / Cloud.ru blocks
**What goes wrong:** Default `uv run pytest` hits network.  
**How to avoid:** Register `integration` marker; skip unless env flag (e.g. `RUN_YOUTUBE_INTEGRATION=1`); document in runbook (D-20).  
**Warning signs:** CI red on IP block.

## Code Examples

### extract_video_id (sketch within D-01…D-05)

```python
# ingestion_service/url.py — ~25 lines; table-driven tests own the contract
import re
from urllib.parse import parse_qs, urlparse

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")

def extract_video_id(value: str) -> str:
    raw = value.strip()
    if _ID_RE.fullmatch(raw):
        return raw
    # normalize m.youtube.com → youtube.com; accept watch/youtu.be/shorts/embed
    # reject playlist-without-v, channel, non-youtube, wrong id length
    ...
```

### IngestError envelope (D-11 / D-13)

```python
# ingestion_service/domain/errors.py
from dataclasses import dataclass, field
from typing import Any, Literal

Stage = Literal[
    "url", "captions", "metadata", "consistency", "llm", "llm_truncation", "persist"
]

@dataclass
class IngestError(Exception):
    stage: Stage
    reason: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "ok": False,
            "stage": self.stage,
            "reason": self.reason,
            "message": self.message,
            "exit_code": self.exit_code,
        }
        if self.context:
            payload["context"] = self.context
        return payload
```

### Captions adapter happy path (sync core)

```python
# Adapted from [CITED: Context7 /jdepoix/youtube-transcript-api]
# Prefer list-then-pick for D-07/D-09; join snippets; language = base.

def _pick_track(transcript_list) -> tuple[object, str]:
    tracks = list(transcript_list)
    def base(code: str) -> str:
        return code.split("-")[0].lower()
    for preferred in ("ru", "en"):
        for t in tracks:
            if base(t.language_code) == preferred:
                return t, preferred
    available = sorted({t.language_code for t in tracks})
    raise CaptionsNoPreferredLanguage(video_id=..., available_languages=available)

# empty text after join → CaptionsEmpty
```

### oEmbed (D-22)

```python
# GET https://www.youtube.com/oembed?url={canonical}&format=json
# canonical = f"https://www.youtube.com/watch?v={video_id}"
# author = payload["author_name"]  # required; missing → MetadataInvalidResponse
# published_at = None  # oEmbed never provides it (Phase 6 D-12)
# VideoMetadata(video_id=..., source_url=canonical, author=..., published_at=None)
```

### Existing port to implement against `[VERIFIED]`

```python
# data-collection/src/data_collection/ports/transcript_provider.py
class TranscriptProvider(Protocol):
    async def get(self, video_id: str) -> Transcript: ...
```

### Public API growth `[VERIFIED today: six names]`

```python
# Target __all__ after Phase 7:
# Transcript, VideoMetadata, MaterialDraft, TemplateKind,
# TranscriptProvider, ArticleGenerator, VideoMetadataProvider
# (CaptionsError/MetadataError: discretionary — either public for mapper imports
#  or imported via data_collection.errors.*; prefer exporting error bases if
#  ingestion-service must not deep-import internals.)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `fetch(url)` on transcript port (early ARCHITECTURE) | `get(video_id)` + separate `extract_video_id` | Phase 6 D-15 + Phase 7 D-04 | Parser ownership clear |
| oEmbed optional / later | oEmbed **in Phase 7** with captions | 07-CONTEXT D-21 | Phase 8–10 assume both ports ready |
| CAP-02 = live zero DB rows immediately | Adapter/unit now; spy later | D-14 | Unblocks Phase 7 without persist |
| Static `get_transcript` 0.6.x docs | Instance `YouTubeTranscriptApi().fetch/list` 1.2.x | STACK.md | Pin ≥1.2 |
| Direct env in adapters | Composition injection | D-17 | Testable, backend-aligned |
| Treat IP block as missing captions | Distinct `youtube_blocked` / `bot_challenge` | D-10/D-19 + PITFALLS | Ops-correct runbook |

**Deprecated/outdated for this phase:**
- Early research “oEmbed keep off critical path if captions-only UAT enough” — **superseded** by D-21.
- Sketch `TranscriptProvider.fetch(video_url_or_id)` in `ARCHITECTURE.md` Pattern 2 — **superseded**.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | List-then-pick is preferred over fetch-only for dialect + available_languages | Pattern 2 | Extra list() call; still correct |
| A2 | `asyncio.to_thread` is the right sync→async bridge | Pattern 5 | Could use sync call inside async (blocks loop) — worse under CLI later |
| A3 | Export `VideoMetadataProvider` (+ optionally error bases) from public `__all__` | Structure | Deep-import of errors if not exported |
| A4 | Dedicated `CaptionsBotChallenge` subtype is clearer than context-only | Pattern 3 / Discretion | Either OK if `reason=bot_challenge` tested |
| A5 | Minimal `ingestion-service` without Typer is in Phase 7 scope | Pattern 6 | If planner defers package to Phase 10, URL/`IngestError` need a temporary home — **reject**; CONTEXT places them in ingestion-service now |
| A6 | Integration skip via marker + env `RUN_YOUTUBE_INTEGRATION=1` | D-20 Discretion | Alternate: `pytest -m "not integration"` in addopts |
| A7 | `httpx==0.28.1` already in workspace satisfies oEmbed dep when added to data-collection | Stack | May need explicit dep line on data-collection regardless |
| A8 | Reason `metadata_invalid_response` is acceptable alongside D-25 types | Pattern 3 | May fold into `metadata_unavailable` if planner wants fewer reasons |

**If empty:** N/A — discretion items remain for planner where marked.

## Open Questions (RESOLVED for planning)

1. **Does Phase 7 include oEmbed?** — RESOLVED: **Yes** (D-21…D-26).
2. **Where does URL parsing live?** — RESOLVED: `ingestion-service` `extract_video_id` (D-04).
3. **How is CAP-02 proven without persist?** — RESOLVED: Adapter/unit raises `CaptionsError` / never returns `Transcript`; live spy Phase 9/10 (D-14).
4. **Shared proxy env name?** — RESOLVED: `YOUTUBE_PROXY_URL` (D-16).
5. **bot_challenge subtype?** — RESOLVED as discretion: prefer clear tested mapping; recommend dedicated subtype.
6. **Create `ingestion-service` now or Phase 10?** — RESOLVED by CONTEXT: URL/`IngestError`/Settings live there in Phase 7; Typer one-shot stays Phase 10.

No blockers for planning.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python ≥3.12 | All | ✓ | workspace | — |
| uv | deps + pytest | ✓ | workspace | — |
| pydantic / pytest | DTOs / tests | ✓ | 2.13.5 / 9.1.1 | — |
| httpx | oEmbed | ✓ in workspace | 0.28.1 | Add explicitly to data-collection |
| `httpx[socks]` / socksio | SOCKS oEmbed | ✗ extra not confirmed installed | — | `uv add --package data-collection "httpx[socks]==0.28.1"` |
| youtube-transcript-api | captions | ✗ not installed | latest 1.2.4 on PyPI | `uv add` in phase |
| PySocks | captions SOCKS | ✗ | — | `uv add` per D-18 |
| ingestion-service package | URL / IngestError / Settings | ✗ missing | — | Scaffold in Phase 7 |
| AdGuard SOCKS `192.168.1.68:1080` | optional live proof | ops-local | — | Unit mocks; document runbook |
| Supabase / persist ports | CAP-02 live spy | N/A this phase | — | Deferred Phase 9/10 |
| pytest-asyncio | — | ✗ | — | `asyncio.run` |

**Missing dependencies with no fallback:** none if phase installs transcript API + SOCKS extras and scaffolds `ingestion-service`.  
**Missing with fallback:** live YouTube → mocked unit tests; proxy → direct (expect blocks on Cloud.ru).

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled** (same as Phase 6 research).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `9.1.1` (workspace) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` — today `testpaths = ["tests/unit"]` only |
| Quick run command | `uv run pytest tests/unit/test_extract_video_id.py tests/unit/test_youtube_transcript_adapter.py tests/unit/test_ingest_error.py -x` |
| Full suite command | `uv run pytest` (unit only by default) |
| Integration (optional) | After marker registration, path-explicit because `testpaths = ["tests/unit"]`: `RUN_YOUTUBE_INTEGRATION=1 uv run pytest tests/integration -m integration` (exact env name discretionary) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CAP-01 | `extract_video_id` accepts watch/youtu.be/shorts/embed/bare id; rejects playlist/channel/bad length | unit | `uv run pytest tests/unit/test_extract_video_id.py -x` | ❌ Wave 0 |
| CAP-01 | Adapter prefers `ru` then `en`; dialect `ru-RU`/`en-US` → base; rejects `rue`/`enm` | unit (mocked list/fetch) | `uv run pytest tests/unit/test_youtube_transcript_adapter.py -x` | ❌ Wave 0 |
| CAP-01 | Happy path returns `Transcript` with joined text + normalized language + video_id | unit | same | ❌ Wave 0 |
| CAP-02 | Missing/disabled/blocked/empty → raises `CaptionsError` subtype; never returns `Transcript` | unit | `uv run pytest tests/unit/test_youtube_transcript_adapter.py -x` | ❌ Wave 0 |
| CAP-02 | Mapper emits `IngestError(stage="captions", reason∈locked set)` + `to_dict()` shape | unit | `uv run pytest tests/unit/test_captions_error_mapping.py tests/unit/test_ingest_error.py -x` | ❌ Wave 0 |
| CAP-02 (deferred live) | Persist spy `calls == []` | — | Phase 9/10 only | N/A |
| D-15 | FakeTranscriptProvider failures dict raises; success path unchanged | unit | `uv run pytest tests/unit/test_transcript_provider_fake.py tests/unit/test_fake_transcript_provider_failures.py -x` | ⚠️ partial (success exists) |
| D-21…D-26 | oEmbed adapter builds canonical URL; author required; published_at None; MetadataError mapping | unit | `uv run pytest tests/unit/test_youtube_oembed_adapter.py tests/unit/test_metadata_error_mapping.py -x` | ❌ Wave 0 |
| D-26 | FakeVideoMetadataProvider success+spy+failures | unit | `uv run pytest tests/unit/test_fake_video_metadata_provider.py -x` | ❌ Wave 0 |
| D-17 | Adapter constructed without reading environ (composition injects) | unit | adapter tests with fake clients | ❌ Wave 0 |
| D-20 | Integration tests skipped by default | unit config | `uv run pytest -m integration` exits 5 or 0-skipped | ❌ Wave 0 |
| Public API | `__all__` includes `VideoMetadataProvider`; fakes still excluded | unit | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ⚠️ exists — extend |

### Sampling Rate

- **Per task commit:** targeted new unit file(s) with `-x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full unit suite green before `/gsd-verify-work`; integration optional/manual via runbook
- **Max feedback latency:** ~60s for unit; integration only when explicitly enabled

### Wave 0 Gaps

- [ ] Register `integration` pytest marker; keep default `testpaths` unit-only **or** add `addopts = "-m 'not integration'"` if integration dir is collected
- [ ] RED tests for `extract_video_id` accept/reject matrix (D-01…D-05)
- [ ] RED tests for transcript adapter language preference + error mapping (mocked SDK)
- [ ] RED tests for oEmbed adapter + MetadataError mapping (mocked httpx)
- [ ] RED tests for `IngestError.to_dict()` envelope
- [ ] RED tests for additive fake failure catalogs (D-15/D-26)
- [ ] Scaffold `ingestion-service` workspace member + `data-collection` deps (`youtube-transcript-api`, `httpx[socks]`, `PySocks`)
- [ ] Extend runbook with `YOUTUBE_PROXY_URL` + how to run optional live tests
- [ ] Assert **no** Supabase migrations / persist writers / Typer CLI / openai deps in this phase
- [ ] Document Phase 9/10 follow-up: CAP-02 live spy requirement (D-14)

### Manual-Only Verifications

| Item | Why manual | Notes |
|------|------------|-------|
| Live captions via AdGuard SOCKS | Network + local proxy | Optional; runbook; not CI gate |
| Cloud.ru without proxy → expect `youtube_blocked` | Ops confirmation | Document risk; do not “fix” with Whisper |

## Security Domain

> `security_enforcement` absent in config → treat as **enabled**.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth surface |
| V3 Session Management | no | — |
| V4 Access Control | no | No DB writes |
| V5 Input Validation | yes | Strict URL/`video_id` parsing; reject non-YouTube / bad length |
| V6 Cryptography | no | Optional proxy URL may carry credentials — keep in env only |
| V10 Malicious Input | yes | Do not shell-interpolate URLs; httpx/requests parameterized only |
| V14 Configuration | yes | Adapters never read env; composition-owned Settings; no secrets in adapters |

### Known Threat Patterns for captions/metadata adapters

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| SSRF via attacker-controlled “YouTube URL” | Spoofing / elevation | Allowlist host patterns in `extract_video_id`; oEmbed only after id extract + canonical watch URL built in adapter |
| Proxy credential leakage in logs/errors | Information disclosure | Do not put full `YOUTUBE_PROXY_URL` into `IngestError.context`; redact if logged |
| Treating blocked IP as empty transcript → LLM garbage | Tampering | Fail-closed CaptionsError; no Whisper |
| SDK exception names as operator contract | Spoofing of ops signals | Locked `reason` codes only (D-10) |
| Committing `.env` with proxy/service keys | Information disclosure | gitignore; runbook warns; CLI-05 separate env later |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/07-captions-adapter/07-CONTEXT.md` — D-01…D-26 (law)
- `.planning/phases/07-captions-adapter/07-DISCUSSION-LOG.md` — decision trail
- `.planning/REQUIREMENTS.md` — CAP-01, CAP-02
- `.planning/ROADMAP.md` — Phase 7 goal + success criteria; Phase 8–10 dependents
- `.planning/STATE.md` — Phase 7 context gathered; ready to plan
- `.planning/phases/06-ports-dtos/06-CONTEXT.md` — locked DTOs/ports (D-09, D-11…D-17)
- `.planning/research/STACK.md`, `PITFALLS.md`, `ARCHITECTURE.md`, `SUMMARY.md` — stack/pitfalls (superseded notes called out)
- `.cursor/rules/architecture.mdc`, `tdd.mdc`, `AGENTS.md`
- Live code: `data_collection` ports/DTOs/fakes/`__init__.py`; `backend/.../composition/settings.py`
- `docs/agents/local-platform-runbook.md` — no proxy section yet (must extend)
- PyPI `youtube-transcript-api==1.2.4`; workspace `httpx==0.28.1`, `pydantic==2.13.5`, `pytest==9.1.1`
- Root `pyproject.toml` — workspace members lack `ingestion-service`; pytest `testpaths=["tests/unit"]`

### Secondary (MEDIUM confidence)
- Context7 `/jdepoix/youtube-transcript-api` — `fetch`/`list`, exception catalog, `GenericProxyConfig`, proxy notes
- Context7 `/encode/httpx` — `proxy=` parameter, `httpx[socks]` / `socksio`
- Phase 6 verified AdGuard host `192.168.1.68:1080` (CONTEXT specifics)

### Tertiary (LOW confidence)
- Exact future Typer progress UX — Phase 10
- Whether Cloud.ru always blocks without proxy — ops-dependent; plan for it

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pins + Context7 + PyPI verified; install still pending execution
- Architecture: HIGH — CONTEXT locks + Phase 6 contracts + module ownership rules
- Pitfalls: HIGH — fail-closed / proxy / CAP-02 deferral / SSRF allowlist called out
- Discretion items: MEDIUM — file layout and exact subtype table left for planner

**Research date:** 2026-09-26  
**Valid until:** 2026-10-26 (re-check if `youtube-transcript-api` 2.x appears or YouTube blocks change proxy requirements)
