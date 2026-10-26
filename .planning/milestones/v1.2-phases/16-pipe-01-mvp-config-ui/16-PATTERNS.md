# Phase 16: PIPE-01 MVP config UI - Pattern Map

**Mapped:** 2026-10-04
**Files analyzed:** 20 (17 new/extended from RESEARCH.md + 3 implied wiring/CLI files)
**Analogs found:** 20 / 20 (all tracked-source verified via `git ls-files`)

> This is a Ports & Adapters repo. Every new persistence/validation capability follows the
> same chain: **domain model → port (`Protocol`) → in-memory fake → live adapter → composition
> wiring → thin HTTP route → SPA service → page**. Each section below names the closest tracked
> analog and the concrete lines to copy.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `backend/src/backend/domain/pipeline_config.py` | model | transform | `backend/src/backend/domain/shortlist.py` | role-match |
| `backend/src/backend/domain/errors.py` (extend) | error-type | n/a | `backend/src/backend/domain/errors.py` (`DraftInSendPoolError`) | self |
| `backend/src/backend/application/ports/pipeline_config_repository.py` | port | CRUD | `backend/src/backend/application/ports/shortlist_repository.py` | exact |
| `backend/src/backend/application/ports/pipeline_config_validator.py` | port | transform | `backend/src/backend/application/ports/query_embedder.py` | role-match |
| `backend/src/backend/application/use_cases/get_pipeline_config.py` | use-case | request-response | `backend/src/backend/application/use_cases/get_admin_shortlist.py` | exact |
| `backend/src/backend/application/use_cases/save_pipeline_config.py` | use-case | CRUD + validate | `backend/src/backend/application/use_cases/set_shortlist_decision.py` | role-match |
| `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` | adapter (infra) | transform | none (novel) — see RESEARCH Patterns 1–2 | none |
| `backend/src/backend/composition/container.py` (extend) | composition | wiring | `backend/src/backend/composition/container.py` | self |
| `backend/src/backend/composition/live.py` (extend) | composition | wiring | `backend/src/backend/composition/live.py` | self |
| `backend/src/backend/interface/http/routes/admin.py` (extend) | controller | request-response | `backend/src/backend/interface/http/routes/admin.py` | self |
| `backend/src/backend/tests_support/in_memory.py` (extend) | test-double | CRUD | `InMemoryShortlistRepository` / `InMemoryProfileRepository` | exact |
| `supabase-integration/migrations/011_phase16_pipeline_config.sql` | migration | config | `001_initial_schema.sql` (RLS) + `010` (header) | role-match |
| `supabase-integration/src/supabase_integration/pipeline_config_repository.py` | adapter | CRUD | `supabase-integration/src/supabase_integration/profile_repository.py` | exact |
| `supabase-integration/src/supabase_integration/__init__.py` (extend) | config | wiring | `supabase-integration/src/supabase_integration/__init__.py` | self |
| `web/src/pages/AdminPipelineConfigPage.jsx` | component | request-response | `web/src/pages/AdminDigestPage.jsx` | role-match |
| `web/src/services/pipelineConfigApi.js` | service | request-response | `web/src/services/adminApi.js` | exact |
| `web/src/components/AppShell.jsx` (extend) | component | n/a | `web/src/components/AppShell.jsx` | self |
| `web/src/App.jsx` (extend) | route | n/a | `web/src/App.jsx` | self |
| `web/src/main.jsx` (extend) | config | harness | `web/src/main.jsx` | self |
| `backend/src/backend/interface/http/app.py` (extend, CORS PUT) | config | n/a | `backend/src/backend/interface/http/app.py` | self |
| `tests/unit/test_pipeline_config_validator.py` | test | n/a | `tests/unit/test_supabase_shortlist_repository_contract.py` (fake-client) | partial |
| `tests/unit/test_http_pipeline_config.py` | test | n/a | `tests/unit/test_http_admin.py` | exact |
| `tests/unit/test_phase16_migration_011.py` | test | n/a | `tests/unit/test_phase5_migration_005.py` | exact |
| `tests/admin.spec.js` (extend) | test (e2e) | n/a | `tests/admin.spec.js` (`gotoAsRole`) | self |

---

## Pattern Assignments

### `backend/src/backend/application/ports/pipeline_config_repository.py` (port, CRUD)

**Analog:** `backend/src/backend/application/ports/shortlist_repository.py`

**Imports + Protocol shape** (lines 1-13):
```python
from __future__ import annotations

from datetime import datetime
from typing import Protocol

from backend.domain.shortlist import ShortlistBatch


class ShortlistRepository(Protocol):
    def get_current_batch(self) -> ShortlistBatch | None:
        """..."""
        ...
```

