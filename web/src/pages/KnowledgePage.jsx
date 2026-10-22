import { useEffect, useRef, useState } from 'react'
import { useLocation, useSearchParams } from 'react-router-dom'
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

/** Role chips replace the role select; values sent are analyst | ds | omit (D-62, D-63). */
const ROLE_CHIPS = [
  { value: 'analyst', label: 'Analyst' },
  { value: 'ds', label: 'DS' },
  { value: 'all', label: 'Все' },
]

const FILTER_TOAST_MS = 4000

/** X-1: request counter installed at the `searchKnowledge` boundary (UI-SPEC X-1). */
const SEARCH_COUNT_KEY = '__DIGEST_KNOWLEDGE_SEARCH_COUNT__'

/** Counts every search attempt, throwing ones included — «Повторить» is counted the same way. */
function bumpKnowledgeSearchCount() {
  if (typeof window === 'undefined') return
  const current = typeof window[SEARCH_COUNT_KEY] === 'number' ? window[SEARCH_COUNT_KEY] : 0
  window[SEARCH_COUNT_KEY] = current + 1
}

/**
 * Last result per `(role, q)` for the session (C-04, D-04).
 *
 * Module scope, not component state: `KnowledgePage` unmounts on the way to a material, so a
 * component-local cache would die exactly when Back needs it. It is never persisted to any
 * browser storage — it dies with the document — so a reload re-queries (C-10, T-27-08).
 */
const SEARCH_SNAPSHOT_MAX = 20
const searchSnapshots = new Map()
/** Seeds the `role` state on remount so a chip change is looked up under the same role (C-09). */
let lastRoleForQuery = 'all'

/** A string key — user input is never used as an object key or a selector. */
function snapshotKey(roleValue, q) {
  return `${roleValue ?? 'all'}\u0000${q}`
}

function rememberSearchSnapshot(roleValue, q, entry) {
  const key = snapshotKey(roleValue, q)
  // Delete before set so a re-write is also an LRU touch.
  searchSnapshots.delete(key)
  searchSnapshots.set(key, entry)
  while (searchSnapshots.size > SEARCH_SNAPSHOT_MAX) {
    const oldest = searchSnapshots.keys().next().value
    searchSnapshots.delete(oldest)
  }
}

function recallSearchSnapshot(roleValue, q) {
  const key = snapshotKey(roleValue, q)
  const entry = searchSnapshots.get(key)
  if (!entry) return null
  searchSnapshots.delete(key)
  searchSnapshots.set(key, entry)
  return entry
}

/** An error is never cached: a failed key must re-query on the next visit. */
function forgetSearchSnapshot(roleValue, q) {
  searchSnapshots.delete(snapshotKey(roleValue, q))
}

function searchFailureState(err, { roleValue, append, q }) {
  if (err instanceof KnowledgeApiError && err.code === 'INVALID_ROLE' && roleValue !== 'all') {
    return { invalidRole: true }
  }
  const known = err instanceof KnowledgeApiError
  return {
    invalidRole: false,
    error: {
      message: known ? err.message : 'Не удалось выполнить поиск. Проверьте сеть.',
      retryable: known ? err.retryable : true,
    },
    clearItems: !append,
    activeQuery: q,
  }
}

/**
 * Knowledge SPA — Submit/Enter «Найти» → knowledgeApi (D-57, D-59, D-60, D-61 / KNOW-01).
 * Role chips re-run search when the trimmed query is non-empty (D-62, D-64 / KNOW-02).
 */
