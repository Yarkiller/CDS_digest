# Digest CDS

Digest CDS — корпоративный сервис сбора, структурирования и распространения
знаний для сотрудников СВА. В репозитории: канонический UI Concept 3
(Editorial) и React-приложение ДЗ на его основе.

## Ссылки

| Что | Куда |
|-----|------|
| GitHub | [https://github.com/Yarkiller/digest_cds](https://github.com/Yarkiller/digest_cds) |
| Отчёт о разработке | [`development_report.md`](development_report.md) |
| ТЗ | [`docs/digest-cds/technical_specification.md`](docs/digest-cds/technical_specification.md) |
| Скриншоты адаптива | [`docs/digest-cds/responsive-evidence/`](docs/digest-cds/responsive-evidence/) |
| Local platform runbook | [`docs/agents/local-platform-runbook.md`](docs/agents/local-platform-runbook.md) |
| Cloud.ru app deploy path (docs only) | [`docs/agents/cloudru-app-deploy-path.md`](docs/agents/cloudru-app-deploy-path.md) |

## Технологический стек

| Слой | Выбор |
|------|-------|
| Сборка / dev-сервер | Vite |
| UI-фреймворк | React |
| Роутинг | React Router |
| Стилизация | Tailwind CSS (токены из `design-frontend/styles/tokens.css`) |
| Автотесты UI | Playwright |
| Backend (domain/ports) | Python / `uv` — [`backend/`](backend/) |
| API DTOs | [`data-collection/`](data-collection/) |
| БД / миграции | [`supabase-integration/migrations/`](supabase-integration/migrations/) (Supabase + pgvector) |
| Unit-тесты Python | `uv run pytest` / `npm run test:unit` |

Зависимости приложения: [`web/package.json`](web/package.json).  
Зависимости тестов (корень): [`package.json`](package.json).

### Минимум 3 основные функции

1. **Выпуск и материал** — текущий выпуск и страница статьи (`/`, `/materials/:id`).
2. **Голосование** — выбор и подтверждение темы цикла (`/voting`).
3. **База знаний** — поиск, фильтры и список материалов (`/knowledge`).

## Демо (локальный запуск)

```bash
# из корня репозитория
npm install
npm install --prefix web
npm run dev
```

Открыть: [http://127.0.0.1:5173](http://127.0.0.1:5173)

Эквивалент:

```bash
cd web
npm install
npm run dev
```

Production-сборка: `npm run build` (из корня или `web/`), превью: `npm run preview --prefix web`.

## Local platform (API + remote Supabase)

Phase 1 uses the **existing remote** Supabase VM (`knowledge-db.ru`). Full bring-up,
Auth seed (D-08), and live FE↔BE checklist: [`docs/agents/local-platform-runbook.md`](docs/agents/local-platform-runbook.md).
Cloud.ru **app** deploy is documented only (no Phase 1 deploy): [`docs/agents/cloudru-app-deploy-path.md`](docs/agents/cloudru-app-deploy-path.md).

Quick start:

1. Copy [`.env.example`](.env.example) → `.env` and fill values (never commit secrets;
   never put `SUPABASE_SECRET_KEY` behind a `VITE_` prefix).
2. `uv sync` then, with `APP_CONTAINER=live`:

   ```bash
   uv run uvicorn backend.interface.http.app:create_default_app --factory --host 127.0.0.1 --port 8000
   ```

3. `npm install` / `npm run dev` — set `VITE_USE_MOCKS=false` only for live proof.
4. Seed 1–2 corporate Auth users on the dashboard (see runbook §4).

## Тесты

```bash
npm install                   # подтянет зависимости и при необходимости Chromium в .playwright-browsers/
npm run playwright:install    # явно доустановить браузеры (идемпотентно)
npm test                      # оба проекта
npm run test:web              # только React-приложение (не поднимает статический сервер макетов)
npm run test:design           # только design-frontend
```

Браузеры Playwright хранятся в **`.playwright-browsers/`** (в корне репо, в git не коммитится).
Так они не теряются при смене временного кэша Cursor sandbox.

- `design-frontend` — эталон макетов на `http://127.0.0.1:8765` (Node `serve`, без Python)
- `web` — React-приложение на `http://127.0.0.1:5174` (Vite)

## Каноническая структура

```text
.
├── web/                   # Vite + React + Tailwind (приложение ДЗ)
├── design-frontend/       # эталон UI Concept 3 (статика)
├── docs/
│   ├── digest-cds/        # ТЗ, отчёт, user stories, скриншоты
│   ├── adr/
│   └── agents/
├── tests/                 # Playwright
├── CONTEXT.md
├── AGENTS.md
└── archive/
```

## Эталон макетов

Кроссплатформенно (macOS / Linux / Windows), из корня репозитория:

```bash
npm run serve:design
```

Эквивалент: `npx --yes serve@14.2.4 . -l 8765 --no-port-switching`

Открыть: [http://127.0.0.1:8765/design-frontend/index.html](http://127.0.0.1:8765/design-frontend/index.html)

Карта экранов: [`design-frontend/README.md`](design-frontend/README.md).
