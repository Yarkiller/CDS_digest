import { Link } from 'react-router-dom'

/**
 * Profile stub. Concept 2 progress stats (XP, streak, rank) are deferred to the
 * next version by ADR-0009 and banned in this release by ADR-0007, so the page
 * keeps only the shell entry point.
 */
export default function ProfilePage() {
  return (
    <section data-testid="profile-stub" className="mx-auto max-w-lg">
      <h1 className="font-display text-3xl font-semibold">Профиль</h1>

      {/* No stats card: XP, streak and rank are the deferred next-version variant. */}

      <p className="mt-6 text-text-secondary">
        Полная страница профиля будет разработана в следующих фазах. Пока здесь заглушка.
      </p>
      <p className="mt-8">
        <Link to="/" className="font-medium text-primary-text no-underline hover:underline">
          ← К текущему выпуску
        </Link>
      </p>
    </section>
  )
}
