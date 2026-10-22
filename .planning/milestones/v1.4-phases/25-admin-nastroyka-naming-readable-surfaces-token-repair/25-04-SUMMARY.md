---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
plan: 04
subsystem: ui
tags: [tailwind-v4, design-tokens, wcag, playwright, node-test, tdd, red-green, theme-01]

requires:
  - phase: 25-03
    provides: "13 declared tokens in `web/src/index.css` — `primary-solid`/`success-solid`/`danger-solid`/`on-solid`/`voting-ink`/`scrim` existed but had zero consumers; `tests/helpers/contrast.js` + G-0…G-8"

provides:
  - "`tests/unit/test_semantic_token_coverage.js` — `FILL_TOKENS`, `THEME_DEPENDENT_LABELS`, `VEIL_TOKENS` + token-exact scanners; G-9 (label on a fill) and G-10 (theme-dependent veil)"
  - "`tests/admin-chrome.spec.js` — fourth case `theme-independent labels in both themes` (criterion 4, three pairs × two themes, `voting` pinned positively)"
  - "token-exact pill assertions at five sites of `tests/admin.spec.js` (four positive, one negative)"
  - "`bg-primary-solid` + `text-on-solid` on the active shell pill, all `ActionButton` states, the retry splash and five page CTAs"
  - "`bg-scrim` on all four full-screen overlays (dialog was migrated in 25-03, three here)"
  - "zero consumers left for the theme-dependent label / veil classes: G-9 and G-10 report empty offender lists"

affects: [phase-26, phase-27]

actuals:
  tokens: 4771
  tasks: 3
  commits: 3

tech-stack:
  added: []
  patterns:
    - "Class-string extraction by a string-literal scanner (`'`/`\"`/backtick, newline-terminated for quotes), then `split(/\\s+/)` — token equality is the only shape that cannot read `bg-primary-solid` as `bg-primary`"
    - "Variant prefixes stripped before comparison (`hover:bg-primary` -> `bg-primary`), opacity suffixes kept (`bg-primary/15` stays a tint, not a fill — D-12)"
    - "A whole-tree gate is added and closed inside one plan (RED in task 1, green in task 3) so a plan never ends with a red gate it created"
    - "The recorded ROADMAP exception (`voting`) is asserted **positively** (dark label on yellow), never skipped — a wrong white label must fail"

key-files:
  created: []
  modified:
    - tests/unit/test_semantic_token_coverage.js
    - tests/admin-chrome.spec.js
    - tests/admin.spec.js
    - web/src/components/AppShell.jsx
    - web/src/components/ActionButton.jsx
    - web/src/components/ServiceUnavailable.jsx
    - web/src/pages/LoginPage.jsx
    - web/src/pages/RegisterPage.jsx
    - web/src/pages/KnowledgePage.jsx
    - web/src/pages/AdminDigestPage.jsx

key-decisions:
  - "G-9/G-10 read string literals, not raw source: a class list can only live in a literal (`className` value or a `stateClass`/`variantClass`/`linkClass` array element), so the scan is complete and cannot be fooled by prose in comments or JSX text"
  - "Five pill assertions became `(await el.getAttribute('class')).split(/\\s+/)` + `toContain('bg-primary-solid')` then `not.toContain('bg-primary')`; the content-bearing positive goes first so the RED message reads «нет bg-primary-solid», not «есть bg-primary»"
  - "`voting` is a positive assertion of the recorded exception: `rgb(15, 23, 42)` on `rgb(234, 179, 8)` = 9.31 in both themes; white on `#EAB308` (1.92) provably fails the same row"
  - "Only the `isActive` branch of `linkClass` was edited — `bg-bg-app` / `text-text-primary` / `border-border` stay on the shell root because `test_concept2_canon.js` pins them (T-25-11)"

patterns-established:
  - "A whole-tree gate lands with its RED commit and is closed by the last migration commit of the same plan; splitting it would leave a deliberately red plan boundary"
  - "Every `-solid` claim is asserted twice: exact computed `color`/`background` strings (theme-independent by construction) and a ratio from the single WCAG helper"

