---
last_mapped_commit: 252c024622021ec59fe22abdd251c2047849d1da
---
<!-- refreshed: 2026-09-27 -->
# Coding Conventions

**Analysis Date:** 2026-09-27

## Naming Patterns

**Files:**
- Python packages use snake_case directories and modules under `backend/src/backend/`:
  - Domain: singular nouns — `domain/material.py`, `domain/vote.py`, `domain/razbor.py`, `domain/shortlist.py`
  - Ports: `{noun}_repository.py` or role — `application/ports/vote_repository.py`, `profile_repository.py`, `ping_recorder.py`
  - Use-cases: `{verb}_{noun}.py` — `cast_vote.py`, `update_display_name.py`, `send_digest.py`
  - HTTP routes: feature/resource — `interface/http/routes/voting.py`, `admin.py`, `razbory.py`, `me.py`
  - Composition: `container.py`, `live.py`, `settings.py`
  - Infrastructure: `infrastructure/auth_jwt.py`, `stub_mailer.py`, `local_notebook_storage.py`
- Supabase adapters: `{entity}_repository.py` with class `Supabase{Port}` — `supabase-integration/.../vote_repository.py`
- Data-collection DTOs: `dto/{source}.py`, class suffix `Dto` — `YoutubeSourceDto`, `EmbeddingResultDto`
- Ingestion CLI package (`ingestion-service/src/ingestion_service/`):
  - Workspace member name `ingestion-service`; importable module `ingestion_service` (`module-root = "src"`)
  - Package-root helpers: `url.py` — `extract_video_id`, `InvalidYouTubeUrl` (URL parse lives here, not on provider ports)
  - Domain: `domain/errors.py` — operator `IngestError` + `Stage` Literal
  - Mappers: `mapping/{url,captions,metadata}.py` — `map_url_error`, `map_captions_error`, `map_metadata_error`
  - Composition: `composition/settings.py` (`Settings`), `composition/clients.py` (`build_*` factories)
  - No Typer CLI / HTTP surface yet — composition + mapping only (CLI planned later)
- React pages: `PascalCase` + `Page` — `web/src/pages/VotingPage.jsx`, `AdminDigestPage.jsx`
- React components: `PascalCase` — `ActionButton.jsx`, `ErrorPanel.jsx`, `RequireAuth.jsx`
- Frontend services: camelCase + `Api.js` (or role) — `votingApi.js`, `meApi.js`, `adminApi.js`, `welcomeSession.js`
- Frontend utils: camelCase — `markdownToc.js`, `filters.js`, `ruCount.js`
- Unit tests (pytest): `test_<subject>.py` under `tests/unit/`
- Unit tests (Node): `test_<subject>.js` under `tests/unit/`, or colocated `*.test.js` — `web/src/services/emailDomain.test.js`
- Playwright specs: `<area>.spec.js` under `tests/` — `web-app.spec.js`, `auth.spec.js`, `admin.spec.js`
- SQL migrations: numbered — `supabase-integration/migrations/001_initial_schema.sql`, `003_phase3_voting_ballot.sql`, `005_phase5_admin_shortlist.sql`

**Functions:**
- Python: snake_case; use-cases are **module-level functions**, not classes — `cast_vote`, `publish_material`, `search_knowledge`
- Ingestion: module-level `extract_video_id`, `map_*_error`, `Settings.from_env`, `build_youtube_transcript_api`, `build_httpx_client`
- Private helpers: leading underscore — `_draft`, `_mint`, `_client`, `_cosine`, `_conflict_detail`, `_require_id`, `_forward_context`, `_safe_url_for_diagnostics`
- React components: default-export `PascalCase` function components — `export default function VotingPage()`
- Named JS exports: camelCase — `submitVote`, `fetchBallot`, `armFailNextVoteSubmit`, `isMocksEnabled`

**Variables:**
- Python locals: snake_case; type annotations on public signatures
- Prefer immutable domain fields: frozen `@dataclass`, `tuple[...]` for collections on entities
- Ingestion locked reason sets: module-level `CAPTIONS_REASONS` / `METADATA_REASONS` as `frozenset[str]`; context keys via `_CONTEXT_ALLOWLIST`
- JS: camelCase; interactive button states via `data-state`: `'loading' | 'error' | 'success'` (idle omits attribute)
- HTTP machine codes: snake_case strings — `voting_unavailable`, `invalid_vote`, `profiles_not_configured`
- Conflict payloads: UPPER_SNAKE codes — `CYCLE_CLOSED`, `VOTE_CONFLICT`
- Ingest / captions / metadata reason codes: snake_case — `missing_video_id`, `no_preferred_language`, `metadata_invalid_response` (never SDK exception class names)