**Port method style** (lines 21-39) — keyword-only options, docstring per method, `-> DomainType`:
```python
    def set_decision(
        self,
        *,
        batch_id: int,
        material_id: int,
        decision: str,
        actor_user_id: str,
        decided_at: datetime,
    ) -> ShortlistBatch:
        """Persist shortlist_decision for one material; return updated batch (D-82)."""
        ...
```

**Apply to Phase 16:** define `PipelineConfigRepository(Protocol)` with `get() -> PipelineConfig | None`
and `save(*, yaml: str, updated_at: datetime) -> PipelineConfig` (RESEARCH Pattern 3). One module,
`{noun}_repository.py`, no SDK imports.

---

### `backend/src/backend/application/ports/pipeline_config_validator.py` (port, transform)

**Analog:** `backend/src/backend/application/ports/query_embedder.py`

This is the repo's existing **non-repository capability port** (a pure transformation contract,
not persistence). Copy its form:

**Full file is short** (lines 10-11):
```python
class QueryEmbedder(Protocol):
    def embed(self, text: str) -> list[float]: ...
```

**Apply to Phase 16:** `class PipelineConfigValidator(Protocol): def validate(self, yaml_text: str) -> None: ...`
The validator raises `PipelineConfigValidationError`; it never returns data. Keep `yaml` out of the
port signature (the adapter owns PyYAML). This is what keeps `yaml` out of `use_cases/`.

---

### `backend/src/backend/domain/pipeline_config.py` (model, transform)

**Analog:** `backend/src/backend/domain/shortlist.py`

**Frozen dataclass convention** (lines 44-70):
```python
@dataclass(frozen=True)
class ShortlistItem:
    material_id: int
    rank: int
    title: str
    material_status: str
    decision: str
    score: float | None
    score_factors: Mapping[str, Any]
    decided_by: str | None = None
    ...

@dataclass(frozen=True)
class ShortlistBatch:
    id: int
    week_start: date
    sent_at: datetime | None
    items: tuple[ShortlistItem, ...]
```

**Apply to Phase 16:** `@dataclass(frozen=True) class PipelineConfig: yaml: str; updated_at: datetime | None`
and `@dataclass(frozen=True) class PipelineConfigError: path: str; message: str; line: int | None = None`
with a `to_dict()` that omits `line` when `None` (RESEARCH Code Examples). Module docstring cites
`PIPE-01/02/03` + `D-01…D-13` (see `shortlist.py:1`).

---

### `backend/src/backend/domain/errors.py` (extend — error-type)

**Analog:** same file, admin/digest cluster.

**Domain-error convention with attached payload** (lines 145-150):
```python
class DraftInSendPoolError(DomainError):
    """Raised when any approved shortlist item is still draft (ADMIN-03, D-85)."""

    def __init__(self, draft_material_ids: list[int], *, batch_id: int | None = None) -> None:
        ids = list(draft_material_ids)
        super().__init__(f"approved drafts in send pool: {ids}")
        self.draft_material_ids = ids
        self.batch_id = batch_id
```

**Apply to Phase 16:** append `PipelineConfigValidationError(DomainError)` carrying
`self.errors: tuple[PipelineConfigError, ...]` (RESEARCH Code Examples). Do **not** add an
HTTP status to the domain error — status lives in the route (see Shared Patterns → per-route mapping).

---

### `backend/src/backend/application/use_cases/get_pipeline_config.py` (use-case, request-response)

**Analog:** `backend/src/backend/application/use_cases/get_admin_shortlist.py`

**Read use-case shape** (lines 14-34):
```python
def get_admin_shortlist(shortlist: ShortlistRepository) -> AdminShortlist:
    batch = shortlist.get_current_batch()
    if batch is None:
        latest = shortlist.get_latest_batch()
        if latest is not None and latest.sent_at is not None:
            return AdminShortlist(
                batch_id=None,
                items=(),
                digest_rest=True,
                ...
            )
        return AdminShortlist(...)
    ...
```

**Apply to Phase 16:**
```python
def get_pipeline_config(repo: PipelineConfigRepository) -> PipelineConfig | None:
    return repo.get()
```
Module docstring cites requirement IDs; port injected as first positional parameter.

---

### `backend/src/backend/application/use_cases/save_pipeline_config.py` (use-case, CRUD + validate)

**Analog:** `backend/src/backend/application/use_cases/set_shortlist_decision.py`

