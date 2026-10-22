---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
verified: 2026-10-21T20:12:23Z
status: passed
score: "89/101 must-have entries verified (12 backstop → human)"
behavior_unverified: 0
overrides_applied: 0
goal: "An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product."
goal_clauses:
  - id: GC-1
    clause: "sees it named «Настройка»"
    status: met
    evidence: "Не изменено: три поверхности (sr-only h1, вкладка, <option>) читают «Настройка»; URL, PIPELINE_PATH и data-testid байт-идентичны; маршрута /admin/settings нет."
  - id: GC-2
    clause: "every field and label legible in both themes"
    status: met
    evidence: "GAP-25-5 закрыт: роль подписи `--color-primary-text` (#A78BFA dark / #6D28D9 light) переводит все 36 `text-primary`-сайтов в ≥ 4.5:1; переизмерено этим прогоном — плоские пары 5.844…7.105, retry 6.791/7.048, save-retry 5.984/6.513, худший тинт 4.934. Ранее падавшие статусные/тост/accent/граница остаются 5.201…16.296."
  - id: GC-3
    clause: "chrome that matches the rest of the product"
    status: met
    evidence: "Не изменено: eyebrow «Админ» удалён; кегль вкладки 24px === ingest-sources-heading; column-gap 16px; margin-top 0; nav.top − main.top < 48 (e2e 13/13)."
requirements:
  PIPEUI-01: satisfied
  PIPEUI-02: satisfied
  PIPEUI-03: satisfied
  PIPEUI-04: satisfied
  THEME-01: satisfied
  THEME-02: satisfied
requirement_ids_in_plans: [PIPEUI-01, PIPEUI-02, PIPEUI-03, PIPEUI-04, THEME-01, THEME-02]
requirement_ids_in_requirements_md: [PIPEUI-01, PIPEUI-02, PIPEUI-03, PIPEUI-04, THEME-01, THEME-02]
orphaned_requirements: []
unmapped_requirement_ids: []
re_verification:
  previous_status: gaps_found
  previous_score: "63/78"
  gaps_closed:
    - "GAP-25-5 — GC-2/WR-07: --color-primary как подпись (3.566…4.529) → закрыт 25-08: --color-primary-text (#A78BFA/#6D28D9), 36 литералов в 19 файлах на text-primary-text, гейт G-20 + e2e pipeline retry"
    - "GAP-25-6 — 25-05 #3/WR-10: G-14 измерял захардкоженную альфу → закрыт 25-09: tintAlphaSites читает /N из класса, STATUS_LABEL_TINTS и tintAlpha удалены"
    - "GAP-25-7 — 25-06 #6/WR-08/WR-09: G-16 R1/R3 не падали → закрыт 25-09: REGEX_LITERAL привязан к слэшу, R1 компилирует тело целиком (hasText/name/toHaveAccessibleName + grouped), R3 окно ±15 строк"
    - "behavior_unverified 25-04 #7 → закрыт 25-10: e2e «in-flight vote label keeps its colour and only dims» + гейт G-21"
  gaps_remaining: []
  regressions: []
  gaps_newly_identified: []
gaps: []
deferred:
  - truth: "WR-11 — граница радиокружка (border-border 1.178/1.554 против пола 3:1, TopicBallot.jsx role=radio)"
    addressed_in: "future UI phase"
    evidence: "25-10-SUMMARY.md § Отложено: «отложена верификатором в будущую UI-фазу»; вне must_have фазы (G-17 видит только input|select|textarea)"
  - truth: "WR-12 — провал отправки печатается text-success-ink (AdminDigestPage.jsx:771)"
    addressed_in: "future phase (semantic colour-by-outcome)"
    evidence: "вне трёх заявленных гэпов; вердикт gaps, не fail"
  - truth: "WR-13 — условный страж темы / reuseExistingServer (риск флейка)"
    addressed_in: "future harness-hardening"
    evidence: "вне трёх заявленных гэпов"
