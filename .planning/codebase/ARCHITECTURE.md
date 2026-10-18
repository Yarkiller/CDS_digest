---
last_mapped_commit: 252c024622021ec59fe22abdd251c2047849d1da
---
<!-- refreshed: 2026-09-27 -->
# Architecture

**Analysis Date:** 2026-09-27

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Delivery / UI                                        │
├──────────────────────────────┬──────────────────────────────────────────────┤
│  React app (Vite)            │  Static design prototype                     │
│  `web/src/`                  │  `design-frontend/`                          │
│  pages → components →        │  HTML + CSS tokens + `scripts/app.js`        │
│  `services/` (+ mock/live)   │                                              │
└──────────────┬───────────────┴──────────────────────────────────────────────┘
               │  Bearer JWT (Supabase Auth) + REST
               │  VITE_API_BASE_URL → FastAPI
               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Backend application core                                  │
│  `backend/src/backend/`                                                      │
│  interface/http  → FastAPI app + thin routers                                │
│  composition/    → AppContainer (memory | live)                              │
│  application/    → ports + use_cases                                         │
│  domain/         → entities, VOs, DomainError hierarchy                      │
│  infrastructure/ → JWT verify, LocalNotebookStorage, StubMailer              │
└──────────┬───────────────────────────────┬──────────────────────────────────┘
           │ ports                         │ ports (live adapters)
           ▼                               ▼
┌──────────────────────────┐    ┌─────────────────────────────────────────────┐
│  In-memory fakes         │    │  Adapter modules (workspace packages)       │
│  `tests_support/`        │    │  `supabase-integration/` — repos + SQL      │
│  (APP_CONTAINER=memory)  │    │  `data-collection/` — DTOs + YouTube        │
│                          │    │    adapters/errors (captions, metadata)     │
└──────────────────────────┘    └──────────────────┬──────────────────────────┘
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │  Supabase / Postgres         │
                                    │  schema: `migrations/001–006`│
                                    │  Auth JWKS + profiles RLS    │
                                    └──────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  Ingestion operator CLI (separate composition root; no FastAPI)              │
│  `ingestion-service/` → `ingestion_service`                                  │
│  url parse → mapping(IngestError) → (planned) pipeline stages                │
│  composition/: Settings + ready YouTube/httpx clients (proxy only here)      │
│  Depends on: `data-collection` only (workspace)                              │
│  Boundary: must not import `backend.interface.http` / call FastAPI           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| React shell & routes | Browser UI, navigation, auth gate | `web/src/App.jsx`, `web/src/components/AppShell.jsx`, `RequireAuth.jsx` |
| UI pages | Issue, archive, voting, knowledge, materials, razbory, profile, admin digest, auth | `web/src/pages/*.jsx` |
| Frontend API boundary | REST + Supabase Auth; mock/live switch via `VITE_USE_MOCKS` | `web/src/services/*Api.js`, `authApi.js`, `supabaseClient.js` |
| Mock content | Local fixtures when mocks enabled | `web/src/data/mock.js` |
| FastAPI edge | Thin routers, CORS, request-id, JWT deps | `backend/src/backend/interface/http/` |
| Domain entities | Material, Issue, Vote/Ballot, Razbor, Knowledge, Shortlist, CurrentUser, auth helpers | `backend/src/backend/domain/` |
| Application ports | 13 `Protocol` contracts (+ `StubQueryEmbedder`) | `backend/src/backend/application/ports/` |
| Use-cases | Ballot, issues, materials, search, razbory, profile, shortlist/digest, ping, publish/index | `backend/src/backend/application/use_cases/` |
| Composition root | Memory vs live wiring; settings from env | `backend/src/backend/composition/` |
| Backend-local infra | ES256 JWKS verify, FS notebooks, stub mailer | `backend/src/backend/infrastructure/` |
| In-memory adapters | Test/local port fakes | `backend/src/backend/tests_support/in_memory.py` |
| Supabase adapters | Repositories + digest publisher + clients | `supabase-integration/src/supabase_integration/` |
| SQL schema / RLS / RPCs | Migrations `001`…`006` | `supabase-integration/migrations/` |
| Data-collection | External DTOs + YouTube captions/metadata adapters/errors | `data-collection/src/data_collection/` |
| Ingestion service | Operator CLI package: URL parse, `IngestError`, error mappers, own composition | `ingestion-service/src/ingestion_service/` |
| Design prototype | Canonical Editorial UI (static) | `design-frontend/` |
| Domain glossary | Shared language for agents and product | `CONTEXT.md` |
| Architecture ADRs | Deployment, auth domain, FoundryModels, leaderboard | `docs/adr/` |

