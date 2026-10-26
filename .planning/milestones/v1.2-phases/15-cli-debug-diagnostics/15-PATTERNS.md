# Phase 15: CLI --debug diagnostics - Pattern Map

**Mapped:** 2026-10-04
**Files analyzed:** 10 (4 new production, 2 modified production, 4 new/modified tests)
**Analogs found:** 8 / 10 (2 partial — no exact precedent, use closest role-match)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `ingestion-service/src/ingestion_service/application/ports/diagnostics.py` | port | event-driven | `application/ports/persist.py` | role-match |
| `ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py` | adapter | event-driven / stream-format | `adapters/supabase_persist.py` (+ `adapters/persist_errors.py`) | role-match |
| `ingestion-service/src/ingestion_service/diagnostics/redaction.py` | utility | transform | `mapping/captions.py` (`_CONTEXT_ALLOWLIST`) + `url.py` (`_safe_url_for_diagnostics`) | partial |
| `ingestion-service/src/ingestion_service/diagnostics/__init__.py` | package marker | — | `mapping/__init__.py` | role-match |
| `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` (MOD) | service (use-case) | request-response | self (existing `on_stage` seam) | exact |
| `ingestion-service/src/ingestion_service/cli.py` (MOD) | controller | request-response | self (`_on_stage`, `err=True`, config-error handler) | exact |
| `ingestion-service/src/ingestion_service/tests_support/fakes.py` (MOD) | utility (test-support) | event-driven | self (`FakeDraftPersister` call-spy) | exact |
| `tests/unit/test_cli_debug_diagnostics.py` (NEW) | test | request-response | `tests/unit/test_cli_ingest_contract.py` | exact |
| `tests/unit/test_debug_redaction.py` (NEW) | test | transform | `tests/unit/test_ingest_error.py` (`test_map_url_error_redacts_userinfo_credentials`) | role-match |
| `tests/unit/test_stderr_diagnostics.py` (NEW) | test | event-driven | `tests/unit/test_ingest_error.py` | role-match |
| `tests/unit/test_ingest_pipeline.py` (MOD) | test | request-response | self | exact |

> Note: RESEARCH.md §Recommended Project Structure splits `SystemClock` into `adapters/system_clock.py`. The orchestrator's file list puts `StderrDiagnostics + SystemClock` together in `adapters/stderr_diagnostics.py`. Planner should follow the orchestrator list (one file) unless it prefers the split; both satisfy the `Clock` port.

---

## Pattern Assignments

### `application/ports/diagnostics.py` (port, event-driven)

**Analog:** `application/ports/persist.py`

This is the repo's canonical **`typing.Protocol` + `runtime_checkable` + frozen dataclass DTO** shape — copy it verbatim and extend with the `Clock` / `StageDiagnostics` protocols and `DebugValue` union. `diagnostics.py` will also need the null-object; the nearest in-repo precedent for a no-op is the `runtime_checkable` Protocol pattern itself (there is no existing Null object — see "No Analog Found").

**Imports + Protocol pattern** (`application/ports/persist.py` lines 1-21):
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

**Apply to Phase 15:** keep `DebugValue = str | int | float | bool` explicit (no `Any`, per architecture rule). `Clock` gets `monotonic() -> float` and `now() -> datetime`; `StageDiagnostics` gets `stage_started` / `stage_completed` / `stage_failed` / `config_error`. `NullDiagnostics` lives here as a plain class with no-op bodies (mirrors the port method signatures).

---

### `adapters/stderr_diagnostics.py` (adapter, event-driven / stream-format)

**Analog:** `adapters/supabase_persist.py` (constructor-injected adapter implementing a port; secret-safe error context) and `adapters/persist_errors.py` (module-local helper-function layout).

**Adapter + injected-dependency constructor pattern** (`adapters/supabase_persist.py` lines 27-43):
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

**Module-local helpers + allowlisted context** (`adapters/supabase_persist.py` lines 77-79):
```python
def _safe_context(draft: MaterialDraft, reason: str) -> dict[str, Any]:
    return {"slug": draft.slug, "reason": reason}
```

