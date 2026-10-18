---
last_mapped_commit: 252c024622021ec59fe22abdd251c2047849d1da
---
<!-- refreshed: 2026-09-27 -->
# Technology Stack

**Analysis Date:** 2026-09-27

## Languages

**Primary:**
- Python 3.12 — workspace packages `backend/`, `data-collection/`, `ingestion-service/`, `supabase-integration/` (pinned via `.python-version` and `requires-python = ">=3.12"`)
- JavaScript (ES modules, JSX) — React SPA in `web/`, Playwright tests in `tests/`, static design reference in `design-frontend/`

**Secondary:**
- SQL (Postgres / Supabase) — schema, RLS, RPCs in `supabase-integration/migrations/` (`001`…`006`)
- CSS — Tailwind v4 via Vite plugin in `web/`; design tokens in `design-frontend/styles/`
- Markdown — domain docs (`CONTEXT.md`, `docs/`), ADRs (`docs/adr/`), material body rendering via `react-markdown`

**Not in use for app source:**
- TypeScript — only `@types/react` / `@types/react-dom` as Vite/React typing aids; app sources are `.jsx` / `.js`

## Runtime

**Environment:**
- CPython 3.12 — local `.venv/` managed by `uv`
- Node.js — npm scripts and Vite/Playwright (engine not pinned in `package.json`)
- Uvicorn ASGI server — FastAPI app factory `backend.interface.http.app:create_default_app` on `127.0.0.1:8000`
- Browsers for E2E — Chromium via Playwright, cached under `.playwright-browsers/`
- Ingestion operator path — Python package `ingestion-service` (CLI-oriented; no ASGI app in this package yet)

**Package Manager:**
- **uv** — Python workspace root `pyproject.toml` + `uv.lock`; rule: use `uv add` / `uv sync` / `uv run` only (see `.cursor/rules/python-uv.mdc`)
- **npm** — root `package.json` + `web/package.json`; lockfiles: `package-lock.json`, `web/package-lock.json` (lockfileVersion 3)

## Frameworks

**Core:**
- FastAPI 0.141.1 — HTTP edge (`backend/src/backend/interface/http/`)
- Uvicorn 0.53.0 (`uvicorn[standard]`) — ASGI server
- React 19.2.8 — UI (`web/src/`)
- React Router DOM 7.18.3 — client routing (`web/src/App.jsx`)
- Vite 8.2.2 — build/dev server (`web/vite.config.js`, host `127.0.0.1:5173`)
- Tailwind CSS 4.3.3 + `@tailwindcss/vite` — styling
- Pydantic 2.13.5 — boundary DTOs in `data-collection/`

**Testing:**
- Playwright `@playwright/test` 1.62.1 — E2E for `design-frontend` and `web` (`playwright.config.js`, `tests/`)
- pytest 9.1.1 — Python unit tests (`tests/unit/`, config in root `pyproject.toml`)

**Build/Dev:**
- Vite (`npm run dev` / `build` / `preview`)
- oxlint 1.81.0 — JS lint (`web/.oxlintrc.json`, `npm run lint --prefix web`)
- `serve@14.2.4` (npx) — static design-frontend server on port 8765
- `uv_build` — Python package build backend for workspace members (including `ingestion-service`)

## Key Dependencies

**Critical:**
- `fastapi` 0.141.1 / `uvicorn` 0.53.0 — public API (`/health`, `/me`, `/issues`, `/materials`, `/knowledge`, `/razbory`, `/voting`, `/admin`)
- `supabase` (Python) 2.31.0 — PostgREST adapters in `supabase-integration/` (`create_client` only in `client.py` / composition)
- `@supabase/supabase-js` 2.116.0 — browser Auth (`signInWithPassword` / `signUp`) via `web/src/services/supabaseClient.js`
- `pyjwt` 2.14.0 + `cryptography` 50.0.1 — ES256 JWKS verification (`backend/infrastructure/auth_jwt.py`)
- `react` / `react-dom` 19.2.8 — SPA delivery
- `react-router-dom` 7.18.3 — routes including `/login`, `/register`, `/admin/digest`, `/razbory`
- `pydantic` 2.13.5 — YouTube / Foundry / text-import DTOs in `data-collection`
- `structlog` 26.1.0 — JSON request logs with `request_id` middleware
- `react-markdown` 10.1.0 (+ `remark-gfm`, `rehype-sanitize`, `rehype-slug`) — material / knowledge markdown rendering
- `data-collection` (workspace) — sole declared dependency of `ingestion-service`; DTOs + caption/metadata error types consumed by ingestion mappers
- `youtube-transcript-api` ≥1.2.0,<2 (resolved 1.2.4) — YouTube captions client wired in `ingestion_service.composition.clients` (`YouTubeTranscriptApi` + optional `GenericProxyConfig`)
- `httpx` 0.28.1 (`httpx[socks]` via `data-collection`) — async HTTP client factory in ingestion composition (30s timeout; optional proxy); also used for FastAPI TestClient stack