## Pattern Overview

**Overall:** Ports & Adapters (hexagonal) with module-level bounded contexts, prescribed by `.cursor/rules/architecture.mdc`.

**Key Characteristics:**
- Dependencies point inward: adapters → application → domain; domain has zero FastAPI/httpx/supabase imports.
- Ports are `typing.Protocol` in `backend/.../application/ports/`.
- External systems live in sibling workspace packages (`supabase-integration`, `data-collection`, `ingestion-service`), not inside domain/use-cases.
- Wiring only in composition roots: `backend/.../composition/` for the HTTP app; `ingestion-service/.../composition/` for the operator CLI (separate root).
- HTTP layer is thin: routers call use-cases via `app.state.container`; JWT + corporate email gate in `deps.py`.
- Frontend calls backends only through `web/src/services/`; identity via Supabase Auth client-side; API data via FastAPI with Bearer token.
- Ingestion is a thin CLI-oriented package: URL allowlist parse lives in `ingestion_service`; fetch adapters and typed errors live in `data-collection`; mappers convert adapter errors into operator `IngestError` envelopes.
- TDD (Red–Green–Refactor) is mandatory for behavior changes (`.cursor/rules/tdd.mdc`, `AGENTS.md`).

## Layers

**Domain (`backend/src/backend/domain/`):**
- Purpose: Pure business entities, value objects, domain errors.
- Location: `backend/src/backend/domain/`
- Contains: `Material`/`MaterialStatus`, `Issue`/`IssueItem`, `KnowledgeChunk`/`KnowledgeHit`, voting/ballot types, `Razbor`, shortlist models, `CurrentUser`, `AccessTokenClaims`, email-domain helpers, `DomainError` hierarchy.
- Depends on: Standard library only.
- Used by: Ports, use-cases, adapters (mapping), package exports.

**Application — ports (`backend/src/backend/application/ports/`):**
- Purpose: Persistence/search/mail/embed contracts without implementation.
- Contains: `MaterialRepository`, `KnowledgeChunkRepository`, `IssueRepository`, `ProfileRepository`, `PingRecorder`, `VoteRepository`, `VotingCycleReader`, `RazborRepository`, `ShortlistRepository`, `DigestPublisher`, `NotebookStorage`, `Mailer`, `QueryEmbedder` (+ `StubQueryEmbedder`).
- Depends on: Domain types only.
- Used by: Use-cases and composition typing.

**Application — use-cases (`backend/src/backend/application/use_cases/`):**
- Purpose: Orchestrate domain rules against ports.
- Contains: `get_current_user`, `update_display_name`, `record_platform_ping`, `get_current_issue`, `get_issue_by_number`, `list_archive_issues`, `get_material_for_reader`, `get_ballot`, `cast_vote`, `search_knowledge`, `list_razbors`, `get_razbor`, `download_razbor_notebook`, `get_admin_shortlist`, `set_shortlist_decision`, `preview_digest_email`, `send_digest`, `publish_material`, `index_material_chunks`.
- Depends on: Domain + ports (+ injected callables like embed).
- Used by: HTTP routers and `AppContainer` façade methods (`publish` / `index` / `search`).

**Composition (`backend/src/backend/composition/`):**
- Purpose: Single DI / bootstrap root for the FastAPI app.
- Contains: `AppContainer`, `build_in_memory_container` (`container.py`), `build_live_container` (`live.py`), `Settings` (`settings.py`).
- Depends on: Ports, use-cases, in-memory fakes, and (live only) `supabase_integration` adapters.
- Used by: `interface/http/app.py` via `resolve_container`; unit tests.

**Interface / HTTP (`backend/src/backend/interface/http/`):**
- Purpose: Thin FastAPI edge — map HTTP ↔ use-cases.
- Contains: `app.py` (`create_app`, `create_default_app`), `deps.py`, `middleware.py`, routers under `routes/` (`health`, `me`, `issues`, `materials`, `knowledge`, `razbory`, `voting`, `admin`).
- Depends on: Composition container, domain errors, infrastructure JWT.
- Status: **Present and wired** for reader/admin flows; publish/index use-cases exist but have no dedicated public HTTP routes.

**Infrastructure (backend-local) (`backend/src/backend/infrastructure/`):**
- Purpose: Backend-owned adapters not living in sibling packages.
- Contains: `auth_jwt.py` (JWKS verify), `local_notebook_storage.py`, `stub_mailer.py`.
- Used by: HTTP deps and both memory/live containers (notebooks + mailer).

