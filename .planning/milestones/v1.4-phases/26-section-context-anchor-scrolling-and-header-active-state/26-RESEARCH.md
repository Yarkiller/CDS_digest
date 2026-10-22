# Phase 26: Section context — anchor scrolling and header active state - Research

**Researched:** 2026-10-22
**Domain:** Frontend only — React 19 + `react-router-dom` 7.18.3 (data router) + Tailwind CSS v4.3.3 + Playwright 1.62.1
**Confidence:** HIGH

## Summary

Two defects, one CSS declaration and one navigation-state contract. Everything below was **measured in this session** against the running mock build (Vite on a private port, `VITE_USE_MOCKS=true`, Chromium via the repo's own Playwright 1.62.1) — not inferred from the UI-SPEC.

For NAV-01 the mechanism is confirmed end-to-end: `scroll-padding-top: calc(var(--header-height) + 1rem)` on `:root` inside `@layer base` takes the target heading from `gap = -73.5px` (today, hidden under the header) to `gap = +6.5px`. `scroll-margin-top` is *not* needed and would be a second mechanism. The mobile override `--header-height: 200px` under `@media (max-width: 639.98px)` computes to `scroll-padding-top: 216px` and clears the measured 197px / 123px header at 390 / 639. The UI-SPEC's cascade rationale ("`:root` beats `html` by specificity") is **wrong** — CSS compares *layer order before specificity*, so any declaration in `@layer base` (or unlayered) wins over `@layer theme` at equal or lower specificity; verified by probe.

For NAV-02 one finding changes the shape of the plan: **an explicit `aria-current` on `<NavLink>` is silently discarded when `NavLink` itself is inactive** (`let ariaCurrent = isActive ? ariaCurrentProp : undefined` in the router source). The state-driven pill therefore *cannot* stay a `NavLink`; «Выпуск», «Архив» and «База» must become `<Link>` with a computed `aria-current`, exactly like the existing «Админ» pill (`AppShell.jsx:96-101`). That is what the ROADMAP's "reuse the prefix-active pattern" instruction implies, and this research confirms it is not optional.

**Primary recommendation:** one CSS rule in `index.css` (`@layer base :root` + a `@media (max-width: 639.98px)` token override) and one read point in `AppShell` (`state?.section` validated against three literals), with `IssueToc` / `MaterialListRow` taking a required `section` prop, `MaterialPage` blind-forwarding the marker, and every criterion proven in `tests/web-app.spec.js` (no new spec file — see Pitfall 9).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Обсуждены три зоны: офсет под шапку, охват якорей, контракт происхождения. Форма состояния и поведение при перезагрузке выбраны явно; остальное отдано планировщику — см. `Claude's Discretion`.

#### Офсет под шапку (NAV-01)

- **D-01:** Офсет реализуется **одним глобальным правилом** — `scroll-padding-top` на `html` в `web/src/index.css`, а не `scroll-mt-*`-утилитами на заголовках и не постраничными правилами. Один механизм покрывает материал (`[data-testid="material-prose"]`) и длиннид разбора (`RazborPage`), и ни один компонент править не нужно; новая страница с якорями получает офсет по умолчанию. — **Reversibility:** reversible — удаление одного CSS-правила.
- **D-02:** Величина офсета — `calc(var(--header-height) + 1rem)`. `--header-height` уже объявлена (`web/src/index.css:117`, значение `64px`) и **сегодня нигде не используется**; она становится единственным источником высоты шапки. Нижняя граница `sm` — тот же breakpoint, на котором шапка перестаёт переносить навигацию: на `sm+` `--header-height` = `64px`, ниже `sm` — переопределение на фактическую двухстрочную высоту. — **Reversibility:** reversible.
- **D-03:** Воздух между шапкой и заголовком — **16px (1rem)**. На десктопе цель останавливается в ≈80px от верха вьюпорта. Это же значение работает на мобильном поверх увеличенной `--header-height`. — **Reversibility:** reversible.
- **D-04:** Тестовая формулировка критерия — **сравнение двух измеренных прямоугольников** (`heading.bottom` / `heading.top` против `header.getBoundingClientRect().height`), а не литерал `64` и не литерал `80`. Заголовок обязан быть внутри вьюпорта и ниже шапки с зазором ≥ 1px (не «ровно 16», чтобы не пинить пиксель). — **Reversibility:** reversible.

#### Охват якорей (NAV-01)

- **D-05:** Якоря «Содержания» в разборах **входят в охват** фазы, несмотря на то что ROADMAP называет только материал. `RazborPage.jsx:38` строит тот же `href="#id"` из той же `extractMarkdownHeadings`, то есть дефект там идентичен; закрывать NAV-01 только на материале значило бы объявить починку по букве, а не по смыслу «читатель сохраняет ориентацию». Глобальный механизм D-01 делает это без дополнительных правок. — **Reversibility:** reversible.
- **D-06:** Никаких других внутристраничных якорей в `web/src` не существует (проверено грепом `href=`); глобальное правило не меняет поведение ни одной страницы, где якорей нет. Если в будущем появится якорь, к которому офсет неприменим (например переход к скрытой области), это будет отдельным решением, а не поводом делать правило локальным сейчас. — **Reversibility:** reversible.

#### Контракт происхождения (NAV-02)

- **D-07:** Состояние несёт **маркер раздела, а не путь**: `{ section: 'archive' }`, `{ section: 'base' }` или `{ section: 'issue' }`. Допустимых значений ровно три. Путь происхождения (`{ from: '/archive' }`) отклонён: это второй способ вывести раздел из URL, а ROADMAP требует ровно обратного — происхождение не должно угадываться по адресу. — **Reversibility:** costly — смена формы состояния затрагивает каждый ссылающийся call site (`ArchivePage`, `KnowledgePage` / `MaterialListRow`, `IssuePage` / `IssueToc`, `MaterialPage` «связанные материалы») и единственного потребителя в `AppShell`.
- **D-08:** Проброс по цепочке обязателен, иначе критерий 3 невыполним:
  - `ArchivePage.jsx:71` → `/issues/:number` с `{ section: 'archive' }`;
  - `IssuePage` при `isCurrent === false` пробрасывает `{ section: 'archive' }` в `IssueToc` → `/materials/:slug`. Источником служит **не** полученное состояние, а сам факт «это архивный выпуск»: архивный выпуск существует только внутри архива, поэтому проброс честен и на прямом заходе `/issues/12`;
  - `IssuePage` при `isCurrent === true` (маршрут `/`, текущий выпуск) пробрасывает `{ section: 'issue' }` тем же путём — симметрично архивной ветви (D-09);
  - `KnowledgePage.jsx:387` → `MaterialListRow` с `{ section: 'base' }`;
  - `MaterialPage.jsx:261` («Связанные материалы») переиспользует `section` из `useLocation().state`, а не придумывает свой.
  — **Reversibility:** reversible — каждая стрелка локальна и покрыта собственным ассертом.
- **D-09:** Материал из **текущего** выпуска подсвечивает «Выпуск» — симметрично архиву. `IssueToc` получает маркер от `IssuePage` по уже существующему признаку `isCurrent` и пробрасывает `{ section: 'issue' }` в `/materials/:slug`; `AppShell` зажигает пилл «Выпуск» тем же механизмом, что «Архив» и «Базу» (`aria-current="true"` + `linkClass({ isActive })`). Никакого вывода из URL и никакого нового маркера сверх D-07. — **Reversibility:** reversible — удаление `'issue'` из закрытого списка и одной ветки `IssueToc`.
- **D-10:** Деградация без состояния — **ни один раздел не подсвечен**. Единственный раздел, который зажигается по URL, — «Архив» на `/issues/:number`: этот маршрут существует только внутри архива, поэтому вывод из адреса здесь не догадка. Для `/materials/:id` вывод из `pathname` запрещён. `/` (с `end`), `/archive`, `/knowledge` продолжают зажигаться собственным `NavLink`; на `/materials/:slug` «Выпуск» зажигается **только** маркером `'issue'`, а не совпадением пути. — **Reversibility:** reversible.
- **D-11:** Доступность и внешний вид активного состояния переиспользуются без изобретений: активный по состоянию раздел получает `aria-current="true"` (прецедент «Админ», `AppShell.jsx:99`), собственные маршруты сохраняют `aria-current="page"` от `NavLink`; заливка берётся из существующего `linkClass({ isActive })` — `bg-primary-solid text-on-solid` (Phase 25 / THEME-01). Новых токенов, стилей или вариантов пилла не вводится. — **Reversibility:** reversible.

### Claude's Discretion

Планировщик решает сам, не переспрашивая, в рамках констрейнтов:

1. **Точное значение мобильной `--header-height`.** Измерить фактическую высоту двухстрочной шапки в браузере (ориентир ≈112px; оценка, а не факт) и записать измеренное значение. Не угадывать и не выводить из суммы паддингов на бумаге — критерий D-04 всё равно сравнивает с живым прямоугольником, поэтому ошибка в константе проявится как падение, а не как тихий дефект.
2. **Где объявляется переопределение.** `@media (max-width: 639.98px)`/`min-width` внутри `web/src/index.css` рядом с существующей `--header-height`, либо `:root` + медиа-блок — форма свободна, значение и breakpoint зафиксированы D-02.
3. **API компонентов для проброса.** Проп `section` у `IssueToc` / `MaterialListRow` против обёртки-функции в вызывающей странице; важно лишь то, что `MaterialListRow` — переиспользуемый компонент, и `'base'` не должен быть захардкожен внутри него (иначе будущее использование строки в другом разделе получит ложную подсветку). У `IssueToc` маркер обязан приходить пропом — компонент рендерится и текущим выпуском (`'issue'`), и архивным (`'archive'`), поэтому захардкоженное значение там недопустимо.
4. **Где валидируется маркер.** Читать `state?.section` в `AppShell` и сравнивать с закрытым списком трёх значений (`'archive' | 'base' | 'issue'`); невалидное или отсутствующее значение = «ничего не зажжено». Никакой нормализации пути в состоянии.
5. **Тестовые фикстуры и проба.** `tests/web-app.spec.js` уже владеет «Содержанием» (`:99-115`) и шапкой; критерий 2 требует секции ниже первого экрана, а мок `rag-systems` содержит всего два заголовка (`web/src/data/mock.js:61-68`), поэтому фикстуру придётся расширить или завести отдельную — тестовая правка, не production. Путь к длинной секции и способ прокрутки — на усмотрение планировщика.

### Deferred Ideas (OUT OF SCOPE)

- **Ссылка «← Назад в архив» / «← Назад в результаты»** — новый навигационный элемент; вне NAV-02, требует своего скоупа.
- **Сокращение мобильной шапки** (убрать перенос nav, свернуть имя пользователя), чтобы `--header-height` осталась 64px на всех ширинах — это редизайн хрома, а не починка якоря; фаза решает проблему увеличением офсета.
- **Сохранение раздела между сессиями** через `localStorage`/cookie — прямо запрещено ROADMAP: запомненный раздел сделал бы поздний прямой заход ложно подсвеченным.
- **Sticky-подсветка текущей секции при скролле** (scroll-spy в «Содержании») — не запрашивалось, отдельная функциональность.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAV-01 | A reader who follows a «Содержание» link lands with the target heading fully visible below the sticky header, with breathing room — no heading hidden under the header and no over-scroll past it `[VERIFIED: .planning/REQUIREMENTS.md:28]` | § NAV-01 mechanism (A/B probe: `gap -73.5` → `+6.5`), § Cascade placement, § Mobile override, § C-00 reachability gate procedure, § Fixture extension for `rag-systems` / `razbory` |
| NAV-02 | The header keeps «Архив» lit while the reader views an archived issue or a material opened from the archive, and «База» lit for a material opened from search; a direct URL visit without origin state lights no false section `[VERIFIED: .planning/REQUIREMENTS.md:29]` | § NavLink cannot carry the marker (source-proof), § Router-state contract (reload vs `goto`), § Prop-threading table, § Positive/negative pill matrix |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Anchor scroll offset (NAV-01) | Browser / Client (CSS) | — | `scroll-padding-top` on the document scrollport is a browser primitive; no JS, no measurement, no component |
| Header active state (NAV-02) | Browser / Client (React router state) | — | `location.state` lives in `history.state`; the pill is chrome, not a data concern |
| Origin marker production | Browser / Client (`Link state`) | — | Each call site knows its own section by construction; no API, no backend field exists or is added |
| Origin marker validation | Browser / Client (`AppShell`, single read point) | — | Closed-list comparison; an invalid marker must degrade to "nothing lit" |
| Reachability / offset proof (NAV-01 C-00) | Test harness (Playwright, Chromium) | — | Requires a real layout engine; cannot be proven by a static gate |

No backend, no Supabase, no port or adapter is touched — the phase is confined to `web/` plus `tests/` and `web/src/data/mock.js` (mock fixture only).

## Key Findings

### 1. NAV-01: the mechanism works, and it was proven A/B in this session

**Which property.** `scroll-padding-top` on the *scrollport* is the correct primitive here, because the page scrolls the **document**, not an inner container (`<main>` has no `overflow`; `SectionToc`'s `sticky top-24` rail is `overflow-auto` but only scrolls itself). `scroll-padding-top` "defines offsets for the top of the optimal viewing region of the scrollport … allows the author to exclude regions … obscured by other content (such as fixed-positioned toolbars)" `[CITED: developer.mozilla.org/en-US/docs/Web/CSS/scroll-padding-top]`. `scroll-margin-top` on the headings would also work, but it is the *second* mechanism D-01 forbids. **Use `scroll-padding-top` only.**

**A/B proof (Chromium, mock build, `/materials/rag-systems`, 1280×800, document lengthened in-DOM only — no repo edit):**

| State | `scrollPaddingTop` | heading `top` after click | `gap = top − header.bottom` | verdict |
|---|---|---|---|---|
| today | `auto` (parse → 0) | `-0.5` | **`-73.5`** | RED, exactly the defect |
| `:root { scroll-padding-top: calc(var(--header-height) + 1rem) }` | `80px` | `79.5` | **`+6.5`** | GREEN, inside `[1, 32]` |

`[VERIFIED: session probe, Chromium via @playwright/test 1.62.1, 2026-10-22]`. Predicted value from the UI-SPEC was `80 − 72.6 ≈ 7.4`; the live header at 1280 is **73.0** (not `72.6` — the 0.4px delta is font-metric timing: the Manrope webfont comes from `fonts.googleapis.com` in `index.css:1`, and the UI-SPEC's measurement landed before/after `document.fonts.ready`). **Consequence for the plan: never pin `73`, `72.6` or `7.4`. Pin the band `[1, 32]` and read the live rect (D-04).**

Gate in the same run: `headingDocTop = 396.5`, `maxScroll = 3823` after lengthening (body below target `3426.5`) → `reachable === true`. On the unmodified fixture `maxScroll = 63` → `reachable === false`, confirming the UI-SPEC C-00 table and the requirement to extend the fixture.

**Computed-value serialization.** `getComputedStyle(document.documentElement).scrollPaddingTop` returns the **resolved px string** in Chromium (`"80px"`, not `"calc(64px + 16px)"`), so `Number.parseFloat(...) || 0` works. Before the fix it returns the literal `"auto"` → `NaN` → `|| 0` → `0`. That `|| 0` is load-bearing: without it the RED assertion fails with `NaN` instead of a number. `[VERIFIED: session probe]` — note this is a Chromium-only guarantee (MDN lists the computed value as "as specified"); the `web` project runs Chromium only, so it is safe, but do not port the assertion to WebKit/Firefox without re-checking.

**Exact placement (cascade-correct).** `--header-height: 64px` lives at `web/src/index.css:117` **inside `@theme static`** (`index.css:7`). The built stylesheet proves the compile shape:

```
@layer components;            /* empty, declared first */
@layer properties{…}
@layer theme{:root,:host{…--header-height:64px…}}   /* ← @theme static lands here */
@layer base{…}                                      /* ← base comes AFTER theme */
@layer utilities{…}
```
`[VERIFIED: web/dist/assets/index-BAhCYysH.css (built from the current tree), 2026-10-22]`

**The UI-SPEC's rationale is wrong, its conclusion is right.** CSS cascade layers are compared **before** specificity, so *any* declaration in `@layer base` wins over `@layer theme` regardless of selector specificity. Probe results confirming this:

| injected rule | computed `--header-height` |
|---|---|
| unlayered `html { --header-height: 200px }` | `200px` ✅ |
| `@layer base { html { --header-height: 200px } }` | `200px` ✅ (specificity is irrelevant across layers) |
| `@layer base { :root { --header-height: 200px } }` | `200px` ✅ |
| `@layer base { @media (max-width: 639.98px) { :root { --header-height: 200px } } }` | `200px` at 390, `64px` at 640 ✅ |

`[VERIFIED: session probe, 2026-10-22]`. So: **do not touch `index.css:117`** (a static gate depends on it — see Pitfall 7), and put both new declarations in the *existing* `@layer base { :root { … } }` block at `index.css:144-148`.

### 2. Mobile `--header-height`: measured, and the breakpoint is narrower than assumed

Measured `header.getBoundingClientRect().height` on the mock build (`/`, employee identity, 5 pills), width sweep at 844px height:

| width | header height | nav width | note |
|---|---|---|---|
| 320 | **209** | 288 | nav on its own row(s) |
| 390 | **197** | 358 | UI-SPEC measured 196.6 |
| 500 | **123** | 468 | nav is `w-full` but the *row* now fits |
| 639 | **123** | 607 | UI-SPEC measured 122.6 |
| 640 | **123** | 378.4 | `sm:w-auto` applies, **row still wraps** |
| 700 / 768 | **123** | 378.4 | same |
| 800 | **111** | 378.4 | wordmark no longer wraps its second line |
| 900 | **99** | 378.4 | |
| 1000 / 1024 / 1280 / 1440 | **73** | 378.4 | stable desktop header |

`[VERIFIED: session probe, 2026-10-22]`

Three consequences:

1. The UI-SPEC values (`196.6` @390, `122.6` @639 → `200px`) are **confirmed and plausible from the markup**: `<nav className="order-last flex w-full flex-wrap gap-1 sm:order-none sm:w-auto">` (`AppShell.jsx:73-75`) moves to its own row below `sm` (Tailwind v4 `sm` = `640px`), and at 390 the 5 pills themselves wrap further, adding the extra ~74px over the 639 case.
2. **`max-width: 639.98px` is the correct edge**: at 640 the nav is already `w-auto` (378.4px wide), so the mobile value must *not* apply there.
3. **A residual hole exists at 640–~999px** that the locked contract does not cover: offset is `80px` while the live header is `123 / 111 / 99px`, i.e. `gap ∈ [-43, -19]`. Today that band is also broken (offset 0), so the phase improves but does not complete it. See Open Question Q1 — do **not** widen the scope; record the measurement in the phase summary the same way the 7.4px desktop residual is recorded.

Recommended declaration (discretion item D-02, exact form):

```css
@layer base {
  /* … existing button rule … */

  :root {
    color: var(--color-text-primary);
    background: var(--color-bg-app);
    font-family: var(--font-sans);
    /* NAV-01 (D-01/D-02/D-03): the sticky shell header eats the top of the scrollport,
       so a #fragment target lands underneath it. One declaration covers every in-page
       anchor — material prose (MaterialPage) and razbor prose (RazborPage) alike. */
    scroll-padding-top: calc(var(--header-height) + 1rem);
  }

  /* Measured 2026-10-22 on the mock build, mock identity, 5 nav pills:
     header.getBoundingClientRect().height = 196.6px @390x844 and 122.6px @639x844.
     One value for the whole sub-`sm` range: max(196.6, 122.6) rounded up to a
     multiple of 4 = 200px (D-C1). `sm` starts at 640px, and at 640 the nav no
     longer claims its own row (measured 123px there too, but the token is locked
     to 64px on sm+ by D-02). */
  @media (max-width: 639.98px) {
    :root {
      --header-height: 200px;
    }
  }
}
```

After this, the probe reads `--header-height: 200px`, `scroll-padding-top: 216px` at 390 and `64px` / `80px` at 640 — expected residual `216 − 197 = 19px` at 390 and `216 − 123 = 93px` at 639 `[VERIFIED: session probe]`. That is exactly why C-04/C-05 must **not** assert the `[1, 32]` band: one value cannot produce 1–32px at both widths (93 > 32), and a second value would be chrome design.

`@media (width < 40rem)` is an equivalent alternative (Tailwind v4 itself emits range syntax), but `max-width: 639.98px` is what the UI-SPEC/context name and is universally parseable — prefer it.

### 3. NAV-02: an explicit `aria-current` on `<NavLink>` is discarded — the three pills must become `<Link>`

Official source, quoted verbatim:

```tsx
let ariaCurrent = isActive ? ariaCurrentProp : undefined;

return (
  <Link {...rest} aria-current={ariaCurrent} … />
);
```
`[CITED: github.com/remix-run/react-router/blob/main/packages/react-router/lib/dom/lib.tsx — NavLink]`

So `<NavLink aria-current="true" …>` emits **nothing** whenever the router computes `isActive === false` — which is precisely the `/materials/:slug` case where the marker matters. The repo already learned this once; the comment above the admin pill records the production symptom:

```
// WR-02: NavLink derives aria-current from `to="/admin/digest"`, so the pill
// was announced as inactive on pipeline/preview while looking active. Set it
// from the already-computed prefix instead — "true" (not "page") because the
// href targets digest while the whole admin section is the current context.
```
`[VERIFIED: web/src/components/AppShell.jsx:95-100]`

**Recommendation:** convert «Выпуск» (`:77-79`), «Архив» (`:80-82`) and «База» (`:83-85`) to `<Link>` and compute both the class and the attribute, exactly like «Админ». Keep `<NavLink>` for «Голосование» (`:86-88`) and «Разборы» (`:89-91`) — they have no state-driven branch and C-15 pins them as `page`. Converting is behaviour-preserving for path matching: `/` used `end` (equality), and `/archive` / `/knowledge` have no child routes.

`linkClass` itself must not change (`AppShell.jsx:11-15`): C-18 pins `min-h-11 rounded-full px-2.5 text-sm` in both states plus the exact swap `bg-primary-solid text-on-solid` ↔ `text-text-secondary hover:bg-bg-surface`.

### 4. Router state contract (react-router-dom **7.18.3**, not 6)

`web/package.json` declares `"react-router-dom": "^7.18.3"` and `web/node_modules/react-router/package.json` resolves to **7.18.3** `[VERIFIED: web/package.json + installed tree]`. The data router API in use (`createBrowserRouter` at `App.jsx:34`) is identical to v6.4+, and `Link state` is documented for framework/data/declarative modes: "Adds persistent client side routing state to the next location … This state is inaccessible on the server as it is implemented on top of `history.state`" `[CITED: react-router docs — Link > Props > state]`.

Measured behaviour (`[VERIFIED: session probe, 2026-10-22]`):

| action | `window.history.state` | `useLocation().state` |
|---|---|---|
| SPA click with no `state` | `{ usr: null, key: "…", idx: 1 }` | `null` |
| `history.replaceState({…, usr: {section:'archive'}})` then **`page.reload()`** | `{ idx: 0, usr: { section: 'archive' } }` | **`{ section: 'archive' }`** — F5 preserves |
| `page.goto('/materials/pgvector')` (any full document navigation) | `{ idx: 0 }` | `null` — origin is genuinely gone |
| `page.goto(same URL)` again | `{ idx: 0 }` | `null` |

So: **state survives F5 (expected per D-07…D-10) and is destroyed by any full navigation, including `page.goto`.** A *new* Playwright test gets a brand-new browser context, therefore `history.state` is empty — which is why C-13/C-14 should be **their own `test()` blocks whose first action is `page.goto(...)`**, not a manual `browser.newContext()`. Reason: a manually created context does **not** inherit `use.baseURL` from `playwright.config.js:73`, so `page.goto('/materials/x')` there throws "Invalid URL" and the test author must rebuild the base URL by hand (`test.info().project.use.baseURL`). If strictness is still wanted, `const ctx = await browser.newContext({ baseURL: test.info().project.use.baseURL })`.

Back/forward falls out for free and should not be over-engineered: the `/issues/13` entry carries `usr:{section:'archive'}` (it was pushed by the archive card), so going back from a material re-lights «Архив»; the `/archive` entry carries `usr:null`, so «Архив» is `page` there. No test is required by the contract, but it is a cheap bonus assertion.

**Silent-null trap:** `waitForURL()` resolves as soon as the URL changes, which can be *before* React commits. A manual `page.evaluate()` immediately after `waitForURL` read **stale DOM** in this session (it reported «Архив» `aria-current="page"` on `/issues/13`, while the corrected run showed `null` on all pills). Use web-first assertions (`await expect(link).toHaveAttribute(...)`) or `expect.poll`, never a bare `evaluate` right after `waitForURL`.

**Suggested `AppShell` shape** (single read point, closed list, no path guessing):

```jsx
const { pathname, state } = useLocation()        // :35 today destructures only pathname
const adminActive = pathname.startsWith('/admin/')
const section = state?.section                    // 'archive' | 'base' | 'issue' | undefined

const homeRoute = pathname === '/'
const archiveRoute = pathname === '/archive'
const issuesBranch = pathname.startsWith('/issues/')
const baseRoute = pathname === '/knowledge'

const homeLit = homeRoute || section === 'issue'
const archiveLit = archiveRoute || issuesBranch || section === 'archive'
const baseLit = baseRoute || section === 'base'

// 'page' only for a pill whose own route is current; 'true' when the section is
// claimed by navigation state or by the /issues/ prefix (D-10, D-11).
const current = (ownRoute) => (ownRoute ? 'page' : 'true')
```

```jsx
<Link to="/" aria-current={homeLit ? current(homeRoute) : undefined}
      className={linkClass({ isActive: homeLit })}>Выпуск</Link>
<Link to="/archive" aria-current={archiveLit ? current(archiveRoute) : undefined}
      className={linkClass({ isActive: archiveLit })}>Архив</Link>
<Link to="/knowledge" aria-current={baseLit ? current(baseRoute) : undefined}
      className={linkClass({ isActive: baseLit })}>База</Link>
```

C-20 ("не более одного зажжённого") holds structurally: `section` is a single value and the three `*Lit` expressions can never be true simultaneously for one pathname (`/` ≠ `/archive` ≠ `/knowledge`, and `section` is one literal).

### 5. Prop threading — the minimal change set

| File | Line(s) | Change | Required? |
|---|---|---|---|
| `web/src/index.css` | `139-148` (+ new media block) | `scroll-padding-top` in the existing `@layer base :root`; `@media (max-width: 639.98px) :root { --header-height: 200px }` | **yes** (NAV-01) |
| `web/src/components/AppShell.jsx` | `2`, `35`, `77-85` | `useLocation()` also destructures `state`; three pills become `<Link>` with computed `aria-current` + `linkClass` | **yes** (NAV-02 consumer) |
| `web/src/pages/ArchivePage.jsx` | `70-73` | `<Link to={/issues/${n}} state={{ section: 'archive' }}>` | **yes** (C-08) |
| `web/src/components/IssueToc.jsx` | `4`, `9-11` | new **required** `section` prop (`'archive' \| 'issue'`), forwarded as `state={{ section }}` on every material link | **yes** (C-09/C-10) |
| `web/src/pages/IssuePage.jsx` | `188` | `<IssueToc items={toTocItems(items)} section={isCurrent ? 'issue' : 'archive'} />` | **yes** |
| `web/src/components/MaterialListRow.jsx` | `7`, `13-14` | new **required** `section` prop, forwarded as `state={{ section }}` (never defaulted — see below) | **yes** (C-11) |
| `web/src/pages/KnowledgePage.jsx` | `387` | `<MaterialListRow … section="base" />` | **yes** |
| `web/src/pages/MaterialPage.jsx` | `3`, `60`, `259-266` | **add** `useLocation` to the `:3` import (`{ Link, Navigate, useParams }` today); read `const { state } = useLocation()` in the body at `:61`; related `<Link>` at `:261` carries `state={origin?.section ? { section: origin.section } : undefined}` | **yes** (C-12) |
| `web/src/data/mock.js` | `59-69`, `255-295` | **test fixture only**: lengthen `rag-systems.body_markdown`; lengthen one razbor body; add `related` to an archive-issue material | recommended |
| `tests/web-app.spec.js` | after `:120` | criteria 1-5 | **yes** |
| `tests/unit/test_section_context_gates.js` | new | static gate for C-19 / token / closed list | recommended |

**Why `IssueToc` must take a prop, not infer.** `IssueToc` renders both branches — current (`'issue'`) and archived (`'archive'`) — from `IssuePage`, and `IssuePage` already knows which via its own `isCurrent` prop (`App.jsx:47` sets `isCurrent` for `/`, `App.jsx:49` sets `isCurrent={false}` for `issues/:number`). A hard-coded literal inside `IssueToc` is a guaranteed defect.

**Why `MaterialListRow` must not default to `'base'`.** It is the reusable knowledge hit row (`MaterialListRow.jsx:7`); a default would silently mis-light any future list. Make `section` required (no default) so a second consumer must decide — the TypeScript-less equivalent of a compile error is the JSDoc `@param {{ material: object, section: 'archive'|'base'|'issue' }}`.

**`MaterialPage` should blind-forward, not validate.** C-17 demands a *single* validation point against the three literals. If `MaterialPage` also compared `'archive' | 'base' | 'issue'`, there would be two literal sites. So `MaterialPage` re-emits whatever marker it received, unexamined:

```jsx
const { state: originState } = useLocation()   // MaterialPage.jsx:3 import (+ useLocation), :60 component, body at :61
const originSection = originState?.section     // forwarded verbatim — no literals here
…
<Link to={`/materials/${item.slug}`} state={originSection ? { section: originSection } : undefined}>
```

**`/admin/materials/:id` is safe by construction, not by guard.** The admin preview mounts the *same* `MaterialPage` (`App.jsx:66`), where `useLocation().state` is `null` in every real admin journey, so no marker is produced and no section is lit; the admin pill keeps its own prefix (`AppShell.jsx:39`). Do **not** add a `preview &&` guard or a `section` prop on that route — that would create a second source of truth and a C-16 failure risk.

### 6. Test harness — exactly what exists, and what has to be extended

**Runner.** `playwright.config.js:44-54` starts `npm run dev --prefix web -- --host 127.0.0.1 --port 5174` with `env: { VITE_USE_MOCKS: "true" }` and `reuseExistingServer: !process.env.CI`. The `web` project's `testMatch` is `/(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/` (`playwright.config.js:70`) — **a new `tests/section-context.spec.js` would not run at all** unless that regex is widened. Put the criteria in `tests/web-app.spec.js` (which is where CONTEXT.md says they belong anyway).

**Existing anchors suite.** `tests/web-app.spec.js:96-120` ("keeps the material TOC as a desktop rail and a mobile disclosure") is the natural home: it already locates `getByTestId('material-toc')` (`:99`), the 390px disclosure via `page.locator('details', { hasText: 'Содержание' }).first()` + `summary.click()` (`:108-110`), and pins zero horizontal overflow (`:114-117`). It runs at Playwright's **default 1280×720** — the new rect assertions should set `test.use({ viewport: { width: 1280, height: 800 } })` (a new `test.describe`) so measurements match the UI-SPEC table and `maxScroll` arithmetic is reproducible.

**Anchor ids.** Heading ids are `user-content-…`: `rehypeSlug` + `rehypeSanitize` clobber prefix, mirrored in `web/src/utils/markdownToc.js:6` (`export const HEADING_ID_PREFIX = 'user-content-'`) `[VERIFIED: web/src/utils/markdownToc.js:6]`. Never hand-build an id — read the TOC link's `href`, strip `#`, `decodeURIComponent` it (ids are Cyrillic, e.g. `#user-content-введение`).

**Measured fixtures today (1280×800 unless noted):**

| fixture | anchor | `headingDocTop` | `maxScroll` | `reachable` (`maxScroll ≥ docTop`) |
|---|---|---|---|---|
| `/materials/rag-systems` | `#user-content-введение` | 396.5 | **63** | ❌ |
| `/materials/rag-systems` @390×844 | `#user-content-введение` | 779.75 | **506** | ❌ |
| `/materials/empty-dek-article` | `#user-content-section-one` | 322 | **0** | ❌ (gap today = 249 > 32 → C-02b pin is valid **as-is**) |
| `/razbory/3` @1280×800 | `#user-content-контекст` | 480 | **196** | ❌ |
`[VERIFIED: session probe, 2026-10-22]` — this also **closes the UI-SPEC Spacing FLAG (c)**: `empty-dek-article` now has a row in the C-00 table, and it satisfies both prerequisites C-02b asks for (`reachable === false`, pre-click gap `> 32`).

**Fixture extension (test-only, `web/src/data/mock.js`).** `contentApi.js:289-311` maps the mock material: `body_markdown` is used verbatim when present, otherwise `body[]` is joined `[VERIFIED: web/src/services/contentApi.js:289-311]`. Plan for:

1. `rag-systems` (`mock.js:59-69`): keep `## Введение` first with a **short** body (criterion 1 = "short section"), then add ≥4 more `##`/`###` headings (total ≥6) and ~12–15 paragraphs of prose so that the *last* heading sits > 1 viewport below the fold and `maxScroll ≥ headingDocTop` with ≥1.25 viewports of body under the target. My in-DOM experiment needed ~40 paragraphs at `max-w-3xl` to reach `maxScroll = 3823`; ~20 paragraphs of two-sentence text is enough for the strict gate at 1280×800 (`headingDocTop ≈ 400`, so content below the target must exceed ≈800px). Keep the existing strings `/введение/i` and `/регламент/i` — `tests/web-app.spec.js:92-93` and `:28` assert them.
2. `razbory` — **do not add a new razbor**: `tests/razbory.spec.js:16` pins `chronology-item` count `4` `[VERIFIED: tests/razbory.spec.js:16]`. Lengthen an existing published body instead. Prefer **id 3** for C-06 (its TOC is `#user-content-контекст / -подход / -итоги`, measured above) so the existing pin stays on id 2 (`tests/razbory.spec.js:43-56` clicks «Качество» on `/razbory/2`; adding prose to id 2 would keep that test green but couples two fixtures).
3. **C-12 needs a new `related` entry.** `sql-dashboards` and `prompt-engineering` — the only two materials in `pastIssue` (`mock.js:13-36`) — have **no** `related` key, so "material opened from the archive → Связанные материалы" is currently unreachable. Add `related: [{ slug: 'rag-systems', title: 'Building Production RAG Systems' }]` to `sql-dashboards` (`mock.js:171-189`). No existing test asserts `material-related` on that slug; `tests/web-app.spec.js:79-86` asserts it on `rag-systems`, which already has `related` → `anomaly-detection`. Note: `sql-dashboards` has **no `body_markdown` key at all** — only `body: ['Содержит примеры SQL…']` (`mock.js:188`), which `contentApi.js:289-292` joins into one short paragraph. So its page has no headings and `maxScroll ≈ 0`; that is fine for C-12 (which tests the pill + the related link, not scrolling) and means the C-12 fixture does **not** need prose lengthening.

**C-00 gate snippet (validated form):**

```js
const gate = await page.evaluate((anchorId) => {
  const doc = document.documentElement
  const header = document.querySelector('header').getBoundingClientRect()
  const pad = Number.parseFloat(getComputedStyle(doc).scrollPaddingTop) || 0 // 'auto' → 0
  const target = document.getElementById(anchorId)
  const headingDocTop = target.getBoundingClientRect().top + window.scrollY
  const maxScroll = doc.scrollHeight - window.innerHeight
  return { headerHeight: header.height, pad, headingDocTop, maxScroll,
           reachable: maxScroll >= headingDocTop }
}, anchorId)
```

**Same-anchor re-click is a no-op.** Clicking an `<a href="#x">` when `location.hash` is already `#x` does not scroll again. Any spec that measures "before" and "after" on the same link must first reset
`window.history.replaceState(window.history.state, '', location.pathname + location.search)` and `window.scrollTo(0, 0)` — my probe had to do exactly this. One click per fresh `goto` avoids the whole class of problem.

**Visibility ≠ unoccluded.** `expect(heading).toBeVisible()` passes for a heading sitting under the sticky header (measured `top: -0.5` while "visible"). The rect assertion is the only proof; do not substitute Playwright's visibility.

### 7. UI-SPEC open FLAGs — do they matter?

| FLAG | Verdict |
|---|---|
| **Dimension 4 Typography** — "exactly 2 weights" is incomplete (`font-medium` on the disclosure `<summary>`, `text-xs` rail caption, `text-lg` dek). | **Does not matter.** The phase changes zero sizes/weights; C-18 explicitly forbids a weight change on the active pill. No plan task depends on the claim. |
| **Dimension 5 Spacing (a)** — rule 2 calls C-02b the only unreachable-band case while C-04/C-05 claim 3 live in the same branch. | **Wording only.** C-04/C-05 claim 3 never asserts the band (measured residual 19px @390 and 93px @639), so the "only C-02b" phrasing is imprecise but harmless. |
| **Dimension 5 Spacing (b)** — cascade rationale given as `:root` vs `html` specificity. | **This one is factually wrong and should be corrected in the plan.** Layer order precedes specificity: `@layer base` beats `@layer theme` for *any* selector (probe: `@layer base { html {…} }` and unlayered `html {…}` both win). The practical instruction is unchanged — declare in `@layer base :root` — but write the correct reason, because a future maintainer who "optimises" the rule into `@theme static` would break it silently. |
| **Dimension 5 Spacing (c)** — no C-00 row for `empty-dek-article`. | **Closed by this research:** measured `headingDocTop = 322`, `maxScroll = 0`, current gap `249`. C-02b's fixture and its `gap > 32` precondition both hold today. |

Nothing in the UI-SPEC is unachievable. Two numbers in it are stale-but-harmless (`72.6` → live `73`; `6.5` vs `7.4` predicted gap) and one *stated* residual is under-stated: the desktop gap is `80 − 73 = 7`, and the 640–999px band has a **negative** gap (see Open Question Q1).

## Standard Stack

### Core

| Library | Version | Purpose | Why standard |
|---|---|---|---|
| CSS `scroll-padding-top` (browser primitive) | baseline since Apr 2021 | Anchor offset for a sticky header | Purpose-built for exactly this; no JS, no measurement, survives any new anchor `[CITED: MDN scroll-padding-top]` |
| `react-router-dom` | **7.18.3** (declared `^7.18.3`) `[VERIFIED: web/package.json]` | `Link state` / `useLocation().state` | Built-in location state on top of `history.state`; no custom store `[CITED: react-router Link state]` |
| `tailwindcss` + `@tailwindcss/vite` | 4.3.3 `[VERIFIED: web/package.json]` | `@theme static` tokens + `@layer` output | Already the project's only styling system; the fix rides its layer order |
| `@playwright/test` | 1.62.1 `[VERIFIED: npx playwright --version]` | E2E proof for criteria 1-5 | The repo's existing runner; nothing new to install |

### Supporting

| Library | Version | Purpose | When to use |
|---|---|---|---|
| `react-markdown` + `rehype-slug` + `rehype-sanitize` | 10.1.0 / 6.0.0 / 6.0.0 | Produce `user-content-*` heading ids | Read-only in this phase — the ids the anchors target |
| `node --test` (`npm run test:js`) | Node 24.21.0 | Static gates | For C-19's "exactly one `scroll-*` declaration" proof |

### Alternatives Considered

| Instead of | Could use | Tradeoff |
|---|---|---|
| `scroll-padding-top` on `:root` | `scroll-margin-top` on `[&_h2]:scroll-mt-20` etc. | Works, but is a *second* mechanism and needs a selector per heading level in two pages; D-01 forbids it, and it would also break `:target`/`scrollIntoView` callers |
| Router `state` | React context / `sessionStorage` | Session storage is banned by ROADMAP (a remembered section lies on a later direct visit); a context provider is extra machinery for 3 literals |
| Router `state` | `?from=archive` query param | That is still deriving the origin from the URL *and* pollutes a shareable link with a transient claim |
| Explicit `aria-current` on `<Link>` | Keep `<NavLink>` + `aria-current` prop | Provably cannot work: `NavLink` drops the prop when inactive (router source quoted above) |

**Installation:** none — this phase adds **zero** dependencies.

## Package Legitimacy Audit

Not applicable: **no package is installed, upgraded or removed by this phase.** `@playwright/test` 1.62.1, `react-router-dom` 7.18.3 and `tailwindcss` 4.3.3 are already declared in `package.json` / `web/package.json` and already present in the tree.

## Architecture Patterns

### System Architecture Diagram

```
                reader action
                     │
      ┌──────────────┴───────────────┐
      │                              │
 clicks «Содержание»          clicks a section row
 (# heading in same doc)      (archive card / issue TOC /
      │                        knowledge hit row / related)
      │                              │
      ▼                              ▼
 browser hash navigation      <Link state={{section}}>
      │                              │  (archive | base | issue)
      │                              ▼
      │                     history.state.usr = { section }
      │                              │
      ▼                              ▼
 html scrollport              useLocation() in AppShell
 scroll-padding-top                  │
 = header-height + 1rem     ┌────────┴─────────┐
      │                      │                  │
      │                 state?.section     pathname === '/…'
      │                      │            or '/issues/' prefix
      │                      └────────┬─────────┘
      ▼                               ▼
 heading lands 1–32px below     one pill gets
 header bottom (or a bigger     aria-current + bg-primary-solid
 residual when unreachable)     (or none at all when no origin)
```

Both branches are independent; neither reads the other's state. Nothing leaves the browser.

### Recommended Project Structure (files this phase touches)

```
web/src/
├── index.css                      # NAV-01: one scroll-padding-top + one media token override
├── components/
│   ├── AppShell.jsx               # NAV-02: single read point, 3 pills become <Link>
│   ├── IssueToc.jsx               # required `section` prop → Link state
│   └── MaterialListRow.jsx        # required `section` prop → Link state
├── pages/
│   ├── ArchivePage.jsx            # state={{section:'archive'}} on /issues/:n
│   ├── IssuePage.jsx              # passes isCurrent ? 'issue' : 'archive'
│   ├── KnowledgePage.jsx          # passes 'base'
│   └── MaterialPage.jsx           # blind-forwards location.state.section to related
└── data/mock.js                   # TEST FIXTURE ONLY: longer bodies, one `related`
tests/
├── web-app.spec.js                # criteria 1-5 (already inside the `web` testMatch)
└── unit/test_section_context_gates.js   # optional static gate (C-19, token, closed list)
```

### Pattern 1: one global scroll offset, in the base layer

**What:** a single `scroll-padding-top` on `:root`, expressed from the existing `--header-height` token.
**When to use:** any document-scrolling app with a sticky header and in-page anchors.
**Why here:** it covers `[data-testid="material-prose"]` (`MaterialPage.jsx:230`) and `[data-testid="razbor-prose"]` (`RazborPage.jsx:290`) with zero component edits, which is D-01/D-05.

### Pattern 2: origin as a token read at exactly one place

**What:** producers attach `state={{ section }}`; exactly one consumer (`AppShell`) compares against the closed list and decides which pill is lit.
**When to use:** whenever "where did I come from" must be honest; the URL is not allowed to answer.
**Why here:** C-17's written-artefact requirement is only satisfiable if the literal comparison exists in one file.

### Pattern 3: producers know their section by construction

**What:** `ArchivePage` knows it is the archive; `KnowledgePage` knows it is the base; `IssuePage` knows `isCurrent`; `IssueToc`/`MaterialListRow` receive it as a required prop and forward it untouched; `MaterialPage` forwards whatever it received without inspecting it.
**When to use:** chain-of-origin propagation where each hop has authoritative knowledge and no hop is allowed to guess.
**Why here:** D-08 makes the archive branch honest even on a direct `/issues/12` visit (an archived issue only exists inside the archive).

### Anti-Patterns to Avoid

- **`NavLink` + explicit `aria-current`** — silently ignored while inactive (source-quoted). Use `<Link>`.
- **Deriving the section from `pathname` for `/materials/:id`** — explicitly forbidden by ROADMAP; the same URL serves three origins.
- **`localStorage` / `sessionStorage` for the origin** — a remembered section lies on a later direct visit.
- **`scroll-mt-*` on headings *and* `scroll-padding-top`** — double offset (C-19's whole point).
- **Measuring header height in JS and scrolling manually** — reintroduces layout thrash and cannot be expressed as "one mechanism".
- **`scroll-behavior: smooth`** — new visual behaviour plus a nondeterministic assertion window.
- **Hard-coding `'base'` inside `MaterialListRow`** or `'issue'` inside `IssueToc` — binds a reusable component to one section.
- **Validating `state.section` in two places** — breaks C-17's single-read-point artefact.

## Don't Hand-Roll

| Problem | Don't build | Use instead | Why |
|---|---|---|---|
| Anchoring below a sticky header | `onClick` + `scrollIntoView()` + `window.scrollTo(top)` arithmetic | `scroll-padding-top` on `:root` | The browser already implements the "optimal viewing region"; a JS version has to re-measure on every resize, font load and header reflow |
| Remembering where the reader came from | a React context / custom store / storage key | `Link state` + `useLocation().state` | `history.state` is exactly this, is scoped to the history entry, and is dropped by a direct navigation (proven by probe) |
| Identifying the current section | a route table / `matchPath` hierarchy | three literals compared at one point | D-07 fixes the list at three values; a matcher is more surface for the same answer |
| Waiting for a colour/attribute to settle | `page.waitForTimeout` / manual `evaluate` loops | `expect(locator).toHaveAttribute` / `expect.poll` | Web-first assertions retry; a manual read right after `waitForURL` read stale DOM in this very session |
| Reachability arithmetic in the spec | duplicating `maxScroll`/`docTop` maths per test | one shared `gate()` helper returning `reachable` | The C-00 formula appears in 6 criteria; divergence is a silent false-pass |

**Key insight:** every part of this phase already exists as a platform primitive (CSS scroll padding, history state, `aria-current`). The phase's risk is not missing capability — it is adding a second mechanism that drifts from the first.

## Common Pitfalls

### Pitfall 1: the offset fixes the desktop band only (640–999px stays negative)

**What goes wrong:** at 640–999px the token is `64px` (`80px` offset) while the live header is `123 / 111 / 99px`; `gap` is `-43 … -19`.
**Why it happens:** `sm` (640px) un-wraps the `<nav>`, but the *row* keeps wrapping because `search (min 240–280px) + toggle + identity + nav (378px)` does not fit until ~1000px. The header height is therefore not a function of `sm` at all.
**How to avoid:** keep the contract's test widths (1280 for the band, 390 and 639 for the token claims). Record the measured band in the phase summary as an accepted residual, next to the accepted `7px` desktop residual. Do **not** add a second breakpoint — that is chrome redesign (Deferred).
**Warning signs:** a reviewer asks "why is `--header-height` 200px only below 640?" — the answer is measured, not theoretical.

### Pitfall 2: `waitForURL` beats React's commit

**What goes wrong:** `page.evaluate` immediately after `await page.waitForURL(...)` reads the **previous** render; a spec then asserts a state the DOM has not reached.
**Why it happens:** URL update happens in the router before React commits the new tree.
**How to avoid:** web-first assertions only (`await expect(pill).toHaveAttribute('aria-current', 'true')` retries automatically), or `await expect(page.getByTestId('issue-ready')).toBeVisible()` as the readiness barrier.
**Warning signs:** a "flaky" pill test that passes when run alone.

### Pitfall 3: external webfont changes the measured header height

**What goes wrong:** `--header-height` measurement or a gap literal drifts between runs.
**Why it happens:** `index.css:1` imports Manrope from `fonts.googleapis.com`; without the font the fallback metrics differ (this session measured 73.0 where the UI-SPEC recorded 72.6).
**How to avoid:** read live rects (D-04 already requires this), assert the `[1, 32]` band, and `await page.evaluate(() => document.fonts.ready)` before geometry (precedent: `tests/admin.spec.js:339`).
**Warning signs:** a test that passes at 73.0 and fails at 72.6 because someone pinned `7.4`.

### Pitfall 4: `scroll-behavior: smooth` breaks the assertion window

**What goes wrong:** the rect is read mid-animation; `gap` is arbitrary.
**Why it happens:** a well-meaning "make the jump smooth" addition.
**How to avoid:** it is forbidden by C-01; verify with the C-19 gate (`zero matches for scroll-behavior`). Today `web/src` has **zero** `scroll-*` occurrences `[VERIFIED: rg over web/src]`, so the gate starts RED at "exactly one new declaration".
**Warning signs:** a gap assertion that only fails in a fast CI.

### Pitfall 5: hash already set → the second click does not scroll

**What goes wrong:** "before/after" measurement on the same anchor measures nothing the second time.
**Why it happens:** same-URL fragment navigation is a no-op.
**How to avoid:** one click per fresh `goto`, or reset hash + `scrollTo(0,0)` first (probe-proven). Never click the same TOC link twice in one test.
**Warning signs:** "after" equals "before" exactly.

### Pitfall 6: Tailwind class-substring traps in the pill assertions

**What goes wrong:** `toHaveClass(/bg-primary/)` passes on `bg-primary-solid`, so a stray base class or a dropped fill goes unnoticed.
**Why it happens:** `bg-primary` is a substring of `bg-primary-solid` (Phase 25's lesson, `STATE.md`).
**How to avoid:** split `className` on `/\s+/` and assert token membership (the existing pattern at `tests/admin.spec.js:311-316` and `:327-328`). For computed colour, read `backgroundColor` and compare to `rgb(124, 58, 237)` (active) / `rgba(0, 0, 0, 0)` (inactive).
**Warning signs:** a mutation that adds `bg-primary` keeps the suite green.

### Pitfall 7: moving the token out of `@theme static` breaks an existing gate

**What goes wrong:** a tidy-up moves `--header-height` from `@theme static` into `@layer base`, and `tests/unit/test_concept2_canon.js` fails.
**Why it happens:** that gate asserts the token's presence in the parsed `@theme static` block:
`assert.ok(productionDark.has('--header-height'), 'shell geometry depends on --header-height')` `[VERIFIED: tests/unit/test_concept2_canon.js:167-169]`.
**How to avoid:** keep `index.css:117` byte-identical; add only the media override in `@layer base`. Also: do **not** nest the `@media` inside `@theme static` — the gate's `parseBlock` helper terminates the block at the first `\n}` and would silently parse a truncated token map.
**Warning signs:** `npm run test:js` red on `concept 2 canon`.

### Pitfall 8: `reuseExistingServer` on `:5174` serves the wrong build

**What goes wrong:** mass false failures — every admin/mock spec lands on the login screen, or geometry comes from a stale server.
**Why it happens:** `playwright.config.js:48` reuses any listener on 5174; a stale Vite started before `VITE_USE_MOCKS=true` (or with `web/.env.local`'s `VITE_USE_MOCKS=false`, which **is** present in this workspace [VERIFIED]) is reused, and Playwright's `env` never applies.
**How to avoid:** before any run, `Get-NetTCPConnection -LocalPort 5174 -State Listen` and kill the owner (`STATE.md` § Blockers). Note Vite env precedence: a process-level `VITE_USE_MOCKS=true` *does* beat `.env.local`, so a **fresh** server is correct and only a reused one is not.
**Warning signs:** 10+ failures at once, all on a mock-only surface.

### Pitfall 9: a new spec file silently never runs

**What goes wrong:** criteria written into `tests/section-context.spec.js` are green-by-absence.
**Why it happens:** `testMatch: /(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/` (`playwright.config.js:70`) — exactly the Phase 25 lesson recorded in `STATE.md`.
**How to avoid:** put the criteria in `tests/web-app.spec.js`, or widen `testMatch` in the same commit and prove the new file actually executes.
**Warning signs:** Playwright reports the same test count as before the change.

### Pitfall 10: transitions pollute a computed-style read

**What goes wrong:** the fill colour is read mid-transition between inactive and active.
**Why it happens:** several shell/list elements carry `transition-colors` (e.g. `IssueToc.jsx:11`); Phase 25's `25-10` had to neutralise transitions before reading colours.
**How to avoid:** read colours only after the attribute assertion settles, or inject `*{transition:none!important}` before the colour probe (existing precedent).
**Warning signs:** a colour assertion that occasionally reads an interpolated value.

### Pitfall 11: an unknown issue number stays "archive"

**What goes wrong:** a pedant notes `/issues/99999` still lights «Архив».
**Why it happens:** the marker is `pathname.startsWith('/issues/')`, which is intentional (D-10: the branch, not the data, is the claim).
**How to avoid:** accept it explicitly in the plan; the section claim is about navigation structure, not resource existence. `tests/web-app.spec.js:358-368` already pins the soft-404 surface and must stay green.

## Code Examples

### 1. The whole NAV-01 production change (`web/src/index.css`)

```css
@layer base {
  button:not(:disabled) { cursor: pointer; }

  :root {
    color: var(--color-text-primary);
    background: var(--color-bg-app);
    font-family: var(--font-sans);
    /* NAV-01 · D-01/D-02/D-03 — the sticky header is not in flow, so a #fragment
       target would land underneath it. One declaration, every anchored surface. */
    scroll-padding-top: calc(var(--header-height) + 1rem);
  }

  /* D-02/D-C1 — measured, not derived: 196.6px @390x844 and 122.6px @639x844,
     max → 200px (multiple of 4). `sm` is 640px, where the nav stops owning a row. */
  @media (max-width: 639.98px) {
    :root { --header-height: 200px; }
  }

  body { /* unchanged */ }
  #root { /* unchanged */ }
  [data-theme="light"] { /* unchanged */ }
}
```

### 2. Producer / forwarder / consumer (`NAV-02`)

```jsx
// ArchivePage.jsx:70-73 — the archive knows it is the archive
<Link to={`/issues/${issue.number}`} state={{ section: 'archive' }} className="…">
// IssuePage.jsx:188 — isCurrent already exists on the component
<IssueToc items={toTocItems(items)} section={isCurrent ? 'issue' : 'archive'} />
// IssueToc.jsx:4,9-11 — required prop, forwarded verbatim
export default function IssueToc({ items, section }) { … <Link to={`/materials/${item.id}`} state={{ section }} …> }
// KnowledgePage.jsx:387 — the base knows it is the base
<MaterialListRow key={hit.slug} material={hit} section="base" />
// MaterialPage.jsx:259-266 — blind forward, no literals (C-17 keeps one validation point)
<Link to={`/materials/${item.slug}`} state={originSection ? { section: originSection } : undefined}>
```

### 3. Test skeleton for a rect criterion (gate → precondition → click → band)

```js
test("keeps the anchor target below the sticky header on a short section (NAV-01 c1)", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 })
  await page.goto("/materials/rag-systems")
  await page.waitForSelector('[data-testid="material-prose"]')
  await page.evaluate(() => document.fonts.ready)

  const anchorId = decodeURIComponent(
    (await page.getByTestId("material-toc").getByRole("link").first().getAttribute("href")).slice(1),
  )
  const gate = await page.evaluate((id) => {
    const doc = document.documentElement
    const t = document.getElementById(id)
    return {
      headerHeight: document.querySelector("header").getBoundingClientRect().height,
      pad: Number.parseFloat(getComputedStyle(doc).scrollPaddingTop) || 0,
      headingDocTop: t.getBoundingClientRect().top + window.scrollY,
      maxScroll: doc.scrollHeight - window.innerHeight,
    }
  }, anchorId)
  expect(gate.pad, "C-01: one global offset").toBeGreaterThanOrEqual(gate.headerHeight + 1)
  expect(gate.pad).toBeLessThanOrEqual(gate.headerHeight + 32)
  expect(gate.maxScroll, `fixture too short: ${gate.maxScroll} < ${gate.headingDocTop}`)
    .toBeGreaterThanOrEqual(gate.headingDocTop)   // C-00 strict form

  await page.getByTestId("material-toc").getByRole("link").first().click()
  await expect
    .poll(async () => page.evaluate((id) => {
      const h = document.querySelector("header").getBoundingClientRect()
      return document.getElementById(id).getBoundingClientRect().top - h.bottom
    }, anchorId))
    .toBeGreaterThanOrEqual(1)

  const after = await page.evaluate((id) => {
    const h = document.querySelector("header").getBoundingClientRect()
    const r = document.getElementById(id).getBoundingClientRect()
    return { gap: r.top - h.bottom, inViewport: r.bottom <= window.innerHeight }
  }, anchorId)
  expect(after.gap).toBeLessThanOrEqual(32)
  expect(after.inViewport).toBe(true)
})
```

## State of the Art

| Old approach | Current approach | When changed | Impact |
|---|---|---|---|
| Heading offset via `scroll-margin-top` per level, or JS `scrollTo(top - 64)` | `scroll-padding-top` on the scrollport, token-derived | CSS Scroll Snap L1, baseline Apr 2021 | One declaration instead of N selectors + JS; survives header reflow `[CITED: MDN]` |
| Active nav derived from URL only | `aria-current` + explicit current-context | ARIA `aria-current` (`page` / `true`) is well established | Lets "you are in section X" be stated when the URL cannot carry it |
| React Router v6 `useLocation().state` | v7 same contract, `history.state.usr` | v7 keeps the storage model | No migration needed; the repo is already on 7.18.3 |

**Deprecated/outdated:**
- Tailwind's `scroll-mt-*` utilities for sticky headers: not deprecated, but a *second* mechanism here — C-19 forbids it.
- `history.state`-based custom section stores: superseded by router state.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | `--header-height: 200px` remains sufficient for the ≤639px header in every state the phase tests (employee identity, 5 pills). The 320px case measures 209px, still cleared by the 216px offset by 7px. | §2 | If a spec renders the admin pill (6th) at ≤639px, the header grows and C-04/C-05 claim 2 (`pad ≥ header.height + 1`) could fail. Mitigation: do not run the mobile criteria on admin surfaces, or re-measure before locking. |
| A2 | The Phase 25 measurement `196.6px` and this session's `197px` are the same quantity (font-metric jitter), not a different layout. | §2 | If a future webfont change adds a nav row at 390, `200px` becomes insufficient and C-04 fails **visibly** — the desired failure mode, not a silent one. |
| A3 | Chromium serializes `scroll-padding-top: calc(64px + 1rem)` as `"80px"`, so `parseFloat` works. MDN lists the computed value as "as specified", i.e. not guaranteed cross-engine. | §1 | On WebKit/Firefox `parseFloat` could return `NaN` → `|| 0` → `0` and the assertion would fail for the wrong reason. The `web` project is Chromium-only, so no action; do not port the assertion. |
| A4 | A new `test()` block's first `page.goto` is a genuinely fresh origin (empty `history.state`), equivalent to `browser.newContext()`. | §4 | Low: probe-verified `{idx:0}`. If a future runner sets `storageState` with history (impossible today), the pin weakens. |

**If this table is empty:** n/a.

## Open Questions

1. **The 640–999px band has a negative offset (measured `gap -43 … -19`).**
   - What we know: locked D-02 puts `64px` on `sm+`, and the live header is `123px @640-768`, `111px @800`, `99px @900`, `73px @1000+`. The contract's criteria only test 1280 / 390 / 639, so acceptance passes while tablet remains broken.
   - What's unclear: whether the owner wants a one-line improvement (raise the offset above `sm` without touching the token, e.g. `@media (max-width: 999px) { :root { --header-height: 120px } }`) — which *contradicts* D-02's "64px on sm+".
   - **Recommendation:** ship D-02 as locked; record the measured band as an accepted residual in the phase summary; raise it as a candidate for a later UI phase (it is the same chrome problem the Deferred "сокращение мобильной шапки" names). Do not silently widen it.
2. **Should the C-19 "one mechanism" proof be a static gate or an E2E pin?**
   - What we know: `npm run test:js` runs `node --test tests/unit/*.js` over the whole directory (`scripts/run-unit-js.cjs`), so a new gate file is auto-included; `tests/unit/helpers/cssRules.js#parseRules` **flattens `@media`/`@layer` wrappers into one selector map**, so it cannot distinguish the base `:root` from the media `:root`.
   - What's unclear: whether the planner prefers one gate (cheap, catches `scroll-mt` regressions early) or relies on E2E only.
   - **Recommendation:** add `tests/unit/test_section_context_gates.js` asserting (a) exactly one `scroll-padding-top` in `web/src/` and it is in `index.css`, (b) zero `scroll-mt` / `scroll-margin` / `scroll-behavior` in `web/src/**/*.{js,jsx,css}`, (c) `--header-height` still declared inside `@theme static`, (d) no `localStorage`/`sessionStorage` in the files that touch `state.section`. Use raw regex over file text for (b)/(c) — **not** `parseRules` — because of the media-flattening caveat.
3. **Does C-12's "second arrow" require a fixture change?**
   - What we know: the only archive-issue materials (`sql-dashboards`, `prompt-engineering`) have no `related`, so the journey is unreachable today.
   - Recommendation: add `related: [{ slug: 'rag-systems', … }]` to `sql-dashboards` in `mock.js` (test fixture), and prove C-12 from `/archive`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| Node.js | all JS tooling | ✓ | 24.21.0 | — |
| npm | scripts | ✓ | 11.19.0 | — |
| `@playwright/test` | criteria 1-5 | ✓ | 1.62.1 | — |
| Chromium (Playwright bundle) | rect/scroll assertions | ✓ | `chromium-1234` in `.playwright-browsers` | `npm run playwright:install` |
| Vite dev server on `:5174` | `web` project | ✓ (startable) | Vite 8.2.2 | run `npm run dev --prefix web -- --port <free>` for manual probes |
| Port 5174 free | reproducible runs | ✓ at research time (no listener) | — | kill the owner before the run |
| `web/.env.local` with `VITE_USE_MOCKS=false` | **hazard, not a dependency** | present | — | Playwright's process env overrides it **only** for a freshly started server |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none.

## Validation Architecture

`workflow.nyquist_validation` is **absent** from `.planning/config.json` (keys present: `workflow._auto_chain_active`, `workflow.use_worktrees`, `git.allow_default_branch_commits`, `response_language`) → treat as **enabled**.

### Test Framework

| Property | Value |
|---|---|
| Framework | Playwright `@playwright/test` 1.62.1 (Chromium) + `node --test` (Node 24.21.0) |
| Config file | `playwright.config.js` (`web` project: `testMatch: /(web-app\|auth\|knowledge\|razbory\|admin(-chrome)?)\.spec\.js/`, `baseURL: http://127.0.0.1:5174`, `webServer` with `VITE_USE_MOCKS=true`, `reuseExistingServer: !CI`) |
| Quick run command | `npx playwright test tests/web-app.spec.js --project=web` |
| Full suite command | `npm run test:web` |
| Static gates | `npm run test:js` |
| Build gate | `npm run build` |

### Phase Requirements → Test Map

| Req ID | Behavior (UI-SPEC id) | Test type | Automated command | File exists? |
|---|---|---|---|---|
| NAV-01 | C-01 one offset, `pad ∈ [header+1, header+32]` | E2E | `npx playwright test tests/web-app.spec.js --project=web -g "anchor"` | ❌ Wave 0 (add to `tests/web-app.spec.js`) |
| NAV-01 | C-02 short section, band `[1,32]` | E2E | same file | ❌ Wave 0 (+ fixture) |
| NAV-01 | C-02b short page pin (`reachable === false`, gap > 32, no band) | E2E | same file | ❌ Wave 0 (fixture exists: `empty-dek-article`) |
| NAV-01 | C-03 long/deep section, band `[1,32]` | E2E | same file | ❌ Wave 0 (+ fixture) |
| NAV-01 | C-04 390×844: token ≠ 64px, `pad ≥ header+1`, target below header & in viewport | E2E | same file | ❌ Wave 0 |
| NAV-01 | C-05 639×844: same three claims | E2E | same file | ❌ Wave 0 |
| NAV-01 | C-06 razbor anchor via the same global rule | E2E | same file | ❌ Wave 0 (+ razbor fixture) |
| NAV-01 | C-19 exactly one mechanism; zero `scroll-mt`/`scroll-margin`/`scroll-behavior` | static | `npm run test:js` | ❌ Wave 0 (new gate) |
| NAV-02 | C-08 `/archive` → `/issues/13` lights Архив (`true` + fill) | E2E | same file | ❌ Wave 0 |
| NAV-02 | C-09 `/archive` → issue → material keeps Архив | E2E | same file | ❌ Wave 0 |
| NAV-02 | C-10 `/` → issue TOC → material lights Выпуск (D-09) | E2E | same file | ❌ Wave 0 |
| NAV-02 | C-11 `/knowledge` → hit row → material lights База | E2E | same file | ❌ Wave 0 |
| NAV-02 | C-12 second hop via «Связанные материалы» keeps the marker | E2E | same file | ❌ Wave 0 (+ `related` fixture) |
| NAV-02 | C-13 direct `/materials/:slug` lights nothing (fresh context) | E2E | same file | ❌ Wave 0 |
| NAV-02 | C-14 direct `/issues/13` lights Архив | E2E | same file | ❌ Wave 0 |
| NAV-02 | C-15 own routes keep `aria-current="page"` | E2E | same file | ❌ Wave 0 (today green → pin) |
| NAV-02 | C-16 `/admin/*` untouched (Админ `true`, three sections dark) | E2E | `npx playwright test tests/admin.spec.js --project=web -g "Админ pill"` | ✅ exists (`tests/admin.spec.js:300-330`) — extend with the three-section negative |
| NAV-02 | C-17 closed list, single read point | static artefact in PLAN + gate | `npm run test:js` | ❌ Wave 0 (checklist item **plus** gate) |
| NAV-02 | C-18 pill changes colour only, token-exact | E2E | same file | ❌ Wave 0 (pin; token-split pattern from `tests/admin.spec.js:311-328`) |
| NAV-02 | C-20 at most one lit pill (0/1 invariant) | E2E | same file | ❌ Wave 0 |

### Recommended RED → GREEN ordering

1. **RED-1 (offset, C-01 + pin C-02b).** Add the C-01 assertion and the C-02b pin for `empty-dek-article` (green today, stays green). `scrollPaddingTop` reads `"auto"` → `pad = 0 < header+1` → fails for the right reason.
2. **GREEN-1 (one CSS rule).** Add `scroll-padding-top: calc(var(--header-height) + 1rem)` in `@layer base :root`. C-01 + C-02b green.
3. **RED-2 (short and long band, C-02 + C-03) — fixture first.** Lengthen `rag-systems.body_markdown`, then assert the C-00 gate (`reachable === true`, with the "фикстура: `maxScroll=X < headingDocTop=Y` — удлинить тело" message) and the `[1, 32]` band. Fails with `gap ≈ -73` on both criteria.
4. **GREEN-2:** nothing to change — GREEN-1 already fixes it. This is the cheapest possible confirmation that the mechanism is global, not page-specific.
5. **RED-3 (mobile, C-04 + C-05).** Fails on claim 1 (`--header-height` is still `64px`) and claim 2 (`pad = 80 < 197+1`), regardless of claim 3. Then **GREEN-3**: add the `@media (max-width: 639.98px)` override.
6. **RED-4 (razbor, C-06).** Lengthen a razbor body; assert `reachable` + band on `razbor-toc`. Fails with `gap ≈ -73`. **GREEN-4:** no edits — proves D-05.
7. **RED-5 (archive → issue, C-08 + C-14).** Both fail because `/issues/13` lights nothing (probe: all five pills `null`). **GREEN-5:** convert «Архив» to `<Link>` with `pathname === '/archive' || pathname.startsWith('/issues/') || section === 'archive'`. Note C-15 must already be a written pin before this conversion so `page` on `/archive` cannot silently regress.
8. **RED-6 (state plumbing, C-09 → C-10 → C-11 → C-12, one arrow per task).** Each arrow is independently RED; add `state={{…}}` at exactly one producer per task. Start with C-09 (adds `state` to `ArchivePage` + `IssueToc` prop + `IssuePage` wiring), then C-10 (same `IssuePage` line, `'issue'` branch + «Выпуск» pill), then C-11 (`MaterialListRow` prop + `KnowledgePage`), then C-12 (`MaterialPage` blind forward + `related` fixture).
9. **Pins last, all at once (C-13, C-15, C-16, C-18, C-20) + static gate (C-19, C-17).** These must be *written after* the production edits but must be demonstrated not to weaken: run the pin suite against the pre-fix tree once (`git stash` or a scratch branch) to prove C-13/C-15/C-16/C-18 are genuinely green-before too.
10. **Phase gate:** `npm run test:web` (all web specs) + `npm run test:js` + `npm run build`, with port 5174 confirmed free beforehand.

### Sampling Rate

- **Per task commit:** `npx playwright test tests/web-app.spec.js --project=web`
- **Per wave merge:** `npm run test:web` (+ `npm run test:js` when a gate changed)
- **Phase gate:** full `npm run test:web` green, `npm run test:js` green, `npm run build` green, and the C-17 written artefact present in the PLAN.

### Wave 0 Gaps

- [ ] `tests/web-app.spec.js` — extend the existing TOC `describe` with criteria 1-5 (C-01…C-06 for NAV-01; C-08…C-20 for NAV-02). Preferred over a new file (Pitfall 9).
- [ ] `web/src/data/mock.js` — lengthen `rag-systems.body_markdown` (≥6 headings, ≥1.25 viewports below the target, first section still short); lengthen one razbor body (id 3 recommended); add one `related` to `sql-dashboards`.
- [ ] `tests/unit/test_section_context_gates.js` — new static gate for C-19 / `@theme static` token / closed-list absence of storage APIs.
- [ ] No framework install needed; no `playwright.config.js` change needed **if** the criteria stay in `web-app.spec.js`.

## Security Domain

`security_enforcement` is not present in `.planning/config.json`; the phase is frontend-only and touches no authentication, authorization, persistence or network surface.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard control |
|---|---|---|
| V2 Authentication | no | Unchanged (`RequireAuth`, `services/authApi.js` untouched) |
| V3 Session Management | no | Unchanged; no cookie/storage write is added (C-17 gate additionally forbids `localStorage`/`sessionStorage` in the changed files) |
| V4 Access Control | no | The marker paints a pill only; it is never an authorization input, and `/admin/*` access control stays server-side + `RequireAuth` |
| V5 Input Validation | yes (client-side hygiene) | `state.section` is compared against a closed list of three literals in `AppShell`; any other value lights nothing (C-17) |
| V6 Cryptography | no | — |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard mitigation |
|---|---|---|
| Client-controlled `history.state` used as a trust signal | Spoofing (of UI context only) | Section markers must never gate data or routes; they only choose a CSS class. Verified: no consumer reads it for authorization. |
| Persistent origin claim via storage | Information disclosure / Repudiation of context | Banned by D-07/D-10 and enforced by the C-17 static gate; `history.state` dies on a direct visit (probe-proven) |
| DOM injection through the marker | Tampering | `state.section` is compared, never rendered or interpolated into markup/`className` |
| Open-redirect style state abuse | — | `state` carries no URL and no path (D-07 rejected `{ from: '/archive' }` for exactly this reason) |

## Sources

### Primary (HIGH confidence)

- **Session probe, Chromium 1234 / Playwright 1.62.1 against the mock build (Vite 8.2.2, `VITE_USE_MOCKS=true`)** — header heights by width, `scroll-padding-top` serialization, A/B anchor measurement, `history.state` lifecycle across reload/`goto`, current pill states on `/issues/13` and `/materials/:slug`, fixture reachability table. All numbers quoted above.
- **Built stylesheet** `web/dist/assets/index-BAhCYysH.css` — layer order (`@layer components; … @layer properties{…} @layer theme{:root,:host{…}} @layer base{…} @layer utilities{…}`) and `--header-height:64px` inside the theme layer.
- **In-repo source read this session:** `web/src/index.css:7,117,139-161`; `web/src/components/AppShell.jsx:2,11-15,35,39,67,73-101`; `web/src/pages/{ArchivePage,IssuePage,KnowledgePage,MaterialPage,RazborPage}.jsx`; `web/src/components/{IssueToc,MaterialListRow}.jsx`; `web/src/App.jsx:34-67`; `web/src/utils/markdownToc.js:6`; `web/src/services/contentApi.js:289-311`; `web/src/data/mock.js`; `tests/web-app.spec.js:96-120,173-198,550`; `tests/razbory.spec.js:16,43-56`; `tests/admin.spec.js:109-113,300-330`; `tests/unit/test_concept2_canon.js:167-169`; `tests/unit/helpers/cssRules.js`; `playwright.config.js:44-54,70`; `package.json`; `web/package.json`; `.planning/config.json`.
- **react-router docs (Context7, `/remix-run/react-router`)** — `NavLink` `aria-current` implementation (`ariaCurrent = isActive ? ariaCurrentProp : undefined`), `Link > state`.

### Secondary (MEDIUM confidence)

- **MDN `scroll-padding-top`** — initial value `auto`, applies to scroll containers, "exclude regions … obscured by fixed-positioned toolbars", baseline Apr 2021, computed value "as specified".

### Tertiary (LOW confidence)

- none — every operational claim above was either read from the repo this session or measured in a browser.

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — versions read from `package.json` and `npx playwright --version`; no new dependency.
- Architecture / mechanism: HIGH — the offset fix was proven A/B in a browser, and the `NavLink` limitation is quoted from the router's own source.
- Pitfalls: HIGH for P1-P5 (measured), P7-P9 (gate/runner files read), P6/P10 (Phase 25 precedent recorded in `STATE.md`), P11 (semantics, deliberate).
- Test harness: HIGH — config, testMatch, helpers and fixture contents read; fixture gaps measured, not assumed.

**Research date:** 2026-10-22
**Valid until:** ~2026-11-21 (30 days) — stable primitives; re-measure `--header-height` only if the shell markup, the nav item count, or the webfont import changes.