human_verification:
  - test: "25-02 backstop — 320px / строка вкладок: /admin/pipeline, «Дайджест» и «Настройка»"
    expected: "Обе подписи в одну строку внутри 44px (min-h-11) без обрезки; на < 640px строка скрыта (nav hidden … sm:flex) — работает <select>"
    why_human: "backstop; формулировка «на 320px» не совпадает с контрактом навигации, геометрия 320px не измеряется автотестом"
  - test: "25-02 backstop — 320px: мобильный <select> раздела"
    expected: "Высота 44px, непрозрачная paper, текст ink, выбранная опция не обрезана"
    why_human: "e2e читает только цвета и границу на 480px, но не высоту/обрезку на 320px"
  - test: "25-03 backstop — частично заполненная форма (тип выбран, id и название пусты)"
    expected: "Все три контрола — непрозрачная paper, текст ink-2 в обеих темах"
    why_human: "e2e проверяет пустые поля; смешанное состояние не покрыто"
  - test: "25-03 backstop — 200-символьный id в ingest-sources-id"
    expected: "Прокручивается внутри поля, не расширяет paper, не обрезает CTA «Добавить источник»"
    why_human: "long-text backstop, авто-замера переполнения нет"
  - test: "25-03 backstop — первичная загрузка в полёте"
    expected: "Строк и скелетона нет, заголовок «Источники» и paper остаются отрисованными"
    why_human: "loading-состояние не имеет инжектора в харнессе"
  - test: "25-03 backstop — строка только с id (без названия)"
    expected: "Переключатель и все действия строки видимы и читаемы"
    why_human: "partial backstop, нет фикстуры «id без label»"
  - test: "25-03 backstop — 20 строк на 320px"
    expected: "Страница удлиняется, ни одна строка не обрезана, горизонтальной прокрутки нет"
    why_human: "overflow backstop, 320px-кейса нет"
  - test: "25-03 backstop — 0 / 1 / 20 строк"
    expected: "Одна и та же paper-2 на строку и ритм 8px; singular/plural не вводится"
    why_human: "zero-one-many backstop"
  - test: "25-03 backstop — длинный id канала/плейлиста в строке"
    expected: "Переносится/усекается внутри строки, действия во вьюпорте, текст ≥ 4.5:1"
    why_human: "long-text backstop"
  - test: "25-03 backstop — 320px: диалог несохранённых изменений"
    expected: "Тело переносится, «Остаться» и «Уйти без сохранения» полностью видимы, без горизонтального переполнения"
    why_human: "overflow backstop"
  - test: "25-04 backstop — 320px: самая длинная подпись CTA «Уйти без сохранения»"
    expected: "Переносится внутри 44px-цели без обрезки"
    why_human: "overflow backstop"
  - test: "25-04 backstop — 320px: подпись активной навигационной пилюли"
    expected: "Полностью внутри пилюли, #FFFFFF на primary-solid, без обрезки"
    why_human: "overflow backstop"
review_disposition:
  closed: [CR-01, WR-01, IN-02, WR-02, WR-03, WR-04, WR-05, WR-06, WR-07, WR-08, WR-09, WR-10]
  open_non_blocking: [IN-01, IN-03, IN-04, IN-05, IN-06, IN-07, IN-08, IN-09, IN-10, IN-11, WR-11, WR-12, WR-13]
---

# Phase 25 — Verification Report (Re-verification after gap-closure wave 25-08…25-10)

**Phase:** `25-admin-nastroyka-naming-readable-surfaces-token-repair`
**Goal (ROADMAP § Phase 25):** «An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product.»
**Verified:** 2026-10-21T20:12:23Z
**Re-verification:** да — после gap-closure планов 25-08, 25-09, 25-10 (коммиты `c770512`…`881d669`)
**Verdict:** **`human_needed`** — все три измеримых гэпа закрыты по существу, все три клаузы цели (GC-1/GC-2/GC-3) теперь `met`, единственный `behavior_unverified`-пункт автоматизирован. Остаются **12** человеко-проверочных backstop-пунктов (геометрия 320px, реальный мобильный браузер, частично заполненные формы, длинный текст, zero-one-many), которые по процессу (`passed` валиден только при пустой секции human verification) требуют `human_needed`, а не `passed`.

