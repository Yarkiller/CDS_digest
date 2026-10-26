# Phase 23: Admin-managed ingest sources - Pattern Map

**Mapped:** 2026-10-17
**Files analyzed:** 20
**Analogs found:** 19 / 20

> Primary vertical slice to mirror: Phase 16 pipeline-config (migration → port → fake → Supabase adapter → composition → admin HTTP → SPA service → page). ADUX-10 reuses Phase 19 guard trio unchanged; only the page `dirty` expression widens.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `supabase-integration/migrations/012_phase23_ingest_sources.sql` | migration | CRUD (DDL) | `supabase-integration/migrations/011_phase16_pipeline_config.sql` (+ PK/unique shape from `001_initial_schema.sql`) | exact (RLS) / role-match (PK) |
| `backend/src/backend/domain/ingest_source.py` | model | transform | `backend/src/backend/domain/pipeline_config.py` | exact |
| `backend/src/backend/domain/errors.py` (AMEND) | model | request-response | `PipelineConfigValidationError` in same file | exact |
| `backend/src/backend/application/ports/ingest_sources.py` | service (port) | CRUD | `backend/src/backend/application/ports/pipeline_config.py` | exact |
| `backend/src/backend/application/use_cases/ingest_sources.py` | service | CRUD + validate-then-persist | `backend/src/backend/application/use_cases/pipeline_config.py` | exact |
| `backend/src/backend/tests_support/in_memory.py` (AMEND) | utility (fake) | CRUD | `InMemoryPipelineConfigRepository` in same file | exact |
| `supabase-integration/src/supabase_integration/ingest_source_repository.py` | service (adapter) | CRUD | `pipeline_config_repository.py` + `vote_repository.py` insert + `knowledge_chunk_repository.py` delete + `shortlist_repository.py` update | role-match |
| `supabase-integration/src/supabase_integration/__init__.py` (AMEND) | config | — | same file (`SupabasePipelineConfigRepository` export) | exact |
| `backend/src/backend/composition/container.py` (AMEND) | config | — | same file (`pipeline_config` field wiring) | exact |
| `backend/src/backend/composition/live.py` (AMEND) | config | — | same file (`SupabasePipelineConfigRepository` wire) | exact |
| `backend/src/backend/interface/http/routes/admin.py` (AMEND) | route / controller | request-response | same file (`_require_pipeline_config` + `put_pipeline_config` 400 mapper) | exact |
| `web/src/services/ingestSourcesApi.js` | service | request-response | `web/src/services/pipelineConfigApi.js` | exact |
| `web/src/pages/AdminPipelineConfigPage.jsx` (AMEND) | component | request-response | same file (dirty + guard + error panel) | exact |
| `web/src/components/IngestSourcesSection.jsx` | component | CRUD (immediate) | `AdminPipelineConfigPage.jsx` form/error chrome (+ `ErrorPanel.jsx`) | role-match |
| `tests/unit/test_phase23_migration_012.py` | test | — | `tests/unit/test_phase16_migration_011.py` | exact |
| `tests/unit/test_http_ingest_sources.py` | test | request-response | `tests/unit/test_http_pipeline_config.py` | exact |
| `tests/unit/test_supabase_ingest_source_repository_contract.py` | test | CRUD | `tests/unit/test_supabase_pipeline_config_repository_contract.py` | exact |
| `tests/unit/test_composition_container.py` (AMEND) | test | — | same file + `test_live_container_wiring.py` pipeline asserts | role-match |
| `tests/unit/test_live_container_wiring.py` (AMEND) | test | — | same file (`test_build_live_container_wires_pipeline_config`) | exact |
| `tests/admin.spec.js` (AMEND) | test | request-response | same file (pipeline describes ~1296–1814; **D-22 tripwire PRESERVE**) | exact |

**Reused unchanged (not new files — shared patterns only):**
`web/src/hooks/useUnsavedChangesGuard.js`, `web/src/components/UnsavedChangesDialog.jsx`, `web/src/utils/unsavedChangesGuard.js`.

## Pattern Assignments

### `supabase-integration/migrations/012_phase23_ingest_sources.sql` (migration, CRUD/DDL)

**Analog (RLS / idempotent create):** `supabase-integration/migrations/011_phase16_pipeline_config.sql`

