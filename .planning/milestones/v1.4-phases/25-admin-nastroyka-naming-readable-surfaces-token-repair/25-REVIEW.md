---
phase: 25-admin-nastroyka-naming-readable-surfaces-token-repair
reviewed: 2026-10-21T17:35:00Z
depth: standard
scope: "phase 25 end-to-end (25-01…25-07); diff base 0121d7a..HEAD; 21 source files"
files_reviewed: 21
files_reviewed_list:
  - web/src/index.css
  - tests/helpers/contrast.js
  - tests/unit/test_semantic_token_coverage.js
  - tests/admin-chrome.spec.js
  - tests/admin.spec.js
  - playwright.config.js
  - web/src/components/ActionButton.jsx
  - web/src/components/AdminLayout.jsx
  - web/src/components/AppShell.jsx
  - web/src/components/ErrorPanel.jsx
  - web/src/components/IngestSourcesSection.jsx
  - web/src/components/IngestionScheduleSection.jsx
  - web/src/components/SearchPill.jsx
  - web/src/components/ServiceUnavailable.jsx
  - web/src/components/UnsavedChangesDialog.jsx
  - web/src/pages/AdminDigestPage.jsx
  - web/src/pages/AdminPipelineConfigPage.jsx
  - web/src/pages/KnowledgePage.jsx
  - web/src/pages/LoginPage.jsx
  - web/src/pages/RegisterPage.jsx
  - web/src/pages/VotingPage.jsx
findings:
  critical: 0
  warning: 7
  info: 6
  total: 13
status: issues_found
---

# Phase 25: Code Review Report (Настройка / readable surfaces / token repair)

**Reviewed:** 2026-10-21T17:35:00Z
**Depth:** standard
**Files Reviewed:** 21
**Status:** issues_found
**Scope:** сквозное ревью фазы 25 (25-01…25-07), `0121d7a..HEAD`, с усиленным вниманием к трём gap-closure планам (25-05, 25-06, 25-07) и к вопросу «гейт способен упасть?».

## Summary

Основная работа фазы сделана и проверена не по описанию, а по артефактам:

- `npm run test:js` → **89 passed, 0 failed** (включая все гейты G-0…G-19).
- `web/src/index.css` действительно объявляет четыре новых роли (`--color-success-ink`, `--color-voting-ink-on-tint`, `--color-accent-text`, `--color-field-border`); три первые переопределены под `[data-theme="light"]`, `field-border` — плоская по замыслу, и `G-3`/`G-15` это удерживают.
- Миграции семантически верны там, где их видно: статусные подписи (`text-success-ink`, `text-voting-ink-on-tint`, `text-danger-ink`), accent-подписи (`text-accent-text`) и границы полей (`border-field-border`) применены к своим ролям; разделители (`border-rule`) остались декоративными; `admin-toast` переехал на `bg-paper-2`/`text-ink`/`border-rule` (1.00:1 → 9.13/6.51:1); `ActionButton` теперь эмитит ровно один fill.
- `blendOver()` арифметически корректен для всех заявленных входов: alpha 0/1 нормализуется в `rgb(...)`, собственная альфа тинта игнорируется (как и задокументировано), полупрозрачная база отвергается, `NaN`/вне-диапазона альфа бросает, округление по каналам совпадает с sRGB-композитингом браузера (проверено на закреплённых 216/242/228 и на 1.925).
- Порядок альтернаций в `UTILITY_PATTERN` **корректен**: `paper-2` до `paper`, `ink-2` до `ink`, `voting-ink-on-tint`/`success-ink`/`accent-text` до `ink`, поэтому `text-success-ink` не читается как `text-success`, а `border-field-border` разрешается в `field-border`. Претензий нет.

Чего фаза не закрыла — это **доказуемость** части гейтов и один системный пробел в ролях подписей:

1. Три гейта (G-16 R1, G-16 R3, G-14) остаются зелёными на регрессиях, которые они обязаны ловить. Это проверено мутациями в песочнице-копии (репозиторий не менялся): удаление всех цветовых проверок тоста, альтернация внутри `hasText:`/`getByRole({name:})` и смена `bg-success/15` на `/60` не роняют `npm run test:js`.
2. `--color-primary` используется как роль подписи в 100+ местах (включая шесть сайтов этой фазы), но не входит ни в одну матрицу контраста: 3.756…4.234:1 — ниже 4.5 в обеих темах.
3. Единственный визуальный индикатор радио — декоративная `border-border` (1.18 светлая / 1.55 тёмная): G-17 определяет «control» как `input|select|textarea` и слепа к `role="radio"`.