export default function KnowledgePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const location = useLocation()
  /** One-shot marker for a deliberate re-submit (D-05). `null` on any normal visit. */
  const submitId = location.state?.submitId ?? null
  const consumedSubmitIdRef = useRef(null)
  const [query, setQuery] = useState(() => searchParams.get('q') ?? '')
  /** 'all' omits role; analyst | ds are the only filters sent (D-62). */
  const [role, setRole] = useState(() => lastRoleForQuery)
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

  /** D-01: the URL is the only trigger — one Enter in the header is enough. */
  const qUrl = (searchParams.get('q') ?? '').trim()
  /** Read inside the effect, never listed in its deps (D-62: a chip change is its own action). */
  const roleRef = useRef(role)
  roleRef.current = role
  /** Last *executed* normalised q, written synchronously before the first await (D-03). */
  const lastHandledQueryRef = useRef(null)

  // `runSearch`, `searchParams` and `role` are deliberately omitted: they are new
  // identities on every render, and including them reproduces the duplicate fire
  // this phase removes (KNOW-05 criterion 2).
  useEffect(() => {
    // D-10: the field mirrors ?q for valid, overlong and empty queries alike.
    // Cannot loop — this effect is keyed on the URL, never on `query`.
    setQuery(qUrl)

    // C-16: removing ?q is a view reset, not a data reset — the rows must go, the role chip
    // and the snapshot cache must stay. A bare `return` would leave the previous rows on the
    // landing, which is what the RED case pinned (mutation: removing this branch left 2 rows).
    if (qUrl === '') {
      lastHandledQueryRef.current = null
      setActiveQuery(null)
      setItems([])
      setHasMore(false)
      setNextOffset(0)
      setError(null)
      setInlineError(null)
      setSearching(false)
      setLoadingMore(false)
      return
    }

    const validation = validateKnowledgeQuery(qUrl)
    // Blank and whitespace-only queries were handled above; ONLY an overlong ?q reaches here.
    // The copy comes from the validator (T-27-12): this file must not hold a second literal.
    if (!validation.ok) {
      setInlineError(validation.message)
      return
    }

    const q = validation.q

    // D-06: a deliberate re-submit beats BOTH the ref guard and the cache, so this branch
    // comes first — a forced re-run of the same q can never be swallowed as a duplicate or
    // replay stored rows.
    if (submitId !== null) {
      // The marker is only ever compared with `===`: never a URL segment, query value, CSS
      // selector, element id, cache key or navigation target (C-24, T-27-07).
      if (consumedSubmitIdRef.current === submitId) return
      consumedSubmitIdRef.current = submitId
      // Armed before anything asynchronous, so the strip's re-run returns at the guards.
      lastHandledQueryRef.current = q
      setInlineError(null)
      setError(null)
      setItems([])
      setHasMore(false)
      // D-07: a header submission searches from a clean slate.
      roleRef.current = 'all'
      setRole('all')
      lastRoleForQuery = 'all'
      // Issued AFTER the guards are set: the navigation re-runs this effect, which then
      // finds no marker and returns at the ref guard.
      setSearchParams(searchParams, { replace: true, state: null })
      void runSearch(q, { offset: 0, append: false, role: 'all' })
      return
    }

    if (lastHandledQueryRef.current === q) return
    // Written synchronously BEFORE `runSearch` — StrictMode's setup → cleanup →
    // setup must find the guard already armed, or a reload costs two requests.
    lastHandledQueryRef.current = q

    // C-04: Back from a material, or any remount, replays the stored result and never
    // reaches the adapter. This branch sits above runSearch, whose first statement is the
    // counter, so a restore is structurally unable to bump it.
    const snapshot = recallSearchSnapshot(roleRef.current, q)
    if (snapshot) {
      setActiveQuery(q)
      setItems(snapshot.items)
      setHasMore(snapshot.hasMore)
      setNextOffset(snapshot.nextOffset)
      setSearching(false)
      setLoadingMore(false)
      setError(null)
      return
    }

    setInlineError(null)
    void runSearch(q, { offset: 0, append: false, role: roleRef.current })
  }, [qUrl, submitId])

  async function runSearch(q, { offset = 0, append = false, role: roleValue = role } = {}) {
    if (append) {
      setLoadingMore(true)
    } else {
      setSearching(true)
      setError(null)
      setInlineError(null)
      // Coherent in-flight state: the status node and showZeroHit both read activeQuery.
      setActiveQuery(q)
    }

    let resetInvalidRole = false
    try {
      bumpKnowledgeSearchCount()
      const dto = await searchKnowledge({
        q,
        role: roleValue === 'all' ? null : roleValue,
        limit: DEFAULT_SEARCH_LIMIT,
        offset,
      })
      setActiveQuery(q)
      setItems((prev) => (append ? [...prev, ...dto.items] : dto.items))
      setHasMore(Boolean(dto.has_more))
      const nextCount = offset + (dto.items?.length ?? 0)
      setNextOffset(nextCount)
      if (append) {
        // C-12: a paginated delivery is stored and restored as ONE snapshot.
        const previous = recallSearchSnapshot(roleValue, q)
        rememberSearchSnapshot(roleValue, q, {
          items: previous ? [...previous.items, ...dto.items] : dto.items,
          hasMore: Boolean(dto.has_more),
          nextOffset: nextCount,
          limit: DEFAULT_SEARCH_LIMIT,
        })
      } else {
        rememberSearchSnapshot(roleValue, q, {
          items: dto.items,
          hasMore: Boolean(dto.has_more),
          nextOffset: nextCount,
          limit: DEFAULT_SEARCH_LIMIT,
        })
        // The remount seed: a later visit looks the cache up under this role.
        lastRoleForQuery = roleValue
      }
      setError(null)
      if (!append && q) {
        // Privacy: send only the role filter, never the raw user query, to Metrika.
        trackGoal(ANALYTICS_GOALS.search, { role: roleValue })
      }
    } catch (err) {
      // An error is never cached: evict the key so a cache-eligible revisit re-queries.
      // `roleValue`/`q` are the same pair the success branch would have stored under, so a
      // failure under a different role cannot evict another role's snapshot.
      forgetSearchSnapshot(roleValue, q)
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

  /**
   * Writes the executed `q` into the URL, always with `replace` (D-02, C-06/C-07).
   *
   * Only `q` is written and no `state` is attached: the one-shot `submitId` marker is the
   * header's alone (D-05), so a form or chip submission can never be mistaken for a header
   * one (which would wrongly reset the role per D-07).
   */
  function writeQueryToUrl(q) {
    setSearchParams(q ? { q } : {}, { replace: true })
  }

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
    // D-02 + D-05: the form still executes the search itself, but the URL becomes the
    // record. Arming the ref BEFORE the write is what keeps the URL-change effect from
    // firing a second request for the same q.
    lastHandledQueryRef.current = validation.q
    writeQueryToUrl(validation.q)
    void runSearch(validation.q, { offset: 0, append: false, role })
  }

  function handleRoleChange(nextRole) {
    setRole(nextRole)
    // Keeps the remount seed in agreement with the chip the user just chose (C-09).
    lastRoleForQuery = nextRole
    const validation = validateKnowledgeQuery(query)
    if (!validation.ok) {
      // Empty query: chip state only, no request (D-64). Overlong stays inline.
      if (validation.code === 'QUERY_TOO_LONG') {
        setInlineError('Сократите запрос')
        setError(null)
      }
      return
    }
    setInlineError(null)
    // C-21: write the executed q before executing. On a landing with typed text this is what
    // moves the page off the landing, so hints can never sit above a result surface. When the
    // URL already carries this q the write is byte-identical and replaces (no history entry).
    lastHandledQueryRef.current = validation.q
    writeQueryToUrl(validation.q)
    void runSearch(validation.q, { offset: 0, append: false, role: nextRole })
  }

  function handleRetry() {
    clearFailNextKnowledgeSearch()
    const validation = validateKnowledgeQuery(activeQuery ?? query)
    if (!validation.ok) {
      setInlineError(validation.message)
      return
    }
    void runSearch(validation.q, { offset: 0, append: false })
  }

  function handleLoadMore() {
    if (!hasMore || loadingMore || searching || activeQuery == null) return
    void runSearch(activeQuery, { offset: nextOffset, append: true })
  }

  function handleResetFilter() {
    // D-65 / KNOW-04: clear the role chip only. Query text stays and re-runs.
    setRole('all')
    const validation = validateKnowledgeQuery(query)
    if (!validation.ok) return
    void runSearch(validation.q, { offset: 0, append: false, role: 'all' })
  }

  /**
   * The landing rule, exactly as approved (`qUrl === '' && error === null`). Derived from the
   * URL synchronously, never from `activeQuery`: an overlong `?q` issues no request, so a
   * state-derived flag would leave `activeQuery` null and leak the hints onto a query frame
   * (T-27-13). Also hides the hints while a search is in flight, on zero-hit and on error.
   */
  const preSearch = qUrl === '' && error === null

  const showZeroHit =
    activeQuery !== null && !searching && !error && items.length === 0

  return (
    <section>
      <h1 className="mb-6 font-display text-3xl font-semibold">База знаний</h1>
      <KnowledgeSearchForm
        query={query}
        setQuery={setQuery}
        inlineError={inlineError}
        setInlineError={setInlineError}
        searching={searching}
        onSubmit={handleSubmit}
        role={role}
        onRoleChange={handleRoleChange}
        toast={toast}
      />
      <KnowledgeResults
        preSearch={preSearch}
        setQuery={setQuery}
        error={error}
        onRetry={handleRetry}
        activeQuery={activeQuery}
        searching={searching}
        items={items}
        hasMore={hasMore}
        showZeroHit={showZeroHit}
        onResetFilter={handleResetFilter}
        loadingMore={loadingMore}
        onLoadMore={handleLoadMore}
      />
    </section>
  )
}

