import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import SearchPill from './SearchPill.jsx'
import { getAccessToken } from '../services/authApi.js'
import { isLoginRequired, isMocksEnabled } from '../services/authEnv.js'
import { fetchMe } from '../services/meApi.js'

const MOCK_SHELL_IDENTITY = 'Мария Сидорова'

const linkClass = ({ isActive }) =>
  [
    'inline-flex min-h-11 items-center rounded-full px-3 text-sm',
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
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
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
              <>
                <NavLink to="/admin/digest" className={linkClass}>
                  Админ
                </NavLink>
                <NavLink to="/admin/pipeline" className={linkClass}>
                  Пайплайн
                </NavLink>
              </>
            ) : null}
          </nav>
          <SearchPill />
          {identity ? (
            <Link
              to="/profile"
              className="max-w-[10rem] shrink-0 truncate text-sm text-text-secondary underline-offset-2 hover:text-primary hover:underline sm:max-w-[14rem]"
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
