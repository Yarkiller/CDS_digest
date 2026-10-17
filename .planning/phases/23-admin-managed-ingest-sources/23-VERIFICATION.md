---
phase: 23-admin-managed-ingest-sources
verified: 2026-10-17T17:55:00Z
status: passed
score: 3/7 must-haves verified
covered_files:
  - .planning/phases/23-admin-managed-ingest-sources/23-01-PLAN.md
  - .planning/phases/23-admin-managed-ingest-sources/23-01-SUMMARY.md
  - .planning/phases/23-admin-managed-ingest-sources/23-02-PLAN.md
  - .planning/phases/23-admin-managed-ingest-sources/23-02-SUMMARY.md
  - .planning/phases/23-admin-managed-ingest-sources/23-03-PLAN.md
  - .planning/phases/23-admin-managed-ingest-sources/23-03-SUMMARY.md
  - .planning/phases/23-admin-managed-ingest-sources/23-04-PLAN.md
  - .planning/phases/23-admin-managed-ingest-sources/23-04-SUMMARY.md
  - backend/src/backend/domain/ingest_source.py
  - backend/src/backend/application/ports/ingest_sources.py
  - backend/src/backend/application/use_cases/ingest_sources.py
  - backend/src/backend/tests_support/in_memory.py
  - backend/src/backend/composition/container.py
  - backend/src/backend/composition/live.py
  - backend/src/backend/interface/http/routes/admin.py
  - backend/src/backend/interface/http/app.py
  - web/src/services/ingestSourcesApi.js
  - web/src/components/IngestSourcesSection.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/main.jsx
  - supabase-integration/migrations/012_phase23_ingest_sources.sql
  - supabase-integration/src/supabase_integration/ingest_source_repository.py
  - supabase-integration/src/supabase_integration/__init__.py
  - docs/agents/local-platform-runbook.md
  - tests/unit/test_http_ingest_sources.py
  - tests/unit/test_phase23_migration_012.py
  - tests/unit/test_supabase_ingest_source_repository_contract.py
  - tests/unit/test_live_container_wiring.py
  - tests/admin.spec.js

covered_digest: "v2:sha256:dbcf24566fcf1c0c611d327d923ada4b32ccebb214b8360d61afbfd0bb8c4e17"
behavior_unverified: 1
overrides_applied: 0
decision_coverage:
  honored: 24
  total: 24
  not_honored: []
behavior_unverified_items:
  - truth: "Phase 19 unsaved-changes guard covers the ingest-sources editor on /admin/pipeline (ADUX-10) — dirty OR arms a single leave dialog"
    test: "На /admin/pipeline ввести id или label в форме источников, затем уйти на «Дайджест»; отдельно проверить, что смена только kind не открывает диалог; после успешного add при чистом YAML уход без диалога"
    expected: "Один диалог Phase 19 с копией «Есть несохранённые изменения. Уйти без сохранения?»; kind-only не вооружает; успешный add снимает sourceFormDirty"
    why_human: "Инвариант dirty/blocker — state transition; pytest не покрывает SPA; Playwright-тесты есть, но в этом прогоне сервер не поднимался и e2e не исполнялись"
human_verification:
  - test: "ADUX-10: dirty OR на форме источников (id/label vs kind-only vs после успешного add)"
    expected: "Один UnsavedChangesDialog с Phase-19 копией; kind-only не промптит; успешный add разоружает при чистом YAML"
    why_human: "Поведение guard навигации нельзя доказать grep/presence; нужен браузерный прогон (Playwright или ручной)"
  - test: "Визуально: длинный список источников и YAML ниже на 1280px и узкой ширине"
    expected: "Страница скроллится; редактор YAML остаётся достижимым"
    why_human: "truth с verification: backstop — layout нельзя вывести из кода"
  - test: "Визуально: label 120 символов в строке источника"
    expected: "Перенос/break-words без горизонтального overflow страницы"
    why_human: "truth с verification: backstop"
  - test: "Визуально: раскрытый блок «Где взять id?»"
    expected: "Рецепты канала/плейлиста укладываются в ширину секции без горизонтального overflow"
    why_human: "truth с verification: backstop"
  - test: "Опционально ops: RLS/policies каталог для pipeline_ingest_sources"
    expected: "relrowsecurity=true; count(pg_policies)=0; ingestion_sources не затронут"
    why_human: "Таблица живая подтверждена PostgREST []; полный catalog check требует Studio/psql (POSTGRES_URL недоступен verifier'у)"
