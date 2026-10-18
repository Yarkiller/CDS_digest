# Phase 8: DeepSeek Article & Templates - Pattern Map

**Mapped:** 2026-09-27
**Files analyzed:** 32
**Analogs found:** 29 / 32

Locked decisions D-01…D-17 are copied as constraints. Discretion items below are the RESEARCH recommendations that still satisfy those locks. This map does not replace `response_format` JSON object, the D-13 reason set, the 80000-character cap, or the Russian heading strings.

## File Classification

| New/Modified/Exists File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------------|------|-----------|----------------|---------------|
| `data-collection/.../adapters/deepseek_article.py` | adapter | request-response → side-effect (SDK) | `adapters/youtube_transcript.py` + `adapters/youtube_oembed.py` (injected client, SDK/HTTP → module error) | role-match |
| `data-collection/.../errors/article.py` | error | transform (SDK → module error) | `errors/captions.py` + `errors/metadata.py` | role-match |
| `data-collection/.../templates/lecture.md` | content | transform (prompt section) | **no analog** — no package markdown in tree | none |
| `data-collection/.../templates/podcast.md` | content | transform (prompt section) | **no analog** — same | none |
| `data-collection/.../templates/__init__.py` | service (loader) | transform (files → strings) | `Settings.from_env` fail-at-load class; stdlib `importlib.resources` (not used in tree) | partial |
| `data-collection/.../tests_support/fakes.py` | test utility — **MODIFY** | request-response | same file `FakeTranscriptProvider(failures=)` | exact (extend) |
| `data-collection/pyproject.toml` | config — **MODIFY** | — | same file dependency list | exact (extend) |
| `ingestion-service/.../composition/settings.py` | config — **MODIFY** | — | same file `from_env(environ=)` | exact (extend) |
| `ingestion-service/.../composition/clients.py` | factory — **MODIFY** | side-effect (construct client) | same file `build_youtube_transcript_api` / `build_httpx_client` | exact (extend) |
| `ingestion-service/.../composition/config_error.py` | error | — (startup, not a stage) | **no analog** — do not reuse `IngestError` | none |
| `ingestion-service/.../composition/__init__.py` | config barrel — **MODIFY** | — | same file (`__all__` of Settings + factories) | exact (extend) |
| `ingestion-service/.../mapping/article.py` | service (mapper) | transform | `mapping/captions.py` (`_REASON_BY_TYPE` + allowlist) | exact |
| `ingestion-service/.../mapping/__init__.py` | config barrel — **MODIFY** | — | same file | exact (extend) |
| `ingestion-service/.../provenance.py` | constant | — | `CAPTIONS_REASONS` exact-set tests (string lock, not a builder) | partial |
| `ingestion-service/pyproject.toml` | config — **MODIFY** if factory imports `AsyncOpenAI` | — | same file workspace dep on `data-collection` | role-match |
| `tests/unit/test_ingestion_settings.py` | test — **MODIFY** | — | same file (`from_env({})` + adapter env scan) | exact (extend) |
| `tests/unit/test_article_templates.py` | test | transform | `test_template_kind.py` closed set + heading string asserts | role-match |
| `tests/unit/test_deepseek_article_adapter.py` | test | request-response | `test_youtube_oembed_adapter.py` stub client + `asyncio.run` | role-match |
| `tests/unit/test_article_error_mapping.py` | test | transform | `test_captions_error_mapping.py` | exact |
| `tests/unit/test_fake_article_generator.py` | test | request-response | `test_fake_transcript_provider_failures.py` | exact |
| `tests/unit/test_translation_marker.py` | test | — | `test_locked_reason_set_equals_d10_exactly` | role-match |
| `tests/unit/test_data_collection_public_api.py` | test — **MODIFY** | — | same file `NEGATIVE_ROOT_NAMES` | exact (extend) |
| `data-collection/.../ports/article_generator.py` | port — **EXISTS** | request-response | implement against; do not change signature | exact (reuse) |
| `data-collection/.../dto/article_draft.py` | model — **EXISTS** | transform | `model_validate`; extra keys ignored | exact (reuse) |
| `data-collection/.../dto/template_kind.py` | model — **EXISTS** | — | `lecture` \| `podcast` selects the file | exact (reuse) |
| `data-collection/.../assemble.py` | service — **EXISTS** | transform | copies caller `provenance_label`; do not invent it | exact (reuse) |
| `data-collection/.../__init__.py` | config — **EXISTS** | — | keep exactly seven names | exact (reuse) |
| `ingestion-service/.../domain/errors.py` | error — **EXISTS** | transform | `Stage` already includes `llm` and `llm_truncation` | exact (reuse) |
| `tests/unit/test_article_generator_fake.py` | test — keep green | request-response | success spy; `FakeArticleGenerator(result)` stays valid | exact (reuse) |
| `tests/unit/test_assemble_material_draft.py` | test — keep green | transform | do not weaken; no new provenance field | exact (reuse) |
| `tests/unit/test_ingest_error.py` | test — keep green | transform | seven-stage literal already locked | exact (reuse) |
| `docs/agents/local-platform-runbook.md` | docs — **MODIFY** | — | §1 YouTube env block (names and defaults only) | exact (extend) |

