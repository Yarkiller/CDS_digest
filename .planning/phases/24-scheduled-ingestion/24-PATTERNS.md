# Phase 24: Scheduled ingestion - Pattern Map

**Mapped:** 2026-10-18
**Files analyzed:** 43 (29 новых + 14 изменяемых/расширяемых)
**Analogs found:** 40 / 43 (3 файла без аналога — все systemd-юниты; ещё 4 — только `partial`: `domain/schedule.py`, guard-тест, тест адаптера фида)

Источник списка файлов: `24-CONTEXT.md` (D-01…D-26) + `24-RESEARCH.md` `## Recommendations for Planning` (T1…T15) и `### Recommended Project Structure`.

> Все аналоги ниже — **git-tracked** файлы (`git ls-files` проверено в этой сессии). Каталога `deploy/` в репозитории нет (`git ls-files -- deploy/` пуст) — юниты создаются с нуля.

---

## File Classification

### `data-collection` (T1, T2)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `data-collection/src/data_collection/dto/video_ref.py` | DTO | transform | `data-collection/src/data_collection/dto/video_metadata.py` | role-match (pydantic vs frozen dataclass) |
| `data-collection/src/data_collection/ports/video_list_provider.py` | port | request-response (async) | `data-collection/src/data_collection/ports/video_metadata_provider.py` | exact |
| `data-collection/src/data_collection/adapters/youtube_feed.py` | adapter | streaming + transform | `data-collection/src/data_collection/adapters/youtube_oembed.py` | exact (роль + async httpx), отличается только stream/cap |
| `data-collection/src/data_collection/errors/feed.py` | errors | — | `data-collection/src/data_collection/errors/metadata.py` | exact |
| `data-collection/src/data_collection/__init__.py` | barrel (**AMEND**) | — | сам файл | exact |

### `ingestion-service` (T3…T7)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `ingestion-service/src/ingestion_service/domain/schedule.py` | domain | transform (pure) | `ingestion-service/src/ingestion_service/domain/errors.py` + `application/ports/diagnostics.py` (`Clock`) | partial |
| `ingestion-service/src/ingestion_service/application/ports/collect_sources.py` | port | CRUD (read + conditional update) | `ingestion-service/src/ingestion_service/application/ports/persist.py` | role-match |
| `ingestion-service/src/ingestion_service/adapters/supabase_collect_sources.py` | adapter | CRUD | `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` + `supabase-integration/src/supabase_integration/pipeline_config_repository.py` | exact (client-in-ctor) + role-match (таблица/`_parse_dt`) |
| `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py` | use-case | batch | `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` | exact (вызывает его же) |
| `ingestion-service/src/ingestion_service/collect_cli.py` | CLI entry | request-response | `ingestion-service/src/ingestion_service/cli.py` | exact |
| `ingestion-service/src/ingestion_service/composition/settings.py` (**AMEND**) | config | — | сам файл (`_max_transcript_chars`) | exact |
| `ingestion-service/src/ingestion_service/composition/clients.py` (**AMEND**) | composition | — | сам файл (`build_httpx_client`) | exact |
| `ingestion-service/pyproject.toml` (**AMEND**) | config | — | сам файл (`[project.scripts]`) | exact |
| `ingestion-service/.env.example` (**AMEND**) | config | — | сам файл | exact |

### `backend` (T9, T10)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `backend/src/backend/domain/ingestion_schedule.py` | domain | transform | `backend/src/backend/domain/pipeline_config.py` | exact |
| `backend/src/backend/application/ports/ingestion_schedule.py` | port | CRUD | `backend/src/backend/application/ports/pipeline_config.py` | exact |
| `backend/src/backend/application/use_cases/ingestion_schedule.py` | use-case | CRUD (validate-then-persist) | `backend/src/backend/application/use_cases/pipeline_config.py` + `use_cases/ingest_sources.py` | role-match (валидация/нормализация) |
| `backend/src/backend/interface/http/routes/admin.py` (**AMEND**) | controller | request-response | сам файл (`put_pipeline_config`, `_require_*`) | exact |
| `backend/src/backend/composition/container.py` (**AMEND**) | composition | — | сам файл (`ingest_sources: … | None = None`) | exact |
| `backend/src/backend/composition/live.py` (**AMEND**) | composition | — | сам файл (`ingest_sources=SupabaseIngestSourceRepository(...)`) | exact |
| `backend/src/backend/tests_support/in_memory.py` (**AMEND**) | fake | CRUD | `InMemoryIngestSourceRepository` в том же файле | exact |

### `supabase-integration` (T8, T10)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql` | migration | DDL | `migrations/011_phase16_pipeline_config.sql` (singleton) + `migrations/012_phase23_ingest_sources.sql` (alter-совместимая таблица) | exact |
| `supabase-integration/src/supabase_integration/ingestion_schedule_repository.py` | adapter | CRUD singleton | `pipeline_config_repository.py` | exact |
| `supabase-integration/src/supabase_integration/__init__.py` (**AMEND**) | barrel | — | сам файл | exact |

### `web` (T11, T12)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `web/src/services/ingestScheduleApi.js` | service | request-response (mock+live) | `web/src/services/ingestSourcesApi.js` | exact |
| `web/src/components/IngestionScheduleSection.jsx` | component | event-driven (немедленный PATCH) | `web/src/components/IngestSourcesSection.jsx` | exact |
| `web/src/pages/AdminPipelineConfigPage.jsx` (**AMEND**) | page | orchestration | сам файл (точка вставки `:234-249`) | exact |
| `web/src/main.jsx` (**AMEND**) | harness | — | сам файл (`__DIGEST_INGEST_SOURCES_HARNESS__`) | exact |

### `deploy/systemd` (T13)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `deploy/systemd/digest-ingest.service` | config (ops) | event-driven (oneshot) | — | **none** |
| `deploy/systemd/digest-ingest.timer` | config (ops) | event-driven | — | **none** |
| `deploy/systemd/digest-ingest-alert.service` | config (ops) | event-driven | — | **none** |

### `tests` / docs (T14, T15 + Wave 0)

| New/Modified File | Роль | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tests/unit/test_youtube_feed_adapter.py` | test | — | `tests/unit/test_http_ingest_sources.py` (стиль RED) / нет прямого аналога адаптер-теста с `MockTransport` | partial |
| `tests/unit/test_schedule_due.py` | test | — | `tests/unit/test_cli_ingest_contract.py` (чистые ассерты) | partial |
| `tests/unit/test_collect_batch.py` | test | — | `tests/unit/test_ingest_pipeline.py` + `ingestion_service/tests_support/fakes.py` | role-match |
| `tests/unit/test_collect_cli_contract.py` | test | — | `tests/unit/test_cli_ingest_contract.py` | exact |
| `tests/unit/test_supabase_collect_sources_contract.py` | test | — | `tests/unit/test_supabase_ingest_source_repository_contract.py` | exact |
| `tests/unit/test_phase24_migration_013.py` | test (text-contract) | — | `tests/unit/test_phase23_migration_012.py` | exact |
| `tests/unit/test_phase24_systemd_units.py` | test (text-contract) | — | `tests/unit/test_phase16_migration_011.py` | role-match (тот же приём, другой артефакт) |
| `tests/unit/test_phase24_scheduler_guard.py` | test (static+runtime) | — | `tests/unit/test_data_collection_public_api.py` (rglob + текстовые ассерты) | partial |
| `tests/unit/test_http_ingestion_schedule.py` | test | — | `tests/unit/test_http_ingest_sources.py` | exact |
| `tests/unit/test_ingestion_schedule_domain.py` | test | — | `tests/unit/test_http_ingest_sources.py` (доменные ассерты) | role-match |
| `tests/admin.spec.js` (**AMEND**, новый describe) | test | — | сам файл (`resetIngestSourcesMock` + `test.describe`) | exact |
| `docs/agents/local-platform-runbook.md` (**AMEND** §4j/§5e) | docs | — | сам файл (§4i, §5d) | exact |

---

## Pattern Assignments

### 1. `data-collection/src/data_collection/adapters/youtube_feed.py` (adapter, streaming + transform)

**Analog:** `data-collection/src/data_collection/adapters/youtube_oembed.py`

**Импорты и форма класса** (`:1-31`):

```python
"""YouTube oEmbed adapter — injected httpx client (D-21…D-23, D-17)."""