**Core migration + deny-by-default RLS** (lines 6–15):
```sql
create table if not exists public.pipeline_config (
  id integer primary key default 1 check (id = 1),
  yaml text not null default '',
  updated_at timestamptz not null default now()
);

-- Deny-by-default: RLS enabled, NO permissive policy
alter table public.pipeline_config enable row level security;
```

**Analog (identity PK + unique pair — shape only; do NOT reuse table):** `supabase-integration/migrations/001_initial_schema.sql`

**Identity PK + unique** (lines 48–61):
```sql
create table if not exists ingestion_sources (
  id bigint generated always as identity primary key,
  ...
  unique (source_system, external_id)
);
```

**Copy for 012:** `create table if not exists public.pipeline_ingest_sources` with `bigint generated always as identity` PK, `kind` check, `unique (kind, source_id)`, `enable row level security`, **no** `create policy`, **no** `truncate`/`delete from`. Never ALTER `ingestion_sources` (D-16).

---

### `backend/src/backend/domain/ingest_source.py` (model, transform)

**Analog:** `backend/src/backend/domain/pipeline_config.py`

**Imports + frozen entity + reject-row `to_dict`** (lines 10–42):
```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PipelineConfig:
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

**Copy for ingest:** frozen `IngestSource` entity (`id`, `kind`, `source_id`, `label`, `is_enabled`, timestamps). Reuse `PipelineConfigError.to_dict()` rows for rejects (omit `line` always — D-19), or a tiny identical helper; do **not** invent a second envelope shape.

---

### `backend/src/backend/domain/errors.py` (AMEND — validation exception)

**Analog:** `PipelineConfigValidationError` in same file (lines 191–200):
```python
class PipelineConfigValidationError(DomainError):
    """Raised when the pipeline config fails server-side validation (PIPE-02, D-03/D-05).

    Carries the structured ``PipelineConfigError`` tuple the PUT route maps to a
    top-level ``{"errors": [...]}`` 400 payload.
    """

    def __init__(self, errors: tuple[PipelineConfigError, ...]) -> None:
        super().__init__("pipeline config validation failed")
        self.errors = errors
```

**Copy:** Add `IngestSourceValidationError` carrying `tuple[PipelineConfigError, ...]` (or same row type). HTTP mapper stays one shape.

---

### `backend/src/backend/application/ports/ingest_sources.py` (port, CRUD)

**Analog:** `backend/src/backend/application/ports/pipeline_config.py`

**Protocol style** (lines 9–24):
```python
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.domain.pipeline_config import PipelineConfig


class PipelineConfigRepository(Protocol):
    def get(self) -> PipelineConfig | None: ...

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig: ...
```

**Copy for ingest:** `IngestSourceRepository(Protocol)` with `list() -> list[IngestSource]`, `add(...)`, `set_enabled(id, *, is_enabled) -> IngestSource`, `delete(id) -> None`. No SDK types. Docstrings name the D-* decisions.

---

### `backend/src/backend/application/use_cases/ingest_sources.py` (use case, validate-then-persist)

**Analog:** `backend/src/backend/application/use_cases/pipeline_config.py`

**Validate-then-persist** (lines 9–34):
```python
from __future__ import annotations

from datetime import datetime, timezone

from backend.application.ports.pipeline_config import (
    PipelineConfigRepository,
    PipelineConfigValidator,
)
from backend.domain.pipeline_config import PipelineConfig


def get_pipeline_config(repo: PipelineConfigRepository) -> PipelineConfig | None:
    return repo.get()


def save_pipeline_config(
    repo: PipelineConfigRepository,
    validator: PipelineConfigValidator,
    *,
    yaml_text: str,
    now: datetime | None = None,
) -> PipelineConfig:
    validator.validate(yaml_text)  # raises before any write
    return repo.save(yaml=yaml_text, updated_at=now or datetime.now(timezone.utc))
```

**Copy for ingest:** `list_ingest_sources`, `add_ingest_source` (regex + kind match + label max 120 + duplicate pre-check **before** `repo.add` — D-14/D-15), `set_ingest_source_enabled`, `delete_ingest_source`. Import only domain + ports. Raise `IngestSourceValidationError` on reject so `save_count` / write log stays 0.

---

### `backend/src/backend/tests_support/in_memory.py` (AMEND — recording fake)

**Analog:** `InMemoryPipelineConfigRepository` (lines 648–670):
```python
class InMemoryPipelineConfigRepository:
    """In-memory PipelineConfigRepository — absent by default (D-11 empty state).

    Records every save so route tests can assert zero writes on a validation reject
    (D-03/D-07).
    """

    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config = config
        self.saves: list[PipelineConfig] = []

    @property
    def save_count(self) -> int:
        return len(self.saves)

    def get(self) -> PipelineConfig | None:
        return self._config

    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        stored = PipelineConfig(yaml=yaml, updated_at=updated_at)
        self._config = stored
        self.saves.append(stored)
        return stored
