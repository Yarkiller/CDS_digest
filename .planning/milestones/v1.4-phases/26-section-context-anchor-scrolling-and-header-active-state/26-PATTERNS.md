# Phase 26: Section context — anchor scrolling and header active state - Pattern Map

**Mapped:** 2026-10-22
**Files analyzed:** 12 (11 in the locked change set + 1 recommended extension)
**Analogs found:** 11 / 12 — the one gap is React Router's `Link state` prop, which has **no precedent anywhere in `web/src`** (see [No Analog Found](#no-analog-found))
**Tracked-source gate:** every analog named below was verified with `git ls-files -- <path>` (all non-empty). No `.gsd/capabilities/**` mirror or `node_modules`/`dist` path is used as an analog.

> Read this together with `26-CONTEXT.md` (D-01…D-11 LOCKED), `26-RESEARCH.md` (measured values, `NavLink` source-proof, fixture reachability) and `26-UI-SPEC.md` (C-00…C-20). This document only answers **"which existing code do I copy, and what exactly does it say?"** — it does not re-open any decision.

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `web/src/index.css` | config (design tokens + base layer) | declarative / cascade | same file: `@layer base { :root { … } }` `139-148` next to `@theme static` token map `7-123` | exact (in-file) |
| `web/src/components/AppShell.jsx` | component (shell chrome) | transform: `location` → derived pill state | same file: «Админ» pill `93-104` + `adminActive` `36-39` | exact (in-file) |
| `web/src/components/IssueToc.jsx` | component (presentational list) | prop → `Link` render | `MaterialListRow.jsx:12-16` (same shape: rows of `<Link to={/materials/...}>`) | role-match |
| `web/src/components/MaterialListRow.jsx` | component (presentational list row) | prop → `Link` render | `IssueToc.jsx:9-21` (mirror image of the same pattern) | role-match |
| `web/src/pages/IssuePage.jsx` | page / container | request-response (fetch → render) + prop derivation | `ArchivePage.jsx` (page that owns `Link` construction) + own `isCurrent` JSDoc `97-101` | role-match |
| `web/src/pages/ArchivePage.jsx` | page / container | request-response (fetch → render) | `KnowledgePage.jsx:386-388` (page-level list of navigable rows) | role-match |
| `web/src/pages/KnowledgePage.jsx` | page / container | request-response | own call site `386-388` + `ArchivePage.jsx:68-86` (link-list rendering) | exact (in-file) |
| `web/src/pages/MaterialPage.jsx` | page / container | request-response + blind forward of `location.state` | `RequireAuth.jsx:11,72` / `AnalyticsPageViews.jsx:7` (`useLocation()` reads) | role-match |
| `web/src/data/mock.js` | model / fixture seed | static data (consumed by `contentApi`) | same file: `materials[]` `37-208`, `razbory[]` `257-293` | exact (in-file) |
| `tests/web-app.spec.js` | test (E2E, Playwright) | browser assertions | same file: TOC describe `96-120`; `tests/admin.spec.js:300-330` (pill tokens) | exact / role-match |
| `tests/unit/test_section_context_gates.js` **(new)** | test (static `node --test` gate) | source-text scan | `tests/unit/test_concept2_canon.js:17-26,149-170` + `tests/unit/test_semantic_token_coverage.js:581-591` | role-match |
| `tests/admin.spec.js` *(recommended extension, C-16 negative)* | test (E2E) | browser assertions | same file `108-115` helpers, `300-330` pill test | exact (in-file) |

---

## Pattern Assignments

### 1. `web/src/index.css` (config, cascade)

**Analog:** itself — the existing `@layer base { :root { … } }` block, placed *after* `@theme static`.

**Why this block and not `@theme static`:** the layer order in the built stylesheet is `components → properties → theme → base → utilities`, and cascade layers are compared **before** specificity. So a declaration in `@layer base :root` wins over the token in `@theme` (`RESEARCH.md` §1, probe table). The UI-SPEC's "`:root` beats `html` by specificity" rationale is wrong; the practical placement is the same.

**Existing block to extend** (`web/src/index.css:139-159`):

```css
@layer base {
  button:not(:disabled) {
    cursor: pointer;
  }

  :root {
    color: var(--color-text-primary);
    background: var(--color-bg-app);
    font-family: var(--font-sans);
  }

  body {
    margin: 0;
    min-height: 100svh;
    background: var(--color-bg-app);
    color: var(--color-text-primary);
  }

  #root {
    min-height: 100svh;
  }
}
```

**The token the new rule must consume, and must NOT be edited** (`web/src/index.css:116-117`, inside `@theme static`):

```css
  --container-max: 1280px;
  --header-height: 64px;
```

