---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
verified: 2026-10-21T20:56:00Z
status: gaps_found
score: "63/78 must-have entries verified (2 partial, 1 behavior-unverified, 12 backstop)"
goal: "An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product."
goal_clauses:
  - id: GC-1
    clause: "sees it named «Настройка»"
    status: met
    evidence: "Три поверхности (sr-only h1, вкладка, <option>) читают «Настройка»; URL, PIPELINE_PATH и data-testid не изменены; маршрута /admin/settings нет."
  - id: GC-2
    clause: "every field and label legible in both themes"
    status: partial
    evidence: "Все пары, которые фаза обязалась починить, теперь ≥ 4.5:1 (статусные подписи 5.201…11.007, тост 16.296/14.516, accent-ссылки 5.358/7.248, граница поля 4.759/3.698 при пороге 3:1). Но универсальная формулировка клаузы не выполняется: роль --color-primary как подписи даёт 4.047 (light bg-app), 3.566/4.186 (кнопка повтора сохранения на bg-danger/10) — см. GAP-25-5 / WR-07."
  - id: GC-3
    clause: "chrome that matches the rest of the product"
    status: met
    evidence: "Eyebrow «Админ» удалён из AdminLayout; кегль вкладки 24px === ingest-sources-heading; column-gap 16px; margin-top 0; nav.top − main.top < 48 (e2e 11/11)."
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
behavior_unverified: 1
overrides_applied: 0
re_verification:
  previous_status: human_needed
  previous_score: "65/78"
  gaps_closed:
    - "GAP-25-1 — WR-02: статусные токены как текст на тинтах (1.92/1.62/3.17/3.76 в светлой теме)"
    - "GAP-25-2 — WR-05: тост админки 1.00:1 в обеих темах и carve-out в G-10"
    - "GAP-25-3 — 25-03 must_have #12: ссылка «Повторить загрузку» 2.43:1 на светлой paper"
    - "GAP-25-4 — 25-03 must_have #10: край поля не измерялся и не держал 3:1"
  gaps_remaining: []
  regressions: []
  gaps_newly_identified:
    - "GAP-25-5 — GC-2: --color-primary как подпись (3.566…4.529) в разделе «Настройка» (WR-07)"
    - "GAP-25-6 — 25-05 #3: G-14 измеряет захардкоженную альфу 0.15, а не класс (WR-10)"
    - "GAP-25-7 — 25-06 #6: G-16 R1/R3 не падают на реальных регрессиях (WR-08/WR-09)"
gaps:
  - id: GAP-25-5
    truth: "GC-2: каждая подпись в разделе «Настройка» читается в обеих темах (≥ 4.5:1)"
    status: failed
    reason: "Роль --color-primary (#8B5CF6, без light-переопределения) осталась текстовой ролью. Измерено тем же tests/helpers/contrast.js: 4.047 на светлой bg-app, 4.234 на светлой paper, 4.156 на тёмной paper, 3.756 на тёмной paper-2; кнопка «Повторить сохранение» стоит на bg-danger/10 и даёт 3.566 (light) / 4.186 (dark). Ни один гейт этот класс дефекта не покрывает: G-19 банит только text-accent, G-7 перебирает ink/ink-2/muted/danger-ink."
    artifacts:
      - path: "web/src/pages/AdminPipelineConfigPage.jsx"
        issue: ":242 pipeline-config-retry text-primary — 4.047 (light) / 4.529 (dark)"
      - path: "web/src/pages/AdminPipelineConfigPage.jsx"
        issue: ":370 pipeline-config-save-retry text-primary на bg-danger/10 — 3.566 (light) / 4.186 (dark)"
      - path: "web/src/pages/AdminDigestPage.jsx"
        issue: ":541, :728, :748, :776, :849 — та же роль подписи (3.756…4.234)"
      - path: "web/src/components/ActionButton.jsx"
        issue: ":44 secondary-вариант text-primary — ниже 4.5 хотя бы в одной теме"
    missing:
      - "Ввести роль подписи для primary (например --color-primary-text: #A78BFA dark / #6D28D9 light, 5.84…7.11 на трёх базах) и перевести на неё текстовые text-primary; заливки bg-primary остаются легальными"
      - "Расширить G-7 на text-primary или добавить G-20 по образцу G-19 (FORBIDDEN_LABEL + light-override обязателен)"
      - "Регрессионный ассерт на pipeline-config-retry и pipeline-config-save-retry в admin-chrome.spec.js"
  - id: GAP-25-6
    truth: "25-05 #3 — G-14 измеряет тинт-композиты подписи на paper/paper-2/bg-app и падает при дрейфе альфы"
    status: partial
    reason: "Значения в рабочем дереве проходят (success 5.795…8.778, voting 7.057…10.532, danger 5.201…6.407). Но STATUS_LABEL_TINTS фиксирует alpha: 0.15/0.2/0.1 константой, не связанной с классами bg-success/15, bg-voting/20, bg-danger/10; мутация /15 → /60 оставляет npm run test:js зелёным, хотя реальный композит даёт 4.181 (4.094 на paper-2). Гейт зелёный по текущему коду, но доказательство слабее заявленного."
    artifacts:
      - path: "tests/unit/test_semantic_token_coverage.js"
        issue: ":113-117 STATUS_LABEL_TINTS с захардкоженной альфой"
      - path: "tests/admin-chrome.spec.js"
        issue: ":379 tintAlpha = { success: 0.15, voting: 0.2 } дублирует константу вместо чтения DOM"
    missing:
      - "Выводить альфу из класса (classTokens) или из getComputedStyle(el).backgroundColor, а не из константы"
      - "Proof-тест: смена /15 на /60 обязана ронять G-14"
  - id: GAP-25-7
    truth: "25-06 #6 — G-16 обеспечивает контракт статусных ассертов и обязывает тост читать цвета"
    status: partial
    reason: "Рабочий код честен: e2e «failure toast legible» действительно читает backgroundColor и borderTopColor (16.296/14.516). Но два из трёх правил гейта не могут упасть: R3 ищет подстроки backgroundColor/borderTopColor в том же файле, где они уже есть в хелпере styleTriple(), поэтому удаление всех цветовых expect у тоста оставляет гейт зелёным; R1 не видит альтернацию внутри hasText:/name. R2 работает."
    artifacts:
      - path: "tests/unit/test_semantic_token_coverage.js"
        issue: ":485-486 REGEX_ASSERTION не покрывает hasText/name/toHaveAccessibleName"
      - path: "tests/unit/test_semantic_token_coverage.js"
        issue: ":555-570 toastReaders проверяет текст файла, а не тост"
    missing:
      - "Привязать R3 к блоку admin-toast (окно ±15 строк) или перенести инвариант в спеку"
      - "Расширить R1 до hasText|name|toHaveAccessibleName или разбирать все regex-литералы файла"
