# Phase 25: Admin «Настройка» — naming, readable surfaces, token repair - Context

**Gathered:** 2026-10-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Админ, открывающий раздел пайплайна, видит его названным «Настройка», каждое поле и каждая подпись читаемы в обеих темах, а хром совпадает с остальным продуктом.

Фаза собирает шесть требований — `PIPEUI-01`, `PIPEUI-02`, `PIPEUI-03`, `PIPEUI-04`, `THEME-01`, `THEME-02` — и это **починка уже существующих дефектов**, а не новая функциональность. Ничего не добавляется: ни маршрутов, ни полей, ни панелей.

**In scope (зафиксировано ROADMAP.md, не переобсуждается):**
- Naming: три поверхности «Пайплайн» в `web/src/components/AdminLayout.jsx` (sr-only `h1` :49, вкладка :70, мобильный `<option>` :82) → «Настройка»; `/admin/pipeline`, `PIPELINE_PATH`, `data-testid="admin-tab-pipeline"` и wiring guard'а остаются байт-в-байт.
- `web/src/components/IngestSourcesSection.jsx:171` «Источники ингеста» → «Источники».
- Объявление отсутствующего семейства токенов `paper` / `paper-2` / `ink` / `ink-2` / `muted` / `rule` в `web/src/index.css` — причина нечитаемого `<select>` «Тип» (Tailwind v4 молча не генерирует утилиту для неизвестного токена).
- Chrome 999.2: убрать «Админ»-надпись, кегль вкладок до масштаба контентного заголовка, шире gap, меньше пустоты сверху.

**Out of scope:**
- `/admin/settings`, любой новый маршрут, breadcrumbs.
- Ре-тема читательской поверхности (`bg-app` / `text-primary` остаются как есть).
- Белая подпись на жёлтом `voting`-заливке (запрещено в ROADMAP).
- Мобильный полишинг админки сверх `<select>`-бэкстопа.
- Возврат к `999.4` (объединение Approve + Mark ready).

</domain>

<decisions>
## Implementation Decisions

Обсуждена зона **THEME-01** (белые подписи против арифметики контраста). Остальные зоны осознанно отданы на усмотрение планировщика — см. `Claude's Discretion`.

### Измеренная картина до правки (baseline, обязательна как вход для RED)

Подписи на заливках сегодня заданы `text-text-primary`, который **переворачивается вместе с темой** (`#F1F5F9` в тёмной, `#0F172A` в светлой). Замеренный контраст при пороге 4.5:1:

| Заливка | Значение | Тёмная тема (`#F1F5F9`) | Светлая тема (`#0F172A`) |
|---|---|---|---|
| `bg-primary` | `#8B5CF6` | **3.87** ✗ | **4.22** ✗ |
| `bg-accent` | `#06B6D4` | **2.22** ✗ | 7.35 ✓ |
| `bg-voting` | `#EAB308` | **1.75** ✗ | 9.31 ✓ |
| `bg-success` | `#22C55E` | **2.08** ✗ | 7.83 ✓ |
| `bg-danger` | `#EF4444` | **3.44** ✗ | 4.74 ✓ |

Следствия, которые меняют постановку задачи:

- **D-01:** Дефект шире, чем нечитаемый `<select>`: в тёмной теме проваливают контраст **все пять** заливок, а не только поле «Тип». Фаза не может быть закрыта как «починили select». — **Reversibility:** reversible.

- **D-02:** Белая подпись на текущих значениях заливок **арифметически невозможна**: лучший белый — `primary` 4.23 (`#8B5CF6`), затем `danger` 3.76, `accent` 2.43, `success` 2.28, `voting` 1.92. Критерий 4 ROADMAP выполним только если заливки потемнеют. — **Reversibility:** reversible.

- **D-03:** `text-bg-app` на `voting` — скрытая ловушка: в тёмной теме `#0B0F17` на `#EAB308` даёт 10.0 ✓, в светлой `bg-app` = `#F8FAFC` даёт **1.83** ✗. «Тёмная подпись на жёлтом» сегодня работает только в одной теме. — **Reversibility:** reversible.

### Охват правила

