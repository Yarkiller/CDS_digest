# Phase 7: Captions Adapter - Pattern Map

**Mapped:** 2026-09-26
**Files analyzed:** 34
**Analogs found:** 30 / 34

## File Classification

| New/Modified/Deleted File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------------|------|-----------|----------------|---------------|
| `data-collection/.../ports/video_metadata_provider.py` | port (Protocol) | request-response | `data-collection/.../ports/transcript_provider.py` | exact |
| `data-collection/.../ports/__init__.py` | config | — | same file (extend `__all__`) | exact (extend) |
| `data-collection/.../adapters/youtube_transcript.py` | adapter | request-response → side-effect (network) | `supabase-integration/.../ping_recorder.py` (injected client + SDK→error) | role-match |
| `data-collection/.../adapters/youtube_oembed.py` | adapter | request-response → side-effect (HTTP) | same + `backend/.../composition/live.py` client injection | role-match |
| `data-collection/.../errors/captions.py` | error | transform (SDK → module error) | `backend/.../domain/errors.py` (`DomainError` + typed subtypes) | role-match |
| `data-collection/.../errors/metadata.py` | error | transform | same (`PersistenceError` / typed subtypes) | role-match |
| `data-collection/.../tests_support/fakes.py` | test utility | request-response | same file (`FakeTranscriptProvider`) + RESEARCH additive failures | exact (extend) |
| `data-collection/.../__init__.py` | config (public barrel) | — | same file (add `VideoMetadataProvider`) | exact (extend) |
| `data-collection/pyproject.toml` | config (deps) | — | `supabase-integration/pyproject.toml` (workspace member deps) | exact |
| `ingestion-service/pyproject.toml` | config | — | `data-collection/pyproject.toml` + `backend/pyproject.toml` | exact |
| `ingestion-service/.../__init__.py` | config | — | `data-collection/.../__init__.py` (minimal public surface) | role-match |
| `ingestion-service/.../url.py` | service (pure fn) | transform | **no direct analog** — stdlib `urllib.parse` + table-driven tests | none |
| `ingestion-service/.../domain/errors.py` | error | transform (`to_dict`) | `backend/.../domain/errors.py` (hierarchy) + D-11 envelope (new) | partial |
| `ingestion-service/.../composition/settings.py` | config | — | `backend/.../composition/settings.py` (`from_env` injectable) | exact |
| `ingestion-service/.../composition/clients.py` | config / factory | side-effect (construct clients) | `backend/.../composition/live.py` + `supabase_integration/client.py` | exact |
| `ingestion-service/.../mapping/captions.py` | service (mapper) | transform | HTTP routes catching `PersistenceError` → status; keep thin | role-match |
| `ingestion-service/.../mapping/metadata.py` | service (mapper) | transform | same | role-match |
| `pyproject.toml` (root) | config | — | same file (`[tool.uv.workspace].members`) | exact (extend) |
| `tests/unit/test_extract_video_id.py` | test | transform | parametrized DTO reject tests (`test_video_metadata_dto.py`) | role-match |
| `tests/unit/test_ingest_error.py` | test | transform | `test_search_knowledge.py` (`KnowledgeQueryValidationError` attrs) | role-match |
| `tests/unit/test_youtube_transcript_adapter.py` | test | request-response | `test_supabase_ping_recorder_contract.py` (adapter + mapped errors) | role-match |
| `tests/unit/test_youtube_oembed_adapter.py` | test | request-response | same | role-match |
| `tests/unit/test_captions_error_mapping.py` | test | transform | route/use-case PersistenceError mapping tests | role-match |
| `tests/unit/test_metadata_error_mapping.py` | test | transform | same | role-match |
| `tests/unit/test_fake_transcript_provider_failures.py` | test | request-response | `test_transcript_provider_fake.py` (extend with failures) | exact |
| `tests/unit/test_fake_video_metadata_provider.py` | test | request-response | `test_transcript_provider_fake.py` + `test_article_generator_fake.py` | exact |
| `tests/unit/test_data_collection_public_api.py` | test — **MODIFY** | — | same file (grow `__all__` whitelist) | exact |
| `tests/unit/test_transcript_provider_fake.py` | test — keep green | request-response | same (success+spy must stay unchanged) | exact |
| `tests/integration/test_youtube_captions_live.py` | test (optional) | side-effect (network) | **no analog** — invent `@pytest.mark.integration` + env skip | none |
| `tests/integration/test_youtube_oembed_live.py` | test (optional) | side-effect (network) | **no analog** — same gate | none |
| `docs/agents/local-platform-runbook.md` | docs — **MODIFY** | — | same file (§1 env + optional live sections) | exact (extend) |
| `data-collection/.../ports/transcript_provider.py` | port — **EXISTS** | request-response | implement against; do not change signature | exact (reuse) |
| `data-collection/.../dto/transcript.py` | model — **EXISTS** | transform | implement against; empty text = adapter failure | exact (reuse) |
| `data-collection/.../dto/video_metadata.py` | model — **EXISTS** | transform | oEmbed fills fields; `published_at=None` OK | exact (reuse) |

