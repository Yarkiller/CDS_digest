# Phase 10: CLI Composition & UAT - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 17
**Analogs found:** 16 / 17

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `ingestion-service/src/ingestion_service/cli.py` | controller | request-response | *(none — first Typer entry)*; wiring from `composition/clients.py` + `composition/settings.py` | no-analog / partial |
| `ingestion-service/src/ingestion_service/application/use_cases/ingest_pipeline.py` | service | request-response | `ingestion-service/.../use_cases/ingest_until_persist.py` | exact |
| `ingestion-service/src/ingestion_service/application/ports/persist.py` | model | CRUD | same file (`PersistResult`) | exact |
| `ingestion-service/src/ingestion_service/adapters/supabase_persist.py` | service | CRUD | same file (`_persist_result`) | exact |
| `ingestion-service/src/ingestion_service/tests_support/fakes.py` | utility | CRUD | same file (`FakeDraftPersister`) | exact |
| `ingestion-service/src/ingestion_service/composition/clients.py` | config | request-response | same file (`build_*` factories) | exact |
| `supabase-integration/migrations/008_phase10_persist_already_saved.sql` | migration | CRUD | `supabase-integration/migrations/007_phase9_persist_draft.sql` | exact |
| `ingestion-service/pyproject.toml` | config | — | same file (`[project]` / deps) | exact |
| `ingestion-service/.env.example` | config | — | same file + `tests/unit/test_env_example.py` | role-match |
| `tests/unit/test_cli_ingest_contract.py` | test | request-response | RESEARCH CliRunner shape; I/O split from `domain/errors.py` | partial |
| `tests/unit/test_ingest_pipeline.py` | test | request-response | `tests/unit/test_captions_failure_zero_persist.py` | exact |
| `tests/unit/test_phase10_migration_008.py` | test | file-I/O | `tests/unit/test_phase9_migration_007.py` | exact |
| `tests/unit/test_ingestion_env_example.py` | test | file-I/O | `tests/unit/test_env_example.py` | exact |
| `tests/unit/test_data_collection_public_api.py` | test | file-I/O | same file (`test_ingestion_service_has_no_typer_import`) | exact |
| `tests/unit/test_supabase_draft_persister_contract.py` | test | CRUD | same file (`_happy_data` / `_persist_result` asserts) | exact |
| `tests/unit/test_persist_port.py` (+ idempotency tests) | test | CRUD | same files (`PersistResult(...)` constructors) | exact |
| `.planning/phases/10-cli-composition-uat/10-UAT.md` | config | — | `.planning/phases/09-draft-persist-shortlist-enqueue/09-UAT.md` | role-match |

## Pattern Assignments

### `ingestion-service/src/ingestion_service/cli.py` (controller, request-response)

**Analog:** None in-repo (first Typer console script). Copy **composition/wiring** from `clients.py` / `settings.py`, **error envelope** from `domain/errors.py`, **config vs pipeline split** from `config_error.py`, and Typer shape from `10-RESEARCH.md` Pattern 1/3.

**Settings / no-dotenv pattern** (`composition/settings.py` lines 62–64):
```python
@classmethod
def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
    env = environ if environ is not None else os.environ
```

**Pre-video config errors stay off `IngestError`** (`composition/config_error.py` lines 1–7):
```python
class ConfigurationError(Exception):
    """Settings or client factory misconfiguration before any video is processed."""
```

**Pipeline failure JSON** (`domain/errors.py` lines 30–40):
```python
def to_dict(self) -> dict[str, Any]:
    payload: dict[str, Any] = {
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

**Template enum to reuse** (`data_collection/dto/template_kind.py` lines 5–7):
```python
class TemplateKind(str, Enum):
    LECTURE = "lecture"
    PODCAST = "podcast"
```

**Typer one-shot (from RESEARCH — implement in `cli.py`):**
```python
import typer
from typing import Annotated
from data_collection.dto.template_kind import TemplateKind

app = typer.Typer()