**Out of scope (do not touch):** Typer `--template` and label assembly (Phase 10); persist / shortlist / live `persist.calls == []` (Phase 9); new `IngestError` stage; `assemble_material_draft` behavior; `web/`; Supabase migrations; Whisper / FoundryModels; heading checks inside `body_markdown`; language detection of the reply; fence stripping; tokenizer / chunking.

---

## Pattern Assignments

### `data-collection/.../ports/article_generator.py` (port, exists — do not change)

**Analog:** the port itself (lines 1–15):

```python
class ArticleGenerator(Protocol):
    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft: ...
```

**Copy for Phase 8:** `DeepSeekArticleGenerator.process` matches this signature (D-12). Provenance is not a parameter and not a return field. The injected client, model, template strings, and `max_transcript_chars` are constructor arguments, not port fields.

`ports/__init__.py` already exports `ArticleGenerator`. Do not add the adapter to `ports/__all__` or to `data_collection.__all__`.

---

### `data-collection/.../dto/article_draft.py` + `template_kind.py` (models, exist)

**Analog:** `dto/article_draft.py` (lines 8–16) and `dto/_validators.py` (lines 4–8):

```python
class ArticleDraft(BaseModel):
    title: str = Field(min_length=1)
    dek: str = Field(min_length=1)
    body_markdown: str = Field(min_length=1)

    @field_validator("title", "dek", "body_markdown")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)
```

```python
def strip_non_blank(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("must not be blank")
    return cleaned
```

**Analog:** `dto/template_kind.py` (lines 6–8):

```python
class TemplateKind(str, Enum):
    LECTURE = "lecture"
    PODCAST = "podcast"
```

**Copy for Phase 8:**
- Parse with `json.loads`, then `ArticleDraft.model_validate`. `ValidationError` → `ArticleInvalidDraft` → `reason=invalid_article_draft` (D-11, D-13).
- The model has no `extra="forbid"`. Extra JSON keys are ignored. Do not add `provenance_label` or `prompt_version`.
- Blank or whitespace fields already fail `strip_non_blank`. Do not validate headings inside `body_markdown` (D-15).
- `TemplateKind` selects `lecture.md` or `podcast.md`. Do not add a third member.

---

### `data-collection/.../adapters/deepseek_article.py` (adapter, SDK)

**Analog (injected client, catch SDK, raise module error):** `adapters/youtube_transcript.py` (lines 48–65):

```python
class YouTubeTranscriptAdapter:
    """TranscriptProvider implementation via list-then-pick (ru → en)."""

    def __init__(self, api: Any) -> None:
        self._api = api

    async def get(self, video_id: str) -> Transcript:
        return await asyncio.to_thread(self._fetch, video_id)

    def _fetch(self, video_id: str) -> Transcript:
        try:
            return self._fetch_inner(video_id)
        except CaptionsError:
            raise
        except TranscriptsDisabled as exc:
            raise CaptionsDisabled(
                video_id, exception_class=_exception_class(exc)
            ) from exc
```

