# Phase 30: Classifier practical | conceptual - Pattern Map

**Mapped:** 2026-10-28
**Files analyzed:** 33 (8 new + 12 production-modify + 13 test-extend)
**Analogs found:** 31 / 33

> Phase 30 is a **gate, not an enricher**. New production is a module-private
> `TopicKindClassifier` port + cheap DeepSeek JSON adapter, a KIND-02
> `normalize_topic_kind` sibling of `normalize_roles`, a `## Гайд` strip sibling
> of `strip_audience_section`, additive `topic_kind` on both drafts, pipeline
> stamp, and migration `014` that **DROPs** the 12-arg RPC then recreates it
> with `p_topic_kind`. Tavily / enricher / cheat-sheet / reader badges are out.
>
> **Tracked-source gate:** analog paths below are live in-tree files (Read this
> session). No gitignored mirrors.
>
> **No `conftest.py` exists** under `tests/` (Phase 29 pattern map). New test
> modules declare their own helpers. Do **not** create `tests/unit/conftest.py`.
>
> **Do not widen locked contracts:** `data_collection.__all__` stays the ten
> names in `data-collection/src/data_collection/__init__.py:13-24`;
> `ports/__init__.py` `__all__` stays four names (`:8-14`); `Stage` stays the
> seven values in `ingestion-service/src/ingestion_service/domain/errors.py:8-16`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `data-collection/src/data_collection/ports/topic_kind.py` (NEW) | port (Protocol) | request-response | `data-collection/src/data_collection/ports/article_generator.py` | exact |
| `data-collection/src/data_collection/dto/topic_kind.py` (NEW) | model / utility | transform | `data-collection/src/data_collection/dto/role_kind.py` | exact |
| `data-collection/src/data_collection/adapters/deepseek_classifier.py` (NEW) | adapter (module-private) | request-response | `data-collection/src/data_collection/adapters/deepseek_article.py` | role-match (invert stream + errors) |
| `data-collection/src/data_collection/dto/_body.py` (MODIFIED) | utility | transform | itself: `strip_audience_section` | exact (self) |
| `data-collection/src/data_collection/dto/article_draft.py` (MODIFIED) | model (Pydantic DTO) | transform | itself: `roles` + audience validator | exact (self) |
| `data-collection/src/data_collection/dto/material_draft.py` (MODIFIED) | model (Pydantic DTO) | CRUD payload | itself: `roles` field + before-validator | exact (self) |
| `data-collection/src/data_collection/assemble.py` (MODIFIED) | service (pure assembler) | transform | itself: `roles=article.roles` copy | exact (self) |
| `data-collection/src/data_collection/tests_support/fakes.py` (MODIFIED) | test double | request-response | itself: `FakeArticleGenerator` | exact (self) |
| `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` (MODIFIED) | use-case | request-response | itself: after `article.process`, before `assemble_material_draft` | exact (self) |
| `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py` (MODIFIED) | use-case | batch | itself: `run_ingest_pipeline(...)` call at `:172-181` | exact (self) |
| `ingestion-service/src/ingestion_service/composition/clients.py` (MODIFIED) | composition / config | request-response | itself: `build_deepseek_article_generator` + `build_async_deepseek_client` | exact (self) |
| `ingestion-service/src/ingestion_service/composition/__init__.py` (MODIFIED, optional export) | config barrel | — | itself: `__all__` lists article factory | role-match |
| `ingestion-service/src/ingestion_service/cli.py` (MODIFIED) | CLI controller | request-response | itself: `build_ingest_deps` + `run_ingest_pipeline` kwargs | exact (self) |
| `ingestion-service/src/ingestion_service/collect_cli.py` (MODIFIED) | CLI controller | batch | itself: `CollectDeps(...)` in `build_collect_deps` | exact (self) |
| `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` (MODIFIED) | adapter | CRUD | itself: `_rpc_params` | exact (self) |
| `supabase-integration/migrations/014_phase30_materials_topic_kind.sql` (NEW) | migration | CRUD | `009` RPC body + grants; `005` `ADD COLUMN IF NOT EXISTS`; skill DO-block for CHECK | role-match (DROP FUNCTION has **no** in-repo analog) |
| `tests/unit/test_topic_kind.py` (NEW) | test | transform | `tests/unit/test_article_draft_roles.py` | exact |
| `tests/unit/test_article_draft_body_guide.py` (NEW) | test | transform | `tests/unit/test_article_draft_body_audience.py` | exact |
| `tests/unit/test_phase30_migration_014.py` (NEW) | test | file-I/O SQL contract | `tests/unit/test_phase11_migration_009.py` | exact |
| `tests/unit/test_deepseek_classifier.py` (NEW, implied) | test | request-response | `tests/unit/test_deepseek_article_adapter.py` (`_stub_client`, create-kwargs) | role-match (stub must be **non-stream**) |
| `tests/unit/test_data_collection_public_api.py` (MODIFIED) | test | — | itself: `NEGATIVE_ROOT_NAMES`, `PUBLIC_NAMES`, `test_stage_set_is_unchanged` | exact (self) |
| `tests/unit/test_ingest_pipeline.py` (MODIFIED) | test | request-response | itself: helpers `_article` / `_persist` + `FakeArticleGenerator` | exact (self) |
| `tests/unit/test_assemble_material_draft.py` (MODIFIED) | test | transform | itself: `test_assemble_material_draft_copies_article_roles` | exact (self) |
| `tests/unit/test_supabase_draft_persister_contract.py` (MODIFIED) | test | CRUD | itself: `params["p_roles"]` assertions | exact (self) |
| `tests/unit/test_build_ingest_deps_wiring.py` (MODIFIED) | test | request-response | itself: four-port monkeypatch | exact (self) |
| `tests/unit/test_deepseek_article_adapter.py` (MODIFIED — negative `Гайд` pin) | test | request-response | itself: `SHARED_PROMPT_HEADINGS` | exact (self) |
| `tests/unit/test_collect_batch.py` (MODIFIED) | test | batch | itself: `CollectDeps(...)` constructors | exact (self) |
| `tests/unit/test_collect_cli_contract.py` (MODIFIED) | test | batch | itself: helper `CollectDeps` at `:67-79` | exact (self) |
| `tests/unit/test_cli_ingest_contract.py` (MODIFIED) | test | request-response | itself: `_fake_deps` + `EXPECTED_SUCCESS_LINES` | exact (self) |
| `tests/unit/test_cli_debug_diagnostics.py` (MODIFIED) | test | request-response | itself: `_fake_deps` via monkeypatched `build_ingest_deps` | exact (self) |
| `tests/unit/test_material_draft_roles.py` (MODIFIED or sibling cases) | test | transform | itself | exact (self) |
| `tests/unit/test_ingestion_clients.py` (MODIFIED if composition `__all__` grows) | test | config | itself: `test_composition_exports_supabase_factories` | exact (self) |
| `tests/unit/test_article_generator_fake.py` (optional sibling) | test | request-response | itself: `FakeArticleGenerator` spy | exact (self) |

