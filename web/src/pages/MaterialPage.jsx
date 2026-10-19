import { useCallback, useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import { Link, Navigate, useParams } from 'react-router-dom'
import remarkGfm from 'remark-gfm'
import rehypeSanitize from 'rehype-sanitize'
import rehypeSlug from 'rehype-slug'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import ForbiddenPage from './ForbiddenPage.jsx'
import { clearFailNextContentFetch, fetchMaterial } from '../services/contentApi.js'
import { fetchMaterialPreview } from '../services/adminApi.js'
import ReadingProgress from '../components/ReadingProgress.jsx'
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

/**
 * Concept 3 Long Document TOC (layout.css:218-300).
 *
 * One data source, two presentations, exactly as material.html does it: the rail
 * (`.toc`, >= 80rem) links through `.toc__link`, while the narrow-layout
 * disclosure (`.toc-mobile`) uses bare anchors styled by `.toc-mobile__list a`.
 */
function tocItems(headings, linkClassName) {
  return headings.map((heading) => (
    <li key={heading.id} className={heading.level > 2 ? 'pl-3' : undefined}>
      <a href={`#${heading.id}`} className={linkClassName}>
        {heading.text}
      </a>
    </li>
  ))
}

function TocMobile({ headings }) {
  if (!headings.length) return null

  return (
    <details className="toc-mobile" data-testid="material-toc-mobile">
      <summary className="toc-mobile__summary">
        Содержание <span aria-hidden="true">⌄</span>
      </summary>
      <ul className="toc-mobile__list">{tocItems(headings)}</ul>
    </details>
  )
}

function TocRail({ headings }) {
  if (!headings.length) return null

  return (
    <nav className="toc" aria-label="Содержание" data-testid="material-toc">
      <span className="text-overline mb-3 block">Содержание</span>
      <ul className="toc__list">{tocItems(headings, 'toc__link')}</ul>
    </nav>
  )
}

export default function MaterialPage({ preview = false, loadMaterial }) {
  const { id: slug } = useParams()
  const [material, setMaterial] = useState(null)
  const [status, setStatus] = useState('loading')
  const [notFound, setNotFound] = useState(false)
  const [redirectToReader, setRedirectToReader] = useState(false)
  const [forbidden, setForbidden] = useState(false)
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
    // CR-01: `redirectToReader` is read by an early return that is not guarded by `preview`,
    // and this instance is reused across the /admin/materials/:id -> /materials/:id handoff
    // the flag itself triggers. A stale `true` therefore re-renders <Navigate> to the URL we
    // are already on — i.e. nothing — and wedges every later in-app navigation until a full
    // reload. `forbidden` is the same defect class (WR-01), latent only while no
    // preview->preview link exists.
    setRedirectToReader(false)
    setForbidden(false)

    loader(slug)
      .then((dto) => {
        if (cancelled) return
        setMaterial(dto)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        // A code check (not `instanceof`) so both the reader loader's ContentApiError
        // and the preview loader's AdminApiError map through the same branch (D-12).
        const code = err && typeof err === 'object' ? err.code : null
        if (code === 'NOT_FOUND') {
          if (preview) {
            // Not a previewable draft — the reader route is the honest destination.
            setRedirectToReader(true)
            return
          }
          setNotFound(true)
          setStatus('ready')
          return
        }
        // D-03: the SPA only translates the server's 403 — it never decides the role.
        if (preview && code === 'FORBIDDEN') {
          setForbidden(true)
          return
        }
        setStatus('error')
      })

    return () => {
      cancelled = true
    }
  }, [slug, loadKey, preview])

  if (preview && forbidden) {
    return <ForbiddenPage />
  }

  if (redirectToReader) {
    return <Navigate to={`/materials/${slug}`} replace />
  }

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
      <ReadingProgress />
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

      {/* Concept 3 reading macro: the article takes track one and the sticky TOC
          rail takes track two from 80rem up (layout.css:205-258). Below that the
          rail is hidden and `.toc-mobile` carries the same links, so — exactly as
          in material.html — the disclosure leads the reading column. */}
      <div className="split-layout--reading" data-testid="material-layout">
        <div className="min-w-0">
          <TocMobile headings={headings} />

          <div
            data-testid="material-prose"
            className="prose prose--column"
          >
            <Markdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeSlug, rehypeSanitize]}
              components={{
                // Concept 3 Long Document accent: a markdown quote is a pull quote,
                // not a browser-default indented block.
                blockquote: ({ children }) => <blockquote className="pull-quote">{children}</blockquote>,
              }}
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
            <aside className="editorial-box" data-testid="material-related">
              <div className="editorial-box__title">Связанные материалы</div>
              <ul className="mt-3 space-y-2">
                {related.map((item) => (
                  <li key={item.slug}>
                    <Link to={`/materials/${item.slug}`} className="text-accent no-underline hover:underline">
                      {item.title}
                    </Link>
                  </li>
                ))}
              </ul>
            </aside>
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

        <TocRail headings={headings} />
      </div>
    </article>
  )
}
