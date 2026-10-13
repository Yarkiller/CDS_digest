export default function StreakPill({ count = 12, size = 'md', className = '' }) {
  const isSmall = size === 'sm'
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border border-border bg-bg-elevated font-mono font-semibold text-text-primary ${isSmall ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'} ${className}`}
    >
      <span className="text-streak">
        <svg
          width={isSmall ? 12 : 14}
          height={isSmall ? 12 : 14}
          viewBox="0 0 24 24"
          fill="currentColor"
          aria-hidden="true"
        >
          <path d="M12 2s-5 8-5 12a5 5 0 0 0 10 0c0-4-5-12-5-12z" />
        </svg>
      </span>
      {count}
    </span>
  )
}