Критических находок (уязвимость, потеря данных, падение) нет. Ниже — предупреждения и информационные пункты.

Нумерация продолжает предыдущий раунд (`WR-07…`, `IN-06…`), чтобы не конфликтовать с `25-REVIEW-DISPOSITION.md`, где уже зафиксированы `CR-01`, `WR-01…WR-06`, `IN-01…IN-05`.

## Narrative Findings (AI reviewer)

### Critical Issues

Не найдено. Ни одна находка не даёт уязвимости, потери данных или падения; контрастные дефекты ниже классифицированы как warning (см. обоснование в WR-07).

### Warnings

#### WR-07: `text-primary` — самая частая роль подписи — не проходит 4.5:1 и не покрыта ни одним гейтом

**File:** `web/src/components/ActionButton.jsx:44`; `web/src/pages/AdminDigestPage.jsx:541`, `:728`, `:748`, `:776`, `:849`; `web/src/pages/AdminPipelineConfigPage.jsx:242`, `:370`; `web/src/pages/KnowledgePage.jsx:363`; `web/src/pages/VotingPage.jsx:67`
**Issue:** `--color-primary` (`#8B5CF6`, без light-переопределения) используется как **текстовая** роль на прозрачном фоне и на карточках:

| поверхность | тема | ratio |
|---|---|---|
| `bg-app` `#F8FAFC` | light | **4.047** |
| `paper` `#FFFFFF` | light | **4.234** |
| `bg-surface` `#131925` | dark | **4.156** |
| `paper-2` `#1A2233` | dark | **3.756** |
| `bg-app` `#0B0F17` | dark | 4.529 |

`text-sm` (14px, вес 500) не является «large text», поэтому порог — 4.5:1. Все перечисленные сайты (ссылки «Сделать ready», «Превью материала», «Повторить превью», «К выпуску →», «Обновить список», secondary-вариант `ActionButton`, «Сбросить фильтр») ниже порога минимум в одной из тем. Это ровно тот дефект, который фаза закрыла для `text-accent` (2.43:1) — та же семья, тот же базовый токен в роли подписи, — но `G-19` банит только `accent`, а `G-7` перебирает лишь `ink`/`ink-2`/`muted`/`danger-ink`. Более того, комментарий в `index.css:80-82` декларирует: «labels ride `ink`, `ink-2` or the `-ink` label roles» — `text-primary` этому контракту не соответствует, и ничто этого не проверяет.
**Fix:** ввести отдельную роль подписи и перевести на неё текстовые употребления; значения проверены на всех трёх базах:

```css
/* @theme */                 --color-primary-text: #A78BFA; /* 7.05 / 6.47 / 5.84 на bg-app / paper / paper-2 */
/* [data-theme="light"] */   --color-primary-text: #6D28D9; /* 6.79 / 7.11 / 6.49 там же */
```

Добавить пару в `THEMED` и в матрицу `G-7`, а `text-primary` внести в `FORBIDDEN_*`-скан по аналогии с `G-19` (заливки `bg-primary` остаются легальными). Минимум — расширить `G-7` на `text-primary`, чтобы текущее значение хотя бы перестало быть невидимым.

#### WR-08: `G-16` R3 («тост проверяется цветом») не может упасть — проверка идёт по тексту файла, а не по тосту

**File:** `tests/unit/test_semantic_token_coverage.js:555-570` (в паре с `tests/admin-chrome.spec.js:148-156`)
**Issue:** `toastReaders` отбирает спеки, где встречается строка `admin-toast`, после чего требует, чтобы **в этом же файле** встречались подстроки `backgroundColor` и `borderTopColor`:

```js
const missing = ['backgroundColor', 'borderTopColor'].filter(
  (property) => !source.includes(property),
)
```

В `admin-chrome.spec.js` обе подстроки уже есть в хелпере `styleTriple()` (`:148-156`, `backgroundColor: cs.backgroundColor`) и в тестах pill/CTA. Поэтому условие выполняется независимо от того, читает ли кто-нибудь цвета тоста.

