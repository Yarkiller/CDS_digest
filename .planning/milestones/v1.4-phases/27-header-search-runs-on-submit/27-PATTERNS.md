# Phase 27: Header search runs on submit - Pattern Map

**Mapped:** 2026-10-22
**Files analyzed:** 6 (1 primary production, 1 payload-only, 1 pinned baseline, 3 test files)
**Analogs found:** 5 strong / 6 (the page-level *ref-guarded fetch effect* has **no** analog in the repo — see § "No Analog Found")

Scope confirmed against `27-RESEARCH.md` § "Recommended Project Structure (only files this phase touches)". **No file outside this table is touched. `web/src/main.jsx` is NOT touched** (X-1 is a bare `window` global written from the page — the harness-object wiring in `main.jsx` is a *different* precedent, see § Shared Patterns → Instrument exposure).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `web/src/pages/KnowledgePage.jsx` (**modify**) | page component / client state machine | request-response + in-memory cache | `web/src/pages/IssuePage.jsx` (page fetch effect keyed on a route param) + `web/src/pages/KnowledgePage.jsx` itself (`runSearch` is already the whole execution path) | role-match (the ref guard half has **no** analog) |
| `web/src/components/SearchPill.jsx` (**modify, payload only**) | component | event-driven (navigation payload) | `web/src/components/SearchPill.jsx:21-24` (its own `onSubmit`) + `web/src/components/MaterialListRow.jsx:15-18` (producer of `state`) | exact (in-place extension) |
| `tests/knowledge.spec.js` (**modify: +KNOW-05 block + X-1/X-2 helpers**) | test (Playwright e2e, CommonJS) | request-response journey | `tests/knowledge.spec.js` (existing KNOW-01…04) + `tests/web-app.spec.js:322-341` (header pill pin) | exact |
| `tests/unit/test_knowledge_api_snapshot.js` (**NEW**) | test (static gate, `node:test`) | file I/O (raw bytes → sha256) | `tests/unit/test_design_typography.js:17-27` (node:test + `readFileSync` + `path`) | role-match (no hash pin exists in the repo) |
| `tests/unit/test_knowledge_search_single_call_site.js` (**NEW**) | test (static gate, `node:test`) | file I/O (source text scan) | `tests/unit/test_section_context_gates.js:17-46` (recursive `web/src` walker + occurrence counting) | exact |
| `web/src/services/knowledgeApi.js` (**BYTE-IDENTICAL — pin, not an edit**) | service / adapter | request-response | its own frozen self | pin |

---

## Pattern Assignments

### 1. `web/src/pages/KnowledgePage.jsx` (page component, request-response + cache)

**Analogs:** `web/src/pages/IssuePage.jsx:113-141` (effect keyed on a **route param**, with cleanup) and the same file's own `runSearch` (`KnowledgePage.jsx:70-121`), which must be **reused, never duplicated**.

#### What the file looks like today (reuse everything below; do not rewrite it)

Imports + module constants + the only existing effect (toast timer) — `KnowledgePage.jsx:1-27, 45-68`:

```jsx
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  DEFAULT_SEARCH_LIMIT,
  KnowledgeApiError,
  clearFailNextKnowledgeSearch,
  searchKnowledge,
  validateKnowledgeQuery,
} from '../services/knowledgeApi.js'
import MaterialListRow from '../components/MaterialListRow.jsx'
import ActionButton from '../components/ActionButton.jsx'
import ErrorPanel from '../components/ErrorPanel.jsx'
import { ANALYTICS_GOALS, trackGoal } from '../services/analyticsRuntime.js'

/** Topic hint chips fill the query only — do not execute search (D-60). */
const HINT_CHIPS = ['RAG', 'SQL', 'качество данных', 'pgvector']
```