**Validate-then-persist shape** (lines 12-43) — the closest existing "reject before write" use-case:
```python
_ALLOWED_DECISIONS = frozenset({"pending", "approved", "rejected"})


def set_shortlist_decision(
    shortlist: ShortlistRepository,
    *,
    material_id: int,
    decision: str,
    actor_user_id: str,
    now: datetime | None = None,
) -> AdminShortlist:
    decision_key = (decision or "").strip()
    if decision_key not in _ALLOWED_DECISIONS:
        raise InvalidShortlistDecisionError(decision)

    batch = shortlist.get_current_batch()
    if batch is None:
        raise ShortlistNotFoundError()
    ...
    shortlist.set_decision(
        batch_id=batch.id,
        material_id=material_id,
        decision=decision_key,
        actor_user_id=actor_user_id,
        decided_at=clock,
    )
    return get_admin_shortlist(shortlist)
```

**Apply to Phase 16:**
```python
def save_pipeline_config(
    repo: PipelineConfigRepository,
    validator: PipelineConfigValidator,
    *,
    yaml_text: str,
    now: datetime | None = None,
) -> PipelineConfig:
    validator.validate(yaml_text)          # raises PipelineConfigValidationError BEFORE any write
    return repo.save(yaml=yaml_text, updated_at=now or datetime.now(timezone.utc))
```
The use-case imports only ports + domain; PyYAML/Pydantic stay in the infrastructure adapter.

---

### `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` (adapter, transform)

**No analog found in the repo** — there is no existing YAML or schema validator. Do **not** invent a
pattern; implement from RESEARCH.md precisely:

- **Pattern 1** (RESEARCH lines 206-236): `_StrictSafeLoader(yaml.SafeLoader)` overriding
  `construct_mapping` to raise `yaml.constructor.ConstructorError` on duplicate keys; catch
  `yaml.MarkedYAMLError`, map `exc.problem_mark.line + 1` (0-based → 1-based).
- **Pattern 2** (RESEARCH lines 243-270): Pydantic `ConfigDict(extra="forbid")` model +
  `loc_to_dot_sep`; catch `ValidationError` → one `PipelineConfigError(path=dotted, line=None, message=msg)`.
- Also handle `None` (empty doc) and non-string top-level keys (RESEARCH Pitfalls 4-5).

**Boundary rule (from `architecture.mdc`):** this file is the *only* place `import yaml` appears.
`PersistenceError`-style mapping is not needed here — parse failures become the domain validation error.

---

### `backend/src/backend/composition/container.py` (extend — composition, wiring)

**Analog:** same file.

**Container dataclass + memory wiring** (lines 45-121):
```python
@dataclass
class AppContainer:
    materials: MaterialRepository
    ...
    publisher: DigestPublisher

def build_in_memory_container(...) -> AppContainer:
    ...
    container = AppContainer(
        materials=materials_repo,
        ...
        shortlist=shortlist_repo,
        mailer=StubMailer(),
        publisher=None,  # type: ignore[arg-type]
    )
    container.publisher = InMemoryDigestPublisher(...)
    return container
```

**Apply to Phase 16:**
- Add `pipeline_config: PipelineConfigRepository` and `pipeline_config_validator: PipelineConfigValidator`
  as **new fields with defaults** (`= None` or a default fake) — Pitfall 6: the direct `AppContainer(...)`
  construction in `tests/unit/test_http_knowledge_search.py:100-113` would otherwise break with
  `TypeError: missing required keyword argument`.
- Wire `InMemoryPipelineConfigRepository()` + `InMemoryPipelineConfigValidator()` in
  `build_in_memory_container`.

---

### `backend/src/backend/composition/live.py` (extend — composition, wiring)

**Analog:** same file.

**Live wiring shape** (lines 26-61):
```python
def build_live_container(settings: Settings) -> AppContainer:
    if not settings.supabase_url or not settings.supabase_secret_key:
        raise ValueError(...)
    # service_role: RLS bypass for content reads + activity_events / profiles (T-02-03)
    admin_client = create_service_role_client(
        settings.supabase_url,
        settings.supabase_secret_key,
    )
    ...
    return AppContainer(
        materials=SupabaseMaterialRepository(admin_client),
        ...
        shortlist=SupabaseShortlistRepository(admin_client),
        mailer=resolve_mailer(settings.mailer),
        publisher=SupabaseDigestPublisher(admin_client),
    )
```

**Apply to Phase 16:** `pipeline_config=SupabasePipelineConfigRepository(admin_client)` and the
production `YamlPipelineConfigValidator()`; add the import to the `from supabase_integration import (...)`
block (lines 10-22). Never construct a client anywhere else.