**Out of scope (do not touch):** Typer CLI / DeepSeek / persist / shortlist (Phases 8–10); `supabase-integration/migrations/*`; Whisper/Foundry ASR; fabricated `author="unknown"`.

---

## Pattern Assignments

### `data-collection/.../ports/video_metadata_provider.py` (port, request-response)

**Analog:** `data-collection/src/data_collection/ports/transcript_provider.py` (lines 1–11):
```python
"""TranscriptProvider port — captions by video_id (D-15)."""

from __future__ import annotations

from typing import Protocol

from data_collection.dto.transcript import Transcript


class TranscriptProvider(Protocol):
    async def get(self, video_id: str) -> Transcript: ...
```

**Ports barrel** (`ports/__init__.py` lines 1–6):
```python
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider

__all__ = ["ArticleGenerator", "TranscriptProvider"]
```

**Copy for Phase 7:**
```python
class VideoMetadataProvider(Protocol):
    async def get(self, video_id: str) -> VideoMetadata: ...
```
Mirror transcript port exactly (D-22). Add to `ports/__all__` and package root `__all__`. **Do not** accept URLs on the port (D-04).

---

### `data-collection/.../adapters/youtube_transcript.py` + `youtube_oembed.py` (adapter, network)

**Analog (injected client, never env):** `supabase-integration/src/supabase_integration/ping_recorder.py` (lines 14–35):
```python
class SupabasePingRecorder:
    """Persists platform pings to public.activity_events (kind=platform_ping)."""

    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def record(self, *, user_id: str | None, kind: str, payload: dict) -> str:
        # …
        try:
            result = self._client.table("activity_events").insert(row).execute()
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"activity_events insert failed: {exc}") from exc
```

**Analog (composition builds clients):** `backend/src/backend/composition/live.py` (lines 26–47):
```python
def build_live_container(settings: Settings) -> AppContainer:
    """Wire service_role adapters for profiles, pings, issues, materials, cycles."""
    # …
    admin_client = create_service_role_client(
        settings.supabase_url,
        settings.supabase_secret_key,
    )
    return AppContainer(
        materials=SupabaseMaterialRepository(admin_client),
        # …
        pings=SupabasePingRecorder(admin_client),
```

**Analog (client factories colocated, composition-only):** `supabase-integration/.../client.py` (lines 8–15):
```python
def create_publishable_client(url: str, key: str) -> Client:
    """Browser-safe publishable/anon key client (no service_role)."""
    return create_client(url, key)


def create_service_role_client(url: str, key: str) -> Client:
    """Privileged service_role client for RLS-bypass writes (activity_events, profiles)."""
    return create_client(url, key)
```

**Copy for Phase 7:**
- `YouTubeTranscriptAdapter(api: YouTubeTranscriptApi)` — sync SDK via `await asyncio.to_thread(...)`; never `os.environ`.
- `YouTubeOEmbedAdapter(client: httpx.AsyncClient)` — build canonical `https://www.youtube.com/watch?v={video_id}`; require `author_name`; set `published_at=None`.
- Map SDK/HTTP → `CaptionsError` / `MetadataError` subtypes at the adapter boundary (like `PersistenceError` mapping).
- Proxy/`GenericProxyConfig` / httpx `proxy=` constructed only in `ingestion-service` composition (`clients.py`).

**Language path (transcript only):** list-then-pick with `base = lang.split("-")[0].lower()`; prefer any `ru` then any `en`; else `CaptionsNoPreferredLanguage` with `available_languages` (D-07…D-09). Blank joined text → `CaptionsEmpty` before constructing `Transcript` (Phase 6 D-09).

---

### `data-collection/.../errors/captions.py` + `metadata.py` (error, transform)