requirements-completed: [THEME-01]

coverage:
  - id: C4-PILL
    description: "Активная навигационная пилюля shell в обеих темах: `rgb(255, 255, 255)` на `rgb(124, 58, 237)`, ratio 5.70, токен-набор содержит `bg-primary-solid` и не содержит `bg-primary`"
    requirement: THEME-01
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#theme-independent labels in both themes (pill × dark/light)"
        status: pass
      - kind: e2e
        ref: "tests/admin.spec.js#shell Админ pill exposes aria-current on every admin path (WR-02, IN-04) — 5 token-exact sites"
        status: pass
    human_judgment: false
  - id: C4-ACCENT
    description: "Accent-CTA `ingest-sources-add`: `rgb(255, 255, 255)` на `rgb(14, 116, 144)`, ratio 5.36 в обеих темах — держит миграцию 25-03 от отката"
    requirement: THEME-01
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#theme-independent labels in both themes (add CTA × dark/light)"
        status: pass
    human_judgment: false
  - id: C4-VOTING
    description: "Жёлтая `voting` несёт постоянную тёмную подпись `rgb(15, 23, 42)` на `rgb(234, 179, 8)`, ratio 9.31 в обеих темах; белая подпись (1.92) провалила бы ту же строку"
    requirement: THEME-01
    verification:
      - kind: e2e
        ref: "tests/admin-chrome.spec.js#theme-independent labels in both themes (/voting fixture → confirm-vote)"
        status: pass
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-7 (voting-ink on voting ≥ 4.5)"
        status: pass
    human_judgment: false
  - id: C4-GATE-9
    description: "G-9: ни одна class-строка под `web/src` не несёт одновременно заливку (`bg-primary`/`bg-accent`/`bg-success`/`bg-danger`/`bg-voting`) и темо-зависимую подпись (`text-text-primary`/`text-accent-ink`/`text-bg-app`)"
    requirement: THEME-01
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-9 → npm run test:js (14 offenders RED → 0 GREEN)"
        status: pass
    human_judgment: false
  - id: C4-GATE-10
    description: "G-10: ноль `bg-ink` и ноль `bg-text-primary/<opacity>` под `web/src`; четыре оверлея на `bg-scrim`, `bg-text-primary` без альфы (toast, known defect 1) законен"
    requirement: THEME-01
    verification:
      - kind: unit
        ref: "tests/unit/test_semantic_token_coverage.js#G-10 → 3 offenders RED (AdminDigestPage :821/:885/:948) → 0 GREEN"
        status: pass
    human_judgment: false
  - id: C4-ASSERTS
    description: "Пилюльные ассерты больше не держатся на подстроке: пять сайтов токен-точные, `toHaveClass(/bg-primary/)` в `tests/admin.spec.js` отсутствует (rg → пусто)"
    requirement: THEME-01
    verification:
      - kind: other
        ref: "rg -n --fixed-strings 'toHaveClass(/bg-primary/)' tests/admin.spec.js → exit 1, пустой вывод"
        status: pass
      - kind: e2e
        ref: "RED-прогон -g \"WR-02\" упал ровно один раз на позитивном сайте: Expected [ … ] to contain \"bg-primary-solid\""
        status: pass
    human_judgment: false
  - id: C4-LOADING
    description: "must_have «пока действие в полёте, подпись сохраняет цвет и меняется только прозрачность» — доказано статически: `stateClass.loading` = `cursor-wait opacity-80`, ни одного цветового токена; `stateClass` собирается после `variantClass` без цветовых переопределений"
    requirement: THEME-01
    verification:
      - kind: other
        ref: "web/src/components/ActionButton.jsx:3, :26-34 — reading, не прогон; e2e цвета в loading-состоянии не измеряет"
        status: pass
    human_judgment: true
  - id: C4-BACKSTOP-320
    description: "backstop'ы 320px: перенос «Уйти без сохранения» внутри 44px и полная подпись пилюли на `primary-solid` без обрезки — отдельным прогоном не измерялись"
    requirement: THEME-01
    verification:
      - kind: other
        ref: "не измерялось — по контракту `verification: backstop` верификатор абстенится (human_needed); `min-h-11` и структура пилюли не менялись"
        status: pass
    human_judgment: true

