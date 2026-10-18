import { useCallback, useEffect, useState } from 'react'
import IngestSourcesSection from '../components/IngestSourcesSection.jsx'
import IngestionScheduleSection from '../components/IngestionScheduleSection.jsx'
import ServiceUnavailable from '../components/ServiceUnavailable.jsx'
import UnsavedChangesDialog from '../components/UnsavedChangesDialog.jsx'
import { useUnsavedChangesGuard } from '../hooks/useUnsavedChangesGuard.js'
import ForbiddenPage from './ForbiddenPage.jsx'
import { getAccessToken } from '../services/authApi.js'
import {
  IngestScheduleError,
  fetchIngestionSchedule,
} from '../services/ingestScheduleApi.js'
import { MeApiError, fetchMe } from '../services/meApi.js'
import {
  PipelineConfigError,
  fetchPipelineConfig,
  savePipelineConfig,
} from '../services/pipelineConfigApi.js'

/**
 * Human-readable prefix for a structured server validation error (D-05):
 * «Строка {line}: » when the parser supplied a line, else «{path}: » when a path
 * is present, else nothing. The server message is rendered verbatim afterwards.
 */
function errorPrefix(error) {
  if (typeof error?.line === 'number') return `Строка ${error.line}: `
  if (error?.path) return `${error.path}: `
  return ''
}

/** Reset-to-saved confirm copy (UI-SPEC; D-12). */
const RESET_CONFIRM = 'Отменить изменения и вернуть последнюю сохранённую версию?'

/**
 * Admin pipeline config — view + edit the raw YAML config without running the
 * pipeline (PIPE-01/PIPE-03; D-10/D-11/D-12/D-13). Minimal tracer surface:
 * editor + Save toolbar. No run/trigger/scheduler control ships here.
 */
