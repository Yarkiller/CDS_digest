# Phase 7: Captions Adapter - Context

**Gathered:** 2026-09-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Operator-facing YouTube fetch for v1.1 ingestion: resolve a YouTube URL (or bare video id) to a `Transcript` and `VideoMetadata`, or exit loudly with staged errors and no database side effects. This phase delivers: URL parser in `ingestion-service`; ports `TranscriptProvider` + `VideoMetadataProvider`; adapters `YouTubeTranscriptAdapter` + `YouTubeOEmbedAdapter`; `CaptionsError` / `MetadataError` taxonomies in `data-collection`; `IngestError` + diagnostic JSON in `ingestion-service`; shared optional `YOUTUBE_PROXY_URL`; additive fake failure catalogs. DeepSeek/LLM, persist/shortlist, and the Typer one-shot composition stay in Phases 8–10 (adapters and error contracts here unlock them).

</domain>

<decisions>
## Implementation Decisions

### URL → video_id
- **D-01:** Accept `youtube.com/watch?v=…`, `youtu.be/…`, `/shorts/…`, `/embed/…` (with or without `www`). Normalize `m.youtube.com` → `youtube.com`. Strip noise query params (`t`, `list`, `si`, `feature`, `ab_channel`, etc.). Reject playlist-without-`v=`, channel URLs, non-YouTube, watch without `v=`, and ids not exactly 11 chars. — **Reversibility:** reversible — new URL forms are additive with tests.
- **D-02:** Out of scope for v1.1: `/live/`, `/v/`, `/e/` — add later when operators hit them, with a test.
- **D-03:** Also accept a bare 11-char video id (`[A-Za-z0-9_-]{11}`) as input.
- **D-04:** Parser is `extract_video_id(url)` (~25 lines) in `ingestion-service/`, **not** on `TranscriptProvider` / metadata ports. — **Reversibility:** costly — moving parse into the port would change both provider signatures and all fakes/tests.
- **D-05:** Parse failures use `stage=url` (before network). Caption unavailability uses `stage=captions` (after network). Both `exit_code=1`; distinguish via `stage` + `reason` in JSON. CAP-02 covers captions only; URL parse is not CAP-02.

### Language preference
- **D-06:** Allow auto-generated captions when language matches preference (no manual-only filter).
- **D-07:** Dialect tags via prefix normalization: `base = lang.split("-")[0].lower()`; accept only if `base in ("ru", "en")`. Examples: `ru`, `ru-RU`, `en`, `en-US` match; `rue` / `enm` do not. Store `Transcript.language` as normalized base `"ru"` or `"en"` — no dialect kept. Tests: those five cases.
- **D-08:** Prefer order: if any `ru` track (manual or auto) → take it; else any `en`; else fail. No manual/auto ranking within a language. — **Reversibility:** reversible — manual-preference can be added later as an adapter option.
- **D-09:** If neither preferred language exists → fail closed `stage=captions`, `reason=no_preferred_language`, include available languages in error `context`. Any-language fallback deferred to v1.2+.

### Fail-closed error surface
- **D-10:** Mapped stable `reason` codes under `stage=captions`: `no_captions`, `no_preferred_language`, `captions_disabled`, `video_unavailable`, `youtube_blocked`, `bot_challenge`, `network_error`, `empty_captions`, `unknown_captions_error`. Do not pass through SDK exception class names as `reason`.
- **D-11:** `IngestError` lives in `ingestion-service/.../domain/errors.py` (not `data-collection`). Stages: `Literal["url", "captions", "metadata", "consistency", "llm", "llm_truncation", "persist"]`. CLI JSON via `to_dict()`. `data-collection` does not know pipeline stages. — **Reversibility:** costly — stage set is the CLI/operator contract across Phases 7–10.
- **D-12:** Adapter exceptions in `data-collection/errors/captions.py`: base `CaptionsError(video_id, **context)` plus subtypes `CaptionsUnavailable`, `CaptionsDisabled`, `CaptionsBlocked`, `CaptionsVideoUnavailable`, `CaptionsNoPreferredLanguage`, `CaptionsNetworkError`, `CaptionsEmpty` (and map bot challenges appropriately toward `bot_challenge`). Adapter maps SDK → these types; ingestion use-case maps → `IngestError(stage="captions", reason=...)`.
- **D-13:** Diagnostic JSON envelope: `{ok, stage, reason, message, context?, exit_code}`. `context` holds typed values (e.g. `video_id`, `available_languages`, exception class string) — not a free-form dump.
- **D-14:** Phase 7 proves CAP-02 at adapter/unit level: failures raise `CaptionsError` / never return a `Transcript`. Live “zero DB rows” with persist spy deferred to Phase 9/10 when persist exists. — **Reversibility:** one-way once Phase 9/10 omit the spy — must add roadmap/test requirement: fake failing `TranscriptProvider` + spy `PersistPort` → `persist.calls == []`.
- **D-15:** Extend `FakeTranscriptProvider` with additive `failures: dict[str, CaptionsError]` — `get` raises if `video_id` in map; existing success+spy tests unchanged.

### Captions network / proxy
- **D-16:** Shared optional env `YOUTUBE_PROXY_URL` (`socks5://…` or `http://…`) for captions (`GenericProxyConfig`) and oEmbed (`httpx`). Unset → direct. Document Cloud.ru risk: without proxy, expect `IpBlocked` / `youtube_blocked`. — **Reversibility:** reversible — env name is local ops config.
- **D-17:** Composition/`Settings` in `ingestion-service` reads env and injects ready clients into adapters. Adapters never read `os.environ`. Matches backend composition pattern.
- **D-18:** SOCKS support required for verified AdGuard path: `uv add` `httpx[socks]` and `PySocks` / `requests[socks]`.
- **D-19:** `PoTokenRequired` (and similar bot challenges) → `reason=bot_challenge`, distinct from `youtube_blocked`. Both fail-closed; no cookie/poToken bypass in v1.1.
- **D-20:** Tests: unit with mocked SDK always in CI; optional `@pytest.mark.integration` skipped by default; run with proxy via runbook (document in `docs/agents/local-platform-runbook.md`).

