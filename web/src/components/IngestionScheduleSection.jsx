import { useEffect, useState } from 'react'
import {
  IngestScheduleError,
  patchIngestionSchedule,
} from '../services/ingestScheduleApi.js'

const DAY_LABELS = [
  { day: 1, label: 'пн' },
  { day: 2, label: 'вт' },
  { day: 3, label: 'ср' },
  { day: 4, label: 'чт' },
  { day: 5, label: 'пт' },
  { day: 6, label: 'сб' },
  { day: 7, label: 'вс' },
]

const EMPTY_WEEK_MSG = 'Выберите хотя бы один день недели.'

/**
 * Admin block «Автоматический сбор» — immediate PATCH, no Save button (ING-06; D-15/D-16/D-17).
 *
 * @param {{
 *   schedule: import('../services/ingestScheduleApi.js').IngestionScheduleDto | null,
 *   loadError?: string | null,
 *   loading?: boolean,
 *   onScheduleChange: (next: import('../services/ingestScheduleApi.js').IngestionScheduleDto) => void,
 *   onLoadError?: (message: string) => void,
 *   onRetry?: () => void,
 * }} props
 */
export default function IngestionScheduleSection({
  schedule,
  loadError = null,
  loading = false,
  onScheduleChange,
  onLoadError: _onLoadError,
  onRetry,
}) {
  const [busy, setBusy] = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [timeDraft, setTimeDraft] = useState(schedule?.time_of_day ?? '06:00')

  useEffect(() => {
    if (schedule?.time_of_day) {
      setTimeDraft(schedule.time_of_day)
    }
  }, [schedule?.time_of_day])

  const enabledLabel = schedule?.enabled ? 'Включён' : 'Выключен'
  // Empty-week validation is shown alone (D-15); other messages append after state.
  const statusText =
    statusMsg === EMPTY_WEEK_MSG
      ? EMPTY_WEEK_MSG
      : [enabledLabel, statusMsg].filter(Boolean).join('. ')

  async function onToggle() {
    if (!schedule || busy) return
    setBusy(true)
    setStatusMsg('')
    try {
      const updated = await patchIngestionSchedule({ enabled: !schedule.enabled })
      onScheduleChange(updated)
      setStatusMsg('Сохранено')
    } catch (err) {
      setStatusMsg(
        err instanceof IngestScheduleError
          ? err.message
          : 'Не удалось сохранить настройки сбора. Повторите действие.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function onTimeBlur() {
    if (!schedule || busy) return
    const next = String(timeDraft ?? '').trim()
    if (!next || next === schedule.time_of_day) return
    setBusy(true)
    setStatusMsg('')
    try {
      const updated = await patchIngestionSchedule({ time_of_day: next })
      onScheduleChange(updated)
      setTimeDraft(updated.time_of_day)
      setStatusMsg('Сохранено')
    } catch (err) {
      setTimeDraft(schedule.time_of_day)
      setStatusMsg(
        err instanceof IngestScheduleError
          ? err.message
          : 'Не удалось сохранить настройки сбора. Повторите действие.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function onDayToggle(day) {
    if (!schedule || busy) return
    const current = Array.isArray(schedule.days_of_week) ? schedule.days_of_week : []
    const has = current.includes(day)
    const nextDays = has ? current.filter((d) => d !== day) : [...current, day].sort((a, b) => a - b)
    if (nextDays.length === 0) {
      setStatusMsg(EMPTY_WEEK_MSG)
      return
    }
    setBusy(true)
    setStatusMsg('')
    try {
      const updated = await patchIngestionSchedule({ days_of_week: nextDays })
      onScheduleChange(updated)
      setStatusMsg('Сохранено')
    } catch (err) {
      setStatusMsg(
        err instanceof IngestScheduleError
          ? err.message
          : 'Не удалось сохранить настройки сбора. Повторите действие.',
      )
    } finally {
      setBusy(false)
    }
  }

  const showError = Boolean(loadError) && !schedule
  const ariaBusy = loading || busy

  return (
    <section
      data-testid="ingestion-schedule-section"
      className="mt-6 mb-6 rounded-2xl border border-rule bg-paper p-4 md:p-6"
      aria-busy={ariaBusy}
    >
      <h2
        data-testid="ingestion-schedule-heading"
        className="font-sans text-2xl font-semibold text-ink"
      >
        Автоматический сбор
      </h2>
      <p className="mt-1 text-sm text-muted">Время указывается по московскому времени</p>

      {loading && !schedule ? (
        <p className="mt-4 text-sm text-muted">Загрузка…</p>
      ) : null}

      {showError ? (
        <div className="mt-4">
          <p className="text-sm text-ink-2">{loadError}</p>
          <button
            type="button"
            data-testid="ingestion-schedule-retry"
            className="mt-2 inline-flex min-h-11 items-center font-medium text-accent hover:underline"
            onClick={() => {
              if (typeof onRetry === 'function') onRetry()
            }}
          >
            Повторить загрузку
          </button>
        </div>
      ) : null}

      {schedule ? (
        <div className="mt-4 space-y-5">
          <div>
            <p className="text-sm font-medium text-ink-2">Сбор</p>
            <button
              type="button"
              data-testid="ingestion-schedule-enabled"
              className="mt-2 inline-flex min-h-11 items-center justify-center rounded-full border border-rule px-5 text-sm font-medium text-ink-2 disabled:cursor-not-allowed disabled:opacity-45"
              aria-pressed={schedule.enabled}
              disabled={busy}
              onClick={onToggle}
            >
              {schedule.enabled ? 'Выключить' : 'Включить'}
            </button>
          </div>

          <div>
            <label htmlFor="ingestion-schedule-time" className="text-sm font-medium text-ink-2">
              Время
            </label>
            <input
              id="ingestion-schedule-time"
              type="time"
              data-testid="ingestion-schedule-time"
              className="mt-2 block min-h-11 rounded-xl border border-rule bg-paper px-3 text-sm text-ink"
              value={timeDraft}
              disabled={busy}
              onChange={(e) => setTimeDraft(e.target.value)}
              onBlur={onTimeBlur}
            />
          </div>

          <div>
            <p className="text-sm font-medium text-ink-2">Дни недели</p>
            <div
              data-testid="ingestion-schedule-days"
              className="mt-2 flex flex-wrap gap-2"
              role="group"
              aria-label="Дни недели"
            >
              {DAY_LABELS.map(({ day, label }) => {
                const pressed = schedule.days_of_week.includes(day)
                return (
                  <button
                    key={day}
                    type="button"
                    data-testid={`ingestion-schedule-day-${day}`}
                    className="inline-flex min-h-11 min-w-11 items-center justify-center rounded-full border border-rule px-3 text-sm font-medium text-ink-2 disabled:cursor-not-allowed disabled:opacity-45"
                    aria-pressed={pressed}
                    disabled={busy}
                    onClick={() => onDayToggle(day)}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>

          <p
            data-testid="ingestion-schedule-status"
            role="status"
            className="text-sm text-muted"
          >
            {statusText}
          </p>
        </div>
      ) : null}
    </section>
  )
}
