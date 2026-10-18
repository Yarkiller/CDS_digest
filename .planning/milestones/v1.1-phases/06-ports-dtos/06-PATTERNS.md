# Phase 6: Ports & DTOs - Pattern Map

**Mapped:** 2026-09-26
**Files analyzed:** 28
**Analogs found:** 27 / 28

## File Classification

| New/Modified/Deleted File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------------|------|-----------|----------------|---------------|
| `data-collection/.../dto/transcript.py` | model (DTO) | transform | `data-collection/.../dto/foundry.py` (`TranscriptResultDto`) | exact |
| `data-collection/.../dto/video_metadata.py` | model (DTO) | transform | `data-collection/.../dto/youtube.py` (`YoutubeSourceDto`) | exact |
| `data-collection/.../dto/material_draft.py` | model (DTO) | transform | `backend/.../domain/material.py` (`Material` field names) + `foundry.py` (`ArticleAssistDto` title/dek/body) | exact |
| `data-collection/.../dto/article_draft.py` | model (DTO, **internal**) | transform | `foundry.py` (`ArticleAssistDto` title/dek/body only) | exact |
| `data-collection/.../dto/template_kind.py` | model (Enum) | — | `backend/.../domain/material.py` (`MaterialStatus`) | exact |
| `data-collection/.../ports/transcript_provider.py` | port (Protocol) | request-response | `backend/.../ports/material_repository.py` / `ping_recorder.py` | exact (async delta) |
| `data-collection/.../ports/article_generator.py` | port (Protocol) | request-response | `backend/.../ports/query_embedder.py` (`QueryEmbedder`) | exact (async delta) |
| `data-collection/.../ports/__init__.py` | config | — | `data-collection/.../dto/__init__.py` | role-match |
| `data-collection/.../assemble.py` | service (pure fn) | transform | `backend/.../use_cases/publish_material.py` (pure orchestration) | role-match |
| `data-collection/.../tests_support/__init__.py` | test utility | — | `backend/.../tests_support/__init__.py` | exact |
| `data-collection/.../tests_support/fakes.py` | test utility | request-response | `backend/.../tests_support/in_memory.py` + `StubMailer` spy style | exact |
| `data-collection/.../__init__.py` | config (public barrel) | — | same file (rewrite `__all__`) | exact (replace) |
| `data-collection/.../dto/__init__.py` | config | — | same file (optional re-exports) | exact (extend) |
| `data-collection/.../dto/youtube.py` | model — **DELETE** | — | replaced by `video_metadata.py` | delete |
| `data-collection/.../dto/foundry.py` | model — **DELETE** | — | replaced by transcript/article/material drafts | delete |
| `data-collection/.../dto/text_import.py` | model — **DELETE** | — | out of Phase 6 public API (D-02) | delete |
| `tests/unit/test_transcript_dto.py` | test | transform | `tests/unit/test_foundry_dtos.py` (blank-text reject) | exact |
| `tests/unit/test_video_metadata_dto.py` | test | transform | `tests/unit/test_youtube_source_dto.py` | exact |
| `tests/unit/test_material_draft_dto.py` | test | transform | `test_foundry_dtos.py` (`ArticleAssistDto`) + Material field asserts | exact |
| `tests/unit/test_template_kind.py` | test | — | Enum unit style (new; mirror `MaterialStatus` usage) | role-match |
| `tests/unit/test_article_draft_internal.py` | test | transform | `test_foundry_dtos.py` article fields | exact |
| `tests/unit/test_assemble_material_draft.py` | test | transform | pure-function unit (publish_material tests pattern) | role-match |
| `tests/unit/test_transcript_provider_fake.py` | test | request-response | in-memory port unit tests / StubMailer last_* spy | exact |
| `tests/unit/test_article_generator_fake.py` | test | request-response | same | exact |
| `tests/unit/test_material_draft_type_boundary.py` | test | transform | **no direct analog** — runtime isinstance guard (RESEARCH Pattern 3) | none |
| `tests/unit/test_youtube_source_dto.py` | test — **DELETE** | — | superseded by `test_video_metadata_dto.py` | delete |
| `tests/unit/test_foundry_dtos.py` | test — **DELETE** | — | superseded by new DTO tests | delete |
| `tests/unit/test_text_import_dto.py` | test — **DELETE** | — | no Phase 6 replacement (D-02) | delete |