```

**Copy:** `InMemoryIngestSourceRepository` with in-memory list, auto-increment ids, and a `writes` / `adds` log so HTTP tests assert `write_count == 0` on 400. Import `IngestSource` at module top (mirror `PipelineConfig` import at line 22).

---

### `supabase-integration/src/supabase_integration/ingest_source_repository.py` (adapter, CRUD)

**Primary analog (injected client + PersistenceError boundary):** `supabase-integration/src/supabase_integration/pipeline_config_repository.py`

**Imports + client Protocol + error mapping** (lines 9–56):
```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Protocol

from backend.domain.errors import PersistenceError
from backend.domain.pipeline_config import PipelineConfig


class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...


class SupabasePipelineConfigRepository:
    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

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

**List pattern:** `knowledge_chunk_repository.py` `list_all` (lines 87–103) — `.select(...).execute()`, map rows, map exceptions.

**Insert pattern:** `vote_repository.py` `_insert_vote` (lines 52–67) — `.insert({...}).execute()`, require returned rows.

**Update pattern:** `shortlist_repository.py` `set_decision` (lines 145–166) — `.update({...}).eq(...).execute()`, empty result → domain not-found.

**Delete pattern:** `knowledge_chunk_repository.py` (lines 107–118) — `.delete().eq(...).execute()` with PersistenceError mapping.

**Copy:** Table name **`pipeline_ingest_sources` only**. Reuse `_parse_dt` / `_iso` helpers from pipeline_config adapter (copy verbatim). Never touch `ingestion_sources`.

---

### `supabase-integration/src/supabase_integration/__init__.py` (AMEND — export)

**Analog:** same file (lines 11, 23–38):
```python
from supabase_integration.pipeline_config_repository import SupabasePipelineConfigRepository
...
__all__ = [
    ...
    "SupabasePipelineConfigRepository",
    ...
]
```

**Copy:** Import + append `"SupabaseIngestSourceRepository"` to `__all__` (D-24 AMEND). Contract test asserts membership (see adapter contract analog below).

---

### `backend/src/backend/composition/container.py` + `live.py` (AMEND — wiring)

**Analog — AppContainer optional field** (`container.py` lines 65–68, 134–135):
```python
    # Declared here with None defaults so a bare AppContainer(...) still constructs
    pipeline_config: PipelineConfigRepository | None = None
    pipeline_config_validator: PipelineConfigValidator | None = None
...
    container.pipeline_config = InMemoryPipelineConfigRepository()
    container.pipeline_config_validator = YamlPipelineConfigValidator()
```

**Analog — live service_role wire** (`live.py` lines 11–25, 60–62):
```python
from supabase_integration import (
    ...
    SupabasePipelineConfigRepository,
    ...
)
...
        pipeline_config=SupabasePipelineConfigRepository(admin_client),
        pipeline_config_validator=YamlPipelineConfigValidator(),
```

**Copy (D-21):** `ingest_sources: IngestSourceRepository | None = None` on `AppContainer`; in-memory fake in `build_in_memory_container`; `SupabaseIngestSourceRepository(admin_client)` in `build_live_container`.

---

### `backend/src/backend/interface/http/routes/admin.py` (AMEND — routes + DTOs)

**Analog — DTO + require helper** (lines 176–210):
```python
class PipelineConfigSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    yaml: str


class PipelineConfigResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    yaml: str
    updated_at: datetime | None = None


def _require_pipeline_config(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "pipeline_config", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_not_configured",
        )
    return container.pipeline_config
```

**Analog — require_admin + 400 top-level errors** (lines 629–655):
```python
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
        # Top-level {"errors":[...]}, never nested under detail. Zero writes.
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"errors": [error.to_dict() for error in exc.errors]},
        )
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="pipeline_config_unavailable",
        ) from exc
```

**List wrapper shape:** `AdminShortlistResponse` / items list (lines 68–76) — prefer `{sources: [...]}` per D-18.

