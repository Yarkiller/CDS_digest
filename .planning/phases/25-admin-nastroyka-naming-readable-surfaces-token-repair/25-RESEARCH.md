# Phase 25: Admin «Настройка» — naming, readable surfaces, token repair - Research

**Researched:** 2026-10-21
**Domain:** Tailwind CSS v4 CSS-first токены (`@theme static` + `[data-theme="light"]`), WCAG 2.x контраст, Playwright computed-style доказательства, `node:test` CSS-гейт
**Confidence:** HIGH

---

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

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

- **D-04:** Правило «постоянная подпись + контраст ≥ 4.5:1 в обеих темах» распространяется на **все заливки, кроме `voting`**: `primary`, `accent`, `success`, `danger`. `voting` остаётся жёлтым `#EAB308` с постоянной тёмной подписью — это и есть зафиксированное исключение ROADMAP, и оно пинится положительной проверкой, а не пропуском. — **Reversibility:** costly.
- **D-05:** Потемневшие значения вводятся **отдельными `-solid` токенами**, а не правкой базовых `--color-primary` / `--color-accent`. База `primary` используется как текст, бордер, фокус-ринг и тинт в 24 файлах, включая читательские `MaterialPage` (11), `RazborPage` (11), `IssueToc`, `ArchivePage`, `KnowledgePage` — потемнение базы перекрасило бы читательскую поверхность, что ROADMAP прямо запрещает. — **Reversibility:** costly.
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

- **D-10:** `--color-accent-ink` **не объявляется** и вычищается из трёх мест, где он сейчас инертен: `web/src/components/UnsavedChangesDialog.jsx:53`, `web/src/components/IngestSourcesSection.jsx:308`, `web/src/pages/AdminPipelineConfigPage.jsx:305`. Все три — заливки `bg-accent`, они переезжают на `bg-accent-solid text-on-solid`. Это **осознанно перекрывает** строку ROADMAP «declaring the family also repairs the currently inert `accent-ink` labels»: после D-04/D-05 у `accent-ink` не остаётся ни одного потребителя, а мёртвый объявленный токен — ровно тот класс дефекта, который фаза и убирает. — **Reversibility:** reversible.

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

### Deferred Ideas (OUT OF SCOPE)

- **Тинтованные чипы и подложки** (`bg-success/15 text-success`, `bg-voting/20 text-voting`, `bg-primary/15`) — контраст текста на полупрозрачной подложке не входит в критерий 4; отдельная проверка, если появится требование.
- **`bg-ink/40` скрайм модалки** — зависит от значения `ink` из необсуждённой зоны 1; если планировщик выберет светлый `ink`, скрайм потребует отдельного решения (например `bg-black/40` или `bg-app/60`). Возможный кандидат в отдельную фазу, если решение окажется вне фазы 25.
- **Ре-тема читательской поверхности на новое семейство** — осознанно вне фазы (ROADMAP).
- **Обновление `16-UI-SPEC` § Color** под продакшн-значения (`accent` = `#06B6D4`, а не OKLCH-фиолетовый) — документ устарел, но его правка не требуется критериями фазы.

</user_constraints>

---

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PIPEUI-01 | Раздел пайплайна называется «Настройка» во всех трёх поверхностях, URL `/admin/pipeline` не меняется | Три поверхности локализованы с точными строками (§ Change Inventory); tab/select/sr-only h1 проверены замером; URL и `data-testid` не затрагиваются |
| PIPEUI-02 | `<select>` «Тип» и опции «Канал»/«Плейлист» читаемы в обеих темах, явная поверхность вместо UA-вида | Замер до правки: `background-color: rgba(0, 0, 0, 0)`, `color` наследуется — § Current State; механика `@theme static` + `[data-theme="light"]` подтверждена сборкой |
| PIPEUI-03 | Заголовок блока источников читается «Источники» | `IngestSourcesSection.jsx:169-173` + существующий ассерт `tests/admin.spec.js:1834` (`"Источники ингеста"`) — точная строка и место правки |
| PIPEUI-04 | «Админ»-надпись убрана, кегль вкладок равен контентному `h2`, gap шире, пустота сверху меньше | Замер baseline: `tabFontSize 30px`, `headingFontSize 24px`, `navGap 8px`, `nav.top − main.top = 64`; целевые значения и относительные ассерты — § Validation Architecture |
| THEME-01 | В светлой теме подписи на заливках и активном нав-пилле белые; жёлтая `voting` сохраняет тёмную подпись | Замер до правки: пилл `rgb(15,23,42)` на `rgb(139,92,246)` (4.22), `voting` `rgb(248,250,252)` на `rgb(234,179,8)` (1.83) — оба проваливаются, оба становятся GREEN только после `-solid` |
| THEME-02 | Семейство `paper`/`paper-2`/`ink`/`ink-2`/`muted`/`rule`/`accent-ink` объявлено в `@theme` с light-override'ами, и тест падает при необъявленном используемом токене | Гейт G-1…G-8 (§ Test Harness), полный инвентарь потребителей (только 7 файлов), подтверждённое отсутствие токенов в собранном CSS |

</phase_requirements>

---

## Summary

Фаза — **починка, а не функциональность**. Всё, что нужно сделать, уже описано в `25-CONTEXT.md` (D-01…D-12) и `25-UI-SPEC.md`; исследование подтвердило каждое число, каждую строку кода и каждую механику, на которые эти два документа опираются, и нашло четыре расхождения, которые иначе стоили бы исполнителю цикла RED→GREEN.

Первое: **новый Playwright-спек `admin-chrome.spec.js` сегодня не запускается вообще**. `playwright.config.js` фильтрует файлы по `testMatch: /(web-app|auth|knowledge|razbory|admin)\.spec\.js/`, и `admin-chrome.spec.js` не попадает ни в один проект — прогон `--list` даёт «148 tests in 5 files» без него. Без правки этого конфига критерий 1, 2, 4 и 5 не имеют RED'а: тест молча не существует.

Второе: **корень нечитаемого `<select>` — `background-color: rgba(0, 0, 0, 0)`**, а не «UA-белое поле». Chromium + Tailwind preflight даёт прозрачный фон и унаследованный цвет, поэтому проверка «фон не прозрачный» — единственная не вакуумная форма ассерта; «фон не `rgb(255,255,255)`» прошла бы на текущем дереве. Замерено: и `#ingest-sources-kind`, и оба соседних инпута дают пару `rgba(0,0,0,0)` / `rgb(241,245,249)` в тёмной и `rgba(0,0,0,0)` / `rgb(15,23,42)` в светлой.

Третье: **объявление семейства — это `@theme static` + существующий блок `[data-theme="light"]` внутри `@layer base`**, и это работает именно из-за порядка слоёв: собранный CSS — `@layer theme{…}` → `@layer base{…}` → `@layer utilities{…}`, поэтому `[data-theme="light"]` из `base` перебивает `:root` из `theme`. Второй блок `@theme` или второй `[data-theme="light"]` создавать нельзя: `parseBlock` в `test_concept2_canon.js` читает только первое вхождение, и гейт ослепнет.

Четвёртое: **`tests/admin.spec.js:1834` уже пинит `"Источники ингеста"`** — этой строки нет в таблице амендментов UI-SPEC; без неё PIPEUI-03 останется красным после «зелёного» гейта.

**Primary recommendation:** писать два новых теста (node-гейт `tests/unit/test_semantic_token_coverage.js` + `tests/admin-chrome.spec.js`) до любой правки CSS/JSX, первым делом расширив `testMatch` в `playwright.config.js`, затем — объявление токенов в `web/src/index.css`, затем `AdminLayout` chrome, затем миграции `-solid`/`scrim`/`paper-2`, затем амендменты `admin.spec.js`.

---

## Project Constraints (from .cursor/rules/)

| Источник | Директива | Как влияет на план |
|---|---|---|
| `.cursor/rules/tdd.mdc` | `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`. RED → минимальный прод-код → полный прогон → рефактор только на зелёном. Исключения (конфиг, сгенерированное, прототипы) — только с явным согласованием | Гейт и `admin-chrome.spec.js` обязаны существовать и падать по ожидаемой причине **до** правки `index.css`; правка `playwright.config.js` — конфиг, попадает под разрешённое исключение |
| `AGENTS.md` | Тот же TDD-цикл, повторённый как обязательный | Амендменты `admin.spec.js` — часть RED-шага, не «после факта» |
| `.cursor/rules/architecture.mdc` | Границы модулей, `web/src/services/` как единственный канал к API, бизнес-логика не в компонентах, зависимости внутрь | Фаза не касается backend/`supabase-integration`; ни один файл `services/` не редактируется; правки — только className-строки и CSS-токены |
| `.cursor/rules/context7.mdc` | Документация библиотек — через Context7 | `@theme static` и семантика overrides подтверждены через `/websites/tailwindcss` (§ Sources) |
| `.planning/config.json` | `response_language: russian` | Проза по-русски, идентификаторы/пути/заголовки — английский |

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|---|---|---|---|
| Переименование раздела (PIPEUI-01, PIPEUI-03) | Browser / Client (React-компонент) | — | Это литерал в JSX; маршрут и guard не участвуют |
| Объявление токенов (THEME-02, PIPEUI-02) | CSS delivery (Tailwind v4 build → browser cascade) | — | Токен существует только если он в `@theme`; никакой JS-слой темы не нужен |
| Резолв темо-зависимого цвета | Browser (каскад слоёв) | — | Разрешается кастомным свойством, а не классом-переключателем |
| Тема-независимые подписи на заливках (THEME-01) | CSS delivery (значения токенов) | Browser / Client (замена className) | Значение обязано быть одинаковым в обеих темах; компонент лишь перестаёт использовать темо-зависимый токен |
| Chrome geometry (PIPEUI-04) | Browser / Client (className + Tailwind scale) | — | `text-2xl` / `gap-4` / `mt-0` — утилиты, не значения в CSS-файле |
| Доказательство контраста | Test tier (`node:test` для статических значений) | Test tier (Playwright `getComputedStyle`) | Значения в CSS доказываются арифметикой; достижение утилиты до DOM — только computed style |
| Переключение темы в тестах | Browser (атрибут `data-theme` на `<html>` + `localStorage`) | — | Контракт `ThemeToggle`; тест обязан выставить его до первой загрузки |