**Types:**
- Domain entities: frozen `@dataclass` — `Material`, `BallotSnapshot`, `KnowledgeHit`, `CurrentUser`
- Status enums: `str, Enum` where used — `MaterialStatus` with lowercase values (`"draft"`, `"ready"`)
- Ports: `typing.Protocol` with ellipsis stubs — `VoteRepository`, `ProfileRepository` in `application/ports/`
- HTTP boundary: Pydantic v2 `BaseModel` with `ConfigDict(extra="forbid")` — `CastVoteRequest`, `BallotSnapshotResponse`
- External/API payloads: Pydantic DTOs in `data-collection/.../dto/` — suffix `Dto`
- Domain errors: subclasses of `DomainError` in `backend/src/backend/domain/errors.py`
- Ingestion operator errors: `@dataclass` `IngestError(Exception)` with `Stage = Literal["url","captions","metadata","consistency","llm","llm_truncation","persist"]` in `ingestion_service/domain/errors.py` (separate from backend `DomainError`)
- Frontend API errors: `*ApiError` / `*SubmitError` extending `Error` with `code` and `retryable`

## Code Style

**Formatting:**
- Python: no Black/Ruff config in repo; follow existing style — `from __future__ import annotations` on nearly all backend/supabase/ingestion/test modules; blank line after imports; 4-space indent; `X | Y` unions
- Frontend (`web/src`): **no semicolons**, single quotes, ESM with **explicit `.js` / `.jsx` extensions** in imports
- Playwright specs and `playwright.config.js`: CommonJS `require` and **semicolons** / often double quotes — keep that style in E2E files
- Node unit tests under `tests/unit/*.js`: CommonJS `require('node:test')` / `require('node:assert/strict')`
- Tailwind v4: `@import "tailwindcss"` + `@theme { … }` tokens in `web/src/index.css`; semantic utilities (`text-ink-2`, `bg-voting`, `font-display`) plus occasional inline `oklch(...)` for error chrome
- Utility class composition via `.join(' ')` arrays on interactive components (`ActionButton.jsx`)

**Linting:**
- Frontend: Oxlint via `npm run lint --prefix web`; config `web/.oxlintrc.json`
  - Plugins: `react`, `oxc`
  - Enforced: `react/rules-of-hooks` as error; `react/only-export-components` as warn (constants allowed)
- Python: no dedicated linter/formatter config in workspace `pyproject.toml` files (pytest only)
- TypeScript: not applicable — app source is JSX/JS (React type packages present for tooling only)
- No Prettier / ESLint / pre-commit config detected

## Import Organization

**Order (Python):**
1. Module docstring (often requirement IDs: `VOTE-01`, `D-52`, `ADMIN-01`, `CAP-01`, `D-11`)
2. `__future__` annotations (when needed)
3. stdlib (`datetime`, `uuid`, `pathlib`, `os`, `re`, `urllib.parse`, …)
4. third-party (`fastapi`, `pydantic`, `structlog`, `pytest`, `jwt`, `httpx`, `youtube_transcript_api`)
5. workspace packages (`backend.*`, `data_collection.*`, `supabase_integration.*`, `ingestion_service.*`)
6. Absolute imports across packages — avoid deep relative imports between modules

**Order (Frontend):**
1. React / library imports (`react`, `react-router-dom`)
2. Local components/pages (`../components/...`, `../pages/...`)
3. Services, utils, mock data (`../services/`, `../utils/`, `../data/`)
4. Side-effect CSS last in entry (`./index.css` in `main.jsx`)

**Path Aliases:**
- Not detected — relative imports from `web/src/`; Python package names for workspace members
- Python path for tests: root `pythonpath = ["."]` in `pyproject.toml` so `backend` / `data_collection` / `ingestion_service` resolve under `uv run pytest`
- No Vite `@/` alias — `web/vite.config.js` is plugins + server only