**Copy (D-18):** Keep routes in this file. Add:
- `IngestSourceCreateRequest` / `IngestSourcePatchRequest` with `ConfigDict(extra="forbid")`
- `_require_ingest_sources` → 503 `ingest_sources_not_configured`
- `GET/POST /ingest-sources`, `PATCH/DELETE /ingest-sources/{id}`
- POST 201; DELETE → `Response(status_code=204)` (no existing admin 204 analog — use FastAPI `Response` already imported at line 7)
- PersistenceError → 503 `ingest_sources_unavailable`

---

### `web/src/services/ingestSourcesApi.js` (service, request-response)

**Analog:** `web/src/services/pipelineConfigApi.js`

**Typed error + mock arm/reset + live Bearer fetch** (lines 12–24, 63–82, 151–193):
```javascript
import { delay } from '../utils/delay.js'
import { getAccessToken } from './authApi.js'
import { isMocksEnabled } from './authEnv.js'

export class PipelineConfigError extends Error {
  constructor(message, { code = 'PIPELINE_CONFIG_FAILED', retryable = true, errors = null } = {}) {
    super(message)
    this.name = 'PipelineConfigError'
    this.code = code
    this.retryable = retryable
    this.errors = errors
  }
}

export function armFailNextLoad() { ... }
export function resetPipelineConfigHarness() { ... }

export async function fetchPipelineConfig(accessToken) {
  if (mocksEnabled()) { ... }
  const token = accessToken ?? (await getAccessToken())
  ...
  response = await fetch(`${apiBase()}/admin/pipeline/config`, {
    headers: { Authorization: `Bearer ${token}` },
  })
}
```

**400 mapping with `errors` array** (lines 129–136):
```javascript
  if (response.status === 400) {
    const errors = Array.isArray(body?.errors) ? body.errors : null
    return new PipelineConfigError('Конфиг не прошёл проверку', {
      code: 'INVALID_CONFIG',
      retryable: false,
      errors,
    })
  }
```

**Copy:** `IngestSourcesError` (or reuse name pattern), sessionStorage seed list, `armFail*` / `armRejectNextAdd` / `resetIngestSourcesHarness`, methods `listIngestSources` / `addIngestSource` / `setIngestSourceEnabled` / `deleteIngestSource` hitting `/admin/ingest-sources`. Mock branch required (`VITE_USE_MOCKS=true`).

---

### `web/src/pages/AdminPipelineConfigPage.jsx` (AMEND — dirty OR + section host)

**Analog:** same file

**Dirty + single guard** (lines 106–107 — **widen only**):
```javascript
  const dirty = yaml !== savedYaml
  const blocker = useUnsavedChangesGuard(dirty)
```

**Target (D-03/D-04):**
```javascript
  const yamlDirty = yaml !== savedYaml
  const sourceFormDirty = sourceId.trim() !== '' || label.trim() !== ''
  const dirty = yamlDirty || sourceFormDirty
  const blocker = useUnsavedChangesGuard(dirty) // still ONE call
```

**Structured error rendering** (lines 267–294) — reuse for add-form rejects (`path` + `message`, no `line`):
```javascript
      {rejected ? (
        <div data-testid="pipeline-config-errors" role="alert" className="...">
          <h2 className="font-sans text-2xl font-semibold ...">
            Проверьте конфиг перед сохранением
          </h2>
          ...
                  {errorPrefix(error) ? (
                    <span className="font-mono">{errorPrefix(error)}</span>
                  ) : null}
                  {String(error?.message ?? '')}
```

**Dialog wiring** (lines 331–335) — keep single modal:
```javascript
      <UnsavedChangesDialog
        open={blocker.state === 'blocked'}
        onStay={() => blocker.reset()}
        onLeave={() => blocker.proceed()}
      />
```

**Placement (D-02):** render `IngestSourcesSection` **above** the YAML empty/editor/toolbar stack; page hint stays first.

---

### `web/src/components/IngestSourcesSection.jsx` (component, immediate CRUD)

**Analog:** Extract chrome from `AdminPipelineConfigPage.jsx` (form fields, `min-h-11`, `rounded-2xl` / `border-rule`, mono, alert panel). Secondary: `web/src/components/ErrorPanel.jsx` for generic load/action failures.

**ErrorPanel shell** (lines 1–12):
```javascript
export default function ErrorPanel({ title, message, meta, onDismiss }) {
  return (
    <div
      role="alert"
      className="mr-auto w-full max-w-md rounded-xl border border-[oklch(70%_0.12_25)] bg-[oklch(96%_0.03_25)] p-4 ..."
    >
```