**Apply to Phase 15:** `StderrDiagnostics.__init__(self, *, clock: Clock, secrets: Sequence[str], stream: ... = sys.stderr)` — injected `Clock` and a `SecretRegistry`. `SystemClock` (or the injected clock) is the `time.monotonic()` / `datetime.now()` adapter. Emit with `typer.echo(line, err=True)` **exclusively** (see cli.py analog below). Format `[HH:MM:SS] debug stage=…` from `clock.now()`, `elapsed_ms` from `clock.monotonic()` deltas, then pass the assembled line through `redaction.sanitize()` before echo. Never format raw objects/`Settings`/exceptions.

---

### `diagnostics/redaction.py` (utility, transform) — PARTIAL

**Analog:** `mapping/captions.py` `_CONTEXT_ALLOWLIST` (allowlist-by-default emission) + `url.py::_safe_url_for_diagnostics` (userinfo stripping) + `composition/settings.py` (`repr=False` secret discipline).

**Allowlist frozenset pattern** (`mapping/captions.py` lines 34-41):
```python
_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "available_languages",
        "exception_class",
    }
)
```

**Allowlisted forwarding loop** (`mapping/captions.py` lines 55-61):
```python
def _forward_context(error: CaptionsError) -> dict[str, Any]:
    forwarded: dict[str, Any] = {"video_id": error.video_id}
    raw = dict(error.context)
    for key in _CONTEXT_ALLOWLIST:
        if key == "video_id":
            continue
        if key in raw:
            forwarded[key] = raw[key]
    return forwarded
```

**Userinfo credential stripping** (`url.py` lines 20-32):
```python
def _safe_url_for_diagnostics(value: str) -> str:
    """Strip userinfo credentials from URL-like diagnostic values."""
    parsed = urlparse(value)
    if not parsed.scheme or not parsed.netloc:
        return value
    if parsed.username is None and parsed.password is None:
        return value
    host = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port is not None else ""
    netloc = f"{host}{port}"
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )
```

**Secret `repr=False` discipline** (`composition/settings.py` lines 55, 59):
```python
deepseek_api_key: str | None = field(default=None, repr=False)
...
supabase_secret_key: str | None = field(default=None, repr=False)
```

**Apply to Phase 15:** `ALLOWED_KEYS: frozenset[str]` uses the `frozenset({...})` literal style; `DENY_PATTERNS: tuple[re.Pattern[str], ...]` follows the module-constant style used for `_REASON_BY_TYPE` / `_CONFLICT_CODES`. Reuse the `_safe_url_for_diagnostics` approach for URL userinfo (consider importing it from `url.py` rather than duplicating). `SecretRegistry` masks exact runtime values from `Settings` (sourced from `Settings`, never `os.environ`). This file has **no exact analog** — the allowlist idiom is copied from `mapping/*.py`, but the pure denylist-regex + registry layer is new code.

---

### `application/use_cases/ingest_pipeline.py` (service/use-case, request-response) — MODIFY

**Analog:** itself.

The `on_stage` callback seam and the try/except-mapping boundary per stage are the exact places to add diagnostics hooks. Do **not** touch `on_stage` semantics.

**Existing callback seam + stage mapping** (`application/use_cases/ingest_pipeline.py` lines 40-84):
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
) -> PersistResult:
    try:
        video_id = extract_video_id(url)
    except InvalidYouTubeUrl as err:
        raise map_url_error(err) from err

    try:
        transcript = await captions.get(video_id)
    except CaptionsError as err:
        raise map_captions_error(err) from err
    if on_stage is not None:
        on_stage("transcript")

    try:
        metadata = await metadata_provider.get(video_id)
    except MetadataError as err:
        raise map_metadata_error(err) from err

    # CONSISTENCY-01: fail closed before LLM when DTO video ids diverge.
    if transcript.video_id != metadata.video_id:
        raise IngestError(
            stage="consistency",
            reason="video_id_mismatch",
            ...
        )
    ...
    try:
        article_draft = await article.process(transcript, template)
    except ArticleError as err:
        raise map_article_error(err) from err
    if on_stage is not None:
        on_stage("llm")
    ...