function KnowledgeSearchForm({
  query,
  setQuery,
  inlineError,
  setInlineError,
  searching,
  onSubmit,
  role,
  onRoleChange,
  toast,
}) {
  return (
    <>
      <form className="mb-4" role="search" onSubmit={onSubmit}>
        <label className="sr-only" htmlFor="kb-search">
          Поиск по базе знаний
        </label>
        <div className="flex max-w-xl flex-col gap-3 sm:flex-row sm:items-stretch">
          <input
            id="kb-search"
            type="search"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              if (inlineError) setInlineError(null)
            }}
            placeholder="Спросите своими словами: SQL, дашборды, RAG…"
            disabled={searching}
            aria-invalid={inlineError ? true : undefined}
            aria-describedby={inlineError ? 'kb-search-inline-error' : undefined}
            className="min-w-0 flex-1 break-words rounded-xl border border-field-border bg-bg-surface px-4 py-3 text-sm outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-primary"
          />
          <ActionButton
            type="submit"
            variant="primary"
            state={searching ? 'loading' : 'idle'}
            disabled={searching}
            className="shrink-0"
          >
            Найти
          </ActionButton>
        </div>
        {inlineError ? (
          <p
            id="kb-search-inline-error"
            role="alert"
            className="mt-2 text-sm text-danger-ink"
            data-testid="kb-inline-error"
          >
            {inlineError}
          </p>
        ) : null}
      </form>

      <div className="mb-6 flex flex-wrap gap-2" role="group" aria-label="Роль" data-testid="kb-role-chips">
        {ROLE_CHIPS.map((chip) => {
          const selected = role === chip.value
          return (
            <button
              key={chip.value}
              type="button"
              aria-pressed={selected}
              disabled={searching}
              onClick={() => onRoleChange(chip.value)}
              className={
                selected
                  ? 'min-h-11 rounded-full bg-primary-solid px-3 text-sm text-on-solid'
                  : 'min-h-11 rounded-full border border-border bg-bg-surface px-3 text-sm text-text-primary hover:bg-bg-app'
              }
            >
              {chip.label}
            </button>
          )
        })}
      </div>

      {toast ? (
        <p className="mb-4 text-sm text-text-secondary" role="status" data-testid="kb-filter-toast">
          {toast}
        </p>
      ) : null}
    </>
  )
}