**Ни один capability не принадлежит API-тиру.** Фаза не делает ни одного сетевого вызова и не меняет ни одного контракта бэкенда.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---|---|---|---|
| `tailwindcss` | `4.3.3` (установлен; `web/package.json` `^4.3.3`) | CSS-first дизайн-токены и утилиты | Единственный источник истины по токенам — `@theme` в `web/src/index.css`; конфиг-файла нет |
| `@tailwindcss/vite` | `4.3.3` | Vite-плагин сборки CSS | Уже в `web/vite.config.js`; менять не нужно |
| `vite` | `8.2.2` | Dev/build | Dev-сервер Playwright-проекта `web` на `127.0.0.1:5174` |
| `react` / `react-dom` / `react-router-dom` | `19.2.8` / `19.2.8` / `7.18.3` | UI и маршруты | `AdminLayout` — pathless layout; маршруты не меняются |
| `@playwright/test` | `1.62.1` | DOM и computed-style доказательства | Уже единственный e2e-раннер; webServer-конфиг готов |
| `node:test` (Node.js) | `v24.21.0` | CSS/контрактные гейты | `npm run test:js` → `scripts/run-unit-js.cjs` уже перечисляет `tests/unit/*.js` |

### Supporting

| Library | Version | Purpose | When to Use |
|---|---|---|---|
| `tests/unit/helpers/cssRules.js` (`parseRules`) | в репо | Разбор CSS в `selector → declarations` | Для проверки байт-идентичности алиасов (G-8); **не** для чтения `@theme`-блока — там нужен собственный `parseBlock` |
| `tests/unit/helpers/` (собственный `parseBlock`) | 8 строк | `@theme static` / `[data-theme="light"]` → `Map<name, value>` | Копия локальной функции из `test_concept2_canon.js` (её нельзя импортировать — она не экспортируется, а файл менять запрещено) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|---|---|---|
| Один общий `tests/helpers/contrast.js` | Дублировать формулу в node-тесте и в спеке | Дублирование = два места, где формула может разойтись; helper дешевле и не ломает ни один раннер (Playwright собирает только `*.spec.js`, `run-unit-js.cjs` — только `tests/unit/*.js`) |
| `@theme inline` для `--color-paper` | `@theme static` (обычный) | `inline` подставляет *значение*, а не `var(--color-*)`; это сломало бы контракт `getPropertyValue('--color-*')`, которым уже пользуется `tests/web-app.spec.js:51`, и разошлось бы с существующим идиомом файла |
| Библиотека контраста (`color-contrast-checker` и т.п.) | 10 строк WCAG-формулы в `tests/helpers/contrast.js` | Новый npm-пакет в фазе, которая чинит зависимости от цветов, — расширение объёма; формула тривиальна и уже воспроизведена в § Contrast Arithmetic |

**Installation:**

```bash
# Ничего не устанавливается. Фаза не добавляет ни одной зависимости.
```

**Version verification:** версии прочитаны из `web/package.json` и подтверждены установленным деревом (`web/node_modules/tailwindcss/package.json` → `4.3.3`), `node --version` → `v24.21.0`, `npm --version` → `11.19.0`.

---

## Package Legitimacy Audit

**Эта фаза не устанавливает ни одного пакета.** `npm run test:js`, `npm run test:web`, `npm run build` — всё уже в дереве.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | Не применимо |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

---

## Architecture Patterns

### System Architecture Diagram

```
JSX className strings (web/src/**/*.jsx)
        │
        │  Tailwind v4 scanner (vite plugin, build-time)
        ▼
utility CSS:  .bg-paper  →  background-color: var(--color-paper)
              .text-ink-2 →  color: var(--color-ink-2)
              .border-rule → border-color: var(--color-rule)
        │                              │
        │  (утилита НЕ генерируется,   │  (значение кастомного свойства)
        │   если токена нет)           ▼
        │                     ┌──────────────────────────────────┐
        │                     │ @layer theme                      │
        │                     │  :root { --color-paper: #131925 } │  ← @theme static
        │                     ├──────────────────────────────────┤
        │                     │ @layer base                       │
        │                     │  [data-theme="light"] {           │  ← light override
        │                     │    --color-paper: #FFFFFF }       │     (позже в каскаде →
        │                     ├──────────────────────────────────┤      перебивает theme)
        │                     │ @layer utilities                  │
        │                     │  .bg-paper { background-color:    │
        │                     │     var(--color-paper) }          │
        │                     └──────────────────────────────────┘
        ▼
computed style в браузере: background-color / color / column-gap / font-size
        │
        ├── node:test  ──►  читает web/src/index.css + web/src/**/*.jsx
        │                   (G-1…G-8: объявлено / есть override / нет мёртвых токенов / контраст)
        └── Playwright ──►  читает getComputedStyle + считает WCAG-отношение
                            (критерии 1, 2, 4, 5)
```

Ключевое следствие для планировщика: **есть два независимых класса проверок, и они не заменяют друг друга.** Node-гейт доказывает, что объявление существует и арифметика верна; Playwright доказывает, что утилита реально долетела до DOM. Причина исходного бага — ровно разрыв между этими двумя слоями.

### Recommended Project Structure (только затронутое)

```
tests/
├── helpers/
│   └── contrast.js                 # NEW: hex/rgb → WCAG 2.x ratio (общий для node и Playwright)
├── unit/
│   ├── helpers/cssRules.js         # EXISTING: parseRules
│   ├── test_concept2_canon.js      # EXISTING: НЕ ТРОГАТЬ
│   └── test_semantic_token_coverage.js   # NEW: G-1…G-8 (критерий 3)
├── admin.spec.js                   # AMEND: ассерты-строки и toHaveClass
└── admin-chrome.spec.js            # NEW: критерии 1, 2, 4, 5

web/src/
├── index.css                       # EDIT: семейство + -solid + scrim
├── components/
│   ├── AdminLayout.jsx             # EDIT: 3 метки, eyebrow, tabClass, nav/select
│   ├── IngestSourcesSection.jsx    # EDIT: heading, bg-paper-2/40 ×2, accent CTA
│   ├── UnsavedChangesDialog.jsx    # EDIT: bg-ink/40, accent CTA
│   ├── AppShell.jsx                # EDIT: linkClass active branch
│   ├── ActionButton.jsx            # EDIT: 4 заливки
│   └── ServiceUnavailable.jsx      # EDIT: primary CTA
└── pages/
    ├── LoginPage.jsx               # EDIT: 2 primary CTA
    ├── RegisterPage.jsx            # EDIT: 2 primary CTA
    ├── KnowledgePage.jsx           # EDIT: 1 primary chip
    ├── AdminDigestPage.jsx         # EDIT: 2 success CTA + 3 scrim
    └── AdminPipelineConfigPage.jsx # EDIT: 1 accent CTA

playwright.config.js                # EDIT (config): testMatch должен включать admin-chrome
```

### Pattern 1: Двухслойный токен (dark в `@theme static`, light в `[data-theme="light"]`)

**What:** значение живёт в `@theme static` (слой `theme`), а светлая тема — обычным CSS-правилом в `@layer base`.
**When to use:** любой токен, чьё значение зависит от темы (`paper`, `paper-2`, `ink`, `ink-2`, `muted`, `rule`).
**Why it works (verified):** собранный `web/dist/assets/index-*.css` содержит `@layer theme{:root,:host{…}}` → `@layer base{… [data-theme=light]{…} …}` → `@layer utilities{…}`. Слой `base` идёт после `theme`, поэтому `[data-theme="light"]` перебивает `:root` при равной специфичности. Рантайм это уже доказывает: `tests/web-app.spec.js:47-57` переключает тему и получает `#F8FAFC` из `--color-bg-app`.

```css
/* Source: web/src/index.css:7-68 (existing @theme static) + 106-121 (existing light block) */
@theme static {
  --color-bg-app: #0B0F17;            /* line 8  */
  --color-primary-hover: #7C3AED;     /* line 19 — источник значения primary-solid */
  /* … новое семейство добавляется сюда же, НЕ во второй @theme … */
}

@layer base {
  /* … */
  [data-theme="light"] {
    --color-bg-app: #F8FAFC;          /* line 107 */
    /* … light override'ы добавляются сюда же, НЕ во второй блок … */
  }
}
```

### Pattern 2: Тема-независимая роль — отдельный токен, не перекраска базы

**What:** `--color-primary` остаётся `#8B5CF6` (текст/бордер/ринг/тинт в 24 файлах); для заливки вводится `--color-primary-solid: #7C3AED` и подпись `--color-on-solid: #FFFFFF`.
**When to use:** любая поверхность, где текст лежит *на* заливке.
**Why:** D-05 — потемнение базы перекрасило бы читательские `MaterialPage`/`RazborPage`, что ROADMAP запрещает.

### Pattern 3: Контрактный гейт как node-тест по CSS + исходникам

**What:** тест читает `web/src/index.css` и `web/src/**/*.{js,jsx}`, строит `Map<token, value>` и ассертит покрытие + арифметику.
**When to use:** любой инвариант, который выражается в статике (объявлено / есть override / нет мёртвых токенов / контраст значений).
**Why:** уже дважды принятый в репо паттерн (`test_concept2_canon.js`, `test_design_typography.js`); авто-обнаружение через `scripts/run-unit-js.cjs`, кроссплатформенно (PowerShell/cmd/bash).

### Pattern 4: Computed-style доказательство в Playwright

**What:** `page.evaluate` над `getComputedStyle`, пара `color` / `backgroundColor` возвращается в Node-контекст, отношение считается общей функцией.
**When to use:** критерии 2, 4, 5 — всё, где важно, что утилита дошла до DOM.
**Why:** считать контраст внутри `page.evaluate` нельзя без дублирования формулы в браузерном контексте; возврат строк `rgb(...)` даёт один источник истины.

### Anti-Patterns to Avoid