**Out of scope (do not touch):** `backend/.../query_embedder.py` (`EMBEDDING_DIM`), `supabase-integration/migrations/*`, network adapters, CLI.

---

## Pattern Assignments

### `data-collection/.../dto/transcript.py` (model, transform)

**Analog:** `data-collection/src/data_collection/dto/foundry.py` — `TranscriptResultDto`

**Strip / blank validator** (lines 11–24):
```python
class TranscriptResultDto(BaseModel):
    source_ref: str = Field(min_length=1)
    text: str = Field(min_length=1)
    language: str = Field(min_length=2)
    confidence: float | None = None
    model_id: str = Field(min_length=1)
    duration_ms: int | None = None

    @field_validator("text")
    @classmethod
    def _non_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("transcript text must not be blank")
        return value
```

**Also strip video_id** from `youtube.py` (lines 32–38):
```python
@field_validator("video_id")
@classmethod
def _strip_video_id(cls, value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("video_id must not be empty")
    return cleaned
```

**Copy for Phase 6:** `Transcript(text, language, video_id)` — drop `source_ref` / `confidence` / `model_id` / `duration_ms` (D-09). Keep Pydantic v2 + `Field(min_length=…)` + strip validators. `language` open string `min_length=2`, `max_length=10` (not `ru`/`en` enum).

---

### `data-collection/.../dto/video_metadata.py` (model, transform)

**Analog:** `data-collection/src/data_collection/dto/youtube.py` — `YoutubeSourceDto`

**Required identity + published datetime** (lines 6–22):
```python
class YoutubeSourceDto(BaseModel):
    video_id: str = Field(min_length=1)
    canonical_url: str = Field(min_length=1)
    title: str = Field(min_length=1)
    channel_id: str = Field(min_length=1)
    channel_title: str = Field(min_length=1)
    published_at: datetime  # REQUIRED today — Phase 6 makes this optional
    # … duration, counts, etag, fetched_at, adapter_version …
```

**Copy for Phase 6:** Slim to D-11: `video_id`, `source_url`, `author` required; `published_at: datetime | None` optional. **Do not** keep required `published_at` — that breaks oEmbed-only runs (D-13). Rename `canonical_url` → `source_url`, `channel_title` → `author`. Drop Data-API-only fields (channel_id, duration, etag, adapter_version).

---

### `data-collection/.../dto/material_draft.py` + `article_draft.py` (model, transform)

**Analog (article fields):** `foundry.py` `ArticleAssistDto` (lines 57–66):
```python
class ArticleAssistDto(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    related_material_ids: list[str] = Field(default_factory=list)
    tags: list[TagItem] = Field(default_factory=list)
    role_hints: list[RoleHint] = Field(default_factory=list)
    model_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    format: Literal["статья"] = "статья"
```

**Analog (provenance + naming):** `backend/src/backend/domain/material.py` (lines 15–25):
```python
@dataclass(frozen=True)
class Material:
    id: int
    slug: str
    title: str
    dek: str
    body_markdown: str
    format: str
    status: MaterialStatus
    reading_minutes: int
    provenance_label: str
    # … roles/tags/related — NOT on MaterialDraft (D-05)
```

**Copy for Phase 6:**
- **Internal** `ArticleDraft`: only `title`, `dek`, `body_markdown` (D-06) — no tags/model_id.
- **Public** `MaterialDraft`: article fields + `source_url`, `youtube_video_id`, `source_author`, `provenance_label`, optional `source_published_at` (D-05). Missing required → `ValidationError`. Do **not** export `ArticleDraft` from package `__all__`.

---

### `data-collection/.../dto/template_kind.py` (model, Enum)

**Analog:** `backend/src/backend/domain/material.py` (lines 10–12):
```python
class MaterialStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
```

**Secondary:** `backend/src/backend/domain/razbor.py` `RazborStatus(str, Enum)`.

**Copy for Phase 6:** `TemplateKind(str, Enum)` with `LECTURE = "lecture"`, `PODCAST = "podcast"` only (D-10). Closed set — not free-form `str`.

---

### `data-collection/.../ports/transcript_provider.py` + `article_generator.py` (port, request-response)

**Analog (Protocol shape):** `backend/src/backend/application/ports/material_repository.py` (lines 1–13):
```python
from __future__ import annotations

from typing import Protocol

from backend.domain.material import Material


class MaterialRepository(Protocol):
    def get(self, material_id: int) -> Material | None: ...

    def get_by_slug(self, slug: str) -> Material | None: ...

    def save(self, material: Material) -> Material: ...
```