**Do not create / do not modify (locked or out of scope):**

| File | Why |
|------|-----|
| `data-collection/src/data_collection/__init__.py` | ten-name `__all__` pin |
| `data-collection/src/data_collection/ports/__init__.py` | do not append `TopicKindClassifier` |
| `ingestion-service/src/ingestion_service/domain/errors.py` | `Stage` seven values |
| `data-collection/src/data_collection/templates/lecture.md` / `podcast.md` | Phase 29 pin: no `Гайд` |
| `ingestion-service/src/ingestion_service/diagnostics/redaction.py` | DBG-03 is Phase 34; do not add `topic_kind` / classify stderr this phase |
| `supabase-integration/src/supabase_integration/material_repository.py` | reader SELECT list must **omit** `topic_kind` |
| `backend/` / `web/` | no SPA/backend DTO |
| `supabase-integration/migrations/007`–`009` | amend-don't-edit-applied |
| `ingestion-service/src/ingestion_service/application/use_cases/ingest_until_persist.py` | CAP-02 test-only slice; not the CLI ingest path. Do not add classifier unless a test already requires KIND-01 there. |

---

## Pattern Assignments

### `data-collection/src/data_collection/ports/topic_kind.py` (port, request-response)

**Analog:** `data-collection/src/data_collection/ports/article_generator.py`

**Imports + Protocol shape** (lines 1-15) — copy docstring/module-private tone, `from __future__`, `typing.Protocol`, DTO imports. Do **not** add this name to `ports/__init__.py` or package `__all__`. Callers import the module path the same way the pipeline already imports `ArticleGenerator`:

```python
from data_collection.ports.article_generator import ArticleGenerator
```

```1:15:data-collection/src/data_collection/ports/article_generator.py
"""ArticleGenerator port — LLM prepares ArticleDraft from Transcript (D-16)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.article_draft import ArticleDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript


class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...
```

**Target method (from RESEARCH; return raw `object`, not a validated enum):**

```python
class TopicKindClassifier(Protocol):
    async def classify(
        self, transcript: Transcript, article: ArticleDraft
    ) -> object: ...
```

Sibling Protocol style (one-method, no `runtime_checkable` unless persist-style): `ports/transcript_provider.py:10-11`.

---

### `data-collection/src/data_collection/dto/topic_kind.py` (model / utility, transform)

**Analog:** `data-collection/src/data_collection/dto/role_kind.py`

**Entire analog (lines 1-16)** — clone Literal + frozenset + fail-closed mapper. KIND-02 default is `"conceptual"` (roles default is `"employee"`). Accept **only** the two tokens after `strip` + `casefold`; everything else including `"unsure"` / `None` / dict / list → `"conceptual"`. D-08 lives in the **prompt**, not here.

```1:16:data-collection/src/data_collection/dto/role_kind.py
"""Closed audience-role set for ingestion drafts (D-14). Not a public export."""

from __future__ import annotations

from typing import Literal

RoleKind = Literal["employee", "analyst", "ds"]
VALID_ROLES: frozenset[str] = frozenset({"employee", "analyst", "ds"})


def normalize_roles(value: object) -> list[RoleKind]:
    """Filter unknown roles; empty or malformed input becomes ['employee']."""
    if not isinstance(value, list):
        return ["employee"]
    filtered: list[RoleKind] = [role for role in value if role in VALID_ROLES]
    return filtered or ["employee"]
```

**Before-validator hook analog** (so Pydantic `Literal` never sees garbage → `ValidationError` → `stage=llm`):

```28:31:data-collection/src/data_collection/dto/article_draft.py
    @field_validator("roles", mode="before")
    @classmethod
    def _normalize_roles(cls, value: object) -> list[RoleKind]:
        return normalize_roles(value)
```

Copy that onto `ArticleDraft.topic_kind` **and** `MaterialDraft.topic_kind`. Default field value `"conceptual"`.

**Adapter may return a dict** (`{"topic_kind": "practical"}`). `normalize_topic_kind` must still only accept a str in the closed set — if the adapter returns a dict, either unwrap `payload.get("topic_kind")` **in the adapter** (then still run normalize in the pipeline) or have normalize look up that one key. Prefer unwrap in the adapter + always `normalize_topic_kind` in the pipeline so `"kind": "practical"` cannot launder (research Pitfall 1).