Проверено мутацией: в копии спеки блок `const toastPair = await styleTriple(toast)` … `toBeGreaterThanOrEqual(4.5)` (525 символов, включая все три цветовых `expect`) заменён на `await expect(toast).toHaveText("Не сохранено")` — `npm run test:js` остался **зелёным**, `G-16` не упал. То есть заявленный в комментарии контракт «R3: `admin-toast` is checked at least once, by its computed colours» кодом не обеспечен.
**Fix:** привязать проверку к самому тосту, а не к файлу — например, искать `getByTestId("admin-toast")` и требовать, чтобы `backgroundColor`/`borderTopColor` встречались в пределах ±15 строк от него, либо (надёжнее) перенести инвариант в спеку: `assert` внутри `expect(toast).toHaveJSProperty`/отдельный `test` в `admin-chrome.spec.js`, который читает оба свойства, — а гейт пусть проверяет наличие именно такой композиции (`admin-toast` + `borderTopColor` в одном `evaluate`-блоке).

#### WR-09: `G-16` R1 не видит альтернацию внутри `hasText:` и `getByRole({ name: … })` — самый вероятный способ схлопнуть два исхода

**File:** `tests/unit/test_semantic_token_coverage.js:485-486`
**Issue:** `REGEX_ASSERTION` распознаёт регулярку только сразу после `toMatch|toContainText|toHaveText|getByText`:

```js
const REGEX_ASSERTION =
  /\b(toMatch|toContainText|toHaveText|getByText)\s*\(\s*\/((?:\\\/|[^/\n\\]|\\.)+)\/([a-z]*)/g
```

`hasText`, `name`, `toHaveAccessibleName`, `filter({ hasText })` в списке нет — а именно `filter({ hasText: … })` является идиомой этого набора спек (см. `tests/admin.spec.js:946`, `:982`). Проверено мутациями:

| мутация | `G-16` |
|---|---|
| `toHaveText(/Уже отправлено\|Выпуск опубликован/)` | **падает** ✅ |
| `getByText(/Выпуск опубликован\|Уже отправлено/)` | **падает** ✅ (по правилу «одна строка — два исхода») |
| `getByRole("status").filter({ hasText: /Выпуск опубликован\|Рассылка не отправлена/ })` | **зелёный** ❌ |
| `getByRole("heading", { name: /Уже отправлено\|Не сохранено/ })` | **зелёный** ❌ |

То есть ровно тот дефект, который описывает `T-25-16` («one assertion, one outcome»), воспроизводится в естественной для Playwright форме и остаётся незамеченным.
**Fix:** либо расширить альтернацию до `(toMatch|toContainText|toHaveText|getByText|hasText|name|toHaveAccessibleName)`, либо отказаться от регэксп-эвристики и разбирать все regex-литералы файла (`/….…/`) независимо от вызываемой функции, оставив особый случай только для комментариев. Первое — минимальная правка, второе — устойчивее.

#### WR-10: `G-14` (и спека пилюль) измеряют захардкоженную альфу, а не ту, что стоит в классах

**File:** `tests/unit/test_semantic_token_coverage.js:113-117`, `:924-958`; `tests/admin-chrome.spec.js:379`, `:409`, `:413`
**Issue:** `STATUS_LABEL_TINTS` фиксирует `alpha: 0.15 / 0.2 / 0.1`, а спека дублирует это в `const tintAlpha = { success: 0.15, voting: 0.2 }`. Ничто не связывает эти числа с фактическими `bg-success/15`, `bg-voting/20`, `bg-danger/10` в компонентах. Проверено мутацией: замена в `AdminDigestPage.jsx` `bg-success/15` → `bg-success/60` оставляет `npm run test:js` **зелёным**, хотя реальный композит становится `rgb(120, 218, 157)` и `success-ink` на нём даёт **4.181** (на `paper-2` — **4.094**), то есть ниже 4.5. Комментарий в спеке «the ratio is taken on the composite — the same arithmetic G-14 uses statically» создаёт ложное впечатление, что измеряется реальный фон элемента.
**Fix:** читать альфу из класса/из DOM, а не из константы. Минимальный вариант в спеке:

```js
expect(await classTokens(readyPill)).toContain("bg-success/15")
```

Вариант лучше: вытащить альфу из `getComputedStyle(el).backgroundColor` (Chrome отдаёт `oklab(… / 0.15)`) либо измерять контраст по реальному скриншоту/`color-mix`-резолву. В юнит-гейте — производный словарь `{ ink, tint, alpha }`, собираемый из классов `web/src`, чтобы `G-14` падал при дрейфе альфы.

#### WR-11: у радио нет границы 3:1 — G-17 определяет «control» только как `input|select|textarea`

