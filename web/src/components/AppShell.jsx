import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import RankChip from './RankChip.jsx'
import SearchPill from './SearchPill.jsx'
import StreakPill from './StreakPill.jsx'
import ThemeToggle from './ThemeToggle.jsx'
import XpBar from './XpBar.jsx'
import { getAccessToken } from '../services/authApi.js'
import { isLoginRequired, isMocksEnabled } from '../services/authEnv.js'
import { fetchMe } from '../services/meApi.js'
import { DEMO_ME_STATS } from '../data/gamification.js'

const MOCK_SHELL_IDENTITY = 'Мария Сидорова'

const linkClass = ({ isActive }) =>
  [
    'inline-flex min-h-11 items-center rounded-full px-2.5 text-sm',
    isActive ? 'bg-primary text-text-primary' : 'text-text-secondary hover:bg-bg-surface',
  ].join(' ')

/** Fallback identity for local mock browsing — never shown when login is required. */
function mockIdentity() {
  return isMocksEnabled() && !isLoginRequired() ? MOCK_SHELL_IDENTITY : ''
}

async function resolveShellSession(token) {
  if (!token) {
    const me = await fetchMe(null)
    return { identity: mockIdentity(), appRole: me.role ?? 'employee' }
  }
  const me = await fetchMe(token)
  const identity = me.display_name?.trim() || me.email || mockIdentity()
  return { identity, appRole: me.role ?? 'employee' }
}

export default function AppShell() {
  const [identity, setIdentity] = useState(() => mockIdentity())
  const [appRole, setAppRole] = useState(/** @type {string | null} */ (null))
  const { pathname } = useLocation()
  // D-09: «Админ» lights up on digest, pipeline, and the materials preview alike.
  // IN-04: the /admin/ prefix is the single source of truth — there is no /admin route
  // (D-04), and the catch-all redirects /admin to /, so an equality branch is dead code.
  const adminActive = pathname.startsWith('/admin/')

  useEffect(() => {
    let cancelled = false

    async function loadIdentity() {
      try {
        const session = await resolveShellSession(await getAccessToken())
        if (!cancelled) {
          setIdentity(session.identity)
          setAppRole(session.appRole)
        }
      } catch {
        if (!cancelled) {
          setIdentity(mockIdentity())
          setAppRole('employee')
        }
      }
    }

    loadIdentity()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="min-h-svh bg-bg-app text-text-primary">
      <header className="sticky top-0 z-40 border-b border-border bg-bg-app">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-1.5 px-4 py-3">
          <div className="mr-auto min-w-0">
            <p className="font-display text-sm font-semibold text-primary">Digest CDS</p>
            <p className="text-xs text-text-disabled">СВА · издание</p>
          </div>
          <nav
            className="order-last flex w-full flex-wrap gap-1 sm:order-none sm:w-auto"
            aria-label="Основная навигация"
          >
            <NavLink to="/" end className={linkClass}>
              Выпуск
            </NavLink>
            <NavLink to="/archive" className={linkClass}>
              Архив
            </NavLink>
            <NavLink to="/knowledge" className={linkClass}>
              База
            </NavLink>
            <NavLink to="/voting" className={linkClass}>
              Голосование
            </NavLink>
            <NavLink to="/razbory" className={linkClass}>
              Разборы
            </NavLink>
            {appRole === 'admin' ? (
              <Link
                to="/admin/digest"
                // WR-02: NavLink derives aria-current from `to="/admin/digest"`, so the pill
                // was announced as inactive on pipeline/preview while looking active. Set it
                // from the already-computed prefix instead — "true" (not "page") because the
                // href targets digest while the whole admin section is the current context.
                aria-current={adminActive ? 'true' : undefined}
                className={linkClass({ isActive: adminActive })}
              >
                Админ
              </Link>
            ) : null}
          </nav>
          <SearchPill />
          <div
            className="flex flex-wrap items-center gap-1.5"
            data-testid="shell-gamification"
            title="Демо-данные: геймификация появится после v1 (ADR-0001)"
          >
            <StreakPill data-testid="streak-pill" count={DEMO_ME_STATS.streakDays} />
            <XpBar
              data-testid="xp-bar"
              className="hidden sm:flex"
              level={DEMO_ME_STATS.level}
              current={DEMO_ME_STATS.xp}
              max={DEMO_ME_STATS.xpMax}
            />
            <RankChip data-testid="rank-chip" rank={DEMO_ME_STATS.rank} />
            <ThemeToggle data-testid="theme-toggle" />
          </div>
          {identity ? (
            <Link
              to="/profile"
              className="max-w-[10rem] shrink-0 truncate text-sm text-text-secondary underline-offset-2 hover:text-primary hover:underline sm:max-w-[8rem]"
              data-testid="shell-identity"
              title={identity}
            >
              {identity}
            </Link>
          ) : null}
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-10">
        <Outlet />
      </main>
    </div>
  )
}