**Infrastructure:**
- Self-hosted Supabase (PostgreSQL + `vector` + `pg_trgm`) — schema and adapters owned by `supabase-integration/`
- In-memory fakes — `backend/src/backend/tests_support/in_memory.py` via `APP_CONTAINER=memory` (default) or live adapters via `APP_CONTAINER=live`
- `python-multipart` 0.0.32 — FastAPI form/multipart support
- Playwright browsers — project-local `.playwright-browsers/` via `scripts/ensure-playwright-browsers.cjs`

## Configuration

**Environment:**
- `.env.example` → gitignored `.env` at repo root (backend); `web/.env.local` for Vite (Vite does not read repo-root `.env`)
- Backend loads env only via `Settings.from_env()` / `uv run --env-file .env` (nothing auto-loads `.env` into the process)
- Key backend vars: `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_JWKS_URL`, `SUPABASE_JWT_ISSUER`, `API_CORS_ORIGINS`, `ALLOWED_EMAIL_DOMAINS`, `APP_CONTAINER`, `NOTEBOOK_ROOT`, `MAILER`
- Key Vite vars: `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_API_BASE_URL`, `VITE_USE_MOCKS` (default offline mocks; `false` for live FE↔BE)
- Ingestion composition (`ingestion_service.composition.settings.Settings`): `YOUTUBE_PROXY_URL` (optional; blank/missing → no proxy). Applied only in composition client factories — never inside adapters
- Playwright: `PLAYWRIGHT_BROWSERS_PATH` → `.playwright-browsers/`; forces `VITE_USE_MOCKS=true` for web project
- CI flag: `process.env.CI` controls `reuseExistingServer` in Playwright webServers

**Build:**
- `web/vite.config.js` — React + Tailwind plugins; fixed host/port
- Root `pyproject.toml` — uv workspace members (`backend`, `data-collection`, `ingestion-service`, `supabase-integration`), pytest `testpaths = ["tests/unit"]`
- Member `pyproject.toml` under `backend/`, `data-collection/`, `ingestion-service/`, `supabase-integration/`
- `ingestion-service/pyproject.toml` — package `ingestion-service` 0.1.0; `uv_build` module `ingestion_service` under `src/`; workspace source `data-collection`
- `web/.oxlintrc.json` — React hooks rules

## Platform Requirements

**Development:**
- Python ≥ 3.12 + `uv` (`uv sync`, `uv run pytest`, `uv run --env-file .env uvicorn …`)
- Node.js + npm (`npm install`, `npm install --prefix web`)
- Optional: WSL for Cursor Origin git auth (`docs/agents/git-origin.md`)
- Ports: Vite `5173` (dev) / `5174` (Playwright web); FastAPI `8000`; design static `8765`
- Live path: remote self-hosted Supabase VM (`https://knowledge-db.ru/`) — no local Docker Supabase required (runbook D-05)
- Optional outbound proxy for YouTube ingest: set `YOUTUBE_PROXY_URL` when calling ingestion composition factories

**Production:**
- Application VM on **Cloud.ru** (ADR-0002)
- Separate VM for **self-hosted Supabase** via Docker Compose (ADR-0004); managed Supabase Cloud and managed Postgres Cloud.ru are out of scope
- ML calls stay in Cloud.ru **FoundryModels** (no public foreign LLM/Whisper APIs) — DTO contracts exist; live SDK adapters not installed yet
- Digest mailer: `MAILER=stub` in v1; live corporate SMTP deferred (`SmtpMailer` fails fast)

## Workspace Layout (stack-relevant)

| Path | Role |
|------|------|
| `web/` | Vite + React + Tailwind SPA (Auth + content APIs) |
| `design-frontend/` | Static UI Concept 3 reference (HTML/CSS/JS) |
| `backend/` | Domain, ports, use-cases, FastAPI HTTP, composition |
| `data-collection/` | External API DTOs + YouTube caption/oEmbed adapters (YouTube, Foundry, text import) |
| `ingestion-service/` | Operator ingest package: URL parse, staged `IngestError` mapping, composition client factories (YouTube transcript + httpx); CLI/LLM/persist not shipped in-package yet |
| `supabase-integration/` | Migrations + Supabase PostgREST adapters |
| `tests/` | Playwright E2E + `tests/unit` pytest |
| `docs/adr/` | Architecture decisions binding stack choices |
| `docs/agents/local-platform-runbook.md` | Local FE↔BE bring-up against knowledge-db.ru |

---

*Stack analysis: 2026-09-27*
*Update after major dependency changes*
