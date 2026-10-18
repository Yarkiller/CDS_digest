import { useCallback, useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'
import rehypeSlug from 'rehype-slug'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import {
  RAZBOR_EDITOR_BYLINE,
  RazboryApiError,
  clearFailNextRazboryFetch,
  downloadRazborNotebook,
  fetchRazbor,
  razborStatusLabel,
} from '../services/razboryApi.js'
import { extractMarkdownHeadings } from '../utils/markdownToc.js'

const TOAST_DISMISS_MS = 4000

function formatMeetingLabel(iso) {
  if (!iso) return null
  try {
    return new Date(iso).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    })
  } catch {
    return null
  }
}

function SectionToc({ headings }) {
  if (!headings.length) return null

  const links = headings.map((heading) => (
    <li key={heading.id} className={heading.level > 2 ? 'pl-3' : undefined}>
      <a href={`#${heading.id}`} className="text-sm text-accent no-underline hover:underline">
        {heading.text}
      </a>
    </li>
  ))

  return (
    <>
      <details className="mb-8 rounded-lg border border-rule bg-paper-2 p-3 lg:hidden">
        <summary className="cursor-pointer text-sm font-medium">Содержание</summary>
        <ul className="mt-3 space-y-2">{links}</ul>
      </details>
      <nav
        aria-label="Содержание"
        data-testid="razbor-toc"
        className="sticky top-24 hidden max-h-[70vh] w-56 shrink-0 overflow-auto lg:block"
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Содержание</p>
        <ul className="mt-3 space-y-2">{links}</ul>
      </nav>
    </>
  )
}

/**
 * Dual notebook strip — top + bottom on published longread (D-70…72 / RAZB-03).
 * Missing notebook: strip stays; download disabled + «Notebook скоро будет».
 */
function NotebookStrip({ available, downloading, onDownload, placement }) {
  return (
    <div
      data-testid={`razbor-notebook-strip-${placement}`}
      className="flex flex-col gap-3 rounded-lg border border-rule bg-paper-2 p-5 sm:flex-row sm:items-center sm:justify-between"
    >
      <div className="min-w-0">
        <p className="text-sm text-ink-2">Код не выполняется — только просмотр.</p>
        {!available ? (
          <p data-testid="razbor-notebook-pending" className="mt-1 text-xs text-muted">
            Notebook скоро будет
          </p>
        ) : null}
      </div>
      <button
        type="button"
        data-testid={`razbor-notebook-download-${placement}`}
        disabled={!available || downloading}
        onClick={onDownload}
        className="inline-flex min-h-11 shrink-0 items-center justify-center rounded-full border border-rule bg-paper px-4 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:border-rule disabled:text-muted disabled:opacity-70"
      >
        Скачать .ipynb
      </button>
    </div>
  )
}

/**
 * Razbor detail — published longread + TOC + notebook dual strip, announcement stub, soft 404
 * (RAZB-02 / RAZB-03 / D-68 / D-70…72).
 */