from __future__ import annotations

import json
from typing import Any

import httpx

from data_collection.dto.video_metadata import VideoMetadata
from data_collection.errors.metadata import (
    MetadataError,
    MetadataInvalidResponse,
    MetadataNetworkError,
    MetadataUnavailable,
)

_OEMBED_ENDPOINT = "https://www.youtube.com/oembed"

def _canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"

def _exception_class(exc: BaseException) -> str:
    return type(exc).__name__

class YouTubeOEmbedAdapter:
    """VideoMetadataProvider via YouTube oEmbed; builds canonical URL itself."""

    def __init__(self, client: Any) -> None:
        self._client = client
```

**Маппинг ошибок на границе** (`:33-60`) — копировать ровно этот порядок `except`-ветвей (`свой FeedError → Timeout/Network → HTTPError`):

```python
    async def get(self, video_id: str) -> VideoMetadata:
        canonical = _canonical_watch_url(video_id)
        try:
            response = await self._client.get(
                _OEMBED_ENDPOINT,
                params={"url": canonical, "format": "json"},
            )
        except MetadataError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise MetadataNetworkError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
        except httpx.HTTPError as exc:
            raise MetadataNetworkError(
                video_id, exception_class=_exception_class(exc)
            ) from exc
```

Что **не** копировать: `.get(...)` (тело целиком в память — ломает D-26). Вместо него — `async with self._client.stream("GET", _FEED_ENDPOINT, params=...)` + `aiter_bytes()` + cap 1 MiB из RESEARCH §1.4. Сигнатура клиента — `httpx.AsyncClient` (см. `build_httpx_client` ниже), порт листинга **обязан** быть `async def`.

---

### 2. `data-collection/src/data_collection/errors/feed.py` (errors)

**Analog:** `data-collection/src/data_collection/errors/metadata.py` — целиком (26 строк):

```python
"""Metadata adapter errors — module-local taxonomy only (D-11, D-25)."""

from __future__ import annotations

from typing import Any

class MetadataError(Exception):
    """Base metadata failure at the adapter boundary."""

    def __init__(self, video_id: str, **context: Any) -> None:
        self.video_id = video_id
        self.context = context
        for key, value in context.items():
            setattr(self, key, value)
        super().__init__(f"metadata error for {video_id}")

class MetadataUnavailable(MetadataError):
    """oEmbed returned 404/403 or the resource is blocked."""
```

Копировать: базовый класс принимает идентификатор позиционно и произвольный `**context`, каждое поле контекста выставляется атрибутом (на это опирается диагностика/тесты). Для `FeedError` — `source_id` позиционно + `reason: str` (D-25: `feed_status`, `feed_network`, `feed_invalid_xml`, `feed_too_large`, `feed_doctype`, `unsupported_kind`).

---

### 3. `data-collection/src/data_collection/ports/video_list_provider.py` (port, async)

**Analog:** `data-collection/src/data_collection/ports/video_metadata_provider.py` — целиком:

```python
"""VideoMetadataProvider port — provenance by video_id (D-21, D-22)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.video_metadata import VideoMetadata

class VideoMetadataProvider(Protocol):
    async def get(self, video_id: str) -> VideoMetadata: ...
```

Копировать: `from __future__ import annotations`, `typing.Protocol` (не `abc.ABC`), `async def`, docstring с requirement-id, DTO из `data_collection.dto.*`. Никаких `Any`.

---

### 4. `data-collection/src/data_collection/dto/video_ref.py` (DTO, transform)

**Analog (форма валидации):** `data-collection/src/data_collection/dto/video_metadata.py`

```python
class VideoMetadata(BaseModel):
    video_id: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    author: str = Field(min_length=1)
    published_at: datetime | None = None

    @field_validator("video_id", "source_url", "author")
    @classmethod
    def _strip_non_blank(cls, value: str) -> str:
        return strip_non_blank(value)

    @field_validator("published_at")
    @classmethod
    def _require_aware(self, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        return value
```

Копировать **инвариант tz-aware**, но не pydantic: RESEARCH §1.3 задаёт `@dataclass(frozen=True)` для `VideoRef` / `FeedSkip` / `FeedListing` (адаптер — не граница пользовательского ввода; pydantic здесь даст лишние исключения на отбраковке). Валидация `video_id` — локальный `re.compile(r"^[A-Za-z0-9_-]{11}$")`, а не pydantic-валидатор.

---

### 5. `data-collection/src/data_collection/__init__.py` (AMEND)

**Analog:** сам файл (`:1-20`):

```python
"""Public API for data-collection ingestion contracts (D-01, D-04, D-21)."""

from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from data_collection.ports.video_metadata_provider import VideoMetadataProvider

__all__ = [
    "Transcript",
    "VideoMetadata",
    "MaterialDraft",
    "TemplateKind",
    "TranscriptProvider",
    "ArticleGenerator",
    "VideoMetadataProvider",
]
```

AMEND аддитивно: `VideoRef`, `VideoListProvider` (+ `FeedListing`/`FeedSkip`, если решено их экспортировать). Адаптер `YouTubeFeedAdapter` и `FeedError` **не** попадают в root `__all__` — они в `NEGATIVE_ROOT_NAMES`-логике (`tests/unit/test_data_collection_public_api.py:23-42`).

Обязательно **не забыть** `data_collection/ports/__init__.py` (barrel портов) — он держит свой `__all__` из трёх имён (`ports/__init__.py:5`), а тест `test_ports_package_exports_both_provider_protocols` (`:59`) читает именно его.

---

### 6. `ingestion-service/src/ingestion_service/composition/settings.py` (AMEND: `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE`)

**Analog:** сам файл, `_max_transcript_chars` (`:16-28`) — точный шаблон fail-loud чтения positive int:

```python
def _max_transcript_chars(env: dict[str, str]) -> int:
    raw = env.get("MAX_TRANSCRIPT_CHARS")
    if raw is None or raw.strip() == "":
        return _DEFAULT_MAX_TRANSCRIPT_CHARS
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigurationError(
            "MAX_TRANSCRIPT_CHARS must be a positive integer"
        ) from exc
    if value <= 0:
        raise ConfigurationError("MAX_TRANSCRIPT_CHARS must be a positive integer")
    return value
```

И `Settings` + `from_env` (`:51-89`):

```python
@dataclass(frozen=True)
class Settings:
    youtube_proxy_url: str | None = None
    max_transcript_chars: int = _DEFAULT_MAX_TRANSCRIPT_CHARS
    deepseek_api_key: str | None = field(default=None, repr=False)
    ...
    shortlist_batch_size: int = _DEFAULT_SHORTLIST_BATCH_SIZE

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        ...
        return cls(
            youtube_proxy_url=proxy,
            max_transcript_chars=_max_transcript_chars(env),
            ...
            shortlist_batch_size=_shortlist_batch_size(env),
        )
```

Для `INGEST_TEMPLATE` — `TemplateKind(raw)` → `ValueError` → `ConfigurationError` (D-02, дефолт `lecture`). Секретов среди новых ключей нет → `repr=False` не нужен.

---

### 7. `ingestion-service/src/ingestion_service/composition/clients.py` (AMEND: `build_youtube_feed`, `build_collect_deps`)

**Analog:** сам файл, `build_httpx_client` (`:33-48`) и фабрики портов (`:40-48`):

```python
def build_httpx_client(settings: Settings) -> httpx.AsyncClient:
    proxy = settings.youtube_proxy_url
    if proxy:
        return httpx.AsyncClient(proxy=proxy, timeout=_DEFAULT_TIMEOUT)
    return httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT)

def build_youtube_captions(settings: Settings) -> YouTubeTranscriptAdapter:
    """Wire YouTube captions adapter from Settings (D-02; adapters never read os.environ)."""
    return YouTubeTranscriptAdapter(build_youtube_transcript_api(settings))

def build_youtube_metadata_provider(settings: Settings) -> YouTubeOEmbedAdapter:
    """Wire YouTube oEmbed metadata adapter from Settings (D-02)."""
    return YouTubeOEmbedAdapter(build_httpx_client(settings))
```

Шов: фабрика адаптера **не** читает env (это делает `Settings`), клиент инжектируется. `build_youtube_feed(settings) -> YouTubeFeedAdapter` копирует `build_youtube_metadata_provider` буквально. `build_collect_deps()` живёт в `collect_cli.py` (как `build_ingest_deps`), а не здесь — иначе `test_build_ingest_deps_wiring.py` смешается с двумя билдерами.

---

### 8. `ingestion-service/src/ingestion_service/domain/schedule.py` (domain, pure)

**Частичный аналог:** `ingestion-service/src/ingestion_service/domain/errors.py` (frozen-контракт + ноль внешних импортов) и `application/ports/diagnostics.py:16-21` (`Clock`):

```python
@runtime_checkable
class Clock(Protocol):
    def monotonic(self) -> float: ...

    def now(self) -> datetime: ...
```

И фриз-датакласс из `domain/errors.py:18-27`:

```python
@dataclass
class IngestError(Exception):
    stage: Stage
    reason: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)
    exit_code: int = 1
```

Правило слоя: **никакого `zoneinfo`, `datetime.now()`, `httpx`, `supabase`** в этом модуле. `is_due(schedule, *, now_utc, tz)` и `is_newer(...)` — чистые функции из RESEARCH §2.2/§5.3; `tzinfo` — параметр, не модульная константа (иначе `ZoneInfoNotFoundError` на Windows ломает импорт — Pitfall 24-3). `Clock` переиспользовать как есть, второй порт не заводить.

---

### 9. `ingestion-service/src/ingestion_service/application/ports/collect_sources.py` (port, CRUD)

**Analog:** `ingestion-service/src/ingestion_service/application/ports/persist.py` — целиком:

```python
"""PersistPort — application persist contract (D-01, D-03)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from data_collection.dto.material_draft import MaterialDraft