function knowledgeResultSummary({ searching, items, hasMore }) {
  if (searching) return 'Ищем…'
  if (items.length === 0) return 'Найдено 0 материалов'
  return `Показано ${items.length}${hasMore ? '+' : ''}`
}

function KnowledgeResults({
  preSearch,
  setQuery,
  error,
  onRetry,
  activeQuery,
  searching,
  items,
  hasMore,
  showZeroHit,
  onResetFilter,
  loadingMore,
  onLoadMore,
}) {
  return (
    <>
      {preSearch ? (
        <div className="mb-8" data-testid="kb-hint-chips">
          <p className="mb-3 text-xs text-text-secondary">Попробуйте тему:</p>
          <div className="flex flex-wrap gap-2">
            {HINT_CHIPS.map((hint) => (
              <button
                key={hint}
                type="button"
                className="min-h-11 rounded-full border border-border bg-bg-surface px-3 text-sm text-text-primary hover:bg-bg-app"
                onClick={() => setQuery(hint)}
              >
                {hint}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {error ? (
        <div className="mb-6" data-testid="kb-search-error">
          <ErrorPanel title="Не удалось найти материалы" message={error.message} />
          {error.retryable ? (
            <ActionButton variant="secondary" className="mt-4" onClick={onRetry}>
              Повторить
            </ActionButton>
          ) : null}
        </div>
      ) : null}

      {searching || (activeQuery !== null && !error) ? (
        <p className="mb-4 text-xs text-text-secondary" aria-live="polite">
          {knowledgeResultSummary({ searching, items, hasMore })}
        </p>
      ) : null}

      {showZeroHit ? (
        <div className="max-w-md rounded-2xl border border-border bg-bg-surface p-8">
          <h2 className="font-display text-2xl font-semibold">Ничего не нашли</h2>
          <p className="mt-2 text-sm text-text-secondary">
            По запросу нет материалов — уточните формулировку или смените роль.
          </p>
          <button
            type="button"
            onClick={onResetFilter}
            className="mt-4 inline-flex min-h-11 items-center text-sm text-primary-text"
          >
            Сбросить фильтр
          </button>
        </div>
      ) : null}

      <KnowledgeHitList
        items={items}
        loadingMore={loadingMore}
        hasMore={hasMore}
        searching={searching}
        onLoadMore={onLoadMore}
      />
    </>
  )
}

function KnowledgeHitList({ items, loadingMore, hasMore, searching, onLoadMore }) {
  if (items.length === 0) return null
  return (
    <div>
      {items.map((hit) => (
        // KNOW-03: every hit, including DS, opens /materials/{slug}.
        <MaterialListRow key={hit.slug} material={hit} section="base" />
      ))}
      {loadingMore ? (
        <div data-testid="kb-skeleton" className="mt-4 space-y-3" aria-busy="true">
          <div className="h-16 animate-pulse rounded-xl bg-bg-surface" />
          <div className="h-16 animate-pulse rounded-xl bg-bg-surface" />
        </div>
      ) : null}
      {hasMore && !loadingMore ? (
        <div className="mt-6">
          <ActionButton variant="secondary" onClick={onLoadMore} disabled={searching}>
            Показать ещё
          </ActionButton>
        </div>
      ) : null}
    </div>
  )
}