**No exact child-section analog** — first extracted admin section on this page. Lift list + form dirty fields to the page so the single `dirty` OR stays obvious (RESEARCH discretion). Copy strings from `23-UI-SPEC.md` Copywriting Contract. Ban D-22 words. `data-testid`s from UI-SPEC host contract.

---

### `tests/unit/test_phase23_migration_012.py` (test)

**Analog:** `tests/unit/test_phase16_migration_011.py` (full file pattern):
```python
_MIGRATION = "supabase-integration/migrations/011_phase16_pipeline_config.sql"

def _text() -> str:
    path = Path(_MIGRATION)
    assert path.exists(), f"migration missing: {_MIGRATION}"
    return path.read_text(encoding="utf-8")

def test_migration_011_enables_rls_with_no_permissive_policy() -> None:
    lower = _text().lower()
    assert "enable row level security" in lower
    assert "create policy" not in lower

def test_migration_011_has_no_wipe_statements() -> None:
    lower = _text().lower()
    assert "\ntruncate " not in lower
    assert "\ndelete from" not in lower
```

**Copy:** Point at `012_phase23_ingest_sources.sql`; assert `pipeline_ingest_sources`, identity PK, `unique (kind, source_id)`, kind check, RLS, no wipe. Do **not** edit `test_schema_migration_contract.py` / `001` (D-23).

---

### `tests/unit/test_http_ingest_sources.py` (test)

**Analog:** `tests/unit/test_http_pipeline_config.py`

**ES256 JWT + container attach harness** (lines 44–127):
```python
ISSUER = "https://auth.example/auth/v1"
CONFIG_URL = "/admin/pipeline/config"
...
def _admin_env(*, config=None, attach_repo=True, attach_validator=True):
    private_key = ec.generate_private_key(ec.SECP256R1())
    jwk = _public_jwk(private_key)
    container = build_in_memory_container()
    container.pipeline_config = (
        InMemoryPipelineConfigRepository(config) if attach_repo else None
    )
    ...
    return client, {"Authorization": f"Bearer {token}"}, container
```

**400 + zero writes** (lines 224–245 pattern):
```python
    assert response.status_code == 400
    body = response.json()
    assert "detail" not in body
    assert body["errors"] == [...]
    assert container.pipeline_config.save_count == 0
```

**Admin gate / 503 not_configured** (lines 248–317) — mirror for ingest paths and `ingest_sources_not_configured`.

**Copy:** New file; do **not** edit `test_http_pipeline_config.py` (D-23 PRESERVE). Cover list/add/patch/delete, regex/kind/label/duplicate rejects, zero writes, require_admin.

---

### `tests/unit/test_supabase_ingest_source_repository_contract.py` (test)

**Analog:** `tests/unit/test_supabase_pipeline_config_repository_contract.py`

**Offline FakeSupabaseClient + PersistenceError + `__all__`** (lines 16–83, 127–169):
```python
class FakeSupabaseClient:
    def __init__(self) -> None:
        self.tables: dict[str, _FakeTable] = {
            "pipeline_config": _FakeTable("pipeline_config"),
        }
...
def test_repository_is_exported_from_package() -> None:
    import supabase_integration
    assert "SupabasePipelineConfigRepository" in supabase_integration.__all__
```

**Copy:** Fake table `pipeline_ingest_sources`; extend fake query for `insert` / `update` / `delete` as needed; assert export of `SupabaseIngestSourceRepository`.

---

### `tests/unit/test_live_container_wiring.py` + `test_composition_container.py` (AMEND)

**Analog:** `test_live_container_wiring.py` lines 93–130:
```python
    assert isinstance(container.pipeline_config, SupabasePipelineConfigRepository)
    assert not isinstance(container.pipeline_config, InMemoryPipelineConfigRepository)
...
def test_build_live_container_wires_pipeline_config(...):
    ...
    assert isinstance(container.pipeline_config, SupabasePipelineConfigRepository)
```

**Copy (D-24):** Assert `ingest_sources` is `SupabaseIngestSourceRepository` live / `InMemoryIngestSourceRepository` in-memory. Additive only.

---

### `tests/admin.spec.js` (AMEND — journey + dirty; D-22 PRESERVE)

**Analog:** same file — pipeline describes (~1296–1814)