@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int
    already_saved: bool = False

@runtime_checkable
class PersistPort(Protocol):
    def persist(self, material_draft: MaterialDraft) -> PersistResult: ...
```

Копировать: порт и его DTO-результаты в одном модуле, `@runtime_checkable`, docstring с D-номерами. Методы `CollectSourceReader`: `get_schedule()`, `list_enabled_sources()`, `advance_cursor(source_pk, *, published, video_id)`, `stamp_last_run(at)` — синхронные (SDK `supabase` синхронный), в отличие от async-листинга.

---

### 10. `ingestion-service/src/ingestion_service/adapters/supabase_collect_sources.py` (adapter, CRUD)

**Analog (client-in-ctor + маппинг ошибок):** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py:28-42`:

```python
class SupabaseDraftPersister:
    """Implements PersistPort with a single named-parameter RPC call."""

    def __init__(self, client: Client, batch_size: int) -> None:
        self._client = client
        self._batch_size = batch_size

    def persist(self, material_draft: MaterialDraft) -> PersistResult:
        params = _rpc_params(material_draft, self._batch_size)
        try:
            result = self._client.rpc(_RPC_NAME, params).execute()
            return _persist_result(result.data)
        except DraftPersistError:
            raise
        except Exception as exc:
            raise _map_exception(exc, material_draft) from None
```

**Analog (идиомы таблицы/таймстампов):** `supabase-integration/src/supabase_integration/pipeline_config_repository.py:23-76` — копировать `_parse_dt`/`_iso` **буквально**:

```python
def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(text)

def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
```

```python
    def get(self) -> PipelineConfig | None:
        try:
            result = (
                self._client.table("pipeline_config")
                .select("yaml,updated_at")
                .eq("id", _CONFIG_ID)
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"pipeline_config get failed: {exc}") from exc
```

Монотонный UPDATE курсора (RESEARCH §6.4) — единственное место, где нужен не-`eq` фильтр: `.or_(...)` у PostgREST, а не Python-сравнение. Тест-аналог для захвата payload/фильтров — `tests/unit/test_supabase_ingest_source_repository_contract.py` (`_FakeQuery` записывает `_filters`/`last_update`, `:20-60`).

---

### 11. `ingestion-service/src/ingestion_service/application/use_cases/collect_batch.py` (use-case, batch)

**Analog:** `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py:32-42` — вызываемый seam:

```python
async def run_ingest_pipeline(
    url: str,
    template: TemplateKind,
    *,
    captions: TranscriptProvider,
    metadata_provider: VideoMetadataProvider,
    article: ArticleGenerator,
    persist: PersistPort,
    on_stage: OnStage | None = None,
    diagnostics: StageDiagnostics | None = None,
) -> PersistResult:
```

Три guard'а, которые делают `on_stage=None` бесшумным (`:73`, `:132`, `:158`):

```python
    if on_stage is not None:
        on_stage("transcript")
...
    if on_stage is not None:
        on_stage("llm")
...
    if on_stage is not None:
        on_stage("saved")
    return result
```

Вызов из батча (RESEARCH §3.3):

```python
result = await run_ingest_pipeline(
    video.video_id,          # голый id: extract_video_id принимает ^[A-Za-z0-9_-]{11}$
    template,
    captions=deps.captions,
    metadata_provider=deps.metadata_provider,
    article=deps.article,
    persist=deps.persist,
    on_stage=None,           # D-03: ни одного '✓ …' в stdout сводки
    diagnostics=None,
)
```

`run_ingest_pipeline`, `cli.py`, `url.py`, `persist.py` — **нулевой дифф**. Единственный seam — значение аргумента `on_stage`.

Фейки для тестов батча — `ingestion_service/tests_support/fakes.py`: `FakeDraftPersister` хранит `self.calls` / `self.stored` (`:13-48`), `FakeClock` — scripted `monotonic` + фиксированный `now` (`:51-65`). Новые фейки (`FakeFeed`, `FakeCollectSourceReader`) добавлять **в тот же файл** с той же формой: список вызовов + scripted-исключения по ключу.

---

### 12. `ingestion-service/src/ingestion_service/collect_cli.py` (CLI entry, request-response)

**Analog:** `ingestion-service/src/ingestion_service/cli.py` — целиком, но копировать **форму**, не трогая оригинал.

App + `build_*_deps` seam (`:30-49`):