**Adapter — supabase-integration:**
- Purpose: Postgres/Supabase schema, RLS, SDK repositories implementing ports.
- Location: `supabase-integration/`
- Contains: `client.py`, repository adapters, `digest_publisher.py`, migrations `001`…`006`, public `__init__.py` exports.
- Depends on: Workspace package `backend` (domain types / `PersistenceError` mapping).

**Adapter — data-collection:**
- Purpose: External API boundary — DTOs plus YouTube captions/metadata adapters and typed errors.
- Location: `data-collection/src/data_collection/`
- Contains: Pydantic models in `dto/`; captions/metadata error types and adapters consumed by ingestion mapping.
- Depends on: Declared package deps (e.g. httpx, youtube-transcript-api) — **not imported by backend** for ingest; consumed by `ingestion-service`.

**Ingestion — operator package (`ingestion-service/`):**
- Purpose: YouTube → (planned LLM) → Supabase draft-material CLI; own composition root, no HTTP app.
- Location: `ingestion-service/src/ingestion_service/`
- Contains:
  - `url.py` — `extract_video_id`, `InvalidYouTubeUrl` (allowlisted hosts/paths; bare 11-char id).
  - `domain/errors.py` — `IngestError` + `Stage` Literal (`url`, `captions`, `metadata`, `consistency`, `llm`, `llm_truncation`, `persist`).
  - `mapping/` — `map_url_error`, `map_captions_error`, `map_metadata_error` → operator `IngestError` with locked reasons + context allowlists.
  - `composition/` — `Settings.from_env` (`YOUTUBE_PROXY_URL`), `build_youtube_transcript_api`, `build_httpx_client` (proxy wiring only here).
- Depends on: Workspace package `data-collection` only (`ingestion-service/pyproject.toml`).
- Status: Scaffold + URL/error-mapping + client factories present; full pipeline CLI / LLM / persist stages not yet implemented in this package.

**Frontend delivery (`web/`):**
- Purpose: Production React UI for Digest CDS.
- Location: `web/src/`
- Contains: Pages, components, services, utils, mock data, Tailwind styles (`index.css`).
- Depends on: React 19, React Router 7, Vite, `@supabase/supabase-js` for Auth when live.

**Design delivery (`design-frontend/`):**
- Purpose: Static Editorial concept (UI Concept 3); design tokens source of truth.
- Location: `design-frontend/`
- Contains: `pages/*.html`, `styles/*.css`, `scripts/app.js`, assets.
- Depends on: Browser only; served statically for Playwright design project.

## Data Flow

### Auth (identity outside FastAPI)

1. Browser uses `web/src/services/authApi.js` → Supabase Auth (`signInWithPassword` / session).
2. Protected pages pass `Authorization: Bearer <access_token>` via service helpers.
3. FastAPI `deps.py` verifies JWT (ES256 JWKS), enforces corporate email allowlist, loads profile via `get_current_user` for admin gates.
4. Login/register are **not** proxied through FastAPI.

### Profile / platform ping

1. `GET|PATCH /me`, `POST /me/ping` → use-cases `get_current_user` / `update_display_name` / `record_platform_ping`.
2. Live: `SupabaseProfileRepository`, `SupabasePingRecorder` on `profiles` / ping tables.

### Issues, archive, materials (reader)

1. `GET /issues/current`, `/issues/{number}`, `/archive`, `/materials/{slug}`.
2. Use-cases read via `IssueRepository` / `MaterialRepository` (ready-only for materials).
3. Live: `SupabaseIssueRepository`, `SupabaseMaterialRepository`.

### Voting ballot

1. `GET /voting/current` → `get_ballot(votes, voting_cycles, user_id)`.
2. `POST /voting/votes` → `cast_vote` with optimistic concurrency (`expected_updated_at`).
3. Live: `SupabaseVoteRepository`, `SupabaseVotingCycleReader`.

### Knowledge search

1. `GET /knowledge/search` → `AppContainer.search` → `StubQueryEmbedder.embed` + `search_knowledge`.
2. Live chunks via `SupabaseKnowledgeChunkRepository` (hybrid/pgvector in adapter); embedder remains stub in both containers today.

### Razbory + notebooks

1. `GET /razbory`, `/razbory/{id}` → `RazborRepository`.
2. `GET /razbory/{id}/notebook` → `download_razbor_notebook` + `NotebookStorage.resolve` (`LocalNotebookStorage` under `NOTEBOOK_ROOT` even in live mode).