---

# Phase 23: Admin-managed ingest sources — Verification Report

**Phase Goal:** An admin manages the list of ingest sources (YouTube channel or playlist) on the pipeline page, stored in the database, with server-side canonical-id validation.

**Verified:** 2026-10-17T17:55:00Z  
**Status:** human_needed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Admin can list, add, enable/disable, remove ingest sources on the pipeline page; list survives reload via new DB table + idempotent migration | ✓ VERIFIED | HTTP lifecycle pytest green; section mounted above YAML via `IngestSourcesSection` → `ingestSourcesApi`; migration `012` + live PostgREST `pipeline_ingest_sources` → `[]`; runbook §4i Applied (2026-10-17) |
| 2 | API validates UC…/PL… server-side; rejects with top-level `{errors:[…]}` and zero writes; UI states where to obtain the id | ✓ VERIFIED | `test_post_invalid_source_id_*` / kind-mismatch / duplicate / label-too-long assert 400 + unchanged `write_count`; mapper `content={"errors":[…]}`; UI «Где взять id?» + recipes in `IngestSourcesSection.jsx` |
| 3 | Sources via `IngestSourceRepository` port; Supabase adapter only in composition; SPA only through service module | ✓ VERIFIED | Port + use cases; `live.py` wires `SupabaseIngestSourceRepository(admin_client)`; in-memory in `build_in_memory_container`; no supabase imports in `web/src/pages`/`components`; service `ingestSourcesApi.js` |
| 4 | Phase 19 unsaved-changes guard covers ingest-sources editor (ADUX-10) | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | Code: `dirty = yamlDirty \|\| sourceFormDirty`, один `useUnsavedChangesGuard`, один `UnsavedChangesDialog`. Playwright cases существуют (`sourceFormDirty id arms…` и др.), но e2e в этом прогоне не запускались (нет dev-server) |
| 5 | Longer-than-typical source list scrolls; YAML remains reachable at 1280px / narrow (backstop) | ⚠️ insufficient_spec | Нет held-out/property теста layout; presence секции не доказывает overflow |
| 6 | 120-char label wraps/truncates without horizontal page overflow (backstop) | ⚠️ insufficient_spec | Заявлено в 23-04; human_judgment в SUMMARY; нет automated proof |
| 7 | Expanded id-help recipes wrap without horizontal overflow (backstop) | ⚠️ insufficient_spec | То же |

**Score:** 3/7 truths verified (1 present, behavior-unverified; 3 insufficient_spec / backstop)

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `backend/.../domain/ingest_source.py` | Entity | ✓ VERIFIED | Frozen entity fields |
| `backend/.../ports/ingest_sources.py` | Protocol | ✓ VERIFIED | list/add/set_enabled/delete |
| `backend/.../use_cases/ingest_sources.py` | Validate-then-persist | ✓ VERIFIED | UC/PL regex, duplicate, label max |
| `backend/.../tests_support/in_memory.py` | Fake + write log | ✓ VERIFIED | `write_count`, stable sort |
| `backend/.../composition/container.py` | In-memory wire | ✓ VERIFIED | `ingest_sources` field |
| `backend/.../composition/live.py` | Supabase wire | ✓ VERIFIED | `SupabaseIngestSourceRepository` |
| `backend/.../interface/http/routes/admin.py` | GET/POST/PATCH/DELETE | ✓ VERIFIED | `require_admin`, top-level errors |
| `backend/.../interface/http/app.py` | CORS DELETE | ✓ VERIFIED | `allow_methods` includes DELETE |
| `web/src/services/ingestSourcesApi.js` | SPA transport | ✓ VERIFIED | mock+live+harness |
| `web/src/components/IngestSourcesSection.jsx` | Full UI section | ✓ VERIFIED | empties, help, rows, busy, YouTube link |
| `web/src/pages/AdminPipelineConfigPage.jsx` | Host + dirty OR | ✓ VERIFIED | section above YAML; single guard |
| `supabase-integration/migrations/012_phase23_ingest_sources.sql` | Idempotent DDL | ✓ VERIFIED | `pipeline_ingest_sources`, RLS, no policy, no wipe |
| `supabase-integration/.../ingest_source_repository.py` | Adapter | ✓ VERIFIED | table-only + PersistenceError |
| `docs/agents/local-platform-runbook.md` | §4i | ✓ VERIFIED | Applied stamp 2026-10-17 |
| `tests/unit/test_http_ingest_sources.py` | HTTP contract | ✓ VERIFIED | reject + PATCH/DELETE |
| `tests/unit/test_phase23_migration_012.py` | Migration text | ✓ VERIFIED | |
| `tests/unit/test_supabase_ingest_source_repository_contract.py` | Adapter contract | ✓ VERIFIED | |
| `tests/unit/test_live_container_wiring.py` | Live type | ✓ VERIFIED | |
| `tests/admin.spec.js` | Playwright journeys | ✓ VERIFIED (exists) | Cases present; not re-executed this pass |