- **D-04:** Правило «постоянная подпись + контраст ≥ 4.5:1 в обеих темах» распространяется на **все заливки, кроме `voting`**: `primary`, `accent`, `success`, `danger`. `voting` остаётся жёлтым `#EAB308` с постоянной тёмной подписью — это и есть зафиксированное исключение ROADMAP, и оно пинится положительной проверкой, а не пропуском. — **Reversibility:** costly — пересмотр охвата снова трогает каждую залитую поверхность (`AppShell`, `ActionButton`, `LoginPage`, `RegisterPage`, `ServiceUnavailable`, `KnowledgePage`, `AdminDigestPage`) и заново открывает половину бага.

### Форма токенов

- **D-05:** Потемневшие значения вводятся **отдельными `-solid` токенами**, а не правкой базовых `--color-primary` / `--color-accent`. База `primary` используется как текст, бордер, фокус-ринг и тинт в 24 файлах, включая читательские `MaterialPage` (11), `RazborPage` (11), `IssueToc`, `ArchivePage`, `KnowledgePage` — потемнение базы перекрасило бы читательскую поверхность, что ROADMAP прямо запрещает. — **Reversibility:** costly — переименование токенов позже затрагивает ~15 call sites в 10 файлах плюс гейт покрытия.

- **D-06:** Подпись на заливке — один токен `--color-on-solid`, значение строго **`#FFFFFF`**, не `#F1F5F9`. Причина: `#F1F5F9` на `danger-solid #DC2626` даёт **4.41** и проваливает порог 4.5; чистый белый даёт 4.83. — **Reversibility:** reversible.

- **D-07:** Подпись на `voting` — константа `--color-voting-ink: #0F172A` (9.31 на `#EAB308`), **не** `text-bg-app`. Токен темы здесь недопустим: `bg-app` в светлой теме даёт 1.83 (D-03). — **Reversibility:** reversible.

- **D-08:** Новые токены объявляются в `@theme static` (`--color-primary-solid`, `--color-accent-solid`, `--color-success-solid`, `--color-danger-solid`, `--color-on-solid`, `--color-voting-ink`) с **одинаковыми значениями в обеих темах**, поэтому `[data-theme="light"]`-override для них не заводится. Гейт критерия 3 требует light-override только от токенов, чьё значение зависит от темы. — **Reversibility:** reversible.

### Значения

- **D-09:** Минимально-проходной набор (наименьший визуальный сдвиг; переиспользует существующий `primary-hover`):

  | Токен | Значение | Белый | `#F1F5F9` |
  |---|---|---|---|
  | `--color-primary-solid` | `#7C3AED` | 5.70 ✓ | 5.20 ✓ |
  | `--color-accent-solid` | `#0E7490` | 5.36 ✓ | 4.89 ✓ |
  | `--color-success-solid` | `#15803D` | 5.02 ✓ | 4.58 ✓ |
  | `--color-danger-solid` | `#DC2626` | **4.83** ✓ | 4.41 ✗ |
  | `--color-on-solid` | `#FFFFFF` | — | — |
  | `--color-voting-ink` | `#0F172A` | — | 9.31 на `#EAB308` ✓ |

  Худший случай набора — `danger-solid` 4.83; любой будущий сдвиг значений обязан этот запас сохранить. — **Reversibility:** reversible (одна строка CSS на токен), но любое потемнение ниже проходит через гейт контраста.

### `accent-ink`

- **D-10:** `--color-accent-ink` **не объявляется** и вычищается из трёх мест, где он сейчас инертен: `web/src/components/UnsavedChangesDialog.jsx:53`, `web/src/components/IngestSourcesSection.jsx:308`, `web/src/pages/AdminPipelineConfigPage.jsx:305`. Все три — заливки `bg-accent`, они переезжают на `bg-accent-solid text-on-solid`. Это **осознанно перекрывает** строку ROADMAP «declaring the family also repairs the currently inert `accent-ink` labels»: после D-04/D-05 у `accent-ink` не остаётся ни одного потребителя, а мёртвый объявленный токен — ровно тот класс дефекта, который фаза и убирает. — **Reversibility:** reversible — вернуть токен и три call site локально.

### Обязательные миграции подписей

