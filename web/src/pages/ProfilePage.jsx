import { Link } from 'react-router-dom'
import RankChip from '../components/RankChip.jsx'
import StreakPill from '../components/StreakPill.jsx'
import XpBar from '../components/XpBar.jsx'
import { DEMO_ME_STATS } from '../data/gamification.js'

/**
 * Profile stub with Concept 2 progress stats. Full profile UI lands in a later
 * phase; stats are labelled demo seed (gamification is post-v1, ADR-0001).
 */
export default function ProfilePage() {
  const remaining = Math.max(0, DEMO_ME_STATS.xpMax - DEMO_ME_STATS.xp)

  return (
    <section data-testid="profile-stub" className="mx-auto max-w-lg">
      <h1 className="font-display text-3xl font-semibold">Профиль</h1>

      <div
        data-testid="profile-stats"
        className="mt-6 rounded-2xl border border-border bg-bg-surface p-5"
        title="Демо-данные: геймификация появится после v1 (ADR-0001)"
      >
        <div className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-sm text-text-secondary">Уровень {DEMO_ME_STATS.level}</span>
          <span className="font-mono text-sm text-xp">
            {DEMO_ME_STATS.xp} / {DEMO_ME_STATS.xpMax} XP
          </span>
        </div>
        <XpBar
          data-testid="xp-bar"
          className="mt-3"
          level={DEMO_ME_STATS.level}
          current={DEMO_ME_STATS.xp}
          max={DEMO_ME_STATS.xpMax}
        />
        <p className="mt-2 text-xs text-text-disabled">{remaining} XP до следующего уровня</p>

        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-text-secondary">
          <span className="flex items-center gap-2">
            Серия
            <StreakPill data-testid="streak-pill" count={DEMO_ME_STATS.streakDays} size="sm" />
          </span>
          <span className="flex items-center gap-2">
            Ранг
            <RankChip data-testid="rank-chip" rank={DEMO_ME_STATS.rank} />
          </span>
        </div>
      </div>

      <p className="mt-6 text-text-secondary">
        Полная страница профиля будет разработана в следующих фазах. Пока здесь заглушка.
      </p>
      <p className="mt-8">
        <Link to="/" className="font-medium text-primary no-underline hover:underline">
          ← К текущему выпуску
        </Link>
      </p>
    </section>
  )
}