@app.command()
def main(
    url: Annotated[str, typer.Argument()],
    template: Annotated[TemplateKind, typer.Option("--template")],
) -> None:
    ...
```

**Error exit (from RESEARCH — stderr + `typer.Exit`):**
```python
except IngestError as err:
    typer.echo(json.dumps(err.to_dict()), err=True)
    raise typer.Exit(code=err.exit_code)
except ConfigurationError as err:
    typer.echo(str(err), err=True)
    raise typer.Exit(code=1)
```

**Packaging** — add via `uv add --package ingestion-service typer`, then:
```toml
[project.scripts]
ingest = "ingestion_service.cli:app"
```

---

### `ingestion-service/.../use_cases/ingest_pipeline.py` (service, request-response)

**Analog:** `ingestion-service/src/ingestion_service/application/use_cases/ingest_until_persist.py`

**Imports + core CAP-02 composer** (lines 1–31) — extend this into the full operator path (URL → captions → metadata → consistency → provenance → LLM → persist); do **not** hard-code provenance without the EN suffix:
```python
from data_collection.assemble import assemble_material_draft
from data_collection.dto.template_kind import TemplateKind
from data_collection.dto.video_metadata import VideoMetadata
from data_collection.ports.article_generator import ArticleGenerator
from data_collection.ports.transcript_provider import TranscriptProvider
from ingestion_service.application.ports.persist import PersistPort, PersistResult
from ingestion_service.application.use_cases.persist_draft import persist_draft


async def run_ingest_until_persist(
    video_id: str,
    captions: TranscriptProvider,
    article: ArticleGenerator,
    persist: PersistPort,
    metadata: VideoMetadata,
    *,
    template_kind: TemplateKind = TemplateKind.LECTURE,
) -> PersistResult:
    transcript = await captions.get(video_id)
    article_draft = await article.process(transcript, template_kind)
    material = assemble_material_draft(
        article_draft,
        metadata,
        f"YouTube · {metadata.author}",  # Phase 10: add EN suffix when language != "ru"
    )
    return persist_draft(material, persist)
```

**URL stage mapping** (`mapping/url.py` lines 18–24):
```python
def map_url_error(error: InvalidYouTubeUrl) -> IngestError:
    return IngestError(
        stage="url",
        reason=error.reason,
        message=f"url {error.reason}",
        context=_forward_context(error),
    )
```

**Captions / metadata / LLM / persist mappers** — call existing `map_captions_error`, `map_metadata_error`, `map_article_error`, `map_persist_error` (same allowlist style as `mapping/captions.py` lines 65–72).

**Consistency fail-closed** — raise `IngestError(stage="consistency", reason="video_id_mismatch", ...)` when `transcript.video_id != metadata.video_id`; do not call article or persist (mirror CAP-02 spy pattern).

**Provenance inline** (not in `provenance.py` — Phase 8 lock):
```python
from ingestion_service.provenance import ENGLISH_TRANSLATION_SUFFIX

label = f"YouTube · {metadata.author}"
if transcript.language != "ru":
    label = f"{label}{ENGLISH_TRANSLATION_SUFFIX}"
```

**Stage progress callback** — print-as-you-go after captions / article / persist (`✓ transcript` / `✓ LLM` / `✓ saved`); prefer `on_stage: Callable[[str], None] | None` so CliRunner and unit tests can spy without coupling to Typer.

---

### `ingestion-service/.../application/ports/persist.py` (model, CRUD)

**Analog:** same file

**Current DTO** (lines 11–16) — add `already_saved: bool`:
```python
@dataclass(frozen=True)
class PersistResult:
    material_id: int
    slug: str
    batch_id: int
    rank: int
    # Phase 10: already_saved: bool
```

**Port signature** (lines 19–21) stays `persist(self, material_draft: MaterialDraft) -> PersistResult`.

---

### `ingestion-service/.../adapters/supabase_persist.py` (service, CRUD)

**Analog:** same file

**Result keys + parse** (lines 22–23, 64–73) — extend `_RESULT_KEYS` and `_persist_result`:
```python
_RESULT_KEYS = ("material_id", "slug", "batch_id", "rank")  # + "already_saved"

