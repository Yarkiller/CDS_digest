/**
 * Unsaved-changes leave copy and (later) beforeunload arming helper (ADUX-09).
 * Vite-free / React-free so node --test can import this module.
 */

/** Unsaved-changes leave copy (UI-SPEC; D-01/D-07) — the modal body only. */
export const UNSAVED_LEAVE_CONFIRM =
  'Есть несохранённые изменения. Уйти без сохранения?'
