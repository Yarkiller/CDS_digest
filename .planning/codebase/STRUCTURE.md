---
last_mapped_commit: 252c024622021ec59fe22abdd251c2047849d1da
---
<!-- refreshed: 2026-09-27 -->
# Codebase Structure

**Analysis Date:** 2026-09-27

## Directory Layout

```
Digital_CDS/
├── backend/                    # Python FastAPI + domain/application (uv package)
│   └── src/backend/
│       ├── domain/             # Entities, VOs, errors
│       ├── application/
│       │   ├── ports/          # Protocol interfaces
│       │   └── use_cases/      # Scenarios
│       ├── composition/        # DI: container, live, settings
│       ├── infrastructure/     # JWT, local notebooks, stub mailer
│       ├── interface/http/     # FastAPI app, deps, middleware, routes/
│       └── tests_support/      # In-memory port fakes
├── data-collection/            # External-API DTOs + YouTube adapters (uv package)
│   └── src/data_collection/
│       ├── dto/
│       ├── adapters/           # YouTube fetch adapters (consumed by ingestion)
│       └── errors/             # Captions/metadata typed errors
├── ingestion-service/          # Operator CLI package (uv member; own composition)
│   └── src/ingestion_service/
│       ├── url.py              # extract_video_id / InvalidYouTubeUrl
│       ├── domain/             # IngestError (+ Stage Literal)
│       ├── mapping/            # Adapter/parse → IngestError mappers
│       └── composition/        # Settings + ready YouTube/httpx clients
├── supabase-integration/       # DB adapters + SQL migrations
│   ├── migrations/             # 001…006
│   └── src/supabase_integration/
├── web/                        # React + Vite production UI
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── data/
│       └── utils/
├── design-frontend/            # Static Editorial UI concept
│   ├── pages/
│   ├── styles/
│   ├── assets/
│   └── scripts/
├── tests/                      # Pytest unit + Playwright E2E
│   └── unit/                   # Python + Node unit/contract tests
├── docs/                       # Specs, ADRs, agent docs
│   ├── adr/
│   ├── agents/
│   └── digest-cds/
├── notebooks/                  # Sample notebook assets
├── scripts/                    # Tooling (Playwright browsers)
├── .cursor/rules/              # Always-on agent architecture/TDD rules
├── .agents/skills/             # Project skills (supabase, hallmark, …)
├── .scratch/                   # Local issue tracker markdown
├── .planning/                  # GSD planning artifacts (incl. this map)
├── archive/                    # Archived homework zip / notes
├── CONTEXT.md                  # Domain glossary
├── AGENTS.md                   # Agent entry (TDD, skills pointers)
├── pyproject.toml              # uv workspace root
├── package.json                # Root npm scripts + Playwright
├── playwright.config.js
├── uv.lock
└── .env                        # Local env (exists; secrets — do not read/commit)
```

## Directory Purposes

**`backend/`:**
- Purpose: Core business logic + FastAPI HTTP edge (`name = "backend"`).
- Contains: Domain, ports, use-cases, composition, infrastructure, HTTP interface, in-memory test adapters.
- Key files: `backend/src/backend/composition/container.py`, `composition/live.py`, `interface/http/app.py`, `backend/pyproject.toml`.

**`data-collection/`:**
- Purpose: Bounded context for inbound external data (YouTube captions/metadata adapters, DTOs, typed errors).
- Contains: Pydantic DTOs; adapters/errors consumed by `ingestion-service` mapping; not wired into backend HTTP path.
- Key files: `data-collection/src/data_collection/__init__.py`, `dto/`, `adapters/`, `errors/`.

**`ingestion-service/`:**
- Purpose: YouTube → LLM → Supabase operator CLI package (`name = "ingestion-service"`, module `ingestion_service`); separate composition root from FastAPI.
- Contains: URL allowlist parse, `IngestError` domain diagnostics, error mappers, env-backed Settings + ready client factories.
- Depends on: `data-collection` only (workspace).
- Key files: `ingestion-service/pyproject.toml`, `src/ingestion_service/url.py`, `domain/errors.py`, `mapping/{url,captions,metadata}.py`, `composition/{settings,clients}.py`.
- Status: Scaffold present; no `__main__.py` / Typer CLI entry yet.

**`supabase-integration/`:**
- Purpose: Postgres/Supabase schema and repository adapters implementing backend ports.
- Contains: SQL migrations `001`…`006`; client factories; repository + digest publisher modules.
- Key files: `supabase-integration/src/supabase_integration/__init__.py`, `client.py`, `*_repository.py`, `digest_publisher.py`, `migrations/001_initial_schema.sql`.

**`web/`:**
- Purpose: Primary React delivery for Digest CDS UI.
- Contains: Pages, components, service boundary (mock/live), mock data, Tailwind styles.
- Key files: `web/src/main.jsx`, `web/src/App.jsx`, `web/vite.config.js`, `web/package.json`.