### Admin shortlist / digest send

1. `GET /admin/shortlist`, decision/preview/send under `/admin/shortlist/...` (requires `profiles.role=admin`).
2. `send_digest` → `DigestPublisher.claim_and_publish` (RPC) + `Mailer.send_digest` (`StubMailer` today; `MAILER=smtp` fail-fast).

### Publish → index → search (container façade; limited HTTP)

1. `AppContainer.publish` / `.index` / `.search` wrap use-cases for tests and internal flows.
2. Material publish for digest is tied to admin send / `claim_and_publish` RPC, not a public CRUD publish route.
3. No HTTP routes for `publish_material` / `index_material_chunks` as standalone admin APIs.

### Ingestion path (operator CLI; partial)

1. Operator input (URL or bare video id) → `ingestion_service.url.extract_video_id` (allowlist; strips userinfo from diagnostics).
2. On parse failure: `InvalidYouTubeUrl` → `map_url_error` → `IngestError(stage="url").to_dict()` operator envelope.
3. Planned fetch stages use `data-collection` adapters; failures map via `map_captions_error` / `map_metadata_error` into `IngestError` with locked reasons and allowlisted context keys.
4. Composition builds ready clients (`YouTubeTranscriptApi`, `httpx.AsyncClient`) with optional `YOUTUBE_PROXY_URL` — proxy config stays in composition, not in adapters.
5. Later stages (`consistency`, `llm`, `llm_truncation`, `persist`) are reserved on `Stage` but not implemented in this package yet.
6. Hard boundary: ingestion writes toward Supabase (planned); must not call FastAPI or import `backend.interface.http`.

**State Management:**
- Backend: Stateless use-cases; state in repository adapters (in-memory dicts or Supabase).
- Frontend: Local React state per page; no global store library. Mock/live toggled by `VITE_USE_MOCKS`.
- Auth session: Supabase client session (live) or mock harness (Playwright / mocks).
- Ingestion: Stateless CLI-oriented package; operator diagnostics via `IngestError.to_dict()`.

## Key Abstractions

**Material:**
- Purpose: Publishable article unit (draft → ready) with provenance, roles, tags.
- Examples: `backend/src/backend/domain/material.py`
- Pattern: Frozen dataclass + `MaterialStatus`; `assert_publishable` / `as_ready`.

**KnowledgeChunk / KnowledgeHit:**
- Purpose: Indexed atomic content for retrieval; search result DTO.
- Examples: `backend/src/backend/domain/knowledge.py`
- Pattern: Frozen dataclasses; embeddings as `list[float]` (dim aligned with Foundry `EMBEDDING_DIM = 1024`).

**Repository / capability ports:**
- Purpose: Persist and side-effect without coupling to Supabase/SMTP/FS details.
- Examples: `application/ports/*_repository.py`, `digest_publisher.py`, `mailer.py`, `notebook_storage.py`
- Pattern: `Protocol` with narrow methods.

**AppContainer:**
- Purpose: Application façade holding all ports; used by HTTP and tests.
- Examples: `backend/src/backend/composition/container.py`
- Pattern: Dataclass of ports; methods delegate to pure use-case functions.

**HTTP deps:**
- Purpose: Authn/authz at the edge without bloating routers.
- Examples: `backend/src/backend/interface/http/deps.py`
- Pattern: Bearer verify → email allowlist → optional admin via DB role.

**Frontend service module:**
- Purpose: Isolate side effects from UI components.
- Examples: `web/src/services/contentApi.js`, `votingApi.js`, `adminApi.js`
- Pattern: Async functions + typed errors; mock/live branch; Playwright harnesses on `window`.

**External DTOs / data-collection errors:**
- Purpose: Validate/normalize boundary payloads; typed captions/metadata failures for ingestion mapping.
- Examples: `data-collection/src/data_collection/dto/*.py`, `data_collection.errors.captions`, `data_collection.errors.metadata`
- Pattern: Pydantic `BaseModel` for DTOs; exception hierarchies mapped at `ingestion_service.mapping`.

**IngestError:**
- Purpose: Operator-facing staged diagnostic for the ingestion CLI.
- Examples: `ingestion-service/src/ingestion_service/domain/errors.py`
- Pattern: Dataclass exception with `stage`, `reason`, `message`, `context`, `exit_code`; `to_dict()` JSON envelope (`ok: false`).

