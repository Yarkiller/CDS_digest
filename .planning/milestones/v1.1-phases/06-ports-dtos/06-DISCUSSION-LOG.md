# Phase 6: Ports & DTOs - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-26
**Phase:** 6-Ports & DTOs
**Areas discussed:** Existing DTO overlap, MaterialDraft contents, Transcript shape, In-memory fake behavior, VideoMetadata fields / source / fallback / PERS-01

---

## Existing DTO overlap

| Option | Description | Selected |
|--------|-------------|----------|
| Add beside existing DTOs | Keep YouTube/Foundry DTOs exported; add new types | |
| Replace overlapping types | New types become public API | ✓ |
| You decide | Claude picks | |

**User's choice:** Replace overlapping types.
**Notes:** Also chose remove TextImport/Foundry summary/tagging/embedding/`EMBEDDING_DIM` from public API; delete old modules and tests; fakes in tests_support only.

---

## MaterialDraft contents

| Option | Description | Selected |
|--------|-------------|----------|
| Article plus provenance | Include Phase 9 provenance columns on draft | ✓ |
| Article only | Provenance stays on VideoMetadata until persist | |
| You decide | Claude picks | |

**User's choice:** Article plus provenance; required now; implement assembler in Phase 6 (pattern B: generator returns internal ArticleDraft); provenance_label caller-supplied.
**Notes:** Later revised `source_published_at` to optional (see VideoMetadata).

---

## Transcript shape

| Option | Description | Selected |
|--------|-------------|----------|
| Text and language only | No video_id on Transcript | |
| Text, language, and video id | Transcript names its video | ✓ |
| You decide | Claude picks | |

**User's choice:** text + language + video_id; language open (`min_length=2`, later `max_length=10`); both text and video_id required blank-rejected.
**Notes:** User updated LLM-04 (always Russian) for Phase 8; CONSISTENCY-01 for Phase 10 — assembler does not check ids.

---

## In-memory fake behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Scripted success + call spy | Canned returns + `.calls`; no failure catalog | ✓ |
| Success only, no spy | Call counting later | |
| You decide | Claude picks | |

**User's choice:** Success + spy; `get(video_id)`; `TemplateKind` closed enum lecture/podcast; async ports.
**Notes:** Fakes in `data-collection/tests_support`; not package `__init__`.

---

## VideoMetadata fields / source / fallback / PERS-01

| Option | Description | Selected |
|--------|-------------|----------|
| All four required | Including published_at | |
| Hybrid | video_id, source_url, author required; published_at optional | ✓ |
| Identity required, author/time optional | Weaker author requirement | |

**User's choice:** Hybrid. Author via oEmbed proxy (verified). published_at optional / Pass None through. PERS-01: source_author required, source_published_at nullable. Label convention `YouTube · {author}` without date. yt-dlp/Data API rejected for this milestone.
**Notes:** MaterialDraft.source_published_at revised from required → optional to match.

---

## Claude's Discretion

- Module layout and scaffolding details within locked field/port contracts
- Exact shape of the type-boundary unit test

## Deferred Ideas

- LLM-04 updated (Phase 8) — always-Russian output; translation marker on provenance_label
- CONSISTENCY-01 (Phase 10) — video_id match before LLM
- YtDlpMetadataAdapter / publish-time enrichment (v1.2+)