**`design-frontend/`:**
- Purpose: Canonical static design (Editorial Concept 3); visual/token reference and design E2E target.
- Contains: HTML pages, CSS tokens/layout/components, covers, notebook assets, `UI-SPEC_3.md`.
- Key files: `design-frontend/index.html`, `design-frontend/styles/tokens.css`, `design-frontend/pages/*.html`.

**`tests/`:**
- Purpose: Automated verification — Python unit (pytest), JS unit under Node, Playwright E2E.
- Contains: `tests/unit/*`, `tests/*.spec.js` (`web-app`, `auth`, `knowledge`, `razbory`, `admin`, `design-frontend`).
- Key files: `tests/unit/test_composition_container.py`, `playwright.config.js` (root).

**`docs/`:**
- Purpose: Product/tech docs and decision records.
- Contains: ADRs, agent workflow docs, digest-cds specs and responsive evidence.
- Key files: `docs/adr/0004-self-hosted-supabase-on-vm.md`, `docs/agents/local-platform-runbook.md`, `docs/agents/domain.md`.

**`notebooks/`:**
- Purpose: Sample notebook assets used with razbory / hybrid retrieval demos.
- Key files: `notebooks/hybrid-retrieval.ipynb` (also mirrored under design-frontend assets).

**`scripts/`:**
- Purpose: Repo tooling helpers.
- Contains: Playwright browser cache installer.
- Key files: `scripts/ensure-playwright-browsers.cjs`.

**`.cursor/rules/`:**
- Purpose: Always-applied agent constraints (architecture, TDD, uv, Context7).
- Key files: `.cursor/rules/architecture.mdc`, `.cursor/rules/tdd.mdc`.

**`.agents/skills/`:**
- Purpose: Project-bundled agent skills (hallmark, supabase, postgres best practices).

**`.planning/`:**
- Purpose: GSD maps, plans, research outputs, phase artifacts.
- Contains: `codebase/` analysis docs (this folder), `phases/`, `milestones/`, `research/`.

**`.scratch/`:**
- Purpose: Local markdown issues (see `docs/agents/issue-tracker.md`).
- Generated: No (hand-maintained). Committed: Per project policy for scratch issues.

**`archive/`:**
- Purpose: Historical homework artifacts.
- Key files: `archive/README.md`.

## Key File Locations

**Entry Points:**
- `web/src/main.jsx`: React bootstrap (+ Playwright harness globals).
- `web/src/App.jsx`: Route table (`/`, `/archive`, `/issues/:number`, `/voting`, `/knowledge`, `/materials/:id`, `/razbory`, `/profile`, `/admin/digest`, `/login`, `/register`).
- `backend/src/backend/interface/http/app.py`: FastAPI factory (`create_default_app`).
- `backend/src/backend/composition/container.py`: Application façade + in-memory builder.
- `backend/src/backend/composition/live.py`: Live Supabase wiring.
- `backend/src/backend/__init__.py`: Public domain exports.
- `data-collection/src/data_collection/__init__.py`: Public DTO / adapter exports.
- `ingestion-service/src/ingestion_service/__init__.py`: Package marker (YouTube URL → draft material CLI).
- `ingestion-service/src/ingestion_service/composition/`: Operator composition (`Settings`, client builders).
- `supabase-integration/src/supabase_integration/__init__.py`: Adapters + `migrations_dir()`.
- `design-frontend/index.html`: Static prototype entry.

**Configuration:**
- `pyproject.toml`: uv workspace members (`backend`, `data-collection`, `ingestion-service`, `supabase-integration`), pytest `testpaths = ["tests/unit"]`.
- `backend/pyproject.toml`, `data-collection/pyproject.toml`, `ingestion-service/pyproject.toml`, `supabase-integration/pyproject.toml`: Per-package metadata.
- `package.json`: Root scripts (`dev`, `test`, `test:unit`, `test:web`, `test:design`, `serve:design`, `platform:runbook`).
- `web/package.json`: Vite/React/Tailwind/oxlint.
- `playwright.config.js`: E2E projects and webServers.
- `.python-version`: Python version pin.
- `.env` / `.env.example`: Local environment (existence only — never quote secrets). Ingestion-relevant: `YOUTUBE_PROXY_URL`.

**HTTP routes:**
- `backend/src/backend/interface/http/routes/health.py` — `GET /health`
- `routes/me.py` — `GET|PATCH /me`, `POST /me/ping`
- `routes/issues.py` — current/by number + `/archive`
- `routes/materials.py` — `GET /materials/{slug}`
- `routes/knowledge.py` — `GET /knowledge/search`
- `routes/razbory.py` — list/detail/notebook download
- `routes/voting.py` — ballot + cast vote
- `routes/admin.py` — shortlist decision/preview/send

