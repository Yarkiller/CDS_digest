---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 03
subsystem: ui
tags: [tailwind-v4, design-tokens, wcag, playwright, node-test, tdd, red-green, theme-02, pipeui-02]

requires:
  - phase: 25-01
    provides: "`tests/admin-chrome.spec.js` (gotoAdmin / stylePair / classTokens) собирается проектом `web` через расширенный testMatch"
  - phase: 25-02
    provides: "источники на `/admin/pipeline` уже зелёные в chrome-кейсе; `web/src/index.css` намеренно не тронут — объявление семейства осталось за этим планом"

provides:
  - "`tests/helpers/contrast.js` — единственная реализация WCAG 2.x в репозитории (`parseColor`, `channelLuminance`, `relativeLuminance` (бросает при альфе < 1), `contrastRatio`)"
  - "`tests/unit/test_semantic_token_coverage.js` — гейт критерия 3, проверки G-0…G-8"
  - "тест `select legible in both themes` — computed-пара трёх контролов в обеих темах + рантайм-резолв `--color-paper`"
  - "13 объявленных токенов в `web/src/index.css`: 6 темо-зависимых (объявление + light-override) и 7 тема-независимых (без override)"
  - "три accent-CTA на `bg-accent-solid`/`text-on-solid`, скрайм диалога на `bg-scrim`, две сплошные `bg-paper-2`"

affects: [25-04, phase-26]

actuals:
  tokens: 5920
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Node-гейт по CSS + исходникам как единственная честная форма для «объявлено / переопределено / не переопределено»; computed-style остаётся в Playwright, потому что исходный дефект — ровно разрыв между этими слоями"
    - "`parseBlock` копируется локально из `test_concept2_canon.js` (не экспортируется), канон-файл не редактируется; поэтому G-0 машинно запрещает второй блок — иначе оба гейта ослепли бы одинаково"
    - "WCAG-арифметика живёт в одном CJS-файле вне обоих раннеров (`tests/helpers/`) — `run-unit-js.cjs` перечисляет только `tests/unit/*.js`, Playwright только `*.spec.js`, двойного запуска нет"
    - "`relativeLuminance` бросает при `a < 1`: «контраст на прозрачном фоне» невозможен по конструкции, а не по дисциплине"

key-files:
  created:
    - tests/helpers/contrast.js
    - tests/unit/test_semantic_token_coverage.js
  modified:
    - tests/admin-chrome.spec.js
    - web/src/index.css
    - web/src/components/IngestSourcesSection.jsx
    - web/src/components/UnsavedChangesDialog.jsx
    - web/src/pages/AdminPipelineConfigPage.jsx

key-decisions:
  - "G-0 считает открытия блоков по тексту после вырезания комментариев: в шапке `index.css:4` подстрока `[data-theme=\"light\"]` стоит внутри комментария, поэтому наивный подстрочный счётчик всегда давал бы 2 и не мог позеленеть"
  - "В `select legible` контролы измеряются раньше рантайм-резолва токена: acceptance плана требует, чтобы RED называл измеренную причину (`rgba(0, 0, 0, 0)`), а не только пустую строку `--color-paper`"
  - "Семь тема-независимых токенов пинятся как «объявлен И отсутствует в светлом блоке» (G-3), а осознанные светлые отклонения `rule`/`muted` — как `notEqual` к канону (G-8): иначе позднейший cleanup молча вернул бы 1.23:1 / 4.34:1"
  - "`parseColor` бросает на `%`-каналах и на `var(...)`: ни `index.css`, ни `getComputedStyle` таких строк не дают, а тихая аппроксимация скрыла бы ошибку"
  - "Импорт хелпера в спеке — `./helpers/contrast`, а не `../tests/helpers/contrast` из текста плана: обе формы резолвятся в один файл, но вторая читается так, будто спек лежит вне `tests/`"

patterns-established:
  - "RED-коммит содержит и гейт, и computed-style кейс; GREEN-коммит — только объявления и пять class-строк, поэтому «красное до зелёного» видно в истории по двум SHA"
  - "Гейт, который читает дерево, обязан иметь анти-вакуум: G-4 требует найти все шесть имён семейства, иначе молча опустевшее семейство прошло бы зелёным"

