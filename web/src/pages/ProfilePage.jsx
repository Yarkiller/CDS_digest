import { Link } from 'react-router-dom'

/**
 * Profile stub — full profile UI lands in a later phase.
 */
export default function ProfilePage() {
  return (
    <section data-testid="profile-stub" className="mx-auto max-w-lg">
      <h1 className="font-display text-3xl font-semibold">Профиль</h1>
      <p className="mt-4 text-ink-2">
        Страница профиля будет разработана в следующих фазах. Пока здесь заглушка.
      </p>
      <p className="mt-8">
        <Link to="/" className="font-medium text-accent no-underline hover:underline">
          ← К текущему выпуску
        </Link>
      </p>
    </section>
  )
}