## Что изменилось с прошлой проверки (gaps_found, 63/78)

| Гэп | Как закрыт | Доказательство в этом прогоне |
|---|---|---|
| **GAP-25-5** (GC-2/WR-07): `--color-primary` как подпись 3.566…4.529 | 25-08: `--color-primary-text` (#A78BFA dark / #6D28D9 light), 36 литералов → `text-primary-text`, гейт G-20, e2e `pipeline retry actions…` | переизмерено (ниже): все ≥ 4.5, худший 4.934; 0 `text-primary`, 36 `text-primary-text`; G-20 ловит мутацию |
| **GAP-25-6** (25-05 #3/WR-10): G-14 захардкоженная альфа | 25-09: `tintAlphaSites` читает `/N` из класса; `STATUS_LABEL_TINTS`/`tintAlpha` удалены | 0 `STATUS_LABEL_TINTS`, 0 `tintAlpha`; G-14 proof `/60` зелёный; анти-вакуум 3 роли + ≥ 4 токена |
| **GAP-25-7** (25-06 #6/WR-08/WR-09): G-16 R1/R3 не падали | 25-09: `REGEX_LITERAL` привязан к слэшу, R1 компилирует тело целиком (4 формы + grouped), R3 окно ±15 строк | 4 proof-теста зелёные; R1/R3 читают не текст файла, а поведение |
| **behavior_unverified 25-04 #7** | 25-10: e2e `in-flight vote label keeps its colour and only dims` + гейт G-21 | e2e рендерит loading в обеих темах (13-й кейс); G-21 ловит мутацию |

## Метод и воспроизведённые команды

- Прочитаны все 10 PLAN и 10 SUMMARY, `25-VERIFICATION.md` (prior), `25-REVIEW.md`, `25-REVIEW-DISPOSITION.md`, `ROADMAP.md` § Phase 25, `REQUIREMENTS.md`, `STATE.md`.
- Каждый `must_have` сверен с **рабочим деревом** (не с текстом SUMMARY): grep по `web/src`, `tests/unit/test_semantic_token_coverage.js`, `tests/admin-chrome.spec.js`, `web/src/index.css`.
- Контрастные пары пересчитаны репозиторным хелпером `tests/helpers/contrast.js` (`parseColor` → `relativeLuminance` → `contrastRatio`, тинты — `blendOver`).
- Невакуумность гейтов G-20 и G-21 доказана **живой мутацией** (правка → прогон → откат; `git diff --stat -- web/src tests` пуст после отката).
- Порт 5174 свободен перед прогоном Playwright.

| Команда | Результат |
|---|---|
| `npm run test:js` | **97 pass / 0 fail** (G-0…G-21 + proofs + canon 51/13) |
| `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` | **13 passed** (54.3 s) |
| `npm run build` | **exit 0**, `✓ built in 348ms` (только прежние chunk-size / `INEFFECTIVE_DYNAMIC_IMPORT` предупреждения) |

### Статические проверки

| Проверка | Результат |
|---|---|
| `--color-primary-text` объявлений | **2** (`#A78BFA` в `@theme static`, `#6D28D9` в `[data-theme="light"]`) |
| `--color-primary:` объявлений | **1** — `#8B5CF6` (база не тронута, D-05) |
| `text-primary` (standalone, не `-text`/`text-`) под `web/src` | **0** |
| `text-primary-text` вхождений | **36** |
| коррупция `text-text-primary-text` / `bg-primary-text` | **0** |
| `text-text-primary` (основной текст) | сохранён (38 вхождений, не тронут) |
| `bg-primary` / `border-primary` / `outline-primary` (заливки/бордеры) | 4 / 2 / 5 — остаются легальными |
| `text-accent-text` сайтов | **3** (не расширен) |
| `tintAlpha` в `admin-chrome.spec.js` | **0** (константа удалена, хелпер `pillAlpha`) |
| `STATUS_LABEL_TINTS` в unit-тесте | **0** (заменён `TINT_LABEL_ROLES` без альфы) |
| `waitForTimeout` / `page.clock` в спеке | **0** |
| `test.skip` / `test.fixme` | **0** |

## Goal-Backward Analysis

| Клауза | Статус | Доказательство |
|---|---|---|
| **GC-1** «sees it named «Настройка»» | **MET** | не изменено планами 08/09/10; `AdminLayout.jsx` sr-only h1 / вкладка / `<option>` = «Настройка»; URL/testid/`aria-label` байт-идентичны |
| **GC-2** «every field and label legible in both themes» | **MET** | закрыт GAP-25-5: роль `--color-primary-text` даёт ≥ 4.5 на всех 6 плоских базах + худший тинт 4.934; ранее падавшие пары (статус/тост/accent/граница) остаются 5.201…16.296 |
| **GC-3** «chrome that matches the rest of the product» | **MET** | не изменено; eyebrow удалён, кегль 24px, gap 16px, mt-0, nav.top−main.top < 48 |

**Почему `human_needed`, а не `passed`.** Три измеримых гэпа закрыты, все три клаузы цели `met`, `behavior_unverified` пуст. Но 12 backstop-пунктов — это человеко-проверочные требования (геометрия на 320px, реальный мобильный браузер, частично заполненные формы, длинный текст, zero-one-many), которые процесс верификации классифицирует как `Always needs human` (Step 8). По дереву решений (Step 9) `passed` валиден только при пустой human-секции — поэтому статус `human_needed`. Эти пункты закрываются `/gsd-verify-work` (UAT), а не планом.

## Must-Have Scorecard (все 10 планов)

| План | Записей | ✓ verified | ⊘ backstop → human | ✗/⚠️ |
|---|---|---|---|---|
| 25-01 (PIPEUI-01) | 6 | 6 | 0 | 0 |
| 25-02 (PIPEUI-03/04) | 11 | 9 | 2 | 0 |
| 25-03 (THEME-02/PIPEUI-02) | 23 | 15 | 8 | 0 |
| 25-04 (THEME-01) | 11 | 9 | 2 | 0 |
| 25-05 (gap: роли + граница) | 9 | **9** | 0 | 0 |
| 25-06 (gap: 18 сайтов + тост) | 9 | **9** | 0 | 0 |
| 25-07 (gap: accent-text + field-border) | 9 | 9 | 0 | 0 |
| 25-08 (gap: primary-text + G-20) | 7 | **7** | 0 | 0 |
| 25-09 (gap: G-14 альфа + G-16 R1/R3) | 9 | **9** | 0 | 0 |
| 25-10 (gap: in-flight + G-21) | 7 | **7** | 0 | 0 |
| **Итого** | **101** | **89** | **12** | **0** |

Изменения относительно prior (63/78): 25-05 #3 и 25-06 #6 переведены из `partial` в `verified` (GAP-25-6/25-7), 25-04 #7 из `behavior-unverified` в `verified` (25-10); добавлены 23 новых must_have планов 08/09/10 — все `verified`.

## Измеренный контраст — GAP-25-5 (пересчитано `tests/helpers/contrast.js`)

Роль подписи `--color-primary-text`: `#A78BFA` (dark) / `#6D28D9` (light); база `--color-primary` `#8B5CF6` — заливка/бордер/ринг/тинт (не трогается).

### Плоские пары (порог 4.5)

| Поверхность | dark `#A78BFA` | light `#6D28D9` |
|---|---|---|
| `bg-app` (`#0B0F17` / `#F8FAFC`) | **7.048** | **6.791** |
| `paper` (`#131925` / `#FFFFFF`) | **6.466** | **7.105** |
| `paper-2` (`#1A2233` / `#F1F5F9`) | **5.844** | **6.485** |

### Две кнопки раздела «Настройка» (было → стало)

| Кнопка | поверхность | было (`#8B5CF6`) | стало |
|---|---|---|---|
| `pipeline-config-retry` | `bg-app` | 4.047 light / 4.529 dark | **6.791** / **7.048** |
| `pipeline-config-save-retry` | `bg-danger/10` над `bg-app` | 3.566 light / 4.186 dark | **5.984** / **6.513** |

### Худший тинт `bg-primary/15` (над `paper-2`)

| Тема | ratio | запас над 4.5 |
|---|---|---|
| dark (`#A78BFA` на `blendOver(#8B5CF6, #1A2233, 0.15)`) | **4.934** | 0.434 |
| light (`#6D28D9` на `blendOver(#8B5CF6, #F1F5F9, 0.15)`) | **5.430** | 0.930 |

Все шесть плоских пар и оба тинта выше порога 4.5 — GAP-25-5 закрыт по существу. Числа дословно совпадают с 25-08-SUMMARY.md (5.844 / 4.934 / 6.791 / 7.048 / 5.984 / 6.513) — независимый пересчёт это подтверждает.

## Невакуумность гейтов (живая мутация)

| Гейт | Мутация | Результат | Откат |
|---|---|---|---|
| **G-20** | `AdminPipelineConfigPage.jsx:242` `text-primary-text` → `text-primary` | ✖ `AssertionError: primary is not a label role — … AdminPipelineConfigPage.jsx: text-primary` (96/97) | зелёный |
| **G-21** | `ActionButton.jsx` `stateChrome.loading` → `'cursor-wait opacity-80 bg-danger'` | ✖ `stateChrome.loading paints a colour — in-flight only dims` (96/97) | зелёный |
| **G-14** | proof-тест `/15 → /60` (синтетика) | ✔ утверждает 4.181/4.094/4.264 light, 3.011/2.699/2.850 dark — все < 4.5 | — |
| **G-16 R1/R3** | 4 proof-теста (альтернация в hasText/name/toHaveAccessibleName, grouped, текстовый тост, single-alternative) | ✔ каждый утверждает ровно ожидаемых нарушителей | — |

`git diff --stat -- web/src tests` после откатов пуст — рабочее дерево не изменено.

## Behavioral Spot-Checks

| Поведение | Команда | Результат | Статус |
|---|---|---|---|
| Все статические гейты + proofs + канон | `npm run test:js` | 97 pass / 0 fail | ✓ PASS |
| Наименование, хром, читаемость, retry, in-flight | `npx playwright test tests/admin-chrome.spec.js --project=web` | 13 passed (54.3 s) | ✓ PASS |
| Сборка | `npm run build` | exit 0 | ✓ PASS |
| Контраст primary-text | node + `tests/helpers/contrast.js` | 5.844…7.105 flat, 4.934…5.430 tint | ✓ PASS |
| Пробы | `scripts/**/tests/probe-*.sh` | не найдено | SKIPPED (проб нет) |

## Requirements Coverage

Объединение фронтматтера всех 10 планов — **шесть** ID, байт-идентично `REQUIREMENTS.md` и `ROADMAP.md` § Phase 25. Сирот и необъявленных ID нет.

| Requirement | Статус | Доказательство |
|---|---|---|
| **PIPEUI-01** — «Настройка» на трёх поверхностях, URL не меняется | ✓ SATISFIED | e2e `naming:` + `AdminLayout.jsx`; не тронут 25-08/09/10 |
| **PIPEUI-02** — «Тип» и опции «Канал»/«Плейлист» читаемы | ✓ SATISFIED | e2e `select legible…` 11.852/10.355 |
| **PIPEUI-03** — «Источники», без «ингеста» | ✓ SATISFIED | `IngestSourcesSection.jsx`; e2e `chrome:` |
| **PIPEUI-04** — eyebrow удалён, кегль= h2, шире gap, меньше пустоты | ✓ SATISFIED | e2e `chrome:` 24px/gap 16/mt-0 |
| **THEME-01** — белые подписи на primary/accent, voting тёмная; in-flight только dims | ✓ SATISFIED | e2e 5.699/5.358/9.309 + новый in-flight (9.309, opacity 0.55) + G-9/G-10/G-21 |
| **THEME-02** — семейство объявлено + гейт падает на необъявленном токене | ✓ SATISFIED | `index.css` + G-0…G-21 (включая G-20 primary-text) |

**Сироты:** нет. **Необъявленные ID:** нет.

## Data-Flow Trace (Level 4) — ключевые артефакты 08/09/10

| Артефакт | Переменная/токен | Источник | Реальные данные | Статус |
|---|---|---|---|---|
| `web/src/index.css` → компоненты | `--color-primary-text` | единственный `@theme static` + единственный light-блок | да — e2e читает `getComputedStyle`: `rgb(167,139,250)`/`rgb(109,40,217)` | ✓ FLOWING |
| `AdminPipelineConfigPage.jsx` retry | `text-primary-text` | утилита резолвится из токена | да — e2e `pipeline retry actions…` | ✓ FLOWING |
| `G-14` → `web/src` | `tintAlphaSites` | дерево (`stringLiterals` + `tokenSet`) | да — 7 сайтов / 4 токена с файлами | ✓ FLOWING |
| `G-16` R1/R3 → `tests/*.spec.js` | `regexLiterals` / окно ±15 | спеки (комментарии замаскированы) | да — 13 литералов / 10 тел / 0 нарушителей | ✓ FLOWING |
| `ActionButton.jsx` loading | `stateFill.loading` / `stateChrome.loading` | объект-литералы (парсится, не регулярка) | да — e2e читает computed `rgb(15,23,42)` на `rgb(234,179,8)`, opacity 0.55 | ✓ FLOWING |

## Anti-Patterns Found

| Файл | Паттерн | Severity | Влияние |
|---|---|---|---|
| — | `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` | — | 0 |
| — | `return null` / `=> {}` / пустые реализации | — | 0 |
| — | произвольные цвета / `!important` / inline-стили цвета | — | 0 (G-12 allow-list пуст) |
| — | `console.log` в proof-замерах | ℹ️ Info | отчёт о коэффициентах при падении; не production |
| `TopicBallot.jsx` | `border-border` у `role="radio"` 1.178/1.554 (WR-11) | ℹ️ Info → deferred | вне must_have; отложено в UI-фазу |
| `AdminDigestPage.jsx:771` | провал отправки `text-success-ink` (WR-12) | ℹ️ Info → deferred | семантически неверный цвет исхода; вне гэпов |
| `playwright.config.js` / `gotoAdmin` | условный страж темы (WR-13) | ℹ️ Info → deferred | риск флейка, не дефект фазы |

## Human Verification Required (12 backstop-пунктов)

Все 12 — геометрия/визуал на 320px, реальный мобильный браузер, частично заполненные формы, длинный текст, zero-one-many. Viewport задавать явно; темы — обе (`data-theme="light"` и отсутствие атрибута = тёмная), `VITE_USE_MOCKS=true`. Полный список — во frontmatter `human_verification`. Закрываются `/gsd-verify-work`, а не планом.

## Gaps Summary

Goal-backward картина: naming, хром, семейство токенов, 18 статусных подписей, тост, accent-ссылки, граница поля **и** роль подписи `primary` — всё в дереве, измерено и закреплено тестами. Три прежних гэпа закрыты по существу, а не по форме: G-20/G-21 доказаны живой мутацией, G-14 читает альфу из класса, G-16 R1/R3 читают поведение, а не текст файла. Пять success criteria ROADMAP выполнены; все шесть требований `SATISFIED`; блокирующих anti-pattern нет.

Остаются **12 человеко-проверочных backstop-пунктов** — это не дефекты, а явно объявленные в планах человеческие проверки (геометрия 320px, реальный мобильный браузер). Они не блокируют цель, но по процессу верификации исключают `passed` и дают `human_needed`.

Отложенные ревью-замечания `WR-11` (граница радио 1.178/1.554), `WR-12` (провал отправки зелёным), `WR-13` (стабильность харнесса) и `IN-01…IN-11` не входят в must_have фазы и на вердикт не влияют; `WR-11` — тот же класс дефекта, что закрывал 25-07, стоит взять в ближайшую UI-фазу.

---

_Verified: 2026-10-21T20:12:23Z_
_Verifier: Claude (gsd-verifier)_