requirements-completed: [THEME-02, PIPEUI-02]

coverage:
  - id: C2-SELECT
    description: "`#ingest-sources-kind`, `#ingest-sources-id`, `#ingest-sources-label` в тёмной теме отдают `rgb(203, 213, 225)` на `rgb(19, 25, 37)`, в светлой — `rgb(51, 65, 85)` на `rgb(255, 255, 255)`; фон непрозрачен, контраст ≥ 4.5; опции ровно `Канал` / `Плейлист`"
    requirement: PIPEUI-02
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#select legible in both themes"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-4 (bg-paper / text-ink-2 / border-rule резолвятся в объявленные токены)"
        status: pass
    human_judgment: false
  - id: C3-GATE
    description: "Гейт покрытия токенов: единственный `@theme` и единственный `[data-theme=\"light\"]`, объявление шести темо-зависимых, light-override с другим значением, отсутствие override у семи плоских, ноль `accent-ink`, ноль `bg-ink` и альфы на `bg-paper*`, контраст 4.5 с floor 4.829, алиасы"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-0…G-8 → npm run test:js 59 pass / 0 fail"
        status: pass
      - kind: unit
        ref: "tests/unit/test_concept2_canon.js (канон 51/13 не изменён, остаётся зелёным)"
        status: pass
    human_judgment: false
  - id: C2-RUNTIME
    description: "`--color-paper` резолвится в рантайме (`getComputedStyle(document.documentElement).getPropertyValue('--color-paper').trim()` непустая) в обеих темах; собранный CSS содержит объявление"
    requirement: THEME-02
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#select legible in both themes (token check per theme)"
        status: pass
      - kind: other
        ref: "npm run build → web/dist/assets/index-*.css: `--color-paper:` ×2 (dark + light), `--color-on-solid:` ×1 (без override)"
        status: pass
    human_judgment: false
  - id: C2-SURFACES
    description: "`bg-paper-2/40` → сплошная `bg-paper-2`; accent-CTA на `bg-accent-solid`+`text-on-solid` в трёх местах; скрайм диалога на `bg-scrim`"
    requirement: THEME-02
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-5, G-6"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js (88 passed) — leave-guard и source journeys не изменились"
        status: pass
    human_judgment: false
  - id: C3-CONFLICT-ERROR
    description: "must_have «при ошибке загрузки … оба ≥ 4.5:1» — не доказан: ветка ошибки не покрыта ни одним тестом, а действие «Повторить загрузку» использует `text-accent` (2.43:1 на белом), который план прямо запрещает трогать (known adjacent defect 3)"
    requirement: THEME-02
    verification:
      - kind: other
        ref: "не измерялось — см. § must_have assessment, строка 12"
        status: fail
    human_judgment: true

metrics:
  duration: 15min
  started: "2026-10-21T12:53:00Z"
  completed: "2026-10-21T13:07:00Z"
  tasks: 2
  files: 7
status: complete
---

# Phase 25 Plan 03: Семейство токенов и читаемый «Тип» Summary

**Шесть темо-зависимых токенов объявлены в `@theme static` с шестью light-override'ами, семь тема-независимых ролей — без override; `#ingest-sources-kind` и оба соседних поля впервые рисуют непрозрачную поверхность `paper` с текстом `ink-2` и контрастом ≥ 4.5 в обеих темах, а гейт G-0…G-8 падает на любом необъявленном токене семейства**

## Performance

- **Duration:** 15 min
- **Started:** 2026-10-21T12:53:00Z
- **Completed:** 2026-10-21T13:07:00Z
- **Tasks:** 2/2
- **Files modified:** 7 (2 созданы, 5 изменены)

## Accomplishments