**Analog (JSON that is not an object / decode failure):** `adapters/youtube_oembed.py` (lines 29–33, 68–76):

```python
class YouTubeOEmbedAdapter:
    def __init__(self, client: Any) -> None:
        self._client = client
```

```python
        try:
            payload = response.json()
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            raise MetadataInvalidResponse(
                video_id, exception_class=_exception_class(exc)
            ) from exc

        if not isinstance(payload, dict):
            raise MetadataInvalidResponse(video_id)
```

**Analog (env scan already covers every adapter file):** `tests/unit/test_ingestion_settings.py` (lines 99–108):

```python
def test_adapters_do_not_read_environ() -> None:
    adapter_root = (
        REPO_ROOT / "data-collection" / "src" / "data_collection" / "adapters"
    )
    for path in adapter_root.glob("*.py"):
        if path.name == "__init__.py":
            continue
        body = path.read_text(encoding="utf-8")
        assert "os.environ" not in body, path.name
        assert "os.getenv" not in body, path.name
```

**Copy for Phase 8:**
- `DeepSeekArticleGenerator(client, model, templates, max_transcript_chars)`. No `os.environ`. The port is already async: `await client.chat.completions.create(...)`. Do not wrap a sync client in `asyncio.to_thread` (that was only for the sync YouTube SDK).
- First line of `process`: `if len(transcript.text) > max_transcript_chars: raise ArticleBudgetError(...)`. Do not call `create`. Template text and the system prompt do not count (D-08). `len == max_chars` still calls the SDK.
- Request: `response_format={"type": "json_object"}`. Then `json.loads` on `message.content` only. Fences and surrounding prose are `invalid_json`. Do not strip fences and do not extract the first `{...}` (D-11).
- Shared system prompt (same for both templates, D-14): honesty, always Russian, `ru` format-only, `en` translate, preserve terms/names/numbers/units, one JSON object with `title` / `dek` / `body_markdown`. The word `json` must appear. User message carries the chosen template markdown, `transcript.language`, and `transcript.text` unchanged.
- Thinking disabled and `max_retries=0` are set on the **client factory**, not by reading env in the adapter (see clients section).
- `adapters/__init__.py` is a one-line docstring today. YouTube adapters are imported by module path. Do not re-export `DeepSeekArticleGenerator` from a barrel.

**SDK → subtype (reasons are locked; subtype names follow the captions split):**

| Condition | Subtype | Mapped reason |
|-----------|---------|---------------|
| `len(text) > max_chars` before `create` | `ArticleBudgetError` | `llm_truncation` / `transcript_too_long` |
| timeout, DNS, connection refused | `ArticleNetworkError` | `network_error` |
| HTTP 429 and 5xx | `ArticleProviderError` | `provider_error` |
| HTTP 401 and 403 | `ArticleAuthError` | `auth_error` |
| HTTP 400 whose code token is context length | `ArticleContextLengthError` | `provider_context_length` |
| `json.loads` fails, content missing/non-str, JSON not an object | `ArticleInvalidJson` | `invalid_json` |
| `ArticleDraft` validation fails | `ArticleInvalidDraft` | `invalid_article_draft` |
| anything else, including HTTP 402 | `ArticleUnknownError` | `unknown_llm_error` |

Classify with `status_code` and `code`. Do not put `str(exc)`, `exc.body`, or the transcript into the exception message or context (captions CR-01). SDK class names stay out of `reason` (D-13). Empty `content` is `invalid_json`; do not read `reasoning_content`. HTTP 200 `finish_reason="length"` is not `provider_context_length`.

---

### `data-collection/.../errors/article.py` (error, transform)

**Analog:** `errors/captions.py` (lines 8–16) and `errors/metadata.py` (lines 8–16):

```python
class CaptionsError(Exception):
    """Base captions failure at the adapter boundary."""

    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"captions error for {video_id}")
```