**Analog (narrow side-effect Protocol):** `backend/src/backend/application/ports/ping_recorder.py` (lines 1–15):
```python
from __future__ import annotations

from typing import Protocol


class PingRecorder(Protocol):
    def record(
        self,
        *,
        user_id: str | None,
        kind: str,
        payload: dict,
    ) -> str: ...
```

**Analog (port + colocated stub):** `backend/src/backend/application/ports/query_embedder.py` (lines 8–12):
```python
EMBEDDING_DIM = 1024


class QueryEmbedder(Protocol):
    def embed(self, text: str) -> list[float]: ...
```
Note: Phase 6 fakes stay in `tests_support`, **not** next to the Protocol (D-04) — unlike `StubQueryEmbedder` in the same file.

**Copy for Phase 6:**
```python
class TranscriptProvider(Protocol):
    async def get(self, video_id: str) -> Transcript: ...

class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...
```
Async is intentional (D-15/D-16); backend ports are sync — do not “correct” to sync. No SDK imports. `ArticleDraft` return type is package-internal.

---

### `data-collection/.../tests_support/fakes.py` (test utility, request-response)

**Analog (placement):** `backend/src/backend/tests_support/__init__.py` + `in_memory.py` — fakes live under `tests_support`, not package public barrel.

**Package docstring** (`tests_support/__init__.py`):
```python
"""In-memory fakes for unit tests."""
```

**Analog (scripted success + call recording):** `backend/src/backend/infrastructure/stub_mailer.py` (lines 10–33):
```python
class StubMailer:
    def __init__(self) -> None:
        self.last_batch_id: int | None = None
        # … last_* fields …

    def send_digest(self, *, batch_id: int, issue_url: str, ...) -> dict[str, object]:
        self.last_batch_id = batch_id
        # …
```

**Analog (in-memory seed constructor):** `InMemoryMaterialRepository` (`in_memory.py` lines 201–207):
```python
class InMemoryMaterialRepository:
    def __init__(self, materials: list[Material] | None = None) -> None:
        self._by_id: dict[int, Material] = {m.id: m for m in (materials or [])}
```

**Copy for Phase 6 (D-15…D-17):**
- `FakeTranscriptProvider(result: Transcript)` — `async def get` appends `video_id` to `.calls: list[str]`, returns scripted result.
- `FakeArticleGenerator(result: ArticleDraft)` — `.calls` records `{transcript, template}` (or equivalent pairs).
- Scripted success + spy only — **no** failure catalog this phase.
- Never export fakes from `data_collection.__all__`.

---

### `data-collection/.../assemble.py` (service, transform — pure)

**Analog:** `backend/src/backend/application/use_cases/publish_material.py` (lines 10–16) — pure function, ports/entities only, no I/O:
```python
def publish_material(repo: MaterialRepository, material_id: int, *, now: datetime | None = None) -> Material:
    material = repo.get(material_id)
    if material is None:
        raise MaterialNotFoundError(material_id)
    published_at = now or datetime.now(timezone.utc)
    ready = material.as_ready(published_at)
    return repo.save(ready)
```

**Copy for Phase 6:** Pure `assemble_material_draft(article, metadata, provenance_label) -> MaterialDraft` with **no** port/repo args and **no** network/DB. Field map (D-07/D-13):

| MaterialDraft | Source |
|---------------|--------|
| `title`, `dek`, `body_markdown` | `ArticleDraft` |
| `source_url` | `VideoMetadata.source_url` |
| `youtube_video_id` | `VideoMetadata.video_id` |
| `source_author` | `VideoMetadata.author` |
| `source_published_at` | `VideoMetadata.published_at` (may be `None`) |
| `provenance_label` | **caller argument only** |

**Forbidden:** invent label/date; read `Transcript`; compare video ids (CONSISTENCY-01 = Phase 10).

**Optional colocated helper (Roadmap SC-3):** `require_material_draft(value) -> MaterialDraft` with runtime `isinstance` → `TypeError` (RESEARCH Pattern 3; prefer public tiny helper so Phase 9 can reuse).

---

### `data-collection/.../__init__.py` (config — REPLACE public surface)

