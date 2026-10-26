---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 01
subsystem: ui
tags: [playwright, admin, naming, tdd, adminlayout, testmatch, red-green]

requires: []

provides:
  - "playwright `testMatch` web-проекта собирает `admin(-chrome).spec.js` — 149 тестов в 6 файлах"
  - "`tests/admin-chrome.spec.js`: `THEME_KEY`, `gotoAdmin`, `resetIngestSourcesMock`, `stylePair`, `classTokens` — дом для критериев 1, 2, 4, 5"
  - "«Настройка» на трёх поверхностях `AdminLayout.jsx` (sr-only h1, вкладка, мобильный `<option>`) при неизменном `/admin/pipeline`"

affects: [25-02, 25-03, 25-04, phase-26]

actuals:
  tokens: 2483
  tasks: 2
  commits: 3

tech-stack:
  added: []
  patterns:
    - "`tests/admin-chrome.spec.js` — отдельный спек для приёмочных проверок админ-хрома (двойной прогон тем, computed style), хелперы модульные, стиль Playwright-конвенции репозитория"
    - "Роль и тема ставятся одним `addInitScript` до загрузки; тёмная тема — явный `removeItem`, а не дефолт"
    - "Reset ингест-стора внутри `gotoAdmin` для любого пути `/admin/pipeline` (Shared Pattern 1), а не в отдельных кейсах"

key-files:
  created:
    - tests/admin-chrome.spec.js
  modified:
    - playwright.config.js
    - tests/admin.spec.js
    - web/src/components/AdminLayout.jsx

key-decisions:
  - "Трассирующий срез сдан как TDD-пара: спек и конфиг коммитятся красными (RED), амендмент `admin.spec.js` — отдельный RED-коммит, переименование — GREEN-коммит; так «красное до зелёного» видно в истории"
  - "`gotoAdmin` сбрасывает `__DIGEST_ADMIN_HARNESS__`, затем ингест-стор, затем `document.fonts.ready` — порядок обязателен: ингест-стор живёт в отдельном харнессе и без него `ingest-sources-kind` приходит из предыдущего кейса"
  - "`stylePair`/`classTokens` объявлены в этом плане, но используются только планами 02/04; они часть контракта файла, а не мёртвый код"
  - "Заголовки и комментарии `admin.spec.js:164`, `:439`, `:461` с литералом «Пайплайн» оставлены как есть — план перечисляет ровно шесть точек, а оба негативных ассерта по решению остаются `/пайплайн/i`"

patterns-established:
  - "Красный спек коммитится отдельным `test(25-01)` коммитом до правки production-файла — история доказывает RED, а не пересказывает его"
  - "Одна регексп-правка `testMatch` вместо нового проекта: `admin-chrome` въезжает в существующий web-проект без второго webServer"

requirements-completed: [PIPEUI-01]

coverage:
  - id: D1
    description: "На `/admin/pipeline` вкладка раздела, sr-only h1 и мобильный `<option>` читаются «Настройка», соседняя вкладка — «Дайджест», URL остаётся `/admin/pipeline`, `data-testid` и `aria-label` не изменены"
    requirement: PIPEUI-01
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#naming: the section reads Настройка on all three surfaces and the URL is unchanged"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js:139#admin-section nav lists Дайджест then Настройка and marks digest active"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js:252#admin surfaces expose exactly one visually hidden h1 (IN-01, D-06)"
        status: pass
    human_judgment: false
  - id: D2
    description: "`tests/admin-chrome.spec.js` физически собирается проектом `web` — без этого критерии 2, 4, 5 фазы не имеют RED"
    requirement: PIPEUI-01
    verification:
      - kind: other
        ref: "npx playwright test --list --project=web → 149 tests in 6 files, admin-chrome.spec.js назван"
        status: pass
    human_judgment: false

metrics:
  duration: 11min
  started: "2026-10-21T12:19:00Z"
  completed: "2026-10-21T12:30:00Z"
  tasks: 2
  files: 4
status: complete
---