---

### `backend/src/backend/interface/http/routes/admin.py` (extend — controller, request-response)

**Analog:** same file. This single file holds every pattern the new routes need.

**Request/response DTOs with `extra="forbid"`** (lines 71-77):
```python
class SetShortlistDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str = Field(
        ...,
        min_length=1,
        description="shortlist_decision: pending|approved|rejected (D-82; allowlist in use-case)",
    )
```

**503 guard helper** (lines 167-175):
```python
def _require_shortlist(request: Request):
    container = request.app.state.container
    if container is None or getattr(container, "shortlist", None) is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_not_configured",
        )
    return container.shortlist
```

**Route + `require_admin` + per-route domain→HTTP mapping** (lines 325-364):
```python
@router.post(
    "/shortlist/items/{material_id}/decision",
    response_model=AdminShortlistResponse,
    summary="Set shortlist decision for one material",
    description="... Requires admin. ... Unknown material → 404; invalid body → 400; ...",
)
def post_shortlist_decision(
    material_id: int,
    body: SetShortlistDecisionRequest,
    request: Request,
    admin: CurrentUser = Depends(require_admin),
) -> AdminShortlistResponse:
    shortlist = _require_shortlist(request)
    try:
        dto = set_shortlist_decision(...)
    except InvalidShortlistDecisionError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid_decision",
        ) from exc
    except PersistenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="shortlist_unavailable",
        ) from exc
    return _to_response(dto)
```

**Structured (non-`detail`) error payload precedent** (lines 454-466) — closest existing shape to D-05:
```python
    except DraftInSendPoolError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "draft_in_send_pool",
                "draft_material_ids": exc.draft_material_ids,
            },
        ) from exc
```

**Apply to Phase 16** (RESEARCH Pattern 4 — **not** `HTTPException(detail=...)` for the config reject):
```python
from fastapi.responses import JSONResponse

@router.put("/pipeline/config")
def put_pipeline_config(body: PipelineConfigSaveRequest, request: Request,
                        _admin: CurrentUser = Depends(require_admin)):
    repo = _require_pipeline_config(request)
    try:
        cfg = save_pipeline_config(repo, request.app.state.container.pipeline_config_validator,
                                   yaml_text=body.yaml)
    except PipelineConfigValidationError as exc:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={"errors": [e.to_dict() for e in exc.errors]})
    return PipelineConfigResponse(yaml=cfg.yaml, updated_at=cfg.updated_at)
```
Also add a `_require_pipeline_config(request)` 503 guard modelled on `_require_shortlist`
(RESEARCH lines 294-305). GET mirrors the read route (lines 300-322).

**Route docstrings** carry requirement IDs + status contract (see the existing `description=` text).

---

### `backend/src/backend/tests_support/in_memory.py` (extend — test-double, CRUD)

**Analog:** same file — `InMemoryShortlistRepository` (lines 178-292) and
`InMemoryProfileRepository` (lines 299-326).

**Fake repository shape** (lines 178-215):
```python
class InMemoryShortlistRepository:
    """In-memory ShortlistRepository — empty by default (D-80)."""

    def __init__(self, batch: ShortlistBatch | None = None, ...) -> None:
        self._batch = batch
        ...

    def get_current_batch(self) -> ShortlistBatch | None:
        if self._batch is None or self._batch.sent_at is not None:
            return None
        return self._overlay_batch(self._batch)

    def seed(self, batch: ShortlistBatch | None) -> None:
        self._batch = batch

    def set_decision(self, *, batch_id: int, ...) -> ShortlistBatch:
        ...
```

**Simple dict-backed fake** (lines 299-311):
```python
class InMemoryProfileRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, CurrentUser] = {}

    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser:
        ...
```

**Apply to Phase 16:**
```python
class InMemoryPipelineConfigRepository:
    """In-memory PipelineConfigRepository — absent by default (D-11 empty state)."""
    def __init__(self, config: PipelineConfig | None = None) -> None:
        self._config = config
    def get(self) -> PipelineConfig | None:
        return self._config
    def save(self, *, yaml: str, updated_at: datetime) -> PipelineConfig:
        self._config = PipelineConfig(yaml=yaml, updated_at=updated_at)
        return self._config
```
Add a `InMemoryPipelineConfigValidator` that records calls / can be armed to raise
`PipelineConfigValidationError` (structural duck-typing — no inheritance, see CONVENTIONS §Module Design).

---

### `supabase-integration/src/supabase_integration/pipeline_config_repository.py` (adapter, CRUD)