export default function RazborPage() {
  const { id } = useParams()
  const [razbor, setRazbor] = useState(null)
  const [status, setStatus] = useState('loading')
  const [notFound, setNotFound] = useState(false)
  const [loadKey, setLoadKey] = useState(0)
  const [toast, setToast] = useState('')
  const [downloading, setDownloading] = useState(false)

  const reload = useCallback(() => {
    clearFailNextRazboryFetch()
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    setNotFound(false)

    fetchRazbor(id)
      .then((dto) => {
        if (cancelled) return
        setRazbor(dto)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        if (err instanceof RazboryApiError && err.code === 'NOT_FOUND') {
          setNotFound(true)
          setStatus('ready')
          return
        }
        setStatus('error')
      })

    return () => {
      cancelled = true
    }
  }, [id, loadKey])

  useEffect(() => {
    if (!toast) return undefined
    const timer = window.setTimeout(() => setToast(''), TOAST_DISMISS_MS)
    return () => window.clearTimeout(timer)
  }, [toast])

  const handleNotebookDownload = useCallback(async () => {
    if (downloading) return
    setDownloading(true)
    setToast('')
    try {
      const { blob, filename } = await downloadRazborNotebook(id)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(url)
    } catch {
      setToast('Не удалось скачать')
    } finally {
      setDownloading(false)
    }
  }, [downloading, id])

  if (status === 'loading') {
    return (
      <section aria-busy="true" data-testid="razbor-loading">
        <div className="mt-3 h-4 w-40 animate-pulse rounded bg-rule" />
        <div className="mt-4 h-10 max-w-xl animate-pulse rounded bg-rule" />
        <div className="mt-6 h-40 animate-pulse rounded bg-rule" />
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section>
        <ServiceUnavailable onRetry={reload} />
      </section>
    )
  }

  if (notFound || !razbor) {
    return (
      <section data-testid="razbor-not-found">
        <h1 className="font-display text-3xl font-semibold">Разбор не найден</h1>
        <p className="mt-3 max-w-prose text-ink-2">
          Возможно, ссылка устарела или разбор ещё готовится.
        </p>
        <p className="mt-6">
          <Link
            to="/razbory"
            className="inline-flex min-h-11 items-center text-accent no-underline hover:underline"
          >
            К списку разборов
          </Link>
        </p>
      </section>
    )
  }

  const dateLabel = formatMeetingLabel(razbor.meeting_at)
  const statusLabel = razborStatusLabel(razbor.status)
  const isAnnouncement = razbor.status === 'announcement'
  const isOverview = !isAnnouncement && razbor.content_kind === 'overview'
  const isQuality = !isAnnouncement && razbor.content_kind === 'quality'
  const typeBadge = isAnnouncement ? 'Анонс' : isOverview ? 'Обзор' : 'Разбор'
  const overline = [dateLabel, statusLabel].filter(Boolean).join(' · ')

  if (isAnnouncement) {
    return (
      <article className="max-w-3xl" data-testid="razbor-announcement-stub">
        <p className="mb-6">
          <Link to="/razbory" className="text-sm text-ink-2 no-underline hover:underline">
            ← Все разборы
          </Link>
        </p>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">
          {overline || 'Анонс'}
        </p>
        <span
          data-testid="razbor-type-badge"
          className="mt-2 inline-block rounded bg-paper-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-ink"
        >
          {typeBadge}
        </span>
        <h1 className="mt-3 break-words font-display text-4xl font-semibold sm:text-5xl">
          {razbor.title}
        </h1>
        <p className="mt-3 text-sm text-ink-2">{razbor.editor ?? RAZBOR_EDITOR_BYLINE}</p>
        <p
          data-testid="razbor-pending-note"
          className="mt-8 max-w-prose rounded-lg border border-rule bg-paper-2 p-5 text-ink-2"
        >
          Полный разбор ещё готовится — следите за обновлениями.
        </p>
      </article>
    )
  }

  const headings = extractMarkdownHeadings(razbor.body_markdown ?? '')
  const notebookAvailable = Boolean(razbor.notebook_available)

  return (
    <article className="max-w-5xl" data-testid="razbor-longread">
      <p className="mb-6">
        <Link to="/razbory" className="text-sm text-ink-2 no-underline hover:underline">
          ← Все разборы
        </Link>
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">
          {overline || (isOverview ? 'Обзор' : 'Разбор')}
        </p>
        <span
          data-testid="razbor-type-badge"
          className="rounded bg-paper-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-ink"
        >
          {typeBadge}
        </span>
      </div>

      <h1 className="mt-3 break-words font-display text-4xl font-semibold sm:text-5xl">
        {razbor.title}
      </h1>
      <p className="mt-3 text-sm text-ink-2">{razbor.editor ?? RAZBOR_EDITOR_BYLINE}</p>

      {isQuality ? (
        <p data-testid="razbor-quality-label" className="mt-4 text-sm font-semibold text-ink">
          Качество
        </p>
      ) : null}

      <div className="mt-6">
        <NotebookStrip
          placement="top"
          available={notebookAvailable}
          downloading={downloading}
          onDownload={handleNotebookDownload}
        />
      </div>

      <hr className="my-8 border-rule" />

      <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
        <SectionToc headings={headings} />

        <div className="min-w-0 flex-1">
          <div
            data-testid="razbor-prose"
            className="prose-column max-w-3xl leading-relaxed text-ink-2 [&_h1]:mt-8 [&_h1]:font-display [&_h1]:text-3xl [&_h1]:font-semibold [&_h1]:text-ink [&_h2]:mt-8 [&_h2]:font-display [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:text-ink [&_h3]:mt-6 [&_h3]:font-display [&_h3]:text-xl [&_h3]:font-semibold [&_h3]:text-ink [&_p]:mt-4 [&_table]:mt-4 [&_table]:w-full [&_ul]:mt-4 [&_ul]:list-disc [&_ul]:pl-5"
          >
            <Markdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeSlug, rehypeSanitize]}>
              {razbor.body_markdown}
            </Markdown>
          </div>

          <div className="mt-10">
            <NotebookStrip
              placement="bottom"
              available={notebookAvailable}
              downloading={downloading}
              onDownload={handleNotebookDownload}
            />
          </div>

          <p className="mt-10">
            <Link to="/razbory" className="text-sm text-accent no-underline hover:underline">
              ← К списку разборов
            </Link>
          </p>
        </div>
      </div>

      {toast ? (
        <div
          role="status"
          data-testid="razbor-notebook-toast"
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full border border-rule bg-paper px-4 py-2 text-sm text-ink shadow-sm"
        >
          {toast}
        </div>
      ) : null}
    </article>
  )
}