- **D-11:** Каждая залитая поверхность расстаётся с темозависимой подписью. Полный список (все проверены в коде):

  - `bg-primary` → `bg-primary-solid text-on-solid`: `web/src/components/AppShell.jsx:14` (активный нав-пилл, ветка `isActive`), `web/src/components/ActionButton.jsx:21`, `web/src/pages/LoginPage.jsx:126` и `:198`, `web/src/pages/RegisterPage.jsx:107` и `:210`, `web/src/components/ServiceUnavailable.jsx:38`, `web/src/pages/KnowledgePage.jsx:278`.
  - `bg-accent` → `bg-accent-solid text-on-solid`: `web/src/components/UnsavedChangesDialog.jsx:53`, `web/src/components/IngestSourcesSection.jsx:308`, `web/src/pages/AdminPipelineConfigPage.jsx:305`.
  - `bg-success` → `bg-success-solid text-on-solid`: `web/src/pages/AdminDigestPage.jsx:794` и `:919`, `web/src/components/ActionButton.jsx:5`.
  - `bg-danger` → `bg-danger-solid text-on-solid`: `web/src/components/ActionButton.jsx:4`.
  - `bg-voting` → `bg-voting text-voting-ink`: `web/src/components/ActionButton.jsx:18`.

  Не трогаются: заливки без текста — `TopicBallot.jsx:26` (`border-primary bg-primary` — радиокружок), `VotingPage.jsx:448` (`bg-voting` — полоса прогресса), тинты `EditorialCallout.jsx:10` (`bg-primary/15`). — **Reversibility:** reversible.

- **D-12:** Тинтованные чипы **вне охвата THEME-01** — у них нет заливки, текст лежит на полупрозрачной подложке: `AdminDigestPage.jsx:717-718` (`bg-success/15 text-success` / `bg-voting/20 text-voting`), `EditorialCallout.jsx:10`. Критерий 4 их не называет; отдельное решение по ним в этой фазе не принимается. — **Reversibility:** reversible.

### Claude's Discretion

Пользователь обсудил только зону THEME-01. Три зоны осознанно не обсуждались — планировщик решает их сам в рамках констрейнтов ниже, **не переспрашивая**:

1. **Значения семейства `paper` / `paper-2` / `ink` / `ink-2` / `muted` / `rule`** (PIPEUI-02 / THEME-02). Констрейнты: объявление живёт в `web/src/index.css`; тёмные значения — в `@theme static`, светлые — override'ами под `[data-theme="light"]`; никакого по-компонентного хардкода цветов, никаких `!important` и inline-стилей; `ink` обязан быть светлым-на-тёмном в тёмной теме и тёмным-на-светлом в светлой (это подпись основного текста). Отдельно решить судьбу `bg-ink/40` скрайма (`UnsavedChangesDialog.jsx:26`) и полупрозрачных подложек `bg-paper-2/40` — сейчас они инертны, после объявления станут видимыми.
2. **Числа chrome 999.2** (PIPEUI-04). Констрейнты: «Админ»-надпись исчезает из DOM; кегль вкладок равен масштабу контентного `h2` (не `text-3xl`); gap вкладок шире текущего `gap-2`; пустота над строкой вкладок меньше текущей. Абсолютные значения выбираются по канону типографики, проверяются относительными ассертами критерия 5. Отдельно решить, сохраняется ли sr-only `h1` (IN-01 из Phase 22) после исчезновения видимой «Админ»-надписи.
3. **Объём и место гейта покрытия токенов** (критерий 3). Констрейнты: гейт обязан падать **до** правки `index.css` по ожидаемой причине; он покрывает `paper`, `paper-2`, `ink`, `ink-2`, `muted`, `rule` и требует light-override для токенов, чьё значение зависит от темы; гейт читает `web/src/index.css`, а не `design-frontend/styles/tokens.css`. Форма (node-тест по образцу `test_concept2_canon.js` против Playwright computed-style) — на усмотрение планировщика; помнить, что причина исходного бага именно в том, что утилита не долетела до DOM, поэтому вычисленный стиль как минимум на `select` «Тип» всё равно нужен (критерий 2).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Scope and requirements
- `.planning/ROADMAP.md` § Phase 25 — цель, шесть требований, locked scope facts, пять критериев успеха с указанием формы доказательства.
- `.planning/ROADMAP.md` § Execution notes (v1.4) — порядок фаз, запрет на расширение, операционная засада с Vite на `:5174`.
- `.planning/REQUIREMENTS.md` — `PIPEUI-01…04`, `THEME-01`, `THEME-02`.
- `.planning/STATE.md` § Blockers/Concerns — Vite dev-server flakiness и `VITE_USE_MOCKS=false` как источники массовых ложных падений.