metrics:
  duration: 17min
  started: "2026-10-21T13:14:00Z"
  completed: "2026-10-21T13:31:00Z"
  tasks: 3
  files: 10
status: complete
---

# Phase 25 Plan 04: Тема-независимые подписи на заливках Summary

**Все заполненные поверхности под `web/src` несут постоянную подпись — белая на фиолетовой, циановой, зелёной и красной заливках, тёмная на жёлтой `voting`, — а четыре полноэкранных оверлея затемняют сцену одинаково в обеих темах; G-9/G-10 падают на 14+3 реальных сайтах и зеленеют только после миграции**

## Performance

- **Duration:** 17 min
- **Started:** 2026-10-21T13:14:00Z
- **Completed:** 2026-10-21T13:31:00Z
- **Tasks:** 3/3
- **Files modified:** 10 (0 создано, 10 изменены)

## Accomplishments

- `tests/unit/test_semantic_token_coverage.js` получил три константы (`FILL_TOKENS`, `THEME_DEPENDENT_LABELS`, `VEIL_TOKENS`), сканер строковых литералов и два whole-tree гейта. **RED измерим:** G-9 назвал **14** class-строк в 7 файлах (`AppShell`, `ActionButton` ×4, `ServiceUnavailable`, `LoginPage` ×2, `RegisterPage` ×2, `KnowledgePage`, `AdminDigestPage` ×2), G-10 — **3** скрайма `AdminDigestPage`.
- `tests/admin-chrome.spec.js` — четвёртый кейс `theme-independent labels in both themes`: три пары × две темы, включая **положительный** ассерт `voting`. Хелперы `gotoAdmin`/`stylePair`/`classTokens` переиспользованы, второй копии нет.
- `tests/admin.spec.js` — пять пилюльных ассертов переведены на токен-точную пару. RED критерия 4 измерен: `-g "WR-02"` упал ровно на позитивном сайте (`Expected [ … ] to contain "bg-primary-solid"`), негативный сайт на `/` остался зелёным, весь файл до амендмента был зелёным целиком.
- Семь мигрированных подписей: активная пилюля shell (`bg-primary-solid` + `text-on-solid`), четыре состояния `ActionButton` (`danger-solid`/`success-solid`/`voting`+`voting-ink`/`primary-solid`), CTA повтора в `ServiceUnavailable`, две CTA `LoginPage`, две `RegisterPage`, выбранный чип роли `KnowledgePage`, две кнопки отправки `AdminDigestPage`.
- Три скрайма `AdminDigestPage` (`:821`, `:885`, `:948`) переехали с `bg-text-primary/40` на `bg-scrim`; `data-testid`/`role`/`aria-*` и поведение диалогов (Esc = остаться, без focus-trap) не тронуты.

## Task Commits

1. **Task 1: G-9/G-10, кейс критерия 4 и пять токен-точных пилюльных ассертов — RED** — `a907985` (test)
2. **Task 2 (tdd): пилюля shell, `ActionButton` и error-splash на `-solid`-роли — GREEN, часть 1** — `d25483e` (feat)
3. **Task 3 (tdd): CTA страниц и три скрайма `AdminDigestPage` — GREEN, часть 2** — `cae4342` (feat)

**Plan metadata:** _(docs-коммит этого SUMMARY)_

_Note: обе GREEN-половины — таски с `tdd="true"`, но их RED по плану живёт в task 1 (это один критерий 4 плюс его гейты). История поэтому читается как один RED-коммит и две GREEN-половины, а не как три пары._

## Доказательство RED → GREEN