def _persist_result(data: object) -> PersistResult:
    payload = data[0] if isinstance(data, list) and data else data
    if not isinstance(payload, dict) or any(key not in payload for key in _RESULT_KEYS):
        raise DraftPersistRpcError("rpc_error")
    return PersistResult(
        material_id=int(payload["material_id"]),
        slug=str(payload["slug"]),
        batch_id=int(payload["batch_id"]),
        rank=int(payload["rank"]),
        # already_saved=bool(payload["already_saved"]),
    )
```

Keep single named RPC `_RPC_NAME = "persist_draft_and_enqueue"` and `_map_exception` taxonomy unchanged.

---

### `ingestion-service/.../tests_support/fakes.py` (utility, CRUD)

**Analog:** same file — `FakeDraftPersister` re-run branch (lines 27–36):
```python
def persist(self, material_draft: MaterialDraft) -> PersistResult:
    self.calls.append(material_draft)
    failure = self._failures.get(material_draft.youtube_video_id)
    if failure is not None:
        raise failure
    existing = self.stored.get(material_draft.youtube_video_id)
    if existing is not None:
        return existing  # Phase 10: return already_saved=True + stored slug
    self.stored[material_draft.youtube_video_id] = self._result
    return self._result
```

Also update `BatchTrackingFakePersister.persist` constructors of `PersistResult(...)` (lines 94–100) to include `already_saved=False` on insert / `True` on conflict.

**Upstream fakes for pipeline tests** — `data_collection/tests_support/fakes.py` (`FakeTranscriptProvider`, `FakeVideoMetadataProvider`, `FakeArticleGenerator`).

---

### `ingestion-service/.../composition/clients.py` (config, request-response)

**Analog:** same file

**Factory style** (lines 52–74, 85–87) — CLI composition root should call these; adapters must not read `os.environ`:
```python
def build_deepseek_article_generator(
    settings: Settings,
    template_root: object | None = None,
) -> DeepSeekArticleGenerator:
    ...

def build_supabase_draft_persister(settings: Settings) -> SupabaseDraftPersister:
    client = build_supabase_service_client(settings)
    return SupabaseDraftPersister(client, batch_size=settings.shortlist_batch_size)
```

`ConfigurationError` on empty Supabase/DeepSeek keys (lines 41–42, 80–81) feeds D-08 human stderr path.

---

### `supabase-integration/migrations/008_phase10_persist_already_saved.sql` (migration, CRUD)

**Analog:** `supabase-integration/migrations/007_phase9_persist_draft.sql`

**Conflict return bug to fix** (lines 148–169) — replace `p_slug` with stored `materials.slug` and add `already_saved`:
```sql
  if v_inserted = 0 then
    select si.batch_id, si.rank
    into v_batch_id, v_rank
    from public.digest_shortlist_items si
    join public.digest_shortlist_batches b on b.id = si.batch_id
    where si.material_id = v_material_id
      and b.sent_at is null
    order by b.week_start desc, b.created_at desc
    limit 1;
    -- ...
    return jsonb_build_object(
      'material_id', v_material_id,
      'slug', p_slug,  -- Phase 10: SELECT m.slug FROM materials WHERE id = v_material_id
      'batch_id', v_batch_id,
      'rank', v_rank
      -- Phase 10: 'already_saved', true
    );
  end if;
```

**Success path** (lines 212–217) — also emit `'already_saved', false`.

**Grants ritual** (lines 221–229) — keep `security invoker`, revoke public/anon/authenticated, grant `service_role` only. Use `CREATE OR REPLACE`; never edit applied `007` in place; no `TRUNCATE`/`DROP TABLE`.

---

### `ingestion-service/pyproject.toml` (config)

**Analog:** same file (lines 1–11) — add `typer` via `uv add`, keep workspace `data-collection` source; add `[project.scripts]` entry `ingest = "ingestion_service.cli:app"`.

---

### `ingestion-service/.env.example` (config)

**Analog:** current file (lines 1–3) + root env-example test pattern.

Expand keys (empty values): `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `SHORTLIST_BATCH_SIZE`, `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`, `DEEPSEEK_MODEL`, `YOUTUBE_PROXY_URL`, `MAX_TRANSCRIPT_CHARS`. Do not autoload in CLI.