---

### `data-collection/src/data_collection/adapters/deepseek_classifier.py` (adapter, request-response)

**Analog:** `data-collection/src/data_collection/adapters/deepseek_article.py`

**Copy these slices; invert the rest.**

**Imports / injected client / JSON mode / thinking.disabled** (lines 1-21, 85-98, 139-145):

```85:98:data-collection/src/data_collection/adapters/deepseek_article.py
class DeepSeekArticleGenerator:
    """ArticleGenerator implementation over an injected async OpenAI client."""

    def __init__(
        self,
        client: Any,
        model: str,
        templates: dict[TemplateKind, str],
        max_transcript_chars: int,
    ) -> None:
        self._client = client
        self._model = model
        self._templates = templates
        self._max_transcript_chars = max_transcript_chars
```

```139:145:data-collection/src/data_collection/adapters/deepseek_article.py
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                response_format={"type": "json_object"},
                extra_body={"thinking": {"type": "disabled"}},
                stream=True,
            )
```

**Classifier call shape (do not copy `stream=True`):**

```python
response = await self._client.chat.completions.create(
    model=self._model,
    messages=messages,
    response_format={"type": "json_object"},
    extra_body={"thinking": {"type": "disabled"}},
    max_tokens=128,
    stream=False,
)
content = response.choices[0].message.content
```

**JSON parse analog** (lines 111-120) — keep `json.loads`, but **do not** raise `ArticleInvalidJson` / `ArticleInvalidDraft`. Empty content, non-dict, missing key → return a raw value the pipeline will map to `conceptual`.

```111:120:data-collection/src/data_collection/adapters/deepseek_article.py
        if not isinstance(content, str) or content == "":
            raise ArticleInvalidJson(transcript.video_id)

        try:
            payload = json.loads(content)
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise ArticleInvalidJson(transcript.video_id) from exc

        if not isinstance(payload, dict):
            raise ArticleInvalidJson(transcript.video_id)
```

**Do NOT copy** the exception taxonomy at lines 154-192 (`ArticleNetworkError` / `ArticleAuthError` / …). Those become `map_article_error` → `stage="llm"` and drop a finished pass-1 draft (research Pitfall 2). Classifier transport errors: either return `None` or raise a **generic** exception that the pipeline `except Exception` swallows. Never `from data_collection.errors.article import …` in this module.

**Do NOT copy** `ARTICLE_SYSTEM_PROMPT` keys (`title, dek, body_markdown, roles` at line 50) and do **not** add `topic_kind` there. Classifier gets its own system prompt encoding D-01…D-08. User message **must contain the word `json`** (DeepSeek JSON mode HTTP 400 otherwise).

**Classifier input (discretion, from RESEARCH):** `article.title` + `article.dek` + transcript **head+tail** truncation. Do **not** send `body_markdown` (СВА analog / `## Конкретика` look practical). Fence transcript as untrusted data.

**Message-builder analog** (structure only — different content):

```54:70:data-collection/src/data_collection/adapters/deepseek_article.py
def build_article_messages(
    transcript: Transcript,
    template: TemplateKind,
    templates: dict[TemplateKind, str],
) -> list[dict[str, str]]:
    """System prompt + user message carrying template, language, and transcript."""
    user_parts = [
        templates[template],
        "",
        f"Transcript language: {transcript.language}",
        "",
        transcript.text,
    ]
    return [
        {"role": "system", "content": ARTICLE_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(user_parts)},
    ]
```

**Factory analog** — clone `build_deepseek_article_generator`, reuse `build_async_deepseek_client` (`trust_env=False`). Do **not** share `build_httpx_client` (YouTube SOCKS5). No new Settings env var.

```64:100:ingestion-service/src/ingestion_service/composition/clients.py
def build_async_deepseek_client(
    api_key: str, base_url: str, timeout: float
) -> AsyncOpenAI:
    if not api_key or not api_key.strip():
        raise ConfigurationError("DEEPSEEK_API_KEY is required")
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
        max_retries=0,
        http_client=DefaultAsyncHttpxClient(trust_env=False),
    )


def build_deepseek_article_generator(
    settings: Settings,
    template_root: object | None = None,
) -> DeepSeekArticleGenerator:
    import importlib.resources

    root = (
        template_root
        if template_root is not None
        else importlib.resources.files("data_collection.templates")
    )
    templates = load_article_templates(root)
    client = build_async_deepseek_client(
        settings.deepseek_api_key or "",
        settings.deepseek_base_url,
        _DEEPSEEK_TIMEOUT,
    )
    return DeepSeekArticleGenerator(
        client=client,
        model=settings.deepseek_model,
        templates=templates,
        max_transcript_chars=settings.max_transcript_chars,
    )
```

New factory: `build_deepseek_topic_kind_classifier(settings)` — own client via `build_async_deepseek_client`, same model/key, **no** templates, **no** `max_transcript_chars` fail-closed (truncate in the classifier instead).

Adapters package `__init__.py` is an empty docstring (`adapters/__init__.py:1`) — keep the new module off any barrel.

---

### `data-collection/src/data_collection/dto/_body.py` (utility, transform)

**Analog:** itself — `strip_audience_section`

**Heading regex + next-h1/h2 walk** (lines 16-41). Add `_GUIDE_HEADING_RE` with the same ATX shape, text exactly `Гайд`, `re.IGNORECASE | re.MULTILINE` (so `## гайд` cannot leak; D-12 “exact” means do **not** match `Guide` / `How-to` / `Как сделать` / `Tutorial` / `Шпаргалка`). Then delete the exact substring `ссылки скоро появятся`. Leave in-prose «гайд».