# Phase 25 Plan 01: Трассирующий срез `admin-chrome` + «Настройка» на трёх поверхностях Summary

**`tests/admin-chrome.spec.js` собран web-проектом Playwright и пинит «Настройка» на вкладке, sr-only `h1` и мобильном `<option>` при неизменном `/admin/pipeline`, доказав RED до GREEN**

## Performance

- **Duration:** 11 min
- **Started:** 2026-10-21T12:19:00Z
- **Completed:** 2026-10-21T12:30:00Z
- **Tasks:** 2/2
- **Files modified:** 4 (1 создан, 3 изменены)

## Accomplishments

- `playwright.config.js` web-проект теперь матчит `admin(-chrome)?.spec.js` — раннер видит новый файл (`--list`: **149 tests in 6 files**, до правки было 148 в 5).
- `tests/admin-chrome.spec.js` создан с модульными хелперами `THEME_KEY`, `gotoAdmin(page, path, theme)`, `resetIngestSourcesMock(page)`, `stylePair(locator)`, `classTokens(locator)` и одним тестом `naming:` из восьми утверждений.
- Три литерала в `AdminLayout.jsx` читаются «Настройка»; маршрут, `PIPELINE_PATH`/`DIGEST_PATH`, `handleSectionTabClick`, `aria-label` и все `data-testid` не тронуты (diff — ровно 3 строки, 0 удалений).
- `tests/admin.spec.js` аменднут в шести местах (7 строк), включая guard «shell не владеет ссылкой» и sr-only `h1`; негативные `/пайплайн/i` и «Конфиг пайплайна» оставлены байт-идентичными.

## Task Commits

1. **Task 1 (tracer): собрать `admin-chrome.spec.js` в проекте `web` и запинить три поверхности — RED** — `42d4374` (test)
2. **Task 2 (tdd): амендмент ожиданий в `admin.spec.js` — RED** — `2c8c040` (test)
3. **Task 2 (tdd): переименовать три литерала в `AdminLayout.jsx` — GREEN** — `456e3e9` (feat)

**Plan metadata:** _(docs-коммит этого SUMMARY)_

_Note: TDD-таск разделён на два коммита, чтобы RED был виден в истории до production-правки._

## Доказательство RED → GREEN

| Шаг | Команда | Результат |
|---|---|---|
| RED (task 1) | `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line -g "naming"` | exit 1 — `Expected: "Настройка" / Received: "Пайплайн"` на `getByTestId('admin-tab-pipeline')` |
| RED (task 2) | `npx playwright test tests/admin.spec.js --project=web --reporter=line -g "admin-section nav lists"` | exit 1 — `Expected: "Настройка" / Received: "Пайплайн"` на `sectionLinks.nth(1)` |
| GREEN | `npx playwright test tests/admin-chrome.spec.js tests/admin.spec.js --project=web --reporter=line -g "naming\|admin-section nav lists"` | exit 0 — **2 passed (5.3s)** |
| Волновой гейт | `npx playwright test tests/admin-chrome.spec.js tests/admin.spec.js --project=web --reporter=line` | exit 0 — **89 passed (3.9m)** |
| Список | `npx playwright test --list --project=web` | exit 0 — **149 tests in 6 files**, `admin-chrome.spec.js:75:1` назван |
| JS-юниты | `npm run test:js` | exit 0 — **50 pass / 0 fail** |
| Сборка | `npm run build` | exit 0 — `✓ built in 440ms` (только предсуществующие предупреждения о chunk size / INEFFECTIVE_DYNAMIC_IMPORT) |

Перед каждым прогоном проверялось отсутствие слушателя на `127.0.0.1:5174` (`Get-NetTCPConnection -LocalPort 5174 -State Listen` → пусто), т.е. stale `VITE_USE_MOCKS=false` из STATE.md § Blockers не участвовал.

## Files Created/Modified