```jsx
export default function KnowledgePage() {
  const [searchParams] = useSearchParams()
  const [query, setQuery] = useState(() => searchParams.get('q') ?? '')
  /** 'all' omits role; analyst | ds are the only filters sent (D-62). */
  const [role, setRole] = useState('all')
  /** null = pre-search landing; string = last successful/attempted submitted q */
  const [activeQuery, setActiveQuery] = useState(null)
  const [items, setItems] = useState([])
  const [hasMore, setHasMore] = useState(false)
  const [nextOffset, setNextOffset] = useState(0)
  const [searching, setSearching] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)
  /** Inline validation — blank/overlong; never hits knowledgeApi (KNOW-01). */
  const [inlineError, setInlineError] = useState(null)
  const [toast, setToast] = useState('')

  useEffect(() => {
    if (!toast) return undefined
    const timer = window.setTimeout(() => setToast(''), FILTER_TOAST_MS)
    return () => window.clearTimeout(timer)
  }, [toast])
```

> **Only import change needed:** add `useRef` and `useLocation` (`react` / `react-router-dom`), and take the setter from `useSearchParams`. `knowledgeApi.js` already exports everything the effect needs — no new service import, no new file.

#### Core pattern to extend — `runSearch` (the single execution path) `:70-121`

```jsx
  async function runSearch(q, { offset = 0, append = false, role: roleValue = role } = {}) {
    if (append) {
      setLoadingMore(true)
    } else {
      setSearching(true)
      setError(null)
      setInlineError(null)
    }

    let resetInvalidRole = false
    try {
      const dto = await searchKnowledge({
        q,
        role: roleValue === 'all' ? null : roleValue,
        limit: DEFAULT_SEARCH_LIMIT,
        offset,
      })
      setActiveQuery(q)
      setItems((prev) => (append ? [...prev, ...dto.items] : dto.items))
      setHasMore(Boolean(dto.has_more))
      setNextOffset(offset + (dto.items?.length ?? 0))
      setError(null)
      if (!append && q) {
        // Privacy: send only the role filter, never the raw user query, to Metrika.
        trackGoal(ANALYTICS_GOALS.search, { role: roleValue })
      }
    } catch (err) {
      const failure = searchFailureState(err, { roleValue, append, q })
      if (failure.invalidRole) {
        // Tampered role: toast and fall back to «Все» without clearing q (D-62).
        resetInvalidRole = true
        setError(null)
      } else {
        setError(failure.error)
        if (failure.clearItems) {
          setItems([])
          setHasMore(false)
          setActiveQuery(failure.activeQuery)
        }
      }
    } finally {
      setSearching(false)
      setLoadingMore(false)
    }

    if (resetInvalidRole) {
      setRole('all')
      setToast('Фильтр недоступен')
      void runSearch(q, { offset: 0, append: false, role: 'all' })
    }
  }
```

**How to use it (do not fork it):**
- X-1 counter: **first statement inside the `try`**, i.e. directly before `const dto = await searchKnowledge({` (`:81`) — this counts throws too (C-23 «Повторить»).
- Cache write: in the success branch next to `setNextOffset(...)` (`:90`), **not** inside a `setItems` updater (StrictMode double-invokes updaters — RESEARCH Key Finding 4).
- Cache delete: in the non-append `catch` branch (`:98-106`).
- `role` must be passed explicitly (`role: forced ? 'all' : roleRef.current`) so a stale closure cannot leak the wrong role.

#### Existing handler to extend — `handleSubmit` `:123-135` (D-02: write `?q` via `replace`)

```jsx
  function handleSubmit(event) {
    event.preventDefault()
    const validation = validateKnowledgeQuery(query)
    if (!validation.ok) {
      // Inline copy locked to UI-SPEC (must appear in this source for honesty/verify).
      setInlineError(
        validation.code === 'QUERY_TOO_LONG' ? 'Сократите запрос' : 'Введите запрос',
      )
      setError(null)
      // Do not call searchKnowledge (KNOW-01 / D-57).
      return
    }
    setInlineError(null)
    void runSearch(validation.q, { offset: 0, append: false, role })
  }
```

Note: the two literals on `:128` are why the static call-site gate must strip comments **and** why the effect must take its overlong copy from `validation.message`, not from a third literal (UI-SPEC § Copywriting Contract).

#### Two derived switches to rewrite (exact lines) `:174-179` and `:345-352`

```jsx
  const preSearch = activeQuery === null && !error
  const showZeroHit =
    activeQuery !== null && !searching && !error && items.length === 0
```