`errors/__init__.py` is a one-line docstring. Captions and metadata types are imported from their modules (`from data_collection.errors.captions import CaptionsError`). Do the same for `ArticleError`. Do not export it from the package root.

**Copy for Phase 8:**
- Base `ArticleError` plus the subtypes in the table above. `data-collection` must not import `IngestError`.
- `ArticleBudgetError` context holds only `char_count` and `max_chars` (D-09). No transcript text.
- Other subtypes may carry `video_id`, `exception_class`, `status_code`. Never `transcript`, `body`, `response`, `prompt`, or the API key.
- `TemplateLoadError` is a startup failure, not an `ArticleError` mapped to a stage (D-17). See the loader section.

---

### `data-collection/.../templates/` (content + loader)

**No in-repo markdown package.** Closest fail-at-load shape is `Settings.from_env` rejecting a bad value before any video (see settings). File names come from the existing enum:

```python
class TemplateKind(str, Enum):
    LECTURE = "lecture"
    PODCAST = "podcast"
```

**Copy for Phase 8 (D-16, D-17):**
- `lecture.md` contains `## Тезис`, `## Ход рассуждения`, `## Вывод` unchanged.
- `podcast.md` contains `## О чём разговор`, `## Позиции`, `## Что запомнить` unchanged.
- Instructions around the headings may be English. One shared system prompt lives in the adapter, not as a third template voice (D-14).
- `load_article_templates(root)` iterates `TemplateKind`, reads `{kind.value}.md` as UTF-8, and raises `TemplateLoadError` if a file is missing or `read_text` raises `OSError`. Production root: `importlib.resources.files("data_collection.templates")`. Tests pass `tmp_path`. On Windows, mock `read_text` for the unreadable case; do not `chmod`.
- Composition calls the loader while building the generator, before any video id. Do not `open()` inside `process`.
- `TemplateLoadError` is the same class of failure as a bad `MAX_TRANSCRIPT_CHARS`: not an `IngestError` stage.
- `uv_build` has no `source-include` / package-data analog in this repo. During execution, confirm a wheel still contains both markdown files, or set the build-backend include. Source-tree `uv run pytest` is the gate.

---

### `ingestion-service/.../composition/settings.py` (config, extend)

**Analog:** `composition/settings.py` (lines 9–20):

```python
@dataclass(frozen=True)
class Settings:
    youtube_proxy_url: str | None = None

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        raw = env.get("YOUTUBE_PROXY_URL")
        if raw is None:
            return cls(youtube_proxy_url=None)
        stripped = raw.strip()
        return cls(youtube_proxy_url=stripped or None)
```

`from_env({})` is already a passing test (`test_ingestion_settings.py` lines 22–26). New fields must keep that green.

**Copy for Phase 8 (D-07):**

| Env | Unset or blank | Invalid |
|-----|----------------|---------|
| `MAX_TRANSCRIPT_CHARS` | `80000` | non-integer, `0`, negative → `ConfigurationError` at `from_env` |
| `DEEPSEEK_API_KEY` | `None` on the dataclass | rejected in `build_async_deepseek_client`, not in `from_env` |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | stripped value as-is |
| `DEEPSEEK_MODEL` | `deepseek-flash` | stripped value as-is |

Parse the cap with `int` after `strip`. Do not use `float`. A bad cap is a config error, not `stage=llm_truncation`. Keep `youtube_proxy_url` behavior unchanged. Do not require the API key inside `from_env` (YouTube-only tests call `from_env({})`).

---

### `ingestion-service/.../composition/clients.py` + `config_error.py` (factory)

**Analog:** `composition/clients.py` (lines 11–27):

```python
_DEFAULT_TIMEOUT = 30.0


def build_youtube_transcript_api(settings: Settings) -> YouTubeTranscriptApi:
    proxy = settings.youtube_proxy_url
    if proxy:
        return YouTubeTranscriptApi(
            proxy_config=GenericProxyConfig(http_url=proxy, https_url=proxy)
        )
    return YouTubeTranscriptApi()


def build_httpx_client(settings: Settings) -> httpx.AsyncClient:
    proxy = settings.youtube_proxy_url
    if proxy:
        return httpx.AsyncClient(proxy=proxy, timeout=_DEFAULT_TIMEOUT)
    return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)
```