**Dirty-guard journey pattern** (lines 1459–1477 init-script style; 1540+ in-app nav):
```javascript
  test("pipeline config dirty gating arms the unsaved-leave guard", async ({ page }) => {
    await page.addInitScript(() => { ... beforeunload registry ... });
    await gotoAsRole(page, "admin", "/admin/pipeline");
    ...
  });
```

**Tripwire — PRESERVE byte-identical** (lines 1804–1813, D-22):
```javascript
  test("pipeline config no execution controls render", async ({ page }) => {
    await gotoAsRole(page, "admin", "/admin/pipeline");
    const pageText = await page.getByTestId("admin-pipeline-page").innerText();
    for (const banned of ["Запустить", "Выполнить", "Запуск", "Планировщик", "Расписание"]) {
      expect(pageText).not.toContain(banned);
    }
    ...
  });
```

**Copy:** Add describe for sources journey (add → row → disable → delete) + add-form dirty prompts (kind-only does **not** arm). Do **not** edit the tripwire body. Import/reset `ingestSourcesApi` harness like pipeline mock arms.

## Shared Patterns

### Authentication / admin gate
**Source:** `backend/src/backend/interface/http/routes/admin.py` + `backend.interface.http.deps.require_admin`
**Apply to:** All four ingest-source routes
```python
_admin: CurrentUser = Depends(require_admin)
```
Plus `_require_*` 503 when container field is `None` (mirror `_require_pipeline_config`, lines 203–210).

### Error handling — top-level `{errors:[…]}` 400
**Source:** `admin.py` lines 643–648 + `PipelineConfigError.to_dict()` (`domain/pipeline_config.py` 38–42)
**Apply to:** POST add rejects (id/kind/label/duplicate)
```python
return JSONResponse(
    status_code=status.HTTP_400_BAD_REQUEST,
    content={"errors": [error.to_dict() for error in exc.errors]},
)
```
Never nest under `detail`. Zero repository writes on reject.

### PersistenceError → 503
**Source:** `admin.py` lines 609–613 / 650–654
**Apply to:** All ingest-source routes
```python
detail="ingest_sources_unavailable"  # or not_configured when repo missing
```

### Composition-only wiring
**Source:** `composition/container.py`, `composition/live.py`
**Apply to:** `ingest_sources` field — never construct Supabase client in use cases or SPA.

### SPA service boundary
**Source:** `web/src/services/pipelineConfigApi.js`
**Apply to:** `ingestSourcesApi.js` only; components never fetch `/admin/ingest-sources` directly.

### Unsaved-changes guard (ADUX-10)
**Source:** `useUnsavedChangesGuard.js`, `UnsavedChangesDialog.jsx`, `unsavedChangesGuard.js`
**Apply to:** Page dirty OR only — **do not** instantiate a second blocker/dialog
```javascript
export const UNSAVED_LEAVE_CONFIRM =
  'Есть несохранённые изменения. Уйти без сохранения?'
```

### Validation (Pydantic DTOs)
**Source:** Admin DTOs with `ConfigDict(extra="forbid")` (`admin.py` 176–180)
**Apply to:** Create/patch request bodies → unknown fields 422.

### TDD / RED split (D-20)
**Source:** Phase 18/16 precedent via `test_http_pipeline_config.py` + Playwright journey
**Apply to:** pytest owns regex/400/zero-writes; Playwright owns UI journey + dirty guard. Mocks cannot prove server reject.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `web/src/components/IngestSourcesSection.jsx` (as a **dedicated child section**) | component | CRUD | No existing extracted section under `AdminPipelineConfigPage`; closest chrome is the page itself + `ErrorPanel`. Planner should treat as **role-match** to the page, not invent a new design system. |
| Admin `DELETE → 204` response | route | request-response | No existing admin route returns 204; use FastAPI `Response` (already imported in `admin.py`). Pattern is standard FastAPI, not project-local. |

## Metadata

**Analog search scope:** `backend/src/backend/{domain,application,composition,interface/http/routes,tests_support}`, `supabase-integration/{migrations,src}`, `web/src/{services,pages,components,hooks,utils}`, `tests/unit`, `tests/admin.spec.js`
**Files scanned:** ~45 tracked analogs (git `ls-files` verified for every named path)
**Pattern extraction date:** 2026-10-17
**Tracked-source gate:** all analogs confirmed via `git ls-files` (non-empty)