deferred: []
behavior_unverified_items:
  - truth: "25-04 #7 — пока действие в полёте, подпись кнопки сохраняет тот же тема-независимый цвет, меняется только прозрачность"
    test: "Открыть /voting в обеих темах, выбрать радио и нажать confirm-vote; прочитать вычисленную пару color/background-color в состоянии data-state=loading"
    expected: "Цвет подписи остаётся #FFFFFF на -solid-заливке (или #0F172A на bg-voting), меняется только opacity"
    why_human: "ActionButton.jsx рендерит в loading только stateChrome = 'cursor-wait opacity-80' без цветового токена, но e2e измеряет лишь idle и error; состояние loading не отрисовывается ни одним тестом."
coincidental_reliance_items: []
human_verification:
  - test: "25-02 backstop — 320px / строка вкладок: открыть /admin/pipeline, посмотреть «Дайджест» и «Настройка»"
    expected: "Обе подписи в одну строку внутри 44px (min-h-11) без обрезки; на < 640px строки нет (nav объявлен hidden … sm:flex) — там работает <select>"
    why_human: "backstop; формулировка «на 320px» не совпадает с контрактом навигации, геометрия 320px не измеряется"
  - test: "25-02 backstop — 320px: мобильный <select> раздела"
    expected: "Высота 44px, непрозрачная paper, текст ink, выбранная опция не обрезана"
    why_human: "e2e читает только цвета и границу на 480px, но не высоту/обрезку на 320px"
  - test: "25-03 backstop — частично заполненная форма (тип выбран, id и название пусты)"
    expected: "Все три контрола рисуют непрозрачную paper и текст ink-2 в обеих темах"
    why_human: "e2e проверяет пустые поля; смешанное состояние не покрыто"
  - test: "25-03 backstop — 200-символьный id в ingest-sources-id"
    expected: "Прокручивается внутри поля, не расширяет блок paper, не обрезает CTA «Добавить источник»"
    why_human: "long-text backstop, автоматического замера переполнения нет"
  - test: "25-03 backstop — первичная загрузка в полёте"
    expected: "Строк и скелетона нет, заголовок «Источники» и поверхность paper остаются отрисованными"
    why_human: "loading-состояние не имеет инжектора в харнессе"
  - test: "25-03 backstop — строка только с id (без названия)"
    expected: "Переключатель включения и все действия строки видимы и читаемы"
    why_human: "partial backstop, нет фикстуры «id без label»"
  - test: "25-03 backstop — 20 строк на 320px"
    expected: "Страница удлиняется, ни одна строка не обрезана, горизонтальной прокрутки нет"
    why_human: "overflow backstop, 320px-кейса нет"
  - test: "25-03 backstop — 0 / 1 / 20 строк"
    expected: "Одна и та же поверхность paper-2 на строку и ритм 8px; singular/plural не вводится"
    why_human: "zero-one-many backstop"
  - test: "25-03 backstop — длинный id канала/плейлиста в строке"
    expected: "Переносится или усекается внутри строки, действия строки во вьюпорте, текст ≥ 4.5:1"
    why_human: "long-text backstop"
  - test: "25-03 backstop — 320px: диалог несохранённых изменений"
    expected: "Тело переносится, «Остаться» и «Уйти без сохранения» полностью видимы, горизонтального переполнения нет"
    why_human: "overflow backstop"
  - test: "25-04 backstop — 320px: самая длинная подпись CTA «Уйти без сохранения»"
    expected: "Переносится внутри 44px-цели без обрезки"
    why_human: "overflow backstop"
  - test: "25-04 backstop — 320px: подпись активной навигационной пилюли"
    expected: "Полностью внутри пилюли, #FFFFFF на primary-solid, без обрезки"
    why_human: "overflow backstop"
  - test: "25-04 #7 — подпись кнопки в состоянии loading"
    expected: "Цвет подписи не переворачивается вместе с темой; меняется только прозрачность"
    why_human: "см. behavior_unverified_items"
review_disposition:
  closed: [CR-01, WR-01, IN-02, WR-02, WR-03, WR-04, WR-05, WR-06]
  open_blocking: [WR-07, WR-08, WR-09, WR-10]
  open_non_blocking: [IN-01, IN-03, IN-04, IN-05, WR-11, WR-12, WR-13]
---

# Phase 25 — Verification Report