**Analog:** same file — brownfield barrel to delete (lines 1–23):
```python
"""Public API for data-collection DTOs."""

from data_collection.dto.foundry import (
    EMBEDDING_DIM,
    ArticleAssistDto,
    EmbeddingResultDto,
    SummaryResultDto,
    TaggingResultDto,
    TranscriptResultDto,
)
from data_collection.dto.text_import import TextImportDto
from data_collection.dto.youtube import YoutubeSourceDto

__all__ = [
    "EMBEDDING_DIM",
    "ArticleAssistDto",
    "EmbeddingResultDto",
    "SummaryResultDto",
    "TaggingResultDto",
    "TextImportDto",
    "TranscriptResultDto",
    "YoutubeSourceDto",
]
```

**Copy for Phase 6:** Replace with six public names only (D-01/D-04):
`Transcript`, `VideoMetadata`, `MaterialDraft`, `TemplateKind`, `TranscriptProvider`, `ArticleGenerator`.
Do **not** export `ArticleDraft`, fakes, or `EMBEDDING_DIM` (backend owns `EMBEDDING_DIM` in `query_embedder.py:8`).

---

### Deletes (D-03) — modules + tests

| Delete | Replaced by |
|--------|-------------|
| `dto/youtube.py` | `dto/video_metadata.py` |
| `dto/foundry.py` | `transcript.py` + `article_draft.py` + `material_draft.py` (no Foundry stubs) |
| `dto/text_import.py` | none this milestone |
| `tests/unit/test_youtube_source_dto.py` | `test_video_metadata_dto.py` |
| `tests/unit/test_foundry_dtos.py` | new DTO/port tests |
| `tests/unit/test_text_import_dto.py` | none |

**Safe to delete:** sole production consumers are these unit tests (`[VERIFIED: RESEARCH summary]`). No backend/web imports of old DTOs.

**Test analog to mirror when writing replacements** — blank reject (`test_foundry_dtos.py` lines 31–42):
```python
def test_transcript_result_dto_rejects_empty_text() -> None:
    from data_collection.dto.foundry import TranscriptResultDto

    with pytest.raises(ValidationError):
        TranscriptResultDto(
            source_ref="youtube:dQw4w9WgXcQ",
            text="   ",
            language="ru",
            confidence=0.9,
            model_id="whisper-like",
            duration_ms=1000,
        )
```

And empty `video_id` (`test_youtube_source_dto.py` lines 33–53) — same `pytest.raises(ValidationError)` shape for new DTOs.

---

### Schema gap (reference only — do not migrate)

**Source:** `supabase-integration/migrations/001_initial_schema.sql` (lines 89–104):
```sql
create table if not exists materials (
  -- …
  provenance_label text not null,
  source_id bigint references ingestion_sources (id) on delete set null,
  -- NO source_url / youtube_video_id / source_author / source_published_at yet
);
```

**Copy for Phase 6:** `MaterialDraft` fields are application-boundary shapes only. Phase 9 owns PERS-01 migration. No new files under `supabase-integration/migrations/`.

---

## Data-Flow / Ports & Adapters Notes

Aligned with `.cursor/rules/architecture.mdc`:

```text
[Future Phase 10 CLI / composition]
        |
        |  public types + ports only (no deep-import)
        v
[data-collection PUBLIC API]
  Transcript | VideoMetadata | MaterialDraft | TemplateKind
  TranscriptProvider | ArticleGenerator
        |
        |  NOT public: ArticleDraft, tests_support fakes
        v
[assemble_material_draft]  -- pure; no Transcript; no I/O
        |
        v
MaterialDraft  -->  (Phase 9 persist)

[Phase 7+] YouTubeTranscriptAdapter  --implements--> TranscriptProvider
[Phase 8+] DeepSeekArticleAdapter    --implements--> ArticleGenerator
```

| Rule | Phase 6 implication |
|------|---------------------|
| `data-collection` owns external/ingestion DTOs | All new types + ports live here |
| Ports = `typing.Protocol` | `TranscriptProvider`, `ArticleGenerator` |
| No SDK in domain/use-case | Assembler + DTOs: zero httpx/supabase/fastapi |
| Public barrel only | `__init__.__all__` = 6 names; fakes in `tests_support` |
| Adapters implement later | Phase 6 ships fakes only; real adapters Phases 7–8 |
| Composition root later | `ingestion-service` wiring is Phase 10 — not this phase |
| No `Any` on boundaries | Explicit DTO/Protocol types |