---

### `tests/unit/test_cli_ingest_contract.py` (test, request-response)

**Analog:** none for CliRunner; copy RESEARCH contract + spy wiring from CAP-02 tests.

**Expected success stdout (CONTEXT D-06/D-07/D-09):**
```text
✓ transcript
✓ LLM
✓ saved
material_id: 42
slug: kak-ispolzovat-pgvector-dQw4w9WgXcQ
batch_id: 7
rank: 1
already_saved: false
```

**CliRunner shape (RESEARCH):**
```python
from typer.testing import CliRunner
runner = CliRunner()
result = runner.invoke(app, ["https://youtu.be/dQw4w9WgXcQ", "--template", "lecture"])
assert result.exit_code == 0
assert result.stdout.splitlines() == [...]
assert result.stderr == ""
```

Assert D-08: missing env → human stderr, no JSON keys `stage`/`ok`; pipeline `IngestError` → JSON on stderr, prior checkmarks remain on stdout.

---

### `tests/unit/test_ingest_pipeline.py` (test, request-response)

**Analog:** `tests/unit/test_captions_failure_zero_persist.py`

**Fake wiring + zero-persist spy** (lines 41–68):
```python
def _persist_spy() -> FakeDraftPersister:
    return FakeDraftPersister(
        PersistResult(material_id=1, slug="unused", batch_id=1, rank=1)
    )

def test_captions_failure_leaves_persist_calls_empty() -> None:
    provider = FakeTranscriptProvider(
        result=_transcript(),
        failures={VIDEO_ID: CaptionsUnavailable(VIDEO_ID)},
    )
    generator = FakeArticleGenerator(result=_article())
    spy = _persist_spy()
    with pytest.raises(CaptionsError):
        asyncio.run(run_ingest_until_persist(...))
    assert spy.calls == []
    assert generator.calls == []
```

Phase 10 adds: mismatch ids → `stage=consistency`, article not called; captions-then-metadata call order; EN provenance suffix; checkmark/`on_stage` order.

---

### `tests/unit/test_phase10_migration_008.py` (test, file-I/O)

**Analog:** `tests/unit/test_phase9_migration_007.py`

**SQL-as-text contract helpers** (lines 7–25, 57–69, 102–107):
```python
REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION = REPO_ROOT / "supabase-integration/migrations/008_phase10_persist_already_saved.sql"

def _normalized_executable_sql() -> str:
    return " ".join(_sql_without_line_comments().lower().split())

# Assert create or replace, security invoker, already_saved, stored slug on conflict,
# grant execute to service_role, revoke anon/authenticated, no truncate/drop.
```

Assert conflict branch does **not** return `'slug', p_slug` alone for the conflict path; assert `already_saved` appears in both insert and conflict `jsonb_build_object` returns.

---

### `tests/unit/test_ingestion_env_example.py` (test, file-I/O)

**Analog:** `tests/unit/test_env_example.py` (lines 26–46) — point at `ingestion-service/.env.example`, assert required keys, assert not gitignored, assert distinct from root backend `.env.example` (no Vite keys required).

---

### `tests/unit/test_data_collection_public_api.py` (test, file-I/O)

**Analog:** same file — replace Phase 8 ban (lines 119–125):
```python
def test_ingestion_service_has_no_typer_import() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "ingestion-service" / "src" / "ingestion_service"
    for path in src_root.rglob("*.py"):
        body = path.read_text(encoding="utf-8")
        assert "import typer" not in body, path.name
        assert "from typer" not in body, path.name
```

**Phase 10 replacement:** only `cli.py` may contain `import typer` / `from typer`; all other `ingestion_service` modules stay clean.