**File:** `tests/unit/test_semantic_token_coverage.js:259`; evidence: `web/src/components/TopicBallot.jsx:23-28`
**Issue:** `CONTROL_TAG_START = /<(input|select|textarea)(?=[\s/>])/g` покрывает 16 элементов — и ровно их перекрасил 25-07. Но единственный визуальный индикатор выбора темы — кружок внутри `<button role="radio">`:

```jsx
<span className={['mt-1 inline-block size-5 rounded-full border-2',
  checked ? 'border-primary bg-primary' : 'border-border bg-bg-app'].join(' ')} aria-hidden="true" />
```

Невыбранное состояние — это `border-border` 2px на `bg-bg-app`: **1.178:1** в светлой теме (`#E2E8F0` на `#F8FAFC`) и **1.554:1** в тёмной (`#2A3548` на `#0B0F17`). Для сравнения: текст рядом даёт 4.5+, поэтому дефект не в читаемости подписи, а именно в границе компонента — WCAG 1.4.11 требует 3:1 для визуальной информации, необходимой для идентификации контрола, и здесь это единственная такая информация (у кружка нет текста внутри). Это обратная сторона той же ошибки, которую закрывал 25-07: декоративный `rule` остался границей контрола. Кнопки с текстовыми подписями (`border-rule` в `IngestionScheduleSection`) сюда не относятся — их идентифицирует текст; кружок радио — относится.
**Fix:** `... checked ? 'border-primary bg-primary' : 'border-field-border bg-bg-app'` (3.698/3.342/4.030 dark и 4.759/4.344/4.548 light — уже доказано `G-15`). Дополнительно расширить определение контрола в `G-17`: `input|select|textarea` **или** элемент с `role="radio"|"checkbox"|"switch"` + `aria-hidden`-индикатор внутри, иначе следующая правка вернёт `border-rule` безнаказанно.

#### WR-12: провал отправки красится success-ролью

**File:** `web/src/pages/AdminDigestPage.jsx:462` (значение) и `:771` (класс)
**Issue:** один и тот же `<p role="status">` печатает и успех (`'Выпуск опубликован'`, `'Уже отправлено'`), и отказ (`setBanner('Рассылка не отправлена')`), а класс у него — `text-success-ink`. То есть сообщение об ошибке рендерится зелёным (в light `#166534`, dark `#4ADE80`). Миграция 25-06 перевела элемент с `text-success` на `text-success-ink` и сохранила семантическую ошибку: статус-токен выбран по «ветке успеха», а не по фактическому исходу. `G-16` этот литерал явно исключает из R2 («no harness arm»), поэтому ни статический гейт, ни `admin-chrome.spec.js` (там проверяется только успешный баннер) этого не видят.
**Fix:** разделить роль по исходу, например:

```jsx
<p className={`mt-1 text-sm font-medium ${bannerKind === 'error' ? 'text-danger-ink' : 'text-success-ink'}`} role="status">
```

с `setBanner({ kind: 'error', text: 'Рассылка не отправлена' })`; и добавить в `admin-chrome.spec.js` кейс на отказ (`armFailNextSend` уже есть в харнессе — `main.jsx:82`), проверяющий `color` баннера. Литерал при этом перестанет быть «непроверяемым исключением».

#### WR-13: в `gotoAdmin` остался условный страж темы, а `webServer` переиспользует чужой dev-сервер

**File:** `tests/admin-chrome.spec.js:40-58`; `playwright.config.js:30-53`
**Issue:** Два независимых риска стабильности:

1. Ожидание темы выполняется только если в момент сэмпла найден `theme-toggle` (`:50-58`). Один `page.evaluate` — это гонка: если разметка на первом коммите ещё не содержит тоггл (например, `RequireAuth` с `VITE_REQUIRE_LOGIN`, lazy-route, будущий рефакторинг оболочки), `mountsToggle === false`, ожидание молча пропускается, и `expect(...).toBe("rgb(255, 255, 255)")` в light-ветке читает тёмную тему. Сейчас `AppShell` монтируется синхронно (`web/src/App.jsx:40-44` + мок-режим `RequireAuth`), поэтому зелено, но инвариант держится на свойстве, которое тест не проверяет. Дополнительно `await page.evaluate(() => document.fonts.ready)` (`:40`) ждёт сетевую загрузку Google Fonts; офлайн-прогон зависит от таймаута фетча, а не от теста.
2. `reuseExistingServer: !process.env.CI` (`playwright.config.js:38`, `:49`) означает, что локально Playwright может подключиться к уже запущенному `npm run dev` **без** `VITE_USE_MOCKS=true` (env задаётся только для собственного процесса, `:46-49`). Тогда «offline proof» из комментария не действует, а падение будет выглядеть как продуктовое.

