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

/** Topic hint chips fill the query only — do not execute search (D-60). */
const HINT_CHIPS = ['RAG', 'SQL', 'качество данных', 'pgvector']

/** Role chips replace the role select; values sent are analyst | ds | omit (D-62, D-63). */
const ROLE_CHIPS = [
  { value: 'analyst', label: 'Analyst' },
  { value: 'ds', label: 'DS' },
  { value: 'all', label: 'Все' },
]

const FILTER_TOAST_MS = 4000

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

  function handleRoleChange(nextRole) {
    setRole(nextRole)
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

  const preSearch = activeQuery === null && !error
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
            className="min-w-0 flex-1 break-words rounded-xl border border-rule bg-[oklch(98%_0.009_95)] px-4 py-3 text-sm outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent"
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
            className="mt-2 text-sm text-[oklch(35%_0.12_25)]"
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
                  ? 'min-h-11 rounded-full bg-accent px-3 text-sm text-accent-ink'
                  : 'min-h-11 rounded-full border border-rule bg-paper-2 px-3 text-sm text-ink hover:bg-paper'
              }
            >
              {chip.label}
            </button>
          )
        })}
      </div>

      {toast ? (
        <p className="mb-4 text-sm text-ink-2" role="status" data-testid="kb-filter-toast">
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
          <p className="mb-3 text-xs text-ink-2">Попробуйте тему:</p>
          <div className="flex flex-wrap gap-2">
            {HINT_CHIPS.map((hint) => (
              <button
                key={hint}
                type="button"
                className="min-h-11 rounded-full border border-rule bg-paper-2 px-3 text-sm text-ink hover:bg-paper"
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

      {activeQuery !== null && !error ? (
        <p className="mb-4 text-xs text-ink-2" aria-live="polite">
          {knowledgeResultSummary({ searching, items, hasMore })}
        </p>
      ) : null}

      {showZeroHit ? (
        <div className="max-w-md rounded-2xl border border-rule bg-[oklch(98.5%_0.009_95)] p-8">
          <h2 className="font-display text-2xl font-semibold">Ничего не нашли</h2>
          <p className="mt-2 text-sm text-ink-2">
            По запросу нет материалов — уточните формулировку или смените роль.
          </p>
          <button
            type="button"
            onClick={onResetFilter}
            className="mt-4 inline-flex min-h-11 items-center text-sm text-accent"
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
        <MaterialListRow key={hit.slug} material={hit} />
      ))}
      {loadingMore ? (
        <div data-testid="kb-skeleton" className="mt-4 space-y-3" aria-busy="true">
          <div className="h-16 animate-pulse rounded-xl bg-paper-2" />
          <div className="h-16 animate-pulse rounded-xl bg-paper-2" />
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
