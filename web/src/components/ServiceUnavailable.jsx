import { useState } from 'react'

/**
 * Page-level load-failure splash (D-21…D-23).
 * Friendly art + fixed Russian copy + Retry — never HTTP codes/stacktraces.
 */
export default function ServiceUnavailable({ onRetry }) {
  const [busy, setBusy] = useState(false)

  async function handleRetry() {
    if (busy || !onRetry) return
    setBusy(true)
    try {
      await onRetry()
    } finally {
      setBusy(false)
    }
  }

  return (
    <section
      role="alert"
      data-testid="service-unavailable"
      className="mx-auto flex w-full max-w-lg flex-col items-center px-2 py-8 text-center"
    >
      <img
        src="/bad_gateway.png"
        alt="Котёнок: ошибочка вышла"
        width={420}
        height={360}
        className="h-auto w-full max-w-[360px] sm:max-w-[420px]"
      />
      <p className="mt-6 max-w-prose text-sm leading-relaxed text-ink-2 sm:text-base">
        Не удалось загрузить. Проверьте соединение и попробуйте ещё раз.
      </p>
      <button
        type="button"
        className="mt-6 inline-flex min-h-11 items-center justify-center rounded-full bg-accent px-5 text-sm font-medium text-accent-ink disabled:cursor-wait disabled:opacity-60"
        disabled={busy}
        aria-busy={busy}
        onClick={handleRetry}
      >
        {busy ? 'Загрузка…' : 'Повторить'}
      </button>
    </section>
  )
}
