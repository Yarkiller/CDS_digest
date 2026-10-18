import { Link } from 'react-router-dom'

/**
 * Editorial voting callout — open CTA optional; closed omits action (D-35).
 * @param {{ children: import('react').ReactNode, actionTo?: string, actionLabel?: string, muted?: boolean }} props
 */
export default function EditorialCallout({ children, actionTo, actionLabel, muted = false }) {
  const surface = muted
    ? 'border-rule bg-paper-2 text-ink-2'
    : 'border-voting bg-[oklch(94%_0.025_278)]'
  return (
    <div
      data-testid="editorial-callout"
      className={`my-8 flex flex-wrap items-center justify-between gap-4 border p-5 ${surface}`}
    >
      <div className="text-sm text-ink">{children}</div>
      {actionTo && actionLabel ? (
        <Link
          to={actionTo}
          className="inline-flex min-h-11 items-center rounded-full px-3 text-sm text-accent hover:bg-paper-2"
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  )
}