**Fix:** сделать ожидание темы безусловным для страниц, где `ThemeToggle` гарантированно есть (параметр `expectsToggle` в `gotoAdmin` для `/admin/*`, `/voting`, `/knowledge`), а для auth-страниц — явный `forceTheme` (он уже есть, но применяется после `gotoAdmin`): тогда условие «смонтирован ли тоггл» вообще не нужно. Для шрифтов — заменить на `document.fonts.status === 'loaded'` c коротким таймаутом либо убрать ожидание (проверяются `font-size`, а не метрики шрифта). Для сервера — `reuseExistingServer: false` на порту 5174 либо отдельный порт для proof-прогона.

### Info

#### IN-06: комментарий «the seven theme-independent roles» устарел — их восемь

**File:** `web/src/index.css:167-170`
**Issue:** «*The seven theme-independent roles are deliberately absent*» — после 25-05 плоских ролей восемь: `primary-solid`, `accent-solid`, `success-solid`, `danger-solid`, `on-solid`, `voting-ink`, `scrim`, **`field-border`** (последний сам объявлен как «deliberately **not** theme-dependent» строкой выше, `:76-80`). `FLAT` в гейте содержит ровно 8 элементов, то есть комментарий противоречит коду и собственной декларации.
**Fix:** «the eight theme-independent roles» (или перечислить их поимённо, чтобы список нельзя было промахнуться при следующем добавлении).

#### IN-07: `--color-xp-text` объявлен дважды с одинаковым значением

**File:** `web/src/index.css:24` и `:186`
**Issue:** `--color-xp-text: #1A2E05` есть и в `@theme`, и в `[data-theme="light"]` с тем же значением. Это ровно тот шаблон, который `G-2` считает дефектом («light value equals the dark value»), просто токен не входит ни в `THEMED`, ни в `FLAT`, поэтому гейт молчит. Плюс токен нигде не потребляется (gamification отложена ADR-0007/0009), то есть это ещё и мёртвая декларация.
**Fix:** удалить строку `:186`; если токен нужен как контракт — добавить в `FLAT`, чтобы `G-3` запрещал переопределение.

#### IN-08: контракт «never paint text with `field-border`» ничем не проверяется

**File:** `web/src/index.css:80-82`; `tests/unit/test_semantic_token_coverage.js:66-73`
**Issue:** Комментарий объявляет жёсткое правило («Non-text boundary role only — never paint text with `field-border`»), но `UTILITY_PATTERN` включает `text-` как префикс и `field-border` как имя, поэтому `G-4` спокойно пропустит `text-field-border` (токен объявлен), а `G-17` проверяет только `border-field-border`. Правило держится на дисциплине, а не на гейте — при этом сама фаза строилась на тезисе «контракт без гейта = контракта нет».
**Fix:** добавить запрет по аналогии с `G-19`: `FORBIDDEN_LABELS = ['field-border']` для префикса `text` (+ proof-тест), либо убрать декларацию из CSS, если правило не является обязательным.

#### IN-09: `readJsxOpeningTag` молча выбрасывает контрол, а анти-вакуумный порог ровно равен текущему числу

**File:** `tests/unit/test_semantic_token_coverage.js:259-290`, `:1185-1192`
**Issue:** если сканер не находит `>` на нулевой глубине, `controlTags()` делает `continue` — тег исчезает из проверки без единого сообщения. `assert.ok(controlCount >= 16)` защищает только от массовой слепоты: сегодня в дереве ровно 16 контролов, поэтому один «ослепший» тег маскируется одним добавленным. Плюс `controlClassNames` (используется как allow-list для `decorativeBoundaryOffences`) собирается глобально: любой литерал, встретившийся как `className` контрола **где угодно**, освобождает такой же литерал на декоративном элементе.
**Fix:** сделать `return null` фатальным (`offenders.push('unparsed control tag at …')`), поднять порог до фактического числа с запасом (`>= 16` → точное равенство по файлам-владельцам или `>= 16` + отдельный assert «нет unparsed»), а allow-list сузить до `(файл, литерал)` вместо глобального множества.

#### IN-10: мёртвый проп `_onLoadError` и разнобой focus-ring токенов