- **По-компонентный хардкод цвета** (`text-[#CBD5E1]`, `style={{color:…}}`) — нарушает D-05/zone-1 констрейнт и обходит гейт.
- **`!important`** — маскирует вместо исправления каскада.
- **`@theme inline` для этого семейства** — ломает `var(--color-*)`-индирекцию, на которой стоит существующий тест темы.
- **Второй блок `@theme` или второй `[data-theme="light"]`** — `parseBlock` читает только первое вхождение; гейт ослепнет, канон-тест прочитает неполный набор.
- **Темо-зависимый токен как подпись на заливке** (`text-text-primary`, `text-bg-app`, `text-secondary` на `bg-*`) — это и есть дефект THEME-01.
- **Объявление токена без потребителей** (`--color-accent-ink`) — ровно тот класс дефекта, который фаза убирает (D-10).
- **`toHaveClass(/bg-primary/)` для проверки `bg-primary-solid`** — подстрока совпадает, ассерт становится вакуумным.
- **Ассерт «фон не прозрачный» как единственная проверка критерия 2** — верно, но недостаточно: нужна ещё пара `color`/`background` и ожидаемые `rgb(...)`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| Рантайм-переключение темы | JS-провайдер темы, пересчитывающий цвета | `data-theme` на `<html>` + `localStorage['digest-cds-theme']` (уже есть в `ThemeToggle.jsx`) | Контракт ADR-0009, на нём стоит существующий тест |
| Парсер CSS | Свой токенизатор | `parseRules` из `tests/unit/helpers/cssRules.js` для плоских правил | Уже спускается в `@layer`/`@media`, склеивает повторные селекторы |
| Парсер `@theme`-блока | Универсальный CSS-парсер | 8-строчный `parseBlock` по образцу `test_concept2_canon.js:31-40` | Формат файла фиксирован; универсальный парсер добавил бы зависимость |
| Проверка «класс есть в className» | Регексп на подстроку | `el.getAttribute('class').split(/\s+/)` → `toContain` / `not.toContain` | Регексп `/bg-primary/` совпадает внутри `bg-primary-solid` |
| Переключение темы в Playwright | Клик по `theme-toggle` перед каждым ассертом | `page.addInitScript(() => localStorage.setItem('digest-cds-theme','light'))` до `goto` | Уже принятый приём (`tests/admin.spec.js:633-636`); без него возможен flash тёмной темы и гонка |
| Контраст | Внешняя библиотека или онлайн-калькулятор | `tests/helpers/contrast.js` — 10 строк WCAG 2.x | Ноль зависимостей; значения проверены по шкале (§ Contrast Arithmetic) |

**Key insight:** в этой фазе «не изобретай» относится к *инфраструктуре проверки*, а не к цветам. Формулу контраста писать нужно (библиотека = новая зависимость), ассерт-хелпер — нет.

---

## Runtime State Inventory

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | **None.** Переименование — строковый литерал в JSX. В БД/`localStorage`/URL нет ни одного места, где «Пайплайн» был бы ключом, id или collection name. `localStorage` хранит только `digest-cds-theme` (`ThemeToggle.jsx:3`), не связан с названием раздела | None |
| Live service config | **None.** Ни один внешний сервис не знает про эту метку. Аналитики/дашбордов/Datadog-тегов с «Пайплайн» в репо нет | None |
| OS-registered state | **None.** Нет systemd-юнитов/pm2/launchd, зарегистрированных с этой строкой (Phase 24 юниты относятся к `ingest`, не к UI-метке) | None |
| Secrets/env vars | **None** по переименованию. Операционный нюанс: `web/.env.local` содержит `VITE_USE_MOCKS=false`, что ломает Playwright при переиспользовании живого сервера (STATE.md blocker) | Проверить порт 5174 перед прогоном; файл не менять |
| Build artifacts | `web/dist/` (в `.gitignore`) содержит CSS, собранный из старого `index.css` — 32.04 kB, `--color-paper` / `--color-ink` / `--color-rule` / `--color-muted` отсутствуют. `web/node_modules/` и `.playwright-browsers/` не затронуты | `web/dist` перегенерируется `npm run build`; git не видит, действий не требуется |
| Browser state | `localStorage['digest-cds-theme']` переживает навигацию в пределах origin. Тест, которому нужна тёмная тема, обязан её *сбросить*, а не полагаться на дефолт | В фикстуре явно снимать/ставить ключ |

**Canonical question:** *после правки каждого файла в репо — какие рантайм-системы всё ещё держат старую строку?* Ответ: ни одна. Единственный «кэш» — сборка `web/dist`, которая не под контролем версий и пересоздаётся.

---

## Current State — Measured Ground Truth

Всё в этом разделе **измерено** в этом сеансе: `npm run build --prefix web`, затем headless-Chromium прогон по живому `127.0.0.1:5174` с `VITE_USE_MOCKS=true` и `window.__DIGEST_MOCK_ME_ROLE__='admin'`.

### Собранный CSS (до правки)

Файл `web/dist/assets/index-D0QJWfON.css` (32.04 kB). Вхождения подстрок:

| Подстрока | Вхождений | Что значит |
|---|---|---|
| `--color-paper` | **0** | токен не объявлен |
| `--color-ink` | **0** | токен не объявлен |
| `--color-rule` | **0** | токен не объявлен |
| `--color-muted` | **0** | токен не объявлен (есть только `--color-bg-muted`) |
| `.bg-paper`, `.text-ink`, `.text-ink-2`, `.bg-paper-2`, `.text-muted`, `.border-rule` | **0 каждый** | утилиты не сгенерированы |
| `--color-bg-app` | 8 | объявленный токен действительно долетает (control group) |
| `--color-xp`, `--color-streak`, `--color-rank-1` | 4 / 1 / 1 | `@theme static` действительно эмитит неиспользуемые токены |

Структура слоёв в том же файле (verbatim): `@layer theme{:root,:host{…}}` … `@layer base{…}` … `[data-theme=light]{--color-bg-app:#f8fafc; …}` … `@layer utilities{…}`. Отсюда и работоспособность overrides.

### Computed style до правки

`/admin/pipeline`, 1280×900, `document.fonts.ready` выполнен.

| Probe | Dark | Light |
|---|---|---|
| `html[data-theme]` | `null` (тёмная = отсутствие атрибута) | `"light"` |
| `#ingest-sources-kind` `color` / `background-color` | `rgb(241, 245, 249)` / **`rgba(0, 0, 0, 0)`** | `rgb(15, 23, 42)` / **`rgba(0, 0, 0, 0)`** |
| `#ingest-sources-id` (same pair) | `rgb(241, 245, 249)` / `rgba(0, 0, 0, 0)` | `rgb(15, 23, 42)` / `rgba(0, 0, 0, 0)` |
| `#ingest-sources-label` (same pair) | `rgb(241, 245, 249)` / `rgba(0, 0, 0, 0)` | `rgb(15, 23, 42)` / `rgba(0, 0, 0, 0)` |
| `#ingest-sources-kind` options | `["Канал","Плейлист"]` | те же |
| `--color-paper` / `--color-ink` (getPropertyValue) | `""` / `""` | `""` / `""` |
| `#ingest-sources-section` `background-color` | `rgba(0, 0, 0, 0)` | `rgba(0, 0, 0, 0)` |
| `#ingest-sources-section` `border-top-color` | `rgb(241, 245, 249)` (= `currentColor`) | `rgb(15, 23, 42)` (= `currentColor`) |
| `#ingest-sources-heading` text / size | `"Источники ингеста"` / `24px` | те же |
| `#admin-section-nav` `column-gap` | `8px` | `8px` |
| `nav.top − main.top` | `137 − 73 = 64` | `64` |
| `#admin-tab-pipeline` `font-size` / `line-height` / `min-height` | `30px` / `36px` / `44px` | те же |
| `#admin-tab-pipeline` text | `"Пайплайн"` | `"Пайплайн"` |
| `#admin-tab-digest` text | `"Дайджест"` | `"Дайджест"` |
| `h1` text | `"Пайплайн"` | `"Пайплайн"` |
| `getByText('Админ', { exact: true })` count на `/admin/pipeline` | **2** (eyebrow `<p>` + shell `<a>`) | 2 |
| Shell pill `color` / `background-color` | `rgb(241, 245, 249)` / `rgb(139, 92, 246)` | `rgb(15, 23, 42)` / `rgb(139, 92, 246)` |
| `#ingest-sources-add` `color` / `background-color` | `rgb(241, 245, 249)` / `rgb(6, 182, 212)` | `rgb(15, 23, 42)` / `rgb(6, 182, 212)` |
| `#confirm-vote` на `/voting` после выбора радио `color` / `background-color` | `rgb(11, 15, 23)` / `rgb(234, 179, 8)` | `rgb(248, 250, 252)` / `rgb(234, 179, 8)` |

### Три вывода, которые меняют форму тестов

1. **Фон `<select>` сегодня — `rgba(0, 0, 0, 0)`, а не «белое UA-поле».** Tailwind preflight задаёт `background-color: transparent` и `color: inherit` для `select`. Значит: утверждение «фон не `rgb(255,255,255)`» пройдёт на текущем дереве (вакуумный ассерт); валидный RED — **`background-color` обязан быть равен объявленному `rgb(19, 25, 37)` / `rgb(255, 255, 255)`** и не иметь альфы. Белый текст на белом пользователь видит в **раскрытом списке опций** (его рисует UA), а не в закрытом поле — закрытое поле сегодня прозрачно и наследует цвет.
2. **`border-rule` сегодня красит `currentColor`.** Preflight эмитит `border: 0 solid` без `border-color`, поэтому начальное значение `currentColor` и даёт `rgb(241,245,249)` / `rgb(15,23,42)`. Объявление токена *заменит* почти невидимую границу на `#2A3548` — это ожидаемое и зафиксированное UI-SPEC изменение, но визуально границы станут заметнее, а не «появятся».
3. **Числа критерия 5 сходятся с UI-SPEC точно:** `64 → 40` (`main.top + 40` остаётся, 24 px над вкладками исчезают), `8px → 16px`, `30px → 24px`, «Админ» `2 → 1`.