**Phase:** `25-admin-nastroyka-naming-readable-surfaces-token-repair`
**Goal (ROADMAP § Phase 25):** «An admin opening the pipeline section sees it named «Настройка», every field and label legible in both themes, and chrome that matches the rest of the product.»
**Verified:** 2026-10-21T20:56:00Z
**Re-verification:** да — после gap-closure планов 25-05, 25-06, 25-07 и после ревью `25-REVIEW.md` (c4ec7e4)
**Verdict:** **`gaps_found`** — четыре прежних гэпа закрыты и переизмерены, пять success criteria ROADMAP выполнены. Но клауза GC-2 в её универсальной формулировке не выполнена: роль `--color-primary` как подписи даёт **3.566…4.529:1**, в том числе на двух кнопках самого раздела «Настройка». Плюс два must_have (25-05 #3, 25-06 #6) опираются на гейты, которые ревью доказало мутациями как неспособные упасть, — они помечены `partial`, а не `met`.

## Что изменилось с прошлой проверки

Предыдущий отчёт (`human_needed`, 65/78, 18:05) описывал состояние **после** 25-05…25-07 и был прав в том, что четыре гэпа закрыты. Он не учёл находки свежего ревью, и его frontmatter содержал артефакты нумерации строк. Настоящая проверка переизмеряет то же дерево и добавляет три расхождения.

| Гэп | Как закрыт | Доказательство в этом прогоне |
|---|---|---|
| **GAP-25-1** (WR-02): статусные токены как подпись на тинтах — 1.92 / 1.62 / 3.17 / 3.76 в светлой теме | `--color-success-ink`, `--color-voting-ink-on-tint`, `--color-danger-ink` + миграция всех 18 сайтов | 18 вхождений `text-*-ink` (0 базовых `text-success`/`text-voting`/`text-danger`); G-14/G-18 зелёные; e2e `status labels legible in both themes` |
| **GAP-25-2** (WR-05): тост админки 1.00:1 в обеих темах | `border border-rule bg-paper-2 text-ink`; carve-out `bg-text-primary` удалён из G-10 | `AdminDigestPage.jsx:808-809`; e2e читает `backgroundColor`/`borderTopColor`: **16.296** светлая / **14.516** тёмная; `bg-text-primary` под `web/src` — 0 |
| **GAP-25-3** / 25-03 #12: ссылка повтора 2.43:1 на светлой `paper` | новая роль подписи `--color-accent-text` на трёх сайтах | e2e `load-error actions and the preview link are legible in both themes`: `rgb(14,116,144)` = **5.358**, сообщение `ink-2` = **10.355** |
| **GAP-25-4** / 25-03 #10: край поля не измерялся и не держал 3:1 | `--color-field-border: #64748B` (плоский) на всех 16 контролах + G-15/G-17 | e2e `control boundaries clear 3:1…`: **4.759** светлая / **3.698** тёмная; карточка остаётся `rule` (**1.485**) — гейт различает роли |
| **GAP-25-5** (новый): `--color-primary` как подпись | не закрыт ни одним планом | измерено ниже: 3.566 / 4.047 / 4.156 / 4.234 / 4.529 |
| **GAP-25-6** (новый): G-14 и захардкоженная альфа | не закрыт | мутация `/15 → /60` не роняет `test:js` (ревью), значения в дереве проходят |
| **GAP-25-7** (новый): G-16 R1/R3 | не закрыт | мутации ревью: удаление цветовых expect у тоста и альтернация в `hasText:` остаются зелёными |
| **WR-03** | `ActionButton` — одна заливка на состояние | e2e `the vote button paints exactly one fill in every state` (11-й кейс) |
| **WR-04** | `gotoAdmin` ждёт `(dataset.theme ?? 'dark') === theme` | `admin-chrome.spec.js:44-57`; `waitForTimeout` в спеке — 0 |

## Метод и воспроизведённые команды

- Прочитаны семь PLAN и семь SUMMARY, `25-REVIEW.md`, `ROADMAP.md` § Phase 25, `web/src/index.css`, `AdminLayout.jsx`, `IngestSourcesSection.jsx`, `AdminPipelineConfigPage.jsx`, `ActionButton.jsx`.
- Каждый `must_haves`-пункт сверен с рабочим деревом и прогонами, а не с текстом SUMMARY.
- Контрастные пары пересчитаны хелпером репозитория `tests/helpers/contrast.js` (`parseColor` → `relativeLuminance` → `contrastRatio`, тинты — через `blendOver`).
- Перед прогоном Playwright освобождён порт 5174: висел устаревший Vite (PID 23844), снят `Stop-Process`.

| Команда | Результат |
|---|---|
| `npm run test:js` | **89 pass / 0 fail** — G-0…G-19 + proof'ы + канон 51/13 |
| `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` | **11 passed** (53.2 s) |
| `npm run build` | **exit 0**, `✓ built in 425ms` (только прежние chunk-size / `INEFFECTIVE_DYNAMIC_IMPORT` предупреждения) |

### Статические проверки

| Проверка | Результат |
|---|---|
| Блоки `@theme` / `[data-theme="light"]` в `web/src/index.css` | **1 / 1** (G-0) |
| Объявлений `--color-field-border` | **1** (строка 82, в `@theme static`, без light-override — G-3) |
| `accent-ink` в CSS и под `web/src` | **0 / 0** (G-5) |
| `bg-ink`, `bg-text-primary`, `bg-paper*` с альфой | **0** (G-6 / G-10 без carve-out) |
| `text-success` / `text-voting` / `text-danger` как подпись | **0**; `text-*-ink` — ровно **18** сайтов |
| `text-accent` (без `-text`) | **0**; `text-accent-text` — 3 сайта (G-19) |
| `border-field-border` | 16 контролов (G-17, anti-vacuum `controlCount >= 16`) |
| «Настройка» в `AdminLayout.jsx` | **3** литерала: sr-only `h1` (`:47`), вкладка (`:68`), `<option>` (`:81`) |
| `/admin/settings` | **0**; маршрут `admin/pipeline` — `App.jsx:62` |
| «Источники ингеста» | **0**; `ingest-sources-heading` = «Источники» (`IngestSourcesSection.jsx:170-173`) |
| `!important`, произвольные цвета, inline-стили цвета | **0** (G-12 allow-list пуст) |
| `TBD` / `FIXME` / `XXX` / `TODO` / `HACK` в файлах фазы | **0** (совпадения `placeholder` — атрибуты полей) |
| `waitForTimeout` в `admin-chrome.spec.js` | **0** |

## Goal-Backward Analysis

| Клауза | Статус | Доказательство |
|---|---|---|
| **GC-1** «sees it named «Настройка»» | **MET** | e2e `naming:` — вкладка `admin-tab-pipeline` = «Настройка», sr-only `h1` = «Настройка» (единственный, `width ≤ 1px`), `<option>` = «Настройка», `value` = `/admin/pipeline`, `page.url()` не изменился, `aria-label="Разделы админки"` ×2 целы; `AdminLayout.jsx:47`, `:68`, `:81`; `App.jsx:62`; `/admin/settings` — 0 |
| **GC-2** «every field and label legible in both themes» | **PARTIAL** | Обязательные пары ≥ 4.5: статусные подписи 5.201…11.007, тост 16.296/14.516, accent-ссылки 5.358/7.248, граница поля 4.759/3.698 (порог 3:1). Не выполнено для `text-primary`: **4.047** (light bg-app), **4.234** (light paper), **4.156** (dark paper), **3.756** (dark paper-2), **4.529** (dark bg-app, единственная проходящая база), а `pipeline-config-save-retry` на `bg-danger/10` — **3.566 / 4.186**. См. GAP-25-5 |
| **GC-3** «chrome that matches the rest of the product» | **MET** | e2e `chrome:` — «Админ» ровно 1 узел и это shell-пилюля (eyebrow удалён), кегль вкладки === `ingest-sources-heading` === 24px, `column-gap` 16px (> 8), `margin-top` 0, `nav.top − main.top < 48`; `AdminLayout.jsx:13` `text-2xl`, `:50` `mt-0 … gap-4` |

**Почему не `passed`.** Во-первых, GC-2 не держится в универсальной формулировке (измеримый дефект в самом разделе «Настройка»). Во-вторых, два must_have опираются на гейты, которые по мутациям ревью не падают на реальных регрессиях; рабочий код сегодня верен, но доказательство слабее заявленного, поэтому `partial`, а не `met`. Наконец, двенадцать backstop-пунктов и одно поведенческое утверждение не исполняются ни одним тестом.

## Must-Have Scorecard

| План | Записей | ✓ verified | ✗/partial | ⊘ backstop → human | ⚠️ behavior-unverified |
|---|---|---|---|---|---|
| 25-01 (PIPEUI-01) | 6 | **6** | 0 | 0 | 0 |
| 25-02 (PIPEUI-03/04) | 11 | **9** | 0 | 2 | 0 |
| 25-03 (THEME-02/PIPEUI-02) | 23 | **15** | 0 | 8 | 0 |
| 25-04 (THEME-01) | 11 | **8** | 0 | 2 | 1 |
| 25-05 (gap: роли подписи + граница) | 9 | **8** | 1 partial | 0 | 0 |
| 25-06 (gap: 18 сайтов + тост) | 9 | **8** | 1 partial | 0 | 0 |
| 25-07 (gap: accent-text + field-border) | 9 | **9** | 0 | 0 | 0 |
| **Итого** | **78** | **63** | **2** | **12** | **1** |

### 25-01 — naming tracer (PIPEUI-01)

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | вкладка `admin-tab-pipeline` читается «Настройка», соседняя — «Дайджест» | ✓ | `admin-chrome.spec.js:172-186`; `AdminLayout.jsx:60`, `:68` |
| 2 | sr-only `h1` «Настройка», единственный, `width ≤ 1px` | ✓ | `:187-193`; `AdminLayout.jsx:47` |
| 3 | мобильный `<option>` «Настройка», тексты опций `['Дайджест','Настройка']`, `value` = `/admin/pipeline` | ✓ | `:194-204`; `AdminLayout.jsx:80-81` |
| 4 | `page.url()` оканчивается на `/admin/pipeline`, testid один, `aria-label` цел | ✓ | `:205-212`; `App.jsx:62` |
| 5 | `tests/admin-chrome.spec.js` собирается проектом `web` | ✓ | прогон дал 11 passed; `playwright.config.js` `testMatch` |
| 6 | PIPEUI-01 flagged assumption (статический литерал, входного домена нет) | ✓ | три текстовых ассерта + ассерт неизменного URL — ровно то покрытие, которое план и объявляет |

### 25-02 — хром админки + «Источники» (PIPEUI-03, PIPEUI-04)

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | «Админ» ровно 1 узел и это shell-пилюля; eyebrow нет в DOM | ✓ | `admin-chrome.spec.js:214-240`; в `AdminLayout.jsx` слова «Админ» нет; `AppShell.jsx:102` |
| 2 | кегль вкладки === кегль контентного `h2` === 24px | ✓ | `:242-247`; `AdminLayout.jsx:13` `text-2xl`; `IngestSourcesSection.jsx:171` |
| 3 | `column-gap` === 16px и > 8 | ✓ | `:249-252`; `AdminLayout.jsx:50` `gap-4` |
| 4 | `margin-top` === 0 и `nav.top − main.top < 48` | ✓ | `:254-263`; `AdminLayout.jsx:50` `mt-0` |
| 5 | `ingest-sources-heading` ровно «Источники» | ✓ | `:265-268`; `IngestSourcesSection.jsx:170-173` |
| 6 | `aria-label`, четыре `data-testid`, `mt-6` без изменений | ✓ | `:265-268`; `AdminLayout.jsx:48-50`, `:72-74`, `:84` |
| 7 | 320px: обе подписи вкладок в одну строку в 44px-цели | ⊘ backstop | Human #1 (на < 640px строка скрыта контрактом `sm:flex`) |
| 8 | 320px: мобильный селектор 44px, `paper`, `ink`, без обрезки | ⊘ backstop | Human #2 |
| 9-11 | flagged assumptions PIPEUI-03 (`unclassified`), PIPEUI-04 (`boundary`, `precision`) | ✓ | точное равенство строки и относительные замеры — как план и формулирует |

### 25-03 — семейство токенов и читаемый «Тип» (THEME-02, PIPEUI-02)

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | гейт покрытия токенов зелёный | ✓ | `npm run test:js` 89/0; G-0…G-13 |
| 2 | ровно один `@theme` и один `[data-theme="light"]` | ✓ | G-0; независимый пересчёт 1 / 1 |
| 3 | `#ingest-sources-kind`: тёмная `rgb(203,213,225)`/`rgb(19,25,37)`, светлая `rgb(51,65,85)`/`rgb(255,255,255)`, непрозрачно, ≥ 4.5 | ✓ | e2e `select legible in both themes`; 11.852 / 10.355 |
| 4 | соседние `-id` / `-label` дают ту же пару | ✓ | тот же кейс, цикл по трём локаторам |
| 5 | опции ровно `Канал` / `Плейлист` | ✓ | тот же кейс |
| 6 | `--color-paper` резолвится в рантайме | ✓ | тот же кейс + собранный CSS |
| 7 | ноль `accent-ink`, `bg-ink`, альфы на `bg-paper*` | ✓ | G-5 / G-6; grep 0 / 0 / 0 |
| 8 | контраст семейства, включая `on-solid`/`danger-solid` пол 4.829 | ✓ | G-7; пересчёт: 5.699 / 5.358 / 5.016 / 4.829; `voting-ink` на `voting` 9.309 |
| 9 | алиасы `paper`/`paper-2`/`ink` в обеих темах, `rule`/`muted` — только в тёмной | ✓ | G-8 |
| 10 | пустые поля: непрозрачная `paper`, значение `ink-2`, **край поля** | ✓ (с замещением) | Значение и заливка — e2e; край теперь `border-field-border` (**4.759 / 3.698 ≥ 3:1**), осознанное замещение пункта 25-07 (см. § Замещённые must_have) |
| 11 | ноль источников: заголовок + «Пока нет источников» на `paper`, `ink`/`muted` | ✓ | `IngestSourcesSection.jsx:169-200`; тексты запинены `tests/admin.spec.js` |
| 12 | ошибка загрузки: сообщение **и** действие ≥ 4.5:1 на `paper` в обеих темах | ✓ | e2e `load-error actions…`: сообщение `ink-2` 10.355 / 11.852, действие `accent-text` **5.358 / 7.248** |
| 13-20 | восемь backstop'ов (частичная форма, 200-символьный id, загрузка, строка без label, 20 строк @320, 0/1/20, длинный id, диалог @320) | ⊘ backstop | Human #3…#10 |
| 21-23 | flagged assumptions PIPEUI-02 (`empty`, `encoding`) и THEME-02 (`unclassified`) | ✓ | непрозрачность проверяется до арифметики + точное равенство `rgb(...)`; CSS-контракт закрыт G-0…G-19 |

### 25-04 — тема-независимые подписи (THEME-01)

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | пилюля shell: `rgb(255,255,255)` на `rgb(124,58,237)`, ≥ 4.5 в обеих темах | ✓ | e2e `theme-independent labels in both themes`; 5.699 |
| 2 | `ingest-sources-add`: белая подпись на `rgb(14,116,144)`, ≥ 4.5 | ✓ | там же; 5.358 |
| 3 | `voting`: `rgb(15,23,42)` на `rgb(234,179,8)`, ≥ 4.5 — положительный ассерт | ✓ | там же, обе темы; 9.309; e2e падает, если подпись станет белой (1.918); `ActionButton.jsx:42` `bg-voting text-voting-ink` |
| 4 | ни одна заливка не несёт темо-зависимую подпись (G-9) | ✓ | G-9 / G-9b зелёные; `ActionButton.jsx:11-12`, `:45` только `text-on-solid` |
| 5 | ни один скрайм не использует темо-зависимый токен (G-10) | ✓ | G-10 без carve-out; четыре оверлея на `bg-scrim` |
| 6 | ни один ассерт пилюли не держится на подстроке | ✓ | пять token-exact сайтов; `toHaveClass(/bg-primary/)` — 0 |
| 7 | в полёте подпись сохраняет цвет, меняется только прозрачность | ⚠️ PRESENT_BEHAVIOR_UNVERIFIED | `ActionButton.jsx` `stateChrome.loading = 'cursor-wait opacity-80'`; e2e измеряет только `idle` и `error` → Human #13 |
| 8-9 | 320px: длинная подпись CTA и подпись пилюли без обрезки | ⊘ backstop | Human #11…#12 |
| 10-11 | flagged assumptions THEME-01 (`empty`, `encoding`) | ✓ | непрозрачность проверяется до `contrastRatio`; сравнение точных `rgb(...)` |

### 25-05 — роли подписи и граница поля

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | `--color-success-ink`, `--color-voting-ink-on-tint`, `--color-accent-text` в `@theme static` + отличающиеся light-override | ✓ | `index.css:59-61`, `:182-184`; G-14 |
| 2 | `--color-field-border: #64748B` без light-override | ✓ | `index.css:82`; одна декларация; G-3 (`FLAT`) |
| 3 | G-14 измеряет тинт-композиты ≥ 4.5 на `paper`/`paper-2`/`bg-app` | **partial** | Значения проходят: success 7.801/7.044/8.778 и 6.262/5.795/6.024; voting 9.419/8.473/10.532 и 7.621/7.057/7.326; danger 5.837/5.283/6.407 и 5.665/5.201/5.449. **Но** альфа захардкожена (`STATUS_LABEL_TINTS` `:113-117`), мутация `/15 → /60` гейт не роняет → GAP-25-6 |
| 4 | G-14 измеряет роли на непрозрачных поверхностях | ✓ | accent 7.248/6.550/7.900 и 5.358/4.891/5.121; success-ink 10.098/9.126/11.007 и 7.130/6.509/6.815; danger-ink 6.361/5.749/6.934 и 6.470/5.906/6.184 |
| 5 | G-15: граница поля ≥ 3:1, а `rule` порог не держит | ✓ | 4.759 / 4.344 / 4.548 и 3.698 / 3.342 / 4.030; `rule` 1.485 / 1.425 |
| 6 | `blendOver(colour, base, alpha)` — нормализованный непрозрачный `rgb()` | ✓ | `blendOver('#22C55E','#F8FAFC',0.15)` = `rgb(216, 242, 228)`; alpha 1 → `rgb(34, 197, 94)`; alpha 0 → база; proof-тест G-14 |
| 7 | G-18 появляется в 25-06, G-19 — в 25-07 | ✓ | обе проверки существуют и зелёные |
| 8 | G-14 proof воспроизводит 1.925 и 1.918 | ✓ | пересчёт: 1.925 и 1.918 |
| 9 | гейт односторонний по дереву, `test:js` зелёный | ✓ | `git show 77a8315` — только `index.css`; 89/0 |

### 25-06 — 18 статусных подписей и тост

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | GAP-25-1 закрыт на всех 18 сайтах, каждый сайт принадлежит одному плану | ✓ | 18 вхождений `text-success-ink`/`text-voting-ink-on-tint`/`text-danger-ink` в семи файлах; базовых подписей — 0 |
| 2 | измеренные после правки пары ≥ 4.5 | ✓ | 11.007 / 10.098 / 10.532 / 6.361 / 6.407 / 6.934 (тёмная); 6.815 / 7.130 / 7.326 / 6.470 / 5.449 / 6.184 (светлая) |
| 3 | GAP-25-2: баннер на `text-success-ink`, тост на `border border-rule bg-paper-2 text-ink`, carve-out снят, тост только для ошибок | ✓ | `AdminDigestPage.jsx:770`, `:809`; `setToast` только на `:316`, `:366`; e2e: фон `rgb(241,245,249)`/`rgb(26,34,51)`, текст `rgb(15,23,42)`/`rgb(241,245,249)`, граница `rgb(203,213,225)`/`rgb(42,53,72)` |
| 4 | `test:js` падал до правки и проходит после на G-10 / G-18 / G-16 | ✓ (текущее состояние) | offender-списки пусты, proof'ы воспроизводят нарушителей; исторический RED — коммиты `2f699c3`, `e3fe0e2` |
| 5 | G-18: базовые статус-токены запрещены как текст, `-ink` разрешены; proof | ✓ | proof ловит `'bg-success/15 text-success'` и не ловит `text-success-ink` |
| 6 | G-16: контракт статусных ассертов, тост обязан читать цвета; proof | **partial** | R2 и e2e `failure toast legible` честны (16.296/14.516), но R3 ищет подстроки `backgroundColor`/`borderTopColor` в файле спеки (они уже есть в `styleTriple()`), а R1 не видит `hasText:`/`name` — мутации ревью зелёные → GAP-25-7 |
| 7 | поведенческое доказательство в обеих темах: пилюли, auth-ошибки, баннер, тост | ✓ | четыре e2e-кейса (`:371`, `:419`, `:452`, `:496`); значения совпали |
| 8 | `tests/admin.spec.js` не редактируется и не регрессирует | ✓ | файл не входит в diff 25-05…25-07 |
| 9 | все прогоны зелёные | ✓ | `test:js` 89/0; `admin-chrome` 11/11; `build` exit 0 |

### 25-07 — accent-text и field-border

| # | must_have | Статус | Доказательство |
|---|---|---|---|
| 1 | GAP-25-3: три сайта на `text-accent-text`, сообщение не тронуто | ✓ | `IngestSourcesSection.jsx:186`, `IngestionScheduleSection.jsx:156`, `AdminDigestPage.jsx:993`; e2e читает все три: 5.358 / 7.248 и сообщение 10.355 / 11.852 |
| 2 | GAP-25-4: каждый контрол `border-top-color === rgb(100,116,139)`, ≥ 3.0 | ✓ | G-17 статически на всех 16 (`controlCount >= 16`), e2e — на четырёх реальных; плоский токен делает вычисленное значение тем же у всех |
| 3 | декоративная граница остаётся декоративной (4 точных class-строки) | ✓ | `DECORATIVE_RULE_EDGES` в G-17; e2e: карточка `border-rule`, контраст < 3 |
| 4 | G-17 существует, падает до правки, proof разделяет `<input>` / `<div>` / `field-border` | ✓ | proof'ы зелёные |
| 5 | G-19 существует, `text-accent` — offender, `text-accent-text` — нет; proof | ✓ | `text-accent/80` тоже ловится |
| 6 | WR-03: ровно одна заливка, `secondary` без `bg-transparent` | ✓ | `ActionButton.jsx:30-48`; e2e 11-й кейс: idle `['bg-voting']`, error `['bg-danger-solid']` |
| 7 | WR-04: `gotoAdmin` ждёт `data-theme`, `?? 'dark'` | ✓ | `admin-chrome.spec.js:44-57`; `waitForTimeout` — 0 |
| 8 | залоченный объём байт-идентичен | ✓ | «Источники», «Повторить загрузку», все `data-testid`, оба `aria-label`, `PIPELINE_PATH`/`DIGEST_PATH`/`handleSectionTabClick`, три литерала «Настройка» |
| 9 | три прогона зелёные | ✓ | см. § Метод |

## Замещённые must_have (осознанные, не гэпы)

| Пункт | Исходная формулировка | Действующее состояние | Почему это не гэп |
|---|---|---|---|
| 25-03 #10 | «край `rule`» у пустых контролов | `border-field-border` (`#64748B`) | 25-07 явно закрывает GAP-25-4 и переводит все контролы на boundary-роль; `rule` остаётся декоративной (**1.485**), G-17 запрещает путать роли. Порог ужесточён с 1.485:1 до 4.759:1 |
| 25-03 #12 | «не трогать `text-accent`» (внутреннее противоречие плана) | добавлена роль `--color-accent-text`; `--color-accent` не менялся | 25-05 § Резолюция: подпись получила свою роль, фокус-обводка осталась на базовом акценте |
| THEME-02 | семейство перечисляет `accent-ink` | `--color-accent-ink` не существует; потребители на `text-on-solid` | D-10: токен выведен; G-5 запрещает имя. Оперативная клауза («тест падает на необъявленном используемом токене») выполняется — G-0…G-4 |

## Requirement Coverage

Frontmatter планов объявляет `PIPEUI-01` (25-01), `PIPEUI-03` + `PIPEUI-04` (25-02), `THEME-02` + `PIPEUI-02` (25-03), `THEME-01` (25-04). Объединение — **шесть** ID, байт-идентично `REQUIREMENTS.md` и `ROADMAP.md` § Phase 25. Сирот и необъявленных ID нет.

| Requirement | Источник | Статус | Доказательство |
|---|---|---|---|
| **PIPEUI-01** — раздел «Настройка» на вкладке, sr-only заголовке и мобильном селекте; URL не меняется | 25-01 | ✓ **SATISFIED** | e2e `naming:` — тексты трёх поверхностей + ассерты неизменного URL/testid/`aria-label`; `AdminLayout.jsx:47`, `:68`, `:81`; `App.jsx:62`; `/admin/settings` — 0 |
| **PIPEUI-02** — «Тип» и опции «Канал»/«Плейлист» читаемы в обеих темах, явная поверхность и текст | 25-03 | ✓ **SATISFIED** | e2e `select legible…`: 11.852 / 10.355, непрозрачно, соседние поля идентичны, опции точные |
| **PIPEUI-03** — заголовок блока «Источники», слова «ингеста» нет | 25-02 | ✓ **SATISFIED** | `IngestSourcesSection.jsx:170-173`; e2e `chrome:`; «Источники ингеста» под `web/src` — 0 |
| **PIPEUI-04** — eyebrow удалён, кегль вкладок = `h2`, шире gap, меньше пустоты сверху | 25-02 | ✓ **SATISFIED** | e2e `chrome:`: 1 узел «Админ» (shell), 24px === 24px, gap 16 > 8, `mt-0`, `nav.top − main.top < 48` |
| **THEME-01** — белые подписи на `primary`/`accent`-заливках и активной пилюле; `voting` сохраняет тёмную подпись; ≥ 4.5 | 25-04 | ✓ **SATISFIED** | e2e (3 пары × 2 темы): 5.699 / 5.358 / 9.309; G-9/G-10 пусты; пять token-exact ассертов; `ActionButton.jsx:42` |
| **THEME-02** — семейство объявлено в `@theme` с light-override и тест падает на необъявленном токене | 25-03 (+ гейты 25-04…25-07) | ✓ **SATISFIED** (одно зафиксированное отклонение) | `index.css:39-44` + `:171-176`; плоские роли `:59-82`; G-0…G-19. Отклонение: `accent-ink` выведен (D-10), G-5 его запрещает |

**Сироты:** нет. **Необъявленные ID:** нет.

## Измеренный контраст

Пересчитано `tests/helpers/contrast.js`; тинты — `blendOver(colour, base, alpha)`.

### G-14: подпись на тинте (порог 4.5)

| База | success-ink на `success/15` | voting-ink-on-tint на `voting/20` | danger-ink на `danger/10` |
|---|---|---|---|
| тёмная `paper` | **7.801** | **9.419** | **5.837** |
| тёмная `paper-2` | **7.044** | **8.473** | **5.283** |
| тёмная `bg-app` | **8.778** | **10.532** | **6.407** |
| светлая `paper` | **6.262** | **7.621** | **5.665** |
| светлая `paper-2` | **5.795** | **7.057** | **5.201** |
| светлая `bg-app` | **6.024** | **7.326** | **5.449** |

### G-14: подпись на непрозрачной поверхности (порог 4.5)

| Роль | тёмная `paper` / `paper-2` / `bg-app` | светлая `paper` / `paper-2` / `bg-app` |
|---|---|---|
| `accent-text` | 7.248 / 6.550 / 7.900 | 5.358 / 4.891 / 5.121 |
| `success-ink` | 10.098 / 9.126 / 11.007 | 7.130 / 6.509 / 6.815 |
| `danger-ink` | 6.361 / 5.749 / 6.934 | 6.470 / 5.906 / 6.184 |

### G-15: граница контрола (порог 3.0) против декоративного `rule`

| Роль | тёмная `paper` / `paper-2` / `bg-app` | светлая `paper` / `paper-2` / `bg-app` |
|---|---|---|
| `field-border` `#64748B` | **3.698 / 3.342 / 4.030** | **4.759 / 4.344 / 4.548** |
| `rule` (декор) | 1.425 | 1.485 |

### GAP-25-5: `--color-primary` `#8B5CF6` как подпись — не покрыт ни одной матрицей

| Поверхность | Тема | Ratio |
|---|---|---|
| `bg-app` `#F8FAFC` | светлая | **4.047** |
| `paper` `#FFFFFF` | светлая | **4.234** |
| `bg-surface`/`paper` `#131925` | тёмная | **4.156** |
| `paper-2` `#1A2233` | тёмная | **3.756** |
| `bg-app` `#0B0F17` | тёмная | 4.529 |
| `bg-danger/10` над `bg-app` (`pipeline-config-save-retry`) | светлая | **3.566** |
| `bg-danger/10` над `bg-app` (`pipeline-config-save-retry`) | тёмная | **4.186** |

### Ранее падавшие пары — теперь проходят

| Пара | Было | Стало |
|---|---|---|
| `success`-пилюля как текст на `bg-success/15` | 1.92 | **6.262** (светлая) / **7.801** (тёмная) |
| `voting`-пилюля на `bg-voting/20` | 1.62 | **7.621** / **9.419** |
| панель ошибок конфига на `bg-danger/10` | 3.17 | **5.665** / **5.837** |
| ошибки auth-полей на белой карточке | 3.76 | **6.470** / **6.361** |
| тост `bg-text-primary` + `text-text-primary` | 1.00 | **16.296** / **14.516** |
| ссылка повтора `text-accent` на светлой `paper` | 2.43 | **5.358** |
| край поля `border-rule` на светлой `paper` | 1.485 | **4.759** |

## Data-Flow Trace (Level 4)

| Артефакт | Переменная/токен | Источник | Реальные данные | Статус |
|---|---|---|---|---|
| `web/src/index.css` → компоненты | `--color-paper` … `--color-field-border` | единственный `@theme static` + единственный light-блок | да — e2e читает `getComputedStyle` на живой странице (11.852, 4.759, `rgb(100,116,139)`) | ✓ FLOWING |
| `AdminLayout.jsx` → DOM | «Настройка» | статический JSX-литерал | да — тексты вкладки, `h1`, `<option>` | ✓ FLOWING (статический по природе) |
| `IngestSourcesSection.jsx` → DOM | `loadError`, `data-testid` | `IngestSourcesError` из сервиса, e2e армит `armFailNextLoad` | да — реальный текст ошибки и действие | ✓ FLOWING |
| `AdminDigestPage.jsx` тост | `toast` | `setToast` на путях отказа `:316`, `:366` | да — e2e армит `armFailNextDecision` | ✓ FLOWING |
| `ActionButton.jsx` | `stateFill[state]`, `variantClass` | props `variant`/`state` | да — e2e читает вычисленный фон в idle и error | ✓ FLOWING |

## Key Link Verification

| From | To | Via | Статус |
|---|---|---|---|
| `tests/unit/test_semantic_token_coverage.js` | `web/src/index.css` | `parseBlock('@theme…')` / `parseBlock('[data-theme="light"]')` | ✓ WIRED (89/0) |
| `tests/unit/test_semantic_token_coverage.js` | `tests/helpers/contrast.js` | `require('../helpers/contrast')` — `blendOver` + `contrastRatio` | ✓ WIRED (G-14 proof) |
| `tests/unit/test_semantic_token_coverage.js` | все `.jsx` под `web/src` | G-17 / G-18 / G-19 сканируют `sources()` | ✓ WIRED (anti-vacuum 16) |
| `tests/admin-chrome.spec.js` | `web/src/components/AdminLayout.jsx` | `data-testid` трёх поверхностей + computed style | ✓ WIRED (11/11) |
| `tests/admin-chrome.spec.js` | `web/src/index.css` | `getComputedStyle` + `contrastRatio` | ✓ WIRED |
| `gotoAdmin` | `ThemeToggle.jsx` | `waitForFunction((dataset.theme ?? 'dark') === theme)` | ✓ WIRED (WR-04) |
| `ActionButton.jsx` | `tests/admin-chrome.spec.js` | `bg-voting` / `bg-danger-solid` против вычисленного фона | ✓ WIRED |

## Behavioral Spot-Checks

| Поведение | Команда | Результат | Статус |
|---|---|---|---|
| Все статические гейты и канон | `npm run test:js` | 89 pass / 0 fail | ✓ PASS |
| Наименование, хром, читаемость в обеих темах | `npx playwright test tests/admin-chrome.spec.js --project=web` | 11 passed (53.2 s) | ✓ PASS |
| Сборка | `npm run build` | exit 0 | ✓ PASS |
| Матрица G-14/G-15 | node + `tests/helpers/contrast.js` | совпала с must_have 25-05 до третьего знака | ✓ PASS |
| Пробы | `scripts/**/tests/probe-*.sh` | не найдено ни одного | SKIPPED (проб нет) |

## Probe Execution

Не применимо: план и SUMMARY фазы не объявляют проб, `scripts/**/tests/probe-*.sh` в дереве отсутствует.

## Anti-Patterns Found

| Файл | Паттерн | Severity | Влияние |
|---|---|---|---|
| — | `TBD` / `FIXME` / `XXX` | — | 0 |
| — | `TODO` / `HACK` / «coming soon» / «not implemented» | — | 0 |
| — | Пропущенные/`.todo` тесты в файлах фазы | — | 0; 11 e2e-кейсов и 89 unit-ассертов исполняются |
| — | Пустые реализации (`return null`, `=> {}`) в изменённых компонентах | — | 0 |
| — | Второй `@theme` / второй `[data-theme="light"]` | — | 1 / 1 |
| — | Произвольные цвета (`text-[#…]`, `oklch(`), `!important`, inline-стили цвета | — | 0 (G-12 allow-list пуст) |
| `web/src/pages/AdminPipelineConfigPage.jsx` | `text-primary` как роль подписи на `bg-app` и `bg-danger/10` | ⚠️ Warning → **GAP-25-5** | 3.566…4.529 — ниже 4.5 хотя бы в одной теме |
| `tests/unit/test_semantic_token_coverage.js` | `STATUS_LABEL_TINTS` с захардкоженной альфой | ⚠️ Warning → **GAP-25-6** | Гейт не видит дрейф `/15 → /60` |
| `tests/unit/test_semantic_token_coverage.js` | G-16 R1/R3 проверяют текст файла, а не поведение | ⚠️ Warning → **GAP-25-7** | Гейт не падает на удалении цветовых expect тоста и на альтернации в `hasText:` |
| `web/src/components/TopicBallot.jsx` | `border-border` у `role="radio"` — 1.178 / 1.554 (WR-11) | ℹ️ Info | Единственный визуальный индикатор выбора ниже 3:1; вне must_have фазы (G-17 видит только `input\|select\|textarea`) |
| `web/src/pages/AdminDigestPage.jsx:771` | провал отправки печатается `text-success-ink` (WR-12) | ℹ️ Info | Читаемо, но семантически неверный цвет исходу не противоречит контрастной клаузе |
| `playwright.config.js` / `gotoAdmin` | условный страж темы, `reuseExistingServer` (WR-13) | ℹ️ Info | Риск флейка, не дефект фазы |
| `tests/unit/test_semantic_token_coverage.js` | `console.log` в proof-замерах | ℹ️ Info | Отчёт о коэффициентах при падении; не production |

## Human Verification Required

Ниже — 12 backstop-пунктов и одно поведенческое утверждение. Viewport задавать явно; темы — обе (`data-theme="light"` и отсутствие атрибута = тёмная), моки `VITE_USE_MOCKS=true`.

| # | План | Что сделать | Ожидаемо | Почему человек |
|---|---|---|---|---|
| 1 | 25-02 | `/admin/pipeline`, строка вкладок на ≥ 640px и мобильный селектор на 320px | Подписи вкладок в одну строку в 44px без обрезки; на < 640px строка скрыта и работает `<select>` | backstop; формулировка «на 320px» противоречит `hidden … sm:flex`, автотеста нет |
| 2 | 25-02 | 320px: мобильный `<select>` | 44px, `paper`, `ink`, опция не обрезана | backstop; e2e мерит только цвета/границу на 480px |
| 3 | 25-03 | Частично заполненная форма (тип выбран, id и название пусты) | Все три контрола — непрозрачная `paper`, текст `ink-2`, обе темы | partial backstop |
| 4 | 25-03 | 200-символьный id в `ingest-sources-id` | Скроллится внутри поля, блок не расширяется, CTA не обрезан | long-text backstop |
| 5 | 25-03 | Первичная загрузка в полёте | Нет строк и скелетона; «Источники» и `paper` на месте | loading backstop, инжектора нет |
| 6 | 25-03 | Строка только с id | Переключатель и действия строки видимы и читаемы | partial backstop |
| 7 | 25-03 | 20 строк на 320px | Вертикальное удлинение, без обрезки и горизонтальной прокрутки | overflow backstop |
| 8 | 25-03 | 0 / 1 / 20 строк | Одинаковая `paper-2` и ритм 8px; без singular/plural | zero-one-many backstop |
| 9 | 25-03 | Длинный id канала/плейлиста | Перенос/усечение внутри строки, действия во вьюпорте, ≥ 4.5:1 | long-text backstop |
| 10 | 25-03 | 320px: диалог несохранённых изменений | Оба действия полностью видны, без горизонтального переполнения | overflow backstop |
| 11 | 25-04 | 320px: «Уйти без сохранения» | Переносится в 44px-цели без обрезки | overflow backstop |
| 12 | 25-04 | 320px: активная пилюля навигации | Полностью внутри пилюли, белая на `primary-solid` | overflow backstop |
| 13 | 25-04 | `/voting`, выбрать радио, нажать `confirm-vote`, прочитать пару в `loading` | Цвет подписи не меняется, только `opacity` | поведение в полёте не исполняется ни одним тестом |

## Gaps Summary

Goal-backward картина: нaming, хром, семейство токенов, 18 статусных подписей, тост, accent-ссылки и граница поля — **в дереве, измерены и закреплены тестами**. Пять success criteria ROADMAP выполнены; все шесть требований `SATISFIED`; блокирующих anti-pattern нет.

Открыты три пункта, каждый — про доказанность, а не про сломанную функцию:

1. **GAP-25-5 (GC-2, измеримый дефект).** `--color-primary` как подпись не проходит 4.5:1 в большинстве баз (3.566…4.529), включая две кнопки раздела «Настройка». Ни один план фазы этого не касался, поэтому это гэп *цели*, а не проваленная задача плана.
2. **GAP-25-6 (25-05 #3, `partial`).** Рабочие пары `-ink`/тинт проходят (5.201…10.532), но G-14 измеряет захардкоженную альфу 0.15 вместо реального класса — мутация `/60` не роняет гейт.
3. **GAP-25-7 (25-06 #6, `partial`).** Тост сегодня действительно читается по цвету в e2e (16.296/14.516), но R3 и R1 гейта G-16 не могут упасть на реальных регрессиях.

Остаточные замечания ревью `WR-11` (граница радиокнопки 1.178/1.554), `WR-12` (провал отправки зелёным), `WR-13` (стабильность харнесса) и `IN-01…IN-05` не относятся к must_have фазы и на вердикт не влияют; `WR-11` стоит взять в ближайшую UI-фазу — это тот же класс дефекта, что закрывал 25-07.

---

_Verified: 2026-10-21T20:56:00Z_
_Verifier: Claude (gsd-verifier)_
