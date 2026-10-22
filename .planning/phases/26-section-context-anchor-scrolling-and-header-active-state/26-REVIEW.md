---
phase: 26-section-context-anchor-scrolling-and-header-active-state
reviewed: 2026-10-22T06:20:00Z
depth: standard
scope: "phase 26 end-to-end (26-01…26-03); diff base 8a6d388..HEAD; 12 source files"
files_reviewed: 12
files_reviewed_list:
  - tests/admin.spec.js
  - tests/unit/test_section_context_gates.js
  - tests/web-app.spec.js
  - web/src/components/AppShell.jsx
  - web/src/components/IssueToc.jsx
  - web/src/components/MaterialListRow.jsx
  - web/src/data/mock.js
  - web/src/index.css
  - web/src/pages/ArchivePage.jsx
  - web/src/pages/IssuePage.jsx
  - web/src/pages/KnowledgePage.jsx
  - web/src/pages/MaterialPage.jsx
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 26: Code Review Report (section context — anchor offset + header active state)

**Reviewed:** 2026-10-22T06:20:00Z
**Depth:** standard
**Files Reviewed:** 12
**Status:** issues_found
**Scope:** сквозное ревью фазы 26 (`8a6d388..HEAD`), контракт `26-UI-SPEC.md` (C-00…C-20), locked decisions D-01…D-11, критерии NAV-01/NAV-02. Проверялось не «сделано ли», а «что сломается и какой гейт это пропустит».

## Summary

Механика фазы в основе верна, и это проверено живьём, а не по описанию:

- **NAV-01.** `scroll-padding-top: calc(var(--header-height) + 1rem)` объявлен ровно один раз (`web/src/index.css:152`), мобильный токен — один блок `@media (max-width: 639.98px)` внутри `@layer base` (`:159-163`). Измерено на dev-сборке (1280×800): `pad = 80px` при `header = 72.6px`, после клика по первой ссылке «Содержания» `gap = 6.5px`, `heading.bottom = 111.5 ≤ 800`. На 390: `pad = 216`, `gap = 18.75`. Продакшн-сборка сохраняет и правило, и медиа-блок (`web/dist/assets/index-*.css`).
- **NAV-02.** Маркер доезжает по всем четырём стрелкам и **не протекает**: проверены back/forward (`usr` возвращается вместе с записью истории), F5 (сохраняется — задокументированное поведение D-07…D-10), переход по `<Link>` без `state` (`usr: null` — стейл не остаётся), админ-превью (`usr` отсутствует). Класс и `aria-current` совпадают на всех проверенных локациях; «Админ» не конфликтует. `aria-current` не выводится из URL нигде, кроме `/issues/` (D-10).
- **Гейты существуют и зелёные:** `npm run test:js` → 108/108 (включая статические гейты, читающие сырой текст `index.css`, а не разобранный парсером CSS), NAV-спеки покрывают все стрелки и все шесть rect-сценариев. Где именно гейт не способен упасть — см. WR-02…WR-05.

Найден один критический дефект (регрессия поведения `NavLink`, которую заменили ручным сравнением строк) и пять предупреждений — в основном «гейты, которые не могут упасть» и один вакуумный `expect.poll` в шести NAV-01 тестах. Принятые фазы остатки (положительный зазор ≈7px на 1280 и отрицательный в полосе 640–999) не переоткрываются.

Методика: чтение диффа + два прогона живых проб на `127.0.0.1:5174` (Vite dev, `VITE_USE_MOCKS=true`) — обмер шапки/офсета на 320/390/639/640/768/1024/1280 и обход цепочек навигации с чтением `history.state.usr`, `aria-current` и токенов класса.

## Critical Issues

### CR-01: Ручное сравнение `pathname` потеряло семантику `NavLink` — раздел гаснет на валидных URL

**File:** `web/src/components/AppShell.jsx:49-52`
**Issue:** Три пилла переведены с `NavLink` на `pathname === '/archive'` / `=== '/knowledge'` / `=== '/'` и `pathname.startsWith('/issues/')`. `NavLink` определял активность через `matchPath`, который **нормализует хвостовой слэш и нечувствителен к регистру**; равенство строк — нет. Маршрутизатор при этом такие URL по-прежнему матчит, то есть страница рендерится, а раздел в шапке «не заявлен ни одним» — ровно тот класс дефекта, который фаза чинит.

Воспроизведено на текущем дереве (`page.goto` в свежем контексте, 1280×800):

