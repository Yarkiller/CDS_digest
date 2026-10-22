---
phase: 27-header-search-runs-on-submit
reviewed: 2026-10-22T12:15:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - web/src/pages/KnowledgePage.jsx
  - web/src/components/SearchPill.jsx
  - tests/knowledge.spec.js
  - tests/unit/test_knowledge_api_snapshot.js
  - tests/unit/test_knowledge_search_single_call_site.js
findings:
  critical: 0
  warning: 4
  info: 1
  total: 5
status: issues_found
---

# Phase 27: Code Review Report

**Reviewed:** 2026-10-22T12:15:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Непустые submit-пути действительно `replace`, одноразовый `submitId` снимается через `replace` без `state` у формы/чипа, `forgetSearchSnapshot` в `catch` бьёт в тот же ключ `(role, q)`, что и успешный store, а `?q` нигде не уходит в HTML-sink. `web/src/services/knowledgeApi.js` не редактировался: LF-нормализованный sha256 = `bce5c54e08f588e4ebf816466411b74bbe8d1896f6ab6942afb2469298d2f29f` (совпадает с `FROZEN_SHA256` и с Wave 0 в `27-PATTERNS.md`); `git diff --exit-code -- web/src/services/knowledgeApi.js` чист. В `web/src` нет `dangerouslySetInnerHTML`, `.innerHTML`, `document.write`, `document.title =`. Ошибка рисуется только в `<main>` через `ErrorPanel` текстовыми детьми, не в `<header>`.

Оставшиеся дефекты — не «забыли replace на RAG», а дыры вокруг этого контракта: нет поколения/отмены inflight-запроса (пилл шапки по контракту фазы нельзя `disabled`), пустой header-submit по-прежнему `push`, overlong-ветка эффекта не сбрасывает выдачу/панель ошибки, «Сбросить фильтр» исполняет живое поле и не пишет `?q`.

## Warnings

### WR-01: `runSearch` принимает любой завершившийся ответ — стейл-запрос перетирает новый `q` и сбивает in-flight

**File:** `web/src/pages/KnowledgePage.jsx:217-287`
**Issue:** У `runSearch` нет поколения, `AbortController` и проверки «это ещё актуальный запрос». `await searchKnowledge` затем безусловно делает `setItems` / `rememberSearchSnapshot` / `setError`, а `finally` всегда ставит `setSearching(false)` и `setLoadingMore(false)`.

`SearchPill` по контракту фазы не знает про поиск и не может быть `disabled` (`27-PATTERNS.md` § payload-only). Значит перекрывающиеся submit из шапки — поддерживаемый поток, не экзотика:

1. `/knowledge?q=RAG` ушёл в полёт (мок ~80 мс, live — дольше).
2. Пользователь сразу Enter `SQL` из шапки. Эффект по `submitId` стартует второй `runSearch` и даже делает `setItems([])`.
3. Если RAG отвечает позже SQL, C-03 ломается: в DOM снова RAG при URL `?q=SQL`. Если RAG отвечает первым, его `finally` снимает `searching`, пока SQL ещё летит — live-регион и disabled поля страницы врут, что поиск закончен.

Та же дыра бьёт C-16/C-18: пустая ветка (`:145-156`) обнуляет строки, но не инвалидирует уже запущенный `runSearch`; late success вернёт хиты на лендинг (подсказки и строки одновременно). Overlong-return (`:161-164`) не трогает `searching`, поэтому in-flight RAG после overlong-навигации дорисует выдачу на кадре «Сократите запрос».

Дубль *одного* submit эффект+handler закрыт (`lastHandledQueryRef` до `writeQueryToUrl`) — это не то. Гонка здесь между *двумя* вызовами `runSearch`.

**Fix:** счётчик поколения, инкремент на каждый `runSearch` и на сброс `qUrl === ''` / overlong; игнор ответа и `finally`, если поколение сменилось.

```javascript
const searchGenRef = useRef(0)

async function runSearch(q, { offset = 0, append = false, role: roleValue = role } = {}) {
  const gen = ++searchGenRef.current
  // ...setSearching / setLoadingMore...
  try {
    bumpKnowledgeSearchCount()
    const dto = await searchKnowledge({ /* unchanged */ })
    if (gen !== searchGenRef.current) return
    // ...existing success writes...
  } catch (err) {
    if (gen !== searchGenRef.current) return
    // ...existing catch (keep forgetSearchSnapshot)...
  } finally {
    if (gen !== searchGenRef.current) return
    setSearching(false)
    setLoadingMore(false)
  }
  // resetInvalidRole recursive call stays after the gen check
}
```

В ветке `qUrl === ''` (и в overlong-return) сделайте `searchGenRef.current += 1` до очистки стейта, чтобы late success не воскресил строки.

### WR-02: пустой submit из шапки делает `push`, Back возвращает предыдущий `?q`

**File:** `web/src/components/SearchPill.jsx:35-37`
**Issue:** Непустой путь корректно `replace: true` (`:45-48`). Пустой/пробельный — нет:

```javascript
if (!q) {
  navigate('/knowledge')
  return
}
```

