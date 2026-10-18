import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ChronologyItem from '../components/ChronologyItem.jsx'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import { clearFailNextRazboryFetch, fetchRazbory } from '../services/razboryApi.js'

/**
 * Razbory chronology list at /razbory (RAZB-01 / D-66…D-69).
 */
export default function RazboryListPage() {
  const [items, setItems] = useState([])
  const [status, setStatus] = useState('loading')
  const [loadKey, setLoadKey] = useState(0)

  const reload = useCallback(() => {
    clearFailNextRazboryFetch()
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    fetchRazbory()
      .then((dto) => {
        if (cancelled) return
        setItems(dto.items ?? [])
        setStatus('ready')
      })
      .catch(() => {
        if (cancelled) return
        setStatus('error')
      })
    return () => {
      cancelled = true
    }
  }, [loadKey])

  return (
    <section data-testid="razbory-page">
      <h1 className="mb-2 font-display text-3xl font-semibold">Разборы</h1>
      <p className="mb-10 text-xs text-muted">
        Встречи раз в две недели · материалы от Data Scientist
      </p>

      {status === 'loading' ? (
        <div aria-busy="true" data-testid="razbory-loading">
          <div className="h-4 w-48 animate-pulse rounded bg-rule" />
          <div className="mt-4 h-24 animate-pulse rounded bg-rule" />
        </div>
      ) : null}

      {status === 'error' ? <ServiceUnavailable onRetry={reload} /> : null}

      {status === 'ready' && items.length === 0 ? (
        <div data-testid="razbory-empty">
          <h2 className="font-display text-2xl font-semibold">Разборов пока нет</h2>
          <p className="mt-3 max-w-prose text-ink-2">
            Когда появятся — опубликуем здесь. Пока можно проголосовать за следующую тему.
          </p>
          <p className="mt-6">
            <Link
              to="/voting"
              className="inline-flex min-h-11 items-center font-medium text-accent no-underline hover:underline"
            >
              К голосованию
            </Link>
          </p>
        </div>
      ) : null}

      {status === 'ready' && items.length > 0 ? (
        <div data-testid="razbory-list">
          {items.map((item) => (
            <ChronologyItem key={item.id} item={item} />
          ))}
        </div>
      ) : null}
    </section>
  )
}