**Analog:** `supabase-integration/src/supabase_integration/profile_repository.py` (get/upsert) and
`shortlist_repository.py` (`_parse_dt` / `_iso` helpers).

**Client protocol + boundary error mapping** (profile_repository lines 5-80):
```python
from typing import Any, Protocol
from backend.domain.errors import PersistenceError

class _SupabaseClient(Protocol):
    def table(self, name: str) -> Any: ...

class SupabaseProfileRepository:
    def __init__(self, client: _SupabaseClient) -> None:
        self._client = client

    def get_or_upsert(self, user_id: str, email: str) -> CurrentUser:
        try:
            existing = (
                self._client.table("profiles")
                .select("id,email,role,display_name")
                .eq("id", user_id)
                .execute()
            )
            rows = getattr(existing, "data", None) or []
            if rows:
                return _row_to_user(rows[0])
            upserted = (
                self._client.table("profiles")
                .upsert({...})
                .execute()
            )
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"profiles get_or_upsert failed: {exc}") from exc
        data = getattr(upserted, "data", None) or []
        ...
```

**Timestamp helpers** (shortlist_repository lines 15-33) — reuse, do not re-implement:
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

**Apply to Phase 16:** `SupabasePipelineConfigRepository.get()` selects `yaml,updated_at` where
`id == 1`, returns `None` when no row (empty state); `save()` upserts `{"id": 1, "yaml": ..., "updated_at": _iso(...)}`
(RESEARCH Code Examples lines 455-485). Map SDK failures → `PersistenceError` at the boundary.

`supabase-integration/src/supabase_integration/__init__.py` (extend): add the import +
`__all__` entry alongside `SupabaseProfileRepository` (lines 1-35).

---

### `supabase-integration/migrations/011_phase16_pipeline_config.sql` (migration, config)

**Analog:** `supabase-integration/migrations/001_initial_schema.sql` (RLS convention) +
`010_phase13_scrub_test_header.sql` (header/comment + "never reset" convention).

**RLS convention** (001_initial_schema.sql lines 241-258) — tables enable RLS; there is **no admin
`create policy`** anywhere (deny-by-default + `service_role` backend bypass):
```sql
alter table profiles enable row level security;
alter table ingestion_sources enable row level security;
...
alter table activity_events enable row level security;
```

**File header convention** (010 lines 1-5):
```sql
-- Phase 13: defensive scrub of closed ban tokens from materials text (ADUX-04, D-20).
-- ... Idempotent UPDATE — 0-row apply is OK when live rows are already clean.
-- Shared VM: apply once via Studio SQL / psql / supabase db push — never reset.
```

**Apply to Phase 16** (RESEARCH Code Examples lines 434-452): create-if-not-exists singleton
`public.pipeline_config(id integer primary key default 1 check (id = 1), yaml text not null default '',
updated_at timestamptz not null default now())`, then `alter table public.pipeline_config enable row
level security;` with **no** permissive policy. No wipe statements (asserted by the migration test).

---

### `web/src/services/pipelineConfigApi.js` (service, request-response)

**Analog:** `web/src/services/adminApi.js` — the exact template.

**Typed error class** (lines 23-31):
```js
export class AdminApiError extends Error {
  constructor(message, { code = 'ADMIN_FAILED', retryable = true, detail = null } = {}) {
    super(message)
    this.name = 'AdminApiError'
    this.code = code
    this.retryable = retryable
    this.detail = detail
  }
}
```

**Mock/live cutover + no silent fallback** (lines 58-60, 216-232):
```js
function useMocks() {
  return isMocksEnabled()
}
...
function mapHttpError(response, fallbackMessage) {
  if (response.status === 403) {
    return new AdminApiError('Недостаточно прав.', { code: 'FORBIDDEN', retryable: false })
  }
  ...
  if (response.status === 400) {
    return new AdminApiError(fallbackMessage, { code: 'BAD_REQUEST', retryable: false })
  }
  ...
  return new AdminApiError(fallbackMessage, { code: 'NETWORK', retryable: true })
}
```

**Live fetch + token + mapper** (lines 279-301):
```js
  const token = accessToken ?? (await getAccessToken())
  if (!token) {
    throw new AdminApiError('Требуется вход.', { code: 'UNAUTHORIZED', retryable: false })
  }

  let response
  try {
    response = await fetch(`${apiBase()}/admin/shortlist`, {
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch {
    throw new AdminApiError('Не удалось загрузить shortlist. Проверьте сеть.', {
      code: 'NETWORK', retryable: true,
    })
  }
  if (!response.ok) {
    throw mapHttpError(response, 'Не удалось загрузить shortlist. Проверьте сеть.')
  }
```