**Video id extraction:**
- Purpose: Normalize YouTube URL / bare id before adapters see a `video_id`.
- Examples: `ingestion-service/src/ingestion_service/url.py`
- Pattern: Allowlisted hosts + path families (`watch`, `shorts`, `embed`, `youtu.be`); reject deferred forms (`live`/`v`/`e`).

## Entry Points

**React SPA:**
- Location: `web/src/main.jsx` → `web/src/App.jsx`
- Triggers: Vite dev (`npm run dev`, port 5173) or production build; Playwright uses 5174 with mocks.
- Responsibilities: Mount React, register routes, expose `__DIGEST_*_HARNESS__` for E2E.

**FastAPI / Uvicorn:**
- Location: `backend.interface.http.app:create_default_app` (factory)
- Triggers: `uv run --env-file .env uvicorn backend.interface.http.app:create_default_app --factory --host 127.0.0.1 --port 8000`
- Responsibilities: Load `Settings`, resolve memory/live container, serve routers.

**Python composition (backend):**
- Location: `backend/src/backend/composition/container.py`, `live.py`
- Triggers: App factory, unit tests.
- Responsibilities: Construct adapters and expose use-case façade.

**Ingestion composition:**
- Location: `ingestion-service/src/ingestion_service/composition/`
- Triggers: Future CLI / tests importing `Settings`, `build_youtube_transcript_api`, `build_httpx_client`.
- Responsibilities: Env-backed settings and ready clients; proxy only at this boundary.
- Status: No `__main__.py` / Typer entry yet — package is library-shaped scaffolding for the operator CLI.

**Backend public package API:**
- Location: `backend/src/backend/__init__.py`
- Triggers: `from backend import Material, ...`
- Responsibilities: Re-export domain types/errors for consumers/adapters.

**Data-collection public API:**
- Location: `data-collection/src/data_collection/__init__.py`
- Triggers: `from data_collection import …`
- Responsibilities: Export DTOs / adapter surface used by ingestion.

**Ingestion package:**
- Location: `ingestion-service/src/ingestion_service/`
- Triggers: `import ingestion_service`; `from ingestion_service.url import extract_video_id`; mapping / composition imports.
- Responsibilities: URL parse, operator errors, error mappers, client factories.

**Supabase-integration public API:**
- Location: `supabase-integration/src/supabase_integration/__init__.py`
- Triggers: Client factories, repository classes, `migrations_dir()`.
- Responsibilities: Adapter surface for live composition.

**Design prototype:**
- Location: `design-frontend/index.html` and `design-frontend/pages/*.html`
- Triggers: Static serve on port 8765 (`npm run serve:design` / Playwright).
- Responsibilities: Visual reference and design E2E.

**Root workspace:**
- Location: `pyproject.toml` (uv workspace), `package.json` (npm scripts).
- Triggers: `uv run pytest`, `npm test`, `npm run test:unit`, `npm run platform:runbook`.
- Responsibilities: Orchestrate multi-package tooling. Workspace members: `backend`, `data-collection`, `ingestion-service`, `supabase-integration`.

## Architectural Constraints

- **Threading:** Python use-cases are synchronous; FastAPI routes call them directly. Frontend is browser event loop. Ingestion composition exposes an async `httpx.AsyncClient` factory alongside sync transcript SDK.
- **Composition modes:** `APP_CONTAINER=memory` (default) vs `live` (requires `SUPABASE_URL` + `SUPABASE_SECRET_KEY`). Live imports `supabase_integration` from workspace root install (`digest-cds` meta-package); `backend` alone does not declare that dependency.
- **Circular imports:** `supabase-integration` depends on `backend`; domain/use-cases must not import `supabase_integration` or `data_collection`. `ingestion-service` depends on `data-collection` only — must not import FastAPI edge.
- **Module boundaries:** No deep-imports into another package’s internals; use package `__init__.py` / ports. uv members: `backend`, `data-collection`, `ingestion-service`, `supabase-integration`.
- **Ingestion boundary:** Operator path owns URL parse + staged diagnostics; adapters stay in `data-collection`; proxy/env wiring only in `ingestion_service.composition`.
- **Secrets:** `.env` at repo root for local config — never import secrets into domain; never commit values. Ingestion reads `YOUTUBE_PROXY_URL` via `Settings.from_env`.
- **Auth split:** JWT issuance is Supabase-only; FastAPI validates tokens and enforces email/role policy.
- **Notebooks:** Always local filesystem (`LocalNotebookStorage`), not Supabase Storage.
- **TDD:** No production behavior without a failing automated test first.