С `/knowledge?q=RAG` это кладёт новую запись лендинга поверх query-варианта. Back снова даёт `?q=RAG` — ровно та прогулка по вариантам запроса, которую C-07/C-20/T-27-16 запрещают для submit. Кейс `removing ?q clears the rows` проверяет DOM и счётчик, но не `history.length` и не `goBack`.

27-05 явно оставил empty submit «как было» (D-08, ноль запросов). Слепой `{ replace: true }` на этом `navigate` тоже неверен: с `/` пустой Enter должен оставить возможность вернуться на выпуск. Дыра только когда пилл уже на `/knowledge`.

**Fix:** replace только когда текущий pathname уже база знаний.

```javascript
const location = useLocation()
// ...
if (!q) {
  navigate('/knowledge', { replace: location.pathname === '/knowledge' })
  return
}
```

И пин: с `/knowledge?q=RAG` пустой Enter → `history.length` не растёт, `goBack` уводит с `/knowledge`.

### WR-03: overlong-`?q` на смонтированной выдаче не сбрасывает строки и панель ошибки

**File:** `web/src/pages/KnowledgePage.jsx:161-164`
**Issue:** C-18 требует на overlong: inline «Сократите запрос», **строк нет**, **`kb-search-error` нет**, лендинга нет. Ветка делает только `setInlineError` и `return`. Пустая ветка рядом (`:145-156`) сбрасывает `items`/`error`/`searching`/`activeQuery`; overlong — нет.

На уже смонтированной странице:

- populated `?q=RAG` → header Enter 501 символов → URL overlong, inline-ошибка, **хиты RAG остаются**;
- `kb-search-error` на экране → тот же overlong → панель ошибки **не снимается** (нет `setError(null)`), E8/C-18 «нет search-error» ломается.

Тест `an overlong header submit is rejected inline` стартует с `/`, где строк не было — гейт зелёный и не ловит mounted-переход. `handleRoleChange` к тому же делает `setRole`/`lastRoleForQuery` *до* валидации (`:329-338`), поэтому клик DS при overlong в поле перекрашивает чип, не перезапрашивая — расхождение чип/выдача (C-13) на том же кадре.

**Fix:** в overlong-return сбрасывать поверхность выдачи так же, как в empty, не трогая кэш и роль:

```javascript
if (!validation.ok) {
  setInlineError(validation.message)
  setError(null)
  setItems([])
  setHasMore(false)
  setNextOffset(0)
  setSearching(false)
  setLoadingMore(false)
  setActiveQuery(null)
  lastHandledQueryRef.current = null
  return
}
```

И перенести `setRole`/`lastRoleForQuery` в `handleRoleChange` ниже `validation.ok` (для overlong чип не должен расходиться с оставшейся выдачей; для пустого поля D-64 по-прежнему может менять чип — это отдельная ветка `EMPTY_QUERY`).

### WR-04: «Сбросить фильтр» исполняет живое поле и не пишет `?q`

**File:** `web/src/pages/KnowledgePage.jsx:365-371`
**Issue:** C-21 (и must-have плана 05): после чипа, «Сбросить фильтр» и «Повторить» URL обязан нести *исполненный* `q` через `replace`. План оставил `handleResetFilter` с прямым `runSearch`, исходя из «q уже в URL». Поле при этом редактируемо, zero-hit-карточка остаётся на экране.

```javascript
function handleResetFilter() {
  setRole('all')
  const validation = validateKnowledgeQuery(query) // live field, not URL / activeQuery
  if (!validation.ok) return
  void runSearch(validation.q, { offset: 0, append: false, role: 'all' })
}
```

Сценарий: zero-hit по `?q=RAG` → дописать в поле `SQL` без «Найти» → «Сбросить фильтр». Уходит поиск `SQL`, адрес остаётся `?q=RAG`. `handleRetry` для сравнения берёт `activeQuery ?? query` (`:352`) и поэтому не разъезжается с URL. `handleRoleChange` уже пишет URL; reset — нет. `lastRoleForQuery` тоже не ставится в `'all'` до успеха `runSearch`.

**Fix:**

```javascript
function handleResetFilter() {
  setRole('all')
  lastRoleForQuery = 'all'
  const validation = validateKnowledgeQuery(query)
  if (!validation.ok) return
  lastHandledQueryRef.current = validation.q
  writeQueryToUrl(validation.q)
  void runSearch(validation.q, { offset: 0, append: false, role: 'all' })
}
```

## Info

### IN-01: idle-пин «ровно один запрос» стоит на `waitForTimeout(1200)`

**File:** `tests/knowledge.spec.js:217-218`
**Issue:** Кейс `header submit issues exactly one search request` после набора текста ждёт фиксированные 1200 мс и читает счётчик. Комментарий честно говорит, что 4-секундный toast здесь недостижим. Если дубль когда-нибудь уедет на таймер >1.2 с (или на медленный identity-fetch в `AppShell`), пин останется зелёным. Это не ломает текущий suite, но делает критерий 2 частично вакуумным.

**Fix:** убрать `waitForTimeout`; держать `expectCount` через `expect.poll` ещё один тик после известных re-render триггеров (theme/focus/typing уже есть) либо явно крутануть 4 с toast-таймера в отдельном кейсе, где `INVALID_ROLE` достижим.

---

_Reviewed: 2026-10-22T12:15:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