**Apply to Phase 16** (RESEARCH Code Examples lines 489-505): `PipelineConfigError` with an
extra `errors` field; `fetchPipelineConfig(accessToken)` (empty → `{ yaml: '', updated_at: null }`);
`savePipelineConfig(yaml, accessToken)` — on 400 read `body.errors` (→ `INVALID_CONFIG`, `retryable:false`),
422 → generic non-retryable, 5xx/network → retryable. Always route through `getAccessToken()` +
`apiBase()` + `isMocksEnabled()`; never a silent mock fallback after a live failure.

---

### `web/src/pages/AdminPipelineConfigPage.jsx` (component, request-response)

**Analog:** `web/src/pages/AdminDigestPage.jsx`.

**Role gate + page shell** (AdminDigestPage lines 132-160 and 518-527):
```jsx
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import ForbiddenPage from './ForbiddenPage.jsx'
import { getAccessToken } from '../services/authApi.js'
import { MeApiError, fetchMe } from '../services/meApi.js'
...
      try {
        const token = await getAccessToken()
        const me = await fetchMe(token)
        if (!cancelled) {
          setRoleState(me.role === 'admin' ? 'admin' : 'forbidden')
        }
      } catch (err) {
        if (cancelled) return
        if (
          err instanceof MeApiError &&
          (err.code === 'UNAUTHORIZED' || err.code === 'FORBIDDEN')
        ) {
          setRoleState('forbidden')
        } else {
          setRoleState('error')
        }
      }
...
  return (
    <section data-testid="admin-digest-page" className="pb-32">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>
      <h1 className="mt-2 font-sans text-3xl font-semibold text-ink">Shortlist дайджеста</h1>
```

**Admin `<textarea>` chrome + states** (lines 592-604) — the editor/label/hint pattern:
```jsx
              <label className="mt-4 block text-sm">
                <span className="font-medium text-ink-2">Вводный текст</span>
                <textarea
                  className="mt-2 min-h-28 w-full rounded-xl border border-rule bg-paper p-3 text-sm"
                  value={contextText}
                  onChange={(e) => setContextText(e.target.value)}
                  rows={5}
                />
                <span className="mt-1 block text-xs text-muted">Пустая строка = новый абзац</span>
              </label>
```

**Apply to Phase 16:** mirror the page shape with `data-testid="admin-pipeline-page"`, eyebrow
«Админ», H1 «Конфиг пайплайна», subhead «Просмотр и правка без запуска пайплайна». Load state
machine `loading | ready | empty | error` (AdminDigestPage `loadState`/`loadKey` idempotent-retry
effect, lines 171-195). Editor/panel/toolbar testids + copy come from `16-UI-SPEC.md`
(`pipeline-config-editor`, `-save`, `-reload`, `-status`, `-errors`, `-error`, `-empty`, `-retry`).
Reject → render `errors[]` above the editor (`role="alert"`), keep dirty; failure → `ErrorPanel`
with retry. **No run/trigger/scheduler control** (UI-SPEC hard boundary).

---

### `web/src/components/AppShell.jsx` (extend — component)

**Analog:** same file.

**Admin nav gate** (lines 86-90):
```jsx
            {appRole === 'admin' ? (
              <NavLink to="/admin/digest" className={linkClass}>
                Админ
              </NavLink>
            ) : null}
```

**Apply to Phase 16:** add one more `appRole === 'admin'` `NavLink` to `/admin/pipeline` labelled
«Пайплайн» using the same `linkClass` pill (no second nav bar).

---

### `web/src/App.jsx` (extend — route)

**Analog:** same file.

**Admin route** (lines 37-39):
```jsx
          <Route path="admin/digest" element={<AdminDigestPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
```

**Apply to Phase 16:** import `AdminPipelineConfigPage` and add
`<Route path="admin/pipeline" element={<AdminPipelineConfigPage />} />` inside the existing
`RequireAuth`/`AppShell` group.

---

### `web/src/main.jsx` (extend — harness)

**Analog:** same file.

**Harness exposure** (lines 46-56):
```jsx
window.__DIGEST_ADMIN_HARNESS__ = {
  armFailNextShortlistFetch,
  clearFailNextShortlistFetch,
  armFailNextDecision,
  armFailNextPreview,
  clearFailNextPreview,
  armFailNextSend,
  armAlreadySentOnSend,
  resetAdminHarness,
  getMockMarkReadyBatchCalls,
}
```