**Analog (typed hierarchy + context attrs):** `backend/src/backend/domain/errors.py` (lines 1–56):
```python
class DomainError(Exception):
    """Base domain error."""


class MaterialNotFoundError(DomainError):
    def __init__(self, material_id: int | str) -> None:
        super().__init__(f"material {material_id} not found")
        self.material_id = material_id


class PersistenceError(DomainError):
    """Raised when an infrastructure adapter cannot complete a persistence operation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class KnowledgeQueryValidationError(DomainError):
    """Raised for blank or overlong knowledge search queries (KNOW-01)."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
```

**Also:** subtypes with extra context (`VoteConflictError`, `NotebookNotAvailableError`) — store typed fields on the instance, not free-form dumps.

**Copy for Phase 7:**
- Base `CaptionsError(video_id, **context)` + subtypes per D-12 (recommend dedicated `CaptionsBotChallenge` for `bot_challenge` — CONTEXT discretion).
- Base `MetadataError(video_id, **context)` + `MetadataUnavailable` / `MetadataNetworkError` / `MetadataInvalidResponse` (D-25).
- **No** `stage=` / pipeline vocabulary in these modules (D-11).
- SDK exception class names may live in `context["exception_class"]` only — never as operator `reason`.

---

### `ingestion-service/.../domain/errors.py` (error — IngestError + `to_dict`)

**Analog (module home for domain exceptions):** `backend/.../domain/errors.py` — exceptions live in owning package’s `domain/`, not in adapters.

**No exact `to_dict()` analog** in live tree — invent per D-11/D-13 RESEARCH sketch:

```python
@dataclass
class IngestError(Exception):
    stage: Stage  # Literal["url", "captions", "metadata", "consistency", "llm", "llm_truncation", "persist"]
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

**Copy for Phase 7:** Envelope keys locked: `{ok, stage, reason, message, context?, exit_code}`. Stages include future Phase 8–10 values now (costly reversibility). Do **not** put `IngestError` in `data-collection`.

**Anti-pattern:** copying `PersistenceError`’s free-form `message: str` only — operator contract needs stable `reason` codes (D-10).

---

### `ingestion-service/.../composition/settings.py` + `clients.py` (config)

**Analog (injectable environ):** `backend/src/backend/composition/settings.py` (lines 13–55):
```python
@dataclass(frozen=True)
class Settings:
    # …
    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        env = environ if environ is not None else os.environ
        # …
        return cls(
            api_cors_origins=env.get("API_CORS_ORIGINS", ""),
            # …
        )
```

**Test analog** (`tests/unit/test_stub_mailer.py` lines 46–53; `test_live_container_wiring.py` 117–127):
```python
settings = Settings.from_env({})
assert settings.mailer == "stub"

settings = Settings.from_env(
    {
        "SUPABASE_JWKS_URL": "https://jwks.example/jwks.json",
        "SUPABASE_JWT_ISSUER": "https://issuer.example/auth/v1",
        "APP_CONTAINER": "live",
    }
)
```

**Copy for Phase 7:**
- `Settings.youtube_proxy_url: str | None` from optional `YOUTUBE_PROXY_URL` via `from_env(environ=...)`.
- `clients.py` builds `YouTubeTranscriptApi(proxy_config=...)` and `httpx.AsyncClient(proxy=...)` when set; unset → direct.
- Adapters receive ready clients only (D-17). Never put full proxy URL into `IngestError.context` (security).

---

### `ingestion-service/.../url.py` (service, transform — NEW)

**No live URL-parser analog** in repo (Phase 6 deferred parse off ports). Closest test *style*: table-driven `@pytest.mark.parametrize` rejects in `tests/unit/test_video_metadata_dto.py`.

**Copy for Phase 7:** Pure `extract_video_id(value: str) -> str` (~25 lines) using `urllib.parse` + 11-char id regex (D-01…D-05). Raise → map to `IngestError(stage="url", ...)` in caller/mapper — not CAP-02. Reject playlist-without-`v=`, channels, `/live|/v|/e`, bad length.

---

### `ingestion-service/.../mapping/captions.py` + `metadata.py` (service, transform)

**Analog (boundary maps infra error → contract):** HTTP routes / use-cases catching `PersistenceError` (e.g. `backend/.../routes/materials.py` → 503). Keep mappers as thin functions:

| CaptionsError subtype | `IngestError.reason` |
|-----------------------|----------------------|
| `CaptionsUnavailable` | `no_captions` |
| `CaptionsNoPreferredLanguage` | `no_preferred_language` |
| `CaptionsDisabled` | `captions_disabled` |
| `CaptionsVideoUnavailable` | `video_unavailable` |
| `CaptionsBlocked` | `youtube_blocked` |
| `CaptionsBotChallenge` (discretion) | `bot_challenge` |
| `CaptionsNetworkError` | `network_error` |
| `CaptionsEmpty` | `empty_captions` |
| base / catch-all | `unknown_captions_error` |

| MetadataError | Suggested reason |
|---------------|------------------|
| `MetadataUnavailable` | `metadata_unavailable` |
| `MetadataNetworkError` | `network_error` |
| `MetadataInvalidResponse` | `metadata_invalid_response` |

**Copy for Phase 7:** Always `stage="captions"` / `stage="metadata"`; never pass SDK class names as `reason`.

---

### `data-collection/.../tests_support/fakes.py` (test utility — EXTEND)

**Analog (current success+spy):** `data-collection/src/data_collection/tests_support/fakes.py` (lines 17–24):
```python
class FakeTranscriptProvider:
    def __init__(self, result: Transcript) -> None:
        self._result = result
        self.calls: list[str] = []

    async def get(self, video_id: str) -> Transcript:
        self.calls.append(video_id)
        return self._result