---

## Tailwind v4 Token Mechanics (verified)

| Утверждение | Статус | Доказательство |
|---|---|---|
| `@theme static` эмитит **все** переменные, даже без потребителей; обычный `@theme` — только использованные | `[CITED: tailwindcss.com/docs/theme]` | Context7 `/websites/tailwindcss`: «By default only used CSS variables will be generated in the final CSS output. If you want to always generate all CSS variables, you can use the `static` theme option» |
| Токены `@theme` обязаны быть top-level, их нельзя объявлять под селектором или media query | `[CITED: tailwindcss.com/docs/theme]` | «Theme variables are also required to be defined top-level and not nested under other selectors or media queries» — поэтому light-override **не может** жить внутри `@theme` |
| `@theme` эмитится в слой `theme`, а `@layer base` идёт **после** | `[VERIFIED: web/dist/assets/index-D0QJWfON.css]` | verbatim: `@layer theme{:root,:host{` … `@layer base{*,:after,:before,::backdrop{box-sizing:border-box;border:0 solid;margin:0;padding:0}` … `[data-theme=light]{--color-bg-app:#f8fafc;` … `@layer utilities{` |
| Ключ `--color-paper-2` даёт утилиту `bg-paper-2` (суффикс переносится дословно, цифры и дефисы не требуют escaping) | `[VERIFIED: web/src/index.css:8 + build]` | `--color-bg-app: #0B0F17;` → `.bg-bg-app{background-color:var(--color-bg-app)}`; тот же механизм для любого `--color-<key>` |
| Модификатор прозрачности компилируется в `color-mix(… var(--color-*) …)` с литеральным fallback | `[VERIFIED: build]` | `.bg-bg-app\/95{background-color:#0b0f17f2}@supports (color:color-mix(in lab, red, red)){.bg-bg-app\/95{background-color:color-mix(in oklab, var(--color-bg-app) 95%, transparent)}}` — то есть `bg-paper-2/40` после объявления станет реальными 40 % и даст 1.04:1 на белом (см. Contrast Arithmetic) |
| `focus-visible:outline-primary` уже генерируется и красит только `outline-color` | `[VERIFIED: build]` | `.focus-visible\:outline-primary:focus-visible{outline-color:var(--color-primary)}` |
| Rgba-значение в токене допустимо | `[VERIFIED: web/src/index.css:12]` | `--color-bg-glass: rgba(19, 25, 37, 0.72);` — паттерн для `--color-scrim: rgba(0, 0, 0, 0.6)` |

**Что это значит для планировщика:** все шесть новых theme-зависимых токенов идут в *существующий* блок `@theme static` (7-68) и в *существующий* блок `[data-theme="light"]` (106-121). Все семь тема-независимых — только в `@theme static`, без light-override (D-08), и гейт пинит **отсутствие** override у них.

---

## Contrast Arithmetic (verified)

Формула — WCAG 2.x relative luminance, посчитана этим же кодом, который попадёт в `tests/helpers/contrast.js`.

| Пара | Отношение | Порог 4.5 |
|---|---|---|
| **До правки (RED-базис)** | | |
| `#F1F5F9` на `#8B5CF6` (pill/primary, dark) | 3.8652 | ✗ |
| `#0F172A` на `#8B5CF6` (pill/primary, light) | 4.2161 | ✗ |
| `#F1F5F9` на `#06B6D4` (accent, dark) | 2.2162 | ✗ |
| `#0F172A` на `#06B6D4` (accent, light) | 7.3532 | ✓ |
| `#F1F5F9` на `#22C55E` (success, dark) | 2.0799 | ✗ |
| `#F1F5F9` на `#EF4444` (danger, dark) | 3.4350 | ✗ |
| `#0F172A` на `#EF4444` (danger, light) | 4.7441 | ✓ |
| `#0B0F17` на `#EAB308` (voting, dark) | 10.0007 | ✓ |
| `#F8FAFC` на `#EAB308` (voting, light) | **1.8330** | ✗ |
| `#FFFFFF` на `#8B5CF6` (лучший белый на текущей базе) | 4.2344 | ✗ |
| **После правки — заливки** | | |
| `#FFFFFF` на `#7C3AED` (`on-solid` / `primary-solid`) | 5.6986 | ✓ |
| `#FFFFFF` на `#0E7490` (`accent-solid`) | 5.3578 | ✓ |
| `#FFFFFF` на `#15803D` (`success-solid`) | 5.0156 | ✓ |
| `#FFFFFF` на `#DC2626` (`danger-solid`) — **худший случай** | **4.8294** | ✓ (floor **4.829**) |
| `#F1F5F9` на `#DC2626` (почему `on-solid` = чистый белый) | 4.4083 | ✗ |
| `#0F172A` на `#EAB308` (`voting-ink`) | 9.3088 | ✓ |
| **После правки — текстовое семейство** | | |
| `ink` `#F1F5F9` на `paper` `#131925` / `paper-2` `#1A2233` | 16.0618 / 14.5161 | ✓ / ✓ |
| `ink` light `#0F172A` на `#FFFFFF` / `#F1F5F9` | 17.8525 / 16.2960 | ✓ / ✓ |
| `ink-2` `#CBD5E1` на `#131925` / `#1A2233` | 11.8515 / 10.7110 | ✓ / ✓ |
| `ink-2` light `#334155` на `#FFFFFF` / `#F1F5F9` | 10.3547 / 9.4519 | ✓ / ✓ |
| `muted` `#94A3B8` на `#131925` / `#1A2233` | 6.8626 / 6.2022 | ✓ / ✓ |
| `muted` light `#475569` на `#FFFFFF` / `#F1F5F9` / `bg-app #F8FAFC` | 7.5777 / 6.9170 / 7.2425 | ✓ / ✓ / ✓ |
| `muted` light `#64748B` на `paper-2` (отклонённый вариант) | 4.3439 | ✗ |
| `muted` `#94A3B8` на `paper-2` light (отклонённый вариант) | 2.3405 | ✗ |
| **Границы (`rule`) — не текстовые** | | |
| `rule` light `#CBD5E1` на `paper` / `paper-2` / `bg-app` | 1.4847 / 1.3553 / 1.4190 | n/a |
| `rule` canon-parity `#E2E8F0` на `paper` / `paper-2` | 1.2328 / 1.1253 | n/a |
| `rule` dark `#2A3548` на `paper` / `paper-2` | 1.4255 / 1.2883 | n/a |
| Заливка `paper` на `paper-2` (light) | 1.0955 | n/a |
| `paper-2` при 40 % на белом | 1.0379 | n/a |

Каждое число UI-SPEC воспроизвелось с точностью до 2 знаков. Одно расхождение: UI-SPEC называет шаг заливки `#FFFFFF` на `#F1F5F9` = **1.13**, фактически **1.10** (1.0955). Вывод не меняется (`#E2E8F0` даёт 1.13 — то есть ровно шаг заливки и ни крошки края), но в тексте плана лучше писать **1.10**.

**Фокус-ринги (WCAG 1.4.11, порог 3:1):** `--color-primary #8B5CF6` = 4.0471 на светлом `bg-app`, 4.2344 на светлом `paper`, 4.5294 на тёмном `bg-app`, 4.1555 на тёмном `paper` — все > 3. `--color-accent #06B6D4` = 2.4279 на белом — почему UI-SPEC и требует `outline-primary` для новых рингов.

---

## Change Inventory (file:line → change)

### `web/src/index.css`

Текущее (verbatim, `[VERIFIED: web/src/index.css:7-8]`):
```css
@theme static {
  --color-bg-app: #0B0F17;
```
Текущее (verbatim, `[VERIFIED: web/src/index.css:106-107]`):
```css
  [data-theme="light"] {
    --color-bg-app: #F8FAFC;
```

**Добавить в блок 7-68** (значения нормативны по `25-UI-SPEC.md`, не пере-выводить):

```css
  /* Semantic admin family — declared here so the utilities the admin
     components already use actually reach the DOM (Tailwind v4 emits
     nothing for an unknown token). Light values live in the
     [data-theme="light"] block below. */
  --color-paper: #131925;
  --color-paper-2: #1A2233;
  --color-ink: #F1F5F9;
  --color-ink-2: #CBD5E1;
  --color-muted: #94A3B8;
  --color-rule: #2A3548;

  /* Theme-independent roles: identical in both themes, so no override. */
  --color-primary-solid: #7C3AED;
  --color-accent-solid: #0E7490;
  --color-success-solid: #15803D;
  --color-danger-solid: #DC2626;
  --color-on-solid: #FFFFFF;
  --color-voting-ink: #0F172A;
  --color-scrim: rgba(0, 0, 0, 0.6);
```

**Добавить в блок 106-121** (только шесть theme-зависимых):

```css
    --color-paper: #FFFFFF;
    --color-paper-2: #F1F5F9;
    --color-ink: #0F172A;
    --color-ink-2: #334155;
    --color-muted: #475569;
    --color-rule: #CBD5E1;
```

`--color-accent-ink` **не** объявляется (D-10).

### Компоненты

