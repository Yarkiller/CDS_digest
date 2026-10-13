import { Link } from 'react-router-dom'

/**
 * 403 deep-link page for non-admin /admin/* (D-75, ADMIN-01).
 */
export default function ForbiddenPage() {
  return (
    <section
      data-testid="forbidden-page"
      className="mx-auto flex w-full max-w-lg flex-col items-start rounded-2xl border border-border bg-bg-app px-6 py-10 sm:px-10"
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-text-disabled">Админ</p>
      <h1 className="mt-2 font-sans text-3xl font-semibold text-text-primary">Недостаточно прав</h1>
      <p className="mt-4 text-sm leading-relaxed text-text-secondary sm:text-base">
        Этот раздел доступен только администраторам Digest CDS.
      </p>
      <Link
        to="/"
        className="mt-8 inline-flex min-h-11 items-center font-medium text-primary no-underline hover:underline"
      >
        На выпуск
      </Link>
    </section>
  )
}