- `tests/helpers/contrast.js` — единственная WCAG 2.x реализация. `parseColor` принимает `#rgb` / `#rrggbb` / `#rrggbbaa` / `rgb(r, g, b)` / `rgba(r, g, b, a)` / `rgb(r g b / a)` / `transparent` и бросает на `var(...)` и `%`-каналах; `relativeLuminance` бросает при `a < 1`.
- `tests/unit/test_semantic_token_coverage.js` — гейт критерия 3 (G-0…G-8), авто-подхвачен `run-unit-js.cjs` без правки раннера. `test_concept2_canon.js` не тронут.
- `tests/admin-chrome.spec.js` — третий кейс `select legible in both themes`: три контрола × две темы, равенство объявленным `rgb(...)`, непрозрачность, контраст ≥ 4.5, опции `Канал`/`Плейлист`, рантайм-резолв `--color-paper`.
- `web/src/index.css` — **34 добавленные строки, 0 изменённых/удалённых**: семейство `paper`/`paper-2`/`ink`/`ink-2`/`muted`/`rule` + шесть light-override'ов; `primary-solid`/`accent-solid`/`success-solid`/`danger-solid`/`on-solid`/`voting-ink`/`scrim` только в `@theme static`.
- Пять class-строк мигрированы (3 файла, 40 вставок / 6 удалений суммарно): две сплошные `bg-paper-2`, три accent-CTA на `bg-accent-solid` + `text-on-solid`, скрайм на `bg-scrim`.

## Task Commits

1. **Task 1: общий WCAG-хелпер, гейт G-0…G-8 и кейс «select legible» — RED** — `e953d93` (test)
2. **Task 2 (tdd): объявить 13 токенов в существующих блоках и убрать запрещённые шаблоны — GREEN** — `0a7abdc` (feat)

**Plan metadata:** _(docs-коммит этого SUMMARY)_

_Note: RED-артефакты обоих критериев закоммичены до правки CSS, поэтому «красное до зелёного» видно в истории, а не пересказано._

## Доказательство RED → GREEN

| Шаг | Команда | Результат |
|---|---|---|
| RED (task 1, гейт) | `npm run test:js` | exit 1 — **51 pass / 8 fail**; G-1 называет все шесть: `--color-paper, --color-paper-2, --color-ink, --color-ink-2, --color-muted, --color-rule`; G-6 называет `bg-ink` и две `bg-paper-2/40`; G-7 падает на `unsupported colour: undefined` |
| RED (task 1, select) | `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line -g "select legible"` | exit 1 — `ingest-sources-kind (dark) must paint an opaque surface` / `Expected: not "rgba(0, 0, 0, 0)"` |
| GREEN (task 2, гейт) | `npm run test:js` | exit 0 — **59 pass / 0 fail**, канон 51/13 без изменений |
| GREEN (task 2, admin-chrome) | `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` | exit 0 — **3 passed (11.2s)** (`naming`, `chrome`, `select legible`) |
| Волновой гейт | `npx playwright test tests/admin.spec.js --project=web --reporter=line` | exit 0 — **88 passed (4.0m)** |
| Полный suite (дополнительно) | `npm test` | exit 0 — **157 passed (4.5m)** (baseline 156 + новый кейс) |
| Список | `npx playwright test --list --project=web` | exit 0 — **151 tests in 6 files** (baseline 150) |
| Сборка | `npm run build` | exit 0 — `✓ built in 454ms`, CSS 32.04 → **32.93 kB** |

Перед каждым прогоном проверялось отсутствие слушателя на `5174` (и на `8765` перед полным suite) — stale `VITE_USE_MOCKS=false` из STATE.md § Blockers не участвовал.

Самопроверка хелпера (acceptance-критерий плана), выполненная `node -e`:

```
hex3==hex6 true
rgba0 throws  transparent throws  alpha8 throws  var throws
equal-calls true          # contrastRatio('#FFFFFF','#131925') === contrastRatio('rgb(255 255 255 / 1)','rgb(19, 25, 37)')
space-slash {"r":19,"g":25,"b":37,"a":0.6}
pct throws
```

## Files Created/Modified

- `tests/helpers/contrast.js` — **создан**: `parseColor` / `channelLuminance` / `relativeLuminance` / `contrastRatio`, ноль npm-зависимостей.
- `tests/unit/test_semantic_token_coverage.js` — **создан**: локальная копия `parseBlock`, `THEMED` (6), `FLAT` (7), `UTILITY_PREFIXES` (8), рекурсивный скан `web/src`, G-0…G-8.
- `tests/admin-chrome.spec.js` — +46 строк: импорт `contrastRatio` и третий тест; хелперы `gotoAdmin`/`stylePair` переиспользованы, второй копии нет.
- `web/src/index.css` — +34 / −0: две новые группы внутри существующих блоков.
- `web/src/components/IngestSourcesSection.jsx` — ровно 3 строки (`:219`, `:264`, `:308`).
- `web/src/components/UnsavedChangesDialog.jsx` — ровно 2 строки (`:26`, `:53`).
- `web/src/pages/AdminPipelineConfigPage.jsx` — ровно 1 строка (`:305`).

