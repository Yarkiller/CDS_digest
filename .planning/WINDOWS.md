---
schema_version: 1
open_count: 0
waived_count: 8
fixed_count: 12
total_count: 20
last_updated: 2026-10-16T15:25:19.633Z
---

# Broken Windows Ledger

> Cross-phase defect register. With `workflow.windows_enforce` enabled, `/gsd-ship` blocks while `open_count > 0`.
> Waive with `gsd-tools windows waive <id> "<reason>"` (reason required).
> Mark fixed with `gsd-tools windows fixed <id>`.

| id | phase | kind | file | line | description | status | reason | recorded_at | resolved_at |
|----|-------|------|------|------|-------------|--------|--------|-------------|-------------|
| 1 | 01 | deviation | README.md |  | Auth dashboard corporate test-user seed deferred to Plan 01-06 (D-08) | fixed |  | 2026-09-19T15:26:47.454Z | 2026-10-13T18:06:26.543Z |
| 2 | 01 | deviation | playwright.config.js |  | Expanded web testMatch to include auth.spec.js so Plan 01-05 verify can run | waived | Standing config: playwright browser testMatch intentionally covers web-app auth knowledge razbory admin specs | 2026-09-19T15:32:14.897Z | 2026-10-13T18:06:37.725Z |
| 3 | 02 | skipped-test | tests/web-app.spec.js | 406 | UI-SPEC visual backstops describe.skip held for /gsd-verify-work | fixed |  | 2026-09-20T11:09:43.276Z | 2026-10-13T18:06:27.166Z |
| 4 | 04 | stub | backend/src/backend/application/ports/query_embedder.py |  | StubQueryEmbedder deterministic hash embedder, not Foundry HTTP (Phase 4 OPT-OUT) | waived | StubQueryEmbedder is the accepted state; real Foundry embedder deferred to v1.3 per PROJECT.md | 2026-09-21T04:34:37.222Z | 2026-10-13T18:06:38.386Z |
| 5 | 04 | stub | backend/src/backend/composition/live.py |  | live.py chunks still InMemoryKnowledgeChunkRepository until 04-08 | fixed |  | 2026-09-21T04:34:37.841Z | 2026-10-13T18:06:27.749Z |
| 6 | 04 | skipped-test | tests/web-app.spec.js |  | Knowledge Playwright tests still assert client filterMaterials/tag facets; rewrite deferred to 04-09 | fixed |  | 2026-09-21T04:40:59.311Z | 2026-09-21T05:04:04.951Z |
| 7 | 04 | deviation | web/src/services/knowledgeApi.js |  | Dynamic import of authEnv/authApi so mockSearchKnowledge stays node:test-friendly without Vite env | waived | Intentional Vite import.meta boundary so knowledgeApi stays node:test friendly | 2026-09-21T04:40:59.943Z | 2026-10-13T18:06:38.984Z |
| 8 | 04 | stub | backend/src/backend/application/use_cases/get_razbor.py |  | get_razbor NotFound only; detail HTTP deferred to 04-06 | fixed |  | 2026-09-21T04:45:39.748Z | 2026-10-13T18:06:28.336Z |
| 9 | 04 | stub | backend/src/backend/composition/live.py |  | live.py razbors still InMemoryRazborRepository until adapter | fixed |  | 2026-09-21T04:45:40.363Z | 2026-10-13T18:06:28.912Z |
| 10 | 04 | deviation | tests/web-app.spec.js |  | Retired Загрузить ещё Playwright case; mock catalog is smaller than page size 10 | waived | Deliberate: Zagruzit eshche case retired because the mock catalog is smaller than page size 10 | 2026-09-21T05:02:21.685Z | 2026-10-13T18:06:39.592Z |
| 11 | 04 | stub | web/src/App.jsx |  | /razbory/:id placeholder shell until 04-06 | fixed |  | 2026-09-21T05:12:01.843Z | 2026-10-13T18:06:29.492Z |
| 12 | 04 | stub | tests/ |  | Playwright razbory list/empty/nav deferred to 04-09 | fixed |  | 2026-09-21T05:12:02.428Z | 2026-09-21T09:25:00.909Z |
| 13 | 04 | stub | tests/web-app.spec.js |  | Playwright notebook enable/disable proofs deferred to 04-09 | fixed |  | 2026-09-21T05:25:32.263Z | 2026-09-21T09:25:01.654Z |
| 14 | 04 | unmet-truth | .planning/phases/04-knowledge-razbory/04-VALIDATION.md |  | UI-SPEC overflow/long-text backstops held for verify-work (pagination has_more, many chronology, visual wrap) | fixed |  | 2026-09-21T09:25:10.848Z | 2026-10-13T18:06:30.085Z |
| 15 | 05 | deviation | web/src/services/adminPreviewComposition.js |  | Extracted pure composition helpers for node --test (Vite import.meta boundary) | waived | Intentional extraction of pure composition helpers to keep adminPreviewComposition.js Vite free for node --test | 2026-09-21T18:31:58.934Z | 2026-10-13T18:06:45.952Z |
| 16 | 10 | deviation | ingestion-service/src/ingestion_service/application/ports/persist.py |  | already_saved defaults False for deferred 10-05 call sites | waived | Benign False default on the persist port; no behavior gap, call sites pass it explicitly | 2026-09-29T17:58:41.951Z | 2026-10-13T18:06:46.581Z |
| 17 | 11 | deviation | tests/unit/test_cli_ingest_contract.py |  | Unexpected GREEN Task1: CLI sent-batch contract passed without cli.py change (prior plans) | waived | Observation only: a contract test passed without a code change, no defect to fix | 2026-10-02T13:36:12.392Z | 2026-10-13T18:06:47.183Z |
| 18 | 15 | deviation | ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py |  | Deviation: sink emits via injected emitter (cli.py typer.echo err=True) not direct typer import, to satisfy test_ingestion_service_has_no_typer_import | waived | Intentional shipped design: sink emits via injected emitter to keep ingestion-service typer free | 2026-10-04T08:12:39.822Z | 2026-10-13T18:06:47.759Z |
| 19 | 16 | stub | backend/src/backend/interface/http/routes/admin.py | 552 | 16-01 tracer: PUT /admin/pipeline/config has no PipelineConfigValidationError reject branch yet; structured 400 {errors:[...]} lands in 16-02 behind the same validator port | fixed |  | 2026-10-04T10:43:11.118Z | 2026-10-13T18:06:30.673Z |
| 20 | 21 | unrun-verify |  |  | Playwright tests/admin.spec.js stub-banner assertions amended but not executed | fixed |  | 2026-10-16T15:01:10.477Z | 2026-10-16T15:25:19.633Z |

