/**
 * Unsaved-changes leave copy and beforeunload arming helper (ADUX-09).
 * Vite-free / React-free so node --test can import this module.
 */

/** Unsaved-changes leave copy (UI-SPEC; D-01/D-07) — the modal body only. */
export const UNSAVED_LEAVE_CONFIRM =
  'Есть несохранённые изменения. Уйти без сохранения?'

/**
 * Exact `beforeunload` contract (D-05/D-06): two statements, nothing else.
 * No window.confirm / alert — the prompt text is browser-owned; the string form
 * of returnValue is deprecated and ignored by modern browsers.
 *
 * @param {BeforeUnloadEvent} event
 */
export function armBeforeUnload(event) {
  event.preventDefault()
  event.returnValue = true
}