```

**Apply to Phase 15:** add an optional `diagnostics: StageDiagnostics | None = None` keyword. Follow the exact `if on_stage is not None:` guard style but wrap with `diagnostics.stage_started(...)` / `stage_completed(stage, signals)` / `stage_failed(stage, reason=..., exit_code=...)`, defaulting to `NullDiagnostics` semantics (or the `None`-guard). The use-case must **not** import `time`, `sys`, `typer`, or `datetime`. Signals come from DTOs: `Transcript(text, language, video_id)` (`text`/`language`/`video_id`), `ArticleDraft(title, dek, body_markdown, roles)`, `VideoMetadata(video_id, source_url, author)`, `PersistResult(material_id, slug, batch_id, rank, already_saved)`, `IngestError(stage, reason, exit_code)`. Emit only lengths/counters for bodies — never `text`/`body_markdown` (D-08).

**Failure attribution:** the exception-mapping `except … as err: raise map_*_error(err) from err` blocks are where `stage_failed` belongs. Use the **`IngestError.stage` token verbatim** (domain vocabulary below) so debug lines correlate 1:1 with the JSON envelope.

---

### `cli.py` (controller, request-response) — MODIFY

**Analog:** itself.

**Existing CLI structure + stderr discipline** (`cli.py` lines 27-84):
```python
_STAGE_CHECKMARKS = {
    "transcript": "✓ transcript",
    "llm": "✓ LLM",
    "saved": "✓ saved",
}


def build_ingest_deps() -> Any:
    """Composition seam for live adapters; CliRunner monkeypatches this with fakes."""
    settings = Settings.from_env()
    return SimpleNamespace(
        captions=build_youtube_captions(settings),
        metadata_provider=build_youtube_metadata_provider(settings),
        article=build_deepseek_article_generator(settings),
        persist=build_supabase_draft_persister(settings),
    )


def _on_stage(name: str) -> None:
    typer.echo(_STAGE_CHECKMARKS[name])


@app.command()
def main(
    url: Annotated[str, typer.Argument(help="YouTube URL or video id")],
    template: Annotated[
        TemplateKind,
        typer.Option("--template", help="Prompt template: lecture or podcast"),
    ],
) -> None:
    """Ingest a YouTube URL into a materials draft + shortlist row."""
    try:
        deps = build_ingest_deps()
        result = asyncio.run(
            run_ingest_pipeline(
                url,
                template,
                captions=deps.captions,
                metadata_provider=deps.metadata_provider,
                article=deps.article,
                persist=deps.persist,
                on_stage=_on_stage,
            )
        )
    except (ConfigurationError, TemplateLoadError) as err:
        # D-08: pre-video failures stay human text — never mint a new IngestError stage.
        typer.echo(str(err), err=True)
        raise typer.Exit(code=1) from err
    except IngestError as err:
        typer.echo(json.dumps(err.to_dict()), err=True)
        raise typer.Exit(code=err.exit_code) from err

    typer.echo(f"material_id: {result.material_id}")
    typer.echo(f"slug: {result.slug}")
    typer.echo(f"batch_id: {result.batch_id}")
    typer.echo(f"rank: {result.rank}")
    typer.echo(f"already_saved: {'true' if result.already_saved else 'false'}")