| File | Line | Current (verbatim) | Target |
|---|---|---|---|
| `AdminLayout.jsx` | 13 | `'inline-flex min-h-11 items-end border-b-2 pb-2 text-3xl',` | `'inline-flex min-h-11 items-end border-b-2 pb-2 text-2xl focus-visible:outline-primary',` |
| `AdminLayout.jsx` | 15 | `? 'border-accent font-semibold text-ink'` | без изменений (после объявления токенов станет реальным) |
| `AdminLayout.jsx` | 16 | `: 'border-transparent font-normal text-muted hover:text-ink',` | без изменений |
| `AdminLayout.jsx` | 42 | `<p className="text-xs font-semibold uppercase tracking-wide text-muted">Админ</p>` | **удалить элемент целиком** |
| `AdminLayout.jsx` | 49 | `<h1 className="sr-only">{section === PIPELINE_PATH ? 'Пайплайн' : 'Дайджест'}</h1>` | `… ? 'Настройка' : 'Дайджест'` — h1 сохраняется |
| `AdminLayout.jsx` | 52 | `className="mt-2 hidden gap-2 border-b border-rule sm:flex"` | `className="mt-0 hidden gap-4 border-b border-rule sm:flex"` |
| `AdminLayout.jsx` | 70 | `Пайплайн` (текст вкладки) | `Настройка` |
| `AdminLayout.jsx` | 77 | `className="mt-2 min-h-11 w-full max-w-sm rounded-xl border border-rule bg-paper px-3 text-base text-ink focus-visible:outline-accent sm:hidden"` | `className="mt-0 min-h-11 w-full max-w-sm rounded-xl border border-rule bg-paper px-3 text-base text-ink focus-visible:outline-primary sm:hidden"` |
| `AdminLayout.jsx` | 83 | `<option value={PIPELINE_PATH}>Пайплайн</option>` | `…>Настройка</option>` |
| `IngestSourcesSection.jsx` | 171-173 | `<h2 … className="font-sans text-2xl font-semibold text-ink">` / `Источники ингеста` | текст → `Источники` (класс не трогать) |
| `IngestSourcesSection.jsx` | 219 | `className="rounded-xl border border-rule bg-paper-2/40 p-3"` | `… bg-paper-2 p-3` |
| `IngestSourcesSection.jsx` | 264 | `className="mt-6 space-y-3 rounded-xl bg-paper-2/40 p-4"` | `… bg-paper-2 p-4` |
| `IngestSourcesSection.jsx` | 308 | `… rounded-full bg-accent px-5 text-sm font-medium text-accent-ink disabled:…` | `… bg-accent-solid … text-on-solid …` |
| `UnsavedChangesDialog.jsx` | 26 | `className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"` | `… bg-scrim p-4` |
| `UnsavedChangesDialog.jsx` | 53 | `… rounded-full bg-accent px-4 text-sm font-medium text-accent-ink"` | `… bg-accent-solid … text-on-solid"` |
| `AppShell.jsx` | 14 | `isActive ? 'bg-primary text-text-primary' : 'text-text-secondary hover:bg-bg-surface',` | `isActive ? 'bg-primary-solid text-on-solid' : …` |
| `ActionButton.jsx` | 4 | `error: 'bg-danger text-text-primary',` | `error: 'bg-danger-solid text-on-solid',` |
| `ActionButton.jsx` | 5 | `success: 'bg-success text-text-primary',` | `success: 'bg-success-solid text-on-solid',` |
| `ActionButton.jsx` | 18 | `? 'bg-voting text-bg-app'` | `? 'bg-voting text-voting-ink'` |
| `ActionButton.jsx` | 21 | `: 'bg-primary text-text-primary'` | `: 'bg-primary-solid text-on-solid'` |
| `ServiceUnavailable.jsx` | 38 | `… rounded-full bg-primary px-5 text-sm font-medium text-text-primary …` | `bg-primary-solid` + `text-on-solid` |
| `LoginPage.jsx` | 126, 198 | `… rounded-full bg-primary px-4 text-sm [font-medium ]text-text-primary …` | `bg-primary-solid` + `text-on-solid` |
| `RegisterPage.jsx` | 107, 210 | то же | то же |
| `KnowledgePage.jsx` | 278 | `? 'min-h-11 rounded-full bg-primary px-3 text-sm text-text-primary'` | `bg-primary-solid` + `text-on-solid` |
| `AdminDigestPage.jsx` | 794, 919 | `… rounded-full bg-success px-4 text-sm font-medium text-text-primary …` | `bg-success-solid` + `text-on-solid` |
| `AdminDigestPage.jsx` | 821, 885, 948 | `className="fixed inset-0 z-[400] flex items-center justify-center bg-text-primary/40 p-4"` | `… bg-scrim p-4` |
| `AdminPipelineConfigPage.jsx` | 305 | `… rounded-full bg-accent px-5 text-sm font-medium text-accent-ink …` | `bg-accent-solid` + `text-on-solid` |
| `MaterialPage.jsx` | 187 | `… border border-rule bg-paper-2 … text-ink` | **не редактировать** — станет нарисованным callout'ом (принято в UI-SPEC) |

Не трогать: `TopicBallot.jsx:26`, `VotingPage.jsx:448`, `EditorialCallout.jsx:10`, `AdminDigestPage.jsx:717-718`, `AdminDigestPage.jsx:808` (известный дефект 1), `border-danger`/`bg-danger/10` в `AdminPipelineConfigPage.jsx:333,362`.

### `playwright.config.js` (конфиг, не прод-код)

Текущее (verbatim, `[VERIFIED: playwright.config.js:71]`; строка 72 рядом — `use.baseURL`, её не трогать):
```js
      testMatch: /(web-app|auth|knowledge|razbory|admin)\.spec\.js/,
```
Заменить на `/(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/` (или `/(web-app|auth|knowledge|razbory|admin)[\w-]*\.spec\.js/`).

**Доказательство необходимости:** временный `tests/admin-chrome.spec.js` с одним тестом → `npx playwright test --list --project=web` печатает `Total: 148 tests in 5 files` и **не содержит** `admin-chrome.spec.js`. Без правки конфига все четыре новых критерия не имеют RED'а — тест молча игнорируется, а не падает.

---

## Test Harness Decisions

### Где живёт гейт (критерий 3)

**node:test → `tests/unit/test_semantic_token_coverage.js`.** Обоснование измеренное, а не вкусовое:

1. `scripts/run-unit-js.cjs:13-17` перечисляет `tests/unit/*.js` — новый файл подхватывается без правки раннера.
2. `test_concept2_canon.js` и `test_design_typography.js` уже читают `web/src/index.css` и `web/src/*.jsx` — паттерн не изобретается.
3. Гейт проверяет **статику** (объявлено / есть override / арифметика) — Playwright для этого был бы медленнее и потребовал бы браузера.
4. Node API: `readdirSync(dir, { recursive: true })` (Node 24) покрывает `web/src/**/*.{js,jsx}` без глоба.

Половинка проверки критерия 2 остаётся в Playwright — «утилита долетела до DOM» нельзя доказать статикой.

### Где живёт computed-style проверка (критерии 1, 2, 4, 5)

**`tests/admin-chrome.spec.js`** (+ правка `testMatch`). Переиспользовать существующие фикстуры:

| Нужно | Готовое решение в репо |
|---|---|
| Admin-роль | `page.addInitScript(() => { window.__DIGEST_MOCK_ME_ROLE__ = 'admin' })` (`tests/admin.spec.js:24-29`) |
| Сброс модульных моков после Vite HMR | `window.__DIGEST_ADMIN_HARNESS__.resetAdminHarness()` + `page.reload()` (`tests/admin.spec.js:37-48`) |
| Светлая тема | `page.addInitScript(() => localStorage.setItem('digest-cds-theme','light'))` (`tests/admin.spec.js:633-636`) — работает, потому что `ThemeToggle.jsx:3,8-19` читает этот ключ и ставит `data-theme` на `<html>` |
| Шрифты перед геометрией | `await page.evaluate(() => document.fonts.ready)` (`tests/admin.spec.js:324, 356`) |
| `/voting` fixture | `page.goto('/voting')` → клик по радио `/RAG в корпоративной среде/i` → `confirm-vote` enabled (`tests/web-app.spec.js:294-297`) |
| Shell-пилл | `page.getByRole('navigation', { name: /основная навигация/i }).getByRole('link', { name: /^Админ$/ })` (`tests/admin.spec.js:110-114`) |
| `storageState` / `baseURL` | Не нужны: `storageState` не используется нигде, `baseURL` уже `http://127.0.0.1:5174` для проекта `web` |

### Baseline прогонов (для «до/после»)

| Прогон | Сейчас | После фазы |
|---|---|---|
| `npm run test:js` | `tests 50, pass 50, fail 0` | 50 + новые G-кейсы |
| `npx playwright test --list --project=web` | `Total: 148 tests in 5 files` | + новый файл (после правки `testMatch`) |
| `npm run build` | succeeds, CSS 32.04 kB | succeeds |

---

## Common Pitfalls

### Pitfall 1: Новый спек не запускается и RED'а не существует
**What goes wrong:** `admin-chrome.spec.js` не попадает под `testMatch`; `npx playwright test` его игнорирует, исполнитель видит «всё зелено» и считает критерии доказанными.
**Why:** `testMatch` — allow-list по именам, а не по каталогу.
**How to avoid:** правка `playwright.config.js` идёт **первым** шагом плана; проверить `--list` и увидеть имя файла до написания ассертов.
**Warning signs:** `--list` печатает «148 tests in 5 files», в выводе нет `admin-chrome`.

### Pitfall 2: «Фон не прозрачный» — единственный ассерт, но неверная его форма
**What goes wrong:** проверка «`backgroundColor !== 'rgba(0, 0, 0, 0)'`» проходит после фикса, но её отрицательная форма «не `rgb(255,255,255)`» проходит **и до** фикса.
**Why:** preflight делает фон прозрачным, а не белым (замерено).
**How to avoid:** ассертить **равенство ожидаемому** `rgb(19, 25, 37)` / `rgb(255, 255, 255)` плюс отсутствие альфы; контраст считать только после этой проверки (на прозрачном фоне отношение не определено).
**Warning signs:** тест зелёный на pre-fix дереве.

### Pitfall 3: `toHaveClass(/bg-primary/)` становится вакуумным
**What goes wrong:** `bg-primary-solid` содержит подстроку `bg-primary`, поэтому позитивный ассерт `toHaveClass(/bg-primary/)` проходит и после миграции, ничего не проверяя; негативный `not.toHaveClass(/bg-primary/)` начинает врать в обратную сторону.
**Why:** `toHaveClass(regexp)` тестирует весь атрибут `class`.
**How to avoid:** разбить атрибут: `const tokens = (await el.getAttribute('class')).split(/\s+/)` → `expect(tokens).toContain('bg-primary-solid')` **и** `expect(tokens).not.toContain('bg-primary')` в каждой строке.
**Warning signs:** позитивный ассерт продолжает зеленеть, если временно откатить миграцию.