**Analog barrel:** `composition/__init__.py` (lines 4–13) re-exports `Settings` and the two builders. Add the DeepSeek builder the same way.

**Copy for Phase 8:**
- Factory takes plain strings from `Settings`. It does not call `os.environ`.
- `AsyncOpenAI(api_key=..., base_url=..., timeout=..., max_retries=0)`. Do not leave the SDK defaults (10-minute timeout, 2 retries).
- Blank or missing `DEEPSEEK_API_KEY` raises `ConfigurationError` here. The error must not echo the key.
- DeepSeek must not reuse `YOUTUBE_PROXY_URL`. If the SDK HTTP client honors `HTTP_PROXY`, construct it with `trust_env=False`.
- `ConfigurationError` has **no analog**. Do not subclass `IngestError` and do not add a stage (D-17). A plain `Exception` in `composition/config_error.py` matches “fail when settings/client load, before any video.”
- If `clients.py` imports `AsyncOpenAI`, declare `openai` on `ingestion-service` as well as `data-collection` (the adapter needs the exception types; the factory needs the client class).

`data-collection/pyproject.toml` dependencies today (lines 6–11) are pydantic, `youtube-transcript-api`, and httpx/requests. Add with `uv add --package data-collection "openai>=3.0,<4"`. Do not pip-install. Do not import `httpx2` in app code.

---

### `ingestion-service/.../mapping/article.py` (mapper, transform)

**Analog:** `mapping/captions.py` (lines 20–72):

```python
CAPTIONS_REASONS: frozenset[str] = frozenset(
    {
        "no_captions",
        "no_preferred_language",
        "captions_disabled",
        "video_unavailable",
        "youtube_blocked",
        "bot_challenge",
        "network_error",
        "empty_captions",
        "unknown_captions_error",
    }
)

_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "available_languages",
        "exception_class",
    }
)

def map_captions_error(error: CaptionsError) -> IngestError:
    reason = _REASON_BY_TYPE.get(type(error), "unknown_captions_error")
    return IngestError(
        stage="captions",
        reason=reason,
        message=f"captions {reason} for {error.video_id}",
        context=_forward_context(error),
    )
```

Metadata’s allowlist (`mapping/metadata.py` lines 23–28) is the closer key set for `stage=llm`: `video_id`, `status_code`, `exception_class`.

**Copy for Phase 8:**
- `ArticleBudgetError` → `IngestError(stage="llm_truncation", reason="transcript_too_long", context={char_count, max_chars})`. Those two keys only. No `video_id` (D-09). This is stricter than the captions mapper, which always forwards `video_id`.
- Every other `ArticleError` → `stage="llm"` and a D-13 reason: `network_error`, `provider_error`, `auth_error`, `invalid_json`, `invalid_article_draft`, `provider_context_length`, `unknown_llm_error`.
- Message is English and contains the reason. Build it from the reason, not from `str(exc)`. Do not copy transcript text or a response body.
- Export `LLM_REASONS` (or equivalent) the way `CAPTIONS_REASONS` is exported, and re-export `map_article_error` from `mapping/__init__.py` next to the three existing mappers.
- `domain/errors.py` `Stage` already lists `"llm"` and `"llm_truncation"` (`errors.py` lines 7–16). Do not add a member. `test_ingest_error.py` asserts that exact seven-stage set.

---

### `ingestion-service/.../provenance.py` (constant only)

**No label-builder analog.** The assembler already copies a caller string (`assemble.py` lines 10–24):

```python
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
    )
```

**Copy for Phase 8 (D-05, D-06):** one constant:

```python
ENGLISH_TRANSLATION_SUFFIX = " · пер. с англ."
```