```python
app = typer.Typer(add_completion=False)

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

Разделение потоков и exit codes (`:71-124`):

```python
@app.command()
def main(
    url: Annotated[str, typer.Argument(help="YouTube URL or video id")],
    template: Annotated[
        TemplateKind,
        typer.Option("--template", help="Prompt template: lecture or podcast"),
    ],
    ...
) -> None:
    ...
    except (ConfigurationError, TemplateLoadError) as err:
        # D-08/D-12: pre-video failures stay human text — never mint a new IngestError stage.
        diagnostics.config_error(error_type=type(err).__name__, message=str(err))
        typer.echo(str(err), err=True)
        raise typer.Exit(code=1) from err
    except IngestError as err:
        typer.echo(json.dumps(err.to_dict()), err=True)
        raise typer.Exit(code=err.exit_code) from err

    typer.echo(f"material_id: {result.material_id}")
```

Критично для `collect_cli.py`:
- `import typer` разрешён **только** здесь → нужен AMEND-тест (см. `### Amendment points`).
- Диагностика — только `typer.echo(..., err=True)`; сводка — `typer.echo(...)` без `err`.
- `typer.Exit(code=0|1|2)` по D-12; `ConfigurationError` → человеческий текст в stderr + exit 1 (как выше).
- **Не** переносить сюда `_STAGE_CHECKMARKS` / `_on_stage` — батч передаёт `on_stage=None`.
- `build_collect_deps()` — **отдельная** функция (monkeypatch-точка для `CliRunner`, ровно как `build_ingest_deps`).

---

### 13. `ingestion-service/pyproject.toml` (AMEND)

**Analog:** сам файл, `[project.scripts]` (`:27-28`):

```toml
[project.scripts]
ingest = "ingestion_service.cli:app"
```

Добавить одну строку `ingest-collect = "ingestion_service.collect_cli:app"`. `dependencies` не меняются (zero new runtime packages, success criterion 5).

---

### 14. `backend/src/backend/application/ports/ingestion_schedule.py` (port, CRUD)

**Analog:** `backend/src/backend/application/ports/pipeline_config.py` — целиком:

```python
from datetime import datetime
from typing import Protocol

from backend.domain.pipeline_config import PipelineConfig

class PipelineConfigRepository(Protocol):
    def get(self) -> PipelineConfig | None:
        """Current saved config, or None when the singleton row is absent (D-11)."""
        ...

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        """Persist the YAML document and return the stored config (D-08)."""
        ...
```

Копировать: `Protocol` (не ABC), keyword-only аргументы в `save`, возврат доменного объекта, docstring с D-номером и семантикой `None`. Сигнатура: `get(self) -> IngestionSchedule` (не `| None` — отсутствие строки отдаёт дефолты, RESEARCH §Runtime State Inventory) и `save(self, schedule: IngestionSchedule) -> IngestionSchedule` (upsert `id=1`).

---

### 15. `backend/src/backend/domain/ingestion_schedule.py` (domain, transform)

**Analog:** `backend/src/backend/domain/pipeline_config.py` — домен + структурная ошибка с `to_dict()` (`:16-42`):

```python
@dataclass(frozen=True)
class PipelineConfig:
    """A saved pipeline config document plus its last-saved timestamp (D-08/D-11)."""

    yaml: str
    updated_at: datetime | None

@dataclass(frozen=True)
class PipelineConfigError:
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"path": self.path, "message": self.message}
        if self.line is not None:
            payload["line"] = self.line
        return payload
```

Ноль `fastapi`/`pydantic`/`supabase`; `to_dict()` держит конверт `{errors:[…]}`, который роутер отдаёт как есть.

---

### 16. `backend/src/backend/application/use_cases/ingestion_schedule.py` (use-case, validate-then-persist)

**Analog:** `backend/src/backend/application/use_cases/pipeline_config.py`:

```python
def get_pipeline_config(repo: PipelineConfigRepository) -> PipelineConfig | None:
    """Return the current config, or None for the empty state (D-11)."""
    return repo.get()

def save_pipeline_config(
    repo: PipelineConfigRepository,
    validator: PipelineConfigValidator,
    *,
    yaml_text: str,
    now: datetime | None = None,
) -> PipelineConfig:
    """Validate then persist the document, returning the stored config (D-08/D-11)."""
    validator.validate(yaml_text)
    return repo.save(yaml=yaml_text, updated_at=now or datetime.now(timezone.utc))
```

Плюс стиль валидации/нормализации из `use_cases/ingest_sources.py:29-47` (validate-список → исключение → нормализация → запись):

```python
def add_ingest_source(repo, *, kind, source_id, label=None) -> IngestSource:
    """Validate then persist. Raises IngestSourceValidationError before any write."""
    errors = _validate_add(kind=kind, source_id=source_id, label=label, existing=repo.list())
    if errors:
        raise IngestSourceValidationError(tuple(errors))
    normalized_label = _normalize_label(label)
    return repo.add(...)
```

Для schedule: `sorted(set(days))`, диапазон `1..7`, непустой список, `time_of_day` — `datetime.time` (Pitfall 24-9). `now` инъектируется параметром (`now: datetime | None = None`) — как в `save_pipeline_config`, чтобы тесты не зависели от `datetime.now`.

---

### 17. `backend/src/backend/interface/http/routes/admin.py` (AMEND, controller)

**Analog:** сам файл. DTO-форма (`:186-240`):

```python
class PipelineConfigSaveRequest(BaseModel):
    """PUT /admin/pipeline/config body — the raw YAML document only (D-11, D-13)."""

    model_config = ConfigDict(extra="forbid")

    yaml: str

class PipelineConfigResponse(BaseModel):
    """Read DTO {yaml, updated_at} — no version, no secret/credential key (D-11; PIPE-03)."""

    model_config = ConfigDict(extra="forbid")

    yaml: str
    updated_at: datetime | None = None
```

`_require_*`-хелпер + 503 (`:265-281`):

```python
def _require_pipeline_config(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "pipeline_config", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_not_configured",
        )
    return container.pipeline_config
```

Роут с `require_admin`, конвертом `{errors:[…]}` и маппингом `PersistenceError → 503` (`:690-727`):

```python
@router.put(
    "/pipeline/config",
    response_model=PipelineConfigResponse,
    summary="Save the pipeline config (server-authoritative, no execution)",
    description=(...),
)
def put_pipeline_config(
    body: PipelineConfigSaveRequest,
    request: Request,
    _admin: CurrentUser = Depends(require_admin),
) -> PipelineConfigResponse:
    repo = _require_pipeline_config(request)
    ...
    try:
        config = save_pipeline_config(repo, validator, yaml_text=body.yaml)
    except PipelineConfigValidationError as exc:
        # D-05 / RESEARCH Pitfall 2: top-level {"errors":[...]}, never nested under detail.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errors": [error.to_dict() for error in exc.errors]},
        )
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_unavailable",
        ) from exc
    return PipelineConfigResponse(yaml=config.yaml, updated_at=config.updated_at)
```

Для новой поверхности: `GET /admin/ingestion-schedule` + `PATCH /admin/ingestion-schedule` (RESEARCH Open Q4), `_require_ingestion_schedule(request)` с `detail="ingestion_schedule_not_configured"`, `IngestionSchedulePatchRequest` с `extra="forbid"` и `pattern` на `time_of_day`.

---

### 18. `backend/src/backend/composition/container.py` + `live.py` (AMEND, composition)

**Analog:** сам `container.py` (`:68-72`) — объявление None-дефолта:

```python
    # Declared here (deferred from 16-01) with None defaults so a bare AppContainer(...)
    # still constructs; build_in_memory_container wires the real adapter.
    pipeline_config: PipelineConfigRepository | None = None
    pipeline_config_validator: PipelineConfigValidator | None = None
    # D-21: ingest sources port — None until wired (503 ingest_sources_not_configured).
    ingest_sources: IngestSourceRepository | None = None
```

`live.py` (`:62-67`) — единственное место `create_client`-производных адаптеров:

```python
        pipeline_config=SupabasePipelineConfigRepository(admin_client),
        pipeline_config_validator=YamlPipelineConfigValidator(),
        # SRC-03 / D-21 / D-24: ingest sources behind the port (pipeline_ingest_sources, migration 012)
        ingest_sources=SupabaseIngestSourceRepository(admin_client),
```

Добавить `ingestion_schedule: IngestionScheduleRepository | None = None` в `AppContainer` + одну строку в `build_in_memory_container` (там же, где `container.ingest_sources = InMemoryIngestSourceRepository()`, `:140`) и одну в `live.py`.

---

### 19. `backend/src/backend/tests_support/in_memory.py` (AMEND, fake)

**Analog:** `InMemoryIngestSourceRepository` (`:684-712`) — форма фейка с логом записей:

```python
class InMemoryIngestSourceRepository:
    """In-memory IngestSourceRepository with write log for zero-write asserts (SRC-03, D-21).

    Stable list order: created_at ascending then id ascending. Auto-increment ids.
    """

    def __init__(self, sources: list[IngestSource] | None = None) -> None:
        self._sources: list[IngestSource] = list(sources or [])
        self._next_id = (max((s.id for s in self._sources), default=0) + 1)
        self.adds: list[IngestSource] = []
        self.writes: list[str] = []

    @property
    def write_count(self) -> int:
        return len(self.writes)

    def list(self) -> list[IngestSource]:
        return sorted(self._sources, key=lambda s: (s.created_at, s.id))
```

`InMemoryIngestionScheduleRepository` — тот же приём: `self.writes: list[str]`, `write_count`, `get()` отдаёт дефолты при отсутствии строки (не `None`), `save()` кладёт в `self.schedule` и пишет `self.writes.append("save")`.

---

### 20. `supabase-integration/migrations/013_phase24_scheduled_ingestion.sql` (migration, DDL)

**Analog A — singleton-таблица:** `migrations/011_phase16_pipeline_config.sql` (целиком, 21 строка):

```sql
-- Phase 16: PIPE-01 MVP pipeline config singleton (PIPE-01/PIPE-02/PIPE-03, D-08).
-- Idempotent: create-if-not-exists; the primary key + CHECK enforce the single row.
-- No wipe, no reset. Shared VM: apply once via Studio SQL / psql / supabase db push.

create table if not exists public.pipeline_config (
  id integer primary key default 1 check (id = 1),
  yaml text not null default '',
  updated_at timestamptz not null default now()
);

-- Deny-by-default: RLS enabled, NO permissive policy (T-16-10, RESEARCH Pitfall 7).
-- Only the service_role client (backend composition/live.py) reaches this table;
-- admin gating for the GET/PUT routes is backend require_admin (D-10).
alter table public.pipeline_config enable row level security;
```

**Analog B — таблица, к которой добавляются колонки:** `migrations/012_phase23_ingest_sources.sql` (`:18-25`):

```sql
-- Deny-by-default: RLS enabled, NO permissive policy (T-23-11, D-17).
-- Only the service_role client (backend composition/live.py) reaches this table;
-- admin gating for the ingest-sources routes is backend require_admin.
alter table public.pipeline_ingest_sources enable row level security;
```

Идиомы, которые тест будет искать подстроками (см. `test_phase23_migration_012.py`): `create table if not exists public.`, `id integer primary key default 1`, `check (id = 1)`, `alter column … add column if not exists`, `enable row level security`, отсутствие `create policy`, отсутствие `\ntruncate ` / `\ndelete from`, отсутствие `alter table public.ingestion_sources`.

Новое в 013 (нет в аналогах): `days_of_week smallint[] not null default '{1,2,3,4,5,6,7}'` + CHECK через `<@ ARRAY[...]::smallint[]` (RESEARCH §6.2, A6 — не проверено локально), `time_of_day time not null default '06:00'`, `last_run_at timestamptz`, плюс `add column if not exists last_seen_published_at timestamptz` / `last_seen_video_id text` на `pipeline_ingest_sources`. Seed-строку `id=1` **не** вставлять.

---

### 21. `supabase-integration/src/supabase_integration/ingestion_schedule_repository.py` (adapter, singleton CRUD)

**Analog:** `supabase_integration/pipeline_config_repository.py` — копировать структуру целиком: `_CONFIG_ID = 1` → `_SCHEDULE_ID = 1`, приватный `_SupabaseClient` Protocol (`:20-21`), `_parse_dt`/`_iso`, `try/except PersistenceError: raise / except Exception: raise PersistenceError(...)` в каждом методе, `upsert({"id": _SCHEDULE_ID, ...})` в `save`.

Особенность singleton'а настроек: `get()` **не** возвращает `None` — при отсутствии строки отдаёт доменные дефолты (`enabled=True`, `06:00`, `1..7`), потому что «админ ничего не настраивал» должно работать как «включено по умолчанию» без seed-строки (RESEARCH §Runtime State Inventory).

`supabase-integration/src/supabase_integration/__init__.py` — AMEND: импорт + имя в `__all__` (алфавитный порядок сохраняется, `:24-41`). Экспорт проверяется тестом на `in`, а не на точное равенство — безопасно.

---

### 22. `web/src/services/ingestScheduleApi.js` (service, mock+live)

**Analog:** `web/src/services/ingestSourcesApi.js`. Типизированная ошибка (`:20-29`):

```javascript
export class IngestSourcesError extends Error {
  constructor(message, { code = 'INGEST_SOURCES_FAILED', retryable = true, errors = null } = {}) {
    super(message)
    this.name = 'IngestSourcesError'
    this.code = code
    this.retryable = retryable
    this.errors = errors
  }
}
```

Harness-армы через `sessionStorage` (`:30-98`):

```javascript
const MOCK_STORAGE_KEY = 'digest:ingest-sources-mock'
const ARM_STORAGE_KEY = 'digest:ingest-sources-mock-arm'

function readArm() {
  if (typeof window === 'undefined') return {}
  try {
    const raw = window.sessionStorage.getItem(ARM_STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch {
    return {}
  }
}

export function armFailNextSetEnabled() {
  writeArm({ ...readArm(), failSetEnabled: true })
}

/** Clear every armed mock control (Playwright reset); the saved mock list is kept. */
export function resetIngestSourcesHarness() {
  if (typeof window === 'undefined') return
  window.sessionStorage.removeItem(ARM_STORAGE_KEY)
}
```

Mock-арм / live-арм в одной функции (`:296-350`) — копировать структуру `setIngestSourceEnabled`: сначала `if (mocksEnabled()) { await delay(80); … return }`, затем `getAccessToken()` → `fetch(... PATCH ...)` → `mapHttpError`. Для расписания достаточно одного `patchIngestionSchedule(payload)` + `fetchIngestionSchedule()`; армы — `armFailNextScheduleLoad`, `armFailNextScheduleSave`.

---

### 23. `web/src/components/IngestionScheduleSection.jsx` (component, немедленный PATCH)

**Analog:** `web/src/components/IngestSourcesSection.jsx`. Каркас секции (`:162-175`):