```16:41:data-collection/src/data_collection/dto/_body.py
_AUDIENCE_HEADING_RE = re.compile(
    r"^#{2,6}[ \t]+Аудитория[ \t]*$", re.IGNORECASE | re.MULTILINE
)
_NEXT_TOP_HEADING_RE = re.compile(r"^#{1,2}[ \t]+\S", re.MULTILINE)


def strip_audience_section(body_markdown: str) -> str:
    """Drop the trailing `## Аудитория` prompt-scaffolding block, if present.

    Removes the heading and its content up to the next h1/h2 heading (normally
    end-of-body, since the templates place it last). Leaves the text untouched
    when no such heading exists, so an in-prose mention of "аудитория" survives.
    """
    match = _AUDIENCE_HEADING_RE.search(body_markdown)
    if match is None:
        return body_markdown

    tail = body_markdown[match.end():]
    next_heading = _NEXT_TOP_HEADING_RE.search(tail)
    if next_heading is None:
        cleaned = body_markdown[: match.start()]
    else:
        cleaned = body_markdown[: match.start()] + tail[next_heading.start():]
    return cleaned.strip()
```

Reuse `_NEXT_TOP_HEADING_RE`. Hook from a **second** `@field_validator("body_markdown")` on `ArticleDraft` so it runs on **every** pass-1 body (D-11), including practical drafts. Do not fail ingest if the heading leaked (Phase 8 D-15).

Audience validator analog:

```21:26:data-collection/src/data_collection/dto/article_draft.py
    @field_validator("body_markdown")
    @classmethod
    def _strip_audience_scaffolding(cls, value: str) -> str:
        # `## Аудитория` is prompt scaffolding for the `roles` key, not article
        # content; models sometimes leak it (as JSON or the echoed instruction).
        return strip_audience_section(value)
```

---

### `data-collection/src/data_collection/dto/article_draft.py` (model, transform)

**Analog:** itself.

Add `topic_kind: TopicKind = "conceptual"` + `field_validator("topic_kind", mode="before")` calling `normalize_topic_kind`. Keep existing audience strip. Add guide-strip validator. Pipeline **overwrites** `article_draft.topic_kind` after classify even if pass-1 JSON leaked a key (research Pitfall 4). Do **not** add `topic_kind` to `ARTICLE_SYSTEM_PROMPT`.

```10:31:data-collection/src/data_collection/dto/article_draft.py
class ArticleDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    roles: list[RoleKind] = ["employee"]

    @field_validator("title", "dek", "body_markdown")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)

    @field_validator("body_markdown")
    @classmethod
    def _strip_audience_scaffolding(cls, value: str) -> str:
        # `## Аудитория` is prompt scaffolding for the `roles` key, not article
        # content; models sometimes leak it (as JSON or the echoed instruction).
        return strip_audience_section(value)

    @field_validator("roles", mode="before")
    @classmethod
    def _normalize_roles(cls, value: object) -> list[RoleKind]:
        return normalize_roles(value)
```

---

### `data-collection/src/data_collection/dto/material_draft.py` (model, CRUD)

**Analog:** itself — additive field next to `roles`.

```11:22:data-collection/src/data_collection/dto/material_draft.py
class MaterialDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    youtube_video_id: str = Field(min_length=1)
    source_author: str = Field(min_length=1)
    provenance_label: str = Field(min_length=1)
    source_published_at: datetime | None = None
    roles: list[RoleKind] = ["employee"]
    slug: str = ""
    reading_minutes: int = 1
```

Same before-validator pattern as `roles` (`:44-47`). Do **not** stuff kind into `provenance_label`.

---

### `data-collection/src/data_collection/assemble.py` (service, transform)

**Analog:** itself — additive field copy, same as `roles=article.roles`.

```10:25:data-collection/src/data_collection/assemble.py
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
        provenance_label=provenance_label,
        source_published_at=metadata.published_at,
        roles=article.roles,
    )
```

Add `topic_kind=article.topic_kind`. Provenance stays caller-supplied.

Test analog: `tests/unit/test_assemble_material_draft.py:35-55` (`test_assemble_material_draft_copies_article_roles`) — clone for `topic_kind`.

---

### `data-collection/src/data_collection/tests_support/fakes.py` (test double, request-response)

**Analog:** `FakeArticleGenerator` (lines 58-76)

```58:76:data-collection/src/data_collection/tests_support/fakes.py
class FakeArticleGenerator:
    def __init__(
        self,
        result: ArticleDraft,
        failures: dict[str, ArticleError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[ArticleGeneratorCall] = []

    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft:
        self.calls.append({"transcript": transcript, "template": template})
        failure = self._failures.get(transcript.video_id)
        if failure is not None:
            raise failure
        await asyncio.sleep(0)
        return self._result
```

`FakeTopicKindClassifier`: script `result: object` (str or dict), record `calls`, optional `failures` that the **pipeline must swallow** (generic `Exception`, **not** `ArticleError`). Spy tests clone `tests/unit/test_article_generator_fake.py:6-23`.

---

### `ingestion-service/.../ingest_pipeline.py` (use-case, request-response)

**Analog:** itself. Insert classify **after** the LLM success path (after `on_stage("llm")`, before `assemble_material_draft`). Required kwarg `classifier=` — no `None` default (research Pitfall 6).

Spine to copy (lines 113-140):

```113:140:ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py
    if diagnostics is not None:
        diagnostics.stage_started("llm")
    try:
        article_draft = await article.process(transcript, template)
    except ArticleError as err:
        mapped = map_article_error(err)
        if diagnostics is not None:
            diagnostics.stage_failed(
                mapped.stage, reason=mapped.reason, exit_code=mapped.exit_code
            )
        raise mapped from err
    if diagnostics is not None:
        diagnostics.stage_completed(
            "llm",
            {
                "template": template.value,
                "response_chars": len(article_draft.body_markdown),
            },
        )
    if on_stage is not None:
        on_stage("llm")

    material = assemble_material_draft(article_draft, metadata, provenance)
    if diagnostics is not None:
        diagnostics.stage_started("persist")
    try:
        result = persist_draft(material, persist)
```

**Stamp pattern (from RESEARCH — invert article error handling):**

```python
try:
    raw = await classifier.classify(transcript, article_draft)
except Exception:
    raw = None
article_draft.topic_kind = normalize_topic_kind(raw)
material = assemble_material_draft(article_draft, metadata, provenance)
```

Always stamp, even when the draft already has a value (Pitfall 4). Do **not** emit a fourth stdout checkmark (`on_stage` stays transcript/llm/saved). Do **not** call `diagnostics.stage_failed` for classify. Prefer **no** classify diagnostic this phase (DBG-03 is Phase 34; `ALLOWED_KEYS` at `diagnostics/redaction.py:13-33` has no `topic_kind`).

**Fail-soft analog** (closest in-repo swallow, not LLM): `collect_batch.py:182-187` per-video `except Exception` — classifier is the same shape but **must still persist**.

Do **not** wire Tavily/enricher/cheat-sheet. Pin absence: grep the pipeline module for those names in `test_ingest_pipeline.py`.

Existing pipeline tests all call `run_ingest_pipeline` **without** `classifier=` (`tests/unit/test_ingest_pipeline.py:61-68` and every subsequent call). Adding a required kwarg will TypeError the whole file plus:

- `tests/unit/test_cli_ingest_contract.py` (`_fake_deps` `:62-70` — deps object; CLI forwards kwargs)
- `tests/unit/test_cli_debug_diagnostics.py`
- `tests/unit/test_collect_batch.py` (indirect via `CollectDeps` + `run_ingest_pipeline` `:172-181`)
- `tests/unit/test_collect_cli_contract.py`

**Call-site analog to extend:**

```172:181:ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py
                result = await run_ingest_pipeline(
                    video.video_id,
                    template,
                    captions=deps.captions,
                    metadata_provider=deps.metadata_provider,
                    article=deps.article,
                    persist=deps.persist,
                    on_stage=None,
                    diagnostics=None,
                )
```

Add `classifier=deps.classifier`. Extend frozen `CollectDeps` (`:25-35`) with a `classifier` field — every `CollectDeps(` in `test_collect_batch.py` and `test_collect_cli_contract.py:67-79` must grow the kwarg.

---

### `ingestion-service/.../cli.py` + `collect_cli.py` (CLI, request-response / batch)

**`build_ingest_deps` analog** (`cli.py:39-48`):

```39:48:ingestion-service/src/ingestion_service/cli.py
def build_ingest_deps() -> Any:
    """Composition seam for live adapters; CliRunner monkeypatches this with fakes."""
    settings = Settings.from_env()
    return SimpleNamespace(
        captions=build_youtube_captions(settings),
        metadata_provider=build_youtube_metadata_provider(settings),
        article=build_deepseek_article_generator(settings),
        persist=build_supabase_draft_persister(settings),
        settings=settings,
    )
```

Add `classifier=build_deepseek_topic_kind_classifier(settings)` and pass `classifier=deps.classifier` into `run_ingest_pipeline` (`:99-108`).

**Stdout contract must not grow a checkmark** (`test_cli_ingest_contract.py:20-29`):

```20:29:tests/unit/test_cli_ingest_contract.py
EXPECTED_SUCCESS_LINES = [
    "✓ transcript",
    "✓ LLM",
    "✓ saved",
    "material_id: 42",
    f"slug: {EXPECTED_SLUG}",
    "batch_id: 7",
    "rank: 1",
    "already_saved: false",
]
```

`_STAGE_CHECKMARKS` (`cli.py:32-36`) stays three keys.

**Collect composition analog** (`collect_cli.py:35-54`):

```44:54:ingestion-service/src/ingestion_service/collect_cli.py
    return CollectDeps(
        feed=build_youtube_feed(settings),
        sources=build_collect_source_reader(settings),
        captions=build_youtube_captions(settings),
        metadata_provider=build_youtube_metadata_provider(settings),
        article=build_deepseek_article_generator(settings),
        persist=build_supabase_draft_persister(settings),
        emit_diagnostic=emit_diagnostic,
        clock=UtcClock(),
        tz=tz,
    )
```

**Wiring test analog to extend** (`test_build_ingest_deps_wiring.py:26-68`): currently asserts `calls == ["captions", "metadata", "article", "persist"]`. Add a fifth factory track `"classifier"` and assert `deps.classifier`. Source-delegation test (`:12-23`) must also see `build_deepseek_topic_kind_classifier`.

---

### `ingestion-service/.../adapters/supabase_persist.py` (adapter, CRUD)

**Analog:** itself — `_rpc_params`.

```46:61:ingestion-service/src/ingestion_service/adapters/supabase_persist.py
def _rpc_params(draft: MaterialDraft, batch_size: int) -> dict[str, Any]:
    published = draft.source_published_at
    return {
        "p_title": draft.title,
        "p_dek": draft.dek,
        "p_body_markdown": draft.body_markdown,
        "p_slug": draft.slug,
        "p_reading_minutes": draft.reading_minutes,
        "p_provenance_label": draft.provenance_label,
        "p_source_url": draft.source_url,
        "p_youtube_video_id": draft.youtube_video_id,
        "p_source_author": draft.source_author,
        "p_source_published_at": published.isoformat() if published is not None else None,
        "p_roles": list(draft.roles),
        "p_batch_size": batch_size,
    }
```

Add `"p_topic_kind": draft.topic_kind`. Do not send `status` (existing pin `test_persist_never_forwards_status_or_ready_to_rpc`).

Test analog: `tests/unit/test_supabase_draft_persister_contract.py:87-113` — after `params["p_roles"]` assert `params["p_topic_kind"]`. `_draft()` helper (`:56-72`) needs no extra field if MaterialDraft defaults to `conceptual`; add an override case for `"practical"`.

`persist_draft` (`persist_draft.py:13-24`) `model_copy`s only `slug` / `reading_minutes` — it will forward `topic_kind` automatically. Do not touch that use-case unless a test proves otherwise.

---

### `supabase-integration/migrations/014_phase30_materials_topic_kind.sql` (migration, CRUD)

**Analogs (compose three; DROP FUNCTION has no in-repo sibling):**

1. **Column add:** `005_phase5_admin_shortlist.sql:8-9` — `alter table … add column if not exists`.
2. **RPC body + grants:** `009_phase11_persist_sent_batch_already_saved.sql` — copy function body, INSERT list, `ON CONFLICT (youtube_video_id) DO NOTHING`, `already_saved`, `security invoker`, revoke/grant **the new signature**.
3. **CHECK constraint idempotency:** `.agents/skills/supabase-postgres-best-practices/references/schema-constraints.md:20-35` — `DO $$ IF NOT EXISTS (pg_constraint) $$`. **`ADD CONSTRAINT IF NOT EXISTS` is invalid Postgres.** Prefer `text` + CHECK, not `CREATE TYPE … ENUM`.

**Live 12-arg signature to DROP** (`009:8-21` and grants `009:179-187`):

```8:21:supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql
create or replace function public.persist_draft_and_enqueue(
  p_title text,
  p_dek text,
  p_body_markdown text,
  p_slug text,
  p_reading_minutes int,
  p_provenance_label text,
  p_source_url text,
  p_youtube_video_id text,
  p_source_author text,
  p_source_published_at timestamptz,
  p_roles text[],
  p_batch_size int
)
```

```179:187:supabase-integration/migrations/009_phase11_persist_sent_batch_already_saved.sql
revoke all on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) from public;
revoke all on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) from anon, authenticated;
grant execute on function public.persist_draft_and_enqueue(
  text, text, text, text, int, text, text, text, text, timestamptz, text[], int
) to service_role;
```

**INSERT column list to extend** (`009:40-72`) — add `topic_kind` / `p_topic_kind` (DEFAULT `'conceptual'`). Do not overwrite on `ON CONFLICT DO NOTHING`.

**Required 014 sequence (RESEARCH Pattern 4):**

1. `ALTER TABLE public.materials ADD COLUMN IF NOT EXISTS topic_kind text NOT NULL DEFAULT 'conceptual';`
2. `DO $$ … ADD CONSTRAINT materials_topic_kind_check CHECK (topic_kind IN ('practical', 'conceptual'))`
3. `DROP FUNCTION IF EXISTS public.persist_draft_and_enqueue(text, text, text, text, int, text, text, text, text, timestamptz, text[], int);`
4. `CREATE FUNCTION` (not `CREATE OR REPLACE` of the old arity) with `p_topic_kind text DEFAULT 'conceptual'`
5. Revoke/grant the **13-arg** signature to `service_role` only

**Do not** `CREATE OR REPLACE` a 13-arg function without DROP — Postgres will leave the 12-arg overload and PostgREST will keep calling it (research Pitfall 3).

**SQL contract-test analog:** `tests/unit/test_phase11_migration_009.py`

Copy helpers `_sql` / `_sql_without_line_comments` / `_normalized_executable_sql` (`:17-31`). Pin:

- `add column if not exists` + `topic_kind`
- `drop function` with the exact 12 types
- `p_topic_kind` in INSERT
- `'already_saved', true` / `false` still present
- `on conflict (youtube_video_id) do nothing`
- `security invoker`
- `grant execute` … `to service_role` (new arity)
- `truncate ` / `drop table` absent
- applied `009` (and `007`/`008`) unmodified via `git diff --` like `test_migration_008_file_unchanged_relative_to_git_blob` (`:120-138`)

Inline CHECK analog from `012` table create (`check (kind in ('channel', 'playlist'))`) is the **value list** shape, not the idempotent ADD — use the skill DO-block for an existing table.

---

### `tests/unit/test_article_draft_body_guide.py` (test, transform)

**Analog:** `tests/unit/test_article_draft_body_audience.py` — clone `_draft()` and the case matrix.

```17:23:tests/unit/test_article_draft_body_audience.py
def _draft(body_markdown: str, roles=None):
    from data_collection.dto.article_draft import ArticleDraft

    payload = {"title": "t", "dek": "d", "body_markdown": body_markdown}
    if roles is not None:
        payload["roles"] = roles
    return ArticleDraft.model_validate(payload)
```

Clone these behaviours (map Аудитория → Гайд):

| Audience case | Guide equivalent |
|---------------|------------------|
| trailing section (`:26-33`) | empty `## Гайд` stripped |
| echoed prompt (`:36-43`) | filled `## Гайд` also stripped (D-10) |
| unchanged when absent (`:46-51`) | `Guide` / `Как сделать` / `Шпаргалка` **kept** (D-12) |
| later section follows (`:54-63`) | mid-body `## Гайд` … next h2 kept |
| in-prose mention (`:66-72`) | in-prose «гайд» kept (Phase 29 live title even contains it) |
| idempotent (`:75-81`) | same |
| extra | exact substring `ссылки скоро появятся` removed even outside the section |
| extra | lowercase `## гайд` stripped (A3) |
| extra | strip runs on a draft that will be stamped `practical` too (D-11) |

Do **not** fail ingest in these tests; the helper is `model_validate`, not a parser that raises.

Keep `tests/unit/test_article_draft_body_audience.py` green (regression).

---

### `tests/unit/test_topic_kind.py` (test, transform)

**Analog:** `tests/unit/test_article_draft_roles.py` + `tests/unit/test_material_draft_roles.py`

```8:42:tests/unit/test_article_draft_roles.py
def test_article_draft_keeps_valid_roles() -> None:
    from data_collection.dto.article_draft import ArticleDraft

    draft = ArticleDraft.model_validate(
        {
            "title": "t",
            "dek": "d",
            "body_markdown": "b",
            "roles": ["employee", "analyst"],
        }
    )
    assert draft.roles == ["employee", "analyst"]


def test_article_draft_filters_unknown_roles() -> None:
    ...
    assert draft.roles == ["employee"]


def test_article_draft_missing_roles_falls_back_to_employee() -> None:
    ...
    assert draft.roles == ["employee"]
```

Matrix for `normalize_topic_kind` / DTO:

- `"practical"` / `"conceptual"` kept (casefold+strip: `" Practical "` → practical)
- missing / `None` / `""` / `"unsure"` / `"howto"` / `{"kind": "practical"}` / `[]` → `"conceptual"`
- constructor + `model_validate` both normalize
- **must not** `ValidationError` on garbage (that would become `stage=llm`)

Two-layer pin (do not merge D-08 into code): Fake returning `"practical"` on an ambiguous how-to is stored practical; Fake/`None`/`"unsure"` is stored conceptual.

---

### `tests/unit/test_deepseek_classifier.py` (test, request-response) — implied

**Analog:** `tests/unit/test_deepseek_article_adapter.py`

**Create-kwargs pin** (`:205-222`) — copy the assertion shape, change `stream`:

```205:222:tests/unit/test_deepseek_article_adapter.py
def test_create_kwargs_include_json_object_and_disabled_thinking() -> None:
    ...
    call = client.chat.completions.calls[0]
    assert call["response_format"] == {"type": "json_object"}
    assert call["extra_body"] == {"thinking": {"type": "disabled"}}
```

Classifier: same two asserts **plus** `stream is False` (or absent+default false) **plus** `max_tokens == 128`. Pass-1 pin `test_create_kwargs_include_json_object_and_disabled_thinking` must **stay** `stream=True`.

**Stub must invert streaming.** Current `_stub_client` (`:37-54`) returns an async generator of delta chunks. Classifier `stream=False` needs `choices[0].message.content`. Write a **non-stream** stub; do not reuse `_stub_client` as-is.

**Honesty-prompt isolation:** `ARTICLE_SYSTEM_PROMPT` (`deepseek_article.py:50`) stays `keys title, dek, body_markdown, roles` — pin `topic_kind` **absent** from the pass-1 system prompt (existing `test_system_prompt_contains_honesty_and_language_rules` neighborhood `:159-202`). Classifier user message contains `json`.

**Negative heading pin on templates** (extend existing, do not rewrite templates):

```34:34:tests/unit/test_deepseek_article_adapter.py
SHARED_PROMPT_HEADINGS = ("## Конкретика", "## Зачем это СВА", "## Аудитория")
```

Add `assert "Гайд" not in _user_content(...)` (and not in `SHARED_PROMPT_HEADINGS`). Do not add `## Гайд` to templates.

**No live DeepSeek in default suite** (same as article tests — injected stub only).

---

### `tests/unit/test_ingest_pipeline.py` (test, request-response)

**Analog:** itself. Helpers `_transcript` / `_article` / `_metadata` / `_persist` (`:30-49`). Every `run_ingest_pipeline(...)` must pass `classifier=FakeTopicKindClassifier(...)`.

New cases to add **in this file** (KIND-01/02):

1. Fake returns `"practical"` → persisted `MaterialDraft.topic_kind == "practical"` (`persist.calls[0]`)
2. Fake returns `"unsure"` / raises `RuntimeError` / returns `None` → persist still called with `"conceptual"`; `IngestError` **not** raised; `stage` is not `llm`
3. Pass-1 `ArticleDraft(topic_kind="practical")` + Fake returns `"conceptual"` → persisted conceptual (Pitfall 4)
4. No Tavily/enricher/cheat-sheet attributes on the pipeline module / extras uncalled
5. Diagnostics order (`:189-233`) stays captions → metadata → llm → persist; classify must **not** insert `stage_failed`

Do not change `test_article_failure_records_stage_failed_after_completed_stages` (`:263-293`) — article errors still `stage=llm`.

---

### `tests/unit/test_data_collection_public_api.py` (test)

**Analog:** itself.

```10:49:tests/unit/test_data_collection_public_api.py
PUBLIC_NAMES = frozenset(
    {
        "Transcript",
        "VideoMetadata",
        "MaterialDraft",
        "TemplateKind",
        "TranscriptProvider",
        "ArticleGenerator",
        "VideoMetadataProvider",
        "VideoRef",
        "FeedListing",
        "VideoListProvider",
    }
)

NEGATIVE_ROOT_NAMES = (
    "RoleKind",
    "ArticleDraft",
    "normalize_roles",
    "FakeTranscriptProvider",
    "FakeArticleGenerator",
    ...
    "DeepSeekArticleGenerator",
    ...
)
```

Append to `NEGATIVE_ROOT_NAMES`: `"FakeTopicKindClassifier"`, `"TopicKindClassifier"`, `"normalize_topic_kind"`, `"DeepSeekTopicKindClassifier"`, `"TopicKind"`. Do **not** add them to `PUBLIC_NAMES`. `test_stage_set_is_unchanged` (`:109-122`) must stay green with the same seven values — no `"classify"`.

`test_ports_package_exports_both_provider_protocols` (`:63-84`) currently lists four names in `ports.__all__`. Do **not** append `TopicKindClassifier`; optionally pin it is **absent** from that barrel.

---

## Shared Patterns

### Ports stay module-private; composition is the only wiring

**Source:** `data-collection/src/data_collection/__init__.py:13-24`, `ports/__init__.py:8-14`, `ingestion-service/src/ingestion_service/composition/clients.py`
**Apply to:** classifier port, adapter, CLI, collect

New ports are imported by path (`from data_collection.ports.topic_kind import TopicKindClassifier`), never added to package `__all__`. Live adapters are constructed only in `composition/clients.py`. Tests use `Fake*` from `tests_support.fakes`.

### KIND-02 mapping clones `normalize_roles` (code default conceptual)

**Source:** `dto/role_kind.py:7-16` + `field_validator(..., mode="before")` on `ArticleDraft` / `MaterialDraft`
**Apply to:** `topic_kind` on both drafts, pipeline stamp, adapter unwrap

Allowlist only. `"unsure"` is **not** practical in Python. Prompt D-08 is a sentence, not a third enum.

### Body sanitizers run in DTO validators, never fail-closed

**Source:** `dto/_body.py:16-41` + `ArticleDraft._strip_audience_scaffolding`
**Apply to:** `strip_guide_section` + placeholder substring

Same heading-until-next-h1/h2 walk. Strip on every pass-1 body. Do not add a heading parser that rejects ingest (Phase 8 D-15).

### DeepSeek JSON: `json_object` + `thinking.disabled` + injected `trust_env=False` client

**Source:** `deepseek_article.py:139-145`, `clients.py:64-75`
**Apply to:** classifier adapter and its factory

Classifier differs: `stream=False`, `max_tokens=128`, no `ArticleError`. User message must contain `json`. Empty content → conceptual, not `ArticleInvalidJson`.

### Fail-soft vs fail-closed

**Source (fail-closed):** `ingest_pipeline.py` captions/metadata/llm/persist `except *Error` → `IngestError` + `stage_failed`
**Source (fail-soft, closest):** `collect_batch.py:182-187` swallow + continue
**Apply to:** classifier only — swallow, stamp conceptual, **still persist**. Never `stage=llm`. Never a new `Stage` value.

### Additive persist field via new migration, not in-place 009

**Source:** Phase 11 `009` CREATE OR REPLACE same arity; this phase **changes arity** so DROP first
**Apply to:** `014`, `_rpc_params`, persister tests
**Grants:** copy 009 revoke public/anon/authenticated, grant `service_role`, `security invoker`

### stdout checkmarks stay three lines

**Source:** `cli.py:32-36`, `test_cli_ingest_contract.py:20-29`
**Apply to:** CLI. Classifier is not an `on_stage` name. DBG-03 stderr is Phase 34.

### TDD: no `conftest.py`; tests live in `tests/unit/`

**Source:** Phase 29 PATTERNS; `pyproject.toml` `testpaths = ["tests/unit"]`
**Apply to:** every new test module. Red first. Full suite `uv run pytest tests/unit -q`.

### Reader/admin surfaces omit `topic_kind`

**Source:** `material_repository.py:147-152` explicit SELECT list without the new column
**Apply to:** do not add the column to backend Material DTO or web this phase

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `014` `DROP FUNCTION IF EXISTS persist_draft_and_enqueue(<12 types>)` | migration | CRUD | Repo only ever `CREATE OR REPLACE`d the **same** 12-arg signature (`007`→`008`→`009`). Planner must follow RESEARCH Pattern 4 + Postgres docs, then contract-test the DROP. Function **body** still copies `009`. |
| Classifier fail-soft adapter (no `ArticleError`) | adapter | request-response | Every existing DeepSeek path is fail-closed via `ArticleError`. Invert: return raw / raise generic; pipeline `except Exception`. Do not invent a parallel `ClassifierError` hierarchy that `map_article_error` could catch. |

Classifier **prompt prose** (D-01…D-08, named products, Diátaxis job-of-the-page, “if unsure pick practical”, JSON example `{"topic_kind": "conceptual"}`) has no in-repo twin — write new, keep it out of `ARTICLE_SYSTEM_PROMPT`.

---

## Metadata

**Analog search scope:** `data-collection/src/data_collection/` (ports, dto, adapters, assemble, fakes), `ingestion-service/src/ingestion_service/` (pipeline, collect, cli, composition, persist, errors, diagnostics), `supabase-integration/migrations/` (`001`–`013`), `tests/unit/` (audience, roles, pipeline, persister, wiring, public API, DeepSeek adapter, phase 9/11/23 migrations), `.agents/skills/supabase-postgres-best-practices/references/schema-constraints.md`
**Files scanned:** ~50 production/test files Read or Grep this session
**Pattern extraction date:** 2026-10-28