**Module boundaries (prescriptive):**
- Domain/use-cases must not import `supabase`, `httpx`, `fastapi`, or React
- Frontend UI must call APIs only through `web/src/services/` (e.g. `votingApi.js`, `meApi.js`)
- Wire adapters / `create_client` only in `backend/src/backend/composition/` (`container.py`, `live.py`)
- `ingestion-service` depends on `data-collection` only; maps adapter errors → `IngestError` in `mapping/`; proxy/env only in `composition/` (never in data-collection adapters)
- Public package surfaces use `__all__` — `supabase_integration/__init__.py`, `data_collection/__init__.py`, `ingestion_service.mapping`, `ingestion_service.composition`; backend root `__init__.py` exports a narrow domain surface
- HTTP maps domain errors **per-route** (no global `DomainError` exception handler)

## Error Handling

**Domain hierarchy** (`backend/src/backend/domain/errors.py` — all subclass `DomainError`):
- Materials / issues: `MaterialNotFoundError`, `MaterialValidationError`, `MaterialNotReadyError`, `IssueNotFoundError`
- Knowledge: `KnowledgeQueryValidationError` (`.code`)
- Voting: `VotingCycleClosedError`, `VoteConflictError`, `InvalidVoteError` (ballot attached on conflicts)
- Razbory: `RazborNotFoundError`, `NotebookNotAvailableError`, `NotebookPathInvalidError`
- Admin / digest: `ShortlistNotFoundError`, `InvalidShortlistDecisionError`, `EmptySendPoolError`, `InvalidPreviewCompositionError`, `DraftInSendPoolError`, `InvalidSendOrderError`, `AlreadySentError`
- Infra boundary: `PersistenceError` (adapters wrap SDK failures)

**Ingestion operator hierarchy** (`ingestion-service/.../domain/errors.py` — not backend `DomainError`):
- `InvalidYouTubeUrl` — parse failure with `.reason`, `.value`, `.context` (credentials stripped via `_safe_url_for_diagnostics`)
- `IngestError` — staged diagnostic: `stage`, `reason`, `message`, optional `context`, `exit_code=1`; serialize with `.to_dict()` → `{ ok: false, stage, reason, message, exit_code [, context] }`
- Mappers (`map_url_error` / `map_captions_error` / `map_metadata_error`) convert parse / `data_collection.errors.*` into `IngestError` with locked snake_case reasons and allowlisted context keys only (redact `proxy_url`, `YOUTUBE_PROXY_URL`, userinfo)

**Patterns:**
- Raise typed domain exceptions from use-cases/entities — never bare `Exception` for business failures
- Validation on entities via methods that raise — `Material.assert_publishable()` / `as_ready()`
- Map Pydantic `ValidationError` at DTO boundaries; assert with `pytest.raises(ValidationError)` in unit tests
- HTTP: `try/except` in routes → `HTTPException` with snake_case `detail` or structured 409 `{ code, message, ballot }`
- Auth deps (`interface/http/deps.py`): 401 on JWT failure; 403 `domain_not_allowed` / `forbidden` (admin from DB `profiles.role`, not JWT claim)
- Frontend: typed error classes — `VoteSubmitError`, `BallotFetchError`, `MeApiError`, `AuthApiError`, `AdminApiError`, `KnowledgeApiError`, `RazboryApiError`, `ContentApiError`
- UI catches API errors, normalizes unknowns, drives `data-state` and `ErrorPanel` / `role="alert"`
- Ingestion: data-collection raises typed `CaptionsError` / `MetadataError` subtypes; ingestion-service owns stage vocabulary and operator JSON envelope

**Do this:**
```python
# use-case
material = repo.get(material_id)
if material is None:
    raise MaterialNotFoundError(material_id)
```

```python
# ingestion mapper boundary
from ingestion_service.mapping.captions import map_captions_error

mapped = map_captions_error(captions_error)
payload = mapped.to_dict()  # operator diagnostic JSON
```

```javascript
// service boundary
throw new VoteSubmitError(message, { code: 'NETWORK', retryable: true })
```

## Logging

**Framework:**
- **structlog** JSON to stdout — configured in `interface/http/middleware.py` via `configure_structlog()` from the app factory
- **RequestIdMiddleware**: binds `request_id` in contextvars, echoes `X-Request-ID`, logs `request_finished` with method/path/status (**never Authorization**)
- Sparse stdlib `logging` in a few use-cases/infra helpers (`send_digest`, `stub_mailer`)
- Ingestion-service: no dedicated logger yet — operator diagnostics via `IngestError.to_dict()` (CLI progress/logging TBD with Typer)