```jsx
  return (
    <section
      data-testid="ingest-sources-section"
      className="mt-6 mb-6 rounded-2xl border border-rule bg-paper p-4 md:p-6"
      aria-busy={loadState === 'loading' || adding || busyRowId != null}
    >
      <h2
        data-testid="ingest-sources-heading"
        className="font-sans text-2xl font-semibold text-ink"
      >
        Источники ингеста
      </h2>
```

Немедленное сохранение с откатом при ошибке (`:115-135`) — ровно модель D-16:

```jsx
  async function onToggle(row) {
    if (busyRowId != null) return
    const id = Number(row.id)
    setBusyRowId(id)
    ...
    try {
      const updated = await setIngestSourceEnabled(id, !row.is_enabled)
      setSources((prev) => prev.map((s) => (Number(s.id) === id ? updated : s)))
    } catch (err) {
      setRowErrors((prev) => ({
        ...prev,
        [id]: err instanceof IngestSourcesError ? err.message : ROW_ACTION_ERROR,
      }))
    } finally {
      setBusyRowId(null)
    }
  }
```

Правила для `IngestionScheduleSection`:
- props: `schedule`, `onScheduleChange` (подъём состояния в страницу для немедленного рендера по ответу сервера), без собственного dirty-сигнала.
- копирайт: «Автоматический сбор», «Дни недели», «Время», «включён/выключен», «Время указывается по московскому времени». **Запрещено**: «Расписание», «Планировщик», «Запуск», «Запустить», «Выполнить» (D-17).
- `data-testid="ingestion-schedule-section"` / `-heading` / `-enabled` / `-time` / `-days` / `-status` — по образцу `ingest-sources-*`.
- время (`type="time"`) сохранять на `onBlur`/`onChange`-с-дебаунсом, не на каждую клавишу (D-16).

---

### 24. `web/src/pages/AdminPipelineConfigPage.jsx` (AMEND: точка вставки)

**Analog:** сам файл. Точка вставки — между `<IngestSourcesSection … />` и блоком `{!savedYaml ? (` (`:234-249`):

```jsx
      <IngestSourcesSection
        sourceId={sourceId}
        label={sourceLabel}
        kind={sourceKind}
        onSourceIdChange={setSourceId}
        onLabelChange={setSourceLabel}
        onKindChange={setSourceKind}
        onFormCleared={() => {
          setSourceId('')
          setSourceLabel('')
          setSourceKind('channel')
        }}
      />

      {!savedYaml ? (
```

`dirty` **не меняется** (`:112-114`):

```jsx
  const yamlDirty = yaml !== savedYaml
  const sourceFormDirty = sourceId.trim() !== '' || sourceLabel.trim() !== ''
  const dirty = yamlDirty || sourceFormDirty
```

Тест-трипваер требует, чтобы редактор оставался `data-testid="pipeline-config-editor"` (`:338`) — порядок проверяется по `boundingBox().y` источников < блока < редактора.

---

### 25. `web/src/main.jsx` (AMEND: harness)

**Analog:** сам файл (`:80-86` + `:43-47`):

```jsx
window.__DIGEST_INGEST_SOURCES_HARNESS__ = {
  armFailNextLoad: armFailNextIngestSourcesLoad,
  armFailNextAdd,
  armFailNextSetEnabled,
  armFailNextDelete,
  armRejectNextAdd,
  resetIngestSourcesHarness,
  resetIngestSourcesMockStore,
}
```

Добавить `window.__DIGEST_INGESTION_SCHEDULE_HARNESS__ = { armFailNextLoad, armFailNextSave, resetIngestionScheduleHarness, resetIngestionScheduleMockStore }`.

---

### 26–28. `deploy/systemd/*` (config, ops)

**Аналог:** отсутствует (каталога `deploy/` нет). Источник формы — RESEARCH §9 (скелет уже выверен против D-19…D-23):

```ini
[Unit]
Description=Digest CDS scheduled ingestion (drafts + pending shortlist rows only)
Wants=network-online.target
After=network-online.target
OnFailure=digest-ingest-alert.service

[Service]
Type=oneshot
User=digestcds
Group=digestcds
WorkingDirectory=/opt/digest-cds
EnvironmentFile=/etc/digest-cds/ingest.env
Environment=TZ=UTC
RuntimeDirectory=digest-ingest
RuntimeDirectoryMode=0750
ExecStart=/usr/bin/flock -n -E 75 /run/digest-ingest/lock /opt/digest-cds/.venv/bin/ingest-collect
TimeoutStartSec=1800
SuccessExitStatus=0 75
NoNewPrivileges=true
PrivateTmp=true
```

Обязательные токены (их проверит `test_phase24_systemd_units.py`): `Type=oneshot`, `EnvironmentFile=`, `OnFailure=digest-ingest-alert.service`, `TimeoutStartSec=1800`, `flock -n`, `-E 75`, `SuccessExitStatus=`, абсолютный путь `/.venv/bin/ingest-collect`; в timer — `OnCalendar=*:0/15`, `Persistent=false`; ни в одном юните — `DEEPSEEK_API_KEY=`, `SUPABASE_SECRET_KEY=`, `SUPABASE_URL=`, `publish`, `/admin/shortlist/send`, `curl`.

---

### 29. `tests/unit/test_phase24_migration_013.py` (text-contract)

**Analog:** `tests/unit/test_phase23_migration_012.py` — целиком (31 строка). Каркас (`:1-20`):

```python
"""RED/contract: migration 012 pipeline_ingest_sources + RLS (SRC-01, D-16/D-17).

Reads the migration as text (no DB). Mirrors tests/unit/test_phase16_migration_011.py.
"""

from __future__ import annotations

from pathlib import Path

_MIGRATION = "supabase-integration/migrations/012_phase23_ingest_sources.sql"

def _text() -> str:
    path = Path(_MIGRATION)
    assert path.exists(), f"migration missing: {_MIGRATION}"
    return path.read_text(encoding="utf-8")
```

И негативные ассерты (`:37-57`):

```python
def test_migration_012_has_no_wipe_statements() -> None:
    """Shared VM safety: insert/DDL only — never a destructive wipe."""
    lower = _text().lower()
    assert "\ntruncate " not in lower
    assert "\ndelete from" not in lower
```

Копировать дословно: путь относительный (cwd = корень репозитория), `.lower()` один раз, `assert not in` для запретов.

---

### 30. `tests/unit/test_phase24_systemd_units.py` (text-contract)

**Analog:** тот же приём, другой артефакт — `tests/unit/test_phase16_migration_011.py` (`_text()` + `Path(...).exists()`), плюс текстовые скан-циклы из `tests/unit/test_data_collection_public_api.py:120-135`:

```python
def test_ingestion_service_has_no_typer_import() -> None:
    """Only cli.py may import typer; all other ingestion_service modules stay clean."""
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "ingestion-service" / "src" / "ingestion_service"
    for path in src_root.rglob("*.py"):
        if path.name == "cli.py":
            continue
        body = path.read_text(encoding="utf-8")
        assert "import typer" not in body, path.name
        assert "from typer" not in body, path.name
```

Тот же `rglob("*.service")`-обход по `deploy/systemd/` с `assert banned not in body` и `assert token in body`; в `assert`-сообщение — `path.name` (иначе диагностика бесполезна).

---

### 31. `tests/admin.spec.js` (AMEND: новый describe + `resetIngestionScheduleMock`)

**Analog:** сам файл, `resetIngestSourcesMock` (`:1815-1823`) и describe (`:1825-1840`):