```

**Package placement** (`tests_support/__init__.py`):
```python
"""In-memory fakes for unit tests (not public package API — D-04)."""
```

**Copy for Phase 7 (D-15 / D-26):** Additive `failures: dict[str, CaptionsError] | None = None` — raise if `video_id` in map **after** recording call; default `None`/`{}` keeps Phase 6 success tests green. Add `FakeVideoMetadataProvider` with parallel `VideoMetadata` + `MetadataError` catalog. Never export fakes from `__all__`.

---

### `data-collection/.../__init__.py` (config — EXTEND public surface)

**Analog:** same file (lines 1–17):
```python
"""Public API for data-collection ingestion contracts (D-01, D-04)."""

from data_collection.dto.material_draft import MaterialDraft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.transcript import Transcript
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider

__all__ = [
    "Transcript",
    "VideoMetadata",
    "MaterialDraft",
    "TemplateKind",
    "TranscriptProvider",
    "ArticleGenerator",
]
```

**Copy for Phase 7:** Grow to seven names — add `VideoMetadataProvider`. Optionally export error bases if ingestion-service must avoid deep-imports (RESEARCH A3 discretion — prefer exporting bases if needed). Still exclude fakes / `ArticleDraft`.

**Test analog to update:** `tests/unit/test_data_collection_public_api.py` — today asserts exactly six names (lines 9–18, 35–40). Extend `PUBLIC_NAMES`; keep negative list including fakes.

---

### Workspace scaffold: `ingestion-service/` + root `pyproject.toml`

**Analog (workspace member):** root `pyproject.toml` (lines 7–22):
```toml
dependencies = [
    "backend",
    "data-collection",
    "supabase-integration",
]

[tool.uv.workspace]
members = ["backend", "data-collection", "supabase-integration"]

[tool.uv.sources]
backend = { workspace = true }
data-collection = { workspace = true }
supabase-integration = { workspace = true }
```

**Analog (member pyproject):** `data-collection/pyproject.toml` (lines 1–16) + `supabase-integration/pyproject.toml` (workspace dep on sibling):
```toml
[project]
name = "data-collection"
# …
dependencies = [
    "pydantic>=2.10.0",
]
```

**Copy for Phase 7:**
- New member `ingestion-service` with `module-name = "ingestion_service"`, depends on `data-collection` only this phase.
- Append to root `members` / `sources` / optionally root `dependencies`.
- `data-collection` deps: `youtube-transcript-api>=1.2.0,<2`, `httpx[socks]==0.28.1`, `PySocks` (D-18).
- **Do not** add `typer` / `openai` this phase (Pitfall 7).

---

### Existing contracts to implement against (reuse — do not reopen)

**`Transcript`** (`dto/transcript.py` lines 8–24) — blank text rejected by validators; adapter must raise `CaptionsEmpty` instead of returning whitespace.

**`VideoMetadata`** (`dto/video_metadata.py` lines 10–26) — `published_at` optional; oEmbed leaves `None`.

**`TranscriptProvider`** — async `get(video_id)` only.

**Fake success tests** (`test_transcript_provider_fake.py` lines 6–16):
```python
def test_fake_transcript_provider_returns_scripted_and_records_calls() -> None:
    # …
    out = asyncio.run(fake.get("vid-a"))
    assert out is scripted
    assert fake.calls == ["vid-a"]