```

**Apply to Phase 15:**
- Add `debug: Annotated[bool, typer.Option("--debug", help="Emit secret-safe stage diagnostics on stderr")] = False` (explicit flag name suppresses Typer's auto `--no-debug`). RESEARCH.md lines 343-360.
- Build the sink after `build_ingest_deps()`: `NullDiagnostics()` when off, `StderrDiagnostics(clock=SystemClock(), secrets=[...])` when on.
- `stage=config` line in the existing `except (ConfigurationError, TemplateLoadError)` block (D-12) — emit the debug line **before** `typer.echo(str(err), err=True)`; do not mint an `IngestError`.
- Failure path (D-10): completed-stage lines + failed-stage line must be written by the sink before the existing `json.dumps(err.to_dict())` echo; the two streams/order must not change the JSON envelope.
- Secrets list must come from `Settings` via `getattr(deps, "settings", None)` fallback (Pitfall 8) — `build_ingest_deps` needs `settings=settings` added to its `SimpleNamespace`.
- Do **not** touch `_on_stage`, `_STAGE_CHECKMARKS`, or the five stdout result lines (DBG-02).

**Wiring invariant** (`tests/unit/test_build_ingest_deps_wiring.py` lines 12-23): `build_ingest_deps` source must keep calling `Settings.from_env` + the four composition factories, and must **not** contain `load_dotenv` or `os.environ`. Adding `settings=settings` is safe; reading secrets from env directly is not.

---

### `tests_support/fakes.py` (test-support utility, event-driven) — MODIFY

**Analog:** itself — `FakeDraftPersister` is the call-spy precedent.

**Call-spy fake pattern** (`tests_support/fakes.py` lines 13-45):
```python
class FakeDraftPersister:
    def __init__(
        self,
        result: PersistResult,
        failures: dict[str, DraftPersistError] | None = None,
    ) -> None:
        self._result = result
        self._failures = failures or {}
        self.calls: list[MaterialDraft] = []
        self.stored: dict[str, PersistResult] = {}

    def persist(self, material_draft: MaterialDraft) -> PersistResult:
        self.calls.append(material_draft)
        ...
```

**Apply to Phase 15:** add `FakeClock` (scripted `monotonic()` sequence + fixed `now()`, mirroring the `result`/`failures` constructor style) and `RecordingDiagnostics` (records `stage_started`/`stage_completed`/`stage_failed`/`config_error` calls into a `calls` list) so `test_ingest_pipeline.py` can assert event order. Keep the same `self.calls: list[...]` spy convention.

---

### `tests/unit/test_cli_debug_diagnostics.py` (NEW, test, request-response)

**Analog:** `tests/unit/test_cli_ingest_contract.py` (exact).

**CliRunner + monkeypatch + frozen stdout contract** (`test_cli_ingest_contract.py` lines 20-85):
```python
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


def test_cli_happy_path_stdout_contract(monkeypatch) -> None:
    from typer.testing import CliRunner

    from ingestion_service import cli as cli_mod

    deps = _fake_deps()
    monkeypatch.setattr(cli_mod, "build_ingest_deps", lambda: deps)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code == 0
    assert result.stdout.splitlines() == EXPECTED_SUCCESS_LINES
    assert result.stderr == ""
```

**mid-pipeline error → JSON stderr assertion** (`test_cli_ingest_contract.py` lines 176-200):
```python
    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    stdout_lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert stdout_lines == ["✓ transcript"]
    assert "✓ LLM" not in result.stdout
    assert "✓ saved" not in result.stdout
    payload = json.loads(result.stderr.strip())
    assert payload["ok"] is False
    assert payload["stage"] == "llm"
```

**Config-error human stderr, no JSON** (`test_cli_ingest_contract.py` lines 242-271):
```python
    def _raise_config() -> object:
        raise ConfigurationError("SUPABASE_URL is required")

    monkeypatch.setattr(cli_mod, "build_ingest_deps", _raise_config)

    result = CliRunner().invoke(cli_mod.app, [URL, "--template", "lecture"])
    assert result.exit_code != 0
    ...
    err = result.stderr.strip()
    assert err
    assert "SUPABASE_URL" in err
