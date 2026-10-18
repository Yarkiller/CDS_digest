import { Link } from 'react-router-dom'
import StreakPill from '../components/StreakPill.jsx'
import { DEMO_LEADERBOARD, LEADERBOARD_NOTE } from '../data/gamification.js'

function rankClass(rank) {
  if (rank === 1) return 'text-rank-1'
  if (rank === 2) return 'text-rank-2'
  if (rank === 3) return 'text-rank-3'
  return 'text-text-secondary'
}

/**
 * Public leaderboard (ADR-0001). Renders labelled demo seed data until the
 * gamification module ships (post-v1).
 */
export default function LeaderboardPage() {
  return (
    <section data-testid="leaderboard-page" className="mx-auto max-w-3xl">
      <h1 className="font-display text-3xl font-semibold">Лидерборд</h1>
      <p className="mt-2 text-text-secondary">Публичный рейтинг активности · ADR-0001</p>
      <p data-testid="leaderboard-note" className="mt-2 text-xs text-text-disabled">
        {LEADERBOARD_NOTE}
      </p>

      <div className="mt-8 overflow-hidden rounded-2xl border border-border bg-bg-surface">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-text-disabled">
              <th scope="col" className="px-4 py-3">#</th>
              <th scope="col" className="px-4 py-3">Участник</th>
              <th scope="col" className="px-4 py-3">Ур.</th>
              <th scope="col" className="px-4 py-3">XP</th>
              <th scope="col" className="px-4 py-3">Серия</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_LEADERBOARD.map((row) => (
              <tr
                key={row.rank}
                data-testid="leaderboard-row"
                data-self={row.isSelf ? 'true' : undefined}
                className="border-t border-border"
              >
                <td className="px-4 py-3">
                  <span className={`font-mono font-semibold ${rankClass(row.rank)}`}>#{row.rank}</span>
                </td>
                <td className="px-4 py-3">
                  {row.isSelf ? <strong>Вы</strong> : row.name}
                </td>
                <td className="px-4 py-3">Ур. {row.level}</td>
                <td className="px-4 py-3 font-mono">{row.xp}</td>
                <td className="px-4 py-3">
                  <StreakPill count={row.streakDays} size="sm" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mt-6">
        <Link to="/" className="font-medium text-primary no-underline hover:underline">
          ← К текущему выпуску
        </Link>
      </p>
    </section>
  )
}
