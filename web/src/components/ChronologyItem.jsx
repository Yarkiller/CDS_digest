import { Link } from 'react-router-dom'
import { RAZBOR_EDITOR_BYLINE, razborStatusLabel } from '../services/razboryApi.js'

/**
 * Format meeting_at ISO → Russian long date for chronology overline.
 * @param {string | null | undefined} iso
 */
export function formatRazborMeetingDate(iso) {
  if (!iso) return null
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return null
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(d)
}

/**
 * Chronology-item row (D-67) — not MaterialListRow covers.
 * @param {{ item: { id: number, title: string, meeting_at?: string | null, status: string } }} props
 */
export default function ChronologyItem({ item }) {
  const dateLabel = formatRazborMeetingDate(item.meeting_at)
  const statusLabel = razborStatusLabel(item.status)
  const overline = [dateLabel, statusLabel].filter(Boolean).join(' · ')

  return (
    <article className="border-b border-rule py-6" data-testid="chronology-item">
      {overline ? (
        <span className="mb-2 block text-xs font-semibold uppercase tracking-wide text-muted">
          {overline}
        </span>
      ) : null}
      <h2 className="mb-3 font-display text-2xl font-semibold text-ink">{item.title}</h2>
      <p className="mb-4 text-sm text-ink-2">{RAZBOR_EDITOR_BYLINE}</p>
      {item.status === 'announcement' ? (
        <p className="text-sm text-muted" data-testid="chronology-pending">
          Разбор этой темы ещё готовится — следите за обновлениями
        </p>
      ) : (
        <Link
          to={`/razbory/${item.id}`}
          className="inline-flex min-h-11 items-center text-sm font-medium text-accent no-underline hover:underline"
        >
          Читать разбор →
        </Link>
      )}
    </article>
  )
}