```

**Apply to Phase 15:** copy the `_fake_deps` / `_transcript` / `_article` / `_metadata` / `_persist_result` fixtures and `EXPECTED_SUCCESS_LINES`. New asserts: `--debug` off ⇒ `result.stderr == ""` (D-13); `--debug` on ⇒ regex `^\[\d{2}:\d{2}:\d{2}\] debug stage=captions .*elapsed_ms=\d+` per stage while `result.stdout.splitlines() == EXPECTED_SUCCESS_LINES`; failure ⇒ debug lines precede JSON envelope; config ⇒ `stage=config` before human text with no `{"ok": false}`. **Assert on `result.stdout` / `result.stderr`, never `result.output`** (Pitfall 6). Because the CLI uses real `SystemClock`, assert structure/regex, not exact ms.

---

### `tests/unit/test_debug_redaction.py` (NEW, test, transform)

**Analog:** `tests/unit/test_ingest_error.py` — the credential-redaction assertions (role-match).

**Redaction assertion style** (`test_ingest_error.py` lines 93-108):
```python
def test_map_url_error_redacts_userinfo_credentials() -> None:
    from ingestion_service.mapping.url import map_url_error
    from ingestion_service.url import InvalidYouTubeUrl, extract_video_id

    credentialed = "https://user:secret@evil.com/watch?v=dQw4w9WgXcQ"
    with pytest.raises(InvalidYouTubeUrl) as exc_info:
        extract_video_id(credentialed)

    mapped = map_url_error(exc_info.value)
    payload = mapped.to_dict()

    assert "secret" not in mapped.message
    assert "user:secret" not in mapped.message
    assert "secret" not in str(mapped.context)
    assert "secret" not in payload["message"]
    assert "secret" not in str(payload.get("context", {}))
    assert "secret" not in str(exc_info.value)
```

**Apply to Phase 15:** mirror the "plant a secret, assert it is absent everywhere" style. Test `sanitize()` directly: allowlist drops unknown keys; `SecretRegistry` masks exact `deepseek_api_key`/`supabase_secret_key`/proxied-URL values with `[redacted]`; denylist regexes catch cookies/bearer tokens/foreign JWTs; control chars stripped and value length capped; mask-not-fail (returns sanitized mapping, never raises).

---

### `tests/unit/test_stderr_diagnostics.py` (NEW, test, event-driven)

**Analog:** `tests/unit/test_ingest_error.py` (role-match) + the `FakeClock` spy.

**Apply to Phase 15:** instantiate `StderrDiagnostics(clock=FakeClock(...), secrets=[...], stream=io.StringIO())` and assert exact `[HH:MM:SS] debug stage=…` output, exact `elapsed_ms` from scripted monotonic values, and control-char stripping. This is the determinism test (Pitfall 5).

---

### `tests/unit/test_ingest_pipeline.py` (MODIFY, test, request-response)

**Analog:** itself.

**Direct use-case invocation style** (`test_ingest_pipeline.py` lines 52-79):
```python
    captions = FakeTranscriptProvider(result=_transcript(video_id=VIDEO_ID))
    metadata = FakeVideoMetadataProvider(result=_metadata(video_id=OTHER_VIDEO_ID))
    article = FakeArticleGenerator(result=_article())
    persist = _persist()

    with pytest.raises(IngestError) as exc_info:
        asyncio.run(
            run_ingest_pipeline(
                URL,
                TemplateKind.LECTURE,
                captions=captions,
                metadata_provider=metadata,
                article=article,
                persist=persist,
            )
        )