**Patterns:**
- Prefer domain exceptions + UI error panels for user-facing failures
- Do not introduce ad-hoc `console.log` / `print` in production paths without an agreed approach
- Correlation: clients may send `X-Request-ID`; otherwise server generates UUID
- Never put proxy credentials or URL userinfo into ingest messages/context

## Comments

**When to Comment:**
- Module docstrings for intent / requirement IDs — use-cases and routes often cite `VOTE-01`, `D-52`, etc.; ingestion cites `CAP-01`, `D-01…D-05`, `D-10`, `D-11`, `D-13`, `D-16`, `D-17`, `D-23`, `D-25`
- Unit tests: `"""RED→GREEN: ..."""` or requirement-focused module docstrings; JS headers may include `Run: node --test ...`
- Composition root docstring — wire adapters into use-cases / ready clients
- Non-obvious helpers — markdown split, notebook path rules, score factors, URL credential scrubbing
- Frontend: JSDoc on public utils/services when harness or types are non-obvious

**JSDoc/TSDoc:**
- Light JSDoc on service harness and helpers; no TSDoc (JSX codebase)
- Python: prefer type annotations over verbose docstrings; short docstrings on public helpers and error classes

## Function Design

**Size:**
- Keep use-cases focused on one scenario per function file (`cast_vote.py`, `send_digest.py`)
- Extract pure helpers in the same module when needed
- Ingestion mappers: one stage per module; thin `map_*_error` + private `_forward_context`
- React page components may own local state + handlers; push pure logic to `web/src/utils/` or extractable modules under `services/` (e.g. `adminPreviewComposition.js` for Node unit tests)

**Parameters:**
- Inject ports as early positional parameters; keyword-only for options — `cast_vote(..., *, now: datetime | None = None)`
- Never construct Supabase/HTTP clients inside use-cases
- Ingestion: inject ready clients from composition — adapters must not read `os.environ` / `YOUTUBE_PROXY_URL`
- `Settings.from_env(environ: dict[str, str] | None = None)` — pass a dict in tests; default `os.environ` in production
- Optional clocks/time: `now=` for testability
- Callables for side effects: `embed: Callable[[str], list[float]]` rather than embedding SDK inside use-case
- FastAPI: resolve ports from `request.app.state.container` via thin route helpers

**Return Values:**
- Use-cases return domain objects or snapshots (`BallotSnapshot`, `Material`, `list[KnowledgeHit]`, `CurrentUser`)
- Ports return domain types or `None` for missing
- Ingestion mappers return `IngestError` instances (caller decides raise vs print `to_dict()`)
- Avoid `Any` on ports and module boundaries (ingest context dicts use `dict[str, Any]` only for the operator envelope)

## Module Design

**Exports:**
- Explicit `__all__` on adapter/DTO package public APIs
- Ingestion: `ingestion_service.mapping.__all__` = mappers; `ingestion_service.composition.__all__` = `Settings` + client builders
- React: default export for pages/components; named exports for utils/services/errors
- In-memory fakes live in `backend/src/backend/tests_support/in_memory.py` (structural Protocol duck-typing — no inheritance required)
- Data-collection fakes: `data_collection.tests_support.fakes` (e.g. `FakeTranscriptProvider`) — used with ingestion mappers in unit tests

**Barrel Files:**
- Thin package `__init__.py` re-exports only the public surface
- Use-cases package may stay empty of re-exports — import use-case modules directly

**Architecture rules to follow when adding code:**
1. New domain concept → `backend/src/backend/domain/`
2. New persistence/search capability → Protocol in `application/ports/`, fake in `tests_support/`
3. New scenario → function in `application/use_cases/` + failing unit test first
4. New HTTP surface → thin router under `interface/http/routes/` + `test_http_<area>.py`
5. New external payload shape → Pydantic DTO in `data-collection/src/data_collection/dto/`
6. New Supabase adapter → `supabase-integration/` + `test_supabase_<port>_contract.py`
7. New UI feature → page/component under `web/src/`; API calls only via `web/src/services/`
8. Wiring → only `composition/container.py` (memory) / `composition/live.py` (Supabase)
9. New ingest pipeline stage → `IngestError` stage already reserved; add `mapping/<stage>.py` mapper + `tests/unit/test_*_error_mapping.py`; keep proxy/env in `ingestion_service.composition` only
10. YouTube URL parse changes → `ingestion_service/url.py` only (not provider ports)

---

*Convention analysis: 2026-09-27*