## Anti-Patterns

### SDK or HTTP client inside use-case / domain

**What happens:** Importing `supabase`, `httpx`, or `requests` in `domain/` or `use_cases/`.
**Why it's wrong:** Couples business rules to one vendor; breaks unit tests without network/DB.
**Do this instead:** Define a port in `application/ports/`, implement in `supabase-integration` or `data-collection`, wire in composition.

### Business rules in React pages or fat FastAPI routers

**What happens:** Scoring, publishability, or ranking computed in `web/src/pages/*.jsx` or thick route handlers.
**Why it's wrong:** Duplicates domain logic; UI and API diverge.
**Do this instead:** Keep rules in domain/use-cases; UI renders DTOs; routers only map HTTP ↔ use-cases.

### Bypassing `web/src/services/`

**What happens:** Pages call `fetch`/Supabase client directly (except auth, which is confined to `authApi`/`supabaseClient`).
**Why it's wrong:** Leaks infrastructure into UI; hard to swap mock → live.
**Do this instead:** Add/extend modules under `web/src/services/`.

### Wiring outside composition root

**What happens:** `create_client(...)` or repository construction scattered in use-cases or routers; or proxy/env reads inside YouTube adapters.
**Why it's wrong:** Multiple composition points; adapters become undeleteable.
**Do this instead:** Construct adapters in `backend/.../composition/` (HTTP app) or ready clients in `ingestion_service.composition` (CLI); adapters receive injected clients.

### Routing ingestion through FastAPI

**What happens:** CLI or adapters call `backend.interface.http` or browser APIs for ingest writes.
**Why it's wrong:** Couples operator pipeline to reader/admin HTTP surface; breaks the locked ingest→Supabase boundary.
**Do this instead:** Keep orchestration in `ingestion-service`; persist via dedicated adapters (planned), not the web API.

### Treating design-frontend as production app

**What happens:** Shipping features only in static HTML under `design-frontend/`.
**Why it's wrong:** Product path is `web/`; design folder is concept/reference.
**Do this instead:** Implement product behavior in `web/` + backend packages; keep design-frontend aligned for visuals/E2E.

## Error Handling

**Strategy:** Domain exceptions for business failures; infrastructure/token errors at the edge; frontend typed errors for UX; adapters map SDK failures into domain/`PersistenceError` at the boundary; ingestion maps adapter/parse failures into staged `IngestError` for operators.

**Patterns:**
- Domain: `DomainError` family in `backend/src/backend/domain/errors.py` (material, issue, razbor, notebook, knowledge, voting, shortlist/digest).
- HTTP: Routers/deps translate domain and `TokenVerificationError` into status codes.
- Frontend: Service-level error classes (e.g. vote/admin/content failures) surfaced via `ErrorPanel` / `ServiceUnavailable`.
- DTO validation: Pydantic `ValidationError` at data-collection boundary.
- Ingestion: `InvalidYouTubeUrl` / `CaptionsError` / `MetadataError` → `map_*_error` → `IngestError.to_dict()` with locked `reason` sets and context allowlists.

## Cross-Cutting Concerns

**Logging:** `structlog` configured at HTTP edge (`middleware.py` / `configure_structlog`); prefer logging at adapter/HTTP edges, not inside pure domain.

**Validation:**
- Domain invariants on entities (e.g. `Material.assert_publishable`).
- DTOs: Pydantic validators in `data-collection`.
- SQL: check constraints, enums, RLS in migrations.
- Ingestion URL: allowlisted hosts/paths + `[A-Za-z0-9_-]{11}` video id.

**Authentication / authorization:**
- Supabase Auth for identity; FastAPI Bearer JWKS verify.
- Corporate email allowlist (ADR-0003) in domain helpers + `deps.py` / frontend `emailDomain.js`.
- Admin: DB `profiles.role=admin` via `require_admin`, not JWT app-role claim alone.
- Ingestion CLI: operator tool (no FastAPI JWT path in this package).

**CORS / request ID:** `CORSMiddleware` from `Settings.cors_origins`; `RequestIdMiddleware` + `X-Request-ID`.

**Design tokens:** Editorial tokens in `design-frontend/styles/tokens.css`; React mirrors via Tailwind/`@theme` in `web/src/index.css`.

**Documentation / ADRs:** Product language in `CONTEXT.md`; decisions in `docs/adr/`; agent runbooks in `docs/agents/`.

---

*Architecture analysis: 2026-09-27*
