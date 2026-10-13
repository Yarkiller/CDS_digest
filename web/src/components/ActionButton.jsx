const stateClass = {
  idle: '',
  loading: 'cursor-wait opacity-80',
  error: 'bg-danger text-text-primary',
  success: 'bg-success text-text-primary',
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
      ? 'bg-voting text-bg-app'
      : variant === 'secondary'
        ? 'border border-border bg-transparent text-primary'
        : 'bg-primary text-text-primary'

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
