# Phase 6: Ports & DTOs - Research

**Researched:** 2026-09-26
**Domain:** `data-collection` typed ingestion contracts — Transcript vs prepared-article MaterialDraft boundary, Protocol ports + in-memory fakes, assembler (ArticleDraft + VideoMetadata + provenance_label → MaterialDraft)
**Confidence:** HIGH (CONTEXT D-01…D-17 + REQUIREMENTS DTO-01/DTO-02 + brownfield DTO/test inventory + schema provenance gap); MEDIUM (exact `dto/` / `ports/` file names are Claude's Discretion); LOW (none blocking — no new packages, no network/DB)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Existing DTO overlap
- **D-01:** Replace overlapping brownfield DTOs. Public API is `Transcript`, `VideoMetadata`, `MaterialDraft`, `TemplateKind`, plus ports `TranscriptProvider` and `ArticleGenerator`. Do not keep `YoutubeSourceDto`, `TranscriptResultDto`, or `ArticleAssistDto` as parallel types. — **Reversibility:** costly — consumers and unit tests must move to the new names; reintroducing the old surface is a second public contract.
- **D-02:** Remove the rest of the old public surface too: `TextImportDto`, `SummaryResultDto`, `TaggingResultDto`, `EmbeddingResultDto`, and package-exported `EMBEDDING_DIM`. Phase 6 public API is only the new ingestion types and ports. Backend keeps its own `EMBEDDING_DIM = 1024` in `query_embedder.py`; schema `vector(1024)` is unchanged. — **Reversibility:** costly — Foundry-shaped stubs return only when a later milestone reintroduces them.
- **D-03:** Delete old modules and their tests: `dto/youtube.py`, `dto/foundry.py`, `dto/text_import.py`, and unit tests that import them (`test_youtube_source_dto.py`, `test_foundry_dtos.py`, `test_text_import_dto.py`).
- **D-04:** Fakes live in `data-collection/tests_support` only. Public package `__init__` exports types and ports, not fakes. Matches backend `tests_support` pattern.

#### MaterialDraft and assembler
- **D-05:** `MaterialDraft` fields: required `title`, `dek`, `body_markdown`, `source_url`, `youtube_video_id`, `source_author`, `provenance_label`; optional `source_published_at: datetime | None`. Tags, role hints, and model ids stay off this type. Missing any required field is a validation error. — **Reversibility:** costly — persist (PERS-01) and assembler copy these names; revising them rewrites Phase 9 contracts.
- **D-06:** `ArticleGenerator` returns an internal `ArticleDraft` (`title`, `dek`, `body_markdown` only). `ArticleDraft` is not part of the public package API. The adapter stays LLM-only and does not learn YouTube field names. — **Reversibility:** costly — swapping to “generator builds MaterialDraft” would push provenance into the adapter.
- **D-07:** Phase 6 implements a tested assembler: `ArticleDraft` + `VideoMetadata` + explicit `provenance_label` → `MaterialDraft`. No network, no database. Assembler does not invent `provenance_label`. Assembler never sees `Transcript` / does not compare video ids.
- **D-08:** `provenance_label` is a caller-supplied string. Expected later convention (not built by the assembler): `YouTube · {author}` with no date; when `transcript.language != "ru"`, caller appends a translation marker (e.g. ` · пер. с англ.`).

#### transcript and TemplateKind
- **D-09:** `Transcript` fields: required `text` (strip, `min_length=1`, blank/whitespace-only → validation error), `language` (`min_length=2`, `max_length=10`, open string — not a `ru`/`en` enum), `video_id` (strip, `min_length=1`, blank rejected). No confidence, model id, or duration. Empty captions are a Phase 7 failure, not an empty `Transcript`.
- **D-10:** `TemplateKind` is a closed `Enum`: `LECTURE = "lecture"`, `PODCAST = "podcast"`. Not an open string. Extension is additive (new enum value + template file + test + UAT).

#### VideoMetadata and PERS-01 alignment
- **D-11:** `VideoMetadata` fields: required `video_id`, `source_url`, `author`; optional `published_at: datetime | None`. — **Reversibility:** costly — assembler and PERS-01 columns depend on this shape.
- **D-12:** Author source for this milestone: oEmbed via proxy (verified 2026-09-26: AdGuard VPN `192.168.1.68:1080`, oEmbed returns `author_name`). `published_at` is not available from oEmbed; yt-dlp and YouTube Data API are rejected for this milestone (API key / geo-risk). Publish-time enrichment is additive later (e.g. `YtDlpMetadataAdapter` in a later milestone).
- **D-13:** Assembler copies `source_published_at = metadata.published_at` (may be `None`). No invented date. Fail-on-`None` is forbidden — it would break every oEmbed-only run.
- **D-14:** PERS-01 alignment (Phase 9): `source_author` required; `source_published_at` nullable (`timestamptz NULL`). UI shows no date when null. — **Reversibility:** one-way — schema nullability becomes the persist contract once migration lands.

#### Ports and fakes
- **D-15:** `TranscriptProvider.get(video_id: str) -> Transcript` — async, neutral verb, accepts `video_id` only (URL parsing is Phase 7). Fake records video ids in `.calls`.
- **D-16:** `ArticleGenerator.process(transcript, template) -> ArticleDraft` — async. Fake records `{transcript, template}` in `.calls`.
- **D-17:** Phase 6 fakes: scripted success + call spy only. No failure catalog. Phases 7/8 add failure scripts additively on the same fakes.

### Claude's Discretion
- Exact module layout under `data-collection` (file names for ports vs dto package) as long as public exports and tests_support placement match D-01…D-04.
- Exact Pydantic / Protocol / Enum scaffolding details within the locked field sets.
- How the type-boundary test proves `Transcript` is not accepted where `MaterialDraft` is required (static typing vs intentional runtime check) — prefer the smallest failing test that locks the contract.

### Deferred Ideas (OUT OF SCOPE)
- **LLM-04 (updated, Phase 8):** System prompt enforces honesty AND always-Russian output. If transcript language is `ru`: format only, do not translate. If not `ru`: translate to Russian. Preserve technical terms, proper names, library names, numbers, units as-is. Caller appends translation marker to `provenance_label` when `language != "ru"`. Phase 8 tests both `ru` and `en`. UAT (Phase 10): at least one English video among 3–5.
- **CONSISTENCY-01 (Phase 10):** Before `ArticleGenerator.process`, `transcript.video_id == metadata.video_id` or `IngestError(stage="consistency")` — zero LLM calls, zero DB rows. Test with fakes/spy asserting generator not called.
- **YtDlpMetadataAdapter / publish-time enrichment** — later milestone (v1.2+); not yt-dlp or Data API in v1.1.
- Captions adapter, DeepSeek client, persist, CLI — Phases 7–10 as already roadmapped.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DTO-01 | Types `Transcript`, `VideoMetadata`, `MaterialDraft`, and `TemplateKind` live in `data-collection` and are covered by unit tests | New Pydantic models + `TemplateKind` Enum; delete old DTOs/tests; public `__all__` only new surface |
| DTO-02 | Ports `TranscriptProvider` and `ArticleGenerator` have in-memory fakes usable by unit tests | Async `typing.Protocol` + fakes in `tests_support` with `.calls` spies (D-15…D-17) |
| *(CONTEXT beyond REQ IDs)* | Assembler `ArticleDraft` + `VideoMetadata` + `provenance_label` → `MaterialDraft` | D-06/D-07/D-13 — **in Phase 6 planning scope** even though not a separate REQ id |
| *(Roadmap SC-3)* | `Transcript` cannot be passed where `MaterialDraft` is required | Smallest runtime `isinstance` guard + pytest (no mypy/pyright in repo) |
</phase_requirements>

## Summary

Phase 6 is a **contracts-only** cut of `data-collection`: replace the brownfield Foundry/YouTube/text-import DTO public surface with four ingestion types + two async Protocol ports, ship in-memory fakes under `tests_support` (not the package barrel), and add a **pure** assembler that stitches internal `ArticleDraft` with `VideoMetadata` and a **caller-supplied** `provenance_label` into `MaterialDraft`. No network, no DB, no migrations, no CLI.

**Critical planner override vs early milestone research:** `.planning/research/ARCHITECTURE.md` / `STACK.md` / `FEATURES.md` said “keep `YoutubeSourceDto` / Foundry DTOs and add additive types.” That advice is **SUPERSEDED** by CONTEXT **D-01…D-03** — delete old modules and their three unit tests. Safe to delete: only those unit tests import the old DTOs; no production code outside `data-collection` itself consumes them `[VERIFIED: tests/unit/test_youtube_source_dto.py, test_foundry_dtos.py, test_text_import_dto.py` are sole importers; notebooks have zero `data_collection` matches]`.

**Primary recommendation:** Mirror backend Ports & Adapters shape inside `data-collection` (`dto/` + `ports/` + `assemble_material_draft` + `tests_support/`), keep Pydantic v2 only (already pinned at `2.13.5`), prove type boundary with a tiny runtime consumer + `TypeError` test (smallest lock without adding a typechecker), and treat assembler + public-API barrel rewrite as first-class plan work alongside DTO-01/DTO-02.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ingestion DTO definitions | `data-collection` | — | Module owns external/ingestion contracts (`architecture.mdc`) |
| Protocol ports (`TranscriptProvider`, `ArticleGenerator`) | `data-collection` | Future adapters (Phases 7–8) | Ports live with DTOs; adapters implement later |
| In-memory fakes + spies | `data-collection/tests_support` | Unit tests | D-04 — never public `__init__` |
| Assembler (ArticleDraft → MaterialDraft) | `data-collection` | Phase 10 composition | Pure function; no I/O; D-07 |
| Domain `Material` / HTTP readers | Backend | SPA | Unchanged this phase — readers stay on existing schema |
| Provenance columns migration | Out of scope | Phase 9 | Schema lacks URL/author/published columns today |
| Captions / LLM / CLI | Out of scope | Phases 7–10 | CONTEXT deferred |

## Project Constraints (from .cursor/rules/)

| Directive | Implication for Phase 6 |
|-----------|-------------------------|
| Ports & Adapters (`architecture.mdc`) | DTOs + Protocols in `data-collection`; no Supabase/httpx/fastapi in types or assembler |
| No deep-imports across modules | Public barrel `__init__.py` / `__all__` only; later `ingestion-service` imports public names |
| TDD Red–Green–Refactor (`tdd.mdc` / `AGENTS.md`) | Failing unit tests first for each type/port/assembler/boundary; then minimal code |
| No `Any` on ports/boundaries | Explicit types on Protocol methods and DTOs |
| Unit tests without network/DB | Fakes only; no live YouTube/DeepSeek/Supabase |
| D-CONTENT-01 / glossary | Material = prepared article; `Transcript` is исходный текст — never treat as material content |
| ADR-0002 | FoundryModels long-term; DeepSeek is later-phase bend — Phase 6 does not call either |
| No new packages | `pydantic>=2.10` already in `data-collection/pyproject.toml` |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | `2.13.5` (resolved) / `>=2.10` `[VERIFIED: uv run import; data-collection/pyproject.toml:6-8]` | DTO validation, Field/validators, Enum | Already the data-collection DTO standard |
| Python typing `Protocol` | stdlib `[CITED: Context7 /python/cpython typing.Protocol]` | Port interfaces | Matches backend `application/ports/*` pattern `[VERIFIED: material_repository.py:7-13]` |
| `enum.Enum` / `str, Enum` | stdlib | `TemplateKind` closed set | D-10 |
| pytest | `9.1.1` (resolved) / workspace `>=8.3` `[VERIFIED: uv run import; pyproject.toml]` | Unit tests for DTOs/ports/assembler/boundary | Existing `tests/unit/` |
| uv workspace | existing | `data-collection` member | `[VERIFIED: root pyproject.toml members include data-collection]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `datetime` / `timezone` | stdlib | Optional `published_at` / `source_published_at` | Assembler copy of `None` must stay legal (D-13) |
| `asyncio.run` | stdlib | Drive async fake methods from sync pytest | No `pytest-asyncio` in workspace `[VERIFIED: no matches in *.py/*.toml]` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic BaseModel | `@dataclass` + manual validate | Loses Field/`ValidationError` consistency with brownfield validators; reject |
| Keep old DTOs + add new (early research) | Delete per D-01…D-03 | Coexistence creates dual public contracts — **forbidden** |
| Sync Protocol methods | Async `get` / `process` | Locked by D-15/D-16 (I/O adapters will be async) |
| Export fakes from package `__init__` | `tests_support` only | Violates D-04 / backend analog |
| mypy/pyright CI gate for boundary | Runtime `isinstance` guard test | No typechecker configured `[VERIFIED: no mypy/pyright in pyproject.toml]` — runtime is smallest locking test |
| `StringConstraints(strip_whitespace=True)` | Brownfield `@field_validator` strip | Context7 confirms strip-before-min_length `[CITED: Context7 /pydantic/pydantic]`; prefer matching existing youtube/foundry validators for consistency |
| Assembler invents provenance_label | Caller-supplied | Violates D-07/D-08 |

**Installation:** none — **do not add new PyPI packages**.

**Version verification:** Pydantic `2.13.5` and pytest `9.1.1` confirmed via `uv run python -c "import …"` (2026-09-26 session).

## Package Legitimacy Audit

> Phase 6 installs **no new** external packages. Existing `pydantic>=2.10` remains. Legitimacy gate on a fresh `pydantic` install returned `[SUS]` (too-new / unknown-downloads) — **ignore for this phase** because no install occurs and the package is already a workspace dependency with official GitHub + Context7 docs.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| _(none new)_ | — | — | — | — | — | N/A |

**Packages removed due to [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none (for Phase 6 install list)

## Architecture Patterns

### System Architecture Diagram

```text
[Future Phase 10 CLI / composition]
        |
        |  uses public types + ports only
        v
[data-collection PUBLIC API]
  Transcript | VideoMetadata | MaterialDraft | TemplateKind
  TranscriptProvider (Protocol) | ArticleGenerator (Protocol)
        |
        |  NOT public: ArticleDraft, tests_support fakes
        v
[assemble_material_draft(article, metadata, provenance_label)]
  -> MaterialDraft  (pure; no Transcript; no network/DB)

[require_material_draft(value)]  --optional tiny helper--
  -> TypeError if not MaterialDraft   (Roadmap SC-3)

[Phase 7+] YouTubeTranscriptAdapter  --implements--> TranscriptProvider
[Phase 8+] DeepSeekArticleAdapter    --implements--> ArticleGenerator
[Phase 9+] Persist MaterialDraft columns (migration then)

[DELETE in Phase 6]
  dto/youtube.py, foundry.py, text_import.py
  test_youtube_source_dto.py, test_foundry_dtos.py, test_text_import_dto.py
```

### Recommended Project Structure (discretion — recommended layout)

```text
data-collection/
  src/data_collection/
    __init__.py                 # PUBLIC barrel: types + ports only (D-01/D-04)
    dto/
      __init__.py               # optional internal re-exports
      transcript.py             # Transcript
      video_metadata.py         # VideoMetadata
      material_draft.py         # MaterialDraft
      article_draft.py          # ArticleDraft — INTERNAL (not in package __all__)
      template_kind.py          # TemplateKind Enum
    ports/
      __init__.py
      transcript_provider.py    # Protocol TranscriptProvider
      article_generator.py      # Protocol ArticleGenerator
    assemble.py                 # assemble_material_draft + require_material_draft
    tests_support/
      __init__.py
      fakes.py                  # FakeTranscriptProvider, FakeArticleGenerator
  pyproject.toml                # pydantic only — unchanged deps

tests/unit/
  test_transcript_dto.py
  test_video_metadata_dto.py
  test_material_draft_dto.py
  test_template_kind.py
  test_article_draft_internal.py
  test_assemble_material_draft.py
  test_transcript_provider_fake.py
  test_article_generator_fake.py
  test_material_draft_type_boundary.py
  test_data_collection_public_api.py   # __all__ + not-exported asserts
```

**Why this layout:** Mirrors backend `application/ports` + model split; keeps `ArticleDraft` importable by assembler/ports without advertising it on the public barrel; fakes colocated under `tests_support` like `[VERIFIED: backend/src/backend/tests_support/in_memory.py exists]`.

### Pattern 1: Pydantic v2 strip / blank validators (mirror brownfield)

**What:** Required strings use `Field(min_length=1)` plus `@field_validator` that strips and rejects whitespace-only — same pattern as existing YouTube `video_id` and Foundry `text` validators.  
**When to use:** `Transcript.text`, `Transcript.video_id`, and other required non-blank strings on `VideoMetadata` / `MaterialDraft` / `ArticleDraft` as locked by D-05/D-09/D-11.  
**Source patterns:** `[VERIFIED: data-collection/src/data_collection/dto/youtube.py:32-38]` quote: `cleaned = value.strip()` / `raise ValueError("video_id must not be empty")`. `[VERIFIED: data-collection/src/data_collection/dto/foundry.py:19-24]` quote: `if not value.strip(): raise ValueError("transcript text must not be blank")`.  
**Docs:** Context7 confirms whitespace strip-before-min_length for `StringConstraints` `[CITED: Context7 /pydantic/pydantic]` — discretionary alternative; prefer brownfield `field_validator` for consistency.

### Pattern 2: Async Protocol + scripted fake spy

**What:** Ports are `typing.Protocol` with `async def`; fakes return a constructor-injected success value and append call args to `.calls`.  
**When to use:** DTO-02 / D-15…D-17.  
**Docs:** Protocol is structural; fakes need matching methods `[CITED: Context7 /python/cpython typing.Protocol]`. Do **not** require `@runtime_checkable` for injection — backend ports omit it `[VERIFIED: material_repository.py:7-13]`.  
**Note:** Backend ports today are sync. Async here is intentional for future I/O adapters. Prefer `asyncio.run(...)` inside sync pytest tests — no `pytest-asyncio` package and no existing `asyncio.run` usage in repo yet `[VERIFIED: session grep]`.

### Pattern 3: Type-boundary lock (smallest recommended)

**What:** A tiny consumer that **runtime-requires** `MaterialDraft`:

```python
def require_material_draft(value: MaterialDraft) -> MaterialDraft:
    if not isinstance(value, MaterialDraft):
        raise TypeError("MaterialDraft required")
    return value
```

Unit test constructs a valid `Transcript` and asserts `pytest.raises(TypeError)` when passed (with `# type: ignore[arg-type]` if editors complain).  
**Why not mypy-only:** No mypy/pyright config in workspace — a static-only “test” would not run in CI.  
**Why not structural duck typing:** `Transcript` and `MaterialDraft` share no required field set; isinstance is the honest runtime boundary for Pydantic models.  
**When to use:** Roadmap success criterion 3. **Recommend** placing helper next to assembler so Phase 9 persist can reuse it (still zero I/O).

### Pattern 4: Assembler as pure mapping

**What:** Single function copies article fields + maps metadata → provenance fields + takes `provenance_label: str` as argument.  
**Field map (locked):**

| MaterialDraft field | Source |
|---------------------|--------|
| `title`, `dek`, `body_markdown` | `ArticleDraft` |
| `source_url` | `VideoMetadata.source_url` |
| `youtube_video_id` | `VideoMetadata.video_id` |
| `source_author` | `VideoMetadata.author` |
| `source_published_at` | `VideoMetadata.published_at` (may be `None`) |
| `provenance_label` | **caller argument only** |

**Forbidden in assembler:** reading `Transcript`, inventing label/date, comparing video ids, network/DB.

### Anti-Patterns to Avoid

- **Keeping `YoutubeSourceDto` / Foundry DTOs “for later”:** Violates D-01…D-03; early `.planning/research/*.md` is superseded.
- **Re-exporting `EMBEDDING_DIM` from data-collection:** Backend already owns it `[VERIFIED: query_embedder.py:8]` quote: `EMBEDDING_DIM = 1024`; D-02 removes package export.
- **Putting fakes in `__init__.__all__`:** Violates D-04.
- **Making `ArticleDraft` public:** Violates D-06.
- **Assembler builds `provenance_label`:** Violates D-07/D-08.
- **`source_published_at` required / fail-on-None:** Violates D-13/D-14.
- **Migrations for provenance URL columns in Phase 6:** Columns absent today `[VERIFIED: 001_initial_schema.sql:89-104]` — Phase 9 only.
- **Empty `Transcript` for missing captions:** Phase 7 failure; D-09 forbids empty text.
- **Open string `TemplateKind`:** Must be Enum (D-10).
- **Confusing REQUIREMENTS LLM-01 wording:** LLM-01 says DeepSeek returns `MaterialDraft`; Phase 6/CONTEXT path is `ArticleDraft` + assembler → `MaterialDraft`. Phase 8 composition owns that story — do not collapse generator into MaterialDraft in Phase 6.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DTO validation | Ad-hoc if/raise dicts | Pydantic v2 `BaseModel` + Field/validators | Already standard; ValidationError tests exist |
| Port interfaces | ABC hierarchy + metaclass | `typing.Protocol` | Backend convention; structural typing for fakes |
| Closed template set | Free-form `str` | `TemplateKind(str, Enum)` | D-10; CLI `--template` later maps to enum |
| Test doubles | pytest-mock / MagicMock as default | Explicit `Fake*` with `.calls` | D-17; readable spy asserts |
| Type boundary | Add mypy CI just for this phase | Runtime `isinstance` + one unit test | Smallest lock; no new toolchain |
| Async test harness | New `pytest-asyncio` dep | `asyncio.run` in sync tests | Zero new packages |
| Provenance columns | Invent SQL in Phase 6 | Defer migration to Phase 9 | Schema gap is known and intentional |

**Key insight:** Phase 6 success is a **clean public contract** and a **pure assembler**, not adapter I/O. Deleting the old surface is part of the deliverable, not cleanup debt.

## Runtime State Inventory

> Delete/replace of public DTO names — treat as rename/refactor for residual-state audit.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — DTOs are code types only; no DB tables/collections named after old DTO classes. Schema has `materials.provenance_label` only among provenance fields `[VERIFIED: 001_initial_schema.sql:89-104]` | None for Phase 6 (Phase 9 adds columns) |
| Live service config | None — no n8n/Datadog/tunnel names tied to `YoutubeSourceDto` / Foundry DTO identifiers | None — verified by absence of those names outside code/docs |
| OS-registered state | None — no scheduled tasks / services keyed to old DTO names | None |
| Secrets/env vars | None — old DTOs carry no secret key names; Phase 6 introduces no env vars | None |
| Build artifacts | Possible stale `data-collection` egg-info / `.pyc` after module delete | Code edit + normal `uv run pytest`; reinstall only if import cache confuses local env |

**Nothing found in category** responses above are explicit (researched this session).

## Common Pitfalls

### Pitfall 1: Following early research that said “keep YoutubeSourceDto”
**What goes wrong:** Dual public APIs; planners schedule coexistence; DTO-01 never truly replaces brownfield.  
**Why it happens:** `[VERIFIED: .planning/research/ARCHITECTURE.md` additive keep advice] / `STACK.md` / `FEATURES.md`.  
**How to avoid:** Treat CONTEXT D-01…D-03 as law; delete modules + three unit tests in the same wave that introduces new types.  
**Warning signs:** `__all__` still lists `YoutubeSourceDto` or `ArticleAssistDto`.

### Pitfall 2: Inventing DB columns or writing migrations
**What goes wrong:** Phase 6 grows schema scope; conflicts with Phase 9 PERS-01 plan.  
**Why it happens:** `MaterialDraft` fields look like columns; `materials` today only has `provenance_label` among provenance fields `[VERIFIED: 001_initial_schema.sql:98]` quote: `provenance_label text not null`.  
**How to avoid:** DTOs are application-boundary shapes only; document Phase 9 migration as consumer.  
**Warning signs:** New files under `supabase-integration/migrations/` in a Phase 6 plan.

### Pitfall 3: Assembler rejects `published_at is None`
**What goes wrong:** Every oEmbed-only metadata path fails before Phase 7/8 exist.  
**Why it happens:** Habit of “required datetime” from old `YoutubeSourceDto.published_at` (required) `[VERIFIED: youtube.py:15]` quote: `published_at: datetime`.  
**How to avoid:** D-13 — copy `None` through; unit test explicitly asserts `source_published_at is None`.  
**Warning signs:** ValidationError on assemble when metadata omits publish time.

### Pitfall 4: Exporting `ArticleDraft` or fakes from public `__init__`
**What goes wrong:** CLI/persist start depending on LLM-internal shape; fakes become production imports.  
**Why it happens:** Convenience barrel dumping.  
**How to avoid:** `__all__` whitelist = six public names (4 types + 2 ports). Import `ArticleDraft` from `data_collection.dto.article_draft` only inside package / tests.  
**Warning signs:** `from data_collection import ArticleDraft` or `FakeTranscriptProvider` works.

### Pitfall 5: Mixing Transcript into MaterialDraft consumers without a test
**What goes wrong:** Roadmap SC-3 unmet; later persist accidentally accepts transcript-shaped dicts.  
**Why it happens:** Separate models alone do not prove rejection without a consumer guard.  
**How to avoid:** Ship `require_material_draft` (or equivalent) + RED then GREEN boundary test.  
**Warning signs:** Only “models exist” tests; no TypeError path.

### Pitfall 6: Removing backend `EMBEDDING_DIM` while cleaning data-collection
**What goes wrong:** Knowledge search / StubQueryEmbedder breaks.  
**Why it happens:** Same constant name in two packages `[VERIFIED: foundry.py:6]` quote: `EMBEDDING_DIM = 1024`; `[VERIFIED: query_embedder.py:8]` quote: `EMBEDDING_DIM = 1024`.  
**How to avoid:** Delete **only** data-collection export; leave backend constant and `vector(1024)` alone (D-02).  
**Warning signs:** Diffs under `query_embedder.py` in Phase 6 plans.

### Pitfall 7: Language as `Literal["ru","en"]` enum
**What goes wrong:** Non-ru/en captions fail validation before Phase 7 preference logic.  
**Why it happens:** CAP-01 ru/en preference misread as DTO enum.  
**How to avoid:** D-09 open string length 2–10; preference is adapter policy in Phase 7.  
**Warning signs:** Enum named `TranscriptLanguage`.

## Code Examples

### Brownfield public surface to delete (verbatim exports)

```python
# Source: [VERIFIED: data-collection/src/data_collection/__init__.py:14-23]
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

### Recommended public barrel (target)

```python
# [ASSUMED file layout — names match D-01; planner may split modules]
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.article_generator import ArticleGenerator

__all__ = [
    "Transcript",
    "VideoMetadata",
    "MaterialDraft",
    "TemplateKind",
    "TranscriptProvider",
    "ArticleGenerator",
]
```

### Transcript validators (discretionary scaffolding within D-09)

```python
# Adapted from [VERIFIED: dto/foundry.py:19-24 + dto/youtube.py:32-38]
# Docs: [CITED: Context7 /pydantic/pydantic field_validator / StringConstraints]
from pydantic import BaseModel, Field, field_validator

class Transcript(BaseModel):
    text: str = Field(min_length=1)
    language: str = Field(min_length=2, max_length=10)
    video_id: str = Field(min_length=1)

    @field_validator("text", "video_id")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("language")
    @classmethod
    def _strip_language(cls, value: str) -> str:
        cleaned = value.strip()
        if not (2 <= len(cleaned) <= 10):
            raise ValueError("language length must be 2–10")
        return cleaned
```

### TemplateKind (D-10)

```python
from enum import Enum

class TemplateKind(str, Enum):
    LECTURE = "lecture"
    PODCAST = "podcast"
```

### Ports + fakes (D-15…D-17)

```python
# Protocol pattern: [CITED: Context7 /python/cpython typing.Protocol]
# Analog: [VERIFIED: backend/.../ports/material_repository.py:7-13]
from typing import Protocol
from data_collection.dto.transcript import Transcript
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.article_draft import ArticleDraft  # internal

class TranscriptProvider(Protocol):
    async def get(self, video_id: str) -> Transcript: ...

class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...


class FakeTranscriptProvider:
    def __init__(self, result: Transcript) -> None:
        self._result = result
        self.calls: list[str] = []

    async def get(self, video_id: str) -> Transcript:
        self.calls.append(video_id)
        return self._result


class FakeArticleGenerator:
    def __init__(self, result: ArticleDraft) -> None:
        self._result = result
        self.calls: list[dict] = []

    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft:
        self.calls.append({"transcript": transcript, "template": template})
        return self._result
```

### Async fake test without pytest-asyncio

```python
import asyncio
import pytest

def test_fake_transcript_provider_records_calls() -> None:
    # FakeTranscriptProvider constructed with a valid Transcript
    fake = FakeTranscriptProvider(result=...)
    out = asyncio.run(fake.get("dQw4w9WgXcQ"))
    assert out is fake._result
    assert fake.calls == ["dQw4w9WgXcQ"]
```

### Assembler (D-07 / D-13)

```python
# [ASSUMED function name — planner may rename]
from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.dto.material_draft import MaterialDraft

def assemble_material_draft(
    article: ArticleDraft,
    metadata: VideoMetadata,
    provenance_label: str,
) -> MaterialDraft:
    return MaterialDraft(
        title=article.title,
        dek=article.dek,
        body_markdown=article.body_markdown,
        source_url=metadata.source_url,
        youtube_video_id=metadata.video_id,
        source_author=metadata.author,
        provenance_label=provenance_label,  # caller-supplied; never invent
        source_published_at=metadata.published_at,  # may be None
    )
```

### Type-boundary test sketch (Roadmap SC-3)

```python
import pytest
from data_collection import Transcript, MaterialDraft
# require_material_draft: package helper next to assembler — Pattern 3

def test_transcript_rejected_where_material_draft_required() -> None:
    transcript = Transcript(text="hello", language="en", video_id="abc")
    with pytest.raises(TypeError):
        require_material_draft(transcript)  # type: ignore[arg-type]
```

### Domain Material alignment (names only — not the same type)

```python
# Source: [VERIFIED: backend/src/backend/domain/material.py:16-25]
# Quote: title, dek, body_markdown, provenance_label on Material
# MaterialDraft aligns article field names + provenance_label;
# domain Material also has id/slug/status/roles/tags — NOT on MaterialDraft (D-05).
```

### Schema gap (do not migrate in Phase 6)

```sql
-- Source: [VERIFIED: supabase-integration/migrations/001_initial_schema.sql:89-104]
-- Quote: provenance_label text not null
-- materials has provenance_label NOT NULL
-- NO source_url, youtube_video_id, source_author, source_published_at columns yet
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Foundry-shaped public DTOs + YoutubeSourceDto | Ingestion-only public API (D-01…D-03) | Phase 6 CONTEXT 2026-09-26 | Delete brownfield DTO modules/tests |
| Additive “keep old DTOs” research advice | **Superseded** by CONTEXT | 2026-09-26 | Planner must not schedule coexistence |
| ArticleAssistDto includes tags/model_id | `ArticleDraft` = title/dek/body only; `MaterialDraft` adds provenance | Phase 6 | LLM adapter stays YouTube-agnostic (D-06) |
| Required `published_at` on YoutubeSourceDto | Optional `published_at` / nullable `source_published_at` | Phase 6 (D-11…D-14) | oEmbed-only path viable |
| Sync backend ports only | Async ingestion ports | Phase 6 (D-15/D-16) | Matches future HTTP LLM/captions I/O |
| EMBEDDING_DIM exported from data-collection | Backend-only constant | Phase 6 (D-02) | Safe delete of package export |

**Deprecated/outdated:**
- `.planning/research/ARCHITECTURE.md` “Prefer additive DTOs; keep YoutubeSourceDto…” — superseded by D-01…D-03.
- `.planning/research/STACK.md` “Coexist / keep TranscriptResultDto…” — superseded.
- Treating `ArticleAssistDto` as the Phase 8 return type — use internal `ArticleDraft` + assembler → `MaterialDraft`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Layout `dto/` + `ports/` + `assemble.py` + `tests_support/` is optimal | Discretion | Rename-only churn if planner prefers flat modules |
| A2 | Type-boundary via runtime `isinstance` + `TypeError` is the smallest CI-enforced lock | Pattern 3 | If team adds pyright later, may dual-gate; still keep runtime test |
| A3 | `require_material_draft` as public tiny helper next to assembler is preferred over test-only | Pattern 3 | Test-only still meets SC-3; Phase 9 loses reuse |
| A4 | Fake `.calls` for ArticleGenerator stores `dict` with keys `transcript`/`template` | D-16 / Code Examples | Predicate assert on tuple pairs also fine |
| A5 | Strip validators apply to all required MaterialDraft/VideoMetadata strings (same spirit as D-09) | Discretion | Over-strict strip on URLs unlikely harmful |
| A6 | `ArticleDraft` stays importable via `data_collection.dto.article_draft` for tests without being in `__all__` | D-06 | Deep-import OK inside package tests |
| A7 | `asyncio.run` in sync tests is sufficient (no pytest-asyncio) | Pattern 2 | Confirmed no plugin today; if added later, either style works |

**If empty:** N/A — discretion items remain for planner confirmation where marked ASSUMED.

## Open Questions (RESOLVED)

1. **Where to place `require_material_draft`** — RESOLVED
   - Locked by 06-01: public tiny helper `require_material_draft` in `assemble.py` (Phase 9 persist can reuse; zero I/O).

2. **Async test runner** — RESOLVED
   - Locked by 06-01/06-02: `asyncio.run(...)` inside sync pytest tests; **do not** add `pytest-asyncio` for Phase 6.

3. **Exact MaterialDraft string validators beyond requiredness** — RESOLVED
   - Locked by 06-01/06-02: strip/non-blank on MaterialDraft required strings (`title`, `dek`, `body_markdown`, `source_url`, `youtube_video_id`, `source_author`, `provenance_label`); allow `source_published_at=None`. Same spirit for ArticleDraft article fields.

No blockers for planning.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | DTO/port unit tests | ✓ | ≥3.12 (package) | — |
| uv | `uv run pytest` | ✓ | workspace | — |
| pydantic (data-collection) | DTOs | ✓ | 2.13.5 | — |
| pytest | unit suite | ✓ | 9.1.1 | — |
| Network / YouTube / DeepSeek | — | N/A | — | **Not used** in Phase 6 |
| Supabase / migrations | — | N/A | — | **Forbidden** this phase |
| mypy / pyright | — | ✗ not configured | — | Runtime boundary test |
| pytest-asyncio | — | ✗ | — | `asyncio.run` |

**Missing dependencies with no fallback:** none for Phase 6 scope.  
**Missing dependencies with fallback:** typechecker → runtime isinstance test; async plugin → `asyncio.run`.

Step 2.6 note: Phase 6 is code/config-only for new contracts; external I/O tools are out of scope.

## Validation Architecture

> `workflow.nyquist_validation` absent in `.planning/config.json` → treat as **enabled**.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `9.1.1` (workspace `tests/unit`) |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`pythonpath = ["."]`) |
| Quick run command | `uv run pytest tests/unit/test_transcript_dto.py tests/unit/test_assemble_material_draft.py tests/unit/test_material_draft_type_boundary.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DTO-01 | Transcript validation (strip/blank/language length) | unit | `uv run pytest tests/unit/test_transcript_dto.py -x` | ❌ Wave 0 |
| DTO-01 | VideoMetadata required author/url/id; published_at optional | unit | `uv run pytest tests/unit/test_video_metadata_dto.py -x` | ❌ Wave 0 |
| DTO-01 | MaterialDraft required provenance fields; None published_at OK | unit | `uv run pytest tests/unit/test_material_draft_dto.py -x` | ❌ Wave 0 |
| DTO-01 | TemplateKind only lecture\|podcast | unit | `uv run pytest tests/unit/test_template_kind.py -x` | ❌ Wave 0 |
| DTO-02 | FakeTranscriptProvider returns scripted Transcript; `.calls` records video_id | unit (`asyncio.run`) | `uv run pytest tests/unit/test_transcript_provider_fake.py -x` | ❌ Wave 0 |
| DTO-02 | FakeArticleGenerator returns ArticleDraft; `.calls` records pair | unit (`asyncio.run`) | `uv run pytest tests/unit/test_article_generator_fake.py -x` | ❌ Wave 0 |
| CONTEXT D-07 | Assembler maps fields; None published_at copied; label not invented | unit | `uv run pytest tests/unit/test_assemble_material_draft.py -x` | ❌ Wave 0 |
| Roadmap SC-3 | Transcript → TypeError where MaterialDraft required | unit | `uv run pytest tests/unit/test_material_draft_type_boundary.py -x` | ❌ Wave 0 |
| D-01…D-03 | Old DTO modules/tests gone; public `__all__` is new surface | unit / import | `uv run pytest tests/unit/test_data_collection_public_api.py -x` | ❌ Wave 0 |
| D-04 / D-06 | Fakes and ArticleDraft not in `data_collection.__all__` | unit | same public-api test | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** targeted new unit file(s) (`-x`)
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full `uv run pytest` green before `/gsd-verify-work` (no Playwright required for Phase 6)

### Wave 0 Gaps

- [ ] Write RED tests for new DTOs/ports/assembler/boundary/public API **before** production code (`tdd.mdc`)
- [ ] Delete `dto/youtube.py`, `dto/foundry.py`, `dto/text_import.py` and three unit test files once new surface is green
- [ ] Rewrite `data_collection/__init__.py` `__all__` to six public names only
- [ ] Create `ports/`, `assemble.py`, internal `ArticleDraft`, `tests_support/fakes.py`
- [ ] Use `asyncio.run` for async fake tests (do not add pytest-asyncio)
- [ ] Assert no diffs under `supabase-integration/migrations/` or `query_embedder.py` for this phase

## Security Domain

> `security_enforcement` absent in config → treat as **enabled**.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No HTTP/auth in Phase 6 |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | yes | Pydantic validation on all public DTOs; reject blank provenance/title/body |
| V6 Cryptography | no | No secrets; no network clients |

### Known Threat Patterns for ingestion contracts

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Treating raw transcript as publishable material | Tampering / integrity | Separate types + type-boundary test; D-CONTENT-01 |
| Empty/whitespace “article” slipping through | Tampering | Field validators strip + min_length |
| Fake doubles imported in production composition | Spoofing | Fakes only in `tests_support` (D-04) |
| Invented provenance label in assembler | Repudiation / honesty | Caller-supplied label only (D-07/D-08) |
| Accidental migration / data writes | Tampering | Out of scope; no DB clients in phase |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/06-ports-dtos/06-CONTEXT.md` — D-01…D-17 (law)
- `.planning/REQUIREMENTS.md` — DTO-01, DTO-02
- `.planning/ROADMAP.md` — Phase 6 goal + success criteria (incl. type boundary)
- `.planning/STATE.md` — Phase 6 context gathered
- `.cursor/rules/architecture.mdc`, `tdd.mdc`, `AGENTS.md`
- Brownfield Read this session: `data-collection` DTOs + `__init__.py`, three `tests/unit/test_*_dto.py`
- `backend/.../domain/material.py`, `backend/.../application/ports/query_embedder.py`, `material_repository.py`
- `backend/.../tests_support/in_memory.py` — fake placement analog
- `supabase-integration/migrations/001_initial_schema.sql:89-104` — provenance_label only
- `uv run` version checks: pydantic `2.13.5`, pytest `9.1.1`

### Secondary (MEDIUM confidence)
- Context7 `/pydantic/pydantic` — Field/validators, StringConstraints strip-before-min_length
- Context7 `/python/cpython` — `typing.Protocol` structural subtyping / `@runtime_checkable`
- Early `.planning/research/ARCHITECTURE.md` / `STACK.md` / `FEATURES.md` — **superseded** on DTO coexistence; still useful for milestone intent

### Tertiary (LOW confidence)
- Exact future oEmbed adapter module path — Phase 7+; author field shape locked only

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pinned deps verified this session; no new installs
- Architecture: HIGH — CONTEXT locked decisions + brownfield inventory + backend port analog
- Pitfalls: HIGH — delete/replace hazards and schema gap verified from source files

**Research date:** 2026-09-26  
**Valid until:** 2026-10-26 (stable contracts domain; re-check if pydantic major or workspace test tooling changes)