Unit-test that exact string (leading space, middot, trailing period). Do not implement `f"YouTube · {metadata.author}"`. Do not append the suffix inside the adapter. Do not change `assemble_material_draft`. Phase 10 builds the full label and appends the suffix when `transcript.language != "ru"`.

---

### `data-collection/.../tests_support/fakes.py` (extend, do not replace)

**Analog:** `FakeTranscriptProvider` (lines 20–34) next to the success-only `FakeArticleGenerator` (lines 54–63):

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

```python
class FakeArticleGenerator:
    def __init__(self, result: ArticleDraft) -> None:
        self._result = result
        self.calls: list[ArticleGeneratorCall] = []

    async def process(
        self, transcript: Transcript, template: TemplateKind
    ) -> ArticleDraft:
        self.calls.append({"transcript": transcript, "template": template})
        return self._result
```

**Copy for Phase 8:** add optional `failures: dict[str, ArticleError] | None = None`, keyed by `transcript.video_id`. Append to `calls`, then raise, then return `self._result`. `FakeArticleGenerator(result)` and the existing spy test (`test_article_generator_fake.py`) stay valid. Do not export the fake from `data_collection.__all__`.

---

### Tests (TDD shape)

**Public barrel stay-seven** (`test_data_collection_public_api.py` lines 8–38, 75–85):

```python
PUBLIC_NAMES = frozenset(
    {
        "Transcript",
        "VideoMetadata",
        "MaterialDraft",
        "TemplateKind",
        "TranscriptProvider",
        "ArticleGenerator",
        "VideoMetadataProvider",
    }
)

NEGATIVE_ROOT_NAMES = (
    "ArticleDraft",
    "FakeTranscriptProvider",
    "FakeArticleGenerator",
    # ...
    "CaptionsError",
    "MetadataError",
    "YouTubeTranscriptAdapter",
    "YouTubeOEmbedAdapter",
)
```

Add `DeepSeekArticleGenerator` and `ArticleError` to `NEGATIVE_ROOT_NAMES`. Keep `len(__all__) == 7`. `test_error_bases_importable_from_errors_submodules` may grow an `ArticleError` import from `data_collection.errors.article` the way it already imports `CaptionsError` and `MetadataError` (lines 88–94).

**Stub client + `asyncio.run`** (`test_youtube_oembed_adapter.py` lines 41–68): a tiny object records the call and returns a scripted payload. The DeepSeek stub records `chat.completions.create` kwargs and returns `choices[0].message.content` as a string. Do not add `pytest-asyncio`.

**Mapping redaction** (`test_captions_error_mapping.py` lines 110–131): assert the secret is absent from `context`, `message`, and `to_dict()["message"]`, not only from `context`.

**Additive fake** (`test_fake_transcript_provider_failures.py` lines 23–47): mapped id raises the scripted error and records the call; another id still returns the scripted success; positional construction still works.

**Prompt asserts (D-04, D-15, D-16):** lecture messages contain the three lecture headings and not `## О чём разговор`; podcast contains the three podcast headings; both contain honesty / always-Russian / preserve-terms and the word `json`. Scripted JSON that still contains `pgvector`, `RAG`, and `embedding` round-trips onto `ArticleDraft`. Do not language-detect the reply.

---

### `docs/agents/local-platform-runbook.md` (docs, extend §1)

**Analog:** §1 item 4 (lines 28–35):

```markdown
4. Optional **YouTube ingestion** vars (Phase 7 captions/oEmbed — composition only, never adapters):
   - `YOUTUBE_PROXY_URL` — optional SOCKS/HTTP proxy ...
   - Never put the full `YOUTUBE_PROXY_URL` ... into logs or `IngestError.context`.
```

**Copy for Phase 8:** document names and defaults only: `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL` (`https://api.deepseek.com`), `DEEPSEEK_MODEL` (`deepseek-flash`), `MAX_TRANSCRIPT_CHARS` (`80000`). State that adapters do not read these. Do not commit a key. Do not put the key behind `VITE_`. Live draft quality stays Phase 10 UAT. Default `uv run pytest` stays unit-only (runbook §5c).

