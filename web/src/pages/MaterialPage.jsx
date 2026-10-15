import { useCallback, useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, useParams } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'
import rehypeSlug from 'rehype-slug'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import { ContentApiError, clearFailNextContentFetch, fetchMaterial } from '../services/contentApi.js'
import { fetchMaterialPreview } from '../services/adminApi.js'
import { extractMarkdownHeadings } from '../utils/markdownToc.js'

function formatPublishedLabel(material) {
  if (material.published_label) return material.published_label
  if (!material.published_at) return null
  try {
    return new Date(material.published_at).toLocaleDateString('ru-RU', {
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
      <a
        href={`#${heading.id}`}
        className="text-sm text-accent no-underline hover:underline"
      >
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
        data-testid="material-toc"
        className="sticky top-24 hidden max-h-[70vh] w-56 shrink-0 overflow-auto lg:block"
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">Содержание</p>
        <ul className="mt-3 space-y-2">{links}</ul>
      </nav>
    </>
  )
}

export default function MaterialPage({ preview = false, loadMaterial }) {
  const { id: slug } = useParams()
  const [material, setMaterial] = useState(null)
  const [status, setStatus] = useState('loading')
  const [notFound, setNotFound] = useState(false)
  const [loadKey, setLoadKey] = useState(0)

  // Additive injection: the reader route passes nothing, so it keeps loading
  // through fetchMaterial byte-identically (D-02).
  const loader = loadMaterial ?? (preview ? fetchMaterialPreview : fetchMaterial)

  const reload = useCallback(() => {
    clearFailNextContentFetch()
    setLoadKey((k) => k + 1)
  }, [])

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    setNotFound(false)

    loader(slug)
      .then((dto) => {
        if (cancelled) return
        setMaterial(dto)
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
  }, [slug, loadKey, preview])

  if (status === 'loading') {
    return (
      <section aria-busy="true" data-testid="material-loading">
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

  if (notFound || !material) {
    return (
      <section data-testid="material-not-found">
        <h1 className="font-display text-3xl font-semibold">Материал не найден</h1>
        <p className="mt-3 max-w-prose text-ink-2">
          Возможно, ссылка устарела или материал ещё готовится. Вернитесь к выпуску или в архив.
        </p>
        <p className="mt-6 flex flex-wrap gap-4">
          <Link to="/" className="inline-flex min-h-11 items-center text-accent no-underline hover:underline">
            ← К выпуску
          </Link>
          <Link
            to="/archive"
            className="inline-flex min-h-11 items-center text-accent no-underline hover:underline"
          >
            В архив
          </Link>
        </p>
      </section>
    )
  }

  const headings = extractMarkdownHeadings(material.body_markdown ?? '')
  const tags = material.tags ?? []
  const related = material.related ?? []
  const dek = (material.dek ?? '').trim()
  const provenance = (material.provenance ?? '').trim()
  const dateLabel = formatPublishedLabel(material)
  const overlineTag = tags[0] ?? null

  return (
    <article className="max-w-5xl">
      {preview ? (
        <p
          data-testid="material-preview-banner"
          className="mb-6 rounded-lg border border-rule bg-paper-2 px-4 py-3 text-sm font-medium text-ink"
        >
          Черновик — предпросмотр, не опубликовано
        </p>
      ) : null}

      <div className="flex flex-wrap items-center gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted">
          Статья{overlineTag ? ` · ${overlineTag}` : ''}
        </p>
        <span
          data-testid="material-format-badge"
          className="rounded bg-paper-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-ink"
        >
          Статья
        </span>
      </div>

      <h1 className="mt-3 font-display text-4xl font-semibold sm:text-5xl">{material.title}</h1>

      {dek ? (
        <p data-testid="material-dek" className="mt-4 max-w-prose text-lg leading-relaxed text-ink-2">
          {dek}
        </p>
      ) : null}

      <p className="mt-3 text-sm text-ink-2">
        {[
          dateLabel,
          provenance ? `provenance: ${provenance}` : null,
          material.reading_minutes != null ? `~${material.reading_minutes} мин чтения` : null,
        ]
          .filter(Boolean)
          .join(' · ')}
      </p>

      <hr className="my-8 border-rule" />

      <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
        <SectionToc headings={headings} />

        <div className="min-w-0 flex-1">
          <div
            data-testid="material-prose"
            className="prose-column max-w-3xl leading-relaxed text-ink-2 [&_h1]:mt-8 [&_h1]:font-display [&_h1]:text-3xl [&_h1]:font-semibold [&_h1]:text-ink [&_h2]:mt-8 [&_h2]:font-display [&_h2]:text-2xl [&_h2]:font-semibold [&_h2]:text-ink [&_h3]:mt-6 [&_h3]:font-display [&_h3]:text-xl [&_h3]:font-semibold [&_h3]:text-ink [&_p]:mt-4 [&_ul]:mt-4 [&_ul]:list-disc [&_ul]:pl-5"
          >
            <Markdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeSlug, rehypeSanitize]}
            >
              {material.body_markdown}
            </Markdown>
          </div>

          {tags.length > 0 ? (
            <div className="mt-8 flex flex-wrap gap-2" data-testid="material-tags">
              {tags.map((tag) => (
                <Link
                  key={tag}
                  to="/knowledge"
                  className="rounded-full bg-paper-2 px-2 py-1 text-xs text-accent no-underline"
                >
                  #{tag}
                </Link>
              ))}
            </div>
          ) : null}

          {related.length > 0 ? (
            <section className="mt-10" data-testid="material-related">
              <h2 className="font-display text-xl font-semibold">Связанные материалы</h2>
              <ul className="mt-3 space-y-2">
                {related.map((item) => (
                  <li key={item.slug}>
                    <Link to={`/materials/${item.slug}`} className="text-accent no-underline hover:underline">
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <p className="mt-10 flex flex-wrap gap-4">
            <Link to="/" className="text-sm text-accent no-underline hover:underline">
              ← К выпуску
            </Link>
            <Link to="/archive" className="text-sm text-accent no-underline hover:underline">
              В архив
            </Link>
          </p>
        </div>
      </div>
    </article>
  )
}