```
Keep green after additive `failures=` default.

---

### Optional integration tests + pytest marker (D-20)

**No live `@pytest.mark.integration` analog** — root `pyproject.toml` today:
```toml
[tool.pytest.ini_options]
testpaths = ["tests/unit"]
pythonpath = ["."]
```

**Copy for Phase 7:**
- Register `integration` marker under `[tool.pytest.ini_options].markers`.
- Keep default `testpaths = ["tests/unit"]` **or** add `addopts = "-m 'not integration'"` if `tests/integration/` is collected.
- Gate live tests with env (e.g. `RUN_YOUTUBE_INTEGRATION=1`) + skip otherwise.
- Document in runbook (below). Unit suite remains network-free.

---

### `docs/agents/local-platform-runbook.md` (docs — EXTEND)

**Analog:** same file §1 Environment (lines 11–28) — env vars documented, secrets warning; optional live sections (§5 / §5b) for non-CI proofs.

**Copy for Phase 7:** New subsection for captions/oEmbed:
- Optional `YOUTUBE_PROXY_URL` (`socks5://192.168.1.68:1080` AdGuard example from Phase 6).
- Cloud.ru risk: without proxy expect `IpBlocked` → `youtube_blocked`.
- How to run (path-explicit — `testpaths` stays `tests/unit`, so a bare `-m integration` collects zero tests): `RUN_YOUTUBE_INTEGRATION=1 uv run pytest tests/integration -m integration`.
- Never commit proxy URLs with credentials; never `VITE_*` for proxy.

---

## Data-Flow / Ports & Adapters Notes

Aligned with `.cursor/rules/architecture.mdc` + RESEARCH architecture diagram:

```text
Operator input (URL or bare video_id)
        |
        v
[ingestion-service]
  extract_video_id  --fail--> IngestError(stage="url")
  Settings.from_env → clients (proxy optional)
        |
        | inject ready clients (adapters NEVER read os.environ)
        v
[data-collection adapters]
  YouTubeTranscriptAdapter  --implements--> TranscriptProvider
  YouTubeOEmbedAdapter      --implements--> VideoMetadataProvider
        | raise CaptionsError / MetadataError (no stage=)
        v
[ingestion-service mapping]
  CaptionsError  --> IngestError(stage="captions", reason=locked)
  MetadataError  --> IngestError(stage="metadata", reason=...)
  IngestError.to_dict() --> operator JSON

Phase 10 (NOT this phase): captions FIRST, then metadata, then LLM, then persist
Phase 9/10: failing TranscriptProvider + spy PersistPort => persist.calls == []
```

| Rule | Phase 7 implication |
|------|---------------------|
| External SDKs in `data-collection` | `youtube-transcript-api` / httpx only in adapters |
| Composition owns wiring | `ingestion-service` Settings + clients |
| No SDK in domain/use-case | URL parse + mappers + `IngestError` only |
| Public barrel | Add `VideoMetadataProvider`; fakes stay private |
| Fail-closed | Never empty `Transcript`; never fabricated author |
| CAP-02 this phase | Adapter/unit raise only — no live DB spy |

**Anti-patterns to reject in plans:**
- Adapters call `os.environ` / `os.getenv("YOUTUBE_PROXY_URL")`
- `reason=TranscriptsDisabled` (SDK class names)
- `stage=` inside `data-collection`
- URL parse on `TranscriptProvider.get`
- Returning empty/`" "` `Transcript` on failure
- Fabricating `author="unknown"`
- Whisper on IP block
- Exporting fakes from `__all__`
- Shipping Typer / DeepSeek / migrations this phase
- Claiming CAP-02 complete via live Supabase without persist (D-14)
- Accepting `/live/`, `/v/`, `/e/` or silent any-language fallback

---

## TDD Notes

Aligned with `.cursor/rules/tdd.mdc` / `AGENTS.md`:

> **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST**

| Order | Action |
|-------|--------|
| 1 | RED: `test_extract_video_id`, `test_ingest_error`, adapter mocks, mapping, fake failures, public API extend |
| 2 | `uv run pytest tests/unit/test_<name>.py -x` — expect ImportError / AssertionError |
| 3 | Minimal production: ports/errors/adapters/ingestion-service scaffold |
| 4 | Keep `test_transcript_provider_fake.py` green (additive failures default) |
| 5 | Full `uv run pytest` (unit only) before phase gate; integration optional/manual |