## Decisions Made

- **G-0 считает блоки после вырезания комментариев.** `index.css:4` содержит `[data-theme="light"]` внутри файлового комментария; наивный счётчик всегда давал 2. Гейт падает с сообщением, что `parseBlock` читает только первое вхождение.
- **Порядок ассертов в `select legible`.** Сначала контролы, потом рантайм-токен: иначе RED называл бы только `--color-paper === ""`, а acceptance требует измеримую причину `rgba(0, 0, 0, 0)`.
- **Семь плоских токенов пинятся как отсутствие override (G-3), светлые отклонения `rule`/`muted` — как `notEqual` (G-8).** Отклонения осознанные (UI-SPEC § Boundary legibility / § Token contract A), и без явного пина позднейший «cleanup» вернул бы 1.23:1 и 4.34:1.
- **`parseColor` не поддерживает `%`-каналы и `var(...)`.** Ни `index.css`, ни `getComputedStyle` их не дают, а тихая аппроксимация скрыла бы ошибку парсера.
- **Дополнительно прогнан полный `npm test`** (вне `<verify>` плана) — объявления в `index.css` глобальны, поэтому волновая страховка дешевле повторного разбора регрессий.

## Deviations from Plan

### Auto-fixed Issues

None.

### Process notes (не отклонения от результата)

1. **Импорт хелпера — `./helpers/contrast`.** План пишет `../tests/helpers/contrast`; из `tests/admin-chrome.spec.js` обе формы резолвятся в один и тот же файл, но первая — обычная для файла в `tests/`. Поведение и путь артефакта не изменились.
2. **`npm run test:js` прогонялся трижды** (RED, GREEN и внутри полного прогона) — это наблюдение, не правка.
3. **`npm run build` не оставил оболочку в `web/`** (проверено `git rev-parse --show-toplevel` перед коммитом); коммиты `e953d93` / `0a7abdc` сделаны из корня репозитория.
4. **`full-suite.log`** — временный файл вывода полного прогона, удалён после чтения; в дерево не попал.

## Issues Encountered

- Ни одного технического блокера. Единственный шум — предсуществующие `NO_COLOR` / `React DevTools hook` предупреждения в выводе Playwright и предсуществующие `INEFFECTIVE_DYNAMIC_IMPORT` / chunk-size предупреждения сборки.
- Первый прогон `-g "select legible"` упал на рантайм-токене, а не на измеренной паре; ассерты переставлены внутри того же таска до коммита, чтобы RED соответствовал acceptance-критерию.

## must_have assessment