```jsx
      {activeQuery !== null && !error ? (
        <p className="mb-4 text-xs text-text-secondary" aria-live="polite">
          {knowledgeResultSummary({ searching, items, hasMore })}
        </p>
      ) : null}
```

- Landing: `activeQuery === null && !error` → **`qUrl === '' && error === null`**.
- R-1 live-region gate: `activeQuery !== null && !error` → **`searching || (activeQuery !== null && !error)`** — node, classes and CSS stay byte-identical (only the `{…}` condition changes).

`qUrl` must be read **synchronously during render**, never seeded into state:

```jsx
const [searchParams, setSearchParams] = useSearchParams()
const qUrl = (searchParams.get('q') ?? '').trim()
```

The existing `useState(() => searchParams.get('q') ?? '')` seed for the field gains a mirror (D-10): the field must follow `qUrl` when it changes (C-22), while the `toHaveValue("RAG")` pin (`tests/web-app.spec.js:341`) stays green.

#### The fetch-effect idiom to copy from `IssuePage.jsx:113-141` (page fetch keyed on a route param)

```jsx
  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    setNotFound(false)

    const load = isCurrent
      ? fetchCurrentIssue()
      : fetchIssueByNumber(numberParam)

    load
      .then((dto) => {
        if (cancelled) return
        setIssue(dto)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof ContentApiError && err.code === 'NOT_FOUND') {
          setNotFound(true)
          setStatus('ready')
          return
        }
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [isCurrent, numberParam, loadKey])
```

Copy from it: the effect **depends on the route param**, resets its own state at the top, and uses a `cancelled` closure flag to swallow late settles after unmount/param change.

**Copy `cancelled` only as a late-settle guard — it is NOT the double-fire guard.** `cancelled` cannot prevent StrictMode's `setup → cleanup → setup` from issuing two requests: both setups run synchronously before any settle. The anti-duplicate mechanism must be the **ref written before the first `await`** (D-03), which does not exist in this repo — see § "No Analog Found".

Related: `MaterialPage.jsx:82-105` shows the same `cancelled` idiom plus a `loadKey` reload counter; `ArchivePage.jsx:17-33` is the minimal version of it.

#### The intentional-narrow-deps precedent — `VotingPage.jsx:147-180`

```jsx
  const reloadBallot = useCallback(() => {
    clearFailNextBallotFetch()
    setError(null)
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoadState('loading')
    fetchBallot()
      .then((snapshot) => {
        if (cancelled) return
        applySnapshot(snapshot, snapshotSetters)
        setLoadState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        const fetchError =
          err instanceof BallotFetchError
            ? err
            : new BallotFetchError('Не удалось загрузить голосование.', { code: 'UNKNOWN' })
        setError({
          title: 'Ошибка загрузки',
          message: fetchError.message,
          code: fetchError.code,
          retryable: fetchError.retryable,
        })
        setLoadState('error')
      })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload via loadKey only
  }, [loadKey])
```

- Precedent for **deliberately narrowing the deps array** and saying why in a comment.
- `web/.oxlintrc.json` enables only `react/rules-of-hooks` — `react-hooks/exhaustive-deps` is off — so `[qUrl, submitId]` needs **no** disable comment (RESEARCH hazard 12). Do not add one.

---

### 2. `web/src/components/SearchPill.jsx` (component, event-driven navigation payload)

**Analog:** the file itself — `SearchPill.jsx:21-24` (D-05 adds `state`, nothing else):

```jsx
  function onSubmit(event) {
    event.preventDefault()
    const q = query.trim()
    navigate(q ? `/knowledge?q=${encodeURIComponent(q)}` : '/knowledge')
  }
```

**Navigation-state producer idiom** (`MaterialListRow.jsx:15-18`, same channel D-05 uses):

```jsx
    <Link
      to={`/materials/${slug}`}
      state={{ section }}
```