`tests/unit/test_concept2_canon.js:167-169` asserts `productionDark.has('--header-height')`, where `productionDark` is produced by `parseBlock(css, '@theme(?:\\s+static)?')` — a helper that terminates the block at the first `\n}` (`test_concept2_canon.js:30-38`). Two consequences the executor must honour:

1. Keep `--header-height: 64px;` **byte-identical, in place** at line 117.
2. Never nest the new `@media` inside `@theme static` — `parseBlock` would truncate the token map there.

**Comment style to match** (in-file precedent `index.css:4-6`, `34-44`): a short justification with the decision id, wrapped at ~95 columns.

**Declaration shape** (RESEARCH.md §1/Code Examples 1 — the only new production CSS):

```css
  :root {
    /* … existing three declarations unchanged … */
    /* NAV-01 · D-01/D-02/D-03 — the sticky header is out of flow, so a #fragment
       target lands underneath it. One declaration covers every in-page anchor. */
    scroll-padding-top: calc(var(--header-height) + 1rem);
  }

  @media (max-width: 639.98px) {
    :root { --header-height: 200px; }
  }
```

`200px` is measured (`196.6` @390×844, `122.6` @639×844 → max, rounded up to a multiple of 4), not derived from padding sums; record that provenance in the comment (precedent: the measured-ratio comments at `index.css:48-50`, `57-59`).

---

### 2. `web/src/components/AppShell.jsx` (component, transform)

**Analog:** the «Админ» pill in the same file — the only state-derived, non-`NavLink` pill in the codebase.

**Imports** (`AppShell.jsx:1-6`) — `Link` is already imported, nothing to add:

```jsx
import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import SearchPill from './SearchPill.jsx'
import ThemeToggle from './ThemeToggle.jsx'
import { getAccessToken } from '../services/authApi.js'
import { isLoginRequired, isMocksEnabled } from '../services/authEnv.js'
import { fetchMe } from '../services/meApi.js'
```

**The one class source, unchanged** (`AppShell.jsx:11-15`) — C-18 pins every token here:

```jsx
const linkClass = ({ isActive }) =>
  [
    'inline-flex min-h-11 items-center rounded-full px-2.5 text-sm',
    isActive ? 'bg-primary-solid text-on-solid' : 'text-text-secondary hover:bg-bg-surface',
  ].join(' ')
```

**The single read point and its comment style** (`AppShell.jsx:35-39`):

```jsx
  const { pathname } = useLocation()
  // D-09: «Админ» lights up on digest, pipeline, and the materials preview alike.
  // IN-04: the /admin/ prefix is the single source of truth — there is no /admin route
  // (D-04), and the catch-all redirects /admin to /, so an equality branch is dead code.
  const adminActive = pathname.startsWith('/admin/')
```

`state` joins this destructuring (`const { pathname, state } = useLocation()`), so `state?.section` is read in exactly one file (C-17).

**Current markup to convert** (`AppShell.jsx:73-92`) — «Выпуск»/«Архив»/«База» are `NavLink`; «Голосование»/«Разборы» stay `NavLink`:

```jsx
          <nav
            className="order-last flex w-full flex-wrap gap-1 sm:order-none sm:w-auto"
            aria-label="Основная навигация"
          >
            <NavLink to="/" end className={linkClass}>
              Выпуск
            </NavLink>
            <NavLink to="/archive" className={linkClass}>
              Архив
            </NavLink>
            <NavLink to="/knowledge" className={linkClass}>
              База
            </NavLink>
            <NavLink to="/voting" className={linkClass}>
              Голосование
            </NavLink>
            <NavLink to="/razbory" className={linkClass}>
              Разборы
            </NavLink>
```

**The pattern to copy verbatim — «Админ» pill** (`AppShell.jsx:93-104`). Note the four-line `WR-02` comment (the exact reason `NavLink` cannot be used), `aria-current="true"` (not `page`), and `className={linkClass({ isActive: adminActive })}`:

```jsx
            {appRole === 'admin' ? (
              <Link
                to="/admin/digest"
                // WR-02: NavLink derives aria-current from `to="/admin/digest"`, so the pill
                // was announced as inactive on pipeline/preview while looking active. Set it
                // from the already-computed prefix instead — "true" (not "page") because the
                // href targets digest while the whole admin section is the current context.
                aria-current={adminActive ? 'true' : undefined}
                className={linkClass({ isActive: adminActive })}
              >
                Админ
              </Link>
            ) : null}
```

**Derivation block to add** (RESEARCH.md §3, suggested shape). Keep it beside `adminActive`, above `useEffect`, with the same "why" comment density:

```jsx
  const { pathname, state } = useLocation()
  const adminActive = pathname.startsWith('/admin/')
  // D-07: closed list — 'archive' | 'base' | 'issue'. Anything else lights nothing (D-10).
  const section = state?.section

  const homeRoute = pathname === '/'
  const archiveRoute = pathname === '/archive'
  const issuesBranch = pathname.startsWith('/issues/')
  const baseRoute = pathname === '/knowledge'

  const homeLit = homeRoute || section === 'issue'
  const archiveLit = archiveRoute || issuesBranch || section === 'archive'
  const baseLit = baseRoute || section === 'base'

  // D-11: 'page' only for the pill's own route; 'true' when the section is claimed by
  // navigation state or by the /issues/ prefix.
  const current = (ownRoute) => (ownRoute ? 'page' : 'true')
```

Then each of the three becomes:

```jsx
            <Link
              to="/"
              aria-current={homeLit ? current(homeRoute) : undefined}
              className={linkClass({ isActive: homeLit })}
            >
              Выпуск
            </Link>
```

Do **not** add `'page'` to `linkClass` consumers, do not touch `min-h-11 rounded-full px-2.5 text-sm`, do not add a new token — C-18 compares the two states as token *sets*.

---

### 3. `web/src/components/IssueToc.jsx` (component, prop → Link)

**Analog:** `MaterialListRow.jsx` — same shape (a reusable row whose sole link target is `/materials/:slug`), different visual layout.

**Current file** (`IssueToc.jsx:1-27`) — the whole component is 27 lines; the link is `9-21`:

```jsx
import { Link } from 'react-router-dom'
import { padIssueNumber } from '../utils/filters.js'

export default function IssueToc({ items }) {
  return (
    <div className="divide-y divide-border border-y border-border">
      {items.map((item) => (
        <div key={item.id} className="py-5">
          <Link
            to={`/materials/${item.id}`}
            className="grid min-h-11 grid-cols-[2rem_minmax(0,1fr)_auto] items-baseline gap-4 rounded-xl px-2 text-inherit no-underline transition-colors hover:bg-primary/15 hover:text-primary-text sm:grid-cols-[2rem_minmax(0,1fr)_auto_auto]"
          >
```

**Change:** a required `section` prop, forwarded untouched as `state={{ section }}`:

```jsx
export default function IssueToc({ items, section }) {
  …
          <Link
            to={`/materials/${item.id}`}
            state={{ section }}
            className="… unchanged …"
          >
```

