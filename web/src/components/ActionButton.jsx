const stateClass = {
  idle: '',
  loading: 'cursor-wait opacity-80',
  error: 'bg-[oklch(48%_0.15_25)] text-accent-ink',
  success: 'bg-[oklch(45%_0.13_155)] text-accent-ink',
}

export default function ActionButton({
  children,
  state = 'idle',
  variant = 'voting',
  className = '',
  disabled = false,
  ...props
}) {
  const variantClass =
    variant === 'voting'
      ? 'bg-voting text-[oklch(24%_0.02_38)]'
      : variant === 'secondary'
        ? 'border border-rule bg-transparent text-accent'
        : 'bg-accent text-accent-ink'

  return (
    <button
      type="button"
      data-state={state === 'idle' ? undefined : state}
      disabled={disabled || state === 'loading'}
      className={[
        'inline-flex min-h-11 items-center justify-center rounded-full px-4 text-sm font-medium transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-55',
        variantClass,
        stateClass[state] ?? '',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </button>
  )
}