### Pitfall 4: Второй блок `@theme` / `[data-theme="light"]` ослепляет гейт и канон-тест
**What goes wrong:** токены объявлены «рядом», в новом блоке; `parseBlock` (`test_concept2_canon.js:31-40`) берёт **первое** совпадение по head-паттерну и не видит второй блок. Гейт G-1 падает на объявленных токенах, канон-тест может прочитать неполный набор.
**Why:** `new RegExp(headPattern + '\\s*\\{([\\s\\S]*?)\\n\\}')` без глобала.
**How to avoid:** дописывать в существующие блоки (7-68 и 106-121). Если по каким-то причинам нужен второй блок — гейт обязан собирать **все** вхождения, а это уже другой тест.
**Warning signs:** G-1 «token not declared» при видимом объявлении в файле.

### Pitfall 5: `bg-ink/40` превращается в белую плёнку 40 %
**What goes wrong:** `ink` — текстовый цвет (`#F1F5F9` в тёмной). После объявления `bg-ink/40` даёт белый скрайм в тёмной теме и чёрный в светлой — то есть тот же темо-флип, который фаза убирает.
**Why:** утилита «молчала», потому что токена не было.
**How to avoid:** отдельный тема-независимый `--color-scrim`; G-6 запрещает **любое** `bg-ink` в `web/src`. Три `bg-text-primary/40` в `AdminDigestPage.jsx` (821/885/948) — тот же дефект, уже белая плёнка в тёмной теме сегодня; мигрируют вместе.

### Pitfall 6: `bg-paper-2/40` даёт невидимую подложку
**What goes wrong:** 40 % от `#F1F5F9` на `#FFFFFF` = 1.0379:1 — вложенная панель невидима в светлой теме.
**How to avoid:** солид `bg-paper-2` (1.0955 шаг заливки) + `border-rule` `#CBD5E1` (1.3553) как край; G-6 запрещает альфа-модификатор на `bg-paper`/`bg-paper-2`.

### Pitfall 7: `border-rule` меняет смысл — от `currentColor` к нарисованному цвету
**What goes wrong:** сейчас `border border-rule` рисует `currentColor` (`rgb(241,245,249)` в тёмной — почти белая рамка). После объявления рамка станет `#2A3548` (1.43:1 на `paper`). Визуально это читается как «рамки потускнели», хотя формально они впервые нарисованы.
**How to avoid:** зафиксировать это в плане как ожидаемое изменение (UI-SPEC § Boundary legibility) и не пытаться «вернуть как было» через `currentColor`.

### Pitfall 8: Массовые ложные падения Playwright
**What goes wrong:** `reuseExistingServer: !process.env.CI` переиспользует живой Vite на 5174, поднятый вручную с `VITE_USE_MOCKS=false` из `web/.env.local` → админ-спеки падают на логине (STATE.md: 17 падений).
**How to avoid:** перед прогоном `Get-NetTCPConnection -LocalPort 5174 -State Listen` и убить слушателя; Playwright сам поднимет сервер с `VITE_USE_MOCKS=true` (`playwright.config.js:50-55`).

### Pitfall 9: Незамеченный ассерт «Источники ингеста»
**What goes wrong:** `tests/admin.spec.js:1834` содержит `toHaveText("Источники ингеста")` — его нет в таблице амендментов UI-SPEC. После PIPEUI-03 тест краснеет, и «зелёный» прогон не достигается.
**How to avoid:** включить строку в амендменты (→ `"Источники"`).

### Pitfall 10: Слишком широкий амендмент негативных ассертов
**What goes wrong:** UI-SPEC предлагает заменить `/пайплайн/i` на `/настройк/i` в `:439-443` и `:461-465`. Это **ослабляет** проверку: `«Пайплайн»` — запрещённая строка (banned copy), и утверждение «в теле страницы дайджеста её нет» остаётся истинным и осмысленным.
**How to avoid:** негативные `getByText(/пайплайн/i)` **оставить как есть**; менять только позитивные ассерты (test titles, тексты вкладки/h1/option) и `toHaveClass(/text-3xl/)`.

### Pitfall 11: Гонка при измерении геометрии
**What goes wrong:** `column-gap`/`font-size`/`nav.top` читаются до подгрузки Manrope, метрики шумят.
**How to avoid:** `await page.evaluate(() => document.fonts.ready)` перед `boundingBox`/`evaluate` — уже принятый приём в repo.

### Pitfall 12: Тема «по умолчанию» в тесте — не тёмная
**What goes wrong:** предыдущий тест оставил `digest-cds-theme=light` в `localStorage`; ассерт «тёмной темы» падает по чужой вине.
**How to avoid:** init-script ставит ключ **явно** для обеих веток (`removeItem` для dark, `setItem` для light) и тест ассертит `html`-атрибут до измерений.

---

## Code Examples

### Двухслойное объявление токенов (единственно верная форма)

```css
/* Source: web/src/index.css:7-68 — дописать внутрь существующего @theme static */
@theme static {
  /* … существующие токены … */
  --color-paper: #131925;
  --color-paper-2: #1A2233;
  --color-ink: #F1F5F9;
  --color-ink-2: #CBD5E1;
  --color-muted: #94A3B8;
  --color-rule: #2A3548;
  --color-primary-solid: #7C3AED;
  --color-accent-solid: #0E7490;
  --color-success-solid: #15803D;
  --color-danger-solid: #DC2626;
  --color-on-solid: #FFFFFF;
  --color-voting-ink: #0F172A;
  --color-scrim: rgba(0, 0, 0, 0.6);
}

@layer base {
  /* … */
  [data-theme="light"] {
    /* … существующие overrides … */
    --color-paper: #FFFFFF;
    --color-paper-2: #F1F5F9;
    --color-ink: #0F172A;
    --color-ink-2: #334155;
    --color-muted: #475569;
    --color-rule: #CBD5E1;
  }
}
```

### Нормативный `tabClass` (PIPEUI-04)

```js
// Source: web/src/components/AdminLayout.jsx:11-18 — целевое состояние
function tabClass({ isActive }) {
  return [
    'inline-flex min-h-11 items-end border-b-2 pb-2 text-2xl focus-visible:outline-primary',
    isActive
      ? 'border-accent font-semibold text-ink'
      : 'border-transparent font-normal text-muted hover:text-ink',
  ].join(' ')
}
```

### WCAG 2.x отношение (общий helper для обоих раннеров)

```js
// Source: WCAG 2.x relative luminance — tests/helpers/contrast.js (NEW)
function parseColor(value) {
  const m = /^rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s/]+([\d.]+))?\s*\)$/i.exec(String(value).trim())
  if (!m) throw new Error(`unsupported color: ${value}`)
  return { r: Number(m[1]), g: Number(m[2]), b: Number(m[3]), a: m[4] === undefined ? 1 : Number(m[4]) }
}

function channelLuminance(c) {
  const s = c / 255
  return s <= 0.04045 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4)
}

function relativeLuminance(value) {
  const { r, g, b, a } = parseColor(value)
  if (a < 1) throw new Error(`transparent surface has no contrast: ${value}`)
  return 0.2126 * channelLuminance(r) + 0.7152 * channelLuminance(g) + 0.0722 * channelLuminance(b)
}

function contrastRatio(foreground, background) {
  const a = relativeLuminance(foreground)
  const b = relativeLuminance(background)
  const [hi, lo] = a >= b ? [a, b] : [b, a]
  return (hi + 0.05) / (lo + 0.05)
}

module.exports = { parseColor, relativeLuminance, contrastRatio }
```

Заметьте: `relativeLuminance` **бросает** на альфе < 1 — это делает Pitfall 2 невозможным по конструкции (нельзя случайно посчитать контраст на прозрачном фоне).

### Гейт G-1/G-2 (ядро, остальное — по таблице UI-SPEC)

```js
// Source: pattern from tests/unit/test_concept2_canon.js:31-40
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')
const css = readFileSync(path.join(ROOT, 'web/src/index.css'), 'utf8')

function parseBlock(source, headPattern) {
  const withoutComments = source.replace(/\/\*[\s\S]*?\*\//g, '')
  const match = new RegExp(`${headPattern}\\s*\\{([\\s\\S]*?)\\n\\}`, 'm').exec(withoutComments)
  const tokens = new Map()
  if (!match) return tokens
  for (const d of match[1].matchAll(/(--[a-z0-9-]+)\s*:\s*([^;]+);/g)) {
    tokens.set(d[1], d[2].trim())
  }
  return tokens
}

const dark = parseBlock(css, '@theme(?:\\s+static)?')
const light = parseBlock(css, '\\[data-theme="light"\\]')

const THEMED = ['paper', 'paper-2', 'ink', 'ink-2', 'muted', 'rule']
const FLAT = ['primary-solid', 'accent-solid', 'success-solid', 'danger-solid', 'on-solid', 'voting-ink', 'scrim']
```

### Playwright: фикстура темы + computed-style + token-exact ассерт

