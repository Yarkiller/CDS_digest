export default function ErrorPanel({ title, message, meta, onDismiss }) {
  return (
    <div
      role="alert"
      className="mr-auto w-full max-w-md rounded-xl border border-[oklch(70%_0.12_25)] bg-[oklch(96%_0.03_25)] p-4 text-[oklch(35%_0.12_25)] sm:w-auto"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-base font-semibold">{title}</h2>
          <p className="mt-1 text-sm leading-snug">{message}</p>
          {meta ? <p className="mt-2 text-xs opacity-80">{meta}</p> : null}
        </div>
        {onDismiss ? (
          <button
            type="button"
            className="min-h-11 shrink-0 rounded-full px-2 text-sm hover:bg-[oklch(92%_0.04_25)]"
            aria-label="Скрыть сообщение об ошибке"
            onClick={onDismiss}
          >
            ✕
          </button>
        ) : null}
      </div>
    </div>
  )
}