- `tests/admin-chrome.spec.js` — **создан**: роль+тема через один `addInitScript`, reset админского и ингест-харнессов, `document.fonts.ready`, тест `naming:` с восьмью утверждениями.
- `playwright.config.js` — одна строка: `testMatch` web-проекта → `/(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/`. `baseURL`, `webServer.*`, `reuseExistingServer`, проект `design-frontend` байт-идентичны.
- `tests/admin.spec.js` — 7 строк в шести точках (`:139`, `:151`, `:165`, `:274`, `:1754`, `:1759`, `:1764`).
- `web/src/components/AdminLayout.jsx` — строки `:49`, `:70`, `:83`: только текст, три замены без удалений.

## Decisions Made

- **Трассирующий гейт исполнен как TDD-пара, а не как `checkpoint:human-verify`.** `<verify>` трассирующего таска по определению требует *красного* результата (`fails_when exit 0`), поэтому «проверить рабочий срез у человека» здесь означало бы проверить сломанное состояние. Вместо остановки гейт прогнан дважды: RED зафиксирован выводом, GREEN — тем же прогоном после правки компонента; оба коммита лежат в истории.
- **Два коммита внутри TDD-таска** (`test` → `feat`), чтобы RED не растворился в одном diff.
- **`stylePair`/`classTokens` объявлены сразу, хотя naming-тест их не вызывает.** Это контракт файла, зафиксированный в артефактах фазы; планы 02/04 дописывают кейсы, а не инфраструктуру.
- **Комментарии `admin.spec.js:164`, `:439`, `:461` с литералом «Пайплайн» не тронуты.** План перечисляет ровно шесть точек амендмента, а оба негативных ассерта осознанно остаются `/пайплайн/i` (они скоупятся на тело дайджеста и продолжают ловить banned-copy). Строки остаются фактически верными по смыслу («shell не владеет этой ссылкой», «в теле страницы дайджеста этой строки нет»), но упоминают старое имя — это осознанный остаток, не дрейф.

## Deviations from Plan

None — план исполнен как написано. Единственное отличие в процессе: `playwright test --list` выполнен до правки конфига (для базовой линии 148/5) — это не меняет ни одного файла.

## Issues Encountered

- Ни одного технического блокера: Vite на 5174 поднимался Playwright'ом с `VITE_USE_MOCKS=true`, stale-слушателей не было, полный `admin.spec.js` прошёл с первого раза (89 passed).
- Разовые предупреждения `NO_COLOR`/`React DevTools hook` в выводе Playwright — предсуществующие и безвредные.

## Known Stubs

Нет. Ни один проверяемый ассерт не заглушен, все восемь утверждений `naming:` исполняются на реальном дереве.

## Threat Flags

Нет новой поверхности. T-25-01 закрыт ассертами `page.url()` + `aria-label` + `toHaveCount(1)` при нулевых правках wiring; T-25-04 закрыт видимым именем файла в `--list`; T-25-05 — предполётной проверкой порта 5174.

## User Setup Required

None — внешней конфигурации не требуется.

## Next Phase Readiness

- Волна 1 следующего плана (`25-02`) может опираться на `admin-chrome.spec.js` как на готовый дом: хелперы тем/стилей/токенов уже здесь, `testMatch` их собирает.
- `AdminLayout.jsx` получил только тексты; класс-строки (`text-3xl`, `gap-2`, `mt-2`, eyebrow, `<select>`-классы) остались нетронутыми намеренно — иначе `chrome:`-RED плана 02 нельзя было бы отличить от naming-RED.
- Пять `toHaveClass(/bg-primary/)` в `admin.spec.js` (`:186`, `:198`, `:216`, `:299`, `:312`) по-прежнему ждут плана 04; ни один из них этим планом не изменён.

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- Все пять заявленных путей существуют (4 файла кода/тестов + этот SUMMARY).
- Все три коммита (`42d4374`, `2c8c040`, `456e3e9`) найдены в истории.
- `--list --project=web` = 149 тестов в 6 файлах; волновой гейт 89 passed; `npm run test:js` 50 pass; `npm run build` exit 0.
