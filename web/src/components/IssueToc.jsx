import { Link } from 'react-router-dom'
import { padIssueNumber } from '../utils/filters.js'

export default function IssueToc({ items }) {
  return (
    <div className="divide-y divide-rule border-y border-rule">
      {items.map((item) => (
        <div key={item.id} className="py-5">
          <Link
            to={`/materials/${item.id}`}
            className="grid min-h-11 grid-cols-[2rem_minmax(0,1fr)_auto] items-baseline gap-4 rounded-xl px-2 text-inherit no-underline transition-colors hover:bg-[oklch(94%_0.025_278)] hover:text-accent sm:grid-cols-[2rem_minmax(0,1fr)_auto_auto]"
          >
            <span className="font-mono text-xs text-muted">{padIssueNumber(item.issuePosition)}</span>
            <span className="min-w-0 font-display text-lg font-semibold">{item.title}</span>
            <span className="hidden text-xs text-ink-2 sm:inline">
              {item.format} · {item.readingMinutes} мин
            </span>
            <span className="text-muted" aria-hidden="true">
              →
            </span>
          </Link>
          <p className="mt-2 max-w-prose pl-12 text-sm text-ink-2">{item.dek}</p>
        </div>
      ))}
    </div>
  )
}