```js
// Source: tests/admin.spec.js:23-48 (role/admin harness) + :633-636 (theme) + web-app.spec.js:49-57 (computed)
async function gotoAdmin(page, path, theme) {
  await page.addInitScript((t) => {
    window.__DIGEST_MOCK_ME_ROLE__ = 'admin'
    if (t === 'light') localStorage.setItem('digest-cds-theme', 'light')
    else localStorage.removeItem('digest-cds-theme')
  }, theme)
  await page.goto(path)
  await page.evaluate(() => document.fonts.ready)
}

const pairOf = (page, testId) =>
  page.getByTestId(testId).evaluate((el) => {
    const cs = getComputedStyle(el)
    return { color: cs.color, background: cs.backgroundColor, fontSize: cs.fontSize }
  })

function classTokens(locator) {
  return locator.evaluate((el) => (el.getAttribute('class') ?? '').split(/\s+/).filter(Boolean))
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|---|---|---|---|
| `tailwind.config.js` → `theme.extend.colors` | CSS-first `@theme` в `index.css` | Tailwind v4 (2025) | Единственный source of truth — CSS; конфиг-файла в `web/` нет |
| `darkMode: 'class'` + `dark:` варианты | Свои токены + `[data-theme="light"]` override-слой | ADR-0009 (этот проект) | Тёмная = отсутствие атрибута; светлая — override |
| `@theme` только | `@theme static` для контрактных токенов | v4.0 | Неиспользуемый токен всё равно попадает в `:root` |
| `stylelint`/цветовые линтеры | node-тест, читающий CSS и ассертящий значения + WCAG | этот проект (`test_concept2_canon.js`) | Ноль зависимостей, кроссплатформенно |

**Deprecated/outdated:**
- `!important` и inline-стили для «переопределить тему» — запрещены констрейнтами зоны 1.
- `theme(borderColor.DEFAULT)`-подход v3 (фон/бордер по умолчанию) — в v4 preflight даёт `border: 0 solid` и `currentColor`.
- `bg-ink/40`, `bg-text-primary/40` как скрайм — темо-зависимый дефект; заменяются на `--color-scrim`.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | Chromium рисует раскрытый список опций `<select>`, используя `color`/`background-color` самого контрола, поэтому объявленная непрозрачная поверхность делает и попап читаемым | Current State / Pitfall 2 | Средний. Если попап всегда системно-белый, то в тёмной теме `ink-2` `#CBD5E1` на нём даст ~1.6:1. Критерий 2 (текст ROADMAP) выполняется по computed style контрола, но «опции читаемы» останется верой. Митигация: не выводить это как доказанное; при желании — отдельный `color-scheme` (вне объёма фазы). Проверяется визуально один раз человеком |
| A2 | `text-2xl` = 24px и равен контентному `h2` | Change Inventory | Низкий. Уже замерено: `#ingest-sources-heading` (класс `text-2xl`) даёт `24px` |
| A3 | `gap-4` = 16px | Change Inventory | Низкий. Собранный CSS: `--spacing:.25rem` → `gap-4` = 1rem; критерий 5 всё равно ассертит `> 8` |
| A4 | Удаление eyebrow `<p>` не ломает ни один landmark/ARIA-контракт | Change Inventory | Низкий. `<p>` не несёт роли; единственный landmark-контракт — `aria-label="Разделы админки"` на nav/select, он сохраняется |
| A5 | Числа UI-SPEC § Color нормативны и не требуют пере-вывода | Contrast Arithmetic | Низкий. Все проверены независимым расчётом (одно расхождение 1.13 → 1.10, не влияет на решение) |

---

## Open Questions

1. **Читаемость раскрытого списка опций (A1) — (RESOLVED)**
   - What we know: закрытое поле после фикса будет иметь непрозрачную объявленную поверхность и `ink-2` текст (критерий 2 — computed style).
   - What's unclear: рисует ли Chromium попап из `color`/`background-color` контрола в этом стеке; headless-скриншот нативные попапы не захватывает.
   - Recommendation: ассертить точно то, что названо в ROADMAP (computed pair + наличие опций `Канал`/`Плейлист`) и зафиксировать A1 в плане как ограничение доказательства; не добавлять `color-scheme` (вне объёма).
   - **(RESOLVED)** Доказательство ограничено ровно тем, что называет ROADMAP: computed-пара закрытого контрола + наличие опций `Канал`/`Плейлист` (тест `select legible in both themes`, план 25-03); раскрытый попап не ассертится, `color-scheme` не вводится — принятое ограничение, а не долг.

2. **Где физически живёт общий `contrastRatio` — (RESOLVED)**
   - What we know: оба раннера CommonJS; `tests/helpers/` не собирается ни одним из них.
   - What's unclear: предпочтёт ли планировщик `tests/unit/helpers/contrast.js` (рядом с `cssRules.js`) или `tests/helpers/contrast.js`.
   - Recommendation: `tests/helpers/contrast.js` — явный сигнал «общий», и это не ломает `run-unit-js.cjs` (перечисляет только `tests/unit/*.js`).
   - **(RESOLVED)** Файл — `tests/helpers/contrast.js` (план 25-03, task 1a): единственная реализация WCAG-формулы, импортируется node-гейтом через `require('../helpers/contrast')` и Playwright-спеком; `run-unit-js.cjs` его не перечисляет, поэтому двойного запуска нет.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Node.js | `node:test`-гейт, раннеры | ✓ | `v24.21.0` | — |
| npm | `test:js`, `test:web`, `build` | ✓ | `11.19.0` | — |
| `tailwindcss` (+`@tailwindcss/vite`) | генерация утилит | ✓ | `4.3.3` (в `web/node_modules`) | — |
| `vite` | dev-сервер Playwright (`:5174`) | ✓ | `8.2.2` | — |
| `@playwright/test` | критерии 1/2/4/5 | ✓ | `1.62.1` | — |
| Chromium для Playwright | то же | ✓ | `.playwright-browsers/chromium-1234` | — |
| Порт `127.0.0.1:5174` | проект `web` | ✓ (свободен на момент исследования) | — | `reuseExistingServer` поднимет свой, если порт пуст |
| `uv` | python-тесты (не нужны фазе) | ✓ | `0.10.9` | — |

**Missing dependencies with no fallback:** none
**Missing dependencies with fallback:** none

---

## Validation Architecture

`workflow.nyquist_validation` в `.planning/config.json` отсутствует → раздел обязателен.

### Test Framework

| Property | Value |
|---|---|
| Framework | `node:test` (Node 24.21.0) для CSS/контракта + `@playwright/test` 1.62.1 для DOM/computed style |
| Config file | `scripts/run-unit-js.cjs` (авто-обнаружение `tests/unit/*.js`); `playwright.config.js` (требует правки `testMatch`) |
| Quick run command | `npm run test:js` (≈0.3 s) и `npx playwright test tests/admin-chrome.spec.js --project=web --reporter=line` |
| Full suite command | `npm run test:js` затем `npm run test:web` (`--project=web`, 148 тестов сейчас) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|
| PIPEUI-01 | три поверхности читают «Настройка», URL и `data-testid` не изменились | e2e | `npx playwright test tests/admin-chrome.spec.js -g "naming" --project=web` | ❌ Wave 0 |
| PIPEUI-02 | `#ingest-sources-kind` + 2 инпута: непрозрачный `paper`, `ink-2` текст, `rule` край, ≥ 4.5:1, в обеих темах | e2e | `... -g "select legible"` | ❌ Wave 0 |
| PIPEUI-02 | статика: `border-rule`/`bg-paper`/`text-ink-2` резолвятся в объявленные токены | unit | `npm run test:js` (G-1/G-4) | ❌ Wave 0 |
| PIPEUI-03 | `#ingest-sources-heading` === `Источники`; «ингеста» отсутствует в `web/src` (grep-ассерт опционален) | e2e | `... -g "chrome"` | ❌ Wave 0 |
| PIPEUI-04 | eyebrow отсутствует (`getByText('Админ',{exact:true})` count 1), tab `24px` === heading `24px`, `column-gap 16px > 8`, `margin-top 0`, `nav.top−main.top < 48` | e2e | `... -g "chrome"` | ❌ Wave 0 |
| THEME-01 | пилл `#FFFFFF` на `rgb(124,58,237)`; accent CTA `#FFFFFF` на `rgb(14,116,144)`; `voting` `rgb(15,23,42)` на `rgb(234,179,8)` — в обеих темах, каждое ≥ 4.5 | e2e | `... -g "theme-independent labels"` | ❌ Wave 0 |
| THEME-02 | G-1…G-8 (объявлено / light-override / нет override у плоских / нет `accent-ink` / нет `bg-ink` / нет альфы на `bg-paper*` / контраст значений / алиасы) | unit | `npm run test:js` | ❌ Wave 0 |
| THEME-02 | `--color-paper` существует в рантайме (не пустая строка) | e2e | тот же спек | ❌ Wave 0 |

### Как каждый критерий падает на pre-fix дереве (RED-доказательство)

| Критерий | Проверка | Pre-fix результат (замерено) | Причина падения |
|---|---|---|---|
| 1 | `admin-tab-pipeline` text | `"Пайплайн"` | три литерала не переименованы |
| 1 | `h1` text / `admin-section-select` options | `"Пайплайн"` / `["Дайджест","Пайплайн"]` | то же |
| 2 | `background-color` === `rgb(19, 25, 37)` | `rgba(0, 0, 0, 0)` | `bg-paper` не генерируется → фон наследуется прозрачным |
| 2 | `color` === `rgb(203, 213, 225)` | `rgb(241, 245, 249)` | `text-ink-2` не генерируется → наследуется `text-primary` |
| 2 | `contrastRatio(color, background)` ≥ 4.5 | бросает `transparent surface has no contrast` | фон прозрачен — helper падает до арифметики |
| 3 | G-1…G-8 | падение на первом же `assert.ok(dark.has('--color-paper'))` | все шесть токенов отсутствуют (`getPropertyValue` = `""`) |
| 4 | pill `color` === `rgb(255, 255, 255)` | dark `rgb(241, 245, 249)` / light `rgb(15, 23, 42)` | `text-text-primary` темо-зависим |
| 4 | pill ratio ≥ 4.5 | dark 3.87 / light 4.22 | обе темы проваливаются |
| 4 | accent CTA ratio ≥ 4.5 | dark 2.22 | `text-accent-ink` инертен → наследует `text-primary` |
| 4 | `voting` `color` === `rgb(15, 23, 42)` **и** ratio ≥ 4.5 | dark `rgb(11, 15, 23)` (10.00 ✓) / light `rgb(248, 250, 252)` (**1.83 ✗**) | `text-bg-app` переворачивается; критерий падает в светлой теме — **положительная** проверка исключения, а не пропуск |
| 5 | `getByText('Админ',{exact:true})` count === 1 | **2** | eyebrow `<p>` + shell `<a>` |
| 5 | tab `font-size` === heading `font-size` | `30px` vs `24px` | `text-3xl` |
| 5 | `column-gap` === `16px` | `8px` | `gap-2` |
| 5 | `nav.top − main.top < 48` | `64` | eyebrow 16px + `mt-2` 8px |
| 5 | `#ingest-sources-heading` === `Источники` | `"Источники ингеста"` | текст |

### Sampling Rate