| URL | `main h1` | зажжённые пиллы |
|---|---|---|
| `/archive` | Архив | Архив `page` |
| `/archive/` | **Архив** (`archive-page` виден) | **нет ни одной** |
| `/Archive` | **Архив** | **нет ни одной** |
| `/knowledge/` | **База знаний** (`kb-role-chips` видны) | **нет ни одной** |
| `/Knowledge` | **База знаний** | **нет ни одной** |
| `/issues/13/` | — | Архив `true` (префикс спасает) |

До фазы `NavLink to="/archive"` на `/archive/` был активен. Дефект достижим вставкой URL с хвостовым слэшем (частый артефакт копирования ссылки) либо капитализацией; `end` у `/` в предыдущем коде был задан явно и проблему `/` не создаёт.

**Fix:** не сравнивать строки руками, а спросить роутер — это возвращает ровно ту семантику, что была у `NavLink`, и не заводит второго способа матчить маршруты:

```jsx
import { Link, matchPath, NavLink, Outlet, useLocation } from 'react-router-dom'
// ...
const homeRoute = Boolean(matchPath({ path: '/', end: true }, pathname))
const archiveRoute = Boolean(matchPath({ path: '/archive', end: true }, pathname))
const baseRoute = Boolean(matchPath({ path: '/knowledge', end: true }, pathname))
const issuesBranch = Boolean(matchPath({ path: '/issues/:number' }, pathname))
```

`useMatch('/archive')` — равнозначная замена. Пины C-15 честно останутся зелёными, а таблица выше перестанет врать. Тест, который это ловит, стоит добавить рядом с C-15: `goto('/archive/')` и `goto('/knowledge/')` → `aria-current="page"` (сегодня оба красные).

## Warnings

### WR-01: Три претензии на пилл считаются аддитивно — взаимная исключительность не гарантирована конструкцией

**File:** `web/src/components/AppShell.jsx:54-58`
**Issue:** `homeLit` / `archiveLit` / `baseLit` — три независимых дизъюнкции «маршрут ИЛИ маркер». Приоритета нет, поэтому пара «маршрут пилла + чужой маркер» зажигает **два** пилла. Проверено: сегодня такая пара недостижима (единственные ссылки на `/`, `/archive`, `/knowledge` — `AppShell`, `MaterialPage` «← К выпуску»/«В архив», `IssuePage` «В текущий/В архив», `Navigate replace` — все без `state`), но инвариант C-20 держится на дисциплине вызывающих, а не на коде. Один будущий `<Link to="/" state={{ section: 'archive' }}>` (или `<Navigate state=…>`) молча даст две заливки, и C-20 это не поймает: он смотрит только `/` и `/issues/13`, где маркер чужого раздела неоткуда взять.

**Fix:** свести к одному значению с приоритетом маршрута — тогда «две заливки» невозможны по построению:

```jsx
const routeSection = homeRoute ? 'issue' : archiveRoute || issuesBranch ? 'archive' : baseRoute ? 'base' : null
const claimed = routeSection ?? SECTION_MARKERS[section] // SECTION_MARKERS = новый Map/Set из трёх литералов, а не объект-литерал
const homeLit = claimed === 'issue'
const archiveLit = claimed === 'archive'
const baseLit = claimed === 'base'
```

(Как и сейчас, `section` вне закрытого списка обязан не зажигать ничего — поэтому именно `Map`/`Set`, а не `{ 'archive': … }[section]`, где `'constructor'` вернёт функцию.)

### WR-02: C-08 не может упасть, если убрать проброс из `ArchivePage` — стрелка D-08 недоказана

**File:** `tests/web-app.spec.js:1020-1037`, `web/src/pages/ArchivePage.jsx:70-75`
**Issue:** C-08 проходит `/archive` → карточка выпуска → `/issues/13` и требует `aria-current="true"` у «Архива». На `/issues/13` этот пилл уже зажжён префиксом `issuesBranch` (`AppShell.jsx:51,55`), а `IssueToc` выводит свой маркер из `isCurrent` (`IssuePage.jsx:188`), а не из полученного состояния. Значит `state={{ section: 'archive' }}` в `ArchivePage` **не читается ни одной строкой кода** (единственные потребители `state.section` — `AppShell` и `MaterialPage`), и тест зелен ровно так же, если этот проброс удалить. C-14 (прямой `/issues/13`) тоже опирается только на префикс. То есть из четырёх стрелок D-08 три доказаны поведенчески (C-09, C-10, C-11, C-12), а первая — нет.

