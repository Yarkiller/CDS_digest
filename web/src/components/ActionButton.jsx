/**
 * The fill a state *replaces* the variant fill with.
 *
 * `loading` is deliberately empty: it paints no fill of its own and only dims the variant
 * (25-VERIFICATION #13 — «in-flight the label keeps its colour, only opacity changes»), so
 * it must not enter the "has a fill" branch below.
 */
const stateFill = {
  idle: '',
  loading: '',
  error: 'bg-danger-solid text-on-solid',
  success: 'bg-success-solid text-on-solid',
}

/** Additive per-state chrome; never carries a background. */
const stateChrome = {
  loading: 'cursor-wait opacity-80',
}

export default function ActionButton({
  children,
  state = 'idle',
  variant = 'voting',
  className = '',
  disabled = false,
  ...props
}) {
  const hasStateFill = Boolean(stateFill[state])

  /**
   * WR-03: exactly one fill source. The state fill REPLACED the variant fill instead of being
   * appended after it — two `bg-*` in one class list make the outcome depend on stylesheet
   * order, and white on the yellow `voting` fill measures 1.918. For `secondary` the state
   * fill keeps only `border border-border`: `bg-transparent` would be a second `bg-*` and
   * `text-primary-text` would compete with `text-on-solid`. The base `primary` stays a
   * fill/border/ring/tint (D-05); the label role is the separate `primary-text` token
   * (`--color-primary` as text reads 3.566…4.529, below the 4.5:1 floor — G-20).
   */
  const variantClass = hasStateFill
    ? variant === 'secondary'
      ? 'border border-border'
      : ''
    : variant === 'voting'
      ? 'bg-voting text-voting-ink'
      : variant === 'secondary'
        ? 'border border-border bg-transparent text-primary-text'
        : 'bg-primary-solid text-on-solid'

  return (
    <button
      type="button"
      data-state={state === 'idle' ? undefined : state}
      disabled={disabled || state === 'loading'}
      className={[
        'inline-flex min-h-11 items-center justify-center rounded-full px-4 text-sm font-medium transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-55',
        variantClass,
        stateFill[state] ?? '',
        stateChrome[state] ?? '',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </button>
  )
}