- **Per task commit:** `npm run test:js` (≈0.3 s) + целевой `-g`-прогон `admin-chrome.spec.js`.
- **Per wave merge:** `npm run test:js` и `npm run test:web` (148 + новые).
- **Phase gate:** оба зелёные перед `/gsd-verify-work`; плюс `npm run build`, чтобы убедиться, что CSS собирается.

### Wave 0 Gaps

- [ ] `tests/helpers/contrast.js` — `parseColor` / `relativeLuminance` / `contrastRatio` (бросает на альфе < 1)
- [ ] `tests/unit/test_semantic_token_coverage.js` — G-1…G-8, собственный `parseBlock`, скан `web/src/**/*.{js,jsx}`
- [ ] `tests/admin-chrome.spec.js` — критерии 1, 2, 4, 5 (обе темы)
- [ ] `playwright.config.js` — `testMatch` должен включать `admin-chrome` (иначе файл молча не запускается)
- [ ] `tests/admin.spec.js` — амендменты: `:139/:151`, `:165`, `:274`, `:416`, `:1307`, `:1834`, `:1754-1764`, `:186/:198/:216/:299/:312`

*(Инфраструктура есть: `node:test`, Playwright + браузеры, Vite, `run-unit-js.cjs`. Устанавливать нечего.)*

---

## Security Domain

`security_enforcement` в `.planning/config.json` не выставлен в `false` → раздел обязателен.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | Фаза не касается логина; `RequireAuth`/`/me` не редактируются |
| V3 Session Management | no | Сессия не затрагивается |
| V4 Access Control | no (но pinned) | Guard и маршрут `/admin/pipeline` остаются **байт-идентичными**; `admin.spec.js:1754-1790` продолжает доказывать, что employee не видит админских данных |
| V5 Input Validation | no (косвенно) | Ни одно поле не добавляется и не валидируется в этой фазе; `ingest-sources-id` валидация — серверная, не трогается |
| V6 Cryptography | no | Ничего не хэшируется и не шифруется |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---|---|---|
| Переименование «заодно» меняет маршрут или ослабляет guard (T-25-01) | Elevation of Privilege | `PIPELINE_PATH`, `data-testid`, `handleSectionTabClick`, `useBlocker` — не редактируются; ассерты URL и `aria-current` остаются зелёными |
| CSS-инъекция через имя токена (T-25-02) | Tampering | Имена токенов — статические CSS-идентификаторы в версионируемом файле; ни одного значения из пользовательских данных в `@theme` нет |
| Тинт/скрайм, унаследованный от темо-зависимого токена, маскирует модальное состояние (T-25-03) | Spoofing (UI redress) | `--color-scrim` — тема-независимый `rgba(0,0,0,0.6)`; G-6 запрещает `bg-ink` и альфу на `bg-paper*` |
| Новый тестовый файл не собирается → «доказательство» отсутствует (T-25-04) | Repudiation | `--list`-проверка входит в Wave 0; критерий закрыт только при видимом имени файла в выводе |
| Флейки Playwright выдаются за провал функциональности (T-25-05) | Denial of Service (процесса) | Проверка порта 5174 и `VITE_USE_MOCKS` перед прогоном (Pitfall 8) |

---

## Sources

### Primary (HIGH confidence — прочитано/измерено в этом сеансе)

- `web/src/index.css:7-68` — `@theme static` блок; `:106-121` — `[data-theme="light"]`; `:8` `--color-bg-app: #0B0F17;`; `:19` `--color-primary-hover: #7C3AED;`; `:26` `--color-voting: #EAB308;`
- `web/src/components/AdminLayout.jsx:11-18, 42, 49, 52, 70, 77, 83` — `tabClass`, eyebrow, h1, nav, tab label, select, option
- `web/src/components/IngestSourcesSection.jsx:163-176, 219, 264, 268-276, 308`
- `web/src/components/AppShell.jsx:12-15` — `linkClass`
- `web/src/components/ActionButton.jsx:1-24`
- `web/src/components/UnsavedChangesDialog.jsx:24-58`
- `web/src/components/ThemeToggle.jsx:3, 8-19, 29-35` — `digest-cds-theme`, `setAttribute('data-theme','light')`, `removeAttribute` для dark
- `web/src/pages/KnowledgePage.jsx:266-283`; `AdminPipelineConfigPage.jsx:294-320, 387`; `AdminDigestPage.jsx:794, 808, 821, 885, 919, 948`; `MaterialPage.jsx:187`
- `playwright.config.js:46-56, 60-79` — `webServer.env.VITE_USE_MOCKS`, `baseURL`, `testMatch`
- `tests/unit/test_concept2_canon.js:31-40, 48-56, 150-170`; `tests/unit/helpers/cssRules.js`; `tests/unit/test_design_typography.js:26-56`; `scripts/run-unit-js.cjs`
- `tests/admin.spec.js:23-48, 110-114, 139-167, 186/198/216/274/299/312, 416-417, 439-465, 633-636, 1307-1308, 1754-1764, 1790-1796, 1834`
- `tests/web-app.spec.js:44-64, 280-320` — тема и `/voting` fixture
- `web/dist/assets/index-D0QJWfON.css` — собранный CSS: отсутствие токенов, порядок слоёв, `color-mix` для модификатора прозрачности, `focus-visible:outline-primary`
- Замер headless-Chromium по живому `127.0.0.1:5174` (таблица § Current State)
- `npm run test:js` → `tests 50 / pass 50`; `npx playwright test --list --project=web` → `Total: 148 tests in 5 files`
- `.planning/REQUIREMENTS.md` (PIPEUI-01…04, THEME-01/02), `.planning/STATE.md` (blockers, Vite/5174), `25-CONTEXT.md`, `25-UI-SPEC.md`, `25-DISCUSSION-LOG.md`

### Secondary (MEDIUM confidence — Context7)

- `/websites/tailwindcss` — `@theme static` («always generate all CSS variables, even if unused»); «theme variables are required to be defined top-level and not nested under other selectors or media queries»; `@layer theme, base, components, utilities` order; `@theme inline` + `:root`/`[data-theme]` override pattern

### Tertiary (LOW confidence)

- Нет. Единственное непроверенное поведение (A1, раскрытый список опций) помечено `[ASSUMED]` в Assumptions Log, а не выдаётся за факт.

---

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — версии прочитаны из `web/package.json` и установленного дерева; новых пакетов нет
- Architecture (механика токенов): **HIGH** — порядок слоёв и эмиссия переменных зафиксированы в собранном CSS, семантика `@theme static` подтверждена официальной документацией
- Baseline/значения: **HIGH** — каждое число вычислено независимо (WCAG-формула) или замерено в браузере; расхождение с UI-SPEC одно (1.13 → 1.10) и не влияет на решение
- Pitfalls: **HIGH** — четыре из двенадцати найдены прямым экспериментом (сборка, `--list`, computed style), остальные — чтением кода
- Test harness: **HIGH** для node-гейта (паттерн дважды в репо), **HIGH** для Playwright (фикстуры существуют), **MEDIUM** для A1

**Research date:** 2026-10-21
**Valid until:** ~2026-11-20 (30 дней; Tailwind v4 и Playwright стабильны, но `@theme static` — относительно молодая семантика; при апгрейде `tailwindcss` ≥ 4.4 перепроверить эмиссию неиспользуемых токенов)

---

## RESEARCH COMPLETE

**Phase:** 25 - Admin «Настройка» — naming, readable surfaces, token repair
**Confidence:** HIGH

### Key Findings

- **`admin-chrome.spec.js` сегодня не запускается:** `playwright.config.js:71` `testMatch: /(web-app|auth|knowledge|razbory|admin)\.spec\.js/` (строка 72 рядом — `use.baseURL`) не матчит это имя — `--list` даёт «148 tests in 5 files» без него. Правка конфига обязательна, иначе четыре из пяти критериев не имеют RED'а.
- **Корень нечитаемого `<select>` — прозрачный фон, не белый:** замерено `background-color: rgba(0, 0, 0, 0)` и унаследованный `color` в обеих темах (Tailwind preflight задаёт `select { background-color: transparent; color: inherit }`). Валидный ассерт — равенство объявленному `rgb(19, 25, 37)` / `rgb(255, 255, 255)`, а не «не белый».
- **Механика overrides подтверждена сборкой:** `@layer theme` → `@layer base` (`[data-theme="light"]`) → `@layer utilities`; поэтому light-override перебивает `:root` из `@theme`. Второй блок `@theme`/`[data-theme]` создавать нельзя — `parseBlock` читает только первое вхождение.
- **`tests/admin.spec.js:1834` уже пинит `"Источники ингеста"`** — этой правки нет в таблице амендментов UI-SPEC; без неё PIPEUI-03 останется красным.
- **Все числа UI-SPEC воспроизведены** независимым WCAG-расчётом (включая `danger-solid` 4.8294 → floor 4.829); одно расхождение: шаг заливки `paper` на `paper-2` = 1.10, не 1.13.
- **Гейт критерия 3 живёт в `node:test`** (`tests/unit/test_semantic_token_coverage.js`, авто-обнаружение через `run-unit-js.cjs`), а computed-style половина — в Playwright; общая WCAG-функция — `tests/helpers/contrast.js`, который бросает на полупрозрачном фоне.

### File Created

`.planning/phases/25-admin-nastroyka-naming-readable-surfaces-token-repair/25-RESEARCH.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Версии из `package.json` и `node_modules`; новых зависимостей ноль |
| Architecture | HIGH | Порядок слоёв и эмиссия токенов зафиксированы в собранном CSS + официальная документация Tailwind v4 |
| Pitfalls | HIGH | Четыре найдены экспериментом (build, `--list`, computed style), остальные — чтением кода |

### Open Questions

- A1 **(RESOLVED)**: рисует ли Chromium раскрытый список опций из `color`/`background-color` контрола — остаётся `[ASSUMED]`, но вопрос закрыт как принятое ограничение: доказательство ограничено computed style закрытого контрола + наличием опций (см. § Open Questions, п. 1).

### Ready for Planning

Research complete. Planner can now create PLAN.md files.