**Suggested RED files first (from RESEARCH Test Map / Wave 0):**
- `test_extract_video_id.py` — accept watch/youtu.be/shorts/embed/bare; reject playlist/channel/bad length
- `test_youtube_transcript_adapter.py` — mocked list/fetch; dialect + `no_preferred_language`; SDK→CaptionsError
- `test_youtube_oembed_adapter.py` — mocked httpx; canonical URL; missing author → MetadataInvalidResponse
- `test_ingest_error.py` + mapping tests — `to_dict()` envelope + locked reasons
- `test_fake_transcript_provider_failures.py` / `test_fake_video_metadata_provider.py`
- Extend `test_data_collection_public_api.py` for `VideoMetadataProvider`

**Async harness:** `asyncio.run(...)` in sync pytest — **do not** add `pytest-asyncio` (Phase 6 lock). Sync SDK → `asyncio.to_thread` in adapter.

**Unit layer constraints:** no network, no DB, no migrations, no Playwright required for Phase 7 gate.

---

## Cross-Cutting Patterns

### Protocol + real adapter (injected client)
**Source:** `TranscriptProvider` + `SupabasePingRecorder` / `live.py`
**Apply to:** YouTube adapters; composition constructs proxy-aware clients.

### Module-local error taxonomy → operator envelope
**Source:** `DomainError` / `PersistenceError` hierarchy + new `IngestError.to_dict`
**Apply to:** Two-hop map: SDK → CaptionsError/MetadataError → IngestError(stage, reason).

### Settings.from_env(environ=)
**Source:** `backend/composition/settings.py`
**Apply to:** `YOUTUBE_PROXY_URL` only in ingestion-service composition.

### Additive fake failure catalog
**Source:** Phase 6 `FakeTranscriptProvider` + RESEARCH Pattern 4
**Apply to:** Optional `failures=` dict; success path unchanged.

### Public API barrel growth
**Source:** `data_collection/__init__.py` + `test_data_collection_public_api.py`
**Apply to:** Add `VideoMetadataProvider`; keep fakes excluded.

### Workspace member scaffold
**Source:** root + `data-collection` / `supabase-integration` pyprojects
**Apply to:** New `ingestion-service` + deps on `data-collection`; root members update.

### Optional live proof via runbook
**Source:** `docs/agents/local-platform-runbook.md` optional live sections
**Apply to:** Proxy + `pytest -m integration` docs; not CI gate.

### Async ports + sync SDK
**Source:** Phase 6 async Protocols + `asyncio.run` tests
**Apply to:** `asyncio.to_thread` in transcript adapter; httpx async for oEmbed.

---

## No Analog Found

| File / concern | Role | Data Flow | Reason |
|----------------|------|-----------|--------|
| `ingestion-service/.../url.py` (`extract_video_id`) | service | transform | No YouTube URL parser in live tree; invent with stdlib + table-driven tests (D-01…D-05) |
| `IngestError.to_dict()` envelope | error | transform | Domain errors lack JSON envelope; invent per D-11/D-13 (partial: hierarchy style from `domain/errors.py`) |
| `tests/integration/test_youtube_*_live.py` + marker gate | test | side-effect | No `@pytest.mark.integration` / `tests/integration/` today; invent marker + env skip (D-20) |
| Dedicated captions/metadata error packages under `data-collection/errors/` | error | transform | No `data-collection/errors/` yet; closest is backend `DomainError` subtypes — role-match only |

---

## Metadata

**Analog search scope:** `data-collection/src/data_collection/{ports,dto,tests_support,__init__}`, `backend/src/backend/{composition,domain/errors}`, `supabase-integration/src/supabase_integration/{ping_recorder,client,__init__}`, `tests/unit/test_{transcript_provider_fake,data_collection_public_api,live_container_wiring,stub_mailer,video_metadata_dto}.py`, root + member `pyproject.toml`, `docs/agents/local-platform-runbook.md`
**Files scanned:** ~34 primary (planned create/modify + live analogs) + `06-PATTERNS.md` format
**Pattern extraction date:** 2026-09-26
**Discretion noted:** Exact subtype ↔ reason table and optional public export of error bases remain Claude's Discretion within locked reason codes (CONTEXT). Prefer dedicated `CaptionsBotChallenge` for clear `bot_challenge` mapping. Integration skip via marker + `RUN_YOUTUBE_INTEGRATION=1` (RESEARCH A6). CAP-02 live persist spy documented as Phase 9/10 follow-up only (D-14).

## PATTERN MAPPING COMPLETE
