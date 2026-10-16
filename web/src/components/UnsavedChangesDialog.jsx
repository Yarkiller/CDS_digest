import { useEffect } from 'react'
import { UNSAVED_LEAVE_CONFIRM } from '../utils/unsavedChangesGuard.js'

/**
 * In-app unsaved-leave modal (ADUX-09, D-01/D-02/D-03).
 * Esc = stay (safe action). No focus trap / auto-focus / restore (D-02).
 *
 * @param {{ open: boolean, onStay: () => void, onLeave: () => void }} props
 */
export default function UnsavedChangesDialog({ open, onStay, onLeave }) {
  useEffect(() => {
    if (!open) return undefined
    function onKeyDown(event) {
      if (event.key === 'Escape') onStay()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onStay])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-[400] flex items-center justify-center bg-ink/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="unsaved-changes-title"
    >
      <div className="w-full max-w-md rounded-2xl bg-paper p-6">
        <h2 id="unsaved-changes-title" className="text-2xl font-semibold text-ink">
          Несохранённые изменения
        </h2>
        <p
          data-testid="unsaved-changes-message"
          className="mt-4 text-sm leading-relaxed text-ink-2"
        >
          {UNSAVED_LEAVE_CONFIRM}
        </p>
        <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            data-testid="unsaved-changes-stay"
            className="inline-flex min-h-11 items-center justify-center rounded-full border border-rule px-4 text-sm text-ink-2"
            onClick={onStay}
          >
            Остаться
          </button>
          <button
            type="button"
            data-testid="unsaved-changes-leave"
            className="inline-flex min-h-11 items-center justify-center rounded-full bg-accent px-4 text-sm font-medium text-accent-ink"
            onClick={onLeave}
          >
            Уйти без сохранения
          </button>
        </div>
      </div>
    </div>
  )
}
