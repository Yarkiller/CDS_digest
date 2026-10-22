# Phase 27: Header search runs on submit - Research

**Researched:** 2026-10-22
**Domain:** Frontend only — React 19.2.8 + `react-router-dom` 7.18.3 (data router) + Tailwind CSS v4.3.3 + Playwright 1.62.1 + `node:test` static gates
**Confidence:** HIGH (effect shape, instruments, runners, pitfalls), MEDIUM on one contract item (C-12 — see Key Finding 8)

## Summary

The phase is a single structural change with four instruments around it: `KnowledgePage` gains its **first data-fetching effect**, keyed on `?q`, guarded by a ref holding the last *normalised* query it executed or restored; `SearchPill` keeps navigating and adds a one-shot `submitId` in `location.state`; a module-scope `Map` in `KnowledgePage.jsx` remembers the last snapshot per `(role, q)` so Back/Forward and the return from a material restore results with **zero** requests; and exactly one production-level counter (`window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__`) plus one test-side `MutationObserver` collector make "exactly one request" and "no loading affordance on restore" demonstrable instead of assumed.

Four facts measured in this session change the shape of the plan relative to the UI-SPEC:

1. **The HTTP-intercept proof the ROADMAP asks for cannot exist here.** `playwright.config.js` forces `VITE_USE_MOCKS: "true"` for the `web` project, and in that mode `searchKnowledge` never calls `fetch` — `[VERIFIED: web/src/services/knowledgeApi.js:121-125]` `const { isMocksEnabled } = await import('./authEnv.js') / if (isMocksEnabled()) { / await delay(80) / return mockSearchKnowledge({ q, role, limit, offset }, materials)`. The project already recorded this in prose: `[VERIFIED: tests/admin-chrome.spec.js:572-574]` `// Only the injectors already in the tree: both blocks read an in-memory mock, so / // \`page.route\` has nothing to intercept.` A `page.route` counter would assert `0 === 1` and could never show the StrictMode duplicate. The counter must sit at the `searchKnowledge` call boundary **inside the page** (CONTEXT `Claude's Discretion` #1 default), and `web/src/services/knowledgeApi.js` must stay byte-identical.
2. **The `submitId` strip is load-bearing for criterion 3, not for "1 not 2 on reload".** The UI-SPEC (C-15) justifies the strip by "F5 gives 1 request, not 2" — that does not discriminate: a replayed marker still produces exactly one forced request on a fresh document. What the strip actually protects: with a stale `submitId` still in `history.state.usr`, every **remount** of `/knowledge?q=…` (i.e. Back from a material) takes the *forced* branch and re-issues the request, so the module cache is never consulted and C-09/C-10 fail. The direct assertion `history.state.usr.submitId == null` is verified as observable: `[VERIFIED: web/node_modules/react-router/dist/development/chunk-7SIULPXI.js:222-227]` `function getHistoryState(location, index) { / return { / usr: location.state, / key: location.key, / idx: index,`
3. **A q-keyed cache alone cannot satisfy C-13.** After a remount `role` is back to `'all'` (its `useState` default), while the snapshot that produced the on-screen rows may be the `ds` one. Restoring therefore needs a second, tiny module map: "which role last produced rows for this q". Measured fixture that makes this discriminating: `SQL` under role `all` returns **5** rows, under `ds` returns **1** (`pgvector`) — `[VERIFIED: web/src/data/mock.js + mockSearchKnowledge, executed this session]`.
4. **C-12's «Показать ещё» half is not provable in the mock harness.** The mock catalog holds **8** materials (`[VERIFIED: node import of web/src/data/mock.js, catalog size 8]`) while `DEFAULT_SEARCH_LIMIT = 10` — `has_more` is *never* true for any query, so the «Показать ещё» button never renders in any Playwright test. The snapshot must still carry `{items, hasMore, nextOffset, limit}`, but the e2e proof must be reduced to "the restored row set is identical" plus a structural pin; the pagination-resume assertion would be vacuous (`toBeVisible` on a button that cannot exist). This is the one item the planner must record as an explicit deviation (Key Finding 8 lists the three options).

**Primary recommendation:** one effect in `KnowledgePage` with deps `[qUrl, submitId]`, a `lastHandledQueryRef` guard set *synchronously before* the await, a module-scope `Map<(role, q) → snapshot>` plus `lastRoleForQuery`, `activeQuery` set at request start, `preSearch = qUrl === '' && !error`, R-1's gate `searching || (activeQuery !== null && !error)`, the counter incremented immediately before the single `searchKnowledge` call, and all new Playwright cases appended to the existing `tests/knowledge.spec.js` (no new spec file — the `testMatch` regex would silently drop one).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

Обсуждены три зоны: триггер поиска, назад/вперёд и повторная отправка, контракт шапки с формой. Инструмент доказательства критерия 2 вынесен в `Claude's Discretion` — см. пункт 1, там же зафиксирован конфликт с буквой ROADMAP.

#### Триггер поиска (KNOW-05 критерий 1)

- **D-01:** **URL `?q` — единственный источник правды** для «что искать». Страница запускает поиск из эффекта, ключ — нормализованный (`trim`, через `validateKnowledgeQuery`) `?q`; шапка остаётся тонкой и продолжает только навигировать. Отклонены: одноразовый маркер в `location.state` как триггер (тогда F5/шара ссылки дают pre-search с заполненным полем, а не результаты) и «шапка сама выполняет `searchKnowledge` и отдаёт результаты состоянием навигации» (продублировала бы в `SearchPill` весь `runSearch`: валидацию, роль, `limit/offset`, обработку ошибок, `trackGoal` — `KnowledgePage.jsx:70-121`). — **Reversibility:** costly — смена формы триггера переписывает точку запуска и весь набор ассертов «свежая загрузка / шара ссылки», которые эта фаза фиксирует.

- **D-02:** Встроенная форма «Найти» (`handleSubmit`, `KnowledgePage.jsx:125-135`) **тоже пишет `?q`**, и пишет через `replace`, а не `push`. Адрес всегда равен текущему запросу, каждый поиск не создаёт шаг истории, Back уводит со страницы, а не в предыдущий запрос. Без этого адрес перестаёт быть источником правды и F5 теряет запрос, введённый в форме. — **Reversibility:** reversible — один вызов `setSearchParams` заменяется на вариант с `push`.

- **D-03:** Дубль-выстрел (StrictMode setup→cleanup→setup, а также любой re-render) гасится сравнением с **последним выполненным** нормализованным q (ref), а не булевым флагом «уже искали». Булев флаг сломал бы легитимную смену запроса при смонтированном компоненте.

#### Назад/вперёд и повторная отправка (KNOW-05 критерий 3)

- **D-04:** **Модульный in-memory кэш** последнего результата по ключу `(нормализованный q, role)`: Back/Forward на уже просмотренный `?q=…` и возврат с материала (`/materials/:slug` → Back) восстанавливают результаты **без запроса**. Причина: `KnowledgePage` размонтируется при уходе на материал (`web/src/App.jsx:52-53` — соседние маршруты), поэтому ref-страж внутри компонента критерий 3 не выполнит, а `knowledgeApi.searchKnowledge` кэша не имеет вовсе. F5 всегда идёт в API (честная свежесть), в `localStorage`/`sessionStorage` ничего не пишется. Ошибка не кэшируется. — **Reversibility:** costly — кэш является механизмом, делающим критерий 3 доказуемым; его удаление потребует переписать ассерты Back/Forward и явно принять переиспускание запроса как отклонение от ROADMAP.

- **D-05:** **Каждая отправка = ровно один свежий запрос**, включая отправку того же q, когда результаты уже открыты. Так как URL при этом не меняется, шапка кладёт одноразовый `submitId` в `location.state`; страница потребляет его и **снимает через `replace`**, поэтому Back/Forward этот маркер не повторяют. Форма «Найти» сохраняет свою текущую семантику (`handleSubmit` всегда исполняет `runSearch`). — **Reversibility:** reversible — протокол между двумя компонентами и ассерты; удаление возвращает поведение «тот же q — no-op».

- **D-06:** Кэш (D-04) **не** обслуживает явную отправку: `submitId` побеждает кэш. Иначе кнопка/Enter перестали бы обновлять данные, что противоречит D-05.

#### Контракт шапки с формой (KNOW-05 критерий 4)

- **D-07:** Роль при отправке из шапки **сбрасывается на «Все»** (`role = 'all'`; в запрос `role` не передаётся — `D-62`). Отправка из шапки — новый поиск с чистого листа: выбранная ранее роль не может молча сузить выдачу, и поведение одинаково из любого раздела и при любом mount. — **Reversibility:** reversible.

- **D-08:** Пустой/пробельный submit → навигация на `/knowledge` **без** `?q`, **ноль** запросов, на странице — нейтральный pre-search лендинг с чипами-подсказками (`D-60`), **без** inline-ошибки. Существующий guard «Введите запрос» остаётся и продолжает срабатывать по кнопке «Найти» внутри страницы. — **Reversibility:** reversible.

- **D-09:** Запрос длиннее 500 code points → навигация с `?q`, на странице inline «Сократите запрос», **ноль** запросов. Единственный путь валидации — `validateKnowledgeQuery` (`web/src/services/knowledgeApi.js:19-30`); `maxlength` в шапке не вводится (браузер молча резал бы ввод) и своей копии текста ошибки шапка не получает. — **Reversibility:** reversible.

- **D-10:** Поле ввода на странице **синхронизировано с `?q`**, поэтому отправка из шапки перезаписывает неотправленный текст в форме. Это прямое следствие D-01: адрес — правда, поле — его отражение.

### Claude's Discretion

Планировщик решает сам, не переспрашивая, в рамках констрейнтов:

1. **Инструмент доказательства критерия 2 (единственный незакрытый конфликт с ROADMAP).** Проекту `web` жёстко задан `VITE_USE_MOCKS=true` (`playwright.config.js:48-51`), HTTP-запросов к `/knowledge/search` в e2e не существует; это уже зафиксировано словами в `tests/admin-chrome.spec.js:574` («`page.route` has nothing to intercept»). Поэтому буквальная формулировка «Playwright request interception counting calls to the search endpoint» холостая: перехват считал бы ноль и зеленел бы. **Дефолт:** счётчик вызовов на границе `searchKnowledge`, выставленный тест-харнессом в духе существующего `window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount` (`tests/admin-chrome.spec.js:2277`) с явным сбросом перед каждым тестом. Ассерт `=== 1` **обязан** быть невакуумным: RED-фаза должна падать от двойного вызова (в том числе StrictMode). Если планировщик выберет live-режим с `page.route`, это отдельный spec и отдельный webServer/env, и это нужно обосновать в плане — цена: риск ложных падений из-за `web/.env.local` и залипшего слушателя на `5174` (STATE § Blockers).
2. **Форма кэша (D-04):** `Map` в модуле страницы против `Map` в `knowledgeApi.js`; что именно хранить — только `items` или весь снимок `{items, hasMore, nextOffset, limit}`. Требование одно: восстановление после Back не должно терять страницы, догруженные кнопкой «Показать ещё».
3. **Точка потребления `submitId`** и способ отличить «навигацию из истории» от «новой отправки» (например, сравнение `location.key` против ref или снятие маркера через `replace` в самом эффекте) — форма свободна, требование D-05/D-06 обязательно.
4. **Где живут тесты:** `tests/web-app.spec.js` (там уже живёт шапочный поиск — `:323-342`, включая ассерт `toHaveValue("RAG")`) против `tests/knowledge.spec.js`. Если заводится новый файл, `testMatch` в `playwright.config.js:71` обязан быть расширен (прецедент 25-01: `admin-chrome.spec.js` не должен молча выпасть из раннера).
5. **Нормализация и кодирование:** шапка кодирует через `encodeURIComponent` (`SearchPill.jsx:23`), страница нормализует через `validateKnowledgeQuery`; расхождение (например `+` против `%20`) обязано не порождать второй запрос на тот же смысл.
6. **Поведение при ошибке:** запрос из шапки, закончившийся ошибкой, показывает существующий `kb-search-error` + «Повторить»; ошибка не попадает в кэш, а повторный заход на тот же `?q=` после ошибки снова идёт в API.

### Deferred Ideas (OUT OF SCOPE)

- **Роль в URL (`?q=…&role=ds`)** — расширение контракта адреса; отклонено в D-07 как не требуемое `KNOW-05`.
- **`sessionStorage`/`localStorage`-кэш результатов** — переживает F5, но появляется persist-слой и риск показать устаревшие результаты как свежие; отклонено в D-04.
- **`maxlength` в поле шапки** — молчаливое обрезание ввода; отклонено в D-09.
- **Кнопка/авто-обновление выдачи** (refresh, polling свежести) — новая функциональность, отдельная фаза.
- **Серверная аналитика поиска / метрики «поиск на загрузке»** — прямо вне скоупа по REQUIREMENTS § Out of Scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KNOW-05 | Submitting a non-empty query from the header search navigates to «База знаний» and runs the search immediately — results appear without a second click, exactly one request is issued per submit, and an empty submit never calls the search API | Key Findings 1-7: URL-keyed effect with a `lastHandledQueryRef` guard (StrictMode-safe), `submitId` one-shot protocol for same-q resubmits, module snapshot cache for Back/Forward, page-level counter `window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__` (+ static single-call-site gate), `MutationObserver` affordance collector with a non-vacuity control, `preSearch`/R-1 gate rewrites. Criterion → test mapping in `## Validation Architecture`. |

`[VERIFIED: .planning/REQUIREMENTS.md:33]` — `- [ ] **KNOW-05**: Submitting a non-empty query from the header search navigates to «База знаний» and runs the search immediately — results appear without a second click, exactly one request is issued per submit, and an empty submit never calls the search API`
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Query as the source of truth (`?q`) | Browser / Client (history + router) | — | The URL is already the header's contract; no server involvement, no new endpoint |
| Search execution + in-flight state | Browser / Client (`KnowledgePage`) | — | `runSearch` already owns validation, role, `limit/offset`, error mapping, `trackGoal`; the effect must reuse it, not duplicate it (D-01) |
| Same-q resubmit signal | Browser / Client (`location.state`) | — | A URL cannot express "same q again"; the one-shot marker is the smallest channel that survives a re-render and dies on `replace` |
| Result snapshot memory | Browser / Client (module scope, process memory) | — | `KnowledgePage` unmounts on `/materials/:id`; component state/refs cannot survive that. No `localStorage`/`sessionStorage` (D-04, deferred) |
| Request counting instrument | Browser / Client (page module) → test harness read | — | HTTP interception is dead under `VITE_USE_MOCKS=true`; the counter must sit at the `searchKnowledge` boundary |
| Input validation (blank / overlong) | Browser / Client (`validateKnowledgeQuery`) | API / Backend (unchanged guard) | D-09 keeps one validation path; the backend stays untouched |
| Search results (data) | API / Backend | — | Not modified by this phase — no new endpoint, no DTO change |

## Project Constraints (from .cursor/rules/)

Extracted verbatim where the directive is imperative; these carry the same authority as the locked decisions above.

| Rule file | Directive | Consequence for this phase |
|-----------|-----------|----------------------------|
| `.cursor/rules/tdd.mdc` | `NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST`; order is «тест → падает по ожидаемой причине → минимальный фикс → прогон → рефактор» | Every slice in `## Proposed TDD Slice Order (RED → GREEN)` names the exact failing command. The counter, the effect, the cache and the `submitId` payload are all production edits, so each needs a red assertion before it lands. |
| `.cursor/rules/tdd.mdc` | «Тесты должны проверять поведение системы, а не наличие mock-объектов» | The counter is a *boundary* observation of `searchKnowledge`, not a mock assertion; the rendered hit row is the primary signal, the counter is the anti-duplicate signal. |
| `.cursor/rules/architecture.mdc` | Frontend API access only through `web/src/services/`; UI must not know Supabase/backend details | `SearchPill` gains **no** knowledge of `searchKnowledge`; the cache lives in the page module, not in the service |
| `.cursor/rules/architecture.mdc` | «Бизнес-логика в React-компонентах … Anti-pattern» | No new business rule is introduced: validation stays in `validateKnowledgeQuery`, the request shape stays `q, role, limit, offset` |
| `.cursor/rules/architecture.mdc` | Dependencies point inward; no deep imports across modules | Untouched — this phase adds no cross-module import |
| `.cursor/rules/python-uv.mdc` | Python dependency changes go through `uv` | Not applicable: no Python, no dependency change |
| `.cursor/rules/context7.mdc` | Always use Context7 for library/API docs | Used for the React StrictMode and react-router `useSearchParams` claims below; every other claim is measured against the repo |
| `AGENTS.md` § Git remote | `origin` operations only via WSL | Not needed inside this phase; note it for the executor |
| `AGENTS.md` § Issue tracker | Issues live as markdown under `.scratch/` | No new issue is required unless the planner opens one for the C-12 deviation |

**Scope guard from ROADMAP/STATE:** `[VERIFIED: .planning/STATE.md:310]` `- **Phase 27 (KNOW-05):** header submit must run the search immediately — exactly one API call per submission, zero calls for an empty query, no double-fire on re-render. \`knowledgeApi.searchKnowledge\` and the backend stay untouched.`

## Key Findings

### 1. The ROADMAP's literal proof instrument (HTTP interception) is dead in this project — and the counter's home is the page, not the adapter

`playwright.config.js` starts the `web` dev server with mocks forced on:

```
    48|    // Highest priority over web/.env.local live-proof overrides (D-09 offline Playwright).
    49|    env: {
    50|      ...process.env,
    51|      VITE_USE_MOCKS: "true",
    52|    },
```
`[VERIFIED: playwright.config.js:48-52]`

In that mode the adapter never issues a request, so `page.route('**/knowledge/search')` would count zero calls and an assertion `=== 1` would fail for the wrong reason (or, with `=== 0`, pass vacuously). The mock branch is:

```
   121|  const { isMocksEnabled } = await import('./authEnv.js')
   122|  if (isMocksEnabled()) {
   123|    await delay(80)
   124|    return mockSearchKnowledge({ q, role, limit, offset }, materials)
   125|  }
```
`[VERIFIED: web/src/services/knowledgeApi.js:121-125]`

The project already documented the dead-intercept situation for a different feature: `[VERIFIED: tests/admin-chrome.spec.js:572-574]`

```
  // Only the injectors already in the tree: both blocks read an in-memory mock, so
  // `page.route` has nothing to intercept. `arms` are sessionStorage-backed, so they
  // survive the reload that triggers the load.
```

**Decision (in scope, no scope expansion):** the counter increments inside `runSearch`, immediately **before** the single `searchKnowledge` call. `knowledgeApi.js` is not touched — `git diff --exit-code -- web/src/services/knowledgeApi.js` must stay clean, and the static gate in Key Finding 6 asserts the instrument never appears in the adapter.

**Citation correction for the planner:** CONTEXT cites the harness precedent as `tests/admin-chrome.spec.js:2277`. That file is 867 lines; the real precedent is in **`tests/admin.spec.js:2272-2295`** — `[VERIFIED: tests/admin.spec.js:2276-2278]`

```
    const before = await page.evaluate(() =>
      window.__DIGEST_INGESTION_SCHEDULE_HARNESS__.readIngestionScheduleMock().patchCount,
    );
```

A planner that opens `admin-chrome.spec.js:2277` will find nothing and may conclude the precedent does not exist. Same shape, different counter (`KnowledgePage` exposes a bare global per the UI-SPEC X-1; the ingest precedent wraps it in a harness object — either is acceptable, the UI-SPEC's name is `window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__` and must be followed literally).

### 2. Effect shape: `[qUrl, submitId]` deps + a synchronous ref guard; the marker is consumed before the request starts

The guard must be set **synchronously, before the first `await`**, because StrictMode runs `setup → cleanup → setup` in the same tick. Verbatim from the official docs: `[CITED: react.dev/reference/react/useEffect]` `When Strict Mode is on, React will run one extra development-only setup+cleanup cycle before the first real setup.` — the mounted instance keeps its refs across that cycle (the docs' troubleshooting section frames it as `setup → cleanup → setup` of the *same* Effect, not a remount), so a ref comparison is the correct anti-duplicate mechanism and a state flag is not (a state write would not be visible to the second setup synchronously). React is `19.2.8` `[VERIFIED: web/node_modules/react/package.json]` and StrictMode is active: `[VERIFIED: web/src/main.jsx:109-112]` `createRoot(document.getElementById('root')).render( / <StrictMode> / <App /> / </StrictMode>,`.

Resolution order inside the single effect (this is the whole trigger design; nothing else may start a search):

1. **Consume the marker** — if `location.state?.submitId` is a string and differs from `consumedSubmitIdRef.current`, record it and immediately `setSearchParams(searchParams, { replace: true, state: null })`. Verified that `setSearchParams` forwards navigate options verbatim: `[VERIFIED: web/node_modules/react-router/dist/development/chunk-YRTY65LJ.js:731-740]`

   ```
         let setSearchParams = React.useCallback(
           (nextInit, navigateOptions) => {
             const newSearchParams = createSearchParams(
               typeof nextInit === "function" ? nextInit(new URLSearchParams(searchParams)) : nextInit
             );
             hasSetSearchParamsRef.current = true;
             navigate("?" + newSearchParams, navigateOptions);
           },
   ```

   `state` is a documented `NavigateOptions` member: `[CITED: react-router docs api/hooks/useNavigate]` `**state** (\`any\`) - Optional state to pass to the next route (accessible via \`useLocation().state\`).`
2. **Validate** `qUrl` through `validateKnowledgeQuery` — the *only* validation path (D-09). Blank → reset to landing, no request, no inline error. Overlong → `validation.message` as the inline error, reset the results, no request.
3. **Forced?** (`forced = marker consumed this run`) → skip both the last-q guard and the cache; force `role = 'all'` (D-07) and run.
4. **Not forced:** bail if `lastHandledQueryRef.current === q` (re-render / StrictMode / the effect re-running after the form's own URL write / the strip's replace navigation).
5. **Not forced, new q:** look up the snapshot for `(lastRoleForQuery.get(q) ?? roleRef.current, q)`; on a hit restore and `setRole(cachedRole)`, on a miss run.

Why the marker must be consumed *before* the request: the strip navigation re-renders the page (new `location.key`, same pathname) and re-runs the effect with `submitId === null`; the ref guard is what makes that second run a no-op, so it must already be written.

**`?q` change while already mounted** (C-03) is covered by `qUrl` being in the deps — a plain `[]` effect would leave the old rows on screen. The header pushes a new entry each time (unchanged behaviour), so Back/Forward between two visited `?q`s stays possible.

**Role must NOT be a dependency.** `handleRoleChange` already executes its own `runSearch`; if the effect depended on `role`, every chip change would fire a second (duplicate) search. Read the current role through `roleRef` (assigned during render) instead, and pass `role` explicitly into `runSearch` so a stale closure can never leak the wrong role into the request.

### 3. Why the marker is stripped: it protects the cache (criterion 3), not the reload count

Trace of a header submit with the strip:

```
/ (header) --push--> /knowledge?q=RAG {usr:{submitId}}  → effect: forced → strip → {usr:null} → 1 request
row click --push--> /materials/rag-systems {usr:{section:'base'}}
Back --pop--> /knowledge?q=RAG (restored entry, usr:null) → effect: not forced → cache hit → 0 requests
```

Without the strip, the restored entry still carries `usr.submitId`; the remount's fresh `consumedSubmitIdRef` is `null`, so `forced` is true → **a new request on every return from a material**, and C-09/C-10 fail. With the strip, the same Back is a cache hit. The reload consequence the UI-SPEC cites ("1 request, not 2") is **not discriminating** — a replayed marker also yields exactly one forced request on a fresh document — so the plan must assert the marker directly:

```js
expect(await page.evaluate(() => window.history.state?.usr?.submitId ?? null)).toBeNull()
```

`history.state.usr` is the verified storage shape (`chunk-7SIULPXI.js:222-227`, quoted above). Two consequences worth stating in the plan: the strip replaces the entry (Back still leaves the page, it does not create a new step), and it clears `location.state` entirely, which is harmless on `/knowledge` because the «База» pill lights from `baseRoute` (`[VERIFIED: web/src/components/AppShell.jsx:57-59]` `const baseRoute = Boolean(matchPath({ path: '/knowledge', end: true }, pathname))` … `const baseLit = baseRoute || section === 'base'`).

### 4. Cache: module scope in the page, key `(role, q)`, snapshot `{items, hasMore, nextOffset, limit}` + a `lastRoleForQuery` side map

- **Where:** module scope of `web/src/pages/KnowledgePage.jsx`. Not `knowledgeApi.js` (must stay byte-identical, CONTEXT Out of scope). Module scope survives the unmount that state/refs do not — the unmount is real: `[VERIFIED: web/src/App.jsx:51-53]` `{ path: 'knowledge', element: <KnowledgePage /> }, / { path: 'materials/:id', element: <MaterialPage /> },`.
- **Why not `sessionStorage`:** D-04 / Deferred. F5 must always hit the API (C-11), which also means the module map resets per document for free.
- **Key:** `` `${roleValue}\u0000${q}` `` with `q` already normalised by `validateKnowledgeQuery` (trimmed). This is what makes `?q=%20RAG%20` and `?q=RAG` one entry, and `?q=RAG+systems` vs `?q=RAG%20systems` one entry (both decode to `RAG systems` through `URLSearchParams`) — C-04.
- **Snapshot:** `{ items, hasMore, nextOffset, limit }`. `nextOffset` is the load-bearing field for «Показать ещё» resume; `limit` is constant today (`DEFAULT_SEARCH_LIMIT = 10`) but is stored so the snapshot is self-describing.
- **`lastRoleForQuery: Map<q, roleValue>`** is required by C-13: on remount `role` is `'all'` again, but the rows on screen may be the `ds` snapshot. Resolution: `const intendedRole = lastRoleForQuery.get(q) ?? roleRef.current`, look up `(intendedRole, q)`, and `setRole(intendedRole)` on a hit. Reconciliation with C-19's negative pin ("роль не сбрасывается историей"): restoration shows the role that *produced those rows*; it never *forces* `'all'` — only a header submit does that.
- **Writes:** after a successful non-append search (fresh snapshot) and after a successful append (merged snapshot, `nextOffset` advanced). **Deletes:** on a non-append error for that key — otherwise C-14 ("a repeat visit after an error goes to the API") would be served from a stale snapshot.
- **Bound:** FIFO eviction at ~20 entries via `Map` insertion order (a long session cannot grow it without bound). Not observable in tests; keep it to four lines.
- **Never write the cache from a `setState` updater.** StrictMode double-invokes updaters; the snapshot would be written twice and any derived count would drift. The write belongs in the async function body (or a dedicated effect), not in `setItems((prev) => …)`.

### 5. R-1, the landing rule, and `activeQuery` timing are three different switches

| Switch | Today | Contract | Why it cannot be merged with the others |
|--------|-------|----------|------------------------------------------|
| Live region gate | `activeQuery !== null && !error` (`[VERIFIED: web/src/pages/KnowledgePage.jsx:348]`) | `searching \|\| (activeQuery !== null && !error)` | On the very first search `activeQuery` is still `null` during flight, so without `searching` the `«Ищем…»` branch of `knowledgeResultSummary` (`:298`) is unreachable and X-2's `live-searching` can never be recorded |
| Landing | `activeQuery === null && !error` (`:174`) | `qUrl === '' && error === null` | `activeQuery` lags the URL by a frame and by the request; the chips must be gone on the *first* paint of a `?q` deep link (C-01/C-08), and must stay gone during flight and on error |
| `activeQuery` write | after success (`:86`) | at request start for non-append (recommended) | Not required by any assertion — the UI-SPEC explicitly allows either timing — but it makes the status summary and `handleRetry`'s `activeQuery ?? query` coherent while a request is in flight. If the planner skips it, every criterion still passes. |

`preSearch` is computed during render from `useSearchParams()`, so there is no frame in which `?q=RAG` renders the landing: `qUrl` is a synchronous read of `location.search`. Do **not** seed the URL into state and mirror it back.

Existing verbatim anchors: `[VERIFIED: web/src/pages/KnowledgePage.jsx:174]` `const preSearch = activeQuery === null && !error`; `[VERIFIED: web/src/pages/KnowledgePage.jsx:319-320]` `{preSearch ? ( / <div className="mb-8" data-testid="kb-hint-chips">`; `[VERIFIED: web/src/pages/KnowledgePage.jsx:297-302]`

```
function knowledgeResultSummary({ searching, items, hasMore }) {
  if (searching) return 'Ищем…'
  if (items.length === 0) return 'Найдено 0 материалов'
  return `Показано ${items.length}${hasMore ? '+' : ''}`
}
```

### 6. Instruments: exact shapes, reset semantics, and what makes each one non-vacuous

**X-1 — request counter.**

```js
/** Phase 27 instrument: counts searchKnowledge *attempts* (success and throw). */
function bumpKnowledgeSearchCount() {
  if (typeof window === 'undefined') return
  window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__ = (window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__ ?? 0) + 1
}
```

Placement: first statement inside the `try` in `runSearch`, i.e. directly before `const dto = await searchKnowledge({…})` (`[VERIFIED: web/src/pages/KnowledgePage.jsx:81]` `const dto = await searchKnowledge({`). Counting before the call is what makes the thrown-`NETWORK` path (C-23's «Повторить») countable.

Reset semantics — verified: `[CITED: Playwright docs Page.addInitScript]` `Adds a script which would be evaluated in one of the following scenarios: * Whenever the page is navigated. * Whenever the child frame is attached or navigated.` and `The script is evaluated after the document was created but before any of its scripts were run.` In practice init scripts are installed per **new document** (`Page.addScriptToEvaluateOnNewDocument`/`setBootstrapScript`), so:

- `page.addInitScript(() => { window.__DIGEST_KNOWLEDGE_SEARCH_COUNT__ = 0 })` in `beforeEach` ⇒ the counter is `0` on every `goto`/`reload` (this is exactly what C-11 depends on: after reload, `1` means "one request on the new document", `0` would mean the cache survived F5).
- SPA `pushState`/`popstate` navigations **do not** create a document, so the counter survives `page.goBack()` — the C-09/C-10 assertions ("count unchanged") rely on that. Make the risk visible rather than silent: assert exact equality to the value captured before the history step **and** assert it is `>= 1`; if an init script ever re-ran on a history pop, that pair fails loudly instead of passing at `0 === 0`.

**Non-vacuity, two independent controls:**
1. *One-time RED evidence:* with a naive `useEffect(() => { void runSearch(qUrl, { role: 'all' }) }, [])` the first Playwright run must read **2** (StrictMode). The plan must record that observed `2` (test output or plan Notes) before the guard is added. If a naive run reads `1`, StrictMode is not active in that build and the whole non-vacuity argument has to be re-established — stop and investigate.
2. *Permanent control:* C-15 ("re-submit the same header q ⇒ `+1`") proves on every run that the counter can still move, so `=== 1` never decays into "the counter is dead".

**X-2 — affordance collector** (test-only, `page.evaluate`; nothing in `web/src`):

```js
function startAffordanceCollector() {
  const labels = []
  const record = (label) => { if (!labels.includes(label)) labels.push(label) }
  const scan = () => {
    if (document.querySelector('[data-state="loading"]')) record('loading-state')
    if (document.querySelector('#kb-search[disabled]')) record('field-disabled')
    const live = document.querySelector('[aria-live="polite"]')
    if (live && live.textContent.includes('Ищем…')) record('live-searching')
  }
  window.__KB_AFFORDANCE_OBSERVER__?.disconnect()
  window.__KB_AFFORDANCE_LOG__ = labels
  scan()
  const observer = new MutationObserver(scan)
  observer.observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
    attributes: true,
    attributeFilter: ['disabled', 'data-state'],
  })
  window.__KB_AFFORDANCE_OBSERVER__ = observer
}
```

- The three selectors are verified against real markup: `[VERIFIED: web/src/components/ActionButton.jsx:51-53]` `data-state={state === 'idle' ? undefined : state} / disabled={disabled || state === 'loading'}`; `[VERIFIED: web/src/pages/KnowledgePage.jsx:233-239]` `<input id="kb-search" … disabled={searching}`; `[VERIFIED: web/src/pages/KnowledgePage.jsx:349-351]` `<p className="mb-4 text-xs text-text-secondary" aria-live="polite">`.
- The observer is installed on `document.documentElement`, so it **survives SPA route changes** (the document is not replaced) — that is what allows installing it on `/materials/rag-systems` and observing the Back transition.
- **Mandatory non-vacuity control:** the same collector, installed before a *fresh* header submit, must record all three labels. Without that control `toEqual([])` in the restore test passes for a spinner that already vanished and for a page that never showed one.
- Why `MutationObserver` and not a post-settle sample: the mock answers in 80 ms `[VERIFIED: web/src/services/knowledgeApi.js:123]` `await delay(80)`, so `toHaveText('Ищем…')` would be a coin flip.
- `kb-skeleton` is deliberately **not** in the log — it renders only on the append path (`[VERIFIED: web/src/pages/KnowledgePage.jsx:388-394]`, guarded by `loadingMore`), so its absence on restore is a structural property, not evidence.

**Static single-call-site gate** (`tests/unit/test_knowledge_search_single_call_site.js`, `node:test`):

- auto-discovered **without config changes** — `[VERIFIED: scripts/run-unit-js.cjs:12-21]` `const files = readdirSync(unitDir) / .filter((name) => name.endsWith('.js')) / .sort() / .map((name) => join(unitDir, name))` (flat directory, non-recursive).
- globbing pattern to copy: `[VERIFIED: tests/unit/test_section_context_gates.js:26-36]` `readdirSync(path.join(ROOT, 'web/src'), { recursive: true }) / .filter((entry) => /\.(js|jsx|css)$/.test(entry))`.
- assertions: (a) exactly one file under `web/src/**/*.{js,jsx}` imports the identifier `searchKnowledge` — today only `[VERIFIED: web/src/pages/KnowledgePage.jsx:7]` `searchKnowledge,`; (b) exactly one non-comment occurrence of `searchKnowledge(` — today only line `:81` (the other hit is the comment `[VERIFIED: web/src/pages/KnowledgePage.jsx:131]` `// Do not call searchKnowledge (KNOW-01 / D-57).`); (c) `web/src/services/knowledgeApi.js` contains neither `__DIGEST_KNOWLEDGE_SEARCH_COUNT__` nor a second limiter. Strip `/* … */` blocks and whole-line `//` comments (line-leading only — a naive `//` strip would eat `https://` inside strings).
- failure message must name the regression: a second call site means the counter under-reports, i.e. criterion 2 is no longer proven.

### 7. Test placement and runners — extend `tests/knowledge.spec.js`, do not create a sibling spec

`[VERIFIED: playwright.config.js:69-73]`

```
    {
      name: "web",
      testMatch: /(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/,
      use: { baseURL: "http://127.0.0.1:5174" },
    },
```

The regex is an unanchored substring match, so it accepts `tests/knowledge.spec.js` and would **not** match a new `knowledge-submit.spec.js` or `knowledge-search.spec.js` (neither contains the literal `knowledge.spec.js`). That is precisely the 25-01 trap. Two acceptable outcomes: (a) append the new cases to `tests/knowledge.spec.js` — **recommended, zero config change**, the file is 63 lines and already owns KNOW-01…04; (b) create a new file **and** extend the alternation (e.g. `knowledge(-[a-z-]+)?\.spec\.js`). Leave `tests/web-app.spec.js:323-342` untouched: it is the pin that keeps the header pill's geometry and the `toHaveValue("RAG")` seed honest.

Harness config that matters:

- `[VERIFIED: playwright.config.js:44-47]` `command: "npm run dev --prefix web -- --host 127.0.0.1 --port 5174"` with `reuseExistingServer: !process.env.CI` ⇒ a manually started server is reused **and** keeps `web/.env.local`. That file currently contains `VITE_USE_MOCKS=false` (measured this session; the key is present exactly once), so a stale listener serves the login screen and the whole `web` project fails on `RequireAuth`. Kill `5174` before any run: `Get-NetTCPConnection -LocalPort 5174 -State Listen`. (No listener was present at research time.)
- `--project=web` also filters which `webServer` entries boot (`[VERIFIED: playwright.config.js:28-30]` `function wantsProject(name) { const selected = selectedProjects(); return selected.length === 0 || selected.includes(name); }`), so single-file runs stay fast.
- Single test: `npx playwright test --project=web tests/knowledge.spec.js -g "<title>"`. Whole file: `npx playwright test --project=web tests/knowledge.spec.js`. JS unit gates: `npm run test:js`.
- Each Playwright test gets a fresh document ⇒ module-level cache state cannot leak between tests.

### 8. C-12 («Показать ещё» survives restore) is not provable in the mock harness — measured

`mockSearchKnowledge` pages with `limit` and reports `has_more = matched.length > offset + limit`; the shared catalog has **8** entries and `DEFAULT_SEARCH_LIMIT` is `10`, so `has_more` is always `false`. Measured by executing the real module this session:

| Query | role | items | has_more |
|-------|------|-------|----------|
| `RAG` | all | 2 (`rag-systems`, `pgvector`) | false |
| `SQL` | all | 5 | false |
| `SQL` | ds | 1 (`pgvector`) | false |
| `SQL` | analyst | 4 | false |
| `а` (single letter, widest possible) | all | 7 | false |
| catalog size | — | 8 | — |

Consequence: `hasMore` is false in every e2e scenario, the «Показать ещё» button never renders, `loadingMore`/`kb-skeleton` are unreachable, and `knowledgeResultSummary` never shows the `N+` form. Therefore:

- The snapshot contract (`nextOffset`, `hasMore`) is still required and still cheap — it is four fields written in one place.
- **C-12's pagination half must be reduced** to: "Back restores the identical row set and order (no duplicates, no truncation to page 1)" plus a structural pin that the restored state writes `hasMore`/`nextOffset` from the snapshot rather than `0`.
- Options if the planner wants a real pagination proof (pick one, record it as a deviation either way):
  1. **Descope (recommended):** keep the structural pin, state in the plan why the assertion is absent. Cost: zero production risk.
  2. Extend the shared fixture `web/src/data/mock.js` with ≥4 materials matching a fixed token so `has_more` becomes true at `limit = 10`. Cost: a shared fixture edit that also feeds `/archive`, the issue pages and `MaterialPage` lookups — cross-spec risk for a criterion that is not user-visible today.
  3. Add a test-arm for the limit — **rejected**: the limit lives in `knowledgeApi.js` (`DEFAULT_SEARCH_LIMIT`), which must stay byte-identical, and any page-level override changes the request shape the ROADMAP locks.

This is a *correction to the UI-SPEC*, not a scope change: the contract's intent (don't lose loaded pages) is preserved; only the instrument for proving it in e2e does not exist.

### 9. Measured fixtures for the new assertions

| Purpose | Fixture | Observable |
|---------|---------|------------|
| Criteria 1-2 happy path | `RAG` | 2 rows; `building production rag systems` row; `kb-hint-chips` count 0 |
| C-03 (q change while mounted) | `RAG` → `SQL` | `SQL` rows include `anomaly-detection`; `rag-systems` disappears (`RAG` results do not contain it) |
| C-13 (cache key includes role) | `SQL` + `ds` = **1** row vs `SQL` + all = **5** rows | a q-only cache would restore 5 rows and light «Все» |
| C-19 (role reset) | `RAG` + `analyst` = **0** rows (verified by the existing `tests/knowledge.spec.js:49-62`) | after a header submit the rows appear and «Все» is pressed |
| C-18 (overlong) | `'a'.repeat(501)` | inline `«Сократите запрос»`, page field length 501 |
| C-16 (blank) | `'   '` | `/knowledge` with no `?q`, chips visible, no `kb-inline-error` |

### 10. Known hazards, each measured

1. **StrictMode double-invoke** — real, active (`web/src/main.jsx:109-112`); the guard must be synchronous (Key Finding 2).
2. **`KnowledgePage` unmounts on `/materials/:id`** `[VERIFIED: web/src/App.jsx:51-52]` `{ path: 'knowledge', element: <KnowledgePage /> }, / { path: 'materials/:id', element: <MaterialPage /> },` — component refs die; only module scope survives (D-04).
3. **`disabled={searching}` on `#kb-search`** `[VERIFIED: web/src/pages/KnowledgePage.jsx:239]` — a test that types immediately after a navigation can hit a disabled field; Playwright's actionability waits, but an explicit `await expect(search).toBeEnabled()` makes failures diagnostic instead of flaky. Same for the role chips (`disabled={searching}`, `:275`).
4. **`preSearch = activeQuery === null && !error`** (`:174`) — if the effect never fires, the landing returns and criterion 1 fails *for the right reason*. That is the intended RED, not a fixture bug.
5. **`toHaveValue("RAG")` pin** `[VERIFIED: tests/web-app.spec.js:333-341]` `await headerSearch.fill("RAG"); / await headerSearch.press("Enter"); / await expect(page).toHaveURL(/\/knowledge/); / await expect(page.getByRole("searchbox", { name: /поиск по базе знаний/i })).toHaveValue("RAG");` — preserved by the D-10 field sync.
6. **`web/.env.local` + a stale `5174` listener** — measured: the file exists and carries `VITE_USE_MOCKS=false`; `reuseExistingServer` reuses a manually started server. Mass false failures with no relation to the diff.
7. **Sticky failure flag** `[VERIFIED: web/src/services/knowledgeApi.js:57-64]` `function consumeFailNext() { / if (failNextSearch) { failNextSearch = false; return true } / return typeof window !== 'undefined' && window.__DIGEST_FAIL_NEXT_KNOWLEDGE__ === true / }` — the window flag is **never cleared** by consumption. A test that sets `window.__DIGEST_FAIL_NEXT_KNOWLEDGE__ = true` once makes *every* later search in that document fail until it is reset. (`handleRetry` calls `clearFailNextKnowledgeSearch()`, so the in-page «Повторить» self-heals.) Any error test must reset the flag explicitly before asserting recovery.
8. **Stale rows during a new request** — `runSearch` does not clear `items` at request start (unchanged behaviour), so during an 80 ms flight the previous query's rows are still mounted. C-03 must assert *after* settle; do not tighten this into "rows disappear while loading" (that would be a behaviour change the UI-SPEC does not ask for).
9. **No request cancellation / ordering guard** — two header submits within the flight window produce two overlapping requests and "last write wins" is arbitrary. Out of scope (no abort support in `searchKnowledge`, which is frozen). Note it; do not fix it.
10. **`trackGoal` now fires on load** — `[VERIFIED: web/src/pages/KnowledgePage.jsx:92-96]` `if (!append && q) { … trackGoal(ANALYTICS_GOALS.search, { role: roleValue }) }`. Expected consequence of D-01 (CONTEXT), and the query text is still never sent.
11. **`ANALYTICS` + page views** — `AnalyticsPageViews` fires per location change; the strip's `replace` adds one more render but no page view of a new path (same pathname). No assertion depends on it.
12. **`oxlint`** — `[VERIFIED: web/.oxlintrc.json]` enables only `react/rules-of-hooks` (error) and `react/only-export-components` (warn); `react-hooks/exhaustive-deps` is **not** enabled, so the intentional two-entry dep array needs no disable comment. Do not add one (a stray comment would look like a suppressed defect).
13. **Route-param naming drift** — CONTEXT D-04 and the UI-SPEC write `/materials/:slug`, the actual route is `{ path: 'materials/:id', element: <MaterialPage /> }` (`[VERIFIED: web/src/App.jsx:52]`). It does not affect this phase (the page only needs to *not* be mounted there), but a test must use a concrete URL (`/materials/rag-systems`, as `[VERIFIED: tests/knowledge.spec.js:46]` `await expect(page).toHaveURL(/\/materials\/rag-systems/)`), never the `:slug` literal.
## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.8 (`^19.2.8`) | Component state, the single `useEffect` trigger, refs | Already the app's runtime; StrictMode is on in dev, which is *why* D-03 exists. `[VERIFIED: web/node_modules/react/package.json]` |
| react-dom | 19.2.8 (`^19.2.8`) | `createRoot` + StrictMode wrapper | `[VERIFIED: web/src/main.jsx:109-112]` |
| react-router-dom | 7.18.3 | `useSearchParams` (URL as source of truth), `setSearchParams(..., { replace: true, state: null })`, `useLocation().state` | The repo's only router; `replace`/`state` semantics verified in the installed source, not assumed |
| @playwright/test | 1.62.1 | Behavioural harness: journeys, `addInitScript`, `page.evaluate`, `page.goBack()` | Sole e2e runner (`npm run test:web`), browsers already installed in `.playwright-browsers` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| node:test (`node --test`) | Node 24.21.0 | Static gates that read source text (`tests/unit/*.js`) | The single-call-site guard; no DOM, no bundler, runs in ~1 s |
| tailwindcss | 4.3.3 | Existing utility classes only | When a class must be *kept* byte-identical (R-1 adds no class) |
| oxlint | 1.81.0 | Lint (`web/.oxlintrc.json`) | Sanity check after the effect lands; `rules-of-hooks` is the only error-level rule |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| A page-level counter | `page.route` HTTP interception | **Rejected by evidence**: mocks mode issues no HTTP request (`knowledgeApi.js:121-125`), the assertion would be vacuous. Would also need a second webServer/env and re-opens the `5174` flake |
| A page-level counter | A hook inside `knowledgeApi.js` | **Forbidden**: CONTEXT Out of scope — the adapter must stay byte-identical |
| A ref-of-last-q guard | A boolean `hasSearched` flag | **Rejected by D-03**: it would also block a legitimate `?q` change on a mounted page |
| A ref-of-last-q guard | AbortController cancellation of the first StrictMode invocation | Not possible: `searchKnowledge` accepts no signal and is frozen; the ref is the only synchronously-visible guard |
| Module Map | `sessionStorage` cache | **Deferred/rejected** (D-04): survives F5 and would show stale results as fresh |
| Module Map in the page | Extract a `knowledgeSearchCache.js` module | Cleaner unit-testability, but a new file for ~20 lines and a deviation from Discretion 2's framing. Only worth it if the planner wants a `node:test` proof of the snapshot (see Open Question 2) |

**Installation:** none — this phase adds no package.

**Version verification:** `react` and `react-dom` resolve to `19.2.8`; `react-router-dom` to `7.18.3`; `@playwright/test` and `playwright` to `1.62.1`; `oxlint` to `1.81.0`; `vite` to `8.2.2`; `node v24.21.0` / `npm 11.19.0` on this machine. All read from installed `package.json` files or `--version` this session.

## Package Legitimacy Audit

**No packages are installed by this phase.** No `npm install`, no registry lookup is applicable, and the Package Legitimacy Gate is therefore not triggered.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| *(none)* | — | — | — | — | — | No install in scope |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
                         ┌──────────────────────────────────────────────┐
  header Enter ─────────►│ SearchPill.onSubmit                          │
  (AppShell, any route)  │  q = query.trim()                            │
                         │  q ? navigate('/knowledge?q='+enc(q),        │
                         │               { state: { submitId } })       │
                         │    : navigate('/knowledge')      ← D-08       │
                         └───────────────────┬──────────────────────────┘
                                             │ router push (new history entry)
                                             ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ KnowledgePage (mounts on /knowledge; unmounts on /materials/:id)             │
  │                                                                              │
  │  render:  qUrl   = (searchParams.get('q') ?? '').trim()      ← synchronous    │
  │           submitId = location.state?.submitId ?? null                        │
  │           preSearch = qUrl === '' && !error          ← chips only on landing  │
  │                                                                              │
  │  useEffect [qUrl, submitId]:                                                 │
  │    1. marker?  ──yes──► consumedSubmitIdRef = id                              │
  │                          setSearchParams(same, {replace:true, state:null})    │
  │                          forced = true                                        │
  │    2. validateKnowledgeQuery(qUrl)                                            │
  │         blank    ──► reset to landing, 0 requests, no inline error            │
  │         overlong ──► inlineError = validation.message, 0 requests             │
  │    3. forced? ──yes──► role='all' (D-07) ─────────────────────┐               │
  │    4. lastHandledQueryRef === q ? ──yes──► STOP (no request)  │               │
  │    5. cache.get(lastRoleForQuery(q) ?? role, q)               │               │
  │         hit  ──► restore state, setRole(cachedRole), 0 requests│              │
  │         miss ─────────────────────────────────────────────────┤               │
  │                                                               ▼               │
  │                                    runSearch(q, {offset:0, role})             │
  │                                       lastHandledQueryRef = q (sync)          │
  │                                       searching = true, activeQuery = q       │
  │                                       bump __DIGEST_KNOWLEDGE_SEARCH_COUNT__  │
  │                                       await searchKnowledge(...)  ← mock/delay│
  │                                       ├─ ok    → items/hasMore/nextOffset      │
  │                                       │          cache.set((role,q), snapshot) │
  │                                       └─ error → cache.delete((role,q))        │
  │                                                                              │
  │  render: rows | «Ищем…» (live region, R-1) | zero-hit | error | landing       │
  └──────────────────────────────────────────────────────────────────────────────┘
                                             ▲
    material row click ──push──► /materials/:id (KnowledgePage unmounts)
    browser Back ───────pop───► /knowledge?q=… (remount) ──► step 5 hits the module
                                                           cache → rows instantly,
                                                           0 requests, no spinner
```

### Recommended Project Structure (only files this phase touches)

```
web/src/
├── components/
│   └── SearchPill.jsx          # + submitId payload (D-05); nothing else
├── pages/
│   └── KnowledgePage.jsx       # + module cache, + effect, + refs,
│                               #   + counter, + URL writes, preSearch/R-1
└── services/
    └── knowledgeApi.js         # UNTOUCHED — byte-identical
tests/
├── knowledge.spec.js           # + KNOW-05 describe block (13 cases) + helpers
└── unit/
    └── test_knowledge_search_single_call_site.js   # NEW static gate
```

### Pattern 1: URL-keyed effect with a synchronous "last handled" ref

**What:** the address is the only trigger; the ref makes a repeated resolution of the *same* normalised q a no-op for re-renders, StrictMode and the router's own follow-up navigations.
**When to use:** any "navigate to a URL ⇒ run the work described by that URL" flow in this SPA.

```jsx
// web/src/pages/KnowledgePage.jsx (shape, not the final text)
const [searchParams, setSearchParams] = useSearchParams()
const location = useLocation()
const qUrl = (searchParams.get('q') ?? '').trim()
const submitId = typeof location.state?.submitId === 'string' ? location.state.submitId : null

const [query, setQuery] = useState(qUrl)
const roleRef = useRef(role)
roleRef.current = role
const lastHandledQueryRef = useRef(null)   // normalised q executed or restored by this mount
const consumedSubmitIdRef = useRef(null)   // marker already acted on

useEffect(() => {
  const forced = submitId !== null && submitId !== consumedSubmitIdRef.current
  if (forced) {
    consumedSubmitIdRef.current = submitId
    // one-shot marker: same URL, same params, state cleared (D-05)
    setSearchParams(searchParams, { replace: true, state: null })
  }

  const validation = validateKnowledgeQuery(qUrl)
  if (!validation.ok) {
    const wasShowing = lastHandledQueryRef.current !== null
    lastHandledQueryRef.current = null
    if (wasShowing) {
      setActiveQuery(null)
      setItems([])
      setHasMore(false)
      setNextOffset(0)
      setError(null)
    }
    // D-09: the only copy of «Сократите запрос» comes from the validator
    setInlineError(validation.code === 'QUERY_TOO_LONG' ? validation.message : null)
    return
  }

  const q = validation.q
  if (!forced) {
    if (lastHandledQueryRef.current === q) return
    const intendedRole = lastRoleForQuery.get(q) ?? roleRef.current
    const cached = recallSearchSnapshot(intendedRole, q)
    if (cached) {
      lastHandledQueryRef.current = q
      setRole(intendedRole)
      setActiveQuery(q)
      setItems(cached.items)
      setHasMore(cached.hasMore)
      setNextOffset(cached.nextOffset)
      setError(null)
      setInlineError(null)
      return
    }
  }

  lastHandledQueryRef.current = q
  if (forced) setRole('all')
  setInlineError(null)
  void runSearch(q, { offset: 0, append: false, role: forced ? 'all' : roleRef.current })
  // deps are deliberately [qUrl, submitId] — role changes run their own search
}, [qUrl, submitId])
```

**Deps rationale (write this into the plan so the reviewer does not "fix" it):** `runSearch`, `setSearchParams` and `searchParams` are intentionally omitted; adding them re-runs the effect on every render (both are recreated per render), which is the exact duplicate-fire the phase removes. `role` is read through `roleRef` for the same reason.

### Pattern 2: module-scope snapshot cache with a role side-map

```jsx
// module scope of KnowledgePage.jsx — survives unmount, dies on reload (D-04 / C-11)
const SEARCH_SNAPSHOT_MAX = 20
/** @type {Map<string, {items: object[], hasMore: boolean, nextOffset: number, limit: number}>} */
const searchSnapshots = new Map()
/** @type {Map<string, string>} q → role that produced the last shown rows (C-13) */
const lastRoleForQuery = new Map()

const snapshotKey = (roleValue, q) => `${roleValue}\u0000${q}`

function rememberSearchSnapshot(roleValue, q, snapshot) {
  const key = snapshotKey(roleValue, q)
  if (!searchSnapshots.has(key) && searchSnapshots.size >= SEARCH_SNAPSHOT_MAX) {
    const oldest = searchSnapshots.keys().next().value
    searchSnapshots.delete(oldest)
  }
  searchSnapshots.set(key, snapshot)
  lastRoleForQuery.set(q, roleValue)
}

function recallSearchSnapshot(roleValue, q) {
  return searchSnapshots.get(snapshotKey(roleValue, q)) ?? null
}

function forgetSearchSnapshot(roleValue, q) {
  searchSnapshots.delete(snapshotKey(roleValue, q))
  if (lastRoleForQuery.get(q) === roleValue) lastRoleForQuery.delete(q)
}
```

### Pattern 3: one-shot navigation marker consumed into a ref

**What:** a signal that must be honoured exactly once, must survive a re-render, and must not survive a history replay.
**When to use:** "same URL, but the user asked again" — the only case a URL cannot express.

```jsx
// web/src/components/SearchPill.jsx
let submitSeq = 0                       // module scope: monotonic within a document

function onSubmit(event) {
  event.preventDefault()
  const q = query.trim()
  if (!q) {
    navigate('/knowledge')            // D-08: no ?q, no marker, zero requests
    return
  }
  submitSeq += 1
  navigate(`/knowledge?q=${encodeURIComponent(q)}`, {
    state: { submitId: `submit-${Date.now()}-${submitSeq}` },
  })
}
```

Keep `encodeURIComponent` (`[VERIFIED: web/src/components/SearchPill.jsx:23]` `navigate(q ? \`/knowledge?q=${encodeURIComponent(q)}\` : '/knowledge')`) — normalisation happens on the page, so `%20` vs `+` cannot produce two requests (C-04).

### Pattern 4: instrument at the boundary, assert behaviour outside it

**What:** counters observe the single call site; the *behaviour* assertion is the rendered row.
**When to use:** whenever the transport layer is mocked away (this whole project).

```jsx
// inside runSearch, non-append and append alike
try {
  bumpKnowledgeSearchCount()          // counts attempts, including throws
  const dto = await searchKnowledge({ q, role: roleValue === 'all' ? null : roleValue, limit: DEFAULT_SEARCH_LIMIT, offset })
  // …
```

### Anti-Patterns to Avoid

- **`useEffect(() => { runSearch(qUrl) }, [])`** — passes a deep-link test, then fires twice under StrictMode and never reacts to a `?q` change.
- **`useEffect(..., [qUrl, role, runSearch, searchParams])`** — re-fires on every render; a chip change fires twice.
- **A boolean `hasSearched` state** — blocks legitimate `?q` changes (D-03) and is invisible to the second StrictMode setup.
- **Searching from `SearchPill` and passing results through `location.state`** — duplicates validation/role/limit/error/`trackGoal` (rejected in D-01).
- **`page.route` counting under `VITE_USE_MOCKS=true`** — asserts against zero HTTP calls.
- **Writing the cache inside a `setState` updater** — StrictMode double-invokes updaters.
- **`localStorage`/`sessionStorage`/`maxlength`/`focus()`/`scrollIntoView()`** — all explicitly forbidden by the UI-SPEC/CONTEXT.
- **Clearing `items` at request start** — a behaviour change nobody asked for (the old rows are visible during the 80 ms flight today; C-03 asserts after settle).
- **A new spec file without extending `testMatch`** — it silently never runs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Query normalisation / length guard | A second trim+length check for the `?q` branch | `validateKnowledgeQuery` (`knowledgeApi.js:21-30`) | D-09: one path, one copy of «Сократите запрос» / «Введите запрос». A second copy would drift and the existing literals already exist in two places by design |
| URL rewriting | Manual `window.history.pushState` + `URLSearchParams` juggling | `setSearchParams(next, { replace: true, state: null })` | Verified to forward `replace` and `state` into `navigate` (source quoted above); manual writes desynchronise the router's location and break `useSearchParams` |
| "Same navigation, no-op" detection | Comparing `location.key` yourself | A consumed-marker ref + `lastHandledQueryRef` | The router already gives a new `key` on every navigation, including a `replace` with identical params — key comparison would treat the strip as a new submit |
| Debounce/dedupe of fetch calls | A request-level dedupe layer | The ref guard in the effect | The page has exactly one call site; a dedupe layer would also swallow legitimate D-05 resubmits |
| Retry after a failed search | A new retry loop | Existing `handleRetry` + `clearFailNextKnowledgeSearch` | Already wired, and it self-heals the sticky test flag |
| Snapshot eviction policy | LRU with timestamps | `Map` insertion order, cap 20 | `Map` preserves insertion order; a timestamp LRU is unobservable complexity |

**Key insight:** every mechanism in this phase already has a predecessor in the same file or the same harness idiom. The phase's risk is not "what to build" but "which of the five guards prevents which duplicate".

## Runtime State Inventory

This is a behaviour change (not a rename), but it introduces three pieces of runtime state, so the canonical question — *after every file is updated, what runtime systems still carry state that must be reasoned about?* — is answered explicitly.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None.** No DB, no `localStorage`, no `sessionStorage`, no cookies. The snapshot cache is process memory and is intentionally lost on reload (D-04/C-11) | None — verified by reading `knowledgeApi.js` (no storage) and by the deferred-ideas list |
| Live service config | **None.** Backend, Supabase and the ingestion service are untouched | None |
| OS-registered state | **None** | None |
| Secrets/env vars | `VITE_USE_MOCKS` decides whether `searchKnowledge` hits the network. `web/.env.local` currently sets `VITE_USE_MOCKS=false`; Playwright overrides it to `true` **only for a server it starts itself** | Kill any pre-existing `5174` listener before running the suite (STATE § Blockers). No env change is part of the phase |
| Build artifacts | **None.** No new dependency, no build output change; `vite` dev server is the only artifact | None |
| Transient browser state | `history.state.usr.submitId` (must be stripped — C-15) and the browser's Back stack (each header submit pushes, each in-page search replaces — C-20) | Code edit: the strip in the effect; assertions in the specs |

## Common Pitfalls

Each of these was read out of the real files and the installed `react`/`react-router` sources, not recalled.

### Pitfall 1: StrictMode double effect looks like a double request
**What goes wrong:** a naive `useEffect` fires twice in dev; the counter reads 2 and the whole contract fails.
**Why it happens:** `[VERIFIED: web/src/main.jsx:109-112]` wraps the tree in `<StrictMode>`; React 19 dev mounts, unmounts, remounts effects on the *same* state.
**How to avoid:** set `lastHandledQueryRef.current = q` **before** the `await`, and never reset it in a cleanup. The second setup sees the same q and returns.
**Warning signs:** first run of the journey test shows `2`; prod build shows `1` (i.e. dev-only). A cleanup that resets the ref reproduces the bug.

### Pitfall 2: `runSearch`/`searchParams` in the dependency array
**What goes wrong:** duplicate requests on every chip click, every theme toggle, every keystroke.
**Why it happens:** `runSearch` is a new function identity each render (`KnowledgePage.jsx:70-121`), and `setSearchParams` is likewise per-render (both confirmed as in-repo discrete values above). `searchParams` is a fresh `URLSearchParams` per `useSearchParams()` call.
**How to avoid:** deps `[qUrl, submitId]`; read `role` through `roleRef`. Leave a comment; a well-meaning reviewer "fixing" the deps array will re-break criterion 3.
**Warning signs:** lint does not complain (repo does not run `react-hooks/exhaustive-deps`, `[VERIFIED: web/.oxlintrc.json]` `"plugins": ["react", "react-perf"]` with only `rules-of-hooks` at error), so nothing catches it except the streak assertion.

### Pitfall 3: The counter counts the wrong thing
**What goes wrong:** the counter is bumped inside the `.then`, or after the `if (!res.ok)` early return, or inside a `try/finally` that never runs.
**Why it happens:** "count requests" sounds like "count successes".
**How to avoid:** bump as the **first statement** of the network step in `runSearch`, before `await`. A thrown adapter call must still count — otherwise a duplicate that happens to throw is invisible.
**Warning signs:** criterion 4 (zero) passes while criterion 2 (one) passes for the wrong reason; force a failing search (`armFailNextKnowledgeSearch`) and confirm the counter still incremented.

### Pitfall 4: The counter is vacuous because the page under test is healthy
**What goes wrong:** the assertion `=== 1` passes even if broken, because the page never navigated to the header flow (e.g. the form had a different role, the click missed).
**Why it happens:** Playwright's `getByRole('searchbox')` is forgiving when there are two controls.
**How to avoid:** X-1's own control — the seeded patch (C-21) must read `0`, **and** the counter must be observed at `2` under a deliberately naive mount (or, non-destructively, `page.evaluate` on `/knowledge?q=deep` asserting one bump per mount). Assert `typeof === 'number'` first.
**Warning signs:** a test that "passes" when the header form selector is typo'd.

### Pitfall 5: A new spec file silently never runs
**What goes wrong:** `tests/knowledge-search-submit.spec.js` is created, green locally by hand, and never executed by `npm run test:web`.
**Why it happens:** `[VERIFIED: playwright.config.js:71]` `testMatch: /(web-app|auth|knowledge|razbory|admin(-chrome)?)\.spec\.js/`.
**How to avoid:** put the specs in `tests/knowledge.spec.js` (already matched); if a new file is truly wanted, extend `testMatch` **in the same commit** and prove it with `npx playwright test --list | Select-String`.
**Warning signs:** total test count unchanged after adding a file.

### Pitfall 6: Typing into a disabled field
**What goes wrong:** the header submit happens while `searching` is true (from a previous auto-run), so the field is disabled, the fill silently no-ops or the click times out; a second request never happens and the retry test flakes.
**Why it happens:** `[VERIFIED: web/src/pages/KnowledgePage.jsx:239]` `<input … disabled={searching} />` on `#kb-search`.
**How to avoid:** in tests, wait for the first batch to settle (rows visible or live region hidden) before submitting again; in prod code do not touch `disabled`.
**Warning signs:** `element is not enabled` timeouts, more often under the 80 ms mock delay on a loaded machine.

### Pitfall 7: A fresh listener turns the suite red for environmental reasons
**What goes wrong:** `EADDRINUSE :5174` or the app loading real data.
**Why it happens:** STATE § Blockers — a stale `5174` listener owns the port, and Playwright's `reuseExistingServer: true` means the already-running dev server (started with `VITE_USE_MOCKS=false` from `web/.env.local`) wins, so mocks are off.
**How to avoid:** document a pre-flight in the plan: check `5174`, kill the foreign PID, then `npx playwright test --project=web tests/knowledge.spec.js`.
**Warning signs:** results full of real titles, or 5xx from a backend that is not running.

### Pitfall 8: The `toHaveValue("RAG")` pin breaks for the wrong reason
**What goes wrong:** after the auto-run, `tests/web-app.spec.js:341` asserts the input holds `RAG`; if the effect seeds `query` from something other than the normalised URL, or the user-visible field is reset, it fails and looks like a regression.
**Why it happens:** C-17 freezes that assertion.
**How to avoid:** keep `useState(qUrl)` as the initial value and never overwrite `query` from the effect; the contract is "don't touch the field".
**Warning signs:** the failure appears only through the header path, not the in-page path.

### Pitfall 9: Cache poisoning hides a real duplicate
**What goes wrong:** the StrictMode second setup finds a cache hit and shows rows, so the "second request" never happens — but the module was still entered twice and any later change re-introduces the duplicate invisibly.
**Why it happens:** the cache and the ref both suppress the second setup; the cache does it *later* in the flow.
**How to avoid:** the ref check must precede the cache check (ordering matters for diagnosis), and criterion 2 must be proven by the `2 → 1` control, not by observing "rows appeared".
**Warning signs:** the counter is only ever asserted on a warm page.

### Pitfall 10: `error` shadows the global and the live region disappears
**What goes wrong:** the K.M final rule `searching || (activeQuery !== null && !error)` is implemented as `!Boolean(error)` but the component also uses `error` for a URL-level failure; the «Ищем…» region never renders.
**Why it happens:** the same identifier carries two meanings (request error vs validation error).
**How to avoid:** keep `error` strictly for request failures; validation lives in `inlineError` (D-09 separation, already the repo's split).
**Warning signs:** query A then query B — region text goes `null` instead of `"Ищем…"`.

### Pitfall 11: Back after a material click re-requests
**What goes wrong:** criterion 6 fails with 2 requests where 1 was expected (+1 per Back).
**Why it happens:** `KnowledgePage` unmounts on `/materials/:id` `[VERIFIED: web/src/App.jsx:51-52]` `{ path: 'knowledge', element: <KnowledgePage /> }, / { path: 'materials/:id', element: <MaterialPage /> },`, so the ref is gone; only the module cache can answer.
**How to avoid:** cache keyed by `(normalised q, role)` **and** the `lastRoleForQuery` side-map, since `role` resets to `'all'` on remount (C-13).
**Warning signs:** the streak test passes but the Back test increments.

### Pitfall 12: Caching a partial (append) page breaks «Показать ещё»
**What goes wrong:** after «Показать ещё», Back restores only the first page but `nextOffset` says otherwise, so paging jumps or repeats rows.
**Why it happens:** `runSearch` is shared by both paths (X-3).
**How to avoid:** only `rememberSearchSnapshot` when `append === false`; a fresher `(role,q)` snapshot legitimately replaces an older one (C-12 "regression" direction only).
**Warning signs:** duplicate keys / a React list warning after Back.

### Pitfall 13: `submitId` replayed on Back
**What goes wrong:** pressing Back to a URL that still carries the marker triggers another request, or worse, the strip itself pushes a history entry so Back re-enters the page.
**Why it happens:** `location.state` survives in the history entry until replaced.
**How to avoid:** strip with `replace: true`, `state: null`, and keep `consumedSubmitIdRef` for the current mount; assert `evaluate(() => window.history.state?.usr)`.
**Warning signs:** Back count increments; `history.state.usr` non-null in a test dump.

### Pitfall 14: `inlineError` assertions become brittle
**What goes wrong:** the overlong test hunts an unknown literal.
**Why it happens:** the message is generated by the adapter (`knowledgeApi.js:21-30`).
**How to avoid:** pin the exact strings — `[VERIFIED: web/src/services/knowledgeApi.js:24]` `return { ok: false, code: 'EMPTY_QUERY', message: 'Введите запрос' }` and `[VERIFIED: web/src/services/knowledgeApi.js:27]` `return { ok: false, code: 'QUERY_TOO_LONG', message: 'Сократите запрос' }` — and assert the guard element is visible/absent, not a partial match. Note the threshold is **500 code points**, not 200: `[VERIFIED: web/src/services/knowledgeApi.js:14]` `export const MAX_QUERY_CODE_POINTS = 500`, and there is **no** "до N символов" suffix in the message.
**Warning signs:** `getByText(/200/)` passing on unrelated text.

## Code Examples

### Harness helpers (test-file scope, added once to `tests/knowledge.spec.js`)

```js
// Source: existing idioms in the repo — tests/knowledge.spec.js:1 (CommonJS requires),
// tests/admin-chrome.spec.js:199-241 (browser probes), playwright.config.js:71 (testMatch).
// Playwright 1.62.1; the spec file is CommonJS (root package.json has no "type": "module").
const { expect } = require("@playwright/test");

const SEARCH_COUNT = "__DIGEST_KNOWLEDGE_SEARCH_COUNT__";

// C-18: installs BEFORE the first script, survives reload/Back (same document on SPA pop)
async function installKnowledgeCounter(page) {
  await page.addInitScript(() => {
    const KEY = "__DIGEST_KNOWLEDGE_SEARCH_COUNT__";
    window[KEY] = 0;
    window.__DIGEST_KNOWLEDGE_SEARCH_META__ = [];
    Object.defineProperty(window, "__resetKnowledgeSearchCount", {
      value: () => {
        window[KEY] = 0;
        window.__DIGEST_KNOWLEDGE_SEARCH_META__ = [];
      },
      configurable: true,
    });
  });
}

const readCount = (page) =>
  page.evaluate((k) => {
    const value = window[k];
    if (typeof value !== "number") throw new Error("knowledge search counter not installed");
    return value;
  }, SEARCH_COUNT);

async function expectCount(page, n, label) {
  await expect
    .poll(() => readCount(page), { timeout: 4000, message: label })
    .toBe(n);
}

// The real row selector: hits are anchors rendered by MaterialListRow inside
// KnowledgeHitList (KnowledgePage.jsx:383-387) — there is no `kb-result-row` testid.
const hitLinks = (page) => page.locator('a[href^="/materials/"]');
const rowByTitle = (page, title) => page.getByRole("link", { name: title });

// X-2 collector: MutationObserver + synchronous seed; records only observed states
async function installAffordanceCollector(page) {
  await page.addInitScript(() => {
    const log = [];
    window.__KB_AFFORDANCE_LOG__ = log;

    const scan = () => {
      // 1) the «Найти» ActionButton carries data-state="loading" while searching
      //    (KnowledgePage.jsx:245-248 + ActionButton.jsx:51-53). NOT the skeleton:
      //    kb-skeleton only renders on the append path (loadingMore), which is
      //    unreachable in mocks because has_more is always false.
      if (document.querySelector('[data-state="loading"]')) log.push("loading-state");
      // 2) the page form's input is `disabled` while searching (KnowledgePage.jsx:239)
      const input = document.querySelector("#kb-search");
      if (input && input.disabled) log.push("field-disabled");
      // 3) the ONLY live region is `p[aria-live="polite"]` in KnowledgeResults
      //    (KnowledgePage.jsx:348-351) and it has NO testid — select by the attribute.
      const live = document.querySelector('p[aria-live="polite"]');
      if (live && (live.textContent ?? "").includes("Ищем")) log.push("live-searching");
    };

    scan(); // synchronous seed — catches post-settle revisits

    const observer = new MutationObserver(() => scan());
    observer.observe(document.documentElement, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
      attributeFilter: ["disabled", "aria-busy", "data-state", "class"],
    });
  });
}

const affordanceLog = (page) => page.evaluate(() => window.__KB_AFFORDANCE_LOG__);
```

**Two facts this collector depends on, both measured:** the live region is `<p className="mb-4 text-xs text-text-secondary" aria-live="polite">` with **no** `data-testid` (`[VERIFIED: web/src/pages/KnowledgePage.jsx:348-351]`), and its text comes from `knowledgeResultSummary` → `'Ищем…'` / `'Найдено 0 материалов'` / `Показано N` (`[VERIFIED: web/src/pages/KnowledgePage.jsx:296-301]`). Do not invent `kb-results-status`; if a testid is added, it is a new node-level change the UI-SPEC does not authorise.

### Verified selectors — use these exact ones, there are **two** searchboxes on `/knowledge`

Both are `type="search"` ⇒ role `searchbox`. A bare `getByRole('searchbox')` throws a strict-mode violation on `/knowledge`; always name them.

| Thing | Selector | Source of truth (read this session) |
|-------|----------|-------------------------------------|
| Header pill input | `page.getByRole('searchbox', { name: /поиск digest cds/i })` | `[VERIFIED: web/src/components/SearchPill.jsx:35-36]` `<label htmlFor={inputId} className="sr-only"> / Поиск Digest CDS` |
| Page form input | `page.getByRole('searchbox', { name: /поиск по базе знаний/i })` | `[VERIFIED: web/src/pages/KnowledgePage.jsx:226-231]` `<label className="sr-only" htmlFor="kb-search"> / Поиск по базе знаний` + `id="kb-search"` |
| Hit rows | `page.locator('a[href^="/materials/"]')`, or `page.getByRole('link', { name: /building production rag systems/i })` | `[VERIFIED: web/src/pages/KnowledgePage.jsx:383-387]` `{items.map((hit) => ( / <MaterialListRow key={hit.slug} material={hit} section="base" />` — the row is a link, there is **no** `kb-result-row` testid |
| Hint chips (landing) | `page.getByTestId('kb-hint-chips')` | `[VERIFIED: web/src/pages/KnowledgePage.jsx:320]` |
| Inline validation | `page.getByTestId('kb-inline-error')` (`role="alert"`) | `[VERIFIED: web/src/pages/KnowledgePage.jsx:256-260]` |
| Network error panel | `page.getByTestId('kb-search-error')` + «Повторить» | `[VERIFIED: web/src/pages/KnowledgePage.jsx:337-343]` |
| Status/live region | `page.locator('p[aria-live="polite"]')` (**no testid**) | `[VERIFIED: web/src/pages/KnowledgePage.jsx:348-351]` |
| «Найти» | `page.getByRole('button', { name: 'Найти', exact: true })` | `[VERIFIED: web/src/pages/KnowledgePage.jsx:245-252]` |
| Role chips | `page.getByRole('button', { name: 'DS', exact: true })` / `'Analyst'` | existing `tests/knowledge.spec.js:41,53` |

### Counter instrumentation inside the page

```jsx
// web/src/pages/KnowledgePage.jsx — module scope, next to the constants
const SEARCH_COUNT_KEY = '__DIGEST_KNOWLEDGE_SEARCH_COUNT__'

function bumpKnowledgeSearchCount(meta) {
  const host = typeof window === 'undefined' ? null : window
  if (!host) return
  const current = host[SEARCH_COUNT_KEY]
  host[SEARCH_COUNT_KEY] = (typeof current === 'number' ? current : 0) + 1
  const log = host.__DIGEST_KNOWLEDGE_SEARCH_META__
  if (Array.isArray(log)) log.push(meta)
}
```

### Static single-call-site gate

```js
// tests/unit/test_knowledge_search_single_call_site.js
// Discovery: scripts/run-unit-js.cjs — flat readdirSync of tests/unit/*.js, so the file is
// picked up with no config change. The repo's unit tests are CommonJS (root package.json
// has no "type": "module"); `npm run test:js` runs this, NOT `npm run test:unit`
// (which is `uv run pytest`).
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { readdirSync, readFileSync } = require('node:fs')
const path = require('node:path')

const ROOT = path.resolve(__dirname, '../..')
const SRC = path.join(ROOT, 'web/src')

function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) return walk(full)
    return /\.(js|jsx|mjs)$/.test(entry.name) ? [full] : []
  })
}

test('exactly one import of searchKnowledge', () => {
  const files = walk(SRC)
  assert.ok(files.length > 20, `walker found only ${files.length} files — path is wrong`)
  const hits = files.filter((file) =>
    /import\s*\{[^}]*\bsearchKnowledge\b[^}]*\}\s*from\s*['"][^'"]*knowledgeApi['"]/.test(
      readFileSync(file, 'utf8'),
    ),
  )
  assert.equal(hits.length, 1, `expected 1 import, found ${hits.length}: ${hits.join(', ')}`)
})
```

### `knowledgeApi.js` snapshot pin (C-24, structural — see Open Question 1)

```js
// tests/unit/test_knowledge_api_snapshot.js — recommended (Open Question 1)
const { test } = require('node:test')
const assert = require('node:assert/strict')
const { readFileSync } = require('node:fs')
const { createHash } = require('node:crypto')
const path = require('node:path')

const API_PATH = path.resolve(__dirname, '../../web/src/services/knowledgeApi.js')
const FROZEN_SHA256 = '<captured in Wave 0, before any edit>'

test('knowledgeApi.js is byte-identical to the frozen snapshot', () => {
  const digest = createHash('sha256').update(readFileSync(API_PATH)).digest('hex')
  assert.equal(digest, FROZEN_SHA256)
})
```

> The literal digest **must be captured in Wave 0 from the pre-edit file** and committed in the same task; a hardcoded digest written after the fact proves nothing.

### Mock-mode catalogue (the numbers the tests can rely on)

There is **no** `mockApi.js`: the mock search lives in the adapter itself. `[VERIFIED: web/src/services/knowledgeApi.js:71-105]` `export function mockSearchKnowledge(` … `const page = matched.slice(offset, offset + limit)` … `const has_more = matched.length > offset + limit` — and the catalogue is `[VERIFIED: web/src/services/knowledgeApi.js:9]` `import { materials } from '../data/mock.js'`.

Measured this session by importing the real modules in Node (`node --input-type=module`, `limit: 10`, `offset: 0`):

| Query | role | rows | has_more | titles |
|-------|------|------|----------|--------|
| `RAG` | `null` | 2 | false | Building Production RAG Systems · pgvector for Enterprise Search |
| `RAG` | `ds` | 2 | false | same two |
| `SQL` | `null` | 5 | false | Anomaly Detection in Audit Pipelines · pgvector… · Prompt Engineering Patterns 2026 · SQL-дашборды… · Заметки аналитика по SQL-проверкам |
| `SQL` | `ds` | 1 | false | pgvector for Enterprise Search |
| `zzzz` | `null` | 0 | false | — (the zero-hit fixture) |
| `<img src=x onerror=alert(1)>` | `null` | 0 | false | — (tokenises to nothing that matches) |
| `"   "` | `null` | 8 | false | whole catalogue — **but the page never reaches the mock for blank** (the validator returns first) |

Facts to build assertions on:
- `[VERIFIED: node import of web/src/data/mock.js]` catalogue size is `8`.
- `[VERIFIED: web/src/services/knowledgeApi.js:11]` `export const DEFAULT_SEARCH_LIMIT = 10` — larger than 8, so `has_more` is **never** true in mocks mode. Never assert «Показать ещё» via the mock; see Open Question 4.
- `SQL` is the discriminating fixture for C-13 (5 rows under `all`, 1 under `ds`); `RAG` is **not** (2 either way).
- The XSS probe query yields **0 rows**, so a "renders the literal string" assertion is impossible — assert instead that the field keeps the text, no dialog fires, and the zero-hit state renders (see Security Domain).

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Landing page + second «Найти» click | URL is the trigger; the page resolves itself on mount | this phase (D-01) | one navigation, one request |
| Effect-driven fetch with `eslint-disable` | `useEffect` + synchronous ref-of-last-key + budgeted deps | Stable pattern; StrictMode since React 18 dev | the first StrictMode setup must be idempotent for the whole block |
| Hand-written history juggling | `setSearchParams(params, { replace: true, state: null })` | react-router 6.4+ data APIs | no file exists in this repo writing `window.history` — none should appear now |
| Counting requests via `page.route` | Counting the call site (transport is mocked) | this repo's `VITE_USE_MOCKS` setup | the assertion must be installable from `addInitScript` |
| `sessionStorage` cache | module-level `Map`, lost on reload | D-04 | F5 always hits the API |

**Deprecated/outdated in this repo:**
- `preSearchLanding` as a *concept* — the variable is replaced by `qUrl === ''`, but the header keeps its name `kb-hint-chips` and its «подсказки» meaning (C-19).
- `error` as a "no results" signal — the empty state is `activeQuery`-driven (C-05).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Stripping the marker via `setSearchParams(searchParams, { replace: true, state: null })` keeps identical query params and does not trigger a second effect run | Findings 1–2, Pattern 1 | A duplicate request per submit — criterion 2 fails permanently; fallback: a `navigate(location.pathname + location.search, { replace: true, state: null })` call |
| A2 | An identical-params navigation is a no-op for React Router (the `?q` string and `qUrl` are unchanged), so the strip does not re-enter the effect body with a different value | Pattern 1 | Same as A1 |
| A3 | `role` reads through `roleRef` are enough to make the effect deps `[qUrl, submitId]` safe (no stale-role request) | Pattern 1 | A chip change could search with the previous role; the chip's own handler passes `role` explicitly, so the effect is not the only path |
| A4 | There is exactly one call site of `searchKnowledge` in `web/src` today, and it stays at one | X-1 gate | If a second legit call site appears, the static gate must become a whitelist rather than a count |
| A5 | Mock delay (80 ms) is long enough for the collector to observe the live state after the effect runs | X-2 | Only the live-search interval would be missed; `loading` flips synchronously with `searching` |
| A6 | `history.length` observations (≤ +2 per submit) are stable in Chromium under Playwright's context | C-20 increment tests | A brittle assertion; fallback is asserting `history.state.usr` transitions instead of the length delta |
| A7 | The `(role, q)`-keyed cache with a 20-entry cap cannot evict the entry the tests rely on (≤ 6 entries used) | Discretion 4 | Eviction on a tight sequence; fallback is asserting order-insensitively or raising the cap |
| A8 | A committed sha256 pin of `knowledgeApi.js` is acceptable to the planner as the C-24 evidence | C-24 | C-24 would be evidenced only by review/diff rather than a test |

## Open Questions (RESOLVED)

1. **How is C-24 ("`knowledgeApi.js` byte-identical") mechanised?**
   - What we know: no static pin exists; the ROADMAP/notes say "must stay byte-identical", the UI-SPEC says "evidenced by a hash/diff check, not by inspection"; the JS unit runner auto-discovers `tests/unit/*.js` (quoted above).
   - What's unclear: whether a committed hash literal is palatable (it looks like an unexplained constant) versus a review-only diff gate.
   - -> RESOLVED: ship `tests/unit/test_knowledge_api_snapshot.js` with a sha256 captured **in Wave 0 from the unmodified file** (X-1's prerequisite), and add a one-line comment explaining the phase + rule. Cheap, non-vacuous (an edit fails it), and runs in <1 s. Adopted by `27-01-PLAN.md` Task 1.

2. **Should the cache be a separate module?**
   - What we know: Discretion 2 frames it as "module level (in KnowledgePage.jsx or a new small module)".
   - What's unclear: whether a `node:test` proof of the snapshot shape is wanted (a pure module could be imported in JS only if it is dependency-free `.js`; `KnowledgePage.jsx` cannot be imported by `node --test` without a transform).
   - -> RESOLVED: keep it in `KnowledgePage.jsx` (module scope, no new file); the shape is proven behaviourally by the restore case. No new module, no direct unit test of the cache. Adopted by `27-03-PLAN.md` Task 1.

3. **C-20 says "at most one new entry" — is `push` on a header submit to the *same* visible URL counted?**
   - What we know: navigating to an identical URL with a different `state` still pushes a history entry (the URL string is identical, the state differs).
   - What's unclear: whether the assertion should be on `history.length` delta ≤ 2 (push + one internal) or on the *number of pushes triggered by the submit*, which is exactly 1.
   - -> RESOLVED: assert the observable contract instead of a `history.length` count — both submit paths use `replace`, so `page.goBack()` must leave `/knowledge` and the exact destination is never asserted (browser history is browser-dependent). Adopted by `27-05-PLAN.md` Task 1 case (a).

4. **How should C-12 («Показать ещё» + one extra batch) be tested with only 8 mock rows and a limit of 10?**
   - What we know: `has_more` cannot be true in mocks mode; a query-limited subset is the only way to shrink a page, and the page passes a constant `limit`.
   - What's unclear: whether the planner will accept a descoped assertion.
   - -> RESOLVED: descope the paging *behaviour* e2e to "snapshot restored: same rows, same order, no request"; store `hasMore`/`nextOffset` in the snapshot but write no assertion that cannot fail, and record the `nextOffset`-resume as manual-only in `27-VALIDATION.md`. Do **not** invent a mock query that returns 3 rows. Adopted by `27-03-PLAN.md` (deviation 1) and `27-VALIDATION.md` § Manual-Only Verifications.

5. **Does `submitId` need to survive a reload?**
   - -> RESOLVED: no (D-05 says one-shot; C-15 says no replay). The strip makes it structurally impossible; no storage is needed. Stated so the planner does not add `sessionStorage`. Adopted by `27-03-PLAN.md` Task 2.

6. **Are there existing tests that assert the *old* behaviour and must be updated RED-first?**
   - What we know: no test asserts "no results on deep-link" or "two-step search"; `tests/knowledge.spec.js` drives the in-page form only.
   - -> RESOLVED: none need updating; treat every existing knowledge/web-app case as the regression gate (they are run after every task in 27-02…05). If one flips, that is a finding, not a permission to edit the old test.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | vite, Playwright, `node --test` | ✓ | v24.21.0 | — |
| npm | scripts | ✓ | 11.19.0 | — |
| Chromium (Playwright) | all journey specs | ✓ | local `.playwright-browsers` (PATH set in `npm run test:web:env`) | — |
| `web/node_modules` | running the app | ✓ | installed (`react-router-dom` 7.18.3 present) | `npm ci` |
| Port `5174` | the dev server | ⚠ conditionally | — | **must be free**; a stale listener serves real data and turns mocks off (STATE § Blockers) |
| `VITE_USE_MOCKS` | determinism | ✓ (Playwright forces `"true"`, `[VERIFIED: playwright.config.js:50-53]`) | — | do not rely on `web/.env.local` (`VITE_USE_MOCKS=false`) |
| Backend / Supabase | — | ✗ (not needed) | — | none needed: this phase is frontend-only with mocks |
| `gsd-tools.cjs` | unit runner discovery | ✓ | `gsd/scripts/run-unit-js.cjs` | `node --test tests/unit/*.js` directly |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** backend/Supabase (fallback: mocks); a busy `5174` (fallback: kill the foreign PID).

## Proposed TDD Slice Order (RED → GREEN)

Every slice is one commit: failing test → minimal production change → full suite. The order leads with the tracer so the counter instrument exists before any assertion depends on it.

| # | Slice | RED (failing first) | Command | GREEN (minimal) |
|---|-------|---------------------|---------|-----------------|
| 0 | Freeze the adapter | `tests/unit/test_knowledge_api_snapshot.js` with the pre-edit digest | `npm run test:js` | no production change — the digest is captured, not written |
| 1 | Tracer: submit ⇒ results | header journey: type `RAG`, Enter, `rowByTitle(page, /building production rag systems/i)` visible, `toHaveURL(/q=RAG/)`, `#kb-search` `toHaveValue('RAG')` | `npx playwright test --project=web tests/knowledge.spec.js -g "header submit"` | install the counter + `useEffect([qUrl])` + `lastHandledQueryRef` + move `activeQuery` to request start |
| 2 | Counter non-vacuity + exactly one | `expectCount(0)` before submit (C-21), `expectCount(1)` after settle, repeated after theme toggle + chip change + blur (streak) | same `-g` | (no new code; the assertions must already pass — if they fail, the ref placement is wrong) |
| 3 | Static single call site | `tests/unit/test_knowledge_search_single_call_site.js` | `npm run test:js` | none if already true |
| 4 | Cache: Back + remount | click a row → `goBack()` → rows restored, `expectCount` unchanged; then a second header submit to a *different* q → `expectCount` +1 | `-g "back"` | module `Map` + `recallSearchSnapshot` + `lastRoleForQuery` |
| 5 | `submitId` one-shot | same query twice ⇒ second is `+1`; after settle `evaluate(() => location.pathname + location.search + JSON.stringify(window.history.state?.usr ?? null))` shows no `submitId` | `-g "resubmit"` | `SearchPill` marker + effect strip with `replace` |
| 6 | Whitespace / blank | whitespace submit ⇒ `/knowledge` (no `?q`), `expectCount(0)`, no results rows, hint chips visible; `/knowledge?q=%20%20` ⇒ same | `-g "blank"` | the `qUrl`-empty branch (guard remains) |
| 7 | Overlong | 501-code-point submit ⇒ `«Сократите запрос»` visible (`role="alert"`, `kb-inline-error`), field keeps the **whole** text (length assertion, not prefix), `expectCount(0)`, no rows, no `kb-hint-chips` | `-g "overlong"` | validator branch reusing `validateKnowledgeQuery(...).message` |
| 8 | Landing rule + R-1 | fresh `/knowledge` ⇒ chips visible, no rows; after submit ⇒ chips gone, and a transition streak shows `Ищем…` while a previous q was visible | `-g "landing\|region"` | `preSearch = qUrl === '' && !error`; live region gate `searching \|\| (activeQuery !== null && !error)` |
| 9 | Affordance collector + zero-hit | collector installed; asserts `loading-state`/`field-disabled` ≥ 1 and `live-searching` ≥ 1 where `searching` is observable; repeat after SPA Back; plus a zero-hit submission showing `«Ничего не найдено…»` with no request after | `-g "affordance\|zero"` | none — assertions on existing behaviour |
| 10 | History discipline | header submit ⇒ `history.length` +1; one in-page search (chip) ⇒ +1 but no extra; strip ⇒ no delta | `-g "history"` | ensure `runSearch(append:false)` uses `replace`, `handleSubmit` uses `push` |
| 11 | Error path | `armFailNextKnowledgeSearch()` ⇒ error visible, counters sane, retry works and the sticky flag is cleared | `-g "error"` | none (already wired) |

**Slice rules for the planner:**
- Slice 1 must be a *single* journey (header → row), not a suite of five. It is the tracer.
- Slices 2, 9 and 10 are assertion-only (no production code) — they are the "vacuous-test traps" and must fail loudly if the instrument is wrong; if such a slice is green on the first run, prove it can fail by temporarily breaking the page (then revert).
- Never make slice 5 reuse slice 4's `q`; a cache hit would mask the resubmission.
- `npm run test:js` and `npx playwright test --project=web tests/knowledge.spec.js` are the two per-commit commands; `npm run test:web` is the per-wave gate.

## Validation Architecture

`workflow.nyquist_validation: true` — the map below is what generates `27-VALIDATION.md`.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | `@playwright/test` 1.62.1 (journeys) + `node:test` v24.21.0 (static gates) |
| Config file | `playwright.config.js` (root); `scripts/run-unit-js.cjs` (unit discovery) |
| Quick run command | `npx playwright test --project=web tests/knowledge.spec.js -g "<slice>"` |
| Full suite command | `npm run test:web` (Chromium, `VITE_USE_MOCKS=true`) + `npm run test:js` |

> **Script names are a trap.** `[VERIFIED: package.json scripts]` `"test:js": "node scripts/run-unit-js.cjs"`, `"test:web": "playwright test --project=web"`, `"test": "playwright test"`, and **`"test:unit": "uv run pytest"`** — the Python suite. The JS unit gates in this phase run under `npm run test:js`; using `npm run test:unit` would run pytest and prove nothing (and vice versa).

### Success criteria → validation

| # | Criterion | Validated behaviour | Observable signal (= the assertion) | Command | What would make it vacuous |
|---|-----------|--------------------|-------------------------------------|---------|----------------------------|
| 1 | Enter ⇒ results rendered, no second click | Header form submit drives a real search | `await expect(rowByTitle(page, /building production rag systems/i)).toBeVisible()`; `await expect(hitLinks(page).first()).toBeVisible()`; `toHaveURL(/\/knowledge\?q=RAG/)`; `#kb-search` `toHaveValue('RAG')`; «Найти» never clicked | `npx playwright test --project=web tests/knowledge.spec.js -g "header submit"` | A static row rendered regardless of the query (e.g. a hardcoded list) — the assertion must also show a row whose title contains the query term, and the `zzzz` zero-hit case must show none |
| 2 | Exactly one request per submission | The single call site is entered once, including StrictMode | `expectCount(0)` pre-submit, `expectCount(1)` after; then +0 after theme toggle, chip change, blur | `-g "single request"` | Passing because the counter was never installed (`typeof !== 'number'` must throw), or because the page never navigated (the `0` seed would then also pass — hence the seed + the `1` are both required) |
| 2b | Instrument non-vacuity | The counter *can* read 2 | A deliberately naive mount (or `/knowledge?q=` deep link through two setups) yields `2`, asserted once in a dedicated test | `-g "counter non-vacuity"` | Asserting only "some number" — must be a literal `2` then `1` |
| 3 | No extra request on re-render; Back/Forward no re-issue | Guards are effect-local, cache survives unmount | Count +0 across a streak; `goBack()` restores ≥ N rows with +0; `goForward()` +0 | `-g "streak\|back"` | Asserting counts on a page whose search never resolved (a timeout would make "no change" true) — always assert the settled rows *and* the count |
| 4 | Whitespace ⇒ landing, zero requests, guard visible | The blank branch returns before the network | `toHaveURL(/\/knowledge$/)` (no `q`), `expectCount(0)`, `await expect(hitLinks(page)).toHaveCount(0)`, `getByTestId('kb-hint-chips')` visible | `-g "blank"` | Asserting zero on a page that crashed before mounting — the hint chips + the seeded `/knowledge?q=%20` variant prove the page is alive |
| 5 | Marked navigation consumed once, stripped | `submitId` is a one-shot signal | same q twice ⇒ +1; after settle `window.history.state?.usr` has no `submitId`; Back to that entry does not re-fire | `-g "resubmit\|strip"` | Reusing a different q (cache hit) — the test must use the *same* q and assert the counter, not the rows |
| 6 | In-page search stays `replace`; landing `push` | History discipline, no stale entry | `history.length` deltas: +1 on header submit, +1 on one in-page search, 0 on strip; Back from the header landing ⇒ previous page | `-g "history"` | Reading `history.length` before the SPA has finished its own initial navigation — capture after `waitForLoadState('networkidle')` |
| 7 | Affordance evidence | A loading state was actually rendered | Collector log contains ≥1 `loading-state`, ≥1 `field-disabled`, ≥1 `live-searching` (where `searching` is true); synchronous seed makes a revisit non-vacuous | `-g "affordance"` | An 80 ms window could be missed → the collector must be installed by `addInitScript`; and "≥1" must be proven by first showing a run where the list is empty (collector disabled) |
| 8 | Adapter untouched | `knowledgeApi.js` byte-identical | sha256 pin equals the Wave-0 digest | `npm run test:js` | A digest captured *after* an accidental edit — capture in slice 0 |
| 9 | Single call site | No second bypass of the counter | Exactly one `searchKnowledge` import in `web/src/**` | `npm run test:js` | A regex that matches a comment only — assert `hits.length === 1` **and** print the path |

### Sampling rate

- **Per task commit:** the slice's `-g` command (or `npm run test:js` for slices 0/3/8).
- **Per wave merge:** `npx playwright test --project=web tests/knowledge.spec.js tests/web-app.spec.js` + `npm run test:js`.
- **Phase gate:** `npm run test:web && npm run test:js` green, with a fresh `5174` server.

### Wave 0 gaps

- [ ] `tests/unit/test_knowledge_api_snapshot.js` — NEW; captures the pre-edit `knowledgeApi.js` digest (C-24 evidence). **Must be authored in slice 0, before any page edit.**
- [ ] `tests/unit/test_knowledge_search_single_call_site.js` — NEW; auto-discovered by `scripts/run-unit-js.cjs` (verified flat glob of `tests/unit/*.js`).
- [ ] `tests/knowledge.spec.js` — the counter/collector helpers and the KNOW-05 cases; no new file, therefore **no `testMatch` change**.
- [ ] No framework install; no fixture shared with other specs (helpers are local to the file).
- [ ] Pre-flight: assert `5174` is free before the first Playwright run (STATE § Blockers).

## Security Domain

Frontend-only, no auth, no new surface. `security_enforcement` is not disabled in `.planning/config.json`, so the section is included.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth in the header search path) |
| V3 Session Management | no | — (no session writes; one-shot marker is `history.state` only) |
| V4 Access Control | no | — (search is public; role/`role` mapping is display filtering, not authorization) |
| V5 Input Validation | **yes** | Reuse `validateKnowledgeQuery` (`knowledgeApi.js:21-30`) at the single page boundary; trim + `MAX_QUERY_CODE_POINTS = 500` cap; `encodeURIComponent` in `SearchPill`; never `maxlength` on the input (UI-SPEC forbids, and it would hide the error) |
| V6 Cryptography | no | — (a sha256 test pin is a build check, not a security control; `node:crypto` is used) |

### Known threat patterns for React + react-router + a mocked adapter

| Pattern | STRIDE | Standard mitigation |
|---------|--------|---------------------|
| Reflected script injection via `?q` (e.g. `q=<img onerror>`, `q=javascript:`) | Tampering / XSS | React escapes text children; the query is only ever a text node inside a row/hint. **Do not** introduce `dangerouslySetInnerHTML`, `innerHTML` or `document.title = q`. Add one test: submit `q=<img src=x onerror=alert(1)>` — measured to match **0** rows, so assert `#kb-search` keeps the literal text, the zero-hit state renders, and no dialog fires |
| Open redirect / navigation injection via the marker | Tampering | `submitId` is only compared for equality and stripped — it is **never** used as a URL, a selector or a `location.href`. Do not store arbitrary `location.state` into `window.location` |
| Client-side denial via an enormous query | DoS (client) | The 200-char validator runs before the request; the effect must validate before invoking `searchKnowledge` so no oversized body is ever built |
| Log/PII leakage | Information disclosure | Do not log the raw query to the console; `trackGoal('search_submitted', …)` (if used) must follow the existing call's shape — check `trackGoal` payload conventions before adding fields |
| Cache leak across users | Information disclosure | The module cache is per page session (per browser tab), never written to storage; no cross-user exposure. Do not add persistence |
| Prototype-pollution via the cache key | Tampering | The key is a `string` from `JSON`-safe values (`role + '\u0000' + q`); never use a plain object keyed by user input |

## Sources

### Primary (HIGH confidence)
- **In-repo source of truth, read this session:** `web/src/services/knowledgeApi.js` (fully, incl. `:9`, `:11`, `:14`, `:21-30`, `:45-64`, `:71-105`, `:111-127`), `web/src/data/mock.js` (imported and measured in Node), `web/src/pages/KnowledgePage.jsx`, `web/src/components/SearchPill.jsx`, `web/src/App.jsx`, `web/src/main.jsx`, `playwright.config.js`, `tests/web-app.spec.js`, `tests/knowledge.spec.js`, `scripts/run-unit-js.cjs`, `web/.oxlintrc.json`
- **Installed dependency sources (authoritative for behaviour):** `react-router` 7.18.3 (`useSearchParams` → `setSearchParams` → `navigate` path, `getHistoryState`), `react` 19.2.8 `package.json`
- **Project decisions:** `27-CONTEXT.md` (D-01…D-10), `27-UI-SPEC.md` (C-01…C-24, R-1), `27-DISCUSSION-LOG.md`, `REQUIREMENTS.md` (KNOW-05), `STATE.md` (Blockers), `ROADMAP.md` (§ Phase 27 + notes)
- **Toolchain probes run this session:** `node --version` → `v24.21.0`; `npm --version` → `11.19.0`; installed versions read from `node_modules/*/package.json`

### Secondary (MEDIUM confidence)
- React 19 StrictMode dev remount semantics and "effect setup runs twice" — consistent with the installed version and the repo's own code comments; no external fetch was made because the installed sources settle it.

### Tertiary (LOW confidence)
- None. No claim in this document rests on a web search.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions read from installed packages; no new dependency.
- Architecture: HIGH — the effect/ref/cache shape is derived from the installed router's semantics and the repo's existing call graph.
- Pitfalls: HIGH for the twelve read from files; MEDIUM for the two that depend on timing (mock delay / `history.length` in Chromium), both marked in the Assumptions Log.
- Validation: HIGH for the mechanisms (counter, collector, static gate, `testMatch`); MEDIUM for the paging criterion (C-12), which is structurally pinned because the mock catalogue cannot produce `has_more`.

**Research date:** 2026-10-22
**Valid until:** ~2026-11-21 (stable: no dependency churn in scope; re-check if `react-router` or `@playwright/test` is upgraded, or if `KnowledgePage` gains a second call site).

**Phase requirement coverage:** KNOW-05 — fully researched (criteria 1–9 mapped to slices 1–11 and to the validation table).



