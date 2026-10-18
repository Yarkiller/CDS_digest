import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import EditorialCallout from '../components/EditorialCallout.jsx'
import IssueToc from '../components/IssueToc.jsx'
import PlatformProofBanner from '../components/PlatformProofBanner.jsx'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import {
  ContentApiError,
  clearFailNextContentFetch,
  fetchCurrentIssue,
  fetchIssueByNumber,
} from '../services/contentApi.js'
import { materialCountLabel } from '../utils/ruCount.js'

function toTocItems(items) {
  return items.map((item) => ({
    id: item.slug,
    title: item.title,
    issuePosition: item.position,
    format: item.format,
    readingMinutes: item.reading_minutes,
    dek: item.dek,
  }))
}

function IssueStatusView({ status, notFound, isEmpty, isCurrent, reload }) {
  if (status === 'loading') {
    return (
      <section aria-busy="true" data-testid="issue-loading">
        {isCurrent ? <PlatformProofBanner /> : null}
        <div className="mt-3 h-4 w-48 animate-pulse rounded bg-rule" />
        <div className="mt-4 h-10 max-w-xl animate-pulse rounded bg-rule" />
        <div className="mt-6 h-24 animate-pulse rounded bg-rule" />
      </section>
    )
  }
  if (status === 'error') {
    return (
      <section>
        {isCurrent ? <PlatformProofBanner /> : null}
        <ServiceUnavailable onRetry={reload} />
      </section>
    )
  }
  if (notFound) {
    return (
      <section data-testid="issue-not-found">
        <h1 className="font-display text-3xl font-semibold">Выпуск не найден</h1>
        <p className="mt-3 max-w-prose text-ink-2">
          Проверьте номер выпуска или вернитесь к актуальному.
        </p>
        <p className="mt-6">
          <Link
            to="/"
            className="inline-flex min-h-11 items-center font-medium text-accent no-underline hover:underline"
          >
            К текущему выпуску →
          </Link>
        </p>
      </section>
    )
  }
  if (isEmpty) {
    return (
      <section data-testid="issue-empty">
        {isCurrent ? <PlatformProofBanner /> : null}
        <h2 className="font-display text-2xl font-semibold">Выпуск готовится</h2>
        <p className="mt-3 max-w-prose text-ink-2">
          Свежий выпуск скоро появится. А пока — загляните в архив прошлых недель.
        </p>
        <p className="mt-6">
          <Link to="/archive" className="font-medium text-accent no-underline hover:underline">
            В архив →
          </Link>
        </p>
      </section>
    )
  }
  return null
}

/** Format cycle closes_at for callout copy (UI-SPEC). */
function formatClosesAt(iso) {
  if (!iso) return ''
  try {
    return new Intl.DateTimeFormat('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      timeZone: 'UTC',
    }).format(new Date(iso))
  } catch {
    return String(iso)
  }
}

/**
 * @param {{ isCurrent?: boolean }} props
 * isCurrent=true on `/` (EditorialCallout, D-34); false on `/issues/:number`.
 */
export default function IssuePage({ isCurrent = true }) {
  const { number: numberParam } = useParams()
  const [issue, setIssue] = useState(null)
  const [status, setStatus] = useState('loading')
  const [notFound, setNotFound] = useState(false)
  const [loadKey, setLoadKey] = useState(0)

  const reload = useCallback(() => {
    clearFailNextContentFetch()
    setLoadKey((k) => k + 1)
  }, [])

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

  const items = issue?.items ?? []
  const isEmpty = items.length === 0
  if (status !== 'ready' || notFound || isEmpty) {
    return (
      <IssueStatusView
        status={status}
        notFound={notFound}
        isEmpty={isEmpty}
        isCurrent={isCurrent}
        reload={reload}
      />
    )
  }

  const cycle = isCurrent ? issue?.voting_cycle : null
  const showCallout = Boolean(cycle?.status)

  return (
    <section data-testid="issue-ready">
      {isCurrent ? <PlatformProofBanner /> : null}
      <p className="text-xs uppercase tracking-wide text-muted">
        Выпуск №{issue.number} · {issue.period_label}
      </p>
      <h1 className="mt-3 max-w-4xl font-display text-4xl font-semibold leading-tight sm:text-5xl">
        {issue.title}
      </h1>
      <p className="mt-3 text-sm text-ink-2">
        {issue.editor ?? 'Редакция Digest CDS'} · {materialCountLabel(items.length)}
      </p>

      <hr className="my-8 border-rule" />

      {showCallout && cycle.status === 'open' ? (
        <EditorialCallout actionTo="/voting" actionLabel="Выбрать тему →">
          <strong>Голосование открыто</strong> до {formatClosesAt(cycle.closes_at)} — выберите тему
          следующего разбора.
        </EditorialCallout>
      ) : null}

      {showCallout && cycle.status === 'closed' ? (
        <EditorialCallout muted>
          <strong>Голосование закрыто.</strong> Итоги появятся в ближайшем разборе.
        </EditorialCallout>
      ) : null}

      <h2 className="mb-6 font-display text-2xl font-semibold">В этом выпуске</h2>
      <IssueToc items={toTocItems(items)} />
    </section>
  )
}