**Fix:** либо доказать её напрямую, проверив запись истории после клика (это единственное наблюдаемое следствие маркера на `/issues/:number`):

```js
expect(await page.evaluate(() => history.state.usr)).toEqual({ section: 'archive' })
```

либо признать проброс избыточным и убрать его из `ArchivePage` вместе с упоминанием в D-08 (но тогда придётся переписать C-07/C-08 в UI-SPEC: «маркер на `/issues/:number` не передаётся, раздел заявлен префиксом»). Держать одновременно недоказуемый код и тест, который его не проверяет, — худший из трёх вариантов.

### WR-03: `expect.poll(... gap >= 1)` в шести NAV-01 тестах не ждёт скролла — условие истинно ещё до клика

**File:** `tests/web-app.spec.js:777-778, 813-814, 852-853, 895-896, 931-932, 960-961`
**Issue:** Полл создан как барьер «дождаться, пока браузер прокрутит к цели», но зазор `heading.top − header.bottom` при `scrollY = 0` уже положителен во всех фикстурах (цель лежит ниже шапки), поэтому первая же проверка проходит и полл возвращается мгновенно. Измерено: C-02 до клика `heading.top = 396.5`, `header.bottom = 72.6` → `gap ≈ 324` (полл зелёный без скролла). Следующая строка — обычный (не retry) `expect(...).toBeLessThanOrEqual(32)`, то есть тест меряет геометрию сразу после `click()` и держится на том, что фрагментная навигация в Chromium синхронна внутри обработчика.

Последствия:
- Если скролл когда-нибудь станет асинхронным (кто-то добавит `scroll-behavior: smooth` — статический гейт его ловит, но обходной путь через `scrollIntoView({ behavior })` в компоненте не ловится), C-02/C-03/C-06 начнут падать **не по той причине**, а C-02b начнёт «плавать».
- C-05 claim 3 при 639×844 сегодня **вакуумна по отношению к скроллу**: до клика `heading.top = 808.5`, `bottom ≈ 840.5 ≤ 844`, `gap ≈ 685` — все три условия claim 3 выполнены ещё до клика. Если клик ничего не сделает (сломанный `href`, `preventDefault`), тест останется зелёным.
- C-04 claim 3 не вакуумна (на 390 цель `top = 971.75` ниже фолда), но держится на той же синхронности.

**Fix:** поллить итоговое условие, а не заведомо истинное промежуточное, и требовать доказательство факта прокрутки:

```js
await link.click()
await expect
  .poll(async () => (await gapAfterScroll(page, anchorId)).gap)
  .toBeLessThanOrEqual(32)          // поститог, а не «уже верный» >= 1
expect(await page.evaluate(() => window.scrollY), 'клик обязан прокрутить').toBeGreaterThan(0)
```

### WR-04: «Анти-вакуумные» претензии гейта C-17 выполнены посторонними вхождениями

**File:** `tests/unit/test_section_context_gates.js:188-196`
**Issue:** Гейт утверждает «AppShell must feed the marker into aria-current, not into className» и «must reuse linkClass for the fill», но проверяет `count(shell, 'aria-current') >= 1` и `count(shell, 'linkClass') >= 1`. В `AppShell` четыре атрибута `aria-current` (три раздела + «Админ» с WR-02) и семь вхождений `linkClass`; удаление `aria-current` у всех трёх разделов или сборка класса руками (`className={['inline-flex …', lit && 'bg-primary-solid text-on-solid'].join(' ')}`) оставят обе претензии зелёными. Это ровно тот случай, который комментарий называет «anti-vacuum», то есть гейт не делает того, ради чего написан.

**Fix:** проверять выражение, а не подстроку-счётчик:

```js
assert.equal(count(shell, 'aria-current={homeLit ?'), 1)
assert.equal(count(shell, 'aria-current={archiveLit ?'), 1)
assert.equal(count(shell, 'aria-current={baseLit ?'), 1)
assert.equal(count(shell, "className={linkClass({ isActive: homeLit })}"), 1)
// и обратное: маркер не попадает в className/в текст
assert.equal(/className=\{[^}]*\bsection\b/.test(shell), false)
```

### WR-05: Гейт «медиа-блок внутри `@layer base`» проверяет порядок в файле, а не вложенность