**Anti-patterns to reject in plans:**
- Keeping `YoutubeSourceDto` / Foundry DTOs “additive” (early research superseded by D-01…D-03)
- Exporting fakes or `ArticleDraft` from `__all__`
- Assembler inventing `provenance_label` or failing on `published_at is None`
- Touching `query_embedder.EMBEDDING_DIM` or writing migrations

---

## TDD Notes

Aligned with `.cursor/rules/tdd.mdc` / `AGENTS.md`:

> **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

| Order | Action |
|-------|--------|
| 1 | Write failing unit tests for new DTOs / ports / assembler / type boundary |
| 2 | Run targeted `uv run pytest tests/unit/test_<name>.py -x` — expect ImportError / AssertionError |
| 3 | Minimal production modules to green |
| 4 | Rewrite `__init__.__all__`; delete old DTO modules + old tests in same wave after new surface is green |
| 5 | Full `uv run pytest` before phase gate |

**Suggested RED files first (from RESEARCH Test Map):**
- `test_transcript_dto.py`, `test_video_metadata_dto.py`, `test_material_draft_dto.py`, `test_template_kind.py`
- `test_article_draft_internal.py`, `test_assemble_material_draft.py` (assert `source_published_at is None` path)
- `test_transcript_provider_fake.py`, `test_article_generator_fake.py` — use `asyncio.run(...)` inside sync pytest (prefer no new `pytest-asyncio` dep)
- `test_material_draft_type_boundary.py` — `pytest.raises(TypeError)` when `Transcript` passed to `require_material_draft`
- Assert `__all__` excludes fakes / `ArticleDraft` / old names

**Exceptions that do not apply:** this phase is not config-only or a one-off prototype — full TDD applies. Deletes of obsolete modules happen after new failing→green tests exist (Wave 0), not as untested cleanup.

**Unit layer constraints:** no network, no DB, no migrations, no Playwright required for Phase 6 gate.

---

## Cross-Cutting Patterns

### Validation (Pydantic v2)
**Source:** `dto/youtube.py`, `dto/foundry.py`, `dto/text_import.py`
**Apply to:** All new DTOs — `Field(min_length=…)`, `@field_validator` strip + reject whitespace-only.

### Public API barrel
**Source:** `data_collection/__init__.py`
**Apply to:** Rewrite `__all__` to six names; deep-import `ArticleDraft` only inside package/tests.

### Protocol + tests_support fake
**Source:** `backend/application/ports/*` + `backend/tests_support/in_memory.py`
**Apply to:** Async Protocols in `data-collection/ports/`; fakes with `.calls` spies in `data-collection/tests_support/`.

### Pure transform (assembler)
**Source:** `publish_material.py` style (no FastAPI/SDK)
**Apply to:** `assemble_material_draft` — field mapping only; caller-supplied `provenance_label`.

### Type boundary (Roadmap SC-3)
**Source:** RESEARCH Pattern 3 (no mypy/pyright in repo)
**Apply to:** Runtime `isinstance(MaterialDraft)` guard + one unit test — smallest CI-enforced lock.

### EMBEDDING_DIM ownership
**Source:** `backend/.../query_embedder.py:8`
**Apply to:** Delete data-collection export only; leave backend constant and `vector(1024)` alone.

---

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| `tests/unit/test_material_draft_type_boundary.py` + `require_material_draft` | test / tiny helper | transform | No existing runtime type-boundary consumer in repo; invent smallest isinstance guard per RESEARCH Pattern 3 |

---

## Metadata

**Analog search scope:** `data-collection/src/data_collection/{dto,__init__}`, `backend/src/backend/{domain,application/ports,tests_support,infrastructure,application/use_cases}`, `tests/unit/test_*_dto.py`, `supabase-integration/migrations/001_initial_schema.sql`
**Files scanned:** ~28 primary + prior `05-PATTERNS.md` format
**Pattern extraction date:** 2026-09-26
**Discretion noted:** Exact `dto/` vs `ports/` filenames remain Claude's Discretion (CONTEXT). OQ1–OQ3 are RESOLVED locks (06-01 assumptions / RESEARCH recommendations adopted): (OQ1) `require_material_draft` public tiny helper in `assemble.py`; (OQ2) `asyncio.run(...)` in sync pytest — no `pytest-asyncio`; (OQ3) strip/non-blank on MaterialDraft required strings (same spirit for ArticleDraft article fields).

## PATTERN MAPPING COMPLETE