```

**Apply to Phase 15:** add a `RecordingDiagnostics` (from `tests_support/fakes.py`) to the `run_ingest_pipeline(...)` call and assert the event order `captions start/complete → metadata start/complete → llm start/complete → persist start/complete`, plus a failure case asserting `stage_failed` fires for the mapped stage. Keep existing tests untouched.

---

## Shared Patterns

### Secret-safe allowlist emission
**Source:** `mapping/captions.py` (`_CONTEXT_ALLOWLIST`, lines 34-41) and `mapping/persist.py` (`_CONTEXT_ALLOWLIST`, lines 26-33)
**Apply to:** `diagnostics/redaction.py` (`ALLOWED_KEYS`), `adapters/stderr_diagnostics.py`
```python
_CONTEXT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "video_id",
        "slug",
        "batch_id",
        "reason",
    }
)
```
Nothing is emitted unless it is in the allowlist (D-07). This is the established repo discipline for forwarding only safe context keys.

### URL userinfo stripping
**Source:** `url.py::_safe_url_for_diagnostics` (lines 20-32)
**Apply to:** `diagnostics/redaction.py` denylist net (D-08 proxy credentials)
Reuse rather than reinvent — the userinfo path is already unit-tested (`test_map_url_error_redacts_userinfo_credentials`). Consider extracting/importing into `redaction.py`.

### `repr=False` secret discipline
**Source:** `composition/settings.py` (lines 55, 59)
**Apply to:** `SecretRegistry` construction source — derive secrets from `Settings` fields, never `os.environ` (guarded by `test_build_ingest_deps_wiring.py`).

### Error-mapping boundary (origin → `IngestError`)
**Source:** `mapping/captions.py` (`map_captions_error`, lines 65-73), `mapping/persist.py` (`map_persist_error`, lines 56-63), `domain/errors.py` (`Stage` literal, lines 7-17)
**Apply to:** `ingest_pipeline.py` `stage_failed` calls — report `IngestError.stage` verbatim so debug correlates with the JSON envelope.
```python
Stage = Literal[
    "url", "captions", "metadata", "consistency",
    "llm", "llm_truncation", "persist",
]
```

### Port + runtime_checkable Protocol + frozen DTO
**Source:** `application/ports/persist.py` (lines 1-21)
**Apply to:** `application/ports/diagnostics.py` — export `Clock`, `StageDiagnostics`, `DebugValue`, `NullDiagnostics`. No `Any` at the port boundary.

### Adapter constructor injection + module-local helpers
**Source:** `adapters/supabase_persist.py` (lines 27-43, 77-79)
**Apply to:** `adapters/stderr_diagnostics.py` — inject `Clock` + secrets; keep formatting/redaction helpers module-local.

### CLI stderr discipline
**Source:** `cli.py` (lines 72-77) — every error path uses `typer.echo(..., err=True)`.
**Apply to:** `StderrDiagnostics` must echo **only** with `err=True`; never `print()` and never plain `typer.echo` (Pitfall 2 — stdout contamination).

### CLI contract lock (no drift)
**Source:** `tests/unit/test_cli_ingest_contract.py` (`EXPECTED_SUCCESS_LINES`, `result.stderr == ""`)
**Apply to:** all new CLI tests — freeze stdout lines and assert `stderr == ""` when `--debug` is off (DBG-02).

---

## No Analog Found

Files with no close match in the codebase (planner should use RESEARCH.md patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `diagnostics/redaction.py` (pure denylist/registry layer) | utility | transform | Repo has allowlist-forwarding helpers (`mapping/*`) and userinfo stripping (`url.py`), but **no standalone denylist-regex + exact-value secret registry**. The allowlist idiom is copied; the denylist + `SecretRegistry` are new. |
| `NullDiagnostics` null-object inside `application/ports/diagnostics.py` | port | event-driven | No existing no-op port implementation in the repo; pattern comes from RESEARCH.md §Pattern 1. |
| `diagnostics/__init__.py` | package marker | — | New package; copy empty-marker style from `mapping/__init__.py`. |

---

## Metadata

**Analog search scope:** `ingestion-service/src/ingestion_service/**` (`application/ports`, `application/use_cases`, `adapters`, `mapping`, `composition`, `domain`, `tests_support`), `data-collection/src/data_collection/tests_support`, `data-collection/src/data_collection/dto`, `tests/unit/`
**Files scanned:** ~20 (12 read directly + glob map of 25 source + 85 test files)
**Tracked-source gate:** all named analogs verified with `git ls-files` (non-empty output) — none are gitignored mirrors
**Pattern extraction date:** 2026-10-04