**Apply to Phase 16:** expose `window.__DIGEST_PIPELINE_CONFIG_HARNESS__ = { armFailNextLoad,
armRejectNextSave, resetPipelineConfigHarness }` from `pipelineConfigApi.js` (Playwright needs the
reset hook in `gotoAsRole`, see below).

---

### `backend/src/backend/interface/http/app.py` (extend — CORS PUT)

**Analog:** same file.

**CORS allow-list** (lines 41-47):
```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
```

**Apply to Phase 16 (RESEARCH Pitfall 1):** add `"PUT"` to `allow_methods`, otherwise the live
browser preflight fails only in live mode (mock Playwright stays green). Extend `test_cors.py` with a
`PUT` preflight assertion.

---

### `tests/unit/test_http_pipeline_config.py` (test)

**Analog:** `tests/unit/test_http_admin.py` — copy the harness verbatim.

**ES256 JWT + resolver harness** (lines 27-76):
```python
def _public_jwk(private_key: ec.EllipticCurvePrivateKey) -> dict[str, Any]:
    data = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    data["kid"] = "test-kid-1"
    ...
    return data

def _mint(private_key, *, email, sub="user-uuid-1", role="authenticated") -> str:
    now = int(time.time())
    return jwt.encode({...}, private_key, algorithm="ES256", headers={"kid": "test-kid-1"})

def _client(signing_jwk: dict[str, Any], container: AppContainer) -> TestClient:
    settings = Settings(api_cors_origins="http://127.0.0.1:5173", ...)
    app = create_app(settings, container=container, signing_key_resolver=lambda _token: signing_jwk)
    return TestClient(app)

def _seed_profile(container: AppContainer, *, user_id: str, email: str, role: str) -> None:
    container.profiles._by_id[user_id] = CurrentUser(id=user_id, email=email, role=role, display_name=None)
```

**Auth-gate assertions** (lines 124-149): unauthenticated → 401; employee profile → 403 with
`response.json()["detail"] == "forbidden"` and no data key.

**Apply to Phase 16:** reuse `_public_jwk`/`_mint`/`_client`/`_seed_profile`; swap
`container.pipeline_config = InMemoryPipelineConfigRepository(...)` post-build (same trick as
`container.shortlist = ...`). Cover: GET DTO, empty state, valid save round-trip, unknown key →
top-level `{"errors":[...]}` (assert `"detail" not in body`), 503 guard, non-admin 403 / unauth 401,
and the PIPE-03 boundary guard (no `supabase` import in the page).

---

### `tests/unit/test_phase16_migration_011.py` (test)

**Analog:** `tests/unit/test_phase5_migration_005.py` — exact structural template.

**Full pattern** (lines 8-31):
```python
def test_migration_005_has_delivery_columns_and_demo_seed() -> None:
    path = Path("supabase-integration/migrations/005_phase5_admin_shortlist.sql")
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert "delivery_status" in text
    ...
    # Insert/alter only — no destructive wipe statements (comments may mention TRUNCATE).
    assert "\ntruncate " not in text.lower()
    assert "\ndelete from digest_shortlist" not in text.lower()
```

**Apply to Phase 16:** assert `pipeline_config` exists, `id = 1` singleton CHECK, `enable row level
security`, **no** `create policy`, no `\ntruncate ` / `\ndelete from`. Read the migration as text —
no DB required.

---

### `tests/unit/test_pipeline_config_validator.py` (test)

**Analog:** closest is `tests/unit/test_supabase_shortlist_repository_contract.py` (fake-client
contract style), but the validator is pure — test it directly. Implement the RED behaviors from
RESEARCH Validation Architecture (lines 574-590): syntax reject (with `line`), duplicate key reject,
unknown key reject (`extra_forbidden`), non-string keys, empty doc, valid round-trip.

---

### `tests/admin.spec.js` (extend — e2e)

**Analog:** same file.

**Role harness + reset** (lines 23-49):
```js
async function gotoAsRole(page, role, path = "/", extraInit) {
  await page.addInitScript(
    ({ r, extra }) => {
      window.__DIGEST_MOCK_ME_ROLE__ = r
      ...
    },
    { r: role, extra: extraInit ?? null },
  )
  await page.goto(path)
  if (path.startsWith("/admin")) {
    await page.waitForFunction(() => Boolean(window.__DIGEST_ADMIN_HARNESS__))
    await page.evaluate((extra) => {
      window.__DIGEST_ADMIN_HARNESS__.resetAdminHarness()
      ...
    }, extraInit ?? null)
    await page.reload()
  }
}
```