**Convention:** no default value (see [Shared Patterns › Required prop, no default](#required-prop-no-default-the-typescript-substitute)). `IssueToc` renders both the current issue (`'issue'`) and archived issues (`'archive'`), so a hard-coded literal here is a guaranteed defect (RESEARCH.md §5). Carry the existing JSDoc-free style; if adding a contract comment, mirror `MaterialListRow.jsx:3-6` rather than inventing a new format.

---

### 4. `web/src/components/MaterialListRow.jsx` (component, prop → Link)

**Analog:** `IssueToc.jsx` (mirror image) — and it is the file that already documents its own contract and link derivation.

**Imports + contract comment + derivation** (`MaterialListRow.jsx:1-10`):

```jsx
import { Link } from 'react-router-dom'

/**
 * Knowledge / issue hit row. Links by slug (KNOW-01 / D-59).
 * cover_url/cover may be null — degrade without thumbnail (Q2).
 */
export default function MaterialListRow({ material }) {
  const slug = material.slug ?? material.id
  const cover = material.cover_url ?? material.cover ?? null
  const tags = material.tags ?? []
```

**Link to extend** (`MaterialListRow.jsx:12-16`):

```jsx
    <Link
      to={`/materials/${slug}`}
      className="grid grid-cols-[4rem_minmax(0,1fr)] gap-4 border-b border-border py-5 text-inherit no-underline hover:bg-bg-surface sm:grid-cols-[5rem_minmax(0,1fr)]"
    >
```

**Change:** `export default function MaterialListRow({ material, section })` + `state={{ section }}` on the `Link`. Add the JSDoc `@param` (see shared pattern) recording `section: 'archive'|'base'|'issue'`. **Never** default to `'base'` inside the component (CONTEXT.md Claude's Discretion #3): the next consumer must be forced to choose.

---

### 5. `web/src/pages/IssuePage.jsx` (page, fetch → render)

**Analog:** the page itself — `isCurrent` already exists and is documented; the only new thing is passing a literal derived from it.

**Imports** (`IssuePage.jsx:1-7`) — nothing to add:

```jsx
import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import EditorialCallout from '../components/EditorialCallout.jsx'
import IssueToc from '../components/IssueToc.jsx'
import PlatformProofBanner from '../components/PlatformProofBanner.jsx'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
```

**Existing prop contract, the precedent for a documented prop** (`IssuePage.jsx:97-101`):

```jsx
/**
 * @param {{ isCurrent?: boolean }} props
 * isCurrent=true on `/` (EditorialCallout, D-34); false on `/issues/:number`.
 */
export default function IssuePage({ isCurrent = true }) {
```

**Call site to change** (`IssuePage.jsx:187-189`):

```jsx
      <h2 className="mb-6 font-display text-2xl font-semibold">В этом выпуске</h2>
      <IssueToc items={toTocItems(items)} />
    </section>
```

becomes:

```jsx
      <IssueToc items={toTocItems(items)} section={isCurrent ? 'issue' : 'archive'} />
```

`isCurrent` is set by the route table (`web/src/App.jsx`: `/` → `isCurrent`, `issues/:number` → `isCurrent={false}`), so no URL parsing and no `useLocation()` is added here. Note the file already imports `useParams` but not `useLocation` — keep it that way.

---

### 6. `web/src/pages/ArchivePage.jsx` (page, fetch → render)

**Analog:** `KnowledgePage.jsx:386-388` for "a page maps rows to navigable links"; the card markup is in this file at `68-86`.

**Imports** (`ArchivePage.jsx:1-2`) — `Link` already imported:

```jsx
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
```

**Card link to change** (`ArchivePage.jsx:68-73`):

```jsx
          {issues.map((issue) => (
            <li key={issue.number}>
              <Link
                to={`/issues/${issue.number}`}
                className="block min-h-11 rounded-xl border border-border bg-bg-surface p-5 no-underline transition hover:border-primary"
              >
```

Add `state={{ section: 'archive' }}` as the second prop, before `className`, keeping the existing prop order (`to`, `state`, `className`) — that is the order the `AppShell` admin pill uses (`to`, comment, `aria-current`, `className`).

---

### 7. `web/src/pages/KnowledgePage.jsx` (page, fetch → render)

**Analog:** its own `KnowledgeHitList` — the **only** `MaterialListRow` consumer (also cited as `KNOW-03` in the comment).

**Imports** (`KnowledgePage.jsx:1-`) include `useSearchParams`; `MaterialListRow` is imported at the top of the file. No import changes are needed.

**Call site** (`KnowledgePage.jsx:381-390`):

```jsx
function KnowledgeHitList({ items, loadingMore, hasMore, searching, onLoadMore }) {
  if (items.length === 0) return null
  return (
    <div>
      {items.map((hit) => (
        // KNOW-03: every hit, including DS, opens /materials/{slug}.
        <MaterialListRow key={hit.slug} material={hit} />
      ))}
```

becomes `<MaterialListRow key={hit.slug} material={hit} section="base" />`. The literal lives **here**, in the base-section page, not in the row. Keep the `KNOW-03` comment untouched.

---

### 8. `web/src/pages/MaterialPage.jsx` (page, blind forward)

**Analog:** `RequireAuth.jsx:11,72` and `AnalyticsPageViews.jsx:7` for the `useLocation()` read convention; the link to change is its own `255-266`.

**Imports to extend** (`MaterialPage.jsx:3`) — `useLocation` is missing today:

```jsx
import { Link, Navigate, useParams } from 'react-router-dom'
```

→ `import { Link, Navigate, useLocation, useParams } from 'react-router-dom'` (keep alphabetical order inside the braces — that is the file's convention).

**Component head** (`MaterialPage.jsx:60-62`):

```jsx
export default function MaterialPage({ preview = false, loadMaterial }) {
  const { id: slug } = useParams()
  const [material, setMaterial] = useState(null)
```

add, after the `useParams` line and **before** the `useState` cluster (so the hook order reads location → params → state):

```jsx
  // C-17: this page forwards the marker verbatim — it never compares the three literals.
  // /admin/materials/:id mounts the same page with no router state, so nothing is produced.
  const { state: originState } = useLocation()
```

**Derived block precedent** (`MaterialPage.jsx:174-179`) — this is where a `const originSection = originState?.section` belongs, next to the other `material`-derived values:

```jsx
  const headings = extractMarkdownHeadings(material.body_markdown ?? '')
  const tags = material.tags ?? []
  const related = material.related ?? []
  const dek = (material.dek ?? '').trim()
  const provenance = (material.provenance ?? '').trim()
  const dateLabel = formatPublishedLabel(material)
```

**Link to change** (`MaterialPage.jsx:255-266`):

```jsx
          {related.length > 0 ? (
            <section className="mt-10" data-testid="material-related">
              <h2 className="font-display text-xl font-semibold">Связанные материалы</h2>
              <ul className="mt-3 space-y-2">
                {related.map((item) => (
                  <li key={item.slug}>
                    <Link to={`/materials/${item.slug}`} className="text-primary-text no-underline hover:underline">
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
```

becomes:

```jsx
                    <Link
                      to={`/materials/${item.slug}`}
                      state={originSection ? { section: originSection } : undefined}
                      className="text-primary-text no-underline hover:underline"
                    >
```

**Do not** add a `preview &&` guard or validate the marker here (RESEARCH.md §5: two literal sites would break C-17). The footer links «← К выпуску» / «В архив» (`MaterialPage.jsx:270-277`) stay untouched — UI-SPEC "что категорически не меняется".

---

### 9. `web/src/data/mock.js` (fixture seed)

**Analog:** the same file's existing entries. This is a **test-only** edit (no production behaviour, no schema change).

**`materials[]` entry shape — the one to lengthen** (`mock.js:37-70`), including `body_markdown` **and** the `body[]` fallback and the existing `related` precedent:

```js
  {
    id: 'rag-systems',
    title: 'Building Production RAG Systems',
    …
    body: [
      'Для СВА наиболее релевантны сценарии поиска по регламентам, методологиям аудита и внутренним отчётам с цитированием источников.',
      'На этапе поиска система объединяет семантическое совпадение с точным совпадением терминов.',
    ],
    body_markdown: [
      '## Введение',
      '',
      'Для СВА наиболее релевантны сценарии поиска по регламентам, методологиям аудита и внутренним отчётам с цитированием источников.',
      '',
      '## Гибридный поиск',
      '',
      'На этапе поиска система объединяет семантическое совпадение с точным совпадением терминов.',
    ].join('\n'),
    related: [{ slug: 'anomaly-detection', title: 'Anomaly Detection in Audit Pipelines' }],
  },
```

Facts the fixture edit must respect (all measured / pinned):

- `contentApi.js:289-311` uses `body_markdown` verbatim when present, else joins `body[]`.
- `tests/web-app.spec.js:92-93` and `:28` assert `/введение/i` and `/регламент/i` — keep both strings.
- C-02 requires the **first** section to stay short while ≥1.25 viewports of prose sit below the target; C-03 requires ≥6 headings. Six headings is a **test-count decision** to be written in the test, not in the fixture comment.
- `empty-dek-article` already satisfies C-02b and must not be lengthened (`mock.js:89`: `body_markdown: '## Section One\n\nFixture prose without an audit dek.'`).

**The archive-issue material that needs `related`** (`mock.js:170-189`) — note it has **no** `body_markdown` at all, only `body:`, so it has no headings and `maxScroll ≈ 0` (irrelevant for C-12):

```js
  {
    id: 'sql-dashboards',
    title: 'SQL-дашборды для аудиторской отчётности',
    …
    summary: 'Гайд для Data Analyst: витрины, KPI и контроль сроков отчётности.',
    body: ['Содержит примеры SQL и структуру дашборда цикла аудита.'],
  },
```

Add `related: [{ slug: 'rag-systems', title: 'Building Production RAG Systems' }]` after `body`. `tests/web-app.spec.js:79-86` asserts `material-related` on `rag-systems` only, so this addition cannot flip an existing assertion.

**`razbory[]` entry shape** (`mock.js:257-293`) — lengthen **an existing** body (id 3 preferred; id 2 is pinned by `tests/razbory.spec.js:43-56` which clicks «Качество»):

```js
export const razbory = [
  {
    id: 4,
    title: 'RAG в корпоративной среде',
    meeting_at: '2026-04-14T10:00:00.000Z',
    status: 'announcement',
    body_markdown: '',
    notebook_path: null,
  },
  {
    id: 3,
    title: 'LLM для анализа аудиторских данных',
    meeting_at: '2026-03-31T10:00:00.000Z',
    status: 'published',
    body_markdown:
      '## Контекст\n\nКак LLM помогают разбирать аудиторские выборки.\n\n## Подход\n\nЧанкинг, промпты и проверка фактов.\n\n## Итоги\n\nЧто взять в следующий цикл.',
    notebook_path: null,
  },
```

**Hard constraint:** `tests/razbory.spec.js:16` pins `chronology-item` count to `4` — **do not add a razbor**. Bodies are single-line `\n\n`-joined strings; keep that form.

---

### 10. `tests/web-app.spec.js` (E2E)

**Analog (layout + locators):** the existing TOC test at `96-120`; **analog (pill attribute + token assertions):** `tests/admin.spec.js:300-330`.

**File conventions** (`web-app.spec.js:1-3`) — CommonJS, double quotes, explicit `test.describe`:

```js
const { expect, test } = require("@playwright/test");

test.describe("web app main flows", () => {
```

**Existing anchor/TOC test — the describe to extend (criteria 1-2, C-01…C-06)** (`web-app.spec.js:96-120`):

```js
  test("keeps the material TOC as a desktop rail and a mobile disclosure", async ({ page }) => {
    await page.goto("/materials/rag-systems");

    const rail = page.getByTestId("material-toc");
    await expect(rail).toBeVisible();
    await expect(rail).toHaveCSS("position", "sticky");
    await expect(rail.getByRole("link").first()).toBeVisible();

    // Below the lg breakpoint the rail gives way to a disclosure with the same links.
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(rail).toBeHidden();

    const disclosure = page.locator("details", { hasText: "Содержание" }).first();
    await expect(disclosure).toBeVisible();
    await disclosure.locator("summary").click();
    await expect(disclosure.getByRole("link").first()).toBeVisible();

    // Neither layout may introduce horizontal overflow on a phone.
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });
```

Note: this test mutates the viewport **mid-test**; the new rect criteria must set the viewport **first** (`await page.setViewportSize({ width: 1280, height: 800 })` or a scoped `test.describe` + `test.use({ viewport })`, precedent `tests/razbory.spec.js:8`).

**Existing shell-nav test — locator conventions for criteria 3-5** (`web-app.spec.js:173-198`):

```js
    const nav = page.getByRole("navigation", { name: /основная навигация/i });
    const archiveNav = nav.getByRole("link", { name: /^Архив$/ });
    await expect(archiveNav).toBeVisible();

    // Архив sits between Выпуск and База (D-28)
    const labels = await nav.getByRole("link").allTextContents();
```

Reuse exactly this shape: `getByRole("navigation", { name: /основная навигация/i })` scoped, then `getByRole("link", { name: /^Архив$/ })` (anchored — «Архив» is a substring of nothing here, but the anchored form is the repo convention and survives future copy).

**Token-split class assertion — the Phase 25 lesson, copy verbatim** (`tests/admin.spec.js:308-316` and `327-328`):

```js
    // The negative site: the inactive pill must carry neither the -solid fill nor a stray
    // bare base class — this is the only row that catches a leftover `bg-primary`.
    const homeTokens = (await homeLink.getAttribute("class")).split(/\s+/);
    expect(homeTokens).not.toContain("bg-primary");
    expect(homeTokens).not.toContain("bg-primary-solid");

    // …
      const loopTokens = (await adminLink.getAttribute("class")).split(/\s+/);
      expect(loopTokens).toContain("bg-primary-solid");
      expect(loopTokens).not.toContain("bg-primary");
```

`toHaveClass(/bg-primary/)` is forbidden: `bg-primary` is a substring of `bg-primary-solid` (RESEARCH.md Pitfall 6). C-18 additionally requires asserting `min-h-11`, `rounded-full`, `px-2.5`, `text-sm` in **both** states.

**Helper shape for the shell nav** (`tests/admin.spec.js:108-115`) — copy into the new `describe` rather than importing across spec files (no shared spec helper module exists):

```js
  function shellNav(page) {
    return page.getByRole("navigation", { name: /основная навигация/i });
  }

  function shellAdminLink(page) {
    return shellNav(page).getByRole("link", { name: /^Админ$/ });
  }
```

**Readiness / timing conventions.** `issue-ready` is the render barrier used by this file (`web-app.spec.js:168`) — use `await expect(page.getByTestId("issue-ready")).toBeVisible()` after navigation, then web-first assertions. Never `page.evaluate` straight after `waitForURL` (RESEARCH.md Pitfall 2). For geometry, `await page.evaluate(() => document.fonts.ready)` first (precedent `tests/admin.spec.js:339`).

**Fresh-origin rule for C-13/C-14:** a brand-new `test()` whose first action is `page.goto(...)` is already a fresh `history.state` (RESEARCH.md §4/A4). Do **not** hand-roll `browser.newContext()` — it loses `use.baseURL` from `playwright.config.js:73`.

**New spec file is forbidden** (C-19/`RESEARCH.md` Pitfall 9): `playwright.config.js:70` testMatch is `/(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/`.

---

### 11. `tests/unit/test_section_context_gates.js` (new static gate)

**Analog:** `tests/unit/test_concept2_canon.js` — same `node --test` + `assert/strict` + `describe/it` style with a `read()` helper and regex assertions on source text.

**Header/import/helper convention** (`test_concept2_canon.js:17-26`):

```js
const assert = require('node:assert/strict')
const { existsSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { parseRules } = require('./helpers/cssRules')

const ROOT = path.join(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')
const exists = (relativePath) => existsSync(path.join(ROOT, relativePath))
```

**Regex-absence assertion to copy** (`test_concept2_canon.js:151-157`) — the shape for "zero `scroll-mt` / `scroll-margin` / `scroll-behavior` in `web/src`":

```js
describe('Concept 2 shell is expressed through tokens', () => {
  const shell = read('web/src/components/AppShell.jsx')

  it('has no literal colours', () => {
    const literals = shell.match(/#[0-9a-fA-F]{3,8}\b/g) ?? []
    assert.deepEqual(literals, [], `shell must paint from tokens, not literals: ${literals.join(', ')}`)
  })
```

**Token-presence assertion to copy** (`test_concept2_canon.js:166-169`):

```js
  it('keeps the header geometry token the shell depends on', () => {
    assert.ok(productionDark.has('--header-height'), 'shell geometry depends on --header-height')
  })
```

**Directory-walk helper** for "scan every file under `web/src`" — copy from `tests/unit/test_semantic_token_coverage.js:581-591`:

```js
/** Every .js/.jsx source under web/src, as `{ relative, source }` pairs. */
function sources() {
  return readdirSync(path.join(ROOT, 'web/src'), { recursive: true })
    .filter((entry) => entry.endsWith('.js') || entry.endsWith('.jsx'))
    .map((entry) => {
      const relative = path.join('web/src', entry).split(path.sep).join('/')
      return { relative, source: read(relative) }
    })
}
```

**Caveat that dictates raw regex, not `parseRules`:** `tests/unit/helpers/cssRules.js:49-56` descends into `@layer`/`@media`/`@supports` and **merges rules by selector**, so the base `:root` and the media `:root` collapse into one entry. A gate that must prove "the override lives in a media block" while "the token stays in `@theme static`" cannot use it. Use `read()` + `match` on the raw file (RESEARCH.md Open Question 2).

**Auto-inclusion is free:** `scripts/run-unit-js.cjs` reads `tests/unit` with `readdirSync(...).filter(name => name.endsWith('.js'))`, so a new file under `tests/unit/` runs under `npm run test:js` with no config edit.

---

### 12. `tests/admin.spec.js` *(recommended extension, C-16 negative)*

**Analog:** the same file's pill test, `300-330` (already quoted above). C-16 adds a **negative** to the existing loop: on `/admin/digest` and `/admin/materials/sql-dashboards-for-audit-reporting`, the three section pills must have no `aria-current` and no `bg-primary-solid`.

Copy the locator from `tests/admin.spec.js:108-115` (`shellNav`) and reuse `gotoAsRole(page, "admin", target)` (`tests/admin.spec.js:23-35`) — the admin identity helper already exists and sets `window.__DIGEST_MOCK_ME_ROLE__`, which is what makes the «Админ» pill render at all.

---

## Shared Patterns

### Token-only CSS, with the decision id in the comment

**Source:** `web/src/index.css:4-6`, `34-44`, `63-66`, `79-87`.
**Apply to:** the `scroll-padding-top` rule and the mobile token override.
Every non-obvious value in `index.css` carries its *reason* (an ADR, a measurement, or a decision id). The new comments must say **NAV-01 / D-01…D-03** for the offset and record the measured `196.6 / 122.6 → 200px` provenance for the mobile token. No hex colours, no new `--space-*`.

### `linkClass({ isActive })` is the only pill style

**Source:** `web/src/components/AppShell.jsx:11-15`.
**Apply to:** all three converted pills.
Call it with a computed boolean; never string-concatenate variants, never add a class conditionally inline. C-18 is a token-set comparison, so a "small extra class" is a failure.

### `aria-current="true"` for a state-claimed section, `"page"` for its own route

**Source:** `web/src/components/AppShell.jsx:93-104` (the `WR-02` comment at `95-98` is the written rationale the phase reuses).
**Apply to:** «Выпуск», «Архив», «База».
`undefined` — not `null`, not `"false"` — is how "no attribute" is expressed (React drops `undefined`). The admin pill is the only precedent, and C-08 asserts the negative site's attribute is `null` via `getAttribute`.

### Required prop, no default (the TypeScript substitute)

**Source:** `web/src/components/MaterialListRow.jsx:3-6` (JSDoc contract) + `web/src/pages/IssuePage.jsx:97-100` (`@param {{ isCurrent?: boolean }}`).
**Apply to:** `IssueToc`, `MaterialListRow`.
The repo is plain JSX with no prop-types package; the JSDoc block is the contract. Declare `section` as required and give it **no** default, and record the union in the JSDoc, e.g.:

```jsx
/**
 * @param {{ items: Array<object>, section: 'archive' | 'issue' }} props
 * `section` is required: this list renders inside both the current issue ('issue')
 * and an archived one ('archive'), so it cannot infer the marker (D-08/D-09).
 */
```

### Single read point / no duplicated literals

**Source:** `web/src/components/AppShell.jsx:36-39` (`IN-04`, "the prefix is the single source of truth") + `web/src/components/AdminLayout.jsx:28` ("Hard-coded whitelist (T-22-02)").
**Apply to:** `state?.section` handling.
The three literals are compared in `AppShell` **only**. Producers emit their own literal without comparing (`ArchivePage` = `'archive'`, `KnowledgePage` = `'base'`, `IssuePage` = `isCurrent ? 'issue' : 'archive'`); `MaterialPage` re-emits whatever it received unexamined. C-17's written artefact is a grep-level claim: one file reads `state?.section`.

### Locator + assertion conventions for chrome

**Source:** `tests/admin.spec.js:108-115`, `300-330`; `tests/web-app.spec.js:173-198`.
**Apply to:** every C-08…C-20 test.
`getByRole("navigation", { name: /основная навигация/i })` → `getByRole("link", { name: /^Архив$/ })`; attributes via `toHaveAttribute`; classes via `(await link.getAttribute("class")).split(/\s+/)`; no new `data-testid` on the pills (UI-SPEC matrix note); web-first assertions only.

### Measured geometry, never literals

**Source:** `tests/admin.spec.js:339` (`await page.evaluate(() => document.fonts.ready)`) + `26-RESEARCH.md` §6 gate snippet.
**Apply to:** C-01…C-06.
Read `header.getBoundingClientRect().height` live, read `getComputedStyle(document.documentElement).scrollPaddingTop` with `Number.parseFloat(...) || 0`, derive the reachability gate from `scrollHeight − innerHeight`. Pin the band `[1, 32]` — never `7.4`, `72.6`, `73`, or `80`.

### Comments carry the decision id and the failure they prevent

**Source:** every touched file already does this (`AppShell.jsx:36-38`, `95-98`; `index.css:63-66`; `mock.js:251-255`; `AdminLayout.jsx:7-9,27-33`).
**Apply to:** all production edits. One short block per non-obvious line, naming the decision (`D-08`) or the regression (`WR-02`). This is the repo's substitute for tests-as-documentation in chrome code, and the planner should treat it as a task requirement, not a nicety.

---

## No Analog Found

| File / pattern | Role | Data Flow | Reason | Use instead |
|---|---|---|---|---|
| React Router `state={{ section }}` on `<Link>` (applies to `ArchivePage`, `IssueToc`, `MaterialListRow`, `MaterialPage`) | component / page | router-state propagation | `rg 'state=\{' web/src` finds only `data-state` and component `state` props — **there is no `Link state` precedent in the codebase**; `useLocation()` is destructured only as `pathname` (`AppShell.jsx:35`, `AdminLayout.jsx:25`, `RequireAuth.jsx:11`, `AnalyticsPageViews.jsx:7`) | `26-RESEARCH.md` §4 (measured `history.state.usr` behaviour) and §5 (the exact prop-threading table). Copy the *style* from the admin pill (`to` → attribute/state → `className`), not a semantic precedent that does not exist |
| A static gate that proves a CSS declaration lives in a specific at-rule wrapper | test | source scan | `tests/unit/helpers/cssRules.js:49-56` flattens `@layer`/`@media` wrappers by design, so no existing consumer distinguishes them | raw `read()` + regex on `web/src/index.css` (precedent: the `has no literal colours` regex at `test_concept2_canon.js:154-157`) |

No other file in scope lacks an analog.

---

## Metadata

**Analog search scope:** `web/src/components/`, `web/src/pages/`, `web/src/data/`, `web/src/index.css`, `tests/`, `tests/unit/`, `tests/unit/helpers/`, `playwright.config.js`, `scripts/run-unit-js.cjs`.
**Files read for extraction:** `web/src/index.css`, `AppShell.jsx`, `IssueToc.jsx`, `MaterialListRow.jsx`, `AdminLayout.jsx`, `RequireAuth.jsx`, `ArchivePage.jsx`, `IssuePage.jsx`, `KnowledgePage.jsx` (hit-list region), `MaterialPage.jsx` (head / derived / related), `web/src/data/mock.js` (materials, razbory, archive seeds), `tests/web-app.spec.js` (head, TOC, nav, overflow), `tests/admin.spec.js` (helpers, pill test), `tests/razbory.spec.js` (chronology pin), `tests/unit/test_concept2_canon.js`, `tests/unit/test_semantic_token_coverage.js`, `tests/unit/helpers/cssRules.js`, `playwright.config.js`, `scripts/run-unit-js.cjs`.
**Tracked-source gate:** `git ls-files --` confirmed all 13 analog paths are tracked (no gitignored mirror used).
**Pattern extraction date:** 2026-10-22.