**Artifacts:** all planned paths exist, substantive, wired (gsd `verify.artifacts` 11+5+8+4 = all_passed).

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| AdminPipelineConfigPage | IngestSourcesSection | render above YAML | ✓ WIRED | gsd key-links + source read |
| IngestSourcesSection | ingestSourcesApi | list/add/setEnabled/delete | ✓ WIRED | |
| ingestSourcesApi | admin routes | `/admin/ingest-sources` | ✓ WIRED | |
| admin routes | use_cases → port | list/add/set/delete | ✓ WIRED | |
| container.py | InMemory repo | build_in_memory | ✓ WIRED | |
| live.py | SupabaseIngestSourceRepository | admin_client | ✓ WIRED | |
| use_cases | in_memory write log | zero-write rejects | ✓ WIRED | |
| AdminPipelineConfigPage | useUnsavedChangesGuard | dirty OR | ✓ WIRED | pattern; behavior unrun |
| admin.spec.js | UnsavedChangesDialog copy | dirty leave | ✓ WIRED (test text) | e2e not executed |

**Wiring:** all declared key_links verified by `verify.key-links` (plans 01–04).

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| IngestSourcesSection | `sources` | `listIngestSources()` → GET `/admin/ingest-sources` → repo.list() | Live: Supabase `pipeline_ingest_sources`; mock: sessionStorage | ✓ FLOWING |
| add form | POST body | `addIngestSource` → use_case validate → repo.add | Rejects before write | ✓ FLOWING |
| row toggle/delete | PATCH/DELETE | service → use_case → repo | Hard delete; no soft | ✓ FLOWING |
| Validation UI | `validationErrors` | server 400 `errors` (mock armReject / live) | Structured rows | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Invalid id → 400 + zero writes | `uv run pytest …::test_post_invalid_source_id_returns_400_and_writes_nothing` (+ sibling rejects in same file) | passed (batch 17 incl. wiring) | ✓ PASS |
| PATCH disable + hard DELETE | `…::test_patch_disable_then_delete_hard_removes_row` | passed | ✓ PASS |
| Migration 012 text | `…::test_migration_012_creates_pipeline_ingest_sources_table` | passed | ✓ PASS |
| Live container type | `tests/unit/test_live_container_wiring.py` | passed | ✓ PASS |
| Duplicate + CORS DELETE | `test_post_duplicate…` + `test_cors.py -k delete` | 5 passed | ✓ PASS |
| Adapter contract | `test_supabase_ingest_source_repository_contract.py` | 10 passed | ✓ PASS |
| Live table reachable | Supabase MCP `query pipeline_ingest_sources limit 5` | `[]` | ✓ PASS |
| ADUX-10 Playwright | single named e2e | servers down; not started | ? SKIP → human |

### Probe Execution

| Probe | Command | Result | Status |
| --- | --- | --- | --- |
| — | — | Phase не migration-probe / нет `scripts/*/tests/probe-*.sh` в scope | SKIP |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| SRC-01 | 23-01, 23-02, 23-03, 23-04 | List/add/enable/disable/remove + DB storage | ✓ SATISFIED | HTTP CRUD + UI section + migration 012 + live table |
| SRC-02 | 23-02, 23-04 | Canonical validation + `{errors:[…]}` + id help | ✓ SATISFIED | pytest reject matrix; UI disclosure |
| SRC-03 | 23-01, 23-03 | Port + composition-only Supabase + SPA service | ✓ SATISFIED | architecture grep + live wire test |
| ADUX-10 | 23-01, 23-04 | Guard on ingest-sources editor | ? NEEDS HUMAN | Code wired; e2e behavior not re-proven this pass |

