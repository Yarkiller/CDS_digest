# Phase 6: Ports & DTOs - Context

**Gathered:** 2026-09-26
**Status:** Ready for planning

<domain>
## Phase Boundary

`data-collection` exposes typed ingestion contracts so adapters and the CLI never mix a transcript with a prepared article. This phase delivers: types `Transcript`, `VideoMetadata`, `MaterialDraft`, and `TemplateKind`; ports `TranscriptProvider` and `ArticleGenerator` with in-memory fakes; a tested assembler that builds `MaterialDraft` from an internal `ArticleDraft` plus `VideoMetadata` plus a caller-supplied `provenance_label`; and a type-boundary guarantee that a `Transcript` cannot be passed where a `MaterialDraft` is required. Captions fetching, DeepSeek, database writes, and the CLI one-shot stay in Phases 7–10.

</domain>

<decisions>
## Implementation Decisions

### Existing DTO overlap
- **D-01:** Replace overlapping brownfield DTOs. Public API is `Transcript`, `VideoMetadata`, `MaterialDraft`, `TemplateKind`, plus ports `TranscriptProvider` and `ArticleGenerator`. Do not keep `YoutubeSourceDto`, `TranscriptResultDto`, or `ArticleAssistDto` as parallel types. — **Reversibility:** costly — consumers and unit tests must move to the new names; reintroducing the old surface is a second public contract.
- **D-02:** Remove the rest of the old public surface too: `TextImportDto`, `SummaryResultDto`, `TaggingResultDto`, `EmbeddingResultDto`, and package-exported `EMBEDDING_DIM`. Phase 6 public API is only the new ingestion types and ports. Backend keeps its own `EMBEDDING_DIM = 1024` in `query_embedder.py`; schema `vector(1024)` is unchanged. — **Reversibility:** costly — Foundry-shaped stubs return only when a later milestone reintroduces them.
- **D-03:** Delete old modules and their tests: `dto/youtube.py`, `dto/foundry.py`, `dto/text_import.py`, and unit tests that import them (`test_youtube_source_dto.py`, `test_foundry_dtos.py`, `test_text_import_dto.py`).
- **D-04:** Fakes live in `data-collection/tests_support` only. Public package `__init__` exports types and ports, not fakes. Matches backend `tests_support` pattern.

### MaterialDraft and assembler
- **D-05:** `MaterialDraft` fields: required `title`, `dek`, `body_markdown`, `source_url`, `youtube_video_id`, `source_author`, `provenance_label`; optional `source_published_at: datetime | None`. Tags, role hints, and model ids stay off this type. Missing any required field is a validation error. — **Reversibility:** costly — persist (PERS-01) and assembler copy these names; revising them rewrites Phase 9 contracts.
- **D-06:** `ArticleGenerator` returns an internal `ArticleDraft` (`title`, `dek`, `body_markdown` only). `ArticleDraft` is not part of the public package API. The adapter stays LLM-only and does not learn YouTube field names. — **Reversibility:** costly — swapping to “generator builds MaterialDraft” would push provenance into the adapter.
- **D-07:** Phase 6 implements a tested assembler: `ArticleDraft` + `VideoMetadata` + explicit `provenance_label` → `MaterialDraft`. No network, no database. Assembler does not invent `provenance_label`. Assembler never sees `Transcript` / does not compare video ids.
- **D-08:** `provenance_label` is a caller-supplied string. Expected later convention (not built by the assembler): `YouTube · {author}` with no date; when `transcript.language != "ru"`, caller appends a translation marker (e.g. ` · пер. с англ.`).

### Transcript and TemplateKind
- **D-09:** `Transcript` fields: required `text` (strip, `min_length=1`, blank/whitespace-only → validation error), `language` (`min_length=2`, `max_length=10`, open string — not a `ru`/`en` enum), `video_id` (strip, `min_length=1`, blank rejected). No confidence, model id, or duration. Empty captions are a Phase 7 failure, not an empty `Transcript`.
- **D-10:** `TemplateKind` is a closed `Enum`: `LECTURE = "lecture"`, `PODCAST = "podcast"`. Not an open string. Extension is additive (new enum value + template file + test + UAT).

### VideoMetadata and PERS-01 alignment

- **D-11:** `VideoMetadata` fields: required `video_id`, `source_url`, `author`; optional `published_at: datetime | None`. — **Reversibility:** costly — assembler and PERS-01 columns depend on this shape.
- **D-12:** Author source for this milestone: oEmbed via proxy (verified 2026-09-26: AdGuard VPN `192.168.1.68:1080`, oEmbed returns `author_name`). `published_at` is not available from oEmbed; yt-dlp and YouTube Data API are rejected for this milestone (API key / geo-risk). Publish-time enrichment is additive later (e.g. `YtDlpMetadataAdapter` in a later milestone).
- **D-13:** Assembler copies `source_published_at = metadata.published_at` (may be `None`). No invented date. Fail-on-`None` is forbidden — it would break every oEmbed-only run.
- **D-14:** PERS-01 alignment (Phase 9): `source_author` required; `source_published_at` nullable (`timestamptz NULL`). UI shows no date when null. — **Reversibility:** one-way — schema nullability becomes the persist contract once migration lands.