**Core logic:**
- `backend/src/backend/domain/` — entities and errors.
- `backend/src/backend/application/ports/` — 13 ports.
- `backend/src/backend/application/use_cases/` — scenario modules.
- `supabase-integration/migrations/` — canonical DB schema + phase RPCs.
- `ingestion-service/src/ingestion_service/url.py` — video id extraction.
- `ingestion-service/src/ingestion_service/domain/errors.py` — operator `IngestError`.
- `ingestion-service/src/ingestion_service/mapping/` — URL/captions/metadata → `IngestError`.

**Frontend logic:**
- `web/src/services/` — Auth (Supabase), content, voting, knowledge, razbory, me, admin APIs.
- `web/src/data/mock.js` — fixtures when `VITE_USE_MOCKS`.
- `web/src/utils/` — filters, voting helpers, markdown TOC, delay, ruCount.

**Testing:**
- `tests/unit/` — pytest + Node unit/contract tests (includes ingestion helpers such as `test_extract_video_id.py`, `test_ingest_error.py` when present).
- `tests/*.spec.js` — Playwright against Vite app / design static server.
- `backend/src/backend/tests_support/in_memory.py` — shared fakes for unit tests / memory container.

**Domain / product docs:**
- `CONTEXT.md`: Glossary and language rules.
- `docs/digest-cds/`: Specs, user stories, development notes.
- `docs/adr/`: Architecture Decision Records.
- `docs/agents/local-platform-runbook.md`: Local platform run instructions.

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g. `publish_material.py`, `knowledge_chunk_repository.py`, `map_captions_error` in `mapping/captions.py`).
- React components/pages: `PascalCase.jsx` (e.g. `VotingPage.jsx`, `AppShell.jsx`).
- Frontend utils/services/data: `camelCase.js` (e.g. `votingApi.js`, `mock.js`); Auth helpers may omit `Api` suffix (`authEnv.js`, `emailDomain.js`).
- SQL migrations: numbered prefix `NNN_description.sql` under `supabase-integration/migrations/`.
- ADRs: `NNNN-kebab-title.md` under `docs/adr/`.
- Playwright specs: `*.spec.js` under `tests/`.
- Pytest / JS unit: `test_*.py` / `test_*.js` under `tests/unit/`.

**Directories:**
- Python packages under `src/<package_name>/` (src layout for all uv members).
- Backend layers: `domain/`, `application/`, `composition/`, `infrastructure/`, `interface/http/`, `tests_support/`.
- Ingestion layers: `domain/` (operator errors), `mapping/` (boundary mappers), `composition/` (settings + clients); URL parse at package root `url.py`.
- Frontend folders by role: `components/`, `pages/`, `services/`, `data/`, `utils/` — not feature-sliced.
- Design pages mirror product routes: `design-frontend/pages/issue.html`, `voting.html`, `knowledge.html`, etc.

**Symbols:**
- Python: `snake_case` functions; `PascalCase` classes/protocols/enums; domain errors end with `Error`.
- React: default-export page/component functions in `PascalCase`.
- Ports: noun + capability (`MaterialRepository`, `DigestPublisher`, `QueryEmbedder`).
- Use-cases: verb phrases as module and function names (`cast_vote`, `send_digest`).
- Ingestion mappers: `map_<stage>_error` returning `IngestError`; reasons are locked string sets per stage.
- Env (frontend): `VITE_*`; backend: `APP_CONTAINER`, `SUPABASE_*`, `ALLOWED_EMAIL_DOMAINS`, `NOTEBOOK_ROOT`, `MAILER`, `API_CORS_ORIGINS`; ingestion: `YOUTUBE_PROXY_URL`.

## Where to Add New Code

**New domain behavior:**
- Primary code: `backend/src/backend/domain/` and/or `backend/src/backend/application/use_cases/`
- New port (if I/O needed): `backend/src/backend/application/ports/<name>.py`
- Wire: `backend/src/backend/composition/container.py` and `live.py` when live adapter exists
- HTTP (if public): thin handler under `backend/src/backend/interface/http/routes/`
- Tests first: `tests/unit/test_<behavior>.py` with in-memory fakes in `tests_support/`
- Do **not** put SDK calls in domain/use-cases.

**New HTTP API endpoint:**
- Router module under `backend/src/backend/interface/http/routes/`; register in `app.py`.
- Auth via `deps.py` patterns; compose dependencies only from `app.state.container`.
- Tests: unit for use-case; HTTP contract tests under `tests/unit/`.

**New Supabase / Postgres persistence:**
- Schema: new migration under `supabase-integration/migrations/`.
- Adapter implementing ports: under `supabase-integration/src/supabase_integration/` (export via package `__init__.py`).
- Wire adapter in `composition/live.py`.
- Contract tests: extend migration/repository contract tests in `tests/unit/`.

