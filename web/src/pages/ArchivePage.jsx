import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import { clearFailNextContentFetch, fetchArchive } from '../services/contentApi.js'
import { materialCountLabel } from '../utils/ruCount.js'

export default function ArchivePage() {
  const [issues, setIssues] = useState([])
  const [status, setStatus] = useState('loading')
  const [loadKey, setLoadKey] = useState(0)

  const reload = useCallback(() => {
    clearFailNextContentFetch()
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    fetchArchive()
      .then((dto) => {
        if (cancelled) return
        setIssues(dto.issues ?? [])
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
    <section data-testid="archive-page">
      <p className="mb-4">
        <Link to="/" className="inline-flex min-h-11 items-center text-sm text-primary-text no-underline hover:underline">
          ← К текущему выпуску
        </Link>
      </p>

      <h1 className="mb-6 font-display text-3xl font-semibold">Архив</h1>

      {status === 'loading' ? (
        <div aria-busy="true" data-testid="archive-loading">
          <div className="h-4 w-48 animate-pulse rounded bg-border" />
          <div className="mt-4 h-24 animate-pulse rounded bg-border" />
        </div>
      ) : null}

      {status === 'error' ? <ServiceUnavailable onRetry={reload} /> : null}

      {status === 'ready' && issues.length === 0 ? (
        <div data-testid="archive-empty">
          <h2 className="font-display text-2xl font-semibold">Архив пуст</h2>
          <p className="mt-3 max-w-prose text-text-secondary">Прошлых выпусков пока нет.</p>
          <p className="mt-6">
            <Link to="/" className="inline-flex min-h-11 items-center font-medium text-primary-text no-underline hover:underline">
              К текущему выпуску →
            </Link>
          </p>
        </div>
      ) : null}

      {status === 'ready' && issues.length > 0 ? (
        <ul className="grid gap-4 sm:grid-cols-2" data-testid="archive-list">
          {issues.map((issue) => (
            <li key={issue.number}>
              <Link
                to={`/issues/${issue.number}`}
                className="block min-h-11 rounded-xl border border-border bg-bg-surface p-5 no-underline transition hover:border-primary"
              >
                <p className="text-xs uppercase tracking-wide text-text-disabled">
                  Выпуск №{issue.number}
                </p>
                <h2 className="mt-2 font-display text-xl font-semibold text-text-primary">
                  {issue.period_label}
                </h2>
                <p className="mt-1 text-sm text-text-secondary">{issue.title}</p>
                <p className="mt-3 text-xs text-text-disabled">
                  {materialCountLabel(issue.material_count ?? 0)}
                </p>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