```javascript
async function resetIngestSourcesMock(page) {
  await page.waitForFunction(() => Boolean(window.__DIGEST_INGEST_SOURCES_HARNESS__));
  await page.evaluate(() => {
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesMockStore();
    window.__DIGEST_INGEST_SOURCES_HARNESS__.resetIngestSourcesHarness();
  });
  await page.reload();
  await expect(page.getByTestId("ingest-sources-section")).toBeVisible();
}

test.describe("Admin pipeline — ingest sources (SRC-01, D-01/D-02)", () => {
  test("ingest sources section above YAML — empty then add channel row", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    await resetIngestSourcesMock(page);
```

Порядок блоков — через `boundingBox().y` (`:1834-1843`) — копировать этот приём для тройки «источники < сбор < редактор».

Трипваер `"pipeline config no execution controls render"` (`:1804-1813`) — **не трогать**:

```javascript
  test("pipeline config no execution controls render", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const pageText = await page.getByTestId("admin-pipeline-page").innerText();
    for (const banned of ["Запустить", "Выполнить", "Запуск", "Планировщик", "Расписание"]) {
      expect(pageText).not.toContain(banned);
    }
```

---

### 32. `tests/unit/test_collect_cli_contract.py` (CLI contract)

**Analog:** `tests/unit/test_cli_ingest_contract.py` — **PRESERVE**, читать как шаблон, не редактировать. Контрактный список (`:20-29`):

```python
EXPECTED_SUCCESS_LINES = [
    "✓ transcript",
    "✓ LLM",
    "✓ saved",
    "material_id: 42",
    ...
    "already_saved: false",
]
```

Для `ingest-collect` — свой `EXPECTED_SUMMARY_LINES` (без `✓`), плюс тест `assert "✓" not in result.stdout` (D-03) и monkeypatch `build_collect_deps` через `cli_mod.build_collect_deps` (как `test_build_ingest_deps_wiring.py:28-33` патчит `cli_mod.Settings.from_env`).

---

### 33. `tests/unit/test_supabase_collect_sources_contract.py` (adapter contract)

**Analog:** `tests/unit/test_supabase_ingest_source_repository_contract.py` — `_FakeExecuteResult` / `_FakeQuery` / `_FakeTable`, где `_FakeQuery` записывает операцию, payload, фильтры и порядок (`:14-60`):

```python
class _FakeQuery:
    def __init__(self, table: "_FakeTable") -> None:
        self._table = table
        self._op: str | None = None
        self._payload: Any = None
        self._filters: list[tuple[str, Any]] = []
        self._order: list[tuple[str, bool]] = []

    def update(self, payload: dict[str, Any]) -> "_FakeQuery":
        self._op = "update"
        self._payload = dict(payload)
        self._table.last_update = dict(payload)
        return self

    def eq(self, column: str, value: Any) -> "_FakeQuery":
        self._filters.append((column, value))
        return self
```

Для монотонного курсора нужен ещё `or_`/`is_`/`lt` в фейке — добавить методы в **свой** фейк-класс, не в чужой тест (он PRESERVE).

---

### 34. `tests/unit/test_http_ingestion_schedule.py` (admin HTTP)

**Analog:** `tests/unit/test_http_ingest_sources.py` — JWT-харнесс **копируется** (файл-источник сам копировал `test_http_pipeline_config.py`, который PRESERVE). Ключевое: отложенные импорты, чтобы RED был ассерт-уровня (`:1-11`, `:42-46`):

```python
"""RED→GREEN: GET/POST /admin/ingest-sources tracer — SRC-01/SRC-03, D-18/D-21.

Imports of not-yet-shipped symbols are deferred inside helpers so collection
succeeds and failures are assertion-level RED (missing routes / wiring), not
import noise.
"""

def _ingest_repo_cls() -> type:
    try:
        from backend.tests_support.in_memory import InMemoryIngestSourceRepository
    except ImportError as exc:  # pragma: no cover - RED until fake ships
        pytest.fail(f"InMemoryIngestSourceRepository not importable: {exc}")
    return InMemoryIngestSourceRepository
```

Плюс `_public_jwk` / `_mint` (ES256, `kid="test-kid-1"`, `:49-79`) — копировать без изменений.

---

### 35. `tests/unit/test_phase24_scheduler_guard.py` (ING-07)

**Аналог:** нет. Частично — текстовый rglob-стиль `test_data_collection_public_api.py:120-135` (для статической части) и `subprocess.run([...], cwd=REPO_ROOT, capture_output=True)` из `test_ingestion_env_example.py:41-50` (для runtime-части). Оба приёма уже приняты в репозитории — собрать из них, не изобретать.

---

### 36. `docs/agents/local-platform-runbook.md` (AMEND: §4j + §5e)

**Analog:** сам файл — §4i (`:503-549`) для миграции и §5d (`:595`) для CLI-UAT. Формат §4i: «Checked-in idempotent SQL: …» → «Why:» → «What it does (safe on shared VM):» → «Apply once on the shared VM» → «Do not» → «Verify after apply» (SQL-блок с `-- expect …`) → «Applied (дата):».

Для `ingest-collect` добавить: `uv sync` **до** `systemctl start` (entry point появляется только после sync), создание `/etc/digest-cds/ingest.env` (0600), копирование трёх юнитов, `systemctl daemon-reload`, smoke `systemctl start digest-ingest.service`, `journalctl -u digest-ingest.service`, ручной ретрай `uv run --env-file ingestion-service/.env ingest <video_id> --template lecture` (D-13), интерпретация exit 0/1/2 + `flock` 75 (D-12/Pitfall 24-1).

---

## Shared Patterns

### A. Инжектированный клиент, ноль `os.environ` в адаптере
**Source:** `ingestion-service/src/ingestion_service/composition/clients.py:40-48`
**Apply to:** `youtube_feed.py`, `supabase_collect_sources.py`, все фабрики.

```python
def build_youtube_metadata_provider(settings: Settings) -> YouTubeOEmbedAdapter:
    """Wire YouTube oEmbed metadata adapter from Settings (D-02)."""
    return YouTubeOEmbedAdapter(build_httpx_client(settings))
```

### B. Маппинг ошибок ровно на границе адаптера
**Source:** `ingestion-service/src/ingestion_service/adapters/supabase_persist.py:36-42` + `data_collection/adapters/youtube_oembed.py:38-52`
**Apply to:** оба новых адаптера.

```python
        except DraftPersistError:
            raise
        except Exception as exc:
            raise _map_exception(exc, material_draft) from None
```

### C. Слои: порт в `application/ports`, use-case без SDK, wiring только в composition
**Source:** `.cursor/rules/architecture.mdc` + `backend/composition/live.py:62-67`
**Apply to:** schedule-порт/use-case/роут; collect-порт/use-case.

### D. Диагностика только в stderr
**Source:** `ingestion-service/src/ingestion_service/cli.py:66-69`
**Apply to:** `collect_cli.py`, `collect_batch.py`.

```python
def _emit_debug(line: str) -> None:
    """D-01: debug lines go to stderr only — never stdout."""
    typer.echo(line, err=True)
```

### E. Немедленное сохранение: запрос → рендер по ответу сервера → откат при ошибке
**Source:** `web/src/components/IngestSourcesSection.jsx:115-135`
**Apply to:** `IngestionScheduleSection.jsx` (toggle, time, days).

### F. Mock+live в одном сервисе + армы в `sessionStorage`
**Source:** `web/src/services/ingestSourcesApi.js:30-98, 296-350`
**Apply to:** `ingestScheduleApi.js`.

### G. Idempotent DDL + deny-by-default RLS + ноль политик
**Source:** `migrations/011` + `migrations/012`
**Apply to:** `013`.