Contract for this file (UI-SPEC § "Поверхности фазы"): **payload only**. No knowledge of `searchKnowledge`, no validation copy, no spinner/`disabled`/`data-state`, `min-h-12`, `rounded-full`, `px-4 py-3`, `placeholder`, `sr-only` label and the `Ctrl+K` effect (`:10-19`) all stay byte-identical. Empty/whitespace submit keeps `navigate('/knowledge')` (D-08) — **zero** requests, no marker.

---

### 3. `tests/knowledge.spec.js` (Playwright e2e, CommonJS — append, do not fork)

**Analog:** the file itself (`tests/knowledge.spec.js:1-63`, quoted in full below) + the header-pill pin in `tests/web-app.spec.js:322-341`.

Style contract (copy it exactly):

```js
const { expect, test } = require("@playwright/test");

/**
 * Phase 4 knowledge honesty gate (KNOW-01…04) under VITE_USE_MOCKS.
 * No tag/format/topic selects — role chips only (D-62…D-65).
 */
test.describe("knowledge honesty (KNOW-01…04)", () => {
  test("Submit and Enter run search; whitespace shows Введите запрос without hits", async ({
    page,
  }) => {
    await page.goto("/knowledge");

    await expect(page.locator("select")).toHaveCount(0);
    await expect(page.getByLabel(/^(теги|формат|тема)$/i)).toHaveCount(0);

    const search = page.getByRole("searchbox", { name: /поиск по базе знаний/i });
    await search.fill("RAG");
    await page.getByRole("button", { name: "Найти", exact: true }).click();
    await expect(page.getByRole("link", { name: /building production rag systems/i })).toBeVisible();
    // KNOW-01 / D-59: never render numeric score badges on hits.
    await expect(page.getByText(/\bscore\b|\bрейтинг\b|\d+\.\d{2,}/i)).toHaveCount(0);
```

Facts to keep from this file:
- CommonJS `require` (root `package.json` has no `"type": "module"`), double-quoted strings, `test.describe` wrapper, no `beforeEach`.
- Page field is addressed by **name**, not by `#kb-search`: `getByRole("searchbox", { name: /поиск по базе знаний/i })`. The header field is `name: /поиск digest cds/i` (`SearchPill.jsx:35-36`). On `/knowledge` **both exist** → a bare `getByRole("searchbox")` is a strict-mode violation.
- Hit rows are links: `getByRole("link", { name: /…/i })`; there is **no** `kb-result-row` testid (`KnowledgePage.jsx:383-387` renders `MaterialListRow`, whose root is a `<Link>` — `MaterialListRow.jsx:14-19`).
- Existing KNOW-01…04 must stay green untouched (regression gate).

**Header-path pin to imitate** (`tests/web-app.spec.js:322-341`):

```js
  test("keeps header search as an enlarged inline field without a modal", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("dialog")).toHaveCount(0);
    const headerSearch = page.getByRole("searchbox", { name: /поиск digest cds/i });
    await expect(headerSearch).toBeVisible();

    const box = await headerSearch.boundingBox();
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
    expect(box?.width ?? 0).toBeGreaterThanOrEqual(240);

    await page.keyboard.press("Control+k");
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(headerSearch).toBeFocused();

    await headerSearch.fill("RAG");
    await headerSearch.press("Enter");
    await expect(page).toHaveURL(/\/knowledge/);
    await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("RAG");
  });
```

Leave this test **untouched** (C-22 pin). New cases go into `tests/knowledge.spec.js` — do **not** create a sibling spec: `playwright.config.js:71` is `testMatch: /(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/` (unanchored substring), so `knowledge-submit.spec.js` would silently never run (research Key Finding 7 / the 25-01 trap).

---

### 4. `tests/unit/test_knowledge_api_snapshot.js` (NEW static gate — sha256 pin)

**Analog (structure):** `tests/unit/test_design_typography.js:17-27`

```js
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const { parseRules } = require('./helpers/cssRules')

const ROOT = path.join(__dirname, '..', '..')
const readCss = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')
```

Copy from it: single-quoted CommonJS, `node:assert/strict` + `node:test`, `ROOT = path.join(__dirname, '..', '..')`, a header comment that states **why** the gate exists and a `Run: node --test …` line. Discovery needs no config: `scripts/run-unit-js.cjs:12-18` flat-scans `tests/unit/*.js`:

