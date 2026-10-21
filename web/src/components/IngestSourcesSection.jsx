import { useEffect, useState } from 'react'
import {
  IngestSourcesError,
  addIngestSource,
  deleteIngestSource,
  listIngestSources,
  setIngestSourceEnabled,
} from '../services/ingestSourcesApi.js'

function errorPrefix(error) {
  if (error?.path) return `${error.path}: `
  return ''
}

function kindLabel(kind) {
  return kind === 'playlist' ? 'Плейлист' : 'Канал'
}

function youtubeHref(kind, sourceId) {
  const id = String(sourceId ?? '')
  if (kind === 'playlist') {
    return `https://www.youtube.com/playlist?list=${id}`
  }
  return `https://www.youtube.com/channel/${id}`
}

function deleteConfirmMessage(sourceId) {
  return `Удалить источник ${sourceId}? Это действие нельзя отменить.`
}

const ROW_ACTION_ERROR = 'Не удалось обновить источник. Повторите действие.'

/**
 * Admin ingest-sources section — list + add above the YAML editor (SRC-01, D-01/D-02).
 * Form field values are lifted to the host for ADUX-10 dirty OR (D-03/D-04).
 */
export default function IngestSourcesSection({
  sourceId,
  label,
  kind,
  onSourceIdChange,
  onLabelChange,
  onKindChange,
  onFormCleared,
}) {
  const [loadState, setLoadState] = useState('loading')
  const [loadKey, setLoadKey] = useState(0)
  const [sources, setSources] = useState([])
  const [loadError, setLoadError] = useState('')
  const [adding, setAdding] = useState(false)
  const [addError, setAddError] = useState('')
  const [validationErrors, setValidationErrors] = useState([])
  const [rejected, setRejected] = useState(false)
  /** @type {[number | null, function]} row id with in-flight PATCH/DELETE */
  const [busyRowId, setBusyRowId] = useState(null)
  /** @type {[Record<number, string>, function]} per-row inline errors */
  const [rowErrors, setRowErrors] = useState({})

  useEffect(() => {
    let cancelled = false
    setLoadState('loading')
    setLoadError('')
    listIngestSources()
      .then((rows) => {
        if (cancelled) return
        setSources(Array.isArray(rows) ? rows : [])
        setLoadState('ready')
      })
      .catch((err) => {
        if (cancelled) return
        setLoadState('error')
        setLoadError(
          err instanceof IngestSourcesError ? err.message : 'Не удалось загрузить источники',
        )
      })
    return () => {
      cancelled = true
    }
  }, [loadKey])

  const trimmedId = (sourceId ?? '').trim()
  const canAdd = trimmedId !== '' && !adding && loadState === 'ready'

  async function onAdd() {
    if (!canAdd) return
    setAdding(true)
    setAddError('')
    setRejected(false)
    setValidationErrors([])
    try {
      const row = await addIngestSource({
        kind: kind || 'channel',
        source_id: trimmedId,
        label: label ?? '',
      })
      setSources((prev) => [...prev, row])
      onFormCleared?.()
    } catch (err) {
      if (err instanceof IngestSourcesError && err.code === 'INVALID_SOURCE') {
        setValidationErrors(Array.isArray(err.errors) ? err.errors : [])
        setRejected(true)
      } else {
        setAddError(
          err instanceof IngestSourcesError
            ? err.message
            : 'Не удалось добавить источник. Проверьте данные и повторите.',
        )
      }
    } finally {
      setAdding(false)
    }
  }

  async function onToggle(row) {
    if (busyRowId != null) return
    const id = Number(row.id)
    setBusyRowId(id)
    setRowErrors((prev) => {
      const next = { ...prev }
      delete next[id]
      return next
    })
    try {
      const updated = await setIngestSourceEnabled(id, !row.is_enabled)
      setSources((prev) => prev.map((s) => (Number(s.id) === id ? updated : s)))
    } catch (err) {
      setRowErrors((prev) => ({
        ...prev,
        [id]: err instanceof IngestSourcesError ? err.message : ROW_ACTION_ERROR,
      }))
    } finally {
      setBusyRowId(null)
    }
  }

  async function onDelete(row) {
    if (busyRowId != null) return
    const ok = window.confirm(deleteConfirmMessage(row.source_id))
    if (!ok) return
    const id = Number(row.id)
    setBusyRowId(id)
    setRowErrors((prev) => {
      const next = { ...prev }
      delete next[id]
      return next
    })
    try {
      await deleteIngestSource(id)
      setSources((prev) => prev.filter((s) => Number(s.id) !== id))
    } catch (err) {
      setRowErrors((prev) => ({
        ...prev,
        [id]: err instanceof IngestSourcesError ? err.message : ROW_ACTION_ERROR,
      }))
    } finally {
      setBusyRowId(null)
    }
  }

  const enabledCount = sources.filter((s) => s.is_enabled).length
  const showZeroEnabled = sources.length > 0 && enabledCount === 0

  return (
    <section
      data-testid="ingest-sources-section"
      className="mt-6 mb-6 rounded-2xl border border-rule bg-paper p-4 md:p-6"
      aria-busy={loadState === 'loading' || adding || busyRowId != null}
    >
      <h2
        data-testid="ingest-sources-heading"
        className="font-sans text-2xl font-semibold text-ink"
      >
        Источники
      </h2>

      {loadState === 'loading' ? (
        <p className="mt-4 text-sm text-muted">Загрузка…</p>
      ) : null}

      {loadState === 'error' ? (
        <div className="mt-4">
          <p className="text-sm text-ink-2">{loadError || 'Не удалось загрузить источники'}</p>
          <button
            type="button"
            data-testid="ingest-sources-load-retry"
            className="mt-2 inline-flex min-h-11 items-center font-medium text-accent-text hover:underline"
            onClick={() => setLoadKey((k) => k + 1)}
          >
            Повторить загрузку
          </button>
        </div>
      ) : null}

      {loadState === 'ready' && sources.length === 0 ? (
        <div data-testid="ingest-sources-empty" className="mt-4">
          <p className="text-base text-ink-2">Пока нет источников</p>
          <p className="mt-1 text-sm text-muted">
            Добавьте канал или плейлист по каноническому id — список сохранится для последующего
            сбора.
          </p>
        </div>
      ) : null}

      {showZeroEnabled ? (
        <p data-testid="ingest-sources-zero-enabled" className="mt-4 text-sm text-muted">
          Нет включённых источников — новые видео собираться не будут
        </p>
      ) : null}

      {loadState === 'ready' && sources.length > 0 ? (
        <ul data-testid="ingest-sources-list" className="mt-4 space-y-3">
          {sources.map((row) => {
            const id = Number(row.id)
            const rowBusy = busyRowId === id
            return (
              <li
                key={row.id}
                data-testid="ingest-source-row"
                className="rounded-xl border border-rule bg-paper-2 p-3"
              >
                <p className="break-words font-mono text-base text-ink-2">{row.source_id}</p>
                <p className="mt-1 break-words text-xs text-muted">
                  {kindLabel(row.kind)} · {row.is_enabled ? 'включён' : 'выключен'}
                  {row.label ? ` · ${row.label}` : ''}
                </p>
                <div className="mt-2 flex flex-wrap items-center gap-2">
                  <button
                    type="button"
                    className="inline-flex min-h-11 items-center rounded-xl border border-rule px-3 text-sm font-normal text-ink-2 disabled:cursor-not-allowed disabled:opacity-45"
                    disabled={rowBusy}
                    onClick={() => onToggle(row)}
                  >
                    {row.is_enabled ? 'Выключить' : 'Включить'}
                  </button>
                  <button
                    type="button"
                    className="inline-flex min-h-11 items-center rounded-xl border border-danger-ink/60 px-3 text-sm font-normal text-danger-ink disabled:cursor-not-allowed disabled:opacity-45"
                    disabled={rowBusy}
                    onClick={() => onDelete(row)}
                  >
                    Удалить
                  </button>
                  <a
                    href={youtubeHref(row.kind, row.source_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex min-h-11 items-center underline text-sm font-normal text-ink-2"
                  >
                    Открыть на YouTube
                  </a>
                </div>
                {rowErrors[id] ? (
                  <p role="alert" className="mt-2 text-sm text-danger-ink">
                    {rowErrors[id]}
                  </p>
                ) : null}
                {rowBusy ? <span className="sr-only">Обновление…</span> : null}
              </li>
            )
          })}
        </ul>
      ) : null}

      <div className="mt-6 space-y-3 rounded-xl bg-paper-2 p-4">
        <div className="flex flex-wrap items-end gap-2">
          <label className="flex flex-col gap-1 text-xs font-semibold text-ink-2">
            Тип
            <select
              data-testid="ingest-sources-kind"
              className="min-h-11 rounded-xl border border-field-border bg-paper px-3 text-base font-normal text-ink-2 focus-visible:outline-accent"
              value={kind || 'channel'}
              disabled={adding}
              onChange={(e) => onKindChange?.(e.target.value)}
            >
              <option value="channel">Канал</option>
              <option value="playlist">Плейлист</option>
            </select>
          </label>
          <label className="flex min-w-[12rem] flex-1 flex-col gap-1 text-xs font-semibold text-ink-2">
            Идентификатор
            <input
              data-testid="ingest-sources-id"
              type="text"
              autoComplete="off"
              spellCheck={false}
              className="min-h-11 rounded-xl border border-field-border bg-paper px-3 font-mono text-base font-normal text-ink-2 focus-visible:outline-accent"
              value={sourceId ?? ''}
              disabled={adding}
              onChange={(e) => onSourceIdChange?.(e.target.value)}
            />
          </label>
          <label className="flex min-w-[10rem] flex-1 flex-col gap-1 text-xs font-semibold text-ink-2">
            Название
            <input
              data-testid="ingest-sources-label"
              type="text"
              maxLength={120}
              placeholder="Необязательно"
              className="min-h-11 rounded-xl border border-field-border bg-paper px-3 text-base font-normal text-ink-2 focus-visible:outline-accent"
              value={label ?? ''}
              disabled={adding}
              onChange={(e) => onLabelChange?.(e.target.value)}
            />
          </label>
          <button
            type="button"
            data-testid="ingest-sources-add"
            className="inline-flex min-h-11 items-center justify-center rounded-full bg-accent-solid px-5 text-sm font-medium text-on-solid disabled:cursor-not-allowed disabled:opacity-45"
            disabled={!canAdd}
            onClick={onAdd}
          >
            Добавить источник
          </button>
        </div>
        <p data-testid="ingest-sources-id-help" className="text-xs text-muted">
          Только канонический id: UC… для канала или PL… для плейлиста.
        </p>
        <details className="text-sm text-ink-2">
          <summary className="min-h-11 cursor-pointer font-normal">Где взять id?</summary>
          <div className="mt-2 space-y-2 break-words text-sm text-muted">
            <p>
              Канал: YouTube Studio → «Настройки» → «Канал» → «Расширенные настройки» →
              «Идентификатор канала» (UC…).
            </p>
            <p>
              Плейлист: откройте плейлист и скопируйте параметр list= из адресной строки (PL…).
            </p>
          </div>
        </details>
      </div>

      {rejected ? (
        <div
          data-testid="ingest-sources-errors"
          role="alert"
          className="mt-4 rounded-2xl border border-danger-ink/60 bg-danger/10 p-4"
        >
          <h3 className="font-sans text-2xl font-semibold text-danger-ink">
            Проверьте данные источника
          </h3>
          {validationErrors.length > 0 ? (
            <ol className="mt-2 space-y-2">
              {validationErrors.map((error, index) => (
                <li
                  key={`${error?.path ?? 'error'}-${index}`}
                  className="break-words text-sm text-danger-ink"
                >
                  {errorPrefix(error) ? (
                    <span className="font-mono">{errorPrefix(error)}</span>
                  ) : null}
                  {String(error?.message ?? '')}
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-sm text-danger-ink">Источник не добавлен</p>
          )}
        </div>
      ) : null}

      {addError ? (
        <p role="alert" className="mt-4 text-sm text-danger-ink">
          {addError}
        </p>
      ) : null}
    </section>
  )
}