**Apply to Phase 16:** add a `test.describe("Admin pipeline config …")` block; extend `gotoAsRole`
(and/or the pipeline harness reset) so `/admin/pipeline` resets module-level mock state like the
admin digest path. Cases: editor loads saved YAML; Save disabled while clean; invalid save renders
every error row + keeps dirty; valid save shows «Сохранено»; non-admin → ForbiddenPage; **no
execution control renders** (assert banned strings absent); nav item only for admin.

---

## Shared Patterns

### `require_admin` (all `/admin/pipeline` routes)
**Source:** `backend/src/backend/interface/http/deps.py` lines 53-70
**Apply to:** both `GET` and `PUT` pipeline-config routes (D-10).
```python
def require_admin(
    request: Request,
    claims: AccessTokenClaims = Depends(get_principal),
) -> CurrentUser:
    """Authorize admin from profiles.role only — never JWT role claim (D-74 / AUTH-03)."""
    container = request.app.state.container
    if container is None or getattr(container, "profiles", None) is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="profiles_not_configured")
    user = get_current_user(container.profiles, claims)
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return user
```

### Per-route domain→HTTP mapping (no global handler)
**Source:** `backend/src/backend/interface/http/routes/admin.py` lines 285-323, 350-365, 454-484
**Apply to:** every pipeline-config route.
```python
    except SomeDomainError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="snake_case_code") from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="pipeline_config_unavailable") from exc
```
Exception for the config reject: `PipelineConfigValidationError` returns `JSONResponse(400,
{"errors": [...]})` (D-05) — never `HTTPException(detail=...)` (RESEARCH Pitfall 2).

### Pydantic `extra="forbid"` at the HTTP boundary
**Source:** `backend/src/backend/interface/http/routes/admin.py` lines 41-42, 71-77, 90-127
**Apply to:** `PipelineConfigSaveRequest` (`{yaml: str}`) and all response models.
```python
class SomeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ...
```

### `PersistenceError` boundary mapping
**Source:** `supabase-integration/src/supabase_integration/profile_repository.py` lines 58-70;
`shortlist_repository.py` lines 88-98
**Apply to:** `SupabasePipelineConfigRepository`.
```python
        except PersistenceError:
            raise
        except Exception as exc:  # noqa: BLE001 — map all SDK failures at boundary
            raise PersistenceError(f"pipeline_config get failed: {exc}") from exc
```

### `isMocksEnabled()` cutover + explicit UNAUTHORIZED
**Source:** `web/src/services/adminApi.js` lines 58-60, 216-232, 279-283
**Apply to:** `pipelineConfigApi.js` only (the SPA's sole transport boundary, PIPE-03).
```js
function useMocks() {
  return isMocksEnabled()
}
```

### TDD RED-first (mandatory)
**Source:** `.cursor/rules/tdd.mdc` + AGENTS.md + CONVENTIONS.md lines 183-189
**Apply to:** every behavior in the phase — write the failing `pytest`/Playwright case first, run it,
then implement. Test headers use `"""RED→GREEN: …"""` / requirement-focused docstrings;
fake ports live in `tests_support/in_memory.py`, never network.

### Module-boundary discipline
**Source:** `.planning/codebase/CONVENTIONS.md` lines 101-110; ARCHITECTURE.md lines 83-130
**Apply to:** all backend files.
- `domain/` + `use_cases/` import **no** `fastapi`, `supabase`, `httpx`, `yaml`.
- `yaml`/Pydantic live only in `infrastructure/yaml_pipeline_config_validator.py`.
- Adapters get an injected client; wiring only in `composition/`.
- The SPA calls the API only through `web/src/services/pipelineConfigApi.js` (no Supabase import in pages).

---

## No Analog Found

Files with no close match in the codebase (planner should use `16-RESEARCH.md` patterns instead):

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `backend/src/backend/infrastructure/yaml_pipeline_config_validator.py` | adapter (infra) | transform | No YAML parser / schema validator exists anywhere in the repo; no `yaml` import today. Implement RESEARCH Patterns 1-2 verbatim (strict `SafeLoader` subclass + Pydantic `extra="forbid"` + `loc_to_dot_sep`). |

---

## Metadata

**Analog search scope:** `backend/src/backend/{domain,application/{ports,use_cases},composition,interface/http,infrastructure,tests_support}`, `supabase-integration/{migrations,src}`, `web/src/{pages,components,services}`, `tests/unit`, `tests/`
**Files scanned:** ~25 (read); all cited analogs confirmed **git-tracked** via `git ls-files` (tracked-source gate #3645)
**Pattern extraction date:** 2026-10-04