### Design contract
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` § Color — откуда пришла палитра `paper` / `paper-2` / `rule` / `accent` (OKLCH, светлая «бумажная» схема); § Typography; § Component contract для редактора. **Внимание:** значения `--color-accent` в UI-SPEC (oklch(52% 0.13 278), фиолетовый) не совпадают с продакшн `#06B6D4` (циан) — продакшн прав, спека устарела.
- `.planning/milestones/v1.2-phases/16-pipe-01-mvp-config-ui/16-UI-SPEC.md` § A-2 — обновлён Phase 22 (вкладки «Дайджест | Пайплайн» → здесь переименовываются в «Дайджест | Настройка»).
- `.planning/milestones/v1.3-phases/22-admin-nav-grouping/22-CONTEXT.md` — D-05…D-08 (underline-вкладки, замена H1, кегль активной вкладки `text-3xl font-semibold`) — **переопределяется** по кеглю и по метке см. `Claude's Discretion` / PIPEUI-01.

### Token canon и его тесты
- `web/src/index.css` — единственное место, где живут `@theme static` и `[data-theme="light"]`; здесь объявляется семейство (PIPEUI-02/THEME-02) и `-solid`-токены (D-08).
- `design-frontend/styles/tokens.css` — канон Concept 2. **Семейства `paper` / `ink` / `rule` / `accent-ink` в нём нет** (только `--color-bg-muted` из пересечения), поэтому добавлять их в канон не требуется и счётчики канона не двигаются.
- `tests/unit/test_concept2_canon.js` — контракт канона: `canonDark.size === 51`, `canonLight.size === 13`, «каждый тёмный токен канона обязан присутствовать в `@theme`», байт-идентичность значений. Проверка идёт **канон → продакшн**, поэтому добавление новых токенов в `@theme` её не ломает.
- `tests/unit/test_design_typography.js` + `tests/unit/helpers/cssRules.js` — готовый паттерн node-теста, читающего CSS и парсящего правила; образец для гейта критерия 3.

### Код, который меняется
- `web/src/components/AdminLayout.jsx` — три поверхности «Пайплайн», «Админ»-надпись (`:41`), `tabClass` (`:11-17`), `gap-2` (`:52`), `mt-2` / `mt-6`.
- `web/src/components/IngestSourcesSection.jsx:163-176` — заголовок «Источники ингеста», `mt-6 mb-6` секции; `:268-276` — `<select>` «Тип» с `bg-paper text-ink-2`.
- `web/src/components/AppShell.jsx:11-15` — `linkClass`, активный нав-пилл `bg-primary text-text-primary`.
- `web/src/components/ActionButton.jsx:1-24` — `stateClass` и `variantClass`, все заливки.
- `web/src/components/UnsavedChangesDialog.jsx` — кнопка `bg-accent text-accent-ink` (`:53`), скрайм `bg-ink/40` (`:26`).
- `web/src/pages/AdminPipelineConfigPage.jsx`, `web/src/components/IngestionScheduleSection.jsx`, `web/src/pages/MaterialPage.jsx:187` — остальные потребители семейства.

### Тесты, которые придётся амендить
- `tests/admin.spec.js:139,151,164-165,274,439,461,1754-1764` — ассерты на текст «Пайплайн» в трёх местах; после переименования становятся RED'ом, затем амендятся на «Настройка». `data-testid="admin-tab-pipeline"` остаётся.
- `tests/admin.spec.js` — существующие ассерты на `bg-primary` / computed style нав-пилла, если такие есть; проверить перед правкой.

### Rules
- `.cursor/rules/tdd.mdc`, `AGENTS.md` — RED-first, без production-кода до падающего теста.
- `.cursor/rules/architecture.mdc` — фаза чисто фронтендовая (`web/`); API-слой не затрагивается.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Готовый паттерн CSS-гейта:** `tests/unit/test_design_typography.js` + `tests/unit/helpers/cssRules.js` (`parseRules`) — node-тест читает CSS, парсит правила и ассертит токены. Раннер `npm run test:js` (`scripts/run-unit-js.cjs`). Это дешёвый дом для гейта покрытия токенов (критерий 3).
- **Канон-тест уже умеет парсить `@theme` и `[data-theme="light"]`** (`parseBlock`) — ту же функцию можно переиспользовать, чтобы не писать второй парсер.
- **`@theme static`** уже применяется в `index.css` именно для токенов без потребителей — комментарий в файле объясняет, почему `static`: токен обязан существовать в `:root` в рантайме.
- **Tailwind v4 без конфиг-файла** — единственный источник истины по токенам это `@theme` в `web/src/index.css`.