### Ports and fakes
- **D-15:** `TranscriptProvider.get(video_id: str) -> Transcript` — async, neutral verb, accepts `video_id` only (URL parsing is Phase 7). Fake records video ids in `.calls`.
- **D-16:** `ArticleGenerator.process(transcript, template) -> ArticleDraft` — async. Fake records `{transcript, template}` in `.calls`.
- **D-17:** Phase 6 fakes: scripted success + call spy only. No failure catalog. Phases 7/8 add failure scripts additively on the same fakes.

### Claude's Discretion
- Exact module layout under `data-collection` (file names for ports vs dto package) as long as public exports and tests_support placement match D-01…D-04.
- Exact Pydantic / Protocol / Enum scaffolding details within the locked field sets.
- How the type-boundary test proves `Transcript` is not accepted where `MaterialDraft` is required (static typing vs intentional runtime check) — prefer the smallest failing test that locks the contract.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product & requirements
- `.planning/ROADMAP.md` — Phase 6 goal, success criteria, DTO-01/DTO-02
- `.planning/REQUIREMENTS.md` — DTO-01, DTO-02; later CAP/LLM/PERS/CLI (do not implement here). Treat LLM-04 and PERS-01 as updated by decisions in this CONTEXT (always-Russian output deferred to Phase 8; `source_published_at` nullable)
- `.planning/PROJECT.md` — v1.1 ingestion milestone; D-CONTENT-01, D-ARCH-01, DeepSeek MVP bend of ADR-0002
- `CONTEXT.md` — glossary: material = prepared article; provenance language

### Architecture & content rules
- `.cursor/rules/architecture.mdc` — Ports & Adapters; `data-collection` owns external DTOs/ports
- `.cursor/rules/tdd.mdc` / `AGENTS.md` — Red–Green–Refactor
- `docs/adr/0002-cloud-ru-foundrymodels-deployment.md` — FoundryModels long-term; DeepSeek is temporary bend for this milestone
- `backend/src/backend/domain/material.py` — domain `Material` requires `provenance_label`; article fields shape
- `backend/src/backend/application/ports/query_embedder.py` — local `EMBEDDING_DIM = 1024` (do not re-export from data-collection)

### Schema (Phase 9 will migrate; Phase 6 must not invent columns)
- `supabase-integration/migrations/001_initial_schema.sql` — `materials.provenance_label not null`; provenance URL/video/author/published columns not yet present

### Brownfield to remove or evolve
- `data-collection/src/data_collection/__init__.py` — replace exports
- `data-collection/src/data_collection/dto/youtube.py`, `foundry.py`, `text_import.py` — delete per D-03
- `tests/unit/test_youtube_source_dto.py`, `test_foundry_dtos.py`, `test_text_import_dto.py` — delete/replace with new DTO/port tests
- `backend/src/backend/tests_support/in_memory.py` — pattern analog for fakes placement

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Pydantic v2 in `data-collection` — keep for new DTOs
- Backend `Protocol` ports + `tests_support` in-memory fakes — mirror for `TranscriptProvider` / `ArticleGenerator`
- Domain `Material` field names (`title`, `dek`, `body_markdown`, `provenance_label`) — align `MaterialDraft` / `ArticleDraft` naming

### Established Patterns
- Public package barrel via `__init__.py` `__all__`
- Unit tests under `tests/unit/` with TDD; no network/DB in unit layer
- Composition wiring later in `ingestion-service` (not Phase 6)

### Integration Points
- Phase 7 implements `YouTubeTranscriptAdapter.get(video_id)` and URL→`video_id` outside the port
- Phase 8 implements DeepSeek `ArticleGenerator` + lecture/podcast templates
- Phase 9 persists `MaterialDraft` (nullable `source_published_at`) and shortlist enqueue
- Phase 10 one-shot composition + CONSISTENCY-01 before LLM

</code_context>

<specifics>
## Specific Ideas

- Verified 2026-09-26: AdGuard VPN proxy `192.168.1.68:1080`; oEmbed returns `author_name` (e.g. "Rick Astley"); YouTube HTTP/2 200. Author is required because that path works; publish time is optional because oEmbed never provides it.
- Label without date: `YouTube · {author}`.
- Fake spy shape: `FakeTranscriptProvider.calls` = video ids; `FakeArticleGenerator.calls` = `{transcript, template}`.

</specifics>

<deferred>
## Deferred Ideas

- **LLM-04 (updated, Phase 8):** System prompt enforces honesty AND always-Russian output. If transcript language is `ru`: format only, do not translate. If not `ru`: translate to Russian. Preserve technical terms, proper names, library names, numbers, units as-is. Caller appends translation marker to `provenance_label` when `language != "ru"`. Phase 8 tests both `ru` and `en`. UAT (Phase 10): at least one English video among 3–5.
- **CONSISTENCY-01 (Phase 10):** Before `ArticleGenerator.process`, `transcript.video_id == metadata.video_id` or `IngestError(stage="consistency")` — zero LLM calls, zero DB rows. Test with fakes/spy asserting generator not called.
- **YtDlpMetadataAdapter / publish-time enrichment** — later milestone (v1.2+); not yt-dlp or Data API in v1.1.
- Captions adapter, DeepSeek client, persist, CLI — Phases 7–10 as already roadmapped.

</deferred>

---

*Phase: 6-Ports & DTOs*
*Context gathered: 2026-09-26*