**File:** `tests/unit/test_section_context_gates.js:126-129`
**Issue:** `assert.ok(css.indexOf('@media') > css.indexOf('@layer base {'))` истинно для **любого** `@media`, стоящего в файле ниже открытия слоя, включая блок, вынесенный за закрывающую `}` слоя. Текст сообщения («must live inside @layer base, above nothing that re-declares it») обещает больше, чем проверка. Сейчас вложенность реальна (`index.css:159-163`), но гейт не упадёт, если переопределение `--header-height: 200px` окажется в `layer theme`/вне слоёв — а именно от этого зависит, перебьёт ли `200px` токен `64px` из `@theme static`. (Поведенчески это поймали бы C-04/C-05, но статический гейт объявлен их заменой для структуры.)

**Fix:** вырезать тело слоя по балансу скобок и искать медиа-блок внутри него:

```js
const start = css.indexOf('@layer base {')
let depth = 0
let end = start
for (let i = start + '@layer base {'.length - 1; i < css.length; i += 1) {
  if (css[i] === '{') depth += 1
  if (css[i] === '}') { depth -= 1; if (depth === 0) { end = i; break } }
}
const baseLayer = css.slice(start, end)
assert.match(baseLayer, /@media\s*\(max-width:\s*639\.98px\)\s*\{\s*:root\s*\{\s*--header-height:\s*200px;?\s*\}\s*\}/)
```

## Info

### IN-01: Мобильный токен `200px` меньше фактической шапки на 320px (209px), запас воздуха падает с 16px до 6.75px

**File:** `web/src/index.css:155-163`
**Issue:** Комментарий фиксирует базис измерения («196.6 на 390×844 и 122.6 на 639×844 → max 200px»), но 320×568 — тоже поддерживаемая ширина (её гоняет `tests/web-app.spec.js:572-591`) — в замере отсутствует. Измерено на текущем дереве: `header = 209px` при 320 (и 209 же для роли `admin`, дополнительный пилл новую строку не создаёт), `scroll-padding-top = 216px` → после клика `gap = 6.75px`. Инвариант `pad ≥ header + 1` держится, поэтому это не блокер, но фактический воздух на самом узком экране втрое меньше контрактных 16px (D-03), а не «измеренный максимум» 196.6. При росте шапки ещё на 8px (например, длинное имя + перенос) цель уедет под шапку именно на 320.
**Fix:** добавить 320 в измеренную таблицу (и в комментарий), либо взять `216px`-кратное значение с запасом на 320 (например `208px` при сохранении `+1rem` = 224), либо явно записать 320 как принятый остаток рядом с двумя уже записанными.

### IN-02: Гейт «нет второго механизма офсета» не знает шортхенда `scroll-padding`

**File:** `tests/unit/test_section_context_gates.js:99-108`
**Issue:** Запрещены `scroll-mt`, `scroll-margin`, `scroll-behavior`; первый гейт считает только `scroll-padding-top:`. Второй глобальный офсет можно завести как `scroll-padding: 80px` (шортхенд) — оба гейта останутся зелёными, хотя C-19 запрещает второй механизм.
**Fix:** расширить запрещённый список шортхендом и логическими свойствами — `'scroll-padding:'`, `'scroll-padding-block'`, `'scroll-padding-inline'` (и `'scroll-snap-'` заодно, если он попадёт в тот же механизм). Единственное разрешённое вхождение (`scroll-padding-top:` в `index.css`) от этого не меняется.

### IN-03: `expect.soft` в C-04/C-05 сохраняет оба RED-а, но следующая жёсткая проверка маскирует их таймаутом

**File:** `tests/web-app.spec.js:873-901` (и симметрично `:911-936`)
**Issue:** Смысл `expect.soft` здесь — показать в одном RED-прогоне и «токен всё ещё 64px», и «офсет 0» (комментарий это и заявляет). Но claim 3 идёт жёстким `expect.poll(gap ≥ 1)`: при неисправленном офсете на 390 браузер поставит цель в `top ≈ 0` при `header.bottom = 197`, полл упадёт по таймауту с сообщением про `gap ≈ −197`, и в отчёте это будет выглядеть как третья независимая поломка, а не как следствие первых двух. Диагностика RED-раунда теряет смысл, который в него вложили.
**Fix:** сделать claim 3 тоже `expect.soft` (или выполнять его только когда claims 1–2 прошли), чтобы отчёт показывал причину, а не следствие.

---

_Reviewed: 2026-10-22T06:20:00Z_
_Reviewer: gsd-code-reviewer (adversarial pass)_
_Depth: standard_