### VideoMetadata / oEmbed (in Phase 7)
- **D-21:** Phase 7 ships captions **and** oEmbed: ports `TranscriptProvider` + `VideoMetadataProvider`; adapters `YouTubeTranscriptAdapter` + `YouTubeOEmbedAdapter`; `CaptionsError` + `MetadataError`; fakes for both; shared proxy; URL parser. — **Reversibility:** costly — splitting metadata out later rewrites Phase 8–10 readiness assumptions.
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria, CAP-01/CAP-02; Phase 8–10 dependents
- `.planning/REQUIREMENTS.md` — CAP-01, CAP-02; later LLM/PERS/CLI (do not implement LLM/persist/CLI one-shot here)
- `.planning/PROJECT.md` — captions via `youtube-transcript-api`; no Whisper this milestone; DeepSeek bend of ADR-0002
- `.planning/phases/06-ports-dtos/06-CONTEXT.md` — locked DTOs/ports: `Transcript`, `VideoMetadata`, `TranscriptProvider.get(video_id)`, empty captions = Phase 7 failure, oEmbed author + AdGuard proxy (D-11…D-17), fake spy shapes
- `CONTEXT.md` — glossary: material = prepared article; provenance language

### Research (v1.1 ingestion)
- `.planning/research/STACK.md` — `youtube-transcript-api` ≥1.2 instance `.fetch`; language list; exception catalog; pin guidance
- `.planning/research/PITFALLS.md` — fail-closed captions; Cloud.ru IP block; do not treat block as Whisper opportunity
- `.planning/research/ARCHITECTURE.md` — adapters in `data-collection`; thin CLI composition root
- `.planning/research/SUMMARY.md` — captions-first pipeline overview

### Architecture & ops
- `.cursor/rules/architecture.mdc` — Ports & Adapters; `data-collection` owns external adapters; composition wiring
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — FoundryModels long-term; captions-only + temporary DeepSeek for this milestone
- `docs/agents/local-platform-runbook.md` — document optional integration run + `YOUTUBE_PROXY_URL` (extend as needed)

### Code contracts from Phase 6
- `data-collection/src/data_collection/ports/transcript_provider.py` — async `get(video_id) -> Transcript`
- `data-collection/src/data_collection/dto/transcript.py` — `text`, `language`, `video_id`
- `data-collection/src/data_collection/dto/` — `VideoMetadata` fields per Phase 6 D-11
- `data-collection/src/data_collection/tests_support/fakes.py` — extend fakes; do not export fakes from package root

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Phase 6 `Transcript` / `VideoMetadata` / `TranscriptProvider` Protocol + `FakeTranscriptProvider` — implement real adapters against these contracts; add `VideoMetadataProvider` + fake
- Pydantic v2 DTOs in `data-collection`
- Backend composition pattern (`Settings` + injected clients) — mirror in `ingestion-service` composition
- Verified AdGuard SOCKS `192.168.1.68:1080` for YouTube oEmbed (Phase 6)

### Established Patterns
- Public `data-collection` exports types/ports only; fakes in `tests_support`
- Unit tests under `tests/unit/` with TDD; no network in default CI
- Optional integration markers used elsewhere in the project for live checks
- Adapter maps SDK/HTTP errors at the boundary into module-local exception types

### Integration Points
- Phase 8: DeepSeek `ArticleGenerator` consumes `Transcript`; honesty / always-Russian (deferred LLM-04 from Phase 6)
- Phase 9: persist `MaterialDraft` needs `VideoMetadata` author + nullable `published_at`; CAP-02 live zero-row spy
- Phase 10: Typer one-shot wires URL parse → captions → metadata → LLM → persist; CONSISTENCY-01 video_id check; UAT 3–5 videos

</code_context>

<specifics>
## Specific Ideas

- Shared proxy env name: `YOUTUBE_PROXY_URL`.
- Canonical watch URL built inside oEmbed adapter: `https://www.youtube.com/watch?v={video_id}`.
- Captions language preference implemented via library `languages=["ru", "en"]` plus explicit no-preferred-language failure when only other langs exist (do not silently accept `de`/`es`).
- Operator JSON must remain stable across phases — stage/`reason` are the contract, not SDK names.
- Phase 6 verified proxy host example: AdGuard VPN `192.168.1.68:1080` (SOCKS5).

</specifics>

<deferred>
## Deferred Ideas

- URL forms `/live/`, `/v/`, `/e/` — additive when operators need them
- Any-language caption fallback + translation marker (v1.2+)
- Manual-over-auto preference within a language (v1.2+)
- PoToken / cookie bypass for `bot_challenge` (monitor via reason; implement later if needed)
- Fabricated author fallback on metadata failure (v1.2+)
- **Phase 9/10 requirement note:** use-case test with failing `TranscriptProvider` + spy persist port asserting `persist.calls == []` (live CAP-02)
- DeepSeek, templates, persist, shortlist, Typer one-shot — Phases 8–10 as roadmapped
- CONSISTENCY-01 (`transcript.video_id == metadata.video_id`) — Phase 10

</deferred>

---

*Phase: 7-Captions Adapter*
*Context gathered: 2026-09-26*