```js
const unitDir = join(__dirname, '..', 'tests', 'unit')
const files = readdirSync(unitDir)
  .filter((name) => name.endsWith('.js'))
  .sort()
  .map((name) => join(unitDir, name))
```

**No hash-pin precedent exists** in `tests/unit` (verified: no `createHash` anywhere in the repo's JS tests). Two things the pin must do that the analog does not:

1. **Capture the digest in Wave 0, before any edit** — measured on the current, unmodified file (LF endings, 6283 bytes):
   - raw `sha256(readFileSync(path))` = `bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f`
   - LF-normalised `sha256(crlf→lf)` = `bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f` (**identical today**, file has 0 CRLF pairs)
   - A hardcoded digest written *after* the fact proves nothing; re-run and re-verify at Wave 0 (that file is `git status`-clean now).
2. **Normalise line endings before hashing** (`readFileSync(p,'utf8').replace(/\r\n/g,'\n')`). A raw-byte digest breaks on a CRLF checkout (Windows `core.autocrlf`), producing a false RED for the wrong reason. With normalisation the digest is checkout-independent *and* still fails on any real edit.

Failure message must name the contract: `C-24: web/src/services/knowledgeApi.js must stay byte-identical — 27-CONTEXT.md § Out of scope`.

---

### 5. `tests/unit/test_knowledge_search_single_call_site.js` (NEW static gate — one call site)

**Analog (exact role match):** `tests/unit/test_section_context_gates.js:17-46` — a `node:test` gate that reads raw source under `web/src` and counts occurrences:

```js
const assert = require('node:assert/strict')
const { readdirSync, readFileSync } = require('node:fs')
const path = require('node:path')
const { describe, it } = require('node:test')

const ROOT = path.join(__dirname, '..', '..')

const read = (relativePath) => readFileSync(path.join(ROOT, relativePath), 'utf8')

/** Every .js/.jsx/.css source under web/src, as `{ relative, source }` pairs. */
function sources() {
  return readdirSync(path.join(ROOT, 'web/src'), { recursive: true })
    .filter((entry) => /\.(js|jsx|css)$/.test(entry))
    .map((entry) => {
      const relative = path.join('web/src', entry).split(path.sep).join('/')
      return { relative, source: read(relative) }
    })
}
```

And the "exactly one mechanism, named file, explicit anti-vacuum" assertion shape (`:47-66`):

```js
  it('declares exactly one scroll offset in web/src', () => {
    const found = sources()
      .map(({ relative, source }) => ({ relative, hits: count(source, 'scroll-padding-top:') }))
      .filter((entry) => entry.hits > 0)
    const total = found.reduce((sum, entry) => sum + entry.hits, 0)

    assert.equal(
      total,
      1,
      `NAV-01: expected exactly one scroll-padding-top in web/src, found ${total} — объявите его в web/src/index.css`,
    )
```

Copy from it: recursive `readdirSync(..., { recursive: true })` walker, `relative` path normalised with `split(path.sep).join('/')` (Windows), `count(text, needle)` non-overlapping counter, assertion messages that state the contract ID and the fix.

**Adaptations this gate needs (from `27-RESEARCH.md` Key Finding 6):**
- Walk `web/src` for `.js|.jsx|.mjs`, skip `node_modules` implicitly (it is outside `web/src`).
- Strip `/* … */` blocks and **line-leading** `//` only — a naive `//` strip would eat `https://` in strings.
- Assert: (a) exactly one file imports the identifier `searchKnowledge`; (b) exactly one non-comment `searchKnowledge(` occurrence (today only `:81`; the second textual hit is the comment `KnowledgePage.jsx:131`); (c) `web/src/services/knowledgeApi.js` contains neither `__DIGEST_KNOWLEDGE_SEARCH_COUNT__` nor a limiter — this is the half that keeps X-1 out of the frozen adapter.
- Anti-vacuum: assert a plausible file count (`> 20`) like RESEARCH's `walker found only N files — path is wrong`, so a broken path cannot pass at `0 === 0`.

---

### 6. `web/src/services/knowledgeApi.js` (BYTE-IDENTICAL — a pin, not an edit)

**Analog:** its own current bytes. Nothing to copy; the only action is to **not touch it**.

The three things the phase relies on, verbatim:

`knowledgeApi.js:19-30` — the single validation path (D-09; `validation.message` is the only overlong copy the effect may use):

```js
export function validateKnowledgeQuery(raw) {
  const trimmed = String(raw ?? '').trim()
  if (!trimmed) {
    return { ok: false, code: 'EMPTY_QUERY', message: 'Введите запрос' }
  }
  if ([...trimmed].length > MAX_QUERY_CODE_POINTS) {
    return { ok: false, code: 'QUERY_TOO_LONG', message: 'Сократите запрос' }
  }
  return { ok: true, q: trimmed }
}
```

`knowledgeApi.js:110-125` — the boundary X-1 must be counted **outside** of, and the reason `page.route` is dead:

```js
export async function searchKnowledge(
  { q, role = null, limit = DEFAULT_SEARCH_LIMIT, offset = 0 } = {},
  accessToken = null,
) {
  if (consumeFailNext()) {
    throw new KnowledgeApiError('Не удалось выполнить поиск. Проверьте сеть.', {
      code: 'NETWORK',
      retryable: true,
    })
  }

  const { isMocksEnabled } = await import('./authEnv.js')
  if (isMocksEnabled()) {
    await delay(80)
    return mockSearchKnowledge({ q, role, limit, offset }, materials)
  }
```

`knowledgeApi.js:41, 55-64` — module-scope mutable harness flag; the `window` guard is the idiom X-1 should copy:

```js
let failNextSearch = false
```

```js
export function clearFailNextKnowledgeSearch() {
  failNextSearch = false
  if (typeof window !== 'undefined') {
    window.__DIGEST_FAIL_NEXT_KNOWLEDGE__ = false
  }
}
```

**Hazards pinned by this file:** `consumeFailNext()` never clears `window.__DIGEST_FAIL_NEXT_KNOWLEDGE__` on consumption (only `clearFailNextKnowledgeSearch()` does) — an error test that sets the flag must clear it before asserting recovery. `DEFAULT_SEARCH_LIMIT = 10` > catalog size 8 ⇒ `has_more` is never true in mocks ⇒ «Показать ещё» is unreachable (C-12 descope).

---

## Shared Patterns

### Instrument exposure (X-1) — copy the *guard*, not the *wrapper*

Two precedents exist; the UI-SPEC chooses the first one's shape, not the second:

1. **Bare global, page-owned** (UI-SPEC X-1, follow literally): `window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__`, incremented in `KnowledgePage.jsx`, no `main.jsx` change, no harness object. Guard with `typeof window === 'undefined'` exactly like `knowledgeApi.js:56,61`.
2. **`main.jsx` harness object** (`main.jsx:60-107`) — this is how *service-level* test arms are exposed:

```js
window.__DIGEST_INGESTION_SCHEDULE_HARNESS__ = {
  armFailNextLoad: armFailNextScheduleLoad,
  armFailNextSave: armFailNextScheduleSave,
  resetIngestionScheduleHarness,
  resetIngestionScheduleMockStore,
  readIngestionScheduleMock,
}
```

**Do not add `KnowledgePage`'s counter here.** `main.jsx` is outside the phase's file set; the counter is written by the page itself, so no wiring is needed.

### Harness counter consumed from Playwright — real precedent

- **Read accessor:** `web/src/services/ingestScheduleApi.js:138-141`:

```js
/** Read mock store (Playwright PATCH-count assertions). */
export function readIngestionScheduleMock() {
  return readMockStore()
}
```

- **Reset + read + assert:** `tests/admin.spec.js:2207-2215` and `:2271-2295`:

```js
async function resetIngestionScheduleMock(page) {
  await page.waitForFunction(() => Boolean(window.__DIGEST_INGESTION_SCHEDULE_HARNESS__));
  await page.evaluate(() => {
    window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.resetIngestionScheduleMockStore();
    window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.resetIngestionScheduleHarness();
  });
  await page.reload();
  await expect(page.getByTestId("ingestion-schedule-section")).toBeVisible();
}
```

```js
    const before = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );

    const time = page.getByTestId("ingestion-schedule-time");
    await time.fill("07:30");

    const mid = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );
    expect(mid).toBe(before);

    await time.blur();
    await expect(page.getByTestId("ingestion-schedule-status")).toContainText("Сохранено");
    await expect(time).toHaveValue("07:30");

    const after = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock(),
    );
    expect(after.patchCount).toBe(before + 1);
```

Copy: `waitForFunction` before reading (the global must exist), **read a baseline**, act, **assert a delta** (`before` / `mid` / `after`), and a reset helper called at test start.

> **Dead citation to avoid:** `27-CONTEXT.md` cites `tests/admin-chrome.spec.js:2277` — that file is **868 lines**; the `patchCount` precedent lives in **`tests/admin.spec.js:2272-2295`** (reset helper at `:2207`). Do not open `admin-chrome.spec.js:2277`.

Difference from the precedent to encode in the plan: `patchCount` lives in `sessionStorage` (persists across reload); X-1 lives in `window` and is **zeroed by `page.addInitScript` on every new document** — that is exactly what makes C-11 (`reload ⇒ 1`) and C-09 (`Back ⇒ +0`, SPA pop keeps the document) distinguishable.

### Playwright `addInitScript` seeding (the repo's only per-test state-seeding idiom)

`tests/admin.spec.js:23-35` shows the pattern with arguments:

```js
async function gotoAsRole(page, role, path = "/", extraInit) {
  await page.addInitScript(
    ({ r, extra }) => {
      window.__DIGEST_MOCK_ME_ROLE__ = r;
      if (extra && typeof extra === "object") {
        for (const [key, value] of Object.entries(extra)) {
          window[key] = value;
        }
      }
    },
    { r: role, extra: extraInit ?? null },
  );
  await page.goto(path);
```

Copy the shape for `installKnowledgeCounter(page)` / `installAffordanceCollector(page)` (arguments object, `page.addInitScript`, then `goto`). Note the difference: these two helpers must be installed **before the first navigation**, and the counter helper must also expose a synchronous reset (`window.__resetKnowledgeSearchCount`) because an init script does not re-run on an SPA pop.

### SPA-boundary context (why the cache is module-scope)

`web/src/main.jsx:109-112` — StrictMode is real, in dev and in the Playwright dev server:

```jsx
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

`web/src/App.jsx:51-53` — `/knowledge` and `/materials/:id` are **siblings**, so a row click unmounts `KnowledgePage`:

```jsx
          { path: 'knowledge', element: <KnowledgePage /> },
          { path: 'materials/:id', element: <MaterialPage /> },
          { path: 'razbory', element: <RazboryListPage /> },
```

Consequence: component state and refs die on a material click ⇒ the cache must be **module scope** (D-04), and any test URL must be concrete (`/materials/rag-systems`), never the `:id`/`:slug` literal.

### Module-scope mutable state (the only cache-shaped precedent in `web/src`)

There is **no module-scope `Map` cache** anywhere in `web/src` (all six `new Map(` sites are local/defaults: `adminPreviewComposition.js:30`, `markdownToc.js:51`, `adminApi.js:549,605,618`, `AdminDigestPage.jsx:237`). The precedents to copy for *scope* are module-scope `let`, not `Map` at module scope:

`web/src/pages/AdminDigestPage.jsx:29-33` — page-level module sequence counter:

```js
let issueBlockSeq = 0
function nextIssueBlockId(prefix) {
  issueBlockSeq += 1
  return `${prefix}-${issueBlockSeq}`
}
```

`web/src/services/knowledgeApi.js:41` — module flag with reset function (same file family, closest style):

```js
let failNextSearch = false
```

`web/src/utils/markdownToc.js:50-52` — the `Map` usage *shape* (key → value, membership by `has`), local scope only:

```js
  const headings = []
  const seen = new Map()
```

⇒ For `searchSnapshots` / `lastRoleForQuery`: follow RESEARCH "Pattern 2" (module-scope `Map` + `snapshotKey(role, q)` with `\u0000` separator + FIFO eviction at 20). There is no repo file to copy verbatim; the *style* comes from Pattern 2 and the *scope justification* from the two `let` precedents above.

---

## No Analog Found

| File (part of) | Role | Data Flow | Reason / what to use instead |
|----------------|------|-----------|-------------------------------|
| `KnowledgePage.jsx` — the ref-guarded, URL-keyed fetch effect (`lastHandledQueryRef`, `consumedSubmitIdRef`) | page component hook | request-response (trigger dedupe) | **No `useRef` exists anywhere in `web/src` except `SearchPill.jsx:6,16` (an input focus target).** No page-level fetch is guarded by a ref, and no effect is keyed on a URL search param — every page fetch is keyed on `loadKey` and guarded by a `cancelled` closure flag (`IssuePage.jsx:113-141`, `MaterialPage.jsx:82+`, `ArchivePage.jsx:17-33`, `VotingPage.jsx:153-180`), which cannot prevent StrictMode's double setup. → Use `27-RESEARCH.md` § "Pattern 1" shape verbatim; borrow only the *state machine* (`IssuePage`) and the *narrow-deps comment* (`VotingPage.jsx:180`). |
| `KnowledgePage.jsx` — module-scope snapshot cache with a role side-map | cache (in-memory) | CRUD on a promise-less map | No module-scope `Map` exists in `web/src`; the closest scope precedent is module-scope `let` (`AdminDigestPage.jsx:29`, `knowledgeApi.js:41`). The storage-backed lookalike (`ingestScheduleApi.js:107-141`) must **not** be copied: it is `sessionStorage`, which D-04 forbids. → Use `27-RESEARCH.md` § "Pattern 2". |
| `KnowledgePage.jsx` — `submitId` strip via `setSearchParams(..., { replace: true, state: null })` | router side effect | event-driven (one-shot marker) | No `setSearchParams` call exists in the repo — all four `useSearchParams` uses are read-only (`KnowledgePage.jsx:48`, `VotingPage.jsx:117`, `LoginPage.jsx:26`, `RegisterPage.jsx:17`). → Use `27-RESEARCH.md` § "Pattern 3" + the verified `setSearchParams` implementation (`chunk-YRTY65LJ.js:731-740`, quoted in Key Finding 2). |
| `tests/unit/test_knowledge_api_snapshot.js` — the sha256 literal itself | static pin | file I/O | No hash pin exists in `tests/unit` (no `createHash` anywhere). → Structure from `test_design_typography.js:17-27`; digest captured in Wave 0 (values in § 4 above); normalise CRLF before hashing. |

---

## Metadata

**Analog search scope:** `web/src/pages`, `web/src/components`, `web/src/services`, `web/src/hooks`, `web/src/utils`, `tests/`, `tests/unit/`, `scripts/`, `playwright.config.js`, `package.json`.
**Files scanned:** 22 read in full/targeted (`KnowledgePage.jsx`, `SearchPill.jsx`, `App.jsx`, `main.jsx`, `AppShell.jsx`, `MaterialListRow.jsx`, `IssueToc.jsx`, `IssuePage.jsx`, `MaterialPage.jsx`, `VotingPage.jsx`, `ArchivePage.jsx`, `AdminDigestPage.jsx`, `knowledgeApi.js`, `ingestScheduleApi.js`, `markdownToc.js`, `useUnsavedChangesGuard.js`, `tests/knowledge.spec.js`, `tests/web-app.spec.js`, `tests/admin.spec.js`, `tests/admin-chrome.spec.js` (length check), `tests/unit/test_design_typography.js`, `tests/unit/test_section_context_gates.js`, `tests/unit/test_knowledge_api.js`, `scripts/run-unit-js.cjs`, `playwright.config.js`, `package.json`).
**Pattern extraction date:** 2026-10-22.
**Repo facts measured during mapping:** `web/src/services/knowledgeApi.js` is `git status`-clean, 6283 bytes, 0 CRLF; sha256 (raw and LF-normalised) `bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f`; `tests/admin-chrome.spec.js` is 868 lines (the `patchCount` precedent is in `tests/admin.spec.js`).