**File:** `web/src/components/IngestionScheduleSection.jsx:35`; `web/src/components/IngestSourcesSection.jsx:270`, `:282`, `:296`; `web/src/components/AdminLayout.jsx:74`
**Issue:** `onLoadError: _onLoadError` деструктурируется и нигде не вызывается, хотя `AdminPipelineConfigPage.jsx:284` его передаёт (`onLoadError={setScheduleError}`) — мёртвый контракт между компонентом и страницей. Отдельно: 25-07 перевёл focus-ring мобильного селекта на `focus-visible:outline-primary`, а три поля «Источников» остались на `focus-visible:outline-accent` — один и тот же контроль-тип мигает разными кольцами в одном экране (оба варианта легальны для `G-19`, поэтому гейт разнобой не заметит).
**Fix:** удалить проп из сигнатуры и из вызывающей стороны (или начать его использовать — например, для сообщения о падении PATCH); выбрать один токен кольца (по UI-SPEC это, судя по `AdminLayout`, `outline-primary`) и применить его во всех 16 контролах.

#### IN-11: открытые пункты прошлого раунда, которые остаются в силе

**File:** `web/src/pages/AdminDigestPage.jsx:444`, `:776`; `web/src/index.css:121-132`; `tests/unit/test_semantic_token_coverage.js:97`, `:163-165`, `:722-728`
**Issue:** Ревью прошлого раунда закрыло `CR-01`, `WR-01`(hole 1), `WR-02`, `WR-03`, `WR-05`, `WR-06`; перечисленное ниже было отложено и по-прежнему не исправлено (проверено по текущему коду):

- `issue_url` по-прежнему принимается любой строкой (`setIssueUrl(typeof result.issue_url === 'string' ? result.issue_url : '')`) и уходит в `<Link to={issueUrl}>`; middle-click/`ctrl`-click последует за `javascript:`- или внешним URL, если ответ API окажется подконтрольным. Санитайзер того же вида уже есть: `sanitizeReturnUrl` (`services/authEnv.js`).
- `.sr-only` в `@layer utilities` дублирует встроенную утилиту Tailwind v4; утверждение `boundingBox().width <= 1` в `admin-chrome.spec.js:189-191` держится на локальной копии, а не на фреймворке.
- `assert.ok(worst >= 4.829)` остаётся change-detector’ом: значение пересчитывается из тех же деклараций, которые охраняет, и не поймает, например, `#DC2625`.
- `THEME_DEPENDENT_LABELS` (`:97`) по-прежнему содержит `text-accent-ink` (запрещён `G-5`, в дереве отсутствует) и `text-bg-app` (после миграции на `text-voting-ink` потребителей нет): список рекламирует три запрета, реально работает один.
- Докстринг `stringLiterals` (`:163-165`) утверждает «scanning literals is both complete»; для склеенных списков (`[...].join(' ')`, `variantClass` + `stateFill`) fill и label лежат в разных литералах и не сравниваются — та самая вторая дыра `WR-01` прошлого раунда. Сегодня она не стреляет (25-07 сделал fill взаимоисключающим), но заявление в комментарии ложное.
**Fix:** либо закрыть каждый пункт профильной правкой (санитайзер URL, удаление `.sr-only`, `assert.equal(dark.get('--color-danger-solid'), '#DC2626')`, чистка `THEME_DEPENDENT_LABELS`, склейка литералов одного `join` перед `tokenSet`), либо переписать комментарии так, чтобы они описывали фактическую силу проверки. Второе дешевле, но оставляет четыре известные слепые зоны.

---

## Как проверялось

- `npm run test:js` на рабочем дереве → 89 passed / 0 failed.
- Мутационное тестирование гейтов выполнялось на копии (`web/src` + `tests`) вне репозитория; исходники не изменялись. Результаты: `G-14` и `G-18` падают при удалении light-override и при `text-success-ink → text-success`; `G-17` падает при возврате `border-field-border → border-border` на `<input>`; `G-19` падает при `text-accent-text → text-accent`; `G-16` падает на альтернации в `getByText`/`toHaveText`, но **не** падает на альтернации в `hasText`/`name` (WR-09) и **не** падает при удалении цветовых проверок тоста (WR-08); `G-14` **не** падает при смене альфы тинта `/15 → /60` (WR-10).
- Контрастные значения получены тем же `tests/helpers/contrast.js`, которым пользуются гейты (включая `blendOver` для композитов).

---

_Reviewed: 2026-10-21T17:35:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