**Orphaned requirements:** none — REQUIREMENTS.md maps SRC-01/02/03 + ADUX-10 only to Phase 23; all appear in PLAN frontmatter.

### Decision Coverage

All trackable CONTEXT.md decisions are honored by shipped artifacts. (`honored: 24 / total: 24`, `not_honored: []`)

### Test Quality Audit

| Test File | Linked Req | Active | Skipped | Circular | Assertion Level | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| `tests/unit/test_http_ingest_sources.py` | SRC-01, SRC-02, SRC-03 | yes | 0 | no | Behavioral (status+body+write_count) | PASS |
| `tests/unit/test_phase23_migration_012.py` | SRC-01 | yes | 0 | no | Value (SQL text) | PASS |
| `tests/unit/test_supabase_ingest_source_repository_contract.py` | SRC-03 | yes | 0 | no | Behavioral (fake client) | PASS |
| `tests/unit/test_live_container_wiring.py` | SRC-03 | yes | 0 | no | Type | PASS |
| `tests/unit/test_cors.py` (DELETE case) | SRC-01 | yes | 0 | no | Value (header) | PASS |
| `tests/admin.spec.js` (ingest / dirty) | SRC-01, SRC-02, ADUX-10 | yes (not skipped) | 0 | no | Behavioral e2e | PASS file / not re-run |

**Disabled tests on requirements:** 0  
**Circular patterns detected:** 0  
**Insufficient assertions:** 0 blockers (Playwright mock is integration proof per D-20; server authority owned by pytest)

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| — | — | TBD/FIXME/XXX in phase impl files | none | — |
| — | — | D-22 banned execution words in section | none | grep clean |
| — | — | Second Save / second guard | none | single dirty OR |
| — | — | supabase in pages/components | none | none |

### Prohibitions (judgment / grep)

| Prohibition | Status | Evidence |
| --- | --- | --- |
| MUST NOT reuse `ingestion_sources` | held | New table `pipeline_ingest_sources` only |
| MUST NOT nest errors under `detail` | held | `JSONResponse(content={"errors":…})` |
| MUST NOT import supabase in domain/use_cases / pages/components | held | grep clean |
| MUST NOT second guard/dialog | held | one hook, one dialog |
| MUST NOT buffered «Сохранить источники» / optimistic inserts | held | immediate add; busyRowId disables |
| MUST NOT soft-delete | held | hard DELETE use case + 204 |
| MUST NOT CREATE POLICY on pipeline_ingest_sources | held | migration text |
| MUST NOT edit 001/011 migration contracts | held | separate `test_phase23_migration_012.py` |

### Human Verification Required

### 1. ADUX-10 dirty OR

**Test:** На `/admin/pipeline` ввести id или label → уйти на «Дайджест»; отдельно сменить только kind; после успешного add (YAML clean) уйти снова.  
**Expected:** Один диалог с Phase-19 копией; kind-only без промпта; после add — без промпта.  
**Why human:** State-transition; e2e не запускались в verify-прогоне.

### 2–4. Backstop layout (overflow / scroll)

**Test:** Длинный список; label 120 символов; раскрытый «Где взять id?» на desktop и узкой ширине.  
**Expected:** Нет горизонтального overflow; YAML достижим.  
**Why human:** `verification: backstop`.

### 5. Ops RLS catalog (optional confirmation)

**Test:** Studio/psql checklist из §4i (`relrowsecurity`, `pg_policies`).  
**Expected:** RLS on, zero policies.  
**Why human:** Table existence confirmed via PostgREST; catalog SQL needs DB URL.

### Gaps Summary

Кодовых gaps по ROADMAP SC 1–3 нет: порт, валидация, миграция, UI-секция и живая таблица подтверждены. Статус `human_needed` из-за (a) не исполненного в этом прогоне ADUX-10 e2e и (b) трёх backstop layout truths. После ручной/Playwright проверки ADUX-10 и визуальных backstop — фаза может перейти в `passed` без code fix (если UI ок).

---

_Verified: 2026-10-17T17:55:00Z_  
_Verifier: Claude (gsd-verifier)_