---

## Shared Patterns

### Ports & Adapters

| Rule | Phase 8 implication |
|------|---------------------|
| External SDK in `data-collection` | `openai` only in the adapter (exception types) and the composition factory (client) |
| Composition owns env | `Settings.from_env` + `build_async_deepseek_client` |
| No SDK in domain | Mapper and `IngestError` only; adapter raises `ArticleError` |
| Public barrel | Stay at seven names; fakes, `ArticleDraft`, adapter, `ArticleError` stay private |
| Fail closed | No partial `ArticleDraft`; no silent truncation; no fence salvage |
| LLM-03 this phase | Unit proof that no draft is returned. Live zero-row spy is Phase 9 |

**Anti-patterns to reject in plans:**
- Adapter calls `os.environ` / `os.getenv`
- `reason` equal to an SDK class name (`APIConnectionError`, …)
- `stage=` or `IngestError` inside `data-collection`
- New stage for templates or bad `MAX_TRANSCRIPT_CHARS`
- Stripping ``` fences or regex-extracting `{...}`
- `str(exc)` / `exc.body` in `message` or `context`
- Counting template or system-prompt characters toward the cap
- Heading validation of `body_markdown`
- Language detection of the reply
- `provenance_label` in the JSON or the adapter
- Building `YouTube · {author}` in this phase
- Exporting the adapter, `ArticleError`, or fakes from `__all__`
- Typer, Supabase writes, migrations, Whisper, FoundryModels
- Leaving SDK `timeout` / `max_retries` at library defaults
- Requiring `DEEPSEEK_API_KEY` inside `Settings.from_env`
- `chat.completions.parse` or the Responses API
- Mining `reasoning_content` when `content` is empty

---

## TDD Notes

Aligned with `.cursor/rules/tdd.mdc` / `AGENTS.md`:

> **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

| Order | Action |
|-------|--------|
| 1 | RED: settings cap, template headings + missing file, mocked adapter, mapping allowlists, fake failures, suffix constant, public-API negatives |
| 2 | `uv run pytest tests/unit/test_<name>.py -x` — expect ImportError / AssertionError |
| 3 | `uv add --package data-collection "openai>=3.0,<4"` when tests first import `openai`, then minimal production |
| 4 | Keep `test_article_generator_fake.py`, `test_assemble_material_draft.py`, `test_ingest_error.py` green |
| 5 | Full `uv run pytest` (unit only) before the phase gate |

**Suggested RED files first (from RESEARCH Test Map / Wave 0):**
- Extend `test_ingestion_settings.py` — unset/blank cap → `80000`; `0`, negative, non-integer → `ConfigurationError`; `from_env({})` still works; key stays optional on the dataclass
- `test_article_templates.py` — D-16 headings in the real package files; missing file raises before any client call
- `test_deepseek_article_adapter.py` — mocked JSON → `ArticleDraft`; prompt rules; `ru`/`en` passthrough; preserved tokens; fence → `invalid_json`; `len == 80000` calls `create`; `80001` does not
- `test_article_error_mapping.py` — D-13 reasons, truncation context exactly `{char_count, max_chars}`, message redaction on `message` and `to_dict()`
- `test_fake_article_generator.py` — additive `failures`; success path unchanged
- `test_translation_marker.py` — exact ` · пер. с англ.`
- Extend `test_data_collection_public_api.py` negatives

**Async harness:** `asyncio.run(...)` in sync pytest. Do not add `pytest-asyncio`.

**Unit layer constraints:** no network, no DB, no migrations, no Playwright. Optional live DeepSeek is not the phase gate.

---

## Cross-Cutting Patterns

### Protocol + real adapter (injected client)
**Source:** `ArticleGenerator` + `YouTubeTranscriptAdapter` / `YouTubeOEmbedAdapter`
**Apply to:** `DeepSeekArticleGenerator`; composition builds `AsyncOpenAI`.

### Module-local error → operator envelope
**Source:** `CaptionsError` → `map_captions_error` → `IngestError.to_dict`
**Apply to:** `ArticleError` → `map_article_error`. Local cap uses `stage=llm_truncation`; provider rejection uses `stage=llm` / `provider_context_length` (D-10).

### Settings.from_env(environ=)
**Source:** `ingestion_service.composition.settings.Settings`
**Apply to:** `MAX_TRANSCRIPT_CHARS` and `DEEPSEEK_*` with defaults so `from_env({})` stays valid.

### Additive fake failure catalog
**Source:** `FakeTranscriptProvider(failures=)`
**Apply to:** `FakeArticleGenerator`; key is `video_id`.

### Public API barrel freeze
**Source:** `data_collection/__init__.py` + `test_public_all_is_exactly_seven_ingestion_names`
**Apply to:** do not publish the adapter, `ArticleDraft`, or `ArticleError`.

### Secret-safe diagnostics
**Source:** captions mapper message built from `reason`; redaction test checks `to_dict()["message"]`
**Apply to:** English `llm {reason}` / `llm_truncation transcript_too_long`. No transcript, no API key.

### Startup failure vs pipeline stage
**Source:** invalid config is outside `IngestError.Stage` (D-17)
**Apply to:** `ConfigurationError` and `TemplateLoadError` before any video and before any DeepSeek call.

---

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| `templates/lecture.md`, `templates/podcast.md` | content | transform | No repository markdown package. Invent two files whose heading strings are the D-16 literals. |
| `composition/config_error.py` (`ConfigurationError`) | error | — | No startup-config exception. Do not reuse `IngestError` (that would add a stage or mis-label a bad int as `llm_truncation`). |
| `TemplateLoadError` | error | — | Same gap. Raise from the loader; do not map it in `mapping/article.py`. |
| Wheel include for non-Python templates | config | — | No `source-include` / package-data key in member `pyproject.toml` files. Confirm during execution. |
| `provenance.py` suffix constant | constant | — | No label helper. Lock the suffix string only; the assembler already copies a caller label. |

---

## Metadata

**Analog search scope:** `data-collection/src/data_collection/{ports,dto,adapters,errors,assemble,tests_support,__init__}`, `ingestion-service/src/ingestion_service/{composition,mapping,domain}`, `tests/unit/test_{article_generator_fake,article_draft_internal,template_kind,captions_error_mapping,fake_transcript_provider_failures,ingestion_settings,data_collection_public_api,ingest_error,youtube_oembed_adapter,youtube_transcript_adapter}.py`, `data-collection/pyproject.toml`, `ingestion-service/pyproject.toml`, `docs/agents/local-platform-runbook.md`
**Files scanned:** 32 planned create/modify/reuse files plus the live analogs above
**Pattern extraction date:** 2026-09-27

**Locked (do not reopen):** always Russian (D-01); `ru` format-only / `en` translate with terms preserved (D-02, D-04); no reply language detector (D-03); suffix constant only, Phase 10 builds the label (D-05, D-06); cap is `len(transcript.text)` default `80000`, env `MAX_TRANSCRIPT_CHARS`, bad int fails at settings load (D-07); over cap → `llm_truncation` / `transcript_too_long` with only `char_count` and `max_chars` (D-08, D-09); provider context rejection is `stage=llm` / `provider_context_length` (D-10); one JSON object via `response_format` `json_object` then `json.loads` then `ArticleDraft` (D-11); `process` returns `ArticleDraft` only (D-12); D-13 reason set; templates differ by outline only (D-14); no heading validator (D-15); Russian heading strings (D-16); missing template fails at load, no new stage (D-17).

**Discretion recorded from RESEARCH (still inside the locks):** templates under `data_collection/templates/`; char-cap check inside the adapter on an injected int; `ArticleError` subtype names; `ConfigurationError` / `TemplateLoadError` as non-`IngestError` startup errors; `timeout` explicit and `max_retries=0`; thinking disabled via `extra_body`; `stage=llm` context keys `video_id`, `exception_class`, `status_code`; English messages that include the reason and exclude the transcript.

## PATTERN MAPPING COMPLETE