---

### `tests/unit/test_supabase_draft_persister_contract.py` + persist unit tests (test, CRUD)

**Analog:** same files

**Happy RPC payload** (`test_supabase_draft_persister_contract.py` lines 75–95):
```python
def _happy_data() -> dict[str, object]:
    return {
        "material_id": 101,
        "slug": SLUG,
        "batch_id": 7,
        "rank": 3,
        # Phase 10: "already_saved": False,
    }

assert result == PersistResult(101, SLUG, 7, 3)  # + already_saved=
```

Update every `PersistResult(...)` construction in `test_persist_port.py`, `test_persist_idempotency_overflow.py`, `test_captions_failure_zero_persist.py`, etc.

---

### `.planning/phases/10-cli-composition-uat/10-UAT.md` (config / manual)

**Analog:** `.planning/phases/09-draft-persist-shortlist-enqueue/09-UAT.md`

Frontmatter + checklist rows for four videos (lecture+ru, lecture+en, podcast+ru, podcast+en): URL, template, `material_id`, `slug`, `/admin/digest` checks (unsent shortlist, `status=draft`, Russian body, EN provenance suffix, template headings). No Playwright.

## Shared Patterns

### Composition owns wiring (no env in adapters)
**Source:** `ingestion-service/src/ingestion_service/composition/clients.py`, `composition/settings.py`
**Apply to:** `cli.py`, pipeline use-case injection, live UAT command
```python
Settings.from_env()  # process env only — operator: uv run --env-file ingestion-service/.env
build_supabase_draft_persister(settings)
build_deepseek_article_generator(settings)
```

### Config vs pipeline errors
**Source:** `composition/config_error.py` + `domain/errors.py`
**Apply to:** `cli.py` catch branches (D-08 vs D-05)
- `ConfigurationError` / template load / Typer usage → short human stderr, exit ≠ 0, no checkmarks, no JSON
- `IngestError` after video work starts → `json.dumps(err.to_dict())` on stderr, `typer.Exit(err.exit_code)`, prior checkmarks stay on stdout

### Stage → IngestError mappers
**Source:** `mapping/url.py`, `mapping/captions.py`, `mapping/metadata.py`, `mapping/article.py`, `mapping/persist.py`
**Apply to:** `ingest_pipeline.py` exception boundaries — never invent a second envelope; stage set stays url|captions|metadata|consistency|llm|llm_truncation|persist

### In-memory fakes for unit suite
**Source:** `data_collection/tests_support/fakes.py` + `ingestion_service/tests_support/fakes.py`
**Apply to:** `test_ingest_pipeline.py`, `test_cli_ingest_contract.py` (via injectable builder)
```python
FakeTranscriptProvider / FakeVideoMetadataProvider / FakeArticleGenerator / FakeDraftPersister
```

### Migration amend ritual
**Source:** `007_phase9_persist_draft.sql` + `test_phase9_migration_007.py`
**Apply to:** `008_phase10_persist_already_saved.sql`
- `CREATE OR REPLACE FUNCTION` + identical grant/revoke
- SQL contract tests on executable SQL (strip `--` comments)
- Human gate before shared-VM apply; no `db reset`

### Provenance suffix constant only
**Source:** `ingestion_service/provenance.py` + `tests/unit/test_translation_marker.py`
**Apply to:** pipeline label assembly — do **not** add `build_provenance_label` to `provenance.py`

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `ingestion-service/src/ingestion_service/cli.py` | controller | request-response | No Typer/Click CLI exists yet; use RESEARCH Typer one-shot + composition/error patterns above |

## Metadata

**Analog search scope:** `ingestion-service/src/`, `data-collection/src/`, `supabase-integration/migrations/`, `tests/unit/`, `.planning/phases/*/UAT.md`
**Files scanned:** ~40 tracked sources (use-cases, adapters, fakes, migrations 007, unit tests, UAT notes)
**Tracked-source gate:** all named analogs verified via `git ls-files`
**Pattern extraction date:** 2026-09-29