---

## Seam lines (швы, которые план должен назвать явно)

| Шов | Файл:строки | Что с ним делать |
|---|---|---|
| `on_stage=None` в батче | `application/use_cases/ingest_pipeline.py:73,132,158` | Передавать **только** `None`; не заводить `partial`/лямбду-обёртку — иначе `✓ …` утечёт в сводку (D-03, Pitfall 24-8) |
| `cli.py` — **не редактируется** | `ingestion-service/src/ingestion_service/cli.py` (весь файл) | Нулевой дифф (D-01); вторая команда в том же `app` ломает `ingest <url>` (exit 2) |
| `build_ingest_deps` — **не меняется** | `cli.py:39-48` | Новые зависимости — только в `build_collect_deps` в `collect_cli.py`; `test_build_ingest_deps_wiring.py` PRESERVE |
| `build_httpx_client` | `composition/clients.py:33-37` | Переиспользовать как есть; возвращает **`httpx.AsyncClient`** → порт листинга async |
| `Settings.from_env` | `composition/settings.py:62-89` | Два новых ключа встраиваются сюда же; не читать env в адаптере/CLI |
| `Clock`-порт | `application/ports/diagnostics.py:16-21` | Переиспользовать `now()`; второй порт не заводить |
| `pipeline_config` singleton (011) | `migrations/011_phase16_pipeline_config.sql` | Форма-образец для `ingestion_schedule`; **не** добавлять колонки в `pipeline_config` |
| `ingest_sources`-порт (Phase 23) | `backend/application/ports/ingest_sources.py` | Не расширять; курсорные колонки читает **другой** адаптер (`ingestion-service`), не этот порт |
| `IngestSourcesSection` insertion point | `web/src/pages/AdminPipelineConfigPage.jsx:234-249` | Новый блок **после** `/>` этого компонента и **до** `{!savedYaml ? (` |
| `dirty` | `AdminPipelineConfigPage.jsx:112-114` | Остаётся `yamlDirty \|\| sourceFormDirty`; третьего слагаемого нет (D-16) |
| `resetIngestSourcesMock` harness | `tests/admin.spec.js:1815-1823` | Копировать как `resetIngestionScheduleMock`; функцию-источник не менять |
| `test_phase23_migration_012.py` text-ассерты | `tests/unit/test_phase23_migration_012.py:19-57` | Шаблон для `test_phase24_migration_013.py`; сам тест PRESERVE |
| `test_cli_ingest_contract.py` | `tests/unit/test_cli_ingest_contract.py:20-29, .83, .112` | **PRESERVE**; новый контракт — в отдельном файле |
| `__all__` из семи имён | `data_collection/__init__.py:12-20` | AMEND аддитивно; негативный список не расширять новыми публичными именами |

---

## Amendment points

Тесты из RESEARCH.md `### Трипваеры: PRESERVE / AMEND` — план обязан разложить их по задачам явно.

### AMEND (правка существующего теста обязательна — иначе «чужой» RED)

| Тест | Файл:строка | Требуемая правка | Блокирует задачу |
|---|---|---|---|
| `test_ingestion_service_has_no_typer_import` | `tests/unit/test_data_collection_public_api.py:120-128` | `if path.name == "cli.py":` → `if path.name.endswith("cli.py"): continue` | T7 (`collect_cli.py` с `import typer`) |
| `test_public_all_is_exactly_seven_ingestion_names` | `tests/unit/test_data_collection_public_api.py:47-56` | переименовать/переосмыслить: `== PUBLIC_NAMES` → `>= PUBLIC_NAMES` (или расширить `PUBLIC_NAMES` и переименовать в `…exact_public_names`) | T1 (`__all__` += `VideoRef`, `VideoListProvider`) |
| `REQUIRED_INGESTION_KEYS` | `tests/unit/test_ingestion_env_example.py:14-22` | только добавление: `INGEST_TEMPLATE`, `INGEST_MAX_VIDEOS_PER_SOURCE` | T4 |
| `test_ports_package_exports_both_provider_protocols` (по смыслу) | `tests/unit/test_data_collection_public_api.py:59-79` | не ломается при аддитивном `ports/__init__.py`, но новый порт нужно **добавить** в barrel, иначе он не консистентен с root `__all__` | T1 |

### PRESERVE (не редактировать; падение = регресс)

| Тест | Файл:строка | Почему |
|---|---|---|
| `test_cli_ingest_contract` (`EXPECTED_SUCCESS_LINES`, `stderr == ""`) | `tests/unit/test_cli_ingest_contract.py:20-29` | ROADMAP tripwire, success criterion 4 (D-01) |
| `"pipeline config no execution controls render"` | `tests/admin.spec.js:1804-1813` | D-17, бан-лист слов байт-в-байт |
| `test_stage_set_is_unchanged` | `tests/unit/test_data_collection_public_api.py:104-116` | Не добавлять значений в `Stage` |
| `test_build_ingest_deps_wiring` | `tests/unit/test_build_ingest_deps_wiring.py` | `build_ingest_deps` не меняется |
| `test_phase16_migration_011`, `test_phase23_migration_012` | `tests/unit/test_phase16_migration_011.py`, `tests/unit/test_phase23_migration_012.py` | 013 — новый файл; старые миграции не правятся |
| `test_http_ingest_sources`, `test_supabase_ingest_source_repository_contract` | `tests/unit/test_http_ingest_sources.py`, `test_supabase_ingest_source_repository_contract.py` | Schedule-поверхность — отдельные файлы |
| `test_ingestion_env_example` (остальные 4 теста) | `tests/unit/test_ingestion_env_example.py:25-57` | AMEND только кортеж ключей |

---

## No Analog Found

| File | Роль | Data Flow | Причина / что использовать вместо |
|---|---|---|---|
| `deploy/systemd/digest-ingest.service` | config (ops) | event-driven | Каталога `deploy/` нет вовсе; форма — RESEARCH §9, проверка — text-contract |
| `deploy/systemd/digest-ingest.timer` | config (ops) | event-driven | То же |
| `deploy/systemd/digest-ingest-alert.service` | config (ops) | event-driven | То же |
| `ingestion-service/src/ingestion_service/domain/schedule.py` | domain | transform | Точного аналога чистой due-функции нет; собрать из `Clock`-порта + фриз-датаклассов `domain/errors.py` + RESEARCH §2.2/§5.3 |
| `tests/unit/test_phase24_scheduler_guard.py` | test (static+runtime) | — | AST-обход графа импортов в репозитории не встречается; собрать из `rglob`-скана (`test_data_collection_public_api.py`) + `subprocess.run` (`test_ingestion_env_example.py:41-50`) |
| `tests/unit/test_youtube_feed_adapter.py` | test | — | Нет теста адаптера с `httpx.MockTransport`; ближайший стиль — `test_http_ingest_sources.py` (отложенные импорты) + RESEARCH §Validation |

---

## Metadata

**Analog search scope:** `data-collection/src/`, `ingestion-service/src/`, `backend/src/`, `supabase-integration/`, `web/src/`, `tests/`, `docs/agents/`.
**Files scanned:** 24 файла-аналога прочитаны `Read` в этой сессии (полностью или непересекающимися диапазонами; повторных чтений не было) + верифицированные цитаты из `24-RESEARCH.md` §Codebase Grounding.
**Tracked-source gate:** `git ls-files` подтвердил все перечисленные аналоги как tracked; mirror-путей нет; `deploy/` отсутствует в индексе.
**Pattern extraction date:** 2026-10-18