**New external API (YouTube, FoundryModels, …):**
- DTOs / validation: `data-collection/src/data_collection/dto/`
- Typed adapter errors: `data-collection/src/data_collection/errors/`
- Live client/adapter: `data-collection/src/data_collection/adapters/` (inject ready clients; no env/proxy reads inside adapters).
- Operator diagnostics: map in `ingestion-service/src/ingestion_service/mapping/` → `IngestError`.
- Ready clients / proxy: `ingestion-service/src/ingestion_service/composition/`.
- Export from package `__init__.py` public barrels.
- Tests: `tests/unit/test_*_dto.py` / adapter / mapper patterns.

**New ingestion pipeline stage:**
- Stage name must already exist (or be extended carefully) on `IngestError.Stage`.
- Mapper + locked reasons under `ingestion-service/.../mapping/` when mapping adapter errors.
- Orchestration / CLI entry under `ingestion-service` (not FastAPI).
- Do **not** import `backend.interface.http` or call the web API for persist.

**New UI page or component:**
- Page: `web/src/pages/<Name>Page.jsx` + route in `web/src/App.jsx`
- Component: `web/src/components/<Name>.jsx`
- API calls: `web/src/services/<name>Api.js` only
- Shared pure helpers: `web/src/utils/`
- Fixtures: `web/src/data/` when mocks needed
- Design alignment: matching `design-frontend/pages/` + tokens
- E2E: extend or add `tests/*.spec.js`

**New ADR / domain term:**
- ADR: `docs/adr/NNNN-title.md`
- Glossary: `CONTEXT.md` (single source; see `docs/agents/domain.md`)

**Utilities:**
- Prefer ownership inside a bounded context (backend / web / data-collection / ingestion-service / supabase-integration).
- Avoid new root-level “common utils” packages without a clear owner.
- Root `scripts/` is for tooling only, not business logic.

## Special Directories

**`web/dist/`:**
- Purpose: Vite production build output.
- Generated: Yes.
- Committed: No (build artifact).

**`node_modules/`, `.venv/`, `.pytest_cache/`, `test-results/`, `.playwright-browsers/`:**
- Purpose: Dependencies, caches, test artifacts, local browsers.
- Generated: Yes.
- Committed: No.

**`.env`:**
- Purpose: Local secrets and environment configuration.
- Generated: No (local).
- Committed: No — never quote contents in docs or commits.

**`.planning/codebase/`:**
- Purpose: Generated architecture maps for GSD planners/executors.
- Generated: By `/gsd-map-codebase`.
- Committed: Yes when orchestrator commits planning artifacts.

**`design-frontend/.hallmark/`:**
- Purpose: Hallmark design skill log/metadata.
- Generated: Tooling.
- Committed: As present in tree.

**Planned / incomplete (do not invent early beyond ports):**
- Full ingestion CLI entry (`python -m ingestion_service`) and pipeline stages `consistency` / `llm` / `llm_truncation` / `persist`.
- Live Foundry clients beyond current data-collection surface.
- Real `QueryEmbedder` adapter (live still uses `StubQueryEmbedder`).
- `SmtpMailer` (`MAILER=smtp` currently fails fast).
- Dedicated HTTP for standalone publish/index admin APIs.

## Prescriptive Placement Checklist

| Change type | Put it here |
|-------------|-------------|
| Entity / domain error | `backend/src/backend/domain/` |
| Use-case | `backend/src/backend/application/use_cases/` |
| Port (Protocol) | `backend/src/backend/application/ports/` |
| Wire adapters | `backend/src/backend/composition/` (`container.py` / `live.py`) |
| Backend-local adapter | `backend/src/backend/infrastructure/` |
| HTTP router | `backend/src/backend/interface/http/routes/` |
| In-memory fake | `backend/src/backend/tests_support/` |
| SQL schema / RPC | `supabase-integration/migrations/` |
| Supabase port adapter | `supabase-integration/src/supabase_integration/` |
| External DTO | `data-collection/src/data_collection/dto/` |
| External adapter / typed fetch error | `data-collection/src/data_collection/adapters/` / `errors/` |
| Ingestion URL parse | `ingestion-service/src/ingestion_service/url.py` |
| IngestError / Stage | `ingestion-service/src/ingestion_service/domain/errors.py` |
| Map adapter → IngestError | `ingestion-service/src/ingestion_service/mapping/` |
| Ingestion clients / proxy Settings | `ingestion-service/src/ingestion_service/composition/` |
| React page | `web/src/pages/` |
| React component | `web/src/components/` |
| Frontend API call | `web/src/services/` |
| Unit test (Python/JS) | `tests/unit/` |
| E2E test | `tests/*.spec.js` |

---

*Structure analysis: 2026-09-27*