| # | must_have | Доказательство | Статус |
|---|---|---|---|
| 1 | Гейт критерия 3 зелёный (резолв утилит, override у темо-зависимых, отсутствие у плоских) | G-0…G-8 | proven |
| 2 | Ровно один `@theme` и один `[data-theme="light"]` | G-0 | proven |
| 3 | `#ingest-sources-kind`: пара + непрозрачный фон + ≥ 4.5 в обеих темах | `select legible in both themes` | proven |
| 4 | Соседние `-id` / `-label` отдают ту же пару | тот же кейс, цикл по трём локаторам | proven |
| 5 | Опции ровно `Канал` / `Плейлист` | тот же кейс | proven |
| 6 | `--color-paper` резолвится в рантайме | тот же кейс + собранный CSS (`×2`) | proven |
| 7 | Ноль `accent-ink`, ноль `bg-ink`, ноль альфы на `bg-paper*` | G-5, G-6 | proven |
| 8 | Контраст семейства 4.5, floor `on-solid`/`danger-solid` ≥ 4.829 | G-7 | proven |
| 9 | Алиасы `paper`/`paper-2`/`ink` обе темы; `rule`/`muted` — только тёмная | G-8 (+ `notEqual` на светлые отклонения) | proven |
| 10 | Пустые три контрола: заливка `paper`, значение `ink-2`, **край `rule`** | заливка и текст — `select legible`; край — статически G-4 (`border-rule` → объявленный `--color-rule`), computed `border-color` планом не ассертится | partial (край только статически) |
| 11 | Ноль источников: заголовок «Источники» + «Пока нет источников» на `paper`, `ink`/`muted` | `tests/admin.spec.js:1834`, `:1844-1845` (88 passed) + G-4 для поверхностей | proven (текст — существующими тестами) |
| 12 | Ошибка загрузки: «Не удалось загрузить источники» + «Повторить загрузку» **оба ≥ 4.5:1** | теста нет; текст `text-ink-2` прошёл бы (11.85 / 10.35), но действие — `text-accent` = 2.43:1 на белом, и план прямо запрещает его трогать (§ Known adjacent defects 3) | **NOT PROVEN — противоречие внутри плана/UI-SPEC** |
| 13-19 | backstop'ы: частично заполненная форма, 200-символьный id, первичная загрузка, строка только с id, 20 строк, ритм 0/1/20, длинный id, 320px диалог | отдельным прогоном не измерялись — по контракту `verification: backstop` верификатор абстенится (`human_needed`) | backstop |

## Known Stubs

Нет. Ни один ассерт не заглушен; все три кейса спека исполняются на реальном дереве, гейт сканирует реальные файлы.

## Threat Flags

Нет новой поверхности. T-25-02 закрыт G-0 (второй блок запрещён машинно) при статических CSS-идентификаторах; T-25-03 закрыт `bg-scrim` + G-6 (ни `bg-ink`, ни альфы на `bg-paper*`); T-25-09 закрыт G-7 с floor 4.829; T-25-04 — кейс добавлен в уже собираемый файл, `--list` показывает 151 тест в 6 файлах.

## User Setup Required

None.

## Next Phase Readiness

- **25-04 применяет объявленные роли.** Сейчас потребителей имеют `bg-accent-solid` (3), `text-on-solid` (3), `bg-paper-2` (2), `bg-scrim` (1); `bg-primary-solid`, `bg-success-solid`, `bg-danger-solid`, `text-voting-ink` объявлены и **пока не используются** — это ожидаемо до 25-04, а не мёртвые токены (их отсутствие запрещено только для `accent-ink`, D-10).
- **25-04 обязан не сломать G-6/G-5:** три скрайма `AdminDigestPage.jsx:821/:885/:948` пока несут `bg-text-primary/40` — G-6 их не ловит (это не `bg-ink`), но по UI-SPEC § Same-root-cause addendum они переезжают на `bg-scrim` в 25-04. Любая оставшаяся `*-accent-ink` утилита немедленно валит G-5.
- **Принятые визуальные следствия уже наступили:** `border-rule` стал нарисованным (`#2A3548` / `#CBD5E1`), `MaterialPage.jsx:187` — нарисованным callout'ом, `MaterialPage` не редактировался. Это зафиксировано в UI-SPEC § Boundary legibility / § Reader-surface delta, «возвращать как было» запрещено.
- **Пять `toHaveClass(/bg-primary/)`** в `tests/admin.spec.js` (`:186`, `:198`, `:216`, `:299`, `:312`) по-прежнему ждут 25-04; ни один не изменён — поэтому `bg-primary-solid` пока не появляется ни в одном assert'е.
- **must_have #12 требует решения планировщика:** либо ветка ошибки получает тест и тему-независимое действие, либо формулировка must_have уточняется (сейчас она противоречит § Known adjacent defects 3, который запрещает трогать `text-accent`).

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- Все семь заявленных путей существуют и изменены в указанных объёмах (`index.css` +34/−0; компоненты 3/3, 2/2, 1/1).
- Оба коммита (`e953d93`, `0a7abdc`) найдены в истории.
- `npm run test:js` = 59 pass / 0 fail; `admin-chrome.spec.js` = 3 passed; `admin.spec.js` = 88 passed; `npm test` = 157 passed; `--list --project=web` = 151 тест / 6 файлов; `npm run build` exit 0.