````json
[
  {
    "id": 1,
    "kind": "deviation",
    "phase": "01",
    "file": "README.md",
    "line": null,
    "description": "Auth dashboard corporate test-user seed deferred to Plan 01-06 (D-08)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-19T15:26:47.454Z",
    "resolved_at": "2026-10-13T18:06:26.543Z"
  },
  {
    "id": 2,
    "kind": "deviation",
    "phase": "01",
    "file": "playwright.config.js",
    "line": null,
    "description": "Expanded web testMatch to include auth.spec.js so Plan 01-05 verify can run",
    "status": "waived",
    "reason": "Standing config: playwright browser testMatch intentionally covers web-app auth knowledge razbory admin specs",
    "recorded_at": "2026-09-19T15:32:14.897Z",
    "resolved_at": "2026-10-13T18:06:37.725Z"
  },
  {
    "id": 3,
    "kind": "skipped-test",
    "phase": "02",
    "file": "tests/web-app.spec.js",
    "line": 406,
    "description": "UI-SPEC visual backstops describe.skip held for /gsd-verify-work",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-20T11:09:43.276Z",
    "resolved_at": "2026-10-13T18:06:27.166Z"
  },
  {
    "id": 4,
    "kind": "stub",
    "phase": "04",
    "file": "backend/src/backend/application/ports/query_embedder.py",
    "line": null,
    "description": "StubQueryEmbedder deterministic hash embedder, not Foundry HTTP (Phase 4 OPT-OUT)",
    "status": "waived",
    "reason": "StubQueryEmbedder is the accepted state; real Foundry embedder deferred to v1.3 per PROJECT.md",
    "recorded_at": "2026-09-21T04:34:37.222Z",
    "resolved_at": "2026-10-13T18:06:38.386Z"
  },
  {
    "id": 5,
    "kind": "stub",
    "phase": "04",
    "file": "backend/src/backend/composition/live.py",
    "line": null,
    "description": "live.py chunks still InMemoryKnowledgeChunkRepository until 04-08",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T04:34:37.841Z",
    "resolved_at": "2026-10-13T18:06:27.749Z"
  },
  {
    "id": 6,
    "kind": "skipped-test",
    "phase": "04",
    "file": "tests/web-app.spec.js",
    "line": null,
    "description": "Knowledge Playwright tests still assert client filterMaterials/tag facets; rewrite deferred to 04-09",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T04:40:59.311Z",
    "resolved_at": "2026-09-21T05:04:04.951Z"
  },
  {
    "id": 7,
    "kind": "deviation",
    "phase": "04",
    "file": "web/src/services/knowledgeApi.js",
    "line": null,
    "description": "Dynamic import of authEnv/authApi so mockSearchKnowledge stays node:test-friendly without Vite env",
    "status": "waived",
    "reason": "Intentional Vite import.meta boundary so knowledgeApi stays node:test friendly",
    "recorded_at": "2026-09-21T04:40:59.943Z",
    "resolved_at": "2026-10-13T18:06:38.984Z"
  },
  {
    "id": 8,
    "kind": "stub",
    "phase": "04",
    "file": "backend/src/backend/application/use_cases/get_razbor.py",
    "line": null,
    "description": "get_razbor NotFound only; detail HTTP deferred to 04-06",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T04:45:39.748Z",
    "resolved_at": "2026-10-13T18:06:28.336Z"
  },
  {
    "id": 9,
    "kind": "stub",
    "phase": "04",
    "file": "backend/src/backend/composition/live.py",
    "line": null,
    "description": "live.py razbors still InMemoryRazborRepository until adapter",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T04:45:40.363Z",
    "resolved_at": "2026-10-13T18:06:28.912Z"
  },
  {
    "id": 10,
    "kind": "deviation",
    "phase": "04",
    "file": "tests/web-app.spec.js",
    "line": null,
    "description": "Retired Загрузить ещё Playwright case; mock catalog is smaller than page size 10",
    "status": "waived",
    "reason": "Deliberate: Zagruzit eshche case retired because the mock catalog is smaller than page size 10",
    "recorded_at": "2026-09-21T05:02:21.685Z",
    "resolved_at": "2026-10-13T18:06:39.592Z"
  },
  {
    "id": 11,
    "kind": "stub",
    "phase": "04",
    "file": "web/src/App.jsx",
    "line": null,
    "description": "/razbory/:id placeholder shell until 04-06",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T05:12:01.843Z",
    "resolved_at": "2026-10-13T18:06:29.492Z"
  },
  {
    "id": 12,
    "kind": "stub",
    "phase": "04",
    "file": "tests/",
    "line": null,
    "description": "Playwright razbory list/empty/nav deferred to 04-09",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T05:12:02.428Z",
    "resolved_at": "2026-09-21T09:25:00.909Z"
  },
  {
    "id": 13,
    "kind": "stub",
    "phase": "04",
    "file": "tests/web-app.spec.js",
    "line": null,
    "description": "Playwright notebook enable/disable proofs deferred to 04-09",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T05:25:32.263Z",
    "resolved_at": "2026-09-21T09:25:01.654Z"
  },
  {
    "id": 14,
    "kind": "unmet-truth",
    "phase": "04",
    "file": ".planning/phases/04-knowledge-razbory/04-VALIDATION.md",
    "line": null,
    "description": "UI-SPEC overflow/long-text backstops held for verify-work (pagination has_more, many chronology, visual wrap)",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-09-21T09:25:10.848Z",
    "resolved_at": "2026-10-13T18:06:30.085Z"
  },
  {
    "id": 15,
    "kind": "deviation",
    "phase": "05",
    "file": "web/src/services/adminPreviewComposition.js",
    "line": null,
    "description": "Extracted pure composition helpers for node --test (Vite import.meta boundary)",
    "status": "waived",
    "reason": "Intentional extraction of pure composition helpers to keep adminPreviewComposition.js Vite free for node --test",
    "recorded_at": "2026-09-21T18:31:58.934Z",
    "resolved_at": "2026-10-13T18:06:45.952Z"
  },
  {
    "id": 16,
    "kind": "deviation",
    "phase": "10",
    "file": "ingestion-service/src/ingestion_service/application/ports/persist.py",
    "line": null,
    "description": "already_saved defaults False for deferred 10-05 call sites",
    "status": "waived",
    "reason": "Benign False default on the persist port; no behavior gap, call sites pass it explicitly",
    "recorded_at": "2026-09-29T17:58:41.951Z",
    "resolved_at": "2026-10-13T18:06:46.581Z",
    "milestone": "v1.1"
  },
  {
    "id": 17,
    "kind": "deviation",
    "phase": "11",
    "file": "tests/unit/test_cli_ingest_contract.py",
    "line": null,
    "description": "Unexpected GREEN Task1: CLI sent-batch contract passed without cli.py change (prior plans)",
    "status": "waived",
    "reason": "Observation only: a contract test passed without a code change, no defect to fix",
    "recorded_at": "2026-10-02T13:36:12.392Z",
    "resolved_at": "2026-10-13T18:06:47.183Z",
    "milestone": "v1.1"
  },
  {
    "id": 18,
    "kind": "deviation",
    "phase": "15",
    "file": "ingestion-service/src/ingestion_service/adapters/stderr_diagnostics.py",
    "line": null,
    "description": "Deviation: sink emits via injected emitter (cli.py typer.echo err=True) not direct typer import, to satisfy test_ingestion_service_has_no_typer_import",
    "status": "waived",
    "reason": "Intentional shipped design: sink emits via injected emitter to keep ingestion-service typer free",
    "recorded_at": "2026-10-04T08:12:39.822Z",
    "resolved_at": "2026-10-13T18:06:47.759Z",
    "milestone": "v1.2"
  },
  {
    "id": 19,
    "kind": "stub",
    "phase": "16",
    "file": "backend/src/backend/interface/http/routes/admin.py",
    "line": 552,
    "description": "16-01 tracer: PUT /admin/pipeline/config has no PipelineConfigValidationError reject branch yet; structured 400 {errors:[...]} lands in 16-02 behind the same validator port",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-04T10:43:11.118Z",
    "resolved_at": "2026-10-13T18:06:30.673Z",
    "milestone": "v1.2"
  },
  {
    "id": 20,
    "kind": "unrun-verify",
    "phase": "21",
    "file": "",
    "line": null,
    "description": "Playwright tests/admin.spec.js stub-banner assertions amended but not executed",
    "status": "fixed",
    "reason": "",
    "recorded_at": "2026-10-16T15:01:10.477Z",
    "resolved_at": "2026-10-16T15:25:19.633Z",
    "milestone": "v1.3"
  }
]
````