| Шаг | Команда | Результат |
|---|---|---|
| RED (G-9/G-10) | `npm run test:js` | exit 1 — **59 pass / 2 fail**; G-9: 14 offender'ов в 7 ожидаемых файлах; G-10: `AdminDigestPage.jsx: bg-text-primary/40` ×3 |
| RED (критерий 4) | `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line -g "theme-independent labels"` | exit 1 — `pill (dark) color: Expected "rgb(255, 255, 255)" / Received "rgb(241, 245, 249)"` (3.87:1 на `#8B5CF6`) |
| RED (ассерты) | `npx playwright test tests/admin.spec.js --project=web --reporter=line -g "WR-02"` | exit 1 — ровно **одно** падение на позитивном сайте: `toContain("bg-primary-solid")`, получены токены `… "bg-primary", "text-text-primary"` |
| GREEN 1 | тот же `-g "theme-independent labels"` после task 2 | exit 0 — **1 passed (7.0s)** |
| GREEN 1 (гейт) | `npm run test:js` | exit 1 — G-9 сузился до **4 страниц** (7 offender'ов): `AppShell`/`ActionButton`/`ServiceUnavailable` исчезли, канон 51/13 зелёный |
| GREEN 1 (ассерты) | `npx playwright test tests/admin.spec.js --project=web -g "WR-02"` | exit 0 — **1 passed (6.3s)**, все пять сайтов зелёные |
| GREEN 2 (гейт) | `npm run test:js` | exit 0 — **61 pass / 0 fail**, G-9 и G-10 с пустыми списками, канон 51/13 не изменился |
| GREEN 2 (спека) | `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` | exit 0 — **4 passed (17.0s)** (`naming`, `chrome`, `select legible`, `theme-independent labels`) |
| Волновой гейт | `npx playwright test tests/admin.spec.js --project=web --reporter=line` | exit 0 — **88 passed (4.0m)** |
| Полный web-проект | `npm run test:web` | exit 0 — **152 passed (4.6m)** |
| Список | `npx playwright test --list --project=web` | exit 0 — **152 tests in 6 files** (baseline 151) |
| Сборка | `npm run build` | exit 0 — `✓ built in 416ms`, CSS 32.93 → **32.83 kB** (три `bg-text-primary/40` ушли, `bg-scrim` один) |

Перед каждым прогоном проверялось отсутствие слушателя на `5174` (`Get-NetTCPConnection -LocalPort 5174 -State Listen` → пусто), т.е. stale `VITE_USE_MOCKS=false` из STATE.md § Blockers не участвовал.

## Files Created/Modified

- `tests/unit/test_semantic_token_coverage.js` — **+99 строк**: `FILL_TOKENS`, `THEME_DEPENDENT_LABELS`, `VEIL_TOKENS`, `stringLiterals()` (сканер литералов), `baseToken()` (снятие variant-префикса), `tokenSet()`, G-9, G-10. `parseBlock` и G-0…G-8 не тронуты.
- `tests/admin-chrome.spec.js` — **+58 строк**: четвёртый тест; хелперы не дублированы.
- `tests/admin.spec.js` — **26 строк в пяти точках**: `:186`, `:198`, `:216`, `:299`, `:312` (номера после правки сместились). Ни один другой ассерт не тронут — негативные `/пайплайн/i` и «Конфиг пайплайна» байт-идентичны.
- `web/src/components/AppShell.jsx` — **1 строка** (`:14`, ветка `isActive`); `text-text-primary` остался на корневом `<div>` (`:66`).
- `web/src/components/ActionButton.jsx` — **4 строки** (`:4`, `:5`, `:18`, `:21`); `secondary`-ветка отсутствует в диффе.
- `web/src/components/ServiceUnavailable.jsx` — **1 строка** (`:38`).
- `web/src/pages/{Login,Register}Page.jsx` — по **2 строки**; `KnowledgePage.jsx` — **1 строка**; `AdminDigestPage.jsx` — **5 строк** (2 CTA + 3 скрайма).

## Decisions Made

- **Класс-строка извлекается сканером литералов, а не грепом по подстроке.** `bg-primary-solid` — подстрока `bg-primary`, поэтому G-9 обязан сравнивать токены. Сканер видит `'`/`"`/`` ` `` и обрывает литерал на переводе строки (кроме шаблонных), чтобы апостроф в прозе не «съел» файл. Комментарии и JSX-текст в литералы не попадают — в отличие от грепа, гейт не считает прозу за код.
- **Variant-префиксы снимаются, opacity-суффиксы сохраняются.** `hover:bg-primary` считается заливкой, а `bg-primary/15` — тинтом (D-12: тинт-чипы не мигрируются), иначе `EditorialCallout`/`IssueToc` попали бы в область этого плана.
- **`bg-text-primary` без альфы законен.** Toast `AdminDigestPage.jsx:808` — известный соседний дефект 1 (тот же цвет у текста и заливки), не оверлей; G-10 запрещает только вуаль-форму `/<opacity>`, иначе гейт требовал бы правки вне фазы.
- **Позитив идёт первым в пилюльной паре.** `toContain("bg-primary-solid")` перед `not.toContain("bg-primary")`: RED должен читаться «нет `-solid`-заливки», а не «остался базовый класс». Второй ассерт всё равно обязателен — `:299` без него перестал бы ловить блудный базовый класс.

## Deviations from Plan

### Auto-fixed Issues

None.

### Process notes (не отклонения от результата)

1. **Один RED-коммит на два `tdd="true"`-таска.** Плана структура: task 1 несёт RED обоих критериев (гейты + кейс 4 + амендменты), tasks 2-3 — две GREEN-половины. Это исполнено как написано; RED измерен трижды до первой production-правки (G-9/G-10, критерий 4, WR-02).
2. **Имена локальных переменных.** План называет `const pill` для `:198`/`:216` — так и сделано; на `:186`/`:312`/`:299` сохранены существующие `adminLink`/`loopTokens`/`homeTokens`, чтобы не переименовывать локаторы, объявленные выше по тесту.
3. **Цветовая проверка loading-состояния статическая.** Отдельного e2e на цвет подписи во время полёта нет (существующие кейсы `/voting` проверяют состояние, не цвет); `stateClass.loading` = `cursor-wait opacity-80` не содержит ни одного цветового токена, поэтому «меняется только прозрачность» доказано чтением, а не замером. Отмечено как `human_judgment: true`.
4. **Базлайн `npm run test:js` был 59, стал 61** — два новых гейта; `npm run build` не оставил оболочку в `web/` (проверено `git rev-parse --show-toplevel` перед коммитом).

## Issues Encountered

- Ни одного технического блокера. Единственный шум — предсуществующие `NO_COLOR` / `React DevTools hook` предупреждения Playwright и `INEFFECTIVE_DYNAMIC_IMPORT` / chunk-size предупреждения сборки.

## must_have assessment

| # | must_have | Доказательство | Статус |
|---|---|---|---|
| 1 | Пилюля: `rgb(255,255,255)` на `rgb(124,58,237)`, ≥ 4.5 в обеих темах | `theme-independent labels in both themes` | proven |
| 2 | `ingest-sources-add`: `rgb(255,255,255)` на `rgb(14,116,144)`, ≥ 4.5 | тот же кейс (regression hold) | proven |
| 3 | `voting`: `rgb(15,23,42)` на `rgb(234,179,8)`, ≥ 4.5 — положительный ассерт | тот же кейс ×2 темы + G-7 | proven |
| 4 | Ни одна заливка не несёт `text-text-primary`/`text-accent-ink`/`text-bg-app` | G-9 (14 → 0) | proven |
| 5 | Ни один скрайм не несёт темо-зависимый токен; все четыре на `bg-scrim` | G-10 (3 → 0) + `bg-scrim` в `UnsavedChangesDialog` (25-03) | proven |
| 6 | Ни один пилюльный ассерт не держится на подстроке `bg-primary` | пять токен-точных сайтов + `rg` пусто + измеренный RED | proven |
| 7 | Подпись в полёте меняет только прозрачность | статически (`stateClass.loading` без цветовых токенов); e2e цвета не измеряет | proven (static) |
| 8 | 320px: длинная подпись CTA и подпись пилюли без обрезки | `verification: backstop`, отдельным прогоном не измерялось | backstop |
| 9-10 | THEME-01 flagged assumptions (`empty`, `encoding`) | `background not rgba(0,0,0,0)` до арифметики + точное равенство строк `rgb(...)` — вопроса о «какое значение» у статического class-набора нет | proven |
| P1 | MUST NOT оставлять темо-зависимую подпись на заливке | G-9 | proven |
| P2 | MUST NOT вычищать `text-text-primary` из `AppShell.jsx` | канон `Concept 2 shell is expressed through tokens` зелёный; литерал на корне | proven |
| P3 | MUST NOT ставить белую подпись на жёлтую `voting` | позитивный ассерт `rgb(15,23,42)` (9.31); белая дала бы 1.92 | proven |

## Known Stubs

Нет. Все три проверки исполняются на реальном дереве, оба гейта сканируют реальные файлы (`web/src/**`), ни один ассерт не заглушен и не пропущен.

## Threat Flags

Нет новой поверхности. **T-25-03** закрыт `bg-scrim` на всех четырёх оверлеях при машинном запрете `bg-ink` и `bg-text-primary/<alpha>` (G-10). **T-25-10** закрыт G-9 плюс три пары в обеих темах с порогом 4.5. **T-25-11** закрыт тем, что правка `AppShell.jsx` — одна строка `isActive`-ветки, а канон-тест входит в verify каждого таска. **T-25-12** закрыт: в `ActionButton` изменены только цвета, `data-state`-контракт и `disabled` не тронуты, `confirm-vote` остаётся disabled до выбора радио (фикстура `/voting` это доказывает).

## User Setup Required

None.

## Next Phase Readiness

- **Все пять критериев фазы 25 теперь имеют падающее и пройденное доказательство**; `THEME-01` отмечен полным в `REQUIREMENTS.md`, `STATE.md` — `Phase complete — ready for verification`.
- **`bg-primary-solid` / `bg-success-solid` / `bg-danger-solid` / `text-voting-ink` / `text-on-solid` / `bg-scrim` получили потребителей** — мёртвых токенов из семейства contract B больше нет; единственный неиспользованный остаётся `--color-voting-ink` (используется здесь) — то есть все семь ролей востребованы.
- **Не тронуто намеренно (known adjacent defects):** toast `AdminDigestPage.jsx:808`, тинт-чипы `:717-718` и `EditorialCallout.jsx:10`, `border-danger` / `bg-danger/10`, `outline-accent` на полях источников, `ActionButton variant="secondary"` и базовый `text-primary` как текст, заливки без текста (`TopicBallot.jsx:26`, `VotingPage.jsx:448`).
- **Два backstop'а 320px** (длинная подпись CTA, подпись пилюли) остаются на верификатора как `human_needed` (`insufficient_spec`) — `min-h-11` и структура пилюли этим планом не менялись.
- **Фазы 26-27 потребляют это дерево:** скрайм и `-solid`-роли объявлены и заняты; новые токены фаза 26 объявлять не должна.

---
*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Completed: 2026-10-21*

## Self-Check: PASSED

- Все десять заявленных путей существуют и изменены в указанных объёмах (`AppShell` 1, `ActionButton` 4, `ServiceUnavailable` 1, страницы 2/2/1/5 строк; тесты +99/+58/26 строк).
- Все три коммита (`a907985`, `d25483e`, `cae4342`) найдены в истории.
- `npm run test:js` = 61 pass / 0 fail; `admin-chrome.spec.js` = 4 passed; `admin.spec.js` = 88 passed; `test:web` = 152 passed; `--list --project=web` = 152 теста / 6 файлов; `npm run build` exit 0.