### Established Patterns
- Утилиты собираются массивами строк + `.join(' ')` в `ActionButton.jsx`, `AppShell.jsx` (`linkClass`) — миграция подписи это замена строки в массиве, не рефакторинг компонента.
- Состояния интерактивных элементов — через `data-state` (`ActionButton`), а не через класс-переключатели.
- Тестовая пирамида: node-тесты (`npm run test:js`) для CSS/контрактов, Playwright (`tests/*.spec.js`) для DOM и computed style. Тема переключается атрибутом `[data-theme="light"]` на `<html>` (`ThemeToggle.jsx`), localStorage-ключ `digest-cds-theme` — значит Playwright может выставить тему до загрузки страницы.
- Скрипты Playwright-проектов: `test:web` (Vite `127.0.0.1:5174`), `test:design`.

### Integration Points
- `web/src/index.css` `@theme static` — сюда ложатся `-solid`-токены и (по решению планировщика) семейство `paper`/`ink`/`rule`.
- `web/src/components/AppShell.jsx` — активный нав-пилл читают и `NavLink`, и админский `Link` через `linkClass({ isActive })`; правка одна на оба.
- `tests/admin.spec.js` — единственная спека, которая уже знает про «Пайплайн» в трёх местах.

### Hazards
- **`bg-ink/40` скрайм `UnsavedChangesDialog.jsx:26`** — после объявления семейства `ink` станет реальным цветом. Если `ink` окажется светлым (семантика `text-primary`), скрайм превратится в **белую** плёнку 40 % в тёмной теме. Решение по значениям семейства не принималось (см. `Claude's Discretion`) — планировщик обязан это разрешить и покрыть тестом.
- **`bg-paper-2/40`** подложки (`IngestSourcesSection.jsx:219,264`) — та же зависимость от значения.
- **`MaterialPage.jsx:187`** — читательский callout использует `border-rule bg-paper-2 text-ink`, то есть объявление семейства изменит и читательскую поверхность, хотя ROADMAP запрещает её ре-тему. Это не «ре-тема» (сейчас утилиты инертны и ничего не красят), но факт изменения видимого читателю — зафиксировать в плане явно.

</code_context>

<specifics>
## Specific Ideas

- Контраст считается по WCAG 2.x relative luminance, порог **4.5:1** для обычного текста; замеры приведены в D-01…D-03 и D-09 и служат входными данными для тестов, а не украшением.
- «Постоянная подпись» означает: цвет подписи **не зависит** от темы. Любая подпись, выраженная через тему-зависимый токен (`text-primary`, `text-bg-app`, `text-secondary`), считается дефектом в этой фазе.
- Исключение `voting` пинится **положительной** проверкой («жёлтая заливка несёт тёмную подпись и держит ≥ 4.5»), а не отсутствием проверки — это требование ROADMAP сформулировано как «pinned as a positive assertion (not an omission)».
- Значение `#7C3AED` уже существует в проекте как `--color-primary-hover`; `primary-solid` его переиспользует — новый оттенок фиолетового в палитру не вводится.
- Значения `accent-solid #0E7490`, `success-solid #15803D`, `danger-solid #DC2626` не выведены из канона (в каноне таких токенов нет) — это новые значения, но они не меняют `text-accent` / `border-danger` и прочие текстовые роли.

</specifics>

<deferred>
## Deferred Ideas

- **Тинтованные чипы и подложки** (`bg-success/15 text-success`, `bg-voting/20 text-voting`, `bg-primary/15`) — контраст текста на полупрозрачной подложке не входит в критерий 4; отдельная проверка, если появится требование.
- **`bg-ink/40` скрайм модалки** — зависит от значения `ink` из необсуждённой зоны 1; если планировщик выберет светлый `ink`, скрайм потребует отдельного решения (например `bg-black/40` или `bg-app/60`). Возможный кандидат в отдельную фазу, если решение окажется вне фазы 25.
- **Ре-тема читательской поверхности на новое семейство** — осознанно вне фазы (ROADMAP).
- **Обновление `16-UI-SPEC` § Color** под продакшн-значения (`accent` = `#06B6D4`, а не OKLCH-фиолетовый) — документ устарел, но его правка не требуется критериями фазы.

</deferred>

---

*Phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair*
*Context gathered: 2026-10-21*
