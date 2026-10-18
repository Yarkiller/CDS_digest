import { Link } from 'react-router-dom'

/**
 * Editorial voting callout — open CTA optional; closed omits action (D-35).
 * @param {{ children: import('react').ReactNode, actionTo?: string, actionLabel?: string, muted?: boolean }} props
 */
export default function EditorialCallout({ children, actionTo, actionLabel, muted = false }) {
  const surface = muted
    ? 'border-border bg-bg-surface text-text-secondary'
    : 'border-voting bg-primary/15'
  return (
    <div
      data-testid="editorial-callout"
      className={`my-8 flex flex-wrap items-center justify-between gap-4 border p-5 ${surface}`}
    >
      <div className="text-sm text-text-primary">{children}</div>
      {actionTo && actionLabel ? (
        <Link
          to={actionTo}
          className="inline-flex min-h-11 items-center rounded-full px-3 text-sm text-primary hover:bg-bg-surface"
        >
          {actionLabel}
        </Link>
      ) : null}
    </div>
  )
}