export default function AdminPipelineConfigPage() {
  const [roleState, setRoleState] = useState('loading')
  const [roleKey, setRoleKey] = useState(0)
  const [loadState, setLoadState] = useState('loading')
  const [loadKey, setLoadKey] = useState(0)
  const [yaml, setYaml] = useState('')
  const [savedYaml, setSavedYaml] = useState('')
  const [status, setStatus] = useState('loading')
  const [loadError, setLoadError] = useState('')
  const [saveError, setSaveError] = useState('')
  const [rejected, setRejected] = useState(false)
  const [validationErrors, setValidationErrors] = useState([])
  const [saving, setSaving] = useState(false)
  // ADUX-10 / D-04: source form fields lifted for dirty OR with YAML.
  const [sourceId, setSourceId] = useState('')
  const [sourceLabel, setSourceLabel] = useState('')
  const [sourceKind, setSourceKind] = useState('channel')
  // ING-06 / D-16: schedule saves immediately — never part of dirty.
  const [schedule, setSchedule] = useState(null)
  const [scheduleError, setScheduleError] = useState('')
  const [scheduleLoading, setScheduleLoading] = useState(false)

  const loadSchedule = useCallback(async () => {
    setScheduleLoading(true)
    setScheduleError('')
    try {
      const dto = await fetchIngestionSchedule()
      setSchedule(dto)
    } catch (err) {
      setSchedule(null)
      setScheduleError(
        err instanceof IngestScheduleError
          ? err.message
          : 'Не удалось загрузить настройки сбора',
      )
    } finally {
      setScheduleLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function loadRole() {
      setRoleState('loading')
      try {
        const token = await getAccessToken()
        const me = await fetchMe(token)
        if (!cancelled) {
          setRoleState(me.role === 'admin' ? 'admin' : 'forbidden')
        }
      } catch (err) {
        if (cancelled) return
        // Only authz failures are Forbidden; network/5xx → error + retry.
        if (
          err instanceof MeApiError &&
          (err.code === 'UNAUTHORIZED' || err.code === 'FORBIDDEN')
        ) {
          setRoleState('forbidden')
        } else {
          setRoleState('error')
        }
      }
    }
    loadRole()
    return () => {
      cancelled = true
    }
  }, [roleKey])

  useEffect(() => {
    if (roleState !== 'admin') return undefined
    let cancelled = false
    setLoadState('loading')
    setStatus('loading')
    setLoadError('')
    setSaveError('')
    setRejected(false)
    setValidationErrors([])
    fetchPipelineConfig()
      .then((dto) => {
        if (cancelled) return
        const text = typeof dto?.yaml === 'string' ? dto.yaml : ''
        setYaml(text)
        setSavedYaml(text)
        setLoadState('ready')
        setStatus('clean')
      })
      .catch((err) => {
        if (cancelled) return
        setLoadState('error')
        setLoadError(
          err instanceof PipelineConfigError ? err.message : 'Не удалось загрузить конфиг',
        )
      })
    return () => {
      cancelled = true
    }
  }, [roleState, loadKey])

  useEffect(() => {
    if (roleState !== 'admin') return
    loadSchedule()
  }, [roleState, loadSchedule])

  const yamlDirty = yaml !== savedYaml
  const sourceFormDirty = sourceId.trim() !== '' || sourceLabel.trim() !== ''
  const dirty = yamlDirty || sourceFormDirty
  const blocker = useUnsavedChangesGuard(dirty)

  function reloadRole() {
    setRoleKey((k) => k + 1)
  }

  function reloadConfig() {
    setLoadKey((k) => k + 1)
  }

  function onReset() {
    if (!yamlDirty) return
    if (!window.confirm(RESET_CONFIRM)) return
    setYaml(savedYaml)
    setSaveError('')
    setRejected(false)
    setValidationErrors([])
    setStatus('clean')
  }

  function onEdit(nextValue) {
    setYaml(nextValue)
    setSaveError('')
    setRejected(false)
    setValidationErrors([])
    setStatus(nextValue === savedYaml ? 'clean' : 'dirty')
  }

  async function onSave() {
    if (saving || !yamlDirty) return
    setSaving(true)
    setStatus('saving')
    setSaveError('')
    setRejected(false)
    setValidationErrors([])
    try {
      const dto = await savePipelineConfig(yaml)
      const saved = typeof dto?.yaml === 'string' ? dto.yaml : yaml
      setYaml(saved)
      setSavedYaml(saved)
      setStatus('saved')
    } catch (err) {
      if (err instanceof PipelineConfigError && err.code === 'INVALID_CONFIG') {
        // Server rejected a structurally invalid document: render every structured
        // error and keep the document dirty (never auto-revert or discard).
        setValidationErrors(Array.isArray(err.errors) ? err.errors : [])
        setRejected(true)
        setStatus('dirty')
      } else {
        setSaveError('Конфиг не сохранён')
        setStatus('failed')
      }
    } finally {
      setSaving(false)
    }
  }

  if (roleState === 'loading') {
    return (
      <section aria-busy="true" data-testid="admin-role-loading">
        <p className="text-sm text-muted">Загрузка…</p>
      </section>
    )
  }

  if (roleState === 'forbidden') {
    return <ForbiddenPage />
  }

  if (roleState === 'error') {
    return (
      <section data-testid="admin-pipeline-page">
        <ServiceUnavailable onRetry={reloadRole} />
      </section>
    )
  }

  if (loadState === 'loading') {
    return (
      <section aria-busy="true" data-testid="admin-pipeline-page">
        <p className="mt-2 text-sm text-muted">Просмотр и правка без запуска пайплайна</p>
        <p data-testid="pipeline-config-loading" className="mt-4 text-sm text-muted">
          Загрузка…
        </p>
      </section>
    )
  }

  if (loadState === 'error') {
    return (
      <section data-testid="admin-pipeline-page">
        <p className="mt-2 text-sm text-muted">Просмотр и правка без запуска пайплайна</p>
        <p className="mt-4 text-sm text-ink-2">{loadError || 'Не удалось загрузить конфиг'}</p>
        <button
          type="button"
          data-testid="pipeline-config-retry"
          className="mt-4 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
          onClick={reloadConfig}
        >
          Повторить загрузку
        </button>
      </section>
    )
  }

  const statusText =
    status === 'saving'
      ? 'Сохранение…'
      : status === 'saved'
        ? 'Сохранено'
        : status === 'dirty'
          ? 'Есть несохранённые изменения'
          : status === 'failed'
            ? ''
            : 'Изменений нет'

  return (
    <section data-testid="admin-pipeline-page" className="pb-16">
      <p className="mt-2 text-sm text-muted">Просмотр и правка без запуска пайплайна</p>

      <IngestSourcesSection
        sourceId={sourceId}
        label={sourceLabel}
        kind={sourceKind}
        onSourceIdChange={setSourceId}
        onLabelChange={setSourceLabel}
        onKindChange={setSourceKind}
        onFormCleared={() => {
          setSourceId('')
          setSourceLabel('')
          setSourceKind('channel')
        }}
      />

      <IngestionScheduleSection
        schedule={schedule}
        loadError={scheduleError}
        loading={scheduleLoading}
        onScheduleChange={setSchedule}
        onLoadError={setScheduleError}
        onRetry={loadSchedule}
      />

      {!savedYaml ? (
        <div
          data-testid="pipeline-config-empty"
          className="mt-6 rounded-2xl border border-rule bg-paper-2/40 p-6"
        >
          <h2 className="font-sans text-2xl font-semibold text-ink">Конфиг ещё не задан</h2>
          <p className="mt-2 text-sm text-muted">
            Введите YAML и сохраните — конфиг будет доступен при следующих заходах.
          </p>
        </div>
      ) : null}

      <div className="mt-6 flex flex-wrap items-center gap-3" aria-busy={saving}>
        <button
          type="button"
          data-testid="pipeline-config-save"
          className="inline-flex min-h-11 items-center justify-center rounded-full bg-accent px-5 text-sm font-medium text-accent-ink disabled:cursor-not-allowed disabled:opacity-45"
          disabled={!yamlDirty || saving}
          onClick={onSave}
        >
          Сохранить конфиг
        </button>
        <button
          type="button"
          data-testid="pipeline-config-reload"
          className="inline-flex min-h-11 items-center justify-center rounded-full border border-rule px-5 text-sm font-medium text-ink-2 disabled:cursor-not-allowed disabled:opacity-45"
          disabled={!yamlDirty || saving}
          onClick={onReset}
        >
          Отменить изменения
        </button>
        <p
          data-testid="pipeline-config-status"
          role="status"
          className="text-sm text-muted"
        >
          {statusText}
        </p>
      </div>

      {rejected ? (
        <div
          data-testid="pipeline-config-errors"
          role="alert"
          className="mt-4 rounded-2xl border border-[oklch(70%_0.12_25)] bg-[oklch(96%_0.03_25)] p-4"
        >
          <h2 className="font-sans text-2xl font-semibold text-[oklch(45%_0.14_25)]">
            Проверьте конфиг перед сохранением
          </h2>
          {validationErrors.length > 0 ? (
            <ol className="mt-2 space-y-2">
              {validationErrors.map((error, index) => (
                <li
                  key={`${error?.path ?? 'error'}-${index}`}
                  data-testid="pipeline-config-error"
                  className="break-words text-sm text-[oklch(45%_0.14_25)]"
                >
                  {errorPrefix(error) ? (
                    <span className="font-mono">{errorPrefix(error)}</span>
                  ) : null}
                  {String(error?.message ?? '')}
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-sm text-[oklch(45%_0.14_25)]">Конфиг не прошёл проверку</p>
          )}
        </div>
      ) : null}

      {saveError ? (
        <div
          role="alert"
          className="mt-4 rounded-2xl border border-[oklch(70%_0.12_25)] bg-[oklch(96%_0.03_25)] p-4"
        >
          <h2 className="font-sans text-base font-semibold text-[oklch(35%_0.12_25)]">
            Конфиг не сохранён
          </h2>
          <button
            type="button"
            data-testid="pipeline-config-save-retry"
            className="mt-2 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
            onClick={onSave}
          >
            Повторить сохранение
          </button>
        </div>
      ) : null}

      <textarea
        data-testid="pipeline-config-editor"
        aria-label="YAML конфига пайплайна"
        aria-invalid={rejected}
        spellCheck={false}
        autoComplete="off"
        autoCorrect="off"
        autoCapitalize="off"
        wrap="off"
        className="mt-4 min-h-[20rem] max-h-[60vh] w-full overflow-auto rounded-xl border border-rule bg-paper p-3 font-mono text-base leading-relaxed text-ink-2 focus-visible:outline-accent"
        value={yaml}
        placeholder="# YAML конфига пайплайна"
        onChange={(e) => onEdit(e.target.value)}
      />

      <UnsavedChangesDialog
        open={blocker.state === 'blocked'}
        onStay={() => blocker.reset()}
        onLeave={() => blocker.proceed()}
      />
    </section>
  )
}
